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
- ``operating.deps_bytes`` stops the fetch; unusable input is exit 2 with one JSON line, never a traceback.
"""

from __future__ import annotations

import base64
import copy
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
        proc = subprocess.run([sys.executable, "-m", "runner.deps_npm", *args], cwd=REFEREE,
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
        code, out = self.run_cli("fetch", lock, self.fx.out, "--mirror", self.fx.mirror)
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
        code, out = self.run_cli("fetch", lock, self.fx.out, "--mirror", self.fx.mirror)
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
        args = ("fetch", lock, self.fx.out, "--mirror", self.fx.mirror)
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
            ("fetch", wrong_name, self.fx.out, "--mirror", self.fx.mirror),
            ("fetch", shrink, self.fx.out, "--mirror", empty_mirror),
            ("fetch", shrink, os.path.join(self.base, "no-out"), "--mirror", self.fx.mirror),
            ("fetch", shrink, self.fx.out, "--mirror", self.fx.mirror, "--policy", self.write("p1.json", [])),
            ("fetch", shrink, self.fx.out, "--mirror", self.fx.mirror,
             "--policy", self.write("p2.json", {"operating": {"deps_bytes": {"value": "1"}}})),
            ("fetch", shrink, self.fx.out, "--mirror", self.fx.mirror,
             "--policy", self.write("p3.json", {"constitutional": {"license_allowlist": "MIT"}})),
            ("fetch", shrink, self.fx.out, "--mirror", self.fx.mirror,
             "--policy", self.write("p4.json", {"constitutional": {"license_exceptions": {"a==1": "MIT"}}})),
            ("fetch", shrink, self.fx.out, "--mirror", self.fx.mirror, "--mirror", self.fx.mirror),
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


if __name__ == "__main__":
    unittest.main()
