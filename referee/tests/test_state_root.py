"""Test 11 of asama-0/09 (P1 MF5; tohum/01a "Genellik testi"): on the toy, ``<state_root>`` grows from nothing.

The world is the rehearsal's (``test_rehearsal.Flow`` without the drill's fixtures): a toy that holds ``main``
alone, served by ``loop.job``'s five jobs run after run. Over the genesis and the three cycles after it, the runs
build ``brain/state`` from no branch: an orphan first commit, each later commit on the one before, every path under
``target.branches.STATE_ROOT``, no file lost and at least one more held, both chains extended by whole lines, every
other file but the status block byte for byte as it was, and nothing of the state on ``main`` or
``brain/integration``; each ``yaz`` line carries the harness's report and the offline reading (``harness.offline``)
of the code that ran. No module of its own stands behind this test (reports/seed-077): what it reads is the loop
as built.

Out of scope, stated: an empty toy (this one holds the tree the fake runner tests); the real GitHub
(``fake_github``); the parts of ``<state_root>`` no job writes yet (cases, findings, properties: reports/seed-075);
the copy's state (this flow never writes it, asserted); names of a target in the brain's text (test 14,
``tests/generality.py``).
"""

from __future__ import annotations

import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_rehearsal as R  # noqa: E402
from harness import offline as OF  # noqa: E402
from profile_tree import writable_base  # noqa: E402
from target import branches as B  # noqa: E402


def tree_of(hub, sha: str) -> dict[str, bytes]:
    return {path: hub.blobs[blob] for path, blob in hub.trees[hub.commits[sha]["tree"]].items()}


class StateRoot(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-state-root-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def test_the_toys_state_root_grows_from_nothing(self):
        flow = R.without_fixtures(self.base)
        hub = flow.hubs["o/toy"]
        under = B.STATE_ROOT + "/"
        self.assertEqual(sorted(hub.refs), ["main"])
        self.assertEqual([p for p in tree_of(hub, hub.refs["main"]) if p.startswith(B.STATE_ROOT)], [])
        before: dict[str, bytes] = {}
        head = None
        for run in range(1, 5):
            lines = flow.run()
            line = lines["yaz"]["targets"][0]
            self.assertTrue(lines["yaz"]["ok"], lines["yaz"])
            # the harness: the scorer's report on the target's line, the offline reading of the running code on the job's
            self.assertIn("report", line["harness"])
            self.assertEqual(lines["yaz"]["offline"], {"modules": OF.check(REFEREE)["modules"]})
            sha = hub.refs[B.STATE]
            self.assertEqual(hub.commits[sha]["parents"], [head] if head else [], run)   # orphan, then one line
            now = tree_of(hub, sha)
            self.assertTrue(now and all(p.startswith(under) for p in now), sorted(now))
            self.assertLess(set(before), set(now), run)                                  # nothing lost, more held
            for chain in B.STATE_CHAINS:
                old, new = before.get(chain, b""), now[chain]
                self.assertTrue(new.startswith(old) and len(new) > len(old) and new.endswith(b"\n"), (run, chain))
            self.assertEqual({p: d for p, d in now.items() if p in before and p not in B.STATE_CHAINS
                              and p != B.STATE_STATUS},
                             {p: d for p, d in before.items() if p not in B.STATE_CHAINS and p != B.STATE_STATUS})
            for branch in ("main", B.INTEGRATION):
                self.assertEqual([p for p in tree_of(hub, hub.refs[branch]) if p.startswith(B.STATE_ROOT)], [],
                                 (run, branch))
            before, head = now, sha
        self.assertEqual(sorted(flow.hubs["o/copy"].refs), ["main"])


if __name__ == "__main__":
    unittest.main()
