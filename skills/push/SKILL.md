---
name: push
description: The order of work before any push to the brain's main, records-only pushes and exit requests included. Use it before every git push of main.
---
Every push to `main` goes through these steps, in this order. There is no kind of push that skips them: a push
that changes only `reports/` or the ledger is read by tests too (71f64f0 was rejected, test_failed T38, for one
line of a report pushed without a run; founder ledger f1359 onward).

1. Finish every edit that is not a ledger row first: code, tests, `snowball-tests.json`, `reports/`, `docs/`,
   `exit-request.json`. Rows that describe the run come after the run. While editing,
   `python3 tests/prepush.py quick --since <last accepted SHA> -j 3` runs only the manifest's discover steps whose
   test files reach a changed path by import; it writes no stamp and stands in for no step below, and the paths
   it prints as `unseen` are the ones no step was chosen for.
2. If `referee/` or the map's inputs changed: from `referee/`, `python -m status.depmap brain .` must equal
   `docs/map/brain.md` (regenerate it in the same push); if code under `referee/` changed,
   `python3 tests/vec_compare.py --before <last accepted SHA>` and read every difference.
3. If the change holds more than records (anything outside `founder-ledger.jsonl` and `reports/`): commit it to
   the work branch, then `python3 tests/push_size.py --head <that commit's SHA>`: the diff the rival will be
   handed, against the limit the referee's last result states. A band that is not `fits` is repaired now, by
   what `paths` names, before anyone reads the diff (dd8afd5 and 6820381 were rejected `prompt_too_large`, each
   for a mutant record a whole run rewrote inside the tree; `referee/tests/mutate.py --record` takes a file
   outside the brain, the branch `kayit/mutant-rows`, and refuses one inside). Then
   `python3 tests/agent_run.py packet --agent push-reviewer --base <last accepted SHA> --head
   <that commit's SHA> --out <a new directory outside the brain>` and start the agent `brain:push-reviewer` with
   effort `high` and the bytes of that directory's `message.txt` as its whole message (a SHA and a stated
   effort, so the run's row names the commit that was read and the effort it was read at; the message as
   written, so the row names what the agent was given). Read each finding against the code. A true one is
   repaired with a test that is red before the repair and green after (verdict `caught`); a wrong one is refused
   with its reason (`false_alarm`); a true one this push does not repair is `carried` and names the report or
   the ledger row that keeps it open; one not yet judged is `unjudged`, and no finding leaves the session so.
   The agent adds a check and stands in for none: the steps below run whole whatever it found. Its row is
   written in step 5 with `python3 tests/agent_run.py record --packet <directory> --run <the run's file>
   --snapshot <HEAD's SHA>`; the run file's fields are in the tool's docstring. The skill `brain:agents` is the
   whole order of an agent's run and the rules it is measured by.
4. `python3 tests/prepush.py run -j 3`. It runs the whole manifest as `tests/run_like_referee.py` does and writes
   a stamp only when every command is green on a tree that did not change during the run. Red: repair the cause,
   then run again; do not push. The commands are timed on a python that keeps no bytecode (`cold_home`), as the
   referee's durations say its own does, so a command over the limit (600 s) is red here; where that python
   cannot be built the run is `timed_warm` and writes no stamp. Read each `duration_ms`: a command over half
   the limit is the next thing to make cheaper.
5. Write the ledger rows with `python -m ledger.founder append` (from `referee/`); among them, in every
   session, the outcome row of each agent run of an earlier session that has none (`brain:agents`, step 4: a
   push with no agent run owes it too, and `python3 tests/agent_rules.py`, a lesson's recheck, is red without
   it). Then
   `python3 tests/lesson_recheck.py record --snapshot <HEAD's SHA>`: it runs the `recheck` of every lesson in
   force and appends one row with each result. Not ok: for each lesson it names, repair the code (step 4 again),
   or close the lesson with a row whose refs carry `closes:<row_id>` and whose summary says why, or replace it
   with a new lesson that closes it (tohum/26g); a lesson is not left failing unseen. Then
   `python -m ledger.founder check`.
6. Commit. Then `python3 tests/prepush.py check -j 3`: ok only when the committed tree is the stamped tree, the
   ledger only grew and the push's size is `fits` by `tests/push_size.py` (`size` in its line); it runs again
   the commands that read the ledger. Push only on `"ok": true`. Any reason it
   prints is the next thing to repair; a changed file means step 4 again.

What a green check does not say is in the docstrings of `tests/prepush.py` and `tests/run_like_referee.py`
(this machine is not the referee's sandbox; the vectors' expected values are not here).
