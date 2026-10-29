"""Static profile derivation and the check of a proposal against it (stage 0, MF4).

Rules: tohum/14 (the referee derives the profile itself; a proposal that differs from the derivation is
refused; security paths by keyword and ownership file; excluded directories; agent configuration excluded
everywhere and case-insensitively; the operator's ``excluded_paths``, which a proposal may only widen),
tohum/26a (``profile.derive``: target tree and ``targets[]`` in; profile, unit candidates, excluded paths
out; no side effect), tohum/26b and 26c (field names, the unit recipe), asama-0/08 (unit selection
criteria), asama-0/09 tests 19 and 47, tohum/29d (group ``profile``).

What ``derive`` returns, and the exact rule for each field (all paths are relative to the tree root,
``/``-separated; names are compared after ``str.casefold``):

- Walk. Every entry below the root is visited in name order without following symlinks; a directory
  the walk cannot list stops the derivation (``DeriveError``), it is never skipped. An entry is not
  descended into, and adds nothing to the fields below the excluded ones, when it is excluded: its name
  is one of ``AGENT_CONFIG`` or ``EXCLUDED_DIR_NAMES``, or it matches an operator pattern.
- ``agent_config``: the seven names of tohum/14 (``.claude``, ``CLAUDE.md``, ``AGENTS.md``,
  ``.mcp.json``, ``.vscode``, ``.envrc``, ``.devcontainer``). A path is agent configuration when any of
  its components equals one of them after casefold, at any depth, file or directory. In the tree, a
  symlink whose target text has such a component (``/`` or ``\\`` separated) is agent configuration too;
  the target is not resolved further. Names are compared as stored: a name that differs by a trailing
  space or dot, a Windows short name or a stream suffix is not one of the seven.
- ``excluded_paths``: the operator's ``targets[].excluded_paths`` as written, plus every topmost agent
  configuration path found in the tree (topmost after casefold: ``.claude`` is covered by ``.Claude``).
  An operator entry is a pattern in the ownership-file syntax below, matched case-insensitively.
- ``excluded_dir_names`` and ``excluded_dirs``: a closed list of dependency, cache, build-output and
  other agents' workspace names (``EXCLUDED_DIR_NAMES``); an entry with such a name is excluded, and
  ``excluded_dirs`` lists the topmost ones found. ``.git`` is skipped and not listed. Other names are
  not excluded here; the operator's ``excluded_paths`` is the channel for them.
- ``languages``: ``{name: {files: n}}`` over regular files that are not excluded, by file extension
  (``EXTENSIONS``, casefolded). A file with another extension, or none, counts for no language.
- ``security_paths``: topmost paths (file or directory, symlinks included, excluded ones not) one of
  whose components contains a security keyword as a substring after casefold, plus the regular files
  and their directories matched by an ownership-file line that names an owner (any of them) containing a
  keyword (``CODEOWNERS``, ``.github/CODEOWNERS``, ``docs/CODEOWNERS``, ``.gitlab/CODEOWNERS``, each read
  only when it is a regular file with no symlink on its way). Those lines' patterns are also kept as written in
  ``security_owner_patterns`` so that paths added later are covered. Keywords are the policy's
  ``security_keywords`` when given, otherwise the fourteen of tohum/14. A substring rule over-includes
  (``author`` holds ``auth``); that is its cost, a narrower rule would let a security path through.
  File contents are not read for keywords.
- ``test_path_rules``: the rules of ``TEST_RULES`` that match at least one non-excluded regular file,
  plus, as literal paths, every non-excluded ``.rs`` file with a ``#[test]`` attribute or a ``#[cfg(...)]``
  that names ``test`` (``INLINE_RUST_TEST``; inline tests). A test file outside these rules (say
  ``FooTest.java``, a Python doctest) is not recognised.
- ``unit_candidates``: the operator's ``unit_candidates`` in their order; when there are none, every
  non-excluded directory that holds a ``package.json``, in path order. Each is ``{path, eligible,
  reasons}``; eligible means none of: ``path_invalid`` (absolute, ``..``, empty), ``path_symlink``,
  ``not_a_directory``, ``excluded``, ``no_package_json``, ``package_json_unparsable``,
  ``no_version_file`` (no non-blank regular ``.nvmrc`` or ``.node-version``, nor a ``.tool-versions``
  with a ``node``/``nodejs`` line, in the unit directory or an ancestor up to the root), ``no_lockfile``
  (no ``npm-shrinkwrap.json`` or ``package-lock.json`` there; the nearest wins, shrinkwrap first),
  ``lock_not_regular`` (it is a symlink or not a file), ``lock_unparsable``, ``lock_v1_unsupported`` (no
  ``packages`` object),
  ``lock_without_integrity`` (an entry under ``node_modules/`` that is neither a link nor bundled has no
  ``integrity`` string; its value is judged by MF5). These are the static parts of asama-0/08 criteria 1 and 3; "small, well tested",
  the service-free tests, the lint tool, the fixable violation and 3/3 green are not judged here (MF6).

Pattern syntax (operator ``excluded_paths`` and ownership-file lines, GitHub's): a leading ``/`` or a
``/`` inside anchors the pattern at the root, otherwise it matches at any depth; ``*`` and ``?`` do not
cross ``/``, ``**`` does, ``[...]`` is a class; a trailing ``/`` is dropped, so the pattern also matches a
file of that name (wider, never narrower); a match on a directory covers everything below it. Out of
scope: ``!`` negation, escaped spaces, GitLab sections (a line starting with ``[`` or ``^[`` is skipped).

``check(derived, proposal)`` refuses (``ok`` false, every reason listed):

- a field ``derive`` does not produce (``field_not_derived:<name>``), so nothing unjudged gets through;
- ``agent_config``, ``security_keywords``, ``security_owner_patterns``, ``excluded_dir_names``,
  ``test_path_rules`` or the language names that are not equal to the derivation as casefolded sets, or
  ``security_paths`` and ``excluded_dirs`` that, reduced to their topmost paths, are not equal to it
  (``differs:<field>``): narrowing and widening are both refused;
- ``excluded_paths`` that leave out a derived entry (``narrowed:excluded_paths:<entry>``): the brain may
  only widen this list (tohum/14). An entry is kept only by the same pattern (casefolded, trailing ``/``
  dropped) or, when the entry is a glob-free anchored path, by a glob-free pattern that matches it; so
  ``/vendor`` does not keep ``vendor`` (any depth) and ``/legacy/*`` does not keep ``/legacy/*.js``;
- a unit recipe (``units``) whose ``path`` is not an eligible candidate, with a field outside the recipe
  of tohum/26c, with an input that is invalid or excluded, or (given the tree) missing or reached through
  a symlink, or with no input that covers its ``path``. An input that holds an excluded path below it is
  accepted: the exclusion still applies to that path; symlinks below an input are not judged here.

A field the proposal does not carry is not proposed, so it is not compared; only the derivation enters
the profile (tohum/14). Out of scope here: every other ``profile.json`` field (toolchains, commands,
graph, banned constructs, ...) and the recipe's own values (image, commands, limits: MF6).

Command line, run from ``referee/`` (one JSON line on stdout; exit 0 fine, 1 refused, 2 no verdict).
Exit 1 comes only from a ``check`` report with ``ok`` false. Every other failure is exit 2 with an
``error`` line and no profile: unusable input (a target or policy file that is missing, not JSON, nested
too deeply for the parser, or of the wrong shape; an operator or ownership-file pattern that does not
compile, such as ``[z-a]``; a tree entry that cannot be listed or stat'ed), and, as a last resort, any
other exception, reported as ``internal error: <type>``. An ownership-file pattern in the target tree
that does not compile stops the derivation rather than being skipped, since skipping it could drop a
security path. A ``package.json`` or lock file nested too deeply to parse counts as unparsable.
Out of scope: signals (``KeyboardInterrupt``) and the interpreter being killed.

    python -m profile.derive derive TREE [--target FILE] [--policy FILE]
    python -m profile.derive check TREE PROPOSAL [--target FILE] [--policy FILE]

``--target`` is one ``targets[]`` entry (``excluded_paths``, ``unit_candidates``); ``--policy`` a
``policy.json`` whose ``constitutional.security_keywords`` replaces the default keywords.
"""

