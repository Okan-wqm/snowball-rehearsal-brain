"""(B)'s flow rehearsal (asama-0/08's order of cycles, 10a): ``loop.job``'s five jobs run after run, from no heads, on
one in-process world, until the flow stalls; the test states where it stalls today.

**The world.** A toy (``t1``) and a copy (``c1``) in ``setup/summary.json``'s ``targets[]`` (toy first), each an
in-process GitHub (``fake_github``, with git's object ids) holding only ``main``; the brain's commit (``referee/``,
each target's ``units.json``, the toy's candidates ``good`` and ``breaks`` with their ``expect.json`` and the copy's
``good``) in ``git_store``'s fake ``git``, which also answers every object and ``ls-remote`` of both GitHubs as they
are at the run's start; one fake Rekor that the root signer of ``yaz`` writes each signed root's entry into, so the
next run's D1 reads it back; the checkout with ``policy.json``, ``bootstrap.json``, ``setup/imports.jsonl``,
``seed/security-ledger.jsonl`` and ``DRILL_SEED`` set in ``yaz``; either no ``seed/drill/revert/`` (the seed as it
is, tohum/26f: no live drill fixtures) or a catalog of this test's (``DRILL_PATCHES``, with the sentinel those patches
turn red, ``test_loop_write.SENTINEL_UNITS``), in ``loop.drill``'s stated place (seed-045). The fake runner runs the
tree's Python (``test_loop_kos.RedAs``), the fake ``claude`` answers the canary.

**A run** (``Flow.run``) is the workflow's order with each job on its own runner: ``cek``; its ``out/pulled`` copied
whole as the ``in/pulled`` of ``getir``, ``kos``, ``cagir`` and ``yaz``; ``getir``'s ``out/deps`` as ``kos``'s
``in/deps``; ``kos``'s ``out/results`` and ``cagir``'s ``out/response`` as ``yaz``'s. A job that is not ``ok`` ends
the run there. The run's record (``Flow.record``) keeps per target what decides the next run: genesis, the merge
and each candidate's reasons, the sentinel's verdict, the drill's action, the gate; and the copy's waiting.

**The stall** is the first run whose record equals the one before it (the flow repeats itself: nothing the next run
reads has moved but the cycle's own rows), or a job that is not ``ok``; no stall within ``MAX_RUNS`` runs fails the
test (a drill that keeps passing never repeats a record: its phases alternate). ``Rehearsal`` asserts every run's
record up to it, so a change that moves (B) one step, or breaks an earlier one, changes this test in the same push.
Today (B) stalls, without the fixtures, with the gate closed on ``#geri-alma`` alone; with them, at the build-break
drill (seed-044). Each run after the genesis also checks that D1 verified the state the run before wrote.

Out of scope, stated: the real runner, git, GitHub, Rekor, Sigstore and model (the jobs' own tests and 10a's live
run); the toy fixture of ``tests/fixtures/toy-repo`` (node; the fake runner runs Python only, so the world's tree is
``test_loop_kos.TREE``); the copy's cycles and the PASS row's write, which the stall here comes before.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import activation_world as AW  # noqa: E402
import fake_claude  # noqa: E402
import git_store as S  # noqa: E402
import test_accepted as TA  # noqa: E402
import test_loop_cagir  # noqa: E402
import yaz_world as YW  # noqa: E402
from fake_github import FakeGitHub  # noqa: E402
from loop import accepted as A  # noqa: E402
from loop import job as J  # noqa: E402
from loop import treehash as T  # noqa: E402
from loop_inputs_world import BOOTSTRAP, install_sigstore, write_bootstrap  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from target import branches as B  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, diff, recipe  # noqa: E402
from test_loop_cek import POLICY, install_listing_git  # noqa: E402
from test_loop_kos import FINDING, TREE, RedAs  # noqa: E402
from test_loop_write import SENTINEL_PY, SENTINEL_UNITS, drill_catalog  # noqa: E402
from test_rekor import entry_for  # noqa: E402
from harness import revert_drill as RD  # noqa: E402
from loop import drill as DR  # noqa: E402

REFEREE_REPO = "o/referee"
TARGETS = (("t1", "toy", "o/toy"), ("c1", "copy", "o/copy"))
MERGE = {"decision": "merge"}
CANDIDATES = {"t1": {"good": (GOOD, MERGE), "breaks": (BREAKS_TEST, {"decision": "reject", "reason": "tests_red"})},
              "c1": {"good": (GOOD, MERGE)}}
# The drill's patches (``test_loop_write.D8``'s, moved to line 2): each turns the sentinel red, rd-lint also adds a
# ``var`` line. They change ``const b``, a line ``good`` leaves as it was, so they apply after its merge.
# rd-build is the catalog's build break: the same red, which stage 0's D7 can only call a test regression.
DRILL_PATCHES = {"rd-test": diff("pkg/a.js", ["const b = 2;"], ["const b = 2; // SENTINEL_RED"], start=2),
                 "rd-lint": diff("pkg/a.js", ["const b = 2;"], ["const b = 2; // SENTINEL_RED", "var z = 2;"], start=2),
                 "rd-build": diff("pkg/a.js", ["const b = 2;"], ["const b = 2; // SENTINEL_RED BUILD"], start=2)}
DRILL_CAUSES = {"rd-test": "test_regression", "rd-lint": "lint_regression", "rd-build": "build_break"}
SHA40 = re.compile(r"\b[0-9a-f]{40}\b")
LISTED = {"brain/state": B.STATE, "brain/integration": B.INTEGRATION, "main": "main"}


class RekorSigner:
    """``yaz``'s root signer: each payload (a root in ASCII, ``ledger.anchor``) gets a Rekor entry recording its
    sha256 (``test_rekor.entry_for``), put into ``rekor`` where the next run's D1 reads it."""

    def __init__(self, rekor: dict, identity: str) -> None:
        self.rekor, self.identity = rekor, identity

    def sign(self, payload: bytes) -> dict:
        uuid, entry = entry_for(hashlib.sha256(payload).hexdigest())
        self.rekor[uuid] = entry
        return {"uuid": uuid, "identity": self.identity}


