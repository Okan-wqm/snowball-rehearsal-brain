"""The catalog a revert drill's commitment draws from (tohum/26f "Taahhüdün kataloğu", E641).

``harness.revert_drill.eligible`` over rows written out here, each expected set stated by hand:

- no plant, and equal counts: every instance, in the catalog's order, each object as given;
- a cause's count is its instances' plants together; the least count wins, zero or not;
- what counts nothing: an id outside the catalog, an id that is no string, a plant of another drill, a ``commit``
  row naming an instance, an ``events`` row of kind ``plant``;
- only the rows after the last ``genesis`` row count; a catalog ``instances`` refuses is unusable.

``loop.drill.step`` and ``drawn`` over chained ledgers (``ledger.append``), the keys computed here with a hand HMAC
over the ids stated in each test:

- the commitment after a finished drill is drawn from the other causes' instances, and after a new genesis from
  every instance again;
- the plant step and the judging step derive a commitment's key from the rows before that commitment, with plants
  after it in the ledger; a commitment drawn from the whole catalog where the rule narrows it is replaced;
- for each of 40 seeds, three drills one after another plant three different causes (one and two instances a
  cause), and the fourth is drawn from every instance again.

``harness.pass_row``'s side of the same derivation is in test_pass_row (``toy_world``'s three drills, and
``Fails.test_a_commitment_not_drawn_from_the_least_planted_causes``); the cycles as ``yaz`` writes them in
test_loop_write ``D8`` and test_rehearsal.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from harness import revert_drill as RD  # noqa: E402
from loop import drill as DR  # noqa: E402
from profile_tree import write_tree  # noqa: E402
from test_kos import diff  # noqa: E402
from test_revert_drill import commit, hand_hmac, ledger_with, plant, reverted, row  # noqa: E402

T1, T2, B1, B2, L1, L2 = "t1", "t2", "b1", "b2", "l1", "l2"
CAUSE = {T1: "test_regression", T2: "test_regression", B1: "build_break", B2: "build_break",
         L1: "lint_regression", L2: "lint_regression"}
# the file's order is not the ids' order, and one instance carries a field nothing here reads
CATALOG = {"instances": [{"id": L2, "cause": CAUSE[L2]}, {"id": T1, "cause": CAUSE[T1], "patch": "t1.patch"},
                         {"id": B1, "cause": CAUSE[B1]}, {"id": T2, "cause": CAUSE[T2]},
                         {"id": L1, "cause": CAUSE[L1]}, {"id": B2, "cause": CAUSE[B2]}]}
SINGLE = {"instances": [{"id": i, "cause": CAUSE[i]} for i in (T1, B1, L1)]}
SEED = {"seed": "draw-seed"}
PATCH = diff("pkg/a.js", ["var a = 1;"], ["var a = 2;"]).decode()


def sha(n: int) -> str:
    return ("%x" % n).rjust(40, "0")


def ids(catalog: dict) -> list[str]:
    return [item["id"] for item in catalog["instances"]]


def genesis(row_id: str) -> dict:
    return row(row_id, "events", "genesis", {})


def start(run: str) -> dict:
    return row(run + "-1:start", "events", "cycle_start", {"cycle_id": run + "-1"})


def hand_key(seed: dict, run: str, among: list[str]) -> dict:
    """The key for ``run`` drawn from the ids ``among``: RFC 2104 by hand, the index over the sorted ids."""
    chosen = hand_hmac(seed["seed"].encode("utf-8"), run.encode())
    instance = sorted(among)[int(chosen, 16) % len(among)]
    return {"cycle_id": run, "selection": chosen, "instance_id": instance, "cause": CAUSE[instance]}


def run_where(pick, start_at: int = 100) -> str:
    """The first run id from ``start_at`` for which ``pick(run id)`` holds (searched: no selection is written)."""
    for n in range(start_at, start_at + 5000):
        if pick(str(n)):
            return str(n)
    raise AssertionError("no run id found")


def drilled(run: int, instance: str, among: list[str], seed: dict = SEED) -> list[dict]:
    """A finished drill's rows over three cycles from ``run``: the commitment drawn from ``among`` (written whatever
    ``instance`` is), the plant of ``instance`` and its revert with the instance's cause."""
    merge = sha(run)
    return [start(str(run)), commit("c%d" % run, hand_key(seed, str(run), among)),
            start(str(run + 1)), plant("p%d" % run, instance, merge),
            start(str(run + 2)), reverted("r%d" % run, merge, CAUSE[instance])]