from __future__ import annotations

import functools
import json
import os
import posixpath
import re
import stat
import sys
from typing import Any

AGENT_CONFIG = (".claude", "CLAUDE.md", "AGENTS.md", ".mcp.json", ".vscode", ".envrc", ".devcontainer")
EXCLUDED_DIR_NAMES = (
    "node_modules", "bower_components", "jspm_packages", "dist", "coverage", ".nyc_output", ".next", ".nuxt",
    ".turbo", ".parcel-cache", ".cache", "__pycache__", ".venv", ".tox", ".mypy_cache", ".pytest_cache",
    ".cursor", ".codex", ".gemini", ".windsurf", ".continue", ".roo", ".aider.tags.cache.v3",
)
SECURITY_KEYWORDS = ("auth", "guard", "security", "session", "token", "secret", "crypto", "tenant",
                     "permission", "role", "policy", "payment", "billing", "pii")
EXTENSIONS = {
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "typescript",
    ".py": "python", ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin", ".rb": "ruby",
    ".php": "php", ".cs": "csharp", ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp",
    ".swift": "swift", ".scala": "scala", ".sh": "shell", ".sql": "sql",
}
TEST_RULES = ("**/test/**", "**/tests/**", "**/__tests__/**", "**/spec/**", "**/*.test.*", "**/*.spec.*",
              "**/test_*.py", "**/*_test.py", "**/*_test.go")
