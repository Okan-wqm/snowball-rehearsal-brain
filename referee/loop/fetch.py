"""One commit of a repository fetched by its id into a new bare git directory (``çek``, D1; stage 0).

Rules: tohum/08 item 1 (``çek`` is credential-less: it fetches the brain's and the target's requested SHAs and
makes their trees an artifact by content identity; it runs no code), asama-0/01 D1. A private target's reader App
(tohum/08) is not stage 0's: both stage 0 targets are public.

``fetch(git_dir, url, sha)`` checks its inputs first and starts no process when one fails (``PulledError``, every
reason that holds listed):

- ``fetch_sha_unsafe``: ``sha`` is not 40 lowercase hex (``loop.gitobj.SHA``);
- ``fetch_url_unsafe``: ``url`` is not ``https://<host>[:<port>]/<segment>[/<segment>...]`` with a host of
  letters, digits, ``-`` and ``.`` labels and segments of letters, digits, ``_``, ``.`` and ``-`` other than
  ``.`` and ``..``: so no other transport (``file://``, ``ssh``, ``ext::``), no user name or password in the URL,
  no query, nothing git could read as an option;
- ``fetch_dir_unsafe``: ``git_dir`` is not an absolute path, already exists, or its parent is not a directory.

Then two git processes, each with ``loop.gitobj.git_env`` plus ``GIT_TERMINAL_PROMPT=0``, stdin and stdout
``/dev/null``. The configuration git reads is then only the new repository's own (``git init``'s) and the ``-c``
values below, so no credential helper is configured; with no ``GIT_ASKPASS``, ``SSH_ASKPASS`` or ``core.askPass``
and no terminal prompt, nothing is asked for a password:

1. ``git init --bare --quiet <git_dir>``;
2. ``git -c protocol.allow=never -c protocol.https.allow=always -c gc.auto=0 -c maintenance.auto=false
   --git-dir=<git_dir> fetch --quiet --no-tags --no-recurse-submodules --depth=1 --no-write-fetch-head --
   <url> <sha>:refs/pulled``: only https, no tags, no submodule, the one commit with its whole tree and no
   history, kept by the ref ``refs/pulled``; no garbage collection after it.

A process that cannot start is ``git_unavailable``; a non-zero exit is ``fetch_failed:init:<code>`` or
``fetch_failed:fetch:<code>`` (git's own message goes to stderr). Last, the commit is read back through
``loop.gitobj.GitBatch`` with ``loop.gitobj.read`` (its id recomputed); its reasons (``object_missing:<sha>``,
``object_mismatch:<sha>``, ``git_batch_unreadable``) are this step's. On any failure after the inputs are
accepted, ``git_dir`` is removed. The tree under the commit is not read here: ``loop.gitobj.tree_tar`` and
``lookup`` read it and refuse what is missing.

Out of scope, stated: which commit and which URL (the caller's: the bootstrap result's accepted SHA, the target's
heads), a time limit (the job's ``timeout-minutes`` bounds a stalled fetch), what the server or a redirect does
beyond these options (git's), and SHA-256 repositories.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

from loop import gitobj as G
from loop.pulled import PulledError

_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
URL = re.compile(r"https://%s(?:\.%s)*(?::[0-9]{1,5})?(?:/(?!\.{1,2}(?:/|$))[A-Za-z0-9_.-]+)+" % (_LABEL, _LABEL))
REF = "refs/pulled"
CONFIG = ("protocol.allow=never", "protocol.https.allow=always", "gc.auto=0", "maintenance.auto=false")


def _checks(git_dir: str, url: str, sha: str) -> list[str]:
    reasons = []
    if not (isinstance(sha, str) and G.SHA.fullmatch(sha)):
        reasons.append("fetch_sha_unsafe")
    if not (isinstance(url, str) and URL.fullmatch(url)):
        reasons.append("fetch_url_unsafe")
    if not (isinstance(git_dir, str) and os.path.isabs(git_dir) and not os.path.lexists(git_dir)
            and os.path.isdir(os.path.dirname(git_dir.rstrip("/")) or "/")):
        reasons.append("fetch_dir_unsafe")
    return reasons


def argv(git: str, git_dir: str, url: str, sha: str) -> list[list[str]]:
    """The two commands ``fetch`` runs, in order."""
    config = [a for c in CONFIG for a in ("-c", c)]
    return [
        [git, "init", "--bare", "--quiet", git_dir],
        [git, *config, "--git-dir=%s" % git_dir, "fetch", "--quiet", "--no-tags", "--no-recurse-submodules",
         "--depth=1", "--no-write-fetch-head", "--", url, "%s:%s" % (sha, REF)],
    ]


def fetch(git_dir: str, url: str, sha: str, git: str = "git", environ: dict[str, str] | None = None) -> None:
    """Fill the new bare git directory ``git_dir`` with commit ``sha`` of ``url`` by the rules above."""
    reasons = _checks(git_dir, url, sha)
    if reasons:
        raise PulledError(reasons)
    env = dict(G.git_env(environ), GIT_TERMINAL_PROMPT="0")
    try:
        for step, cmd in zip(("init", "fetch"), argv(git, git_dir, url, sha)):
            try:
                code = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=env).returncode
            except OSError:
                raise PulledError(["git_unavailable"]) from None
            if code != 0:
                raise PulledError(["fetch_failed:%s:%d" % (step, code)])
        with G.GitBatch(git_dir, git, environ) as source:
            G.read(source, sha, "commit")
    except BaseException:
        shutil.rmtree(git_dir, ignore_errors=True)
        raise
