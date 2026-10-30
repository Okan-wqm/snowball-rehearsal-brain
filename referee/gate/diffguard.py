r"""``gate.diffguard``: a candidate diff changes only plain files, inside the unit's ``inputs``, and none of
the paths the gate never lets an agent change (stage 0, MF7).

Rules: asama-0/08 criterion 1, asama-0/09 test 23, tohum/01b (the refusal list), tohum/04a item 9,
tohum/14 (agent configuration and the operator's excluded paths), tohum/29f (agent configuration and
coverage, the shared rules of ``profile.derive``, MF4) and tohum/29g (group ``diffguard``).

``check`` returns every reason of every changed path, ``<reason>:<path>``, sorted by code point and
unique; the path is the one the diff names, unquoted from git's C-style quoting and otherwise as written
(no normalisation). A block ``diff --git a/A b/B`` changes B; a deletion changes A, a rename A and B, a
copy B. The reasons, each checked on its own:

- ``symlink``: the block's ``new file mode``, ``new mode`` or ``index`` line carries mode 120000;
  ``submodule``: the same lines carry 160000. Recognised by git mode, never by content. The pre-image
  mode (``old mode``, ``deleted file mode``) is not judged: removing or replacing a link leaves no link.
- ``path_escape``: the path is absolute or has a ``..`` component.
- ``security_path``, ``excluded_path``: some ``security_paths`` / ``excluded_dirs`` entry of the profile
  covers the path (29f coverage: case-sensitive, as written).
- ``agent_config``: 29f agent configuration, case-insensitive.
- ``config``: the base name is in 29g's list or matches ``tsconfig.*.json``, or the path is under the root
  ``.github/``; ``manifest``: base name ``package.json``; ``lockfile``: ``package-lock.json``,
  ``npm-shrinkwrap.json``, ``yarn.lock``, ``pnpm-lock.yaml``; ``gitattributes``: base name
  ``.gitattributes``. Beyond 29g, measured on the target: ``config`` also takes a base name of a
  ``CONFIG_TOOLS`` tool in one of the ``MEASURED_CONFIG_SHAPES`` (``<tool>[.-<word>]*.config.<ext>``,
  ``<tool>.preset|workspace.<ext>``, ``.<tool>rc[.<ext>]``) or in ``MEASURED_CONFIG_NAMES`` (Nx targets,
  npm registry and Node version files, Rust toolchain and lint files); ``manifest`` also ``Cargo.toml``
  and ``pyproject.toml``; ``lockfile`` also ``Cargo.lock``, ``poetry.lock``, ``uv.lock``. Base names compare
  case-sensitively. Not recognised: a module that a configuration file imports, whatever its name
  (``eslint.project-overrides.mjs`` imported by ``eslint.config.mjs`` passes), test setup files
  (``jest.setup.ts``), build-only tools, and ecosystems this table does not list.
- ``outside_inputs``: no ``inputs`` entry of the recipe covers the path (29f coverage).

Not judged here, by 29g's interface: banned constructs, banned phrases and gross deletion (tohum/04a 9)
need the profile's ``banned_constructs`` and ``policy.json``, which this command does not take; documentation
paths by class (tohum/03) need the candidate's class.

The parser fails closed (``DiffError``, exit 2) on anything ``git apply`` could read as a change this
module did not see: no ``diff --git`` block; any line before the first block; a header line git does not
write (``EXTENDED``); a mode git does not write (``MODES``); paths that are not ``a/``/``b/``-prefixed,
that differ without ``rename``/``copy`` headers, or that disagree with the ``rename``/``copy``/``---``/
``+++`` lines; a hunk whose lines do not match its ``@@`` counts; a line after a side's ``\ No newline at
end of file``; hunks of a block out of order or overlapping, or a ``+`` start other than the one git
writes for its ``-`` start (``git apply`` places a hunk without context by its ``+`` start, so a diff whose
starts disagree is applied elsewhere than it reads); any line after a block's hunks other than another
hunk or the next block. A ``GIT binary patch`` body is read as base85 lines up to the next
block; ``Binary files ... differ`` carries no body.
"""

from __future__ import annotations

import fnmatch
import json
import posixpath
import re
import sys
from typing import Any

from profile import derive as D

