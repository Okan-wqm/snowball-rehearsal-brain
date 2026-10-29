"""Test 34 (asama-0/09) and group ``npmlock`` (tohum/29d): ``deps.fetch`` for npm, on local fixture
tarballs served by a mirror directory (the sandbox has no network; the HTTPS path is asama-0/10a #getir).

- every tarball equals the lock's ``integrity``; one changed byte is refused and no artifact is written;
- ``resolved`` off the allowed registry (host, scheme, user, port, query, path, name), git and file
  dependencies, bundled entries and workspace keys are refused before anything is fetched;
- a package that needs an install script (lock flag, ``scripts``, ``binding.gyp``) is refused unless the
  recipe marks it by exact key or ``name@version``;
- the same lock gives the same content address, one changed lock byte another; ``verify`` takes the
  artifact by its hash and refuses a changed tarball, lock or manifest and an extra file;
- the license report is written; with ``--product`` an unlisted or missing license is refused;
- ``operating.deps_bytes`` stops the fetch; unusable input is exit 2 with one JSON line, never a traceback;
- the ``npmlock`` vector interface (tohum/29g), ``fetch LOCK MIRROR`` with stdin, is ``TestNpmlock``: the
  named cases, the order of reasons per package, the address recomputed here, exit 2; the artifact is
  written by ``store`` and prints the same ``artefact``.
"""

from __future__ import annotations

import base64
import copy
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import unittest
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from runner import deps_npm as N  # noqa: E402
from profile_tree import writable_base  # noqa: E402

REG = "https://registry.npmjs.org/"


