"""The PASS row's judgement: the conditions of asama-0/10a that the two targets' ``brain/state`` records, judged from
those files alone (stage 0, (B) step 9 of asama-0/08).

Rules: asama-0/10a (the (B) conditions; ``#pass``: the loop referee writes the PASS row on the toy's
``brain/state`` and it carries the hashes of the copy's genesis and merge rows), asama-0/08 (the order of (B)'s
cycles: the toy's genesis, merge, rejects, sentinel and revert drill, then the copy's), tohum/02 item 5 (the exit
decision is a ledger row the referee writes; "PASS is not a signature but the machine check of these conditions"),
26c and spec-038's draft (``expect.json`` ``{decision, reason?}``; a reject holds when its row's ``reasons`` is
exactly ``[reason]``), tohum/29m (``harness.revert_drill``: key, commitment, judge).

**Stated assumptions** (seed-046: no page gives the PASS row's shape, its writer's inputs or which conditions it
judges from the state; its draft): the row is ``events``/``pass`` with ``payload`` below (``ledger.schema``), and
``write`` puts it on the toy's ``brain/state`` as one cycle of its own (``ledger.cycle``: its ``cycle_start``, the
``pass`` row, the status row and block, one signed root), after ``judge`` gave ``PASS``. Which job or command runs
``write``, and how it reads the copy's state, no page says: nothing calls it yet (``status/off_live.json``).

**Inputs** (``judge(toy, copy, toy_expect, copy_expect, drill)``): each state ``{ledger, roots}``, the bytes of
``brain/state``'s ``ledger.jsonl`` and ``chain/root.jsonl``; each target's expectations ``{candidate id:
expect.json}`` (``expectations``: ``{decision: merge}`` or ``{decision: reject, reason: <non-empty string>}``, else
``Unusable``); ``drill`` ``{seed, catalog}`` (``harness.revert_drill``'s seed file and catalog objects) or ``None``.

**First** each state must conform to ``ledger.schema`` (``ledger_reasons``, ``roots_reasons``: the chains and every
row's shape); a state that does not gives ``<target>:state_invalid`` under every condition (``state`` carries the
schema's reasons) and nothing else is judged.

**Conditions judged**, each reason prefixed with its target (``toy:``, ``copy:``); "the first decision" of a
candidate is its first ``events``/``decision`` row (a candidate is offered again every cycle; after its merge its
diff no longer applies, so later rows are not its verdict):

- ``#genesis``: the ledger's first row is ``events``/``genesis`` (``genesis_not_first``) and no other row is
  (``genesis_repeated``);
- ``#taban``: the genesis cycle (its first ``cycle_start`` up to the next) holds a ``ratchet_base`` row
  (``base_missing``);
- ``#merge``: each candidate expected to merge has a first decision (``undecided:<cid>``) that is a merge
  (``not_merged:<cid>``);
- ``#ret``: each candidate expected to be rejected has a first decision (``undecided:<cid>``) that is a reject
  (``merged:<cid>``) whose ``reasons`` is exactly ``[reason]`` (``reason_mismatch:<cid>``);
- ``#nobetci #hayatta``: ``ledger.serial.unfinished`` reads the merges (``serial:<reason>`` when it refuses the
  ledger); every candidate merge (an ``events``/``merge`` row, tohum/26d; a planted merge is the drill's) is finished
  (``sentinel_unfinished:<sha>``) by a ``sentinel`` row of verdict ``green`` (``sentinel_flaky:<sha>``: 10a asks
  for green) and not by a ``revert`` (``reverted:<sha>``);
- ``#geri-alma``, the toy only: without ``drill``, ``drill_inputs_missing``. Each ``plant`` row is judged by
  ``harness.revert_drill.judge`` over the ledger's lines up to the next plant (the judge reads the last plant of
  what it is given), with the key of the last ``commit`` before it (its run id: ``loop.drill.committed_by``):
  no commitment before it is ``drill_uncommitted:<instance>``, a ``FAIL`` is ``drill_fail:<instance>:<reason>``
  for each reason (a plant whose merge is not yet reverted included: ``not_reverted``); each cause of
  ``DRILL_CAUSES`` needs a ``PASS`` drill whose key has it (``cause_unshown:<cause>``);
- ``#kok``: one root row per cycle (``roots_per_cycle:<roots>/<cycles>``) and the last root row's ``root`` is the
  ledger's (``ledger.anchor.root_of``; ``root_mismatch``);
- ``#durum``: each cycle holds exactly one ``status`` row (``status_count:<cycle_id>:<n>``);
- ``#model #belirtec``: some ``cost`` row (``canary_missing``) has outcome ``ok`` (``canary_not_ok``); each ``ok``
  row's ``models_served`` is exactly ``[model_requested]`` (``model_mismatch:<row_id>``); no row's
  ``usd_micros`` exceeds its ``cap_usd_micros`` (``cap_exceeded:<row_id>``).

``verdict`` is ``PASS`` iff no judged condition has a reason; the conditions in ``NOT_CHECKED`` are listed with the
place that holds their evidence and do not enter the verdict. ``payload`` (``PASS`` only, else ``None``): ``{stage:
0, copy_genesis_row_hash, copy_merge_row_hashes, conditions, not_checked}``, the copy's merge rows (its
``events``/``merge`` rows, the ones 26d's stage-open counts) in file order.

**The write** (``write(writer, head, toy, copy, ..., req, imports, signer, canary_cap_usd_micros)``, ``req``
``{cycle_id, ts, snapshot_id}``): nothing is written when the verdict is not ``PASS`` (``refused: [not_pass]``) or the
toy's ledger already holds a ``pass`` row (``already_passed``); else ``ledger.cycle.commit`` on ``brain/state`` at
``head`` (``ledger.append.TargetState``; a branch no longer at ``head`` is ``target.write``'s ``state_head_moved``).
Any refusal or failure of that commit is a ``target.land.HardStop`` naming the refs written. The answer is
``judge``'s with ``refused`` and ``written`` (``{state_sha, row_hashes, root}`` or ``None``).

Out of scope, stated: Rekor (each cycle's root is verified there by the next cycle's D1, ``loop.cek``; at the
opening by ``stage-open``); a candidate decided that no expectation names (not judged); whether the two states are
the targets' current heads (the caller reads them).

Command line, from ``referee/``, one JSON line on stdout::

    python -m harness.pass_row judge TOY_STATE COPY_STATE TOY_CANDIDATES COPY_CANDIDATES [CATALOG SEED]

``*_STATE`` a directory with ``brain/state``'s ``ledger.jsonl`` and ``chain/root.jsonl``; ``*_CANDIDATES`` a
directory of ``<cid>/expect.json``. Exit 0 ``PASS``, 1 ``FAIL``, 2 unusable input (``{"verdict": "FAIL"}``).
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from harness import revert_drill as RD
from ledger import anchor, append, chain, cycle, events, schema, serial
from loop import drill as DR
from target import branches, land, write as W
import cli

TARGETS = ("toy", "copy")
CONDITIONS = ("#genesis", "#taban", "#merge", "#ret", "#nobetci #hayatta", "#geri-alma", "#kok", "#durum",
              "#model #belirtec")
DRILL_CAUSES = ("test_regression", "build_break", "lint_regression")
NOT_CHECKED = {
    "#aktarim": "the import's signed result and the referee repository's setup/imports.jsonl (tohum/25a)",
    "#oyuncak": "the toy tree's hash beside (A)'s toy_tree_sha256 (the activation's input)",
    "#hedefler #drift": "the rulesets and the App as genesis reads them from the API (activate.genesis); "
                        "#genesis judges the genesis row's place, not its facts",
    "#kirmizi #kanarya": "each kos run's results (runner.kos), which brain/state does not hold",
    "#getir #birim": "getir's and kos's job lines, which brain/state does not hold",
    "#oracle-ayirt #mandal #sifir-test": "the gate's judgement of each merge (loop.decide), recorded only as the "
                                         "merge decision; not judged again here",
    "#kapsama-kaydi": "no writer of this repository writes hunk_covered (gate.check leaves it to the loop)",
    "#prompt": "a prompt refused for a secret pattern starts no process and writes no row (loop.cagir)",
    "#main #guvenlik-yolu": "the target's rulesets and target.write's refusals; brain/state records no write",
}


class Unusable(ValueError):
    pass


def _rows(data: bytes) -> list[dict]:
    return [chain.parse_row(line.decode("utf-8")) for line in chain._lines(data)]


def _is(row: dict, part: str, kind: str) -> bool:
    return row["part"] == part and row["kind"] == kind


def expectations(docs: Any) -> dict[str, dict]:
    """``{cid: expect}`` checked (see the module docstring), else ``Unusable``."""
    if not isinstance(docs, dict):
        raise Unusable("expectations must be {candidate id: expect.json}")
    for cid, exp in docs.items():
        ok = isinstance(exp, dict) and (exp == {"decision": "merge"} or (
            set(exp) == {"decision", "reason"} and exp["decision"] == "reject"
            and isinstance(exp["reason"], str) and exp["reason"] != ""))
        if not isinstance(cid, str) or not cid or not ok:
            raise Unusable("candidate %r: expect.json must be {decision: merge} or {decision: reject, reason}" % cid)
    return docs


def _cycles(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """``(cycle_id, rows)`` from each ``cycle_start`` up to the next."""
    out: list[tuple[str, list[dict]]] = []
    for row in rows:
        if _is(row, "events", "cycle_start"):
            out.append((row["payload"]["cycle_id"], []))
        elif out:
            out[-1][1].append(row)
    return out


def _first_decisions(rows: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in rows:
        if _is(row, "events", "decision"):
            out.setdefault(row["payload"]["candidate"], row)
    return out


def _genesis(rows: list[dict]) -> list[str]:
    found = [i for i, row in enumerate(rows) if _is(row, "events", "genesis")]
    out = [] if found[:1] == [0] else ["genesis_not_first"]
    return out + (["genesis_repeated"] if len(found) > 1 else [])


def _base(rows: list[dict]) -> list[str]:
    cycles = _cycles(rows)
    held = cycles and any(_is(row, "events", "ratchet_base") for row in cycles[0][1])
    return [] if held else ["base_missing"]


def _decided(rows: list[dict], expect: dict[str, dict]) -> tuple[list[str], list[str]]:
    first = _first_decisions(rows)
    merges, rejects = [], []
    for cid in sorted(expect):
        exp, row = expect[cid], first.get(cid)
        got = row["payload"] if row else None
        if exp["decision"] == "merge":
            merges += ["undecided:" + cid] if got is None else [] if got["decision"] == "merge" else ["not_merged:" + cid]
        elif got is None:
            rejects.append("undecided:" + cid)
        elif got["decision"] == "merge":
            rejects.append("merged:" + cid)
        elif got["reasons"] != [exp["reason"]]:
            rejects.append("reason_mismatch:" + cid)
    return merges, rejects


def _candidate_merges(rows: list[dict]) -> list[dict]:
    return [row for row in rows if _is(row, "events", "merge")]


def _sentinels(ledger: bytes, rows: list[dict]) -> list[str]:
    try:
        serial.unfinished(ledger)  # its refusals; a merge it counts unfinished has no end row below
    except serial.Unusable as exc:
        return ["serial:" + r for r in exc.reasons]
    out = []
    for row in _candidate_merges(rows):
        sha = row["payload"]["merge_sha"]
        ends = [r for r in rows if r["payload"].get("merge_sha") == sha
                and (_is(r, "events", "sentinel") or _is(r, "events", "revert"))]
        if not ends:
            out.append("sentinel_unfinished:" + sha)
        elif _is(ends[0], "events", "revert"):
            out.append("reverted:" + sha)
        elif ends[0]["payload"]["verdict"] != "green":
            out.append("sentinel_flaky:" + sha)
    return out


def _drills(ledger: bytes, rows: list[dict], drill: dict | None) -> list[str]:
    if drill is None:
        return ["drill_inputs_missing"]
    lines = chain._lines(ledger)
    plants = [i for i, row in enumerate(rows) if RD.is_drill(row, "plant")]
    out, shown = [], set()
    for n, p in enumerate(plants):
        instance = rows[p]["payload"]["instance_id"]
        commits = [i for i in range(p) if RD.is_drill(rows[i], "commit")]
        if not commits:
            out.append("drill_uncommitted:" + instance)
            continue
        try:
            answer = RD.key(drill["seed"], DR.committed_by(rows, commits[-1]), drill["catalog"])
        except (DR.Unusable, RD.Unusable) as exc:
            raise Unusable("drill: %s" % cli.cause(exc)) from None
        end = plants[n + 1] if n + 1 < len(plants) else len(lines)
        verdict = RD.judge(b"".join(line + b"\n" for line in lines[:end]), answer)
        out += ["drill_fail:%s:%s" % (instance, r) for r in verdict["reasons"]]
        if verdict["verdict"] == "PASS":
            shown.add(answer["cause"])
    return out + ["cause_unshown:" + c for c in DRILL_CAUSES if c not in shown]


def _roots(ledger: bytes, roots: bytes, rows: list[dict]) -> list[str]:
    root_rows = _rows(roots)
    cycles = len(_cycles(rows))
    out = [] if len(root_rows) == cycles else ["roots_per_cycle:%d/%d" % (len(root_rows), cycles)]
    last = root_rows[-1]["root"] if root_rows else None
    return out + ([] if last == anchor.root_of(anchor.tips(ledger)) else ["root_mismatch"])


def _status(rows: list[dict]) -> list[str]:
    out = []
    for cycle_id, held in _cycles(rows):
        n = sum(1 for row in held if _is(row, "events", "status"))
        if n != 1:
            out.append("status_count:%s:%d" % (cycle_id, n))
    return out


def _canary(rows: list[dict]) -> list[str]:
    costs = [row for row in rows if _is(row, "cost", "cost")]
    if not costs:
        return ["canary_missing"]
    ok = [row for row in costs if row["payload"]["outcome"] == "ok"]
    out = [] if ok else ["canary_not_ok"]
    out += ["model_mismatch:" + row["row_id"] for row in ok
            if row["payload"]["models_served"] != [row["payload"]["model_requested"]]]
    return out + ["cap_exceeded:" + row["row_id"] for row in costs
                  if row["payload"]["usd_micros"] > row["payload"]["cap_usd_micros"]]


def _target(name: str, state: dict, expect: dict, drill: dict | None) -> dict[str, list[str]]:
    ledger, rows = state["ledger"], _rows(state["ledger"])
    merges, rejects = _decided(rows, expect)
    found = {"#genesis": _genesis(rows), "#taban": _base(rows), "#merge": merges, "#ret": rejects,
             "#nobetci #hayatta": _sentinels(ledger, rows),
             "#geri-alma": _drills(ledger, rows, drill) if name == "toy" else [],
             "#kok": _roots(ledger, state["roots"], rows), "#durum": _status(rows), "#model #belirtec": _canary(rows)}
    return {cond: ["%s:%s" % (name, r) for r in reasons] for cond, reasons in found.items()}


def _payload(copy: dict) -> dict:
    rows = _rows(copy["ledger"])
    return {"stage": 0, "copy_genesis_row_hash": rows[0]["row_hash"],
            "copy_merge_row_hashes": [row["row_hash"] for row in _candidate_merges(rows)],
            "conditions": sorted(CONDITIONS), "not_checked": sorted(NOT_CHECKED)}


def judge(toy: dict, copy: dict, toy_expect: Any, copy_expect: Any, drill: dict | None) -> dict:
    """``{verdict, conditions, not_checked, state, payload}`` (see the module docstring)."""
    expects = {"toy": expectations(toy_expect), "copy": expectations(copy_expect)}
    states = {"toy": toy, "copy": copy}
    invalid = {name: schema.ledger_reasons(s["ledger"]) + schema.roots_reasons(s["roots"])
               for name, s in states.items()}
    conditions: dict[str, list[str]] = {cond: [] for cond in CONDITIONS}
    if any(invalid.values()):
        for cond in CONDITIONS:
            conditions[cond] = ["%s:state_invalid" % name for name in TARGETS if invalid[name]]
    else:
        for name in TARGETS:
            for cond, reasons in _target(name, states[name], expects[name], drill).items():
                conditions[cond] += reasons
    passed = not any(conditions.values())
    return {"verdict": "PASS" if passed else "FAIL", "conditions": conditions, "not_checked": dict(NOT_CHECKED),
            "state": {name: reasons for name, reasons in invalid.items() if reasons},
            "payload": _payload(copy) if passed else None}


def write(writer: W.Writer, head: str, toy: dict, copy: dict, toy_expect: Any, copy_expect: Any, drill: dict | None,
          req: dict, imports: bytes, signer: Any, canary_cap_usd_micros: int) -> dict:
    """The PASS row on the toy's ``brain/state`` at ``head`` (see the module docstring); ``toy`` also carries the
    head's ``status`` bytes (``None`` without a ``status.md``)."""
    got = judge(toy, copy, toy_expect, copy_expect, drill)
    refused = []
    if got["verdict"] != "PASS":
        refused.append("not_pass")
    elif any(row["part"] == "events" and row["kind"] == "pass" for row in _rows(toy["ledger"])):
        refused.append("already_passed")
    if refused:
        return dict(got, refused=refused, written=None)
    rows = [events.start(req), events.row(req, "pass", "pass", got["payload"])]
    facts = {"ts": req["ts"], "snapshot_id": req["snapshot_id"], "row_id": "%s:status" % req["cycle_id"],
             "canary_cap_usd_micros": canary_cap_usd_micros}
    state = append.TargetState(writer, head)
    try:
        planned = cycle.commit(state, "pass: cycle %s" % req["cycle_id"], toy["ledger"], toy["ledger"],
                               toy["roots"], toy["roots"], toy["status"], rows, imports, facts, signer,
                               "%s:root" % req["cycle_id"])
    except (W.ApiError, W.Refused) + cycle.FAILURES as exc:
        raise land.HardStop("%s: %s" % (type(exc).__name__, cli.cause(exc)), sorted(set(writer.written))) from None
    return dict(got, refused=[], written={"state_sha": state.commits_made[-1], "row_hashes": planned["row_hashes"],
                                          "root": planned["root"]})


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m harness.pass_row judge TOY_STATE COPY_STATE TOY_CANDIDATES COPY_CANDIDATES [CATALOG SEED]"


