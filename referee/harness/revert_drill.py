"""``exit.drill``, revert family only: a committed bad merge is planted, reverted, and its ``cause`` judged
against the answer committed before the run (stage 0, MF14).

Rules: asama-0/14 row 14, asama-0/09 test 50, asama-0/01 step D8 (the previous cycle's ``yaz`` commits, this
cycle runs), tohum/22a ``#geri-alma`` (the planted merge is reverted and its ``cause`` equals the answer; the
commitment is in the chain before the run), tohum/26 (``drill`` payload; commitment before the run, reveal after,
a mismatch is ``FAIL``), tohum/29c (commitment = ``sha256(canonical(answer))``; an answer changed after the run,
``tampered_key``, fails), tohum/29d (group ``revert_drill``).

**The answer** (``answer``). The drill seed is the referee's secret, at least 32 bytes (RFC 2104 discourages an
HMAC key shorter than the hash output). ``selection = HMAC-SHA256(drill_seed, cycle_id)`` (``cycle_id`` as UTF-8),
lowercase hex; the planted fixture is ``fixtures[int(selection, 16) % n]`` with the fixtures sorted by ``id`` (code
point order), so the input order does not matter. The answer is exactly ``{drill: "revert", cycle_id, fixture,
cause, selection}`` with ``fixture`` the chosen id and ``cause`` its declared cause. A fixture is ``{id, cause,
files?}``: ``id`` a non-empty string, unique; ``cause`` one of ``gate.revert.CAUSES`` (the causes a revert can
produce, one source); ``files`` ``{path: text}``, the change the bad merge makes (read only when planting).

**The commitment** (``commitment``) is ``sha256(canonical(answer))`` (RFC 8785, ``ledger.chain.canonical``). The
answer carries the secret ``selection``, so the public commitment cannot be inverted by trying each fixture and
cause; and it differs per cycle even when the same fixture is chosen.

**The judge** (``judge``) reads the commitment, the revealed answer, the run's outcome ``{reverted, cause}``,
the seed and the fixtures, and names every reason that holds, in this order:

1. ``commitment_mismatch``: the revealed answer's commitment is not the committed one (an answer changed after
   the run, ``tampered_key``);
2. ``answer_not_from_seed``: the revealed answer is not ``answer(seed, answer.cycle_id, fixtures)`` (a
   commitment made without the seed);
3. ``not_reverted``: the planted merge was not reverted;
4. ``cause_mismatch``: it was reverted with a cause other than the answer's.

``PASS`` when none holds, else ``FAIL``. The outcome is exact: ``{reverted: true, cause: <one of CAUSES>}`` or
``{reverted: false, cause: null}``.

**The cycle before** (``commit_row``): the ``yaz`` job of cycle ``N`` computes the answer for ``cycle_id = N``
and returns a ``drill`` row (``kind: commit``) holding only the commitment and ``instance_id = N``, for that
cycle's one ``ledger.append`` commit. The fixture and the cause are not in it.

**The run** (``run_drill``), a later cycle:

1. The ledger read before the run must be a valid chain extending ``previous`` (``ledger.chain.verify_bytes``,
   the verifier ``ledger.append`` uses) or ``HardStop`` (``ledger.append``'s). The pending commitment is the last ``drill`` row with
   ``kind: commit`` and ``payload.drill: revert``, unless a ``kind: reveal`` row for the same ``instance_id``
   follows it; none is ``NoCommitment``. A commitment whose ``instance_id`` is the running cycle is refused
   (``Refused``): it must come from a previous cycle. Nothing is written in these cases.
2. The answer is recomputed from the seed for the committed cycle. If its commitment is not the committed one,
   the drill is ``FAIL`` (``commitment_mismatch``) and nothing is planted.
3. The fixture's ``files`` are committed on a new branch ``brain/drill/<cycle_id>`` from ``onto``'s head, a pull
   request is opened, a ``check_name`` check is posted with a summary saying the merge is planted by the drill
   and is not a gate decision, and the pull request is merged (``target.write``'s ``Writer``).
4. ``observe(merge)`` returns ``(runs, facts)`` of the contained runs at the planted head (the producer is not
   in the seed yet, as for ``gate.revert``); ``gate.revert.revert_red`` decides and reverts (calls 12 -> 13 -> 14)
   onto the branch ``brain/drill/<cycle_id>-revert``.
5. The judge rules on the revealed answer; ``reveal_row`` is the ``drill`` row (``kind: reveal``) with the
   revealed answer, its hash, the outcome and the verdict, for this cycle's ``ledger.append`` commit.

Out of scope here, stated: merging the revert's pull request (the gate's job, as in ``gate.revert``), writing
the rows (``ledger.append``; this module returns them), where the fixtures come from (the seed's drill
fixtures are not in this repository, seed-001), the other drill families (tohum/22a, stage 2), and covering the
three categories of asama-0/10a ``#geri-alma`` (the selection is per cycle; coverage is a property of the
cycles run, not of one drill).

Command line, run from ``referee/``, one JSON line on stdout, the cause of an error on stderr::

    python -m harness.revert_drill commit  stdin {drill_seed, cycle_id, fixtures}   -> {commitment_sha256}
    python -m harness.revert_drill reveal  stdin {drill_seed, cycle_id, fixtures}   -> {answer, commitment_sha256}
    python -m harness.revert_drill judge   stdin {drill_seed, fixtures, commitment_sha256, answer, outcome}
                                                                                  -> {verdict, reasons}
    ``drill_seed`` lowercase hex. exit 0 (judge: PASS), 1 judge FAIL, 2 unusable input (every output field null,
    ``reasons`` []).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
from typing import Any, Callable

from gate import revert
from ledger import append, chain
from target import write

DRILL = "revert"
PART = "drill"
MIN_SEED_BYTES = 32
ANSWER = {"drill", "cycle_id", "fixture", "cause", "selection"}
FIXTURE = {"id", "cause"}
FIXTURE_OPTIONAL = {"files"}
OUTCOME = {"reverted", "cause"}
REASONS = ("commitment_mismatch", "answer_not_from_seed", "not_reverted", "cause_mismatch")
HardStop = append.HardStop  # one hard stop for a ledger that is not a valid chain extending the previous one
HEX = set("0123456789abcdef")


class Unusable(ValueError):
    pass


class NoCommitment(Exception):
    """No pending revert-drill commitment in the ledger: the drill does not run."""


# ---------------------------------------------------------------- shapes

def _text(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _seed(value: Any) -> bytes:
    if not isinstance(value, bytes) or len(value) < MIN_SEED_BYTES:
        raise Unusable("the drill seed must be at least %d bytes" % MIN_SEED_BYTES)
    return value


def _cycle(value: Any) -> str:
    if not _text(value):
        raise Unusable("cycle_id must be a non-empty string")
    return value


def fixtures_by_id(fixtures: Any) -> dict[str, dict]:
    """The fixtures keyed by id; ``Unusable`` unless a non-empty list of ``{id, cause, files?}``, ids unique."""
    if not isinstance(fixtures, list) or not fixtures:
        raise Unusable("fixtures must be a non-empty list")
    out: dict[str, dict] = {}
    for item in fixtures:
        if not isinstance(item, dict) or not FIXTURE <= set(item) <= FIXTURE | FIXTURE_OPTIONAL:
            raise Unusable("a fixture is {id, cause, files?}")
        if not _text(item["id"]) or item["id"] in out:
            raise Unusable("fixture ids must be non-empty and unique")
        if item["cause"] not in revert.CAUSES:
            raise Unusable("fixture %r: cause must be one of %s" % (item["id"], ", ".join(revert.CAUSES)))
        files = item.get("files", {})
        if not isinstance(files, dict) or not all(write.file_path(p) and isinstance(t, str) for p, t in files.items()):
            raise Unusable("fixture %r: files must be {path: text} with plain file paths" % item["id"])
        out[item["id"]] = item
    return out


# ---------------------------------------------------------------- answer, commitment, judge

def selection(drill_seed: bytes, cycle_id: str) -> str:
    return hmac.new(_seed(drill_seed), _cycle(cycle_id).encode("utf-8"), hashlib.sha256).hexdigest()


def answer(drill_seed: bytes, cycle_id: str, fixtures: Any) -> dict:
    """The answer for ``cycle_id`` (see the module docstring)."""
    by_id = fixtures_by_id(fixtures)
    chosen = selection(drill_seed, cycle_id)
    ids = sorted(by_id)
    fixture = ids[int(chosen, 16) % len(ids)]
    return {"drill": DRILL, "cycle_id": cycle_id, "fixture": fixture, "cause": by_id[fixture]["cause"],
            "selection": chosen}


def commitment(ans: dict) -> str:
    return hashlib.sha256(chain.canonical(ans)).hexdigest()


def _answer_shape(ans: Any) -> dict:
    if not isinstance(ans, dict) or set(ans) != ANSWER or ans["drill"] != DRILL:
        raise Unusable("the answer must be {drill: revert, cycle_id, fixture, cause, selection}")
    if not all(_text(ans[k]) for k in ("cycle_id", "fixture", "cause", "selection")):
        raise Unusable("answer fields must be non-empty strings")
    return ans


def _outcome_shape(outcome: Any) -> dict:
    if not isinstance(outcome, dict) or set(outcome) != OUTCOME or type(outcome["reverted"]) is not bool:
        raise Unusable("the outcome must be {reverted: bool, cause}")
    if outcome["reverted"] != (outcome["cause"] is not None) or (
            outcome["reverted"] and outcome["cause"] not in revert.CAUSES):
        raise Unusable("the outcome's cause is one of the causes when reverted, null otherwise")
    return outcome


def _hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or not chain.HEX64.fullmatch(value):
        raise Unusable("%s must be 64 lowercase hex characters" % name)
    return value


def judge(committed: str, ans: Any, outcome: Any, drill_seed: bytes, fixtures: Any) -> dict:
    """``{verdict: PASS|FAIL, reasons}`` (see the module docstring)."""
    committed = _hex64(committed, "commitment_sha256")
    ans = _answer_shape(ans)
    outcome = _outcome_shape(outcome)
    expected = answer(drill_seed, ans["cycle_id"], fixtures)
    found = {
        "commitment_mismatch": commitment(ans) != committed,
        "answer_not_from_seed": ans != expected,
        "not_reverted": not outcome["reverted"],
        "cause_mismatch": outcome["reverted"] and outcome["cause"] != ans["cause"],
    }
    reasons = [r for r in REASONS if found[r]]
    return {"verdict": "FAIL" if reasons else "PASS", "reasons": reasons}


# ---------------------------------------------------------------- ledger rows

def _row(kind: str, payload: dict, row_id: str, ts: str, snapshot_id: str, cause: str | None = None) -> dict:
    row = {"row_id": row_id, "ts": ts, "part": PART, "kind": kind, "payload": payload, "derivation": "tool",
           "trust": "verified", "snapshot_id": snapshot_id, "evidence_refs": []}
    if cause is not None:
        row["cause"] = cause
    return row


def commit_row(drill_seed: bytes, cycle_id: str, fixtures: Any, row_id: str, ts: str, snapshot_id: str) -> dict:
    """Cycle ``cycle_id``'s commitment row: the commitment only, never the fixture or the cause."""
    payload = {"drill": DRILL, "question": "cause", "family": DRILL, "instance_id": cycle_id,
               "commitment_sha256": commitment(answer(drill_seed, cycle_id, fixtures)),
               "outcome": "committed", "verdict": "PENDING"}
    return _row("commit", payload, row_id, ts, snapshot_id)


