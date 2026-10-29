"""Secret scan for diffs, ledger rows and outgoing prompts (stage 0, MF2).

Rules: tohum/08 item 11 (every diff, ledger row and outgoing prompt is scanned; a match invalidates the
run and the prompt is not sent), tohum/26a (secrets.scan: input diff, row, prompt; output the matches;
callers llm.call, gate.check, ledger.append), tohum/30c (a finding never carries the secret's value, only
where it is and its sha256 fingerprint).

- A match is ``{rule, line, sha256}`` plus ``path`` for diffs: the rule that fired, the 1-based line of
  the input, and the sha256 of the matched text. The matched text itself never leaves this module.
- Rules are the high-confidence token shapes of the providers the system touches (Anthropic, GitHub,
  AWS, Google, Slack, Stripe, npm, GitLab, OpenAI), private key blocks, JWTs, a password of any length
  inside a URL, and a quoted or bare value of 8 or more characters assigned to a secret-named key. The
  exact assignment forms, how a value is read and the only values skipped are in the comment above
  ``ASSIGNMENT``, which keys are secret-named in the comment at ``NAME_PARTS``; what they do not report
  is listed there as a boundary, not left implicit.
  Callers may add ``known`` values (the referee's own secrets, by environment variable name on the
  command line): those match verbatim.
- Every line is scanned several ways: as written; with ``\\uXXXX`` / ``\\xNN`` / ``\\"`` escapes decoded
  (a JSON row may spell a token in escapes, and always escapes the quotes around a value); and
  NFKC-folded with invisible format characters (zero-width space, soft hyphen, BOM ...) removed;
  percent-decoded; and each base64 run that decodes to text is scanned as text. Two adjacent lines are
  also scanned joined, so a token or a key and its value split over a line break is caught. What is
  out of reach: a secret that only code would compute ("gh" + "p_..."), since no text holds it; a token
  split over three or more lines; encodings other than the ones above (hex, HTML entities). A diff
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
    ("url-credentials", re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]{1,15}://[^\s/:@\"'<>]+:([^\s/@\"'<>]+)@")),
]

# A value assigned to a secret-named key (which keys are secret-named: the comment at NAME_PARTS).
# The key may be followed by its closing quote and a closing subscript (config["password"]), by a type
# annotation (password: str =) or by the Go string type (password string =). The operator is one of
# = : := => <- == === != !==; or the key is a command-line flag and the value follows a space
# (--password VALUE); or it is a Dockerfile ENV KEY VALUE (upper-case ENV, anywhere in the line). The
# value is read by ``_value``, not by a pattern:
# - unquoted, it runs to the first whitespace outside brackets, so ; , ( ) [ ] { } inside it are part
#   of it. One trailing , ; . : and closing brackets with no opening one are syntax, not value.
# - quoted (" ' or `, with an optional string prefix such as f or b), it runs to the closing quote that
#   is not escaped by a backslash, so it may hold spaces and escaped quotes. Text glued after the
#   closing quote ("abc"def) is part of it unless it starts with , ; . : ) ] }. A quote that never
#   closes is read like an unquoted value.
# - a quote right after an unquoted part (abc"def") gives two readings: the value ends at the quote (in a
#   JSON row that quote closes the string holding the text, so abc"} is read as abc), and the quoted part
#   is glued on (abc"defghij" is also read as abcdefghij; only that first quoted part). The value is
#   reported when either reading is.
# - an authorization scheme word (Bearer, Basic, Token, Digest, Bot) before the value is skipped.
# Every value of 8 or more characters is reported, weak or random, quoted or not, literal or code: there
# is no entropy test, no placeholder list and no test for code. Text alone cannot tell a passphrase from
# a name (correct_horse_battery, self.token, get_token(request) may each be either), so a name or
# expression on the right of a secret-named key is reported like a literal. A value is skipped only when
# (a) nothing is left once every template in it is removed (TEMPLATE: ${NAME}, upper case $NAME, {name},
# {{ name }}, <word>, %(name)s, %NAME%), or (b) it is, in any case, one of NON_VALUES, the null and
# boolean words of the languages the system reads.
# Stated boundaries, not reported: a secret spelled exactly as a whole template or a null word, a value of
# fewer than 8 characters, a value with no operator after its key other than a flag or Dockerfile ENV
# (PASSWORD hunter22), a value whose first word is a scheme word ("token abc" is read as abc), and a key
# none of whose words is secret-named by the rules below (DB_CONN, DSN or LOGIN holding a password: only
# a URL password or a Password= inside it is reported).
# The stated cost: code that assigns a name or expression of 8 or more characters to a secret-named key
# (self.token or request.form after a token or password key) is reported, as are example values such
# as changeme and namespaced words after a secret-named prefix and a colon (a reason code spelled
# secret_in_x, a colon and a word);
# a match stops the send (tohum/08 item 11), so this scanner errs on the side of not sending.
# Which keys are secret-named. The key is a whole word of letters, digits, _ - and . (no word character,
# - or . before it), judged by ``_secret_key``:
# - a key whose last dotted part is one of FILE_EXTENSIONS is a file name (test_secrets.py: in prose),
#   never secret-named;
# - otherwise it is split into words at _ - . and at camelCase humps (DB_PASS, dbPass, db.pass and
#   X-Api-Key give db pass, db pass, db pass and x api key), each word lower-cased; words in PLAIN_WORDS
#   are ordinary words that hold a part by accident (compass, bypass, author, tokenizer, monkey) and
#   count for nothing, while another word of the same key still counts (bypass_password);
# - it is secret-named when one word (a) holds one of NAME_PARTS anywhere in it (password, DBPASS,
#   passphrase, oauth, authToken, cookie ...), or (b) is one of NAME_WORDS (pw, pin, otp ...), or
#   (c) ends with key or keys, unless that word is the bare key or keys and the key has no other word
#   (STRIPE_KEY, apiKey, masterkey, x-api-key count), or (d) is session followed by the word id.
# Stated boundaries: the bare key or keys alone is not secret-named (Python's sort key, every keyword
# argument named key and every map entry's key spell it); nor is any key none of whose words meets
# (a)-(d), whatever it holds (DB_CONN, DSN, LOGIN). The stated cost: a non-secret key that meets them
# (a cache key, the shell's PWD) is reported when a literal value of 8 or more characters is assigned to
# it; this scanner errs on the side of not sending.
NAME_PARTS = ("pass", "pwd", "secret", "token", "credential", "auth", "sessionid", "cookie", "bearer",
              "jwt", "mnemonic", "kennwort", "parola", "sifre", "şifre", "contrasena", "contraseña",
              "senha", "wachtwoord", "haslo", "hasło", "salasana", "lozinka")
NAME_WORDS = {"pw", "pin", "otp", "totp", "cred", "creds", "mdp", "clave", "anahtar"}
PLAIN_WORDS = {"compass", "encompass", "bypass", "surpass", "passenger", "passengers", "passive",
               "passage", "passages", "passthrough", "passing", "passed", "passes", "author", "authors",
               "authored", "authority", "tokenize", "tokenized", "tokenizer", "tokenizers", "tokenization",
               "monkey", "turkey", "donkey", "hockey", "jockey", "whiskey", "hotkey", "turnkey"}
FILE_EXTENSIONS = {"py", "js", "mjs", "cjs", "ts", "tsx", "jsx", "json", "jsonl", "md", "txt", "yaml", "yml",
                   "toml", "sh", "go", "rs", "java", "kt", "rb", "php", "c", "h", "cpp", "html", "css", "lock",
                   "log"}
KEY = r"(?<![\w\-.])(?P<key>[\w\-.]*\w)"
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
TYPE = r"[A-Za-z_][A-Za-z0-9_.]*(?:\[[^\]\n]*\])?(?:[ \t]*\|[ \t]*[A-Za-z_][A-Za-z0-9_.]*(?:\[[^\]\n]*\])?)*"
ASSIGNMENT = re.compile(
    KEY + r"[\"'`]?\]?[ \t]*"
    r"(?:(?::[ \t]*" + TYPE + r"[ \t]*|[ \t]+string[ \t]*)?(?:===?|!==?|:=|=>|<-|=)|:)[ \t]*")
FLAG = re.compile(r"(?<![\w\-])--?(?P<key>[\w\-]*\w)[ \t]+")
ENV_FORM = re.compile(r"(?<![\w\-.])ENV[ \t]+(?P<key>[\w\-.]+)[ \t]+(?=[^\s=])")  # Dockerfile ENV KEY VALUE
SCHEME = re.compile(r"(?i)(?:bearer|basic|token|digest|bot)[ \t]+")
QUOTES = "\"'`"
STRING_PREFIX = re.compile(r"[rRbBuUfF]{1,2}")
NON_VALUES = {"none", "null", "nil", "true", "false", "undefined"}
TEMPLATE = re.compile(
    r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Z_][A-Z0-9_]*|\{\{[ \t]*[A-Za-z_][A-Za-z0-9_.]*[ \t]*\}\}|"
    r"\{[A-Za-z_][A-Za-z0-9_.]*\}|<[A-Za-z][A-Za-z0-9_\- ]*>|%\([A-Za-z_][A-Za-z0-9_]*\)[sd]|%[A-Z_][A-Z0-9_]*%")

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


def _close_quote(text: str, start: int) -> int:
    """Index of the quote closing the one at ``start`` (a backslash escapes it), or -1."""
    q, i = text[start], start + 1
    while i < len(text):
        if text[i] == "\\" and q != "'":
            i += 2
            continue
        if text[i] == q:
            return i
        i += 1
    return -1


def _value(text: str, pos: int, glue: bool = False) -> str | None:
    """Read the value that starts at ``pos`` with its quotes removed, or None when there is none.

    Without ``glue`` a quote after an unquoted part ends the value; with it, the quoted part is read on
    as part of the value. See the comment above ASSIGNMENT.
    """
    scheme = SCHEME.match(text, pos)
    if scheme:
        pos = scheme.end()
    segments: list[tuple[str, str, bool]] = []  # (content, raw, quoted)
    depth, i, n, open_ended = 0, pos, len(text), False
    while i < n:
        ch = text[i]
        if ch.isspace() and depth == 0:
            break
        if ch in QUOTES:
            prefix = len(segments) == 1 and STRING_PREFIX.fullmatch(segments[0][0]) is not None
            if segments and depth == 0 and not prefix and not glue:
                break
            if segments and depth == 0 and not prefix:
                glue = False  # only the first quoted part after an unquoted one is glued on  # a quote after a value ends it (in a JSON row it closes the string holding the text)
            if open_ended:
                break
            end = _close_quote(text, i)
            if end < 0:
                if segments:
                    break
                open_ended = True  # a quote that never closes: read the rest like an unquoted value
                i += 1
                continue
            segments.append((text[i + 1:end], text[i:end + 1], True))
            i = end + 1
            continue
        if segments and segments[-1][2] and depth == 0 and ch in ",;.:)]}":
            break  # syntax after a closing quote ("abc", or "abc"}), not a glued tail ("abc"def)
        start = i
        while i < n and text[i] not in QUOTES and not (text[i].isspace() and depth == 0):
            if text[i] in "([{":
                depth += 1
            elif text[i] in ")]}":
                depth = max(0, depth - 1)
            i += 1
        segments.append((text[start:i], text[start:i], False))
    if not segments:
        return None
    if not segments[-1][2]:
        # one trailing , ; . : ends a statement or a sentence; closers with no opener close the caller
        tail = segments[-1][0]
        if tail[-1:] in (",", ";", ".", ":"):
            tail = tail[:-1]
        bare = "".join(s[0] for s in segments[:-1] if not s[2]) + tail
        for opener, closer in ("()", "[]", "{}"):
            while tail.endswith(closer) and bare.count(closer) > bare.count(opener):
                tail, bare = tail[:-1], bare[:-1]
        segments[-1] = (tail, tail, False)
    if len(segments) > 1 and segments[1][2] and STRING_PREFIX.fullmatch(segments[0][0]):
        segments = segments[1:]
    value = "".join(s[0] for s in segments)
    scheme = SCHEME.match(value)
    if scheme:
        value = value[scheme.end():]
    return value


def _key_words(key: str) -> list[str]:
    """``key`` split at _ - . (and any other non-word character) and at camelCase humps, lower-cased."""
    return [word.lower() for part in re.split(r"[\W_]+", key) if part for word in CAMEL.split(part) if word]


def _secret_key(key: str) -> bool:
    """True when ``key`` is secret-named (see the comment at NAME_PARTS)."""
    if "." in key and key.rsplit(".", 1)[1].lower() in FILE_EXTENSIONS:
        return False
    words = _key_words(key)
    for index, word in enumerate(words):
        if word in PLAIN_WORDS:
            continue
        if any(part in word for part in NAME_PARTS) or word in NAME_WORDS:
            return True
        if (word.endswith("key") or word.endswith("keys")) and (len(words) > 1 or word not in ("key", "keys")):
            return True
        if word == "session" and words[index + 1:index + 2] == ["id"]:
            return True
    return False


def _assignment_ends(line: str, dangling: bool = False) -> list[int]:
    """Where a value assigned to a secret-named key starts in ``line``: just after each operator.

    With ``dangling``, a key whose operator is a bare colon counts only when it starts the line (after
    blanks, a diff marker, a YAML list dash and an opening quote): a YAML key that ends its line takes
    its value from the next line, a Python if-line that ends in a colon does not."""
    ends = []
    for pattern in (ASSIGNMENT, FLAG, ENV_FORM):
        for m in pattern.finditer(line):
            if not _secret_key(m.group("key")):
                continue
            if dangling and pattern is ASSIGNMENT and line[m.end("key"):].strip(" \t\"'`]") == ":" \
                    and line[:m.start("key")].strip(" \t+-\"'`") != "":
                continue
            ends.append(m.end())
    return ends


def _url_placeholder(password: str) -> bool:
    """A URL password of any length is reported unless it is nothing but templates (a password spelled
    ${DB_PASSWORD}); a placeholder word such as password is reported like any other."""
    return not TEMPLATE.sub("", password)


def _assigned(text: str, pos: int) -> str | None:
    """The secret value assigned at ``pos`` (just after the operator), or None when there is none: the
    first of the two readings of ``_value`` that is 8 or more characters, not a whole template and not
    one of NON_VALUES."""
    for glue in (False, True):
        value = _value(text, pos, glue)
        if value is None or len(value) < 8 or value.lower() in NON_VALUES or not TEMPLATE.sub("", value):
            continue
        return value
    return None


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
                if name == "url-credentials" and _url_placeholder(m.group(1)):
                    continue
                hits.append((name, m.group(0)))
        for end in _assignment_ends(variant) if assignments else ():
            value = _assigned(variant, end)
            if value is not None:
                hits.append(("secret-assignment", value))
        for label, value in known if tokens else ():
            if value in variant:
                hits.append((label, value))
    return hits


def _dangling_hits(head: str, tail: str) -> list[tuple[str, str]]:
    """A key and operator that end ``head`` (YAML "token:" with the value below) take their value
    from the start of ``tail``."""
    hits: list[tuple[str, str]] = []
    for variant in _variants(head):
        if len(variant) not in _assignment_ends(variant, dangling=True):
            continue
        for following in _variants(tail):
            value = _assigned(following, 0)
            if value is not None and ("secret-assignment", value) not in hits:
                hits.append(("secret-assignment", value))
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
            # between the halves; a key that ends a line takes its value from the next one
            following = lines[index + 1]
            if kind == "diff" and following[:1] in ("+", "-", " "):
                following = following[1:]
            alone = set(hits[index]) | set(hits[index + 1])
            head, tail = line.rstrip(), following.lstrip()
            # a trailing backslash continues a string or a shell line: the halves join without it
            pieces = _variants(line) + _variants(following)
            found += [hit for hit in _line_hits(head.removesuffix("\\") + tail, known_values, assignments=False)
                      if hit not in alone and not any(hit[1] in piece for piece in pieces)]
            found += [hit for hit in _dangling_hits(head, tail) if hit not in alone]
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
