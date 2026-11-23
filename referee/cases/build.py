"""``cases.build``: K0 dev cases by mutation (stage 1, P1 row 3): the catalog, the proposal, the validity
judgement over the mutation's hunk, the case, the hit rule tests 2 and 4 read, and the ``produce`` command.

Rules: asama-1/13a (a known violation of the tool's rule catalog is injected into a clean file by a deterministic
operator; the tool runs on the tree with and without the mutation; lines are mapped over the mutation's hunk by
stage 0's mapped line; the case is valid when **exactly one** new (rule, line) violation arises in the mutation's
region; every step that runs the tool is ``koş``'s, selection and judgement are referee code), asama-0/08 "Eşlenmiş
satır" (``gate.check.map_line``, the one mapped line, used here and not written again), asama-1/13e and
tohum/29a (match-rule v2), tohum/26 (the ``case`` and ``finding`` fields), tohum/26a (``cases.build``: job
``çek``, out: dev cases), tohum/29za (the ``census`` vectors: the library must produce each rule of the seed's
set; the command).

**Where each part runs** (``loop.job``): ``çek`` proposes (``propose``, over the files of the clean snapshot it
makes) and ``pulled`` carries the proposal (``mutations.json``); ``koş`` applies each mutation to a copy of the
staged base worktree and runs the unit's ``lint_cmd`` three times on it (``runner.kos``, ``m/<mid>/mut.jsonl``);
``yaz`` judges (``build``) from the ``results`` artifact and puts the cases on its line. Nothing here runs a tool,
reads a clock or the network.

**The catalog** (``CATALOG``; ``rules()`` gives its distinct ``(tool, rule_id)`` pairs, sorted: the rules this
library has an operator for): each operator is ``{id, tool, rule_id, match, replace}``; it rewrites one line,
the first place ``match`` (a regular expression, ``^`` the start of a line, blanks being spaces and tabs) is
found in it, by ``replace``. Eight operators, all of ``eslint``, one a rule; a "code line" below is one whose
first non-blank text is not ``import``, ``//``, ``/*`` or ``*``:

- ``no-var``: a line that starts a ``const`` or ``let`` declaration starts a ``var`` one;
- ``prefer-const``: a ``const <name> =`` line becomes ``let``;
- ``eqeqeq``: the first ``===`` becomes ``==``;
- ``dot-notation``: on a code line, the first ``.name`` after a word character, ``)`` or ``]`` becomes
  ``["name"]``;
- ``object-shorthand``: on a code line, the first ``name.`` that starts a member chain (not after a word
  character, ``.``, ``)``, ``]`` or a quote; not ``this``, ``super``, ``import``, ``new``) becomes
  ``({ name: name }).name.``;
- ``operator-assignment``: a line that is a ``let`` or ``var`` declaration of one name ending in ``;`` gets
  `` name = name + 0;`` after it, on the same line;
- ``prefer-template``: on a code line, the first one-line ``"..."`` or ``'...'`` with no backslash that follows
  ``(``, ``[``, ``,``, ``=`` or ``:`` and is not followed by ``:`` becomes ``("..." + [])``;
- ``yoda``: the first ``name == literal`` (``===``, ``!==``, ``==``, ``!=``; the left side a name or a dotted
  chain of names not under ``typeof``; the literal a number, a one-line string with no backslash, ``true``,
  ``false`` or ``null``) becomes ``literal == name``.

An operator reads text, not syntax, and nothing here says a mutation keeps the program's meaning (13a asks for
a violation, not for an equivalent program): a match inside a comment or a string plants nothing or breaks the
line, a place whose line already violates the rule plants no new violation, and a rule the target's
configuration does not enable reports nothing. All of these are refused by the judgement below, which is the
only thing that makes a mutation a case. What is shown of each operator: on the toy fixture every census rule's
operator has a place the tool's own runs judge valid (``tests/fixtures/toy-mutations.json``, the capture of
ESLint over every place of the fixture; ``tests/test_cases.py``); on any other tree, nothing.

**The census** (tohum/29za): ``producible(tool, rule_id)`` is whether the catalog holds an operator of that
pair; the toy's seven census rules (``cases.census``) each have one, and ``eqeqeq``, which is outside the toy's
set, stays: a case of it counts as ``harness.score`` says ("outside_rules" there).

**The proposal** (``propose(files, inputs, seed, limit)``): ``files`` maps a path to its bytes, ``inputs`` are
the unit's input paths (``.`` is the whole tree). A place is (operator, path, line) where: the path is one of ``inputs`` or under one, ends
in one of ``SUFFIXES`` and is written in ``PLAIN_PATH``'s characters only (a path git would quote in a diff
header is left out); the file is UTF-8; the line ends in a newline, holds no carriage return, and the operator
changes it. The places of each operator are ordered by ``sha256(seed, operator, path, line)``, the operators by
``sha256(seed, "operator", operator)``; the proposal takes them in rounds over the operators in that order
(each operator's first place, then each one's second, ...) until ``limit`` (default ``LIMIT``, 2: each mutation
costs ``koş`` three lint runs every cycle). The operators' order is the seed's so that a catalog longer than
the limit is not always cut to its first two: which operators one proposal holds changes with the seed
(``çek`` gives the commit). One proposal still holds at most ``limit`` rules: a report with every census rule
cased needs cases kept across cycles, which nothing does today (the ledger's ``blocked`` row). Each is ``{operator, tool,
rule_id, path, line, diff}`` under its mutation id ``<operator>-<16 hex of sha256(operator, path, line, the
file's sha256)>``; ``diff`` is a git diff of one hunk that replaces that one line. Same inputs, same proposal.

**The judgement** (``judge(mutation, base_run, mut_run)``; the two run files are ``runner.kos``'s, three run
records each). Every reason that holds is listed, in this order; with any of the first four nothing more is
judged:

- ``mutation_unusable``: the mutation is not the object above, or its diff is not one in-place block of its
  ``path`` whose every hunk has a line on the mutated side;
- ``run_unusable``: a run file ``gate.check.run_file`` refuses;
- ``tool_nondeterministic``: the three records of a run file are not byte-identical;
- ``tool_unexpected``: a run's tool is not the mutation's;
- a violation of the mutated run is **new** unless a violation of the base run with the same rule and path maps,
  through the mutation's diff (``gate.check.map_line``), to a range holding its line: a violation a hunk only
  shifted is not new, and neither is one of a rule the replaced lines already violated. New violations are counted
  as distinct (rule, line) pairs. The **region** is the mutated side of the diff's hunks in ``path``.
  ``violation_none``: no new violation in the region; ``violations_many:<n>``: ``n`` > 1 of them (13a: a mutation
  that plants more than one is refused);
- ``violation_outside_region:<n>``: ``n`` new violations outside the region (in another file or on another
  line). 13a counts "in the region" and is silent on the others; refusing is the choice made here, so a case's
  tree differs from its base by exactly one violation (reports/seed-075);
- ``rule_unexpected``: the one new violation in the region is not of the mutation's ``rule_id`` (the injected
  violation is a *known* one of the catalog, 13a; e.g. a parse error where the operator meant ``no-var``;
  the same report).

Valid (no reason) gives the violation's line and the hunk that holds it.

**The case** (``build(base_sha, mutations, index, read)``: ``index`` is the ``results`` artifact's ``index.json``
parsed, ``read(path)`` the bytes of one of its files or ``None``). For each mutation, in id order:
``mutation_unusable`` (the judgement's); ``kos:<reason>`` for each reason the index's ``mutations`` entry gives a
mutation ``koş`` did not verify (``kos:<verdict>`` without reasons, ``kos:missing`` without an entry; the same
words ``loop.decide`` gives a candidate); ``artefact_hash_mismatch`` when ``base.jsonl`` or
``m/<mid>/mut.jsonl`` is absent or its sha256 is not the index's (``base_run_sha256``, the entry's
``run_sha256``): a run file is read only under its hash; then the judgement's reasons. A valid mutation is the
tohum/26 case ``{case_id: "k0-<mid>", class_level: "K0", property: "lint", provenance: "mutation", base_sha,
mutation_id, touched_paths: [{path, hunks: [{start, end}]}], tool, rule_id, validity_evidence: {kind:
"tool_diff", ref: "m/<mid>/mut.jsonl", output_sha256}, split: "dev", group}``: the hunk is the mutated side of the
hunk holding the violation (lines of the mutated file: the case's mapped line), ``group`` the directory of
``path`` (no page says what a module group is; this module's choice, the same report). Its oracle finding is
``{class_level, property, file, tool, rule_id, evidence_refs: [{path, line_start, line_end}]}`` at the
violation's line. Output ``{cases: [case], oracle: {case_id: finding}, refused: {mid: [reason]}}``.

**The hit** (``hit(finding, case, window)``, match-rule v2 for one finding and one case):

- ``class_level`` K0, K1 or K2: ``tool`` and ``rule_id`` equal (strings), and the finding's **primary**
  reference, ``evidence_refs[0]``, lies whole inside one hunk of the case's touched path of the same ``path``
  (``start <= line_start <= line_end <= end``): the mapped line (tohum/26m "Dev vaka seti" 6). So the right file
  and rule on another line is no hit, a reference wider than the hunk is none either, and no later reference
  makes a hit: not when the first one is elsewhere, and not when the first entry is no reference at all;
- any other ``class_level``: ``property`` equal, ``required_change`` a non-empty list, and one evidence reference
  (any of them, asama-1/13e) on a touched path either with the finding's ``symbol`` equal to that touched path's ``symbol`` (both strings)
  or whole inside one of its hunks widened by ``window`` lines on each side (``window``: the caller's
  ``stage_params.match_window_lines``; ``None`` leaves the symbol alone to decide).

Anything of another shape is no hit. That a finding takes at most one case and a case counts once in a run is
the scorer's rule (``harness.score.match``), not this function's; the scorer is this function's caller in the
loop (``yaz``, on the cases ``build`` gave), ``build`` itself does not call it.

Out of scope, stated: writing the dev set to ``<state_root>/cases/`` (13a). No page gives that directory's
layout, its file format or how an append-only set is carried between cycles (tohum/01b); ``harness.score``
reads the cases from ``yaz``'s line, where they are rebuilt each cycle (reports/seed-075). Also: 13a's first source (history, ``human_fix``); a mutation of more than one line or of a
file that is not UTF-8; tools other than ESLint; the exit sample (``exit.sample``).

**The command**, run from ``referee/`` (tohum/29za's ``census`` vectors)::

    python -m cases.build produce TOOL RULE

prints ``{"producible": true}`` when the catalog holds an operator of that tool and rule, ``{"producible":
false}`` otherwise, exit 0; it reads no file and no tree. Any other argument list: ``{"ok": false, "error":
usage}``, exit 2.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import sys
from typing import Any, Callable

import cli
from gate import check as GC
from gate import diffguard

TOOL = "eslint"
_CODE = r"^(?![ \t]*(?:import\b|//|/\*|\*))"      # the start of a line that begins neither an import nor a comment
_NAME = r"[A-Za-z_$][\w$]*"
CATALOG = (
    {"id": "no-var", "tool": TOOL, "rule_id": "no-var",
     "match": r"^([ \t]*)(?:const|let)([ \t]+[A-Za-z_$\[{])", "replace": r"\1var\2"},
    {"id": "prefer-const", "tool": TOOL, "rule_id": "prefer-const",
     "match": r"^([ \t]*)const([ \t]+[A-Za-z_$][\w$]*[ \t]*=)", "replace": r"\1let\2"},
    {"id": "eqeqeq", "tool": TOOL, "rule_id": "eqeqeq",
     "match": r"(?<![=!<>])===(?!=)", "replace": "=="},
    {"id": "dot-notation", "tool": TOOL, "rule_id": "dot-notation",
     "match": _CODE + r"(.*?[\w$)\]])\.(" + _NAME + ")", "replace": r'\1["\2"]'},
    {"id": "object-shorthand", "tool": TOOL, "rule_id": "object-shorthand",
     "match": _CODE + r"(.*?)(?<![\w$.)\]\"'`])(?!(?:this|super|import|new)\.)(" + _NAME + r")\.(?=[A-Za-z_$])",
     "replace": r"\1({ \2: \2 }).\2."},
    {"id": "operator-assignment", "tool": TOOL, "rule_id": "operator-assignment",
     "match": r"^([ \t]*(?:let|var)[ \t]+(" + _NAME + r")[ \t]*=.*;)[ \t]*$", "replace": r"\1 \2 = \2 + 0;"},
    {"id": "prefer-template", "tool": TOOL, "rule_id": "prefer-template",
     "match": _CODE + r"(.*?[(\[,=:][ \t]*)([\"'])((?:(?!\2)[^\\\n])*)\2(?![ \t]*:)", "replace": r"\1(\2\3\2 + [])"},
    {"id": "yoda", "tool": TOOL, "rule_id": "yoda",
     "match": r"(?<![\w$.])(?<!typeof )(" + _NAME + r"(?:\." + _NAME + r")*)([ \t]*)(===|!==|==|!=)([ \t]*)"
              r"(-?\d+(?:\.\d+)?|\"[^\"\\\n]*\"|'[^'\\\n]*'|true|false|null)(?![\w$.])",
     "replace": r"\5\2\3\4\1"},
)
SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
PLAIN_PATH = re.compile(r"[A-Za-z0-9._/@+\-\[\]()]+\Z")
LIMIT = 2
_MATCH = {op["id"]: re.compile(op["match"], re.MULTILINE) for op in CATALOG}
MUTATION_KEYS = ("operator", "tool", "rule_id", "path", "line", "diff")
DETERMINISTIC = ("K0", "K1", "K2")   # match-rule v2: the classes hit by tool, rule and mapped line
EVIDENCE_KIND = "tool_diff"


def rules() -> list[tuple[str, str]]:
    """The distinct ``(tool, rule_id)`` of the catalog's operators, sorted."""
    return sorted({(op["tool"], op["rule_id"]) for op in CATALOG})


