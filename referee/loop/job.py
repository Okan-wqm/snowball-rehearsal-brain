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
that runs both jobs on the handed-over bytes, a stated unread download, or a producer that stops unwired.

**The shape of every job**, in this order:

1. ``control`` (D0): fetches the referee repository's ``main`` (``bootstrap/`` and the root files, so
   ``control.json`` as it is now, not as it was at the run's commit) and runs the seed's ``control`` command.
   A non-zero exit (the kill switch, or an unreadable ``control.json``) fails the job and every later step and
   every job that needs it is skipped. Exit 0 writes ``go=true`` or ``go=false`` to ``$GITHUB_OUTPUT``;
   ``go=false`` (a scheduled run while ``loop_schedule`` is not true) ends the job green with every later step
   skipped, i.e. ``paused``. The command's flags are this module's assumption (no seed page gives them).
2. the writer App token (``yaz`` only), made inside the job.
3. checkout of the run's own commit of the referee repository, ``persist-credentials: false``.
4. one download per artifact the job reads, by the producing job's artifact id, ``digest-mismatch: error``.
5. ``python3 -m loop.job run <job>``, with the expected artifact digests and the job's secrets in ``env``.
6. the upload of the job's artifact, whose id and digest are job outputs.

Every step after ``control`` runs only if ``go`` is true; no step continues on error.

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
  packages), writing ``$RUNNER_TEMP/out/results``. Its index is in the output
  (``index``) and ``done`` is ``["D3"]``. D7 (the sentinel) and D8 (the drill) of this job are not wired, so the
  job still ends ``cycle_not_wired``, exit 1, after D3: the upload step does not run and ``yaz`` gets nothing.
- ``yaz`` runs D5 (``yaz_d5``): it reads ``control.json`` from the ``control`` step's clone
  (``$RUNNER_TEMP/control/control.json``; unreadable is unusable, exit 2), ``$RUNNER_TEMP/in/pulled`` as ``kos`` does
  (the same refusals, the same one unit), extracts the tree under ``$RUNNER_TEMP/work`` and calls ``loop.decide``
  on ``$RUNNER_TEMP/in/results``: ``decisions`` (every candidate's ``decision`` and ``reasons``) and ``merge`` are in
  the output and ``done`` is ``["D5"]``. The cycle's state (which merges' sentinels are unfinished) is D1's read of
  ``brain/state``, not wired, so D5 is given ``None`` and every candidate carries ``sentinel_state_unread``: no
  candidate merges. D6-D8 are not wired, so the job ends ``cycle_not_wired``, exit 1, after D5, writing nothing.
