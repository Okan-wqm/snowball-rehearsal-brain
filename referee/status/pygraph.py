"""The import graph of a tree of Python files, read from their source: the one reader of "which module imports
which" for ``status.depmap`` (the brain's drawing and the register of the off-live), ``tests/mutate.py`` (which tests
reach a mutated file) and ``harness.offline`` (the harness reaches no client; the loop runs that one).

Rules (``status.depmap``'s "The brain" states them for the drawing; they are these functions'):

- a module is a ``.py`` file under the root, named by its path (``gate/secrets.py`` is ``gate.secrets``,
  ``gate/__init__.py`` is ``gate``); directories named in ``BRAIN_SKIP`` and hidden directories are not entered;
- ``import_statements``: every ``import`` statement of a source, anywhere in it (inside a function too);
- ``module_imports``: the modules under the root those statements name: ``import x.y.z`` and ``from x.y import z``
  name the deepest known module among ``x.y.z``, ``x.y``, ``x`` (``from x.y import z`` names ``x.y.z`` when that
  is a module); a relative ``from .`` is resolved against the importing module's package; a statement naming no
  module under the root, or the module itself, names nothing;
- ``outside_imports``: the first names of the absolute statements that name no module or package under the root
  (the standard library, a third party): what ``module_imports`` leaves out.

Not read, stated: a module imported by a name built at run time (``importlib``, ``__import__``), code run through
``exec`` or ``eval``, a module started as a subprocess. A source that does not parse raises ``SyntaxError``.
"""

from __future__ import annotations

import ast
import functools
import os

BRAIN_SKIP = {"tests", "__pycache__"}
READ_KEPT = 4096   # the texts whose import statements a process keeps (``import_statements``)


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
            rel = "/".join(parts + [name])
            dotted = module_name(rel)
            if dotted:
                modules[dotted] = rel
    return modules


def module_name(rel: str) -> str:
    """The dotted name of a ``.py`` path relative to its root (``a/b.py`` is ``a.b``, ``a/__init__.py`` is ``a``;
    the root's own ``__init__.py`` is ``""``)."""
    parts = rel[:-3].split("/")
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def with_packages(names: set[str], modules: dict[str, str]) -> set[str]:
    """``names`` and every package among ``modules`` holding one of them: importing ``a.b.c`` runs ``a`` and ``a.b``
    first."""
    return set(names) | {".".join(n.split(".")[:i]) for n in names for i in range(1, n.count(".") + 1)} & set(modules)


def _deepest(name: str, modules: dict[str, str]) -> str | None:
    parts = name.split(".")
    for n in range(len(parts), 0, -1):
        candidate = ".".join(parts[:n])
        if candidate in modules:
            return candidate
    return None


@functools.lru_cache(maxsize=READ_KEPT)
def import_statements(source: str) -> tuple[tuple[int, str, tuple[str, ...]], ...]:
    """Every import statement of a Python source, anywhere in it: ``(level, module, names)``; ``import a.b`` is
    ``(0, "a.b", ())``, ``from ..x import y, z`` is ``(2, "x", ("y", "z"))``, ``from . import y`` is
    ``(1, "", ("y",))``. ``SyntaxError`` when the source does not parse. The one reader of both maps. The answer
    is a function of the text alone and is kept by the text (``READ_KEPT`` texts, the least recently asked dropped
    first): a text asked again in this process is not parsed again; a refusal is not kept. The answer is of tuples,
    so no caller can change what the next one is given."""
    return tuple((level, name, tuple(names)) for level, name, names in tree_import_statements(ast.parse(source)))


def tree_import_statements(tree: ast.AST) -> list[tuple[int, str, list[str]]]:
    """``import_statements`` of a parsed source."""
    out: list[tuple[int, str, list[str]]] = []
    for node in ast.walk(tree):
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


def reachable(edges: dict[str, set[str]], roots: list[str]) -> set[str]:
    """``roots`` and every node an arrow of ``edges`` leads to from one of them."""
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node, ()))
    return seen


def outside_imports(source: str, modules: dict[str, str]) -> set[str]:
    """The first names (``a`` of ``a.b``) of the absolute import statements of ``source`` that are no module or
    package under the root: with ``referee/`` first on ``sys.path`` a first name under the root is the root's."""
    tops = {name.split(".")[0] for name in modules}
    return {name.split(".")[0] for level, name, _ in import_statements(source) if not level} - tops
