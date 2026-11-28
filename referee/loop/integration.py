"""``brain/integration``'s head against the commit the verified ``brain/state`` ledger names (``çek``, D1; stage 0).

Rules: tohum/13 "Zincir kırığı" (E637: a ``brain/integration`` head other than the commit the last signed state row
names, a merge or a revert, is a chain break; the naming row is the merge row's ``merge_sha``, the revert row's
``head_sha`` or the cut row's ``base_sha``, 13:53-55; the break's row and commit are reported; in (B) only tohum/25a's
failure procedure repairs it), tohum/01b (``brain/integration`` takes changes only by the gate's pull requests),
tohum/26f (the ``merge``, ``plant`` and ``revert`` rows), ``ledger.serial.integration_tip`` (the one reader of which
row names the commit), ``target.write`` (a merge is made with ``merge_method: merge``, its first parent the base;
a revert commit has the reverted merge as its one parent and the tree of that merge's first parent),
``target.land.revert`` (the revert commit reaches ``brain/integration`` by its own pull request's merge).

**Input**: ``ledger``, the bytes of the ``brain/state`` head's ``ledger.jsonl`` once D1 verified it as a chain and
against its signed root (``loop.state``, ``ledger.anchor``); ``head``, ``brain/integration``'s head as listed.

**The named commit** (``named``): ``ledger.serial.integration_tip``'s answer ``{row_id, kind, sha}``. A ledger that
does not conform to ``ledger.schema`` is refused with ``ledger.serial``'s reasons; a ledger in which no row records
a write on ``brain/integration`` is ``integration_unnamed`` (``activate`` writes the cut row in a target's first
cycle, so a verified ledger without one names nothing to compare the head with).

**The head** (``reasons``), by the row's kind:

- ``cut``, ``merge`` and ``revert`` (a revert row's ``head_sha``, tohum/26f:78-79): the head must be the row's
  ``sha``, else ``head_not_named``. Nothing is fetched.
- ``reverted``: a revert row written before tohum/26f gave it ``head_sha``; it names the merge ``M`` it reverted,
  not the revert's own commit. The head is then judged by what the gate's revert of ``M`` leaves, read from commit objects
  only (``history``, an object source holding the head's ancestry), in this order, the first failing rule the one
  reason: the head has exactly two parents and the first is ``M`` (else ``revert_head_parents``); ``M`` has
  exactly two parents (else ``reverted_not_merge``); the head's second parent, the revert commit, has ``M`` as its
  one parent (else ``revert_commit_parents``); the revert commit's tree id and the head's are both the tree id of
  ``M``'s first parent (else ``revert_head_tree``). A git object reason of these reads (``loop.gitobj``:
  ``object_missing:<sha>``, ``commit_unreadable``, ...) is listed as ``integration:<reason>``.

What the ``reverted`` rules say and do not say: a head that passes is the merge, on top of ``M``, of one commit on ``M``
whose content is the content before ``M``, and has that content. Who wrote the two commits and whether GitHub made
the head from the gate's pull request are not judged; two heads of that shape (other messages, authors, dates) are
not told apart.

Out of scope, stated: the fetch of the ancestry (the job's, ``loop.job._cek_integration``); whether the commit a
``cut`` or ``merge`` row names has the content the row's cycle judged (D6 wrote the row from GitHub's answer);
``brain/c/*``, ``brain/revert/*`` and ``brain/drill/*`` (no row names their heads); a hard stop row (tohum/28's
watcher is not stage 0's: here the cycle is refused in ``çek`` before anything of the target's tree is fetched, as
for a root that does not anchor the ledger).
"""

from __future__ import annotations

from typing import Any

from ledger import serial
from loop import gitobj as G
from loop.pulled import PulledError


def named(ledger: bytes) -> dict[str, str]:
    """The row and commit ``ledger`` names for ``brain/integration`` (see the module); ``PulledError``."""
    try:
        tip = serial.integration_tip(ledger)
    except serial.Unusable as exc:
        raise PulledError(exc.reasons) from None
    if tip is None:
        raise PulledError(["integration_unnamed"])
    return tip


def reasons(tip: dict[str, str], head: str, history: Any = None) -> list[str]:
    """Why ``head`` is not the commit ``tip`` names (see the module); ``history`` is read only for a ``reverted``."""
    if tip["kind"] != "reverted":
        return [] if head == tip["sha"] else ["head_not_named"]
    try:
        found = G.parents(history, head)
        if len(found) != 2 or found[0] != tip["sha"]:
            return ["revert_head_parents"]
        merged = G.parents(history, tip["sha"])
        if len(merged) != 2:
            return ["reverted_not_merge"]
        if G.parents(history, found[1]) != [tip["sha"]]:
            return ["revert_commit_parents"]
        before = G.tree_of(history, merged[0])
        both = G.tree_of(history, found[1]) == before and G.tree_of(history, head) == before
        return [] if both else ["revert_head_tree"]
    except PulledError as exc:
        return ["integration:%s" % r for r in exc.reasons]
