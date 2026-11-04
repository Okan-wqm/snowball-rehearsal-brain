# (B): the exit audit and the rehearsal's stops

Generated, never edited by hand: `python tests/test_rehearsal.py --doc` from `referee/` (`status.exit_b`). The register is checked current by `tests/test_exit_b.py`, each case by `tests/test_rehearsal.py`. The rehearsal is an in-process world (fake runner, git, GitHub, Rekor and model): "no reason" is the gate's answer there, not a measurement of the live loop.

## The register: each 10a condition and where it is judged

From `spec/asama-0/10a-cikis-canli-dongu.md` and `referee/harness/pass_row.py` (`python -m status.exit_b register`).

| 10a row | tag | where |
|---|---|---|
| `#aktarim` | `#aktarim` | not checked: the import's signed result and the referee repository's setup/imports.jsonl (tohum/25a) |
| `#oyuncak` | `#oyuncak` | not checked: the toy tree's hash beside (A)'s toy_tree_sha256 (the activation's input) |
| `#hedefler` `#drift` | `#hedefler` | not checked: the rulesets and the App as genesis reads them from the API (activate.genesis); #genesis judges the genesis row's place, not its facts |
| `#hedefler` `#drift` | `#drift` | not checked: the rulesets and the App as genesis reads them from the API (activate.genesis); #genesis judges the genesis row's place, not its facts |
| `#genesis` | `#genesis` | judged by `harness.pass_row` (`#genesis`) |
| `#taban` | `#taban` | judged by `harness.pass_row` (`#taban`) |
| `#kirmizi` `#kanarya` | `#kirmizi` | not checked: each kos run's results (runner.kos), which brain/state does not hold |
| `#kirmizi` `#kanarya` | `#kanarya` | not checked: each kos run's results (runner.kos), which brain/state does not hold |
| `#getir` `#birim` | `#getir` | not checked: getir's and kos's job lines, which brain/state does not hold |
| `#getir` `#birim` | `#birim` | not checked: getir's and kos's job lines, which brain/state does not hold |
| `#merge` | `#merge` | judged by `harness.pass_row` (`#merge`) |
| `#ret` | `#ret` | judged by `harness.pass_row` (`#ret`) |
| `#oracle-ayirt` `#mandal` `#sifir-test` | `#oracle-ayirt` | not checked: the gate's judgement of each merge (loop.decide), recorded only as the merge decision; not judged again here |
| `#oracle-ayirt` `#mandal` `#sifir-test` | `#mandal` | not checked: the gate's judgement of each merge (loop.decide), recorded only as the merge decision; not judged again here |
| `#oracle-ayirt` `#mandal` `#sifir-test` | `#sifir-test` | not checked: the gate's judgement of each merge (loop.decide), recorded only as the merge decision; not judged again here |
| `#kapsama-kaydi` | `#kapsama-kaydi` | judged by `harness.pass_row` (`#kapsama-kaydi`) |
| `#nobetci` `#hayatta` | `#nobetci` | judged by `harness.pass_row` (`#nobetci #hayatta`) |
| `#nobetci` `#hayatta` | `#hayatta` | judged by `harness.pass_row` (`#nobetci #hayatta`) |
| `#geri-alma` | `#geri-alma` | judged by `harness.pass_row` (`#geri-alma`) |
| `#model` `#belirtec` `#prompt` | `#model` | judged by `harness.pass_row` (`#model #belirtec`) |
| `#model` `#belirtec` `#prompt` | `#belirtec` | judged by `harness.pass_row` (`#model #belirtec`) |
| `#model` `#belirtec` `#prompt` | `#prompt` | not checked: a prompt refused for a secret pattern starts no process and writes no row (loop.cagir) |
| `#kok` | `#kok` | judged by `harness.pass_row` (`#kok`) |
| `#durum` | `#durum` | judged by `harness.pass_row` (`#durum`) |
| `#main` `#guvenlik-yolu` | `#main` | not checked: the target's rulesets and target.write's refusals; brain/state records no write |
| `#main` `#guvenlik-yolu` | `#guvenlik-yolu` | not checked: the target's rulesets and target.write's refusals; brain/state records no write |
| `#pass` | `#pass` | written: `harness.pass_row.write` on the toy's `brain/state`; no job calls it yet (seed-046, seed-048) |

## The rehearsal's stops

<!-- case:without-fixtures -->
### No drill fixtures secret (the operator writes it at the activation, tohum/26f)

(B) stops at run 4: run 4 repeats run 3. The toy's gate: closed. The copy: waiting (never served).

| judged condition | the toy's gate reasons at the stop |
|---|---|
| `#genesis` | no reason |
| `#taban` | no reason |
| `#merge` | no reason |
| `#ret` | no reason |
| `#kapsama-kaydi` | no reason |
| `#nobetci #hayatta` | no reason |
| `#geri-alma` | `toy:drill_inputs_missing` |
| `#kok` | no reason |
| `#durum` | no reason |
| `#model #belirtec` | no reason |

Waits for: no report (the stop is the case's own input)

<!-- case:with-fixtures -->
### Drill fixtures of the three causes

(B) stops at run 11: `yaz` stopped on `drill_fail` (target `t1`). The toy's gate: closed. The copy: waiting (never served).

| judged condition | the toy's gate reasons at the stop |
|---|---|
| `#genesis` | no reason |
| `#taban` | no reason |
| `#merge` | no reason |
| `#ret` | no reason |
| `#kapsama-kaydi` | no reason |
| `#nobetci #hayatta` | no reason |
| `#geri-alma` | `toy:drill_fail:b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0:cause_mismatch`, `toy:cause_unshown:build_break` |
| `#kok` | no reason |
| `#durum` | no reason |
| `#model #belirtec` | no reason |

Waits for: `seed-044-revert-facts-producers` (open)

<!-- case:stale-patches -->
### Drill patches on the file the toy's merge changed (a set 26f's producer refuses)

(B) stops at run 4: run 4 repeats run 3. The toy's gate: closed. The copy: waiting (never served).

| judged condition | the toy's gate reasons at the stop |
|---|---|
| `#genesis` | no reason |
| `#taban` | no reason |
| `#merge` | no reason |
| `#ret` | no reason |
| `#kapsama-kaydi` | no reason |
| `#nobetci #hayatta` | no reason |
| `#geri-alma` | `toy:cause_unshown:test_regression`, `toy:cause_unshown:build_break`, `toy:cause_unshown:lint_regression` |
| `#kok` | no reason |
| `#durum` | no reason |
| `#model #belirtec` | no reason |

Waits for: no report (the stop is the case's own input)

