"""The shapes of the artifacts the stage 0 loop writes on ``brain/state``: ledger rows, root rows, the
``status.md`` block (stage 0, test 14 of asama-0/09, written with MF18).

Rules: tohum/26 (the ledger row; ``derivation``, ``trust``, ``cause`` and ``miss_reason`` closed sets; no float
in a hashed artifact; ``drill`` payload; part -> file), tohum/27a (``chain/root.jsonl`` rows), asama-0/14 row 16
(the block), and the payloads this repository's writers produce, one table (``ROW_TYPES``) for all of them.

**A ledger row** (``row_reasons``) has exactly the keys of tohum/26: ``row_id``, ``ts``, ``part``, ``kind``,
``payload``, ``derivation``, ``trust``, ``snapshot_id``, ``evidence_refs``, ``prev_hash``, ``row_hash``, and
optionally ``cause``, ``miss_reason``, ``derived_from``, ``proposed_by``. ``row_id``, ``kind``, ``snapshot_id``,
``derived_from`` and ``proposed_by`` are non-empty strings; ``ts`` is ``YYYY-MM-DDTHH:MM:SSZ``; ``part`` one of
``PARTS`` (tohum/26's table); ``derivation``, ``trust``, ``cause``, ``miss_reason`` in their closed sets;
``evidence_refs`` a list of ``{path, line_start, line_end}`` with ``1 <= line_start <= line_end``;
``prev_hash`` and ``row_hash`` 64 lowercase hex. No value anywhere in the row is a float.

**Row types.** ``(part, kind)`` must be one of ``ROW_TYPES``; anything else is ``unknown_row_type``: the loop
writes no row whose shape is not written here. Each type gives its payload's keys (required and optional, no
other key), each key's shape, and whether ``cause`` is required (a failed or reverted event, tohum/26). The
``drill`` payloads are tohum/26's fields; ``revert_drill``'s reveal also carries ``answer`` and ``reasons``
(MF14), which tohum/26 does not list (reported, seed-037). The ``cost`` payload is ``llm.call``'s (MF15). The
``events`` payloads are ``status.block``'s (MF16) and ``activate``'s (MF18). Kinds no writer here produces yet
(an ``events`` ``revert`` row, ``rival``, ``accept``, ``freeze``, ``security``, ``looks``, ``founder``) are not in
the table, so they are refused until a writer and its shape are added.

**A root row** (``root_reasons``): exactly ``{row_id, ts, root, rekor_uuid, prev_hash, row_hash}``
(``ledger.anchor.root_row``), ``root`` 64 lowercase hex, ``rekor_uuid`` a non-empty string.

**Files.** ``ledger_reasons`` and ``roots_reasons`` first verify the file as a chain (``ledger.chain``, the one
verifier), then each row. ``status_reasons`` reads ``status.md`` and the ledger: the file starts with the block's
``BEGIN`` line, holds its ``END`` line, and the sha256 of the region ``status.block`` owns equals
``block_sha256`` of the ledger's last ``status`` row.

Each reason is a string ``<where>: <what>``; an empty list means the artifact conforms. Not checked here: the
meaning of a value (that a hash is the hash of what it names; ``activate`` and the tests check those), and the
JSON Schema files tohum/26 places in the referee repository's ``schemas/`` (not in this repository).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Callable

from dispatcher import llm_call
from ledger import chain

ROW_KEYS = ("row_id", "ts", "part", "kind", "payload", "derivation", "trust", "snapshot_id", "evidence_refs",
            "prev_hash", "row_hash")
ROW_OPTIONAL = ("cause", "miss_reason", "derived_from", "proposed_by")
PARTS = ("founder", "events", "cost", "drill", "freeze", "rival", "accept", "security", "looks")
DERIVATIONS = ("tool", "static_analysis", "test_verified", "llm_inference", "name_similarity", "imported")
TRUSTS = ("verified", "observed", "inferred")
CAUSES = ("test_regression", "contract_counterpart", "build_break", "lint_regression", "flaky_dependency",
          "conflict_with_main", "scope_violation", "imported_assumption", "impact_miss", "unknown")
MISS_REASONS = ("map_edge_missing", "unseen_file", "wrong_property", "ref_mismatch", "not_reported", "unknown")
DRILLS = ("lesson", "revert", "context", "genesis", "security")
ROOT_KEYS = ("row_id", "ts", "root", "rekor_uuid", "prev_hash", "row_hash")
INTEGRATION = "brain/integration"

TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")

Check = Callable[[Any, str], "list[str]"]


# ---------------------------------------------------------------- value shapes

def _bad(where: str, what: str) -> list[str]:
    return ["%s: %s" % (where, what)]


def text(value: Any, where: str) -> list[str]:
    return [] if isinstance(value, str) and value else _bad(where, "not a non-empty string")


def hex64(value: Any, where: str) -> list[str]:
    return [] if isinstance(value, str) and HEX64.match(value) else _bad(where, "not 64 lowercase hex")


def hex40(value: Any, where: str) -> list[str]:
    return [] if isinstance(value, str) and HEX40.match(value) else _bad(where, "not 40 lowercase hex")


def timestamp(value: Any, where: str) -> list[str]:
    return [] if isinstance(value, str) and TS.match(value) else _bad(where, "not YYYY-MM-DDTHH:MM:SSZ")


def count(value: Any, where: str) -> list[str]:
    return [] if type(value) is int and value >= 0 else _bad(where, "not an integer >= 0")


def positive(value: Any, where: str) -> list[str]:
    return [] if type(value) is int and value >= 1 else _bad(where, "not an integer >= 1")


def one_of(*allowed: Any) -> Check:
    def check(value: Any, where: str) -> list[str]:
        return [] if isinstance(value, str) and value in allowed else _bad(where, "not one of %s" % "|".join(allowed))
    return check


def nullable(inner: Check) -> Check:
    def check(value: Any, where: str) -> list[str]:
        return [] if value is None else inner(value, where)
    return check


def list_of(inner: Check, non_empty: bool = False, unique_sorted: bool = False) -> Check:
    def check(value: Any, where: str) -> list[str]:
        if not isinstance(value, list):
            return _bad(where, "not a list")
        if non_empty and not value:
            return _bad(where, "empty")
        out = [r for i, v in enumerate(value) for r in inner(v, "%s[%d]" % (where, i))]
        if unique_sorted and not out and value != sorted(set(value)):
            out += _bad(where, "not sorted and unique")
        return out
    return check


def map_of(inner: Check) -> Check:
    def check(value: Any, where: str) -> list[str]:
        if not isinstance(value, dict):
            return _bad(where, "not an object")
        return [r for k, v in value.items() for r in text(k, where + " key") + inner(v, "%s.%s" % (where, k))]
    return check


def any_object(value: Any, where: str) -> list[str]:
    return [] if isinstance(value, dict) else _bad(where, "not an object")


def shape(required: dict[str, Check], optional: dict[str, Check] | None = None) -> Check:
    """An object with exactly the ``required`` keys and any of the ``optional`` ones, each of its shape."""
    optional = optional or {}

    def check(value: Any, where: str) -> list[str]:
        if not isinstance(value, dict):
            return _bad(where, "not an object")
        out = []
        for key in sorted(set(required) - set(value)):
            out += _bad("%s.%s" % (where, key), "missing")
        for key in sorted(set(value) - set(required) - set(optional)):
            out += _bad("%s.%s" % (where, key), "not a field of this shape")
        for key, inner in list(required.items()) + list(optional.items()):
            if key in value:
                out += inner(value[key], "%s.%s" % (where, key))
        return out
    return check


def no_float(value: Any, where: str) -> list[str]:
    """tohum/26: no float in a hashed artifact (integers, or fixed decimal strings)."""
    if isinstance(value, float):
        return _bad(where, "a float")
    if isinstance(value, dict):
        return [r for k, v in value.items() for r in no_float(v, "%s.%s" % (where, k))]
    if isinstance(value, list):
        return [r for i, v in enumerate(value) for r in no_float(v, "%s[%d]" % (where, i))]
    return []


# ---------------------------------------------------------------- row types

_EVIDENCE = shape({"path": text, "line_start": positive, "line_end": positive})


def evidence(value: Any, where: str) -> list[str]:
    out = _EVIDENCE(value, where)
    if not out and value["line_start"] > value["line_end"]:
        out = _bad(where, "line_start after line_end")
    return out


GENESIS = shape({
    "target": shape({"id": text, "repo": text, "kind": one_of("toy", "copy"), "base_sha": hex40}),
    "main_sha": hex40,
    "integration": shape({"branch": one_of(INTEGRATION), "sha": hex40}),
    "seed_epoch": shape({"commit": hex40, "spec_tohum_sha256": hex64, "seed_sha256": hex64,
                         "bootstrap_sha256": hex64}),
    "import": shape({"line_sha256": hex64, "row_hash": hex64, "brain_sha": hex40, "referee_tree_sha256": hex64,
                     "result_sha256": hex64, "toy_tree_sha256": nullable(hex64)}),
    "result": shape({"sha256": hex64, "rekor_uuids": list_of(text, non_empty=True)}),
    "policy_sha256": hex64,
    "summary_sha256": hex64,
    "profile_sha256": hex64,
    "recipe_sha256": hex64,
    "seed_security": shape({"ledger_sha256": hex64, "last_row_hash": hex64}),
    "settings_sha256": shape({"rulesets": hex64, "apps": hex64, "actions": hex64}),
    "ratchet": shape({"base_run_sha256": hex64, "counts": map_of(count)}),
    "candidates": list_of(text, unique_sorted=True),
})

DRILL_COMMON = {"drill": one_of(*DRILLS), "question": text, "family": text, "instance_id": text,
                "commitment_sha256": hex64, "outcome": text, "verdict": text}

# (part, kind) -> (payload shape, cause required)
ROW_TYPES: dict[tuple[str, str], tuple[Check, bool]] = {
    ("events", "genesis"): (GENESIS, False),
    ("events", "integration_cut"): (shape({"branch": one_of(INTEGRATION), "main_sha": hex40, "base_sha": hex40}),
                                    False),
    ("events", "merge"): (shape({"candidate": text, "path": text, "pull": positive, "head_sha": hex40,
                                 "merge_sha": hex40}), False),
    ("events", "reject"): (shape({"candidate": text, "reasons": list_of(text, non_empty=True, unique_sorted=True)}),
                           True),
    ("events", "status"): (shape({"cycle_id": text, "number": positive, "block_sha256": hex64}), False),
    ("events", "status_edited"): (shape({"cycle_id": text, "found_sha256": nullable(hex64),
                                         "expected_sha256": nullable(hex64)}), False),
    ("cost", "cost"): (shape({"tool": one_of("llm.call"), "template": text, "budget": text, "model_requested": text,
                              "models_served": list_of(text), "outcome": one_of(*llm_call.OUTCOMES),
                              "reason": nullable(text), "cost_usd_micros": count, "cost_source": text,
                              "cap_usd_micros": count, "prompt_sha256": hex64, "system_sha256": hex64,
                              "duration_ms": count}), False),
    ("drill", "commit"): (shape(DRILL_COMMON, {"arm": one_of("with", "without")}), False),
    ("drill", "reveal"): (shape(dict(DRILL_COMMON, revealed_sha256=hex64, answer=any_object,
                                     reasons=list_of(text)), {"arm": one_of("with", "without")}), False),
}

ROW = shape(
    {"row_id": text, "ts": timestamp,
     "part": one_of(*PARTS), "kind": text, "payload": any_object, "derivation": one_of(*DERIVATIONS),
     "trust": one_of(*TRUSTS), "snapshot_id": text, "evidence_refs": list_of(evidence), "prev_hash": hex64,
     "row_hash": hex64},
    {"cause": one_of(*CAUSES), "miss_reason": one_of(*MISS_REASONS), "derived_from": text, "proposed_by": text})

ROOT = shape({"row_id": text, "ts": timestamp, "root": hex64, "rekor_uuid": text, "prev_hash": hex64, "row_hash": hex64})


def row_reasons(row: Any, where: str = "row") -> list[str]:
    """Why ``row`` (a stored ledger row) does not conform; see the module docstring."""
    out = ROW(row, where)
    if not isinstance(row, dict):
        return out
    out += no_float(row, where)
    typ = ROW_TYPES.get((row.get("part"), row.get("kind")))
    if typ is None:
        return out + _bad(where, "unknown_row_type %s/%s" % (row.get("part"), row.get("kind")))
    payload_shape, cause_required = typ
    out += payload_shape(row.get("payload"), where + ".payload")
    if cause_required and "cause" not in row:
        out += _bad(where + ".cause", "missing (a failed or reverted event)")
    return out


def payload_reasons(part: str, kind: str, payload: Any) -> list[str]:
    """The payload check alone, for a writer that checks before it chains its row."""
    typ = ROW_TYPES.get((part, kind))
    if typ is None:
        return _bad("row", "unknown_row_type %s/%s" % (part, kind))
    return typ[0](payload, "payload") + no_float(payload, "payload")


def root_reasons(row: Any, where: str = "root") -> list[str]:
    return ROOT(row, where) + (no_float(row, where) if isinstance(row, dict) else [])


def _rows(data: bytes, where: str) -> tuple[list[dict], list[str]]:
    verdict = chain.verify_bytes(data)
    if not verdict["valid"]:
        return [], _bad(where, "not a valid chain: %s (line %s)" % (verdict["reason"], verdict["line"]))
    return [chain.parse_row(line.decode("utf-8")) for line in chain._lines(data)], []


def ledger_reasons(data: bytes) -> list[str]:
    rows, out = _rows(data, "ledger")
    for i, row in enumerate(rows, 1):
        out += row_reasons(row, "ledger line %d" % i)
    return out


def roots_reasons(data: bytes) -> list[str]:
    rows, out = _rows(data, "roots")
    for i, row in enumerate(rows, 1):
        out += root_reasons(row, "roots line %d" % i)
    return out


def status_reasons(status: bytes, ledger: bytes) -> list[str]:
    from status import block  # the block's markers and its region, one source

    lines = status.split(b"\n")
    out = []
    if lines[0] != block.BEGIN.encode("ascii"):
        out += _bad("status.md", "does not start with the block's BEGIN line")
    if block.END.encode("ascii") not in lines:
        out += _bad("status.md", "has no END line")
    rows, bad = _rows(ledger, "ledger")
    out += bad
    owned, _ = block.region(status)
    expected = [r["payload"].get("block_sha256") for r in rows
                if r.get("part") == block.PART and r.get("kind") == block.KIND and isinstance(r.get("payload"), dict)]
    if not expected:
        out += _bad("status.md", "the ledger has no status row")
    elif hashlib.sha256(owned).hexdigest() != expected[-1]:
        out += _bad("status.md", "block sha256 is not the last status row's block_sha256")
    return out