INLINE_RUST_TEST = re.compile(rb"#\s*\[\s*(?:test\s*\]|cfg\s*\([^\]]*\btest\b)")
OWNER_FILES = ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS", ".gitlab/CODEOWNERS")
RECIPE_FIELDS = ("unit_id", "path", "inputs", "toolchain", "env_image", "lockfiles", "install_scripts_required",
                 "lint_cmd", "test_cmd", "affected_test_cmd", "services", "limits")
SET_FIELDS = ("agent_config", "security_keywords", "security_paths", "security_owner_patterns",
              "excluded_dir_names", "excluded_dirs", "test_path_rules")
PROPOSABLE = SET_FIELDS + ("languages", "excluded_paths", "units")

_AGENT = frozenset(n.casefold() for n in AGENT_CONFIG)
_EXCL_DIR = frozenset(n.casefold() for n in EXCLUDED_DIR_NAMES)


class DeriveError(ValueError):
    """The tree or the target cannot be derived; no profile is returned."""


# ---------------------------------------------------------------- patterns and paths

@functools.lru_cache(maxsize=None)
def pattern_regex(pattern: str) -> re.Pattern:
    """Compile an ownership-file / excluded-path pattern; it matches a path or anything below one."""
    p = pattern.casefold()
    anchored = p.startswith("/")
    p = p.strip("/")
    if not p:
        raise DeriveError("empty pattern %r" % pattern)
    anchored = anchored or "/" in p
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "[" and "]" in p[i + 2:]:
            end = p.index("]", i + 2)
            body = p[i + 1:end]
            if body.startswith("!"):
                body = "^" + body[1:]
            out.append("[" + body.replace("\\", "\\\\").replace("/", "") + "]")
            i = end + 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    try:
        return re.compile(("" if anchored else "(?:.*/)?") + "".join(out) + "(?:/.*)?\\Z", re.DOTALL)
    except re.error as exc:
        raise DeriveError("invalid pattern %r: %s" % (pattern, exc)) from None


def pattern_matches(pattern: str, path: str) -> bool:
    return pattern_regex(pattern).match(path.casefold()) is not None


def norm_path(path: Any) -> str | None:
    """A relative ``/`` path inside the tree, normalised; None when absolute, empty, or leaving the tree."""
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return None
    norm = posixpath.normpath(path)
    if norm == ".." or norm.startswith("../"):
        return None
    return norm


def covers(entry: str, path: str) -> bool:
    entry, path = entry.casefold(), path.casefold()
    return entry == "." or path == entry or path.startswith(entry + "/")