# The name rules, one table per reason. ``SEED`` rows are tohum/29g's lists; ``MEASURED`` rows are names the
# target's own tree uses for the same things (missing_capability f111): tool configuration of the lint, type
# and test tools by shape, Nx targets, the npm registry and Node version files, and the Rust and Python
# manifests and locks. Everything here compares base names case-sensitively.
SEED_CONFIG_NAMES = (".eslintrc", ".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.yml",
                     ".eslintrc.yaml", "eslint.config.js", "eslint.config.mjs", "eslint.config.cjs",
                     "tsconfig.json", "jest.config.js", "jest.config.ts", "vitest.config.js",
                     "vitest.config.ts", ".prettierrc", ".prettierrc.json", "biome.json")
SEED_CONFIG_PATTERNS = ("tsconfig.*.json",)
# Lint, type and test tools whose configuration file is found by name. Build-only tools (webpack, rollup,
# postcss, tailwind) are not here: their files change the build, not the oracle.
CONFIG_TOOLS = ("eslint", "prettier", "biome", "jest", "vitest", "vite", "playwright", "cypress", "karma",
                "mocha", "babel", "swc", "stylelint")
CONFIG_EXTS = r"(?:js|cjs|mjs|ts|cts|mts|json|jsonc|json5|yml|yaml|toml)"
MEASURED_CONFIG_SHAPES = (
    # <tool>.config.<ext>, <tool>.<word>.config.<ext>, <tool>-<word>.config.<ext>: jest.e2e.config.ts
    re.compile(r"(?:%s)(?:[.-][A-Za-z0-9_-]+)*\.config\.%s" % ("|".join(CONFIG_TOOLS), CONFIG_EXTS)),
    # <tool>.preset.<ext>, <tool>.workspace.<ext>: jest.preset.js, vitest.workspace.ts
    re.compile(r"(?:%s)\.(?:preset|workspace)\.%s" % ("|".join(CONFIG_TOOLS), CONFIG_EXTS)),
    # .<tool>rc and .<tool>rc.<ext>: .mocharc.yml, .babelrc, .swcrc
    re.compile(r"\.(?:%s)rc(?:\.%s)?" % ("|".join(CONFIG_TOOLS), CONFIG_EXTS)),
)
MEASURED_CONFIG_NAMES = ("project.json", "nx.json", ".npmrc", ".nvmrc", ".node-version", "rust-toolchain",
                         "rust-toolchain.toml", "rustfmt.toml", ".rustfmt.toml", "clippy.toml", ".clippy.toml",
                         "deny.toml")
CONFIG_NAMES = frozenset(SEED_CONFIG_NAMES + MEASURED_CONFIG_NAMES)
CONFIG_PATTERNS = SEED_CONFIG_PATTERNS
CONFIG_ROOT_DIR = ".github/"
MANIFEST_NAMES = frozenset(("package.json",) + ("Cargo.toml", "pyproject.toml"))
LOCK_NAMES = frozenset(("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml")
                       + ("Cargo.lock", "poetry.lock", "uv.lock"))
GITATTRIBUTES_NAMES = frozenset((".gitattributes",))

SYMLINK, SUBMODULE = "120000", "160000"
MODES = frozenset(("100644", "100755", SYMLINK, SUBMODULE))
EXTENDED = ("old mode ", "new mode ", "deleted file mode ", "new file mode ", "copy from ", "copy to ",
            "rename from ", "rename to ", "similarity index ", "dissimilarity index ", "index ")
