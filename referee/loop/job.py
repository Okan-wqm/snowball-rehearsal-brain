"""The loop workflow ``loop.yml`` and its jobs, from one registry (stage 0, MF17).

Rules: asama-0/14 row 17 (module ``.github/workflows/loop.yml``, steps D0-D8), asama-0/09 test 46, tohum/08 item 1
(five jobs in one workflow; top-level ``permissions: {}``; every job's first step is the seed's ``control`` command;
no ``${{ github.* }}`` in ``run:``; actions pinned by SHA; ``persist-credentials: false``; no
``pull_request_target``, ``workflow_run``, ``issue_comment``; jobs run only on ``main``; a job that runs code
carries no secret and a job that carries a secret runs no code), asama-0/01 (the D0-D8 step table and which job
each step runs in), tohum/24 (trigger: a schedule opened by ``control.json`` ``loop_schedule``, and runs the
operator starts by hand in (B)), tohum/25a (the import puts ``referee/.github/workflows/loop.yml`` at the referee
repository's ``.github/workflows/loop.yml`` and ``referee/`` at its root, so the workflow runs ``python3 -m
loop.job`` from the checkout's root).

**One source.** ``JOBS`` holds each job's steps, the MFs it calls, its permissions, the secrets it receives, the
jobs it needs, the artifacts it downloads and the one it uploads. ``render()`` writes the workflow from it, byte
for byte the committed ``referee/.github/workflows/loop.yml`` (test 46 compares them); a change is made here and
the file regenerated with ``python -m loop.job render > .github/workflows/loop.yml`` from ``referee/``. Every
artifact edge of ``JOBS`` (an upload and a download of it) has one status in ``tests/test_loop_handover.py``: a test
that runs both jobs on the handed-over bytes, a stated unread download, or a producer or consumer that stops unwired.

**The shape of every job**, in this order:

1. ``control`` (D0): fetches the referee repository's ``main`` (``bootstrap/`` and the root files, so
   ``control.json`` as it is now, not as it was at the run's commit) and runs the seed's ``control`` command.
   A non-zero exit (the kill switch, or an unreadable ``control.json``) fails the job and every later step and
   every job that needs it is skipped. Exit 0 writes ``go=true`` or ``go=false`` to ``$GITHUB_OUTPUT``;
   ``go=false`` (a scheduled run while ``loop_schedule`` is not true) ends the job green with every later step
   skipped, i.e. ``paused``. The command's flags are this module's assumption (no seed page gives them).
2. the job's install steps (``Job.installs``; tohum/29s, the text in ``loop.inputs.STEPS``): ``sigstore`` in ``cek``
   and ``yaz`` (the pinned Sigstore from the control step's clone, through the seed's license gate, into
   ``$RUNNER_TEMP/sig``), ``claude`` in ``cagir`` (``npm ci`` of the pinned CLI lock in the control step's clone and
   the version check). They carry no secret: a job's secrets are only in its ``run`` step's ``env``.
3. checkout of the run's own commit of the referee repository, ``persist-credentials: false``.
4. (``yaz`` only) the writer scope, ``python3 -m loop.job scope`` (``scope``: ``owner`` and ``repositories`` from
   the ``repo`` of every ``targets[]`` entry of the checkout's ``setup/summary.json``, one owner), then the writer
   App token made inside the job with those two inputs: no operator variable names the owner (tohum/29s). The
   token is asked with ``APP_INPUTS``' four permissions, tohum/25 item 6's.
5. one download per artifact the job reads, by the producing job's artifact id, ``digest-mismatch: error``.
6. ``python3 -m loop.job run <job>``, with the expected artifact digests and the job's secrets in ``env``.
7. the upload of the job's artifact, whose id and digest are job outputs.

Every step after ``control`` runs only if ``go`` is true; no step continues on error.

**Targets** (tohum/29s "Hedefler"). A run serves every ``targets[]`` entry of the checkout's
``setup/summary.json`` in the array's order (``loop.cek.targets``); no variable or trigger input chooses one. ``cek``
alone decides which are served: a ``copy`` entry whose target has neither ``brain/state`` nor ``brain/integration``
is not served this run (its line ``{target, waiting: copy_genesis, heads}``: it writes nothing and is not red, 29s)
unless the copy's genesis gate is open (below); every other entry is. ``cek``'s ``out/pulled`` holds ``served.json``, the served ids in order, and one ``<id>/`` per
served target (``loop.pulled`` "Served"); each later job reads that list from its ``in/pulled`` and serves each id
in turn, every artifact path below being that target's own directory (``in/pulled/<id>``, ``out/deps/<id>``,
``in/deps/<id>``, ``out/results/<id>``, ``in/results/<id>``, ``out/response/<id>``, ``in/response/<id>``; a
``pulled`` whose ``target.id`` is not its directory's name is ``pulled_invalid`` ``target_mismatch``). The job line
holds one line per target in ``targets``; the first target refused stops the job, no later target is served this
run, and its ``reason``, ``reasons`` and id (``target``) are the job's (``run``). Each target's cycle has the same
cycle id (``<GITHUB_RUN_ID>-<GITHUB_RUN_ATTEMPT>``). D8's drill is the toy's (asama-0/08 row 4): off on any other
kind.

**The genesis cycle** (tohum/26a ``activate``: the operator's first cycle, in ``koş`` and ``yaz``; tohum/25a row 7).
A ``toy`` entry whose target has neither ``brain/state`` nor ``brain/integration`` is served as its genesis cycle:
``cek`` reads its ``main`` (``refs/heads/main``, credential-less, ``loop.fetch.heads``; absent is
``head_missing:main`` beside the two others) and assembles ``pulled`` from that commit's tree with
``loop.pulled``'s genesis form (no ``brain/state`` head, both chains empty); there is no state to verify or anchor,
so the target's line has ``genesis: true`` and ``state`` and ``root`` ``null``. ``getir``, ``kos`` and ``cagir`` run
on it as on any cycle (no merge is unfinished: nothing is watched); ``yaz`` runs D5 as on any cycle and then, instead
of ``loop.write_cycle``, ``activate.activate`` (``yaz_genesis``) with D5's answer, D3's base run
(``loop.watch.base_run``: ``base.jsonl`` and the index's ``base_run_sha256``; absent is ``activation_refused``
``base_run_missing``) and D4's cost rows, and the checkout's ``setup/summary.json``, ``setup/imports.jsonl`` and
``setup/security-ledger.jsonl`` (tohum/26c, 29o; an unreadable one is unusable, exit 2), ``pulled``'s policy and its one
unit as the recipe: the genesis row, the cut at that commit, D5's merge, the ratchet base and the orphan
``brain/state`` commit. Its API is ``writer_transport`` with the App's own credential (``WRITER_APP_ID`` and
``WRITER_APP_PRIVATE_KEY``, in the ``yaz`` step's ``env`` beside the token; unset is unusable): genesis' first read,
``GET /app``, is answered only to the App's JWT (``target.app_jwt``; spec/tohum/CHANGELOG.md 2026-11-15), every other
request goes with the token, and an ordinary cycle's writer is given neither secret (the job's ``drift.check`` is: below). Its refusals before any
write (``activate``'s reasons, ``base_moved`` among them) are
``activation_refused`` with the reasons; a hard stop at the cut or after it is ``hard_stop`` with ``written`` (none when the cut itself failed). The line has
``done`` ``["D5", "D6"]``, ``drill`` ``{action: off, why: genesis}`` (D8 starts in the next cycle) and ``written``
(``GENESIS_WRITTEN`` of ``activate``'s answer, ``genesis: true``). The next run's ``cek`` finds both heads and serves
an ordinary cycle.

**The copy's genesis gate** (tohum/25a row 7, 29s: the copy's genesis waits until the toy's cycles 1-5 are green,
read from the toy's ``brain/state``; ``harness.pass_row`` "The copy's genesis gate"). ``yaz`` judges it on each toy's
ordinary cycle (``yaz_gate``, before anything is written: ``harness.pass_row.gate`` on ``pulled``'s state with the
toy's candidates' ``expect.json``, D8's seed and catalog (``loop.drill.inputs``), and the checkout's
``setup/imports.jsonl``), unless the toy's run already holds the gate's row; the line has ``gate`` ``{verdict:
open|closed, conditions, unusable?}`` (only the conditions with reasons). An open gate adds the ``events``/
``copy_gate`` row to the cycle D6 writes (``loop.write_cycle``'s ``gate``). The next run's ``cek`` reads it: after a
``toy`` entry is served on an ordinary cycle, ``harness.pass_row.gate_opened`` of its ``pulled`` ledger (the bytes
D1 verified); a ``copy`` entry later in ``targets[]`` with neither head is then served as its genesis cycle at its
``targets[].base_sha`` (``base_sha_invalid`` when it is not 40 lowercase hex; nothing fetched), assembled with
``loop.pulled``'s genesis form like the toy's, and ``yaz`` runs ``activate`` on it (``activate`` checks the copy's
facts and that ``base_sha`` is the commit ``pulled`` was read from). A copy before the toy in ``targets[]``, or a run
whose toy is refused, in its genesis cycle or without the row, leaves the copy waiting. Out of scope, stated: a
target with exactly one of the two heads (an activation stopped after its cut) stays ``head_missing`` (25a's
failure rule leaves it to the operator); a second genesis after a re-import (tohum/26d) is ``activate``'s
``already_activated`` (seed-047).

**The PASS row** (tohum/26d, asama-0/08 row 9, 10a ``#pass``; ``harness.pass_row``). ``yaz`` judges it on each toy's
ordinary cycle once the toy's run holds the gate's row (``yaz_pass``, before anything is written), until the run holds
its PASS row (``harness.pass_row.passed``): ``harness.pass_row.judge`` on the toy's and the copy's ``pulled`` states
(the bytes this run's D1 verified; the copy is the one served target of kind ``copy``, read from its
``in/pulled/<id>``), each one's candidates' ``expect.json``, D8's seed and catalog, the checkout's
``setup/imports.jsonl`` and the (A) result its last import names, ``setup/results/<result_sha256>.json``
(``harness.pass_row.result_path``; tohum/26c, 29s). The line has ``pass`` ``{verdict: PASS|FAIL, conditions,
unusable?}``, or ``{waiting: copy_not_served|copy_genesis}`` when no copy with a state is served this run (a copy
waiting for its genesis or in its genesis cycle). A ``PASS`` adds the ``events``/``pass`` row with the judge's
payload to the cycle D6 writes (``loop.write_cycle``'s ``passed``); a ``FAIL`` writes nothing more and the cycle
goes on. An input the judge cannot use is ``FAIL`` with ``unusable``; an unreadable checkout file (the result
among them) and a second served copy are unusable (exit 2), nothing written. Both states are the ones this run
started from: the copy's cycle of the same run comes after the toy's in ``targets[]`` and is judged by the next run.

**What ``run`` does now.** It checks the job's environment contract first: a job that runs code (``getir``,
``kos``) refuses to start when any secret of another job, the OIDC request variables or ``GITHUB_TOKEN`` is in its
environment (``secret_in_code_job:<NAME>``, exit 1). Every job that reads the tree extracts it from ``pulled`` into
a fresh ``$RUNNER_TEMP/work/<job>-*/tree`` (``_pulled_tree``, ``cek`` its own assembly through ``_extract``; a
refused tree is ``pulled_invalid``). Then:

- ``getir`` runs D2 (``getir_d2``), and with it the whole job: it reads ``$RUNNER_TEMP/in/pulled`` as ``kos`` does
  (the same refusals, the same one unit), runs the recipe's static check (``profile.unit_verify.check_recipe``,
  the one ``kos`` runs again before staging; a reason is ``recipe_refused`` with the reasons, nothing fetched) and
  then MF5's ``runner.deps_npm.fetch`` on the recipe's lock in the tree, with the default registry (the one the
  static check allows; stage 0 reads no ``registry_egress``), the recipe's ``install_scripts_required``, the
  policy's license lists and ``deps_bytes`` tightened by the recipe's ``limits.deps_bytes``, fetching over HTTPS.
  The artifact is written to ``$RUNNER_TEMP/out/deps/<address>/``, which must not exist before (exit 2). A refusal
  is ``deps_refused`` with MF5's reasons (exit 1, nothing uploaded); a fetch that fails is no verdict (exit 2). On
  success the line has ``ok`` true, ``done`` ``["D2"]``, ``deps`` (``address``, ``packages``, ``bytes``,
  ``artefact``) and ``licenses`` (the report, not gated: the target's dependencies do not enter the product), exit
  0, so the upload step runs. A lock with no packages gives an artifact with none.
- ``kos`` runs D3 (``kos_d3``): it reads ``$RUNNER_TEMP/in/pulled`` with ``loop.pulled.read`` (a refusal is
  ``pulled_invalid`` with the reasons), takes the recipe from its ``units.json`` (stage 0 runs one unit: exactly
  one entry in ``units``, else ``units_not_one``), unpacks the tree under ``$RUNNER_TEMP/work`` and calls
  ``runner.kos.results`` with the policy, the ``targets[]`` entry, ``RED_CONTROL``, every candidate's
  ``diff.patch`` and the ``deps`` artifact, ``runner.deps_npm.artifact_in`` of ``$RUNNER_TEMP/in/deps`` (the
  download of ``getir``'s ``out/deps``; a root that is not exactly one ``<address>/`` directory is ``deps_invalid``,
  nothing run; ``None`` when ``in/deps`` is absent or empty: ``unit_verify`` then accepts only a lock without
  packages), and ``pulled``'s organs (``organs``: its ``organs.json`` as the accepted set and every organ it
  carries; ``runner.kos.results`` calls each through ``runner.organs`` only, "The organs" there, on the
  snapshot directory), writing ``$RUNNER_TEMP/out/results``. The snapshot (P1 MF2): before ``runner.kos.results``,
  ``snapshot.make.write`` writes ``pulled``'s ``snapshot.json`` document out from the extracted tree into
  ``kos-*/snapshot``; a document or a tree it refuses is ``snapshot_refused`` with its reasons and nothing runs;
  the target's line has ``snapshot`` (``snapshot_id`` and the counts of ``files`` and ``links``). The mutations
  (P1 MF3, asama-1/13a: the tool runs in ``koş``): every entry of ``pulled``'s ``mutations.json`` that is an
  object with a string ``diff`` is given to ``runner.kos.results`` (``mutations``, "A mutation" there: three lint
  runs of the base worktree with the diff applied, ``m/<mid>/mut.jsonl``, the index's ``mutations``); an entry
  of another shape is not run (``yaz`` refuses it). The image is fetched in this step, on the host, by
  ``runner.kos.results`` itself before its first contained run (tohum/08 item 2; ``runner.contained.ensure_image``:
  the workflow has no pull step of its own, and a pull that fails prints docker's reason on this step's stderr and
  gives the base ``no_verdict`` ``image_unavailable``). Before the tree is extracted it reads ``pulled``'s
  ``state/ledger.jsonl`` with ``ledger.serial.unfinished``, the reading ``yaz`` uses (a ledger it cannot read is
  ``state_refused`` with its reasons, nothing run): with no unfinished merge nothing is watched; when the one
  unfinished merge is ``brain/integration``'s head (the tree ``pulled`` carries), ``runner.kos.results`` runs D7's
  sentinel there (``watch``: ``sentinel.json`` and the index's ``sentinel``); any other set of unfinished merges is
  ``sentinel_unplaced`` with ``unfinished:<sha>`` reasons, exit 1, nothing run (a red could not be laid on one
  merge). Its index is in the output (``index``), ``ok`` is true and ``done`` is ``["D3", "D7"]`` when a merge was
  watched, else ``["D3"]`` (D7 has nothing to watch), exit 0: the upload step runs and ``yaz`` reads the results
  (D5) and the sentinel's verdict (its half of D7, below). ``kos`` carries no step of D8: the drill's plant is a
  write (``yaz``), and its planted merge is a ``drill``/``plant`` row, which ``ledger.serial`` counts as a merge, so
  the next cycle's ``kos`` watches it with D7's own sentinel run, at ``brain/integration``'s head like any merge.
- ``yaz`` runs D5 (``yaz_d5``): it reads ``control.json`` from the ``control`` step's clone
  (``$RUNNER_TEMP/control/control.json``; unreadable is unusable, exit 2), ``$RUNNER_TEMP/in/pulled`` as ``kos`` does
  (the same refusals, the same one unit), extracts the tree under ``$RUNNER_TEMP/work`` and calls ``loop.decide`` on
  ``$RUNNER_TEMP/in/results`` with the soft freezes in force in ``pulled``'s ledger (``gozcu.watch.closed``: under
  one every candidate carries ``frozen:<trigger>``; a ledger whose lift row names no freeze is ``state_refused``):
  ``decisions`` (every candidate's ``decision`` and ``reasons``) and ``merge`` are in the
  output and ``done`` is ``["D5"]``. Once D5 has decided, the dev cases (P1 MF3, ``yaz_cases``): ``cases.build.build``
  judges ``pulled``'s ``mutations.json`` against the results (``index.json``'s ``mutations`` and ``base_run_sha256``,
  ``base.jsonl`` and each ``m/<mid>/mut.jsonl`` read under its hash) with ``brain/integration``'s head as
  ``base_sha`` and the one unit's ``path`` as the unit's root of a case's group; the target's line has ``cases``
  (``{cases, oracle, refused}``, "The case" there) whatever the
  steps after D5 gave, and D6 adds those cases to the dev case set, ``<state_root>/cases/dev.jsonl``, in the
  cycle's ``brain/state`` commit (``loop.write_cycle``, ``cases.store``, tohum/26m: ``written.cases`` names
  the ids added, kept and refused; a genesis cycle, which ``activate`` writes, and a cycle D6 does not
  write add none); ``build`` makes each planted violation's fingerprint with ``findings.write.fingerprint``
  on the extracted tree with the mutation applied (tohum/26q (7)). No harness report is scored (P1 MF4,
  tohum/26q (6)): no cycle has a hunter run on its cases' snapshot (the first hunter is stage 1 MF1's), so the
  target's line has ``harness`` ``{reason: "no_hunter_run"}`` (``NO_HUNTER_RUN``) in every cycle, with a case and
  without: no report, no verdict, and ``harness.score`` is called by nothing here (``status/off_live.json``).
  The harness reaches no model (P1 MF5, ``harness.offline``): the job's first step, before ``pulled`` is opened
  and before MF6's reads below (``run``), is ``yaz_offline``, which reads the import statements of the running
  code's harness (``CODE_ROOT``); a reason there refuses the job, not a target (``harness_online`` with the
  reasons, ``targets`` ``[]``, no ``target``, exit 1), and the job's line otherwise has ``offline`` (``{modules}``,
  how many modules the reading reached). The copy's genesis gate, the PASS judgement and
  D8's judgement (``loop.drill``) run inside ``harness.offline.run``, and a socket or a child process one of them
  asks for refuses the target (``harness_online``, reasons ``event:<audit event>``) before D6 writes ``brain/state``.
  The organs' outputs (P1 MF10, ``yaz_organs``; read after the dev cases are built): for every organ in the results' ``index.json`` (``organs``;
  an index that is absent, not JSON or without that object has none) the output ``kos`` kept is read by the hash
  its entry names (``output.sha256``) with ``runner.organ_output.read``, which returns no byte that does not lead
  back to that hash; the target's line has ``organs``, per organ ``{read: true, sha256, files, bytes}`` (how many
  files and bytes were read) or ``{read: false, reasons}`` (``output_not_kept`` when the entry names no hash: an
  organ not called, a run not valid, an output not kept; else ``organ_output``'s reasons: missing, changed,
  unusable). The bytes read are dropped: ``yaz`` has no consumer of them (the packages among them
  stand in the results by ``kos``'s hand, below, and are read there), and a refused output stops nothing today.
  The reruns (P1 MF11, ``yaz_reruns``; right after the organs' outputs): for every name under the
  results' ``candidates/`` and every key of the index's ``reruns`` (``loop.candidates.names``),
  ``runner.candidate_rerun.reran`` is asked for the package and the gate's files, which it hands out only for a
  package ``kos`` reran ("Before the gate" there); the target's line has ``reruns``, per id
  ``{reran: true, package_sha256, verified}`` (``verified``: whether ``kos`` verified the rerun; one it did not
  is rejected by D5 with its entry's reasons) or ``{reran: false, reasons}`` (``package_missing``,
  ``rerun_missing``, ``rerun_files_missing``). The line is a report: D5 (``loop.decide``, P1 MF12) reads those of them that
  are candidate ids itself through ``loop.candidates`` in every cycle but the genesis cycle, a candidate that was not rerun takes
  no decision there (tohum/26p (5): its reason stands on this line alone), and D6 gets D5's ``finding_decisions`` and, for a run-time merge, its diff
  read again under the package hash D5 decided on (``loop.candidates.merge_diff``; a package changed in between
  is ``Unusable``).
  Nothing reads ``cases``, ``harness``, ``organs`` or ``reruns`` to decide: no merge, row or exit code
  depends on a case or a report; of the four only ``cases`` is written, to the dev case set. Which merges' sentinels are unfinished (criterion 8) is the cycle's state:
  ``ledger.serial.unfinished`` of ``pulled``'s ``state/ledger.jsonl`` (``brain/state``'s ledger as D1 verified it), read
  before the tree is judged; a ledger it cannot read is ``state_refused`` with its reasons (exit 1), nothing decided. A
  merge is unfinished until its revert row: the end of a green sentinel has no row until D7 writes one, so after the
  first merge no candidate merges. Then D7's half (``yaz_d7``, ``loop.watch``): the merge watched is chosen from the
  same state by ``kos``'s rule (``_watched``; ``sentinel_unplaced`` likewise), and the results' sentinel read by its
  hash and judged again by MF12 (``loop.watch.read``; a reason is ``sentinel_refused`` with it, exit 1, nothing
  written); the output's ``sentinel`` is ``null`` (nothing watched) or ``{merge_sha, verdict, red?, flaky?, reasons?}``,
  with ``facts`` (``loop.watch.facts``: impact, ``build_ok``, lint before and after: what the rule read is in
  the line whether it reverts or not), and with ``cause`` when ``gate.revert.assess`` of the runs and the facts is a
  revert (red tests, or a green or flaky verdict at a head that
  did not build or whose lint rose over the merge's), which D6 reverts. Any other green
  or flaky verdict is ended by D6's ``events``/``sentinel`` row (seed-043's draft, this brain's stated assumption),
  which finishes the merge in ``ledger.serial``, so the next cycle can merge; a ``null`` verdict writes nothing (the
  merge stays unfinished and the next cycle's ``kos`` watches it again). Then D6 (``yaz_d6``): it needs ``YAZ_ENV`` set (``WRITER_TOKEN``, the
  writer App's token of step 2; Actions' own ``GITHUB_REPOSITORY``, ``GITHUB_WORKSPACE``, ``GITHUB_RUN_ID`` and
  ``GITHUB_RUN_ATTEMPT``; unset is unusable), reads ``$RUNNER_TEMP/in/response`` (``cagir``'s download) with
  ``loop.cagir.read_response`` against ``pulled`` (a refusal is ``response_invalid`` with its reasons, nothing written)
  and the checkout's ``setup/imports.jsonl``, and calls ``loop.write_cycle.write`` with a ``target.write.Writer`` on the
  ``targets[]`` entry's ``repo`` (``target_repo_unsafe`` when it is no repository name) over
  ``target.write.HttpTransport`` with that token, the base's lint totals (``loop.watch.base_lint``: D6's
  ``ratchet_base`` row of a cycle that merges) and D7's end, the signer ``loop.sign.SigstoreSigner`` with the
  ``sigstore`` step's program (``_signer``; none installed is unusable), pinned to ``loop.yml`` on
  ``$GITHUB_REPOSITORY``'s ``main`` (``loop.accepted.workflow_identity``, the identity the next cycle's
  D1 verifies the root against), the cycle id ``<GITHUB_RUN_ID>-<GITHUB_RUN_ATTEMPT>`` and the clock's time: the merge,
  if D5 chose one, or the revert of D7's red, or the end row of its green or flaky, and the cycle's one ``brain/state`` commit.
  Before the job serves its first target and after MF5's reading above, stage 1's MF6 (``yaz_drift``, tohum/01b:57-65: before the cycle's first
  write, and a ``yaz`` job writes to every target it serves): ``drift.check`` of the checkout's
  ``setup/summary.json`` for each served target, in the order served, against the repository its ``pulled`` names
  (the one D6, or the activation of a genesis cycle, writes to), through the transport given or, the job's own,
  ``writer_transport`` with the App's credential (``GET /app``; a transport of its own: D6's writer keeps none).
  The job's line carries ``drift`` ``{checked, drifted, stale, activity}``: the ids checked, ``{id: reasons}`` of those with a
  reason (``ref_change``: an item of the repository's activity since the cycle before, on a ``refs/heads/brain/``
  ref, by an actor or of a type tohum/01c does not allow, the items in ``activity`` ``{id: items}``; a rule, the App's scope, a workflow, a difference from the summary's ``drift`` baseline of tohum/01c,
  among them the three hashes of the checkout's operator files, ``policy.json``'s ``constitutional``, ``vectors/``
  and ``seats/``, read once per job by ``drift.check.held``: ``drift.check``'s list, or ``target_repo_mismatch``) and whether the baseline's ``operator_checked_at`` is more
  than 7 days before the job's clock. Any reason on
  any target ends the job there: ``reason`` ``drift`` with the reasons and id of the first drifted target served,
  ``targets`` ``[]``, exit 1, no target served and nothing written on any; with no reason on any target, a stale
  operator check ends it as cleanly, no hard stop: ``reason`` ``operator_check_stale``, no ``target``, ``targets``
  ``[]``, nothing written, and it is the one stop that is not a red job (tohum/01c; ``CLEAN_STOPS``, ``ending``):
  ``ok`` stays false on the line, the exit is 0 and stdout carries, before the line, one ``::warning`` workflow
  command of fixed text (GitHub shows it as an annotation of the run; no answer of a live run was seen here). Between the two, the policy (``yaz_policy``, tohum/29v "Döngüde eksik
  anahtar"): ``harness.params.check`` of every served target's ``pulled`` policy, and a reason on any (a path of
  stage 1's twelve absent, or a judged value off its form: ``policy_invalid:<path>``) ends the job as cleanly:
  ``reason`` ``policy_unusable`` with the reasons and id of the first such target served, ``targets`` ``[]``,
  exit 1, no target served and nothing written on any (after drift's reads, so that it hides no hard stop; the
  job's line carries ``policy`` ``{id: reasons}``, ``{}`` on a usable one). ``cek`` refuses the same policy by the
  same judge when it assembles ``pulled``, so a cycle that reaches ``yaz`` with one was pulled by other code. A
  read drift cannot use, an unreadable
  summary, a summary without the ``drift`` baseline, a checkout whose ``policy.json``, ``vectors/`` or ``seats/``
  has no hash (absent, a link inside, a JSON float under ``constitutional``) or a secret unset is unusable (exit 2,
  no request sent for the checkout's faults). Not checked, stated: a served target whose ``pulled`` is refused
  or names no repository (``pulled_invalid``, ``units_not_one``, ``target_repo_unsafe``: its own step refuses it
  before any request to it; the targets served before it were checked and are written), and a target of the
  summary the job does not serve (a copy waiting for its gate). A genesis cycle's target is checked here like
  any other, and ``activate.genesis`` reads the same facts again by the same rules. The stop lasts as long as the
  drift does: nothing is recorded, the next job reads the facts anew (a record that outlives the drift, tohum/28's
  restart by the operator, is not built here). A standing branch that differs (tohum/26p "Yarım kalmış merge";
  ``_yaz_written``): when the writer refuses the branch of D5's merge, ``brain/c/<id>``, because it stands and is
  not this cycle's commit (``loop.write_cycle.LandingRefused``; no ref written, no pull request opened, no check
  sent), D5 decides again on the same ``pulled``, tree and results with that candidate carrying ``branch_differs``
  (``loop.decide``'s ``refused``), D8's step is taken again from that decision, and D6 writes the cycle so decided:
  the line's ``decisions`` and ``merge`` are the last decision's, the refused candidate a reject. When the branch
  refused is D8's plant's, ``brain/drill/<cycle>``, the cycle is written with no plant and the line's ``drill`` is
  ``{action: none, why: branch_differs}`` (``PLANT_REFUSED``; the commitment stands and a later cycle, whose
  branch has another name, plants it). Each candidate is refused at most once in a cycle and the plant once, so
  D6 is called at most once more than the cycle has candidates, plus one. Not covered, stated: the genesis cycle
  (``activate`` lands its merge; tohum/28:57 keeps its failed write a hard stop) and a standing revert branch that
  differs (``revert_branch_differs``: ``write_refused``, below). A closed pull request (tohum/01b:75-80): when a
  pull request from the branch of D5's merge into ``brain/integration`` was closed without a merge
  (``target.land.land``, one read; nothing written), the same ``LandingRefused`` carries ``pull_closed`` and the
  cycle goes on by the same steps, that candidate a reject with ``pull_closed``; what is and is not read as such a
  pull request is ``target.write``'s "Closed pull". Not covered, stated: the genesis cycle here too, a plant and a
  revert (``target.land``). A used id (tohum/26p:76-80): a candidate whose
  id the ledger holds a merge of since its last genesis does not come this far. D5 judges it by no rule
  (``loop.decide`` "A used id", ``ledger.serial.used_ids``) and the target's line names it under
  ``candidate_id_used``, the sorted list D5 answers (empty when none is offered); no row, no ``cause``, no ref,
  pull request or check is its (shown on a written cycle's line, ``tests.test_loop_write.UsedId``; a refused
  cycle's line carries D5's answer by the same spread, which no test reads for this key). D6's refusals before any write
  (``head_moved:<branch>``, ``state_unwritable: ...``, any other refusal of the writer before any ref is written
  and before the root is signed) are
  ``write_refused`` with the reasons; a hard stop
  (``target.land.HardStop``: a chain break, a root that cannot be signed, the
  watcher's stop on the ledger as pulled, P1 MF7) is
  ``hard_stop`` with ``written``, the refs already written; a GitHub write to the target that failed, the first or a
  later one (``loop.write_cycle.WriteFailed``, tohum/28:51-60: an outage, not a hard stop; the next cycle takes up
  what stands unless the merge landed, ``loop.write_cycle`` "A failure in step 4 or 5"), is ``write_failed`` with ``written`` and ``sign_calls`` and holds nothing; all three exit 1 with
  ``done`` ``["D5"]``. A written cycle
  whose own freeze passed ``soft_freeze_limit`` (``written.gozcu.hard_stop``) is ``hard_stop`` too, exit 1, after
  its writes. A hard stop's line
  and a written cycle's (the genesis cycle's too) carry ``sign_calls``: every run of the signing program made for
  this target's root, each ``{exit, signs, result}`` (``loop.sign`` "Every run named"). tohum/13's count, at most 3
  runs in one ``yaz`` job, is the job's: ``run`` keeps one list of the job's runs and every signer ``_signer``
  makes in the job counts in it (``loop.sign`` "The job's count"), so the ``sign_calls`` of a job's target lines
  hold at most ``loop.sign.RUNS`` entries between them; a signer passed in counts in its own list. On success the line
  carries ``written`` (``loop.write_cycle``'s answer), ``drill`` (D8's step without the planted file's content) and
  ``done``: ``D5`` and ``D6``, ``D7`` when a sentinel was ended, ``D8`` unless the drill is off; ``ok`` is true (exit
  0), except when D8 judged a drill ``FAIL`` (``drill_fail``, exit 1, after the writes: the cycle's state is written,
  the drill's verdict is red). D8 (``yaz_d8``, ``loop.drill``) runs between D7 and D6 and writes nothing itself: with
  ``DRILL_SEED`` and ``DRILL_FIXTURES`` (tohum/26f: the drill seed and the live drill fixtures, two secrets of
  ``yaz``'s step only; no seed turns the drill off, no fixtures is ``off`` with ``why: fixtures_absent``, fixtures
  bound to another import than the checkout's counter's last is ``off`` with ``why: fixtures_import_mismatch``,
  fixtures ``loop.drill.fixtures`` refuses are unusable, exit 2, nothing written; ``loop.drill.inputs``) it
  answers this cycle's step from the same state: a commitment, a plant (D6 lands it as the cycle's one merge, with the
  ``ratchet_base`` and ``plant`` rows; the next cycle's ``kos`` watches it and its ``yaz`` reverts it, D7), a wait,
  or nothing that fits; the previous drill, once its planted merge is finished, is revealed and judged
  (``harness.revert_drill.judge``) in the line's ``drill.judged``.
- ``cek`` runs D1 (``cek_d1``), and with it the whole job. First the accepted-SHA check: it reads the bootstrap
  referee's last signed state with ``loop.accepted.read_state`` (the Actions API of ``$GITHUB_REPOSITORY`` with the
  job's ``GITHUB_TOKEN``, ``actions: read``; the artifact verified by the ``sigstore`` step's program,
  ``loop.inputs.sigstore``, which the Rekor entry's check below runs too), fetches the accepted
  brain commit with ``loop.fetch`` from ``loop.accepted.repo_url`` of ``bootstrap.json``'s ``brain_repo`` in the
  checkout (``loop.inputs.brain_repo``, tohum/29s) into ``$RUNNER_TEMP/work/cek-*/brain.git``, and checks the running tree by tohum/29u
  (``loop.accepted``'s "The running tree"): the last transfer row of the checkout's ``setup/imports.jsonl``
  (``last_import``) names the transfer commit (``transfer_commit``); when it is the accepted commit itself, that
  commit's ``referee/`` hash must be the row's (``check_tree``), nothing more is fetched; when it is another, the
  accepted commit's history is fetched without trees into ``cek-*/history.git`` (``loop.fetch`` ``history``) and the
  transfer commit must be an ancestor (``check_ancestor``), then the transfer commit is fetched into
  ``cek-*/transfer.git`` and its ``referee/`` hash must be the row's; the accepted commit's own ``referee/`` is
  not compared, so a ``main`` that moved on after the transfer does not stop the loop. Then the
  target half, once per ``targets[]`` entry of the checkout's ``setup/summary.json`` in order (``loop.cek.targets``;
  its refusals ``summary_unreadable``, ``targets_empty``, ``target_id_unsafe``, ``target_ambiguous``,
  ``target_kind_invalid`` stop the job before any target is read), each in its own ``cek-*/<id>/``: its ``repo`` made a URL by
  ``loop.accepted.repo_url``, the heads of ``brain/state`` and ``brain/integration`` read credential-less with
  ``loop.fetch.heads``, ``brain/integration``'s head fetched with ``loop.fetch`` into ``cek-*/target.git``, and
  ``loop.cek.assemble`` run on the two repositories' objects with the checkout's ``policy.json``, writing ``pulled``
  into ``cek-*/<id>/pulled``, not into ``out/pulled``: the upload takes the artifact only once D1's other checks
  pass for every target. An unset variable, an unusable ``bootstrap.json`` or ``brain_repo``, no ``sigstore`` step program, a bootstrap
  state that is absent, unreadable or unverified, an unreadable checkout file, a
  failed listing and a failed fetch (of the brain's history, the transfer commit or a ``brain/state`` commit too) are unusable (exit 2: 29b's reader stops). Refusals (exit 1): ``imports_broken``,
  ``imports_no_transfer``, ``imports_invalid``, ``transfer_not_ancestor``, ``transfer_ancestry_unreadable`` (with the object reasons),
  ``referee_tree_refused`` (with the hash's reasons), ``referee_tree_mismatch``; ``target_repo_unsafe``; ``head_missing:<branch>`` for each head the target lacks (a
  toy with neither is its genesis cycle and a copy with neither is waiting, or its genesis cycle once the gate is
  open, above; nothing of the target is fetched). Then, unless it is the genesis cycle, MF1's ``verify --previous`` of ``brain/state`` (``loop.state``), before
  anything else of the target is fetched: its head fetched with ``loop.fetch`` into ``cek-*/state.git``, its one
  parent (the version the previous cycle verified and extended), when it has one, into
  ``cek-*/state-previous.git``, and ``ledger.jsonl`` and ``chain/root.jsonl`` each verified as a chain and as an
  append-only extension of the parent's (a genesis head without parent: as chains only), and the head's
  ``status.md`` read as bytes (``loop.state.status``; not verified: D6 regenerates a block edited by hand and
  records it), carried in ``pulled`` for D6; a refusal is
  ``state_refused`` with ``loop.state``'s reasons and carries ``heads``. Then MF11's verify of the head's root,
  still before the target is fetched: ``ledger.anchor.judge`` of the head's ``ledger.jsonl`` against the last row
  of its ``chain/root.jsonl`` (``root_mismatch``: the ledger holds rows no signed root anchors, e.g. a commit pushed
  on top of the last cycle's) and that row's Rekor entry, read from the public Rekor by ``loop.rekor.RekorHttp``
  (``entry_missing``) and judged by ``loop.rekor.entry_reasons`` (``entry_root_mismatch``; ``entry_unverified``:
  ``sigstore verify identity`` of the bundle made from the entry, with the same ``verifier`` as the bootstrap
  state's, against ``loop.yml`` on ``$GITHUB_REPOSITORY``'s ``main``, ``loop.accepted.workflow_identity``); a
  refusal is ``root_refused`` with those reasons, or ``root_unreadable`` when the ledger or the last root row is
  not of the form ``ledger.anchor`` reads, and carries ``heads`` and ``state``; Rekor unreadable, or an answer that
  is not the entry asked for, is unusable. Then tohum/13's chain break of ``brain/integration`` (E637), still
  before the target's tree is fetched: the listed head against the commit the anchored ledger names
  (``loop.integration``; ``_cek_integration``): for a ``cut`` or ``merge`` row the head must be that commit and
  nothing is fetched; for a ``revert`` row the head's ancestry is fetched without trees into
  ``cek-*/integration-history.git`` (a failed fetch is unusable) and the head judged by its parents and tree id; a
  refusal is ``integration_refused`` with ``loop.integration``'s reasons and carries ``heads``, ``state``, ``root``
  and, when the ledger names one, ``integration`` (the row and the commit it names: the break's row; the head is
  in ``heads``). Then ``pulled_refused`` with
  ``assemble``'s reasons. Then MF4's judgement: the
  assembled artifact is read back as the other jobs read their download (``loop.pulled.read``, exactly one entry of
  ``units``, else ``units_not_one``; the tree extracted by ``loop.pulled.extract_tree`` into ``cek-*/tree``, a tree
  it refuses is ``pulled_invalid``) and the unit gets the static check ``getir`` runs
  (``profile.unit_verify.check_recipe`` with the artifact's policy and ``targets[]`` entry: MF6's recipe rules and,
  on the tree, ``profile.derive check`` of the recipe against the referee's own derivation of that tree; a reason
  is ``recipe_refused`` with the reasons). A refusal after the assembly carries ``heads``, ``state``, ``root``, ``integration``
  and ``assembled``. When all of it holds, the line's ``accepted`` has ``brain_sha`` (the accepted commit: ``candidates/`` and ``targets/`` are read there),
  ``transfer_sha`` (the transfer row's commit) and ``referee_tree_sha256`` (the ``referee/`` hash of
  ``transfer_sha``, equal to the row's), ``result_sha256``, ``artifact_id``; each target's line has ``heads`` (branch to commit), ``state`` (``head``, ``previous``, ``rows``),
  ``root`` (``root``, ``rekor_uuid``), ``integration`` (``row_id``, ``kind``, ``sha``: the row of the ledger that names ``brain/integration``'s commit; ``None`` in a genesis cycle), ``assembled`` (``target``, ``commit``, ``candidates``, ``organs``: the ids of the organs carried, ``loop.cek`` "Organs", ``snapshot_id``: the clean snapshot's, ``snapshot.make``, and ``mutations``: the ids ``cases.build`` proposed), ``profile``
  (``unit_id``); the job's ``checked`` is ``CEK_CHECKED``: every check of D1's row has run. When every target
  holds, each served target's assembled directory, the bytes MF4 judged, is moved to ``$RUNNER_TEMP/out/pulled/<id>``
  and ``served.json`` written (``_hand_over``; ``out/pulled`` must not exist before, else exit 2), the line has ``ok`` true and ``done`` ``["D1"]``, exit 0, so the upload step runs and ``getir``, ``kos``,
  ``cagir`` and ``yaz`` download it. A refusal leaves ``out/pulled`` absent. The proposal stage 0 judges is the
  recipe alone (tohum/14); no other profile field is proposed, so none is compared.
- ``cagir`` runs D4 (``cagir_d4``), and with it the whole job: it needs ``CAGIR_ENV`` set (the provider token;
  Actions' own ``GITHUB_WORKSPACE``, ``GITHUB_RUN_ID`` and ``GITHUB_RUN_ATTEMPT``), takes the CLI the ``claude`` step
  installed (``loop.inputs.claude``) and the model ``bootstrap.json``'s ``rival.model`` in the checkout
  (``loop.inputs.rival_model``; tohum/29s), reads ``$RUNNER_TEMP/in/pulled`` with ``loop.pulled.read`` (a refusal is
  ``pulled_invalid``; no unit or tree is read), hashes the CLI file (its sha512 is the pin MF15 checks again
  before it starts the process, and is in the line as ``claude_sha512``) and runs ``loop.cagir.d4``: MF15's one canary call, budgeted by the artifact's
  ``canary_usd`` less the cost rows of the ledger D1 verified, its ``response`` written to
  ``$RUNNER_TEMP/out/response`` (which must not exist) whatever the call's outcome. The line has ``ok`` true,
  ``done`` ``["D4"]`` and ``call`` (``outcome``, ``reason``, ``sent``, ``models_served``, ``cost_usd_micros``),
  exit 0, so the upload step runs: the exit says the response was written, its ``outcome`` whether the canary
  held. An unset variable, no CLI where the step installs it, an unusable ``bootstrap.json`` or ``rival.model``, a
  ``canary_usd`` that is no amount, a ledger that is not a chain and an existing ``out/response`` are unusable (exit
  2), nothing started.

The D1-D8 composition inside the jobs is MF17's (spec-036, answered by seed epoch 35c8838).

``RED_CONTROL`` is the referee's own known-bad command, ``node -e process.exit(1)`` in the unit's image (the
image's ``node``); it is not taken from ``pulled``, so nothing the Founder writes can choose it. A known-bad
*candidate* (tohum/08 item 3's wording) run through the unit's own test command is not what runs here.

Out of scope, stated: the ``control`` command itself (the seed's, asama-1/13), whether the seed's ``wiring`` check
accepts this file's YAML (the subset is tohum/29r since seed epoch eec6436; this module writes only block mappings,
block sequences, plain and single-quoted scalars, ``|`` literal blocks and ``{}``, forms 29r keeps, but no test here
parses the file by 29r's rules: the seed's ``wiring`` is that judge), and the
behaviour of the pinned actions (their tags were resolved to the SHAs below on 2026-10-30 with ``git ls-remote``).

Command line, from ``referee/``::

    python -m loop.job render        # the workflow on stdout, exit 0
    python -m loop.job run JOB       # one JSON line on stdout; exit 0 the job's steps all done (``ok`` true)
                                     # or a stop of ``CLEAN_STOPS`` (``ok`` false, a ``::warning`` line first),
                                     # 1 refused or not wired, 2 unusable (RUNNER_TEMP unset, an input
                                     # unusable, getir's fetch failed, an out/ directory that exists)
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import sys
import tempfile
from typing import Any, NamedTuple

from cases import build as CB
from findings import write as FW
from dispatcher import llm_call as LL
from drift import check as DC
from gate import revert as RV
from gozcu import watch as GW
from harness import offline as OF
from harness import params as HP
from harness import pass_row as PR
from ledger import anchor as AN
from ledger import append as LA
from ledger import schema as SC
from ledger import serial as SE
import activate as AC
from loop import accepted as A
from loop import cagir as CG
from loop import candidates as LC
from loop import cek as C
from loop import decide as E
from loop import drill as DR
from loop import fetch as F
from loop import gitobj as G
from loop import inputs as IN
from loop import integration as IG
from loop import program as PG
from loop import pulled as P
from loop import rekor as RK
from loop import sign as SG
from loop import state as ST
from loop import watch as WT
from loop import write_cycle as WC
from profile import derive as D
from profile import unit_verify as U
from runner import candidate_rerun as CR
from runner import deps_npm as N
from runner import kos as K
from runner import organ_output as OO
from snapshot import make as SM
from target import app_jwt as AJ
from target import branches as B
from target import land as LN
from target import write as W
import cli

USAGE = "usage: python -m loop.job render | scope | run JOB"

CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"  # v7.0.1
UPLOAD = "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9"  # v7.0.2
DOWNLOAD = "actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333"  # v8.0.2
APP_TOKEN = "actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510"  # v3.3.0

MAIN_ONLY = "github.ref == 'refs/heads/main'"
GO = "steps.control.outputs.go == 'true'"
RUNNER = "ubuntu-24.04"
CRON = "17 * * * *"

CONTROL_RUN = (
    "set -eu\n"
    "git clone --quiet --depth 1 --branch main --filter=blob:none --sparse"
    " \"$GITHUB_SERVER_URL/$GITHUB_REPOSITORY\" \"$RUNNER_TEMP/control\"\n"
    "git -C \"$RUNNER_TEMP/control\" sparse-checkout set bootstrap\n"
    "cd \"$RUNNER_TEMP/control/bootstrap\"\n"
    "python3 -m snowball_bootstrap control --control ../control.json --job \"$LOOP_JOB\""
    " --event \"$GITHUB_EVENT_NAME\" --github-output \"$GITHUB_OUTPUT\"\n"
)

# The writer App's two secrets: the token action's inputs, and ``yaz``'s own for the genesis cycle's ``GET /app``.
APP_ID_ENV, APP_KEY_ENV = "WRITER_APP_ID", "WRITER_APP_PRIVATE_KEY"
APP_SECRETS = {name: "${{ secrets.%s }}" % name for name in (APP_ID_ENV, APP_KEY_ENV)}

# What JavaScript's ``String.prototype.trim`` removes (ECMA-262 WhiteSpace and LineTerminator): the token action
# reads each input through ``@actions/core``'s ``getInput``, which answers ``val.trim()``.
JS_SPACE = "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a" \
           "\u2028\u2029\u202f\u205f\u3000\ufeff"


def action_input(value: str) -> str:
    """``value`` as the token action's ``getInput`` reads an input: without ``JS_SPACE`` at either end, nothing
    else changed (space inside the value stays, and so does a character ``JS_SPACE`` does not hold)."""
    return value.strip(JS_SPACE)


# The writer App token: made in ``yaz``, limited to the App's permissions of tohum/25 item 6 (what target.write
# writes with, MF9, and ``administration: read``, which genesis' ``GET actions/permissions`` on a copy asks of the
# token: a token carries only the permissions asked for when it is made, spec/tohum/CHANGELOG.md 2026-11-15) and to
# the repositories of ``targets[]`` (``scope``, from the checkout's setup/summary.json).
APP_INPUTS = {
    "app-id": APP_SECRETS[APP_ID_ENV],
    "private-key": APP_SECRETS[APP_KEY_ENV],
    "owner": "${{ steps.scope.outputs.owner }}",
    "repositories": "${{ steps.scope.outputs.repositories }}",
    "permission-contents": "write",
    "permission-pull-requests": "write",
    "permission-checks": "write",
    "permission-administration": "read",
}

SCOPE_RUN = "python3 -m loop.job scope\n"

# Names a code-running job must not see (tohum/08 item 1). GITHUB_TOKEN is not in a job's environment unless a
# step puts it there; the OIDC pair is there whenever the job has ``id-token: write``.
OIDC_ENV = ("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_URL")

# The red control of every contained run in ``kos`` (tohum/08 item 3): a command known to fail in the unit's image.
RED_CONTROL = {"cmd": ["node", "-e", "process.exit(1)"]}


class Job(NamedTuple):
    steps: tuple[str, ...]          # asama-0/01's D steps this job carries
    mfs: tuple[int, ...]            # asama-0/14 MFs it calls (the step table's judge column)
    runs_code: bool                 # tohum/08: runs code that is not the referee's own
    permissions: dict[str, str]     # the job's GITHUB_TOKEN permissions; {} for none
    secrets: dict[str, str]         # env name -> expression, given to ``run`` only
    needs: tuple[str, ...]
    downloads: tuple[str, ...]      # artifacts read, each the upload of the job of the same index in needs
    upload: str | None
    installs: tuple[str, ...] = ()  # tohum/29s's install steps (``loop.inputs.STEPS``) the job runs after control


JOBS: dict[str, Job] = {
    "cek": Job(("D1",), (1, 4, 11), False, {"contents": "read", "actions": "read"},
               {"GITHUB_TOKEN": "${{ github.token }}"},
               (), (), "pulled", ("sigstore",)),
    "getir": Job(("D2",), (5,), True, {}, {}, ("cek",), ("pulled",), "deps"),
    "kos": Job(("D3", "D7"), (3, 6, 12), True, {}, {}, ("cek", "getir"), ("pulled", "deps"), "results"),
    "cagir": Job(("D4",), (2, 15), False, {},
                 {"CLAUDE_CODE_OAUTH_TOKEN": "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}"},
                 ("cek",), ("pulled",), "response", ("claude",)),
    "yaz": Job(("D5", "D6", "D7", "D8"), (2, 7, 8, 9, 10, 11, 13, 14, 16), False,
               {"id-token": "write", "contents": "read"},
               {"WRITER_TOKEN": "${{ steps.app.outputs.token }}", **APP_SECRETS,
                DR.SEED_ENV: "${{ secrets.DRILL_SEED }}", DR.FIXTURES_ENV: "${{ secrets.DRILL_FIXTURES }}"},
               ("cek", "getir", "kos", "cagir"), ("pulled", "deps", "results", "response"), None, ("sigstore",)),
}

# What cek reads from the referee repository's checkout, and the target branches whose heads it reads (asama-0/01 D1).
IMPORTS = "setup/imports.jsonl"  # tohum/26c: the counter, in the referee checkout
CEK_FILES = (IMPORTS, "setup/summary.json", "policy.json")
TARGET_REFS = {b: "refs/heads/" + b for b in (B.STATE, B.INTEGRATION)}
MAIN_REF = "refs/heads/main"  # the toy's genesis cycle reads its tree here (tohum/07: brain/integration is cut from main)
# What cek's line lists as checked when D1 holds: every check of asama-0/01's D1 row.
CEK_CHECKED = ("accepted_sha", "referee_tree", "heads", "state_previous", "root", "integration", "assembled", "profile")

SECRET_ENV = tuple(sorted({name for job in JOBS.values() for name in job.secrets} | {"GITHUB_TOKEN"}))


class Unusable(Exception):
    pass


# ---- the workflow ----------------------------------------------------------------------------------------------

def _producer(name: str, artifact: str) -> str:
    for producer, job in JOBS.items():
        if job.upload == artifact:
            if producer not in JOBS[name].needs:
                raise Unusable("%s reads %s but does not need %s" % (name, artifact, producer))
            return producer
    raise Unusable("no job uploads %s" % artifact)


def _env_name(artifact: str) -> str:
    return "LOOP_%s_DIGEST" % artifact.upper()


def _steps(name: str) -> list[dict[str, Any]]:
    job = JOBS[name]
    steps: list[dict[str, Any]] = [
        {"name": "control", "id": "control", "env": {"LOOP_JOB": name}, "run": CONTROL_RUN},
    ]
    steps.extend({"name": step, "if": GO, "run": IN.STEPS[step]} for step in job.installs)
    steps.append({"name": "checkout", "if": GO, "uses": CHECKOUT, "with": {"persist-credentials": "false"}})
    if name == "yaz":
        steps.append({"name": "writer scope", "id": "scope", "if": GO, "run": SCOPE_RUN})
        steps.append({"name": "writer token", "id": "app", "if": GO, "uses": APP_TOKEN, "with": dict(APP_INPUTS)})
    env: dict[str, str] = {}
    for artifact in job.downloads:
        producer = _producer(name, artifact)
        steps.append({"name": "download %s" % artifact, "if": GO, "uses": DOWNLOAD, "with": {
            "artifact-ids": "${{ needs.%s.outputs.%s_id }}" % (producer, artifact),
            "path": "${{ runner.temp }}/in/%s" % artifact,
            "digest-mismatch": "error",
        }})
        env[_env_name(artifact)] = "${{ needs.%s.outputs.%s_digest }}" % (producer, artifact)
    env.update(job.secrets)
    run: dict[str, Any] = {"name": name, "if": GO}
    if env:
        run["env"] = env
    run["run"] = "python3 -m loop.job run %s\n" % name
    steps.append(run)
    if job.upload:
        steps.append({"name": "upload %s" % job.upload, "id": "up", "if": GO, "uses": UPLOAD, "with": {
            "name": job.upload,
            "path": "${{ runner.temp }}/out/%s" % job.upload,
            "if-no-files-found": "error",
        }})
    return steps


def workflow() -> dict[str, Any]:
    jobs: dict[str, Any] = {}
    for name, job in JOBS.items():
        spec: dict[str, Any] = {"if": MAIN_ONLY, "runs-on": RUNNER, "timeout-minutes": "60",
                                "permissions": dict(job.permissions)}
        if job.needs:
            spec["needs"] = list(job.needs)
        if job.upload:
            spec["outputs"] = {
                "%s_id" % job.upload: "${{ steps.up.outputs.artifact-id }}",
                "%s_digest" % job.upload: "${{ steps.up.outputs.artifact-digest }}",
            }
        spec["steps"] = _steps(name)
        jobs[name] = spec
    return {
        "name": "loop",
        "on": {"schedule": [{"cron": CRON}], "workflow_dispatch": {}},
        "permissions": {},
        "concurrency": {"group": "loop", "cancel-in-progress": "false"},
        "jobs": jobs,
    }


_PLAIN = re.compile(r"[A-Za-z0-9_$./(][^\n]*")
_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")


def _scalar(value: str) -> str:
    if (_PLAIN.fullmatch(value) and ": " not in value and " #" not in value and not value.endswith((":", " "))):
        return value
    return "'%s'" % value.replace("'", "''")


def _emit(value: Any, indent: int, out: list[str]) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if not _KEY.fullmatch(key):
                raise Unusable("key outside the subset: %r" % key)
            if isinstance(item, dict) and not item:
                out.append("%s%s: {}" % (pad, key))
            elif isinstance(item, (dict, list)):
                out.append("%s%s:" % (pad, key))
                _emit(item, indent + 2, out)
            elif "\n" in item:
                if not item.endswith("\n") or any(
                        line != line.strip() or not line for line in item[:-1].split("\n")):
                    raise Unusable("literal block outside the subset under %r" % key)
                out.append("%s%s: |" % (pad, key))
                out.extend("%s  %s" % (pad, line) for line in item[:-1].split("\n"))
            else:
                out.append("%s%s: %s" % (pad, key, _scalar(item)))
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                inner: list[str] = []
                _emit(item, indent + 2, inner)
                out.append("%s- %s" % (pad, inner[0][indent + 2:]))
                out.extend(inner[1:])
            else:
                out.append("%s- %s" % (pad, _scalar(item)))
    else:
        raise Unusable("value outside the subset: %r" % (value,))


def render() -> str:
    out: list[str] = []
    _emit(workflow(), 0, out)
    return "\n".join(out) + "\n"


# ---- the job entry -----------------------------------------------------------------------------------------------

def _dir(environ: dict[str, str], *parts: str) -> str:
    temp = environ.get("RUNNER_TEMP")
    if not temp or not os.path.isabs(temp):
        raise Unusable("RUNNER_TEMP must be an absolute path")
    return os.path.join(temp, *parts)


def _pulled_unit(environ: dict[str, str], tid: str) -> tuple[Any, Any, dict | None]:
    """Target ``tid``'s ``pulled``, ``$RUNNER_TEMP/in/pulled/<tid>``, read by ``_read_unit``. Shared by ``getir``,
    ``kos`` and ``yaz``, so each reads the same artifact the same way."""
    return _read_unit(_dir(environ, "in", "pulled", tid), tid)


def _read_unit(path: str, tid: str) -> tuple[Any, Any, dict | None]:
    """Target ``tid``'s ``pulled`` at ``path`` read by ``loop.pulled.read`` and its one unit (stage 0 runs exactly
    one entry of ``units``): ``(artifact, unit, None)``, or ``(None, None, {reason, reasons?})``
    (``pulled_invalid``, with ``target_mismatch`` when the artifact's ``target.id`` is not ``tid``;
    ``units_not_one``). ``cek`` reads its own assembly with it, the other jobs their download."""
    try:
        art = P.read(path)
    except P.PulledError as exc:
        return None, None, {"reason": "pulled_invalid", "reasons": exc.reasons}
    if art.target["id"] != tid:
        return None, None, {"reason": "pulled_invalid", "reasons": ["target_mismatch"]}
    units = art.units.get("units") if isinstance(art.units, dict) else None
    if not (isinstance(units, list) and len(units) == 1):
        return None, None, {"reason": "units_not_one"}
    return art, units[0], None


def _pulled_tree(environ: dict[str, str], art: Any, job: str) -> tuple[str, str, dict | None]:
    """``pulled``'s tree extracted into a fresh ``$RUNNER_TEMP/work/<job>-*/tree``: ``(root, tree, None)``, or
    ``(root, tree, {reason: pulled_invalid, reasons})`` for a tree ``loop.pulled.extract_tree`` refuses. Shared by
    every job that reads the tree, so each reads it the same way."""
    work = _dir(environ, "work")
    os.makedirs(work, exist_ok=True)
    root = tempfile.mkdtemp(prefix=job + "-", dir=work)
    tree = os.path.join(root, "tree")
    return root, tree, _extract(art, tree)


def _extract(art: Any, tree: str) -> dict | None:
    """``pulled``'s tree extracted into ``tree`` by ``loop.pulled.extract_tree``: ``None``, or ``{reason:
    pulled_invalid, reasons}`` for a tree it refuses."""
    try:
        P.extract_tree(art.tree_tar, tree)
    except P.PulledError as exc:
        return {"reason": "pulled_invalid", "reasons": exc.reasons}
    return None


def _recipe_refused(art: Any, unit: Any, tree: str, job: str) -> dict | None:
    """The unit's static check on the extracted tree (``profile.unit_verify.check_recipe``: MF6's recipe rules and,
    on the tree, MF4's ``profile.derive check`` of the recipe against the referee's own derivation): ``None``, or
    ``{reason: recipe_refused, reasons}``. One rule for ``cek`` (D1's profile judgement, before the upload) and
    ``getir`` (before anything is fetched); ``kos`` runs it again inside ``unit.verify``."""
    try:
        reasons = U.check_recipe(unit, art.policy, tree, art.target)
    except (U.VerifyError, D.DeriveError) as exc:
        raise Unusable("%s: %s" % (job, cli.cause(exc))) from None
    return {"reason": "recipe_refused", "reasons": reasons} if reasons else None


def _unfinished(art: Any) -> tuple[list[str], dict | None]:
    """The merges of ``pulled``'s ``brain/state`` ledger whose sentinel has not finished (``ledger.serial.unfinished``):
    ``(shas, None)``, or ``([], {reason: state_refused, reasons})``. One reading for ``kos`` (which merge D7 watches)
    and ``yaz`` (D5's criterion 8)."""
    try:
        return SE.unfinished(art.state[B.STATE_LEDGER]), None
    except SE.Unusable as exc:
        return [], {"reason": "state_refused", "reasons": exc.reasons}


def _watched(unfinished: list[str], head: str) -> tuple[str | None, dict | None]:
    """The merge D7's sentinel runs at: ``(None, None)`` when no merge is unfinished, ``(head, None)`` when the one
    unfinished merge is ``brain/integration``'s head (the tree ``pulled`` carries), else ``(None, {reason:
    sentinel_unplaced, reasons: [unfinished:<sha>, ...]})``: a red at the head could not be laid on one merge."""
    if not unfinished:
        return None, None
    if unfinished == [head]:
        return head, None
    return None, {"reason": "sentinel_unplaced", "reasons": ["unfinished:%s" % sha for sha in unfinished]}


def getir_d2(environ: dict[str, str], tid: str, fetcher: Any = None) -> dict[str, Any]:
    """D2 of ``getir`` for target ``tid`` (see the module docstring): ``{reason?, reasons?, deps?, licenses?}``."""
    art, unit, refused = _pulled_unit(environ, tid)
    if refused:
        return refused
    _, tree, refused = _pulled_tree(environ, art, "getir")
    if refused:
        return refused
    refused = _recipe_refused(art, unit, tree, "getir")
    if refused:
        return refused
    out = _dir(environ, "out", "deps", tid)
    try:
        os.makedirs(out)
    except FileExistsError:
        raise Unusable("getir: %s exists" % out) from None
    try:
        report = N.fetch(os.path.join(tree, D.norm_path(unit["lockfiles"][0])), out, fetcher or N.HttpsFetcher(),
                         N.DEFAULT_REGISTRIES, unit["install_scripts_required"], art.policy,
                         cap=unit["limits"].get("deps_bytes"))
    except N.DepsError as exc:
        raise Unusable("getir: %s" % cli.cause(exc)) from None
    if not report["ok"]:
        return {"reason": "deps_refused", "reasons": report["reasons"]}
    return {"deps": {k: report[k] for k in ("address", "packages", "bytes", "artefact")},
            "licenses": report["licenses"]}


def kos_d3(environ: dict[str, str], tid: str, runner: Any = None,
           red_control: dict | None = None) -> dict[str, Any]:
    """D3 of ``kos`` for target ``tid``, with D7's sentinel when a merge is watched (see the module docstring):
    ``{reason, reasons?}`` or ``{index, done, snapshot}``."""
    art, unit, refused = _pulled_unit(environ, tid)
    if refused:
        return refused
    deps = _dir(environ, "in", "deps", tid)
    if not (os.path.isdir(deps) and os.listdir(deps)):
        deps = None
    else:
        try:
            deps = N.artifact_in(deps)
        except N.DepsError as exc:
            return {"reason": "deps_invalid", "reasons": [cli.cause(exc)]}
    unfinished, refused = _unfinished(art)
    if refused:
        return refused
    watch, refused = _watched(unfinished, art.heads[B.INTEGRATION])
    if refused:
        return refused
    root, tree, refused = _pulled_tree(environ, art, "kos")
    if refused:
        return refused
    snapshot = os.path.join(root, "snapshot")
    try:
        SM.write(art.snapshot, snapshot, lambda path: D._read_regular(tree, path))
    except SM.SnapshotError as exc:
        return {"reason": "snapshot_refused", "reasons": exc.reasons}
    diffs = {cid: files["diff.patch"] for cid, files in art.candidates.items()}
    try:
        index = K.results(unit, tree, art.policy, red_control or RED_CONTROL, diffs, _dir(environ, "out", "results", tid),
                          deps, art.target, runner, base=root, watch=watch,
                          mutations={mid: m["diff"].encode("utf-8", "surrogateescape")
                                     for mid, m in art.mutations.items()
                                     if isinstance(m, dict) and isinstance(m.get("diff"), str)},
                          organs={"accepted": art.accepted, "definitions": art.organs, "tree": snapshot})
    except K.UNUSABLE as exc:
        raise Unusable("kos: %s" % cli.cause(exc)) from None
    return {"index": index, "done": ["D3", "D7"] if watch else ["D3"],
            "snapshot": {"snapshot_id": art.snapshot["snapshot_id"], "files": len(art.snapshot["files"]),
                         "links": len(art.snapshot["links"])}}


def yaz_d5(environ: dict[str, str], tid: str, held: tuple[Any, str] | None = None,
           differs: dict[str, list[str]] | None = None) -> tuple[dict[str, Any], Any, str | None]:
    """D5 of ``yaz`` for target ``tid`` (see the module docstring): ``({reason?, reasons?, decisions?, merge?}, pulled, tree)``, the
    artifact and the extracted tree D6 writes from (``None`` with a reason). ``held``, the ``(pulled, tree)`` an
    earlier call of this cycle returned, is decided on again as it is (nothing is read from ``in/pulled`` or
    extracted a second time), with ``differs``, the writer's refusals of this cycle (``loop.decide``'s ``refused``)."""
    try:
        with open(_dir(environ, "control", "control.json"), encoding="utf-8") as fh:
            control = cli.load(fh)
    except (OSError, ValueError) as exc:
        raise Unusable("yaz: control.json unreadable: %s" % cli.cause(exc)) from None
    if held is None:
        art, unit, refused = _pulled_unit(environ, tid)
        if refused:
            return refused, None, None
    else:
        art, unit = held[0], held[0].units["units"][0]  # ``_read_unit`` read exactly one
    unfinished, refused = _unfinished(art)
    if refused:
        return refused, None, None
    if held is None:
        _, tree, refused = _pulled_tree(environ, art, "yaz")
        if refused:
            return refused, None, None
    else:
        tree = held[1]
    try:
        frozen = GW.closed(art.state[B.STATE_LEDGER])   # the ledger conforms: ``_unfinished`` read it
        return E.decide(art, unit, tree, _dir(environ, "in", "results", tid), control, unfinished, frozen,
                        differs), art, tree
    except GW.Unusable as exc:
        return {"reason": "state_refused", "reasons": [cli.cause(exc)]}, None, None
    except (E.Unusable, D.DeriveError) as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None


def yaz_cases(environ: dict[str, str], tid: str, art: Any, tree: str) -> dict[str, Any]:
    """The dev cases of target ``tid``'s cycle (P1 MF3; see the module docstring): ``cases.build.build`` of
    ``pulled``'s mutations on ``$RUNNER_TEMP/in/results/<tid>``, each file a regular file with no link on its way
    (else absent); an index that is absent or not JSON is an empty one (every mutation ``kos:missing``). The
    tree the mutations are applied to for their fingerprints is the extracted ``tree``, read the same way, and
    a case's group is read on it too, the unit's root being its ``path`` (``cases.build``, "The group")."""
    index, read = _results(environ, tid)
    unit = art.units["units"][0]    # ``_read_unit`` read exactly one
    return CB.build(art.heads[B.INTEGRATION], art.mutations, index, read,
                    lambda path: D._read_regular(tree, path), FW.fingerprint,
                    D.norm_path(unit.get("path")) if isinstance(unit, dict) else None)


def _results(environ: dict[str, str], tid: str) -> tuple[Any, Any]:
    """``(index, read)`` of ``$RUNNER_TEMP/in/results/<tid>``: ``read(path)`` the bytes of a regular file with no
    link on its way, else ``None``; ``index`` its ``index.json`` as JSON, ``None`` when absent or not JSON."""
    read = LC.reader(_dir(environ, "in", "results", tid))
    return LC.index(read), read


def yaz_organs(environ: dict[str, str], tid: str) -> dict[str, Any]:
    """The organs' outputs of target ``tid``'s cycle, read by their hashes (P1 MF10; see the module docstring):
    one entry per organ of the results' index, ``{read: true, sha256, files, bytes}`` when
    ``runner.organ_output.read`` gave the output under the hash the index names, else ``{read: false, reasons}``."""
    index, read = _results(environ, tid)
    organs = index.get("organs") if isinstance(index, dict) else None
    line: dict[str, Any] = {}
    for oid, entry in sorted(organs.items()) if isinstance(organs, dict) else ():
        kept = entry.get("output") if isinstance(entry, dict) else None
        sha = kept.get("sha256") if isinstance(kept, dict) else None
        if sha is None:
            line[oid] = {"read": False, "reasons": ["output_not_kept"]}
            continue
        try:
            files = OO.read(sha, read)
        except OO.Refused as exc:
            line[oid] = {"read": False, "reasons": exc.reasons}
        else:
            line[oid] = {"read": True, "sha256": sha, "files": len(files), "bytes": sum(map(len, files.values()))}
    return line


def yaz_reruns(environ: dict[str, str], tid: str) -> dict[str, Any]:
    """The reruns of target ``tid``'s run-time candidates (P1 MF11; see the module docstring): one entry per name
    under the results' ``candidates/`` and per key of the index's ``reruns``: ``{reran: true, package_sha256, verified}``
    when ``runner.candidate_rerun.reran`` hands out the package and its files, else ``{reran: false, reasons}``."""
    index, read = _results(environ, tid)
    line: dict[str, Any] = {}
    for cid in LC.names(_dir(environ, "in", "results", tid), index):
        try:
            got = CR.reran(index, cid, read)
        except CR.NotRerun as exc:
            line[cid] = {"reran": False, "reasons": exc.reasons}
        else:
            line[cid] = {"reran": True, "package_sha256": CR.key(got.package), "verified": CR.verified(got.entry)}
    return line


NO_HUNTER_RUN = {"reason": "no_hunter_run"}   # ``harness`` on the target's line: no report is scored (tohum/26q (6))


CODE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # the directory ``loop/`` is in


def yaz_offline() -> dict[str, Any]:
    """The static reading of the running harness (P1 MF5, ``harness.offline.check`` of ``CODE_ROOT``, the code this
    process runs): ``{roots, modules, reasons}``; see the module docstring."""
    return OF.check(CODE_ROOT)


def yaz_d7(environ: dict[str, str], tid: str, art: Any) -> tuple[dict[str, Any], dict | None, dict | None]:
    """D7's half in ``yaz`` (see the module docstring): ``({sentinel} or {reason, reasons}, end, base_lint)``:
    ``end`` the verified sentinel D6 ends (``loop.watch.read``'s answer with its ``facts``: D6 reverts what
    ``gate.revert.assess`` calls a revert and writes the end row of any other green or flaky), or ``None``; ``base_lint``
    ``loop.watch.base_lint`` of the results."""
    results = _dir(environ, "in", "results", tid)
    unfinished, refused = _unfinished(art)
    if not refused:
        watch, refused = _watched(unfinished, art.heads[B.INTEGRATION])
    if refused:
        return refused, None, None
    try:
        seen = WT.read(results, watch)
    except WT.Refused as exc:
        return {"reason": "sentinel_refused", "reasons": exc.reasons}, None, None
    lint = WT.base_lint(results)
    if seen is None or seen["verdict"] is None:
        return {"sentinel": seen}, None, lint
    line = {k: v for k, v in seen.items() if k != "runs"}
    try:
        facts = WT.facts(seen, art.state[B.STATE_LEDGER], lint, WT.base_build(results))
    except SE.Unusable as exc:
        return {"reason": "state_refused", "reasons": exc.reasons}, None, None
    line = dict(line, facts=facts)
    assessed = RV.assess(seen["runs"], facts)
    if assessed["revert"]:
        line = dict(line, cause=assessed["cause"])
    return {"sentinel": line}, dict(seen, facts=facts), lint


YAZ_ENV = ("WRITER_TOKEN", "GITHUB_REPOSITORY", "GITHUB_WORKSPACE", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")


def yaz_d8(environ: dict[str, str], art: Any, tree: str, d5: dict[str, Any]) -> dict[str, Any]:
    """D8 of ``yaz`` (see the module docstring): ``loop.drill.step`` of this cycle's state, before anything is
    written; D6 writes what it answers. The drill is the toy's (asama-0/08 row 4, 10a #geri-alma): on a target of
    another kind it is off, as without the seed."""
    toy = art.target.get("kind") == "toy"
    if toy and environ.get(DR.SEED_ENV) and not environ.get("GITHUB_WORKSPACE"):
        raise Unusable("yaz: GITHUB_WORKSPACE is not set")
    unfinished, refused = _unfinished(art)
    if refused:  # yaz_d5 read the same ledger first
        raise Unusable("yaz: %s" % ", ".join(refused["reasons"]))
    try:
        inp = _drill_inputs(environ) if toy else None
        return DR.step(inp, art.state[B.STATE_LEDGER], unfinished, d5["merge"] is not None, tree,
                       environ.get("GITHUB_RUN_ID", ""))
    except DR.Unusable as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None


def _judge_inputs(environ: dict[str, str]) -> tuple[dict | None, bytes]:
    """What ``harness.pass_row`` judges with besides the states, for the gate and the PASS row: D8's ``{seed,
    catalog}`` (``loop.drill.inputs``; ``None`` when the drill is off) and the checkout's counter."""
    if not environ.get("GITHUB_WORKSPACE"):
        raise Unusable("yaz: GITHUB_WORKSPACE is not set")
    try:
        inp = _drill_inputs(environ)
    except DR.Unusable as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None
    drill = {"seed": inp["seed"], "catalog": inp["catalog"]} if inp and "seed" in inp else None
    return drill, _workspace_file(environ, IMPORTS)


def _expectations(art: Any) -> dict:
    """``{cid: expect.json}`` of ``pulled``'s candidates, as JSON (``harness.pass_row.expectations`` checks them)."""
    return {cid: cli.loads(files["expect.json"].decode("utf-8")) for cid, files in art.candidates.items()}


def _state(art: Any) -> dict:
    return {"ledger": art.state[B.STATE_LEDGER], "roots": art.state[B.STATE_ROOTS], "registers": _registers(art.state)}


JUDGE_UNUSABLE = (UnicodeDecodeError, json.JSONDecodeError, RecursionError, PR.Unusable)


def yaz_gate(environ: dict[str, str], art: Any) -> dict[str, Any] | None:
    """The copy's genesis gate on the toy's cycle (``harness.pass_row.gate``; see the module docstring): ``None`` on
    a target that is not a toy or whose run already holds the gate's row; else ``{verdict: open|closed,
    conditions}`` (``conditions``: only those with reasons), judged on ``pulled``'s state before anything is
    written. An input the gate cannot use (an ``expect.json`` that is not ``{decision: merge}`` or ``{decision:
    reject, reason}``, a counter with no import) keeps it ``closed`` with ``unusable``: the toy's cycle goes on; an
    unreadable checkout file is unusable as in D6."""
    if art.target.get("kind") != "toy" or PR.gate_opened(art.state[B.STATE_LEDGER]):
        return None
    drill, imports = _judge_inputs(environ)
    try:
        got = OF.run(lambda: PR.gate(_state(art), _expectations(art), drill, imports))
    except JUDGE_UNUSABLE as exc:
        return {"verdict": "closed", "conditions": {}, "unusable": cli.cause(exc)}
    return {"verdict": got["verdict"], "conditions": {c: r for c, r in got["conditions"].items() if r}}


def yaz_pass(environ: dict[str, str], tid: str, art: Any) -> tuple[dict[str, Any] | None, dict | None]:
    """The PASS row on the toy's cycle (``harness.pass_row.judge``; see the module docstring): ``(line, payload)``.
    ``(None, None)`` on a target that is not a toy, before the copy's genesis gate opened, or when the toy's run
    already holds its PASS row; ``({waiting: copy_not_served|copy_genesis}, None)`` when no copy with a state is
    served this run; else ``{verdict: PASS|FAIL, conditions}`` (only those with reasons) and, on ``PASS``, the
    row's payload, judged before anything is written. An input the judge cannot use (an ``expect.json``, a counter
    with no import, a result that is not the one the import names) is ``FAIL`` with ``unusable``: the toy's cycle
    goes on; an unreadable checkout file is unusable as in D6."""
    ledger = art.state[B.STATE_LEDGER]
    if art.target.get("kind") != "toy" or not PR.gate_opened(ledger) or PR.passed(ledger):
        return None, None
    try:  # run read served.json first; D1 verified each served state
        others = [P.read(_dir(environ, "in", "pulled", other)) for other in P.served(_dir(environ, "in", "pulled"))
                  if other != tid]
    except P.PulledError as exc:
        raise Unusable("yaz: pulled: %s" % ", ".join(exc.reasons)) from None
    copies = [other for other in others if other.target.get("kind") == "copy"]
    if len(copies) > 1:
        raise Unusable("yaz: more than one copy served (tohum/26c: one toy, one copy)")
    if not copies:
        return {"waiting": "copy_not_served"}, None
    if P.genesis(copies[0]):
        return {"waiting": "copy_genesis"}, None
    drill, imports = _judge_inputs(environ)
    try:
        path = PR.result_path(imports)
    except PR.Unusable as exc:
        return {"verdict": "FAIL", "conditions": {}, "unusable": cli.cause(exc)}, None
    result = _workspace_file(environ, path)
    try:
        got = OF.run(lambda: PR.judge(_state(art), _state(copies[0]), _expectations(art), _expectations(copies[0]),
                                      drill, imports, result))
    except JUDGE_UNUSABLE as exc:
        return {"verdict": "FAIL", "conditions": {}, "unusable": cli.cause(exc)}, None
    line = {"verdict": got["verdict"], "conditions": {c: r for c, r in got["conditions"].items() if r}}
    return line, got["payload"]


def yaz_d6(environ: dict[str, str], tid: str, art: Any, tree: str, d5: dict[str, Any], transport: Any = None,
           signer: Any = None, now: Any = None, base_lint: dict | None = None,
           end: dict | None = None, drill: dict | None = None, gate: dict | None = None,
           passed: dict | None = None, job_calls: list | None = None,
           cases: list | None = None) -> dict[str, Any]:
    """D6 of ``yaz``, with D7's ``end``, D8's step, the gate's and the PASS row and the cycle's dev ``cases`` (see the module docstring): ``{reason,
    reasons,
    written?}`` or
    ``{written}``, or ``{landing_refused: cid | None, why}`` when the landing of D5's merge ``cid`` or of D8's
    plant (``None``) was refused for the one reason in ``why`` with nothing written (``loop.write_cycle.LandingRefused``). ``transport``
    is the target's API (``target.write.HttpTransport`` with ``WRITER_TOKEN`` when ``None``), ``signer`` the root's
    (``loop.sign.SigstoreSigner`` pinned to ``loop.yml`` on ``$GITHUB_REPOSITORY`` when ``None``, counting its runs
    in ``job_calls``, the job's list, or in its own when that is ``None`` too), ``now`` the clock."""
    got = _yaz_inputs(environ, tid, art, transport, signer, now, job_calls=job_calls)
    if "reason" in got:
        return got
    writer, signer, imports, cost, cycle_id, ts = (got[k] for k in ("writer", "signer", "imports", "cost", "cycle_id",
                                                                    "ts"))
    seen = len(_sign_calls(signer))
    try:
        sha = d5["decisions"][d5["merge"]].get("package_sha256") if d5["merge"] is not None else None
        diff = None if sha is None else LC.merge_diff(_dir(environ, "in", "results", tid), d5["merge"], sha)
        return {"written": WC.write(art, tree, d5, cost, writer, signer, imports, cycle_id, ts, base_lint, end, drill,
                                    gate, passed, finding_decisions=d5["finding_decisions"], merge_diff=diff,
                                    cases=cases),
                "sign_calls": _sign_calls(signer, seen)}
    except LC.Unusable as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None
    except WC.LandingRefused as exc:  # one landing in a cycle: the merge's branch, or else the plant's
        return {"landing_refused": d5["merge"], "why": [*exc.reasons]}
    except WC.Refused as exc:
        return {"reason": "write_refused", "reasons": exc.reasons}
    except LN.HardStop as exc:
        return {"reason": "hard_stop", "reasons": [cli.cause(exc)], "written": sorted(set(writer.written)),
                "sign_calls": _sign_calls(signer, seen)}
    except WC.WriteFailed as exc:
        return {"reason": "write_failed", "reasons": [cli.cause(exc)],
                "written": sorted(set(writer.written)), "sign_calls": _sign_calls(signer, seen)}
    except (WC.Unusable, W.ApiError, W.Refused) as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None


def _drill_inputs(environ: dict[str, str]) -> dict | None:
    """``loop.drill.inputs`` with the checkout's counter, read only when both drill secrets are given."""
    given = environ.get(DR.SEED_ENV) and environ.get(DR.FIXTURES_ENV)
    return DR.inputs(environ, _workspace_file(environ, IMPORTS) if given else b"")


def _workspace_file(environ: dict[str, str], path: str) -> bytes:
    try:
        with open(os.path.join(environ["GITHUB_WORKSPACE"], *path.split("/")), "rb") as fh:
            return fh.read()
    except OSError as exc:
        raise Unusable("yaz: %s: %s" % (path, cli.cause(exc))) from None


SUMMARY = DC.SUMMARY


def yaz_drift(environ: dict[str, str], served: list[str], transport: Any = None,
              now: Any = None) -> dict[str, Any]:
    """MF6 of stage 1, ``yaz``'s step after ``yaz_offline`` and before any target is served (see the module docstring):
    ``drift.check`` of the checkout's ``setup/summary.json`` for every target of ``served`` whose ``pulled`` is
    read and names a repository, against that repository (the one D6 or the activation would write to):
    ``{checked, drifted, stale, activity}``, the ids checked in the order served, ``{id: reasons}`` of those with a
    reason, whether the summary's operator check is stale at ``now`` (tohum/01c) and ``{id: items}`` of those with
    an activity item that is not allowed (``drift.check``'s ``activity``; their reason is ``ref_change``). The three hashes compared with the
    baseline's are the checkout's (``drift.check.held``: ``policy.json``, ``vectors/``, ``seats/``), read once. Its
    own transport (``transport`` ``None``) is ``writer_transport`` with the App's credential, for ``GET /app``."""
    now = now or (lambda: datetime.datetime.now(datetime.timezone.utc))
    out: dict[str, Any] = {"checked": [], "drifted": {}, "stale": False, "activity": {}}
    summary = None
    for tid in served:
        art, _, refused = _pulled_unit(environ, tid)
        try:
            repo = None if refused else A.repo_name(art.target.get("repo"))
        except A.StateError:
            repo = None
        if repo is None:  # the target's own step refuses it (pulled_invalid, target_repo_unsafe): no request to it
            continue
        if summary is None:  # the first target read: what the reads need, as ``_yaz_inputs`` asks it of D6
            _yaz_env(environ)
            summary = _workspace_file(environ, SUMMARY)
            try:
                hashes = DC.held(environ["GITHUB_WORKSPACE"])
            except DC.Unusable as exc:
                raise Unusable("yaz: drift: %s" % cli.cause(exc)) from None
        transport = transport or writer_transport(environ, now, app=True)
        try:
            got = DC.check(transport, summary, hashes, tid, now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                           _previous_start(art), repo)
        except (DC.Unusable, W.ApiError, W.Unusable) as exc:
            raise Unusable("yaz: drift: %s" % cli.cause(exc)) from None
        out["checked"].append(tid)
        if got["hard_stop"]:
            out["drifted"][tid] = got["reasons"]
        if got["activity"]:
            out["activity"][tid] = got["activity"]
        out["stale"] = out["stale"] or got["stale"]
    return out


def _previous_start(art: Any) -> str | None:
    """The start of the cycle before this one, for the activity window (tohum/01c): ``ledger.serial.last_start``
    of ``pulled``'s ledger. A ledger that does not conform gives ``None``, the widest window (from the baseline's
    ``not_before``): judging that ledger is D6's, which stops on it."""
    try:
        return SE.last_start(art.state[B.STATE_LEDGER])
    except SE.Unusable:
        return None


def yaz_policy(environ: dict[str, str], served: list[str]) -> dict[str, list[str]]:
    """``yaz``'s step after ``yaz_drift`` and before any target is served (see the module docstring; tohum/29v
    "Döngüde eksik anahtar"): ``{id: reasons}``, ``harness.params.check`` of the policy of every target of
    ``served`` whose ``pulled`` is read, those with a reason only. A target whose ``pulled`` is refused is not
    judged here: its own step refuses it, as in ``yaz_drift``."""
    out: dict[str, list[str]] = {}
    for tid in served:
        art, _, refused = _pulled_unit(environ, tid)
        reasons = [] if refused else HP.check(art.policy)
        if reasons:
            out[tid] = reasons
    return out


def _yaz_env(environ: dict[str, str]) -> None:
    for name in YAZ_ENV:
        if not environ.get(name):
            raise Unusable("yaz: %s is not set" % name)


def _yaz_inputs(environ: dict[str, str], tid: str, art: Any, transport: Any, signer: Any,
                now: Any, app: bool = False, job_calls: list | None = None) -> dict[str, Any]:
    """What D6 writes with, in every cycle (the genesis cycle's too): ``{writer, signer, imports, cost, cycle_id,
    ts}``, or ``{reason, reasons?}`` (``response_invalid``, ``target_repo_unsafe``) before anything is written."""
    _yaz_env(environ)
    try:
        cost = CG.read_response(_dir(environ, "in", "response", tid), art)
    except CG.ResponseError as exc:
        return {"reason": "response_invalid", "reasons": exc.reasons}
    imports = _workspace_file(environ, IMPORTS)
    try:
        repo = A.repo_name(art.target.get("repo"))
    except A.StateError:
        return {"reason": "target_repo_unsafe"}
    now = now or (lambda: datetime.datetime.now(datetime.timezone.utc))
    return {"writer": W.Writer(repo, transport or writer_transport(environ, now, app)),
            "signer": signer or _signer(environ, job_calls), "imports": imports, "cost": cost,
            "cycle_id": "%s-%s" % (environ["GITHUB_RUN_ID"], environ["GITHUB_RUN_ATTEMPT"]),
            "ts": now().strftime("%Y-%m-%dT%H:%M:%SZ")}


def writer_transport(environ: dict[str, str], now: Any, app: bool = False, handlers: tuple = ()) -> W.HttpTransport:
    """``yaz``'s API: ``target.write.HttpTransport`` with ``WRITER_TOKEN``, the installation token. ``app`` (the
    genesis cycle's activation and the job's ``drift.check``, whose first read is ``GET /app``) adds the App's own
    credential: a JWT of ``WRITER_APP_ID`` and
    ``WRITER_APP_PRIVATE_KEY`` (``target.app_jwt.token``) made at the clock's time when that read is sent. The two
    secrets are the ones the ``writer token`` step gave the token action in the same job, and each is read here
    as that action reads its input (``action_input``): the installation token in ``WRITER_TOKEN`` was made from
    the trimmed values, so the JWT is too. Either unset, or empty once read so, is unusable before any request;
    an id or a key ``target.app_jwt`` refuses is unusable at that read. Without ``app`` the transport holds no
    App credential, whatever the environment holds. ``handlers`` are urllib's (tests put their GitHub there)."""
    if not app:
        return W.HttpTransport(environ["WRITER_TOKEN"], handlers)
    secrets = {name: action_input(environ.get(name) or "") for name in (APP_ID_ENV, APP_KEY_ENV)}
    for name, value in secrets.items():
        if not value:
            raise Unusable("yaz: %s is not set" % name)

    def jwt() -> str:
        try:
            return AJ.token(secrets[APP_ID_ENV], secrets[APP_KEY_ENV], int(now().timestamp()))
        except AJ.Unusable as exc:
            raise W.Unusable(cli.cause(exc)) from None

    return W.HttpTransport(environ["WRITER_TOKEN"], handlers, app=jwt)


GENESIS_WRITTEN = ("merge", "state_sha", "integration_sha", "root", "rekor_uuid", "rows", "edited")
SECURITY_LEDGER = "setup/security-ledger.jsonl"  # tohum/26c, 29o, 29s: the seed security ledger, in the checkout


def yaz_genesis(environ: dict[str, str], tid: str, art: Any, tree: str, d5: dict[str, Any], transport: Any = None,
                signer: Any = None, now: Any = None, job_calls: list | None = None) -> dict[str, Any]:
    """D6 of the genesis cycle (``loop.pulled.genesis``; see the module docstring): ``activate.activate`` with this
    cycle's D5 and D3 and the checkout's files: ``{reason, reasons, written?}`` or ``{written}``. Its own
    transport (``transport`` ``None``) is ``writer_transport`` with the App's credential, for genesis'
    ``GET /app``; its own signer (``signer`` ``None``) counts its runs in ``job_calls`` as ``yaz_d6``'s does."""
    got = _yaz_inputs(environ, tid, art, transport, signer, now, app=True, job_calls=job_calls)
    if "reason" in got:
        return got
    given = WT.base_run(_dir(environ, "in", "results", tid))
    if given is None:
        return {"reason": "activation_refused", "reasons": ["base_run_missing"]}
    files = {"summary.json": _workspace_file(environ, SUMMARY), "imports.jsonl": got["imports"],
             "policy.json": art.policy_bytes, "security-ledger.jsonl": _workspace_file(environ, SECURITY_LEDGER),
             "recipe.json": json.dumps(art.units["units"][0], sort_keys=True).encode("utf-8"),
             "base.jsonl": given[0]}
    writer = got["writer"]
    seen = len(_sign_calls(got["signer"]))
    try:
        done = AC.activate(writer, files, art, tree, d5, given[1], got["cost"], got["signer"], got["cycle_id"],
                           got["ts"])
    except AC.Refused as exc:
        return {"reason": "activation_refused", "reasons": exc.reasons}
    except LN.HardStop as exc:
        return {"reason": "hard_stop", "reasons": [cli.cause(exc)], "written": sorted(set(writer.written)),
                "sign_calls": _sign_calls(got["signer"], seen)}
    except (AC.Unusable, W.ApiError, W.Unusable) as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None
    return {"written": dict({k: done[k] for k in GENESIS_WRITTEN}, genesis=True),
            "sign_calls": _sign_calls(got["signer"], seen)}


def _sign_calls(signer: Any, seen: int = 0) -> list[dict]:
    """``sign_calls`` of a target's line: the signer's ``calls`` after its first ``seen`` (those made before this
    target's D6 wrote, when the list serves several targets: the job's, or a passed signer's), each
    ``{exit, signs, result}`` (``loop.sign`` "Every run named"); ``[]`` for a signer that keeps none."""
    return [dict(call) for call in list(getattr(signer, "calls", ()))[seen:]]


def _signer(environ: dict[str, str], calls: list | None = None) -> SG.SigstoreSigner:
    """``yaz``'s root signer: ``loop.sign.SigstoreSigner`` with the ``sigstore`` step's program, pinned to ``loop.yml``
    on ``$GITHUB_REPOSITORY``'s ``main``, counting and naming its runs in ``calls`` (the job's list; its own when
    ``None``)."""
    try:
        return SG.SigstoreSigner(A.workflow_identity(environ["GITHUB_REPOSITORY"], A.LOOP_WORKFLOW),
                                 IN.sigstore(environ), calls=calls)
    except (A.StateError, IN.InputError) as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None


CAGIR_ENV = ("CLAUDE_CODE_OAUTH_TOKEN", "GITHUB_WORKSPACE", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")


def cagir_d4(environ: dict[str, str], tid: str, now: Any = None) -> dict[str, Any]:
    """D4 of ``cagir`` for target ``tid`` (see the module docstring): ``{reason, reasons}`` or ``{call}``; with
    ``call`` ``out/response/<tid>`` holds the artifact. ``now`` is the clock (``datetime.now(timezone.utc)`` when ``None``)."""
    for name in CAGIR_ENV:
        if not environ.get(name):
            raise Unusable("cagir: %s is not set" % name)
    out = _dir(environ, "out", "response", tid)  # must not exist: loop.cagir.d4's check, before anything is started
    try:
        path = IN.claude(environ)
        model = IN.rival_model(environ["GITHUB_WORKSPACE"])
    except IN.InputError as exc:
        raise Unusable("cagir: %s" % cli.cause(exc)) from None
    try:
        art = P.read(_dir(environ, "in", "pulled", tid))
    except P.PulledError as exc:
        return {"reason": "pulled_invalid", "reasons": exc.reasons}
    if art.target["id"] != tid:
        return {"reason": "pulled_invalid", "reasons": ["target_mismatch"]}
    ts = (now or (lambda: datetime.datetime.now(datetime.timezone.utc)))().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        # the bytes found after the claude step: MF15 hashes the file again before it starts it (loop.inputs)
        pin = LL.sha512_file(path)
        got = CG.d4(art, out, claude=path, claude_sha512=pin, model=model, token=environ["CLAUDE_CODE_OAUTH_TOKEN"],
                    row_id="cagir-%s-%s" % (environ["GITHUB_RUN_ID"], environ["GITHUB_RUN_ATTEMPT"]), ts=ts)
    except (LL.Unusable, LA.HardStop, OSError) as exc:
        raise Unusable("cagir: %s" % cli.cause(exc)) from None
    return {"call": got, "claude_sha512": pin}


def cek_d1(environ: dict[str, str], http: Any = None, verifier: Any = None, git: str = "git",
           rekor: Any = None) -> dict[str, Any]:
    """D1 of ``cek`` (see the module docstring): ``{reason?, reasons?, accepted?, heads?, state?, root?,
    assembled?, profile?}``; without a reason ``out/pulled`` holds the artifact. ``rekor`` reads Rekor entries (``entry(uuid)``; ``loop.rekor.RekorHttp``
    when ``None``); ``verifier`` runs both Sigstore checks."""
    for name in ("GITHUB_REPOSITORY", "GITHUB_TOKEN", "GITHUB_WORKSPACE"):
        if not environ.get(name):
            raise Unusable("cek: %s is not set" % name)
    try:
        sigstore = IN.sigstore(environ)
        brain_url = A.repo_url(IN.brain_repo(environ["GITHUB_WORKSPACE"]))
        state = A.read_state(http or A.ActionsHttp(environ["GITHUB_TOKEN"]), environ["GITHUB_REPOSITORY"],
                             sigstore, verifier=verifier or PG.run)
    except (A.StateError, IN.InputError) as exc:
        raise Unusable("cek: %s" % cli.cause(exc)) from None
    files = {}
    for name in CEK_FILES:
        try:
            with open(os.path.join(environ["GITHUB_WORKSPACE"], *name.split("/")), "rb") as fh:
                files[name] = fh.read()
        except OSError as exc:
            raise Unusable("cek: %s unreadable: %s" % (name, cli.cause(exc))) from None
    work = _dir(environ, "work")
    os.makedirs(work, exist_ok=True)
    root = tempfile.mkdtemp(prefix="cek-", dir=work)
    brain_dir = os.path.join(root, "brain.git")
    sha = state["last_accepted_sha"]
    try:
        F.fetch(brain_dir, brain_url, sha, git=git, environ=environ)
    except P.PulledError as exc:
        raise Unusable("cek: brain fetch: %s" % ", ".join(exc.reasons)) from None
    try:
        imported, _ = A.last_import(files[IMPORTS])
        transfer = A.transfer_commit(imported)
        transfer_dir = brain_dir
        if transfer != sha:  # main moved on after the transfer (tohum/29u): the running tree is the transfer's
            history_dir, transfer_dir = os.path.join(root, "history.git"), os.path.join(root, "transfer.git")
            try:
                F.fetch(history_dir, brain_url, sha, git=git, environ=environ, history=True)
            except P.PulledError as exc:
                raise Unusable("cek: brain history fetch: %s" % ", ".join(exc.reasons)) from None
            with G.GitBatch(history_dir, git=git, environ=environ) as history:
                A.check_ancestor(history, sha, transfer)
            try:
                F.fetch(transfer_dir, brain_url, transfer, git=git, environ=environ)
            except P.PulledError as exc:
                raise Unusable("cek: transfer fetch: %s" % ", ".join(exc.reasons)) from None
        with G.GitBatch(transfer_dir, git=git, environ=environ) as transferred:
            tree = A.check_tree(transferred, transfer, imported)
    except A.StateError as exc:
        return _refused(exc.reasons)
    accepted = {"brain_sha": sha, "transfer_sha": transfer, "referee_tree_sha256": tree,
                "result_sha256": state["result_sha256"], "artifact_id": state["artifact_id"]}
    try:
        pin = A.workflow_identity(environ["GITHUB_REPOSITORY"], A.LOOP_WORKFLOW)
    except A.StateError as exc:
        raise Unusable("cek: %s" % cli.cause(exc)) from None
    targets, reasons = C.targets(files["setup/summary.json"])
    if reasons:
        return dict(_refused(reasons), accepted=accepted)
    entries = RK.entry_reasons((rekor or RK.RekorHttp()).entry, pin, sigstore, verifier=verifier or PG.run)
    lines: list[dict[str, Any]] = []
    opened = False  # the copy's genesis gate, read from a toy served before it in this run
    for target in targets:
        tid = target["id"]
        os.makedirs(os.path.join(root, tid))
        line = dict({"target": tid}, **_cek_target(environ, files, target, brain_dir, sha,
                                                    os.path.join(root, tid), git, entries, opened,
                                                    run_id=state["run_id"]))
        lines.append(line)
        if "reason" in line:
            return dict(_refused([line["reason"]] + line.get("reasons", [])), target=tid, targets=lines,
                        accepted=accepted)
        if target["kind"] == "toy" and "genesis" not in line:
            served = P.read(os.path.join(root, tid, "pulled"))  # the bytes D1 verified, as assembled
            opened = opened or PR.gate_opened(served.state[B.STATE_LEDGER])
    _hand_over(root, [line["target"] for line in lines if "waiting" not in line], _dir(environ, "out", "pulled"))
    return {"accepted": accepted, "targets": lines}


def _hand_over(root: str, served: list[str], out: str) -> None:
    """D1 held for every target: each served target's assembled ``pulled`` (the bytes MF4 judged, read back) moved
    to ``out/<id>`` and ``served.json`` written (``loop.pulled.write_served``); ``out`` is the upload step's path,
    which must not exist before (an existing directory would be replaced or mixed with another run's)."""
    if os.path.lexists(out):
        raise Unusable("cek: %s exists" % out)
    os.makedirs(out)
    for tid in served:
        shutil.move(os.path.join(root, tid, "pulled"), os.path.join(out, tid))
    P.write_served(out, served)


def _refused(reasons: list[str]) -> dict[str, Any]:
    return dict({"reason": reasons[0]}, **({"reasons": reasons[1:]} if reasons[1:] else {}))


def _cek_target(environ: dict[str, str], files: dict[str, bytes], target: dict, brain_dir: str, brain_sha: str,
                root: str, git: str, entries: Any, opened: bool = False,
                run_id: str | None = None) -> dict[str, Any]:
    """The target half of D1 for one ``targets[]`` entry, in its own directory ``root`` (see the module
    docstring): ``{reason?, reasons?, heads?, state?, root?, assembled?, profile?, genesis?}``, or ``{waiting,
    heads}`` for a copy not yet opened; ``opened``: the copy's genesis gate is open on a toy served before it;
    ``run_id``: the signed result's run id, carried in the artifact's ``accept.json`` (``loop.cek``, "Entry")."""
    target_id = target["id"]
    try:
        url = A.repo_url(target.get("repo"))
    except A.StateError:
        return {"reason": "target_repo_unsafe"}
    try:
        found = F.heads(os.path.join(root, "heads.git"), url, list(TARGET_REFS.values()), git=git, environ=environ)
    except P.PulledError as exc:
        raise Unusable("cek: target heads: %s" % ", ".join(exc.reasons)) from None
    heads = {branch: found[ref] for branch, ref in TARGET_REFS.items()}
    missing = ["head_missing:%s" % b for b, head in heads.items() if head is None]
    if target["kind"] == "copy" and len(missing) == len(heads) and not opened:
        return {"waiting": "copy_genesis", "heads": heads}
    if target["kind"] == "copy" and len(missing) == len(heads):  # its genesis cycle, at targets[].base_sha (25a 7)
        commit = target.get("base_sha")
        if SC.hex40(commit, "base_sha"):
            return dict(_refused(["base_sha_invalid"]), heads=heads)
        state = anchored = status = named = None
        chains = {p: b"" for p in B.STATE_CHAINS}
    elif len(missing) == len(heads):  # a toy with neither head: its genesis cycle, on its main (loop.pulled)
        try:
            commit = F.heads(os.path.join(root, "main.git"), url, [MAIN_REF], git=git, environ=environ)[MAIN_REF]
        except P.PulledError as exc:
            raise Unusable("cek: target heads: %s" % ", ".join(exc.reasons)) from None
        if commit is None:
            return dict(_refused(missing + ["head_missing:main"]), heads=heads)
        state = anchored = status = named = None
        chains = {p: b"" for p in B.STATE_CHAINS}
    elif missing:
        return dict(_refused(missing), heads=heads)
    else:
        state, chains, status = _cek_state(url, heads[B.STATE], root, git, environ)
        if "reason" in state:
            return dict(state, heads=heads)
        anchored = _cek_root(chains, entries)
        if "reason" in anchored:
            return dict(anchored, heads=heads, state=state)
        commit = heads[B.INTEGRATION]
        named = _cek_integration(url, commit, chains[B.STATE_LEDGER], root, git, environ)
        if "reason" in named:
            return dict(named, heads=heads, state=state, root=anchored)
    target_dir = os.path.join(root, "target.git")
    try:
        F.fetch(target_dir, url, commit, git=git, environ=environ)
    except P.PulledError as exc:
        raise Unusable("cek: target fetch: %s" % ", ".join(exc.reasons)) from None
    out = os.path.join(root, "pulled")
    try:
        with G.GitBatch(brain_dir, git=git, environ=environ) as brain, \
                G.GitBatch(target_dir, git=git, environ=environ) as objects:
            manifest = C.assemble(brain, brain_sha, files["setup/summary.json"], files["policy.json"], target_id,
                                  objects, commit, heads[B.STATE], dict(chains), status,
                                  out, run_id=run_id)
    except P.PulledError as exc:
        return dict({"reason": "pulled_refused", "reasons": exc.reasons}, heads=heads)
    assembled = {"target": target_id, "commit": commit,
                 "candidates": sorted({p.split("/")[1] for p in manifest["files"] if p.startswith(P.CANDIDATES + "/")}),
                 "organs": sorted({p.split("/")[1] for p in manifest["files"] if p.startswith(P.ORGANS + "/")}),
                 "snapshot_id": P.read(out).snapshot["snapshot_id"],
                 "mutations": sorted(P.read(out).mutations)}
    # MF4's judgement (D1): the brain's proposal (units.json, its one unit) against the referee's own derivation
    # from the assembled tree, read back the way getir, kos and yaz read their download
    tree = os.path.join(root, "tree")
    art, unit, refused = _read_unit(out, target_id)
    if not refused:
        refused = _extract(art, tree) or _recipe_refused(art, unit, tree, "cek")
    if refused:
        return dict(refused, heads=heads, state=state, root=anchored, integration=named, assembled=assembled)
    return dict({"heads": heads, "state": state, "root": anchored, "integration": named, "assembled": assembled,
                 "profile": {"unit_id": unit["unit_id"]}}, **({"genesis": True} if state is None else {}))


def _cek_state(url: str, head: str, root: str, git: str,
               environ: dict[str, str]) -> tuple[dict[str, Any], dict[str, bytes | None], bytes | None]:
    """MF1's ``verify --previous`` of the target's ``brain/state`` (``loop.state``): its head fetched into
    ``cek-*/state.git``, its parent, when it has one, into ``cek-*/state-previous.git``; ``(loop.state.verify``'s
    line or ``{reason: state_refused, reasons}``, the head's chained files, its ``status.md`` or None)``."""
    dirs = [os.path.join(root, d) for d in ("state.git", "state-previous.git")]
    _fetch_state(dirs[0], url, head, git, environ)
    with G.GitBatch(dirs[0], git=git, environ=environ) as source:
        try:
            prev = ST.parent(source, head)
            if prev is None:
                line = ST.verify(source, head)
            else:
                _fetch_state(dirs[1], url, prev, git, environ)
                with G.GitBatch(dirs[1], git=git, environ=environ) as previous:
                    line = ST.verify(source, head, previous, prev)
            return line, ST.chains(source, head), ST.status(source, head)
        except P.PulledError as exc:
            return {"reason": "state_refused", "reasons": exc.reasons}, {}, None


def _registers(state: dict[str, Any]) -> dict[str, bytes]:
    """The files of ``target.branches.STATE_REGISTERS`` among a head's state files: the ones its root covers
    beside the ledger (tohum/26j)."""
    return {p: state[p] for p in B.STATE_REGISTERS if p in state}


def _cek_root(chains: dict[str, bytes | None], entries: Any) -> dict[str, Any]:
    """MF11's verify of the root (``ledger.anchor.judge`` with the entry read from Rekor, ``loop.rekor``) on the
    verified head's files, its registers under the root with the ledger: ``{root, rekor_uuid}`` or ``{reason:
    root_refused, reasons}``."""
    try:
        found = AN.judge(chains[B.STATE_LEDGER], chains[B.STATE_ROOTS], entries, AN.named(_registers(chains)))
    except AN.Unusable:
        return {"reason": "root_refused", "reasons": ["root_unreadable"]}
    except RK.RekorError as exc:
        raise Unusable("cek: %s" % cli.cause(exc)) from None
    if not found["valid"]:
        return {"reason": "root_refused", "reasons": found["reasons"]}
    return {"root": found["root"], "rekor_uuid": found["rekor_uuid"]}


def _cek_integration(url: str, head: str, ledger: bytes, root: str, git: str,
                     environ: dict[str, str]) -> dict[str, Any]:
    """tohum/13's chain break of ``brain/integration`` (E637, ``loop.integration``) on the verified and anchored
    ledger: the row and commit it names, ``{row_id, kind, sha}``, or ``{reason: integration_refused, reasons,
    integration?}`` (``integration`` the named row and commit, when the ledger names one). Only for a ``revert`` row
    is anything fetched: the head's ancestry without trees (``loop.fetch`` ``history``) into
    ``cek-*/integration-history.git``."""
    try:
        tip = IG.named(ledger)
    except P.PulledError as exc:
        return {"reason": "integration_refused", "reasons": exc.reasons}
    if tip["kind"] != "revert":
        reasons = IG.reasons(tip, head)
    else:
        history_dir = os.path.join(root, "integration-history.git")
        try:
            F.fetch(history_dir, url, head, git=git, environ=environ, history=True)
        except P.PulledError as exc:
            raise Unusable("cek: integration history fetch: %s" % ", ".join(exc.reasons)) from None
        with G.GitBatch(history_dir, git=git, environ=environ) as history:
            reasons = IG.reasons(tip, head, history)
    return {"reason": "integration_refused", "reasons": reasons, "integration": tip} if reasons else tip


def _fetch_state(git_dir: str, url: str, sha: str, git: str, environ: dict[str, str]) -> None:
    try:
        F.fetch(git_dir, url, sha, git=git, environ=environ)
    except P.PulledError as exc:
        raise Unusable("cek: state fetch: %s" % ", ".join(exc.reasons)) from None


def run(name: str, environ: dict[str, str], runner: Any = None, red_control: dict | None = None,
        fetcher: Any = None, http: Any = None, verifier: Any = None, git: str = "git",
        rekor: Any = None, now: Any = None, transport: Any = None,
        signer: Any = None) -> dict[str, Any]:
    """The job's line: ``{job, steps, mfs, ok, targets?, reason?, reasons?, target?}``. ``targets`` holds one line
    per target in the order served, each ``{target, ok, ...}``; the first target refused stops the job (no later
    target is served) and its ``reason``, ``reasons`` and id (``target``) are the job's. ``yaz`` first runs
    ``yaz_offline`` (its line carries ``offline``; a reason stops the job as ``harness_online`` with ``targets``
    ``[]`` and no ``target``, before ``pulled`` is read), then ``yaz_drift`` on every served target (its line
    carries ``drift``); a drifted target stops the job with no target served (``targets`` ``[]``), and so does a
    target whose policy ``yaz_policy`` finds unusable (the line carries ``policy``). ``job_calls``, one list
    made here, is where every root signer the job makes itself counts its runs (``loop.sign`` "The job's count")."""
    if name not in JOBS:
        raise Unusable("unknown job %r" % name)
    job = JOBS[name]
    result: dict[str, Any] = {"job": name, "steps": list(job.steps), "mfs": list(job.mfs), "ok": False}
    if job.runs_code:
        present = sorted(n for n in SECRET_ENV + OIDC_ENV if n in environ)
        if present:
            return dict(result, reason="secret_in_code_job:%s" % present[0])
    if name == "cek":
        d1 = cek_d1(environ, http, verifier, git, rekor)
        if "reason" in d1:
            return dict(result, **d1)
        return dict(result, ok=True, done=["D1"], checked=list(CEK_CHECKED), **d1)
    if name not in TARGET_JOBS:
        raise Unusable("job %r has no entry" % name)
    if name == "yaz":  # MF5 of stage 1: the running harness's own imports, before ``pulled`` or a target is read
        offline = yaz_offline()
        if offline["reasons"]:
            return dict(result, reason="harness_online", reasons=offline["reasons"], targets=[])
        result["offline"] = {"modules": offline["modules"]}
    try:
        served = P.served(_dir(environ, "in", "pulled"))
    except P.PulledError as exc:
        return dict(result, reason="pulled_invalid", reasons=exc.reasons)
    if name == "yaz":  # MF6 of stage 1: every target's setup facts before the first target is served
        drift = yaz_drift(environ, served, transport, now)
        result["drift"] = drift
        if drift["drifted"]:
            first = next(iter(drift["drifted"]))
            return dict(result, reason="drift", reasons=drift["drifted"][first], target=first, targets=[])
        unusable = yaz_policy(environ, served)  # tohum/29v: no target is served on a policy missing a required path
        result["policy"] = unusable
        if unusable:
            first = next(iter(unusable))
            return dict(result, reason="policy_unusable", reasons=unusable[first], target=first, targets=[])
        if drift["stale"]:  # tohum/01c: a clean stop, after every target's reads so that it hides no hard stop
            return dict(result, reason="operator_check_stale", targets=[])
    lines: list[dict[str, Any]] = []
    job_calls: list[dict] = []
    for tid in served:
        line = dict({"target": tid}, **TARGET_JOBS[name](environ, tid, runner=runner, red_control=red_control,
                                                         fetcher=fetcher, now=now, transport=transport,
                                                         signer=signer, job_calls=job_calls))
        lines.append(line)
        if not line["ok"]:
            stop = {k: line[k] for k in ("reason", "reasons") if k in line}
            return dict(result, target=tid, targets=lines, **stop)
    return dict(result, ok=True, targets=lines)


def _getir(environ: dict[str, str], tid: str, fetcher: Any = None, **_: Any) -> dict[str, Any]:
    d2 = getir_d2(environ, tid, fetcher)
    return dict(d2, ok=False) if "reason" in d2 else dict(d2, ok=True, done=["D2"])


def _kos(environ: dict[str, str], tid: str, runner: Any = None, red_control: dict | None = None,
         **_: Any) -> dict[str, Any]:
    d3 = kos_d3(environ, tid, runner, red_control)
    return dict(d3, ok="reason" not in d3)


def _cagir(environ: dict[str, str], tid: str, now: Any = None, **_: Any) -> dict[str, Any]:
    d4 = cagir_d4(environ, tid, now)
    return dict(d4, ok=False) if "reason" in d4 else dict(d4, ok=True, done=["D4"])


def _yaz(environ: dict[str, str], tid: str, transport: Any = None, signer: Any = None, now: Any = None,
         job_calls: list | None = None, **_: Any) -> dict[str, Any]:
    try:
        d5, art, tree = yaz_d5(environ, tid)
        if "reason" in d5:
            return dict(d5, ok=False)
        cases = yaz_cases(environ, tid, art, tree)
        organs = yaz_organs(environ, tid)
        reruns = yaz_reruns(environ, tid)
        written = _yaz_written(environ, tid, d5, art, tree, transport, signer, now, job_calls, cases["cases"])
        return dict(written, organs=organs, reruns=reruns, cases=cases, harness=dict(NO_HUNTER_RUN))
    except OF.Online as exc:
        return {"ok": False, "reason": "harness_online", "reasons": exc.reasons}


def _yaz_written(environ: dict[str, str], tid: str, d5: dict[str, Any], art: Any, tree: str, transport: Any,
                 signer: Any, now: Any, job_calls: list | None = None, cases: list | None = None) -> dict[str, Any]:
    """``yaz``'s line after D5 decided: D7's half, the genesis cycle or D8, the gate, the pass row and D6, which
    adds ``cases`` (the cycle's dev cases) to the dev case set; a genesis cycle writes none."""
    d7, end, lint = yaz_d7(environ, tid, art)
    if "reason" in d7:
        return dict(ok=False, done=["D5"], **d5, **d7)
    if P.genesis(art):  # the activation writes this cycle; D7 watched nothing, D8 starts in the next cycle
        d6 = yaz_genesis(environ, tid, art, tree, d5, transport, signer, now, job_calls)
        if "reason" in d6:
            return dict(ok=False, done=["D5"], **d5, **d7, **d6)
        return dict(ok=True, done=["D5", "D6"], drill=GENESIS_DRILL, **d5, **d7, **d6)
    d8 = yaz_d8(environ, art, tree, d5)
    gate = yaz_gate(environ, art)
    opened = PR.gate_payload() if gate is not None and gate["verdict"] == "open" else None
    judged, passed = yaz_pass(environ, tid, art)
    differs: dict[str, list[str]] = {}
    while True:  # tohum/26p "Yarım kalmış merge", 01b:75-80: a refused landing is its candidate's, not the cycle's
        d6 = yaz_d6(environ, tid, art, tree, d5, transport, signer, now, lint, end, d8, opened, passed, job_calls,
                    cases)
        if "landing_refused" not in d6:
            break
        cid = d6["landing_refused"]
        if cid is None:  # the plant's branch: this cycle plants nothing
            if d8["action"] != "plant":
                raise Unusable("yaz: the writer refused a plant the cycle does not make")
            d8 = PLANT_REFUSED
            continue
        if cid in differs:
            raise Unusable("yaz: the writer refused %s, which D5 had rejected" % cid)
        differs[cid] = d6["why"]
        d5, _, _ = yaz_d5(environ, tid, (art, tree), differs)
        if "reason" in d5:  # the first decision read the same inputs
            raise Unusable("yaz: %s" % d5["reason"])
        d8 = yaz_d8(environ, art, tree, d5)  # a plant is refused only after it: the cycle that plants has no merge
    shown = dict({} if gate is None else {"gate": gate}, **({} if judged is None else {"pass": judged}))
    if "reason" in d6:
        return dict(ok=False, done=["D5"], **d5, **d7, **d6, **shown)
    done = ["D5", "D6"] + (["D7"] if end else []) + ([] if d8["action"] == "off" else ["D8"])
    line = dict(ok=True, done=done, drill=DR.line(d8), **d5, **d7, **d6, **shown)
    if d6["written"]["gozcu"]["hard_stop"]:     # the cycle that tipped the limit is written, and is the last
        return dict(line, ok=False, reason="hard_stop")
    if d8.get("judged", {}).get("verdict") == "FAIL":
        return dict(line, ok=False, reason="drill_fail")
    return line


GENESIS_DRILL = {"action": "off", "why": "genesis"}
PLANT_REFUSED = {"action": "none", "why": W.BRANCH_DIFFERS}  # D8's step of a cycle whose plant the writer refused

# The jobs after ``cek``: each serves ``pulled``'s ``served.json``, one target at a time.
TARGET_JOBS = {"getir": _getir, "kos": _kos, "cagir": _cagir, "yaz": _yaz}


def scope(environ: dict[str, str]) -> str:
    """The writer token's scope (``yaz``'s ``writer scope`` step): ``owner=<owner>`` and ``repositories=<name>,...``
    lines for ``$GITHUB_OUTPUT``, from the ``repo`` of every ``targets[]`` entry of the checkout's
    ``setup/summary.json`` (``loop.cek.targets``, the list ``cek`` serves). Unusable: no ``GITHUB_WORKSPACE``, an
    unreadable file, a refused list, a ``repo`` that is no repository name (``loop.accepted.repo_name``), or
    repositories of more than one owner (one App token is one installation's)."""
    workspace = environ.get("GITHUB_WORKSPACE")
    if not workspace:
        raise Unusable("scope: GITHUB_WORKSPACE is not set")
    try:
        with open(os.path.join(workspace, "setup", "summary.json"), "rb") as fh:
            summary = fh.read()
    except OSError as exc:
        raise Unusable("scope: setup/summary.json unreadable: %s" % cli.cause(exc)) from None
    targets, reasons = C.targets(summary)
    if reasons:
        raise Unusable("scope: %s" % ", ".join(reasons))
    try:
        repos = [A.repo_name(t.get("repo")).split("/") for t in targets]
    except A.StateError:
        raise Unusable("scope: target_repo_unsafe") from None
    owners = sorted({owner for owner, _ in repos})
    if len(owners) != 1:
        raise Unusable("scope: targets of %d owners: %s" % (len(owners), ", ".join(owners)))
    names = list(dict.fromkeys(name for _, name in repos))
    return "owner=%s\nrepositories=%s\n" % (owners[0], ",".join(names))


# tohum/01c: the stops that are not a red job, each with the warning its job shows the operator. The text is fixed:
# nothing read from a file or an API is put in a workflow command.
CLEAN_STOPS = {
    "operator_check_stale": "::warning title=operator check stale::operator check stale: drift.operator_checked_at "
                            "of setup/summary.json is more than 7 days before this job's clock. No target was "
                            "served and nothing was written; the cycle is served again when the summary records "
                            "a newer operator check.",
}


def ending(out: dict[str, Any]) -> tuple[str, int]:
    """What ``run JOB`` ends with for the job's line ``out``: the text of stdout and the exit code. The line is
    always the last line of the text. ``ok`` true: exit 0. A line that is not ok and whose ``reason`` is a key of
    ``CLEAN_STOPS``: that reason's warning on the line before, exit 0. Every other line: exit 1."""
    line = json.dumps(out, sort_keys=True) + "\n"
    if out["ok"]:
        return line, 0
    warning = CLEAN_STOPS.get(out.get("reason"))
    if warning is None:
        return line, 1
    return warning + "\n" + line, 0


def main(argv: list[str]) -> int:
    try:
        if argv == ["render"]:
            sys.stdout.write(render())
            return 0
        if argv == ["scope"]:
            out = os.environ.get("GITHUB_OUTPUT")
            if not out:
                raise Unusable("scope: GITHUB_OUTPUT is not set")
            text = scope(dict(os.environ))
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(text)
            sys.stdout.write(text)
            return 0
        if len(argv) == 2 and argv[0] == "run":
            text, code = ending(run(argv[1], dict(os.environ)))
            sys.stdout.write(text)
            return code
        raise Unusable(USAGE)
    except Unusable as exc:
        sys.stderr.write("unusable input: %s\n" % cli.cause(exc))
        sys.stdout.write(json.dumps({"ok": False, "reason": None}) + "\n")
        return 2


FAULT_LINE = {"ok": False, "reason": None}


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
