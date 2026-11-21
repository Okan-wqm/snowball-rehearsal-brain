"""Test 55 (tohum/26h, tohum/26j "İzin listesi, MF9"; P1 MF9): ``gate.allowlist``, the allowlist of organ
definitions and its ``accept`` rows.

What is proven, each by the test named for it:

- test 55 itself (``Test55``): the candidate of an organ whose definition hash is in no ``accept`` row is
  refused; once the row of that organ and hash is written the same package, with the same definitions, is
  allowed; the hash the package states changes neither answer (absent, the true one, a listed one, another
  organ's, not a hash at all);
- the list (``Listed``): only ``part: accept`` rows are read; the list is of ``(organ_id, definition_sha256)``
  pairs; an accept row of another kind or payload shape (run ids that are not exactly one among them), and rows
  that are no list of objects, list nothing (``Unusable``);
- the decision (``Decision``): every named organ is judged, in the package's order; an organ the accepted SHA
  does not hold; a package naming no organ; any byte, path or entry word of the definition changes the hash
  compared; a hash listed for another organ does not allow; package and definitions of other shapes;
- the entry request (``Request``): exactly ``{organ_ids}``;
- the rows (``Rows``): the row's fields; the hash is computed, the SHA and the one run id are the entry's; an
  entry made twice writes once, a changed definition writes again; every unusable input gives no row for any
  organ; the SHA and the run id are judged only when a row is written; the rows are ledger rows
  ``ledger.schema`` takes, chained by the cycle's own plan.

The wiring is proven where it runs: D5's refusal of every ready candidate outside the genesis cycle in
``test_loop_yaz`` (``Allowlist``), D6's rows in ``test_loop_write`` (``AcceptRows``), the entry request's
reading in ``test_loop_cek`` and its carriage in ``test_pulled``.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from gate import allowlist as A  # noqa: E402
from ledger import append as LA  # noqa: E402
from ledger import chain as LC  # noqa: E402
from ledger import events as LE  # noqa: E402
from ledger import schema as SC  # noqa: E402
from runner import organs as O  # noqa: E402

SHA = "a1" * 20
OTHER_SHA = "b2" * 20
CYCLE = {"cycle_id": "c-7", "ts": "2026-11-21T12:00:00Z", "snapshot_id": "c3" * 20}
RUN = "44862711957"


def definitions() -> dict:
    return {"lint.discover": {"entry": ["python", "/in/adapter.py"], "files": {"adapter.py": b"print('lint')\n"}},
            "fixer.range": {"entry": ["python", "/in/fix.py", "--range"],
                            "files": {"fix.py": b"print('fix')\n", "lib/apply.py": b"# apply\n"}}}


def own(organ_id: str, defs: dict | None = None) -> str:
    return O.definition_sha256((defs or definitions())[organ_id])


def package(*organ_ids: str, **over) -> dict:
    """A candidate package of tohum/26a, stating the true hashes unless told otherwise."""
    out = {"finding": {"rule_id": "no-var"}, "diff": "--- a/x\n", "organ_ids": list(organ_ids),
           "definition_sha256": [own(o) for o in organ_ids if o in definitions()]}
    out.update(over)
    return {k: v for k, v in out.items() if v is not ...}


def stored(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").splitlines()]


class Written:
    def __init__(self, ledger: bytes, rows: list[dict]) -> None:
        self.rows = rows
        self.content = chained(rows, ledger) if rows else ledger


def entry(organ_ids, sha=SHA, run=RUN) -> dict:
    return {"brain_sha": sha, "run_id": run, "organ_ids": organ_ids}


def accept(ledger: bytes, organ_ids, defs=None, cycle=CYCLE, sha=SHA, run=RUN) -> Written:
    """``rows`` of an entry onto ``ledger``, chained as a cycle's plan chains them."""
    return Written(ledger, A.rows(cycle, entry(organ_ids, sha, run), definitions() if defs is None else defs,
                                  stored(ledger)))


def events_row(suffix: str = "start") -> dict:
    return LE.row(CYCLE, suffix, "cycle_start", {"cycle_id": CYCLE["cycle_id"]})


def chained(rows: list[dict], onto: bytes = b"") -> bytes:
    return LA.plan_cycle(onto, onto, lambda: LC.canonical({"rows": rows})).content


