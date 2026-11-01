"""Test 46 (asama-0/09), MF17, D6: ``yaz`` writes the cycle on the target (``loop.write_cycle``, ``loop.job run yaz``),
on the in-process GitHub at ``pulled``'s heads, after ``kos`` ran the candidates with the fake runner; and the
pieces D6 shares with ``activate`` (``ledger.events``, ``target.land``).

- a cycle with a merge: the candidate's branch, pull request, check and merge on ``brain/integration``, then one
  ``brain/state`` commit on the head D1 read: the rows in order (cycle start, decisions, the response's cost row,
  status), the whole ledger of ``ledger.schema``, an append-only extension, the root signed once and its row, the
  ``status.md`` block, and the merge unfinished for the next cycle, which merges nothing and writes its own commit;
- a cycle without a merge writes only ``brain/state``;
- nothing is written when a head moved (a rerun of the same cycle included), when the response is not this cycle's,
  when a row carries a secret, or when the roots file is no chain (a hard stop); a root that cannot be signed after
  the merge is a hard stop naming the refs written; a block edited by hand is regenerated and recorded;
- ``ledger.events.cause``: each rule by name, ``kos:`` reasons and look-alikes are ``unknown``; every reason
  ``gate.diffguard.path_reasons`` gives is in ``PATH_REASONS``;
- ``target.land.applied``: one file applied; more than one file, a missing or linked base, a hunk that does not
  apply, a creation and an unusable diff each refused with their reason.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate import diffguard as G  # noqa: E402
from ledger import anchor as AN  # noqa: E402
from ledger import chain as CH  # noqa: E402
from ledger import cycle as CY  # noqa: E402
from ledger import events as EV  # noqa: E402
from ledger import schema as SC  # noqa: E402
from ledger import serial as SE  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from status import block as SB  # noqa: E402
from target import branches as B  # noqa: E402
from target import land as LN  # noqa: E402
from profile_tree import write_tree  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, diff  # noqa: E402
from test_loop_kos import A_JS, HEADS, candidate  # noqa: E402
from test_loop_yaz import OPEN, YazBase  # noqa: E402
import yaz_world as YW  # noqa: E402

GENESIS_TS = "2026-10-30T12:00:00Z"
CYCLE = "9-1"


def genesis_state() -> dict[str, bytes]:
    """``brain/state``'s files as an activation leaves them: a ``cycle_start`` row, the status block, a signed root."""
    rows = [EV.start({"cycle_id": "g", "ts": GENESIS_TS, "snapshot_id": HEADS[B.INTEGRATION]})]
    facts = {"ts": GENESIS_TS, "snapshot_id": HEADS[B.INTEGRATION], "row_id": "g:status",
             "canary_cap_usd_micros": 1_000_000}
    return CY.plan(b"", b"", b"", b"", None, rows, YW.chained(YW.IMPORTS_ROWS), facts,
                   AN.FakeSigner(True, YW.IDENTITY, "rekor-g"), "g:root")["files"]


def rows_of(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.splitlines()]


