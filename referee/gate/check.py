"""``gate.check``: the gate's pure merge decision over recorded ``koş`` results (stage 0, MF8).

Rules: asama-0/08 criteria 3-8 and the mapped line, asama-0/09 test 35, tohum/04 (zero tests is red),
tohum/07 (merges are serial, the sentinel), tohum/08 item 3 (red control), tohum/01b (the gate re-runs;
it reads results by artifact and hash), tohum/26a (``gate.check`` calls ``secrets.scan`` on the diff,
asama-0/14 ``calls`` 2 -> 8), 26c (``control.json``: a missing ``merge_paused`` is true).

Nothing here runs a tool or a test: the ``koş`` job ran them contained (MF3) and recorded each run as
``run.contained`` does (``status``, ``exit``, ``stdout_sha256``) plus the file holding its stdout. The
gate reads every such file, checks its sha256 against the record, and decides.

The mapped line (asama-0/08), ``map_line``: a base line ``L`` of path ``P`` moves with the candidate's
hunks of the block whose pre-image is ``P``. When ``L`` is in no hunk's base range, it maps to ``L`` plus
the added minus removed lines of every hunk that ends before ``L``; when ``L`` is in a hunk's base range,
it maps to that hunk's whole candidate range. A hunk's base range is ``old_start .. old_start+old_count-1``;
a hunk with no base lines (pure insertion after line ``k``) has an empty base range and ends before ``L``
when ``k < L``. A candidate range with no lines (pure deletion) maps to nothing (``start``/``end`` null).
A path no block changes maps to itself; a rename maps to its new path; a deleted path maps to nothing.
The range follows the diff as written: its context lines are in its hunks, so with context a violation
of the rule on an unchanged line next to the change is inside the mapped range and refuses the oracle
(fail closed); with ``-U0`` the hunks hold only changed lines.
Hunk starts are checked when the diff is parsed (``gate.diffguard``, one parser for MF7 and MF8): a ``+``
start that is not the one git writes makes the diff unusable.

The decision, ``decide``. Inputs: the bundle (below), the candidate diff, ``control.json``. Each reason:

- ``artifact_hash_mismatch:<role>``: a recorded file's sha256 differs from its record. Such a file is not
  read and the decision is reject with these reasons only.
- ``run_invalid:<role>``: a lint or test run whose ``status`` is not ``ok`` (MF3: only ``ok`` is a result).
- ``red_control_green``, ``red_control_fault``: MF3's rule (``runner.contained.red_control_reasons``).
- ``merge_paused``: ``control.json`` ``merge_paused`` is not exactly ``false`` (missing is true, 26c).
- ``sentinel_pending``: some earlier merge's sentinel is not ``green``.
- ``secret_in_diff``: ``gate.secrets`` finds a match in the diff (MF2).
- ``tool_nondeterministic:base``/``:candidate``: the three lint runs of a tree are not byte-identical.
- ``tool_failed``: a lint run's exit is not 0 or 1 (ESLint: 2 is a configuration or internal failure).
- ``tool_fatal``: a lint report holds a fatal message (a parse error hides the rules, so no count holds).
- ``oracle_not_discriminating``: the base report has no active (unsuppressed) message of the finding's
  ``rule_id`` at its ``path`` and ``line``; or the candidate report does not list the mapped path; or it
  holds a message of that rule, active or suppressed, whose ``line`` is in the mapped range. A path the
  diff deletes, or a base line whose hunk leaves no candidate line, has no mapped line and so no
  violation there; ``scope_violation`` judges such a diff.
- ``inline_directive``: the candidate file holds more ESLint directive comments (``/*``/``//``, optional
  space, then ``eslint``, ``eslint-disable[-line|-next-line]``, ``eslint-enable``, ``eslint-env``,
  ``global``, ``globals`` or ``exported``, any case) than the base file: a directive can switch the rule off
  without a suppressed message.
- ``line_basis``: the base file or the candidate file starts with a byte order mark or holds a carriage
  return not followed by a line feed, U+2028 or U+2029. ESLint counts lines and fix offsets differently
  there than git does, so neither the mapped line nor the fix range can be placed.
- ``scope_violation`` (asama-0/08 criterion 4): unless all hold: the diff is one block that modifies the
  finding's path in place (no rename, copy, mode change, binary patch); it applies exactly to the base
  report's ``source`` of that file; and for one target message with a ``fix``, the candidate text keeps the
  base text before and after the fix's ``range`` (UTF-16 offsets, as ESLint gives them): whatever replaces
  the range, nothing outside it changes. The replacing text itself is judged only by the other rules.
- ``ratchet_increase``: the candidate report's total (messages plus suppressed messages, every file) is
  above the base report's.
- ``zero_tests``: no test ran (passed plus failed, plus cancelled for node); skipped and todo are not run.
- ``tests_red``: the test run's exit is not 0, or a test failed or was cancelled, or (jest) a suite failed
  or did not run, or ``success`` is not true.

Every reason found is reported (sorted, unique); the decision is ``merge`` only when there is none. The
output of an invalid or failed lint run is not read (its reasons already reject), nor is the output of a
test run that is not ``ok``; a red test run (exit not 0) is ``tests_red`` even when its output cannot be
read. Otherwise reports and test output that do not have the shape below are unusable input (exit 2, no
decision), as is a bundle of the wrong shape.

Bundle (``runs.json``), file paths relative to its directory, plain (no ``..``, not absolute)::

    {"finding": {"tool": "eslint", "rule_id": str, "path": str, "line": int},
     "lint_base": [RUN, RUN, RUN], "lint_candidate": [RUN, RUN, RUN],
     "tests": {"format": "jest-json" | "node-tap", "run": RUN},
     "red_control": {"status": str, "exit": int | null},
     "sentinels": [{"merge": str, "state": str}]}
    RUN = {"status": str, "exit": int | null, "stdout": path, "stdout_sha256": 64 hex}

Lint output is ESLint's ``json`` formatter: an array of ``{filePath, messages, suppressedMessages,
source?}``; ``filePath`` is under the container's ``/work`` (MF3) and is read relative to it.
``suppressedMessages`` is required, so a suppression is never invisible. Only ESLint is read in stage 0.
Test output is jest's ``--json`` result (``success``, ``numPassedTests``, ``numFailedTests``,
``numFailedTestSuites``, ``numRuntimeErrorTestSuites``; other runners' JSON, vitest's included, is not
read), or node's ``tap`` reporter, whose last eight lines must be its summary (``# tests``, ``# suites``, ``# pass``,
``# fail``, ``# cancelled``, ``# skipped``, ``# todo``, ``# duration_ms``): a test cannot write after it.

``hunk_covered`` (asama-0/08): every hunk is listed with ``covered: "unmeasured"`` and its reason; stage 0
has no coverage measurement and the value is never ``true``.

Not judged here: criterion 1 (``gate.diffguard``) and banned constructs, banned phrases and gross deletion
(f114); what the replacing text does beyond the directive rule (tests and the ratchet judge it); a message
whose ``line`` is before the mapped range though it spans into it; lint tools other than ESLint.

Command line, from ``referee/``; stdout is one JSON line::

    python -m gate.check map DIFF PATH LINE     {"path", "start", "end"}; exit 0, 2 unusable
    python -m gate.check decide RUNS DIFF CONTROL
        {"decision": "merge"|"reject", "ok", "reasons", "mapped", "hunk_covered"}; exit 0 merge, 1 reject,
        2 unusable input
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from typing import Any

from gate import diffguard
from gate import secrets
from runner import contained

DiffError = diffguard.DiffError
WORKDIR = contained.WORKDIR + "/"
LINT_RUNS = 3
TEST_FORMATS = ("jest-json", "node-tap")
TAP_SUMMARY = ("tests", "suites", "pass", "fail", "cancelled", "skipped", "todo", "duration_ms")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# ESLint's directive words (its directive comment parser: the comment's value, trimmed, starts with one
# of these, then white space or the end of the comment).
DIRECTIVE = re.compile(r"(?:/\*|//)\s*(?:eslint(?:-disable(?:-next-line|-line)?|-enable|-env)?|globals?|exported)"
                       r"(?=\s|\*/|\Z)", re.IGNORECASE)
LINE_BASIS = re.compile("\r(?!\n)|[\u2028\u2029]")
BOM = "\ufeff"


class Unusable(ValueError):
    """Input the gate cannot decide on (exit 2)."""


# ---------------------------------------------------------------- the mapped line

def _blocks_from(path: str, blocks: list[dict]) -> list[dict]:
    hits = [b for b in blocks if b["old"] == path and b["kind"] != "copy"]
    if len(hits) > 1:
        raise DiffError("more than one block changes %r" % path)
    if any(b["kind"] == "create" and b["new"] == path for b in blocks):
        raise DiffError("%r is created by the diff, so it has no base line" % path)
    return hits


def map_line(blocks: list[dict], path: str, line: int) -> dict:
    """The candidate place of base line ``line`` of ``path``: ``{path, start, end}``; see the docstring."""
    if type(line) is not int or line < 1:
        raise DiffError("a base line is an integer from 1")
    hits = _blocks_from(path, blocks)
    if not hits:
        return {"path": path, "start": line, "end": line}
    block = hits[0]
    if block["kind"] == "delete":
        return {"path": None, "start": None, "end": None}
    shift = 0
    for h in block["hunks"]:
        os_, oc, ns, nc = h["old_start"], h["old_count"], h["new_start"], h["new_count"]
        if oc and os_ <= line <= os_ + oc - 1:
            if nc == 0:
                return {"path": block["new"], "start": None, "end": None}
            return {"path": block["new"], "start": ns, "end": ns + nc - 1}
        if (os_ + oc - 1 if oc else os_) < line:
            shift += nc - oc
    return {"path": block["new"], "start": line + shift, "end": line + shift}


# ---------------------------------------------------------------- applying one block

def _split(text: str) -> list[tuple[str, bool]]:
    parts = text.split("\n")
    lines = [(p, True) for p in parts[:-1]]
    if parts[-1]:
        lines.append((parts[-1], False))
    return lines


def apply_block(block: dict, source: str) -> str | None:
    """The post-image of ``source`` under ``block``'s hunks, or None when a context or removed line (or its
    end of line) differs from ``source``, or the hunks reach past it."""
    base = _split(source)
    out: list[tuple[str, bool]] = []
    cursor = 0
    for h in block["hunks"]:
        start = h["old_start"] - 1 if h["old_count"] else h["old_start"]
        if start < cursor or start > len(base):
            return None
        out.extend(base[cursor:start])
        cursor = start
        for tag, text, eol in h["lines"]:
            if tag == "+":
                out.append((text, eol))
                continue
            if cursor >= len(base) or base[cursor] != (text, eol):
                return None
            if tag == " ":
                out.append((text, eol))
            cursor += 1
    out.extend(base[cursor:])
    return "".join(t + ("\n" if eol else "") for t, eol in out)


def within_fix(base: str, candidate: str, start: int, end: int) -> bool:
    """True when ``candidate`` keeps ``base`` before UTF-16 offset ``start`` and from ``end`` on."""
    b = base.encode("utf-16-le", "surrogatepass")
    c = candidate.encode("utf-16-le", "surrogatepass")
    s, e = 2 * start, 2 * end
    if not 0 <= s <= e <= len(b):
        return False
    tail = len(b) - e
    return len(c) >= s + tail and c[:s] == b[:s] and c[len(c) - tail:] == b[e:]


# ---------------------------------------------------------------- reading recorded runs

def _plain(path: Any, what: str) -> str:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path \
            or any(p in ("", ".", "..") for p in path.split("/")):
        raise Unusable("%s must be a plain relative path" % what)
    return path


def _int(value: Any, what: str, low: int = 0) -> int:
    if type(value) is not int or value < low:
        raise Unusable("%s must be an integer >= %d" % (what, low))
    return value


def _run(rec: Any, role: str) -> dict:
    if not isinstance(rec, dict) or not isinstance(rec.get("status"), str):
        raise Unusable("%s must be a run record with a status" % role)
    if rec.get("exit") is not None:
        _int(rec["exit"], role + ".exit")
    _plain(rec.get("stdout"), role + ".stdout")
    if not isinstance(rec.get("stdout_sha256"), str) or not SHA256.match(rec["stdout_sha256"]):
        raise Unusable("%s.stdout_sha256 must be 64 lowercase hex" % role)
    return rec


def _shape(bundle: Any) -> dict:
    if not isinstance(bundle, dict):
        raise Unusable("the bundle must be an object")
    f = bundle.get("finding")
    if not isinstance(f, dict) or f.get("tool") != "eslint" or not isinstance(f.get("rule_id"), str) \
            or not f["rule_id"]:
        raise Unusable("finding must be {tool: eslint, rule_id, path, line}")
    _plain(f.get("path"), "finding.path")
    _int(f.get("line"), "finding.line", 1)
    runs = {}
    for tree in ("base", "candidate"):
        key = "lint_" + tree
        recs = bundle.get(key)
        if not isinstance(recs, list) or len(recs) != LINT_RUNS:
            raise Unusable("%s must hold exactly %d runs" % (key, LINT_RUNS))
        runs[key] = [_run(r, "%s[%d]" % (key, i)) for i, r in enumerate(recs)]
    tests = bundle.get("tests")
    if not isinstance(tests, dict) or tests.get("format") not in TEST_FORMATS:
        raise Unusable("tests must be {format: %s, run}" % "|".join(TEST_FORMATS))
    runs["tests"] = [_run(tests.get("run"), "tests")]
    red = bundle.get("red_control")
    if not isinstance(red, dict):
        raise Unusable("red_control must be a run record")
    sentinels = bundle.get("sentinels")
    if not isinstance(sentinels, list) or not all(
            isinstance(s, dict) and isinstance(s.get("merge"), str) and isinstance(s.get("state"), str)
            for s in sentinels):
        raise Unusable("sentinels must be a list of {merge, state}")
    return runs


def _read_runs(runs: dict, base_dir: str) -> tuple[dict, list[str]]:
    """Every recorded stdout, read and checked against its sha256: ``({role: [bytes]}, mismatches)``."""
    data, bad = {}, []
    for key, recs in runs.items():
        data[key] = []
        for i, rec in enumerate(recs):
            role = key if key == "tests" else "%s[%d]" % (key, i)
            try:
                with open(os.path.join(base_dir, rec["stdout"]), "rb") as fh:
                    raw = fh.read()
            except OSError as exc:
                raise Unusable("cannot read %s: %s" % (role, exc)) from exc
            if hashlib.sha256(raw).hexdigest() != rec["stdout_sha256"]:
                bad.append("artifact_hash_mismatch:" + role)
            data[key].append(raw)
    return data, bad


def _message(m: Any) -> dict:
    if not isinstance(m, dict) or not (m.get("ruleId") is None or isinstance(m["ruleId"], str)):
        raise Unusable("an ESLint message must be an object with ruleId string or null")
    if m.get("fatal") is not True and type(m.get("line")) is not int:
        raise Unusable("an ESLint message must carry an integer line")
    fix = m.get("fix")
    if fix is not None:
        r = fix.get("range") if isinstance(fix, dict) else None
        if not (isinstance(r, list) and len(r) == 2 and all(type(x) is int for x in r)
                and isinstance(fix.get("text"), str)):
            raise Unusable("an ESLint fix must be {range: [int, int], text}")
    return m


def eslint_report(raw: bytes) -> dict:
    """ESLint's ``json`` output as ``{path: {messages, suppressed, source}}`` with paths relative to the
    container's work directory."""
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Unusable("lint output is not ESLint JSON: %s" % exc) from exc
    if not isinstance(doc, list):
        raise Unusable("ESLint JSON output is an array")
    files: dict[str, dict] = {}
    for entry in doc:
        if not isinstance(entry, dict) or not isinstance(entry.get("filePath"), str):
            raise Unusable("an ESLint result must have a filePath")
        fp = entry["filePath"]
        if not fp.startswith(WORKDIR):
            raise Unusable("ESLint filePath %r is not under %s" % (fp, WORKDIR))
        rel = _plain(fp[len(WORKDIR):], "ESLint filePath")
        if rel in files:
            raise Unusable("ESLint lists %r twice" % rel)
        msgs, sup = entry.get("messages"), entry.get("suppressedMessages")
        if not isinstance(msgs, list) or not isinstance(sup, list):
            raise Unusable("an ESLint result must carry messages and suppressedMessages lists")
        source = entry.get("source")
        if source is not None and not isinstance(source, str):
            raise Unusable("ESLint source must be a string")
        files[rel] = {"messages": [_message(m) for m in msgs], "suppressed": [_message(m) for m in sup],
                      "source": source}
    return files