- ``cek`` runs D1 as far as it is wired (``cek_d1``). First the accepted-SHA check: it reads the bootstrap
  referee's last signed state with ``loop.accepted.read_state`` (the Actions API of ``$GITHUB_REPOSITORY`` with the
  job's ``GITHUB_TOKEN``, ``actions: read``; the artifact verified by ``sigstore`` on PATH), fetches the accepted
  brain commit with ``loop.fetch`` from ``loop.accepted.repo_url`` of ``$LOOP_BRAIN_REPO`` (the operator's
  repository variable ``BRAIN_REPO``, an assumption: no page this clone has names where the loop finds the brain
  repository's name) into ``$RUNNER_TEMP/work/cek-*/brain.git``, and compares its ``referee/`` hash with the last
  transfer row of the checkout's ``setup/imports.jsonl`` (``loop.accepted.last_import``, ``check_tree``). Then the
  target half, for the target ``$LOOP_TARGET`` (the operator's repository variable ``LOOP_TARGET``, an assumption
  too: no page says which of ``targets[]`` a run serves): its ``targets[]`` entry in the checkout's
  ``setup/summary.json`` (``loop.cek.target_entry``, the reader ``assemble`` uses), its ``repo`` made a URL by
  ``loop.accepted.repo_url``, the heads of ``brain/state`` and ``brain/integration`` read credential-less with
  ``loop.fetch.heads``, ``brain/integration``'s head fetched with ``loop.fetch`` into ``cek-*/target.git``, and
  ``loop.cek.assemble`` run on the two repositories' objects with the checkout's ``policy.json``, writing ``pulled``
  into ``cek-*/pulled``, not into ``out/pulled``: the upload takes the artifact only once D1's other checks pass.
  An unset variable, a state that is absent, unreadable or unverified, an unreadable checkout file, a failed
  listing and a failed fetch are unusable (exit 2: 29b's reader stops). Refusals (exit 1): ``imports_broken``,
  ``imports_no_transfer``, ``imports_invalid``, ``referee_tree_refused`` (with the hash's reasons),
  ``referee_tree_mismatch``; ``summary_unreadable``, ``target_unknown``, ``target_ambiguous``,
  ``target_repo_unsafe``; ``head_missing:<branch>`` for each head the target lacks (before genesis it has neither;
  nothing of the target is fetched); ``pulled_refused`` with ``assemble``'s reasons. Then MF4's judgement: the
  assembled artifact is read back as the other jobs read their download (``loop.pulled.read``, exactly one entry of
  ``units``, else ``units_not_one``; the tree extracted by ``loop.pulled.extract_tree`` into ``cek-*/tree``, a tree
  it refuses is ``pulled_invalid``) and the unit gets the static check ``getir`` runs
  (``profile.unit_verify.check_recipe`` with the artifact's policy and ``targets[]`` entry: MF6's recipe rules and,
  on the tree, ``profile.derive check`` of the recipe against the referee's own derivation of that tree; a reason
  is ``recipe_refused`` with the reasons). A refusal after the assembly carries ``heads`` and ``assembled``. When
  all of it holds, the line has ``accepted`` (``brain_sha``, ``referee_tree_sha256``, ``result_sha256``,
  ``artifact_id``), ``heads`` (branch to commit), ``assembled`` (``target``, ``commit``, ``candidates``),
  ``profile`` (``unit_id``) and ``checked`` ``CEK_CHECKED``, and the job still ends ``cycle_not_wired``, exit 1:
  the rest of D1 (``verify --previous`` of ``brain/state``'s ledger, the root signature) is not wired, so nothing
  is uploaded and in a real run ``kos`` is not reached. The proposal stage 0 judges is the recipe alone
  (tohum/14); no other profile field is proposed, so none is compared.
- ``cagir`` stops at once with ``cycle_not_wired`` (exit 1). The D1-D8 composition inside the jobs (building each
  MF's input from the pulled trees and the previous artifacts, and the cycle's one ``brain/state`` commit) has no
  MF of asama-0/14 that owns it (reported in the founder ledger, spec-036).

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
    python -m loop.job run JOB       # one JSON line on stdout; exit 0 the job's steps all done (``ok`` true),
                                     # 1 refused or not wired, 2 unusable (RUNNER_TEMP unset, an input
                                     # unusable, getir's fetch failed)
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from typing import Any, NamedTuple

from loop import accepted as A
from loop import cek as C
from loop import decide as E
from loop import fetch as F
from loop import gitobj as G
from loop import pulled as P
from profile import derive as D
from profile import unit_verify as U
from runner import deps_npm as N
from runner import kos as K
from target import branches as B
import cli

USAGE = "usage: python -m loop.job render | run JOB"

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

# The writer App token: made in ``yaz``, limited to what target.write uses (tohum/25 item 6, MF9).
APP_INPUTS = {
    "app-id": "${{ secrets.WRITER_APP_ID }}",
    "private-key": "${{ secrets.WRITER_APP_PRIVATE_KEY }}",
    "owner": "${{ vars.TARGET_OWNER }}",
    "permission-contents": "write",
    "permission-pull-requests": "write",
    "permission-checks": "write",
}

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


JOBS: dict[str, Job] = {
    "cek": Job(("D1",), (1, 4, 11), False, {"contents": "read", "actions": "read"},
               {"GITHUB_TOKEN": "${{ github.token }}", "LOOP_BRAIN_REPO": "${{ vars.BRAIN_REPO }}",
                "LOOP_TARGET": "${{ vars.LOOP_TARGET }}"},
               (), (), "pulled"),
    "getir": Job(("D2",), (5,), True, {}, {}, ("cek",), ("pulled",), "deps"),
    "kos": Job(("D3", "D7", "D8"), (3, 6, 12), True, {}, {}, ("cek", "getir"), ("pulled", "deps"), "results"),
    "cagir": Job(("D4",), (2, 15), False, {},
                 {"CLAUDE_CODE_OAUTH_TOKEN": "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}"},
                 ("cek",), ("pulled",), "response"),
    "yaz": Job(("D5", "D6", "D7", "D8"), (2, 7, 8, 9, 10, 11, 13, 14, 16), False,
               {"id-token": "write", "contents": "read"},
               {"WRITER_TOKEN": "${{ steps.app.outputs.token }}"},
               ("cek", "getir", "kos", "cagir"), ("pulled", "deps", "results", "response"), None),
}

# What cek reads from the referee repository's checkout, and the target branches whose heads it reads (asama-0/01 D1).
CEK_FILES = ("setup/imports.jsonl", "setup/summary.json", "policy.json")
TARGET_REFS = {b: "refs/heads/" + b for b in (B.STATE, B.INTEGRATION)}
# What cek's line lists as checked when D1 holds as far as it is wired.
CEK_CHECKED = ("accepted_sha", "referee_tree", "heads", "assembled", "profile")

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
    if name == "yaz":
        steps.append({"name": "writer token", "id": "app", "if": GO, "uses": APP_TOKEN, "with": dict(APP_INPUTS)})
    steps.append({"name": "checkout", "if": GO, "uses": CHECKOUT, "with": {"persist-credentials": "false"}})
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


def _pulled_unit(environ: dict[str, str]) -> tuple[Any, Any, dict | None]:
    """``$RUNNER_TEMP/in/pulled`` read by ``_read_unit``. Shared by ``getir``, ``kos`` and ``yaz``, so each reads the
    same artifact the same way."""
    return _read_unit(_dir(environ, "in", "pulled"))


def _read_unit(path: str) -> tuple[Any, Any, dict | None]:
    """The ``pulled`` artifact at ``path`` read by ``loop.pulled.read`` and its one unit (stage 0 runs exactly one
    entry of ``units``): ``(artifact, unit, None)``, or ``(None, None, {reason, reasons?})`` (``pulled_invalid``,
    ``units_not_one``). ``cek`` reads its own assembly with it, the other jobs their download."""
    try:
        art = P.read(path)
    except P.PulledError as exc:
        return None, None, {"reason": "pulled_invalid", "reasons": exc.reasons}
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


def getir_d2(environ: dict[str, str], fetcher: Any = None) -> dict[str, Any]:
    """D2 of ``getir`` (see the module docstring): ``{reason?, reasons?, deps?, licenses?}``."""
    art, unit, refused = _pulled_unit(environ)
    if refused:
        return refused
    _, tree, refused = _pulled_tree(environ, art, "getir")
    if refused:
        return refused
    refused = _recipe_refused(art, unit, tree, "getir")
    if refused:
        return refused
    out = _dir(environ, "out", "deps")
    try:
        os.makedirs(out)
    except FileExistsError:
        raise Unusable("getir: %s exists" % out) from None
    try:
        report = N.fetch(os.path.join(tree, D.norm_path(unit["lockfiles"][0])), out, fetcher or N.https_fetcher,
                         N.DEFAULT_REGISTRIES, unit["install_scripts_required"], art.policy,
                         cap=unit["limits"].get("deps_bytes"))
    except N.DepsError as exc:
        raise Unusable("getir: %s" % cli.cause(exc)) from None
    if not report["ok"]:
        return {"reason": "deps_refused", "reasons": report["reasons"]}
    return {"deps": {k: report[k] for k in ("address", "packages", "bytes", "artefact")},
            "licenses": report["licenses"]}


def kos_d3(environ: dict[str, str], runner: Any = None, red_control: dict | None = None) -> dict[str, Any]:
    """D3 of ``kos`` (see the module docstring): ``{reason?, reasons?, index?}``."""
    art, unit, refused = _pulled_unit(environ)
    if refused:
        return refused
    deps = _dir(environ, "in", "deps")
    if not (os.path.isdir(deps) and os.listdir(deps)):
        deps = None
    else:
        try:
            deps = N.artifact_in(deps)
        except N.DepsError as exc:
            return {"reason": "deps_invalid", "reasons": [cli.cause(exc)]}
    root, tree, refused = _pulled_tree(environ, art, "kos")
    if refused:
        return refused
    diffs = {cid: files["diff.patch"] for cid, files in art.candidates.items()}
    try:
        index = K.results(unit, tree, art.policy, red_control or RED_CONTROL, diffs, _dir(environ, "out", "results"),
                          deps, art.target, runner, base=root)
    except K.UNUSABLE as exc:
        raise Unusable("kos: %s" % cli.cause(exc)) from None
    return {"index": index}


def yaz_d5(environ: dict[str, str]) -> dict[str, Any]:
    """D5 of ``yaz`` (see the module docstring): ``{reason?, reasons?, decisions?, merge?}``."""
    try:
        with open(_dir(environ, "control", "control.json"), encoding="utf-8") as fh:
            control = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Unusable("yaz: control.json unreadable: %s" % cli.cause(exc)) from None
    art, unit, refused = _pulled_unit(environ)
    if refused:
        return refused
    _, tree, refused = _pulled_tree(environ, art, "yaz")
    if refused:
        return refused
    try:
        # the cycle's state (brain/state: which merges' sentinels are unfinished) is D1's read, not wired: None
        return E.decide(art, unit, tree, _dir(environ, "in", "results"), control, None)
    except (E.Unusable, D.DeriveError) as exc:
        raise Unusable("yaz: %s" % cli.cause(exc)) from None


def cek_d1(environ: dict[str, str], http: Any = None, verifier: Any = None, git: str = "git") -> dict[str, Any]:
    """D1 of ``cek`` as far as it is wired (see the module docstring): ``{reason?, reasons?, accepted?, heads?,
    assembled?}``."""
    for name in ("GITHUB_REPOSITORY", "GITHUB_TOKEN", "GITHUB_WORKSPACE", "LOOP_BRAIN_REPO", "LOOP_TARGET"):
        if not environ.get(name):
            raise Unusable("cek: %s is not set" % name)
    try:
        state = A.read_state(http or A.ActionsHttp(environ["GITHUB_TOKEN"]), environ["GITHUB_REPOSITORY"],
                             verifier=verifier or A.run_verifier)
        brain_url = A.repo_url(environ["LOOP_BRAIN_REPO"])
    except A.StateError as exc:
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
        imported, _ = A.last_import(files["setup/imports.jsonl"])
        with G.GitBatch(brain_dir, git=git, environ=environ) as brain:
            tree = A.check_tree(brain, sha, imported)
    except A.StateError as exc:
        return _refused(exc.reasons)
    accepted = {"brain_sha": sha, "referee_tree_sha256": tree, "result_sha256": state["result_sha256"],
                "artifact_id": state["artifact_id"]}
    pulled = _cek_target(environ, files, brain_dir, sha, root, git)
    return dict(pulled, accepted=accepted)


def _refused(reasons: list[str]) -> dict[str, Any]:
    return dict({"reason": reasons[0]}, **({"reasons": reasons[1:]} if reasons[1:] else {}))


def _cek_target(environ: dict[str, str], files: dict[str, bytes], brain_dir: str, brain_sha: str, root: str,
                git: str) -> dict[str, Any]:
    """The target half of D1 (see the module docstring): ``{reason?, reasons?, heads?, assembled?}``."""
    target_id = environ["LOOP_TARGET"]
    target, reasons = C.target_entry(files["setup/summary.json"], target_id)
    if reasons:
        return _refused(reasons)
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
    if missing:
        return dict(_refused(missing), heads=heads)
    target_dir = os.path.join(root, "target.git")
    commit = heads[B.INTEGRATION]
    try:
        F.fetch(target_dir, url, commit, git=git, environ=environ)
    except P.PulledError as exc:
        raise Unusable("cek: target fetch: %s" % ", ".join(exc.reasons)) from None
    out = os.path.join(root, "pulled")
    try:
        with G.GitBatch(brain_dir, git=git, environ=environ) as brain, \
                G.GitBatch(target_dir, git=git, environ=environ) as objects:
            manifest = C.assemble(brain, brain_sha, files["setup/summary.json"], files["policy.json"], target_id,
                                  objects, commit, out)
    except P.PulledError as exc:
        return dict({"reason": "pulled_refused", "reasons": exc.reasons}, heads=heads)
    assembled = {"target": target_id, "commit": commit,
                 "candidates": sorted({p.split("/")[1] for p in manifest["files"] if p.startswith(P.CANDIDATES + "/")})}
    # MF4's judgement (D1): the brain's proposal (units.json, its one unit) against the referee's own derivation
    # from the assembled tree, read back the way getir, kos and yaz read their download
    tree = os.path.join(root, "tree")
    art, unit, refused = _read_unit(out)
    if not refused:
        refused = _extract(art, tree) or _recipe_refused(art, unit, tree, "cek")
    if refused:
        return dict(refused, heads=heads, assembled=assembled)
    return {"heads": heads, "assembled": assembled, "profile": {"unit_id": unit["unit_id"]}}


def run(name: str, environ: dict[str, str], runner: Any = None, red_control: dict | None = None,
        fetcher: Any = None, http: Any = None, verifier: Any = None, git: str = "git") -> dict[str, Any]:
    if name not in JOBS:
        raise Unusable("unknown job %r" % name)
    job = JOBS[name]
    result: dict[str, Any] = {"job": name, "steps": list(job.steps), "mfs": list(job.mfs), "ok": False}
    if job.runs_code:
        present = sorted(n for n in SECRET_ENV + OIDC_ENV if n in environ)
        if present:
            return dict(result, reason="secret_in_code_job:%s" % present[0])
    if name == "cek":
        d1 = cek_d1(environ, http, verifier, git)
        if "reason" in d1:
            return dict(result, **d1)
        return dict(result, reason="cycle_not_wired", checked=list(CEK_CHECKED),
                    **d1)
    if name == "getir":
        d2 = getir_d2(environ, fetcher)
        if "reason" in d2:
            return dict(result, **d2)
        return dict(result, ok=True, done=["D2"], **d2)
    if name == "kos":
        d3 = kos_d3(environ, runner, red_control)
        if "reason" in d3:
            return dict(result, **d3)
        return dict(result, reason="cycle_not_wired", done=["D3"], index=d3["index"])
    if name == "yaz":
        d5 = yaz_d5(environ)
        if "reason" in d5:
            return dict(result, **d5)
        return dict(result, reason="cycle_not_wired", done=["D5"], **d5)
    return dict(result, reason="cycle_not_wired")


def main(argv: list[str]) -> int:
    try:
        if argv == ["render"]:
            sys.stdout.write(render())
            return 0
        if len(argv) == 2 and argv[0] == "run":
            out = run(argv[1], dict(os.environ))
            sys.stdout.write(json.dumps(out, sort_keys=True) + "\n")
            return 0 if out["ok"] else 1
        raise Unusable(USAGE)
    except Unusable as exc:
        sys.stderr.write("unusable input: %s\n" % cli.cause(exc))
        sys.stdout.write(json.dumps({"ok": False, "reason": None}) + "\n")
        return 2


FAULT_LINE = {"ok": False, "reason": None}


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