class Eligible(unittest.TestCase):
    def got(self, rows: list[dict], catalog: dict = CATALOG) -> list[str]:
        return ids(RD.eligible(catalog, rows))

    def test_without_a_plant_every_instance_as_given(self):
        for rows in ([], [genesis("g")], [genesis("g"), start("5"), commit("c", hand_key(SEED, "5", list(CAUSE)))]):
            self.assertEqual(RD.eligible(CATALOG, rows), CATALOG)
        self.assertEqual(RD.eligible(CATALOG, [])["instances"][1], {"id": T1, "cause": CAUSE[T1], "patch": "t1.patch"})

    def test_a_planted_cause_leaves_with_all_its_instances(self):
        self.assertEqual(self.got([genesis("g"), plant("p", T2, sha(1))]), [L2, B1, L1, B2])
        self.assertEqual(self.got([plant("p", B1, sha(1))]), [L2, T1, T2, L1])  # a ledger with no genesis row
        self.assertEqual(self.got([genesis("g"), plant("p", L1, sha(1))], SINGLE), [T1, B1])

    def test_the_least_count_wins(self):
        t, t2, b, l = (plant("p%d" % n, i, sha(n)) for n, i in enumerate((T1, T2, B2, L2)))
        self.assertEqual(self.got([t, b]), [L2, L1])              # 1, 1, 0
        self.assertEqual(self.got([t, t2, b]), [L2, L1])          # 2, 1, 0: both instances of a cause count for it
        self.assertEqual(self.got([t, b, l]), ids(CATALOG))       # 1, 1, 1: every instance again
        self.assertEqual(self.got([t, t2, b, l]), [L2, B1, L1, B2])  # 2, 1, 1: the least is not zero
        self.assertEqual(self.got([t, t, t2]), [L2, B1, L1, B2])  # a plant row read twice counts twice

    def test_rows_that_count_nothing(self):
        other_drill = row("o", "drill", "plant", {"drill": "lesson", "family": "lesson", "instance_id": T1})
        for name, extra in (("an id outside the catalog", plant("x", "t3", sha(2))),
                            ("an id that is no string", row("x", "drill", "plant", dict(RD.plant_payload(T1, sha(2)),
                                                                                         instance_id=[T1]))),
                            ("another drill's plant", other_drill),
                            ("a commit row naming an instance", row("x", "drill", "commit",
                                                                    dict(RD.plant_payload(T1, sha(2))))),
                            ("an events row of kind plant", row("x", "events", "plant", RD.plant_payload(T1, sha(2))))):
            with self.subTest(name):
                self.assertEqual(self.got([extra]), ids(CATALOG))
                # beside a counted plant of another cause the answer is that plant's alone
                self.assertEqual(self.got([extra, plant("p", B1, sha(1))]), [L2, T1, T2, L1])

    def test_only_the_rows_after_the_last_genesis_count(self):
        before, after = plant("p1", T1, sha(1)), plant("p2", B1, sha(2))
        self.assertEqual(self.got([genesis("g1"), before, genesis("g2")]), ids(CATALOG))
        self.assertEqual(self.got([genesis("g1"), before, genesis("g2"), after]), [L2, T1, T2, L1])
        self.assertEqual(self.got([genesis("g1"), genesis("g2"), before, after]), [L2, L1])
        self.assertEqual(self.got([before, genesis("g1"), after, genesis("g2")]), ids(CATALOG))
        self.assertEqual((RD.last_genesis([]), RD.last_genesis([before]), RD.last_genesis([genesis("g"), before]),
                          RD.last_genesis([genesis("g1"), before, genesis("g2"), after])), (None, None, 0, 2))
        # a row of kind genesis in another part is no genesis row
        self.assertEqual(self.got([before, row("x", "drill", "genesis", {})]), [L2, B1, L1, B2])

    def test_an_unusable_catalog(self):
        for catalog in ({}, {"instances": []}, {"instances": [{"id": "a"}]},
                        {"instances": [{"id": "a", "cause": "x"}, {"id": "a", "cause": "y"}]}):
            with self.subTest(catalog=catalog), self.assertRaises(RD.Unusable):
                RD.eligible(catalog, [])


