"""The one process boundary of every referee command line: each module ends with
``sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))``.

Why: every command here answers with its exit code, and 0 and 1 are verdicts in each of them (clean or match,
merge or reject, valid or broken; each module's docstring gives its own meaning), while 2 is "unusable, no
verdict". Python itself ends a process with exit 1 when an exception escapes, and with 120 when stdout cannot
be flushed at shutdown. So a fault (a bug, an exception a module's own handlers did not expect, an exception in
such a handler, or a stdout that is closed or a broken pipe) would read as a verdict. Measured before this module:
with stdout closed, 20 of the 22 commands exited 1 (``gate.secrets scan`` on a clean file said "match").

Rules ``run`` keeps (each bound by a test in ``tests/test_cli.py``):

1. ``main``'s stdout is held in memory and written to the real stdout only after ``main`` returned; so a run that
   faults never leaves a verdict line, even one ``main`` wrote before the fault.
2. ``main`` must return an ``int`` that is 0, 1 or 2 (a ``bool`` or ``None`` is a fault: ``sys.exit(None)``
   would be exit 0).
3. Any ``Exception`` escaping ``main``, and ``SystemExit`` raised inside it (a command returns its code, it does
   not exit), is a fault.
4. Writing or flushing the held output to the real stdout is part of the run; if it fails, that is a fault.
5. On a fault: exit 2; stderr gets ``internal error: <exception type>`` (the type only, never the message or a
   traceback: a message can carry the scanned or sent text, tohum/30c); stdout gets the module's ``fault_line``
   (a dict, or a function of argv for commands whose exit-2 line depends on the command; if that function fails,
   ``GENERIC_LINE``) as one JSON line. If stdout cannot take that line either, its descriptor is pointed at
   ``/dev/null`` so the interpreter's own flush at shutdown cannot turn the exit into 120. When the real stdout
   breaks part way through (rule 4), the bytes it took before breaking stay where they went; the exit is 2.

6. Outside this module, a handler that catches every exception (bare, ``Exception`` or ``BaseException``) either
   ends with a bare ``raise`` (cleanup) or reports through ``internal_error(<its exception>)``, and uses the
   exception nowhere else; so the last-resort text is this module's, type only. Every command but ``target.write``
   leaves the fault to ``run``; ``target.write`` keeps one handler, because its line says what was already sent. Bound by a register over every source file in ``tests/test_cli.py``. Not this rule's: the narrower
   handlers (``unusable input: <message>`` for ``ValueError``, ``OSError`` ...), whose messages are kept to say
   what was wrong with the input.

Out of scope, stated: a fault while the module is imported (``python -m`` runs the module's top level before this
boundary exists; ``tests/test_cli.py`` imports every command module, so a broken import is red before a push); signals and
``KeyboardInterrupt`` (they end the process with their own codes, never 1); the interpreter being killed;
a child process writing to descriptor 1 directly (no command here lets a child inherit it: ``gate.secrets send``
gives its sender stderr, the others capture or discard the child's stdout).
"""

from __future__ import annotations

import io
import json
import os
import sys
from typing import Any, Callable

FAULT_EXIT = 2
EXITS = (0, 1, 2)
GENERIC_LINE = {"error": "internal error"}


class Fault(Exception):
    """``main`` broke the boundary's contract (rule 2, 3 or 4)."""


def internal_error(exc: BaseException) -> str:
    """The one text of an unexpected exception (rule 5): ``internal error: <type>``, never the message.

    A ``Fault``'s text is written here, by this module, so it is kept (``exit 3``, ``stdout``). Used by ``run`` and
    by the one module handler that reports a fault itself (``target.write``: it knows what it already wrote).
    """
    return "internal error: %s" % (str(exc) if isinstance(exc, Fault) else type(exc).__name__)


def _call(main: Callable[[list[str]], Any], argv: list[str]) -> tuple[int, str]:
    held = io.StringIO()
    real = sys.stdout
    sys.stdout = held
    try:
        try:
            code = main(argv)
        except SystemExit as exc:
            raise Fault("SystemExit") from exc
    finally:
        sys.stdout = real
    if type(code) is not int or code not in EXITS:
        raise Fault("exit %r" % (code,))
    return code, held.getvalue()


def _say(stream: Any, text: str) -> bool:
    """Write and flush ``text``; False when the stream is closed (None) or broken."""
    try:
        stream.write(text)
        stream.flush()
        return True
    except (AttributeError, OSError, ValueError):
        return False


def _quiet_stdout() -> bool:
    """Point descriptor 1 at /dev/null (rule 5); False when there is no descriptor to point (a closed stdout)."""
    try:
        fd = sys.stdout.fileno()
        devnull = os.open(os.devnull, os.O_WRONLY)
    except (AttributeError, OSError, ValueError):
        return False
    try:
        os.dup2(devnull, fd)
    finally:
        os.close(devnull)
    return True


def _line(fault_line: Any, argv: list[str]) -> dict[str, Any]:
    """The module's exit-2 line; a ``fault_line`` function that itself fails gives ``GENERIC_LINE``."""
    if not callable(fault_line):
        return fault_line
    try:
        return fault_line(argv)
    except Exception:  # noqa: BLE001 - the line is chosen during a fault; the exit code already says no verdict
        return GENERIC_LINE


def run(main: Callable[[list[str]], Any], argv: list[str], fault_line: Any) -> int:
    """Run ``main(argv)`` under rules 1-5 of the module docstring and return the process's exit code."""
    try:
        code, out = _call(main, argv)
        if not _say(sys.stdout, out):
            raise Fault("stdout")
        return code
    except Exception as exc:  # noqa: BLE001 - rule 5: a fault is exit 2 with a reason, never exit 1
        # The exit code is the answer; the two lines below are best effort, a closed stream cannot change it.
        _say(sys.stderr, internal_error(exc) + "\n")
        if not _say(sys.stdout, json.dumps(_line(fault_line, argv), sort_keys=True) + "\n"):
            _quiet_stdout()
        return FAULT_EXIT
