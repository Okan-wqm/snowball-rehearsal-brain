"""Test 55 (tohum/26h, P1 MF9): ``gate.allowlist``, the allowlist of organ definitions and its ``accept`` rows.

What is proven, each by the test named for it:

- test 55 itself (``Test55``): the candidate of an organ whose definition hash is in no ``accept`` row is
  refused; once the row of that hash is written the same package, with the same definitions, is allowed; the
  hash the package states changes neither answer (absent, the true one, a listed one, another organ's, not a
  hash at all);
- the list (``Listed``): only ``part: accept`` rows are read; the hash is listed whichever organ's row carries
  it; an accept row of another kind or payload shape, and rows that are no list of objects, list nothing
  (``Unusable``);
- the decision (``Decision``): every named organ is judged, in the package's order; an organ the accepted SHA
  does not hold; a package naming no organ; any byte, path or entry word of the definition changes the hash
  compared; a listed hash of another organ's row allows; package and definitions of other shapes;
- the rows (``Rows``): the row's fields; the hash is computed, the SHA is the signed result's; an entry made
  twice writes once, a changed definition writes again; every unusable input writes no row for any organ;
- the file (``File``): the ledger is a chain extended byte for byte; a ledger that is no extension is a hard
  stop, also with nothing to write; a secret in a row writes nothing.

Not proven here: anything in a cycle (nothing calls the module); that ``ledger.schema.ledger_reasons`` takes an
accept row (it does not: the row type is not in ``ROW_TYPES``, which the last test of ``Rows`` states).
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
STATE = {"last_accepted_sha": SHA, "result_sha256": "d4" * 32}
RUNS = ["44862711957"]


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


def accept(ledger: bytes, organ_ids, defs=None, previous=None, cycle=CYCLE, state=STATE, runs=RUNS) -> A.Accepted:
    return A.accept(ledger, ledger if previous is None else previous, cycle, state,
                    definitions() if defs is None else defs, organ_ids, runs)


def events_row(suffix: str = "start") -> dict:
    return LE.row(CYCLE, suffix, "cycle_start", {"cycle_id": CYCLE["cycle_id"]})


def chained(rows: list[dict], onto: bytes = b"") -> bytes:
    return LA.plan_cycle(onto, onto, lambda: LC.canonical({"rows": rows})).content


def accept_row(hash_: str, organ_id: str = "lint.discover", suffix: str = "a", **over) -> dict:
    payload = {"organ_id": organ_id, "definition_sha256": hash_, "brain_sha": SHA, "evidence_run_ids": []}
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
        # the control: the row lists that hash and no other organ's
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
                                               "evidence_run_ids": []}, part="freeze")
        self.assertEqual(A.listed([]), frozenset())
        self.assertEqual(A.listed([other, freeze]), frozenset())
        self.assertEqual(A.listed([other, accept_row(one), freeze]), {one})
        self.assertEqual(A.listed([accept_row(one), accept_row(two, "fixer.range"), accept_row(one, "third")]),
                         {one, two})
        # rows of other parts are not judged: one of no shape at all beside an accept row
        self.assertEqual(A.listed([{"part": "events"}, {}, accept_row(one)]), {one})

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
               "a fifth key": accept_row(good, state="ACTIVE")}
        for name, row in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(A.Unusable):
                    A.listed([accept_row("2" * 64), row])
                with self.assertRaises(A.Unusable):       # and no candidate is judged against such a ledger
                    A.reasons(package("lint.discover"), definitions(), [accept_row(own("lint.discover")), row])
                with self.assertRaises(A.Unusable):       # also a candidate that names no organ
                    A.reasons(package(), definitions(), [row])
        self.assertEqual(A.listed([accept_row(good, evidence_run_ids=["r1", "r2"])]), {good})    # the control

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

    def test_a_hash_is_listed_whichever_organ_s_row_carries_it(self):
        rows = [accept_row(own("fixer.range"), "some.other.organ")]
        self.assertEqual(A.reasons(package("fixer.range"), definitions(), rows), [])
        # two organs of one definition share a hash and so an entry
        defs = definitions()
        defs["twin"] = definitions()["fixer.range"]
        self.assertEqual(A.reasons(package("twin"), defs, rows), [])
        self.assertEqual(A.reasons(package("lint.discover"), defs, rows), ["organ_not_listed:lint.discover"])

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


class Rows(unittest.TestCase):
    def test_the_row_written(self):
        out = accept(b"", ["lint.discover", "fixer.range"])
        self.assertEqual(out.rows, [
            {"row_id": "c-7:accept:lint.discover", "ts": CYCLE["ts"], "part": "accept", "kind": "accept",
             "payload": {"organ_id": "lint.discover", "definition_sha256": own("lint.discover"), "brain_sha": SHA,
                         "evidence_run_ids": RUNS},
             "derivation": "tool", "trust": "verified", "snapshot_id": CYCLE["snapshot_id"], "evidence_refs": []},
            {"row_id": "c-7:accept:fixer.range", "ts": CYCLE["ts"], "part": "accept", "kind": "accept",
             "payload": {"organ_id": "fixer.range", "definition_sha256": own("fixer.range"), "brain_sha": SHA,
                         "evidence_run_ids": RUNS},
             "derivation": "tool", "trust": "verified", "snapshot_id": CYCLE["snapshot_id"], "evidence_refs": []}])
        written = stored(out.content)
        self.assertEqual([{k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")} for row in written],
                         out.rows)
        for row in written:      # tohum/26's ledger row, and 26b's payload
            self.assertEqual(SC.ROW(row, "row") + SC.no_float(row, "row") + A.PAYLOAD(row["payload"], "payload"), [])
        self.assertEqual(A.listed(written), {own("lint.discover"), own("fixer.range")})
        # the order named is the order written; the runs given are the runs recorded, none included
        back = accept(b"", ["fixer.range", "lint.discover"], runs=[])
        self.assertEqual([r["payload"]["organ_id"] for r in back.rows], ["fixer.range", "lint.discover"])
        self.assertEqual([r["payload"]["evidence_run_ids"] for r in back.rows], [[], []])
        two = accept(b"", ["lint.discover"], runs=["r1", "r2"]).rows[0]["payload"]["evidence_run_ids"]
        self.assertEqual(two, ["r1", "r2"])

    def test_the_sha_is_the_signed_result_s_and_the_hash_is_computed(self):
        out = accept(b"", ["lint.discover"], state={"last_accepted_sha": OTHER_SHA})
        self.assertEqual(out.rows[0]["payload"]["brain_sha"], OTHER_SHA)
        changed = definitions()
        changed["lint.discover"]["entry"].append("--strict")
        out = accept(b"", ["lint.discover"], defs=changed)
        self.assertEqual(out.rows[0]["payload"]["definition_sha256"], own("lint.discover", changed))
        self.assertNotEqual(own("lint.discover", changed), own("lint.discover"))

    def test_an_entry_made_twice_writes_once(self):
        first = accept(chained([events_row()]), ["lint.discover"])
        again = accept(first.content, ["lint.discover"], cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual((again.rows, again.content), ([], first.content))
        # also at another SHA and with other runs: the pair (organ, hash) is what is held
        again = accept(first.content, ["lint.discover"], cycle=dict(CYCLE, cycle_id="c-8"),
                       state={"last_accepted_sha": OTHER_SHA}, runs=["r9"])
        self.assertEqual(again.rows, [])
        # the other organ of the same call is still written
        both = accept(first.content, ["lint.discover", "fixer.range"], cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual([r["row_id"] for r in both.rows], ["c-8:accept:fixer.range"])
        # a changed definition is another hash: a row
        changed = definitions()
        changed["lint.discover"]["files"]["adapter.py"] = b"print('lint 2')\n"
        new = accept(first.content, ["lint.discover"], defs=changed, cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual([r["payload"]["definition_sha256"] for r in new.rows], [own("lint.discover", changed)])
        self.assertEqual(A.listed(stored(new.content)), {own("lint.discover"), own("lint.discover", changed)})
        # the same hash under another organ's id is that organ's row
        twin = dict(definitions(), twin=definitions()["lint.discover"])
        out = accept(first.content, ["twin"], defs=twin, cycle=dict(CYCLE, cycle_id="c-8"))
        self.assertEqual([(r["payload"]["organ_id"], r["payload"]["definition_sha256"]) for r in out.rows],
                         [("twin", own("lint.discover"))])

    def test_unusable_input_writes_no_row_for_any_organ(self):
        bad_definition = dict(definitions(), broken={"entry": [], "files": {}})
        cases = {"an organ the sha does not hold": dict(organ_ids=["lint.discover", "ghost"]),
                 "a definition without a hash": dict(organ_ids=["lint.discover", "broken"], defs=bad_definition),
                 "organ ids a string": dict(organ_ids="lint.discover"), "organ ids null": dict(organ_ids=None),
                 "an id twice": dict(organ_ids=["lint.discover", "lint.discover"]),
                 "an id empty": dict(organ_ids=["lint.discover", ""]),
                 "definitions a list": dict(organ_ids=["lint.discover"], defs=[]),
                 "no state": dict(organ_ids=["lint.discover"], state=None),
                 "a state without the sha": dict(organ_ids=["lint.discover"], state={"result_sha256": "d4" * 32}),
                 "a sha of 64": dict(organ_ids=["lint.discover"], state={"last_accepted_sha": "a" * 64}),
                 "a sha in upper case": dict(organ_ids=["lint.discover"], state={"last_accepted_sha": "A1" * 20}),
                 "runs a string": dict(organ_ids=["lint.discover"], runs="r1"),
                 "runs null": dict(organ_ids=["lint.discover"], runs=None),
                 "a run empty": dict(organ_ids=["lint.discover"], runs=[""]),
                 "a run twice": dict(organ_ids=["lint.discover"], runs=["r1", "r1"]),
                 "a run a number": dict(organ_ids=["lint.discover"], runs=[44862711957])}
        for name, given in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(A.Unusable):
                    accept(b"", given.pop("organ_ids"), **given)
        # runs of another shape are refused also when every organ named is already held
        held = accept(b"", ["lint.discover"]).content
        with self.assertRaises(A.Unusable):
            accept(held, ["lint.discover"], runs="r1")
        with self.assertRaises(A.Unusable):       # and a ledger whose accept row is of another shape takes no row
            accept(chained([accept_row("1" * 64, state="ACTIVE")]), ["lint.discover"])
        self.assertEqual(accept(b"", []).rows, [])       # the control: no organ named is no row, not unusable

    def test_the_row_type_is_not_in_the_ledger_s_table_yet(self):
        # stated in the module: until the writer is wired, a ledger with an accept row is refused by the loop's
        # own reading. When this fails the row type was added: wire the writer and delete this test.
        out = accept(b"", ["lint.discover"])
        self.assertTrue(any("unknown_row_type accept/accept" in r for r in SC.ledger_reasons(out.content)))


class File(unittest.TestCase):
    def setUp(self) -> None:
        self.one = chained([events_row()])
        self.two = accept(self.one, ["lint.discover"]).content

    def test_the_ledger_is_a_chain_extended_byte_for_byte(self):
        self.assertTrue(self.two.startswith(self.one) and len(stored(self.two)) == 2)
        self.assertTrue(LC.verify_bytes(self.two, self.one)["valid"])
        rows = stored(self.two)
        self.assertEqual(rows[1]["prev_hash"], rows[0]["row_hash"])
        self.assertEqual(rows[1]["row_hash"], LC.row_hash(rows[1]))
        self.assertEqual(self.two.splitlines()[1], LC.canonical(rows[1]))

    def test_the_rows_go_onto_the_ledger_not_onto_its_previous_version(self):
        # the ledger grew since the version last verified: the rows of both stay, the new one after them
        out = accept(self.two, ["fixer.range"], previous=self.one)
        self.assertTrue(out.content.startswith(self.two))
        self.assertEqual([r["row_id"] for r in stored(out.content)],
                         ["c-7:start", "c-7:accept:lint.discover", "c-7:accept:fixer.range"])
        self.assertTrue(LC.verify_bytes(out.content, self.two)["valid"])
        self.assertEqual(accept(self.two, ["lint.discover"], previous=b"").content, self.two)

    def test_a_ledger_that_is_no_extension_is_a_hard_stop(self):
        edited = self.two.replace(b"lint.discover", b"lint.discovex")
        self.assertNotEqual(edited, self.two)
        cut = self.two[:-20]
        for name, data, previous in (("an edited row", edited, edited), ("a cut line", cut, cut),
                                     ("a row gone", self.one, self.two),
                                     ("another history", chained([events_row("other")]), self.one)):
            with self.subTest(name=name):
                for organ_ids in (["fixer.range"], ["lint.discover"], []):   # a new row, a held one, nothing
                    with self.assertRaises(LA.HardStop):
                        accept(data, organ_ids, previous=previous)
        with self.assertRaises(LA.HardStop):      # the stop comes before anything else is judged
            A.accept(edited, edited, CYCLE, None, None, None, None)

    def test_a_secret_in_a_row_writes_nothing(self):
        leak = "AKIA" + "IOSFODNN7EXAMPLE"
        defs = dict(definitions(), **{leak: definitions()["fixer.range"]})
        with self.assertRaises(LA.SecretRow):
            accept(self.one, ["fixer.range", leak], defs=defs)
        self.assertEqual(len(accept(self.one, ["fixer.range", "plain"], defs=dict(defs, plain=defs[leak])).rows), 2)


if __name__ == "__main__":
    unittest.main()
