"""The rules this brain's agents are built, run and measured by, judged against the runs.

Why (tohum/00e E697): the owner's task is that agents are set up by rules the Founder writes and keeps in the
brain, that each rule says what it expects and is tested again against the runs, and that a rule the runs
refute is rewritten. The rules are data, ``skills/agents/rules.json`` (the skill ``brain:agents`` is their
prose and the order of work); this tool judges each against the founder ledger, the definitions under
``agents/`` and, when one is readable, the session's log. It calls no model. A session tool, not in
``referee/``. From anywhere:

    python3 tests/agent_rules.py [--ledger FILE] [--log FILE | --no-log]

What it does, each rule bound by ``tests/test_agent_rules.py``:

1. **The rules file** (``load``) is a JSON object ``{"schema": "agent_rules/1", "rules": [...]}``; a rule has
   exactly ``id``, ``says``, ``expects`` (texts) and ``check``, a name of ``CHECKS``; no id twice, and every check
   of ``CHECKS`` is some rule's (a check no rule names would judge nothing). Anything else is a fault.
2. **The agents** are the files ``<name>.md`` of ``agents/`` (``files``; a directory that cannot be listed is the
   fault ``agents_unreadable``). The **runs** are read by ``agent_run.runs`` (the one reader of run rows) for
   each agent and for each other name a ledger row tags with a ref ``agent_run:<name>`` (``tagged``; an agent
   whose definition was removed keeps its runs). A run **under the rules** is a row of the form ``agent_run/2``;
   **before the rules**, of ``agent_run/1``. The session is the ledger's last ``session_start`` row.
3. **The checks**, each giving a state and what it observed:
   - ``definitions``: ``refuted`` when a file of ``agents/`` is not named ``<name>.md``, is no definition by
     ``agent_run.definition``, has a text that does not start with ``Origin. Gap: `` or holds no ``Measure: ``,
     or states no ``tools`` or one outside ``READ_ONLY``; else ``held``.
   - ``calls_are_rows``: ``not_due`` without a log. With one: every call of the tool ``Agent`` or ``Task`` in it
     (``calls``) must be of the type ``brain:<name>`` and its prompt's sha256 the ``message_sha256`` of a run row
     of ``<name>`` under the rules, written in this session, that no other call took; a call with no such row
     is listed and the rule is ``refuted``; so is every call of the tool ``SendMessage`` (a text given to an
     agent beside its packet's message has no row); else ``held`` (a log with no call holds too).
   - ``no_unjudged_left``: ``refuted`` when a finding is ``unjudged`` in a run, of an agent or of another tagged
     name, whose session is not the ledger's last ``session_start`` row (a run before any such row is of no
     session and is listed too); else ``held``.
   - ``repeats_rare``: over each agent's runs under the rules, ``not_due`` with no finding, ``refuted`` when
     ten times the findings that carry ``repeat_of`` reach the findings, else ``held``.
   - ``earns``: ``not_due`` for an agent with no run; ``refuted`` when ``agent_run.measure`` says
     ``retire_due`` or, under the rules, more findings are ``false_alarm`` than ``caught``; else ``held``.
   - ``improves``: ``not_due`` while an agent has fewer than ``AFTER_SESSIONS`` sessions under the rules; then
     ``held`` when, against its runs before the rules, the ``caught`` findings per run are more or the tokens
     per ``caught`` finding are fewer (over the runs whose tokens are a count, ``caught_tokens_known``; a side
     with no run or nothing caught shows no improvement on the measure it would divide by), else
     ``refuted``. Whether the share of repeats among findings is lower is observed beside them and decides
     nothing: ``repeats_rare`` already bounds it.
   The last three are judged for each agent (a name with runs and no definition is not judged by them: its
   definition was removed). A rule over several agents is ``refuted`` when one agent refutes it, ``not_due``
   when every agent is (or there is none), else ``held``.
4. **The log** (``calls``) is the session's transcript, JSON Lines: each line with ``type`` ``assistant`` whose
   ``message.content`` holds items of ``type`` ``tool_use`` named ``Agent`` or ``Task`` gives one call per such
   item, ``{type, sha256}`` from its ``input``'s ``subagent_type`` (null when absent) and ``prompt``; an item
   named ``SendMessage`` gives a call with both null. A line that
   is no JSON object is a fault, except a last line with no line feed (the log is being written). Without
   ``--log`` the log is the newest ``session-*.jsonl`` of ``LOGS``, or none when there is no such file or
   ``--no-log`` is given.
5. One JSON line ``{"ok", "rules": [{"id", "check", "state", "observed"}]}``; exit 0 when no rule is
   ``refuted``, 1 when one is, 2 with ``{"ok": false, "reason"}`` on a fault.

What this does not say, stated. ``held`` is that no run refuted the rule so far, not that the rule is right. The
log is what the capsule wrote: a call the log does not hold is not seen, and that a row's tokens or wall time
are the call's is not checked. The tools of ``TOOLS`` are the ones this capsule gives a session to start or
address an agent; a tool of another name that did so would not be seen. That an agent changed nothing is its
definition's tools (``READ_ONLY``), which the capsule enforces, not this tool. ``improves`` compares two folds
of rows the session wrote: of the owner's three measures (E697, condition 3) it reads true catches as
``caught`` per run and cost per useful finding as tokens per ``caught`` (the cost in money is shown to no
session); rework is not measured, and the
comparison of sessions with and without an agent (E692's third condition) is not here.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agent_run as A  # noqa: E402

SCHEMA = "agent_rules/1"
RULE_KEYS = ("id", "says", "expects", "check")
READ_ONLY = ("Read", "Grep", "Glob")
STARTS = ("Agent", "Task")
TOOLS = (*STARTS, "SendMessage")
MD = ".md"
BRAIN = "brain:"
LOGS = "/work/logs"
AFTER_SESSIONS = 5
HELD, REFUTED, NOT_DUE = "held", "refuted", "not_due"
Fault = A.Fault


def load(root: str) -> list[dict]:
    """Rule 1: the rules of ``root``'s rules file."""
    doc = A._load(os.path.join(root, A.RULES), "rules_unreadable")
    rules = doc.get("rules")
    if sorted(doc) != ["rules", "schema"] or doc["schema"] != SCHEMA or not isinstance(rules, list):
        raise Fault("rules_unreadable")
    for rule in rules:
        if not (isinstance(rule, dict) and sorted(rule) == sorted(RULE_KEYS) and all(A._text(v) for v in rule.values())
                and rule["check"] in CHECKS):
            raise Fault("bad_rule")
    if len({r["id"] for r in rules}) != len(rules):
        raise Fault("rule_id_twice")
    if {r["check"] for r in rules} != set(CHECKS):
        raise Fault("check_without_rule")
    return rules


