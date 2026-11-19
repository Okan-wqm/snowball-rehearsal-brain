"""``harness.offline``: the harness reaches no model (P1 MF5; asama-0/09 test 9, asama-0/02 property 4).

Rules: asama-0/09 test 9 ("harness modules import no client, and pass with the network closed"), asama-1/13 (P1
row 5), tohum/26e (module ``harness/offline.py``), tohum/00 Y6 (the score is the harness's) and Y10 (an agent's one
connection out is the dispatcher's). No page says what a client is or how the absence is held; the two readings
below are this module's and are reported (reports/seed-077).

**What is read as the harness.** Every module of the package ``harness`` under the root (``PACKAGE``: the scorer
and its statistics, the PASS row's and the drill's judges, this module).

**Statically** (``check(root)``, over ``status.pygraph``'s import graph of the root's Python files): from the
harness's modules, every module under the root an ``import`` statement leads to, directly or through other modules.
Reasons, sorted, each once:

- ``client_import:<module>:<client>``: a module reached imports a module of a client package (``CLIENTS``:
  ``dispatcher``, whose ``llm_call`` is the one caller of a model in ``referee/``). A client is reported and not
  read further.
- ``foreign_import:<module>:<name>``: a module reached imports ``<name>``, which is neither under the root nor a
  module of the standard library (``sys.stdlib_module_names`` of the running Python): ``referee/`` has no third-party
  import, and a model's SDK would be one.
- ``dynamic_import:<module>:<name>``: a module reached imports one of ``DYNAMIC`` (``importlib``, ``runpy``,
  ``pkgutil``, ``zipimport``, ``imp``) or names ``__import__``: what it then loads is not in its import statements.
- ``unparsed:<path>``: a module reached does not parse or is not UTF-8; what it imports is unknown.
- ``no_harness_module``: the root holds no module of the package (a wrong root says nothing about the harness).

The answer is ``{roots, modules, reasons}``: the harness's modules, how many modules were reached (clients not
counted), the reasons. The command ``python -m harness.offline [ROOT]`` (default: the directory this package is
in) prints it with ``ok`` as one JSON line; exit 0 without a reason, 1 with one, 2 on any other argument list or a
fault (``FAULT_LINE``, ``cli.run``).

**While it runs** (``run(call)``): ``call()`` with this process's sockets and child processes refused. An audit
hook (``sys.addaudithook``, added once, idle outside ``run``) raises ``Online`` on every audit event named
``socket.<anything>`` and on ``subprocess.Popen``, ``os.exec``, ``os.fork``, ``os.forkpty``, ``os.posix_spawn``,
``os.spawn``, ``os.system``, ``os.startfile`` and ``pty.spawn`` (``REFUSED``): a model is reached over a socket or
by starting a program (``dispatcher.llm_call`` starts the ``claude`` CLI). ``run`` returns ``call``'s answer only
when no such event was raised: an event the call caught and went on from still ends in ``Online(events)`` (the
event names, sorted, each once). A ``run`` inside a ``run`` reports to both.

**Live** (``loop.job``): ``yaz`` runs ``check`` on its own code (``loop.job.CODE_ROOT``) before it reads anything
of a target and refuses the target with ``harness_online`` and the reasons; its four judgements
(``harness.score.report``, ``harness.pass_row.gate`` and ``judge``, and D8's ``harness.revert_drill.judge`` in
``loop.drill``) go through ``run``, and an ``Online`` from one of them refuses the target with ``harness_online``
and ``event:<name>`` reasons before that run writes ``brain/state`` (what the steps before the judgement did on
the target's other branches is not undone and not claimed).

Out of scope, stated: an import by a name built at run time in a module that names none of ``DYNAMIC`` (``exec``,
``eval``, ``sys.modules``); a module started as a program; a model reached without one of the listed audit events
(an extension module or ``ctypes`` calling the system directly, a file or pipe opened to a process that is already
running); other threads (the hook is the process's: while a ``run`` is open, a listed event of any thread is
refused and counted); the network of the machine (``run`` closes nothing outside this process: the referee's
sandbox and the ``koş`` job close theirs themselves); whether a standard-library module is used to reach a model
(``urllib`` and ``subprocess`` may be imported by a module reached: ``run`` is what refuses their use).
"""

