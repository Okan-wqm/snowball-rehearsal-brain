"""Test 56 (P1 MF10, tohum/26j): an organ's output stands in ``koş``'s results with its hash, ``yaz`` reads it by
that hash, and an output with one byte changed is not read.

What is measured:

- ``Store`` (``runner.organ_output`` alone, on real directories): the files ``keep`` writes, against hashes and
  manifest bytes written out by hand here; ``read`` on that store with every single byte of every stored file
  flipped in turn, and with a file cut, grown, removed or swapped; the trees ``keep`` refuses (a symlink, a fifo,
  an entry marked unreadable, a file changed after it was hashed) and that nothing is written for them;
- ``Live`` (the jobs: ``loop.job.run("kos")`` on a ``pulled`` artifact carrying an accepted organ, with the
  recording stand-in for docker that runs the entry point, its ``out/results`` handed over as the download does,
  then ``loop.job.run("yaz")``): the index entry's ``output``, the files under ``o/`` against what the entry point
  wrote, ``yaz``'s line, and ``yaz`` again after one byte of the results changed.

Not run here: a real docker, the artifact's upload and download (the hand-over is a move of the directory), a
brain that holds an organ (it holds none today, so a live cycle's ``organs`` is ``{}``).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import job as J  # noqa: E402
from profile import derive as D  # noqa: E402
from runner import contained  # noqa: E402
from runner import organ_output as OO  # noqa: E402
from runner import organs  # noqa: E402
import test_loop_yaz as LY  # noqa: E402
from test_loop_kos import TARGET, RedAs  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def by_hand(files: dict) -> bytes:
    """The manifest of ``{path: bytes}`` by the module docstring's rule, with no call of the module."""
    return ('{"files":{%s}}\n' % ",".join('%s:"%s"' % (json.dumps(n), sha(files[n])) for n in sorted(files))).encode()


E = hashlib.sha256(b"").hexdigest().encode()     # the hash of no bytes: FILES holds such a file, so it is stored

# A tree an organ may leave: a nested file, two files of the same bytes, an empty file, names a shell would not like.
FILES = {"findings.json": b'[{"rule": "no-var"}]\n', "candidates/c1/package.json": b'{"organ_ids": []}\n',
         "copy.json": b'[{"rule": "no-var"}]\n', "empty": b"", "we ird\n$(x);'.txt": b"\x00\xff\n", "o/x": b"o",
         "caf\udce9": b"a name that is not UTF-8, as the host lists it"}


