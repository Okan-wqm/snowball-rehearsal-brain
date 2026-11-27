"""Test 58 (P1 MF12, tohum/26j "Aday yolu"; tohum/26k T1, T2): ``yaz`` reads ``candidates/<id>/`` from the results by
its hash; ``organ_ids`` goes to the gate, ``finding`` to the finding writer; a malformed package rejects only that
candidate.

What is measured:

- ``Form`` (``loop.candidates`` alone): the package's form over a table of documents, the finding the gate reads,
  and ``merge_diff`` on a package changed after the decision;
- ``Live`` (the jobs, as test 57 runs them: ``loop.job.run("kos")`` on a ``pulled`` artifact whose accepted organ
  writes the packages, then ``loop.decide.decide`` on ``pulled`` and the results, or the whole
  ``loop.job.run("yaz")``): a listed organ's candidate for an open finding merges and its finding is written
  ``fixed`` on ``brain/state``; ``organ_ids`` is what the allowlist judges (each of its reasons); the finding's
  reasons before the merge is chosen (T1), two candidates of one finding (T2); a malformed package, a package of
  which one byte changed, a missing rerun file and an id held by a ready candidate too reject that candidate
  beside one that merges; a package changed between D5 and D6 stops the job (``Unusable``) with nothing written;
  the genesis cycle reads none.

Not run here: a real docker, the artifact's upload and download, an organ's output read as a proposal (the
registry of these tests is written by ``findings.write.observe`` beforehand), a brain that holds an organ.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import listed_world as LW  # noqa: E402
import test_findings_write as TFW  # noqa: E402
from findings import write as FW  # noqa: E402
from gate import allowlist as AL  # noqa: E402
from ledger import append  # noqa: E402
from loop import candidates as LC  # noqa: E402
from loop import decide as E  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from runner import candidate_rerun as CR  # noqa: E402
from target import branches as B  # noqa: E402
from test_candidate_rerun import organ  # noqa: E402
from test_kos import A_JS, BREAKS_TEST, GOOD, diff as kos_diff  # noqa: E402
from test_loop_kos import HEADS, candidate, recipe, state_files  # noqa: E402
from test_loop_yaz import OPEN  # noqa: E402
from test_organ_output import LiveBase  # noqa: E402

OID = "lint.discover"
TREE = {"pkg/a.js": A_JS.encode()}
VAR = TFW.lint(1)                                   # the finding GOOD fixes: line 1 of pkg/a.js, ``var a = 1;``
OTHER = TFW.lint(2, rule_id="prefer-let")           # another finding, of line 2
NAMED = TFW.named(1)                                # a finding on a symbol
PRINT = FW.fingerprint(VAR, TFW.reader(TREE))
NO_APPLY = kos_diff("pkg/a.js", ["no such line"], ["x"])
B_GOOD = kos_diff("pkg/b.js", ["const c = 3;"], ["const c = 4;"])   # a diff that fixes nothing of VAR


def package(diff: bytes = GOOD, finding: dict = VAR, **more) -> bytes:
    doc = dict({"finding": finding, "diff": diff.decode(), "organ_ids": [OID], "definition_sha256": []}, **more)
    return json.dumps({k: v for k, v in doc.items() if v is not None}).encode() + b"\n"


def registry(*findings: dict, state: str | None = None) -> bytes:
    """A findings file holding ``findings`` as open rows (``findings.write.observe``), all in ``state`` when given."""
    data = TFW.observe(b"", list(findings), TREE).content
    return data if state is None else TFW.with_state(data, state)


class Form(unittest.TestCase):
    def test_the_package_is_26a_s_four_keys_each_of_its_form(self):
        good = json.loads(package())
        self.assertEqual(LC.parsed(package()), good)
        self.assertEqual(LC.parsed(package(organ_ids=[], definition_sha256=["a" * 64])),
                         dict(good, organ_ids=[], definition_sha256=["a" * 64]))
        bad = {
            "not UTF-8": b"\xff" + package(),
            "not JSON": b"{",
            "a list": json.dumps([good]).encode(),
            "nested too deeply": b"[" * 200 + b"]" * 200,
            "a fifth key": package(more=1),
            "no finding": package(finding=None),
            "no organ_ids": package(organ_ids=None),
            "no definition_sha256": package(definition_sha256=None),
            "no diff": json.dumps({k: v for k, v in good.items() if k != "diff"}).encode(),
            "diff not a string": json.dumps(dict(good, diff=[GOOD.decode()])).encode(),
            "diff with no UTF-8 encoding": json.dumps(dict(good, diff="\ud800")).encode(),
            "organ_ids a string": package(organ_ids=OID),
            "an organ id twice": package(organ_ids=[OID, OID]),
            "an empty organ id": package(organ_ids=[""]),
            "an organ id no string": package(organ_ids=[1]),
            "definition_sha256 a string": package(definition_sha256="a" * 64),
            "a definition hash not hex64": package(definition_sha256=["A" * 64]),
            "finding no object": package(finding="f-1"),
            "finding of the gate's form": package(finding={"rule_id": "no-var", "path": "pkg/a.js", "line": 1}),
            "finding with a written field": package(finding=dict(VAR, state="open")),
            "finding leaving the tree": package(finding=TFW.lint(1, path="../a.js")),
            "a K0 finding without rule_id": package(finding=TFW.lint(1, rule_id=None)),
            # a string no ledger row can hold and no host can name: anywhere in the package
            "a finding path with a lone surrogate": package(finding=TFW.lint(1, path="\ud800")),
            "a claim with a lone surrogate": package(finding=dict(VAR, claim="a \udc00 var")),
            "an organ id with a lone surrogate": package(organ_ids=["x\ud800"]),
        }
        for name, raw in bad.items():
            with self.subTest(name):
                with self.assertRaises(LC.Refused) as caught:
                    LC.parsed(raw)
                self.assertEqual(caught.exception.reasons, ["package_invalid"])

    def test_the_candidates_are_the_candidate_ids_among_the_names_and_the_rerun_keys(self):
        results = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, results)
        for name in ("b", "bad id", ".hidden", "x" * 129):
            os.makedirs(os.path.join(results, "candidates", name))
        dotted = ["a.b", "a..b", "a.", "a.lock", "1.2"]    # a ready candidate's id may be so, a run-time one's not
        for name in dotted[:2]:
            os.makedirs(os.path.join(results, "candidates", name))
        index = {"reruns": dict({"a": {}, "b": {}, "caf\udce9": {}, "": {}, "../a": {}, "x" * 128: {}, "A_b-9": {}},
                                **{name: {} for name in dotted[2:]})}
        self.assertEqual(LC.names(results, index), sorted(["a", "b", "bad id", ".hidden", "x" * 129, "caf\udce9", "",
                                                            "../a", "x" * 128, "A_b-9"] + dotted))
        # an id kos gives no package a place under (runner.candidate_rerun.ID) is no candidate: no decision names it
        self.assertEqual(LC.ids(results, index), ["A_b-9", "a", "b", "x" * 128])
        self.assertEqual((LC.names(results, None), LC.names(results, {"reruns": ["a"]})), (sorted(os.listdir(
            os.path.join(results, "candidates"))),) * 2)
        self.assertEqual(LC.names(os.path.join(results, "none"), index), sorted(index["reruns"]))

    def test_the_gate_s_finding_is_derived_from_the_proposed_one(self):
        self.assertEqual(LC.found(VAR), {"rule_id": "no-var", "path": "pkg/a.js", "line": 1})
        refs = [{"path": "pkg/b.js", "line_start": 9, "line_end": 9}, {"path": "pkg/a.js", "line_start": 2, "line_end": 3},
                {"path": "pkg/a.js", "line_start": 1, "line_end": 1}]
        # the line is the primary ref's (tohum/26q (3)): the first one, and only when it is in the finding's file
        self.assertEqual(LC.found(dict(VAR, evidence_refs=refs)), {"rule_id": "no-var", "path": "pkg/a.js", "line": None})
        self.assertEqual(LC.found(dict(VAR, evidence_refs=refs[1:] + refs[:1])),
                         {"rule_id": "no-var", "path": "pkg/a.js", "line": 2})
        self.assertEqual(LC.found(dict(VAR, evidence_refs=refs[:1])), {"rule_id": "no-var", "path": "pkg/a.js", "line": None})
        self.assertEqual(LC.found(NAMED), {"rule_id": None, "path": "pkg/a.js", "line": 1})


class Live(LiveBase):
    def world(self, packages: dict, findings: bytes | None = registry(VAR), cands: dict | None = None,
              listed: bool = True) -> None:
        """``kos`` on a ``pulled`` whose accepted organ ``OID`` writes ``packages``, then ``pulled`` written again
        as the cycle after the genesis cycle ``yaz`` reads: ``OID`` listed (unless not ``listed``) and the registry
        ``findings``."""
        carried = {OID: organ(packages)}
        shutil.rmtree(self.temp, ignore_errors=True)
        self.cycle(carried, cands=cands)
        state = state_files()
        if listed:
            rows = AL.rows(LW.CYCLE, dict(LW.ENTRY, organ_ids=[OID]), carried, [])
            ledger = state[B.STATE_LEDGER]
            state[B.STATE_LEDGER] = append.plan_cycle(ledger, ledger, lambda: json.dumps({"rows": rows}).encode()).content
        if findings is not None:
            state[B.STATE_FINDINGS] = findings
        self.again = dict(cands=cands or {}, accepted=P.read(self.pulled).accepted, state=state, organs=carried)
        self.rewrite()

    def rewrite(self, **kw) -> None:
        shutil.rmtree(self.pulled)
        self.write_pulled(**dict(self.again, **kw))

    def judged(self, **kw) -> tuple:
        got = self.decide(**kw)
        return got["merge"], self.reasons(got), got["finding_decisions"]

    def change(self, *parts, to=None) -> bytes:
        """The results' file ``parts`` with its first byte changed (or as ``to``); the bytes it held."""
        with open(self.results(*parts), "rb") as fh:
            held = fh.read()
        with open(self.results(*parts), "wb") as fh:
            fh.write(bytes([held[0] ^ 1]) + held[1:] if to is None else to)
        return held

    def test_a_listed_organ_s_candidate_for_an_open_finding_merges_and_its_finding_is_fixed(self):
        self.world({"rt": package()})
        got = self.decide()
        sha = CR.key(package())
        self.assertEqual(got, {"decisions": {"rt": {"decision": "merge", "reasons": [], "package_sha256": sha}},
                               "merge": "rt", "finding_decisions": [{"fingerprint": PRINT, "reasons": []}]})
        # the whole job: D6 lands the package's diff and writes the finding fixed on brain/state
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["ok"], line["merge"], line["done"]), (True, "rt", ["D5", "D6"]))
        self.assertEqual(line["decisions"], got["decisions"])
        self.assertEqual(line["written"]["findings"], {"rows": 1, "unresolved_rows": 0, "refused": []})
        rows = TFW.stored(self.gh.read_file(B.STATE, B.STATE_FINDINGS))
        self.assertEqual([(r["fingerprint"], r["state"]) for r in rows], [(PRINT, "open"), (PRINT, "fixed")])
        self.assertEqual(self.gh.read_file(B.INTEGRATION, "pkg/a.js"), A_JS.replace("var a", "let a").encode())
        # the package changed between D5 and D6 is not the one decided on: nothing is landed from it
        with self.assertRaisesRegex(LC.Unusable, "rt: the package is not the one decided on"):
            LC.merge_diff(self.results(), "rt", "0" * 64)
        self.assertEqual(LC.merge_diff(self.results(), "rt", sha), GOOD.decode())
        self.change("candidates", "rt", "package.json")
        with self.assertRaisesRegex(LC.Unusable, "rt: rerun_missing"):
            LC.merge_diff(self.results(), "rt", sha)

    def test_a_package_changed_between_d5_and_d6_stops_the_job_and_nothing_is_written(self):
        self.world({"rt": package()})
        self.github()
        decide = E.decide

        def then_changed(*args, **kw):
            got = decide(*args, **kw)
            self.assertEqual(got["merge"], "rt")
            self.change("candidates", "rt", "package.json")
            return got

        with mock.patch.object(E, "decide", then_changed):
            with self.assertRaisesRegex(J.Unusable, "^yaz: candidate rt: rerun_missing$"):
                self.run_yaz()
        self.assertEqual(self.gh.read_file(B.INTEGRATION, "pkg/a.js"), A_JS.encode())
        self.assertIsNone(self.gh.read_file(B.STATE, B.STATE_FINDINGS))

    def test_a_reject_of_the_gate_goes_to_the_finding_writer_with_its_reasons(self):
        self.world({"rt": package(BREAKS_TEST)})
        self.assertEqual(self.judged(), (None, {"rt": ["tests_red"]}, [{"fingerprint": PRINT, "reasons": ["tests_red"]}]))
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["ok"], line["merge"]), (True, None))
        self.assertEqual(line["written"]["findings"], {"rows": 1, "unresolved_rows": 1, "refused": []})
        self.assertEqual(TFW.states(self.gh.read_file(B.STATE, B.STATE_FINDINGS)), ["open", "unresolved"])

    def test_organ_ids_is_what_the_allowlist_judges(self):
        self.world({"rt": package(), "none": package(organ_ids=[]), "other": package(organ_ids=[OID, "x.y"])},
                   findings=registry(VAR, state="fixed"))
        closed = "finding_not_open"     # the finding takes no decision: each candidate is judged alone below
        self.assertEqual(self.judged(), (None, {"rt": [closed], "none": [closed, "no_organ"],
                                                "other": [closed, "organ_unknown:x.y"]}, []))
        # the organ's own definition and row: taken away, the package that names it is refused
        self.rewrite(organs={OID: organ({})})
        self.assertEqual(self.judged()[1]["rt"], [closed, "organ_not_listed:" + OID])
        self.rewrite(organs={})
        self.assertEqual(self.judged()[1]["rt"], [closed, "organ_unknown:" + OID])
        # a definition the allowlist cannot hash is the reject of the candidates that name it, not the cycle's
        # (tohum/26k T2); pulled carries only definitions it could read, so the artifact's object is set here
        art = P.read(self.pulled)._replace(organs={OID: {"entry": {}, "files": {}}})
        got = E.decide(art, recipe(), self.tree(), self.results(), OPEN, [], [])
        self.assertEqual(self.reasons(got), {"rt": [closed, "organ_unusable"], "none": [closed, "no_organ"],
                                             "other": [closed, "organ_unknown:x.y", "organ_unusable"]})
        self.world({"rt": package()}, listed=False)
        self.assertEqual(self.judged(), (None, {"rt": ["organ_not_listed:" + OID]},
                                         [{"fingerprint": PRINT, "reasons": ["organ_not_listed:" + OID]}]))

    def test_a_finding_the_registry_refuses_is_a_reason_before_the_merge_is_chosen(self):
        # tohum/26k T1: the same package that merges for an open finding
        for name, findings, want in (("no registry", None, "finding_unknown"),
                                     ("another finding's", registry(OTHER), "finding_unknown"),
                                     ("fixed", registry(VAR, state="fixed"), "finding_not_open"),
                                     ("unresolved", registry(VAR, state="unresolved"), "finding_not_open"),
                                     ("blocked", registry(VAR, state="blocked"), "finding_not_open"),
                                     ("a cut file", registry(VAR)[:-20], "registry_unusable")):
            with self.subTest(name):
                self.world({"rt": package()}, findings=findings)
                self.assertEqual(self.judged(), (None, {"rt": [want]}, []))
        self.world({"rt": package()}, findings=registry(VAR, state="reopened"))
        self.assertEqual(self.judged()[0], "rt")
        # the whole job on a refused finding: no merge, a reject row's worth of line, nothing written to the registry
        self.rewrite(state=dict(self.again["state"], **{B.STATE_FINDINGS: registry(VAR, state="fixed")}))
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["ok"], line["merge"], line["decisions"]["rt"]["reasons"]), (True, None, ["finding_not_open"]))
        self.assertEqual(line["written"]["findings"], {"rows": 0, "unresolved_rows": 0, "refused": []})

    def test_a_finding_without_a_fingerprint_or_a_line_takes_no_decision(self):
        gone = dict(VAR, evidence_refs=[{"path": "pkg/a.js", "line_start": 9, "line_end": 9}])   # past the file's end
        elsewhere = dict(NAMED, evidence_refs=[{"path": "pkg/b.js", "line_start": 1, "line_end": 1}])
        self.world({"gone": package(finding=gone), "elsewhere": package(finding=elsewhere), "sym": package(finding=NAMED)},
                   findings=registry(VAR, NAMED))
        merge, reasons, sent = self.judged()
        self.assertEqual(reasons["gone"], ["no_line", "target_not_found"])
        # a symbol's finding has a fingerprint without a line; the gate's criteria cannot read it
        self.assertEqual(reasons["elsewhere"], ["candidate_unusable"])
        self.assertEqual(reasons["sym"], ["candidate_unusable", "finding_decided"])     # the same symbol's finding
        self.assertEqual(merge, None)
        self.assertEqual(sent, [{"fingerprint": FW.fingerprint(NAMED, TFW.reader(TREE)), "reasons": ["candidate_unusable"]}])

    def test_two_candidates_of_one_finding_reject_the_later_and_the_cycle_goes_on(self):
        # tohum/26k T2, both orders of the first decision
        self.world({"a": package(), "b": package(), "c": package(B_GOOD, OTHER)}, findings=registry(VAR, OTHER))
        other = FW.fingerprint(OTHER, TFW.reader(TREE))
        merge, reasons, sent = self.judged()
        self.assertEqual((merge, reasons["a"], reasons["b"]), ("a", [], ["finding_decided", "sentinel_pending"]))
        self.assertEqual(sent[0], {"fingerprint": PRINT, "reasons": []})
        self.assertEqual([d["fingerprint"] for d in sent], [PRINT, other])
        self.github()
        line = self.line(self.run_yaz())                    # the writer takes the list: the cycle is written
        self.assertEqual((line["ok"], line["merge"]), (True, "a"))
        self.assertEqual(line["written"]["findings"]["refused"], [])
        self.world({"a": package(BREAKS_TEST), "b": package()})
        self.assertEqual(self.judged(), (None, {"a": ["tests_red"], "b": ["finding_decided"]},
                                         [{"fingerprint": PRINT, "reasons": ["tests_red"]}]))
        # a closed gate's reject is no decision on the finding: the next candidate of the same finding is judged
        self.world({"a": package(organ_ids=[]), "b": package()})
        self.assertEqual(self.judged(), ("b", {"a": ["no_organ"], "b": []},
                                         [{"fingerprint": PRINT, "reasons": ["no_organ"]}, {"fingerprint": PRINT, "reasons": []}]))
        self.github()
        self.assertEqual(self.line(self.run_yaz())["written"]["findings"], {"rows": 1, "unresolved_rows": 0, "refused": []})

    def test_a_malformed_package_rejects_only_that_candidate(self):
        self.world({"bad": package(more=1), "good": package(), "nofinding": package(finding=None),
                    "notjson": b"{", "ready": package()},
                   cands={"ready": candidate(GOOD), "old": candidate(GOOD)})
        merge, reasons, sent = self.judged()
        self.assertEqual(merge, "good")
        self.assertEqual(reasons, {"bad": ["package_invalid"], "good": [], "nofinding": ["package_invalid"],
                                   "notjson": ["kos:package_unusable", "package_invalid"], "old": ["no_organ", "sentinel_pending"],
                                   "ready": ["candidate_id_twice"]})
        self.assertEqual(sent, [{"fingerprint": PRINT, "reasons": []}])
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["ok"], line["merge"], self.reasons(line)), (True, "good", reasons))

    def test_a_package_without_form_keeps_the_reasons_of_its_rerun(self):
        # tohum/26p (5), "girdisinin her nedeniyle": no reason of the entry is lost where the gate cannot be asked
        nodiff = json.dumps({"finding": VAR, "organ_ids": [OID], "definition_sha256": []}).encode()
        self.world({"nodiff": nodiff, "notjson": b"\xff{", "rt": package()})
        refused = ["kos:package_unusable", "package_invalid"]
        self.assertEqual(self.judged(), ("rt", {"nodiff": refused, "notjson": refused, "rt": []},
                                         [{"fingerprint": PRINT, "reasons": []}]))
        index = json.loads(self.change("index.json"))
        index["reruns"]["nodiff"] = dict(index["reruns"]["nodiff"], reasons=["b", "a"])
        index["reruns"]["notjson"] = dict(index["reruns"]["notjson"], verdict="verified")   # a verified one has none
        self.change("index.json", to=json.dumps(index).encode())
        os.makedirs(self.results("r", "notjson"))
        for name in CR.FILES:
            with open(self.results("r", "notjson", name), "wb") as fh:
                fh.write(b"{}")
        self.assertEqual(self.judged()[1], {"nodiff": ["kos:a", "kos:b", "package_invalid"],
                                            "notjson": ["package_invalid"], "rt": []})

    def test_a_rerun_kos_did_not_verify_reaches_the_gate_and_is_rejected_by_its_reasons(self):
        # tohum/26p (5): not a missing rerun; rejected as a ready candidate kos refused, and the finding is decided
        self.world({"noapply": package(NO_APPLY)})
        refused = ["artefact_hash_mismatch", "kos:patch_does_not_apply"]
        got = self.decide()
        self.assertEqual(got, {"decisions": {"noapply": {"decision": "reject", "reasons": refused,
                                                         "package_sha256": CR.key(package(NO_APPLY))}},
                               "merge": None, "finding_decisions": [{"fingerprint": PRINT, "reasons": refused}]})
        with self.assertRaisesRegex(LC.Unusable, "candidate noapply: the rerun is not verified"):
            LC.merge_diff(self.results(), "noapply", CR.key(package(NO_APPLY)))
        # the whole job: no merge, and the finding's reject is written (the loop keeps its lesson)
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["ok"], line["merge"], self.reasons(line)), (True, None, {"noapply": refused}))
        self.assertEqual(line["written"]["findings"], {"rows": 1, "unresolved_rows": 1, "refused": []})
        # a rerun with its three files whose entry is not verified: the entry's reasons alone reject it
        self.world({"rt": package()})
        held = self.change("index.json")
        index = json.loads(held)
        for entry, reasons in (({"verdict": "no_verdict", "reasons": ["red_control_green"]}, ["kos:red_control_green"]),
                               ({"verdict": "no_verdict", "reasons": []}, ["kos:no_verdict"]),
                               ({"reasons": ["x", "y"]}, ["kos:x", "kos:y"])):
            with self.subTest(entry=entry):
                index["reruns"]["rt"] = dict(entry, package_sha256=CR.key(package()))
                self.change("index.json", to=json.dumps(index).encode())
                self.assertEqual(self.judged(), (None, {"rt": reasons}, [{"fingerprint": PRINT, "reasons": reasons}]))
                with self.assertRaisesRegex(LC.Unusable, "candidate rt: the rerun is not verified"):
                    LC.merge_diff(self.results(), "rt", CR.key(package()))
        self.change("index.json", to=held)      # the control: the entry as kos wrote it merges
        self.assertEqual(self.judged()[:2], ("rt", {"rt": []}))

    def test_a_candidate_is_read_by_the_hash_of_its_rerun(self):
        self.world({"rt": package(), "z": package()})
        self.assertEqual(self.judged()[:2], ("rt", {"rt": [], "z": ["finding_decided", "sentinel_pending"]}))
        # one byte of the package: it is not the package rerun; the other candidate is judged as before
        held = self.change("candidates", "rt", "package.json")
        # (tohum/26p (5): it does not reach the gate and takes no decision; the line's ``reruns`` names the reason)
        self.assertEqual(self.judged()[:2], ("z", {"z": []}))
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["reruns"]["rt"], self.reasons(line)), ({"reran": False, "reasons": ["rerun_missing"]}, {"z": []}))
        ledger = self.gh.read_file(B.STATE, B.STATE_LEDGER).decode()
        self.assertIn(":c:z\"", ledger)
        self.assertNotIn(":c:rt\"", ledger)
        self.assertNotIn("rerun_missing", ledger)
        # a valid package of other bytes (another diff) under the rerun of the first: not read either
        self.change("candidates", "rt", "package.json", to=package(B_GOOD))
        self.assertEqual(self.judged()[1], {"z": []})
        self.change("candidates", "rt", "package.json", to=held)
        for name in CR.FILES:
            with self.subTest(name):
                os.rename(self.results("r", "rt", name), self.results("r", "rt", name + ".away"))
                self.assertEqual(self.judged()[1], {"z": []})
                os.rename(self.results("r", "rt", name + ".away"), self.results("r", "rt", name))
        # a run file changed after the rerun: the gate's own criterion, as for a ready candidate
        self.change("r", "rt", "cand.jsonl")
        self.assertEqual(self.judged()[1], {"rt": ["artefact_hash_mismatch"], "z": ["finding_decided"]})
        # the candidates are the names under candidates/ and the keys of the index's reruns, each alone
        os.remove(self.results("candidates", "rt", "package.json"))
        self.assertEqual(self.judged()[1], {"z": []})
        os.rmdir(self.results("candidates", "rt"))
        self.assertEqual(self.judged()[1], {"z": []})
        index = json.loads(self.change("index.json"))
        # (a name that is no id is no candidate even with a package under it and an entry of its hash)
        index["reruns"]["caf\udce9"] = index["reruns"]["bad id"] = {
            "verdict": "refused", "reasons": ["candidate_id_invalid"], "package_sha256": CR.key(package())}
        self.change("index.json", to=json.dumps(index).encode())
        for name in ("stray", "bad id"):
            os.mkdir(self.results("candidates", name))
            with open(self.results("candidates", name, "package.json"), "wb") as fh:
                fh.write(package())
        self.assertEqual(self.judged()[:2], ("z", {"z": []}))
        # a name of the results that is also a ready candidate's id is one reject, rerun or not
        self.again["cands"] = {"stray": candidate(GOOD)}
        self.rewrite()
        self.assertEqual(self.judged()[:2], ("z", {"stray": ["candidate_id_twice"], "z": []}))

    def test_a_freeze_and_the_serial_rule_hold_for_a_run_time_candidate(self):
        self.world({"rt": package()})
        self.assertEqual(self.judged(frozen=["frozen:x"]),
                         (None, {"rt": ["frozen:x"]}, [{"fingerprint": PRINT, "reasons": ["frozen:x"]}]))
        self.assertEqual(self.judged(unfinished=["a" * 40])[1], {"rt": ["sentinel_pending"]})
        self.assertEqual(self.judged(control={"merge_paused": True})[1], {"rt": ["merge_paused"]})

    def test_the_genesis_cycle_reads_no_run_time_candidate(self):
        self.world({"rt": package()}, cands={"old": candidate(GOOD)})
        self.rewrite(heads=dict(HEADS, **{B.STATE: None}), state={p: b"" for p in B.STATE_CHAINS})
        self.assertTrue(P.genesis(P.read(self.pulled)))
        self.assertEqual(self.judged(), ("old", {"old": []}, []))


if __name__ == "__main__":
    unittest.main()
