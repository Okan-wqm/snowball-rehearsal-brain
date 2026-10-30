"""``status.depmap``: the dependency drawings, what depends on what, generated from code and never written by hand.

Owner's rule (2026-10-30): a drawing a human can read, of the target and of the brain, generated from the verified
map, kept in the brain repository and regenerated in the push that changes the code it maps; a stale drawing is a
stale document. The brain's drawing is ``docs/map/brain.md`` and test 42 regenerates it from ``referee/`` and fails
on any byte of difference; the target's is ``docs/map/target.md``, made from a read-only checkout of the target
and carrying the target commit it was made from (the referee's sandbox holds no target, so it is regenerated in
the session that reads the target, not by a test).

**The brain** (``brain_map``), over the Python files under a root (``referee/``), ``tests/``, hidden directories and
``__pycache__`` not read:

- a module is a ``.py`` file, named by its path (``gate/secrets.py`` is ``gate.secrets``, ``gate/__init__.py`` is
  ``gate``, ``activate.py`` is ``activate``);
- an arrow A -> B means A's source holds an ``import`` statement, anywhere in it (inside a function too), that names
  B: ``import x.y.z`` and ``from x.y import z`` name the deepest known module among ``x.y.z``, ``x.y``, ``x``
  (``from x.y import z`` names ``x.y.z`` when that is a module); a relative ``from .`` is resolved against A's
  package; an import naming no module under the root (the standard library, a third party), or A itself, draws
  nothing;
- a live root is a module that a workflow file under ``ROOT/.github/workflows/`` starts with ``python -m`` or
  ``python3 -m``; a module started there that is not under the root is listed as external, not drawn;
- live means reachable from a live root by arrows, and a package (``__init__.py``) holding a live module is live,
  since Python runs it first; no arrow is drawn for that. An import is not a call: a live module may still be one that
  nothing calls (a mechanism imported but not wired). Off the live path means not reachable at all.
- Not read, stated: modules imported by a name built at run time (``importlib``), modules started as a
  subprocess (``python -m`` inside Python code), a file that does not parse (listed, no arrows).

**The target** (``target_map``), over a checkout's files (``SKIP_DIRS`` never entered, symbolic links not followed):

- a project is a directory named by one of three manifests read at the root only: the npm ``workspaces`` of the
  root ``package.json`` (an array, or ``{packages: [...]}``; each pattern matched segment by segment with ``*`` and
  ``?`` inside a segment, ``**`` any number of segments, a leading ``!`` excluding; a match is a directory holding
  a ``package.json``; its name the manifest's ``name``, else the directory); every Nx ``project.json`` (its
  ``name``, else the directory's last segment); the members of the root ``Cargo.toml``'s ``[workspace]`` (globs as
  above, minus ``exclude``; the name ``[package].name``); every ``pyproject.toml`` below the root (its
  ``[project].name``, else the directory's last segment). The root directory itself is never a project. A
  directory named by several manifests is one project with every kind;
- a file belongs to the project with the deepest directory holding it;
- an arrow A -> B, labelled with how it was found: ``npm`` (a key of ``dependencies``, ``devDependencies``,
  ``peerDependencies`` or ``optionalDependencies`` of A's ``package.json`` is B's npm name), ``cargo`` (a dependency
  of A's ``Cargo.toml``, in ``[dependencies]``, ``[dev-dependencies]``, ``[build-dependencies]`` or a
  ``[target.*]`` one, whose ``path``, or whose ``[workspace.dependencies]`` entry's ``path`` when it is
  ``workspace = true``, is B's directory), ``import`` (a JS/TS file of A, one of ``SOURCE_EXTENSIONS``, holds an
  import specifier resolving into B: a relative one by its path, a bare one equal to B's npm name or starting
  with it and ``/``, or one matching a ``compilerOptions.paths`` alias of the root ``tsconfig.base.json``, else
  ``tsconfig.json`` (first target of the first matching alias, exact before ``*``; ``baseUrl`` honoured)),
  ``python`` (a ``.py`` file of A, read by ``import_statements``, imports by an absolute name whose first part is
  a top-level package of B: a directory ``B/<name>/`` or ``B/src/<name>/`` holding ``__init__.py``; the first
  project in path order wins a name two projects hold; a relative import is counted, never drawn);
- an import specifier is the quoted string of ``import ... from``, ``export ... from``, a bare ``import '...'``,
  ``import('...')`` and ``require('...')``, read by ``SPECIFIER`` over the text as written: a commented-out import
  counts, an import whose specifier is not a string literal does not;
- not read, stated: nested workspaces (a ``package.json`` or ``Cargo.toml`` workspace below the root), Rust ``use``
  lines (the manifest is Cargo's own list), a Python package that is a single module file, Go's and every other
  language's imports (counted by extension in ``coverage.unread_code_files``), whether a resolved path exists,
  project references in ``tsconfig``;
- ``coverage`` says how much of the checkout this map holds: files, JS/TS and Python files read, specifiers by
  outcome (an import in a file of no project, or into no project, is ``outside_projects``), manifests that could
  not be parsed, and code files of languages not read.

Command line, run from ``referee/``::

    python -m status.depmap brain ROOT                    the brain's drawing (markdown) on stdout
    python -m status.depmap target ROOT --source LABEL    the target's drawing (markdown) on stdout
    python -m status.depmap coverage ROOT                 the target map's coverage, one JSON line

exit 0, or 2 on a bad command line or a root that is not a directory.
"""

