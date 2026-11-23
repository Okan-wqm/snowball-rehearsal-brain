"""``harness.score``: findings scored against cases by match-rule v2, and the harness report (stage 1, P1 row 4;
tests 1, 6, 7, 12 and, with ``harness.stats``, 28).

Rules: asama-1/13e (match-rule v2: a finding takes at most one case, a case counts at most once in a run; the
metrics ``census``, ``recall``, ``recall_lb``, ``clean_findings``, ``verdict``), tohum/19 (three verdicts;
``x_eff = recall * G``), tohum/26m "Puanlama" (the fingerprint is read from the referee's writer's file; a
fingerprint seen again in a run is a counted re-observation; the verdict), tohum/07 and asama-1/13d (a finding's identity
is its fingerprint; an evidence reference must be in the manifest), tohum/26b (the report's fields; no float),
tohum/26a (``harness.score``: job ``yaz``, in: the findings and the snapshot, out: the report), tohum/29a (the
command line of the ``match`` vectors), asama-0/09 (the tests).

Whether one finding hits one case is ``cases.build.hit`` (the one hit rule, not written again here).

**The findings** (``sift(findings, snapshot, read, ref_max_lines)``). ``findings`` is a list, read in its order;
the answer is ``(accepted, refused, reobserved, other_runs)``: ``refused`` is ``[{index, reasons}]``, ``index`` the
finding's place in the list. First **the run**: with a snapshot (``snapshot`` the ``snapshot.make`` document), the
run scored is the objects of the list whose ``snapshot_id`` is the document's. An object with another
``snapshot_id``, or with none, is of **another run**: counted in ``other_runs`` and nothing else of it is read, so
it is no first observation of its fingerprint, no re-observation, not refused, not matched and no finding of a
clean run, wherever it stands in the list. Without a snapshot the whole list is the run. Then, over the run,
every reason that holds is listed, in this order; with ``finding_invalid`` nothing more is judged:

1. ``finding_invalid``: not an object, ``fingerprint`` not a non-empty string, or ``evidence_refs`` not a
   non-empty list of ``{path: string, line_start, line_end: integers, 1 <= line_start <= line_end}``.
2. The identity of a finding is its ``fingerprint`` string. The first finding of the run that carries a
   fingerprint is the one judged: accepted, or refused by 1, 3 and 4. Every later one of the run carrying it is a
   **re-observation**: counted in ``reobserved``, nothing else of it is read, so it is neither matched nor
   refused nor counted as a finding of a clean run (tohum/26m "Puanlama" 2), whatever its file, rule, line or
   shape, and also when the first one was refused (so a writer's row without an evidence reference, a symbol
   finding's, is one ``finding_invalid`` however many rows its fingerprint has).
3. With ``ref_max_lines`` (a positive integer, ``stage_params.evidence_ref_max_lines``; another value that is not
   ``None`` is ``Unusable``, ``ref_max_lines_invalid``): ``ref_over_max_lines``: the finding's **primary**
   reference, ``evidence_refs[0]``, spans more lines than it (a reference spans ``line_end - line_start + 1``
   lines, both ends counted; tohum/26h). No other reference is bounded in length, whatever the first one is.
4. With a snapshot (``read(path)`` the bytes of a file of the tree the document was made of, or ``None``), for
   the finding's references, each reason once: ``ref_outside_manifest``: a ``path`` that is not a file of
   the document's manifest; ``ref_hash_mismatch``: a path of the manifest whose bytes are absent or do not hash
   (sha256) to the manifest's value; ``ref_line_missing``: ``line_end`` beyond the file's last line (lines are
   counted by ``\\n``; a last line without one is a line).

A refused finding hits nothing. Without a snapshot only 1, 2 and 3 are judged.

**The match** (``match(accepted, cases, window)``): the edges are ``cases.build.hit(finding, case, window)``; the
answer is a largest set of (finding, case) pairs in which no finding and no case is twice (a maximum matching;
``{case_id: place of the finding in accepted}``), so the number of hits depends neither on the order of the
findings nor on that of the cases. Which of several largest sets is returned is fixed by the orders (cases by
``case_id``, findings as given). ``hits`` is its size.

**The cases** are a list of objects with a ``case_id`` (strings, no two the same), a ``class_level`` and a
``group`` (strings), all of one ``class_level``; else ``Unusable`` (``cases_invalid``, ``case_invalid:<index>``,
``case_id_twice:<index>``, ``cases_mixed_class``). The cases are the referee's own product
(``cases.build``); their other fields are read by the hit rule only.

**The report** (``report(findings, cases, snapshot, read, alpha, window, meta, ref_max_lines, census)``) is
``{report, hits, matched, missed_rules, uncased_rules, outside_rules, refused, counts, verdict_reason}``.

``findings`` is the bytes of a findings file of the referee's writer (``findings.write``; empty bytes are the
file with no row), and nothing else is scored: what is not ``bytes`` is ``Unusable`` (``findings_invalid``), and
so is a file ``findings.write.findings_reasons`` finds a reason in (each reason prefixed ``findings:``: a broken
chain, a row that is not the writer's row, a ``finding_id`` that is not ``f-`` and the fingerprint). Its rows in
the file's order are the list ``sift`` reads, the fingerprint as the row holds it (tohum/26m "Puanlama" 1);
the run is its rows of the document's snapshot ("the run" above): the file is one chain over every cycle of a
target, so a finding first written on an earlier snapshot has its earlier rows in other runs, and its first row
of this snapshot is the one judged. Every row of the run is read as an observation, also a row a decision
restated (a finding's ``fixed`` row carries its ``open`` row's ``snapshot_id`` and is a re-observation of it).
What the rows cannot tell is not told here: two runs on one snapshot are one run (a row carries no run id), and
an observation the writer wrote no row for (``findings.write`` rule 7: a finding still open from an earlier
snapshot, or a line equal to one already found) is in no run, so a case only it would hit is a miss
(reports/seed-101: no page gives a run its bounds in the file). ``report`` holds exactly tohum/26b's fields:

- ``snapshot_id``: the document's (``snapshot.make.check`` must accept it, else ``Unusable`` with its reasons
  prefixed ``snapshot:``); ``match_rule_version``: ``v2``; ``run_id``, ``spec_version``, ``hunter_id``,
  ``prompt_sha256``, ``rung``: ``meta``'s value under that name, ``null`` when it has none (the caller's facts;
  nothing here checks them);
- ``n``: the number of cases; ``n_groups``: the number of distinct ``group`` values (G);
- ``recall``: ``hits / n``; ``x_eff``: ``recall * G``; both exact fractions written by ``harness.stats.fixed6``;
  ``recall_lb``: ``fixed6(harness.stats.cp_lower(x_eff, G, alpha))`` with the exact ``x_eff``. With no case all
  three are ``null``; without ``alpha`` (``None``) ``recall_lb`` is ``null``;
- ``census``, for the classes the hit rule matches by tool and rule (``cases.build.DETERMINISTIC``: K0, K1,
  K2; a rule is a (``tool``, ``rule_id``) pair of strings, a case without one is ``case_invalid:<index>``):
  ``{rules_total, rules_covered, misses}``, counted over ``census``, the rule set of the target's ``census``
  vectors (tohum/26q (10); the caller's: a list or set of distinct pairs of strings, at least one, else ``Unusable`` ``census_invalid``: a set
  of no rule would be a ``PASS`` with nothing counted;
  ``loop.job`` gives ``cases.census.rules`` of the target's kind). ``rules_total`` is the size of that set;
  ``rules_covered`` its rules with a case and no case missed; ``misses`` the cases not hit, of any rule. A case
  of a rule outside the set adds nothing to ``rules_total`` or ``rules_covered`` and is a case everywhere else
  (``n``, ``recall``, ``misses``, the verdict's miss). ``null`` for any other class, and ``null`` without a set
  (``census`` ``None``: a target with no census vector has no count);
- ``clean_findings``: with no case (the snapshot is a clean one: nothing was planted), the findings counted, each
  identity once and **every refused finding too** (13e: none is left out of the count); ``null`` with cases;
- ``precision``, ``precision_lb``, ``unresolved``, ``cost_usd``, ``value_per_usd``: ``null`` (below);
- ``verdict``, with its reason beside the report (``verdict_reason``), the first that holds (tohum/26m
  "Puanlama" 3): ``UNMEASURABLE`` ``no_cases``; ``UNMEASURABLE`` ``class_without_census`` (a class outside
  ``DETERMINISTIC``); ``FAIL`` ``misses`` (a case not hit); ``UNMEASURABLE`` ``census_vector_absent`` (no rule
  set was given: never ``PASS``); ``UNMEASURABLE`` ``rule_without_case`` (a rule of the set has no case among
  these); else ``PASS`` (reason ``null``): every rule of the set has a case and every case is hit. The dev report has no floor of groups (tohum/26h): G changes no verdict.

``matched`` is ``{case_id: the finding's fingerprint}``, ``missed_rules`` the sorted ``[tool, rule_id]`` of the
rules with a missed case (``null`` for a class without census), ``uncased_rules`` those of the set with no case
and ``outside_rules`` the rules of the cases that are not in the set (tohum/26q (10): named beside the report;
both ``null`` without a set), ``counts`` ``{given, distinct, reobserved, refused, other_runs}`` over the file's rows (``given`` is the sum of the
other four). The same arguments
give the same output: nothing here reads a clock, the environment, or a file other than through ``read``.

**In the loop** (``loop.job``, ``yaz``): after the dev cases are built, ``report`` runs on them with the cycle's
findings file, ``pulled``'s snapshot document and the extracted tree; its output is ``harness`` on the target's
line.

Out of scope, stated:

- deriving a fingerprint again from the snapshot's bytes (tohum/26n: the P1 exit epoch's): the file's chain and
  row shape are checked, so a file with a valid chain whose fingerprint no ``findings.write.fingerprint`` gave
  is scored as it stands; who may write the file is its holder's rule (``brain/state``, ``loop.write_cycle``);
- ``precision``, ``precision_lb``, ``unresolved`` (they need the triage of findings that hit no case: the panel
  and the oracle, later parties), ``cost_usd``, ``value_per_usd`` (the cost of a hunter's run: P2);
- the census of K4 (tohum/26m "Puanlama" 4: stage 3's);
- which rule set is a target's (``cases.census``), and whether the library can make a case of each of its
  rules (``cases.build produce``): nothing here reads the library's catalog;
- where ``alpha``, ``window`` and ``ref_max_lines`` come from: the caller's (``harness.params.score`` reads
  them from the policy for ``loop.job``); ``stage_params.census_min_groups`` (tohum/26h: the exit sample's,
  ``exit.sample``, not built; nothing here reads it);
- the views of 13e (which of these fields an agent may see) and writing the report anywhere.

Command line, run from ``referee/`` (``CASES`` is a file holding one JSON list)::

    python -m harness.score FINDINGS CASES [--window N] [--ref-max-lines N]
    python -m harness.score FINDINGS CASES --snapshot DOCUMENT --tree DIR [--alpha A] [--census RULES]
                            [--window N] [--ref-max-lines N]

The first form (tohum/29a's ``match`` vectors) prints ``{"hits": N}``: ``FINDINGS`` holds one JSON list, ``sift``
without a snapshot, then ``match``; when a finding was refused the line also has ``refused``. It gives no report
and no verdict, the fingerprints are the list's as given, and no job runs it. The second (tohum/26a: the
findings and the snapshot in, the report out) prints ``report``'s output: ``FINDINGS`` is a findings file of the
writer, read as bytes; ``RULES`` is a file holding the census rule set as one JSON list of ``[tool, rule_id]``
(without it the report has no count and is never ``PASS``); the tree's files are read as regular files with no link on their way
(``profile.derive``'s reader). Exit 0 with the one JSON line. Exit 2 with ``{"ok": false, "error": ...}``: wrong
arguments, a file that cannot be read or is not JSON, a list that is not one, ``Unusable``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from typing import Any, Callable

import cli
from cases import build as CB
from findings import write as FW
from harness import stats
from profile import derive as D
from snapshot import make as SM

FAULT_LINE = {"ok": False, "error": "internal error"}
MATCH_RULE_VERSION = "v2"
META = ("run_id", "spec_version", "hunter_id", "prompt_sha256", "rung")
MAX = "--ref-max-lines"
NOT_MEASURED = ("precision", "precision_lb", "unresolved", "cost_usd", "value_per_usd")


class Unusable(ValueError):
    """The cases or the snapshot document cannot be scored against; ``reasons`` says why."""

    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


# ---------------------------------------------------------------- the findings

def _shaped(finding: Any) -> bool:
    if not (isinstance(finding, dict) and isinstance(finding.get("fingerprint"), str) and finding["fingerprint"]):
        return False
    refs = finding.get("evidence_refs")
    return isinstance(refs, list) and bool(refs) and all(
        isinstance(r, dict) and isinstance(r.get("path"), str) and type(r.get("line_start")) is int
        and type(r.get("line_end")) is int and 1 <= r["line_start"] <= r["line_end"] for r in refs)


def _lines(data: bytes) -> int:
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def _ref_reasons(finding: dict, snapshot: dict, read: Callable[[str], "bytes | None"]) -> list[str]:
    found = set()
    for ref in finding["evidence_refs"]:
        want = snapshot["files"].get(ref["path"])
        if want is None:
            found.add("ref_outside_manifest")
            continue
        data = read(ref["path"])
        if data is None or hashlib.sha256(data).hexdigest() != want:
            found.add("ref_hash_mismatch")
        elif ref["line_end"] > _lines(data):
            found.add("ref_line_missing")
    return [r for r in ("ref_outside_manifest", "ref_hash_mismatch", "ref_line_missing") if r in found]


def sift(findings: list, snapshot: dict | None = None, read: Callable[[str], "bytes | None"] | None = None,
         ref_max_lines: int | None = None) -> tuple[list[dict], list[dict], int, int]:
    """``(accepted, refused, reobserved, other_runs)``: see the module docstring, "The findings"; ``reobserved``
    counts the findings of the run whose fingerprint an earlier one of the run carried, ``other_runs`` the
    objects of another snapshot than the document's."""
    if ref_max_lines is not None and (type(ref_max_lines) is not int or ref_max_lines < 1):
        raise Unusable(["ref_max_lines_invalid"])
    accepted: list[dict] = []
    refused: list[dict] = []
    seen: set[str] = set()
    reobserved = other_runs = 0
    for index, finding in enumerate(findings):
        if snapshot is not None and isinstance(finding, dict) \
                and finding.get("snapshot_id") != snapshot["snapshot_id"]:
            other_runs += 1
            continue
        identity = finding.get("fingerprint") if isinstance(finding, dict) else None
        if isinstance(identity, str) and identity:
            if identity in seen:
                reobserved += 1
                continue
            seen.add(identity)
        if not _shaped(finding):
            refused.append({"index": index, "reasons": ["finding_invalid"]})
            continue
        reasons = []
        primary = finding["evidence_refs"][0]
        if ref_max_lines is not None and primary["line_end"] - primary["line_start"] + 1 > ref_max_lines:
            reasons.append("ref_over_max_lines")
        if snapshot is not None:
            reasons += _ref_reasons(finding, snapshot, read)
        if reasons:
            refused.append({"index": index, "reasons": reasons})
        else:
            accepted.append(finding)
    return accepted, refused, reobserved, other_runs


