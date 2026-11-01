"""What merging one accepted candidate writes on the target, in one place (stage 0; called by ``activate`` and D6 of
``yaz``).

Rules: asama-0/08 (an accepted candidate is applied to ``brain/integration``'s head), asama-0/01 D6 (``yaz``
writes ``brain/c/<id>``, the pull request, the check and the merge; every ref under ``refs/heads/brain/``),
tohum/01b (``brain/integration`` takes changes only by pull request, merges are serial), ``target.write`` (MF9, the
one writer; its guard checks every request).

``applied(tree, diff_text)``: the candidate's one changed file after its diff, ``{reasons, path, content}``. The
diff must parse (``gate.diffguard.parse``) and change exactly one file (``diff_not_one_file`` otherwise: the gate's
criterion 4 lets a candidate change only its finding's file, and nothing here writes more than one); the base file is
read from ``tree`` at the block's path (a regular file, no symbolic link on its way, else ``base_file_missing``) and
the hunks applied (``gate.diffguard.apply``, which takes only an in-place text change: a creation, deletion, rename,
copy, mode change or binary patch is ``patch_does_not_apply`` too). ``content`` is ``None`` with a reason.

``land(writer, cid, path, content, base, check)``: branch ``brain/c/<cid>`` at ``base``, one commit setting ``path``
to ``content``, a pull request into ``brain/integration``, a ``success`` check run named ``check`` on the commit, and
the merge pinned to that commit; returns ``{pull, head_sha, merge_sha}``. Each step is one ``target.write`` call;
an error leaves the earlier steps written (the caller's ``HardStop`` names them, ``writer.written``).

Out of scope, stated: whether ``base`` is still ``brain/integration``'s head (the caller reads it before landing;
GitHub refuses a merge that is not a fast-forward of a moved base only by the ruleset's strict check); that the
file is the finding's (the gate's criterion 4, judged before).
"""

from __future__ import annotations

from typing import Any

from gate import diffguard
from ledger import append
from profile import derive
from target import branches, write

CANDIDATE_PREFIX = "brain/c/"


class HardStop(append.HardStop):
    """A cycle's write failed after its first write; ``written`` names the refs already written (tohum/28)."""

    def __init__(self, message: str, written: list[str]):
        super().__init__("%s (written: %s)" % (message, ", ".join(written) or "nothing"))
        self.written = written


def applied(tree: str, diff_text: str) -> dict:
    """``{reasons, path, content}``: see the module docstring."""
    try:
        blocks = diffguard.parse(diff_text)
    except diffguard.DiffError:
        return {"reasons": ["diff_unusable"], "path": None, "content": None}
    if len(blocks) != 1:
        return {"reasons": ["diff_not_one_file"], "path": None, "content": None}
    path = blocks[0]["new"] or blocks[0]["old"]
    old = derive._read_regular(tree, path)
    if old is None:
        return {"reasons": ["base_file_missing"], "path": path, "content": None}
    try:
        content = diffguard.apply(blocks[0], old)
    except diffguard.DiffError:
        return {"reasons": ["patch_does_not_apply"], "path": path, "content": None}
    return {"reasons": [], "path": path, "content": content}


def land(writer: Any, cid: str, path: str, content: bytes, base: str, check: str) -> dict:
    """Branch, commit, pull request, check and merge of one accepted candidate onto ``brain/integration``."""
    branch = CANDIDATE_PREFIX + cid
    title = "candidate %s" % cid
    writer.create_branch(branch, base)
    head = writer.commit_files(branch, base, {path: content}, title)
    pull = writer.open_pull(branch, branches.INTEGRATION, title, "accepted by the gate (asama-0/08)")
    if pull is None:
        raise write.ApiError(None, "pull request created without a number")
    writer.check(head, check, "success", "gate: merge")
    merge = writer.merge(pull, head)
    return {"pull": pull, "head_sha": head, "merge_sha": merge}
