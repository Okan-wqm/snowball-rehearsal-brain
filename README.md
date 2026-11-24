# kayit/mutant-rows: the kept outcomes of the mutant runner

This branch holds one working file, `mutant-rows.jsonl`: the rows `referee/tests/mutate.py --record FILE` reads
and writes (its docstring, "Kept outcomes", is the rule; a row is `{file, id, outcome, fp}`).

Why it is here and not on `main`: a row is keyed by a fingerprint over the bytes of everything its mutant
reaches, so one edited line in a shared module replaces every row. On `main` that replacement is part of the
diff the rival is handed; on 2026-11-15 it was 820062 of 875761 bytes and the push (6820381) was rejected
`prompt_too_large` (founder ledger f1216 and the rows after it). The record is a cache of runs, read by nothing
on `main`; what a session claims from it (how many killed, at which tree) is written in the ledger with this
file's sha256 and this branch's commit.

Use, from a clone of the brain:

    git fetch origin kayit/mutant-rows
    git show origin/kayit/mutant-rows:mutant-rows.jsonl > /tmp/kayit/mutant-rows.jsonl
    python3 referee/tests/mutate.py referee/tests/mutants/*.json --touched <last accepted sha> \
        --record /tmp/kayit/mutant-rows.jsonl -j <cpus of cpu.max>

then commit the file back to this branch (a commit on top, never a rewrite) and push. The branch is not merged
into `main` and is not a work branch: it is not deleted when a job ends.

History of the copy on `main`, corrected 2026-11-24 (founder ledger f2136): the sentence that stood here, "nothing
writes it any more", did not hold. `tests/mutant-rows.jsonl` on `main` was written again from 88c2586 (2026-11-18)
to dd8afd5, and dd8afd5 was rejected `prompt_too_large` for it, the second time. The rows `main` held at f02cb97
(4130) and at dd8afd5 (401) that this file did not have were appended here on that day (3916 and 273 lines).
Since then `referee/tests/mutate.py` refuses a `--record` inside the brain (`record_in_brain`), and the copy on
`main` is being removed in pushes small enough for the rival's prompt.