from __future__ import annotations

import ast
import json
import os
import posixpath
import re
import sys
from typing import Any

USAGE = "usage: python -m status.depmap brain ROOT | target ROOT --source LABEL | coverage ROOT"
GENERATED = "Generated by `python -m status.depmap %s` from %s; do not edit by hand."

BRAIN_SKIP = {"tests", "__pycache__"}
WORKFLOW_MODULE = re.compile(r"\bpython3?\s+-m\s+([A-Za-z_][A-Za-z0-9_.]*)")

SKIP_DIRS = {".git", "node_modules", "dist", "coverage", ".nx", ".next", ".turbo", ".cache", "target"}
SOURCE_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
OTHER_CODE_EXTENSIONS = {".rs", ".go", ".java", ".kt", ".rb", ".php", ".cs", ".c", ".cc", ".cpp", ".h",
                         ".swift", ".scala", ".sh", ".vue", ".svelte"}
NPM_DEP_FIELDS = ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
CARGO_DEP_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")
SPECIFIER = re.compile(
    r"""(?:\bimport|\bexport)\s[^'"`;]*?\bfrom\s*(['"])([^'"\n]+)\1"""
    r"""|\bimport\s*(['"])([^'"\n]+)\3"""
    r"""|\bimport\s*\(\s*(['"])([^'"\n]+)\5\s*\)"""
    r"""|\brequire\s*\(\s*(['"])([^'"\n]+)\7\s*\)""")


# ---------------------------------------------------------------------------------------------------- the brain


def python_modules(root: str) -> dict[str, str]:
    """Dotted module name -> path relative to ``root``, for every ``.py`` file outside ``BRAIN_SKIP`` and hidden
    directories."""
    modules: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in BRAIN_SKIP and not d.startswith("."))
        rel_dir = os.path.relpath(dirpath, root)
        parts = [] if rel_dir == "." else rel_dir.split(os.sep)
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            stem = name[:-3]
            dotted = ".".join(parts if stem == "__init__" else parts + [stem])
            if dotted:
                modules[dotted] = "/".join(parts + [name])
    return modules


def _deepest(name: str, modules: dict[str, str]) -> str | None:
    parts = name.split(".")
    for n in range(len(parts), 0, -1):
        candidate = ".".join(parts[:n])
        if candidate in modules:
            return candidate
    return None