def accept_row(hash_: str, organ_id: str = "lint.discover", suffix: str = "a", **over) -> dict:
    payload = {"organ_id": organ_id, "definition_sha256": hash_, "brain_sha": SHA, "evidence_run_ids": ["r1"]}
    payload.update(over)
    return LE.row(CYCLE, suffix, "accept", {k: v for k, v in payload.items() if v is not ...}, part="accept")


class Test55(unittest.TestCase):
    """26h: "tanım hash'i hiçbir accept satırında olmayan organın adayı kapıda reddedilir; o hash için accept
    satırı yazılınca aynı aday aynı koşulda geçer; adayın beyan ettiği hash kararı değiştirmez"."""

    def setUp(self) -> None:
        self.before = chained([events_row()])
        self.after = accept(self.before, ["lint.discover"]).content

    def test_refused_until_the_row_of_its_hash_is_written_then_the_same_package_passes(self):
        pkg, defs = package("lint.discover"), definitions()
        self.assertEqual(A.reasons(pkg, defs, stored(self.before)), ["organ_not_listed:lint.discover"])
        self.assertEqual(A.reasons(pkg, defs, stored(self.after)), [])
        # the same condition: nothing but the one accept row differs between the two ledgers
        self.assertEqual(stored(self.after)[:-1], stored(self.before))
        self.assertEqual(stored(self.after)[-1]["payload"]["definition_sha256"], own("lint.discover"))
        # the control: the row lists that organ's hash and no other organ's
        self.assertEqual(A.reasons(package("fixer.range"), defs, stored(self.after)),
                         ["organ_not_listed:fixer.range"])

    def test_the_hash_the_package_states_changes_no_answer(self):
        listed_hash = own("lint.discover")
        stated = [..., [], [listed_hash], [own("fixer.range")], ["0" * 64], [listed_hash] * 3, listed_hash, None,
                  "not a hash", 7, {"lint.discover": listed_hash}, [None]]
        for value in stated:
            with self.subTest(stated=repr(value)):
                # an organ that is not listed stays refused, whatever the package says of itself
                pkg = package("fixer.range", definition_sha256=value)
                self.assertEqual(A.reasons(pkg, definitions(), stored(self.after)), ["organ_not_listed:fixer.range"])
                # and a listed one stays allowed
                pkg = package("lint.discover", definition_sha256=value)
                self.assertEqual(A.reasons(pkg, definitions(), stored(self.after)), [])
                self.assertEqual(A.reasons(pkg, definitions(), stored(self.before)),
                                 ["organ_not_listed:lint.discover"])

    def test_the_hash_compared_is_of_the_files_handed_not_of_a_row_s_organ_id(self):
        # the accepted SHA's files changed after the row was written: the listed hash is not theirs any more,
        # though the package still states the listed hash and the row still names the organ
        changed = definitions()
        changed["lint.discover"]["files"]["adapter.py"] += b"import os\n"
        pkg = package("lint.discover")
        self.assertEqual(pkg["definition_sha256"], [own("lint.discover")])
        self.assertEqual(A.reasons(pkg, changed, stored(self.after)), ["organ_not_listed:lint.discover"])