class D6(YazBase):
    def setUp(self) -> None:
        super().setUp()
        self.state = genesis_state()

    def write_pulled(self, cands=None, **kw) -> dict:
        kw.setdefault("state", {p: self.state[p] for p in B.STATE_CHAINS})
        kw.setdefault("status", self.state[B.STATE_STATUS])
        return super().write_pulled(cands, **kw)

    def github(self) -> None:
        super().github()
        art = P.read(self.pulled)
        self.gh = YW.github_at(art.heads, YW.files_of(self.src), self.state)

    def cycle(self, cands: dict, control=None) -> dict:
        self.kos(cands)
        self.control(OPEN if control is None else control)
        self.github()
        return self.run_yaz()

    def control(self, doc) -> None:
        write_tree(os.path.join(self.temp, "control"), {"control.json": doc})

    def writes(self) -> list[tuple]:
        return [(m, p) for m, p, _ in self.gh.requests if m != "GET"]

    def state_file(self, path: str) -> bytes:
        return self.gh.read_file(B.STATE, path)

    def test_a_cycle_merges_and_writes_one_state_commit(self):
        out = self.cycle({"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST)})
        self.assertEqual((out["ok"], out["reason"], out["done"], out["merge"]),
                         (False, "cycle_not_wired", ["D5", "D6"], "good"))
        written = out["written"]
        merge = written["merge"]
        self.assertEqual({k: merge[k] for k in ("candidate", "path", "pull")}, {"candidate": "good", "path": "pkg/a.js",
                                                                              "pull": 1})
        # the merge: on brain/integration, the candidate's file changed as its diff says, the gate's check on its head
        self.assertEqual(self.gh.refs[B.INTEGRATION], merge["merge_sha"])
        self.assertEqual(self.gh.commits[merge["merge_sha"]]["parents"], [HEADS[B.INTEGRATION], merge["head_sha"]])
        self.assertEqual(self.gh.read_file(B.INTEGRATION, "pkg/a.js"), A_JS.replace("var a = 1;", "let a = 1;").encode())
        self.assertEqual([(c["name"], c["head_sha"], c["conclusion"]) for c in self.gh.checks],
                         [(B.CHECK, merge["head_sha"], "success")])
        # one brain/state commit, on the head D1 read
        head = self.gh.refs[B.STATE]
        self.assertEqual((written["state_sha"], self.gh.commits[head]["parents"]), (head, [HEADS[B.STATE]]))
        self.assertEqual([p for m, p in self.writes() if p.endswith("git/refs/heads/brain/state")],
                         ["/repos/acme/t1/git/refs/heads/brain/state"])
        old, new = self.state[B.STATE_LEDGER], self.state_file(B.STATE_LEDGER)
        self.assertTrue(CH.verify_bytes(new, old)["valid"])
        self.assertEqual(SC.ledger_reasons(new), [])
        added = rows_of(new)[len(rows_of(old)):]
        self.assertEqual([(r["row_id"], r["kind"]) for r in added],
                         [("9-1:start", "cycle_start"), ("9-1:c:breaks", "decision"), ("9-1:c:good", "decision"),
                          ("cagir-9-1", "cost"), ("9-1:status", "status")])
        self.assertEqual(added[1]["payload"], {"decision": "reject", "candidate": "breaks", "reasons": ["tests_red"]})
        self.assertEqual(added[1]["cause"], "test_regression")
        self.assertEqual(added[2]["payload"], dict(merge, decision="merge"))
        self.assertNotIn("cause", added[2])
        self.assertEqual({(r["ts"], r["snapshot_id"]) for r in added if r["part"] == "events"},
                         {(YW.TS, HEADS[B.INTEGRATION])})
        self.assertEqual(written["rows"], 5)
        # the root of the new ledger, signed once, its row appended; status.md's block is the last status row's
        root = AN.root_of(AN.tips(new))
        self.assertEqual(self.signer.payloads, [root.encode()])
        roots = rows_of(self.state_file(B.STATE_ROOTS))
        self.assertEqual((roots[-1]["row_id"], roots[-1]["root"], roots[-1]["rekor_uuid"]), ("9-1:root", root, "rekor-yaz"))
        self.assertTrue(CH.verify_bytes(self.state_file(B.STATE_ROOTS), self.state[B.STATE_ROOTS])["valid"])
        self.assertEqual((written["root"], written["rekor_uuid"], written["edited"]), (root, "rekor-yaz", False))
        self.assertEqual(SC.status_reasons(self.state_file(B.STATE_STATUS), new), [])
        # every ref written is under brain/: created (POST git/refs) or moved (PATCH git/refs/heads/...)
        refs = [b["ref"] for m, p, b in self.gh.requests if m == "POST" and p.endswith("/git/refs")]
        refs += [p.split("/git/", 1)[1] for m, p, _ in self.gh.requests if m == "PATCH"]
        self.assertEqual(sorted(refs), ["refs/heads/brain/c/good", "refs/heads/brain/c/good", "refs/heads/brain/state"])
        self.assertEqual(sorted(self.gh.refs), ["brain/c/good", B.INTEGRATION, B.STATE])
        # the next cycle: the merge is unfinished (its sentinel is D7's), so nothing merges; its own commit is written
        self.assertEqual(SE.unfinished(new), [merge["merge_sha"]])
        self.state = {p: self.state_file(p) for p in B.STATE_CHAINS + (B.STATE_STATUS,)}
        heads = dict(self.gh.refs)
        shutil.rmtree(self.pulled)
        shutil.rmtree(os.path.join(self.temp, "in", "results"))
        self.kos({"good": candidate(GOOD)}, heads={b: heads[b] for b in P.HEAD_BRANCHES})
        gh = self.gh
        self.github()
        self.gh = gh
        art = P.read(self.pulled)
        YW.write_response(self.temp, "t1", art.heads, [YW.cost_row("cagir-10-1", art.heads[B.INTEGRATION])])
        out = self.run_yaz(GITHUB_RUN_ID="10")
        self.assertEqual((out["done"], out["written"]["merge"]), (["D5", "D6"], None))
        added = rows_of(self.state_file(B.STATE_LEDGER))[len(rows_of(self.state[B.STATE_LEDGER])):]
        self.assertEqual([(r["row_id"], r["payload"].get("reasons")) for r in added if r["kind"] == "decision"],
                         [("10-1:c:good", ["sentinel_pending"])])
        self.assertEqual(self.gh.commits[self.gh.refs[B.STATE]]["parents"], [heads[B.STATE]])

    def test_without_a_merge_only_brain_state_is_written(self):
        out = self.cycle({"good": candidate(GOOD)}, control={"merge_paused": True})
        self.assertEqual((out["done"], out["written"]["merge"]), (["D5", "D6"], None))
        self.assertEqual([p for m, p in self.writes() if "/git/refs" in p], ["/repos/acme/t1/git/refs/heads/brain/state"])
        self.assertEqual(self.gh.refs[B.INTEGRATION], HEADS[B.INTEGRATION])
        [decision] = [r for r in rows_of(self.state_file(B.STATE_LEDGER)) if r["kind"] == "decision"]
        self.assertEqual((decision["payload"]["reasons"], decision["cause"]), (["merge_paused"], "unknown"))

    def test_a_moved_head_writes_nothing(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        for branch in P.HEAD_BRANCHES:
            with self.subTest(branch=branch):
                self.github()
                self.gh.commits["c" * 40] = {"tree": self.gh.commits[HEADS[branch]]["tree"], "parents": [HEADS[branch]],
                                             "message": "pushed by someone else"}
                self.gh.refs[branch] = "c" * 40
                out = self.run_yaz()
                self.assertEqual((out["reason"], out["reasons"], out["done"]),
                                 ("write_refused", ["head_moved:%s" % branch], ["D5"]))
                self.assertEqual(self.writes(), [])

    def test_a_rerun_of_the_same_cycle_writes_nothing(self):
        self.cycle({"good": candidate(GOOD)})
        before = len(self.writes())
        out = self.run_yaz(GITHUB_RUN_ATTEMPT="2")
        self.assertEqual((out["reason"], out["reasons"]),
                         ("write_refused", ["head_moved:brain/state", "head_moved:brain/integration"]))
        self.assertEqual(len(self.writes()), before)

    def test_a_response_that_is_not_this_cycles_writes_nothing(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        self.github()
        art = P.read(self.pulled)
        response = os.path.join(self.temp, "in", "response")
        other = dict(art.heads, **{B.STATE: "d" * 40})
        cases = (
            (lambda: None, ["response_missing"]),
            (lambda: YW.write_response(self.temp, "t1", other, []), ["heads_mismatch"]),
            (lambda: YW.write_response(self.temp, "t2", art.heads, []), ["target_mismatch"]),
            (lambda: YW.write_response(self.temp, "t1", art.heads, {}), ["rows_invalid"]),
            (lambda: YW.write_response(self.temp, "t1", art.heads, [], schema="snowball-response/2"), ["schema_unknown"]),
            (lambda: YW.write_response(self.temp, "t1", art.heads, [], extra=1), ["response_unreadable"]),
            (lambda: write_tree(response, {"response.json": "{"}), ["response_unreadable"]),
            (lambda: write_tree(response, {"response.json": {"schema": 1}, "other.json": "x"}),
             ["unlisted:other.json", "response_unreadable"]),
        )
        for make, want in cases:
            with self.subTest(want=want):
                shutil.rmtree(response, ignore_errors=True)
                make()
                out = self.run_yaz()
                self.assertEqual((out["reason"], out["reasons"]), ("response_invalid", want))
                self.assertEqual(self.gh.requests, [])

    def test_a_secret_in_a_row_is_refused_before_any_write(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        self.github()
        art = P.read(self.pulled)
        token = "ghp_" + "Q7x" * 12  # a GitHub token shape, not a real token
        YW.write_response(self.temp, "t1", art.heads, [YW.cost_row(reason="leak " + token)])
        out = self.run_yaz()
        self.assertEqual(out["reason"], "write_refused")
        [reason] = out["reasons"]
        self.assertTrue(reason.startswith("state_unwritable: "), reason)
        self.assertEqual(self.writes(), [])

    def test_a_row_id_already_in_the_ledger_is_refused_before_any_write(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        self.github()
        art = P.read(self.pulled)
        YW.write_response(self.temp, "t1", art.heads, [YW.cost_row("g:start")])  # the genesis cycle's start row
        out = self.run_yaz()
        self.assertEqual(out["reason"], "write_refused")
        self.assertIn("repeats row_id", out["reasons"][0])
        self.assertEqual(self.writes(), [])

    def test_a_roots_file_that_is_no_chain_is_a_hard_stop_before_any_write(self):
        self.state = dict(self.state, **{B.STATE_ROOTS: self.state[B.STATE_ROOTS].replace(b'"g:root"', b'"g:r00t"')})
        out = self.cycle({"good": candidate(GOOD)})
        self.assertEqual((out["reason"], out["written"]), ("hard_stop", []))
        self.assertEqual(self.writes(), [])

    def test_a_root_that_cannot_be_signed_after_the_merge_is_a_hard_stop_naming_the_writes(self):
        self.signer = YW.signer(available=False)
        out = self.cycle({"good": candidate(GOOD)})
        self.assertEqual((out["reason"], out["done"]), ("hard_stop", ["D5"]))
        self.assertEqual(out["written"], ["refs/heads/brain/c/good", "refs/heads/brain/integration"])  # the merge
        self.assertIn("Unsignable", out["reasons"][0])
        self.assertEqual(self.gh.refs[B.STATE], HEADS[B.STATE])  # brain/state untouched

    def test_a_block_edited_by_hand_is_regenerated_and_recorded(self):
        status = self.state[B.STATE_STATUS]
        start = status.index(SB.OPEN) + len(SB.OPEN)
        self.state = dict(self.state, **{B.STATE_STATUS: status[:start] + b"\nEDITED-BY-HAND\n" + status[start:]})
        out = self.cycle({"good": candidate(GOOD)}, control={"merge_paused": True})
        self.assertTrue(out["written"]["edited"])
        new = self.state_file(B.STATE_LEDGER)
        self.assertEqual([r["kind"] for r in rows_of(new)][-2:], ["status_edited", "status"])
        self.assertEqual(SC.status_reasons(self.state_file(B.STATE_STATUS), new), [])
        self.assertNotIn(b"EDITED-BY-HAND", self.state_file(B.STATE_STATUS))

    def test_the_environment_and_the_target_repository(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        self.github()
        for name in J.YAZ_ENV:
            with self.subTest(unset=name):
                with self.assertRaisesRegex(J.Unusable, name):
                    self.run_yaz(**{name: ""})
        shutil.rmtree(self.pulled)
        self.write_pulled({"good": candidate(GOOD)}, target={"id": "t1", "kind": "toy", "excluded_paths": [],
                                                             "unit_candidates": [], "repo": "../x"})
        self.github()
        self.assertEqual(self.run_yaz()["reason"], "target_repo_unsafe")
        self.assertEqual(self.gh.requests, [])


class Cause(unittest.TestCase):
    def test_each_rule_by_name(self):
        for reasons, want in ((["scope_violation"], "scope_violation"), (["manifest:pkg/package.json"], "scope_violation"),
                              (["tests_red"], "test_regression"), (["zero_tests"], "test_regression"),
                              (["ratchet_increase"], "lint_regression"), (["merge_paused"], "unknown"),
                              (["tests_red", "security_path:a"], "scope_violation"), ([], "unknown")):
            with self.subTest(reasons=reasons):
                self.assertEqual(EV.cause(reasons), want)

    def test_kos_reasons_and_look_alikes_are_unknown(self):
        for reason in ("kos:patch_does_not_apply", "kos:base_file_missing", "kos:tests_red", "manifest", "x:manifest",
                       "scope_violation:x"):
            with self.subTest(reason=reason):
                self.assertEqual(EV.cause([reason]), "unknown")

    def test_every_path_reason_of_diffguard_is_named(self):
        profile = {"security_paths": ["s/"], "excluded_dirs": ["e/"]}
        paths = ["/abs", "../up", "s/x.js", "e/x.js", "CLAUDE.md", ".github/w.yml", "package.json",
                 "yarn.lock", ".gitattributes", "out/x.js"]
        found = set()
        for path in paths:
            found.update(r.split(":", 1)[0] for r in G.path_reasons(path, [G.SYMLINK, G.SUBMODULE], profile,
                                                                     {"inputs": ["s/", "e/", "a/"]}))
        self.assertEqual(found, set(G.PATH_REASONS))


class Applied(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = tempfile.mkdtemp(prefix="t-land-")
        self.addCleanup(shutil.rmtree, self.tree, ignore_errors=True)
        write_tree(self.tree, {"pkg/a.js": "var a = 1;\nvar b = 2;\n", "pkg/b.js": "var c = 3;\n"})

    def applied(self, patch: bytes) -> dict:
        return LN.applied(self.tree, patch.decode())

    def test_one_file(self):
        self.assertEqual(self.applied(diff("pkg/a.js", ["var a = 1;"], ["let a = 1;"])),
                         {"reasons": [], "path": "pkg/a.js", "content": b"let a = 1;\nvar b = 2;\n"})

    def test_refusals(self):
        two = diff("pkg/a.js", ["var a = 1;"], ["let a = 1;"]) + diff("pkg/b.js", ["var c = 3;"], ["let c = 3;"])
        create = (b"diff --git a/pkg/n.js b/pkg/n.js\nnew file mode 100644\nindex 0000000..1111111\n--- /dev/null\n"
                  b"+++ b/pkg/n.js\n@@ -0,0 +1 @@\n+x\n")
        os.symlink("a.js", os.path.join(self.tree, "pkg", "l.js"))
        for patch, want in ((two, "diff_not_one_file"), (diff("pkg/z.js", ["x"], ["y"]), "base_file_missing"),
                            (diff("pkg/l.js", ["var a = 1;"], ["y"]), "base_file_missing"),
                            (diff("pkg/a.js", ["var zz = 9;"], ["y"]), "patch_does_not_apply"),
                            (create, "base_file_missing"), (b"not a diff\n", "diff_unusable")):
            with self.subTest(want=want):
                got = self.applied(patch)
                self.assertEqual((got["reasons"], got["content"]), ([want], None))


if __name__ == "__main__":
    unittest.main()
