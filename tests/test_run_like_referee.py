"""``tests/run_like_referee.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source). No git is needed: the file list is read from a fake ``git`` that records its arguments. Run from the
brain's root."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import run_like_referee as R  # noqa: E402

FAKE_GIT = """#!%s
import json, sys
with open(%r, "w") as f:
    json.dump(sys.argv[1:], f)
sys.stdout.write(%r)
sys.exit(%d)
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-like-referee-")
        self.addCleanup(R.remove, self.tmp)
        self.root = os.path.join(self.tmp, "root")
        os.mkdir(self.root)
        self.work = os.path.join(self.tmp, "work")
        os.mkdir(self.work)
        saved = tempfile.tempdir
        tempfile.tempdir = self.work
        self.addCleanup(setattr, tempfile, "tempdir", saved)

    def put(self, name: str, text: str = "x\n", mode: int = 0o644) -> str:
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        os.chmod(path, mode)
        return name

    def run_cmds(self, *cmds: str, names: list[str] | None = None, jobs: int = 1, timeout: float = 60.0):
        lines: list[str] = []
        tests = [{"id": "T%d" % n, "cmd": c} for n, c in enumerate(cmds)]
        summary = R.run(self.root, tests, names if names is not None else [self.put("a.txt")], jobs, timeout,
                        emit=lines.append)
        return [json.loads(l) for l in lines], summary


class Files(Base):
    def git(self, out: str, code: int = 0) -> str:
        path = os.path.join(self.tmp, "git")
        with open(path, "w") as f:
            f.write(FAKE_GIT % (sys.executable, os.path.join(self.tmp, "argv.json"), out, code))
        os.chmod(path, 0o755)
        return path

    def test_what_git_add_all_would_commit_present_in_the_work_tree(self):
        self.put("b/c.py")
        self.put("a.txt")
        os.symlink("gone", os.path.join(self.root, "link"))
        got = R.files(self.root, self.git("b/c.py\0deleted.txt\0a.txt\0link\0a.txt\0"))
        self.assertEqual(got, ["a.txt", "b/c.py", "link"])
        with open(os.path.join(self.tmp, "argv.json")) as f:
            self.assertEqual(json.load(f), ["-C", self.root, "ls-files", "-z", "--cached", "--others",
                                            "--exclude-standard"])

    def test_no_git_and_a_failing_git_are_unreadable(self):
        with self.assertRaisesRegex(R.Unreadable, "^git_unavailable$"):
            R.files(self.root, os.path.join(self.tmp, "no-such-git"))
        with self.assertRaisesRegex(R.Unreadable, "^ls_files_failed:128$"):
            R.files(self.root, self.git("", 128))


class Manifest(Base):
    def write(self, doc) -> None:
        with open(os.path.join(self.root, "snowball-tests.json"), "w") as f:
            f.write(doc if isinstance(doc, str) else json.dumps(doc))

    def test_the_brains_manifest_reads(self):
        tests = R.manifest(ROOT)
        self.assertTrue(tests)
        self.assertTrue(all(set(t) == {"id", "cmd"} for t in tests))

    def test_only_selects_and_an_unknown_id_is_unreadable(self):
        self.write({"tests": [{"id": "T1", "cmd": "a", "stage": 0}, {"id": "T2", "cmd": "b", "stage": 0}]})
        self.assertEqual(R.manifest(self.root, ["T2"]), [{"id": "T2", "cmd": "b"}])
        with self.assertRaisesRegex(R.Unreadable, "^test_unknown:T9$"):
            R.manifest(self.root, ["T2", "T9"])

    def test_unreadable_manifests(self):
        for doc in ("{", {"tests": [{"cmd": "a"}]}, {"x": []}, []):
            self.write(doc)
            with self.assertRaisesRegex(R.Unreadable, "^manifest_unreadable:"):
                R.manifest(self.root)


