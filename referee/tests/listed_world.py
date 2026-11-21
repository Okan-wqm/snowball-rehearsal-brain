"""The world behind an open allowlist gate, for tests of what follows a merge in a cycle after the genesis cycle.

Since P1 MF9 (tohum/26j "İzin listesi, MF9") ``loop.decide`` judges every candidate's package with
``gate.allowlist.reasons`` in every cycle but the genesis cycle, and the package of the candidates it reads (the
ready candidates) is ``loop.decide.READY``, which names no organ: live, none merges (bound without this world by
test_loop_yaz's ``ClosedGate``). The package of a run-time candidate is read by no job before P1 MF12
(``loop/candidates.py``), so no input of a job can name an organ yet. The tests of the merge's mechanics (D5's
serial rule and criteria, D6's writes, D7, D8's wait, Gözcü's triggers over a merge) therefore stand in a world
whose three parts open the gate the way a listed organ's candidate would:

- ``name_organ``: ``loop.decide.READY`` replaced, for one test, by a package naming ``ORGAN``. This is the one
  stand-in: it takes the place of the package MF12 will read, and of nothing else;
- ``ORGANS``: ``ORGAN``'s definition, carried in ``pulled`` as the accepted SHA's (``organs``);
- ``accept_rows`` / ``listed``: ``ORGAN``'s accept row, as ``gate.allowlist.rows`` builds it, in the ledger of
  ``brain/state`` the cycle starts from.

The gate itself is not replaced: ``gate.allowlist.reasons`` runs on the real rows and the real definition, and
with any one of the three parts taken away the candidate is refused (``ClosedGate`` takes each away). What these
tests prove is the mechanics behind an open gate; they do not prove that any candidate reaches it in a live cycle.
"""

from __future__ import annotations

import json
from unittest import mock

from gate import allowlist as AL
from ledger import append
from ledger import chain
from loop import decide as E
from target import branches as B

ORGAN = "listed.organ"
ORGANS = {ORGAN: {"entry": ["python3", "/in/adapters/listed/main.py"],
                  "files": {"adapters/listed/main.py": b"print('[]')\n"}}}
ENTRY = {"brain_sha": "b" * 40, "run_id": "1", "organ_ids": [ORGAN]}
CYCLE = {"cycle_id": "g", "ts": "2026-10-30T12:00:00Z", "snapshot_id": "c" * 40}


def accept_rows(cycle: dict | None = None, held: list[dict] | None = None) -> list[dict]:
    """``ORGAN``'s accept row of ``cycle`` (``gate.allowlist.rows``); none when ``held``'s rows list it already."""
    return AL.rows(cycle or CYCLE, ENTRY, ORGANS, held or [])


def listed(state: dict[str, bytes]) -> dict[str, bytes]:
    """``state`` (``brain/state``'s chained files) with ``ORGAN``'s accept row appended to the ledger's chain,
    unless the ledger lists it already. Not for a state whose root is signed over the ledger: build that one with
    ``accept_rows`` among its rows."""
    ledger = state[B.STATE_LEDGER]
    rows = accept_rows(held=[chain.parse_row(line.decode()) for line in ledger.splitlines()])
    if not rows:
        return state
    content = append.plan_cycle(ledger, ledger, lambda: json.dumps({"rows": rows}).encode()).content
    return dict(state, **{B.STATE_LEDGER: content})


def name_organ(case) -> None:
    """For the test ``case``: the package ``loop.decide`` judges names ``ORGAN`` (undone at the test's end)."""
    patch = mock.patch.dict(E.READY, {"organ_ids": [ORGAN]})
    patch.start()
    case.addCleanup(patch.stop)