def reveal_row(committed: str, ans: dict, outcome: dict, verdict: dict, row_id: str, ts: str,
               snapshot_id: str) -> dict:
    payload = {"drill": DRILL, "question": "cause", "family": DRILL, "instance_id": ans["cycle_id"],
               "commitment_sha256": committed, "revealed_sha256": commitment(ans), "answer": ans,
               "outcome": outcome["cause"] if outcome["reverted"] else "not_reverted",
               "verdict": verdict["verdict"], "reasons": verdict["reasons"]}
    return _row("reveal", payload, row_id, ts, snapshot_id, outcome["cause"])


def _is_drill(row: dict, kind: str) -> bool:
    payload = row.get("payload")
    return (row.get("part") == PART and row.get("kind") == kind and isinstance(payload, dict)
            and payload.get("drill") == DRILL)


def pending_commitment(ledger: bytes, previous: bytes) -> dict:
    """The last revert-drill commitment not yet revealed: ``{instance_id, commitment_sha256}``."""
    verdict = chain.verify_bytes(ledger, previous)
    if not verdict["valid"]:
        raise HardStop("ledger: %s (%s)" % (verdict["reason"], verdict["broken_row"]))
    rows = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(ledger)]
    commits = [i for i, row in enumerate(rows) if _is_drill(row, "commit")]
    if not commits:
        raise NoCommitment("no revert-drill commitment in the ledger")
    payload = rows[commits[-1]]["payload"]
    instance = payload.get("instance_id")
    if not _text(instance):
        raise Unusable("the commitment row's instance_id must be a non-empty string")
    committed = _hex64(payload.get("commitment_sha256"), "the commitment row's commitment_sha256")
    if any(_is_drill(row, "reveal") and row["payload"].get("instance_id") == instance
           for row in rows[commits[-1] + 1:]):
        raise NoCommitment("the last commitment (%s) is already revealed" % instance)
    return {"instance_id": instance, "commitment_sha256": committed}