def test_counts(raw: bytes, fmt: str) -> tuple[int, bool]:
    """``(tests run, any red)`` from a recorded test output."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Unusable("test output is not UTF-8") from exc
    if fmt == "jest-json":
        try:
            doc = json.loads(text)
        except ValueError as exc:
            raise Unusable("jest output is not one JSON document: %s" % exc) from exc
        if not isinstance(doc, dict) or type(doc.get("success")) is not bool:
            raise Unusable("jest output must be an object with a boolean success")
        n = {k: _int(doc.get(k), "jest " + k) for k in (
            "numPassedTests", "numFailedTests", "numFailedTestSuites", "numRuntimeErrorTestSuites")}
        ran = n["numPassedTests"] + n["numFailedTests"]
        red = bool(n["numFailedTests"] or n["numFailedTestSuites"] or n["numRuntimeErrorTestSuites"]
                   or not doc["success"])
        return ran, red
    lines = text.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    tail = lines[-len(TAP_SUMMARY):]
    if len(tail) != len(TAP_SUMMARY):
        raise Unusable("node tap output must end with its summary")
    n = {}
    for key, line in zip(TAP_SUMMARY, tail):
        m = re.fullmatch(r"# %s ([0-9]+)(?:\.[0-9]+)?" % key, line)
        if not m:
            raise Unusable("node tap summary line %r should be '# %s N'" % (line, key))
        n[key] = int(m.group(1))
    return n["pass"] + n["fail"] + n["cancelled"], bool(n["fail"] or n["cancelled"])


# ---------------------------------------------------------------- the decision

def _hunk_covered(blocks: list[dict]) -> list[dict]:
    return [{"path": b["new"] or b["old"], "new_start": h["new_start"], "new_count": h["new_count"],
             "covered": "unmeasured", "reason": "no coverage measurement in stage 0"}
            for b in blocks for h in b["hunks"]]


def _lint_reasons(finding: dict, blocks: list[dict], base: dict, cand: dict) -> tuple[list[str], dict | None]:
    reasons: list[str] = []
    path, line, rule = finding["path"], finding["line"], finding["rule_id"]
    for rep in (base, cand):
        if any(m.get("fatal") is True for f in rep.values() for m in f["messages"] + f["suppressed"]):
            reasons.append("tool_fatal")
            break
    total = lambda rep: sum(len(f["messages"]) + len(f["suppressed"]) for f in rep.values())  # noqa: E731
    if total(cand) > total(base):
        reasons.append("ratchet_increase")
    targets = [m for m in base.get(path, {}).get("messages", [])
               if m.get("ruleId") == rule and m.get("line") == line and m.get("fatal") is not True]
    try:
        mapped: dict | None = map_line(blocks, path, line)
    except DiffError:
        mapped = None
    if not targets or mapped is None or (mapped["path"] is not None and mapped["path"] not in cand):
        reasons.append("oracle_not_discriminating")
    elif mapped["start"] is not None:
        entry = cand[mapped["path"]]
        if any(m.get("ruleId") == rule and mapped["start"] <= m.get("line", 0) <= mapped["end"]
               for m in entry["messages"] + entry["suppressed"]):
            reasons.append("oracle_not_discriminating")
    source = base.get(path, {}).get("source")
    block = blocks[0] if len(blocks) == 1 else None
    candidate_text = None
    in_place = (block is not None and block["old"] == path and block["new"] == path
                and not block["binary"] and block["hunks"] and set(block["headers"]) <= {"index"}
                and set(block["modes"]) <= {"100644", "100755"})
    if in_place and source is not None:
        candidate_text = apply_block(block, source)
    for text in (source, candidate_text):
        if text is not None and (text.startswith(BOM) or LINE_BASIS.search(text)):
            reasons.append("line_basis")
            break
    if source is not None and candidate_text is not None \
            and len(DIRECTIVE.findall(candidate_text)) > len(DIRECTIVE.findall(source)):
        reasons.append("inline_directive")
    if candidate_text is None or "line_basis" in reasons or not any(
            m.get("fix") and within_fix(source, candidate_text, *m["fix"]["range"]) for m in targets):
        reasons.append("scope_violation")
    return reasons, mapped


def decide(bundle: Any, diff_text: str, control: Any, base_dir: str) -> dict:
    """The decision; see the module docstring. Raises ``Unusable`` or ``DiffError`` on unusable input."""
    runs = _shape(bundle)
    blocks = diffguard.parse(diff_text)
    data, mismatches = _read_runs(runs, base_dir)
    if mismatches:
        return {"decision": "reject", "ok": False, "reasons": sorted(set(mismatches)), "mapped": None,
                "hunk_covered": _hunk_covered(blocks)}
    reasons: list[str] = []
    for key, recs in runs.items():
        for i, rec in enumerate(recs):
            if rec["status"] != "ok":
                reasons.append("run_invalid:" + (key if key == "tests" else "%s[%d]" % (key, i)))
    reasons += contained.red_control_reasons(bundle["red_control"])
    if not isinstance(control, dict) or control.get("merge_paused") is not False:
        reasons.append("merge_paused")
    if any(s["state"] != "green" for s in bundle["sentinels"]):
        reasons.append("sentinel_pending")
    if secrets.scan(diff_text, "diff"):
        reasons.append("secret_in_diff")
    lint_usable = True
    for tree in ("base", "candidate"):
        outs, recs = data["lint_" + tree], runs["lint_" + tree]
        if any(o != outs[0] for o in outs):
            reasons.append("tool_nondeterministic:" + tree)
        if any(r["exit"] not in (0, 1) for r in recs):
            reasons.append("tool_failed")
        lint_usable = lint_usable and all(r["status"] == "ok" and r["exit"] in (0, 1) for r in recs)
    mapped = None
    if lint_usable:  # a failed or invalid lint run already rejects; its output is not read
        lint, mapped = _lint_reasons(bundle["finding"], blocks, eslint_report(data["lint_base"][0]),
                                     eslint_report(data["lint_candidate"][0]))
        reasons += lint
    test_run = runs["tests"][0]
    if test_run["exit"] != 0:
        reasons.append("tests_red")
    if test_run["status"] == "ok":
        try:
            ran, red = test_counts(data["tests"][0], bundle["tests"]["format"])
        except Unusable:
            if test_run["exit"] == 0:
                raise
            ran, red = None, True  # a red run need not leave a readable report; it is already rejected
        if red:
            reasons.append("tests_red")
        if ran == 0:
            reasons.append("zero_tests")
    reasons = sorted(set(reasons))
    return {"decision": "reject" if reasons else "merge", "ok": not reasons, "reasons": reasons,
            "mapped": mapped, "hunk_covered": _hunk_covered(blocks)}


# ---------------------------------------------------------------- command line

def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def _text(path: str) -> str:
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "surrogateescape")


def _json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


USAGE = "usage: python -m gate.check map DIFF PATH LINE | decide RUNS DIFF CONTROL"


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 4 and argv[0] == "map":
            if not re.fullmatch(r"[1-9][0-9]*", argv[3]):
                raise Unusable("LINE must be a positive integer")
            _emit(map_line(diffguard.parse(_text(argv[1])), argv[2], int(argv[3])))
            return 0
        if len(argv) == 4 and argv[0] == "decide":
            result = decide(_json(argv[1]), _text(argv[2]), _json(argv[3]),
                            os.path.dirname(os.path.abspath(argv[1])))
            _emit(result)
            return 0 if result["ok"] else 1
        raise Unusable(USAGE)
    except (Unusable, DiffError, ValueError, OSError, RecursionError) as exc:
        _emit({"ok": False, "error": "unusable input: %s" % exc})
        return 2
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a reason
        _emit({"ok": False, "error": "internal error: %s: %s" % (type(exc).__name__, exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