class Tree(Base):
    def test_a_checkouts_modes_and_links_as_links(self):
        # A umask that masks mkdir's 0o755 to 0o700: the modes are set, not left to the umask.
        self.addCleanup(os.umask, os.umask(0o077))
        names = [self.put("d/e/f.txt", mode=0o600), self.put("run.sh", mode=0o700)]
        os.symlink("d/e/f.txt", os.path.join(self.root, "ln"))
        dst = os.path.join(self.tmp, "copy")
        R.stage(self.root, names + ["ln"], dst)
        mode = lambda p: stat.S_IMODE(os.lstat(os.path.join(dst, p)).st_mode)  # noqa: E731
        self.assertEqual([mode(p) for p in ("", "d", "d/e", "d/e/f.txt", "run.sh")],
                         [0o755, 0o755, 0o755, 0o644, 0o755])
        self.assertEqual(os.readlink(os.path.join(dst, "ln")), "d/e/f.txt")

    def test_only_the_named_files_are_copied(self):
        names = [self.put("kept.txt")]
        self.put("ignored/__init__.py")
        out, summary = self.run_cmds("python -c \"import os,sys; sys.exit(sorted(os.listdir('.')) != ['kept.txt'])\"",
                                     names=names)
        self.assertTrue(out[0]["ok"], out)

    def test_a_copy_a_command_makes_of_the_tree_is_its_own(self):
        """057ad34's successor class: a test copying fixtures out of the tree must be able to change the copy."""
        names = [self.put("fx/a/b.txt")]
        cmd = ("python -c \"import os,shutil; d=os.path.join(os.environ['TMPDIR'],'c'); shutil.copytree('fx',d); "
               "os.remove(os.path.join(d,'a','b.txt')); shutil.rmtree(d)\"")
        out, _ = self.run_cmds(cmd, names=names)
        self.assertTrue(out[0]["ok"], out)

    def test_each_command_has_its_own_copy(self):
        out, _ = self.run_cmds("python -c \"open('new.txt','w').write('1')\"",
                               "python -c \"import os,sys; sys.exit(os.path.exists('new.txt'))\"")
        self.assertEqual([(r["ok"], r["wrote"]) for r in out], [(False, ["new.txt"]), (True, [])])


class Writes(Base):
    def setUp(self):
        super().setUp()
        self.names = [self.put("a.txt"), self.put("d/b.txt")]
        os.symlink("a.txt", os.path.join(self.root, "ln"))
        self.names.append("ln")

    def check(self, code: str, wrote: list[str]):
        out, summary = self.run_cmds("python -c %s" % json.dumps(code), names=self.names)
        self.assertEqual((out[0]["exit"], out[0]["wrote"], out[0]["ok"]), (0, wrote, not wrote), out)
        self.assertEqual(summary["ok"], not wrote)

    def test_every_kind_of_write_to_the_tree_is_listed(self):
        self.check("open('n.txt','w').close()", ["n.txt"])
        self.check("import os; os.mkdir('nd')", ["nd"])
        self.check("open('d/b.txt','a').write('y')", ["d/b.txt"])
        self.check("import os; os.remove('a.txt')", ["a.txt"])
        self.check("import os; os.chmod('a.txt', 0o755)", ["a.txt"])
        self.check("import os; os.remove('ln'); os.symlink('d/b.txt', 'ln')", ["ln"])
        self.check("import os; os.remove('ln'); open('ln','w').write('x\\n')", ["ln"])
        self.check("import shutil; shutil.rmtree('d')", ["d", "d/b.txt"])

    def test_no_write_and_writes_out_of_the_tree_are_not_listed(self):
        self.check("open('a.txt').read()", [])
        self.check("import os; open(os.path.join(os.environ['TMPDIR'], 'x'), 'w').write('1')", [])
        self.check("import os; os.utime('a.txt', (1, 1))", [])

    def test_pythons_cache_is_not_compared(self):
        self.check("import os; os.makedirs('d/__pycache__'); open('d/__pycache__/m.pyc','w').write('1')", [])
        self.check("import os; os.makedirs('__pycache__/x')", [])


