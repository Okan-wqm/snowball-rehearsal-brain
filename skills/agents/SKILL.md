---
name: agents
description: The rules by which this brain builds, runs, judges and measures its agents, and the order of one run. Use it before starting any agent and before adding or changing a definition under agents/.
---
The rules are data: `skills/agents/rules.json`, each with what it says, what it expects of the runs, and the
check of `tests/agent_rules.py` that judges it against the ledger, the definitions and the session's log. This
text is the order of work that keeps them; where the two differ, the file and its checks are the source. The
owner's conditions are tohum/00e E692 and E697: an agent adds a check and stands in for none (the Founder's own
reading, the whole prepush, the bootstrap referee and the rival run whatever an agent found).

Before a run:

1. The session's `session_start` row is in the ledger (`python -m ledger.founder append`, from `referee/`): a
   run's session is the last such row before its own.
2. `python3 tests/agent_rules.py`. A rule that is `refuted` is repaired before any new run: a finding left
   `unjudged` by an earlier session is judged with an amending row (step 8), a run of an earlier session
   without its outcome is answered (step 4), an agent that no longer earns its runs is rewritten or removed.
3. `python3 tests/agent_run.py cost --agent <name> --snapshot <HEAD's SHA>`, for each agent with a run in an
   earlier session: what a run cost is in the launcher's mirror (`/work/logs/mirror.json`, tohum/26o) from the
   session after it on, and the mirror holds the newest 20 sessions only. The command writes one row beside
   each run it can tie to a call (the session's stamp and the call's `tool_use_id` are in the row) and names
   the runs it cannot (`unpaired`); a run left so is read by hand before its session leaves the mirror.
4. The outcome of each run of the last session (rule `answered`): `python3 tests/agent_run.py record --agent
   <name> --run <a file with outcome_of> --snapshot <HEAD's SHA>`. The file has exactly `outcome_of` (the run's
   row id), `head` (the 40 hex of the commit that was pushed; null only when nothing was pushed and the verdict
   is `unknown`), `verdict` (`accepted`, `rejected`, or `unknown` when no verdict was given: an outage, a
   session that ended before its push), `source` (where that was read: the result file's commit, the
   `session_start` row that states it) and `missed`: empty unless `rejected`, then one object for each reason
   of the rejection with `reason`, `claim` (the defect in a sentence), `in_diff` (true when the defect was in
   the diff the run read, false when it came into the push after the run or lies outside what a packet shows;
   found by running the reproducer on the run's `head`, not by reading) and `lesson` (the row id of the lesson
   written from it, in force as the row is written, or null). A miss with `in_diff` true takes its lesson in
   that session, the lesson row first: every later packet carries the lessons in force, and that is how a
   missed class reaches the agent. A run's outcome is not written in the run's own session (refused).

One run (rule `recorded`):

5. `python3 tests/agent_run.py packet --agent <name> --base <last accepted SHA> --head <the commit's SHA> --out
   <a new directory outside the brain>`. The packet is the whole of what the agent is given: the diff and its
   paths, every lesson in force, whole, and the agent's memory, the findings of its earlier runs that were
   refused, are carried or are not judged yet (rule `remembers`). Only an agent the capsule loaded for this
   session has a packet.
6. Start the agent with the Agent tool: the type `brain:<name>`, a stated effort, and the bytes of the
   packet's `message.txt` as the whole prompt, nothing added. No other type of agent is started, and no agent
   is started with a prompt written by hand, and a running agent is sent no further text (`SendMessage`): such
   a call has no row of this session and refutes `recorded`.
7. Read each finding against the code yourself and give it a verdict (rule `judged`): `caught` with the test
   that was red before the repair and green after, or the rival's or the referee's confirmation; `false_alarm`
   with the reason; `carried` when it is true and this push does not repair it, with `carried_in` naming the
   report (`reports/<file>.json`) or the ledger row that keeps it open; a finding that says an earlier one again
   keeps the agent's `repeat_of`. `unjudged` is for a run still being read; no finding leaves the session so.
8. `python3 tests/agent_run.py record --packet <directory> --run <the run's file> --snapshot <HEAD's SHA>`
   writes the run's row: agent, model, effort, the definition's sha256, the sha256 of the diff, of the lessons,
   of the memory and of the message as the packet wrote them (a file of the four changed since is refused),
   tokens, wall time and the findings; the cost is null there, with the reason in `not_measured` (step 3 of
   the next session writes it). A later reading of a run's findings (the rival's answer, a finding
   judged in a later session) is `python3 tests/agent_run.py record --agent <name> --run <a file with amends
   and findings> --snapshot <HEAD's SHA>`.
9. `python3 tests/agent_rules.py` again, and `python3 tests/agent_run.py measure --agent <name>`. The lesson
   row that carries the first command as its `recheck` runs it at every push (`skills/push/SKILL.md`, step 5).

A new agent or a changed definition (rule `defined`): the file `agents/<name>.md` starts its text with
`Origin. Gap: ` (the measured gap it is born for, with the ledger rows) and holds `Measure: ` (how its runs are
measured); it states its `tools`, and they only read (`Read`, `Grep`, `Glob`); the choice is a `decision` row.
It is loaded by the session after the push that adds it, so its first run is in a later session. An agent that
would write or run commands is not added under these rules: the rule is rewritten first, with the check its
output then needs.

When a rule is refuted: `earns` (five sessions with nothing caught, or five sessions and a cost over what the
agent can have saved, `cost_over_gain`, or more false alarms than catches under the rules) rewrites or removes
the definition in that push; `answered` (a run of an earlier session without its outcome, or a miss in a run's
diff without a lesson) is closed by writing the row; `remembers` (one finding in ten or more is a repeat) and
`improves` (after five sessions whose runs under the design in force have an accepted or rejected outcome, a
higher share of missed defects than under the design before it, or neither a lower one nor a higher share of
caught findings) are recorded in a `decision` row with the measure's output, and the rule is designed again:
its `says`, its `expects` or its check changes in `skills/agents/rules.json`, never only the number that
failed. A refuted `improves` closes the design: the sha256 of every rules file its runs carry
(`rules_sha256` in their rows) goes into the file's `designs` with the rows that recorded which rule
closed it and on what numbers, so the next design is judged against that one and its refutation stays readable. The first
design (the runs before any rule are design 0) was closed so: caught findings a run and tokens per caught
finding followed what each push held, not the rules.

What these rules do not reach, stated: an agent whose task is no diff has no packet form yet; a run's cost is
the launcher's derived figure, known a session later and only for a run the mirror can cost (of two runs of
one model in one session it gives a floor each, summed apart by `measure`); what a
`caught` finding saved is measured nowhere, so `measure` reads E692's "costs more than it saves" from one side
only (`cost_over_gain`: the agent's least cost against one median session per `caught` finding; `earns` is
refuted by it after five sessions) and an agent under that line is not shown to earn; a comparison of sessions with and
without an agent is not measured here. A miss is known only from a rejection: a defect neither the agent nor
the rival found is counted nowhere, an outage leaves a run's outcome `unknown`, and with one rejection among
the runs so far the missed share moves by whole runs. The caught share rests on the Founder's own verdicts.
