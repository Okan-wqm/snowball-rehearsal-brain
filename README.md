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

`tests/mutant-rows.jsonl` on `main` is the record as it stood at the accepted bb80d93; nothing writes it any more.