class Environment(Base):
    def test_only_four_variables_and_path_holds_only_python(self):
        os.environ["LIKE_REFEREE_LEAK"] = "1"
        self.addCleanup(os.environ.pop, "LIKE_REFEREE_LEAK")
        dump = os.path.join(self.tmp, "env.json")
        out, _ = self.run_cmds("python -c \"import json,os; e=dict(os.environ); e['ls']=sorted(os.listdir(e['PATH'])); "
                               "json.dump(e, open(%r,'w'))\"" % dump)
        self.assertTrue(out[0]["ok"], out)
        with open(dump) as f:
            env = json.load(f)
        listed = env.pop("ls")
        # PWD is the shell's, LC_CTYPE python's own (C locale coercion), not this process's.
        self.assertLessEqual(set(env), {"PATH", "HOME", "TMPDIR", "LANG", "PWD", "LC_CTYPE"})
        self.assertEqual((env["HOME"], env["LANG"]), ("/nonexistent", "C.UTF-8"))
        self.assertEqual(listed, ["python", "python3"])
        self.assertTrue(env["TMPDIR"].startswith(self.work))

    def test_a_program_other_than_python_is_not_found(self):
        out, _ = self.run_cmds("python -c pass && python3 -c pass", "command -v ls", "git --version")
        self.assertEqual([r["ok"] for r in out], [True, False, False])

    def test_stdin_is_dev_null_not_the_runners(self):
        # The runner's fd 0 becomes a pipe holding bytes: an inherited stdin would read them.
        r, w = os.pipe()
        os.write(w, b"leak")
        os.close(w)
        saved = os.dup(0)
        self.addCleanup(os.close, saved)
        os.dup2(r, 0)
        os.close(r)
        self.addCleanup(os.dup2, saved, 0)
        null = os.stat(os.devnull).st_rdev
        out, _ = self.run_cmds("python -c \"import os,sys; sys.exit(sys.stdin.read() != '' or "
                               "os.fstat(0).st_rdev != %d)\"" % null)
        self.assertTrue(out[0]["ok"], out)

    def test_the_command_runs_from_the_root_under_sh(self):
        names = [self.put("sub/m.txt")]
        out, _ = self.run_cmds("cd sub && python -c \"open('m.txt').read()\"", names=names)
        self.assertTrue(out[0]["ok"], out)


class Results(Base):
    def test_exit_tail_and_order(self):
        out, summary = self.run_cmds("python -c \"import time; time.sleep(0.3); print('a'*700)\"",
                                     "python -c \"import sys; sys.stderr.write('boom'); sys.exit(3)\"",
                                     "python -c pass", jobs=3)
        self.assertEqual([r["id"] for r in out], ["T0", "T1", "T2"])
        self.assertEqual([(r["exit"], r["ok"]) for r in out], [(0, True), (3, False), (0, True)])
        self.assertEqual(out[0]["tail"], "a" * 599 + "\n")
        self.assertEqual(out[1]["tail"], "boom")
        self.assertEqual(summary, {"ok": False, "tests": 3, "failed": ["T1"], "network": "not_isolated"})

    def test_a_command_over_the_limit_is_timed_out(self):
        out, summary = self.run_cmds("python -c \"import time; time.sleep(30)\"", timeout=0.5)
        self.assertEqual((out[0]["exit"], out[0]["timed_out"], out[0]["ok"]), (None, True, False))
        self.assertLess(out[0]["duration_ms"], 10000)

    def test_a_commands_copy_is_removed_when_it_ends(self):
        path = R.bindir(os.path.join(self.tmp, "bin"))
        r = R.run_one({"id": "T0", "cmd": "python -c \"import os; os.chmod('.', 0o555)\""}, self.root,
                      [self.put("a.txt")], path, self.work, 60.0)
        self.assertEqual((r["exit"], os.listdir(self.work)), (0, []))

    def test_nothing_is_left_behind(self):
        cmd = ("python -c \"import os; d=os.path.join(os.environ['TMPDIR'],'ro'); os.mkdir(d); "
               "open(os.path.join(d,'f'),'w').close(); os.chmod(d, 0o500); os.chmod('.', 0o555)\"")
        self.run_cmds(cmd)
        self.assertEqual(os.listdir(self.work), [])


class Main(Base):
    def setUp(self):
        super().setUp()
        self.git = os.path.join(self.tmp, "git")
        with open(self.git, "w") as f:
            f.write(FAKE_GIT % (sys.executable, os.path.join(self.tmp, "argv.json"), "snowball-tests.json\0", 0))
        os.chmod(self.git, 0o755)
        with open(os.path.join(self.root, "snowball-tests.json"), "w") as f:
            json.dump({"tests": [{"id": "T1", "cmd": "python -c pass", "stage": 0},
                                 {"id": "T2", "cmd": "python -c \"raise SystemExit(1)\"", "stage": 0}]}, f)

    def main(self, *argv: str) -> tuple[int, list[dict]]:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = R.main(list(argv), root=self.root, git=self.git)
        return code, [json.loads(l) for l in buf.getvalue().splitlines()]

    def test_exit_codes(self):
        self.assertEqual(self.main("--only", "T1")[0], 0)
        code, lines = self.main("-j", "2")
        self.assertEqual((code, lines[-1]["failed"]), (1, ["T2"]))
        self.assertEqual(self.main("--only", "T7"), (2, [{"ok": False, "reason": "test_unknown:T7"}]))
        self.git = os.path.join(self.tmp, "absent")
        self.assertEqual(self.main(), (2, [{"ok": False, "reason": "git_unavailable"}]))


if __name__ == "__main__":
    unittest.main()