def producible(tool: str, rule_id: str) -> bool:
    """Whether the catalog holds an operator of this tool and rule (tohum/29za, the ``census`` vectors' question)."""
    return (tool, rule_id) in rules()


def _sha(*parts: str) -> str:
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()


def run_path(mid: str) -> str:
    """Where ``runner.kos`` writes mutation ``mid``'s run file in ``results``, and a case's evidence ``ref``."""
    return "m/%s/mut.jsonl" % mid


# ---------------------------------------------------------------- the proposal

def _diff(path: str, line: int, old: str, new: str) -> str:
    return "diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n@@ -{n} +{n} @@\n-{old}\n+{new}\n".format(
        p=path, n=line, old=old, new=new)


def _places(files: dict[str, bytes], inputs: list[str]) -> dict[str, list[tuple[str, int]]]:
    """Every place ``(path, line)`` of every operator (see the module docstring), by operator id. One scan of
    each file per operator: a tree of millions of lines is read in seconds, and nothing is kept of a place but
    its path and line."""
    out: dict[str, list[tuple[str, int]]] = {op["id"]: [] for op in CATALOG}
    for path in sorted(files):
        if not (path.endswith(SUFFIXES) and PLAIN_PATH.match(path)
                and any(i == "." or path == i or path.startswith(i + "/") for i in inputs)):
            continue
        try:
            text = files[path].decode("utf-8")
        except UnicodeDecodeError:
            continue
        for op in CATALOG:
            line, at, last = 1, 0, 0
            for found in _MATCH[op["id"]].finditer(text):
                line += text.count("\n", at, found.start())
                at = found.start()
                if line == last:
                    continue        # the line's first match decided it
                last = line
                end = text.find("\n", at)
                if end >= 0 and "\r" not in text[text.rfind("\n", 0, at) + 1:end]:
                    out[op["id"]].append((path, line))      # not a last line without its newline, no carriage return
    return out


