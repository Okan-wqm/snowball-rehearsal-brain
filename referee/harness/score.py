"""``harness.score``: findings scored against cases by match-rule v2, and the harness report (stage 1, P1 row 4;
tests 1, 6, 7, 12 and, with ``harness.stats``, 28).

Rules: asama-1/13e (match-rule v2: a finding takes at most one case, a case counts at most once in a run; the
metrics ``census``, ``recall``, ``recall_lb``, ``clean_findings``, ``verdict``), tohum/19 (three verdicts;
``x_eff = recall * G``), tohum/07 and asama-1/13d (a finding's identity is its fingerprint, the line number is
not in it, the same fingerprint again is a re-observation; an evidence reference must be in the manifest),
tohum/26b (the report's fields; no float), tohum/26a (``harness.score``: job ``yaz``, in: the findings and the
snapshot, out: the report), tohum/29a (the command line of the ``match`` vectors), asama-0/09 (the tests).

Whether one finding hits one case is ``cases.build.hit`` (the one hit rule, not written again here).

**The findings** (``sift(findings, snapshot, read)``). ``findings`` is a list, read in its order; the answer is
``(accepted, refused)``: ``refused`` is ``[{index, reasons}]``, ``index`` the finding's place in the list. Every
reason that holds is listed, in this order; with ``finding_invalid`` nothing more is judged:

1. ``finding_invalid``: not an object, ``fingerprint`` not a non-empty string, or ``evidence_refs`` not a
   non-empty list of ``{path: string, line_start, line_end: integers, 1 <= line_start <= line_end}``.
2. The identity of a finding is its ``fingerprint`` string. A finding whose fingerprint an earlier accepted
   finding of the list carries is a **re-observation**: it is not counted again and nothing of it is read to
   match (so the same finding in two runs is one, and a re-observation on another line is the same one); except
   ``fingerprint_conflict``: its ``property``, ``file``, ``symbol``, ``tool`` or ``rule_id`` is not the earlier
   one's (tohum/07 derives the fingerprint from those, so one fingerprint cannot stand for two of them), and
   then it is refused, not folded.
3. With a snapshot (``snapshot`` the ``snapshot.make`` document, ``read(path)`` the bytes of a file of the tree
   the document was made of, or ``None``): ``snapshot_mismatch``: the finding's ``snapshot_id`` is not the
   document's; for its references, each reason once: ``ref_outside_manifest``: a ``path`` that is not a file of
   the document's manifest; ``ref_hash_mismatch``: a path of the manifest whose bytes are absent or do not hash
   (sha256) to the manifest's value; ``ref_line_missing``: ``line_end`` beyond the file's last line (lines are
   counted by ``\\n``; a last line without one is a line).

A refused finding hits nothing. Without a snapshot only 1 and 2 are judged.

**The match** (``match(accepted, cases, window)``): the edges are ``cases.build.hit(finding, case, window)``; the
answer is a largest set of (finding, case) pairs in which no finding and no case is twice (a maximum matching;
``{case_id: place of the finding in accepted}``), so the number of hits depends neither on the order of the
findings nor on that of the cases. Which of several largest sets is returned is fixed by the orders (cases by
``case_id``, findings as given). ``hits`` is its size.

**The cases** are a list of objects with a ``case_id`` (strings, no two the same), a ``class_level`` and a
``group`` (strings), all of one ``class_level``; else ``Unusable`` (``cases_invalid``, ``case_invalid:<index>``,
``case_id_twice:<index>``, ``cases_mixed_class``). The cases are the referee's own product
(``cases.build``); their other fields are read by the hit rule only.

**The report** (``report(findings, cases, snapshot, read, alpha, min_groups, window, meta)``) is ``{report,
hits, matched, missed_rules, refused, counts, verdict_reason}``. ``report`` holds exactly tohum/26b's fields:

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
  ``{rules_total, rules_covered, misses}``: the distinct rules of the cases, those with no case missed, and the
  cases not hit. ``null`` for any other class;
- ``clean_findings``: with no case (the snapshot is a clean one: nothing was planted), the findings counted, each
  identity once and **every refused finding too** (13e: none is left out of the count); ``null`` with cases;
- ``precision``, ``precision_lb``, ``unresolved``, ``cost_usd``, ``value_per_usd``: ``null`` (below);
- ``verdict``, with its reason beside the report (``verdict_reason``):
  ``UNMEASURABLE`` ``no_cases``; ``UNMEASURABLE`` ``class_without_census`` (a class outside ``DETERMINISTIC``);
  ``FAIL`` ``misses`` (a case not hit: 13e's gate is every rule covered and no miss); with no miss,
  ``UNMEASURABLE`` ``min_groups_unknown`` when ``min_groups`` is ``None`` and ``groups_below_min`` when G is
  under it, else ``PASS`` (reason ``null``). So ``PASS`` needs a floor the caller gave and met.

``matched`` is ``{case_id: the finding's fingerprint}``, ``missed_rules`` the sorted ``[tool, rule_id]`` of the
rules with a missed case (``null`` without census), ``counts`` ``{given, distinct, reobserved, refused}`` over
the findings. The same arguments give the same output: nothing here reads a clock, the environment, or a file
other than through ``read``.

**In the loop** (``loop.job``, ``yaz``): after the dev cases are built, ``report`` runs on them with the cycle's
findings, ``pulled``'s snapshot document and the extracted tree; its output is ``harness`` on the target's line.

Out of scope, stated:

- deriving or checking a fingerprint (tohum/07's formula; no code writes a finding yet, the registry's intake
  is a later row). So findings on different lines of one file and rule that carry one fingerprint are one
  finding here, whoever gave them that fingerprint (reports/seed-076);
- ``precision``, ``precision_lb``, ``unresolved`` (they need the triage of findings that hit no case: the panel
  and the oracle, later parties), ``cost_usd``, ``value_per_usd`` (the cost of a hunter's run: P2);
- the census of K4 (13e names it a census class; no page says what its rule is; the same report);
- whether ``min_groups`` is ``stage_params.census_min_groups`` "or all there are" (tohum/18a: the exit sample's
  judgement, ``exit.sample``), and where ``alpha``, ``min_groups`` and ``window`` come from: ``policy.json``
  holds none of ``confidence_level``, ``census_min_groups``, ``match_window_lines`` today (the same report);
- the views of 13e (which of these fields an agent may see) and writing the report anywhere.

Command line, run from ``referee/`` (``FINDINGS`` and ``CASES`` are files holding one JSON list each)::

    python -m harness.score FINDINGS CASES [--window N]
    python -m harness.score FINDINGS CASES --snapshot DOCUMENT --tree DIR [--alpha A] [--min-groups N] [--window N]

The first form (tohum/29a) prints ``{"hits": N}``: ``sift`` without a snapshot, then ``match``; when a finding
was refused the line also has ``refused``. The second (tohum/26a: the findings and the snapshot in, the report
out; one command for both pages) prints ``report``'s output, the tree's files read as regular files with no link
on their way (``profile.derive``'s reader). Exit 0 with the one JSON line. Exit 2 with ``{"ok": false, "error":
...}``: wrong arguments, a file that cannot be read or is not JSON, a list that is not one, ``Unusable``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from typing import Any, Callable

import cli
from cases import build as CB
from harness import stats
from profile import derive as D
from snapshot import make as SM

FAULT_LINE = {"ok": False, "error": "internal error"}
MATCH_RULE_VERSION = "v2"
IDENTITY_FIELDS = ("property", "file", "symbol", "tool", "rule_id")   # tohum/07: what a fingerprint is derived from
META = ("run_id", "spec_version", "hunter_id", "prompt_sha256", "rung")
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
    if finding.get("snapshot_id") != snapshot["snapshot_id"]:
        found.add("snapshot_mismatch")
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
    return [r for r in ("snapshot_mismatch", "ref_outside_manifest", "ref_hash_mismatch", "ref_line_missing")
            if r in found]


def sift(findings: list, snapshot: dict | None = None,
         read: Callable[[str], "bytes | None"] | None = None) -> tuple[list[dict], list[dict], int]:
    """``(accepted, refused, reobserved)``: see the module docstring, "The findings"; ``reobserved`` counts the
    findings folded into an earlier one."""
    accepted: list[dict] = []
    refused: list[dict] = []
    first: dict[str, dict] = {}
    reobserved = 0
    for index, finding in enumerate(findings):
        if not _shaped(finding):
            refused.append({"index": index, "reasons": ["finding_invalid"]})
            continue
        earlier = first.get(finding["fingerprint"])
        reasons = []
        if earlier is not None and any(finding.get(k) != earlier.get(k) for k in IDENTITY_FIELDS):
            reasons.append("fingerprint_conflict")
        if snapshot is not None:
            reasons += _ref_reasons(finding, snapshot, read)
        if reasons:
            refused.append({"index": index, "reasons": reasons})
        elif earlier is not None:
            reobserved += 1
        else:
            first[finding["fingerprint"]] = finding
            accepted.append(finding)
    return accepted, refused, reobserved


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
           alpha: Fraction | None = None, min_groups: int | None = None, window: int | None = None,
           meta: dict | None = None) -> dict[str, Any]:
    """The harness report and what stands beside it; see the module docstring, "The report"."""
    try:
        SM.check(snapshot)
    except SM.SnapshotError as exc:
        raise Unusable(["snapshot:%s" % r for r in exc.reasons]) from None
    if not isinstance(findings, list):
        raise Unusable(["findings_invalid"])
    ordered = _checked(cases)
    accepted, refused, reobserved = sift(findings, snapshot, read)
    matched = match(accepted, ordered, window)
    n, groups, hits = len(ordered), len({case["group"] for case in ordered}), len(matched)
    out: dict[str, Any] = {name: (meta or {}).get(name) for name in META}
    out.update(snapshot_id=snapshot["snapshot_id"], match_rule_version=MATCH_RULE_VERSION, n=n, n_groups=groups,
               x_eff=None, recall=None, recall_lb=None, census=None, clean_findings=None)
    out.update({name: None for name in NOT_MEASURED})
    missed_rules = None
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
            out["census"] = {"rules_total": len(rules), "rules_covered": len(rules - missed), "misses": n - hits}
            if hits < n:
                verdict, why = "FAIL", "misses"
            elif min_groups is None:
                verdict, why = "UNMEASURABLE", "min_groups_unknown"
            elif groups < min_groups:
                verdict, why = "UNMEASURABLE", "groups_below_min"
            else:
                verdict, why = "PASS", None
    out["verdict"] = verdict
    return {"report": out, "hits": hits, "matched": {cid: accepted[f]["fingerprint"] for cid, f in matched.items()},
            "missed_rules": missed_rules, "refused": refused, "verdict_reason": why,
            "counts": {"given": len(findings), "distinct": len(accepted), "reobserved": reobserved,
                       "refused": len(refused)}}


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
    names = ("--snapshot", "--tree", "--alpha", "--min-groups", "--window")
    if len(argv) % 2 or any(name not in names for name in argv[::2]) or len(set(argv[::2])) != len(argv) // 2:
        raise Unusable(["usage"])
    options = dict(zip(argv[::2], argv[1::2]))
    if ("--snapshot" in options) != ("--tree" in options) \
            or ("--snapshot" not in options and ("--alpha" in options or "--min-groups" in options)):
        raise Unusable(["usage"])
    return options


def main(argv: list[str]) -> int:
    usage = ("usage: harness.score FINDINGS CASES [--snapshot DOCUMENT --tree DIR [--alpha A] [--min-groups N]] "
             "[--window N]")
    try:
        if len(argv) < 2:
            raise Unusable(["usage"])
        options = _options(argv[2:])
        window = int(stats._number(options["--window"], stats.INTEGER)) if "--window" in options else None
        findings, cases = _list(argv[0]), _list(argv[1])
        if "--snapshot" not in options:
            accepted, refused, _ = sift(findings)
            line: dict[str, Any] = {"hits": len(match(accepted, cases, window))}
            if refused:
                line["refused"] = refused
        else:
            with open(options["--snapshot"], encoding="utf-8") as fh:
                document = cli.load(fh)
            tree = options["--tree"]
            alpha = stats._number(options["--alpha"], stats.DECIMAL) if "--alpha" in options else None
            if alpha is not None and not 0 < alpha < 1:
                raise Unusable(["usage"])
            floor = int(stats._number(options["--min-groups"], stats.INTEGER)) if "--min-groups" in options else None
            line = report(findings, cases, document, lambda path: D._read_regular(tree, path), alpha, floor, window)
    except Unusable as exc:
        return _refuse(usage if exc.reasons == ["usage"] else "unusable input: %s" % cli.cause(exc))
    except (OSError, ValueError, RecursionError) as exc:
        return _refuse("unusable input: %s" % cli.cause(exc))
    sys.stdout.write(json.dumps(line, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
