"""The PASS row's judgement: the conditions of asama-0/10a that the two targets' ``brain/state`` records, judged from
those files alone (stage 0, (B) step 9 of asama-0/08).

Rules: asama-0/10a (the (B) conditions; ``#pass``: the loop referee writes the PASS row on the toy's
``brain/state`` and it carries the hashes of the copy's genesis and merge rows), asama-0/08 (the order of (B)'s
cycles: the toy's genesis, merge, rejects, sentinel and revert drill, then the copy's), tohum/02 item 5 (the exit
decision is a ledger row the referee writes; "PASS is not a signature but the machine check of these conditions"),
26c and spec-038's draft (``expect.json`` ``{decision, reason?}``; a reject holds when its row's ``reasons`` is
exactly ``[reason]``), tohum/29m (``harness.revert_drill``: key, commitment, judge), tohum/26d (the PASS row's
``payload``; the referee's own row; (B) runs on each ledger's last genesis and only the rows from it on count;
stage-open's conditions 2-7).

**The row** (tohum/26d): ``events``/``pass`` (26d leaves ``kind`` free; ``ledger.schema``'s type), written by
``ledger.events.row``: ``derivation`` ``tool``, ``trust`` ``verified``, no ``proposed_by``. **Stated assumptions**
(seed-046 (b)-(e), still open): which (B) conditions are judged from the states (below; the others are in
``NOT_CHECKED``), and that ``write`` puts the row on the toy's ``brain/state`` as one cycle of its own
(``ledger.cycle``: its ``cycle_start``, the ``pass`` row, the status row and block, one signed root), after ``judge``
gave ``PASS``. The module is on the live path through the copy's genesis gate (below: ``gate`` and
``gate_opened``, called by ``loop.job``, and ``GATE_ROW`` by ``loop.write_cycle``); ``judge`` and ``write`` have no
caller in the loop yet: 26d:9 and 29s:19-24 name the loop referee's run over both targets as the writer, but the PASS
row's ``owner_exception`` needs the bytes of the signed (A) result, which no page puts where a run can read them
(the import keeps only their hash in ``setup/imports.jsonl``; seed-048).

**Inputs** (``judge(toy, copy, toy_expect, copy_expect, drill, imports, result)``): each state ``{ledger, roots}``, the
bytes of ``brain/state``'s ``ledger.jsonl`` and ``chain/root.jsonl``; each target's expectations ``{candidate id:
expect.json}`` (``expectations``: ``{decision: merge}`` or ``{decision: reject, reason: <non-empty string>}``, else
``Unusable``); ``drill`` ``{seed, catalog}`` (``harness.revert_drill``'s seed file and catalog objects) or ``None``;
``imports``, the bytes of the referee repository's ``setup/imports.jsonl`` (its last import, the last row carrying
``referee_tree_sha256``: ``loop.accepted.last_import``, the reader D1 and ``activate`` share), and ``result``, the
bytes of the signed (A) result that import names. ``imported`` reads them; each is ``Unusable`` when: the imports
are not a valid chain or hold no import (``loop.accepted``'s reasons); sha256 of ``result`` is not the import's
``result_sha256``; ``result`` is not a JSON object with an ``exit`` object; its ``exit.owner_exception``, when
present, is not ``ledger.schema.OWNER_EXCEPTION``.

**The run** of a target is its ledger from the last ``events``/``genesis`` row on (the whole ledger when the first
row is not a genesis: ``#genesis`` fails then). ``#taban``, ``#merge``, ``#ret``, the merges of ``#nobetci
#hayatta``, the plants and commitments of ``#geri-alma``, and ``#model #belirtec`` read the run; ``#kok``,
``#durum`` and ``ledger.serial``'s refusals read the whole files.

**First** each state must conform to ``ledger.schema`` (``ledger_reasons``, ``roots_reasons``: the chains and every
row's shape); a state that does not gives ``<target>:state_invalid`` under every condition (``state`` carries the
schema's reasons) and nothing else is judged.

**Conditions judged**, each reason prefixed with its target (``toy:``, ``copy:``); "the first decision" of a
candidate is its first ``events``/``decision`` row (a candidate is offered again every cycle; after its merge its
diff no longer applies, so later rows are not its verdict):

- ``#genesis``: the ledger's first row is ``events``/``genesis`` (``genesis_not_first``; nothing else is judged
  under it then); the last genesis's ``import_line_sha256``, ``referee_tree_sha256`` and ``result_sha256`` are the
  import's (``genesis_import:<key>`` each, 26d stage-open 2 and 5);
- ``#taban``: the run's first cycle (its first ``cycle_start`` up to the next) holds a ``ratchet_base`` row
  (``base_missing``);
- ``#merge``: the run holds at least one ``events``/``merge`` row (``merge_missing``; 26d stage-open 4 for the toy,
  ``copy_merge_row_hashes`` non-empty for the copy); each candidate expected to merge has a first decision
  (``undecided:<cid>``) that is a merge (``not_merged:<cid>``);
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
place that holds their evidence and do not enter the verdict. ``payload`` (``PASS`` only, else ``None``), 26d's
fields and two of this brain's: ``{stage: 0, verdict: "PASS", import_line_sha256, copy_genesis_row_hash,
copy_merge_row_hashes, owner_exception?, conditions, not_checked}``: the import's line hash; the ``row_hash`` of the
copy's last genesis; the copy's run's ``events``/``merge`` rows (the ones 26d's stage-open counts) in file order;
the (A) result's ``exit.owner_exception`` as read, absent when the result has none.

**The write** (``write(writer, head, toy, copy, ..., req, imports, result, signer, canary_cap_usd_micros)``,
``req`` ``{cycle_id, ts, snapshot_id}``): nothing is written when the verdict is not ``PASS`` (``refused:
[not_pass]``) or the toy's run already holds a ``pass`` row (``already_passed``; a PASS before a later genesis is
another run's); else ``ledger.cycle.commit`` on ``brain/state`` at ``head`` (``ledger.append.TargetState``; a
branch no longer at ``head`` is ``target.write``'s ``state_head_moved``).
Any refusal or failure of that commit is a ``target.land.HardStop`` naming the refs written. The answer is
``judge``'s with ``refused`` and ``written`` (``{state_sha, row_hashes, root}`` or ``None``).

**The copy's genesis gate** (tohum/25a row 7 and 29s: the copy's genesis waits until the toy's cycles 1-5, asama-0/08
rows 1-5, are green, read from the toy's ``brain/state``). ``gate(toy, toy_expect, drill, imports)`` judges every
condition of ``CONDITIONS`` on the toy's state alone, exactly as ``judge`` judges the toy's half (the same
``_judged``; ``import_keys`` gives ``#genesis`` its three keys from the imports alone, no (A) result is read):
rows 1-5 are ``#genesis`` and ``#taban`` (1), ``#merge`` and ``#ret`` (2), ``#nobetci #hayatta`` (3),
``#geri-alma`` (4), ``#model #belirtec`` (5), and every cycle's ``#kok`` and ``#durum``. ``open`` iff no condition
has a reason. It is judged where the drill seed is, ``yaz`` (tohum/26f: only ``yaz``'s step holds it), on the toy's
state as D1 verified it, and recorded there: ``yaz`` adds the referee's own row ``events``/``copy_gate``
(``GATE_ROW``; payload ``gate_payload``, the conditions judged) to the toy's cycle when the gate is open and the
toy's run holds none yet; the next run's ``cek`` reads it from the toy's verified ledger (``gate_opened``: such a row,
without ``proposed_by``, after the last genesis; a ledger that does not conform to ``ledger.schema`` opens nothing) and
only then serves a copy with neither head as its genesis cycle. The row's shape is this brain's (no seed page names
the gate's record; seed-048's draft).

Out of scope, stated: Rekor (each cycle's root is verified there by the next cycle's D1, ``loop.cek``; at the
opening by ``stage-open``); a candidate decided that no expectation names (not judged); whether the two states are
the targets' current heads (the caller reads them); the (A) result's signature (``imported`` checks only that it is
the result the import names; ``loop.accepted.open_state`` verifies D1's, ``stage-open`` the opening's).

Command line, from ``referee/``, one JSON line on stdout::

    python -m harness.pass_row judge TOY_STATE COPY_STATE TOY_CANDIDATES COPY_CANDIDATES IMPORTS RESULT [CATALOG SEED]

``*_STATE`` a directory with ``brain/state``'s ``ledger.jsonl`` and ``chain/root.jsonl``; ``*_CANDIDATES`` a
directory of ``<cid>/expect.json``; ``IMPORTS`` and ``RESULT`` the two files ``imported`` reads. Exit 0 ``PASS``,
1 ``FAIL``, 2 unusable input (``{"verdict": "FAIL"}``).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

from harness import revert_drill as RD
from ledger import anchor, append, chain, cycle, events, schema, serial
from loop import accepted as AC
from loop import drill as DR
from target import branches, land, write as W
import cli

TARGETS = ("toy", "copy")
IMPORT_KEYS = ("import_line_sha256", "referee_tree_sha256", "result_sha256")  # a genesis row's, the import's (29o)
CONDITIONS = ("#genesis", "#taban", "#merge", "#ret", "#nobetci #hayatta", "#geri-alma", "#kok", "#durum",
              "#model #belirtec")
DRILL_CAUSES = ("test_regression", "build_break", "lint_regression")
GATE_ROW = ("events", "copy_gate")  # the toy's record that the copy's genesis gate opened (ledger.schema)
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


def _last_genesis(rows: list[dict]) -> int:
    """The index of the ledger's last ``genesis`` row (tohum/26d: (B) runs on it), 0 when there is none."""
    found = [i for i, row in enumerate(rows) if _is(row, "events", "genesis")]
    return found[-1] if found else 0