# ---------------------------------------------------------------- the run

def run_drill(writer: Any, drill_seed: bytes, fixtures: Any, ledger: bytes, previous: bytes, cycle_id: str,
              observe: Callable[[str], tuple], onto: str, check_name: str) -> dict:
    """One revert drill in cycle ``cycle_id`` (see the module docstring). Returns ``{verdict, reasons, answer,
    commitment_sha256, planted, revert, outcome}``; ``planted`` and ``revert`` are null when nothing was
    planted. ``HardStop``, ``NoCommitment``, ``Refused`` and ``Unusable`` are raised before anything is written."""
    by_id = fixtures_by_id(fixtures)
    _cycle(cycle_id)
    pending = pending_commitment(ledger, previous)
    if pending["instance_id"] == cycle_id:
        raise write.Refused(["drill_committed_in_this_cycle"])
    ans = answer(drill_seed, pending["instance_id"], fixtures)
    committed = pending["commitment_sha256"]
    out = {"answer": ans, "commitment_sha256": committed, "planted": None, "revert": None}
    if commitment(ans) != committed:
        outcome = {"reverted": False, "cause": None}
        return dict(out, outcome=outcome, **judge(committed, ans, outcome, drill_seed, fixtures))
    files = by_id[ans["fixture"]].get("files")
    if not files:
        raise Unusable("fixture %r has no files to plant" % ans["fixture"])
    branch = "brain/drill/%s" % cycle_id
    title = "drill %s: planted merge" % cycle_id
    base = writer.head(onto)
    writer.create_branch(branch, base)
    head = writer.commit_files(branch, base, {p: t.encode("utf-8") for p, t in files.items()}, title)
    pull = writer.open_pull(branch, onto, title, "planted by exit.drill (revert)")
    writer.check(head, check_name, "success",
                 "planted by exit.drill (revert) in cycle %s; not a gate decision" % cycle_id)
    merge = writer.merge(pull, head)
    runs, facts = observe(merge)
    done = revert.revert_red(writer, runs, facts, merge, onto, branch + "-revert")
    outcome = {"reverted": done["reverted"], "cause": done["cause"]}
    return dict(out, planted={"merge": merge, "pull": pull}, revert=done, outcome=outcome,
                **judge(committed, ans, outcome, drill_seed, fixtures))


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m harness.revert_drill commit|reveal|judge < JSON"
INPUTS = {"commit": {"drill_seed", "cycle_id", "fixtures"}, "reveal": {"drill_seed", "cycle_id", "fixtures"},
          "judge": {"drill_seed", "fixtures", "commitment_sha256", "answer", "outcome"}}
