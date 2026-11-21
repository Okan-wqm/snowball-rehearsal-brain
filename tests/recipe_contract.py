"""The recipe contract: can the reader ``koş`` puts behind a recipe command read what that command prints, judged
from the command alone, before any run and any transfer.

Why (founder ledger f1560, tohum/00c E650): run 44473678747 of (B) ended ``zero_tests`` on a recipe whose test
command was jest without ``--json``; the recipe had been on ``main`` for a transfer, and its text alone showed
that ``runner.test_results`` would read no test of it. This tool reads every ``targets/<id>/units.json`` and
answers, for each unit's ``lint_cmd``, ``test_cmd`` and ``affected_test_cmd``, one of ``read``, ``unread`` and
``unknown``. Run from anywhere: ``python3 tests/recipe_contract.py [--targets DIR]``. It runs nothing of a
target and no command of a recipe.

The rules, each bound by ``tests/test_recipe_contract.py``:

1. **The program** of a command (a list of strings) is found by taking wrappers off, as often as one applies:
   (a) a first element ``env`` or ``/usr/bin/env`` goes with every ``NAME=value`` element after it (``NAME`` a
   shell name); (b) ``/bin/sh`` or ``sh``, ``-c``, exactly ``profile.nx.CD_EXEC`` and one directory element go
   (the form ``profile.nx`` composes); (c) ``node`` followed by an element that does not start with ``-`` goes,
   so the script is the program (``node <dir>/eslint.js``). The program word is the last ``/`` part of the first
   element left. A command that is not a non-empty list of strings, one with nothing left, and an ``env`` or
   ``sh`` form outside (a) and (b) are ``unknown`` (``not_a_command``, ``wrapper_not_read``).
2. Only the elements after the program and before the first element ``--`` are read as options.
3. **jest** (program word ``jest`` or ``jest.js``; reader ``jest``): ``read`` when an element is exactly
   ``profile.nx.JEST_JSON`` and no element is ``--outputFile`` or starts with ``--outputFile=``; else ``unread``
   (``jest_without_json``, ``jest_output_file``: the document then goes to no stdout
   ``runner.test_results.jest`` reads).
4. **node's test runner** (program word ``node`` with an element ``--test``; reader ``tap``). The reporters are
   the values of ``--test-reporter`` and the destinations those of ``--test-reporter-destination`` (``--opt=value``
   or ``--opt value``). ``unread`` when a reporter is not ``tap`` or a destination is not ``stdout``
   (``reporter_not_tap``, ``destination_not_stdout``). Otherwise ``read`` when the unit's ``toolchain`` is
   ``node@<major>...`` with a major of ``NODE_TAP_DEFAULT`` (the majors for which TAP on a stdout that is no
   terminal is measured: see the constant), else ``unknown`` (``node_major_not_measured``).
5. **ESLint** (program word ``eslint`` or ``eslint.js``; reader ``eslint``): ``read`` when the format, the value
   of ``--format`` or ``-f`` (``--format=json``, ``--format json``, ``-f json``; the last one given), is ``json``
   and no element is ``-o``, ``--output-file`` or starts with ``--output-file=``; else ``unread``
   (``eslint_format_not_json``, ``eslint_output_file``).
6. **The field's reader**: ``lint_cmd`` is read by ``runner.lint_record`` (reader ``eslint``), ``test_cmd`` and
   ``affected_test_cmd`` by ``runner.test_results`` (readers ``jest`` and ``tap``). A program of rules 3-5 in a
   field whose reader is another is ``unread`` (``program_not_for_field``).
7. Every other program is ``unknown`` (``program_not_known``): ``npm run`` (the script is the owner's;
   ``profile.fit`` states what it does not judge), mocha, vitest, pytest, a shell text.
8. **The answer**: one JSON line ``{ok, units, commands, read, unread, unknown, rows}``, ``rows`` one
   ``{target, unit_id, field, verdict, reader, why}`` per command in the order of the target directories' names,
   the units and ``FIELDS``. ``ok`` only when every command is ``read`` and there is at least one. Exit 0 when
   ok, 1 when not, 2 when ``DIR`` holds no ``<id>/units.json`` or one is not ``{"units": [objects]}``
   (``{"ok": false, "reason"}``).

Out of scope, stated: this is a reading of the command's text, not a run. ``read`` says the command asks its
program for the format the reader reads; it does not say the program is installed, starts, finds a test, or that
a configuration file does not change the output (jest's ``json`` and ``outputFile`` set in its config, a custom
ESLint formatter named ``json``, ``NODE_OPTIONS``, a reporter set by a ``--test`` config of a later node). The
shape of each program's document is the reader's own knowledge (``runner.test_results``, ``runner.lint_record``)
and is not repeated here; rule 4's fact is bound to the reader by a capture
(``tests/capture_node_reporters.py``). ``unknown`` is unknown: the first run decides, as before this tool. The
kept test asks ``ok`` of this tree's ``targets/``, so a recipe whose command is ``unknown`` is decided (a rule
added here with its evidence, or the command changed) before it reaches ``main``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from profile import nx as X  # noqa: E402

READ, UNREAD, UNKNOWN = "read", "unread", "unknown"
JEST, TAP, ESLINT = "jest", "tap", "eslint"
FIELDS = ("lint_cmd", "test_cmd", "affected_test_cmd")
READERS = {"lint_cmd": (ESLINT,), "test_cmd": (JEST, TAP), "affected_test_cmd": (JEST, TAP)}
# node majors whose ``--test`` writes TAP to a stdout that is no terminal when no reporter is named.
# 20: the toy's recipe (node@20.11.0) in the live loop, its tests read by runner.test_results (run 44862981944,
# kos: toy base verified, bad-test tests_red). 22: tests/fixtures/node-test-reporters.json (captured on 22.23.4).
NODE_TAP_DEFAULT = (20, 22)
ENV = ("env", "/usr/bin/env")
SH = ("sh", "/bin/sh")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
TOOLCHAIN = re.compile(r"node@(\d+)(?:\.|\Z)")
TARGETS = os.path.join(ROOT, "targets")


class Unreadable(Exception):
    """The targets directory or a units file cannot be read; the message is the reason."""


def program(cmd: object) -> tuple[list[str] | None, str]:
    """``(the command from its program on, "")``, or ``(None, why)`` (rule 1)."""
    if not (isinstance(cmd, list) and cmd and all(isinstance(a, str) for a in cmd)):
        return None, "not_a_command"
    rest = list(cmd)
    while rest:
        if rest[0] in ENV:
            rest = rest[1:]
            while rest and ASSIGNMENT.match(rest[0]):
                rest = rest[1:]
            if rest and rest[0].startswith("-"):
                return None, "wrapper_not_read"
        elif rest[0] in SH:
            if len(rest) < 4 or rest[1] != "-c" or rest[2] != X.CD_EXEC:
                return None, "wrapper_not_read"
            rest = rest[4:]
        elif rest[0].rsplit("/", 1)[-1] == "node" and len(rest) > 1 and not rest[1].startswith("-"):
            rest = rest[1:]
        else:
            return rest, ""
    return None, "not_a_command"


def _options(rest: list[str]) -> list[str]:
    """The elements after the program and before the first ``--`` (rule 2)."""
    args = rest[1:]
    return args[:args.index("--")] if "--" in args else args


def _values(options: list[str], names: tuple[str, ...]) -> list[str]:
    """The values given to an option of ``names``: ``name=value`` (long names) or ``name value``."""
    out = []
    for i, arg in enumerate(options):
        if arg in names and i + 1 < len(options):
            out.append(options[i + 1])
        else:
            out.extend(arg[len(n) + 1:] for n in names if n.startswith("--") and arg.startswith(n + "="))
    return out


def _given(options: list[str], names: tuple[str, ...]) -> bool:
    return any(a in names or any(n.startswith("--") and a.startswith(n + "=") for n in names) for a in options)


def _jest(options: list[str], toolchain: object) -> tuple[str, str]:
    if _given(options, ("--outputFile",)):
        return UNREAD, "jest_output_file"
    return (READ, "") if X.JEST_JSON in options else (UNREAD, "jest_without_json")


def _node_test(options: list[str], toolchain: object) -> tuple[str, str]:
    if any(v != "tap" for v in _values(options, ("--test-reporter",))):
        return UNREAD, "reporter_not_tap"
    if any(v != "stdout" for v in _values(options, ("--test-reporter-destination",))):
        return UNREAD, "destination_not_stdout"
    major = TOOLCHAIN.match(toolchain) if isinstance(toolchain, str) else None
    if major is None or int(major.group(1)) not in NODE_TAP_DEFAULT:
        return UNKNOWN, "node_major_not_measured"
    return READ, ""


def _eslint(options: list[str], toolchain: object) -> tuple[str, str]:
    if _given(options, ("-o", "--output-file")):
        return UNREAD, "eslint_output_file"
    formats = _values(options, ("--format", "-f"))
    return (READ, "") if formats and formats[-1] == "json" else (UNREAD, "eslint_format_not_json")


def _known(rest: list[str]) -> tuple[str, object] | None:
    """``(reader, its rule)`` of the program of ``rest``, or ``None`` (rules 3-5 and 7)."""
    word = rest[0].rsplit("/", 1)[-1]
    if word in ("jest", "jest.js"):
        return JEST, _jest
    if word in ("eslint", "eslint.js"):
        return ESLINT, _eslint
    if word == "node" and "--test" in _options(rest):
        return TAP, _node_test
    return None


def judge(field: str, cmd: object, toolchain: object = None) -> dict:
    """``{verdict, reader, why}`` of one recipe command (rules 1-7)."""
    rest, why = program(cmd)
    if rest is None:
        return {"verdict": UNKNOWN, "reader": None, "why": why}
    known = _known(rest)
    if known is None:
        return {"verdict": UNKNOWN, "reader": None, "why": "program_not_known"}
    reader, rule = known
    if reader not in READERS[field]:
        return {"verdict": UNREAD, "reader": reader, "why": "program_not_for_field"}
    verdict, why = rule(_options(rest), toolchain)
    return {"verdict": verdict, "reader": reader, "why": why}


def units_of(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, RecursionError):
        raise Unreadable("units_unreadable:%s" % os.path.basename(os.path.dirname(path))) from None
    units = doc.get("units") if isinstance(doc, dict) else None
    if not (isinstance(units, list) and all(isinstance(u, dict) for u in units)):
        raise Unreadable("units_not_a_list:%s" % os.path.basename(os.path.dirname(path)))
    return units


def survey(targets: str = TARGETS) -> dict:
    """The answer of rule 8 over ``targets``."""
    try:
        names = sorted(n for n in os.listdir(targets) if os.path.isfile(os.path.join(targets, n, "units.json")))
    except OSError:
        raise Unreadable("targets_unreadable") from None
    if not names:
        raise Unreadable("no_units_file")
    rows, units = [], 0
    for name in names:
        for unit in units_of(os.path.join(targets, name, "units.json")):
            units += 1
            for field in FIELDS:
                rows.append(dict({"target": name, "unit_id": unit.get("unit_id"), "field": field},
                                 **judge(field, unit.get(field), unit.get("toolchain"))))
    counts = {v: sum(r["verdict"] == v for r in rows) for v in (READ, UNREAD, UNKNOWN)}
    return dict({"ok": bool(rows) and counts[READ] == len(rows), "units": units, "commands": len(rows)}, **counts,
                rows=rows)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Whether each recipe command's output has a reader (see the docstring).")
    parser.add_argument("--targets", default=TARGETS)
    args = parser.parse_args(argv)
    try:
        answer = survey(args.targets)
    except Unreadable as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(answer, sort_keys=True))
    return 0 if answer["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
