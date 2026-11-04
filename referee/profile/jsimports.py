"""``profile.jsimports``: one reader of a JS/TS tree's references, used by ``status.depmap`` (the target's drawing)
and ``profile.fit`` (the files a unit candidate reaches): the walk of a checkout, the import specifiers of a
JS/TS file, a tsconfig's ``extends``, the root tsconfig's path aliases and the package a bare specifier names.

- ``walk``: files and directories under a root, relative and ``/``-separated, sorted (the root is ``""``);
  ``SKIP_DIRS`` never entered, symbolic links not followed (a link is neither a file nor a directory here).
- ``specifiers``: the quoted string of ``import ... from``, ``export ... from``, a bare ``import '...'``,
  ``import('...')`` and ``require('...')``, read by ``SPECIFIER`` over the code (``code_view``): an import inside
  a comment, a string, a template or a regular expression is not one, nor is one whose specifier is not a string
  literal. ``code_view``'s lexing, stated: a ``'`` or ``"`` string ends at its closing quote or at the line's end
  (so an apostrophe in JSX text blanks the rest of its line only); a template ends at its closing backtick, its
  ``${...}`` included (an import inside one is not read); a ``/`` starts a regular expression after nothing, after
  one of ``REGEX_AFTER`` or after a word of ``REGEX_WORDS``, else it is division.
- ``extends``: a tsconfig's ``extends``, a string or a list of strings (TypeScript 5), read as ``jsonc_loads``
  reads tsconfig's dialect; ``[]`` when the text does not parse or holds none.
- ``jest_preset``: a jest configuration's (``JEST_CONFIG``) ``preset``, the first ``preset: '<value>'`` of its code
  (a quoted key too); none when the code names ``rootDir``. Not read: a preset built at run time or given by a
  variable, a configuration in ``package.json`` or in a JSON file.
- ``alias_file`` and ``aliases``: the ``compilerOptions.paths`` of the root ``tsconfig.base.json``, else
  ``tsconfig.json`` (only the root's: a ``paths`` of a nested tsconfig is not read), each alias with the first
  target of its list, ``baseUrl`` honoured (one leaving the root is the root), exact aliases before ``*`` ones;
  ``alias_path`` gives the first match's path (``*`` replaced by what it matched). ``aliases`` raises
  ``ValueError`` when the text does not parse.
- ``package_name``: the package a bare specifier names (``@s/n/x`` -> ``@s/n``, ``n/x`` -> ``n``); None for a
  relative (``.``, ``..``, ``./``, ``../``) or absolute specifier, a ``node:`` builtin, a ``#`` subpath import, a
  URL-like one (holding ``:``) and a scope without a name.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
from typing import Any

SKIP_DIRS = {".git", "node_modules", "dist", "coverage", ".nx", ".next", ".turbo", ".cache", "target"}
SOURCE_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
ALIAS_FILES = ("tsconfig.base.json", "tsconfig.json")
FILL = "x"
JEST_CONFIG = re.compile(r"jest\.config\.(?:js|ts|mjs|cjs|mts|cts)")
PRESET = re.compile(r"""(?<![\w$.])['"]?preset['"]?\s*:\s*(['"])([^'"\n]+)\1""")
ROOT_DIR = re.compile(r"""(?<![\w$.])['"]?rootDir['"]?\s*:""")
REGEX_AFTER = set("(,=:[!&|?{};+-*%~^")
REGEX_WORDS = {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw", "yield", "await"}
SPECIFIER = re.compile(
    r"""(?:\bimport|\bexport)\s[^'"`;]*?\bfrom\s*(['"])([^'"\n]+)\1"""
    r"""|\bimport\s*(['"])([^'"\n]+)\3"""
    r"""|\bimport\s*\(\s*(['"])([^'"\n]+)\5\s*\)"""
    r"""|\brequire\s*\(\s*(['"])([^'"\n]+)\7\s*\)""")


def walk(root: str) -> tuple[list[str], list[str]]:
    files: list[str] = []
    dirs: list[str] = [""]
    stack = [""]
    while stack:
        rel = stack.pop()
        with os.scandir(os.path.join(root, rel) if rel else root) as entries:
            for entry in entries:
                path = rel + "/" + entry.name if rel else entry.name
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if entry.name not in SKIP_DIRS:
                        dirs.append(path)
                        stack.append(path)
                elif entry.is_file():
                    files.append(path)
    return sorted(files), sorted(dirs)


def code_view(text: str) -> str:
    """``text`` of the same length with every comment blanked (newlines kept) and the inside of every string,
    template and regular-expression literal written ``FILL`` (a quote, a newline and the delimiters kept), so a
    keyword or quote inside one is not code."""
    out = list(text)
    i, n = 0, len(text)
    last = ""  # the last code character that is not a blank, "" at the start
    word = ""  # the last word of code
    while i < n:
        c = text[i]
        if text.startswith("//", i) or text.startswith("/*", i):
            end = text.find("\n", i) if text[i + 1] == "/" else text.find("*/", i + 2)
            end = n if end < 0 else end if text[i + 1] == "/" else end + 2
            for k in range(i, end):
                out[k] = "\n" if text[k] == "\n" else " "
            i = end
        elif c in "'\"`" or (c == "/" and (last == "" or last in REGEX_AFTER or word in REGEX_WORDS)):
            j, in_class = i + 1, False
            while j < n:
                d = text[j]
                if d == "\\":
                    j += 2
                    continue
                if d == "\n" and c != "`":
                    break
                if c == "/" and d in "[]":
                    in_class = d == "["
                elif d == c and not in_class:
                    break
                j += 1
            for k in range(i + 1, min(j, n)):
                out[k] = text[k] if text[k] == "\n" else FILL
            i, last, word = j + 1, c, ""
        else:
            if not c.isspace():
                word = word + c if (c.isalnum() or c in "_$") and (last.isalnum() or last in "_$") else \
                    (c if c.isalnum() or c in "_$" else "")
                last = c
            i += 1
    return "".join(out)


def specifiers(text: str) -> list[str]:
    view = code_view(text)
    out = []
    for m in SPECIFIER.finditer(view):
        group = next(g for g in (2, 4, 6, 8) if m.group(g) is not None)
        out.append(text[m.start(group):m.end(group)])
    return out


def jsonc_loads(text: str) -> Any:
    """JSON with ``//`` and ``/* */`` comments and trailing commas (tsconfig's dialect); strings kept as written."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", "".join(out)))


def jest_preset(text: str) -> str | None:
    """The string of the first ``preset`` key of a jest configuration's code (``code_view``), written
    ``preset: '<value>'`` or with ``"``; None when there is none or the configuration's code names ``rootDir``
    (a preset is resolved from ``rootDir``, which this reader does not evaluate)."""
    view = code_view(text)
    if _in_code(ROOT_DIR, text, view):
        return None
    m = _in_code(PRESET, text, view)
    return m.group(2) if m else None


def _in_code(regex: re.Pattern, text: str, view: str) -> re.Match | None:
    """The first match of ``regex`` (a key and its ``:``) over ``text`` whose first character and first ``:`` are
    code (the same in ``code_view``), so a key inside a comment or a string is not one."""
    def code(i: int) -> bool:
        return view[i] == text[i]
    return next((m for m in regex.finditer(text)
                 if code(m.start()) and code(m.start() + m.group(0).index(":"))), None)


def extends(text: str) -> list[str]:
    try:
        value = jsonc_loads(text)
    except (ValueError, RecursionError):
        return []
    value = value.get("extends") if isinstance(value, dict) else None
    values = [value] if isinstance(value, str) else value if isinstance(value, list) else []
    return [v for v in values if isinstance(v, str) and v]


def alias_file(files) -> str | None:
    return next((name for name in ALIAS_FILES if name in files), None)


def aliases(text: str) -> list[tuple[str, str]]:
    options = (jsonc_loads(text) or {}).get("compilerOptions") or {}
    base = options.get("baseUrl", ".")
    base = posixpath.normpath(base) if isinstance(base, str) else "."
    base = "" if base == "." or base == ".." or base.startswith("../") or base.startswith("/") else base
    found = []
    for pattern, targets in (options.get("paths") or {}).items():
        if isinstance(targets, list) and targets and isinstance(targets[0], str):
            found.append((pattern, posixpath.join(base, targets[0]) if base else targets[0]))
    exact = [a for a in found if "*" not in a[0]]
    return sorted(exact) + sorted(a for a in found if "*" in a[0])


def alias_path(spec: str, table: list[tuple[str, str]]) -> str | None:
    for pattern, target in table:
        if "*" not in pattern:
            if spec == pattern:
                return target
            continue
        head, _, tail = pattern.partition("*")
        if spec.startswith(head) and spec.endswith(tail) and len(spec) >= len(head) + len(tail):
            return target.replace("*", spec[len(head):len(spec) - len(tail)], 1)
    return None


def is_relative(spec: str) -> bool:
    return spec in (".", "..") or spec.startswith("./") or spec.startswith("../")


def package_name(spec: str) -> str | None:
    if is_relative(spec) or spec.startswith("/") or spec.startswith("#") or ":" in spec or "\\" in spec:
        return None
    parts = spec.split("/")
    if spec.startswith("@"):
        return "/".join(parts[:2]) if len(parts) >= 2 and len(parts[0]) > 1 and parts[1] else None
    return parts[0] or None