def import_statements(source: str) -> list[tuple[int, str, list[str]]]:
    """Every import statement of a Python source, anywhere in it: ``(level, module, names)``; ``import a.b`` is
    ``(0, "a.b", [])``, ``from ..x import y, z`` is ``(2, "x", ["y", "z"])``, ``from . import y`` is
    ``(1, "", ["y"])``. ``SyntaxError`` when the source does not parse. The one reader of both maps."""
    out: list[tuple[int, str, list[str]]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out.extend((0, alias.name, []) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.append((node.level, node.module or "", [a.name for a in node.names if a.name != "*"]))
    return out


def module_imports(source: str, module: str, is_package: bool, modules: dict[str, str]) -> set[str]:
    """The modules under the root that ``module``'s import statements name (rules in the module docstring)."""
    found: set[str] = set()
    for level, name, names in import_statements(source):
        if level:
            package = module.split(".") if is_package else module.split(".")[:-1]
            up = level - 1
            if up > len(package):
                continue
            base = ".".join(package[:len(package) - up] + (name.split(".") if name else []))
        else:
            base = name
        if not names:
            target = _deepest(base, modules) if base else None
            if target:
                found.add(target)
        for alias in names:
            full = base + "." + alias if base else alias
            target = full if full in modules else _deepest(base, modules) if base else None
            if target:
                found.add(target)
    found.discard(module)
    return found


def workflow_modules(root: str) -> list[str]:
    """Every module name a workflow file under ``ROOT/.github/workflows`` starts with ``python -m``, sorted."""
    names: set[str] = set()
    wf_dir = os.path.join(root, ".github", "workflows")
    if os.path.isdir(wf_dir):
        for name in sorted(os.listdir(wf_dir)):
            if name.endswith((".yml", ".yaml")):
                with open(os.path.join(wf_dir, name), encoding="utf-8") as f:
                    names.update(WORKFLOW_MODULE.findall(f.read()))
    return sorted(names)


def reachable(edges: dict[str, set[str]], roots: list[str]) -> set[str]:
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))
    return seen


def brain_map(root: str) -> dict[str, Any]:
    modules = python_modules(root)
    edges: dict[str, set[str]] = {}
    unparsed: list[str] = []
    entry: set[str] = set()
    for name, rel in modules.items():
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            source = f.read()
        try:
            edges[name] = module_imports(source, name, rel.endswith("__init__.py"), modules)
        except SyntaxError:
            unparsed.append(rel)
            edges[name] = set()
            continue
        if re.search(r"^if __name__ == [\"']__main__[\"']:", source, re.M):
            entry.add(name)
    started = workflow_modules(root)
    roots = [m for m in started if m in modules]
    live = reachable(edges, roots)
    live |= {".".join(n.split(".")[:i]) for n in live for i in range(1, n.count(".") + 1)} & set(modules)
    return {
        "modules": modules,
        "edges": {k: sorted(v) for k, v in sorted(edges.items())},
        "roots": roots,
        "external_roots": [m for m in started if m not in modules],
        "live": sorted(live),
        "off_live": sorted(set(modules) - live),
        "entry_points": sorted(entry),
        "unparsed": sorted(unparsed),
    }


# --------------------------------------------------------------------------------------------------- the target