class Listed(unittest.TestCase):
    def test_only_accept_rows_are_read(self):
        one, two = "1" * 64, "2" * 64
        other = LE.row(CYCLE, "o", "cycle_start", {"cycle_id": "x", "definition_sha256": two})
        freeze = LE.row(CYCLE, "f", "accept", {"organ_id": "o", "definition_sha256": two, "brain_sha": SHA,
                                               "evidence_run_ids": ["r1"]}, part="freeze")
        self.assertEqual(A.listed([]), frozenset())
        self.assertEqual(A.listed([other, freeze]), frozenset())
        self.assertEqual(A.listed([other, accept_row(one), freeze]), {("lint.discover", one)})
        self.assertEqual(A.listed([accept_row(one), accept_row(two, "fixer.range"), accept_row(one, "third"),
                                   accept_row(one)]),
                         {("lint.discover", one), ("fixer.range", two), ("third", one)})
        # rows of other parts are not judged: one of no shape at all beside an accept row
        self.assertEqual(A.listed([{"part": "events"}, {}, accept_row(one)]), {("lint.discover", one)})

    def test_an_accept_row_of_another_shape_lists_nothing(self):
        good = "1" * 64
        bad = {"another kind": dict(accept_row(good), kind="accepted"),
               "no kind": {k: v for k, v in accept_row(good).items() if k != "kind"},
               "no payload": {k: v for k, v in accept_row(good).items() if k != "payload"},
               "payload a list": dict(accept_row(good), payload=[good]),
               "hash upper": accept_row("A" * 64), "hash short": accept_row("1" * 63),
               "hash long": accept_row("1" * 65), "hash absent": accept_row(...), "hash a number": accept_row(1),
               "organ empty": accept_row(good, ""), "organ absent": accept_row(good, ...),
               "organ a number": accept_row(good, 3),
               "sha short": accept_row(good, brain_sha="a" * 39), "sha absent": accept_row(good, brain_sha=...),
               "sha 64": accept_row(good, brain_sha="a" * 64),
               "runs absent": accept_row(good, evidence_run_ids=...),
               "runs a string": accept_row(good, evidence_run_ids="r1"),
               "a run empty": accept_row(good, evidence_run_ids=[""]),
               "a run a number": accept_row(good, evidence_run_ids=[1]),
               "a run twice": accept_row(good, evidence_run_ids=["r1", "r1"]),
               "two runs": accept_row(good, evidence_run_ids=["r1", "r2"]),
               "no run": accept_row(good, evidence_run_ids=[]),
               "a fifth key": accept_row(good, state="ACTIVE")}
        for name, row in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(A.Unusable):
                    A.listed([accept_row("2" * 64), row])
                with self.assertRaises(A.Unusable):       # and no candidate is judged against such a ledger
                    A.reasons(package("lint.discover"), definitions(), [accept_row(own("lint.discover")), row])
                with self.assertRaises(A.Unusable):       # also a candidate that names no organ
                    A.reasons(package(), definitions(), [row])
        self.assertEqual(A.listed([accept_row(good, evidence_run_ids=["r2"])]), {("lint.discover", good)})  # control

    def test_rows_that_are_no_list_of_objects_list_nothing(self):
        for rows in (None, {}, "rows", (accept_row("1" * 64),), [accept_row("1" * 64), "row"], [None], [[]]):
            with self.subTest(rows=repr(rows)[:40]):
                with self.assertRaises(A.Unusable):
                    A.listed(rows)