# ---------------------------------------------------------------- the cases and the match

def _checked(cases: Any) -> list[dict]:
    """The cases in ``case_id`` order, or ``Unusable`` (see "The cases")."""
    if not isinstance(cases, list):
        raise Unusable(["cases_invalid"])
    reasons, seen = [], set()
    for index, case in enumerate(cases):
        if not (isinstance(case, dict) and all(isinstance(case.get(k), str) for k in ("case_id", "class_level", "group"))):
            reasons.append("case_invalid:%d" % index)
        elif case["case_id"] in seen:
            reasons.append("case_id_twice:%d" % index)
        elif case["class_level"] in CB.DETERMINISTIC and not all(isinstance(case.get(k), str) for k in ("tool", "rule_id")):
            reasons.append("case_invalid:%d" % index)
        else:
            seen.add(case["case_id"])
    if not reasons and len({case["class_level"] for case in cases}) > 1:
        reasons.append("cases_mixed_class")
    if reasons:
        raise Unusable(reasons)
    return sorted(cases, key=lambda case: case["case_id"])


def _census(census: Any) -> "set[tuple[str, str]] | None":
    """The census rule set as pairs, ``None`` for none; else ``Unusable`` (``census_invalid``); see the module
    docstring, ``census``."""
    if census is None:
        return None
    if isinstance(census, (str, bytes, dict)) or not isinstance(census, (list, tuple, set, frozenset)):
        raise Unusable(["census_invalid"])
    pairs = [tuple(rule) if isinstance(rule, (list, tuple)) else None for rule in census]
    if not pairs or len(set(pairs)) != len(pairs) \
            or any(pair is None or len(pair) != 2 or not all(isinstance(part, str) for part in pair) for pair in pairs):
        raise Unusable(["census_invalid"])
    return set(pairs)                                                   # type: ignore[arg-type]