def _segment(seg: str) -> str:
    return "".join("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in seg)


def _glob_regex(pattern: str) -> re.Pattern:
    """One workspace pattern as a regex over ``/`` and a relative directory: ``*`` and ``?`` stay inside one
    segment, ``**`` is any number of whole segments (none included)."""
    segments = [s for s in pattern.strip("/").split("/") if s not in ("", ".")]
    return re.compile("^" + "".join(r"(?:/[^/]+)*" if s == "**" else "/" + _segment(s) for s in segments) + "$")


def glob_dirs(patterns: list[str], dirs: list[str]) -> list[str]:
    """The directories (relative, ``/``-separated) matched by the include patterns and by no ``!`` pattern."""
    include = [_glob_regex(p) for p in patterns if not p.startswith("!")]
    exclude = [_glob_regex(p[1:]) for p in patterns if p.startswith("!")]
    return sorted(d for d in dirs if d and any(r.match("/" + d) for r in include)
                  and not any(r.match("/" + d) for r in exclude))


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


def walk_checkout(root: str) -> tuple[list[str], list[str]]:
    """Files and directories under ``root`` (relative, ``/``-separated, sorted; the root is ``""``), ``SKIP_DIRS``
    never entered and symbolic links not followed (a link is neither a file nor a directory here)."""
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


def _read(root: str, rel: str) -> str | None:
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


class _Projects:
    def __init__(self) -> None:
        self.by_dir: dict[str, dict[str, Any]] = {}

    def add(self, d: str, kind: str, name: str) -> None:
        p = self.by_dir.setdefault(d, {"dir": d, "kinds": set(), "names": {}})
        p["kinds"].add(kind)
        p["names"].setdefault(kind, name)

    def owner(self, path: str) -> str | None:
        """The deepest project directory holding ``path`` (a file or a directory), or None."""
        probe = path
        while probe:
            if probe in self.by_dir:
                return probe
            probe = posixpath.dirname(probe)
        return None


def _norm(path: str) -> str | None:
    """``path`` normalised relative to the root, or None when it leaves the root."""
    p = posixpath.normpath(path)
    if p == ".":
        return ""
    if p.startswith("../") or p == ".." or p.startswith("/"):
        return None
    return p


def _tsconfig_aliases(root: str, files: set[str], coverage: dict) -> list[tuple[str, str]]:
    for name in ("tsconfig.base.json", "tsconfig.json"):
        if name in files:
            text = _read(root, name)
            try:
                options = (jsonc_loads(text or "") or {}).get("compilerOptions") or {}
            except ValueError:
                coverage["unparsed_manifests"].append(name)
                return []
            base = _norm(options.get("baseUrl", ".")) or ""
            aliases = []
            for pattern, targets in (options.get("paths") or {}).items():
                if isinstance(targets, list) and targets and isinstance(targets[0], str):
                    aliases.append((pattern, posixpath.join(base, targets[0]) if base else targets[0]))
            exact = [a for a in aliases if "*" not in a[0]]
            return sorted(exact) + sorted(a for a in aliases if "*" in a[0])
    return []


def _alias_path(spec: str, aliases: list[tuple[str, str]]) -> str | None:
    for pattern, target in aliases:
        if "*" not in pattern:
            if spec == pattern:
                return target
            continue
        head, _, tail = pattern.partition("*")
        if spec.startswith(head) and spec.endswith(tail) and len(spec) >= len(head) + len(tail):
            return target.replace("*", spec[len(head):len(spec) - len(tail)], 1)
    return None


def _cargo_deps(manifest: dict) -> list[tuple[str, Any]]:
    deps: list[tuple[str, Any]] = []
    tables = [manifest] + [t for t in (manifest.get("target") or {}).values() if isinstance(t, dict)]
    for table in tables:
        for key in CARGO_DEP_TABLES:
            for name, spec in sorted((table.get(key) or {}).items()):
                deps.append((name, spec))
    return deps


def target_map(root: str) -> dict[str, Any]:
    import tomllib

    files, dirs = walk_checkout(root)
    file_set = set(files)
    coverage: dict[str, Any] = {"files": len(files), "unparsed_manifests": [], "unread_code_files": {},
                                "source_files": 0, "source_files_outside_projects": 0,
                                "python_files": 0, "python_files_unparsed": 0,
                                "specifiers": {"cross_project": 0, "same_project": 0, "external_package": 0,
                                               "outside_projects": 0, "leaves_root": 0, "python_external": 0,
                                               "python_relative": 0}}
    projects = _Projects()
    manifests: dict[str, dict] = {}

    def load_json(rel: str) -> dict | None:
        try:
            value = json.loads(_read(root, rel) or "")
        except ValueError:
            coverage["unparsed_manifests"].append(rel)
            return None
        return value if isinstance(value, dict) else None

    # npm workspaces
    npm_names: dict[str, str] = {}
    root_pkg = load_json("package.json") if "package.json" in file_set else None
    workspaces = (root_pkg or {}).get("workspaces")
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    if isinstance(workspaces, list):
        pkg_dirs = [d for d in dirs if d + "/package.json" in file_set]
        for d in glob_dirs([w for w in workspaces if isinstance(w, str)], pkg_dirs):
            pkg = load_json(d + "/package.json")
            if pkg is None:
                continue
            manifests[d] = pkg
            name = pkg.get("name") if isinstance(pkg.get("name"), str) else d
            projects.add(d, "npm", name)
            npm_names.setdefault(name, d)
    # Nx projects
    for rel in files:
        if posixpath.basename(rel) == "project.json" and posixpath.dirname(rel):
            pj = load_json(rel)
            if pj is None:
                continue
            d = posixpath.dirname(rel)
            projects.add(d, "nx", pj.get("name") if isinstance(pj.get("name"), str) else posixpath.basename(d))
    # Cargo workspace
    cargo: dict[str, dict] = {}
    root_cargo: dict = {}
    if "Cargo.toml" in file_set:
        try:
            root_cargo = tomllib.loads(_read(root, "Cargo.toml") or "")
        except tomllib.TOMLDecodeError:
            coverage["unparsed_manifests"].append("Cargo.toml")
        ws = root_cargo.get("workspace") or {}
        crate_dirs = [d for d in dirs if d + "/Cargo.toml" in file_set]
        members = glob_dirs(list(ws.get("members") or []), crate_dirs)
        members = [d for d in members if d not in set(glob_dirs(list(ws.get("exclude") or []), crate_dirs))]
        for d in members:
            try:
                manifest = tomllib.loads(_read(root, d + "/Cargo.toml") or "")
            except tomllib.TOMLDecodeError:
                coverage["unparsed_manifests"].append(d + "/Cargo.toml")
                continue
            cargo[d] = manifest
            projects.add(d, "cargo", (manifest.get("package") or {}).get("name") or posixpath.basename(d))

    # Python projects: a pyproject.toml below the root; their top-level packages
    py_packages: dict[str, str] = {}
    for rel in files:
        if posixpath.basename(rel) == "pyproject.toml" and posixpath.dirname(rel):
            d = posixpath.dirname(rel)
            try:
                pyproject = tomllib.loads(_read(root, rel) or "")
            except tomllib.TOMLDecodeError:
                coverage["unparsed_manifests"].append(rel)
                continue
            projects.add(d, "python", (pyproject.get("project") or {}).get("name") or posixpath.basename(d))
    for rel in files:
        parts = rel.split("/")
        if parts[-1] != "__init__.py" or len(parts) < 3:
            continue
        holder = "/".join(parts[:-2])
        holder = posixpath.dirname(holder) if posixpath.basename(holder) == "src" else holder
        if holder in projects.by_dir and "python" in projects.by_dir[holder]["kinds"]:
            py_packages.setdefault(parts[-2], holder)

    edges: dict[tuple[str, str], set[str]] = {}

    def edge(a: str | None, b: str | None, kind: str) -> None:
        if a is not None and b is not None and a != b:
            edges.setdefault((a, b), set()).add(kind)

    for d, pkg in manifests.items():
        for field in NPM_DEP_FIELDS:
            for name in sorted(pkg.get(field) or {}):
                if name in npm_names:
                    edge(d, npm_names[name], "npm")
    ws_deps = (root_cargo.get("workspace") or {}).get("dependencies") or {}
    for d, manifest in cargo.items():
        for name, spec in _cargo_deps(manifest):
            if not isinstance(spec, dict):
                continue
            path = None
            if isinstance(spec.get("path"), str):
                path = _norm(posixpath.join(d, spec["path"]))
            elif spec.get("workspace") is True and isinstance(ws_deps.get(name), dict) \
                    and isinstance(ws_deps[name].get("path"), str):
                path = _norm(ws_deps[name]["path"])
            if path is not None and path in projects.by_dir:
                edge(d, path, "cargo")

    aliases = _tsconfig_aliases(root, file_set, coverage)
    counts = coverage["specifiers"]
    for rel in files:
        ext = posixpath.splitext(rel)[1]
        if ext == ".py":
            text = _read(root, rel)
            try:
                statements = import_statements(text) if text is not None else None
            except (SyntaxError, ValueError):
                statements = None
            if statements is None:
                coverage["python_files_unparsed"] += 1
                continue
            coverage["python_files"] += 1
            here = projects.owner(rel)
            for level, name, _names in statements:
                if level:
                    counts["python_relative"] += 1
                    continue
                top = name.split(".")[0]
                if top not in py_packages:
                    counts["python_external"] += 1
                    continue
                there = py_packages[top]
                if here is None:
                    counts["outside_projects"] += 1
                elif here == there:
                    counts["same_project"] += 1
                else:
                    counts["cross_project"] += 1
                    edge(here, there, "python")
            continue
        if ext not in SOURCE_EXTENSIONS:
            if ext in OTHER_CODE_EXTENSIONS:
                coverage["unread_code_files"][ext] = coverage["unread_code_files"].get(ext, 0) + 1
            continue
        text = _read(root, rel)
        if text is None:
            continue
        coverage["source_files"] += 1
        here = projects.owner(rel)
        if here is None:
            coverage["source_files_outside_projects"] += 1
        for m in SPECIFIER.finditer(text):
            spec = m.group(2) or m.group(4) or m.group(6) or m.group(8)
            if spec.startswith("./") or spec.startswith("../") or spec in (".", ".."):
                path = _norm(posixpath.join(posixpath.dirname(rel), spec))
            else:
                path = _alias_path(spec, aliases)
                if path is not None:
                    path = _norm(path)
                else:
                    pkg_name = next((n for n in sorted(npm_names, key=len, reverse=True)
                                     if spec == n or spec.startswith(n + "/")), None)
                    if pkg_name is None:
                        counts["external_package"] += 1
                        continue
                    path = npm_names[pkg_name]
            if path is None:
                counts["leaves_root"] += 1
                continue
            there = projects.owner(path)
            if here is None or there is None:
                counts["outside_projects"] += 1
            elif here == there:
                counts["same_project"] += 1
            else:
                counts["cross_project"] += 1
                edge(here, there, "import")

    coverage["unparsed_manifests"] = sorted(set(coverage["unparsed_manifests"]))
    coverage["unread_code_files"] = dict(sorted(coverage["unread_code_files"].items()))
    coverage["projects"] = len(projects.by_dir)
    coverage["projects_by_kind"] = {k: sum(1 for p in projects.by_dir.values() if k in p["kinds"])
                                    for k in ("npm", "nx", "cargo", "python")}
    nodes = []
    for d, p in sorted(projects.by_dir.items()):
        name = next(p["names"][k] for k in ("npm", "nx", "cargo", "python") if k in p["names"])
        nodes.append({"dir": d, "name": name, "kinds": sorted(p["kinds"])})
    return {"projects": nodes,
            "edges": [{"from": a, "to": b, "kinds": sorted(k)} for (a, b), k in sorted(edges.items())],
            "coverage": coverage}


# ------------------------------------------------------------------------------------------------------ drawing


def _ids(names: list[str]) -> dict[str, str]:
    return {n: "n%d" % i for i, n in enumerate(sorted(names))}


def _label(text: str) -> str:
    return '"' + text.replace('"', "#quot;") + '"'


def render_brain(m: dict[str, Any], source: str = "`referee/`") -> str:
    names = sorted(m["modules"])
    ids = _ids(names)
    importers: dict[str, list[str]] = {n: [] for n in names}
    for a, targets in m["edges"].items():
        for b in targets:
            importers[b].append(a)
    groups: dict[str, list[str]] = {}
    for n in names:
        groups.setdefault(n.split(".")[0] if "." in n else "", []).append(n)
    lines = ["# The brain's dependency map", "", GENERATED % ("brain .", source + ", run there"), "",
             "An arrow A --> B: A holds an import statement naming B. Live roots (double border) are the modules "
             "the workflows under `referee/.github/workflows/` start with `python -m`; a live module (green) is "
             "reachable from one by imports, which is not proof that it is called; the others (grey) are off "
             "the live path: run by tests and vector commands only. Rules and what is not read: "
             "`referee/status/depmap.py`.", "",
             "Modules %d, arrows %d, live roots %s, live %d, off the live path %d." % (
                 len(names), sum(len(v) for v in m["edges"].values()), ", ".join(m["roots"]) or "none",
                 len(m["live"]), len(m["off_live"])), ""]
    if m["external_roots"]:
        lines += ["Started by a workflow but not under the root (not drawn): %s." % ", ".join(m["external_roots"]), ""]
    if m["unparsed"]:
        lines += ["Not parsed (no arrows): %s." % ", ".join(m["unparsed"]), ""]
    lines += ["```mermaid", "flowchart LR"]
    for group, members in sorted(groups.items()):
        if group:
            lines.append("  subgraph g_%s[%s]" % (group, _label(group)))
        for n in members:
            shape = "[[%s]]" if n in m["roots"] else "[%s]"
            lines.append("    %s%s" % (ids[n], shape % _label(n)))
        if group:
            lines.append("  end")
    for a, targets in m["edges"].items():
        for b in targets:
            lines.append("  %s --> %s" % (ids[a], ids[b]))
    lines.append("  classDef live fill:#d8f0d8,stroke:#2e7d32")
    lines.append("  classDef off fill:#eeeeee,stroke:#9e9e9e,color:#616161")
    if m["live"]:
        lines.append("  class %s live" % ",".join(ids[n] for n in m["live"]))
    if m["off_live"]:
        lines.append("  class %s off" % ",".join(ids[n] for n in m["off_live"]))
    lines += ["```", "", "| module | file | live | `__main__` | imports | imported by |", "|---|---|---|---|---|---|"]
    for n in names:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            n, m["modules"][n], "root" if n in m["roots"] else "yes" if n in m["live"] else "no",
            "yes" if n in m["entry_points"] else "", ", ".join(m["edges"][n]), ", ".join(sorted(importers[n]))))
    return "\n".join(lines) + "\n"


