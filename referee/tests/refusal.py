"""One rule for every command-line refusal test: an exit-2 line is the module's own refusal, not ``cli.run``'s fault.

A module refuses unusable input in its own handler: exit 2 and its own line. An exception the module did not expect
reaches ``cli.run`` (rule 5), which also exits 2, but writes ``internal error: <type>`` on stderr and the module's
``FAULT_LINE`` (or ``cli.GENERIC_LINE`` when a fault-line function fails) on stdout. A test that takes any exit-2
line with an ``error`` key as the refusal therefore passes when the module crashes (ledger f951, f952): the crash
looks like a refusal. ``assert_refused`` tells them apart by both marks of a fault, so a caller asserts only what
its own refusal says (its ``error`` text, its ``ok``).

Out of scope: a run whose stderr was not captured (the stderr mark is then not seen; the line check still holds),
and a refusal whose line equals the module's fault line by design (no module here has one: each refusal names its
cause).
"""

from __future__ import annotations

import re
from typing import Any

import cli

FAULT_MARK = re.compile(r"(?m)^internal error: ")


def assert_refused(test: Any, module: Any, argv: list[str], code: int, line: Any, stderr: str | bytes) -> None:
    """``code`` is exit 2 and (``line``, ``stderr``) carry no mark of ``cli.run``'s fault path for ``module``
    run with ``argv``: no ``internal error: `` stderr line, no traceback, and ``line`` is neither the module's
    fault line for ``argv`` nor ``cli.GENERIC_LINE``."""
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", "replace")
    test.assertEqual(code, cli.FAULT_EXIT, (argv, line, stderr))
    test.assertNotIn("Traceback", stderr, argv)
    test.assertIsNone(FAULT_MARK.search(stderr), "cli.run's fault, not a refusal: %r %r" % (argv, stderr))
    for fault in (cli._line(module.FAULT_LINE, argv), cli.GENERIC_LINE):  # the one rule cli.run picks it by
        test.assertNotEqual(line, fault, "cli.run's fault line, not a refusal: %r" % (argv,))