def minimal(paths) -> list[str]:
    """Drop every path that an other path of the list covers."""
    out: list[str] = []
    for p in sorted(set(paths), key=lambda s: (s.casefold().count("/"), s)):
        if not any(covers(q, p) for q in out):
            out.append(p)
    return sorted(out)


def is_agent_config(path: str) -> bool:
    return any(part.casefold() in _AGENT for part in path.split("/"))


def excluded(derived: dict, path: str) -> str | None:
    """Why ``path`` is excluded under ``derived`` (agent_config, excluded_dir, excluded_path), or None."""
    parts = [part.casefold() for part in path.split("/")]
    if any(part in _AGENT for part in parts):
        return "agent_config"
    if any(part in _EXCL_DIR for part in parts):
        return "excluded_dir"
    if any(pattern_matches(p, path) for p in derived.get("excluded_paths", [])):
        return "excluded_path"
    return None


# ---------------------------------------------------------------- derive

def _keywords(policy: dict | None) -> list[str]:
    if policy is None:
        return list(SECURITY_KEYWORDS)
    constitutional = policy.get("constitutional") if isinstance(policy, dict) else None
    words = constitutional.get("security_keywords") if isinstance(constitutional, dict) else None
    if not (isinstance(words, list) and words and all(isinstance(w, str) and w for w in words)):
        raise DeriveError("policy.constitutional.security_keywords is not a list of words")
    return [w.casefold() for w in words]


def _target(target: dict | None) -> tuple[list[str], list[str]]:
    if target is None:
        return [], []
    if not isinstance(target, dict):
        raise DeriveError("target must be an object")
    lists = []
    for key in ("excluded_paths", "unit_candidates"):
        value = target.get(key, [])
        if not (isinstance(value, list) and all(isinstance(v, str) and v.strip("/") for v in value)):
            raise DeriveError("target.%s must be a list of non-empty strings" % key)
        lists.append(value)
    for p in lists[0]:
        pattern_regex(p)
    return lists[0], lists[1]


def _walk(root: str):
    """Yield (relative path, lstat) for every entry, depth first in name order; never follows symlinks.

    The caller sends False into the generator to keep it out of a directory it has just been given.
    The walk keeps its own stack, so tree depth is bounded by the file system, not by Python recursion.
    """
    def listing(rel: str):
        full = os.path.join(root, rel) if rel else root
        try:
            names = sorted(os.listdir(full))
        except OSError as exc:
            raise DeriveError("cannot list %s: %s" % (rel or ".", exc.strerror)) from None
        return iter([posixpath.join(rel, n) if rel else n for n in names if n != ".git"])

    stack = [listing("")]
    while stack:
        child = next(stack[-1], None)
        if child is None:
            stack.pop()
            continue
        try:
            st = os.lstat(os.path.join(root, child))
        except OSError as exc:
            raise DeriveError("cannot stat %s: %s" % (child, exc.strerror)) from None
        descend = yield child, st
        if descend is not False and stat.S_ISDIR(st.st_mode):
            stack.append(listing(child))


