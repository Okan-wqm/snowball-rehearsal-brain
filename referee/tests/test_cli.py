"""``cli.run``, the one process boundary of every referee command (run with test 38: a fault must never read as
a verdict, and ``gate.secrets``' exit 1 is "match").

- Boundary: each rule of ``cli``'s docstring in-process, with fake ``main`` functions: a verdict line written
  before a fault is dropped (rule 1); a return that is not 0, 1 or 2 (``True``, ``None``, 3, "1") is a fault
  (rule 2); an exception and ``SystemExit`` are faults, ``KeyboardInterrupt`` is not caught (rule 3); stderr names
  the type and never the message (rule 5); the fault line is a dict or a function of argv, and a failing
  function gives ``GENERIC_LINE``.
- Register: the commands are found by scanning ``referee/`` for a ``__main__`` block (not a hand-kept list); each
  block is exactly ``sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))``, and each module's ``FAULT_LINE`` gives a
  JSON object for every first argument its usage names and for none.
- Process: every command, started the way the referee starts it, exits 2 when stdout is closed or a broken pipe
  (before this boundary: 20 of 22 exited 1 with stdout closed, and most 120 on a broken pipe); and ``gate.secrets
  scan`` on a clean file and on a file with a fake token exits 0 and 1 with a working stdout and 2 with either
  broken stdout, so the exit carries the verdict only when the verdict line reached its reader.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

import cli  # noqa: E402

ENTRY = "sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))"


def commands() -> dict[str, str]:
    """Module name -> path of every file under referee/ (tests excluded) with a ``__main__`` block."""
    found = {}
    for top, dirs, files in os.walk(REFEREE):
        dirs[:] = sorted(d for d in dirs if d not in ("tests", "__pycache__"))
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(top, name)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            if any(_is_main_block(node) for node in tree.body):
                rel = os.path.relpath(path, REFEREE)[:-3]
                found[rel.replace(os.sep, ".")] = path
    return found


def _is_main_block(node: ast.stmt) -> bool:
    return (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__")


def entry(path: str) -> list[list[str]]:
    """The statements of each ``__main__`` block of ``path``, unparsed."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    return [[ast.unparse(stmt) for stmt in node.body] for node in tree.body if _is_main_block(node)]


