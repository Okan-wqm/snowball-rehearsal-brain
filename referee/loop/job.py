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
the file regenerated with ``python -m loop.job render > .github/workflows/loop.yml`` from ``referee/``.

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

**What ``run`` does now.** It checks the job's environment contract and stops: a job that runs code (``getir``,
``kos``) refuses to start when any secret of another job, the OIDC request variables or ``GITHUB_TOKEN`` is in its
environment (``secret_in_code_job:<NAME>``, exit 1). The D1-D8 composition inside the jobs (building each MF's
input from the pulled trees and the previous artifacts, and the cycle's one ``brain/state`` commit) is not wired
yet: ``run`` prints ``{ok: false, reason: cycle_not_wired, ...}`` and exits 1, so a cycle cannot pass green
through a job that did nothing. No MF of asama-0/14 owns that composition (reported in the founder ledger).

Out of scope, stated: the ``control`` command itself (the seed's, asama-1/13), whether the seed's ``wiring`` check
accepts this file's YAML (the seed's YAML subset is not written in any page this clone has; this module writes
only block mappings, block sequences, plain and single-quoted scalars, ``|`` literal blocks and ``{}``), and the
behaviour of the pinned actions (their tags were resolved to the SHAs below on 2026-10-30 with ``git ls-remote``).

Command line, from ``referee/``::

    python -m loop.job render        # the workflow on stdout, exit 0
    python -m loop.job run JOB       # one JSON line on stdout; exit 1 (refused or not wired), 2 unusable
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, NamedTuple

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
    "cek": Job(("D1",), (1, 4, 11), False, {"contents": "read", "actions": "read"}, {}, (), (), "pulled"),
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

def run(name: str, environ: dict[str, str]) -> dict[str, Any]:
    if name not in JOBS:
        raise Unusable("unknown job %r" % name)
    job = JOBS[name]
    result: dict[str, Any] = {"job": name, "steps": list(job.steps), "mfs": list(job.mfs), "ok": False}
    if job.runs_code:
        present = sorted(n for n in SECRET_ENV + OIDC_ENV if n in environ)
        if present:
            return dict(result, reason="secret_in_code_job:%s" % present[0])
    return dict(result, reason="cycle_not_wired")


def main(argv: list[str]) -> int:
    try:
        if argv == ["render"]:
            sys.stdout.write(render())
            return 0
        if len(argv) == 2 and argv[0] == "run":
            sys.stdout.write(json.dumps(run(argv[1], dict(os.environ)), sort_keys=True) + "\n")
            return 1
        raise Unusable(USAGE)
    except Unusable as exc:
        sys.stderr.write("unusable input: %s\n" % exc)
        sys.stdout.write(json.dumps({"ok": False, "reason": None}) + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