def _read(path: str) -> bytes:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise Unusable("%s: %s" % (path, cli.cause(exc))) from None


def _json(path: str) -> Any:
    return chain.parse_row(_read(path).decode("utf-8"))


def read_state(root: str) -> dict:
    return {"ledger": _read(os.path.join(root, branches.STATE_LEDGER)),
            "roots": _read(os.path.join(root, branches.STATE_ROOTS))}


def read_expectations(root: str) -> dict:
    try:
        names = sorted(os.listdir(root))
    except OSError as exc:
        raise Unusable("%s: %s" % (root, cli.cause(exc))) from None
    return {cid: _json(os.path.join(root, cid, "expect.json")) for cid in names}


def main(argv: list[str]) -> int:
    try:
        if not argv or argv[0] != "judge" or len(argv) not in (5, 7):
            raise Unusable(USAGE)
        drill = {"catalog": _json(argv[5]), "seed": _json(argv[6])} if len(argv) == 7 else None
        result = judge(read_state(argv[1]), read_state(argv[2]), read_expectations(argv[3]),
                       read_expectations(argv[4]), drill)
        sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
        return 0 if result["verdict"] == "PASS" else 1
    except (Unusable, UnicodeDecodeError, chain.ChainError) as exc:
        sys.stderr.write("unusable input: %s\n" % cli.cause(exc))
    sys.stdout.write(json.dumps(FAULT_LINE(argv)) + "\n")
    return 2


def FAULT_LINE(argv: list[str]) -> dict:  # noqa: N802 - cli.run's fault line
    return {"verdict": "FAIL"}


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