class Step(unittest.TestCase):
    """``loop.drill.step`` with every patch applying and nothing unfinished, on ledgers chained here."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tree = temp.name
        write_tree(self.tree, {"pkg/a.js": "var a = 1;\n"})

    def inp(self, catalog: dict = CATALOG, seed: dict = SEED) -> dict:
        return {"seed": seed, "catalog": {"instances": [{"id": i["id"], "cause": i["cause"]}
                                                        for i in catalog["instances"]]},
                "patches": {i["id"]: PATCH for i in catalog["instances"]}}

    def step(self, rows: list[dict], run: str, catalog: dict = CATALOG, seed: dict = SEED) -> dict:
        return DR.step(self.inp(catalog, seed), ledger_with(rows), [], False, self.tree, run)

    def test_the_first_commitment_is_drawn_from_every_instance(self):
        for run in ("7", "8", "9", "10"):
            self.assertEqual(self.step([genesis("g"), start("6")], run),
                             {"action": "commit", "payload": RD.commit_payload(hand_key(SEED, run, list(CAUSE)))})

    def test_the_commitment_after_a_drill_is_drawn_from_the_other_causes(self):
        rest = [B1, B2, L1, L2]
        # a run whose draw from every instance is one the rule excludes: the two catalogs give different keys
        run = run_where(lambda r: hand_key(SEED, r, list(CAUSE))["instance_id"] in (T1, T2))
        rows = [genesis("g")] + drilled(10, T2, list(CAUSE))
        out = self.step(rows, run)
        self.assertEqual((out["action"], out["judged"]["verdict"], out["payload"]),
                         ("commit", "PASS" if hand_key(SEED, "10", list(CAUSE))["instance_id"] == T2 else "FAIL",
                          RD.commit_payload(hand_key(SEED, run, rest))))
        self.assertIn(hand_key(SEED, run, rest)["instance_id"], rest)
        # after a new genesis the earlier plant counts nothing: every instance again
        out = self.step(rows + [genesis("g2"), start("40")], run)
        self.assertEqual(out["payload"], RD.commit_payload(hand_key(SEED, run, list(CAUSE))))

    def second(self) -> tuple[list[dict], str, dict]:
        """A ledger whose first drill planted T1 and whose second commitment, in a run where the whole catalog,
        the four ids the rule gives and the two ids left after its own plant each select another instance, is drawn
        from the four: (rows up to that commitment, its run id, its key)."""
        first = run_where(lambda r: hand_key(SEED, r, list(CAUSE))["instance_id"] == T1)
        rest = [B1, B2, L1, L2]

        def apart(r: str) -> bool:
            key = hand_key(SEED, r, rest)
            left = [i for i in rest if CAUSE[i] != key["cause"]]
            return len({key["instance_id"], hand_key(SEED, r, list(CAUSE))["instance_id"],
                        hand_key(SEED, r, left)["instance_id"]}) == 3
        run = run_where(apart, int(first) + 3)
        key = hand_key(SEED, run, rest)
        return [genesis("g")] + drilled(int(first), T1, list(CAUSE)) + [start(run), commit("c2", key)], run, key

    def test_the_plant_is_the_instance_of_the_key_drawn_at_the_commitment(self):
        rows, run, key = self.second()
        out = self.step(rows + [start(str(int(run) + 1))], str(int(run) + 1))
        self.assertEqual((out["action"], out["instance_id"], out["path"]), ("plant", key["instance_id"], "pkg/a.js"))
        self.assertEqual(DR.drawn(self.inp(), rows, len(rows) - 1), key)

    def test_the_judged_key_is_drawn_from_the_rows_before_its_commitment(self):
        rows, run, key = self.second()
        merge, after = sha(0xabc), str(int(run) + 3)
        rows += [start(str(int(run) + 1)), plant("p2", key["instance_id"], merge),
                 start(str(int(run) + 2)), reverted("r2", merge, key["cause"]), start(after)]
        out = self.step(rows, after)
        # the ledger now holds the second plant too; the key is the one drawn before it
        self.assertEqual(out["judged"], {"verdict": "PASS", "reasons": [], "key": key})
        last = [i for i in (B1, B2, L1, L2) if CAUSE[i] != key["cause"]]
        self.assertEqual((out["action"], out["payload"]), ("commit", RD.commit_payload(hand_key(SEED, after, last))))

    def test_a_commitment_drawn_from_the_whole_catalog_where_the_rule_narrows_is_replaced(self):
        rows, run, key = self.second()
        whole = hand_key(SEED, run, list(CAUSE))
        self.assertNotEqual(whole["instance_id"], key["instance_id"])
        rows = rows[:-1] + [commit("c2", whole), start(str(int(run) + 1))]
        out = self.step(rows, str(int(run) + 1))
        self.assertEqual((out["action"], out["replaces"], out["payload"]),
                         ("commit", "commitment_mismatch",
                          RD.commit_payload(hand_key(SEED, str(int(run) + 1), [B1, B2, L1, L2]))))

    def test_three_drills_in_a_row_plant_three_causes_whatever_the_seed(self):
        for catalog in (SINGLE, CATALOG):
            for n in range(40):
                seed = {"seed": "any-seed-%d" % n}
                rows, run, planted = [genesis("g")], 50, []
                for _ in range(4):
                    out = self.step(rows + [start(str(run))], str(run), catalog, seed)
                    self.assertEqual(out["action"], "commit", out)
                    if planted:
                        self.assertEqual((out["judged"]["verdict"], out["judged"]["key"]["instance_id"]),
                                         ("PASS", planted[-1]))
                    rows += [start(str(run)), row("c%d" % run, "drill", "commit", out["payload"])]
                    out = self.step(rows + [start(str(run + 1))], str(run + 1), catalog, seed)
                    self.assertEqual(out["action"], "plant", out)
                    planted.append(out["instance_id"])
                    rows += [start(str(run + 1)), plant("p%d" % run, planted[-1], sha(run)),
                             start(str(run + 2)), reverted("r%d" % run, sha(run), CAUSE[planted[-1]])]
                    run += 3
                self.assertEqual(sorted(CAUSE[i] for i in planted[:3]), sorted(set(CAUSE.values())), (seed, planted))
                # the fourth is drawn from every instance: its key is the hand key over all the catalog's ids
                fourth = hand_key(seed, str(run - 3), ids(catalog))
                self.assertEqual(planted[3], fourth["instance_id"])


if __name__ == "__main__":
    unittest.main()
