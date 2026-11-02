"""``yaz``'s D8: the revert drill in the loop, one step per cycle (stage 0, MF14 in the cycle).

Rules: asama-0/01 D8 (the previous cycle's ``yaz`` commits, this cycle applies; inputs the seed's drill fixtures and
the drill seed, a referee secret; output ``drill`` rows; judge: the reveal equals the commitment, the planted merge
was reverted, ``cause`` equals the key's), tohum/22a ``#geri-alma`` (the planted bad merge is seen red by the
sentinel and reverted by ``gate.revert``), tohum/29m (``harness.revert_drill``: the key, the commitment, the rows and
the judge, used here as they are), tohum/08 item 1 (the seed is a secret, so only a job that runs no code holds it:
``yaz``), tohum/07 (merges are serial: a planted merge is a merge, ``ledger.serial``).

**Stated assumptions** (seed-045: no page names them; its draft): the catalog is the referee checkout's
``seed/drill/revert/catalog.json`` (29m's ``{instances: [{id, cause, ...}]}``), each instance's ``patch`` the name of
a file in that directory holding a unified diff of one file (``target.land.applied``'s, the one application a
candidate's diff gets); the drill seed is the ``DRILL_SEED`` secret of ``yaz``; the commitment's ``cycle_id`` is the
Actions run id of the cycle that writes it (29m: decimal digits), recovered by a later cycle from the
``events``/``cycle_start`` row of the commitment's cycle (its ``<run id>-<attempt>``); the drill is committed in cycle
N's ``yaz``, planted in a later cycle's ``yaz`` (with that cycle's ``ratchet_base``, so the revert has a lint before),
watched by the next cycle's ``kos`` and reverted by its ``yaz`` (D7, like any merge), and the key revealed and judged
by the first ``yaz`` after the planted merge is finished.

**Inputs** (``inputs(workspace, environ)``): ``None`` when ``DRILL_SEED`` is unset or empty (the drill is off for the
run: the operator has not given the secret). Otherwise the catalog must be readable JSON that
``harness.revert_drill.instances`` accepts, and every instance's ``patch`` a plain file name (no ``/``, not ``.`` or
``..``) of a regular file of that directory, UTF-8 text; else ``Unusable`` (exit 2 before any write).

**The step** (``step``), from ``brain/state``'s ledger as D1 verified it, its unfinished merges
(``ledger.serial.unfinished``), whether D5 merges a candidate this cycle, the tree of ``brain/integration``'s head and
this run's id. Let D be the ledger's revert-drill ``commit`` and ``plant`` rows (``harness.revert_drill``'s reading):

1. no inputs: ``{action: off}``;
2. D's last row is a commitment C. Its cycle's run id is read (``commitment_unplaced`` when no ``cycle_start`` with a
   ``<digits>-<digits>`` id precedes it) and its key derived; a key whose commitment is not C's (the seed or the
   catalog changed since) abandons C: this cycle commits again (rule 4, ``replaces: commitment_mismatch``). Else, with
   an unfinished merge or a candidate D5 merges, ``{action: wait, why: merge_unfinished|candidate_merges}`` (one merge
   at a time, the candidate first). Else the key's instance's patch is applied to the tree: a patch that no longer
   applies abandons C (rule 4, ``replaces: patch_does_not_apply``); one that applies is ``{action: plant,
   instance_id, path, content}``, which D6 lands (``target.land.plant``) with the ``ratchet_base`` and ``plant`` rows;
3. D's last row is a plant P whose merge is unfinished: ``{action: wait, why: drill_unfinished}`` (D7 watches it);
4. otherwise (no drill yet, or P finished, or C abandoned): when P exists and C is kept, ``judged`` is P's drill
   revealed: ``{key, verdict, reasons}`` of ``harness.revert_drill.judge`` over the ledger with the key of the
   commitment before P (a red the loop reverted with the key's cause is ``PASS``; a merge ended green, or reverted
   with another cause, is ``FAIL``). Then a new commitment is written for this run's id when every instance's patch
   applies to the tree (``{action: commit, payload}``), else ``{action: none, why: patch_does_not_apply, instances}``
   (the catalog does not fit this target's head: nothing is committed that could not be planted).

The key and the instance are never in the step's answer before the plant (``commit`` carries the hash only); the
plant names its instance (29m's plant row does), and the key is in the answer only once judged.

Out of scope, stated: how often a drill runs (one after another, as the ledger allows: an assumption, seed-045); a
row for the verdict (29m gives commit and plant rows only; the verdict is in ``yaz``'s line); a candidate that keeps
merging every other cycle delays the plant (the candidate goes first).
"""

from __future__ import annotations

import os
import re
from typing import Any

from harness import revert_drill as RD
from ledger import chain
from target import land
import cli

