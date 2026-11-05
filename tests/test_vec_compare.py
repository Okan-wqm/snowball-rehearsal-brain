"""``tests/vec_compare.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source). No git is needed (the referee's sandbox has none, f396): a fake ``git`` answers ``ls-files`` with the work
tree's files and ``archive`` with a tar of a directory standing for the ``before`` commit. The commands run are
small python modules under the trees' ``referee/``, plus the real ``runner.contained`` for the one normalisation.
Run from the brain's root."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import run_like_referee as RLR  # noqa: E402
import vec_compare as V  # noqa: E402

FAKE_GIT = """#!%s
import io, os, sys, tarfile
args = sys.argv[1:]
if args[2] == "ls-files":
    root = args[1]
    names = []
    for top, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        names += [os.path.relpath(os.path.join(top, n), root) for n in files]
    sys.stdout.write("\\0".join(names) + "\\0")
elif args[2] == "archive" and args[4] == "REV^{commit}":
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name in sorted(os.listdir(%r)):
            tar.add(os.path.join(%r, name), arcname=name)
    sys.stdout.buffer.write(buf.getvalue())
else:
    sys.stderr.write("fatal: not a valid object name\\n")
    sys.exit(128)
"""

ECHO = """import sys
print("out", sys.argv[1:], sys.stdin.read())
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-vec-compare-")
        self.addCleanup(RLR.remove, self.tmp)
        self.root = os.path.join(self.tmp, "root")
        self.before = os.path.join(self.tmp, "before")
        for d in (self.root, self.before):
            os.makedirs(os.path.join(d, "referee"))
        self.git = os.path.join(self.tmp, "git")
        with open(self.git, "w") as f:
            f.write(FAKE_GIT % (sys.executable, self.before, self.before))
        os.chmod(self.git, 0o755)

    def module(self, name: str, text: str, before: bool = True, after: bool = True) -> None:
        for d, on in ((self.before, before), (self.root, after)):
            if on:
                with open(os.path.join(d, "referee", name + ".py"), "w") as f:
                    f.write(text)

    def write_cases(self, *cases: dict) -> str:
        path = os.path.join(self.tmp, "cases.json")
        with open(path, "w") as f:
            json.dump(list(cases), f)
        return path

    def case(self, cid: str, cmd: str, stdin: str = "", changed_cmd: str | None = None, changed_stdin: str = "") -> dict:
        return {"id": cid, "purpose": "p", "cmd": cmd, "stdin": stdin, "fixture": [],
                "changed": {"description": "d", "cmd": changed_cmd or cmd, "stdin": changed_stdin, "fixture": []}}

    def main(self, *cases: dict, extra: list[str] | None = None) -> tuple[int, list[dict]]:
        argv = ["--before", "REV", "--cases", self.write_cases(*cases)] + (extra or [])
        out = subprocess.run([sys.executable, "-c",
                              "import sys; sys.path.insert(0, %r); import vec_compare as V; "
                              "sys.exit(V.main(sys.argv[1:], root=%r, git=%r))" % (os.path.join(ROOT, "tests"),
                                                                                  self.root, self.git), *argv],
                             capture_output=True, text=True, timeout=120)
        return out.returncode, [json.loads(l) for l in out.stdout.splitlines()]


class Compare(Base):
    def test_equal_trees_exit_0_and_every_side_is_run(self):
        self.module("echo", ECHO)
        code, lines = self.main(self.case("a", "python -m echo 1", changed_cmd="python -m echo 2"),
                                self.case("b", "python -m echo 3"))
        self.assertEqual(code, 0)
        self.assertEqual(lines, [{"ok": True, "before": "REV", "cases": 2, "runs": 4, "differ": []}])

    def test_a_change_in_the_work_tree_is_named_by_case_side_and_field(self):
        self.module("echo", ECHO)
        self.module("echo", ECHO.replace('"out"', '"out" if sys.argv[1] != "2" else "changed"'), before=False)
        code, lines = self.main(self.case("a", "python -m echo 1", changed_cmd="python -m echo 2"))
        self.assertEqual(code, 1)
        diff, summary = lines
        self.assertEqual((diff["id"], diff["side"], diff["fields"]), ("a", "changed", ["stdout"]))
        self.assertEqual(diff["before"]["stdout"], "out ['2'] \n")
        self.assertEqual(diff["after"]["stdout"], "changed ['2'] \n")
        self.assertEqual(summary["differ"], ["a/changed"])
        self.assertFalse(summary["ok"])

    def test_exit_and_stderr_are_compared_apart_from_stdout(self):
        self.module("fail", "import sys\nsys.stderr.write('bad\\n')\nsys.exit(3)\n")
        self.module("fail", "import sys\nsys.stderr.write('worse\\n')\nsys.exit(4)\n", before=False)
        code, lines = self.main(self.case("f", "python -m fail"))
        self.assertEqual(code, 1)
        self.assertEqual(lines[0]["fields"], ["exit", "stderr"])
        self.assertEqual((lines[0]["before"]["exit"], lines[0]["after"]["exit"]), (3, 4))

    def test_stdin_is_given_to_the_command_per_side(self):
        self.module("echo", ECHO)
        self.module("echo", ECHO.replace("sys.stdin.read()", "sys.stdin.read().upper()"), before=False)
        code, lines = self.main(self.case("s", "python -m echo", stdin="", changed_stdin="abc"))
        self.assertEqual(code, 1)
        self.assertEqual(lines[0]["side"], "changed")
        self.assertEqual((lines[0]["before"]["stdout"], lines[0]["after"]["stdout"]), ("out [] abc\n", "out [] ABC\n"))

    def test_the_command_runs_from_referee_with_the_runners_environment(self):
        self.module("where", "import os, sys\nprint(os.getcwd().endswith('/referee'), 'VEC_COMPARE_LEAK' in os.environ, "
                    "os.environ['HOME'], os.environ['LANG'], sorted(os.listdir(os.environ['PATH'])), "
                    "os.path.isdir(os.environ['TMPDIR']))\n")
        os.environ["VEC_COMPARE_LEAK"] = "1"
        self.addCleanup(os.environ.pop, "VEC_COMPARE_LEAK")
        runs = V.cases(self.write_cases(self.case("w", "python -m where")))
        work = tempfile.mkdtemp(dir=self.tmp)
        path = RLR.bindir(os.path.join(work, "bin"))
        shutil.copytree(self.root, os.path.join(work, "t"))
        out = V.run_one(runs[0], os.path.join(work, "t"), path, work, 30)
        self.assertEqual(out["stdout"], "True False /nonexistent C.UTF-8 ['python', 'python3'] True\n")

    def test_a_timeout_is_reported_and_compared(self):
        self.module("slow", "import time\ntime.sleep(0)\n")
        self.module("slow", "import time\ntime.sleep(30)\n", before=False)
        code, lines = self.main(self.case("t", "python -m slow"), extra=["--timeout", "2"])
        self.assertEqual(code, 1)
        self.assertEqual(lines[0]["fields"], ["exit", "timed_out"])
        self.assertEqual((lines[0]["after"]["exit"], lines[0]["after"]["timed_out"]), (None, True))

    def test_jobs_keep_the_cases_order(self):
        self.module("echo", ECHO)
        self.module("echo", "import sys\nprint(sys.argv[1:])\n", before=False)
        cases = [self.case("c%d" % n, "python -m echo %d" % n) for n in range(6)]
        code, lines = self.main(*cases, extra=["-j", "4"])
        self.assertEqual(code, 1)
        self.assertEqual(lines[-1]["differ"], ["c%d/%s" % (n, s) for n in range(6) for s in ("base", "changed")])


