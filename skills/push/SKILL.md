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
3. `python3 tests/prepush.py run -j 3`. It runs the whole manifest as `tests/run_like_referee.py` does and writes
   a stamp only when every command is green on a tree that did not change during the run. Red: repair the cause,
   then run again; do not push.
4. Write the ledger rows with `python -m ledger.founder append` (from `referee/`). Then
   `python3 tests/lesson_recheck.py record --snapshot <HEAD's SHA>`: it runs the `recheck` of every lesson in
   force and appends one row with each result. Not ok: for each lesson it names, repair the code (step 3 again),
   or close the lesson with a row whose refs carry `closes:<row_id>` and whose summary says why, or replace it
   with a new lesson that closes it (tohum/26g); a lesson is not left failing unseen. Then
   `python -m ledger.founder check`.
5. Commit. Then `python3 tests/prepush.py check -j 3`: ok only when the committed tree is the stamped tree and the
   ledger only grew; it runs again the commands that read the ledger. Push only on `"ok": true`. Any reason it
   prints is the next thing to repair; a changed file means step 3 again.

What a green check does not say is in the docstrings of `tests/prepush.py` and `tests/run_like_referee.py`
(this machine is not the referee's sandbox; the vectors' expected values are not here).
