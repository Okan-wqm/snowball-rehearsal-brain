"""Secret scan for diffs, ledger rows and outgoing prompts (stage 0, MF2).

Rules: tohum/08 item 11 (every diff, ledger row and outgoing prompt is scanned; a match invalidates the
run and the prompt is not sent), tohum/26a (secrets.scan: input diff, row, prompt; output the matches;
callers llm.call, gate.check, ledger.append), tohum/30c (a finding never carries the secret's value, only
where it is and its sha256 fingerprint).

- A match is ``{rule, line, sha256}`` plus ``path`` for diffs: the rule that fired, the 1-based line of
  the input, and the sha256 of the matched text. The matched text itself never leaves this module.
- Rules are the high-confidence token shapes of the providers the system touches (Anthropic, GitHub,
  AWS, Google, Slack, Stripe, npm, GitLab, OpenAI), private key blocks, JWTs, credentials inside URLs and
  a quoted or bare value assigned to a secret-named key, unless the whole value is a template (or,
  unquoted, a code reference).
  Callers may add ``known`` values (the referee's own secrets, by environment variable name on the
  command line): those match verbatim.
- Every line is scanned three ways: as written; with ``\\uXXXX`` / ``\\xNN`` / ``\\"`` escapes decoded
  (a JSON row may spell a token in escapes, and always escapes the quotes around a value); and
  NFKC-folded with invisible format characters (zero-width space, soft hyphen, BOM ...) removed;
  percent-decoded; and each base64 run that decodes to text is scanned as text. Two adjacent lines are
  also scanned joined, so a token or a key and its value split over a line break is caught. What is
  out of reach: a secret that only code would compute ("gh" + "p_..."), since no text holds it. A diff
  is scanned whole: removed and context lines leak as much as added ones once the diff is put in a
  prompt.
- Fail closed: input that is not UTF-8 is decoded with replacement and still scanned; an unreadable file
  or a bad command line is exit 2, never "clean".

Command line, run from ``referee/`` (stdout is one JSON line; exit 0 clean, 1 match, 2 unusable input):

    python -m gate.secrets scan --kind diff|row|prompt [--known-env NAME ...] [FILE]   FILE or stdin
    python -m gate.secrets send [--known-env NAME ...] -- CMD [ARG ...]

``scan`` prints ``{"clean", "kind", "run_valid", "matches"}``. ``send`` reads a prompt on stdin, scans
it as a prompt and only when it is clean runs CMD with the prompt on CMD's stdin (CMD's stdout goes to
stderr); it prints ``{"clean", "run_valid", "sent", "sender_exit", "matches"}``. A match means
``run_valid: false`` and ``sent: false``: CMD is never started. A clean prompt exits 0 whatever CMD
returned; ``sender_exit`` carries CMD's code.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
from typing import Callable, Iterable

KINDS = ("diff", "row", "prompt")
MIN_KNOWN = 8  # shorter "known" values would match everywhere and mean nothing

# No rule is anchored on a word boundary (\b) or on what follows the token: "_" and letters are word
# characters, so x_<token> or <token>_x would have no boundary and slip through. The prefixes are
# distinctive enough on their own; a token glued to other text still leaks once the text is sent.
RULES: list[tuple[str, re.Pattern]] = [
    ("anthropic-key", re.compile(r"sk-ant-[a-z]{2,8}\d{2}-[A-Za-z0-9_\-]{20,}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,255}")),
    ("github-pat", re.compile(r"github_pat_[A-Za-z0-9_]{60,255}")),
    ("aws-access-key-id", re.compile(r"(?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z2-7]{16}")),
    ("aws-secret-key", re.compile(
        r"(?i)aws_?secret_?(?:access_?)?key[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9/+]{40}")),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("slack-token", re.compile(r"xox[abposr]-[A-Za-z0-9\-]{10,}")),
    ("slack-webhook", re.compile(r"hooks\.slack\.com/services/T[A-Za-z0-9_]+/B[A-Za-z0-9_]+/[A-Za-z0-9_]+")),
    ("stripe-key", re.compile(r"[rs]k_(?:live|test)_[0-9A-Za-z]{24,}")),
    ("npm-token", re.compile(r"npm_[A-Za-z0-9]{36}")),
    ("gitlab-token", re.compile(r"glpat-[A-Za-z0-9_\-]{20,}")),
    ("openai-key", re.compile(r"sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{20,}T3BlbkFJ[A-Za-z0-9_\-]{20,}")),
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("url-credentials", re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]{1,15}://[^\s/:@\"'<>]{1,64}:([^\s/@\"'<>]{6,128})@")),
]

# A value assigned to a secret-named key: quoted (spaces allowed, a passphrase is a secret too) or bare,
# of 8 or more characters. There is no entropy test: a weak password is still a password (hunter22 leaks
# as much as a random string). A value is skipped only when the whole of it is a template or, unquoted,
# a code reference (``_placeholder``); a value that merely starts with ``$`` or holds ``(`` is a value.
ASSIGNMENT = re.compile(
    r"(?i)(?:passw(?:or)?d|passphrase|pwd|secret|token|api[_\-]?key|access[_\-]?key|private[_\-]?key|"
    r"credential|auth)[A-Za-z0-9_\-]*[\"'`]?[ \t]*(?::=|=>|[:=])[ \t]*"
    r"(?:\"([^\"\n]{8,})\"|'([^'\n]{8,})'|`([^`\n]{8,})`|([^\s\"'`,;()\[\]{}]{8,}))")
PLACEHOLDER_WORDS = {"password", "passwd", "secret", "changeme", "example", "redacted", "placeholder",
                     "undefined", "none", "null", "true", "false"}
# Whole-value templates: ${NAME}, $NAME (upper case, an environment variable), {{ name }}, <your-token>,
# %(name)s, %NAME%. Anything after or around them makes the value a value again.
TEMPLATE = re.compile(
    r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Z_][A-Z0-9_]*|\{\{[ \t]*[A-Za-z_][A-Za-z0-9_.]*[ \t]*\}\}|"
    r"<[A-Za-z][A-Za-z0-9_\- ]*>|%\([A-Za-z_][A-Za-z0-9_]*\)[sd]|%[A-Z_][A-Z0-9_]*%")
CODE_PATH = re.compile(r"[A-Za-z]+(?:[._][A-Za-z]+)+")
URL_PLACEHOLDERS = {"password", "passwd", "secret", "changeme", "example", "xxxxxx", "********"}

ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})|\\([\"'/\\])")
DIFF_PATH = re.compile(r"^\+\+\+ (?:b/)?(.*?)\s*$")
BASE64_RUN = re.compile(r"[A-Za-z0-9+/_\-]{16,}={0,2}")


class ScanError(ValueError):
    """The scan could not be done; callers must treat this as not clean."""


class SecretFound(RuntimeError):
    """A scanned text holds a secret: the run is invalid and nothing is sent."""

    def __init__(self, kind: str, matches: list[dict]):
        super().__init__("%s holds %d secret match(es); run invalid" % (kind, len(matches)))
        self.kind = kind
        self.matches = matches


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def _placeholder(value: str, quoted: bool, after: str) -> bool:
    """True when an assigned value cannot be the secret: a whole template, a placeholder word, one
    repeated character, or (unquoted only) a call, a subscript or a dotted or underscored name."""
    if TEMPLATE.fullmatch(value) or len(set(value)) == 1 or value.lower() in PLACEHOLDER_WORDS:
        return True
    if quoted:
        return False
    # get_token(request), os.environ["KEY"], self.token, request.form, secret_value: code, not a value
    return after in ("(", "[") or CODE_PATH.fullmatch(value) is not None


def _unescape(line: str) -> str:
    def one(m: re.Match) -> str:
        if m.group(3):
            return m.group(3)
        code = int(m.group(1) or m.group(2), 16)
        return "" if 0xD800 <= code <= 0xDFFF else chr(code)
    return ESCAPE.sub(one, line)


def _fold(line: str) -> str:
    folded = unicodedata.normalize("NFKC", line)
    return "".join(ch for ch in folded if unicodedata.category(ch) != "Cf")


def _base64_texts(line: str) -> list[str]:
    """Each base64 (standard or URL-safe) run of 16+ characters that decodes to printable UTF-8 text."""
    out = []
    for m in BASE64_RUN.finditer(line):
        run = m.group(0).rstrip("=").replace("-", "+").replace("_", "/")
        try:
            text = base64.b64decode(run + "=" * (-len(run) % 4), validate=True).decode("utf-8")
        except (binascii.Error, ValueError):
            continue
        if text and all(ch.isprintable() or ch in "\t\r\n" for ch in text):
            out.append(text)
    return out


def _variants(line: str) -> list[str]:
    out = [line]
    for candidate in (_unescape(line), _fold(line), _fold(_unescape(line)), urllib.parse.unquote(line)):
        if candidate not in out:
            out.append(candidate)
    for variant in list(out):
        for decoded in _base64_texts(variant):
            for candidate in (decoded, _fold(decoded)):
                if candidate not in out:
                    out.append(candidate)
    return out


def _line_hits(line: str, known: list[tuple[str, str]], tokens: bool = True,
               assignments: bool = True) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for variant in _variants(line):
        for name, pattern in RULES if tokens else ():
            for m in pattern.finditer(variant):
                if name == "url-credentials" and m.group(1).lower() in URL_PLACEHOLDERS:
                    continue
                hits.append((name, m.group(0)))
        for m in ASSIGNMENT.finditer(variant) if assignments else ():
            quoted = m.group(4) is None
            # a bare value loses the full stop or colon that ends a sentence ("... is token:abc.")
            value = m.group(1) or m.group(2) or m.group(3) or m.group(4).rstrip(".:")
            if len(value) >= 8 and not _placeholder(value, quoted, variant[m.end():m.end() + 1]):
                hits.append(("secret-assignment", value))
        for label, value in known if tokens else ():
            if value in variant:
                hits.append((label, value))
    return hits


def scan(text: str, kind: str, known: Iterable[tuple[str, str]] = ()) -> list[dict]:
    """Return the matches in ``text`` (a diff, a ledger row or a prompt); an empty list means clean.

    ``known`` holds ``(label, value)`` pairs that match verbatim; values shorter than ``MIN_KNOWN``
    characters are ignored. No match carries the matched text, only its sha256.
    """
    if kind not in KINDS:
        raise ScanError("kind must be one of %s" % ", ".join(KINDS))
    known_values = [(label, value) for label, value in known if len(value) >= MIN_KNOWN]
    matches: list[dict] = []
    seen: set[tuple[int, str, str]] = set()
    path = None
    lines = text.splitlines()
    hits = [_line_hits(line, known_values) for line in lines]
    for index, line in enumerate(lines):
        lineno = index + 1
        if kind == "diff":
            header = DIFF_PATH.match(line)
            if header:
                path = header.group(1)
        found = list(hits[index])
        if index + 1 < len(lines):
            # a secret split over two lines: join them (the next line without its diff marker and
            # indentation) and keep what neither line holds alone. Tokens are joined with nothing
            # between the halves; a value is joined to its key with a space (YAML "token:" then the
            # value on the next line), so the last word of one line never glues to the first of the next
            following = lines[index + 1]
            if kind == "diff" and following[:1] in ("+", "-", " "):
                following = following[1:]
            alone = set(hits[index]) | set(hits[index + 1])
            head, tail = line.rstrip(), following.lstrip()
            # a trailing backslash continues a string or a shell line: the halves join without it
            pieces = _variants(line) + _variants(following)
            found += [hit for hit in _line_hits(head.removesuffix("\\") + tail, known_values, assignments=False)
                      if hit not in alone and not any(hit[1] in piece for piece in pieces)]
            found += [hit for hit in _line_hits(head + " " + tail, known_values, tokens=False)
                      if hit not in alone]
        for rule, value in found:
            digest = _fingerprint(value)
            if (lineno, rule, digest) in seen:
                continue
            seen.add((lineno, rule, digest))
            match = {"rule": rule, "line": lineno, "sha256": digest}
            if kind == "diff" and path is not None:
                match["path"] = path
            matches.append(match)
    return matches


def require_clean(text: str, kind: str, known: Iterable[tuple[str, str]] = ()) -> None:
    """Raise ``SecretFound`` when ``text`` holds a secret (the caller's run is then invalid)."""
    matches = scan(text, kind, known)
    if matches:
        raise SecretFound(kind, matches)


def send_if_clean(prompt: str, send: Callable[[str], object], known: Iterable[tuple[str, str]] = ()) -> object:
    """Call ``send(prompt)`` only when the prompt is clean; otherwise raise ``SecretFound`` unsent."""
    require_clean(prompt, "prompt", known)
    return send(prompt)


# ---------------------------------------------------------------- command line

def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")
    sys.stdout.flush()


def _known_from_env(names: list[str]) -> list[tuple[str, str]]:
    return [("known:" + name, os.environ[name]) for name in names if os.environ.get(name)]


def _parse(argv: list[str]) -> tuple[str, dict]:
    if not argv or argv[0] not in ("scan", "send"):
        raise ScanError("usage: scan --kind diff|row|prompt [--known-env NAME] [FILE] | send [--known-env NAME] -- CMD")
    command, rest = argv[0], argv[1:]
    opts: dict = {"kind": None, "known_env": [], "file": None, "cmd": []}
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--" and command == "send":
            opts["cmd"] = rest[i + 1:]
            break
        if arg in ("--kind", "--known-env") and i + 1 < len(rest):
            if arg == "--kind":
                opts["kind"] = rest[i + 1]
            else:
                opts["known_env"].append(rest[i + 1])
            i += 2
            continue
        if command == "scan" and opts["file"] is None and not arg.startswith("--"):
            opts["file"] = arg
            i += 1
            continue
        raise ScanError("unexpected argument %r" % arg)
    if command == "scan" and opts["kind"] not in KINDS:
        raise ScanError("scan needs --kind diff|row|prompt")
    if command == "send" and not opts["cmd"]:
        raise ScanError("send needs -- CMD")
    return command, opts


def _read(path: str | None) -> str:
    data = sys.stdin.buffer.read() if path is None else open(path, "rb").read()
    return data.decode("utf-8", "replace")


def main(argv: list[str]) -> int:
    try:
        command, opts = _parse(argv)
        known = _known_from_env(opts["known_env"])
        text = _read(opts["file"])
        kind = opts["kind"] if command == "scan" else "prompt"
        matches = scan(text, kind, known)
    except (ScanError, OSError) as exc:
        _emit({"error": str(exc)})
        return 2
    clean = not matches
    if command == "scan":
        _emit({"clean": clean, "kind": kind, "run_valid": clean, "matches": matches})
        return 0 if clean else 1
    if not clean:
        _emit({"clean": False, "run_valid": False, "sent": False, "sender_exit": None, "matches": matches})
        return 1
    try:
        proc = subprocess.run(opts["cmd"], input=text.encode("utf-8"), stdout=sys.stderr.buffer)
    except OSError as exc:
        _emit({"error": "sender could not start: %s" % exc})
        return 2
    _emit({"clean": True, "run_valid": True, "sent": True, "sender_exit": proc.returncode, "matches": []})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