def _mutation(op: dict, path: str, line: int, data: bytes) -> tuple[str, dict]:
    """``(mutation id, mutation)`` of operator ``op`` at the place ``(path, line)`` of the file ``data``."""
    old = data.decode("utf-8").split("\n")[line - 1]
    new = _MATCH[op["id"]].sub(op["replace"], old, count=1)
    mid = "%s-%s" % (op["id"], _sha(op["id"], path, str(line), hashlib.sha256(data).hexdigest())[:16])
    return mid, {"operator": op["id"], "tool": op["tool"], "rule_id": op["rule_id"], "path": path, "line": line,
                 "diff": _diff(path, line, old, new)}


def propose(files: dict[str, bytes], inputs: list[str], seed: str, limit: int = LIMIT) -> dict[str, dict]:
    """``{mutation id: mutation}``, at most ``limit``; see the module docstring, "The proposal"."""
    places = _places(files, inputs)
    for op_id, found in places.items():
        found.sort(key=lambda p: _sha(seed, op_id, p[0], str(p[1])))
    out: dict[str, dict] = {}
    turns = sorted(CATALOG, key=lambda op: _sha(seed, "operator", op["id"]))
    for rank in range(max([len(found) for found in places.values()] + [0])):
        for op in turns:
            if rank < len(places[op["id"]]) and len(out) < limit:
                path, line = places[op["id"]][rank]
                mid, mutation = _mutation(op, path, line, files[path])
                out[mid] = mutation
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------- the judgement

