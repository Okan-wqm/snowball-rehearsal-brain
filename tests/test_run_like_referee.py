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

    def run_cmds(self, *cmds: str, names: list[str] | None = None, jobs: int = 1, timeout: float = 60.0, **how):
        lines: list[str] = []
        tests = [{"id": "T%d" % n, "cmd": c} for n, c in enumerate(cmds)]
        summary = R.run(self.root, tests, names if names is not None else [self.put("a.txt")], jobs, timeout,
                        emit=lines.append, **how)
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

    def test_an_id_is_no_part_of_the_copys_path(self):
        lines: list[str] = []
        ids = ["T0:referee/tests/test_a*.py", "../../out", "/abs"]
        summary = R.run(self.root, [{"id": i, "cmd": "python -c pass"} for i in ids], [self.put("a.txt")], 1, 60.0,
                        emit=lines.append)
        self.assertEqual((summary["failed"], [json.loads(l)["id"] for l in lines]), ([], ids))
        self.assertEqual((sorted(os.listdir(self.tmp)), os.listdir(self.work)), (["root", "work"], []))


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

    def test_the_summary_names_the_interpreter_the_links_go_to(self):
        dump = os.path.join(self.tmp, "exe.json")
        cmd = ("python -c \"import json,os,sys; json.dump([os.path.realpath(os.path.join(os.environ['PATH'], n)) "
               "for n in ('python', 'python3')] + [sys.executable, os.environ['PATH']], open(%r,'w'))\"" % dump)
        out, summary = self.run_cmds(cmd)
        self.assertTrue(out[0]["ok"], out)
        with open(dump) as f:
            python, python3, executable, path = json.load(f)
        self.assertEqual((python, executable), (python3, os.path.join(path, "python")))
        self.assertIn(summary["python"], ("cold_home", "own", "moved_home"))
        if summary["python"] == "own":
            self.assertEqual(python, os.path.realpath(sys.executable))
        else:
            self.assertTrue(python.startswith(self.work + os.sep), python)

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


FAKE_PYTHON = """#!%s
# A stand-in for a python binary: started as ``<it> -I -c SELF`` it answers from where its own file lies, as a
# python finds its prefix; MODE makes it break one of the things ``interpreter`` and ``cold_home`` check of a
# moved home (``pries``: it opens the closed directory and writes its bytecode all the same).
import json, os, sys
MODE, FIRST, TAG = %r, %r, %r
if sys.argv[1:3] != ["-I", "-c"] or set(os.environ) - {"LC_CTYPE"}:  # LC_CTYPE: python's own locale coercion
    sys.exit(9)
prefix = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
moved = prefix != FIRST
lib = os.path.join(prefix, "lib", "py")
if moved and MODE == "fails":
    sys.exit(1)
if not (moved and MODE == "no_bytecode"):
    try:
        if moved and MODE == "pries":
            os.chmod(os.path.join(lib, "json"), 0o755)
        os.makedirs(os.path.join(lib, "json", "__pycache__"), exist_ok=True)
        open(os.path.join(lib, "json", "__pycache__", "__init__.%%s.pyc" %% TAG), "w").close()
    except OSError:
        pass
said = FIRST if moved and MODE == "old_prefix" else prefix + "/venv" if MODE == "venv" and not moved else prefix
path = [lib, os.path.join(lib, "site"), "/elsewhere"] + (["/more"] if moved and MODE == "other_path" else [])
print(json.dumps([said, said, said, os.path.join(lib, "json", "__init__.py"), path]))
"""