def match(accepted: list[dict], cases: list[dict], window: int | None = None) -> dict[str, int]:
    """A maximum matching of findings to cases over the hit rule: ``{case_id: place in accepted}``."""
    ordered = _checked(cases)
    edges = [[c for c, case in enumerate(ordered) if CB.hit(finding, case, window)] for finding in accepted]
    taken: dict[int, int] = {}   # case -> finding

    def place(start: int) -> None:
        """Give finding ``start`` a case when an augmenting path from it exists (breadth first, no recursion)."""
        came: dict[int, int] = {}   # case -> the finding it was reached from
        queue = [start]
        for finding in queue:
            for c in edges[finding]:
                if c in came:
                    continue
                came[c] = finding
                if c not in taken:
                    while True:   # walk the path back, moving each finding on it to the case it reached
                        finding = came[c]
                        before = next((k for k, f in taken.items() if f == finding), None)
                        taken[c] = finding
                        if before is None:
                            return
                        c = before
                queue.append(taken[c])

    for finding in range(len(accepted)):
        place(finding)
    return {ordered[c]["case_id"]: f for c, f in sorted(taken.items())}


# ---------------------------------------------------------------- the report

def report(findings: Any, cases: Any, snapshot: Any, read: Callable[[str], "bytes | None"],
           alpha: Fraction | None = None, window: int | None = None, meta: dict | None = None,
           ref_max_lines: int | None = None, census: Any = None) -> dict[str, Any]:
    """The harness report and what stands beside it; see the module docstring, "The report"."""
    try:
        SM.check(snapshot)
    except SM.SnapshotError as exc:
        raise Unusable(["snapshot:%s" % r for r in exc.reasons]) from None
    if not isinstance(findings, bytes):
        raise Unusable(["findings_invalid"])
    found = FW.findings_reasons(findings)
    if found:
        raise Unusable(["findings:%s" % reason for reason in found])
    rows = FW.rows(findings)
    ordered = _checked(cases)
    counted = _census(census)
    accepted, refused, reobserved, other_runs = sift(rows, snapshot, read, ref_max_lines)
    matched = match(accepted, ordered, window)
    n, groups, hits = len(ordered), len({case["group"] for case in ordered}), len(matched)
    out: dict[str, Any] = {name: (meta or {}).get(name) for name in META}
    out.update(snapshot_id=snapshot["snapshot_id"], match_rule_version=MATCH_RULE_VERSION, n=n, n_groups=groups,
               x_eff=None, recall=None, recall_lb=None, census=None, clean_findings=None)
    out.update({name: None for name in NOT_MEASURED})
    missed_rules = uncased_rules = outside_rules = None
    if n == 0:
        out["clean_findings"] = len(accepted) + len(refused)
        verdict, why = "UNMEASURABLE", "no_cases"
    else:
        recall = Fraction(hits, n)
        x_eff = recall * groups
        out.update(recall=stats.fixed6(recall), x_eff=stats.fixed6(x_eff))
        if alpha is not None:
            out["recall_lb"] = stats.fixed6(stats.cp_lower(x_eff, groups, alpha))
        if ordered[0]["class_level"] not in CB.DETERMINISTIC:
            verdict, why = "UNMEASURABLE", "class_without_census"
        else:
            rules = {(case["tool"], case["rule_id"]) for case in ordered}
            missed = {(case["tool"], case["rule_id"]) for case in ordered if case["case_id"] not in matched}
            missed_rules = [list(rule) for rule in sorted(missed)]
            if counted is not None:
                uncased_rules = [list(rule) for rule in sorted(counted - rules)]
                outside_rules = [list(rule) for rule in sorted(rules - counted)]
                out["census"] = {"rules_total": len(counted), "rules_covered": len((rules & counted) - missed),
                                 "misses": n - hits}
            if hits < n:
                verdict, why = "FAIL", "misses"
            elif counted is None:
                verdict, why = "UNMEASURABLE", "census_vector_absent"
            elif uncased_rules:
                verdict, why = "UNMEASURABLE", "rule_without_case"
            else:
                verdict, why = "PASS", None
    out["verdict"] = verdict
    return {"report": out, "hits": hits, "matched": {cid: accepted[f]["fingerprint"] for cid, f in matched.items()},
            "missed_rules": missed_rules, "uncased_rules": uncased_rules, "outside_rules": outside_rules,
            "refused": refused, "verdict_reason": why,
            "counts": {"given": len(rows), "distinct": len(accepted), "reobserved": reobserved,
                       "refused": len(refused), "other_runs": other_runs}}