def files(root: str) -> list[str]:
    """Rule 2: the names of ``agents/``'s files, sorted."""
    try:
        return sorted(os.listdir(os.path.join(root, A.AGENTS)))
    except OSError:
        raise Fault("agents_unreadable") from None


def tagged(data: bytes) -> tuple[str | None, list[str]]:
    """Rule 2: the ledger's last ``session_start`` row id (or none) and the names its rows tag as an agent's."""
    session, names = None, set()
    for raw in data.splitlines():
        try:
            row = json.loads(raw)
            if row["kind"] == "session_start":
                session = row["row_id"]
            refs = row["payload"]["refs"]
            names |= {r[len(A.TAG):] for r in (refs if isinstance(refs, list) else ())
                      if isinstance(r, str) and r.startswith(A.TAG)}
        except (ValueError, KeyError, TypeError):
            raise Fault("ledger_unreadable") from None
    return session, sorted(names)


def calls(log: str) -> list[dict]:
    """Rule 4: the agent calls of the session log at ``log``."""
    try:
        with open(log, "rb") as f:
            lines = f.read().split(b"\n")
    except OSError:
        raise Fault("log_unreadable") from None
    out = []
    for i, raw in enumerate(lines):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise ValueError
        except (ValueError, RecursionError):
            if i == len(lines) - 1:
                continue
            raise Fault("log_unreadable") from None
        message = row.get("message")
        content = message.get("content") if row.get("type") == "assistant" and isinstance(message, dict) else None
        for item in content if isinstance(content, list) else ():
            if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") in TOOLS:
                given = item["input"] if isinstance(item.get("input"), dict) else {}
                kind, prompt = given.get("subagent_type"), given.get("prompt")
                out.append({"type": kind if isinstance(kind, str) and item["name"] in STARTS else None,
                            "sha256": hashlib.sha256(prompt.encode("utf-8", "surrogatepass")).hexdigest()
                            if isinstance(prompt, str) and item["name"] in STARTS else None})
    return out


def definitions(ctx: dict) -> tuple[str, dict]:
    broken = []
    for file in ctx["files"]:
        name = file[:-len(MD)] if file.endswith(MD) else file
        try:
            if not file.endswith(MD):
                raise Fault("not_a_definition_file")
            agent = A.definition(ctx["root"], name)
            with open(os.path.join(ctx["root"], A.AGENTS, name + ".md"), "rb") as f:
                _, body = A.front_matter(f.read(), A.AGENT_KEYS)
            if not body.startswith("Origin. Gap: ") or "Measure: " not in body:
                raise Fault("no_origin")
            if agent["tools"] is None or not set(agent["tools"]) <= set(READ_ONLY):
                raise Fault("tools_not_read_only")
        except Fault as e:
            broken.append("%s:%s" % (name, e))
    return (REFUTED if broken else HELD), {"files": len(ctx["files"]), "broken": broken}


def calls_are_rows(ctx: dict) -> tuple[str, dict]:
    if ctx["log"] is None:
        return NOT_DUE, {"log": None}
    free = {name: [r["message_sha256"] for r in ctx["runs"][name].values()
                   if r["form"] == 2 and r["session"] is not None and r["session"] == ctx["session"]]
            for name in ctx["runs"]}
    made = calls(ctx["log"])
    unrecorded = []
    for call in made:
        name = call["type"][len(BRAIN):] if (call["type"] or "").startswith(BRAIN) else None
        if name in free and call["sha256"] in free[name]:
            free[name].remove(call["sha256"])
        else:
            unrecorded.append(call)
    return (REFUTED if unrecorded else HELD), {"calls": len(made), "unrecorded": unrecorded}