class Store(unittest.TestCase):
    def setUp(self) -> None:
        self.base = tempfile.mkdtemp(prefix="t-organ-output-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.made, self.out = os.path.join(self.base, "made"), os.path.join(self.base, "results")
        os.mkdir(self.out)
        self.write(FILES)

    def write(self, files: dict) -> None:
        for rel, data in files.items():
            os.makedirs(os.path.dirname(os.path.join(self.made, rel)), exist_ok=True)
            with open(os.path.join(self.made, rel), "wb") as fh:
                fh.write(data)

    def keep(self, entries=None) -> dict:
        return OO.keep(contained.hash_tree(self.made) if entries is None else entries,
                       lambda rel: D._read_regular(self.made, rel), self.out)

    def read(self, want: str):
        return OO.read(want, lambda rel: D._read_regular(self.out, rel))

    def refused(self, want) -> list:
        with self.assertRaises(OO.Refused) as ctx:
            self.read(want)
        return ctx.exception.reasons

    def stored(self) -> dict:
        """``{name: bytes}`` of everything under the results directory."""
        got = {}
        for dirpath, _, names in os.walk(self.out):
            for name in names:
                with open(os.path.join(dirpath, name), "rb") as fh:
                    got[os.path.relpath(os.path.join(dirpath, name), self.out)] = fh.read()
        return got

    def test_the_output_stands_under_its_hash_and_is_read_by_it(self):
        os.mkdir(os.path.join(self.made, "nothing-in-it"))
        kept = self.keep()
        manifest = by_hand(FILES)
        self.assertEqual(kept, {"sha256": sha(manifest), "reasons": []})
        # one file per distinct content, named by its hash, and the manifest; nothing else in the results
        want = {"o/" + sha(data): data for data in list(FILES.values()) + [manifest]}
        self.assertEqual(len(want), len(FILES))     # two of the files share their bytes
        self.assertEqual(self.stored(), want)
        self.assertEqual(self.read(kept["sha256"]), FILES)

    def test_an_output_without_files_is_kept(self):
        shutil.rmtree(self.made)
        os.mkdir(self.made)
        kept = self.keep()
        self.assertEqual(kept, {"sha256": sha(b'{"files":{}}\n'), "reasons": []})
        self.assertEqual(self.read(kept["sha256"]), {})

    def test_two_outputs_share_the_store(self):
        first = self.keep()["sha256"]
        self.write({"more.txt": b"more", "findings.json": b"[]\n"})
        second = self.keep()["sha256"]
        self.assertNotEqual(first, second)
        self.assertEqual(self.read(first), FILES)
        self.assertEqual(self.read(second), dict(FILES, **{"more.txt": b"more", "findings.json": b"[]\n"}))

    def test_one_changed_byte_anywhere_is_not_read(self):
        kept = self.keep()["sha256"]
        stored = self.stored()
        flips = 0
        for name, data in sorted(stored.items()):
            what = "manifest" if name == "o/" + kept else "file"
            for at in range(len(data)):
                changed = data[:at] + bytes([data[at] ^ 1]) + data[at + 1:]
                with open(os.path.join(self.out, name), "wb") as fh:
                    fh.write(changed)
                self.assertEqual(self.refused(kept), ["output_changed:" + what], (name, at))
                flips += 1
            with open(os.path.join(self.out, name), "wb") as fh:
                fh.write(data)
        self.assertEqual(flips, sum(map(len, stored.values())))
        self.assertEqual(self.read(kept), FILES)        # every byte back: read again

    def test_a_file_cut_grown_removed_or_swapped_is_not_read(self):
        kept = self.keep()["sha256"]
        stored = self.stored()
        one, other = "o/" + sha(FILES["findings.json"]), "o/" + sha(FILES["o/x"])
        empty = "o/" + sha(b"")
        for label, name, data, want in (
                ("cut", one, stored[one][:-1], ["output_changed:file"]),
                ("grown", one, stored[one] + b"\n", ["output_changed:file"]),
                ("grown from nothing", empty, b"\n", ["output_changed:file"]),
                ("another file's bytes", one, stored[other], ["output_changed:file"]),
                ("removed", one, None, ["output_missing:file"]),
                ("manifest cut", "o/" + kept, stored["o/" + kept][:-1], ["output_changed:manifest"]),
                ("manifest removed", "o/" + kept, None, ["output_missing:manifest"]),
                ("manifest is a file's bytes", "o/" + kept, stored[one], ["output_changed:manifest"])):
            with self.subTest(label):
                path = os.path.join(self.out, name)
                os.remove(path)
                if data is not None:
                    with open(path, "wb") as fh:
                        fh.write(data)
                self.assertEqual(self.refused(kept), want)
                with open(path, "wb") as fh:
                    fh.write(stored[name])
        # two changed, one missing: each reason once, sorted
        os.remove(os.path.join(self.out, one))
        for name in (other, empty):
            with open(os.path.join(self.out, name), "wb") as fh:
                fh.write(b"!")
        self.assertEqual(self.refused(kept), ["output_changed:file", "output_missing:file"])

    def test_a_link_in_the_store_is_not_read(self):
        kept = self.keep()["sha256"]
        name = os.path.join(self.out, "o", sha(FILES["o/x"]))
        os.rename(name, os.path.join(self.base, "moved"))
        os.symlink(os.path.join(self.base, "moved"), name)      # the same bytes, behind a link
        self.assertEqual(self.refused(kept), ["output_missing:file"])

    def test_a_hash_that_names_no_manifest_is_not_read(self):
        self.keep()
        for bad in (None, 7, "", "A" * 64, "a" * 63, "a" * 65, "a" * 64 + "\n", "../" + "a" * 61, ["a" * 64]):
            with self.subTest(bad=bad):
                self.assertEqual(self.refused(bad), ["output_hash_invalid"])
        self.assertEqual(self.refused("a" * 64), ["output_missing:manifest"])
        # bytes under their own hash that are no manifest: a kept file, and documents of other shapes
        self.assertEqual(self.refused(sha(FILES["findings.json"])), ["output_unusable"])
        for doc in (b"\xff", b"{", b"[]\n", b'{"files":[]}\n', b'{"files":{},"more":1}\n', b"{}\n",
                    b'{"files":' + b"[" * 100000 + b"]" * 100000 + b"}\n",     # deeper than ``cli.loads`` reads
                    b'{"files":{"a":"%s"}}\n' % (b"A" * 64), b'{"files":{"a":7}}\n',
                    b'{"files":{"a":"%s\\n"}}\n' % (b"a" * 64),
                    # a manifest's object in other bytes than keep's: spacing, no final newline, key order, an
                    # escape json does not write, a key twice
                    b'{"files": {}}\n', b'{"files":{}}', b'{"files":{}}\n\n', b' {"files":{}}\n',
                    b'{"files":{"b":"%s","a":"%s"}}\n' % (E, E), b'{"files":{"\\u0061":"%s"}}\n' % E,
                    b'{"files":{"a":"%s","a":"%s"}}\n' % (E, E),
                    # keys that are no path of a listing
                    b'{"files":{"":"%s"}}\n' % E, b'{"files":{"../x":"%s"}}\n' % E, b'{"files":{"a/../x":"%s"}}\n' % E,
                    b'{"files":{"/a":"%s"}}\n' % E, b'{"files":{"a//b":"%s"}}\n' % E, b'{"files":{"a/":"%s"}}\n' % E,
                    b'{"files":{".":"%s"}}\n' % E, b'{"files":{"a/.":"%s"}}\n' % E):
            with self.subTest(doc=doc):
                with open(os.path.join(self.out, "o", sha(doc)), "wb") as fh:
                    fh.write(doc)
                self.assertEqual(self.refused(sha(doc)), ["output_unusable"])

    def test_an_entry_that_is_no_regular_file_keeps_nothing(self):
        os.symlink("findings.json", os.path.join(self.made, "link"))
        self.assertEqual(self.keep(), {"sha256": None, "reasons": ["output_entry:symlink"]})
        os.mkfifo(os.path.join(self.made, "candidates", "pipe"))
        os.symlink("/etc", os.path.join(self.made, "candidates", "dir-link"))
        self.assertEqual(self.keep(), {"sha256": None, "reasons": ["output_entry:other", "output_entry:symlink"]})
        entries = contained.hash_tree(self.made)
        for label, marked in (("file", {"type": "file", "unreadable": True}), ("dir", {"type": "dir", "unreadable": True}),
                              ("unknown", {"type": "unknown", "unreadable": True})):
            with self.subTest(label):
                clean = {k: v for k, v in entries.items() if v["type"] in ("file", "dir")}
                self.assertEqual(self.keep(dict(clean, empty=marked)),
                                 {"sha256": None, "reasons": ["output_entry:unreadable"]})
        self.assertEqual(self.stored(), {})
        self.assertEqual(os.listdir(self.out), [])

    def test_a_file_that_is_not_the_bytes_hashed_keeps_nothing(self):
        entries = contained.hash_tree(self.made)
        name = os.path.join(self.made, "we ird\n$(x);'.txt")

        def grown() -> None:
            with open(name, "ab") as fh:
                fh.write(b" ")

        def linked() -> None:
            os.rename(name, os.path.join(self.base, "moved"))
            os.symlink(os.path.join(self.base, "moved"), name)      # the bytes hashed, behind a link

        for label, change in (("changed", grown), ("removed", lambda: os.remove(name)), ("a link now", linked)):
            with self.subTest(label):
                shutil.rmtree(self.made)
                self.write(FILES)
                change()
                self.assertEqual(self.keep(entries), {"sha256": None, "reasons": ["output_changed"]})
                self.assertEqual(os.listdir(self.out), [])


# The organ of the live tests: its entry point writes the tree its argument names under /out.
MAIN = (b"import os, sys\n"
        b"out, mode = sys.argv[1], sys.argv[2]\n"
        b"os.makedirs(os.path.join(out, 'candidates', 'c1'))\n"
        b"os.mkdir(os.path.join(out, 'empty-dir'))\n"
        b"for name, data in (('findings.json', b'[1]\\n'), ('candidates/c1/package.json', b'{}\\n'), ('same', b'[1]\\n')):\n"
        b"    with open(os.path.join(out, name), 'wb') as fh:\n"
        b"        fh.write(data)\n"
        b"if mode == 'link':\n"
        b"    os.symlink('findings.json', os.path.join(out, 'link'))\n"
        b"sys.exit(3 if mode == 'fail' else 0)\n")
WROTE = {"findings.json": b"[1]\n", "candidates/c1/package.json": b"{}\n", "same": b"[1]\n"}


def organ(mode: str = "ok") -> dict:
    return {"entry": ["python3", "/in/adapters/lint/main.py", "/out", mode], "files": {"adapters/lint/main.py": MAIN}}


class Live(LY.YazBase):
    """``kos`` then ``yaz`` on a ``pulled`` artifact whose accepted organs are ``carried``."""

    def cycle(self, carried: dict, accepted: dict | None = None, runner=None) -> dict:
        """The ``kos`` job with ``carried`` (all accepted unless ``accepted`` is given), handed over to ``yaz``'s
        ``in/results``; returns the index's ``organs``."""
        accepted = {o: organs.definition_sha256(d) for o, d in carried.items()} if accepted is None else accepted
        self.write_pulled({}, accepted=accepted, organs=carried)
        out = J.run("kos", {"RUNNER_TEMP": self.temp}, runner=runner or RedAs())
        self.assertTrue(out["ok"], out)
        os.makedirs(os.path.dirname(self.results()), exist_ok=True)
        shutil.move(os.path.join(self.temp, "out", "results", TARGET["id"]), self.results())
        os.rmdir(os.path.join(self.temp, "out", "results"))
        self.control(LY.OPEN)
        with open(self.results("index.json")) as fh:
            return json.load(fh)["organs"]

    def yaz(self) -> dict:
        """The ``organs`` of the target's line of a ``yaz`` job that ended ``ok``."""
        self.github()
        line = self.line(self.run_yaz())
        self.assertTrue(line["ok"], line)
        return line["organs"]

    def store(self) -> dict:
        if not os.path.lexists(self.results("o")):
            return {}
        got = {}
        for name in os.listdir(self.results("o")):
            with open(self.results("o", name), "rb") as fh:
                got[name] = fh.read()
        return got

    def test_kos_keeps_the_output_and_yaz_reads_it_by_its_hash(self):
        index = self.cycle({"lint.discover": organ()})
        manifest = by_hand(WROTE)
        entry = index["lint.discover"]
        self.assertEqual((entry["called"], entry["valid"], entry["output"]),
                         (True, True, {"sha256": sha(manifest), "reasons": []}))
        self.assertEqual(self.store(), {sha(b"[1]\n"): b"[1]\n", sha(b"{}\n"): b"{}\n", sha(manifest): manifest})
        read = {"read": True, "sha256": sha(manifest), "files": 3, "bytes": 11}
        self.assertEqual(self.yaz(), {"lint.discover": read})
        # one byte of the results changed, each stored file in turn: yaz does not read the output
        for name, data in sorted(self.store().items()):
            for label, changed in (("first byte", bytes([data[0] ^ 1]) + data[1:]), ("last byte", data[:-1] + b"\x00")):
                with self.subTest(name=name, change=label):
                    with open(self.results("o", name), "wb") as fh:
                        fh.write(changed)
                    what = "manifest" if name == sha(manifest) else "file"
                    self.assertEqual(self.yaz(), {"lint.discover": {"read": False, "reasons": ["output_changed:" + what]}})
                    with open(self.results("o", name), "wb") as fh:
                        fh.write(data)
        self.assertEqual(self.yaz(), {"lint.discover": read})
        # the hash yaz reads by is the index's: another kept hash there, and yaz reads that one or nothing
        with open(self.results("index.json")) as fh:
            doc = json.load(fh)
        for named, want in ((sha(b"[1]\n"), ["output_unusable"]), ("0" * 64, ["output_missing:manifest"]),
                            (sha(manifest).upper(), ["output_hash_invalid"]), (None, ["output_not_kept"])):
            with self.subTest(named=named):
                doc["organs"]["lint.discover"]["output"]["sha256"] = named
                with open(self.results("index.json"), "w") as fh:
                    json.dump(doc, fh)
                self.assertEqual(self.yaz(), {"lint.discover": {"read": False, "reasons": want}})

    def test_a_link_in_the_handed_over_store_is_not_read(self):
        self.cycle({"lint.discover": organ()})
        name = self.results("o", sha(b"{}\n"))
        os.rename(name, os.path.join(self.base, "moved"))
        os.symlink(os.path.join(self.base, "moved"), name)
        self.assertEqual(self.yaz(), {"lint.discover": {"read": False, "reasons": ["output_missing:file"]}})

    def test_a_failing_entry_point_s_output_is_kept(self):
        index = self.cycle({"lint.discover": organ("fail")})
        entry = index["lint.discover"]
        self.assertEqual((entry["exit"], entry["valid"], entry["output"]),
                         (3, True, {"sha256": sha(by_hand(WROTE)), "reasons": []}))
        self.assertEqual(self.yaz()["lint.discover"]["read"], True)

    def test_a_run_that_is_not_valid_keeps_nothing(self):
        index = self.cycle({"lint.discover": organ()}, runner=RedAs("pkg/green.py"))
        entry = index["lint.discover"]
        self.assertEqual((entry["called"], entry["valid"], entry["reasons"], entry["output"]),
                         (True, False, ["red_control_green"], {"sha256": None, "reasons": ["run_invalid"]}))
        self.assertEqual(self.store(), {})
        self.assertEqual(self.yaz(), {"lint.discover": {"read": False, "reasons": ["output_not_kept"]}})

    def test_an_output_holding_a_link_keeps_nothing(self):
        index = self.cycle({"lint.discover": organ("link")})
        entry = index["lint.discover"]
        self.assertEqual((entry["valid"], entry["output"]), (True, {"sha256": None, "reasons": ["output_entry:symlink"]}))
        self.assertEqual(self.store(), {})
        self.assertEqual(self.yaz(), {"lint.discover": {"read": False, "reasons": ["output_not_kept"]}})

    def test_each_organ_s_output_is_its_own_and_a_refused_organ_has_none(self):
        second = dict(organ(), entry=["python3", "/in/adapters/lint/main.py", "/out", "second"])
        carried = {"a.first": organ(), "b.second": second, "c.refused": organ("fail")}
        accepted = {o: organs.definition_sha256(d) for o, d in carried.items() if o != "c.refused"}
        index = self.cycle(carried, accepted)
        self.assertEqual(index["c.refused"], {"called": False, "reasons": ["organ_not_accepted"]})
        manifest = by_hand(WROTE)
        self.assertEqual([index[o]["output"] for o in ("a.first", "b.second")], [{"sha256": sha(manifest), "reasons": []}] * 2)
        self.assertEqual(len(self.store()), 3)      # the same bytes from two organs stand once
        read = {"read": True, "sha256": sha(manifest), "files": 3, "bytes": 11}
        self.assertEqual(self.yaz(), {"a.first": read, "b.second": read,
                                      "c.refused": {"read": False, "reasons": ["output_not_kept"]}})

    def test_without_organs_and_without_an_index_yaz_reads_none(self):
        self.assertEqual(self.cycle({}), {})
        self.assertFalse(os.path.lexists(self.results("o")))
        self.assertEqual(self.yaz(), {})
        for label, doc in (("no organs key", b'{"candidates": {}}'), ("organs a list", b'{"organs": []}'),
                           ("not JSON", b"{"), ("an entry that is no object", b'{"organs": {"x": 1}}'),
                           ("an output that is no object", b'{"organs": {"x": {"output": "a"}}}')):
            with self.subTest(label):
                with open(self.results("index.json"), "wb") as fh:
                    fh.write(doc)
                got = J.yaz_organs({"RUNNER_TEMP": self.temp}, TARGET["id"])
                self.assertEqual(got, {"x": {"read": False, "reasons": ["output_not_kept"]}} if b'"x"' in doc else {})


if __name__ == "__main__":
    unittest.main()