def render_target(m: dict[str, Any], source: str) -> str:
    dirs = [p["dir"] for p in m["projects"]]
    ids = _ids(dirs)
    cov = m["coverage"]
    sp = cov["specifiers"]
    groups: dict[str, list[dict]] = {}
    for p in m["projects"]:
        groups.setdefault(p["dir"].split("/")[0], []).append(p)
    lines = ["# The target's dependency map", "", GENERATED % ("target ROOT --source ...", source), "",
             "A box is a project (a directory named by the root's npm workspaces, an Nx `project.json`, the root "
             "Cargo workspace or a `pyproject.toml`); an arrow A --> B is labelled with how it was found: `npm` or "
             "`cargo` (A's manifest names B), `import` (a JS/TS file of A imports into B), `python` (a Python "
             "file of A imports a package of B). Rules and what is not read: `referee/status/depmap.py`.", "",
             "Projects %d (npm %d, nx %d, cargo %d, python %d), arrows %d. Files %d; JS/TS files read %d (%d outside "
             "any project), Python files read %d (%d not parsed). Imports: %d across projects, %d inside one, %d "
             "of external JS packages, %d of Python modules no project holds, %d relative Python (not drawn), %d "
             "from or into no project, %d leaving the root." % (
                 cov["projects"], cov["projects_by_kind"]["npm"], cov["projects_by_kind"]["nx"],
                 cov["projects_by_kind"]["cargo"], cov["projects_by_kind"]["python"], len(m["edges"]), cov["files"],
                 cov["source_files"], cov["source_files_outside_projects"], cov["python_files"],
                 cov["python_files_unparsed"], sp["cross_project"], sp["same_project"], sp["external_package"],
                 sp["python_external"], sp["python_relative"], sp["outside_projects"], sp["leaves_root"]), "",
             "Code files of languages whose imports are not read: %s." % (
                 ", ".join("%s %d" % kv for kv in cov["unread_code_files"].items()) or "none"), ""]
    if cov["unparsed_manifests"]:
        lines += ["Manifests not parsed: %s." % ", ".join(cov["unparsed_manifests"]), ""]
    lines += ["```mermaid", "flowchart LR"]
    for group, members in sorted(groups.items()):
        lines.append("  subgraph g%d[%s]" % (sorted(groups).index(group), _label(group)))
        for p in members:
            lines.append("    %s[%s]" % (ids[p["dir"]], _label(p["name"])))
        lines.append("  end")
    for e in m["edges"]:
        lines.append("  %s -->|%s| %s" % (ids[e["from"]], " ".join(e["kinds"]), ids[e["to"]]))
    lines += ["```", "", "| project | directory | manifests | depends on |", "|---|---|---|---|"]
    names = {p["dir"]: p["name"] for p in m["projects"]}
    out: dict[str, list[str]] = {d: [] for d in dirs}
    for e in m["edges"]:
        out[e["from"]].append("%s (%s)" % (names[e["to"]], " ".join(e["kinds"])))
    for p in m["projects"]:
        lines.append("| %s | %s | %s | %s |" % (p["name"], p["dir"], " ".join(p["kinds"]), ", ".join(out[p["dir"]])))
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("brain", "target", "coverage") or not os.path.isdir(argv[1]):
        print(USAGE, file=sys.stderr)
        return 2
    command, root, rest = argv[0], argv[1], argv[2:]
    if command == "brain" and not rest:
        sys.stdout.write(render_brain(brain_map(root)))
        return 0
    if command == "target" and len(rest) == 2 and rest[0] == "--source":
        sys.stdout.write(render_target(target_map(root), rest[1]))
        return 0
    if command == "coverage" and not rest:
        print(json.dumps(target_map(root)["coverage"], sort_keys=True))
        return 0
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