# ---------------------------------------------------------------- the command

def _refuse(message: str) -> int:
    sys.stdout.write(json.dumps({"ok": False, "error": message}) + "\n")
    return 2


def _list(path: str) -> list:
    with open(path, encoding="utf-8") as fh:
        value = cli.load(fh)
    if not isinstance(value, list):
        raise Unusable(["not a JSON list"])
    return value


def _options(argv: list[str]) -> dict[str, str]:
    names = ("--snapshot", "--tree", "--alpha", "--census", "--window", "--ref-max-lines")
    if len(argv) % 2 or any(name not in names for name in argv[::2]) or len(set(argv[::2])) != len(argv) // 2:
        raise Unusable(["usage"])
    options = dict(zip(argv[::2], argv[1::2]))
    if ("--snapshot" in options) != ("--tree" in options) \
            or ("--snapshot" not in options and ("--alpha" in options or "--census" in options)):
        raise Unusable(["usage"])
    return options


def main(argv: list[str]) -> int:
    usage = ("usage: harness.score FINDINGS CASES [--snapshot DOCUMENT --tree DIR [--alpha A] [--census RULES]] "
             "[--window N] [--ref-max-lines N]")
    try:
        if len(argv) < 2:
            raise Unusable(["usage"])
        options = _options(argv[2:])
        window = int(stats._number(options["--window"], stats.INTEGER)) if "--window" in options else None
        longest = int(stats._number(options[MAX], stats.INTEGER)) if MAX in options else None
        cases = _list(argv[1])
        if "--snapshot" not in options:
            accepted, refused, _, _ = sift(_list(argv[0]), ref_max_lines=longest)
            line: dict[str, Any] = {"hits": len(match(accepted, cases, window))}
            if refused:
                line["refused"] = refused
        else:
            with open(argv[0], "rb") as fh:
                findings = fh.read()
            with open(options["--snapshot"], encoding="utf-8") as fh:
                document = cli.load(fh)
            tree = options["--tree"]
            alpha = stats._number(options["--alpha"], stats.DECIMAL) if "--alpha" in options else None
            if alpha is not None and not 0 < alpha < 1:
                raise Unusable(["usage"])
            census = _list(options["--census"]) if "--census" in options else None
            line = report(findings, cases, document, lambda path: D._read_regular(tree, path), alpha, window,
                          ref_max_lines=longest, census=census)
    except Unusable as exc:
        return _refuse(usage if exc.reasons == ["usage"] else "unusable input: %s" % cli.cause(exc))
    except (OSError, ValueError, RecursionError) as exc:
        return _refuse("unusable input: %s" % cli.cause(exc))
    sys.stdout.write(json.dumps(line, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
