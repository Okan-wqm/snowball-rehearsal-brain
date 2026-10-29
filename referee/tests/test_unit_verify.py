"""Test 48 (asama-0/09) and group ``recipe`` (tohum/29d): ``unit.verify``, with the fake runner.

- static check: image ``@sha256``, official ``node`` image of the toolchain's version, the nearest version
  file, ``inputs`` (valid, cover the unit, not reserved, not excluded: MF4), commands, ``services``,
  ``limits`` keys of ``operating{}`` that may tighten but not loosen, the lock and its marks (MF5);
- the run: only the inputs' closure enters the worktree (exclusions apply under ``.``), dependencies come
  from the MF5 artifact taken by its hash and are unpacked without scripts, ``.bin`` links; lint and tests
  3/3 in fresh contained runs without network, with a red control; an insufficient closure, one red
  attempt, a non-deterministic lint, a green red control and every limit are caught;
- the command line: exit 0 / 1 / 2, never a traceback.

The fake runner is ``fake_docker.py`` (Python commands only; what it does not emulate is listed there).
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from profile import unit_verify as U  # noqa: E402
from runner import contained as C  # noqa: E402
from runner import deps_npm as N  # noqa: E402
from fake_docker import FakeDocker  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_deps_npm import sri, tgz, url  # noqa: E402

DIGEST = "@sha256:" + "ab" * 32
IMAGE = "node:20.11.1-bookworm-slim" + DIGEST

LINT = """import sys
print("pkg/a.js:1:1 no-var fix=[0,3]")
sys.exit(1)
"""
TESTS = """import os, sys
sys.path.insert(0, "lib")
import shared
problems = []
if shared.VALUE != 42:
    problems.append("shared")
for p in ("pkg/node_modules/left-pad/index.js",):
    if not os.path.isfile(p):
        problems.append("missing " + p)
link = "pkg/node_modules/.bin/left-pad"
if not (os.path.islink(link) and os.path.isfile(link)):
    problems.append("bin link")
for p in ("other", ".claude", "CLAUDE.md", "vendored", ".git", "pkg/node_modules/stale"):
    if os.path.lexists(p):
        problems.append("present " + p)
if os.path.exists("pkg/node_modules/left-pad/BUILT"):
    print("built")