from __future__ import annotations

import ast
import json
import os
import sys
from typing import Any, Callable

import cli
from status import pygraph

PACKAGE = "harness"
CLIENTS = ("dispatcher",)
DYNAMIC = ("imp", "importlib", "pkgutil", "runpy", "zipimport")
REFUSED = ("subprocess.Popen", "os.exec", "os.fork", "os.forkpty", "os.posix_spawn", "os.spawn", "os.system",
           "os.startfile", "pty.spawn")
REFUSED_PREFIX = "socket."
USAGE = "usage: python -m harness.offline [ROOT]"
FAULT_LINE = {"ok": False, "error": "internal error"}


class Online(Exception):
    """A refused event inside ``run``; ``events`` are the audit events' names, ``reasons`` each as
    ``event:<name>``."""

    def __init__(self, events: list[str]) -> None:
        super().__init__("harness went online: %s" % ", ".join(events))
        self.events = events
        self.reasons = ["event:%s" % event for event in events]


def _in(name: str, packages: tuple[str, ...]) -> bool:
    return name.split(".")[0] in packages


def _dynamic(source: str) -> set[str]:
    tree = ast.parse(source)
    found = {name.split(".")[0] for level, name, _ in pygraph.tree_import_statements(tree)
             if not level and name.split(".")[0] in DYNAMIC}
    if any(isinstance(node, ast.Name) and node.id == "__import__" for node in ast.walk(tree)):
        found.add("__import__")
    return found


def check(root: str) -> dict[str, Any]:
    """The static reading of the harness under ``root``; see the module docstring."""
    modules = pygraph.python_modules(root)
    roots = sorted(m for m in modules if _in(m, (PACKAGE,)))
    if not roots:
        return {"roots": [], "modules": 0, "reasons": ["no_harness_module"]}
    reasons: set[str] = set()
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        rel = modules[name]
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                source = f.read()
            imported = pygraph.module_imports(source, name, rel.endswith("__init__.py"), modules)
            outside = pygraph.outside_imports(source, modules)
            dynamic = _dynamic(source)
        except (SyntaxError, UnicodeDecodeError, ValueError):   # ValueError: a NUL in the source
            reasons.add("unparsed:%s" % rel)
            continue
        reasons.update("dynamic_import:%s:%s" % (name, d) for d in dynamic)
        reasons.update("foreign_import:%s:%s" % (name, o) for o in outside - set(sys.stdlib_module_names))
        clients = {target for target in imported if _in(target, CLIENTS)}
        reasons.update("client_import:%s:%s" % (name, target) for target in clients)
        stack.extend(pygraph.with_packages(imported - clients, modules))
    return {"roots": roots, "modules": len(seen), "reasons": sorted(reasons)}


_open: list[list[str]] = []     # one list of refused events per open ``run``, outermost first
_hooked = False


def _hook(event: str, _args: Any) -> None:
    if _open and (event in REFUSED or event.startswith(REFUSED_PREFIX)):
        for seen in _open:
            seen.append(event)
        raise Online([event])


def run(call: Callable[[], Any]) -> Any:
    """``call()`` with this process's sockets and child processes refused; see the module docstring."""
    global _hooked
    if not _hooked:
        sys.addaudithook(_hook)
        _hooked = True
    seen: list[str] = []
    _open.append(seen)
    try:
        answer = call()
    finally:
        _open.pop()
    if seen:
        raise Online(sorted(set(seen)))
    return answer


def main(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print(USAGE, file=sys.stderr)
        return 2
    root = argv[0] if argv else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    got = check(root)
    print(json.dumps(dict(got, ok=not got["reasons"]), sort_keys=True))
    return 1 if got["reasons"] else 0


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