class Normalise(Base):
    def test_a_random_container_name_is_equal_and_nothing_else_is_rewritten(self):
        self.module("rnd", "import secrets\nprint('--name snowball-' + secrets.token_hex(16), 'snowball-' + 'ab' * 15)\n")
        code, lines = self.main(self.case("r", "python -m rnd"))
        self.assertEqual(code, 0, lines)
        self.assertEqual(V.normalise("x snowball-%s y" % ("0f" * 16)), "x snowball-<name> y")
        for kept in ("snowball-%s" % ("0f" * 15), "snowball-%s" % ("0f" * 17), "snowball-%s" % ("0F" * 16),
                     "snowball-run-%s" % ("0f" * 16)):
            self.assertEqual(V.normalise(kept), kept)

    def test_the_real_contained_argv_varies_only_in_what_is_normalised(self):
        """The one normalisation is bound to the code that makes the name: two runs of ``runner.contained argv``
        on a /vec-like request differ raw and are equal normalised."""
        req = json.dumps({"image": "docker.io/library/node@sha256:" + "0" * 64, "cmd": ["npm", "test"],
                          "uid": 1001, "worktree": "/runs/r-0001/work", "outdir": "/runs/r-0001/out",
                          "artefacts": ["/runs/r-0001/deps"], "env": {"LANG": "C.UTF-8"}, "services": [],
                          "operating": {"container_mem_bytes": {"value": 536870912,
                                                                "band": [268435456, 1073741824]}}})
        outs = [subprocess.run([sys.executable, "-m", "runner.contained", "argv"], input=req, text=True,
                               capture_output=True, cwd=os.path.join(ROOT, "referee"), timeout=60) for _ in range(2)]
        self.assertTrue(all(o.returncode == 0 for o in outs), [o.stdout + o.stderr for o in outs])
        self.assertNotEqual(outs[0].stdout, outs[1].stdout)
        self.assertEqual(V.normalise(outs[0].stdout), V.normalise(outs[1].stdout))
        self.assertIn("snowball-<name>", V.normalise(outs[0].stdout))


class Unreadable(Base):
    def test_unreadable_inputs_exit_2(self):
        self.module("echo", ECHO)
        good = self.case("a", "python -m echo")
        self.assertEqual(self.main(good, extra=["--only", "zz"]), (2, [{"ok": False, "reason": "case_unknown:zz"}]))
        code, lines = self.main(good, extra=["--before", "NOPE"])
        self.assertEqual((code, lines), (2, [{"ok": False, "reason": "revision_unreadable:NOPE"}]))
        bad = dict(good)
        del bad["changed"]
        self.assertEqual(self.main(bad), (2, [{"ok": False, "reason": "cases_unreadable:KeyError"}]))
        bad = self.case("a", "python -m echo")
        bad["stdin"] = None
        self.assertEqual(self.main(bad), (2, [{"ok": False, "reason": "cases_unreadable:TypeError"}]))

    def test_only_keeps_the_named_cases(self):
        self.module("echo", ECHO)
        code, lines = self.main(self.case("a", "python -m echo"), self.case("b", "python -m echo"),
                                extra=["--only", "b"])
        self.assertEqual((code, lines[-1]["cases"], lines[-1]["runs"]), (0, 1, 2))


if __name__ == "__main__":
    unittest.main()