def _block(mutation: Any) -> dict | None:
    """The one block of a usable mutation's diff, else ``None``."""
    if not (isinstance(mutation, dict) and set(mutation) == set(MUTATION_KEYS)
            and all(isinstance(mutation[k], str) and mutation[k] for k in MUTATION_KEYS if k != "line")
            and type(mutation["line"]) is int):
        return None
    try:
        blocks = diffguard.parse(mutation["diff"])
    except diffguard.DiffError:
        return None
    if len(blocks) != 1:
        return None
    block = blocks[0]
    if block["kind"] != "modify" or block["old"] != block["new"] or block["old"] != mutation["path"] \
            or block["binary"] or not block["hunks"] or not all(h["new_count"] for h in block["hunks"]):
        return None
    return block


def _region(block: dict) -> list[dict]:
    return [{"start": h["new_start"], "end": h["new_start"] + h["new_count"] - 1} for h in block["hunks"]]


def _new(block: dict, base: dict, mutated: dict) -> list[tuple[str, str, int]]:
    """The mutated run's new violations, distinct ``(rule_id, path, line)``, sorted."""
    carried: dict[tuple[str, str], list[list[int]]] = {}
    for v in base["violations"]:
        mapped = GC.map_line([block], v["path"], v["line"])
        if mapped:
            carried.setdefault((v["rule_id"], v["path"]), []).append(mapped)
    return sorted({(v["rule_id"], v["path"], v["line"]) for v in mutated["violations"]
                   if not any(first <= v["line"] <= last for first, last in carried.get((v["rule_id"], v["path"]), []))})


