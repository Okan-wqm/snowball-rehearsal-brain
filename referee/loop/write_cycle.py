"""``yaz``'s D6: the cycle's writes on the target, from D5's decision (stage 0).

Rules: asama-0/01 D6 (``yaz`` writes ``brain/c/<id>``, the pull request, the check and the merge, and one
``brain/state`` commit per cycle with the signed root and ``status.md``; every ref under ``refs/heads/brain/``;
the chain verified before the write; judges MF9, 10, 11, 16), tohum/07 and tohum/01b (merges are serial, by pull
request; ``brain/state`` takes one direct commit per cycle on the head D1 verified), tohum/13 and tohum/28 (a chain
break or a root that cannot be signed is a hard stop), asama-0/10a ``#model`` (the canary's ``cost`` row is written).

**Inputs** (``write``): ``art``, the ``pulled`` artifact (``loop.pulled.read``): its ``brain/state`` ledger, roots
file and ``status.md`` as D1 read them, its heads, its candidates, its policy; ``tree``, the directory its tree was
extracted to (the tree D3 ran on and D5 judged); ``decided``, ``loop.decide``'s ``{decisions, merge}``; ``cost``,
the cost rows of this cycle's ``response`` (``loop.cagir.read_response``); ``writer``, a ``target.write.Writer`` on
the target's repository; ``signer``, the root's signer (``loop.sign.SigstoreSigner`` in the job); ``imports``,
``setup/imports.jsonl``'s bytes (``status.block``'s human-touch count); ``cycle_id`` and ``ts``.

**Order.** Nothing is written on the target before every check holds, and nothing is signed before the rows are
planned:

1. the merge, when D5 chose one: its diff applied to the tree (``target.land.applied``, the one application
   ``activate`` makes); a reason here means D5 chose a candidate that cannot be written, ``Unusable``;
2. both heads read from the target equal ``pulled``'s (``head_moved:<branch>``, ``Refused``): the state this cycle
   decided on is still the state it writes on, so a second run of the same cycle (a rerun of ``yaz`` after its
   first run wrote) writes nothing;
3. a dry plan: ``ledger.cycle.plan`` of the cycle's rows with the merge's answer left as placeholders and a signer
   that signs nothing (``DRY``): the roots file and the ledger as chains extending themselves (D1's versions are the
   previous ones: nothing was added since), the rows' secret scan, the whole new ledger against ``ledger.schema``,
   the root row's id. A failure is ``Refused`` with ``state_unwritable`` (a ``ledger.append.HardStop`` stays a hard
   stop, ``target.land.HardStop`` with nothing written);
4. the merge landed (``target.land.land``) on ``brain/integration``'s head with the check ``target.branches.CHECK``;
5. ``ledger.cycle.commit`` on ``brain/state`` at ``pulled``'s head (``ledger.append.TargetState``: the writer
   refuses a moved head before creating anything): the rows, ``status.md``'s block and the signed root, one commit.

A failure after the first write of step 4 or 5 is ``target.land.HardStop`` naming the refs written
(``writer.written``).

**The rows**, in this order, each ``ledger.events``': ``cycle_start {cycle_id}``; one ``decision`` per candidate in
code-point order of its id (a reject with D5's reasons and ``ledger.events.cause``; the merge with ``path`` and
``target.land.land``'s ``{pull, head_sha, merge_sha}``); the response's cost rows as they are; then
``status.block``'s rows (``ledger.cycle``). ``ts`` is the given time; ``snapshot_id`` is ``brain/integration``'s
head in ``pulled`` (the snapshot D3 ran on and D5 judged; the cost row carries the same, ``loop.cagir``). Row ids are
``<cycle_id>:start``, ``<cycle_id>:c:<cid>``, ``<cycle_id>:status`` and the root row's ``<cycle_id>:root``. The
status facts' ``canary_cap_usd_micros`` is ``canary_usd`` of ``pulled``'s policy (``loop.cagir.CANARY_USD``, the
cap D4 called with).

Returns ``{merge: {candidate, path, pull, head_sha, merge_sha} | None, state_sha, root, rekor_uuid, rows, edited}``.

Out of scope, stated: D7's sentinel and revert and D8's drill (not wired); whether GitHub's ruleset accepts the
writes (``target.write``'s known limits); the signer's program (``loop.sign``).
"""