class Decision(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [accept_row(own("lint.discover"))]
        self.both = self.rows + [accept_row(own("fixer.range"), "fixer.range", "b")]

    def test_every_named_organ_is_judged_in_the_package_s_order(self):
        defs = definitions()
        self.assertEqual(A.reasons(package("lint.discover", "fixer.range"), defs, self.both), [])
        self.assertEqual(A.reasons(package("lint.discover", "fixer.range"), defs, self.rows),
                         ["organ_not_listed:fixer.range"])
        self.assertEqual(A.reasons(package("fixer.range", "lint.discover"), defs, self.rows),
                         ["organ_not_listed:fixer.range"])
        self.assertEqual(A.reasons(package("fixer.range", "lint.discover"), defs, []),
                         ["organ_not_listed:fixer.range", "organ_not_listed:lint.discover"])
        self.assertEqual(A.reasons(package("lint.discover", "fixer.range"), defs, []),
                         ["organ_not_listed:lint.discover", "organ_not_listed:fixer.range"])
        self.assertEqual(A.reasons(package("ghost", "fixer.range", "lint.discover"), defs, self.rows),
                         ["organ_unknown:ghost", "organ_not_listed:fixer.range"])

    def test_an_organ_the_accepted_sha_does_not_hold_is_unknown(self):
        defs = definitions()
        for organ_id in ("ghost", "lint.discove", "Lint.Discover", "lint.discover ", "lint"):
            with self.subTest(organ_id=organ_id):
                self.assertEqual(A.reasons(package(organ_id), defs, self.both), ["organ_unknown:%s" % organ_id])
        # also when a row names that id and the package states a listed hash: there are no files to hash
        rows = self.both + [accept_row("9" * 64, "ghost", "g")]
        self.assertEqual(A.reasons(package("ghost", definition_sha256=["9" * 64]), defs, rows), ["organ_unknown:ghost"])
        self.assertEqual(A.reasons(package("lint.discover"), {}, self.both), ["organ_unknown:lint.discover"])

    def test_a_package_that_names_no_organ_is_refused(self):
        self.assertEqual(A.reasons(package(), definitions(), self.both), ["no_organ"])
        self.assertEqual(A.reasons(package(definition_sha256=[own("lint.discover")]), definitions(), self.both),
                         ["no_organ"])
        self.assertEqual(A.reasons(package(), {}, []), ["no_organ"])

    def test_each_part_of_the_definition_changes_the_hash_compared(self):
        changes = {"a byte of a file": lambda d: d["files"].__setitem__("fix.py", b"print('fix') \n"),
                   "a file added": lambda d: d["files"].__setitem__("extra.py", b""),
                   "a file removed": lambda d: d["files"].pop("lib/apply.py"),
                   "a path": lambda d: d["files"].__setitem__("lib/apply2.py", d["files"].pop("lib/apply.py")),
                   "an entry word": lambda d: d["entry"].__setitem__(2, "--all"),
                   "the entry's order": lambda d: d["entry"].reverse()}
        for name, change in changes.items():
            with self.subTest(name=name):
                defs = definitions()
                change(defs["fixer.range"])
                self.assertEqual(A.reasons(package("fixer.range"), defs, self.both), ["organ_not_listed:fixer.range"])
                # and a row of the changed definition's own hash allows it
                rows = self.both + [accept_row(own("fixer.range", defs), "fixer.range", "n")]
                self.assertEqual(A.reasons(package("fixer.range"), defs, rows), [])

    def test_a_hash_listed_for_one_organ_is_not_listed_for_another(self):
        # 26j: the list is keyed by (organ_id, definition_sha256)
        rows = [accept_row(own("fixer.range"), "some.other.organ")]
        self.assertEqual(A.reasons(package("fixer.range"), definitions(), rows), ["organ_not_listed:fixer.range"])
        # two organs of one definition share a hash and not an entry
        defs = definitions()
        defs["twin"] = definitions()["fixer.range"]
        rows = [accept_row(own("fixer.range"), "fixer.range")]
        self.assertEqual(A.reasons(package("twin"), defs, rows), ["organ_not_listed:twin"])
        self.assertEqual(A.reasons(package("fixer.range"), defs, rows), [])
        self.assertEqual(A.reasons(package("twin", "fixer.range"), defs, rows + [accept_row(own("twin", defs), "twin")]),
                         [])
        # and an organ's row of another hash does not list its definition
        self.assertEqual(A.reasons(package("fixer.range"), defs, [accept_row(own("lint.discover"), "fixer.range")]),
                         ["organ_not_listed:fixer.range"])

    def test_a_package_of_another_shape_is_unusable(self):
        bad = {"not an object": ["lint.discover"], "none": None, "no organ_ids": package(organ_ids=...),
               "organ_ids a string": package(organ_ids="lint.discover"), "organ_ids null": package(organ_ids=None),
               "an id empty": package(organ_ids=["lint.discover", ""]), "an id a number": package(organ_ids=[1]),
               "an id twice": package(organ_ids=["lint.discover", "lint.discover"]),
               "organ_ids an object": package(organ_ids={"lint.discover": 1})}
        for name, pkg in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(A.Unusable):
                    A.reasons(pkg, definitions(), self.both)
        # the fields that are not read may be anything, or absent
        self.assertEqual(A.reasons({"organ_ids": ["lint.discover"]}, definitions(), self.both), [])
        free = package("lint.discover", finding=None, diff=7, more="x")
        self.assertEqual(A.reasons(free, definitions(), self.both), [])

    def test_definitions_of_another_shape_are_unusable(self):
        for defs in (None, [], "defs", [("lint.discover", definitions()["lint.discover"])]):
            with self.subTest(defs=repr(defs)[:30]):
                with self.assertRaises(A.Unusable):
                    A.reasons(package("lint.discover"), defs, self.both)
        for name, definition in {"no files": {"entry": ["x"]}, "an empty entry": {"entry": [], "files": {}},
                                 "a path leaving the tree": {"entry": ["x"], "files": {"../x": b""}},
                                 "text for bytes": {"entry": ["x"], "files": {"x": "text"}}, "none": None}.items():
            with self.subTest(name=name):
                with self.assertRaises(A.Unusable):
                    A.reasons(package("lint.discover"), dict(definitions(), **{"lint.discover": definition}), self.both)
                # the definition of an organ the package does not name is not hashed
                defs = dict(definitions(), unnamed=definition)
                self.assertEqual(A.reasons(package("lint.discover"), defs, self.both), [])


class Request(unittest.TestCase):
    def test_exactly_organ_ids(self):
        self.assertEqual(A.request({"organ_ids": []}), [])
        self.assertEqual(A.request({"organ_ids": ["fixer.range", "lint.discover"]}), ["fixer.range", "lint.discover"])
        for doc in (None, [], ["lint.discover"], "lint.discover", {}, {"organ_ids": ["a"], "more": 1},
                    {"organs": ["a"]}, {"organ_ids": "a"}, {"organ_ids": None}, {"organ_ids": {"a": 1}},
                    {"organ_ids": ["a", ""]}, {"organ_ids": ["a", "a"]}, {"organ_ids": [1]}):
            with self.subTest(doc=repr(doc)):
                with self.assertRaises(A.Unusable):
                    A.request(doc)


class Rows(unittest.TestCase):
    def test_the_row_written(self):
        out = accept(b"", ["lint.discover", "fixer.range"])
        self.assertEqual(out.rows, [
            {"row_id": "c-7:accept:lint.discover", "ts": CYCLE["ts"], "part": "accept", "kind": "accept",
             "payload": {"organ_id": "lint.discover", "definition_sha256": own("lint.discover"), "brain_sha": SHA,
                         "evidence_run_ids": [RUN]},
             "derivation": "tool", "trust": "verified", "snapshot_id": CYCLE["snapshot_id"], "evidence_refs": []},
            {"row_id": "c-7:accept:fixer.range", "ts": CYCLE["ts"], "part": "accept", "kind": "accept",
             "payload": {"organ_id": "fixer.range", "definition_sha256": own("fixer.range"), "brain_sha": SHA,
                         "evidence_run_ids": [RUN]},
             "derivation": "tool", "trust": "verified", "snapshot_id": CYCLE["snapshot_id"], "evidence_refs": []}])
        # the rows are the ledger's: its schema takes the chained file (the row type is in its table, 26j)
        self.assertEqual(SC.ledger_reasons(out.content), [])
        self.assertEqual(A.listed(stored(out.content)),
                         {("lint.discover", own("lint.discover")), ("fixer.range", own("fixer.range"))})
        # the order named is the order written
        back = accept(b"", ["fixer.range", "lint.discover"])
        self.assertEqual([r["payload"]["organ_id"] for r in back.rows], ["fixer.range", "lint.discover"])

    def test_the_schema_refuses_an_accept_row_of_another_shape(self):
        good = chained([accept_row("1" * 64)])
        self.assertEqual(SC.ledger_reasons(good), [])
        for name, row in {"two runs": accept_row("1" * 64, evidence_run_ids=["r1", "r2"]),
                          "no run": accept_row("1" * 64, evidence_run_ids=[]),
                          "a run empty": accept_row("1" * 64, evidence_run_ids=[""]),
                          "a fifth key": accept_row("1" * 64, state="ACTIVE"),
                          "no sha": accept_row("1" * 64, brain_sha=...),
                          "another kind": dict(accept_row("1" * 64), kind="accepted")}.items():
            with self.subTest(name=name):
                self.assertNotEqual(SC.ledger_reasons(chained([row])), [])

    def test_the_sha_and_the_run_are_the_entry_s_and_the_hash_is_computed(self):
        out = accept(b"", ["lint.discover"], sha=OTHER_SHA, run="r9")
        self.assertEqual((out.rows[0]["payload"]["brain_sha"], out.rows[0]["payload"]["evidence_run_ids"]),
                         (OTHER_SHA, ["r9"]))
        changed = definitions()
        changed["lint.discover"]["entry"].append("--strict")
        out = accept(b"", ["lint.discover"], defs=changed)
        self.assertEqual(out.rows[0]["payload"]["definition_sha256"], own("lint.discover", changed))
        self.assertNotEqual(own("lint.discover", changed), own("lint.discover"))

    def test_an_entry_made_twice_writes_once(self):
        first = accept(chained([events_row()]), ["lint.discover"])
        again = accept(first.content, ["lint.discover"], cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual((again.rows, again.content), ([], first.content))
        # also at another SHA and with another run: the pair (organ, hash) is what is held
        again = accept(first.content, ["lint.discover"], cycle=dict(CYCLE, cycle_id="c-8"), sha=OTHER_SHA, run="r9")
        self.assertEqual(again.rows, [])
        # the other organ of the same entry is still written
        both = accept(first.content, ["lint.discover", "fixer.range"], cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual([r["row_id"] for r in both.rows], ["c-8:accept:fixer.range"])
        # a changed definition is another hash: a row
        changed = definitions()
        changed["lint.discover"]["files"]["adapter.py"] = b"print('lint 2')\n"
        new = accept(first.content, ["lint.discover"], defs=changed, cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual([r["payload"]["definition_sha256"] for r in new.rows], [own("lint.discover", changed)])
        self.assertEqual(A.listed(stored(new.content)), {("lint.discover", own("lint.discover")),
                                                        ("lint.discover", own("lint.discover", changed))})
        # the same hash under another organ's id is that organ's row
        twin = dict(definitions(), twin=definitions()["lint.discover"])
        out = accept(first.content, ["twin"], defs=twin, cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual([(r["payload"]["organ_id"], r["payload"]["definition_sha256"]) for r in out.rows],
                         [("twin", own("lint.discover"))])

    def test_unusable_input_gives_no_row_for_any_organ(self):
        bad_definition = dict(definitions(), broken={"entry": [], "files": {}})
        cases = {"an organ the sha does not hold": dict(organ_ids=["lint.discover", "ghost"]),
                 "a definition without a hash": dict(organ_ids=["lint.discover", "broken"], defs=bad_definition),
                 "organ ids a string": dict(organ_ids="lint.discover"), "organ ids null": dict(organ_ids=None),
                 "an id twice": dict(organ_ids=["lint.discover", "lint.discover"]),
                 "an id empty": dict(organ_ids=["lint.discover", ""]),
                 "definitions a list": dict(organ_ids=["lint.discover"], defs=[]),
                 "no sha": dict(organ_ids=["lint.discover"], sha=None),
                 "a sha of 64": dict(organ_ids=["lint.discover"], sha="a" * 64),
                 "a sha in upper case": dict(organ_ids=["lint.discover"], sha="A1" * 20),
                 "no run": dict(organ_ids=["lint.discover"], run=None),
                 "a run empty": dict(organ_ids=["lint.discover"], run=""),
                 "a run a list": dict(organ_ids=["lint.discover"], run=["r1"]),
                 "a run a number": dict(organ_ids=["lint.discover"], run=44862711957),
                 "the second organ's run": dict(organ_ids=["fixer.range", "lint.discover"], run=None)}
        for name, given in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(A.Unusable):
                    accept(b"", given.pop("organ_ids"), **given)
        for name, bad in {"a list": ["lint.discover"], "a key missing": {"brain_sha": SHA, "organ_ids": []},
                          "a fourth key": dict(entry([]), more=1), "a string": "lint.discover"}.items():
            with self.subTest(entry=name):
                with self.assertRaises(A.Unusable):
                    A.rows(CYCLE, bad, definitions(), [])
        with self.assertRaises(A.Unusable):       # a ledger whose accept row is of another shape takes no row,
            accept(chained([accept_row("1" * 64, state="ACTIVE")]), ["lint.discover"])
        with self.assertRaises(A.Unusable):       # also with no entry
            A.rows(CYCLE, None, definitions(), [accept_row("1" * 64, state="ACTIVE")])

    def test_no_entry_and_an_entry_that_writes_nothing(self):
        self.assertEqual(A.rows(CYCLE, None, definitions(), []), [])
        self.assertEqual(accept(b"", []).rows, [])       # no organ named is no row, not unusable
        # the SHA and the run are judged only when a row is written: a result without a run id enters nothing
        # and stops nothing, as long as nothing is to enter
        self.assertEqual(accept(b"", [], sha=None, run=None).rows, [])
        held = accept(b"", ["lint.discover"]).content
        self.assertEqual(accept(held, ["lint.discover"], sha=None, run=None).rows, [])


if __name__ == "__main__":
    unittest.main()