def _genesis(rows: list[dict], imported: dict) -> list[str]:
    out = [] if rows and _is(rows[0], "events", "genesis") else ["genesis_not_first"]
    if out:
        return out
    payload = rows[_last_genesis(rows)]["payload"]
    return ["genesis_import:" + key for key in IMPORT_KEYS if payload[key] != imported[key]]


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
    lines, since = chain._lines(ledger), _last_genesis(rows)
    plants = [i for i, row in enumerate(rows) if i > since and RD.is_drill(row, "plant")]
    out, shown = [], set()
    for n, p in enumerate(plants):
        instance = rows[p]["payload"]["instance_id"]
        commits = [i for i in range(since, p) if RD.is_drill(rows[i], "commit")]
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
    mine = anchor.root_of(anchor.tips(ledger)) if rows else None  # an empty ledger has no tip (#genesis names it)
    return out + ([] if last == mine else ["root_mismatch"])


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


def _target(name: str, state: dict, expect: dict, drill: dict | None, imported: dict) -> dict[str, list[str]]:
    ledger, rows = state["ledger"], _rows(state["ledger"])
    run = rows[_last_genesis(rows):]  # the rows of the (B) run: its genesis on (tohum/26d)
    merges, rejects = _decided(run, expect)
    found = {"#genesis": _genesis(rows, imported), "#taban": _base(run),
             "#merge": ([] if _candidate_merges(run) else ["merge_missing"]) + merges, "#ret": rejects,
             "#nobetci #hayatta": _sentinels(ledger, run),
             "#geri-alma": _drills(ledger, rows, drill) if name == "toy" else [],
             "#kok": _roots(ledger, state["roots"], rows), "#durum": _status(rows), "#model #belirtec": _canary(run)}
    return {cond: ["%s:%s" % (name, r) for r in reasons] for cond, reasons in found.items()}