def judge(mutation: Any, base_run: bytes, mut_run: bytes) -> tuple[list[str], dict | None]:
    """``(reasons, None)``, or ``([], {line, hunk: {start, end}})`` for a valid mutation; see the module
    docstring, "The judgement"."""
    block = _block(mutation)
    if block is None:
        return ["mutation_unusable"], None
    try:
        base, base_same = GC.run_file(base_run, "base.jsonl")
        mutated, mut_same = GC.run_file(mut_run, "mut.jsonl")
    except GC.Unusable:
        return ["run_unusable"], None
    if not (base_same and mut_same):
        return ["tool_nondeterministic"], None
    if base["tool"] != mutation["tool"] or mutated["tool"] != mutation["tool"]:
        return ["tool_unexpected"], None
    region = _region(block)
    new = _new(block, base, mutated)
    inside = [(rule, line) for rule, path, line in new
              if path == mutation["path"] and any(h["start"] <= line <= h["end"] for h in region)]
    reasons = []
    if not inside:
        reasons.append("violation_none")
    elif len(inside) > 1:
        reasons.append("violations_many:%d" % len(inside))
    if len(new) > len(inside):
        reasons.append("violation_outside_region:%d" % (len(new) - len(inside)))
    if len(inside) == 1 and inside[0][0] != mutation["rule_id"]:
        reasons.append("rule_unexpected")
    if reasons:
        return reasons, None
    line = inside[0][1]
    return [], {"line": line, "hunk": next(h for h in region if h["start"] <= line <= h["end"])}


# ---------------------------------------------------------------- the hit

def _refs(finding: dict) -> list[dict | None]:
    """The finding's ``evidence_refs`` in their order, ``None`` in the place of an entry that is no reference."""
    refs = finding.get("evidence_refs")
    if not isinstance(refs, list):
        return []
    return [r if isinstance(r, dict) and isinstance(r.get("path"), str)
            and type(r.get("line_start")) is int and type(r.get("line_end")) is int
            and r["line_start"] <= r["line_end"] else None for r in refs]


def _touched(case: dict) -> list[dict]:
    touched = case.get("touched_paths")
    if not isinstance(touched, list):
        return []
    return [t for t in touched if isinstance(t, dict) and isinstance(t.get("path"), str)
            and isinstance(t.get("hunks"), list)
            and all(isinstance(h, dict) and type(h.get("start")) is int and type(h.get("end")) is int
                    for h in t["hunks"])]


def _inside(ref: dict, touched: dict, widen: int) -> bool:
    return any(h["start"] - widen <= ref["line_start"] and ref["line_end"] <= h["end"] + widen
               for h in touched["hunks"])


