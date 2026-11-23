"""The packet a brain agent reviews, the ledger row of each of its runs, and the fold that measures the agent.

Why (tohum/00e E692, E697): the first agent of this brain, ``agents/push-reviewer.md``, reads a push's diff
before prepush. The owner's conditions are that every run is a founder row carrying the agent's name, the model
and effort, the definition's sha256, the diff's sha256, the findings, tokens, cost and wall time, that the
agent is measured per finding and retired when it catches nothing (E692), and that agents are run by rules this
brain keeps and measures (E697; the rules are ``skills/agents/rules.json``, judged by ``tests/agent_rules.py``).
This tool is those records; it calls no model and starts no agent (the session does, with the Agent tool). A
session tool, not in ``referee/``. From anywhere:

    python3 tests/agent_run.py packet --agent NAME --base REV [--head REV] --out DIR
    python3 tests/agent_run.py record --packet DIR --run FILE --snapshot SHA [--ts TS] [--ledger FILE]
    python3 tests/agent_run.py record --agent NAME --run FILE --snapshot SHA [--ts TS] [--ledger FILE]
    python3 tests/agent_run.py measure --agent NAME [--ledger FILE]
    python3 tests/agent_run.py cost --agent NAME --snapshot SHA [--mirror FILE] [--ts TS] [--ledger FILE]

The rules, each bound by ``tests/test_agent_run.py``:

1. **A definition's form** (``front_matter``; tohum/24a "Ajan ve skill tanımları"): the first line is ``---``;
   up to the next line ``---`` every line that is not blank is ``<key>: <value>`` with a key of the allowed keys,
   no key twice, a value that is not empty; the text after it is not empty. A value that starts with a quote is
   refused (``quoted_value``): the capsule's loader unquotes such a value and this reader does not.
2. **An agent** (``definition``) is ``agents/<name>.md`` with the keys ``name``, ``description`` and ``model``
   and, optionally, ``tools``: ``name`` is the file's name, ``model`` is one of ``MODELS`` (tohum/00b E643; a
   definition without a model would run on a model its row could not name), ``tools`` a comma list of names
   that are not empty. Its ``sha256`` is of the file's bytes.
3. **packet** takes an agent whose file is a definition by rule 2 and that the capsule's load record
   (``--loaded``, default ``LOADED``; a JSON object whose ``agents`` is a list) lists by that name with a model
   of ``MODELS``, a list of tools and a sha256: the session can start only what was loaded, so the packet's
   ``model``, ``tools`` and ``definition_sha256`` are the record's, not the file's (a file edited in this
   session is not what runs). An agent the record does not list is ``definition_not_loaded``. It writes, into
   ``--out`` (a directory that does not exist or is empty, and is not inside the brain):
   - ``diff.patch``, the bytes of ``push_size``'s diff from ``--base`` to ``--head`` (default ``HEAD``; the same
     git arguments and the same exclusion of the founder's ledger and reports, one source), and ``paths.txt``,
     the changed paths by the same arguments with ``--name-only``, one a line;
   - ``lessons.json``: ``{row_id, summary}`` of every lesson in force in ``--ledger``, the summary whole, oldest
     first; in force is ``lesson_recheck.in_force``'s answer over the capsule's index (``--index``);
   - ``memory.json``: the findings of this agent's earlier runs (rule 6) that are not ``caught`` and carry no
     ``repeat_of``, as each was last read, in ledger order, each with ``id`` (``<the run's row id>#<n>``) in
     place of ``n``;
   - ``message.txt``: ``MESSAGE`` with the directory's absolute path, the text the session gives the agent as
     its whole prompt;
   - ``packet.json``: ``agent``, ``model``, ``tools``, ``definition_sha256``, ``base``, ``head``,
     ``diff_sha256``, ``bytes``, ``files``, ``rules_sha256`` (of the rules file's bytes), ``lessons`` and
     ``memory`` (the counts of the two lists), and ``lessons_sha256``, ``memory_sha256`` and ``message_sha256``
     (of the bytes of ``lessons.json``, ``memory.json`` and ``message.txt``).
   It prints ``packet.json``'s object with ``out``. A fault writes nothing.
4. **The run file** is a JSON object the session writes after the run, with exactly the keys ``invoked_as``
   (text: the agent type the Agent tool was given), ``model_served`` (text: the model as the session saw it
   served, or the alias when it saw none), ``effort`` (text), ``tokens`` (a count), ``cost_usd_micros`` (null:
   a run's cost is a fact of its session's end and comes by rule 7, tohum/26o; a count is the fault
   ``cost_not_null``), ``wall_ms`` (a count), ``not_measured`` (text: why the cost is not here) and
   ``findings``. A finding has exactly ``n`` (the integers 1, 2, ... in order), ``class``, ``claim`` (texts),
   ``ref`` (text or null), ``verdict`` (one of ``VERDICTS2``), ``evidence`` (text or null; text unless the
   verdict is ``unjudged``: for ``caught`` the test that was red before the repair and green after, or the
   referee's or rival's confirmation; for ``false_alarm`` the reason; for ``carried`` why it is true and not
   repaired here), ``carried_in`` (for ``carried``: ``reports/<file>.json`` or a row id ``f<n>``, the place that
   keeps it open; null for any other verdict) and ``repeat_of`` (null, or ``f<n>#<m>``: the earlier finding
   this one says again). A count is an integer of 0 or more, not a boolean; a text is a string that is not
   empty. An **amending file** has exactly ``amends`` (``f<n>``) and ``findings``.
5. **record** with ``--packet`` reads ``packet.json`` (exactly rule 3's keys) and the run file, refuses when
   the sha256 of ``diff.patch``, ``lessons.json``, ``memory.json`` or ``message.txt`` is no longer the packet's
   (``<file's name before the dot>_changed``), and appends one row through ``ledger.founder``
   (``next_row`` and ``append``, the one writer): kind ``build``, the defaults ``llm_inference`` and
   ``inferred`` (the verdicts are the session's judgement), refs ``agents/<name>.md`` and ``agent_run:<name>``,
   and the summary ``agent_run/2 `` followed by one JSON object: the packet's fields without ``tools`` and the
   run file's fields (no key is of both, so ``model`` is the definition's and ``model_served`` the run's). With
   ``--agent`` it reads an amending file and appends a row of the same kind and refs whose object is ``agent``,
   ``amends`` and ``findings``: a later reading of the findings of the run it names (the rival's or the
   referee's answer comes after the push); it is refused unless ``amends`` names a run of this agent that rule
   6 reads in the ledger (``amends_no_run``) and the findings are as many as that run's
   (``amends_other_findings``). Both or neither of ``--packet`` and ``--agent`` is ``packet_or_agent``. Either
   row is refused when a finding's ``carried_in`` names a report that is no file under the brain's root or a
   row id the ledger does not hold (``carried_in_absent``), or its ``repeat_of`` names no finding of a run of
   this agent that is in the ledger before the run the findings are of (``repeat_of_no_finding``). A ledger
   whose run rows rule 6 cannot read takes no further row. A row the writer refuses and a ledger it cannot
   extend are faults; the file is left as it was.
6. **measure** folds the ledger's rows that carry the ref ``agent_run:<name>``, in file order. Such a row whose
   summary is not a form below is a fault, never skipped. ``agent_run/2 `` and one JSON object: either
   ``agent``, ``amends`` and ``findings`` by rule 4, or every field of rule 3's packet but ``tools`` and beside
   them a run file by rule 4 and no other key, or a cost row by rule 7. ``agent_run/1 `` and one JSON object, the form
   of the runs before
   the rules, still read and no longer written: the packet's first nine fields but ``tools``, and beside them
   the run file's keys with ``effort`` and ``tokens`` null too under a ``not_measured``, findings without
   ``carried_in`` and ``repeat_of`` and with a verdict of ``VERDICTS``, and optionally ``amends`` (such a row
   amends and is no run). In each form ``agent`` is ``<name>``; the packet fields' other values are not judged.
   An amending row replaces the findings of the earlier run row it names; naming anything else is a fault. A
   run's ``cost_usd_micros`` is null until a cost row names it: the count a run row of the form ``agent_run/1``
   may carry is the session's own and is not read. A
   cost row gives the earlier run row it names (of either form) its ``cost_usd_micros`` and its floor, the last
   such row of a run standing; naming anything else is a fault (``cost_no_run:<row id>``). The answer:
   ``runs``; ``sessions``, the distinct ``session_start`` rows last seen before each run (a run before
   any such row counts as one more); ``findings`` and the count of each verdict; ``repeats``, the findings that
   carry a ``repeat_of``; the sums ``tokens``, ``cost_usd_micros`` and ``wall_ms`` over the runs that carry a
   count (the cost: from a cost row), with ``tokens_unknown`` and ``cost_unknown`` the runs that carry null,
   and ``caught_tokens_known`` and
   ``caught_cost_known`` the ``caught`` findings of the runs whose tokens, and whose cost, are a count;
   ``cost_floor_usd_micros``, the sum of ``cost_floor_usd_micros`` over the runs whose cost is null and whose
   cost row carries a floor that is a count, and ``cost_floor_runs``, how many those are; ``before_rules`` and
   ``under_rules``, the same counts and sums over the runs of the form ``agent_run/1`` and of ``agent_run/2``
   alone; ``session_cost_usd_micros``, the lower median of what the ledger's ``cost`` rows say a session cost
   (a row of the kind ``cost`` whose summary begins ``session <stamp>: exit <..>, <..> min, turns <..>,
   cost_usd_micros <count>,``, the launcher's form, tohum/26o; a row that says anything else there, ``unknown``
   too, states none), or null when none states one, and ``session_costs``, how many do; ``cost_over_gain``:
   true when a session's cost is known and ``cost_usd_micros`` plus ``cost_floor_usd_micros`` is more than
   ``caught`` times it; and ``retire_due``: true when ``sessions`` is at least ``RETIRE_AFTER`` and ``caught``
   is 0 or ``cost_over_gain`` is true (E692's fourth condition, tohum/00e: a rejected push costs about a
   session, so a ``caught`` finding saved one at most, and an agent whose least possible cost is more than the
   most it can have saved costs more than it saves).
7. **cost** reads what a run cost from the launcher's mirror (tohum/26o "Ajan koşusunun maliyeti": the facts of
   a session's end, readable from the next session on) and writes it beside the run, naming the mirror, the
   session's stamp and the call's ``tool_use_id`` as that page asks.
   - **The mirror** (``--mirror``, default ``MIRROR``) is a JSON object whose ``stamp`` is a stamp
     (``YYYYMMDDTHHMMSSZ``, a real time: the session it was written for) and whose ``delegation.sessions`` is a
     list of objects, each with a stamp earlier than that one, no stamp twice, and ``runs``, a list of objects;
     anything else is ``mirror_unreadable``.
   - **A run's session** is the mirror's session with the latest stamp not after the ``ts`` of the run's row,
     when that ``ts`` is a time written ``YYYY-MM-DDTHH:MM:SSZ`` and before the mirror's own stamp; a run with
     no such session is ``session_not_in_mirror`` (the session reading the mirror is never in it).
   - **A run's call** is the entry of that session's ``runs`` whose ``wall_ms`` is the integer the run's row
     carries and, for a run under the rules, whose ``subagent_type`` is ``brain:<name>``. No such entry is
     ``no_call``; more than one, or another run of this agent with the same session and ``wall_ms``, is
     ``ambiguous``. Neither is guessed.
   - **A cost row** is appended for each run that has a call, in the runs' order, through the one writer, with
     kind, defaults and refs as rule 5's: ``agent_run/2 `` and one JSON object with exactly ``agent``,
     ``cost_of`` (the run's row id), ``source`` (``mirror.json``), ``stamp``, and from the entry
     ``tool_use_id`` (a text that starts with ``toolu_``), ``subagent_type`` and ``effort`` (text or null),
     ``model`` (text: the model the run's messages were served by), ``usage`` (the entry's ``tokens``: exactly
     ``TOKEN_KINDS``, each a count or null; under another name because the ledger's row scan,
     ``gate/secrets.py``, reads eight or more characters under a key named like a secret as one, whatever
     their shape), ``cost_usd_micros`` and ``cost_floor_usd_micros`` (a count or null), ``cost_basis`` and
     ``not_measured`` (text or null; text when ``cost_usd_micros`` is null). A call that does not give such
     an object is ``mirror_unreadable``, and then no row is written; an entry that is no run's call is not
     judged. A run whose last cost row already is that
     object gets none (``unchanged``), so a second run of the command writes nothing.
   - It prints ``recorded`` (the new rows' ids), ``unchanged`` (a count) and ``unpaired`` (the reason of each
     run without a call, by row id). Each row is appended alone: a fault of the writer stops the command and the
     rows appended before it stay.
8. One JSON line; exit 0, or 2 with ``{"ok": false, "reason"}`` on a fault.

What this does not say, stated. A cost is the launcher's figure, derived from its price table and not the
CLI's (tohum/26o); rule 7 copies it and computes none. A run is tied to its call by its row's ``ts`` and
``wall_ms``, both written by the session: a row written in a later session than its run, or with another
``wall_ms`` than the call's notification, finds no call and stays unknown; a run before the rules is tied
without its agent type, so another agent's call of the same session and wall time would be taken for it. The
mirror holds the newest 20 sessions: a run not costed while its session is in it stays unknown. A row is what
the session wrote: nothing here checks that the agent ran, that a
count is the true one (and a run whose ``tokens`` is a count of eight or more digits is refused by the ledger's
row scan for the same reason a cost row says ``usage``: ``row_refused:row_scan:secret-assignment``; the runs so
far are of six digits), that a ``caught`` finding's test exists or was ever red, that a ``carried`` finding's
place speaks of it, or that a ``repeat_of`` is the same claim. That the agent was given ``message.txt`` and
nothing else is read from the session's log by ``tests/agent_rules.py``, not here. The diff is ``push_size``'s,
not the referee's prompt (which is ``--binary`` and adds pages). The packet is of a diff: an agent whose task
is no diff has no packet form yet. ``retire_due`` reads the owner's fourth condition from one side only: it is true
when the
agent cannot have earned its cost and says nothing of an agent below that line, since what a ``caught`` finding
saved is measured nowhere (not every one would have been a rejection); the cost it weighs leaves out every run
with neither a cost nor a floor, the wall time is not weighed, and a session's cost is the median over every
session of the ledger, of any length and price. The capsule's loader
(``brain_defs.py``) is the judge of what a session loads; rules 1 and 2 are tohum/24a's sentence and this
brain's narrower choice of models, and a definition that passes here can still be dropped there (its limits on
length and its name pattern are not copied).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

import lesson_recheck as LR  # noqa: E402
import push_size as PS  # noqa: E402
from ledger import founder as F  # noqa: E402

AGENTS = "agents"
LEDGER = "founder-ledger.jsonl"
AGENT_KEYS = ("name", "description", "tools", "model")
SKILL_KEYS = ("name", "description")
MODELS = ("sonnet", "opus")
CAUGHT, FALSE_ALARM, UNJUDGED = "caught", "false_alarm", "unjudged"
VERDICTS = (CAUGHT, FALSE_ALARM, UNJUDGED)
CARRIED = "carried"
VERDICTS2 = (*VERDICTS, CARRIED)
FORM = "agent_run/1 "
FORM2 = "agent_run/2 "
TAG = "agent_run:"
RETIRE_AFTER = 5
SESSION_COST = re.compile(r"session \d{8}T\d{6}Z: exit [^,]+, [^,]+ min, turns [^,]+, "
                          r"cost_usd_micros (\d+),")
FENCE = "---"
PACKET_KEYS = ("agent", "model", "tools", "definition_sha256", "base", "head", "diff_sha256", "bytes", "files")
RUN_KEYS = ("invoked_as", "model_served", "effort", "tokens", "cost_usd_micros", "wall_ms", "not_measured", "findings")
MAY_BE_UNKNOWN = ("effort", "tokens", "cost_usd_micros")
MAY_BE_SUMMED = ("tokens", "cost_usd_micros")
FINDING_KEYS = ("n", "class", "claim", "ref", "verdict", "evidence")
ROW_ID = re.compile(r"f[1-9][0-9]*")
PACKET_KEYS2 = (*PACKET_KEYS, "rules_sha256", "lessons", "lessons_sha256", "memory", "memory_sha256",
                "message_sha256")
PINNED = (("diff.patch", "diff_sha256"), ("lessons.json", "lessons_sha256"), ("memory.json", "memory_sha256"),
          ("message.txt", "message_sha256"))
FINDING_KEYS2 = (*FINDING_KEYS, "carried_in", "repeat_of")
AMEND_KEYS = ("agent", "amends", "findings")
REPORT = re.compile(r"reports/[^/]+\.json")
FINDING_ID = re.compile(r"(f[1-9][0-9]*)#([1-9][0-9]*)")
MIRROR = "/work/logs/mirror.json"
SOURCE = "mirror.json"
STAMP = "%Y%m%dT%H%M%SZ"
ROW_TS = "%Y-%m-%dT%H:%M:%SZ"
CALL_ID = "toolu_"
BRAIN = "brain:"
TOKEN_KINDS = ("in", "cache_read", "cache_write_5m", "cache_write_1h", "out")
COPIED = ("tool_use_id", "subagent_type", "model", "effort", "cost_usd_micros", "cost_floor_usd_micros",
          "cost_basis", "not_measured")
COST_KEYS = ("agent", "cost_of", "source", "stamp", "usage", *COPIED)
RULES = "skills/agents/rules.json"
LOADED = "/work/logs/brain-definitions.json"
GIVEN = ("diff.patch", "paths.txt", "packet.json", "lessons.json", "memory.json")
MESSAGE = """%s