def import_keys(imports: bytes) -> dict:
    """The counter's last import (``loop.accepted.last_import``, the one reader): ``{referee_tree_sha256,
    result_sha256, import_line_sha256}``, the three keys ``#genesis`` judges, else ``Unusable``."""
    try:
        row, line = AC.last_import(imports)
    except AC.StateError as exc:
        raise Unusable("imports: %s" % exc.reasons[0]) from None
    return {"referee_tree_sha256": row["referee_tree_sha256"], "result_sha256": row.get("result_sha256"),
            "import_line_sha256": hashlib.sha256(line).hexdigest()}


def imported(imports: bytes, result: bytes) -> dict:
    """``import_keys`` and the (A) result the import names: ``{referee_tree_sha256, result_sha256,
    import_line_sha256, owner_exception?}``, else ``Unusable``."""
    out = import_keys(imports)
    if out["result_sha256"] != hashlib.sha256(result).hexdigest():
        raise Unusable("result: not the (A) result the last import names (result_sha256)")
    try:
        doc = chain.parse_row(result.decode("utf-8"))
    except (UnicodeDecodeError, chain.ChainError) as exc:
        raise Unusable("result: %s" % cli.cause(exc)) from None
    exit_ = doc.get("exit") if isinstance(doc, dict) else None
    if not isinstance(exit_, dict):
        raise Unusable("result: no exit object")
    if "owner_exception" in exit_:
        if schema.OWNER_EXCEPTION(exit_["owner_exception"], "owner_exception"):
            raise Unusable("result: exit.owner_exception is not {anchor, stage, carry_to, reason, carry_commitment, "
                           "measured: false}")
        out["owner_exception"] = exit_["owner_exception"]
    return out


def _payload(copy: dict, imported: dict) -> dict:
    rows = _rows(copy["ledger"])
    since = _last_genesis(rows)
    out = {"stage": 0, "verdict": "PASS", "import_line_sha256": imported["import_line_sha256"],
           "copy_genesis_row_hash": rows[since]["row_hash"],
           "copy_merge_row_hashes": [row["row_hash"] for row in _candidate_merges(rows[since:])],
           "conditions": sorted(CONDITIONS), "not_checked": sorted(NOT_CHECKED)}
    if "owner_exception" in imported:
        out["owner_exception"] = imported["owner_exception"]
    return out