print("problems:", problems)
sys.exit(1 if problems else 0)
"""
SLEEP = "import time\ntime.sleep(5)\n"


def operating(**over) -> dict:
    values = {"unit_inputs_bytes": 10 ** 6, "deps_bytes": 10 ** 6, "worktree_bytes": 10 ** 7,
              "container_mem_bytes": 512 * 1024 * 1024, "kos_wall_s": 60, "test_total_s": 60,
              "output_bytes": 10 ** 6}
    values.update(over)
    return {k: {"value": v, "band": [1, 10 ** 12]} for k, v in values.items()}


def policy(**over) -> dict:
    return {"operating": operating(**over)}


def recipe(**over) -> dict:
    r = {"unit_id": "pkg", "path": "pkg", "inputs": ["pkg", "lib"], "toolchain": "node@20.11.1",
         "env_image": IMAGE, "lockfiles": ["pkg/package-lock.json"], "install_scripts_required": [],
         "lint_cmd": ["python", "pkg/lint.py"], "test_cmd": ["python", "pkg/run_tests.py"],
         "affected_test_cmd": ["python", "pkg/affected.py"], "services": [], "limits": {}}
    r.update(over)
    return r


RED = {"cmd": ["python", "pkg/red.py"]}



def unknown_limit(name: str) -> str:
    """The reason for a ``limits`` name not in ``operating``, built so no line reads as an assignment."""
    return "limit_key_unknown" + ":" + name

class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-unit-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.tree = os.path.join(self.base, "tree")
        self.pad = tgz({"package.json": {"name": "left-pad", "version": "1.3.0", "license": "MIT",
                                         "bin": "cli.js"},
                        "index.js": b"module.exports = 1\n", "cli.js": b"#!/usr/bin/env node\n"})
        self.lock = {"lockfileVersion": 3, "packages": {
            "": {"name": "pkg", "version": "1.0.0"},
            "node_modules/left-pad": {"version": "1.3.0", "resolved": url("left-pad", "1.3.0"),
                                      "integrity": sri(self.pad)}}}
        write_tree(self.tree, {
            ".nvmrc": "v20.11.1\n",
            "pkg/package.json": {"name": "pkg", "version": "1.0.0"},
            "pkg/package-lock.json": self.lock,
            "pkg/lint.py": LINT, "pkg/run_tests.py": TESTS, "pkg/affected.py": "raise SystemExit(0)\n",
            "pkg/red.py": "raise SystemExit(1)\n",
            "pkg/node_modules/stale/index.js": "stale",
            "lib/shared.py": "VALUE = 42\n",
            "other/big.txt": "x" * 100,
        })
        self.mirror = os.path.join(self.base, "mirror")
        self.put(url("left-pad", "1.3.0"), self.pad)
        self.deps = self.fetch()

    def put(self, u: str, data: bytes) -> None:
        path = os.path.join(self.mirror, *u.split("://", 1)[1].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)

    def fetch(self, marks=None) -> str:
        out = os.path.join(self.base, "deps")
        os.makedirs(out, exist_ok=True)
        report = N.fetch(os.path.join(self.tree, "pkg", "package-lock.json"), out,
                         N.mirror_fetcher(self.mirror), marks=marks)
        self.assertTrue(report["ok"], report)
        return os.path.join(out, report["address"])

    def lock_bytes(self) -> bytes:
        with open(os.path.join(self.tree, "pkg", "package-lock.json"), "rb") as fh:
            return fh.read()

    def write_lock(self, lock: dict) -> None:
        with open(os.path.join(self.tree, "pkg", "package-lock.json"), "w", encoding="utf-8") as fh:
            json.dump(lock, fh)

    def verify(self, r=None, pol=None, runner=None, red=RED, deps="default", **kw) -> dict:
        self.runner = runner or FakeDocker()
        return U.verify(r or recipe(), self.tree, pol or policy(), red,
                        self.deps if deps == "default" else deps, runner=self.runner, base=self.base, **kw)


# ---------------------------------------------------------------- static check

class StaticCheck(Base):
    def reasons(self, pol=None, tree=False, **over) -> list:
        return U.check_recipe(recipe(**over), pol, self.tree if tree else None)

    def test_good_recipe_passes_without_and_with_tree(self):
        self.assertEqual(self.reasons(), [])
        self.assertEqual(self.reasons(pol=policy(), tree=True), [])

    def test_every_field_required_and_no_other(self):
        r = recipe()
        del r["services"]
        r["install_cmd"] = ["npm", "ci"]
        self.assertEqual(U.check_recipe(r), ["missing:services", "field_not_in_recipe:install_cmd"])
        self.assertEqual(U.check_recipe(["not", "an", "object"]), ["malformed:recipe"])

    def test_image_must_be_pinned_official_and_the_toolchain_version(self):
        cases = {
            "node:20.11.1": "image_not_pinned",
            "node:20.11.1@sha256:" + "AB" * 32: "image_not_pinned",
            "node@sha256:" + "ab" * 31: "image_not_pinned",
            "myorg/node:20.11.1" + DIGEST: "image_not_official",
            "ghcr.io/library/node:20.11.1" + DIGEST: "image_not_official",
            "nodejs:20.11.1" + DIGEST: "image_not_official",
            "node:20.11.0" + DIGEST: "image_version_mismatch",
            "node:20.11.10" + DIGEST: "image_version_mismatch",
            "node:20.11.1alpine" + DIGEST: "image_version_mismatch",
            "node" + DIGEST: "image_version_mismatch",
            "node:lts" + DIGEST: "image_version_mismatch",
        }
        for image, reason in cases.items():
            with self.subTest(image=image):
                self.assertEqual(self.reasons(env_image=image), [reason])
        for image in ("node:20.11.1" + DIGEST, "docker.io/library/node:20.11.1-alpine3.19" + DIGEST):
            with self.subTest(image=image):
                self.assertEqual(self.reasons(env_image=image), [])

    def test_toolchain_is_exact_node_version(self):
        for tc in ("node@20", "node@v20.11.1", "python@3.12.0", "node 20.11.1", 20):
            with self.subTest(tc=tc):
                self.assertIn("invalid:toolchain", self.reasons(toolchain=tc))

    def test_inputs(self):
        self.assertEqual(self.reasons(inputs=["lib"]), ["inputs_miss_unit_path", "lockfile_not_in_inputs"])
        self.assertIn("invalid:inputs", self.reasons(inputs=["pkg", "../outside"]))
        self.assertIn("invalid:inputs", self.reasons(inputs=["/pkg"]))
        self.assertIn("invalid:inputs", self.reasons(inputs=[]))
        self.assertIn("invalid:inputs", self.reasons(inputs="pkg"))
        self.assertEqual(self.reasons(inputs=["pkg", ".snowball/x"]), ["reserved_path"])
        self.assertEqual(self.reasons(inputs=["pkg", ".SNOWBALL"]), ["reserved_path"])
        self.assertEqual(self.reasons(inputs=["."]), [])

    def test_commands(self):
        for field in ("lint_cmd", "test_cmd"):
            for bad in ([], "npm test", ["npm", ""], ["npm", 3], ["npm\x00x"], None):
                with self.subTest(field=field, bad=bad):
                    self.assertEqual(self.reasons(**{field: bad}), ["invalid:%s" % field])
        for bad in ([], "npm test", ["npm", ""]):
            with self.subTest(field="affected_test_cmd", bad=bad):
                self.assertEqual(self.reasons(affected_test_cmd=bad), ["invalid:affected_test_cmd"])

    def test_services_empty_in_stage_0(self):
        self.assertEqual(self.reasons(services=["postgres"]), ["services_not_empty"])
        self.assertEqual(self.reasons(services={}), ["services_not_empty"])

    def test_limits_are_operating_keys_that_only_tighten(self):
        self.assertEqual(self.reasons(limits={"cpu_s": 3}), ["limit_key_unknown:cpu_s"])
        self.assertEqual(self.reasons(limits={"kos_wall_s": True}), ["invalid:limits.kos_wall_s"])
        self.assertEqual(self.reasons(limits={"kos_wall_s": 0}), ["invalid:limits.kos_wall_s"])
        self.assertEqual(self.reasons(limits=[]), ["invalid:limits"])
        self.assertEqual(self.reasons(pol=policy(), limits={"kos_wall_s": 61}), ["limit_above_operating:kos_wall_s"])
        tight = policy()
        tight["operating"]["kos_wall_s"]["band"] = [10, 100]
        self.assertEqual(self.reasons(pol=tight, limits={"kos_wall_s": 9}), ["limit_below_band:kos_wall_s"])
        self.assertEqual(self.reasons(pol=tight, limits={"kos_wall_s": 10}), [])
        self.assertEqual(self.reasons(limits={k: 5 for k in U.OPERATING_NAMES}), [])

    def test_lockfiles(self):
        self.assertEqual(self.reasons(lockfiles=["pkg/package-lock.json", "pkg/npm-shrinkwrap.json"]),
                         ["invalid:lockfiles"])
        self.assertEqual(self.reasons(lockfiles=["pkg/yarn.lock"]), ["invalid:lockfiles"])
        self.assertEqual(self.reasons(lockfiles=["other/package-lock.json"]),
                         ["lockfile_not_in_inputs", "lockfile_not_for_unit"])
        self.assertEqual(self.reasons(inputs=["pkg", "lib", "other"], lockfiles=["other/package-lock.json"]),
                         ["lockfile_not_for_unit"])
        self.assertEqual(self.reasons(inputs=["."], lockfiles=["package-lock.json"]), [])

    def test_nearest_version_file_must_be_exact_and_equal(self):
        self.assertEqual(self.reasons(tree=True), [])
        write_tree(self.tree, {"pkg/.node-version": "20.11.0"})
        self.assertEqual(self.reasons(tree=True), ["toolchain_version_mismatch"])
        write_tree(self.tree, {"pkg/.nvmrc": "20.11.1"})
        self.assertEqual(self.reasons(tree=True), [], "in one directory .nvmrc comes before .node-version")
        for text in ("lts/*", "20", "20.11", "node", "20.11.1.1"):
            write_tree(self.tree, {"pkg/.nvmrc": text})
            with self.subTest(text=text):
                self.assertEqual(self.reasons(tree=True), ["version_file_not_exact"])
        os.remove(os.path.join(self.tree, "pkg/.nvmrc"))
        os.remove(os.path.join(self.tree, "pkg/.node-version"))
        os.remove(os.path.join(self.tree, ".nvmrc"))
        write_tree(self.tree, {".tool-versions": "python 3.12.0\nnodejs 20.11.1\n"})
        self.assertEqual(self.reasons(tree=True), [])
        os.remove(os.path.join(self.tree, ".tool-versions"))
        reasons = self.reasons(tree=True)
        self.assertIn("version_file_missing", reasons)

    def test_with_tree_profile_and_lock_are_judged(self):
        write_tree(self.tree, {".claude/settings.json": "{}"})
        self.assertIn("profile:units[0]:input_excluded:.claude", self.reasons(tree=True, inputs=["pkg", ".claude"]))
        self.assertIn("profile:units[0]:input_missing:nope", self.reasons(tree=True, inputs=["pkg", "nope"]))
        write_tree(self.tree, {"other/package.json": {"name": "other"}})
        reasons = self.reasons(tree=True, path="other", inputs=["other", "lib"], lockfiles=["other/package-lock.json"])
        self.assertIn("profile:units[0]:unit_not_eligible:other", reasons)
        self.assertIn("lockfile_missing", reasons)
        lock = copy.deepcopy(self.lock)
        lock["packages"]["node_modules/left-pad"]["hasInstallScript"] = True
        self.write_lock(lock)
        self.assertEqual(self.reasons(tree=True), ["lock:install_script_not_marked:node_modules/left-pad"])
        self.assertEqual(self.reasons(tree=True, install_scripts_required=["left-pad@1.3.0"]), [])
        os.remove(os.path.join(self.tree, "pkg/package-lock.json"))
        os.symlink("../lib/shared.py", os.path.join(self.tree, "pkg/package-lock.json"))
        self.assertIn("lockfile_missing", self.reasons(tree=True))


# ---------------------------------------------------------------- the run

class Run(Base):
    def test_verified_3_of_3_contained_with_only_the_inputs(self):
        report = self.verify()
        self.assertEqual(report["verdict"], "verified", report)
        self.assertEqual(len(report["runs"]["lint"]), 3)
        self.assertEqual(len(report["runs"]["test"]), 3)
        self.assertTrue(all(r["exit"] == 1 for r in report["runs"]["lint"]))
        self.assertTrue(all(r["exit"] == 0 for r in report["runs"]["test"]))
        self.assertTrue(all(r["red_control_exit"] == 1 for r in report["runs"]["test"]))
        self.assertEqual(report["deps_address"], os.path.basename(self.deps))
        self.assertEqual(report["bin_links"], ["pkg/node_modules/.bin/left-pad"])
        self.assertEqual(report["recipe"], recipe())
        self.assertEqual(report["recipe_sha256"], __import__("hashlib").sha256(U.canonical(recipe())).hexdigest())
        calls = self.runner.calls
        self.assertEqual(len(calls), 12, "every command and its red control, each in its own run")
        roots = set()
        for call in calls:
            argv = call["argv"]
            self.assertTrue(C.check_argv(argv)["ok"])
            self.assertEqual(argv[argv.index("--network") + 1], "none")
            self.assertIn(IMAGE, argv)
            self.assertIn("--env", argv)
            self.assertEqual(call["container_env"]["HOME"], "/work/.snowball/home")
            roots.add(call["mounts"][0]["src"])
            self.assertNotIn("affected.py", " ".join(argv))
        self.assertEqual(len(roots), 12, "a fresh host directory per run")
        self.assertFalse(any(os.path.exists(r) for r in roots), "run directories are removed afterwards")
        self.assertIn(b"problems: []", calls[3]["stdout"])

    def test_exclusions_apply_under_dot(self):
        write_tree(self.tree, {".claude/x": "x", "CLAUDE.md": "x", "vendored/x.js": "x", ".git/HEAD": "x"})
        target = {"excluded_paths": ["vendored"]}
        r = recipe(inputs=["."])
        report = self.verify(r, target=target)
        self.assertEqual(report["verdict"], "refused", "other/ is an input now")
        self.assertIn(b"problems: ['present other']", self.runner.calls[3]["stdout"])

    def test_insufficient_inputs_closure_is_refused(self):
        report = self.verify(recipe(inputs=["pkg"]))
        self.assertEqual(report["verdict"], "refused")
        self.assertEqual(report["reasons"], ["test_red:1", "test_red:2", "test_red:3"])
        self.assertNotIn("recipe", report)

    def test_one_red_attempt_of_three_is_refused(self):
        inner = FakeDocker()
        seen = []

        def flaky(argv, env, timeout):
            res = inner(argv, env, timeout)
            if argv[-1] == "pkg/run_tests.py":
                seen.append(1)
                if len(seen) == 2:
                    return C.RunnerResult(1, res.stdout, res.stderr, False)
            return res
        report = self.verify(runner=flaky)
        self.assertEqual(report["reasons"], ["test_red:2"])
        self.assertEqual(report["verdict"], "refused")

    def test_lint_must_finish_and_be_deterministic(self):
        inner = FakeDocker()
        seen = []

        def vary(argv, env, timeout):
            res = inner(argv, env, timeout)
            if argv[-1] == "pkg/lint.py":
                seen.append(1)
                if len(seen) == 3:
                    return C.RunnerResult(res.exit, res.stdout + b"extra\n", res.stderr, False)
            return res
        self.assertEqual(self.verify(runner=vary)["reasons"], ["lint_not_deterministic"])
        write_tree(self.tree, {"pkg/lint.py": "raise SystemExit(2)\n"})
        report = self.verify()
        self.assertEqual(report["reasons"], ["lint_failed:1", "lint_failed:2", "lint_failed:3"])
        write_tree(self.tree, {"pkg/lint.py": "print('clean')\n"})
        self.assertEqual(self.verify()["verdict"], "verified")

    def test_an_invalid_lint_run_is_no_verdict_not_a_lint_difference(self):
        inner = FakeDocker()
        seen = []

        def stall(argv, env, timeout):
            if argv[-1] == "pkg/lint.py":
                seen.append(1)
                if len(seen) == 2:
                    return C.RunnerResult(None, b"", b"", True)
            return inner(argv, env, timeout)
        report = self.verify(runner=stall)
        self.assertEqual((report["verdict"], report["reasons"]), ("no_verdict", ["limit_hit:kos_wall_s"]))

    def test_green_red_control_is_no_verdict(self):
        write_tree(self.tree, {"pkg/green.py": "raise SystemExit(0)\n"})
        report = self.verify(red={"cmd": ["python", "pkg/green.py"]})
        self.assertEqual(report["verdict"], "no_verdict")
        self.assertEqual(report["reasons"], ["red_control_green"])
        with self.assertRaises(U.VerifyError):
            self.verify(red={})

    def test_network_is_none_in_every_run(self):
        write_tree(self.tree, {"pkg/run_tests.py": "import socket\nsocket.create_connection(('127.0.0.1', 9))\n"})
        report = self.verify()
        self.assertEqual(report["reasons"], ["test_red:1", "test_red:2", "test_red:3"])
        self.assertIn(b"Network is unreachable", self.runner.calls[3]["stderr"])

    def test_unit_inputs_bytes(self):
        size = self.verify()["inputs_bytes"]
        self.assertEqual(self.verify(pol=policy(unit_inputs_bytes=size))["verdict"], "verified")
        report = self.verify(pol=policy(unit_inputs_bytes=size - 1))
        self.assertEqual((report["verdict"], report["reasons"]), ("no_verdict", ["limit_hit:unit_inputs_bytes"]))
        self.assertEqual(self.runner.calls, [])
        report = self.verify(recipe(limits={"unit_inputs_bytes": 100}))
        self.assertEqual(report["reasons"], ["limit_hit:unit_inputs_bytes"])

    def test_copy_stops_once_over_unit_inputs_bytes(self):
        write_tree(self.tree, {"lib/%02d.txt" % i: "y" * 1000 for i in range(20)})
        derived = U.D.derive(self.tree)
        staging = os.path.join(self.base, "stage")
        os.mkdir(staging)
        total = U.copy_inputs(self.tree, ["lib"], derived, staging, 1500)
        self.assertLessEqual(total, 2500)
        copied = sum(len(f) for _, _, f in os.walk(staging))
        self.assertLessEqual(copied, 2)

    def test_test_total_s_caps_the_test_command(self):
        write_tree(self.tree, {"pkg/run_tests.py": SLEEP})
        timeouts = []
        inner = FakeDocker()

        def record(argv, env, timeout):
            timeouts.append((argv[-1], timeout))
            return inner(argv, env, timeout)
        report = self.verify(recipe(limits={"test_total_s": 1}), runner=record)
        self.assertEqual(report["verdict"], "no_verdict")
        self.assertEqual(report["reasons"], ["limit_hit:test_total_s"])
        self.assertIn(("pkg/run_tests.py", 1), timeouts)
        self.assertIn(("pkg/lint.py", 60), timeouts)
        self.assertLess(report["runs"]["test"][0]["duration_s"], 4)

    def test_kos_wall_s_and_worktree_bytes(self):
        write_tree(self.tree, {"pkg/run_tests.py": SLEEP})
        report = self.verify(pol=policy(kos_wall_s=1, test_total_s=5))
        self.assertEqual(report["reasons"], ["limit_hit:kos_wall_s"])
        report = self.verify(pol=policy(worktree_bytes=300))
        self.assertEqual((report["verdict"], report["reasons"]), ("no_verdict", ["limit_hit:worktree_bytes"]))


class Deps(Base):
    def test_artifact_is_taken_by_its_hash(self):
        blob = os.path.join(self.deps, "tarballs", os.listdir(os.path.join(self.deps, "tarballs"))[0])
        with open(blob, "rb") as fh:
            data = bytearray(fh.read())
        data[-5] ^= 1
        with open(blob, "wb") as fh:
            fh.write(bytes(data))
        report = self.verify()
        self.assertEqual(report["verdict"], "no_verdict")
        self.assertEqual(report["reasons"], ["deps:tarball_mismatch:node_modules/left-pad"])
        self.assertEqual(self.runner.calls, [])

    def test_artifact_must_belong_to_the_trees_lock(self):
        self.lock["packages"][""]["version"] = "1.0.1"
        self.write_lock(self.lock)
        report = self.verify()
        self.assertEqual(report["reasons"], ["deps_lock_mismatch"])
        self.assertEqual(self.runner.calls, [])

    def test_lock_without_packages_needs_no_artifact_and_with_packages_does(self):
        with self.assertRaises(U.VerifyError):
            self.verify(deps=None)
        self.write_lock({"lockfileVersion": 3, "packages": {"": {"name": "pkg"}}})
        write_tree(self.tree, {"pkg/run_tests.py": "print('ok')\n"})
        report = self.verify(deps=None)
        self.assertEqual(report["verdict"], "verified", report)
        self.assertIsNone(report["deps_address"])

    def _evil(self, files: dict) -> None:
        data = tgz(files)
        name = "evil"
        u = url(name, "1.0.0")
        self.put(u, data)
        self.lock["packages"]["node_modules/evil"] = {"version": "1.0.0", "resolved": u, "integrity": sri(data)}
        self.write_lock(self.lock)
        self.deps = self.fetch()

    def test_unsafe_member_names_refuse_the_artifact_and_write_nothing_outside(self):
        for member in ("../../../escaped.txt", "a/../../../../escaped.txt"):
            with self.subTest(member=member):
                self.lock["packages"].pop("node_modules/evil", None)
                self._evil({"package.json": {"name": "evil", "version": "1.0.0"}, member: b"x"})
                report = self.verify()
                self.assertEqual(report["reasons"], ["deps_unpack_unsafe:node_modules/evil"])
                self.assertEqual(report["verdict"], "no_verdict")
                for root, _, files in os.walk(self.base):
                    self.assertNotIn("escaped.txt", files, root)

    def test_links_in_tarballs_are_skipped_and_bins_stay_inside(self):
        self._evil({"package.json": {"name": "evil", "version": "1.0.0", "bin": {"x": "../../../etc/passwd",
                                                                                   "../y": "y.js", "ok": "y.js"}},
                    "link": ("symlink", "/etc/passwd"), "y.js": b"1"})
        staging = os.path.join(self.base, "stage")
        os.makedirs(os.path.join(staging, "pkg"))
        bad, info = U.install_deps(staging, "pkg/package-lock.json", self.deps,
                                   self.lock_bytes(), 10 ** 7)
        self.assertEqual(bad, [])
        self.assertEqual(info["skipped"], 1)
        self.assertFalse(os.path.lexists(os.path.join(staging, "pkg/node_modules/evil/link")))
        self.assertEqual(sorted(info["links"]), ["pkg/node_modules/.bin/left-pad", "pkg/node_modules/.bin/ok"])
        self.assertEqual(os.readlink(os.path.join(staging, "pkg/node_modules/.bin/ok")), "../evil/y.js")
        self.assertEqual(os.stat(os.path.join(staging, "pkg/node_modules/evil/y.js")).st_mode & 0o777, 0o755)

    def test_unpacking_refuses_a_symlink_on_the_way(self):
        staging = os.path.join(self.base, "stage")
        os.makedirs(os.path.join(staging, "pkg"))
        outside = os.path.join(self.base, "outside")
        os.makedirs(outside)
        os.symlink(outside, os.path.join(staging, "pkg", "node_modules"))
        bad, _ = U.install_deps(staging, "pkg/package-lock.json", self.deps,
                                self.lock_bytes(), 10 ** 7)
        self.assertEqual(bad, ["deps_unpack_unsafe:node_modules/left-pad"])
        self.assertEqual(os.listdir(outside), [])

    def test_unpacked_bytes_are_bounded(self):
        self._evil({"package.json": {"name": "evil", "version": "1.0.0"}, "big.bin": b"\0" * 50000})
        report = self.verify(pol=policy(worktree_bytes=20000))
        self.assertEqual(report["reasons"], ["limit_hit:worktree_bytes"])
        self.assertEqual(self.runner.calls, [])

    def test_marked_install_scripts_run_contained_before_the_runs(self):
        self.lock["packages"]["node_modules/left-pad"]["hasInstallScript"] = True
        self.write_lock(self.lock)
        self.deps = self.fetch(marks=["left-pad@1.3.0"])
        inner = FakeDocker()
        npm = []

        def runner(argv, env, timeout):
            image_at = argv.index(IMAGE)
            if argv[image_at + 1] == "npm":
                npm.append(argv[image_at + 1:])
                work = argv[argv.index("--mount") + 1].split(",")[1][len("src="):]
                with open(os.path.join(work, "pkg/node_modules/left-pad/BUILT"), "w") as fh:
                    fh.write("1")
                return C.RunnerResult(self.npm_exit, b"", b"", False)
            return inner(argv, env, timeout)
        self.npm_exit = 0
        report = self.verify(recipe(install_scripts_required=["left-pad@1.3.0"]), runner=runner)
        self.assertEqual(report["verdict"], "verified", report)
        self.assertEqual(npm, [["npm", "--prefix", "/work/pkg", "rebuild", "--offline", "--foreground-scripts",
                                "left-pad"]])
        self.assertIn(b"built", inner.calls[-1]["stdout"], "the runs start from the install's worktree")
        self.assertEqual(report["install"]["exit"], 0)
        self.npm_exit = 1
        report = self.verify(recipe(install_scripts_required=["left-pad@1.3.0"]), runner=runner)
        self.assertEqual((report["verdict"], report["reasons"]), ("refused", ["install_scripts_failed"]))
        self.assertEqual(report["runs"], {"lint": [], "test": []})


# ---------------------------------------------------------------- command line

class Cli(Base):
    def cli(self, *args) -> tuple[int, dict, str]:
        proc = subprocess.run([sys.executable, "-m", "profile.unit_verify"] + list(args), cwd=REFEREE,
                              capture_output=True, text=True, timeout=120)
        lines = proc.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        return proc.returncode, json.loads(lines[0]), proc.stderr

    def file(self, name: str, obj) -> str:
        path = os.path.join(self.base, name)
        with open(path, "w", encoding="utf-8") as fh:
            if isinstance(obj, str):
                fh.write(obj)
            else:
                json.dump(obj, fh)
        return path

    def test_check_is_the_vector_form(self):
        code, out, _ = self.cli("check", self.file("r.json", recipe()), self.file("p.json", policy()))
        self.assertEqual((code, out), (0, {"ok": True, "reasons": []}))
        code, out, _ = self.cli("check", self.file("r.json", recipe(env_image="node:20.11.1")),
                                self.file("p.json", policy()))
        self.assertEqual((code, out), (1, {"ok": False, "reasons": ["image_not_pinned"]}))

    def test_unusable_input_is_exit_2(self):
        pol = self.file("pol.json", policy())
        for args in (["check", self.file("bad0.json", "{not json"), pol],
                     ["check", self.file("deep1.json", "[" * 100000 + "]" * 100000), pol],
                     ["check", os.path.join(self.base, "missing.json"), pol],
                     ["check", self.file("r2.json", recipe())],
                     ["check", self.file("r3.json", recipe()), "--policy", pol],
                     ["check", self.file("r4.json", recipe()), pol, "--tree", self.tree],
                     ["verify", self.file("v7.json", {"recipe": recipe()})],
                     ["verify", self.file("v8.json", {"recipe": recipe(), "tree": self.tree, "policy": policy(),
                                                      "red_control": RED}), "extra"],
                     ["check"], ["frobnicate", "x"]):
            with self.subTest(args=args):
                code, out, _ = self.cli(*args)
                self.assertEqual(code, 2)
                self.assertIn("error", out)
                self.assertIs(out["ok"], False)

    def test_verify_refusal_is_exit_1_before_any_run(self):
        req = {"recipe": recipe(services=["redis"]), "tree": self.tree, "policy": policy(), "red_control": RED}
        code, out, _ = self.cli("verify", self.file("v.json", req))
        self.assertEqual((code, out["verdict"], out["reasons"]), (1, "refused", ["services_not_empty"]))

    def test_unexpected_exception_is_exit_2_not_a_traceback(self):
        out = __import__("io").StringIO()
        with mock.patch.object(U, "vector_check", side_effect=ZeroDivisionError("boom")), \
                mock.patch.object(sys, "stdout", out):
            code = U.main(["check", self.file("r.json", recipe()), self.file("p.json", policy())])
        self.assertEqual(code, 2)
        self.assertIn("internal error: ZeroDivisionError", out.getvalue())


# ---------------------------------------------------------------- group recipe (tohum/29g), vector form

class VectorRecipe(unittest.TestCase):
    """``check RECIPE POLICY`` as the seed's runner calls it: a subprocess from ``referee/``, files only."""

    def setUp(self) -> None:
        self.dir = writable_base("t-recipe-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.n = 0

    def run_check(self, r, pol=None) -> tuple[int, dict]:
        self.n += 1
        paths = []
        for name, obj in (("recipe", r), ("policy", policy() if pol is None else pol)):
            path = os.path.join(self.dir, "%s%d.json" % (name, self.n))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(obj if isinstance(obj, str) else json.dumps(obj))
            paths.append(path)
        proc = subprocess.run([sys.executable, "-m", "profile.unit_verify", "check"] + paths, cwd=REFEREE,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        self.assertNotIn("Traceback", proc.stderr)
        last = proc.stdout.strip().splitlines()[-1]
        self.assertNotIn("\n", last)
        return proc.returncode, json.loads(last)

    def expect(self, r, reasons: list, pol=None) -> None:
        code, out = self.run_check(r, pol)
        self.assertEqual((code, out["ok"], out["reasons"]), (0 if not reasons else 1, not reasons, reasons))
        self.assertIs(out["ok"], not reasons)

    def case(self, name: str, r, reasons: list, changed, pol=None, changed_pol=None) -> None:
        """The named case gives ``reasons``; the one-field-changed variant must not give the same result."""
        with self.subTest(case=name):
            self.expect(r, reasons, pol)
            code, out = self.run_check(changed, changed_pol)
            self.assertNotEqual((code, out.get("ok"), out.get("reasons")), (0 if not reasons else 1, not reasons, reasons))

    def test_good(self):
        self.case("good", recipe(), [], recipe(env_image="node:20.11.1"))

    def test_image_tag_only(self):
        self.case("image_tag_only", recipe(env_image="node:20.11.1"), ["image_not_pinned"], recipe())
        for image in ("node:20.11.1-bookworm-slim", "node@sha256:", None, 3):
            with self.subTest(image=image):
                self.expect(recipe(env_image=image), ["image_not_pinned"])
        r = recipe()
        del r["env_image"]
        self.expect(r, ["image_not_pinned"])

    def test_image_digest_malformed(self):
        self.case("image_digest_malformed", recipe(env_image="node:20.11.1@sha256:" + "a" * 63),
                  ["image_not_pinned"], recipe(env_image="node:20.11.1@sha256:" + "a" * 64))
        for digest in ("a" * 65, "A" * 64, "g" * 64, "a" * 64 + " "):
            with self.subTest(digest=digest):
                self.expect(recipe(env_image="node:20.11.1@sha256:" + digest), ["image_not_pinned"])
        self.expect(recipe(env_image="node:20.11.1@sha512:" + "a" * 64), ["image_not_pinned"])

    def test_inputs_missing_unit_dir(self):
        self.case("inputs_missing_unit_dir", recipe(inputs=["lib"]), ["inputs_missing_unit"],
                  recipe(inputs=["lib", "pkg"]))
        for inputs in (["pk", "lib"], ["PKG", "lib"], ["pkg/sub"], [], ["pkgx"]):
            with self.subTest(inputs=inputs):
                self.expect(recipe(inputs=inputs), ["inputs_missing_unit"])
        for inputs in (["pkg/"], ["pkg//"], ["lib", "pkg"]):
            with self.subTest(inputs=inputs):
                self.expect(recipe(inputs=inputs), [])
        self.expect(recipe(path="pkg/sub", inputs=["pkg"]), [])
        self.expect(recipe(path="pkg/sub", inputs=["pkg/su"]), ["inputs_missing_unit"])

    def test_inputs_agent_config(self):
        self.case("inputs_agent_config", recipe(inputs=["pkg", ".Claude"]), ["input_excluded:.Claude"],
                  recipe(inputs=["pkg", ".Claudex"]))
        for e in (".claude", ".CLAUDE/settings.json", "pkg/.vscode", ".DevContainer/x", "CLAUDE.md",
                  "docs/claude.MD", "Agents.md", "pkg/.MCP.json", ".envrc", ".ENVRC/", "a/.vscode/b"):
            with self.subTest(input=e):
                self.expect(recipe(inputs=["pkg", e]), ["input_excluded:%s" % e])
        for e in ("claude", "CLAUDE.md.bak", "CLAUDE.md/notes", "pkg/.envrc.d", "x.mcp.json"):
            with self.subTest(input=e):
                self.expect(recipe(inputs=["pkg", e]), [])

    def test_inputs_not_plain(self):
        self.case("inputs_not_plain", recipe(inputs=["pkg", "/etc"]), ["input_not_plain:/etc"],
                  recipe(inputs=["pkg", "etc"]))
        for e in ("/pkg", "lib\\x", "./lib", "lib/./x", "lib/..", "../lib", "."):
            with self.subTest(input=e):
                self.expect(recipe(inputs=["pkg", e]), ["input_not_plain:%s" % e])
        for e in ("..lib", "lib.", "lib/...", "lib/"):
            with self.subTest(input=e):
                self.expect(recipe(inputs=["pkg", e]), [])
        self.expect(recipe(inputs=["/pkg"]), ["input_not_plain:/pkg", "inputs_missing_unit"])

    def test_limit_key_unknown(self):
        self.case("limit_key_unknown", recipe(limits={"cpu_s": 3}), [unknown_limit("cpu_s")],
                  recipe(limits={"kos_wall_s": 3}))
        self.expect(recipe(limits={"kos_wall_s": -1, "test_total_s": "x", "output_bytes": None}), [])
        pol = policy()
        del pol["operating"]["test_total_s"]
        self.expect(recipe(limits={"test_total_s": 5}), [unknown_limit("test_total_s")], pol)
        self.expect(recipe(limits={"Kos_wall_s": 5}), [unknown_limit("Kos_wall_s")])
        self.expect(recipe(limits={"z": 1, "a": 1}), [unknown_limit("a"), unknown_limit("z")])

    def test_test_cmd_empty(self):
        self.case("test_cmd_empty", recipe(test_cmd=[]), ["cmd_empty:test_cmd"], recipe(test_cmd=["npm", "test"]))
        for bad in ([""], ["npm", ""], ["npm", 3], None, "npm test", {}):
            with self.subTest(bad=bad):
                self.expect(recipe(test_cmd=bad), ["cmd_empty:test_cmd"])
        r = recipe()
        del r["test_cmd"]
        self.expect(r, ["cmd_empty:test_cmd"])

    def test_cmd_entries(self):
        for field in ("lint_cmd", "affected_test_cmd"):
            self.case("cmd_entries:" + field, recipe(**{field: []}), ["cmd_empty:%s" % field],
                      recipe(**{field: ["npm", "run", "x"]}))
            for bad in ([""], [None], "x"):
                with self.subTest(field=field, bad=bad):
                    self.expect(recipe(**{field: bad}), ["cmd_empty:%s" % field])
            r = recipe()
            del r[field]
            self.expect(r, ["cmd_empty:%s" % field])
        self.expect(recipe(lint_cmd=[], test_cmd=[""], affected_test_cmd=[]),
                    ["cmd_empty:affected_test_cmd", "cmd_empty:lint_cmd", "cmd_empty:test_cmd"])

    def test_services_not_empty(self):
        self.case("services", recipe(services=["redis"]), ["services_not_empty"], recipe(services=[]))
        for bad in ({}, None, "", [[]]):
            with self.subTest(bad=bad):
                self.expect(recipe(services=bad), ["services_not_empty"])
        r = recipe()
        del r["services"]
        self.expect(r, ["services_not_empty"])

    def test_every_reason_listed_and_sorted(self):
        r = recipe(env_image="node:20", inputs=["/z", "lib", ".claude", "./.vscode"], lint_cmd=[],
                   affected_test_cmd=None, services=["db"], limits={"zz": 1, "aa": 1})
        self.expect(r, ["cmd_empty:affected_test_cmd", "cmd_empty:lint_cmd", "image_not_pinned",
                        "input_excluded:./.vscode", "input_excluded:.claude", "input_not_plain:./.vscode",
                        "input_not_plain:/z", "inputs_missing_unit", unknown_limit("aa"),
                        unknown_limit("zz"), "services_not_empty"])
        self.expect(recipe(inputs=["pkg", "lib", "lib"]), [])
        self.expect(recipe(inputs=["pkg", "/x", "/x"]), ["input_not_plain:/x"])

    def test_other_fields_are_not_looked_at(self):
        self.expect(recipe(toolchain="python@3", lockfiles="x", unit_id=None, install_cmd=["npm", "ci"]), [])

    def test_unusable_input_is_exit_2(self):
        good = recipe()
        cases = [("recipe_not_json", "{x", policy()), ("recipe_list", [good], policy()),
                 ("policy_not_json", good, "{"), ("policy_no_operating", good, {}),
                 ("operating_list", good, {"operating": []}), ("policy_list", good, [])]
        for field, bad in (("path", None), ("path", 3), ("inputs", None), ("inputs", "pkg"), ("inputs", ["pkg", 1]),
                           ("limits", None), ("limits", [])):
            r = recipe()
            if bad is None:
                del r[field]
            else:
                r[field] = bad
            cases.append(("%s=%r" % (field, bad), r, policy()))
        for name, r, pol in cases:
            with self.subTest(case=name):
                code, out = self.run_check(r, pol)
                self.assertEqual(code, 2)
                self.assertIs(out["ok"], False)
                self.assertNotIn("reasons", out)
        proc = subprocess.run([sys.executable, "-m", "profile.unit_verify", "check",
                               os.path.join(self.dir, "missing.json"), os.path.join(self.dir, "missing2.json")],
                              cwd=REFEREE, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
