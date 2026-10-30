"""``activate``: the operator's first cycle on a target: the genesis row, the ``brain/integration`` cut, the ratchet
base and the ready candidates, written as one orphan ``brain/state`` commit (stage 0, MF18).

Rules: asama-0/14 row 18, asama-0/09 tests 45 and 14, asama-0/10a #genesis (what genesis records) and #taban (the
ratchet base is the referee's own tool run at genesis; the Founder cannot give it), asama-0/08 (the acceptance
rule; cycle order rows 1 and 6), tohum/25a row 7 (``brain/state`` opened with the genesis row, ``brain/integration``
cut from ``main``, the copy from ``targets[].base_sha``), tohum/26a (``activate``: target, ``targets[]``, ready
candidates -> genesis row, cut, ratchet base; writes ``brain/state``), tohum/01a and tohum/24 (``brain/state`` is an
orphan branch), tohum/26 and 26c (row, ``setup/*``, candidate shapes), tohum/29d (group ``genesis``). Calls: 2, 7
and 8 (the decision), 9 (every write), 10, 11 and 16 (the state commit), through their modules.

**Inputs.** ``files``: the bytes of ``summary.json`` (``setup/summary.json``), ``imports.jsonl``
(``setup/imports.jsonl``), ``policy.json``, ``result.json`` (the bootstrap referee's signed result the import
verified), ``security-ledger.jsonl`` (``seed/security-ledger.jsonl``), ``profile.json`` and ``recipe.json`` (the
referee's derived profile and verified unit recipe, MF4 and MF6) and ``base.jsonl`` (the referee's lint tool run
three times on the base tree in ``koş``, MF3; one run record per line as ``gate.check`` reads it). ``request``
``{target_id, base_run_sha256, settings: {rulesets, apps, actions}, rekor_uuids, cycle_id, ts, snapshot_id,
candidates}``, exactly these keys: ``base_run_sha256`` is the hash of ``base.jsonl`` taken outside the container;
``settings`` are the target's rulesets, installed apps and Actions permissions as the API returned them
(asama-0/10a #hedefler; reading them is the job's); ``rekor_uuids`` the (A) result's Rekor entries; ``candidates``
the ids of the ready candidates (``candidates/<target>/<cid>/``).

**The genesis row** (``genesis``, pure), ``part: events, kind: genesis``, row id ``<cycle_id>:genesis``. Its
payload (``ledger.schema.GENESIS``, every key required):

- ``target`` ``{id, repo, kind, base_sha}``: the ``summary.json`` ``targets[]`` entry with ``id == target_id``;
  ``main_sha``: ``main``'s head as read; ``integration`` ``{branch: brain/integration, sha: base_sha}``.
- ``seed_epoch``: the last ``seed_epochs[]`` entry, as written.
- ``import``: of the last ``imports.jsonl`` row: ``line_sha256`` (sha256 of that line's bytes, newline excluded),
  ``row_hash``, ``brain_sha``, ``referee_tree_sha256``, ``result_sha256``, ``toy_tree_sha256`` (null if absent).
- ``result`` ``{sha256, rekor_uuids}``; ``policy_sha256``, ``summary_sha256``, ``profile_sha256``,
  ``recipe_sha256``: sha256 of each file's bytes as given.
- ``seed_security`` ``{ledger_sha256, last_row_hash}``: the security ledger's bytes and its last ``row_hash``.
- ``settings_sha256`` ``{rulesets, apps, actions}``: sha256 of the RFC 8785 form of each API value.
- ``ratchet`` ``{base_run_sha256, counts}``: ``counts`` is violations per tool in the first run record of
  ``base.jsonl`` (``gate.check``'s count, the one the gate's ratchet compares, asama-0/08 criterion 5).
- ``candidates``: the ready candidate ids, sorted, unique.

Files read as bytes are hashed as bytes; values read from the API are hashed in canonical form. Refusals
(``Refused``, every reason that holds, nothing written): ``target_unknown``; ``toy_base_not_main`` (a ``toy``
target's ``base_sha`` is not ``main``'s head: the toy is cut from ``main``, tohum/25a row 7; a ``copy`` is cut at
its ``base_sha`` whatever ``main`` is now, since the copy's ``main`` keeps mirroring); ``imports_invalid``
(``imports.jsonl`` is not a valid chain or is empty); ``result_not_imported`` (sha256 of ``result.json`` is not
the last import row's ``result_sha256``); ``security_ledger_invalid`` (not a valid chain or empty);
``base_run_hash_mismatch``; ``tool_nondeterministic`` (the three lines of ``base.jsonl`` differ: a ratchet base
must be one count). Unusable input (``Unusable``): a file that is not the JSON it names, a request not of the
shape above, or a payload ``ledger.schema`` refuses (a fact of the wrong form, e.g. a ``brain_sha`` that is not
40 hex). Not checked here: that ``referee_tree_sha256`` is the tree the referee runs (the import checks it),
that ``toy_tree_sha256`` is the toy target's tree (no tree hash is computed without git), the meaning of
``settings`` (P1's ``drift.check``).

**Activation** (``activate``), in this order; nothing is written before step 3:

1. ``genesis`` on the inputs, with ``main`` read through ``target.write``.
2. Reads: ``brain/state`` must not exist (``already_activated``), ``brain/integration`` must not exist
   (``integration_exists``), the ``base_sha`` commit must read. Any reason: ``Refused``.
3. Cut: ``brain/integration`` created at ``base_sha`` (``POST git/refs``). If GitHub refuses the creation
   (``ApiError``), nothing else is written.
4. Each ready candidate, in id order, is decided by the acceptance rule (asama-0/08): ``gate.diffguard.check``
   (criterion 1, with the profile's ``security_paths``/``excluded_dirs`` and the recipe's ``inputs``), then
   ``gate.check.decide`` (criteria 2-8 on the candidate's ``koş`` results against ``base.jsonl``, with
   ``unfinished_sentinels`` the merges this activation already made, so at most one candidate merges: criterion 8),
   then the diff is applied to the base file (``gate.diffguard.apply``, read through ``read_base`` from the tree
   pulled at ``base_sha``; a missing file is ``base_file_missing``, a diff that does not apply there
   ``patch_does_not_apply``). A candidate whose files are unusable is rejected (``candidate_unusable``); one whose
   id is not a valid branch name under ``brain/c/`` is ``candidate_id_invalid``. A merge: branch ``brain/c/<cid>``
   at the cut, one commit with the applied file, a pull request into ``brain/integration``, a ``success`` check
   named ``check_name`` on its head, the merge (``target.write``). A reject writes nothing on the target.
   Rows: ``events`` ``merge`` ``{candidate, path, pull, head_sha, merge_sha}`` or ``reject`` ``{candidate,
   reasons}`` with ``cause`` the first of ``REJECT_CAUSES`` that matches a reason, else ``unknown``.
5. The state: rows genesis, ``integration_cut`` ``{branch, main_sha, base_sha}``, the decisions, then
   ``status.block.plan``'s rows (MF16); every row's payload is checked by ``ledger.schema`` before it is chained,
   the chained ledger again after; ``ledger.append.plan_cycle`` chains them (secret scan, MF2); the root is signed
   (``ledger.anchor``, MF11) and its row written; ``ledger.jsonl``, ``chain/root.jsonl`` and ``status.md`` go in
   one orphan commit (``Writer.open_orphan``) that opens ``brain/state``.

A failure after step 3 (an API error, an unsignable root, a row the schema refuses) raises ``HardStop`` carrying
the refs already written: the target holds a cut, and maybe a merge, without the state that records them, which
tohum/25a's failure rule leaves to the operator; activation is not retried over it (step 2 refuses).

Out of scope, stated: running the tools and tests (``koş``, MF3/MF6: their outputs are inputs here), fetching the
settings and Rekor entries, writing ``profile.json`` into ``brain/state``, the observation rows of cycle 1 (tool
output and ``fix`` ranges, asama-0/08), ``expect.json`` (the referee does not trust it; (B)'s #ret compares it),
hunk coverage records, and the wiring of this function into ``loop.yml``'s ``yaz`` job (spec-036). Whether
GitHub lets the writer App create ``brain/integration`` under tohum/25a row 3's ``pull_request`` rule is not
known here (seed-037); the fake GitHub is tested both ways.

Command line (group ``genesis``), run from ``referee/``, one JSON line on stdout, the cause on stderr::

    python -m activate genesis DIR     stdin {target_id, main_sha, base_run_sha256, settings, rekor_uuids,
                                              cycle_id, ts, snapshot_id, candidates}
        DIR holds the eight files named above.
        -> {ok, reasons, row, row_hash}; row_hash as the first row of a new ledger (prev_hash 64 zeros)
        exit 0 the row; 1 refused (reasons); 2 unusable (row null, reasons [])
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any, Callable

from gate import check, diffguard
from ledger import anchor, append, chain, schema
from status import block
from target import write

STATE = "brain/state"
INTEGRATION = schema.INTEGRATION
MAIN = "main"
CANDIDATE_PREFIX = "brain/c/"
FILES = ("summary.json", "imports.jsonl", "policy.json", "result.json", "security-ledger.jsonl", "profile.json",
         "recipe.json", "base.jsonl")
REQUEST = {"target_id", "base_run_sha256", "settings", "rekor_uuids", "cycle_id", "ts", "snapshot_id", "candidates"}
SETTINGS = ("rulesets", "apps", "actions")
CANDIDATE_FILES = ("finding.json", "diff.patch", "cand.jsonl", "checks.json", "hashes.json")
# A reject's cause: the first entry whose test holds for some reason (tohum/26 closed set).
REJECT_CAUSES = (
    ("scope_violation", lambda r: r == "scope_violation" or ":" in r),  # criterion 1's path reasons and 4
    ("test_regression", lambda r: r in ("tests_red", "zero_tests")),
    ("lint_regression", lambda r: r == "ratchet_increase"),
)

HardStopBase = append.HardStop
Refused = write.Refused


class Unusable(ValueError):
    pass


class HardStop(HardStopBase):
    """Activation failed after its first write; ``written`` names the refs already written."""

    def __init__(self, message: str, written: list[str]):
        super().__init__("%s (written: %s)" % (message, ", ".join(written) or "nothing"))
        self.written = written


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes, name: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Unusable("%s is not JSON: %s" % (name, exc)) from exc


def _chain_rows(data: bytes) -> list[dict] | None:
    """The rows of a valid, non-empty chain, else None."""
    if not chain.verify_bytes(data)["valid"]:
        return None
    rows = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(data)]
    return rows or None


def _request(req: Any) -> dict:
    if not isinstance(req, dict) or set(req) != REQUEST:
        raise Unusable("the request must have exactly the keys %s" % ", ".join(sorted(REQUEST)))
    if not isinstance(req["settings"], dict) or set(req["settings"]) != set(SETTINGS):
        raise Unusable("settings must have exactly the keys %s" % ", ".join(SETTINGS))
    for key in ("target_id", "cycle_id", "snapshot_id"):
        if schema.text(req[key], key):
            raise Unusable("%s must be a non-empty string" % key)
    if schema.timestamp(req["ts"], "ts") or schema.hex64(req["base_run_sha256"], "base_run_sha256"):
        raise Unusable("ts must be YYYY-MM-DDTHH:MM:SSZ and base_run_sha256 64 lowercase hex")
    for key in ("rekor_uuids", "candidates"):
        if schema.list_of(schema.text)(req[key], key):
            raise Unusable("%s must be a list of non-empty strings" % key)
    return req


def _canonical_sha(value: Any, name: str) -> str:
    try:
        return _sha(chain.canonical(value))
    except (chain.ChainError, ValueError, TypeError) as exc:
        raise Unusable("%s has no canonical form: %s" % (name, exc)) from exc


def _row(cycle: dict, suffix: str, kind: str, payload: dict, cause: str | None = None) -> dict:
    row = {"row_id": "%s:%s" % (cycle["cycle_id"], suffix), "ts": cycle["ts"], "part": "events", "kind": kind,
           "payload": payload, "derivation": "tool", "trust": "verified", "snapshot_id": cycle["snapshot_id"],
           "evidence_refs": []}
    if cause is not None:
        row["cause"] = cause
    reasons = schema.payload_reasons("events", kind, payload)
    if reasons:
        raise Unusable("%s row: %s" % (kind, "; ".join(reasons)))
    return row


# ---------------------------------------------------------------- genesis

def genesis(files: dict[str, bytes], req: Any, main_sha: str) -> dict:
    """``{reasons, row, target}``: the refusal reasons (row None when any) or the genesis row; see the docstring."""
    req = _request(req)
    missing = [name for name in FILES if not isinstance(files.get(name), bytes)]
    if missing:
        raise Unusable("missing file(s): %s" % ", ".join(missing))
    summary = _json(files["summary.json"], "summary.json")
    for name in ("policy.json", "result.json", "profile.json", "recipe.json"):
        _json(files[name], name)
    if not isinstance(summary, dict) or not isinstance(summary.get("targets"), list) \
            or not isinstance(summary.get("seed_epochs"), list) or not summary["seed_epochs"]:
        raise Unusable("summary.json must carry targets[] and a non-empty seed_epochs[]")
    reasons = []
    targets = [t for t in summary["targets"] if isinstance(t, dict) and t.get("id") == req["target_id"]]
    target = None
    if len(targets) != 1:
        reasons.append("target_unknown")
    else:
        target = {k: targets[0].get(k) for k in ("id", "repo", "kind", "base_sha")}
        if target["kind"] == "toy" and target["base_sha"] != main_sha:
            reasons.append("toy_base_not_main")
    imports = _chain_rows(files["imports.jsonl"])
    if imports is None:
        reasons.append("imports_invalid")
    elif imports[-1].get("result_sha256") != _sha(files["result.json"]):
        reasons.append("result_not_imported")
    security = _chain_rows(files["security-ledger.jsonl"])
    if security is None:
        reasons.append("security_ledger_invalid")
    base_run = files["base.jsonl"]
    counts: dict[str, int] = {}
    if _sha(base_run) != req["base_run_sha256"]:
        reasons.append("base_run_hash_mismatch")
    else:
        try:
            run, same = check.run_file(base_run, "base.jsonl")
        except check.Unusable as exc:
            raise Unusable(str(exc)) from exc
        if not same:
            reasons.append("tool_nondeterministic")
        counts = {run["tool"]: len(run["violations"])}
    if reasons:
        return {"reasons": sorted(reasons), "row": None, "target": target}
    last = imports[-1]
    payload = {
        "target": target,
        "main_sha": main_sha,
        "integration": {"branch": INTEGRATION, "sha": target["base_sha"]},
        "seed_epoch": summary["seed_epochs"][-1],
        "import": {"line_sha256": _sha(chain._lines(files["imports.jsonl"])[-1]), "row_hash": last.get("row_hash"),
                   "brain_sha": last.get("brain_sha"), "referee_tree_sha256": last.get("referee_tree_sha256"),
                   "result_sha256": last.get("result_sha256"), "toy_tree_sha256": last.get("toy_tree_sha256")},
        "result": {"sha256": _sha(files["result.json"]), "rekor_uuids": req["rekor_uuids"]},
        "policy_sha256": _sha(files["policy.json"]),
        "summary_sha256": _sha(files["summary.json"]),
        "profile_sha256": _sha(files["profile.json"]),
        "recipe_sha256": _sha(files["recipe.json"]),
        "seed_security": {"ledger_sha256": _sha(files["security-ledger.jsonl"]),
                          "last_row_hash": security[-1].get("row_hash")},
        "settings_sha256": {k: _canonical_sha(req["settings"][k], "settings." + k) for k in SETTINGS},
        "ratchet": {"base_run_sha256": req["base_run_sha256"], "counts": counts},
        "candidates": sorted(set(req["candidates"])),
    }
    return {"reasons": [], "row": _row(req, "genesis", "genesis", payload), "target": target}


# ---------------------------------------------------------------- the ready candidates

def _cause(reasons: list[str]) -> str:
    for cause, test in REJECT_CAUSES:
        if any(test(r) for r in reasons):
            return cause
    return "unknown"


def decide(cand: dict, base_run: bytes, profile: Any, recipe: Any, control: Any, pending: list[str],
           read_base: Callable[[str], bytes | None]) -> dict:
    """The acceptance rule on one candidate: ``{reasons, path, content}``; ``content`` is the applied file when
    there is no reason. ``cand`` maps ``CANDIDATE_FILES`` to bytes (a missing run file is None)."""
    if write.branch_reasons(CANDIDATE_PREFIX + cand["id"]) or "/" in cand["id"]:
        return {"reasons": ["candidate_id_invalid"], "path": None, "content": None}
    try:
        text = cand["diff.patch"].decode("utf-8", "surrogateescape")
        reasons = diffguard.check(text, profile, recipe)
        found = check.finding(_json(cand["finding.json"], "finding.json"))
        files = {"base.jsonl": base_run, "cand.jsonl": cand.get("cand.jsonl"), "checks.json": cand.get("checks.json")}
        hashes = check.hashes_file(_json(cand["hashes.json"], "hashes.json"))
        decided = check.decide(found, text, files, hashes, check.request(
            {"control": control, "unfinished_sentinels": list(pending)}))
    except (Unusable, check.Unusable, diffguard.DiffError, KeyError, AttributeError):
        return {"reasons": ["candidate_unusable"], "path": None, "content": None}
    reasons = sorted(set(reasons + decided["reasons"]))
    if reasons:
        return {"reasons": reasons, "path": found["path"], "content": None}
    old = read_base(found["path"])
    if old is None:
        return {"reasons": ["base_file_missing"], "path": found["path"], "content": None}
    try:
        content = diffguard.apply(diffguard.parse(text)[0], old)
    except diffguard.DiffError:
        return {"reasons": ["patch_does_not_apply"], "path": found["path"], "content": None}
    return {"reasons": [], "path": found["path"], "content": content}


def land(writer: write.Writer, cid: str, path: str, content: bytes, cut: str, check_name: str) -> dict:
    """Branch, commit, pull request, check and merge of one accepted candidate onto ``brain/integration``."""
    branch = CANDIDATE_PREFIX + cid
    title = "candidate %s" % cid
    writer.create_branch(branch, cut)
    head = writer.commit_files(branch, cut, {path: content}, title)
    pull = writer.open_pull(branch, INTEGRATION, title, "accepted by the gate (asama-0/08)")
    if pull is None:
        raise write.ApiError(None, "pull request created without a number")
    writer.check(head, check_name, "success", "gate: merge")
    merge = writer.merge(pull, head)
    return {"pull": pull, "head_sha": head, "merge_sha": merge}


# ---------------------------------------------------------------- the state commit

def state_files(rows: list[dict], imports: bytes, facts: dict, signer: Any, root_row_id: str) -> dict:
    """The files of the orphan ``brain/state``: ``status.block`` rows added, chained, schema-checked, root signed."""
    planned = block.plan(b"", b"", rows, None, imports, facts)
    for row in planned["rows"]:
        reasons = schema.payload_reasons(row.get("part"), row.get("kind"), row.get("payload"))
        if reasons:
            raise Unusable("row %s: %s" % (row.get("row_id"), "; ".join(reasons)))
    request = json.dumps({"rows": planned["rows"]}, sort_keys=True).encode("utf-8")
    cycle = append.plan_cycle(b"", b"", lambda: request)
    reasons = schema.ledger_reasons(cycle.content)
    if reasons:
        raise Unusable("ledger: %s" % "; ".join(reasons))
    root = anchor.root_of(anchor.tips(cycle.content))
    entry = anchor.anchor(root, signer)
    roots = anchor.root_row(b"", root_row_id, facts["ts"], root, entry["uuid"])
    return {"files": {anchor.LEDGER_PATH: cycle.content, anchor.ROOTS_PATH: roots, block.STATUS_PATH: planned["status"]},
            "row_hashes": cycle.row_hashes, "root": root, "entry": entry}


# ---------------------------------------------------------------- activation

def activate(writer: write.Writer, files: dict[str, bytes], req: Any, candidates: list[dict],
             read_base: Callable[[str], bytes | None], signer: Any, control: Any, check_name: str,
             budgets: dict[str, int]) -> dict:
    """The activation; see the module docstring. ``candidates``: ``{id, <CANDIDATE_FILES>: bytes|None}`` each."""
    ids = [c.get("id") if isinstance(c, dict) else None for c in candidates]
    wanted = _request(req)["candidates"]
    if not all(isinstance(i, str) for i in ids) or sorted(ids) != sorted(set(wanted)) or len(wanted) != len(ids):
        raise Unusable("the candidates given are not the request's candidates, each once")
    main_sha = writer.head(MAIN)
    gen = genesis(files, req, main_sha)
    if gen["reasons"]:
        raise Refused(gen["reasons"])
    target = gen["target"]
    if writer.repo != target["repo"]:
        raise Refused(["target_repo_mismatch"])
    reasons = []
    if writer.exists(STATE):
        reasons.append("already_activated")
    if writer.exists(INTEGRATION):
        reasons.append("integration_exists")
    if reasons:
        raise Refused(reasons)
    cut = target["base_sha"]
    writer.read_commit(cut)
    profile, recipe = _json(files["profile.json"], "profile.json"), _json(files["recipe.json"], "recipe.json")
    try:  # the shapes criterion 1 reads, checked before the first write
        diffguard.check("diff --git a/x b/x\n", profile, recipe)
    except diffguard.DiffError as exc:
        raise Unusable(str(exc)) from exc
    writer.create_branch(INTEGRATION, cut)
    try:
        rows = [gen["row"], _row(req, "cut", "integration_cut",
                                 {"branch": INTEGRATION, "main_sha": main_sha, "base_sha": cut})]
        merges, decisions = [], []
        for cand in sorted(candidates, key=lambda c: c["id"]):
            got = decide(cand, files["base.jsonl"], profile, recipe, control, merges, read_base)
            if got["reasons"]:
                rows.append(_row(req, "c:" + cand["id"], "reject", {"candidate": cand["id"], "reasons": got["reasons"]},
                                 _cause(got["reasons"])))
                decisions.append({"candidate": cand["id"], "decision": "reject", "reasons": got["reasons"]})
                continue
            done = land(writer, cand["id"], got["path"], got["content"], cut, check_name)
            merges.append(done["merge_sha"])
            rows.append(_row(req, "c:" + cand["id"], "merge", dict(done, candidate=cand["id"], path=got["path"])))
            decisions.append(dict(done, candidate=cand["id"], decision="merge", reasons=[]))
        facts = {"cycle_id": req["cycle_id"], "ts": req["ts"], "snapshot_id": req["snapshot_id"],
                 "row_id": "%s:status" % req["cycle_id"], "budgets": budgets, "main_commits_since_cut": 0}
        state = state_files(rows, files["imports.jsonl"], facts, signer, "%s:root" % req["cycle_id"])
        sha = writer.open_orphan(STATE, state["files"], "genesis: cycle %s" % req["cycle_id"])
    except (write.ApiError, write.Refused, Unusable, HardStopBase, block.Unusable, anchor.Unusable) as exc:
        raise HardStop("%s: %s" % (type(exc).__name__, exc), sorted(set(writer.written))) from exc
    return {"state_sha": sha, "integration_sha": cut, "main_sha": main_sha, "row_hashes": state["row_hashes"],
            "root": state["root"], "entry": state["entry"], "decisions": decisions, "files": state["files"]}


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m activate genesis DIR < request"


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2 or argv[0] != "genesis":
            raise Unusable(USAGE)
        req = json.loads(sys.stdin.read())
        if not isinstance(req, dict) or "main_sha" not in req:
            raise Unusable("the request must be an object with main_sha")
        main_sha = req.pop("main_sha")
        if schema.hex40(main_sha, "main_sha"):
            raise Unusable("main_sha must be 40 lowercase hex")
        files = {}
        for name in FILES:
            with open(os.path.join(argv[1], name), "rb") as fh:
                files[name] = fh.read()
        gen = genesis(files, req, main_sha)
        if gen["reasons"]:
            _emit({"ok": False, "reasons": gen["reasons"], "row": None, "row_hash": None})
            return 1
        row = dict(gen["row"], prev_hash=chain.ZERO_HASH)
        _emit({"ok": True, "reasons": [], "row": gen["row"], "row_hash": chain.row_hash(row)})
        return 0
    except (Unusable, ValueError, OSError, RecursionError) as exc:
        cause = "unusable input: %s" % exc
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a reason
        cause = "internal error: %s: %s" % (type(exc).__name__, exc)
    _emit({"ok": False, "reasons": [], "row": None, "row_hash": None})
    sys.stderr.write(cause + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
