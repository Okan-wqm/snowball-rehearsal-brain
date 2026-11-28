"""``yaz``'s D6: the cycle's writes on the target, from D5's decision, D7's end and D8's step (stage 0).

Rules: asama-0/01 D6 (``yaz`` writes ``brain/c/<id>``, the pull request, the check and the merge, and one
``brain/state`` commit per cycle with the signed root and ``status.md``; every ref under ``refs/heads/brain/``;
the chain verified before the write; judges MF9, 10, 11, 16), tohum/07 and tohum/01b (merges are serial, by pull
request; ``brain/state`` takes one direct commit per cycle on the head D1 verified), tohum/13 and tohum/28 (a chain
break or a root that cannot be signed is a hard stop; the watcher's freezes are rows, and more soft freezes than
the limit is a hard stop), tohum/26a (``gozcu.evaluate`` runs in ``yaz`` at the cycle's end and writes the
``freeze`` row), asama-0/10a ``#model`` (the canary's ``cost`` row is written).

**Inputs** (``write``): ``art``, the ``pulled`` artifact (``loop.pulled.read``): its ``brain/state`` ledger, roots
file and ``status.md`` as D1 read them, its heads, its candidates, its policy; ``tree``, the directory its tree was
extracted to (the tree D3 ran on and D5 judged); ``decided``, ``loop.decide``'s ``{decisions, merge}``; ``cost``,
the cost rows of this cycle's ``response`` (``loop.cagir.read_response``); ``writer``, a ``target.write.Writer`` on
the target's repository; ``signer``, the root's signer (``loop.sign.SigstoreSigner`` in the job); ``imports``,
``setup/imports.jsonl``'s bytes (``status.block``'s human-touch count); ``cycle_id`` and ``ts``; ``base_lint``,
the lint totals of the base this cycle's ``kos`` ran (``loop.watch.base_lint``: ``{base_run_sha256, counts,
fixable}``,
required when D5 chose a merge, else ``Unusable``); ``end``, D7's sentinel to end, ``{merge_sha, verdict, runs,
flaky, sha256, facts}`` (``loop.watch.read``'s verified answer at ``brain/integration``'s head, with
``loop.watch.facts``), or ``None``; ``drill``, ``loop.drill.step``'s answer or ``None``: only ``commit``
(``{payload}``) and ``plant`` (``{instance_id, path, content}``) write; an action ``loop.drill`` does not give is
``Unusable``; ``gate``, the payload of the toy's ``copy_gate`` row (``harness.pass_row.gate_payload``) when the copy's
genesis gate opened on this cycle's state, or ``None``; ``passed``, the payload of the toy's PASS row
(``harness.pass_row.judge``'s ``payload``) when the toy's and the copy's states were judged ``PASS``, or ``None``;
``art.accept``, the organ entry of the accepted SHA (``loop.pulled``, "Entry"): its ``accept`` rows
(``gate.allowlist.rows``, P1 MF9, tohum/26j) are among the cycle's rows, after the PASS row and before the cost
rows; an entry the allowlist cannot write is ``Unusable`` with nothing written; no live cycle has an entry
before stage 1 MF6 (no entry request is committed);
``proposals`` (a list of ``(proposed_by, proposal)``) and ``finding_decisions`` (a list of ``{fingerprint,
reasons}``), the cycle's input to the finding registry (``findings.write.cycle``, P1 MF8, tohum/26j): both empty
unless given; ``loop.job`` gives D5's ``finding_decisions`` (P1 MF12, ``loop.decide``) and no proposal (no job
reads an organ's output as one); ``merge_diff``, the diff of a merge that is a run-time candidate (``None`` for
a ready one, whose ``diff.patch`` ``pulled`` holds); ``cases``, the cycle's dev cases (``cases.build.build``'s
``cases``; none unless given), added to the dev case set.

**Order.** Nothing is written on the target before every check holds, and nothing is signed before the rows are
planned:

1. the merge, when D5 chose one: its diff applied to the tree (``target.land.applied``, the one application
   ``activate`` makes); a reason here means D5 chose a candidate that cannot be written, ``Unusable``. An ``end``
   must be of ``brain/integration``'s head in a cycle with no merge (D5 merges nothing while a sentinel is
   unfinished), and MF12's ``gate.sentinel.decide`` of its runs must give its ``verdict`` (and ``flaky``). Whether
   it is a red is ``gate.revert.assess`` of its runs and facts, the one rule (red tests, or a green or flaky verdict
   whose facts state ``build_break`` or ``lint_regression``): a revert's cause is known before any write; a green
   or flaky end that is no revert is ended by a row (``ledger.serial``); anything else (a ``rerun``, a verdict its
   runs do not give, an end without ``facts``) is ``Unusable``. A ``plant`` is the cycle's one merge: with D5's merge or an ``end`` it is ``Unusable``, and like a
   merge it needs ``base_lint``;
2. both heads read from the target equal ``pulled``'s (``head_moved:<branch>``, ``Refused``): the state this cycle
   decided on is still the state it writes on, so a second run of the same cycle (a rerun of ``yaz`` after its
   first run wrote) writes nothing;
   Then the watcher on the ledger as pulled (``gozcu.watch.judge`` with ``pulled``'s policy at ``ts``, no row of
   this cycle): any hard stop is ``target.land.HardStop`` ``gozcu: <triggers>`` with nothing written (the freezes
   already written pass ``soft_freeze_limit``: the cycle after the one that tipped it, and every one after, until
   the window has passed). A threshold of the policy the watcher cannot use is ``Refused`` with
   ``policy_invalid:<path>``; views it cannot read (a lift row of no freeze) are ``Unusable``;
3. the watcher at the cycle's end: ``gozcu.watch.judge`` again, now with the cycle's rows after the ledger's (its
   merge, its revert, its cost rows; the merge's answer is not read by any view), and ``gozcu.watch.rows`` of its
   answer: the cycle's ``freeze`` and ``lift`` rows. A threshold absent from the policy that is not one of the
   seven required (tohum/28a) leaves its rule unjudged and the cycle is written; the answer names the path (a
   required one absent is the ``Refused`` above). Then
   the finding registry: ``findings.write.cycle`` of ``pulled``'s ``findings.jsonl`` and ``unresolved.jsonl``
   (``target.branches.STATE_REGISTERS``; ``b""`` where the head has none) with ``proposals`` and
   ``finding_decisions`` on the cycle's snapshot, a finding's lines read from ``tree`` (a link is not followed).
   A file that is no chain is ``target.land.HardStop`` with nothing written, also on empty input; a secret in a
   proposed row (``ledger.append.SecretRow``) is ``Refused`` with ``state_unwritable``; input of another form is
   ``Unusable``. The two files as it returns them are the cycle's registers: ``ledger.cycle`` roots them with
   the ledger and writes the ones that hold a row in the cycle's commit (a cycle with empty input writes the
   files it read, so a state without them stays without them and its root is the ledger's alone). Then the dev
   case set (tohum/26m "Dev vaka seti" (1), (2), (4)): ``cases.store.add`` of ``cases`` to ``pulled``'s
   ``cases/dev.jsonl`` (``target.branches.STATE_CASES``; ``b""`` where the head has none): a case whose id the
   file has is not written again, and with other content it is refused and named, the cycle going on. A file
   that is no case set is ``target.land.HardStop`` with nothing written, also with no case; a value that is no
   case row is ``Unusable``. The file as it returns it is the cycle's: ``ledger.cycle`` writes it in the cycle's
   commit when it holds a case (it starts with the bytes D1 verified: tohum/01b's append only), and the root
   does not cover it (tohum/26n). Then
   a dry plan: ``ledger.cycle.plan`` of the cycle's rows with the merge's answer left as placeholders and a signer
   that signs nothing (``DRY``): the roots file and the ledger as chains extending themselves (D1's versions are the
   previous ones: nothing was added since), the rows' secret scan, the whole new ledger against ``ledger.schema``,
   the root row's id. A failure is ``Refused`` with ``state_unwritable`` (a ``ledger.append.HardStop`` stays a hard
   stop, ``target.land.HardStop`` with nothing written);
4. the merge landed (``target.land.land``) on ``brain/integration``'s head with the check ``target.branches.CHECK``,
   or a reverted ``end`` (``target.land.revert``: the revert commit on ``brain/revert/<merge_sha>``, its pull
   request, the same check and the merge), or D8's plant landed (``target.land.plant``: ``brain/drill/<cycle_id>``,
   its pull request, the same check, saying it is no gate decision, and the merge); a green or flaky ``end`` and a
   ``commit`` write nothing on ``brain/integration``;
5. ``ledger.cycle.commit`` on ``brain/state`` at ``pulled``'s head (``ledger.append.TargetState``: the writer
   refuses a moved head before creating anything): the rows, ``status.md``'s block and the signed root, one commit.

**A failure in step 4 or 5** (tohum/28:51-60: a GitHub write to the target that fails, the first or a later one, is
an outage like HTTP 429 and not that page's hard stop; the next cycle decides anew and takes up what stands, when
the merge did not land: a failure after the merge leaves ``brain/integration`` at a commit no row names, which the
next ``cek`` refuses, tohum/13:56-57's chain break, kept by tohum/28:58-59; whether a later cycle should take that
merge up instead, as tohum/28:54-55 reads, no page settles and nothing here builds):

- the API's error to a request of these steps or no answer to it (``target.write.ApiError``), the writer's refusal
  after a ref was written (``target.write.Refused``: ``merge_head_moved``) and its refusal of step 5's commit
  (``state_head_moved``: the root is signed by then) are ``WriteFailed`` naming the refs written
  (``writer.written``; none when the first write failed);
- a standing branch of the cycle's merge or of D8's plant that is not this cycle's commit (``target.write``'s
  ``branch_differs``, before any ref is written; the commit's blob and tree may be created by then, objects no ref
  names) is ``BranchDiffers`` (the merge's branch when the cycle merges, else the plant's; tohum/26p "Yarım
  kalmış merge": the refusal is that candidate's and the cycle goes on). Nothing of the cycle is written by this
  call: the caller (``loop.job``) decides again with the refusal and calls ``write`` again;
- any other refusal of the writer in step 4 before a ref is written (a standing revert branch that differs,
  ``revert_branch_differs``; a merge that is no longer the head, ``revert_not_head``; a request its guard refuses)
  is ``Refused`` with the writer's reasons, as step 2's: tohum/26p's rule names ``brain/c/<id>`` and
  ``brain/drill/<cycle>``, not the revert's branch;
- a chain break and a root that cannot be signed (``ledger.append.HardStop``, ``ledger.anchor.Unsignable``: tohum/28's
  triggers ``chain_break`` and ``rekor``) are ``target.land.HardStop`` naming the refs written.

Not decided here, stated: the other failures of ``ledger.cycle.FAILURES`` in step 5 (a secret in a row, an unusable
input) stay ``target.land.HardStop`` as before; step 3's dry plan refuses them before any write and no test reaches
one after it. An API error to step 2's reads of the heads is ``target.write.ApiError``, the caller's (unusable).

**The rows**, in this order, each ``ledger.events``': ``cycle_start {cycle_id}``; ``ratchet_base {base_run_sha256,
counts}`` when the cycle merges or plants (``base_lint``: the merge's lint before, which a later revert reads with
``ledger.serial.lint_before``); ``observation {base_run_sha256, fixable}`` when ``base_lint`` is given and its
``base_run_sha256`` is not the one of the ledger's last observation row (``ledger.serial.observed``): the base's
published tool output (asama-0/08 rows 1 and 6, the fields a ready candidate's ``finding.json`` takes, tohum/26c),
once per base run, in any cycle, merging or not; per candidate in code-point order of its id, ``ledger.events.decided``'s rows (a
reject's ``decision`` with D5's reasons and ``ledger.events.cause``; the merge's ``decision`` and then its ``merge``
row with ``path``, ``target.land.land``'s ``{pull, head_sha, merge_sha}`` and ``hunk_covered``, the record of
the hunks step 1 applied, ``ledger.events.hunk_covered``); ``revert {merge_sha}`` with
``gate.revert``'s cause for an ``end`` it reverts, or ``sentinel {merge_sha, verdict, red: [], flaky}`` for a green or flaky
one (the row that finishes the merge's sentinel, ``ledger.serial``; tohum/26f); D8's ``drill`` row (``commit`` with its payload, or ``plant`` with ``harness.revert_drill``'s
``{drill, family, instance_id, merge_sha}``, the planted merge's SHA; ``ledger.events.drill``); the ``copy_gate`` row
with ``gate`` (``harness.pass_row``'s gate); the ``pass`` row with ``passed`` (tohum/26d); the response's cost rows as
they are; the watcher's ``freeze`` and ``lift`` rows (step 3; ``<cycle_id>:freeze:<trigger>``,
``<cycle_id>:lift:<trigger>``); then
``status.block``'s rows (``ledger.cycle``). ``ts`` is the given time; ``snapshot_id`` is ``brain/integration``'s
head in ``pulled`` (the snapshot D3 ran on and D5 judged; the cost row carries the same, ``loop.cagir``). Row ids are
``<cycle_id>:start``, ``<cycle_id>:ratchet``, ``<cycle_id>:observation``, ``<cycle_id>:c:<cid>``, ``<cycle_id>:m:<cid>``, ``<cycle_id>:revert`` or
``<cycle_id>:sentinel``, ``<cycle_id>:drill``, ``<cycle_id>:gate``, ``<cycle_id>:pass``, ``<cycle_id>:status``
and the root row's ``<cycle_id>:root``. The
status facts' ``canary_cap_usd_micros`` is ``canary_usd`` of ``pulled``'s policy (``loop.cagir.CANARY_USD``, the
cap D4 called with).

Returns ``{merge: {candidate, path, pull, head_sha, merge_sha} | None, revert: {reverted, cause, pull, commit,
merge_sha} | None, plant: {instance_id, pull, head_sha, merge_sha} | None, state_sha, root, rekor_uuid, rows,
edited, gozcu, findings, cases}``, ``cases`` the dev case set's ``{added, kept, refused}``
(``cases.store.add``'s: the ids written by this cycle, the ids the file had already, ``{case_id: reason}``), ``findings`` the registry's ``{rows, unresolved_rows, refused}`` (the numbers of rows
added to each file and ``findings.write.decide``'s refused decisions), ``gozcu`` the watcher's answer of step 3 (``{hard_stop, freezes, lifts, marks, unjudged,
unmeasured}``). A hard stop in it (this cycle's freeze passed ``soft_freeze_limit``) does not undo the cycle: it is
written, with the freeze, and the caller ends red.

Out of scope, stated: a row of the ledger for a case added or refused (the job's line names them); the dev cases of a genesis cycle
(``activate`` writes that cycle and no case: the set starts in the cycle after); a row of the ledger for what the registry wrote or refused, and a refused proposal's
element (``findings.write.Observed.refused`` is not returned: nothing gives a proposal yet); what a freeze closes besides D5's merges (``kos`` and ``cagir`` ran before this job, and
this cycle's revert, drill and rows are written under a freeze); a record of the hard stop or of the operator's
restart (the stop is read off the freeze rows each cycle); which drill step is due (``loop.drill``); whether GitHub's ruleset accepts the writes (``target.write``'s known limits); the signer's program (``loop.sign``).
"""