class Rekor:
    def __init__(self) -> None:
        self.entries: dict = {}

    def entry(self, uuid):
        return self.entries.get(uuid)


class Router:
    """The writer's transport over both GitHubs: a repository's path to its own, and the App's two routes (one App
    installed on both targets, tohum/25a row 3) answered here."""

    def __init__(self, hubs: dict[str, FakeGitHub]) -> None:
        self.hubs = hubs

    def __call__(self, method, path, body):
        if (method, path) == ("GET", "/app"):
            return 200, {"id": AW.APP_ID, "slug": "snowball-writer"}
        if (method, path) == ("GET", "/installation/repositories"):
            return 200, {"total_count": len(self.hubs), "repositories": [{"full_name": r} for r in self.hubs]}
        for repo, hub in self.hubs.items():
            if path.startswith("/repos/%s/" % repo):
                return hub(method, path, body)
        return 404, {"message": "Not Found"}


def _candidate(diff: bytes, expect: dict) -> dict[str, bytes]:
    return {"diff.patch": diff, "finding.json": json.dumps(FINDING).encode(),
            "expect.json": json.dumps(expect).encode() + b"\n"}


class Flow:
    """The world above and its runs, under ``base``."""

    def __init__(self, base: str, drill: dict | None = None, seed: str = "7" * 64) -> None:
        """``drill``: the checkout's drill catalog ``{instance id: cause}`` (its patches ``DRILL_PATCHES``, the
        units' sentinel ``SENTINEL_UNITS``, which those patches turn red), or none; ``seed``: ``DRILL_SEED``."""
        self.base, self.runs, self.seed = base, 0, seed
        self.state_heads: list = []  # the toy's brain/state head after each run
        self.work = os.path.join(base, "checkout")
        self.brain = {"referee/loop/job.py": b"x = 1\n", "referee/a.py": b"a\n"}
        units = SENTINEL_UNITS if drill else {"units": [recipe()]}
        for tid, cands in CANDIDATES.items():
            self.brain["targets/%s/units.json" % tid] = json.dumps(units).encode()
            for cid, (diff, expect) in cands.items():
                self.brain.update({"candidates/%s/%s/%s" % (tid, cid, f): d
                                   for f, d in _candidate(diff, expect).items()})
        self.brain_objects, self.brain_sha = S.store(self.brain)
        tree_files = dict(TREE, **({"pkg/sentinel.py": SENTINEL_PY} if drill else {}))
        files = {p: (json.dumps(v) if isinstance(v, dict) else v).encode() for p, v in tree_files.items()}
        self.hubs: dict[str, FakeGitHub] = {}
        targets = []
        for tid, kind, repo in TARGETS:
            hub = FakeGitHub(repo, required_check=B.CHECK)
            hub.refs["main"] = hub.seed_files(files, msg="main")
            hub.overrides.update({k: v for k, v in AW.facts(kind, repo).items()
                                  if not k[1].startswith(("/app", "/installation"))})
            self.hubs[repo] = hub
            targets.append({"id": tid, "kind": kind, "repo": repo, "excluded_paths": [], "unit_candidates": [],
                            "base_sha": hub.refs["main"], "identifiers": []})
        summary = {"seed_epochs": [{"commit": "1" * 40, "spec_tohum_sha256": "2" * 64, "seed_sha256": "3" * 64,
                                    "bootstrap_sha256": "4" * 64}], "targets": targets}
        tree = T.digest([(p, "file", d) for p, d in self.brain.items()])
        write_tree(self.work, {"setup/summary.json": json.dumps(summary),
                               "setup/imports.jsonl": TA.chained([TA.import_row(tree, self.brain_sha)]).decode(),
                               J.SECURITY_LEDGER: YW.chained([{"row_id": "s1", "part": "security", "kind": "note",
                                                               "payload": {}}]).decode()})
        with open(os.path.join(self.work, "policy.json"), "wb") as fh:
            fh.write(POLICY)
        write_bootstrap(self.work)
        if drill:
            self.catalog = drill_catalog(drill)
            write_tree(os.path.join(self.work, *DR.CATALOG_DIR),
                       dict({DR.CATALOG: self.catalog},
                            **{i["patch"]: DRILL_PATCHES[i["id"]].decode() for i in self.catalog["instances"]}))
        self.rekor = Rekor()
        self.signer = RekorSigner(self.rekor.entries, A.workflow_identity(REFEREE_REPO, A.LOOP_WORKFLOW))
        zipped = TA.zip_of({"result.json": TA.result(self.brain_sha), "result.json.sigstore.json": b"{}"})
        self.api = TA.FakeApi([TA.artifact(11, "2026-11-01T00:00:00Z")], zipped)

    def _git(self, root: str) -> str:
        """The fake ``git`` of this run: every object of the brain and of both GitHubs' refs, each repository's
        ``ls-remote`` answer as its refs are now."""
        objects = dict(self.brain_objects)
        listings = {}
        for repo, hub in self.hubs.items():
            objects.update(hub.git_objects(list(hub.refs.values())))
            listings[A.repo_url(repo)] = b"".join(b"%s\trefs/heads/%s\n" % (hub.refs[b].encode(), b.encode())
                                                  for b in LISTED.values() if b in hub.refs)
        answers = {sha: S.batch_record(sha, kind, data) for sha, (kind, data) in objects.items()}
        bin_dir = os.path.join(root, "bin")
        os.makedirs(bin_dir)
        S.install_git(bin_dir, answers, listing=b"")
        return install_listing_git(bin_dir, listings)

    def run(self) -> dict:
        """One run of the workflow: ``{job: its line}`` for each job run, in order, up to the first not ``ok``."""
        self.runs += 1
        root = os.path.join(self.base, "run%d" % self.runs)
        temps = {job: os.path.join(root, job) for job in ("cek", "getir", "kos", "cagir", "yaz")}
        os.makedirs(temps["cek"])
        install_sigstore(temps["cek"])
        env = {"RUNNER_TEMP": temps["cek"], "GITHUB_REPOSITORY": REFEREE_REPO, "GITHUB_TOKEN": "t",
               "GITHUB_WORKSPACE": self.work, "PATH": os.environ.get("PATH", "")}
        lines = {"cek": J.run("cek", env, http=self.api, verifier=lambda argv: 0, git=self._git(root),
                              rekor=self.rekor)}
        if not lines["cek"]["ok"]:
            return lines
        for job in ("getir", "kos", "cagir", "yaz"):
            shutil.copytree(os.path.join(temps["cek"], "out", "pulled"), os.path.join(temps[job], "in", "pulled"),
                            symlinks=True)
        lines["getir"] = J.run("getir", {"RUNNER_TEMP": temps["getir"]})
        if not lines["getir"]["ok"]:
            return lines
        shutil.copytree(os.path.join(temps["getir"], "out", "deps"), os.path.join(temps["kos"], "in", "deps"))
        lines["kos"] = J.run("kos", {"RUNNER_TEMP": temps["kos"]}, runner=RedAs())
        if not lines["kos"]["ok"]:
            return lines
        claude = os.path.dirname(fake_claude.install_for_loop(temps["cagir"]))
        fake_claude.behave(claude, test_loop_cagir.result(modelUsage={BOOTSTRAP["rival"]["model"]: {"costUSD": 0.01}}))
        run_id = {"GITHUB_RUN_ID": str(self.runs), "GITHUB_RUN_ATTEMPT": "1"}
        lines["cagir"] = J.run("cagir", dict({"RUNNER_TEMP": temps["cagir"], "CLAUDE_CODE_OAUTH_TOKEN": "t",
                                              "GITHUB_WORKSPACE": self.work}, **run_id))
        if not lines["cagir"]["ok"]:
            return lines
        for job, art in (("kos", "results"), ("cagir", "response")):
            shutil.copytree(os.path.join(temps[job], "out", art), os.path.join(temps["yaz"], "in", art))
        write_tree(os.path.join(temps["yaz"], "control"), {"control.json": {"merge_paused": False}})
        now = YW.NOW + datetime.timedelta(hours=self.runs)
        lines["yaz"] = J.run("yaz", YW.env(temps["yaz"], self.work, GITHUB_REPOSITORY=REFEREE_REPO,
                                           DRILL_SEED=self.seed, **run_id),
                             transport=Router(self.hubs), signer=self.signer, now=lambda: now)
        self.state_heads.append(self.hubs[TARGETS[0][2]].refs.get(B.STATE))
        return lines

    @staticmethod
    def record(lines: dict) -> dict:
        """What the next run depends on, from a run's lines (see the module docstring)."""
        cek = lines["cek"]
        out: dict = {"waiting": [t["target"] for t in cek.get("targets", []) if "waiting" in t]}
        last = list(lines)[-1]
        if not lines[last]["ok"]:
            out["stopped"] = {"job": last, "target": lines[last].get("target"), "reason": lines[last].get("reason"),
                              "reasons": lines[last].get("reasons", [])}
        for t in lines.get("yaz", {}).get("targets", []):
            sentinel = t.get("sentinel")
            out[t["target"]] = {
                "genesis": t.get("written", {}).get("genesis", False), "merge": t.get("merge"),
                "decisions": {cid: d["reasons"] for cid, d in t.get("decisions", {}).items()},
                "sentinel": None if sentinel is None else sentinel["verdict"], "drill": t.get("drill"),
                "gate": t.get("gate"), "done": t.get("done")}
        return out