class Interpreter(Base):
    def stdlib(self, name: str = "lib") -> str:
        lib = os.path.join(self.tmp, name)
        os.makedirs(os.path.join(lib, "json"))
        with open(os.path.join(lib, "json", "__init__.py"), "w") as f:
            f.write("")
        return lib

    def bytecode(self, lib: str) -> str:
        return os.path.join(lib, "json", "__pycache__", "__init__.%s.pyc" % sys.implementation.cache_tag)

    def lock(self, path: str) -> None:
        os.chmod(path, 0o555)
        self.addCleanup(os.chmod, path, 0o755)

    def test_cold_is_no_bytecode_and_no_way_to_write_it(self):
        # Not as root: os.access answers for this user, and root can write anywhere.
        lib = self.stdlib()
        self.assertFalse(R.stdlib_cold(lib))                       # no bytecode, but python can write it
        self.lock(os.path.join(lib, "json"))
        self.assertTrue(R.stdlib_cold(lib))                        # no bytecode, no place to write it
        os.chmod(os.path.join(lib, "json"), 0o755)
        os.mkdir(os.path.dirname(self.bytecode(lib)))
        self.lock(os.path.dirname(self.bytecode(lib)))
        self.assertTrue(R.stdlib_cold(lib))                        # the cache directory is there and closed
        os.chmod(os.path.dirname(self.bytecode(lib)), 0o755)
        open(self.bytecode(lib), "w").close()
        self.lock(os.path.dirname(self.bytecode(lib)))
        self.lock(os.path.join(lib, "json"))
        self.assertFalse(R.stdlib_cold(lib))                       # the bytecode is there to load

    def test_mirror_makes_directories_and_links_the_rest(self):
        src, dst = os.path.join(self.tmp, "src"), os.path.join(self.tmp, "dst")
        os.makedirs(os.path.join(src, "pkg", "__pycache__"))
        os.makedirs(os.path.join(src, "__pycache__"))
        for name in ("m.py", os.path.join("pkg", "n.py"), os.path.join("pkg", "__pycache__", "n.pyc")):
            open(os.path.join(src, name), "w").close()
        os.symlink("pkg", os.path.join(src, "alias"))
        R.mirror(src, dst)
        seen = {os.path.relpath(os.path.join(top, n), dst): os.path.islink(os.path.join(top, n))
                for top, dirs, names in os.walk(dst) for n in dirs + names}
        self.assertEqual(seen, {"m.py": True, "pkg": False, os.path.join("pkg", "n.py"): True, "alias": True})
        self.assertEqual(os.readlink(os.path.join(dst, "m.py")), os.path.join(src, "m.py"))
        # a file python writes beside a mirrored module lands in the mirror, not in the source
        os.mkdir(os.path.join(dst, "pkg", "__pycache__"))
        self.assertEqual(sorted(os.listdir(os.path.join(src, "pkg", "__pycache__"))), ["n.pyc"])

    def fake(self, mode: str) -> dict:
        first = os.path.join(self.tmp, "first-" + mode)
        lib = os.path.join(first, "lib", "py")
        os.makedirs(os.path.join(first, "bin"))
        os.makedirs(os.path.join(lib, "json"))
        open(os.path.join(lib, "json", "__init__.py"), "w").close()
        open(os.path.join(first, "lib", "libpython-fake.so"), "w").close()
        open(os.path.join(first, "lib", "other.so"), "w").close()
        exe = os.path.join(first, "bin", "py-fake")
        with open(exe, "w") as f:
            f.write(FAKE_PYTHON % (sys.executable, mode, first, sys.implementation.cache_tag))
        os.chmod(exe, 0o755)
        link = os.path.join(first, "bin", "python")
        os.symlink(exe, link)
        return {"executable": link, "prefix": first, "stdlib": lib, "libdir": os.path.join(first, "lib")}

    def test_a_warm_standard_library_keeps_the_own_interpreter(self):
        py, home = self.fake("good"), os.path.join(self.tmp, "home")
        self.assertEqual(R.interpreter(home, cold=lambda lib: False, python=py), (py["executable"], "own"))
        self.assertFalse(os.path.lexists(home))

    def test_a_cold_one_moves_home_when_the_three_checks_pass(self):
        py, home = self.fake("good"), os.path.join(self.tmp, "home")
        asked = []
        binary, kind = R.interpreter(home, cold=lambda lib: asked.append(lib) or True, python=py)
        self.assertEqual(asked, [py["stdlib"]])
        self.assertEqual((binary, kind), (os.path.join(home, "bin", "py-fake"), "moved_home"))
        self.assertFalse(os.path.islink(binary))                   # the binary is a copy: its place is its prefix
        self.assertTrue(os.access(binary, os.X_OK))
        moved = os.path.join(home, "lib", "py", "json", "__init__.py")
        self.assertEqual(os.readlink(moved), os.path.join(py["stdlib"], "json", "__init__.py"))
        self.assertEqual(sorted(os.listdir(os.path.join(home, "lib"))), ["libpython-fake.so", "py"])
        self.assertEqual(os.readlink(os.path.join(home, "lib", "libpython-fake.so")),
                         os.path.join(py["libdir"], "libpython-fake.so"))

    def test_a_moved_home_failing_a_check_is_removed_and_the_own_one_stays(self):
        for mode in ("old_prefix", "other_path", "no_bytecode", "fails", "venv"):
            with self.subTest(mode=mode):
                py, home = self.fake(mode), os.path.join(self.tmp, "home-" + mode)
                self.assertEqual(R.interpreter(home, cold=lambda lib: True, python=py), (py["executable"], "own"))
                self.assertFalse(os.path.lexists(home))

    def test_a_layout_that_cannot_move_keeps_the_own_interpreter(self):
        py, home = self.fake("good"), os.path.join(self.tmp, "home")
        outside = self.stdlib("outside")
        for change in ({"stdlib": outside}, {"libdir": outside}, {"executable": sys.executable},
                       {"executable": os.path.join(self.tmp, "absent")}):
            with self.subTest(change=change):
                bent = dict(py, **change)
                self.assertEqual(R.interpreter(home, cold=lambda lib: True, python=bent), (bent["executable"], "own"))
                self.assertFalse(os.path.lexists(home))

    def answers(self, cold: str | None) -> list:
        """``cold_home`` and ``interpreter`` replaced: the first answers ``cold``, the second this interpreter as
        ``a-kind``; the list is who was asked, with what."""
        asked: list = []
        self.addCleanup(setattr, R, "interpreter", R.interpreter)
        self.addCleanup(setattr, R, "cold_home", R.cold_home)
        R.interpreter = lambda home: asked.append(("warm", home)) or (sys.executable, "a-kind")
        R.cold_home = lambda home: asked.append(("cold", home)) or cold
        return asked

    def linked(self, **how) -> tuple[str, str, str]:
        """A run of one command: the summary's ``python``, the run's directory, what its ``python3`` links to."""
        dump = os.path.join(self.tmp, "link.txt")
        out, summary = self.run_cmds("python -c \"import json,os; p=os.environ['PATH']; json.dump([p, os.readlink("
                                     "os.path.join(p, 'python3'))], open(%r,'w'))\"" % dump, **how)
        self.assertTrue(out[0]["ok"], out)
        with open(dump) as f:
            path, link = json.load(f)
        self.assertEqual(os.path.dirname(os.path.dirname(path)), self.work)
        return summary["python"], os.path.dirname(path), link

    def test_a_run_asks_for_a_cold_home_first_and_says_cold_home_when_it_gets_one(self):
        asked = self.answers(os.path.realpath(sys.executable))
        kind, run, link = self.linked()
        self.assertEqual((kind, link), ("cold_home", os.path.realpath(sys.executable)))
        # the home is asked for in the run's own directory, beside its PATH directory, so it is removed with it
        self.assertEqual(asked, [("cold", os.path.join(run, "python-cold"))])

    def test_a_run_with_no_cold_home_links_to_what_interpreter_answers_and_says_its_kind(self):
        asked = self.answers(None)
        kind, run, link = self.linked()
        self.assertEqual((kind, link), ("a-kind", sys.executable))
        self.assertEqual(asked, [("cold", os.path.join(run, "python-cold")), ("warm", os.path.join(run, "python-home"))])

    def test_a_run_asked_warm_and_pythons_unasked_build_no_cold_home(self):
        asked = self.answers(os.path.realpath(sys.executable))
        kind, run, link = self.linked(cold=False)
        self.assertEqual((kind, link), ("a-kind", sys.executable))
        self.assertEqual(asked, [("warm", os.path.join(run, "python-home"))])
        work = os.path.join(self.tmp, "w")
        os.mkdir(work)
        self.assertEqual(R.pythons(work), (os.path.join(work, "bin"), "a-kind"))
        self.assertEqual(asked[1:], [("warm", os.path.join(work, "python-home"))])

    def closed(self, home: str) -> None:
        """Every directory under ``home`` is closed to writes and none is a bytecode cache."""
        tops = [top for top, _, _ in os.walk(home)]
        self.assertEqual({stat.S_IMODE(os.lstat(t).st_mode) for t in tops}, {0o555})
        self.assertEqual([t for t in tops if os.path.basename(t) == "__pycache__"], [])

    def test_a_cold_home_is_a_moved_home_closed_to_writes(self):
        # no_bytecode: a python that writes none is what a cold home asks for, not a failed check.
        for mode in ("good", "no_bytecode"):
            with self.subTest(mode=mode):
                py, home = self.fake(mode), os.path.join(self.tmp, "home-" + mode)
                self.assertEqual(R.cold_home(home, python=py), os.path.join(home, "bin", "py-fake"))
                self.assertEqual(os.readlink(os.path.join(home, "lib", "py", "json", "__init__.py")),
                                 os.path.join(py["stdlib"], "json", "__init__.py"))
                self.closed(home)

    def test_a_cold_home_failing_a_check_or_a_layout_that_cannot_move_is_removed_and_is_none(self):
        # pries: the start left bytecode in the home (as root's python would), so the home is not cold.
        for mode in ("old_prefix", "other_path", "fails", "venv", "pries"):
            with self.subTest(mode=mode):
                py, home = self.fake(mode), os.path.join(self.tmp, "home-" + mode)
                self.assertIsNone(R.cold_home(home, python=py))
                self.assertFalse(os.path.lexists(home))
        py, home = self.fake("good"), os.path.join(self.tmp, "home")
        outside = self.stdlib("outside")
        for change in ({"stdlib": outside}, {"libdir": outside}, {"executable": os.path.join(self.tmp, "absent")}):
            with self.subTest(change=change):
                self.assertIsNone(R.cold_home(home, python=dict(py, **change)))
                self.assertFalse(os.path.lexists(home))

    def test_this_interpreter_in_a_cold_home_compiles_at_every_start_and_keeps_nothing(self):
        # The real interpreter, where its layout moves and this user is not root (else the answer is None and
        # nothing is left): a child with an empty environment takes the home as its prefix, imports a module of
        # the standard library from there, and no bytecode of it is there afterwards.
        home = os.path.join(self.tmp, "home")
        python = R.cold_home(home)
        if python is None:
            self.assertFalse(os.path.lexists(home))
            return
        import subprocess
        path = R.bindir(os.path.join(self.tmp, "bin"), python)
        code = "import colorsys, sys; print(sys.prefix); print(colorsys.__file__); print(colorsys.__cached__)"
        for _ in range(2):
            proc = subprocess.run([os.path.join(path, "python"), "-c", code], env={}, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            prefix, source, cached = proc.stdout.decode().split()
            self.assertEqual(prefix, home)
            self.assertTrue(source.startswith(home + os.sep) and cached.startswith(home + os.sep), (source, cached))
            self.assertFalse(os.path.lexists(cached))
        self.closed(home)

    def test_a_run_as_it_is_called_is_cold_where_a_cold_home_builds(self):
        # Nothing replaced: the run says cold_home exactly when this machine's interpreter gives one.
        probe = R.cold_home(os.path.join(self.tmp, "probe"))
        kind, run, link = self.linked()
        self.assertEqual(kind == "cold_home", probe is not None)
        if probe is not None:
            self.assertEqual(link, os.path.join(run, "python-cold", os.path.relpath(
                os.path.realpath(sys.executable), sys.base_prefix)))
        self.assertEqual(os.listdir(self.work), [])

    def test_this_interpreter_made_cold_serves_bytecode_to_a_child_with_an_empty_environment(self):
        # The real interpreter: where its layout moves (the three checks say), a module a child imports is
        # compiled once into the home and loaded from there by the next child, with no variable passed.
        home = os.path.join(self.tmp, "home")
        python, kind = R.interpreter(home, cold=lambda lib: True)
        if kind == "own":
            self.assertEqual((python, os.path.lexists(home)), (sys.executable, False))
            return
        import subprocess
        path = R.bindir(os.path.join(self.tmp, "bin"), python)
        code = "import colorsys, sys; print(sys.prefix); print(colorsys.__file__); print(colorsys.__cached__)"
        said = []
        for _ in range(2):
            proc = subprocess.run([os.path.join(path, "python"), "-c", code], env={}, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            said.append(proc.stdout.decode().split())
        self.assertEqual(said[0], said[1])
        prefix, source, cached = said[0]
        self.assertEqual(prefix, home)
        self.assertTrue(source.startswith(home + os.sep) and cached.startswith(home + os.sep), said[0])
        self.assertEqual(os.path.realpath(source), os.path.realpath(colorsys_source()))
        self.assertTrue(os.path.isfile(cached))


def colorsys_source() -> str:
    import colorsys
    return colorsys.__file__


class Results(Base):
    def test_exit_tail_and_order(self):
        out, summary = self.run_cmds("python -c \"import time; time.sleep(0.3); print('a'*700)\"",
                                     "python -c \"import sys; sys.stderr.write('boom'); sys.exit(3)\"",
                                     "python -c pass", jobs=3)
        self.assertEqual([r["id"] for r in out], ["T0", "T1", "T2"])
        self.assertEqual([(r["exit"], r["ok"]) for r in out], [(0, True), (3, False), (0, True)])
        self.assertEqual(out[0]["tail"], "a" * 599 + "\n")
        self.assertEqual(out[1]["tail"], "boom")
        self.assertIn(summary.pop("python"), ("cold_home", "own", "moved_home"))
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

    def test_warm_is_asked_by_its_flag_only(self):
        asked: list = []
        self.addCleanup(setattr, R, "cold_home", R.cold_home)
        R.cold_home = lambda home: asked.append(home)
        self.assertEqual((self.main("--only", "T1")[0], len(asked)), (0, 1))
        code, lines = self.main("--only", "T1", "--warm")
        self.assertEqual((code, len(asked)), (0, 1))
        self.assertIn(lines[-1]["python"], ("own", "moved_home"))

    def test_exit_codes(self):
        self.assertEqual(self.main("--only", "T1")[0], 0)
        code, lines = self.main("-j", "2")
        self.assertEqual((code, lines[-1]["failed"]), (1, ["T2"]))
        self.assertEqual(self.main("--only", "T7"), (2, [{"ok": False, "reason": "test_unknown:T7"}]))
        self.git = os.path.join(self.tmp, "absent")
        self.assertEqual(self.main(), (2, [{"ok": False, "reason": "git_unavailable"}]))


if __name__ == "__main__":
    unittest.main()