def hit(finding: Any, case: Any, window: int | None = None) -> bool:
    """Whether ``finding`` hits ``case`` by match-rule v2; see the module docstring, "The hit"."""
    if not (isinstance(finding, dict) and isinstance(case, dict) and isinstance(case.get("class_level"), str)):
        return False
    refs = _refs(finding)
    if case["class_level"] in DETERMINISTIC:
        primary = refs[0] if refs else None
        return all(isinstance(case.get(k), str) and finding.get(k) == case[k] for k in ("tool", "rule_id")) \
            and primary is not None \
            and any(_inside(primary, t, 0) for t in _touched(case) if t["path"] == primary["path"])
    pairs = [(r, t) for r in refs if r is not None for t in _touched(case) if r["path"] == t["path"]]
    change = finding.get("required_change")
    if not (isinstance(case.get("property"), str) and finding.get("property") == case["property"]
            and isinstance(change, list) and change):
        return False
    symbol = finding.get("symbol")
    return any((isinstance(symbol, str) and t.get("symbol") == symbol)
               or (type(window) is int and window >= 0 and _inside(r, t, window)) for r, t in pairs)


# ---------------------------------------------------------------- the case

def _kos_reasons(entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return ["kos:missing"]
    if entry.get("verdict") == "verified":
        return []
    reasons = entry.get("reasons")
    if isinstance(reasons, list) and reasons and all(isinstance(r, str) for r in reasons):
        return ["kos:%s" % r for r in reasons]
    return ["kos:%s" % entry.get("verdict")]


def _under_hash(read: Callable[[str], "bytes | None"], path: str, want: Any) -> bytes | None:
    data = read(path)
    if data is None or not isinstance(want, str) or hashlib.sha256(data).hexdigest() != want:
        return None
    return data


def _one(base_sha: str, mid: str, mutation: Any, index: dict, read: Callable[[str], "bytes | None"]) -> tuple:
    """``(reasons, case, oracle)`` of one mutation."""
    if _block(mutation) is None:
        return ["mutation_unusable"], None, None
    entries = index.get("mutations")
    entry = entries.get(mid) if isinstance(entries, dict) else None
    reasons = _kos_reasons(entry)
    if reasons:
        return reasons, None, None
    base_run = _under_hash(read, GC.RUN_FILES[0], index.get("base_run_sha256"))
    mut_run = _under_hash(read, run_path(mid), entry.get("run_sha256"))
    if base_run is None or mut_run is None:
        return ["artefact_hash_mismatch"], None, None
    reasons, found = judge(mutation, base_run, mut_run)
    if reasons:
        return reasons, None, None
    path = mutation["path"]
    case = {"case_id": "k0-%s" % mid, "class_level": "K0", "property": "lint", "provenance": "mutation",
            "base_sha": base_sha, "mutation_id": mid,
            "touched_paths": [{"path": path, "hunks": [found["hunk"]]}],
            "tool": mutation["tool"], "rule_id": mutation["rule_id"],
            "validity_evidence": {"kind": EVIDENCE_KIND, "ref": run_path(mid),
                                  "output_sha256": hashlib.sha256(mut_run).hexdigest()},
            "split": "dev", "group": posixpath.dirname(path) or "."}
    oracle = {"class_level": "K0", "property": "lint", "file": path, "tool": mutation["tool"],
              "rule_id": mutation["rule_id"],
              "evidence_refs": [{"path": path, "line_start": found["line"], "line_end": found["line"]}]}
    return [], case, oracle


def build(base_sha: str, mutations: Any, index: Any, read: Callable[[str], "bytes | None"]) -> dict[str, Any]:
    """``{cases, oracle, refused}`` of the proposed ``mutations`` (``{mid: mutation}``; any other value is no
    mutation) from ``koş``'s results; see the module docstring, "The case"."""
    out: dict[str, Any] = {"cases": [], "oracle": {}, "refused": {}}
    index = index if isinstance(index, dict) else {}
    for mid in sorted(mutations if isinstance(mutations, dict) else {}):
        reasons, case, oracle = _one(base_sha, mid, mutations[mid], index, read)
        if reasons:
            out["refused"][mid] = reasons
        else:
            out["cases"].append(case)
            out["oracle"][case["case_id"]] = oracle
    return out


# ---------------------------------------------------------------- the command

FAULT_LINE = {"ok": False, "error": "internal error"}
USAGE = "usage: cases.build produce TOOL RULE"


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "produce":
        sys.stdout.write(json.dumps({"ok": False, "error": USAGE}) + "\n")
        return 2
    sys.stdout.write(json.dumps({"producible": producible(argv[1], argv[2])}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