def run_boundary(main, argv=(), fault_line=None):
    """``cli.run`` in-process with stdout and stderr captured: (exit, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(main, list(argv), {"ok": False} if fault_line is None else fault_line)
    return code, out.getvalue(), err.getvalue()


def start(module: str, argv: list[str], stdout: str) -> subprocess.CompletedProcess:
    """Run ``python -m module argv`` from referee/ with stdin empty and stdout 'closed', 'broken' (a pipe whose
    reader is gone) or 'pipe' (read normally)."""
    cmd = [sys.executable, "-m", module, *argv]
    common = dict(cwd=REFEREE, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    if stdout == "pipe":
        return subprocess.run(cmd, stdout=subprocess.PIPE, **common)
    if stdout == "closed":
        return subprocess.run(cmd, preexec_fn=lambda: os.close(1), **common)
    read, write = os.pipe()
    os.close(read)
    try:
        return subprocess.run(cmd, stdout=write, **common)
    finally:
        os.close(write)


class Boundary(unittest.TestCase):
    def test_a_good_main_passes_its_code_and_output_through(self):
        for code in (0, 1, 2):
            def main(argv, code=code):
                sys.stdout.write('{"v": %d}\n' % code)
                return code
            self.assertEqual(run_boundary(main), (code, '{"v": %d}\n' % code, ""))

    def test_a_verdict_line_written_before_a_fault_is_dropped(self):
        def main(argv):
            sys.stdout.write('{"clean": true}\n')
            raise ValueError("late")
        code, out, err = run_boundary(main, fault_line={"clean": False})
        self.assertEqual((code, out), (2, '{"clean": false}\n'))
        self.assertEqual(err, "internal error: ValueError\n")

    def test_a_return_that_is_not_0_1_or_2_is_a_fault(self):
        for bad in (True, False, None, 3, -1, "1", 1.0):
            code, out, err = run_boundary(lambda argv, bad=bad: bad)
            self.assertEqual((code, out), (2, '{"ok": false}\n'), bad)
            self.assertEqual(err, "internal error: exit %r\n" % (bad,))

    def test_exceptions_and_system_exit_are_faults(self):
        def recurse(argv):
            return recurse(argv)
        cases = [(recurse, "RecursionError"), (lambda argv: {}["k"], "KeyError"),
                 (lambda argv: sys.exit(1), "SystemExit"), (lambda argv: sys.exit(0), "SystemExit")]
        for main, name in cases:
            code, out, err = run_boundary(main)
            self.assertEqual((code, out, err), (2, '{"ok": false}\n', "internal error: %s\n" % name))

    def test_keyboard_interrupt_is_not_caught(self):
        def main(argv):
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            run_boundary(main)

    def test_stderr_names_the_type_never_the_message(self):
        marker = "MESSAGE-" + "TEXT-OF-THE-INPUT"
        def main(argv):
            raise RuntimeError(marker)
        code, out, err = run_boundary(main)
        self.assertEqual(code, 2)
        self.assertNotIn(marker, out + err)
        self.assertEqual(err, "internal error: RuntimeError\n")

    def test_the_fault_line_is_a_function_of_argv_and_a_failing_one_gives_the_generic_line(self):
        def main(argv):
            raise ValueError
        self.assertEqual(run_boundary(main, ["decide", "x"], lambda argv: {"first": argv[0]})[1], '{"first": "decide"}\n')
        self.assertEqual(run_boundary(main, [], lambda argv: {"first": argv[0]})[1],
                         json.dumps(cli.GENERIC_LINE, sort_keys=True) + "\n")

    def test_a_stdout_that_fails_after_main_returned_is_a_fault(self):
        class Broken(io.StringIO):
            def write(self, text):
                raise BrokenPipeError
        err = io.StringIO()
        with contextlib.redirect_stdout(Broken()), contextlib.redirect_stderr(err):
            code = cli.run(lambda argv: 0, [], {"ok": False})
        self.assertEqual((code, err.getvalue()), (2, "internal error: stdout\n"))


class Register(unittest.TestCase):
    def test_every_command_enters_through_the_boundary(self):
        found = commands()
        self.assertGreaterEqual(len(found), 22, sorted(found))
        for module, path in found.items():
            self.assertEqual(entry(path), [[ENTRY]], module)

    def test_the_register_sees_a_command_that_bypasses_the_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bypass.py")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('import sys\n\ndef main(argv):\n    return 0\n\nif __name__ == "__main__":\n'
                         '    sys.exit(main(sys.argv[1:]))\n')
            self.assertEqual(entry(path), [["sys.exit(main(sys.argv[1:]))"]])
            self.assertNotEqual(entry(path), [[ENTRY]])

    def test_every_fault_line_is_a_json_object_for_any_argv(self):
        for module in commands():
            line = importlib.import_module(module).FAULT_LINE
            for argv in ([], ["argv"], ["check"], ["decide"], ["judge", "a", "b"], ["commit", "a", "b"], ["verify"],
                         ["root"], ["scan"], ["run", "x"]):
                got = line(argv) if callable(line) else line
                self.assertIsInstance(got, dict, (module, argv))
                self.assertEqual(json.loads(json.dumps(got)), got, (module, argv))


class Process(unittest.TestCase):
    def test_every_command_exits_2_when_stdout_is_closed_or_broken(self):
        for module in commands():
            for stdout in ("closed", "broken"):
                proc = start(module, [], stdout)
                self.assertEqual(proc.returncode, 2, (module, stdout, proc.stderr[-300:]))
                self.assertNotIn(b"Traceback", proc.stderr, (module, stdout))

    def test_secrets_verdicts_reach_the_reader_or_the_exit_is_2(self):
        token = "gh" + "p_" + "Q7" * 18
        with tempfile.TemporaryDirectory() as tmp:
            clean, dirty = os.path.join(tmp, "clean.diff"), os.path.join(tmp, "dirty.diff")
            with open(clean, "w", encoding="utf-8") as fh:
                fh.write("+nothing here\n")
            with open(dirty, "w", encoding="utf-8") as fh:
                fh.write("+x = '%s'\n" % token)
            for path, verdict, line in ((clean, 0, {"clean": True, "lines": []}), (dirty, 1, {"clean": False, "lines": [1]})):
                proc = start("gate.secrets", ["scan", "diff", path], "pipe")
                self.assertEqual((proc.returncode, json.loads(proc.stdout)), (verdict, line))
                for stdout in ("closed", "broken"):
                    proc = start("gate.secrets", ["scan", "diff", path], stdout)
                    self.assertEqual((proc.returncode, proc.stderr), (2, b"internal error: stdout\n"), (path, stdout))


if __name__ == "__main__":
    unittest.main()