INDEX = re.compile(r"index [0-9a-f]+\.\.[0-9a-f]+(?: ([0-9]+))?")
SCORE = re.compile(r"[0-9]+%")
HUNK = re.compile(r"@@ -([0-9]+)(?:,([0-9]+))? \+([0-9]+)(?:,([0-9]+))? @@")
BASE85_LINE = re.compile(r"[A-Za-z][0-9A-Za-z!#$%&()*+\-;<=>?@^_`{|}~]+")
BINARY_SIZE = re.compile(r"(?:literal|delta) [0-9]+")
GIT_HEADER = "diff --git "
DEV_NULL = "/dev/null"
QUOTE_ESCAPES = {"a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "\\": 92}


class DiffError(ValueError):
    """Unusable input: no verdict (exit 2)."""


# ---------------------------------------------------------------- parsing

def _unquote(text: str, start: int) -> tuple[str, int]:
    """Decode git's C-quoted name starting at ``text[start] == '"'``; return it and the index after it."""
    out, i = bytearray(), start + 1
    while i < len(text):
        c = text[i]
        if c == '"':
            return out.decode("utf-8", "surrogateescape"), i + 1
        if c != "\\":
            out += c.encode("utf-8", "surrogateescape")
            i += 1
            continue
        nxt = text[i + 1:i + 2]
        if nxt in QUOTE_ESCAPES:
            out.append(QUOTE_ESCAPES[nxt])
            i += 2
        elif re.fullmatch(r"[0-3][0-7][0-7]", text[i + 1:i + 4]):
            out.append(int(text[i + 1:i + 4], 8))
            i += 4
        else:
            raise DiffError("bad escape in quoted name %r" % text)
    raise DiffError("unterminated quoted name %r" % text)


def _name(text: str) -> str:
    """A whole header value: one C-quoted name, or the text as written."""
    if text.startswith('"'):
        name, end = _unquote(text, 0)
        if end != len(text):
            raise DiffError("text after quoted name %r" % text)
        return name
    return text


def _header_names(rest: str) -> tuple[str, str] | None:
    """``a/A b/B`` of a ``diff --git`` line, prefixes kept; None when two unquoted names are not symmetric
    (then only ``rename``/``copy`` headers can name them)."""
    if rest.startswith('"'):
        a, end = _unquote(rest, 0)
        if rest[end:end + 1] != " ":
            raise DiffError("no space after quoted name in %r" % rest)
        return a, _name(rest[end + 1:])
    if rest.endswith('"'):
        cut = rest.rfind(' "')
        if cut > 0:
            return rest[:cut], _name(rest[cut + 1:])
    if (len(rest) - 1) % 2 == 0:
        half = (len(rest) - 1) // 2
        a, b = rest[:half], rest[half + 1:]
        if rest[half] == " " and a[2:] == b[2:]:
            return a, b
    return None


def _strip(prefixed: str, prefix: str) -> str:
    if not prefixed.startswith(prefix) or len(prefixed) == len(prefix):
        raise DiffError("name %r lacks the %r prefix" % (prefixed, prefix))
    return prefixed[len(prefix):]


def _side(line: str, mark: str) -> str:
    """The name on a ``---``/``+++`` line; git appends a tab when the name holds a space."""
    value = line[len(mark):]
    if value.endswith("\t") and " " in value:
        value = value[:-1]
    return _name(value)


def _check_mode(mode: str, line: str) -> str:
    if mode not in MODES:
        raise DiffError("mode git does not write in %r" % line)
    return mode


def _hunk(lines: list[str], i: int) -> tuple[dict, int]:
    """Consume the hunk whose ``@@`` header is ``lines[i]``; return it and the index after it.

    The hunk is ``{old_start, old_count, new_start, new_count, lines}``; each line is ``[tag, text, eol]``
    with tag `` ``, ``-`` or ``+`` (an empty line counts as context) and ``eol`` false when git's ``\\ No
    newline at end of file`` marker follows it."""
    m = HUNK.match(lines[i])
    if not m:
        raise DiffError("bad hunk header %r" % lines[i])
    old = 1 if m.group(2) is None else int(m.group(2))
    new = 1 if m.group(4) is None else int(m.group(4))
    hunk = {"old_start": int(m.group(1)), "old_count": old, "new_start": int(m.group(3)), "new_count": new,
            "lines": []}
    body = hunk["lines"]
    closed = {"-": False, "+": False}  # a side whose last line had no newline takes no further line
    i += 1
    while old > 0 or new > 0 or (i < len(lines) and lines[i].startswith("\\")):
        if i >= len(lines):
            raise DiffError("hunk ends before its counts")
        line = lines[i]
        tag = line[:1]
        if tag in (" ", ""):
            old, new = old - 1, new - 1
        elif tag == "-":
            old -= 1
        elif tag == "+":
            new -= 1
        elif tag == "\\":
            if not body or not body[-1][2]:
                raise DiffError("misplaced %r" % line)
            body[-1][2] = False
            i += 1
            continue
        else:
            raise DiffError("line %r inside a hunk" % line)
        if old < 0 or new < 0:
            raise DiffError("hunk longer than its counts")
        sides = ("-", "+") if tag in (" ", "") else (tag,)
        if any(closed[s] for s in sides):
            raise DiffError("line %r after the end of file" % line)
        if body and not body[-1][2]:
            for s in (("-", "+") if body[-1][0] == " " else (body[-1][0],)):
                closed[s] = True
        body.append([tag or " ", line[1:], True])
        i += 1
    return hunk, i


def _check_positions(hunks: list[dict], header: str) -> None:
    """The hunks of one block are in order, do not overlap, and each ``+`` start is the one git writes for
    its ``-`` start and the line count change of the hunks before it (a start of the empty side names the
    line before it). The mapped line (``gate.check``) reads these starts, so a diff that lies about them is
    unusable, not mapped."""
    delta, end = 0, 0
    for h in hunks:
        os_, oc, ns, nc = h["old_start"], h["old_count"], h["new_start"], h["new_count"]
        if oc == 0 and nc == 0:
            raise DiffError("empty hunk in %r" % header)
        first = os_ if oc else os_ + 1  # first old line the hunk touches or the one it inserts before
        if first <= end or (oc and os_ < 1):
            raise DiffError("hunks out of order or overlapping in %r" % header)
        expect = os_ + delta + (1 if oc == 0 else 0) - (1 if nc == 0 else 0)
        if ns != expect:
            raise DiffError("hunk '+%d' should be '+%d' in %r" % (ns, expect, header))
        delta += nc - oc
        end = os_ + oc - 1 if oc else os_


def parse(text: str) -> list[dict]:
    """The blocks of a git diff, each ``{changed, modes, kind, old, new, hunks, binary, headers}``:
    ``changed`` the paths the block changes, ``modes`` its post-image modes, ``kind`` one of ``modify``,
    ``create``, ``delete``, ``rename``, ``copy``, ``old``/``new`` the pre-/post-image path (None when
    created/deleted), ``hunks`` as ``_hunk`` returns them, ``binary`` true for a binary patch, ``headers``
    the extended header names. See the module docstring for what makes a diff unusable."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or not lines[0].startswith(GIT_HEADER):
        raise DiffError("the diff does not start with a 'diff --git' block")
    blocks, i = [], 0
    while i < len(lines):
        header = lines[i]
        if not header.startswith(GIT_HEADER):
            raise DiffError("line %r outside any block" % header)
        names = _header_names(header[len(GIT_HEADER):])
        i += 1
        ext: dict[str, str] = {}
        modes: list[str] = []
        while i < len(lines) and lines[i].startswith(EXTENDED):
            line = lines[i]
            key = next(k for k in EXTENDED if line.startswith(k))
            value = line[len(key):]
            if key in ext:
                raise DiffError("repeated header %r" % line)
            ext[key] = value
            if key == "index ":
                m = INDEX.fullmatch(line)
                if not m:
                    raise DiffError("bad index line %r" % line)
                if m.group(1) is not None:
                    modes.append(_check_mode(m.group(1), line))
            elif key.endswith("mode "):
                mode = _check_mode(value, line)
                if key in ("new mode ", "new file mode "):
                    modes.append(mode)
            elif key.endswith("index "):
                if not SCORE.fullmatch(value):
                    raise DiffError("bad score %r" % line)
            i += 1
        rename = "rename from " in ext or "rename to " in ext
        copy = "copy from " in ext or "copy to " in ext
        if rename and copy:
            raise DiffError("rename and copy in one block")
        if rename or copy:
            src, dst = ("rename from ", "rename to ") if rename else ("copy from ", "copy to ")
            if src not in ext or dst not in ext:
                raise DiffError("incomplete %s headers" % ("rename" if rename else "copy"))
            a, b = _name(ext[src]), _name(ext[dst])
            if not a or not b:
                raise DiffError("empty name in %r" % header)
            if (names or (None, None)) != ("a/" + a, "b/" + b) and header != "%sa/%s b/%s" % (GIT_HEADER, a, b):
                raise DiffError("%r disagrees with its rename/copy headers" % header)
        else:
            if names is None:
                raise DiffError("cannot split names in %r" % header)
            a, b = _strip(names[0], "a/"), _strip(names[1], "b/")
            if a != b:
                raise DiffError("names differ without rename/copy in %r" % header)
        deleted, created = "deleted file mode " in ext, "new file mode " in ext
        hunks: list[dict] = []
        binary = False
        if deleted and (created or rename or copy or "new mode " in ext):
            raise DiffError("a deletion with other changes in %r" % header)
        if i < len(lines) and lines[i].startswith("--- "):
            if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
                raise DiffError("'---' without '+++' in %r" % header)
            old, new = _side(lines[i], "--- "), _side(lines[i + 1], "+++ ")
            if old != (DEV_NULL if created else "a/" + a) or new != (DEV_NULL if deleted else "b/" + b):
                raise DiffError("'---'/'+++' names disagree with %r" % header)
            i += 2
            if i >= len(lines) or not lines[i].startswith("@@"):
                raise DiffError("no hunk after '+++' in %r" % header)
            while i < len(lines) and lines[i].startswith("@@"):
                hunk, i = _hunk(lines, i)
                hunks.append(hunk)
            _check_positions(hunks, header)
        elif i < len(lines) and lines[i] == "GIT binary patch":
            binary = True
            i += 1
            while i < len(lines) and not lines[i].startswith(GIT_HEADER):
                if not (lines[i] == "" or BINARY_SIZE.fullmatch(lines[i]) or BASE85_LINE.fullmatch(lines[i])):
                    raise DiffError("bad binary patch line %r" % lines[i])
                i += 1
        elif i < len(lines) and lines[i].startswith("Binary files ") and lines[i].endswith(" differ"):
            binary = True
            i += 1
        changed = [a] if deleted else [a, b] if rename else [b]
        kind = ("delete" if deleted else "create" if created else "rename" if rename else "copy" if copy
                else "modify")
        blocks.append({"changed": changed, "modes": modes, "kind": kind, "old": None if created else a,
                       "new": None if deleted else b, "hunks": hunks, "binary": binary,
                       "headers": sorted(k.strip() for k in ext)})
    return blocks


# ---------------------------------------------------------------- rules

def path_reasons(path: str, modes: list[str], profile: dict, recipe: dict) -> list[str]:
    """Every reason of one changed path, as ``<reason>:<path>``."""
    base = posixpath.basename(path)
    found = []
    if SYMLINK in modes:
        found.append("symlink")
    if SUBMODULE in modes:
        found.append("submodule")
    if path.startswith("/") or ".." in path.split("/"):
        found.append("path_escape")
    if any(D.covers_as_written(e, path) for e in profile["security_paths"]):
        found.append("security_path")
    if any(D.covers_as_written(e, path) for e in profile["excluded_dirs"]):
        found.append("excluded_path")
    if D.agent_config_as_written(path):
        found.append("agent_config")
    if (base in CONFIG_NAMES or any(fnmatch.fnmatchcase(base, p) for p in CONFIG_PATTERNS)
            or any(r.fullmatch(base) for r in MEASURED_CONFIG_SHAPES) or path.startswith(CONFIG_ROOT_DIR)):
        found.append("config")
    if base in MANIFEST_NAMES:
        found.append("manifest")
    if base in LOCK_NAMES:
        found.append("lockfile")
    if base in GITATTRIBUTES_NAMES:
        found.append("gitattributes")
    if not any(D.covers_as_written(e, path) for e in recipe["inputs"]):
        found.append("outside_inputs")
    return ["%s:%s" % (r, path) for r in found]


def _strings(obj: Any, key: str, what: str) -> list[str]:
    value = obj.get(key) if isinstance(obj, dict) else None
    if not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
        raise DiffError("%s.%s must be a list of strings" % (what, key))
    return value


def check(diff_text: str, profile: Any, recipe: Any) -> list[str]:
    """Group ``diffguard``'s check (tohum/29g): the sorted, unique reasons; empty when the diff passes.

    Raises ``DiffError`` when the diff is unusable or ``profile.security_paths``, ``profile.excluded_dirs``
    or ``recipe.inputs`` is not a list of strings."""
    prof = {k: _strings(profile, k, "profile") for k in ("security_paths", "excluded_dirs")}
    rec = {"inputs": _strings(recipe, "inputs", "recipe")}
    reasons = set()
    for block in parse(diff_text):
        for path in block["changed"]:
            reasons.update(path_reasons(path, block["modes"], prof, rec))
    return sorted(reasons)


# ---------------------------------------------------------------- command line

def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def _load(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


USAGE = "usage: python -m gate.diffguard check DIFF PROFILE RECIPE"


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 4 or argv[0] != "check":
            raise DiffError(USAGE)
        with open(argv[1], "rb") as fh:
            text = fh.read().decode("utf-8", "surrogateescape")
        reasons = check(text, _load(argv[2]), _load(argv[3]))
        _emit({"ok": not reasons, "reasons": reasons})
        return 0 if not reasons else 1
    except (DiffError, ValueError, OSError, RecursionError) as exc:
        _emit({"ok": False, "error": "unusable input: %s" % exc})
        return 2
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a reason
        _emit({"ok": False, "error": "internal error: %s: %s" % (type(exc).__name__, exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