def derive(tree: str, target: dict | None = None, policy: dict | None = None) -> dict:
    if not os.path.isdir(tree) or os.path.islink(tree):
        raise DeriveError("tree is not a directory")
    op_excluded, op_candidates = _target(target)
    keywords = _keywords(policy)
    agent_found, excl_dirs, security, files, package_dirs = [], [], [], [], []
    languages: dict[str, int] = {}

    walker = _walk(tree)
    send = None
    while True:
        try:
            rel, st = walker.send(send)
        except StopIteration:
            break
        name = rel.rsplit("/", 1)[-1].casefold()
        send = None
        if name in _AGENT or (stat.S_ISLNK(st.st_mode) and _link_to_agent_config(tree, rel)):
            agent_found.append(rel)
            send = False
            continue
        if name in _EXCL_DIR:
            excl_dirs.append(rel)
            send = False
            continue
        if any(pattern_matches(p, rel) for p in op_excluded):
            send = False
            continue
        if any(k in name for k in keywords):
            security.append(rel)
        if stat.S_ISREG(st.st_mode):
            files.append(rel)
            lang = EXTENSIONS.get(posixpath.splitext(name)[1])
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            if name == "package.json":
                package_dirs.append(posixpath.dirname(rel) or ".")

    owner_patterns = _owner_patterns(tree, keywords)
    all_paths = _all_paths(files)
    for pattern in owner_patterns:
        rx = pattern_regex(pattern)
        security.extend(p for p in all_paths if rx.match(p.casefold()))

    derived = {
        "agent_config": list(AGENT_CONFIG),
        "excluded_dir_names": list(EXCLUDED_DIR_NAMES),
        "excluded_dirs": minimal(excl_dirs),
        "excluded_paths": sorted(set(op_excluded) | set(minimal(agent_found))),
        "languages": {k: {"files": v} for k, v in sorted(languages.items())},
        "security_keywords": keywords,
        "security_owner_patterns": owner_patterns,
        "security_paths": minimal(security),
        "test_path_rules": _test_rules(tree, files),
    }
    candidates = op_candidates or sorted(package_dirs)
    derived["unit_candidates"] = [_candidate(tree, derived, c) for c in candidates]
    return derived


def _link_to_agent_config(tree: str, rel: str) -> bool:
    """A symlink whose target text names agent configuration in any component (not resolved further)."""
    try:
        target = os.readlink(os.path.join(tree, rel))
    except OSError:
        return False
    return any(part.casefold() in _AGENT for part in re.split(r"[/\\]", target))


def _all_paths(files: list[str]) -> list[str]:
    """The files and every directory above them."""
    out = set(files)
    for f in files:
        d = posixpath.dirname(f)
        while d:
            out.add(d)
            d = posixpath.dirname(d)
    return sorted(out)