from __future__ import annotations

from typing import Any

from dispatcher import llm_call
from ledger import append, cycle, events
from loop import cagir
from loop import pulled as P
from target import branches as B
from target import land
from target import write as W
import cli

PLACEHOLDER = {"pull": 1, "head_sha": "0" * 40, "merge_sha": "0" * 40}  # the dry plan's merge answer


class Refused(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


class Unusable(ValueError):
    pass


class _Dry:
    """Signs nothing: the dry plan's signer (step 3)."""

    def sign(self, payload: bytes) -> dict:
        return {"uuid": "dry", "identity": "dry"}


DRY = _Dry()


def write(art: P.Pulled, tree: str, decided: dict, cost: list[dict], writer: W.Writer, signer: Any,
          imports: bytes, cycle_id: str, ts: str) -> dict[str, Any]:
    """D6 (see the module docstring)."""
    cyc = {"cycle_id": cycle_id, "ts": ts, "snapshot_id": art.heads[B.INTEGRATION]}
    merge = decided["merge"]
    change = None
    if merge is not None:
        change = land.applied(tree, art.candidates[merge]["diff.patch"].decode("utf-8", "surrogateescape"))
        if change["reasons"]:
            raise Unusable("merge %s cannot be written: %s" % (merge, ", ".join(change["reasons"])))
    moved = ["head_moved:%s" % b for b in P.HEAD_BRANCHES if writer.head(b) != art.heads[b]]
    if moved:
        raise Refused(moved)
    try:
        cap = llm_call.policy_usd(art.policy_bytes, *cagir.CANARY_USD)
    except llm_call.Unusable as exc:
        raise Unusable(cli.cause(exc)) from None
    facts = {"ts": ts, "snapshot_id": cyc["snapshot_id"], "row_id": "%s:status" % cycle_id,
             "canary_cap_usd_micros": cap}

    def rows(merged: dict | None) -> list[dict]:
        out = [events.start(cyc)]
        for cid in sorted(decided["decisions"]):
            out.append(events.decision(cyc, cid, decided["decisions"][cid]["reasons"], merged if cid == merge else None))
        return out + list(cost)

    ledger, roots = art.state[B.STATE_LEDGER], art.state[B.STATE_ROOTS]
    args = (ledger, ledger, roots, roots, art.status)
    root_row_id = "%s:root" % cycle_id
    try:
        cycle.plan(*args, rows(dict(PLACEHOLDER, path=change["path"]) if change else None), imports, facts, DRY,
                   root_row_id)
    except append.HardStop as exc:
        raise land.HardStop("state: %s" % cli.cause(exc), []) from None
    except cycle.FAILURES as exc:
        raise Refused(["state_unwritable: %s" % cli.cause(exc)]) from None
    state = append.TargetState(writer, art.heads[B.STATE])
    merged = None
    try:
        if change is not None:
            merged = dict(land.land(writer, merge, change["path"], change["content"], art.heads[B.INTEGRATION],
                                    B.CHECK), path=change["path"])
        planned = cycle.commit(state, "cycle %s" % cycle_id, *args, rows(merged), imports, facts, signer, root_row_id)
    except (W.ApiError, W.Refused) + cycle.FAILURES as exc:
        raise land.HardStop("%s: %s" % (type(exc).__name__, cli.cause(exc)), sorted(set(writer.written))) from None
    return {"merge": dict(merged, candidate=merge) if merged else None, "state_sha": state.commits_made[-1],
            "root": planned["root"], "rekor_uuid": planned["entry"]["uuid"], "rows": len(planned["row_hashes"]),
            "edited": planned["edited"]}
