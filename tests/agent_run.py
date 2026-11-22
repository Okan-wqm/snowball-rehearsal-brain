"""The packet a brain agent reviews, the ledger row of each of its runs, and the fold that measures the agent.

Why (tohum/00e E692): the first agent of this brain, ``agents/push-reviewer.md``, reads a push's diff before
prepush. The owner's conditions for it are that every run is a founder row carrying the agent's name, the model
and effort, the definition's sha256, the diff's sha256, the findings, tokens, cost and wall time, and that the
agent is measured per finding and retired when it catches nothing. This tool is those records; it calls no
model and starts no agent (the session does, with the Agent tool). A session tool, not in ``referee/``. From
anywhere:

    python3 tests/agent_run.py packet --agent NAME --base REV [--head REV] --out DIR
    python3 tests/agent_run.py record --packet DIR --run FILE --snapshot SHA [--ts TS] [--ledger FILE]
    python3 tests/agent_run.py measure --agent NAME [--ledger FILE]

The rules, each bound by ``tests/test_agent_run.py``:

1. **A definition's form** (``front_matter``; tohum/24a "Ajan ve skill tanımları"): the first line is ``---``;
   up to the next line ``---`` every line that is not blank is ``<key>: <value>`` with a key of the allowed keys,
   no key twice, a value that is not empty; the text after it is not empty. A value that starts with a quote is
   refused (``quoted_value``): the capsule's loader unquotes such a value and this reader does not.
2. **An agent** (``definition``) is ``agents/<name>.md`` with the keys ``name``, ``description`` and ``model``
   and, optionally, ``tools``: ``name`` is the file's name, ``model`` is one of ``MODELS`` (tohum/00b E643; a
   definition without a model would run on a model its row could not name), ``tools`` a comma list of names
   that are not empty. Its ``sha256`` is of the file's bytes.
3. **packet** writes, into ``--out`` (a directory that does not exist or is empty, and is not inside the
   brain): ``diff.patch``, the bytes of ``push_size``'s diff from ``--base`` to ``--head`` (default ``HEAD``; the
   same git arguments and the same exclusion of the founder's ledger and reports, one source); ``paths.txt``, the
   changed paths by the same arguments with ``--name-only``, one a line; ``packet.json``: ``agent``, ``model``,
   ``tools``, ``definition_sha256``, ``base``, ``head``, ``diff_sha256``, ``bytes``, ``files``. It prints
   ``packet.json``'s object with ``out``.
4. **The run file** is a JSON object the session writes after the run, with exactly the keys ``invoked_as``
   (text: the agent type the Agent tool was given), ``model_served`` (text: the model as the session saw it
   served, or the alias when it saw none), ``effort`` (text or null), ``tokens``, ``cost_usd_micros`` (each a count or
   null), ``wall_ms`` (a count), ``not_measured`` (text or null; text when ``effort``, ``tokens`` or
   ``cost_usd_micros`` is null) and ``findings``; and optionally ``amends`` (``f<n>``; rule 5). A finding has
   exactly ``n`` (the integers 1, 2, ... in order), ``class``, ``claim`` (texts), ``ref`` (text or null), ``verdict`` (one of
   ``VERDICTS``) and ``evidence`` (text or null; text unless the verdict is ``unjudged``: for ``caught`` the test
   that was red before the repair and green after, or the referee's or rival's confirmation; for
   ``false_alarm`` the reason). A count is an integer of 0 or more, not a boolean; a text is a string that is
   not empty.
5. **record** reads ``packet.json`` and the run file, refuses when ``diff.patch``'s sha256 is no longer the
   packet's, and appends one row through ``ledger.founder`` (``next_row`` and ``append``, the one writer): kind
   ``build``, the defaults ``llm_inference`` and ``inferred`` (the verdicts are the session's judgement), refs
   ``agents/<name>.md`` and ``agent_run:<name>``, and the summary ``agent_run/1 `` followed by one JSON object:
   the packet's fields without ``tools`` and the run file's fields (no key is of both, so ``model`` is the
   definition's and ``model_served`` the run's). A run file with ``amends`` is refused (``amends_no_run``) unless
   it names a run of this agent that rule 6 reads in the ledger; a ledger whose run rows rule 6 cannot read
   takes no further run. A row the writer refuses and a ledger it cannot extend are faults; the file is left as
   it was.
6. **measure** folds the ledger's rows that carry the ref ``agent_run:<name>``, in file order. Such a row whose
   summary is not rule 5's form is a fault, never skipped: the form is ``agent_run/1 `` and one JSON object that
   has every field of the packet but ``tools``, ``agent`` being ``<name>``, and beside them a run file by rule 4
   and no other key (so a ``wall_ms`` that is no count, ``tokens`` or ``cost_usd_micros`` neither a count nor
   null, and an ``amends`` that is no row id are faults). The packet fields' own values, ``agent`` apart, are
   not judged. A row with ``amends`` replaces the findings of the
   earlier run row it names (a later reading of the same findings: the rival's or the referee's answer comes
   after the push) and is not a run; naming anything else is a fault. The answer: ``runs``; ``sessions``, the
   distinct ``session_start`` rows last seen before each run (a run before any such row counts as one more);
   ``findings`` and the count of each verdict; the sums ``tokens``, ``cost_usd_micros`` and ``wall_ms`` over the
   runs that carry a count, with ``tokens_unknown`` and ``cost_unknown`` the runs that carry null; and
   ``retire_due``: true when ``sessions`` is at least ``RETIRE_AFTER`` and ``caught`` is 0 (E692's fourth
   condition, its first half).
7. One JSON line; exit 0, or 2 with ``{"ok": false, "reason"}`` on a fault.

What this does not say, stated. A row is what the session wrote: nothing here checks that the agent ran, that a
count is the true one, or that a ``caught`` finding's test exists or was ever red. The diff is ``push_size``'s,
not the referee's prompt (which is ``--binary`` and adds pages). ``retire_due`` is the first half of the
owner's fourth condition only; "its cost is more than the minutes it saved" is the session's reading of the
sums. The capsule's loader (``brain_defs.py``) is the judge of what a session loads; rules 1 and 2 are tohum/24a's
sentence and this brain's narrower choice of models, and a definition that passes here can still be dropped
there (its limits on length and its name pattern are not copied).
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

import push_size as PS  # noqa: E402
from ledger import founder as F  # noqa: E402

AGENTS = "agents"
LEDGER = "founder-ledger.jsonl"
AGENT_KEYS = ("name", "description", "tools", "model")
SKILL_KEYS = ("name", "description")
MODELS = ("sonnet", "opus")
CAUGHT, FALSE_ALARM, UNJUDGED = "caught", "false_alarm", "unjudged"
VERDICTS = (CAUGHT, FALSE_ALARM, UNJUDGED)
FORM = "agent_run/1 "
TAG = "agent_run:"
RETIRE_AFTER = 5
FENCE = "---"
PACKET_KEYS = ("agent", "model", "tools", "definition_sha256", "base", "head", "diff_sha256", "bytes", "files")
RUN_KEYS = ("invoked_as", "model_served", "effort", "tokens", "cost_usd_micros", "wall_ms", "not_measured", "findings")
MAY_BE_UNKNOWN = ("effort", "tokens", "cost_usd_micros")
MAY_BE_SUMMED = ("tokens", "cost_usd_micros")
FINDING_KEYS = ("n", "class", "claim", "ref", "verdict", "evidence")
ROW_ID = re.compile(r"f[1-9][0-9]*")


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


def packet(root: str, name: str, base: str, head: str, out: str, git: str = "git") -> dict:
    """Rule 3: write the packet into ``out`` and return ``packet.json``'s object."""
    agent = definition(root, name)
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
           "base": base, "head": head, "diff_sha256": hashlib.sha256(diff).hexdigest(), "bytes": len(diff),
           "files": len(names)}
    os.makedirs(out, exist_ok=True)
    for file, data in (("diff.patch", diff), ("paths.txt", b"".join(n + b"\n" for n in names)),
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


def check_run(run: dict) -> None:
    """Rule 4."""
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


def read_packet(directory: str) -> dict:
    """Rule 5: ``packet.json`` of ``directory``, its diff still the one it names."""
    doc = _load(os.path.join(directory, "packet.json"), "packet_unreadable")
    if sorted(doc) != sorted(PACKET_KEYS):
        raise Fault("packet_unreadable")
    try:
        with open(os.path.join(directory, "diff.patch"), "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
    except OSError:
        raise Fault("packet_unreadable") from None
    if digest != doc["diff_sha256"]:
        raise Fault("diff_changed")
    return doc


def summary(pack: dict, run: dict) -> str:
    """Rule 5: the row's summary."""
    fields = {**{k: v for k, v in pack.items() if k != "tools"}, **run}
    return FORM + json.dumps(fields, ensure_ascii=False, sort_keys=True)


def record(pack: dict, run: dict, ledger: str, snapshot: str, ts: str, kinds: frozenset) -> str:
    """Rule 5: append the run's row and return its ``row_id``."""
    check_run(run)
    refs = ["%s/%s.md" % (AGENTS, pack["agent"]), TAG + pack["agent"]]
    try:
        with open(ledger, "rb") as f:
            data = f.read()
    except OSError as e:
        raise Fault("ledger_unusable:%s" % type(e).__name__) from None
    if run.get("amends", None) not in (None, *runs(data, pack["agent"])):
        raise Fault("amends_no_run")
    try:
        row = F.next_row(data, "build", summary(pack, run), refs, snapshot, ts)
        reasons = F.append(ledger, row, kinds)
    except (OSError, F.Unusable, F.chain.ChainError, UnicodeDecodeError) as e:
        raise Fault("ledger_unusable:%s" % type(e).__name__) from None
    if reasons:
        raise Fault("row_refused:%s" % ";".join(reasons))
    return row["row_id"]


def runs(data: bytes, name: str) -> dict[str, dict]:
    """Rule 6: ``name``'s runs in the ledger's bytes by row id, each ``{session, findings, tokens,
    cost_usd_micros, wall_ms}`` with the findings of the last row that amends it."""
    runs: dict[str, dict] = {}
    session = None
    for raw in data.splitlines():
        try:
            row = json.loads(raw)
            payload = row["payload"]
            kind, row_id, refs, text = row["kind"], row["row_id"], payload["refs"], payload["summary"]
        except (ValueError, KeyError, TypeError):
            raise Fault("ledger_unreadable") from None
        if kind == "session_start":
            session = row_id
        if not isinstance(refs, list) or TAG + name not in refs:
            continue
        try:
            if not isinstance(text, str) or not text.startswith(FORM):
                raise ValueError
            fields = json.loads(text[len(FORM):])
            carried = [k for k in PACKET_KEYS if k != "tools"]
            if fields["agent"] != name or any(k not in fields for k in carried):
                raise ValueError
            check_run({k: v for k, v in fields.items() if k not in carried})
            sums = {k: fields[k] for k in ("tokens", "cost_usd_micros", "wall_ms")}
        except (ValueError, KeyError, TypeError, Fault):
            raise Fault("run_row_unreadable:%s" % row_id) from None
        if "amends" in fields:
            if fields["amends"] not in runs:
                raise Fault("amends_no_run:%s" % row_id)
            runs[fields["amends"]]["findings"] = fields["findings"]
        else:
            runs[row_id] = {"session": session, "findings": fields["findings"], **sums}
    return runs


def measure(data: bytes, name: str) -> dict:
    """Rule 6: the fold of ``name``'s runs."""
    found = runs(data, name)
    verdicts = [f["verdict"] for run in found.values() for f in run["findings"]]
    count = {v: verdicts.count(v) for v in VERDICTS}
    sessions = len({run["session"] for run in found.values()})
    known = {k: [run[k] for run in found.values() if run[k] is not None] for k in MAY_BE_SUMMED}
    return {"ok": True, "agent": name, "runs": len(found), "sessions": sessions, "findings": len(verdicts), **count,
            "tokens": sum(known["tokens"]), "tokens_unknown": len(found) - len(known["tokens"]),
            "cost_usd_micros": sum(known["cost_usd_micros"]),
            "cost_unknown": len(found) - len(known["cost_usd_micros"]),
            "wall_ms": sum(run["wall_ms"] for run in found.values()),
            "retire_due": sessions >= RETIRE_AFTER and count[CAUGHT] == 0}


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("packet")
    p.add_argument("--agent", required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--out", required=True)
    r = sub.add_parser("record")
    r.add_argument("--packet", required=True)
    r.add_argument("--run", required=True)
    r.add_argument("--snapshot", required=True)
    r.add_argument("--ts", default=None)
    m = sub.add_parser("measure")
    m.add_argument("--agent", required=True)
    for s in (r, m):
        s.add_argument("--ledger", default=os.path.join(root, LEDGER))
    args = parser.parse_args(argv)
    try:
        if args.command == "packet":
            out = {"ok": True, **packet(root, args.agent, args.base, args.head, args.out, git), "out": args.out}
        elif args.command == "record":
            pack, run = read_packet(args.packet), _load(args.run, "run_unreadable")
            ts = args.ts or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            out = {"ok": True, "recorded": record(pack, run, args.ledger, args.snapshot, ts, F.spec_kinds())}
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