def tgz(files: dict, top: str = "package") -> bytes:
    """``files``: name -> bytes | dict (JSON) | ("symlink", target); placed under ``top/``."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.USTAR_FORMAT) as tar:
        for name, content in files.items():
            info = tarfile.TarInfo("%s/%s" % (top, name) if top else name)
            info.mtime = 0
            if isinstance(content, tuple):
                info.type, info.linkname = tarfile.SYMTYPE, content[1]
                tar.addfile(info)
                continue
            data = json.dumps(content).encode() if isinstance(content, dict) else content
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def sri(data: bytes, alg: str = "sha512") -> str:
    return "%s-%s" % (alg, base64.b64encode(hashlib.new(alg, data).digest()).decode())


def url(name: str, version: str) -> str:
    return "%s%s/-/%s-%s.tgz" % (REG, name, name.split("/")[-1], version)


class Fixture:
    """A lock, its tarballs in a mirror directory, and an output directory."""

    def __init__(self, base: str):
        self.base = base
        self.mirror = os.path.join(base, "mirror")
        self.out = os.path.join(base, "out")
        os.makedirs(self.out)
        self.lock = {"lockfileVersion": 3, "name": "toy", "packages": {"": {"name": "toy", "version": "1.0.0"}}}
        self.blobs = {}

    def add(self, name: str, version: str, key: str | None = None, manifest: dict | None = None,
            extra: dict | None = None, **entry) -> bytes:
        files = {"package.json": manifest if manifest is not None else
                 {"name": name, "version": version, "license": "MIT"}}
        files.update(extra or {})
        data = tgz(files)
        u = url(name, version)
        self.put(u, data)
        row = {"version": version, "resolved": u, "integrity": sri(data)}
        row.update(entry)
        self.lock["packages"][key or "node_modules/" + name] = row
        return data

    def put(self, u: str, data: bytes) -> None:
        path = os.path.join(self.mirror, *u.split("://", 1)[1].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        self.blobs[u] = data

    def write_lock(self, name: str = "package-lock.json", lock: dict | None = None) -> str:
        path = os.path.join(self.base, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.lock if lock is None else lock, fh)
        return path

    def fetch(self, **kw):
        calls = []
        inner = N.mirror_fetcher(self.mirror)

        def fetcher(u, cap):
            calls.append(u)
            return inner(u, cap)
        report = N.fetch(self.write_lock(kw.pop("lock_name", "package-lock.json")), self.out, fetcher, **kw)
        return report, calls

    def artifacts(self) -> list[str]:
        return sorted(n for n in os.listdir(self.out))


class Base(unittest.TestCase):
    def setUp(self):
        self.base = writable_base("deps-npm-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.fx = Fixture(self.base)
        self.fx.add("left-pad", "1.3.0")
        self.fx.add("@scope/util", "2.0.0")
        self.fx.add("inner", "0.1.0", key="node_modules/left-pad/node_modules/inner",
                    manifest={"name": "inner", "version": "0.1.0", "license": "ISC"})


class TestIntegrity(Base):
    def test_good_lock_fetches_and_writes_artifact(self):
        report, calls = self.fx.fetch()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["packages"], 3)
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.fx.artifacts(), [report["address"]])
        art = os.path.join(self.fx.out, report["address"])
        with open(os.path.join(art, "manifest.json"), "rb") as fh:
            raw = fh.read()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), report["address"])
        manifest = json.loads(raw)
        self.assertEqual([r["key"] for r in manifest["packages"]],
                         ["node_modules/@scope/util", "node_modules/left-pad",
                          "node_modules/left-pad/node_modules/inner"])
        for data in self.fx.blobs.values():
            with open(os.path.join(art, "tarballs", hashlib.sha512(data).hexdigest() + ".tgz"), "rb") as fh:
                self.assertEqual(fh.read(), data)
        self.assertTrue(N.verify(art)["ok"])

    def test_one_changed_byte_is_refused_and_nothing_written(self):
        u = url("left-pad", "1.3.0")
        for pos in (0, len(self.fx.blobs[u]) // 2, len(self.fx.blobs[u]) - 1):
            data = bytearray(self.fx.blobs[u])
            data[pos] ^= 0x01
            with open(os.path.join(self.fx.mirror, "registry.npmjs.org", "left-pad", "-", "left-pad-1.3.0.tgz"),
                      "wb") as fh:
                fh.write(bytes(data))
            report, _ = self.fx.fetch()
            self.assertEqual(report, {"ok": False, "reasons": ["integrity_mismatch:node_modules/left-pad"]})
            self.assertEqual(self.fx.artifacts(), [])

    def test_every_strong_token_must_match(self):
        data = self.fx.blobs[url("left-pad", "1.3.0")]
        entry = self.fx.lock["packages"]["node_modules/left-pad"]
        entry["integrity"] = "%s %s" % (sri(data), sri(b"other", "sha384"))
        self.assertEqual(self.fx.fetch()[0]["reasons"], ["integrity_mismatch:node_modules/left-pad"])
        entry["integrity"] = "%s %s %s" % (sri(b"x", "sha1"), sri(data, "sha256"), sri(data, "sha384"))
        self.assertTrue(self.fx.fetch()[0]["ok"])

    def test_integrity_shape(self):
        data = self.fx.blobs[url("left-pad", "1.3.0")]
        good = sri(data)
        cases = {
            None: "integrity_missing", "": "integrity_missing", 5: "integrity_missing",
            sri(data, "sha1"): "integrity_weak",
            "md5-" + base64.b64encode(hashlib.md5(data).digest()).decode(): "integrity_malformed",
            good[:-4] + "==": "integrity_malformed",            # wrong digest length
            good + "?opt": "integrity_malformed",
            "sha512" + good[6:].replace("-", ""): "integrity_malformed",
            good.replace("sha512-", "sha512-!"): "integrity_malformed",
            "SHA512-" + good[7:]: "integrity_malformed",
        }
        for value, reason in cases.items():
            lock = copy.deepcopy(self.fx.lock)
            lock["packages"]["node_modules/left-pad"]["integrity"] = value
            self.assertEqual(N.check(lock)["reasons"], ["%s:node_modules/left-pad" % reason], value)

    def test_same_lock_same_address_changed_byte_other(self):
        first = self.fx.fetch()[0]
        again = self.fx.fetch()[0]
        self.assertEqual(first["address"], again["address"])
        self.assertEqual(self.fx.artifacts(), [first["address"]])
        self.fx.lock["name"] = "toz"
        other = self.fx.fetch()[0]
        self.assertNotEqual(first["address"], other["address"])
        self.assertEqual(len(self.fx.artifacts()), 2)

    def test_existing_artifact_that_does_not_verify_is_no_verdict(self):
        first = self.fx.fetch()[0]
        lock = os.path.join(self.fx.out, first["address"], "package-lock.json")
        with open(lock, "ab") as fh:
            fh.write(b" ")
        with self.assertRaises(N.DepsError):
            self.fx.fetch()


class TestSource(Base):
    def setUp(self):
        super().setUp()
        self.fetches = []

    def refused(self, key, row, reason, **kw):
        self.fx.lock["packages"][key] = row
        report, calls = self.fx.fetch(**kw)
        self.assertFalse(report["ok"])
        self.assertIn("%s:%s" % (reason, key), report["reasons"], row)
        self.assertEqual(calls, [], "nothing is fetched before the lock passes")
        self.assertEqual(self.fx.artifacts(), [])

    def test_resolved_off_registry(self):
        data = self.fx.blobs[url("left-pad", "1.3.0")]
        good = url("left-pad", "1.3.0")
        for resolved in (
            good.replace("registry.npmjs.org", "registry.evil.org"),
            good.replace("registry.npmjs.org", "registry.npmjs.org.evil.org"),
            good.replace("https://", "http://"),
            good.replace("https://", "https://user@"),
            good.replace("registry.npmjs.org", "registry.npmjs.org:8443"),
            good.replace("registry.npmjs.org", "registry.npmjs.org:443"),
            good.replace("registry.npmjs.org", "regi\u017ftry.npmjs.org"),   # long s casefolds to s
            good.replace("registry.npmjs.org", "registry.npmjs.org."),
            good + "?x=1", good + "#x",
            good.replace("/left-pad/-/", "/other/-/"),                       # another package's tarball
            good.replace("/left-pad/-/", "/left-pad/../other/-/"),
            good.replace("/left-pad/-/", "/left%2dpad/-/"),
            good.replace("1.3.0.tgz", "1.3.1.tgz"),                         # another version
            good.replace(".tgz", ".tar.gz"),
            "", None,
        ):
            reason = "resolved_missing" if not resolved else "resolved_not_allowed"
            self.refused("node_modules/left-pad", {"version": "1.3.0", "resolved": resolved,
                                                    "integrity": sri(data)}, reason)

    def test_host_is_casefolded_and_registries_replace_default(self):
        self.fx.lock["packages"]["node_modules/left-pad"]["resolved"] = url("left-pad", "1.3.0").replace(
            "registry.npmjs.org", "Registry.NPMJS.org")
        self.assertTrue(N.check(self.fx.lock)["ok"])
        self.assertEqual(N.check(self.fx.lock, ["https://npm.example.com/r/"])["reasons"],
                         ["resolved_not_allowed:%s" % k for k in sorted(self.fx.lock["packages"]) if k])
        lock = copy.deepcopy(self.fx.lock)
        for row in lock["packages"].values():
            if "resolved" in row:
                row["resolved"] = row["resolved"].replace(REG, "https://npm.example.com/r/").replace(
                    "Registry.NPMJS.org/", "npm.example.com/r/")
        self.assertTrue(N.check(lock, ["https://npm.example.com/r"])["ok"])
        for bad in ("http://npm.example.com/", "https://u@npm.example.com/", "https://npm.example.com:8/",
                    "https://npm.example.com/?q", "https://npm.example.com/a/../b/", "npm.example.com",
                    "https://npm.ex\u017fample.com/"):
            with self.assertRaises((N.DepsError, ValueError)):
                N.check(lock, [bad])

    def test_git_and_file_dependencies(self):
        for key, row, reason in (
            ("node_modules/g1", {"version": "git+ssh://git@github.com/a/b.git#abc", "resolved":
                                 "git+ssh://git@github.com/a/b.git#abc"}, "git_dependency"),
            ("node_modules/g2", {"version": "1.0.0", "resolved": "GIT+https://github.com/a/b.git"}, "git_dependency"),
            ("node_modules/g3", {"version": "github:a/b", "resolved": "github:a/b#abc"}, "git_dependency"),
            ("node_modules/g4", {"version": "1.0.0", "resolved": "git@github.com:a/b.git"}, "git_dependency"),
            ("node_modules/f1", {"version": "file:../x", "resolved": "file:../x"}, "file_dependency"),
            ("node_modules/f2", {"version": "1.0.0", "resolved": "../x/f2-1.0.0.tgz",
                                 "integrity": sri(b"x")}, "file_dependency"),
            ("node_modules/f3", {"resolved": "packages/f3", "link": True}, "file_dependency"),
            ("node_modules/f4", {"version": "1.0.0", "resolved": url("f4", "1.0.0"), "link": True},
             "file_dependency"),
            ("node_modules/b1", {"version": "1.0.0", "inBundle": True}, "bundled_dependency"),
            ("packages/f3", {"name": "f3", "version": "1.0.0"}, "key_not_allowed"),
            ("node_modules/../evil", {"version": "1.0.0", "resolved": url("evil", "1.0.0"),
                                      "integrity": sri(b"x")}, "key_not_allowed"),
            ("node_modules/.bin", {"version": "1.0.0"}, "key_not_allowed"),
            ("node_modules/a/b", {"version": "1.0.0", "resolved": url("a", "1.0.0"),
                                  "integrity": sri(b"x")}, "key_not_allowed"),
            ("node_modules/ok", "not an object", "key_not_allowed"),
            ("node_modules/v1", {"version": "latest", "resolved": url("v1", "latest"), "integrity": sri(b"x")},
             "version_invalid"),
        ):
            self.setUp()
            self.refused(key, row, reason)

    def test_alias_uses_the_entry_name(self):
        data = tgz({"package.json": {"name": "real", "version": "3.0.0", "license": "MIT"}})
        self.fx.put(url("real", "3.0.0"), data)
        self.fx.lock["packages"]["node_modules/alias"] = {"name": "real", "version": "3.0.0",
                                                          "resolved": url("real", "3.0.0"), "integrity": sri(data)}
        self.assertTrue(self.fx.fetch()[0]["ok"])
        self.fx.lock["packages"]["node_modules/alias"]["resolved"] = url("alias", "3.0.0")
        self.assertEqual(N.check(self.fx.lock)["reasons"], ["resolved_not_allowed:node_modules/alias"])

    def test_lock_shape(self):
        for lock, reason in (([], "lock_unparsable"), ({"lockfileVersion": 1, "dependencies": {}},
                                                       "lock_version_unsupported"),
                             ({"lockfileVersion": True, "packages": {}}, "lock_version_unsupported"),
                             ({"lockfileVersion": 3, "packages": []}, "lock_version_unsupported"),
                             ({"lockfileVersion": "3", "packages": {}}, "lock_version_unsupported")):
            self.assertEqual(N.check(lock)["reasons"], [reason])
        self.assertTrue(N.check({"lockfileVersion": 2, "packages": {"": {}}})["ok"])


class TestInstallScripts(Base):
    def test_lock_flag_needs_a_mark(self):
        self.fx.lock["packages"]["node_modules/left-pad"]["hasInstallScript"] = True
        report, calls = self.fx.fetch()
        self.assertEqual(report["reasons"], ["install_script_not_marked:node_modules/left-pad"])
        self.assertEqual(calls, [])
        for marks in (["node_modules/left-pad"], ["left-pad@1.3.0"]):
            self.assertTrue(self.fx.fetch(marks=marks)[0]["ok"], marks)
        for marks in (["left-pad"], ["left-pad@1.3.1"], ["node_modules/left-pad/"], ["LEFT-PAD@1.3.0"]):
            self.assertFalse(self.fx.fetch(marks=marks)[0]["ok"], marks)

    def test_tarball_scripts_and_binding_gyp_need_a_mark_even_when_lock_is_silent(self):
        for script in N.INSTALL_SCRIPTS:
            self.setUp()
            self.fx.add("left-pad", "1.3.0", manifest={"name": "left-pad", "version": "1.3.0", "license": "MIT",
                                                       "scripts": {script: "node x.js"}})
            self.assertEqual(self.fx.fetch()[0]["reasons"], ["install_script_not_marked:node_modules/left-pad"])
            self.assertTrue(self.fx.fetch(marks=["left-pad@1.3.0"])[0]["ok"])
        self.setUp()
        self.fx.add("left-pad", "1.3.0", extra={"binding.gyp": b"{}"})
        self.assertEqual(self.fx.fetch()[0]["reasons"], ["install_script_not_marked:node_modules/left-pad"])
        self.setUp()
        self.fx.add("left-pad", "1.3.0", manifest={"name": "left-pad", "version": "1.3.0", "license": "MIT",
                                                   "scripts": {"test": "x", "prepare": "y"}})
        report = self.fx.fetch()[0]
        self.assertTrue(report["ok"])
        art = os.path.join(self.fx.out, report["address"], "manifest.json")
        with open(art, encoding="ascii") as fh:
            self.assertFalse(any(r["install_script"] for r in json.load(fh)["packages"]))


class TestTarball(Base):
    def test_tarball_shape(self):
        manifest = {"name": "left-pad", "version": "1.3.0", "license": "MIT"}
        for files, top, reason in (
            ({"index.js": b"x"}, "package", "tarball_no_package_json"),
            ({"package.json": ("symlink", "/etc/passwd")}, "package", "tarball_no_package_json"),
            ({"package.json": b"{not json"}, "package", "tarball_package_json_unreadable"),
            ({"package.json": b"[1]"}, "package", "tarball_package_json_unreadable"),
            ({"package.json": b"[" * 100000}, "package", "tarball_package_json_unreadable"),
            ({"package.json": b" " * (N.PACKAGE_JSON_MAX + 1)}, "package", "tarball_package_json_unreadable"),
            ({"package/package.json": manifest, "other/package.json": manifest}, "", "tarball_ambiguous_package_json"),
            ({"package.json": {"name": "left-pad", "version": "1.3.1"}}, "package", "tarball_manifest_mismatch"),
            ({"package.json": manifest, "node_modules/x/package.json": {"name": "x", "version": "1.0.0",
                                                                        "scripts": {"postinstall": "x"}}},
             "package", "bundled_dependency"),
            ({"package.json": {"name": "right-pad", "version": "1.3.0"}}, "package", "tarball_manifest_mismatch"),
        ):
            self.setUp()
            data = tgz(files, top)
            self.fx.put(url("left-pad", "1.3.0"), data)
            self.fx.lock["packages"]["node_modules/left-pad"]["integrity"] = sri(data)
            report = self.fx.fetch()[0]
            self.assertEqual(report["reasons"], ["%s:node_modules/left-pad" % reason], files)
            self.assertEqual(self.fx.artifacts(), [])
        for data in (b"not gzip", tgz({"package.json": manifest})[:-30]):
            self.setUp()
            self.fx.put(url("left-pad", "1.3.0"), data)
            self.fx.lock["packages"]["node_modules/left-pad"]["integrity"] = sri(data)
            self.assertEqual(self.fx.fetch()[0]["reasons"], ["tarball_unreadable:node_modules/left-pad"])

    def test_top_directory_name_is_free(self):
        data = tgz({"package.json": {"name": "left-pad", "version": "1.3.0", "license": "MIT"}}, "left-pad")
        self.fx.put(url("left-pad", "1.3.0"), data)
        self.fx.lock["packages"]["node_modules/left-pad"]["integrity"] = sri(data)
        self.assertTrue(self.fx.fetch()[0]["ok"])


class TestLicense(Base):
    def lic(self, manifest_license: dict, **kw):
        self.fx.add("left-pad", "1.3.0", manifest=dict({"name": "left-pad", "version": "1.3.0"}, **manifest_license))
        return self.fx.fetch(**kw)[0]

    def test_report_written_not_gated_without_product(self):
        report = self.lic({"license": "GPL-3.0-only"})
        self.assertTrue(report["ok"])
        row = [r for r in report["licenses"] if r["key"] == "node_modules/left-pad"][0]
        self.assertEqual((row["license"], row["allowed"]), (["GPL-3.0-only"], False))
        with open(os.path.join(self.fx.out, report["address"], "manifest.json"), encoding="ascii") as fh:
            rows = {r["key"]: r["license"] for r in json.load(fh)["packages"]}
        self.assertEqual(rows["node_modules/left-pad"], ["GPL-3.0-only"])
        self.assertEqual(rows["node_modules/left-pad/node_modules/inner"], ["ISC"])

    def test_product_gate(self):
        cases = [
            ({"license": "MIT"}, None),
            ({"license": "(MIT OR Apache-2.0)"}, None),
            ({"license": "mit AND isc"}, None),                        # identifiers casefolded
            ({"license": "MIT and ISC"}, "license_not_allowed"),       # operators are not
            ({"license": "MIT AND ISC"}, None),
            ({"license": {"type": "BSD-3-Clause"}}, None),
            ({"licenses": [{"type": "MIT"}, "ISC"]}, None),
            ({"license": "MIT OR GPL-3.0-only"}, "license_not_allowed"),
            ({"license": "Apache-2.0 WITH LLVM-exception"}, "license_not_allowed"),
            ({"license": "MIT+"}, "license_not_allowed"),
            ({"license": "I\u017fC"}, "license_not_allowed"),              # long s casefolds to s
            ({"license": "SEE LICENSE IN LICENSE"}, "license_not_allowed"),
            ({"license": "(MIT"}, "license_not_allowed"),
            ({"license": "MIT)"}, "license_not_allowed"),
            ({"license": "MIT OR"}, "license_not_allowed"),
            ({"license": ""}, "license_not_allowed"),
            ({"license": "MIT", "licenses": [{"type": "GPL-2.0"}]}, "license_not_allowed"),
            ({"license": 5}, "license_not_allowed"),
            ({"licenses": "MIT"}, "license_not_allowed"),
            ({"licenses": [{"name": "MIT"}]}, "license_not_allowed"),
            ({}, "license_not_found"),
            ({"licenses": []}, "license_not_found"),
        ]
        for value, reason in cases:
            self.setUp()
            report = self.lic(value, product=True)
            if reason is None:
                self.assertTrue(report["ok"], (value, report))
            else:
                self.assertEqual(report["reasons"], ["%s:node_modules/left-pad" % reason], value)
                self.assertEqual(self.fx.artifacts(), [])

    def test_policy_allowlist_and_exception(self):
        policy = {"constitutional": {"license_allowlist": ["ISC"]}}
        self.assertEqual(self.lic({"license": "ISC"}, product=True, policy=policy)["reasons"],
                         ["license_not_allowed:node_modules/@scope/util"])
        self.setUp()
        policy = {"constitutional": {"license_exceptions": {
            "left-pad==1.3.0": {"expression": "MIT", "evidence": "reviewed"}}}}
        report = self.lic({}, product=True, policy=policy)
        self.assertTrue(report["ok"], report)
        self.setUp()
        policy["constitutional"]["license_exceptions"]["left-pad==1.3.0"]["expression"] = "GPL-3.0-only"
        self.assertEqual(self.lic({"license": "MIT"}, product=True, policy=policy)["reasons"],
                         ["license_not_allowed:node_modules/left-pad"])
        self.setUp()
        policy["constitutional"]["license_exceptions"] = {"left-pad==1.3.1": {"expression": "MIT", "evidence": "x"}}
        self.assertEqual(self.lic({}, product=True, policy=policy)["reasons"],
                         ["license_not_found:node_modules/left-pad"])


class TestLimitAndVerify(Base):
    def test_deps_bytes(self):
        total = sum(len(b) for b in self.fx.blobs.values())
        ok = {"operating": {"deps_bytes": {"value": total, "band": [0, total]}}}
        self.assertTrue(self.fx.fetch(policy=ok)[0]["ok"])
        over = {"operating": {"deps_bytes": {"value": total - 1, "band": [0, total]}}}
        self.assertEqual(self.fx.fetch(policy=over)[0], {"ok": False, "reasons": ["limit_hit:deps_bytes"]})

    def test_verify_refuses_every_change(self):
        report = self.fx.fetch()[0]
        art = os.path.join(self.fx.out, report["address"])
        self.assertTrue(N.verify(art, report["address"])["ok"])
        self.assertEqual(N.verify(art, "0" * 64)["reasons"], ["address_mismatch"])

        def mutated(change):
            copy_dir = os.path.join(self.base, "copy")
            shutil.rmtree(copy_dir, True)
            shutil.copytree(art, copy_dir, symlinks=True)
            change(copy_dir)
            return N.verify(copy_dir, report["address"])

        tball = sorted(os.listdir(os.path.join(art, "tarballs")))[0]

        def flip(path):
            def change(d):
                with open(os.path.join(d, path), "r+b") as fh:
                    first = fh.read(1)
                    fh.seek(0)
                    fh.write(bytes([first[0] ^ 1]))
            return change

        def extra(path):
            def change(d):
                with open(os.path.join(d, path), "wb") as fh:
                    fh.write(b"x")
            return change

        def link_tarball(d):
            p = os.path.join(d, "tarballs", tball)
            os.rename(p, p + ".real")
            os.symlink(p + ".real", p)

        self.assertTrue(mutated(lambda d: None)["ok"])
        self.assertIn("tarball_mismatch", mutated(flip("tarballs/" + tball))["reasons"][0])
        self.assertEqual(mutated(flip("package-lock.json"))["reasons"], ["lock_mismatch"])
        self.assertEqual(mutated(flip("manifest.json"))["reasons"], ["address_mismatch"])
        self.assertEqual(mutated(extra("node_modules"))["reasons"], ["unexpected_file:node_modules"])
        self.assertEqual(mutated(extra("tarballs/x.tgz"))["reasons"], ["unexpected_file:tarballs/x.tgz"])
        reasons = mutated(link_tarball)["reasons"]
        self.assertIn("tarball_mismatch", reasons[0])
        self.assertIn("unexpected_file:tarballs/%s.real" % tball, reasons)
        self.assertEqual(mutated(lambda d: os.remove(os.path.join(d, "manifest.json")))["reasons"],
                         ["manifest_missing"])


class TestCli(Base):
    def run_cli(self, *args):
        proc = subprocess.run([sys.executable, "-m", "runner.deps_npm", *args], cwd=REFEREE, input="",
                              capture_output=True, text=True, timeout=120)
        lines = proc.stdout.splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        self.assertEqual(proc.stderr, "")
        return proc.returncode, json.loads(lines[0])

    def write(self, name, obj):
        path = os.path.join(self.base, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(obj if isinstance(obj, str) else json.dumps(obj))
        return path

    def test_cli(self):
        lock = self.fx.write_lock()
        code, out = self.run_cli("check", lock)
        self.assertEqual((code, out), (0, {"ok": True, "reasons": []}))
        code, out = self.run_cli("store", lock, self.fx.out, "--mirror", self.fx.mirror)
        self.assertEqual(code, 0)
        self.assertTrue(out["ok"])
        self.assertEqual(self.run_cli("verify", os.path.join(self.fx.out, out["address"]))[0], 0)
        code, out2 = self.run_cli("verify", os.path.join(self.fx.out, out["address"]), "--address", "f" * 64)
        self.assertEqual((code, out2["reasons"]), (1, ["address_mismatch"]))
        u = url("left-pad", "1.3.0")
        with open(os.path.join(self.fx.mirror, *u.split("://")[1].split("/")), "r+b") as fh:
            fh.seek(40)
            b = fh.read(1)
            fh.seek(40)
            fh.write(bytes([b[0] ^ 0x80]))
        code, out = self.run_cli("store", lock, self.fx.out, "--mirror", self.fx.mirror)
        self.assertEqual((code, out["reasons"]), (1, ["integrity_mismatch:node_modules/left-pad"]))
        self.fx.lock["packages"]["node_modules/left-pad"]["hasInstallScript"] = True
        lock = self.fx.write_lock()
        recipe = self.write("units.json", {"install_scripts_required": ["left-pad@1.3.0"]})
        self.assertEqual(self.run_cli("check", lock)[0], 1)
        self.assertEqual(self.run_cli("check", lock, "--recipe", recipe), (0, {"ok": True, "reasons": []}))
        code, out = self.run_cli("check", lock, "--registry", "https://other.example/")
        self.assertEqual(code, 1)

    def test_cli_product_and_policy(self):
        self.fx.add("left-pad", "1.3.0", manifest={"name": "left-pad", "version": "1.3.0", "license": "GPL-2.0"})
        lock = self.fx.write_lock()
        args = ("store", lock, self.fx.out, "--mirror", self.fx.mirror)
        self.assertEqual(self.run_cli(*args)[0], 0)
        code, out = self.run_cli(*args, "--product")
        self.assertEqual((code, out["reasons"]), (1, ["license_not_allowed:node_modules/left-pad"]))
        policy = self.write("policy.json", {"constitutional": {"license_allowlist": ["GPL-2.0", "MIT", "ISC"]}})
        self.assertEqual(self.run_cli(*args, "--product", "--policy", policy)[0], 0)

    def test_cli_unusable_input_is_exit_2_with_json_error(self):
        lock = self.fx.write_lock()
        os.mkdir(os.path.join(self.base, "deep"))
        deep = self.write("deep/package-lock.json", "[" * 100000)
        self.fx.write_lock(name="npm-shrinkwrap.json")
        shrink = os.path.join(self.base, "npm-shrinkwrap.json")
        wrong_name = self.write("lock.json", self.fx.lock)
        empty_mirror = os.path.join(self.base, "empty")
        os.mkdir(empty_mirror)
        cases = [
            ("check", os.path.join(self.base, "missing.json")),
            ("check", self.write("bad.json", "{")),
            ("check", deep),
            ("check", shrink, "--recipe", self.write("r1.json", {"install_scripts_required": "x"})),
            ("check", shrink, "--recipe", self.write("r2.json", "[" * 100000)),
            ("check", shrink, "--registry", "http://registry.npmjs.org/"),
            ("check", shrink, "--registry", "https://registry.npmjs.org:99999/"),
            ("check", shrink, "--registry"),
            ("check", shrink, "--policy", self.write("p0.json", {})),
            ("store", wrong_name, self.fx.out, "--mirror", self.fx.mirror),
            ("store", shrink, self.fx.out, "--mirror", empty_mirror),
            ("store", shrink, os.path.join(self.base, "no-out"), "--mirror", self.fx.mirror),
            ("store", shrink, self.fx.out, "--mirror", self.fx.mirror, "--policy", self.write("p1.json", [])),
            ("store", shrink, self.fx.out, "--mirror", self.fx.mirror,
             "--policy", self.write("p2.json", {"operating": {"deps_bytes": {"value": "1"}}})),
            ("store", shrink, self.fx.out, "--mirror", self.fx.mirror,
             "--policy", self.write("p3.json", {"constitutional": {"license_allowlist": "MIT"}})),
            ("store", shrink, self.fx.out, "--mirror", self.fx.mirror,
             "--policy", self.write("p4.json", {"constitutional": {"license_exceptions": {"a==1": "MIT"}}})),
            ("store", shrink, self.fx.out, "--mirror", self.fx.mirror, "--mirror", self.fx.mirror),
            ("fetch", shrink, self.fx.out, "--mirror", self.fx.mirror),
            ("verify", self.fx.out, "--registry", REG),
            ("nonsense",),
            (),
        ]
        for args in cases:
            code, out = self.run_cli(*args)
            self.assertEqual(code, 2, (args, out))
            self.assertEqual(list(out), ["error"], args)
            self.assertFalse(out["error"].startswith("internal error"), (args, out))
        self.assertEqual(self.run_cli("check", lock)[0], 0)

    def test_unexpected_exception_is_exit_2_not_refusal(self):
        lock = self.fx.write_lock()
        buf = io.StringIO()
        with mock.patch.object(N, "check", side_effect=KeyError("boom")), mock.patch.object(sys, "stdout", buf):
            code = N.main(["check", lock])
        self.assertEqual(code, 2)
        self.assertTrue(json.loads(buf.getvalue())["error"].startswith("internal error: KeyError"))


def vtgz(files: dict, gz_mtime: int = 0) -> bytes:
    """A gzip tar with a fixed gzip header (``mtime``), members under ``package/``."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name, content in files.items():
            data = json.dumps(content).encode() if isinstance(content, dict) else content
            info = tarfile.TarInfo("package/" + name)
            info.mtime, info.size = 0, len(data)
            tar.addfile(info, io.BytesIO(data))
    return gzip.compress(buf.getvalue(), mtime=gz_mtime)