def judge(toy: dict, copy: dict, toy_expect: Any, copy_expect: Any, drill: dict | None, imports: bytes,
          result: bytes) -> dict:
    """``{verdict, conditions, not_checked, state, payload}`` (see the module docstring)."""
    imp = imported(imports, result)
    conditions, invalid = _judged({"toy": toy, "copy": copy},
                                  {"toy": expectations(toy_expect), "copy": expectations(copy_expect)}, drill, imp)
    passed = not any(conditions.values())
    return {"verdict": "PASS" if passed else "FAIL", "conditions": conditions, "not_checked": dict(NOT_CHECKED),
            "state": invalid, "payload": _payload(copy, imp) if passed else None}


def _judged(states: dict, expects: dict, drill: dict | None, imp: dict) -> tuple[dict[str, list[str]], dict]:
    """Every condition's reasons over the named states (``toy``, ``copy`` or both, in ``TARGETS``' order) and the
    states that do not conform to ``ledger.schema`` (their reasons)."""
    names = [name for name in TARGETS if name in states]
    invalid = {name: schema.ledger_reasons(states[name]["ledger"]) + schema.roots_reasons(states[name]["roots"])
               for name in names}
    conditions: dict[str, list[str]] = {cond: [] for cond in CONDITIONS}
    if any(invalid.values()):
        for cond in CONDITIONS:
            conditions[cond] = ["%s:state_invalid" % name for name in names if invalid[name]]
    else:
        for name in names:
            for cond, reasons in _target(name, states[name], expects[name], drill, imp).items():
                conditions[cond] += reasons
    return conditions, {name: reasons for name, reasons in invalid.items() if reasons}


def gate(toy: dict, toy_expect: Any, drill: dict | None, imports: bytes) -> dict:
    """The copy's genesis gate (tohum/25a row 7, 29s: the toy's cycles 1-5 green): every condition judged on the
    toy's state alone, as ``judge`` judges the toy's half (see "The copy's genesis gate" above): ``{verdict:
    open|closed, conditions, state}``, else ``Unusable``."""
    conditions, invalid = _judged({"toy": toy}, {"toy": expectations(toy_expect)}, drill, import_keys(imports))
    return {"verdict": "closed" if any(conditions.values()) else "open", "conditions": conditions, "state": invalid}


def gate_opened(ledger: bytes) -> bool:
    """Whether the toy's ledger (the bytes D1 verified) holds the referee's own ``events``/``copy_gate`` row after its
    last genesis (see "The copy's genesis gate" above); a ledger that does not conform to ``ledger.schema`` opens
    nothing."""
    if schema.ledger_reasons(ledger):
        return False
    rows = _rows(ledger)
    return any(_is(row, *GATE_ROW) and "proposed_by" not in row for row in rows[_last_genesis(rows):])


def gate_payload() -> dict:
    """The ``copy_gate`` row's payload: the conditions ``gate`` judged."""
    return {"conditions": sorted(CONDITIONS)}


def write(writer: W.Writer, head: str, toy: dict, copy: dict, toy_expect: Any, copy_expect: Any, drill: dict | None,
          req: dict, imports: bytes, result: bytes, signer: Any, canary_cap_usd_micros: int) -> dict:
    """The PASS row on the toy's ``brain/state`` at ``head`` (see the module docstring); ``toy`` also carries the
    head's ``status`` bytes (``None`` without a ``status.md``)."""
    got = judge(toy, copy, toy_expect, copy_expect, drill, imports, result)
    rows = _rows(toy["ledger"])
    refused = []
    if got["verdict"] != "PASS":
        refused.append("not_pass")
    elif any(_is(row, "events", "pass") for row in rows[_last_genesis(rows):]):
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

USAGE = ("usage: python -m harness.pass_row judge TOY_STATE COPY_STATE TOY_CANDIDATES COPY_CANDIDATES IMPORTS RESULT "
         "[CATALOG SEED]")


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
        if not argv or argv[0] != "judge" or len(argv) not in (7, 9):
            raise Unusable(USAGE)
        drill = {"catalog": _json(argv[7]), "seed": _json(argv[8])} if len(argv) == 9 else None
        result = judge(read_state(argv[1]), read_state(argv[2]), read_expectations(argv[3]),
                       read_expectations(argv[4]), drill, _read(argv[5]), _read(argv[6]))
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