EMPTY = {"commit": {"commitment_sha256": None}, "reveal": {"answer": None, "commitment_sha256": None},
         "judge": {"verdict": None, "reasons": []}}


def _seed_hex(value: Any) -> bytes:
    if not isinstance(value, str) or len(value) % 2 or not set(value) <= HEX:
        raise Unusable("drill_seed must be lowercase hex")
    return bytes.fromhex(value)


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def main(argv: list[str]) -> int:
    command = argv[0] if len(argv) == 1 and argv[0] in INPUTS else None
    try:
        if command is None:
            raise Unusable(USAGE)
        request = chain.parse_row(sys.stdin.buffer.read().decode("utf-8"))
        if set(request) != INPUTS[command]:
            raise Unusable("stdin must be {%s} and nothing else" % ", ".join(sorted(INPUTS[command])))
        seed = _seed_hex(request["drill_seed"])
        if command == "judge":
            result = judge(request["commitment_sha256"], request["answer"], request["outcome"], seed,
                           request["fixtures"])
            _emit(result)
            return 0 if result["verdict"] == "PASS" else 1
        ans = answer(seed, request["cycle_id"], request["fixtures"])
        _emit({"commitment_sha256": commitment(ans)} if command == "commit"
              else {"answer": ans, "commitment_sha256": commitment(ans)})
        return 0
    except (Unusable, UnicodeDecodeError, chain.ChainError) as exc:
        sys.stderr.write("unusable input: %s\n" % exc)
    except Exception as exc:  # noqa: BLE001 - never a traceback, never an exit without a reason
        sys.stderr.write("internal error: %s: %s\n" % (type(exc).__name__, exc))
    _emit(EMPTY.get(command, {"verdict": None, "reasons": []}))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