def expected_address(rows: list[tuple[str, str]]) -> str:
    """Recomputed by hand: ``[{"integrity":..,"path":..}]`` sorted by path, no spaces, UTF-8."""
    def q(v):
        return json.dumps(v, ensure_ascii=False)
    body = ",".join('{"integrity":%s,"path":%s}' % (q(i), q(p)) for p, i in sorted(rows, key=lambda r: r[0]))
    return "sha256:" + hashlib.sha256(("[" + body + "]").encode("utf-8")).hexdigest()


class TestNpmlock(unittest.TestCase):
    """Group ``npmlock`` (tohum/29g): ``fetch LOCK MIRROR``, stdin ``{registry_egress, install_scripts_required}``."""

    def setUp(self):
        self.base = writable_base("npmlock-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.mirror = os.path.join(self.base, "mirror")
        os.makedirs(self.mirror)
        self.stdin = {"registry_egress": [REG], "install_scripts_required": ["gyp-thing@1.2.0"]}
        # keys deliberately not in sorted order
        self.packages = {"": {"name": "toy", "version": "1.0.0"}}
        self.add("node_modules/zeta", "zeta", "1.0.0", {"license": "MIT"})
        self.add("node_modules/@scope/util", "@scope/util", "2.0.0", {"license": "Apache-2.0"})
        self.add("node_modules/zeta/node_modules/inner", "inner", "0.1.0", {})
        self.add("node_modules/gyp-thing", "gyp-thing", "1.2.0",
                 {"license": {"type": "ISC"}, "scripts": {"postinstall": "node-gyp rebuild"}},
                 extra={"binding.gyp": b"{}"}, hasInstallScript=True)

    def add(self, key, name, version, manifest, extra=None, data=None, resolved=None, **entry):
        files = {"package.json": dict({"name": name, "version": version}, **manifest)}
        files.update(extra or {})
        data = vtgz(files) if data is None else data
        u = resolved or url(name, version)
        self.put(u, data)
        self.packages[key] = dict({"version": version, "resolved": u, "integrity": sri(data)}, **entry)
        return data

    def put(self, u, data):
        path = os.path.join(self.mirror, *u.split("://", 1)[1].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def lock_text(self, packages=None, **dump):
        return json.dumps({"name": "toy", "lockfileVersion": 3, "requires": True,
                           "packages": self.packages if packages is None else packages}, **dump)

    def write(self, text, name="package-lock.json"):
        path = os.path.join(self.base, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def run_fetch(self, lock=None, mirror=None, stdin=None, raw_stdin=None, args=None):
        lock = lock if lock is not None else self.write(self.lock_text())
        argv = args if args is not None else ["fetch", lock, mirror or self.mirror]
        proc = subprocess.run([sys.executable, "-m", "runner.deps_npm", *argv], cwd=REFEREE,
                              input=raw_stdin if raw_stdin is not None else json.dumps(stdin or self.stdin),
                              capture_output=True, text=True, timeout=120)
        lines = proc.stdout.splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        self.assertEqual(proc.stderr, "")
        return proc.returncode, json.loads(lines[-1])

    def good_rows(self):
        return [(k, v["integrity"]) for k, v in self.packages.items() if k]

    def snapshot(self):
        out = {}
        for root, dirs, files in os.walk(self.base):
            for n in dirs + files:
                st = os.lstat(os.path.join(root, n))
                out[os.path.join(root, n)] = (st.st_size, st.st_mtime_ns)
        return out

    def test_integrity_good_and_one_byte(self):
        lock = self.write(self.lock_text())
        before = self.snapshot()
        code, out = self.run_fetch(lock)
        self.assertEqual(self.snapshot(), before)  # nothing written next to the lock or in the mirror
        self.assertEqual(code, 0, out)
        self.assertEqual(out, {
            "ok": True, "rejected": [], "artefact": expected_address(self.good_rows()),
            "licenses": [
                {"path": "node_modules/@scope/util", "name": "@scope/util", "version": "2.0.0",
                 "license": "Apache-2.0"},
                {"path": "node_modules/gyp-thing", "name": "gyp-thing", "version": "1.2.0", "license": None},
                {"path": "node_modules/zeta", "name": "zeta", "version": "1.0.0", "license": "MIT"},
                {"path": "node_modules/zeta/node_modules/inner", "name": "inner", "version": "0.1.0",
                 "license": None}]})
        path = os.path.join(self.mirror, "registry.npmjs.org", "zeta", "-", "zeta-1.0.0.tgz")
        with open(path, "rb") as fh:
            orig = fh.read()
        changed = bytearray(orig)
        changed[4] ^= 0x01  # gzip header MTIME byte
        self.assertEqual(gzip.decompress(bytes(changed)), gzip.decompress(orig))
        with open(path, "wb") as fh:
            fh.write(bytes(changed))
        self.assertEqual(self.run_fetch(lock), (1, {"ok": False, "rejected": ["integrity_mismatch:node_modules/zeta"],
                                                    "artefact": None, "licenses": None}))

    def test_install_script_unmarked(self):
        self.add("node_modules/post", "post", "1.0.0", {"scripts": {"postinstall": "node x.js"}})
        self.add("node_modules/pre", "pre", "1.0.0", {"scripts": {"preinstall": "node x.js"}})
        self.add("node_modules/inst", "inst", "1.0.0", {"scripts": {"install": "node x.js"}})
        self.add("node_modules/gyp", "gyp", "1.0.0", {}, extra={"binding.gyp": b"{}"})
        self.add("node_modules/flag", "flag", "1.0.0", {}, hasInstallScript=True)
        self.add("node_modules/test-only", "test-only", "1.0.0", {"scripts": {"test": "x", "prepare": "y"}})
        stdin = dict(self.stdin, install_scripts_required=["gyp-thing@1.2.0", "node_modules/post", "pre", "inst@2.0.0"])
        code, out = self.run_fetch(stdin=stdin)
        self.assertEqual((code, out["rejected"]), (1, ["install_script_unmarked:node_modules/%s" % n
                                                       for n in ("flag", "gyp", "inst", "post", "pre")]))
        self.assertIsNone(out["artefact"])
        stdin["install_scripts_required"] += ["post@1.0.0", "pre@1.0.0", "inst@1.0.0", "gyp@1.0.0", "flag@1.0.0"]
        self.assertEqual(self.run_fetch(stdin=stdin)[0], 0)
        self.assertEqual(self.run_fetch(stdin=dict(self.stdin, install_scripts_required=[]))[1]["rejected"],
                         ["install_script_unmarked:node_modules/%s" % n
                          for n in ("flag", "gyp", "gyp-thing", "inst", "post", "pre")])

    def test_registry_not_allowed(self):
        for i, host in enumerate(("registry.npmjs.org.evil.com", "registry.npmjs.orgx")):
            self.add("node_modules/look%d" % i, "look%d" % i, "1.0.0", {},
                     resolved="https://%s/look%d/-/look%d-1.0.0.tgz" % (host, i, i))
        self.add("node_modules/plain", "plain", "1.0.0", {},
                 resolved="http://registry.npmjs.org/plain/-/plain-1.0.0.tgz")
        self.add("node_modules/upper", "upper", "1.0.0", {},
                 resolved="https://Registry.npmjs.org/upper/-/upper-1.0.0.tgz")
        code, out = self.run_fetch()
        self.assertEqual((code, out["rejected"]), (1, ["registry_not_allowed:node_modules/%s" % n
                                                       for n in ("look0", "look1", "plain", "upper")]))
        # the same tarballs pass once their registry is allowed: only the prefix stopped them
        stdin = dict(self.stdin, registry_egress=[REG, "https://registry.npmjs.org.evil.com/",
                                                  "https://registry.npmjs.orgx/", "https://Registry.npmjs.org/"])
        code, out = self.run_fetch(stdin=stdin)
        self.assertEqual(out["rejected"], ["registry_not_allowed:node_modules/plain"])
        # a path prefix is a prefix of the whole URL, '/' included
        del self.packages["node_modules/plain"], self.packages["node_modules/upper"]
        del self.packages["node_modules/look0"], self.packages["node_modules/look1"]
        self.add("node_modules/sub", "sub", "1.0.0", {},
                 resolved="https://npm.example/registry-evil/sub/-/sub-1.0.0.tgz")
        self.add("node_modules/ok", "ok", "1.0.0", {}, resolved="https://npm.example/registry/ok/-/ok-1.0.0.tgz")
        stdin = dict(self.stdin, registry_egress=[REG, "https://npm.example/registry/"])
        self.assertEqual(self.run_fetch(stdin=stdin)[1]["rejected"], ["registry_not_allowed:node_modules/sub"])

    def test_git_dependency_and_file_dependency_even_with_integrity(self):
        integrity = self.packages["node_modules/zeta"]["integrity"]
        git = {"g1": "git+ssh://git@github.com/a/b.git#0123", "g2": "git://github.com/a/b.git", "g3": "github:a/b",
               "g4": "git@github.com:a/b.git"}
        files = {"f1": ({"resolved": "file:../local.tgz"}), "f2": {"resolved": "../outside", "link": True},
                 "f3": {"resolved": "/abs/pkg", "link": True}, "f4": {"resolved": "C:\\pkg", "link": True},
                 "f5": {"resolved": "packages/a/../../x", "link": True}}
        for n, u in git.items():
            self.packages["node_modules/" + n] = {"version": "1.0.0", "resolved": u, "integrity": integrity}
        for n, e in files.items():
            self.packages["node_modules/" + n] = dict({"version": "1.0.0", "integrity": integrity}, **e)
        code, out = self.run_fetch()
        self.assertEqual(code, 1)
        self.assertEqual(out["rejected"], sorted(["file_dependency:node_modules/%s" % n for n in files]
                                                 + ["git_dependency:node_modules/%s" % n for n in git]))
        # not a git or file dependency, but nothing of theirs comes from an allowed registry: refused there
        self.packages = {"": {}, "node_modules/inside": {"resolved": "packages/a", "link": True},
                         "packages/a": {"name": "a", "version": "1.0.0"},
                         "node_modules/zeta/node_modules/bundled": {"version": "1.0.0", "inBundle": True},
                         "node_modules/upper": {"version": "1.0.0", "resolved": "GIT+https://x/y.git"}}
        self.assertEqual(self.run_fetch()[1]["rejected"], [
            "registry_not_allowed:node_modules/inside", "registry_not_allowed:node_modules/upper",
            "registry_not_allowed:node_modules/zeta/node_modules/bundled", "registry_not_allowed:packages/a"])

    def test_license_from_tarball(self):
        self.packages["node_modules/zeta"]["license"] = "GPL-3.0"
        self.add("node_modules/copyleft", "copyleft", "3.0.0", {"license": "AGPL-3.0-only"}, license="MIT")
        self.add("node_modules/nolicense", "nolicense", "1.0.0", {}, license="MIT")
        code, out = self.run_fetch()
        self.assertEqual(code, 0, out)  # a report, not a gate
        lic = {r["path"]: r["license"] for r in out["licenses"]}
        self.assertEqual((lic["node_modules/zeta"], lic["node_modules/copyleft"], lic["node_modules/nolicense"]),
                         ("MIT", "AGPL-3.0-only", None))
        self.assertEqual([r["path"] for r in out["licenses"]], sorted(r["path"] for r in out["licenses"]))

    def test_same_lock_same_address(self):
        code, out = self.run_fetch(self.write(self.lock_text(indent=2)))
        self.assertEqual(code, 0, out)
        self.assertEqual(out["artefact"], expected_address(self.good_rows()))
        reordered = {k: dict(reversed(list(v.items()))) for k, v in reversed(list(self.packages.items()))}
        compact = json.dumps({"packages": reordered, "requires": True, "lockfileVersion": 3, "name": "toy"},
                             separators=(",", ":"))
        self.assertEqual(self.run_fetch(self.write(compact, "other.json"))[1]["artefact"], out["artefact"])
        # another tarball for one package: another integrity, another address
        self.add("node_modules/zeta", "zeta", "1.0.0", {"license": "MIT", "description": "changed"})
        code, out2 = self.run_fetch()
        self.assertEqual(code, 0, out2)
        self.assertNotEqual(out2["artefact"], out["artefact"])
        self.assertEqual(out2["artefact"], expected_address(self.good_rows()))

    def test_first_failing_check_is_the_reason_in_order(self):
        bad = "sha512-" + base64.b64encode(hashlib.sha512(b"other").digest()).decode()
        script = {"scripts": {"postinstall": "x"}}
        self.packages.update({
            "node_modules/a": {"version": "1.0.0", "resolved": "git+file:../a", "link": True, "integrity": bad},
            "node_modules/b": {"version": "1.0.0", "resolved": "file:../b", "integrity": bad},
            "node_modules/c": {"version": "1.0.0", "resolved": "../c", "link": True, "integrity": bad},
            "node_modules/d": {"version": "1.0.0", "resolved": "https://other.example/d/-/d-1.0.0.tgz",
                               "integrity": bad, "hasInstallScript": True},
            "node_modules/e": {"version": "1.0.0", "resolved": url("e", "1.0.0"), "integrity": bad,
                               "hasInstallScript": True},
        })
        self.put("https://other.example/d/-/d-1.0.0.tgz", vtgz({"package.json": {"name": "d", "version": "1.0.0"}}))
        self.add("node_modules/f", "f", "1.0.0", script)
        self.packages["node_modules/f"]["integrity"] = bad
        self.add("node_modules/g", "g", "1.0.0", script)
        # an on-registry URL that climbs out of the mirror cannot be in it, even where the file exists
        escape = REG + "../../secret.tgz"
        data = vtgz({"package.json": {"name": "h", "version": "1.0.0"}})
        with open(os.path.join(self.base, "secret.tgz"), "wb") as fh:
            fh.write(data)
        self.packages["node_modules/h"] = {"version": "1.0.0", "resolved": escape, "integrity": sri(data)}
        code, out = self.run_fetch()
        self.assertEqual((code, out["rejected"]), (1, [
            "file_dependency:node_modules/b", "file_dependency:node_modules/c", "git_dependency:node_modules/a",
            "install_script_unmarked:node_modules/g", "integrity_mismatch:node_modules/f",
            "registry_not_allowed:node_modules/d", "tarball_missing:node_modules/e",
            "tarball_missing:node_modules/h"]))

    def test_integrity_reads_the_sha512_tokens(self):
        zeta = self.packages["node_modules/zeta"]
        data_sha1 = "sha1-" + base64.b64encode(hashlib.sha1(b"x").digest()).decode()
        for integrity, ok in ((zeta["integrity"] + " " + data_sha1, True),
                              (sri(b"x", "sha256") + " " + zeta["integrity"], True),
                              (zeta["integrity"].replace("sha512", "sha256"), False),
                              (data_sha1, False), ("", False), (None, False),
                              (zeta["integrity"] + " " + sri(b"x"), False)):
            if integrity is None:
                zeta.pop("integrity", None)
            else:
                zeta["integrity"] = integrity
            code, out = self.run_fetch()
            self.assertEqual(code, 0 if ok else 1, (integrity, out))
            if not ok:
                self.assertEqual(out["rejected"], ["integrity_mismatch:node_modules/zeta"])

    def test_store_prints_the_same_artefact(self):
        lock = self.write(self.lock_text())
        out_dir = os.path.join(self.base, "out")
        os.mkdir(out_dir)
        proc = subprocess.run([sys.executable, "-m", "runner.deps_npm", "store", lock, out_dir, "--mirror", self.mirror,
                               "--recipe", self.write(json.dumps(self.stdin), "units.json")],
                              cwd=REFEREE, input="", capture_output=True, text=True, timeout=120)
        stored = json.loads(proc.stdout.splitlines()[-1])
        self.assertEqual(proc.returncode, 0, stored)
        self.assertEqual(stored["artefact"], self.run_fetch(lock)[1]["artefact"])
        self.assertEqual(os.listdir(out_dir), [stored["address"]])

    def test_unusable_input_is_exit_2(self):
        good = self.lock_text()
        not_dir = self.write("x", "file")
        cases = [
            dict(lock=os.path.join(self.base, "missing.json")),
            dict(lock=self.base),
            dict(lock=self.write("{", "l1.json")),
            dict(lock=self.write(json.dumps({"lockfileVersion": 2, "packages": self.packages}), "l2.json")),
            dict(lock=self.write(good.replace('"lockfileVersion": 3', '"lockfileVersion": 3.0'), "l3.json")),
            dict(lock=self.write(json.dumps({"lockfileVersion": 3, "packages": []}), "l4.json")),
            dict(lock=self.write(json.dumps({"lockfileVersion": 3, "packages": {"node_modules/a": "x"}}), "l5.json")),
            dict(lock=self.write("[" * 100000, "l6.json")),
            dict(mirror=os.path.join(self.base, "no-mirror")),
            dict(mirror=not_dir),
            dict(raw_stdin=""),
            dict(raw_stdin="{"),
            dict(stdin={"registry_egress": [REG]}),
            dict(stdin={"registry_egress": ["https://registry.npmjs.org"], "install_scripts_required": []}),
            dict(stdin={"registry_egress": ["http://registry.npmjs.org/"], "install_scripts_required": []}),
            dict(stdin={"registry_egress": [REG], "install_scripts_required": [1]}),
            dict(args=["fetch", self.write(good, "l7.json")]),
            dict(args=["fetch", self.write(good, "l8.json"), self.base, "--mirror", self.mirror]),
        ]
        for case in cases:
            code, out = self.run_fetch(**case)
            self.assertEqual(code, 2, (case, out))
            self.assertEqual(list(out), ["error"], case)
            self.assertFalse(out["error"].startswith("internal error"), (case, out))
        # a tarball that matches its integrity but cannot be read: no verdict, not a pass
        for name, data in (("raw", b"not gzip"), ("nopkg", vtgz({"index.js": b"x"})),
                           ("badjson", vtgz({"package.json": b"{"}))):
            packages = {"": {}}
            self.packages = packages
            self.add("node_modules/" + name, name, "1.0.0", {}, data=data)
            code, out = self.run_fetch()
            self.assertEqual((code, list(out)), (2, ["error"]), (name, out))
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            self.packages = {"": {}}
            path = self.put(url("zeta", "1.0.0"), b"x")
            self.add("node_modules/zeta", "zeta", "1.0.0", {})
            os.chmod(path, 0)
            self.assertEqual(self.run_fetch()[0], 2)


if __name__ == "__main__":
    unittest.main()