def no_unjudged_left(ctx: dict) -> tuple[str, dict]:
    left = ["%s#%d" % (row_id, f["n"]) for name in ctx["runs"] for row_id, run in ctx["runs"][name].items()
            for f in run["findings"]
            if f["verdict"] == A.UNJUDGED and (run["session"] is None or run["session"] != ctx["session"])]
    return (REFUTED if left else HELD), {"left": left}


def _each(ctx: dict, judge) -> tuple[str, dict]:
    """Rule 3's last sentence: ``judge`` over each agent's measure."""
    seen = {name: judge(A.measure(ctx["data"], name)) for name in ctx["agents"]}
    states = [state for state, _ in seen.values()]
    state = REFUTED if REFUTED in states else HELD if HELD in states else NOT_DUE
    return state, {name: {"state": s, **o} for name, (s, o) in seen.items()}


def repeats_rare(ctx: dict) -> tuple[str, dict]:
    def judge(m: dict) -> tuple[str, dict]:
        under = m["under_rules"]
        state = NOT_DUE if not under["findings"] else REFUTED if 10 * under["repeats"] >= under["findings"] else HELD
        return state, {"findings": under["findings"], "repeats": under["repeats"]}
    return _each(ctx, judge)


def earns(ctx: dict) -> tuple[str, dict]:
    def judge(m: dict) -> tuple[str, dict]:
        under = m["under_rules"]
        state = (NOT_DUE if not m["runs"] else
                 REFUTED if m["retire_due"] or under[A.FALSE_ALARM] > under[A.CAUGHT] else HELD)
        return state, {"retire_due": m["retire_due"], "caught": under[A.CAUGHT], "false_alarm": under[A.FALSE_ALARM]}
    return _each(ctx, judge)


def _lower(a: int, per_a: int, b: int, per_b: int) -> bool:
    """``a / per_a`` is lower than ``b / per_b``; false when either side has nothing to divide by."""
    return per_a > 0 and per_b > 0 and a * per_b < b * per_a


def improves(ctx: dict) -> tuple[str, dict]:
    def judge(m: dict) -> tuple[str, dict]:
        under, before = m["under_rules"], m["before_rules"]
        seen = {"sessions": under["sessions"],
                "caught_per_run_higher": _lower(before[A.CAUGHT], before["runs"], under[A.CAUGHT], under["runs"]),
                "repeats_lower": _lower(under["repeats"], under["findings"], before["repeats"], before["findings"]),
                "tokens_per_caught_lower": _lower(under["tokens"], under["caught_tokens_known"], before["tokens"],
                                                  before["caught_tokens_known"])}
        if under["sessions"] < AFTER_SESSIONS:
            return NOT_DUE, seen
        better = seen["caught_per_run_higher"] or seen["tokens_per_caught_lower"]
        return (HELD if better else REFUTED), seen
    return _each(ctx, judge)


CHECKS = {"definitions": definitions, "calls_are_rows": calls_are_rows, "no_unjudged_left": no_unjudged_left,
          "repeats_rare": repeats_rare, "earns": earns, "improves": improves}


def judge(root: str, data: bytes, log: str | None) -> list[dict]:
    """Rules 2 and 3: each rule of ``root`` with its state over ``data``, the ledger's bytes."""
    rules = load(root)
    found = files(root)
    names = [file[:-len(MD)] for file in found if file.endswith(MD)]
    session, others = tagged(data)
    ctx = {"root": root, "data": data, "log": log, "files": found, "agents": names, "session": session,
           "runs": {name: A.runs(data, name) for name in sorted({*names, *others})}}
    out = []
    for rule in rules:
        state, observed = CHECKS[rule["check"]](ctx)
        out.append({"id": rule["id"], "check": rule["check"], "state": state, "observed": observed})
    return out


def newest(logs: str) -> str | None:
    """Rule 4: the newest session log of ``logs`` by name, or none."""
    found = sorted(glob.glob(os.path.join(glob.escape(logs), "session-*.jsonl")))
    return found[-1] if found else None


def main(argv: list[str] | None = None, root: str = ROOT, logs: str = LOGS) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger", default=os.path.join(root, A.LEDGER))
    parser.add_argument("--log", default=None)
    parser.add_argument("--no-log", action="store_true")
    args = parser.parse_args(argv)
    try:
        try:
            with open(args.ledger, "rb") as f:
                data = f.read()
        except OSError:
            raise Fault("ledger_unreadable") from None
        log = None if args.no_log else args.log or newest(logs)
        rules = judge(root, data, log)
    except Fault as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    ok = all(rule["state"] != REFUTED for rule in rules)
    print(json.dumps({"ok": ok, "rules": rules}, ensure_ascii=False, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