def _owner_patterns(tree: str, keywords: list[str]) -> list[str]:
    patterns: list[str] = []
    for owner_file in OWNER_FILES:
        text = _read_regular(tree, owner_file)
        if text is None:
            continue
        for line in text.decode("utf-8", "replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith(("[", "^[")):
                continue
            pattern, *owners = line.split()
            if any(k in owner.casefold() for owner in owners for k in keywords):
                pattern_regex(pattern)
                patterns.append(pattern)
    return sorted(set(patterns))


def _test_rules(tree: str, files: list[str]) -> list[str]:
    rules = [r for r in TEST_RULES if any(pattern_matches(r, f) for f in files)]
    for f in files:
        if f.casefold().endswith(".rs"):
            data = _read_regular(tree, f)
            if data is not None and INLINE_RUST_TEST.search(data):
                rules.append(f)
    return sorted(rules)


def _read_regular(tree: str, rel: str) -> bytes | None:
    """The bytes of ``rel`` when it and every directory above it are real (no symlink); else None."""
    cur = tree
    for part in rel.split("/"):
        cur = os.path.join(cur, part)
        try:
            st = os.lstat(cur)
        except OSError:
            return None
        if stat.S_ISLNK(st.st_mode):
            return None
    if not stat.S_ISREG(st.st_mode):
        return None
    with open(cur, "rb") as fh:
        return fh.read()


def _real_dir(tree: str, rel: str) -> str | None:
    """'' when ``rel`` is a real directory, else the reason (path_symlink, not_a_directory)."""
    if rel == ".":
        return ""
    cur = tree
    for part in rel.split("/"):
        cur = os.path.join(cur, part)
        try:
            st = os.lstat(cur)
        except OSError:
            return "not_a_directory"
        if stat.S_ISLNK(st.st_mode):
            return "path_symlink"
    return "" if stat.S_ISDIR(st.st_mode) else "not_a_directory"


def _ancestors(rel: str) -> list[str]:
    out = [rel]
    while rel != ".":
        rel = posixpath.dirname(rel) or "."
        out.append(rel)
    return out


def _json(tree: str, rel: str) -> tuple[bool, Any]:
    data = _read_regular(tree, rel)
    if data is None:
        return False, None
    try:
        return True, json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return True, None


def _candidate(tree: str, derived: dict, raw: str) -> dict:
    path = norm_path(raw)
    if path is None:
        return {"path": raw, "eligible": False, "reasons": ["path_invalid"]}
    reasons = []
    where = _real_dir(tree, path)
    if where:
        reasons.append(where)
    if path != "." and excluded(derived, path):
        reasons.append("excluded")
    if not reasons:
        present, pkg = _json(tree, posixpath.join(path, "package.json"))
        if not present:
            reasons.append("no_package_json")
        elif not isinstance(pkg, dict):
            reasons.append("package_json_unparsable")
        if not any(_has_version_file(tree, d) for d in _ancestors(path)):
            reasons.append("no_version_file")
        reasons.extend(_lock_reasons(tree, path))
    return {"path": path, "eligible": not reasons, "reasons": reasons}


def _has_version_file(tree: str, d: str) -> bool:
    for name in (".nvmrc", ".node-version"):
        data = _read_regular(tree, posixpath.join(d, name))
        if data is not None and data.strip():
            return True
    data = _read_regular(tree, posixpath.join(d, ".tool-versions"))
    if data is None:
        return False
    return any(line.split()[:1] in (["node"], ["nodejs"]) and len(line.split()) > 1
               for line in data.decode("utf-8", "replace").splitlines())


def _lock_reasons(tree: str, path: str) -> list[str]:
    for d in _ancestors(path):
        for name in ("npm-shrinkwrap.json", "package-lock.json"):
            present, lock = _json(tree, posixpath.join(d, name))
            if not present:
                if os.path.lexists(os.path.join(tree, d, name)):
                    return ["lock_not_regular"]
                continue
            if not isinstance(lock, dict):
                return ["lock_unparsable"]
            packages = lock.get("packages")
            if not isinstance(packages, dict):
                return ["lock_v1_unsupported"]
            for key, entry in packages.items():
                if "node_modules/" not in key:
                    continue
                if not isinstance(entry, dict):
                    return ["lock_unparsable"]
                if entry.get("link") is True or entry.get("inBundle") is True:
                    continue
                integrity = entry.get("integrity")
                if not (isinstance(integrity, str) and integrity):
                    return ["lock_without_integrity"]
            return []
    return ["no_lockfile"]


# ---------------------------------------------------------------- check

def _str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def check(derived: dict, proposal: Any, tree: str | None = None) -> dict:
    """Judge a proposal (profile fields and/or ``units``) against ``derived``; see the module docstring.

    With ``tree`` (the tree ``derived`` came from), recipe inputs must also exist there with no symlink
    on their way; the command line always passes it.
    """
    if isinstance(proposal, list):
        proposal = {"units": proposal}
    if not isinstance(proposal, dict):
        return {"ok": False, "reasons": ["malformed:proposal"]}
    reasons: list[str] = []
    for field in sorted(proposal):
        if field not in PROPOSABLE:
            reasons.append("field_not_derived:%s" % field)
    for field in SET_FIELDS:
        if field not in proposal:
            continue
        value = proposal[field]
        if not _str_list(value):
            reasons.append("malformed:%s" % field)
            continue
        if field in ("security_paths", "excluded_dirs"):
            same = minimal(value) == derived[field]
        else:
            same = {v.casefold() for v in value} == {v.casefold() for v in derived[field]}
        if not same:
            reasons.append("differs:%s" % field)
    if "languages" in proposal:
        value = proposal["languages"]
        names = list(value) if isinstance(value, (dict, list)) else None
        if names is None or not all(isinstance(n, str) for n in names):
            reasons.append("malformed:languages")
        elif set(names) != set(derived["languages"]):
            reasons.append("differs:languages")
    if "excluded_paths" in proposal:
        value = proposal["excluded_paths"]
        if not _str_list(value):
            reasons.append("malformed:excluded_paths")
        else:
            for entry in derived["excluded_paths"]:
                if not any(_pattern_covers(v, entry) for v in value):
                    reasons.append("narrowed:excluded_paths:%s" % entry)
    if "units" in proposal:
        reasons.extend(_check_units(derived, proposal["units"], tree))
    return {"ok": not reasons, "reasons": reasons}


def _pattern_covers(wide: str, entry: str) -> bool:
    """True when pattern ``wide`` matches at least every path pattern ``entry`` matches.

    Exact for the same pattern (casefolded, trailing ``/`` dropped). Otherwise only for glob-free
    patterns where ``entry`` is anchored (it names one root path): ``wide`` then covers it when it
    matches that path. Any other pair is judged not covered, so the check refuses rather than guesses.
    """
    w, e = wide.rstrip("/").casefold(), entry.rstrip("/").casefold()
    if w == e:
        return True
    if any(c in w + e for c in "*?[") or not ("/" in e.lstrip("/") or e.startswith("/")):
        return False
    path = norm_path(e.lstrip("/"))
    return bool(w.strip("/")) and path is not None and pattern_regex(wide).match(path) is not None


def _input_where(tree: str, rel: str) -> str:
    """'' when ``rel`` exists in ``tree`` with no symlink on its way, else input_missing or input_symlink."""
    if rel == ".":
        return ""
    cur = tree
    for part in rel.split("/"):
        cur = os.path.join(cur, part)
        try:
            st = os.lstat(cur)
        except OSError:
            return "input_missing"
        if stat.S_ISLNK(st.st_mode):
            return "input_symlink"
    return ""


def _check_units(derived: dict, units: Any, tree: str | None) -> list[str]:
    if not isinstance(units, list) or not units:
        return ["malformed:units"]
    eligible = {c["path"]: c["eligible"] for c in derived["unit_candidates"]}
    reasons = []
    for i, unit in enumerate(units):
        if not isinstance(unit, dict):
            reasons.append("malformed:units[%d]" % i)
            continue
        for field in sorted(unit):
            if field not in RECIPE_FIELDS:
                reasons.append("units[%d]:field_not_in_recipe:%s" % (i, field))
        path = norm_path(unit.get("path"))
        if path is None:
            reasons.append("units[%d]:path_invalid" % i)
        elif path not in eligible:
            reasons.append("units[%d]:unit_not_candidate:%s" % (i, path))
        elif not eligible[path]:
            reasons.append("units[%d]:unit_not_eligible:%s" % (i, path))
        inputs = unit.get("inputs")
        if not (_str_list(inputs) and inputs):
            reasons.append("units[%d]:malformed:inputs" % i)
            continue
        normed = []
        for raw in inputs:
            p = norm_path(raw)
            if p is None:
                reasons.append("units[%d]:input_invalid:%s" % (i, raw))
            elif p != "." and excluded(derived, p):
                reasons.append("units[%d]:input_excluded:%s" % (i, p))
            elif tree is not None and _input_where(tree, p):
                reasons.append("units[%d]:%s:%s" % (i, _input_where(tree, p), p))
            else:
                normed.append(p)
        if path is not None and not any(covers(p, path) for p in normed):
            reasons.append("units[%d]:inputs_miss_unit_path" % i)
    return reasons


# ---------------------------------------------------------------- command line

def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def _load(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except RecursionError:
        raise DeriveError("%s: JSON nested too deeply" % path) from None


def main(argv: list[str]) -> int:
    try:
        args, opts = [], {}
        it = iter(argv)
        for a in it:
            if a in ("--target", "--policy"):
                path = next(it, None)
                if path is None:
                    raise DeriveError("%s needs a file" % a)
                opts[a] = _load(path)
            else:
                args.append(a)
        if len(args) == 2 and args[0] == "derive":
            _emit(derive(args[1], opts.get("--target"), opts.get("--policy")))
            return 0
        if len(args) == 3 and args[0] == "check":
            report = check(derive(args[1], opts.get("--target"), opts.get("--policy")), _load(args[2]), args[1])
            _emit(report)
            return 0 if report["ok"] else 1
        _emit({"error": "usage: python -m profile.derive derive TREE | check TREE PROPOSAL"
                        " [--target FILE] [--policy FILE]"})
        return 2
    except (DeriveError, ValueError, OSError) as exc:
        _emit({"error": "unusable input: %s" % exc})
        return 2
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a refusal
        _emit({"error": "internal error: %s: %s" % (type(exc).__name__, exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