That directory is your packet. It holds:
- diff.patch: the whole change you review, from the last accepted commit to the commit named in packet.json.
- paths.txt: the changed paths, one a line.
- packet.json: the base and head commits and the sizes.
- lessons.json: every lesson in force of this brain's ledger, whole. A lesson is a hint about a class of mistake \
made here before, not evidence: look for its class in the change.
- memory.json: the findings of your earlier runs that were refused (false_alarm, with the reason), that are true \
and kept open elsewhere (carried, with the place), or that are not judged yet. Do not report one of them again. Only \
when this change itself makes one newly wrong, report it and give its "id" from memory.json as "repeat_of" in the \
finding."""


class Fault(Exception):
    """A definition, a packet, a run file or the ledger cannot be used; the message is the reason."""


def front_matter(data: bytes, keys: tuple[str, ...]) -> tuple[dict[str, str], str]:
    """Rule 1: the fields and the text after them."""
    try:
        lines = data.decode("utf-8").replace("\r\n", "\n").split("\n")
    except UnicodeDecodeError:
        raise Fault("not_utf8") from None
    if lines[0] != FENCE or FENCE not in lines[1:]:
        raise Fault("no_front_matter")
    end = lines.index(FENCE, 1)
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, sep, value = line.partition(": ")
        value = value.strip()
        if not sep or not value:
            raise Fault("bad_line")
        if key not in keys:
            raise Fault("unknown_key:%s" % key)
        if key in fields:
            raise Fault("repeated_key:%s" % key)
        if value[0] in "\"'":
            raise Fault("quoted_value:%s" % key)
        fields[key] = value
    body = "\n".join(lines[end + 1:])
    if not body.strip():
        raise Fault("empty_body")
    return fields, body


def definition(root: str, name: str) -> dict:
    """Rule 2: ``{name, model, tools, sha256}`` of ``agents/<name>.md``."""
    try:
        with open(os.path.join(root, AGENTS, name + ".md"), "rb") as f:
            data = f.read()
    except OSError:
        raise Fault("no_definition") from None
    fields, _ = front_matter(data, AGENT_KEYS)
    for key in ("name", "description", "model"):
        if key not in fields:
            raise Fault("no_%s" % key)
    if fields["name"] != name:
        raise Fault("name_is_not_the_files")
    if fields["model"] not in MODELS:
        raise Fault("model_not_allowed")
    tools = None
    if "tools" in fields:
        tools = [t.strip() for t in fields["tools"].split(",")]
        if not all(tools):
            raise Fault("empty_tool")
    return {"name": name, "model": fields["model"], "tools": tools, "sha256": hashlib.sha256(data).hexdigest()}


def loaded(record: str, name: str) -> dict:
    """Rule 3: ``{model, tools, sha256}`` of the definition the capsule loaded for this session as ``name``."""
    listed = _load(record, "load_record_unreadable").get("agents")
    if not isinstance(listed, list):
        raise Fault("load_record_unreadable")
    for agent in listed:
        if isinstance(agent, dict) and agent.get("name") == name:
            if (agent.get("model") in MODELS and isinstance(agent.get("sha256"), str)
                    and isinstance(agent.get("tools"), list) and all(_text(t) for t in agent["tools"])):
                return {"model": agent["model"], "tools": agent["tools"], "sha256": agent["sha256"]}
            raise Fault("load_record_unreadable")
    raise Fault("definition_not_loaded")


def lessons(index: str, ledger: str, data: bytes) -> list[dict]:
    """Rule 3: ``{row_id, summary}`` of each lesson in force in ``data``, the ledger's bytes, oldest first; in
    force is ``lesson_recheck.in_force``'s answer (the capsule's index, the one reader of the closing rule)."""
    try:
        digest, rows = LR.in_force(index, ledger)
        LR.rechecks(data, digest, rows)
    except LR.Fault as e:
        raise Fault("lessons:%s" % e) from None
    lines = data.split(b"\n")
    return [{"row_id": r["row_id"], "summary": json.loads(lines[r["line"] - 1])["payload"]["summary"]} for r in rows]


def memory(data: bytes, name: str) -> list[dict]:
    """Rule 3: the findings of ``name``'s runs in ``data`` that are not ``caught`` and are no repeat, as each
    was last read, in file order: ``id`` (``<run's row id>#<n>``) and the finding's fields without ``n``."""
    return [{"id": "%s#%d" % (row_id, f["n"]), **{k: v for k, v in f.items() if k != "n"}}
            for row_id, run in runs(data, name).items() for f in run["findings"]
            if f["verdict"] != CAUGHT and f.get("repeat_of") is None]


def packet(root: str, name: str, base: str, head: str, out: str, git: str = "git", record: str = LOADED,
           index: str = LR.INDEX, ledger: str | None = None) -> dict:
    """Rule 3: write the packet into ``out`` and return ``packet.json``'s object."""
    definition(root, name)
    agent = loaded(record, name)
    ledger = os.path.join(root, LEDGER) if ledger is None else ledger
    try:
        with open(os.path.join(root, RULES), "rb") as f:
            rules = f.read()
        with open(ledger, "rb") as f:
            rows = f.read()
    except OSError:
        raise Fault("no_rules_or_ledger") from None
    given = {"lessons.json": lessons(index, ledger, rows), "memory.json": memory(rows, name)}
    files = {k: (json.dumps(v, ensure_ascii=False, indent=1) + "\n").encode() for k, v in given.items()}
    real, top = os.path.realpath(out), os.path.realpath(root)
    if real == top or real.startswith(top + os.sep):
        raise Fault("out_inside_brain")
    if os.path.lexists(out) and (not os.path.isdir(out) or os.listdir(out)):
        raise Fault("out_not_empty")
    try:
        diff = PS._git(root, git, *PS.DIFF, base, head)
        names = [n for n in PS._git(root, git, *PS.DIFF, "--name-only", "-z", base, head).split(b"\0") if n]
    except PS.Unreadable as e:
        raise Fault(str(e)) from None
    doc = {"agent": name, "model": agent["model"], "tools": agent["tools"], "definition_sha256": agent["sha256"],
           "base": base, "head": head, "bytes": len(diff),
           "files": len(names), "rules_sha256": hashlib.sha256(rules).hexdigest(),
           "lessons": len(given["lessons.json"]), "memory": len(given["memory.json"])}
    files["message.txt"] = (MESSAGE % os.path.abspath(out)).encode()
    files["diff.patch"] = diff
    for file, key in PINNED:
        doc[key] = hashlib.sha256(files[file]).hexdigest()
    os.makedirs(out, exist_ok=True)
    for file, data in (*files.items(), ("paths.txt", b"".join(n + b"\n" for n in names)),
                       ("packet.json", (json.dumps(doc, sort_keys=True) + "\n").encode())):
        with open(os.path.join(out, file), "wb") as f:
            f.write(data)
    return doc


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _load(path: str, reason: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError, RecursionError):
        raise Fault(reason) from None
    if not isinstance(doc, dict):
        raise Fault(reason)
    return doc


def check_findings(findings) -> None:
    """Rule 4's findings; a fault names the first finding that breaks it."""
    if not isinstance(findings, list):
        raise Fault("findings_not_a_list")
    for i, f in enumerate(findings, 1):
        ok = (isinstance(f, dict) and sorted(f) == sorted(FINDING_KEYS) and type(f["n"]) is int and f["n"] == i
              and _text(f["class"]) and _text(f["claim"])
              and (f["ref"] is None or _text(f["ref"])) and f["verdict"] in VERDICTS
              and (_text(f["evidence"]) or (f["evidence"] is None and f["verdict"] == UNJUDGED)))
        if not ok:
            raise Fault("bad_finding:%d" % i)


def check_findings2(findings) -> None:
    """Rule 4's findings in the form of ``agent_run/2``; a fault names the first finding that breaks it."""
    if not isinstance(findings, list):
        raise Fault("findings_not_a_list")
    for i, f in enumerate(findings, 1):
        if not (isinstance(f, dict) and sorted(f) == sorted(FINDING_KEYS2)):
            raise Fault("bad_finding:%d" % i)
        place, again = f["carried_in"], f["repeat_of"]
        ok = ((isinstance(place, str) and bool(REPORT.fullmatch(place) or ROW_ID.fullmatch(place)))
              if f["verdict"] == CARRIED else place is None)
        if not ok or not (again is None or (isinstance(again, str) and FINDING_ID.fullmatch(again))):
            raise Fault("bad_finding:%d" % i)
    check_findings([{k: f[k] if k != "verdict" or f[k] != CARRIED else CAUGHT for k in FINDING_KEYS} for f in findings])


def check_places(findings: list[dict], root: str, data: bytes, name: str, amends: str | None = None) -> None:
    """Rule 5: what a finding points at exists: the report under ``root`` or the row in ``data`` a ``carried``
    finding names, and the finding a ``repeat_of`` names, in a run of ``name`` before the run ``amends`` (any
    run in ``data`` when the findings are a new run's)."""
    ids = None
    found = list(runs(data, name).items())
    found = dict(found[:[row_id for row_id, _ in found].index(amends)] if amends is not None else found)
    for f in findings:
        place, again = f["carried_in"], f["repeat_of"]
        if place is not None and REPORT.fullmatch(place) and not os.path.isfile(os.path.join(root, place)):
            raise Fault("carried_in_absent:%d" % f["n"])
        if place is not None and ROW_ID.fullmatch(place):
            ids = {json.loads(line)["row_id"] for line in data.splitlines()} if ids is None else ids
            if place not in ids:
                raise Fault("carried_in_absent:%d" % f["n"])
        if again is not None:
            row_id, n = FINDING_ID.fullmatch(again).groups()
            if row_id not in found or int(n) > len(found[row_id]["findings"]):
                raise Fault("repeat_of_no_finding:%d" % f["n"])


def check_run2(run: dict) -> None:
    """Rule 4 in the form of ``agent_run/2``."""
    check_run({**run, "findings": []})
    if run["effort"] is None or run["tokens"] is None or "amends" in run:
        raise Fault("bad_run_field")
    if run["cost_usd_micros"] is not None:
        raise Fault("cost_not_null")
    check_findings2(run["findings"])


def check_run(run: dict) -> None:
    """Rule 4 in the form of ``agent_run/1``."""
    extra = sorted(set(run) - set(RUN_KEYS) - {"amends"})
    missing = [k for k in RUN_KEYS if k not in run]
    if extra or missing:
        raise Fault("run_keys:%s" % ",".join(missing + extra))
    if not _text(run["invoked_as"]) or not _text(run["model_served"]) or not _count(run["wall_ms"]):
        raise Fault("bad_run_field")
    if not (run["effort"] is None or _text(run["effort"])):
        raise Fault("bad_run_field")
    if not all(run[k] is None or _count(run[k]) for k in MAY_BE_SUMMED):
        raise Fault("bad_run_field")
    if not (run["not_measured"] is None or _text(run["not_measured"])):
        raise Fault("bad_run_field")
    if run["not_measured"] is None and any(run[k] is None for k in MAY_BE_UNKNOWN):
        raise Fault("unknown_without_reason")
    if "amends" in run and not (isinstance(run["amends"], str) and ROW_ID.fullmatch(run["amends"])):
        raise Fault("bad_amends")
    check_findings(run["findings"])


def _time(text, form: str) -> datetime.datetime | None:
    """The time ``text`` names in ``form`` and writes back the same, or none."""
    try:
        time = datetime.datetime.strptime(text, form)
    except (ValueError, TypeError):
        return None
    return time if time.strftime(form) == text else None


def check_cost(fields: dict) -> None:
    """Rule 7's cost row."""
    if sorted(fields) != sorted(COST_KEYS):
        raise Fault("bad_cost_row")
    tokens = fields["usage"]
    ok = (isinstance(fields["cost_of"], str) and ROW_ID.fullmatch(fields["cost_of"]) and fields["source"] == SOURCE
          and _time(fields["stamp"], STAMP) is not None
          and isinstance(fields["tool_use_id"], str) and fields["tool_use_id"].startswith(CALL_ID)
          and len(fields["tool_use_id"]) > len(CALL_ID) and _text(fields["model"])
          and all(fields[k] is None or _text(fields[k])
                  for k in ("subagent_type", "effort", "cost_basis", "not_measured"))
          and isinstance(tokens, dict) and sorted(tokens) == sorted(TOKEN_KINDS)
          and all(v is None or _count(v) for v in tokens.values())
          and all(fields[k] is None or _count(fields[k]) for k in ("cost_usd_micros", "cost_floor_usd_micros"))
          and (fields["cost_usd_micros"] is not None or fields["not_measured"] is not None))
    if not ok:
        raise Fault("bad_cost_row")


def mirror(path: str) -> tuple[datetime.datetime, list[tuple[datetime.datetime, str, list[dict]]]]:
    """Rule 7's mirror: the time of its own stamp and ``(time, stamp, runs)`` of each session, oldest first."""
    reason = "mirror_unreadable"
    doc = _load(path, reason)
    now = _time(doc.get("stamp"), STAMP)
    try:
        sessions = [(_time(s["stamp"], STAMP), s["stamp"], s["runs"]) for s in doc["delegation"]["sessions"]]
    except (KeyError, TypeError):
        raise Fault(reason) from None
    if now is None or not all(time is not None and time < now and isinstance(found, list)
                              and all(isinstance(m, dict) for m in found) for time, _, found in sessions):
        raise Fault(reason)
    if len({stamp for _, stamp, _ in sessions}) != len(sessions):
        raise Fault(reason)
    return now, sorted(sessions, key=lambda s: s[0])


def pair(found: dict[str, dict], now: datetime.datetime, sessions: list, name: str) -> tuple[dict, dict]:
    """Rule 7: the cost row's object of each run of ``found`` that has a call, and the reason of each other."""
    place: dict[str, tuple | None] = {}
    for row_id, run in found.items():
        ts = _time(run["ts"], ROW_TS)
        earlier = [s for s in sessions if ts is not None and ts < now and s[0] <= ts]
        place[row_id] = (earlier[-1], run["wall_ms"]) if earlier else None
    paired, unpaired = {}, {}
    for row_id, run in found.items():
        if place[row_id] is None:
            unpaired[row_id] = "session_not_in_mirror"
            continue
        (_, stamp, made), wall = place[row_id]
        calls = [m for m in made if _count(m.get("wall_ms")) and m["wall_ms"] == wall
                 and (run["form"] == 1 or m.get("subagent_type") == BRAIN + name)]
        if not calls:
            unpaired[row_id] = "no_call"
        elif len(calls) > 1 or sum(p is not None and p[0][1] == stamp and p[1] == wall for p in place.values()) > 1:
            unpaired[row_id] = "ambiguous"
        else:
            fields = {"agent": name, "cost_of": row_id, "source": SOURCE, "stamp": stamp,
                      **{k: calls[0][k] for k in COPIED if k in calls[0]},
                      **({"usage": calls[0]["tokens"]} if "tokens" in calls[0] else {})}
            try:
                check_cost(fields)
            except Fault:
                raise Fault("mirror_unreadable") from None
            paired[row_id] = fields
    return paired, unpaired


def cost(name: str, path: str, ledger: str, snapshot: str, ts: str, kinds: frozenset) -> dict:
    """Rule 7: append the cost row of each run of ``name`` the mirror at ``path`` has a call for; the answer."""
    found = runs(_read(ledger), name)
    paired, unpaired = pair(found, *mirror(path), name)
    recorded = []
    for row_id, fields in paired.items():
        if found[row_id]["cost"] != fields:
            recorded.append(_write(name, FORM2 + json.dumps(fields, ensure_ascii=False, sort_keys=True), ledger,
                                   _read(ledger), snapshot, ts, kinds))
    return {"recorded": recorded, "unchanged": len(paired) - len(recorded), "unpaired": unpaired}


def read_packet(directory: str) -> dict:
    """Rule 5: ``packet.json`` of ``directory``, each file of ``PINNED`` still the one it names."""
    doc = _load(os.path.join(directory, "packet.json"), "packet_unreadable")
    if sorted(doc) != sorted(PACKET_KEYS2):
        raise Fault("packet_unreadable")
    for file, key in PINNED:
        try:
            with open(os.path.join(directory, file), "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            raise Fault("packet_unreadable") from None
        if digest != doc[key]:
            raise Fault("%s_changed" % file.split(".")[0])
    return doc


def summary(pack: dict, run: dict) -> str:
    """Rule 5: the row's summary."""
    fields = {**{k: v for k, v in pack.items() if k != "tools"}, **run}
    return FORM2 + json.dumps(fields, ensure_ascii=False, sort_keys=True)


def record(pack: dict, run: dict, ledger: str, snapshot: str, ts: str, kinds: frozenset, root: str = ROOT) -> str:
    """Rule 5: append the run's row and return its ``row_id``."""
    check_run2(run)
    return _append(pack["agent"], run["findings"], summary(pack, run), ledger, snapshot, ts, kinds, root)


def amend(name: str, run: dict, ledger: str, snapshot: str, ts: str, kinds: frozenset, root: str = ROOT) -> str:
    """Rule 5: append the row that replaces the findings of the run ``run`` names and return its ``row_id``."""
    if sorted(run) != sorted(AMEND_KEYS[1:]) or not (isinstance(run["amends"], str)
                                                     and ROW_ID.fullmatch(run["amends"])):
        raise Fault("bad_amends")
    check_findings2(run["findings"])
    text = FORM2 + json.dumps({"agent": name, **run}, ensure_ascii=False, sort_keys=True)
    return _append(name, run["findings"], text, ledger, snapshot, ts, kinds, root, run["amends"])


def _append(name: str, findings: list[dict], text: str, ledger: str, snapshot: str, ts: str, kinds: frozenset,
            root: str, amends: str | None = None) -> str:
    data = _read(ledger)
    found = runs(data, name)
    if amends is not None and amends not in found:
        raise Fault("amends_no_run")
    if amends is not None and len(findings) != len(found[amends]["findings"]):
        raise Fault("amends_other_findings")
    check_places(findings, root, data, name, amends)
    return _write(name, text, ledger, data, snapshot, ts, kinds)


def _read(ledger: str) -> bytes:
    try:
        with open(ledger, "rb") as f:
            return f.read()
    except OSError as e:
        raise Fault("ledger_unusable:%s" % type(e).__name__) from None


def _write(name: str, text: str, ledger: str, data: bytes, snapshot: str, ts: str, kinds: frozenset) -> str:
    """Rule 5: append the row of ``name`` whose summary is ``text`` after ``data`` and return its ``row_id``."""
    refs = ["%s/%s.md" % (AGENTS, name), TAG + name]
    try:
        row = F.next_row(data, "build", text, refs, snapshot, ts)
        reasons = F.append(ledger, row, kinds)
    except (OSError, F.Unusable, F.chain.ChainError, UnicodeDecodeError) as e:
        raise Fault("ledger_unusable:%s" % type(e).__name__) from None
    if reasons:
        raise Fault("row_refused:%s" % ";".join(reasons))
    return row["row_id"]


def runs(data: bytes, name: str) -> dict[str, dict]:
    """Rule 6: ``name``'s runs in the ledger's bytes by row id, each ``{session, form, ts, message_sha256,
    findings, cost, tokens, cost_usd_micros, wall_ms}`` with the findings of the last row that amends it and,
    as ``cost``, the object of its last cost row or none (``ts`` is the row's; ``message_sha256`` is null in a
    run of the form ``agent_run/1``)."""
    runs: dict[str, dict] = {}
    session = None
    for raw in data.splitlines():
        try:
            row = json.loads(raw)
            payload = row["payload"]
            kind, row_id, refs, text, ts = row["kind"], row["row_id"], payload["refs"], payload["summary"], row["ts"]
        except (ValueError, KeyError, TypeError):
            raise Fault("ledger_unreadable") from None
        if kind == "session_start":
            session = row_id
        if not isinstance(refs, list) or TAG + name not in refs:
            continue
        try:
            form, fields = _fields(text, name)
            sums = {k: fields[k] for k in ("tokens", "wall_ms") if "invoked_as" in fields}
        except (ValueError, KeyError, TypeError, Fault):
            raise Fault("run_row_unreadable:%s" % row_id) from None
        if "cost_of" in fields:
            if fields["cost_of"] not in runs:
                raise Fault("cost_no_run:%s" % row_id)
            runs[fields["cost_of"]].update(cost=fields, cost_usd_micros=fields["cost_usd_micros"])
        elif "amends" in fields:
            if fields["amends"] not in runs:
                raise Fault("amends_no_run:%s" % row_id)
            runs[fields["amends"]]["findings"] = fields["findings"]
        else:
            runs[row_id] = {"session": session, "form": form, "ts": ts, "cost": None, "cost_usd_micros": None,
                            "message_sha256": fields.get("message_sha256"), "findings": fields["findings"], **sums}
    return runs


def _fields(text, name: str) -> tuple[int, dict]:
    """Rule 6: the form (1 or 2) and the fields of a tagged row's summary; any exception is an unreadable row."""
    if not isinstance(text, str) or not text.startswith((FORM, FORM2)):
        raise ValueError
    form = 1 if text.startswith(FORM) else 2
    fields = json.loads(text[len(FORM):])
    if fields["agent"] != name:
        raise ValueError
    if form == 2 and sorted(fields) == sorted(AMEND_KEYS):
        if not ROW_ID.fullmatch(fields["amends"]):
            raise ValueError
        check_findings2(fields["findings"])
        return form, fields
    if form == 2 and "cost_of" in fields:
        check_cost(fields)
        return form, fields
    carried = [k for k in (PACKET_KEYS, PACKET_KEYS2)[form - 1] if k != "tools"]
    if any(k not in fields for k in carried):
        raise ValueError
    (check_run, check_run2)[form - 1]({k: v for k, v in fields.items() if k not in carried})
    return form, fields


def fold(found: list[dict]) -> dict:
    """Rule 6: the counts and sums of ``found``, a list of runs."""
    findings = [f for run in found for f in run["findings"]]
    count = {v: sum(f["verdict"] == v for f in findings) for v in VERDICTS2}
    known = {k: [run[k] for run in found if run[k] is not None] for k in MAY_BE_SUMMED}
    floors = [run["cost"]["cost_floor_usd_micros"] for run in found
              if run["cost_usd_micros"] is None and run["cost"] is not None
              and run["cost"]["cost_floor_usd_micros"] is not None]
    return {"runs": len(found), "sessions": len({run["session"] for run in found}), "findings": len(findings),
            **count, "repeats": sum(f.get("repeat_of") is not None for f in findings),
            "tokens": sum(known["tokens"]), "tokens_unknown": len(found) - len(known["tokens"]),
            "caught_tokens_known": sum(f["verdict"] == CAUGHT for run in found if run["tokens"] is not None
                                       for f in run["findings"]),
            "cost_usd_micros": sum(known["cost_usd_micros"]),
            "cost_unknown": len(found) - len(known["cost_usd_micros"]),
            "caught_cost_known": sum(f["verdict"] == CAUGHT for run in found if run["cost_usd_micros"] is not None
                                     for f in run["findings"]),
            "cost_floor_usd_micros": sum(floors), "cost_floor_runs": len(floors),
            "wall_ms": sum(run["wall_ms"] for run in found)}


def session_costs(data: bytes) -> list[int]:
    """Rule 6: what each ``cost`` row of the ledger's bytes says its session cost, sorted; a row that states
    none is left out."""
    costs = []
    for raw in data.splitlines():
        try:
            row = json.loads(raw)
            kind, text = row["kind"], row["payload"]["summary"]
        except (ValueError, KeyError, TypeError):
            raise Fault("ledger_unreadable") from None
        said = SESSION_COST.match(text) if kind == "cost" and isinstance(text, str) else None
        if said:
            costs.append(int(said.group(1)))
    return sorted(costs)


def measure(data: bytes, name: str) -> dict:
    """Rule 6: the fold of ``name``'s runs and whether its retirement is due."""
    found = list(runs(data, name).values())
    whole = fold(found)
    costs = session_costs(data)
    session = costs[(len(costs) - 1) // 2] if costs else None
    least = whole["cost_usd_micros"] + whole["cost_floor_usd_micros"]
    over = session is not None and least > whole[CAUGHT] * session
    return {"ok": True, "agent": name, **whole,
            "before_rules": fold([r for r in found if r["form"] == 1]),
            "under_rules": fold([r for r in found if r["form"] == 2]),
            "session_cost_usd_micros": session, "session_costs": len(costs), "cost_over_gain": over,
            "retire_due": whole["sessions"] >= RETIRE_AFTER and (whole[CAUGHT] == 0 or over)}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(ROW_TS)


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("packet")
    p.add_argument("--agent", required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--out", required=True)
    p.add_argument("--loaded", default=LOADED)
    p.add_argument("--index", default=LR.INDEX)
    r = sub.add_parser("record")
    r.add_argument("--packet", default=None)
    r.add_argument("--run", required=True)
    r.add_argument("--snapshot", required=True)
    r.add_argument("--ts", default=None)
    r.add_argument("--agent", default=None)
    m = sub.add_parser("measure")
    m.add_argument("--agent", required=True)
    c = sub.add_parser("cost")
    c.add_argument("--agent", required=True)
    c.add_argument("--mirror", default=MIRROR)
    c.add_argument("--snapshot", required=True)
    c.add_argument("--ts", default=None)
    for s in (p, r, m, c):
        s.add_argument("--ledger", default=os.path.join(root, LEDGER))
    args = parser.parse_args(argv)
    try:
        if args.command == "packet":
            out = {"ok": True, **packet(root, args.agent, args.base, args.head, args.out, git, args.loaded,
                                        args.index, args.ledger), "out": args.out}
        elif args.command == "cost":
            out = {"ok": True, **cost(args.agent, args.mirror, args.ledger, args.snapshot, args.ts or _now(),
                                      F.spec_kinds())}
        elif args.command == "record":
            run = _load(args.run, "run_unreadable")
            ts = args.ts or _now()
            if (args.packet is None) == (args.agent is None):
                raise Fault("packet_or_agent")
            if args.packet is None:
                row_id = amend(args.agent, run, args.ledger, args.snapshot, ts, F.spec_kinds(), root)
            else:
                row_id = record(read_packet(args.packet), run, args.ledger, args.snapshot, ts, F.spec_kinds(), root)
            out = {"ok": True, "recorded": row_id}
        else:
            try:
                with open(args.ledger, "rb") as f:
                    data = f.read()
            except OSError:
                raise Fault("ledger_unreadable") from None
            out = measure(data, args.agent)
    except Fault as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