def seed_choosing(catalog: dict, chosen: dict[str, str]) -> str:
    """A ``DRILL_SEED`` whose key selects ``chosen[run id]`` for each run id (searched, so no selection is written
    here)."""
    for n in range(100000):
        seed = "rehearsal-seed-%d" % n
        if all(RD.key({"seed": seed}, run, catalog)["instance_id"] == i for run, i in chosen.items()):
            return seed
    raise AssertionError("no seed selects %s" % chosen)


def step(record: dict) -> dict:
    """A run's record with commit ids written ``<sha>`` and the drill's line cut to what the flow turns on (its
    action, the planted instance, the judged verdict and reasons): the commitments and keys are the drill's own
    tests' (test_loop_write ``D8``, test_revert_drill)."""
    out = json.loads(SHA40.sub("<sha>", json.dumps(record)))
    for tid in (t for t, _, _ in TARGETS):
        drill = (out.get(tid) or {}).get("drill")
        if drill:
            cut = {k: drill[k] for k in ("action", "why", "instance_id") if k in drill}
            if "judged" in drill:
                cut["judged"] = [drill["judged"]["key"]["instance_id"], drill["judged"]["verdict"],
                                 drill["judged"]["reasons"]]
            out[tid]["drill"] = cut
    return out


def toy(merge=None, decisions=None, sentinel=None, drill=None, gate=None, done=("D5", "D6"), genesis=False) -> dict:
    """The toy's part of an expected record; ``decisions`` default: both candidates' diffs no longer apply (``good``
    merged at the genesis)."""
    stale = ["artefact_hash_mismatch", "kos:patch_does_not_apply"]
    return {"genesis": genesis, "merge": merge, "decisions": decisions or {"breaks": stale, "good": stale},
            "sentinel": sentinel, "drill": drill, "gate": gate, "done": list(done)}