from __future__ import annotations

from typing import Any

from cases import store as case_store
from dispatcher import llm_call
from findings import write as findings_write
from gate import allowlist
from gate import revert as gate_revert
from gate import sentinel
from gozcu import evaluate as gozcu_rules
from gozcu import watch
from harness import params as harness_params
from harness import pass_row as PR
from harness import revert_drill
from ledger import append, cycle, events, schema, serial
from ledger import cost as ledger_cost
from loop import cagir
from loop import pulled as P
from profile import derive
from target import branches as B
from target import land
from target import write as W
import cli

DRILL_ACTIONS = (None, "off", "wait", "none", "commit", "plant")  # loop.drill.step's actions; only the last two write
PLACEHOLDER = {"pull": 1, "head_sha": "0" * 40, "merge_sha": "0" * 40}  # the dry plan's merge answer


class Refused(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


class Unusable(ValueError):
    pass


class BranchDiffers(Exception):
    """The branch step 4 lands from stands and is not this cycle's commit (tohum/26p "Yarım kalmış merge"); no ref
    was written. The branch is the merge's, ``brain/c/<decided["merge"]>``, when the cycle merges, and D8's plant's
    otherwise (a cycle lands one of the two, ``write``)."""


class WriteFailed(Exception):
    """A GitHub write of step 4 or 5 failed (tohum/28:51-60: an outage, no hard stop); ``written`` names the refs
    already written."""

    def __init__(self, message: str, written: list[str]) -> None:
        super().__init__("%s (written: %s)" % (message, ", ".join(written) or "nothing"))
        self.written = written


class _Dry:
    """Signs nothing: the dry plan's signer (step 3)."""

    def sign(self, payload: bytes) -> dict:
        return {"uuid": "dry", "identity": "dry", "bundle": b"dry"}


DRY = _Dry()


def merge_change(art: P.Pulled, tree: str, merge: str | None, diff: str | None = None) -> dict | None:
    """D5's merge applied to the tree (``target.land.applied``): ``{reasons: [], path, content}``, ``None`` with no
    merge; a reason means D5 chose a candidate that cannot be written (``Unusable``). The merge's diff is ``diff``
    (a run-time candidate's, ``loop.candidates.merge_diff``) or, when ``None``, the ready candidate's
    ``diff.patch``. Shared with ``activate``."""
    if merge is None:
        return None
    if diff is None:
        diff = art.candidates[merge]["diff.patch"].decode("utf-8", "surrogateescape")
    change = land.applied(tree, diff)
    if change["reasons"]:
        raise Unusable("merge %s cannot be written: %s" % (merge, ", ".join(change["reasons"])))
    return change


def status_facts(art: P.Pulled, cyc: dict) -> dict:
    """``status.block``'s facts of the cycle ``cyc`` (``{cycle_id, ts, snapshot_id}``): its canary cap is
    ``canary_usd`` of ``pulled``'s policy (``loop.cagir.CANARY_USD``). Shared with ``activate``."""
    try:
        cap = llm_call.policy_usd(art.policy_bytes, *cagir.CANARY_USD)
    except llm_call.Unusable as exc:
        raise Unusable(cli.cause(exc)) from None
    return {"ts": cyc["ts"], "snapshot_id": cyc["snapshot_id"], "row_id": "%s:status" % cyc["cycle_id"],
            "canary_cap_usd_micros": cap}


def candidate_rows(cyc: dict, decided: dict, merged: dict | None, change: dict | None) -> list[dict]:
    """D5's decisions as rows, in code-point order of the candidate id (``ledger.events.decided``); ``merged`` is
    the merge's ``{path, pull, head_sha, merge_sha}`` and ``change`` its ``merge_change``, whose ``hunks`` the merge
    row's ``hunk_covered`` records. Shared with ``activate``."""
    out: list[dict] = []
    for cid in sorted(decided["decisions"]):
        out += events.decided(cyc, cid, decided["decisions"][cid]["reasons"],
                              dict(merged, hunks=change["hunks"]) if cid == decided["merge"] else None)
    return out


def write(art: P.Pulled, tree: str, decided: dict, cost: list[dict], writer: W.Writer, signer: Any,
          imports: bytes, cycle_id: str, ts: str, base_lint: dict | None = None,
          end: dict | None = None, drill: dict | None = None, gate: dict | None = None,
          passed: dict | None = None, proposals: list | None = None,
          finding_decisions: list | None = None, merge_diff: str | None = None,
          cases: list | None = None) -> dict[str, Any]:
    """D6, D7's end of a sentinel, D8's step, the gate's and the PASS row (see the module docstring)."""
    cyc = {"cycle_id": cycle_id, "ts": ts, "snapshot_id": art.heads[B.INTEGRATION]}
    merge = decided["merge"]
    change = None
    action = (drill or {}).get("action")
    planted = action == "plant"
    if action not in DRILL_ACTIONS:
        raise Unusable("drill: %r is no action of loop.drill" % (action,))
    if planted and (merge is not None or end is not None):
        raise Unusable("drill: a plant is the cycle's one merge, in a cycle that ends no sentinel")
    if merge is not None or planted:
        if base_lint is None:
            raise Unusable("merge %s: the base's lint totals are unreadable" % (merge or "planted"))
    change = merge_change(art, tree, merge, merge_diff)
    cause = red = None
    if end is not None:
        if merge is not None or end["merge_sha"] != art.heads[B.INTEGRATION]:
            raise Unusable("a sentinel's end is of brain/integration's head, in a cycle that merges nothing")
        try:
            judged = sentinel.decide(end["runs"])
            if (judged["verdict"], judged["flaky"]) != (end["verdict"], end["flaky"]):
                raise Unusable("sentinel: its runs give %s, not %s" % (judged["verdict"], end["verdict"]))
            if judged["verdict"] != "red" and judged["verdict"] not in schema.SENTINEL_ENDS:
                raise Unusable("sentinel: %s ends nothing" % judged["verdict"])
            assessed = gate_revert.assess(end["runs"], end.get("facts"))
            if assessed["revert"]:
                red, cause = end, assessed["cause"]
        except (gate_revert.Unusable, sentinel.Unusable) as exc:
            raise Unusable("sentinel: %s" % cli.cause(exc)) from None
    observe = None  # the base's tool output, published once per base run (ledger.events.observation)
    try:
        if base_lint is not None:
            if serial.observed(art.state[B.STATE_LEDGER]) != base_lint["base_run_sha256"]:
                observe = base_lint
        written = serial.rows(art.state[B.STATE_LEDGER])
    except serial.Unusable as exc:
        raise Unusable("state: %s" % cli.cause(exc)) from None
    try:
        accepts = allowlist.rows(cyc, art.accept, art.organs, written)
    except allowlist.Unusable as exc:
        raise Unusable("accept: %s" % cli.cause(exc)) from None
    moved = ["head_moved:%s" % b for b in P.HEAD_BRANCHES if writer.head(b) != art.heads[b]]
    if moved:
        raise Refused(moved)
    facts = status_facts(art, cyc)

    def watched(planned: list[dict]) -> dict:
        try:
            return watch.judge(written, planned, art.policy, ts)
        except harness_params.Invalid as exc:
            raise Refused(list(exc.reasons)) from None
        except (gozcu_rules.Unusable, watch.Unusable, ledger_cost.Unusable) as exc:
            raise Unusable("gozcu: %s" % cli.cause(exc)) from None

    stops = watched([])["hard_stop"]
    if stops:
        raise land.HardStop("gozcu: %s" % ", ".join(stop["trigger"] for stop in stops), [])

    def rows(merged: dict | None, plant_sha: str) -> list[dict]:
        out = [events.start(cyc)]
        if merge is not None or planted:
            out.append(events.ratchet_base(cyc, base_lint["base_run_sha256"], base_lint["counts"]))
        if observe is not None:
            out.append(events.observation(cyc, observe["base_run_sha256"], observe["fixable"]))
        out += candidate_rows(cyc, decided, merged, change)
        if red is not None:
            out.append(events.revert(cyc, red["merge_sha"], cause))
        elif end is not None:
            out.append(events.sentinel(cyc, end["merge_sha"], end["verdict"], end["flaky"]))
        if planted:
            out.append(events.drill(cyc, "plant", revert_drill.plant_payload(drill["instance_id"], plant_sha)))
        elif action == "commit":
            out.append(events.drill(cyc, "commit", drill["payload"]))
        if gate is not None:
            out.append(events.row(cyc, "gate", PR.GATE_ROW[1], gate))
        if passed is not None:
            out.append(events.row(cyc, "pass", PR.PASS_ROW[1], passed))
        return out + accepts + list(cost)

    ledger, roots = art.state[B.STATE_LEDGER], art.state[B.STATE_ROOTS]
    args = (ledger, ledger, roots, roots, art.status)
    root_row_id = "%s:root" % cycle_id
    dry = rows(dict(PLACEHOLDER, path=change["path"]) if change else None, PLACEHOLDER["merge_sha"])
    judged = watched(dry)  # no view reads what the placeholders stand for
    frozen = watch.rows(cyc, judged)
    try:
        kept = findings_write.cycle(art.state.get(B.STATE_FINDINGS, b""), art.state.get(B.STATE_UNRESOLVED, b""),
                                    [] if proposals is None else proposals,
                                    [] if finding_decisions is None else finding_decisions, cyc["snapshot_id"],
                                    lambda path: derive._read_regular(tree, path))
    except append.HardStop as exc:
        raise land.HardStop("state: %s" % cli.cause(exc), []) from None
    except append.SecretRow as exc:
        raise Refused(["state_unwritable: %s" % cli.cause(exc)]) from None
    except findings_write.Unusable as exc:
        raise Unusable("findings: %s" % cli.cause(exc)) from None
    registers = {B.STATE_FINDINGS: kept.findings, B.STATE_UNRESOLVED: kept.unresolved}
    try:
        cased = case_store.add(art.state.get(B.STATE_CASES, b""), [] if cases is None else cases)
    except case_store.Broken as exc:
        raise land.HardStop("state: %s" % cli.cause(exc), []) from None
    except case_store.Unusable as exc:
        raise Unusable(cli.cause(exc)) from None
    sets = {B.STATE_CASES: cased["content"]}
    try:
        cycle.plan(*args, dry + frozen, imports, facts, DRY, root_row_id, registers, sets)
    except append.HardStop as exc:
        raise land.HardStop("state: %s" % cli.cause(exc), []) from None
    except cycle.FAILURES as exc:
        raise Refused(["state_unwritable: %s" % cli.cause(exc)]) from None
    state = append.TargetState(writer, art.heads[B.STATE])
    merged = reverted = plant = None
    landing = True  # step 4: the root is not signed yet
    try:
        if change is not None:
            merged = dict(land.land(writer, merge, change["path"], change["content"], art.heads[B.INTEGRATION],
                                    B.CHECK), path=change["path"])
        if red is not None:
            reverted = dict(land.revert(writer, red["merge_sha"], red["runs"], red["facts"], B.CHECK),
                            reverted=red["merge_sha"])
        if planted:
            plant = dict(land.plant(writer, cycle_id, drill["path"], drill["content"], art.heads[B.INTEGRATION],
                                    B.CHECK), instance_id=drill["instance_id"])
        landing = False
        planned = cycle.commit(state, "cycle %s" % cycle_id, *args,
                               rows(merged, plant and plant["merge_sha"]) + frozen, imports, facts, signer,
                               root_row_id, registers, sets)
    except W.Refused as exc:
        if landing and not writer.written:
            if exc.reasons == [W.BRANCH_DIFFERS]:  # ``commit_on``'s: the merge's branch, or the plant's
                raise BranchDiffers(W.BRANCH_DIFFERS) from None
            raise Refused([*exc.reasons]) from None
        raise WriteFailed("%s: %s" % (type(exc).__name__, cli.cause(exc)), sorted(set(writer.written))) from None
    except W.ApiError as exc:
        raise WriteFailed("%s: %s" % (type(exc).__name__, cli.cause(exc)), sorted(set(writer.written))) from None
    except cycle.FAILURES as exc:
        raise land.HardStop("%s: %s" % (type(exc).__name__, cli.cause(exc)), sorted(set(writer.written))) from None
    return {"merge": dict(merged, candidate=merge) if merged else None, "revert": reverted, "plant": plant,
            "state_sha": state.commits_made[-1],
            "root": planned["root"], "rekor_uuid": planned["entry"]["uuid"], "rows": len(planned["row_hashes"]),
            "edited": planned["edited"], "gozcu": judged,
            "cases": {k: cased[k] for k in ("added", "kept", "refused")},
            "findings": {"rows": sum(len(o.rows) for o in kept.observed) + len(kept.decided.rows),
                         "unresolved_rows": len(kept.decided.unresolved_rows), "refused": kept.decided.refused}}