CATALOG_DIR = ("seed", "drill", "revert")
CATALOG = "catalog.json"
SEED_ENV = "DRILL_SEED"
CYCLE_ID = re.compile(r"([0-9]+)-[0-9]+\Z")


class Unusable(ValueError):
    pass


def inputs(workspace: str, environ: dict[str, str]) -> dict | None:
    """``{seed, catalog, patches}`` or ``None`` (see the module docstring)."""
    seed = environ.get(SEED_ENV)
    if not seed:
        return None
    root = os.path.join(workspace, *CATALOG_DIR)
    try:
        with open(os.path.join(root, CATALOG), "rb") as fh:
            catalog = chain.parse_row(fh.read().decode("utf-8"))
        patches = {}
        for item in RD.instances(catalog):
            name = item.get("patch")
            if not isinstance(name, str) or name in ("", ".", "..") or "/" in name or "\\" in name:
                raise Unusable("instance %r: patch must be a file name of the catalog's directory" % item["id"])
            path = os.path.join(root, name)
            if os.path.islink(path) or not os.path.isfile(path):
                raise Unusable("instance %r: %s is not a regular file" % (item["id"], name))
            with open(path, "rb") as fh:
                patches[item["id"]] = fh.read().decode("utf-8")
    except (OSError, UnicodeDecodeError, chain.ChainError, RD.Unusable) as exc:
        raise Unusable("drill: %s" % cli.cause(exc)) from None
    return {"seed": {"seed": seed}, "catalog": catalog, "patches": patches}


def run_id(cycle_id: str) -> str:
    """The Actions run id of the loop's cycle id ``<run id>-<attempt>``."""
    found = CYCLE_ID.match(cycle_id) if isinstance(cycle_id, str) else None
    if found is None:
        raise Unusable("cycle id %r is not <run id>-<attempt>" % (cycle_id,))
    return found.group(1)


def _rows(ledger: bytes) -> list[dict]:
    rows = RD.chain_rows(ledger)
    if rows is None:
        raise Unusable("drill: brain/state's ledger is not a chain")
    return rows


def committed_by(rows: list[dict], at: int) -> str:
    """The run id of the cycle whose rows hold ``rows[at]``: its last ``cycle_start`` before it."""
    starts = [r for r in rows[:at] if r.get("part") == "events" and r.get("kind") == "cycle_start"]
    if not starts:
        raise Unusable("drill: commitment_unplaced")
    return run_id(starts[-1]["payload"].get("cycle_id"))


def step(inp: dict | None, ledger: bytes, unfinished: list[str], merging: bool, tree: str, this_run: str) -> dict:
    """D8's action this cycle (see the module docstring); ``Unusable`` for a run id that is not decimal digits."""
    try:
        return _step(inp, ledger, unfinished, merging, tree, this_run)
    except RD.Unusable as exc:
        raise Unusable("drill: %s" % cli.cause(exc)) from None


def _step(inp: dict | None, ledger: bytes, unfinished: list[str], merging: bool, tree: str, this_run: str) -> dict:
    if inp is None:
        return {"action": "off"}
    rows = _rows(ledger)
    drills = [i for i, r in enumerate(rows) if RD.is_drill(r, "commit") or RD.is_drill(r, "plant")]
    last = rows[drills[-1]] if drills else None
    out: dict[str, Any] = {}
    if last is not None and last["kind"] == "commit":
        answer = RD.key(inp["seed"], committed_by(rows, drills[-1]), inp["catalog"])
        if RD.commit_payload(answer) != last["payload"]:
            out["replaces"] = "commitment_mismatch"
        elif unfinished or merging:
            return {"action": "wait", "why": "merge_unfinished" if unfinished else "candidate_merges"}
        else:
            change = land.applied(tree, inp["patches"][answer["instance_id"]])
            if not change["reasons"]:
                return {"action": "plant", "instance_id": answer["instance_id"], "path": change["path"],
                        "content": change["content"]}
            out["replaces"] = "patch_does_not_apply"
    elif last is not None:
        if last["payload"].get("merge_sha") in unfinished:
            return {"action": "wait", "why": "drill_unfinished"}
        commits = [i for i in drills if rows[i]["kind"] == "commit"]
        if commits:
            answer = RD.key(inp["seed"], committed_by(rows, commits[-1]), inp["catalog"])
            out["judged"] = dict(RD.judge(ledger, answer), key=answer)
    misfits = sorted(i for i, patch in inp["patches"].items() if land.applied(tree, patch)["reasons"])
    if misfits:
        return dict(out, action="none", why="patch_does_not_apply", instances=misfits)
    answer = RD.key(inp["seed"], RD.cycle(this_run), inp["catalog"])
    return dict(out, action="commit", payload=RD.commit_payload(answer))


def line(done: dict) -> dict:
    """The step as ``yaz``'s line shows it: the planted file's content left out."""
    return {k: v for k, v in done.items() if k != "content"}