GENESIS = toy(merge="good", decisions={"breaks": ["tests_red"], "good": []}, drill={"action": "off", "why": "genesis"},
              genesis=True)


def closed(**conditions) -> dict:
    names = {"geri_alma": "#geri-alma", "nobetci": "#nobetci #hayatta"}
    return {"verdict": "closed", "conditions": {names[k]: ["toy:" + r for r in v] for k, v in conditions.items()}}


class Rehearsal(unittest.TestCase):
    MAX_RUNS = 14

    def setUp(self) -> None:
        self.base = writable_base("t-rehearsal-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def rehearse(self, flow: Flow) -> list[dict]:
        """Each run's ``step`` up to and including the stall (see the module docstring). After the genesis every
        run's D1 verified the toy's ``brain/state`` that the run before wrote, as an extension of the one before
        that, and its root's entry read from Rekor."""
        records: list[dict] = []
        for _ in range(self.MAX_RUNS):
            lines = flow.run()
            records.append(step(Flow.record(lines)))
            line = lines["cek"]["targets"][0]
            if len(flow.state_heads) > 1:
                previous = flow.state_heads[-3] if len(flow.state_heads) > 2 else None
                self.assertEqual((line["state"]["head"], line["state"]["previous"]),
                                 (flow.state_heads[-2], previous))
                self.assertIn(line["root"]["rekor_uuid"], flow.rekor.entries)
            if "stopped" in records[-1] or records[-1:] == records[-2:-1]:
                return records
        self.fail("no stall in %d runs: %s" % (self.MAX_RUNS, records))

    def test_without_the_drills_fixtures_b_stalls_at_the_drill(self):
        """The seed as it is (tohum/26f: no live drill fixtures, DRILL_SEED set): the toy's genesis merges ``good``
        and rejects ``breaks``, the next run watches the merge green and ends it, and from then on every run is
        the same: the gate stays closed on ``#geri-alma`` alone and the copy waits (26f:33-36: D8 cannot run live
        and #geri-alma cannot be measured until a seed epoch brings the fixtures)."""
        flow = Flow(self.base)
        off = {"action": "off", "why": "fixtures_absent"}
        gate = closed(geri_alma=["drill_inputs_missing"])
        self.assertEqual(self.rehearse(flow), [
            {"waiting": ["c1"], "t1": GENESIS},
            {"waiting": ["c1"], "t1": toy(sentinel="green", drill=off, done=("D5", "D6", "D7"),
                                          gate=closed(nobetci=["sentinel_unfinished:<sha>"],
                                                      geri_alma=["drill_inputs_missing"]))},
            {"waiting": ["c1"], "t1": toy(drill=off, gate=gate)},
            {"waiting": ["c1"], "t1": toy(drill=off, gate=gate)}])
        hub = flow.hubs["o/copy"]
        self.assertEqual(sorted(hub.refs), ["main"])  # the copy was never written

    def test_with_the_drills_fixtures_b_stalls_at_build_break(self):
        """A catalog of the three causes 10a #geri-alma asks for, with a seed that plants rd-test, rd-lint and
        rd-build in turn: each drill is committed, planted as the cycle's one merge, watched red and reverted by
        D7, then revealed and judged. rd-test and rd-lint pass and leave the gate closed on ``build_break`` alone;
        rd-build is reverted as a test regression (stage 0's ``build_ok`` is always true, ``loop.watch.facts``;
        seed-044), so its judgement is ``FAIL`` and ``yaz`` stops red: (B) cannot open the copy's genesis."""
        catalog = drill_catalog(DRILL_CAUSES)
        flow = Flow(self.base, drill=DRILL_CAUSES,
                    seed=seed_choosing(catalog, {"2": "rd-test", "5": "rd-lint", "8": "rd-build"}))
        unshown = ["cause_unshown:%s" % c for c in ("test_regression", "build_break", "lint_regression")]
        wait = {"action": "wait", "why": "drill_unfinished"}
        commit = {"action": "commit"}
        d8 = ("D5", "D6", "D8")
        d78 = ("D5", "D6", "D7", "D8")
        records = self.rehearse(flow)
        self.assertEqual(records[:-1], [
            {"waiting": ["c1"], "t1": GENESIS},
            {"waiting": ["c1"], "t1": toy(sentinel="green", drill=commit, done=d78,
                                          gate=closed(nobetci=["sentinel_unfinished:<sha>"], geri_alma=unshown))},
            {"waiting": ["c1"], "t1": toy(drill={"action": "plant", "instance_id": "rd-test"}, done=d8,
                                          gate=closed(geri_alma=unshown))},
            {"waiting": ["c1"], "t1": toy(sentinel="red", drill=wait, done=d78,
                                          gate=closed(geri_alma=["drill_fail:rd-test:not_reverted"] + unshown))},
            {"waiting": ["c1"], "t1": toy(drill=dict(commit, judged=["rd-test", "PASS", []]), done=d8,
                                          gate=closed(geri_alma=unshown[1:]))},
            {"waiting": ["c1"], "t1": toy(drill={"action": "plant", "instance_id": "rd-lint"}, done=d8,
                                          gate=closed(geri_alma=unshown[1:]))},
            {"waiting": ["c1"], "t1": toy(sentinel="red", drill=wait, done=d78,
                                          gate=closed(geri_alma=["drill_fail:rd-lint:not_reverted"] + unshown[1:]))},
            {"waiting": ["c1"], "t1": toy(drill=dict(commit, judged=["rd-lint", "PASS", []]), done=d8,
                                          gate=closed(geri_alma=unshown[1:2]))},
            {"waiting": ["c1"], "t1": toy(drill={"action": "plant", "instance_id": "rd-build"}, done=d8,
                                          gate=closed(geri_alma=unshown[1:2]))},
            {"waiting": ["c1"], "t1": toy(sentinel="red", drill=wait, done=d78,
                                          gate=closed(geri_alma=["drill_fail:rd-build:not_reverted"] + unshown[1:2]))}])
        self.assertEqual(records[-1]["stopped"], {"job": "yaz", "target": "t1", "reason": "drill_fail", "reasons": []})
        self.assertEqual(records[-1]["t1"]["drill"]["judged"], ["rd-build", "FAIL", ["cause_mismatch"]])
        self.assertEqual(sorted(flow.hubs["o/copy"].refs), ["main"])


if __name__ == "__main__":
    unittest.main()
