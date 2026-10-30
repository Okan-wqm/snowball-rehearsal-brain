"""``target.write``: the referee's one way to write to a target repository (stage 0, MF9).

Rules: asama-0/14 row 9, asama-0/09 test 49, asama-0/02 property 13 (the target is written only through
the API and only under ``refs/heads/brain/**``; writes to ``main``: 0), tohum/26a (``target.write``: branch,
PR, check, merge or revert request; GitHub REST and Git Data API), tohum/01b (``brain/integration`` takes
changes only by pull request, merges are serial), tohum/07 (the referee reverts a merge), asama-0/09 test 25
(the revert commit's tree is the tree of the merge's first parent), tohum/07 (no force push).

Every request passes ``Guard.check`` before it is sent; a refused request is never sent (``Refused``). The
guard allows exactly these routes, under ``/repos/<owner>/<repo>/`` of the one configured repository, and
nothing else (no contents API, no ``merges`` endpoint, no ref deletion, no repository settings, no GraphQL,
no other repository):

- ``GET git/ref/heads/<branch>``, ``GET git/commits/<sha>``, ``GET pulls/<n>`` (reads; ``<branch>`` must be
  a valid branch name, it need not be under ``brain/``);
- ``POST git/refs`` ``{ref, sha}``: ``ref`` under ``refs/heads/brain/``;
- ``PATCH git/refs/heads/<branch>`` ``{sha, force?}``: branch under ``brain/``, ``force`` absent or false;
- ``POST git/commits`` ``{message, tree, parents}``: one or two parents (creates an object, writes no ref);
- ``POST pulls`` ``{title, head, base, body?}``: ``head`` and ``base`` are branches under ``brain/`` of this
  repository (a ``owner:branch`` head is not a valid name);
- ``POST check-runs`` ``{name, head_sha, status: completed, conclusion: success|failure, output?}`` (a check
  writes no ref; it may name any commit);
- ``PUT pulls/<n>/merge`` ``{sha, merge_method: merge, commit_title?}``: only a pull request this guard has
  seen in a response (``GET pulls/<n>`` or ``POST pulls``) as open, with base and head under ``brain/`` and
  head sha equal to ``sha``. ``merge_method`` is ``merge`` so that a merge has two parents and its first
  parent is the base it was made on (the revert rule reads that).

Fields outside the listed ones, a body that is not an object, a sha that is not 40 lowercase hex, and a path
with a query, fragment, ``%``, backslash, whitespace, ``..``, an empty segment or a trailing slash are
refused. A branch name under ``brain/`` (``ref_invalid`` otherwise) is ``[A-Za-z0-9._/-]`` only, with git's
rules on top: no empty component (no leading, trailing or double slash), no component starting with ``.`` or
ending with ``.lock``, no ``..``, no trailing ``.``. Prefixes are exact and case-sensitive: ``refs/heads/Brain/x``,
``refs/heads/brain`` and ``refs/heads/brainx/y`` are outside.

Revert (``revert_commit``): only the current head of the branch may be reverted, and only a commit with
exactly two parents (a merge); the revert commit has tree = the first parent's tree and one parent, the merge.
A merge that is not the head is refused (``revert_not_head``), since the first parent's tree would also undo
every later merge. ``Writer.revert`` puts that commit on a new ``brain/c/`` branch and opens a pull request
into the branch: ``brain/integration`` takes no direct push (tohum/01b), so the revert goes through check and
merge like any candidate. Merging it with ``merge`` leaves the merge's first parent's tree on the branch.

Known limits, stated: the base of a pull request is checked from the response the guard saw; GitHub's merge
endpoint pins the head (``sha``), not the base, so a base changed between that response and the merge is not
seen here (in write mode the target's ruleset keeps the writer App off ``main``, tohum/21). Rulesets are
enforced by GitHub, not here. Blobs and trees (``POST git/blobs``, ``git/trees``) are not allowed yet: their
first caller is ``ledger.append`` (MF10).

Transport: ``HttpTransport`` sends to ``https://api.github.com`` with the token; it follows no redirect (a
redirect would carry the token and the write elsewhere), so a 3xx is an ``ApiError``. ``Writer`` takes any
callable ``(method, path, body) -> (status, json)``; tests give it an in-process fake.

Command line (one JSON line, exit 0 allowed, 1 refused, 2 unusable input)::

    python -m target.write guard PLAN    PLAN = {repo, pulls?: {n: {base, head, head_sha, state}},
                                                 requests: [{method, path, body?}]}
        -> {ok, reasons: ["<index>:<reason>"], refs: [refs written by the allowed requests]}
    python -m target.write revert STATE  STATE = {head, merge, commits: {sha: {tree, parents}}}
        -> {ok, reasons, commit: {tree, parents} | null}
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Callable

API = "https://api.github.com"
HEADS = "refs/heads/"
BRAIN = "refs/heads/brain/"

_SHA = re.compile(r"[0-9a-f]{40}")
_NAME = re.compile(r"[A-Za-z0-9._/-]+")
_REPO = re.compile(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+")
_N = r"[1-9][0-9]{0,9}"
_CONCLUSIONS = ("success", "failure")

Transport = Callable[[str, str, Any], "tuple[int, Any]"]


class Refused(Exception):
    """The guard refused a request; it was not sent."""

    def __init__(self, reasons: list[str]):
        super().__init__(", ".join(reasons))
        self.reasons = reasons


class ApiError(Exception):
    """The API answered with an error status, or with a body that does not say what was asked."""

    def __init__(self, status: int | None, message: str):
        super().__init__("%s: %s" % (status, message))
        self.status = status


class Unusable(ValueError):
    pass


# ---------------------------------------------------------------- refs

def branch_syntax(name: Any) -> bool:
    """A branch name (after ``refs/heads/``) this module accepts at all."""
    if not isinstance(name, str) or not _NAME.fullmatch(name) or ".." in name or name.endswith("."):
        return False
    return all(part and not part.startswith(".") and not part.endswith(".lock") for part in name.split("/"))


def ref_reasons(ref: Any) -> list[str]:
    """``[]`` when ``ref`` is a writable ref: a valid branch under ``refs/heads/brain/``."""
    if not isinstance(ref, str) or not ref.startswith(BRAIN):
        return ["ref_outside_brain"]
    return [] if branch_syntax(ref[len(HEADS):]) else ["ref_invalid"]


def branch_reasons(name: Any) -> list[str]:
    return ref_reasons(HEADS + name if isinstance(name, str) else name)


# ---------------------------------------------------------------- guard

def _keys(body: Any, required: set[str], optional: set[str] = frozenset()) -> bool:
    return isinstance(body, dict) and required <= set(body) <= required | optional


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA.fullmatch(value))


def _text(value: Any, empty: bool = False) -> bool:
    return isinstance(value, str) and (empty or bool(value))


class Guard:
    """The route and ref rules of the module docstring, with the pull requests seen in responses."""

    def __init__(self, repo: str, pulls: dict[int, dict] | None = None):
        if not isinstance(repo, str) or not _REPO.fullmatch(repo) or ".." in repo:
            raise Unusable("repo must be owner/name")
        self.prefix = "/repos/%s/" % repo
        self.pulls: dict[int, dict] = dict(pulls or {})

    def _rest(self, path: Any) -> str | None:
        if not isinstance(path, str) or not path.startswith(self.prefix):
            return None
        rest = path[len(self.prefix):]
        if (re.search(r"[?#%\\\s]", rest) or ".." in rest or not rest or rest.endswith("/")
                or "//" in rest):
            return None
        return rest

    def check(self, method: Any, path: Any, body: Any = None) -> tuple[list[str], list[str]]:
        """Return ``(reasons, refs)``: why the request is refused, and the refs it writes when allowed."""
        rest = self._rest(path)
        if rest is None:
            return ["route_not_allowed"], []
        if method == "GET":
            if body is not None:
                return ["body_invalid"], []
            m = re.fullmatch(r"git/ref/heads/(.+)", rest)
            if m:
                return ([] if branch_syntax(m.group(1)) else ["ref_invalid"]), []
            if re.fullmatch(r"git/commits/[0-9a-f]{40}|pulls/" + _N, rest):
                return [], []
            return ["route_not_allowed"], []
        if method == "POST" and rest == "git/refs":
            if not _keys(body, {"ref", "sha"}) or not _sha(body["sha"]):
                return ["body_invalid"], []
            reasons = ref_reasons(body["ref"])
            return reasons, ([] if reasons else [body["ref"]])
        if method == "PATCH":
            m = re.fullmatch(r"git/refs/heads/(.+)", rest)
            if not m:
                return ["route_not_allowed"], []
            reasons = branch_reasons(m.group(1))
            if not _keys(body, {"sha"}, {"force"}) or not _sha(body["sha"]):
                reasons = reasons + ["body_invalid"]
            elif "force" in body and body["force"] is not False:
                reasons = reasons + ["force_update"]
            return reasons, ([] if reasons else [HEADS + m.group(1)])
        if method == "POST" and rest == "git/commits":
            ok = (_keys(body, {"message", "tree", "parents"}) and _text(body["message"]) and _sha(body["tree"])
                  and isinstance(body["parents"], list) and 1 <= len(body["parents"]) <= 2
                  and all(_sha(p) for p in body["parents"]))
            return ([] if ok else ["body_invalid"]), []
        if method == "POST" and rest == "pulls":
            if not _keys(body, {"title", "head", "base"}, {"body"}) or not _text(body["title"]) \
                    or not _text(body.get("body", ""), empty=True):
                return ["body_invalid"], []
            return sorted(set(branch_reasons(body["head"]) + branch_reasons(body["base"]))), []
        if method == "POST" and rest == "check-runs":
            ok = (_keys(body, {"name", "head_sha", "status", "conclusion"}, {"output"}) and _text(body["name"])
                  and _sha(body["head_sha"]) and body["status"] == "completed"
                  and body["conclusion"] in _CONCLUSIONS
                  and ("output" not in body or (_keys(body["output"], {"title", "summary"})
                                                and _text(body["output"]["title"])
                                                and _text(body["output"]["summary"], empty=True))))
            return ([] if ok else ["body_invalid"]), []
        m = re.fullmatch(r"pulls/(%s)/merge" % _N, rest)
        if method == "PUT" and m:
            if not _keys(body, {"sha", "merge_method"}, {"commit_title"}) or not _sha(body["sha"]) \
                    or ("commit_title" in body and not _text(body["commit_title"])):
                return ["body_invalid"], []
            reasons = [] if body["merge_method"] == "merge" else ["merge_method"]
            pull = self.pulls.get(int(m.group(1)))
            if pull is None:
                return reasons + ["merge_unknown_pull"], []
            reasons += branch_reasons(pull.get("base")) + branch_reasons(pull.get("head"))
            if pull.get("state") != "open":
                reasons.append("merge_not_open")
            if pull.get("head_sha") != body["sha"]:
                reasons.append("merge_head_moved")
            reasons = sorted(set(reasons))
            return reasons, ([] if reasons else [HEADS + pull["base"]])
        return ["route_not_allowed"], []

    def observe(self, method: str, path: str, data: Any) -> None:
        """Record a pull request from a response to ``GET pulls/<n>`` or ``POST pulls``."""
        rest = self._rest(path)
        if rest is None or not ((method == "GET" and re.fullmatch(r"pulls/" + _N, rest))
                                or (method == "POST" and rest == "pulls")):
            return
        pull = _pull(data)
        if method == "GET" and pull["number"] != int(rest.split("/")[1]):
            raise ApiError(None, "pull response is for another number")
        self.pulls[pull["number"]] = pull


def _pull(data: Any) -> dict:
    try:
        number, state = data["number"], data["state"]
        base, head, head_sha = data["base"]["ref"], data["head"]["ref"], data["head"]["sha"]
    except (KeyError, TypeError) as exc:
        raise ApiError(None, "pull response without %s" % exc) from None
    if not isinstance(number, int) or isinstance(number, bool) or not _sha(head_sha):
        raise ApiError(None, "pull response with a bad number or head sha")
    return {"number": number, "state": state, "base": base, "head": head, "head_sha": head_sha}


# ---------------------------------------------------------------- revert

def revert_commit(commits: dict, head: str, merge: str) -> tuple[list[str], dict | None]:
    """The revert of ``merge`` on a branch whose head is ``head``: ``{tree, parents}`` or reasons."""
    if merge != head:
        return ["revert_not_head"], None
    rec = commits.get(merge)
    if not isinstance(rec, dict):
        return ["commit_unknown"], None
    parents = rec.get("parents")
    if not isinstance(parents, list) or len(parents) != 2:
        return ["revert_not_merge"], None
    first = commits.get(parents[0])
    if not isinstance(first, dict) or not _sha(first.get("tree")):
        return ["commit_unknown"], None
    return [], {"tree": first["tree"], "parents": [merge]}


# ---------------------------------------------------------------- writer

class Writer:
    """Branch, commit, pull request, check, merge and revert on one repository, every request guarded."""

    def __init__(self, repo: str, transport: Transport):
        self.repo = repo
        self.guard = Guard(repo)
        self.transport = transport

    def _call(self, method: str, rest: str, body: Any = None) -> Any:
        path = self.guard.prefix + rest
        reasons, _ = self.guard.check(method, path, body)
        if reasons:
            raise Refused(reasons)
        status, data = self.transport(method, path, body)
        if not isinstance(status, int) or not 200 <= status < 300:
            raise ApiError(status, "%s %s" % (method, path))
        self.guard.observe(method, path, data)
        return data

    def head(self, branch: str) -> str:
        data = self._call("GET", "git/ref/heads/" + branch)
        try:
            ref, sha = data["ref"], data["object"]["sha"]
        except (KeyError, TypeError):
            raise ApiError(None, "ref response without ref or object.sha") from None
        if ref != HEADS + branch or not _sha(sha):
            raise ApiError(None, "ref response is for %r, not %r" % (ref, HEADS + branch))
        return sha

    def read_commit(self, sha: str) -> dict:
        data = self._call("GET", "git/commits/" + sha)
        try:
            got, tree, parents = data["sha"], data["tree"]["sha"], [p["sha"] for p in data["parents"]]
        except (KeyError, TypeError):
            raise ApiError(None, "commit response without sha, tree or parents") from None
        if got != sha or not _sha(tree) or not all(_sha(p) for p in parents):
            raise ApiError(None, "commit response is not for %s" % sha)
        return {"tree": tree, "parents": parents}

    def create_branch(self, branch: str, sha: str) -> None:
        self._call("POST", "git/refs", {"ref": HEADS + branch, "sha": sha})

    def update_branch(self, branch: str, sha: str) -> None:
        self._call("PATCH", "git/refs/heads/" + branch, {"sha": sha, "force": False})

    def commit(self, message: str, tree: str, parents: list[str]) -> str:
        data = self._call("POST", "git/commits", {"message": message, "tree": tree, "parents": parents})
        sha = data.get("sha") if isinstance(data, dict) else None
        if not _sha(sha):
            raise ApiError(None, "commit created without a sha")
        return sha

    def open_pull(self, head: str, base: str, title: str, body: str = "") -> int:
        data = self._call("POST", "pulls", {"title": title, "head": head, "base": base, "body": body})
        pull = self.guard.pulls.get(data["number"])
        if pull is None or pull["base"] != base or pull["head"] != head:
            raise ApiError(None, "pull created for another base or head")
        return pull["number"]

    def check(self, head_sha: str, name: str, conclusion: str, summary: str = "") -> None:
        self._call("POST", "check-runs", {"name": name, "head_sha": head_sha, "status": "completed",
                                          "conclusion": conclusion,
                                          "output": {"title": name, "summary": summary}})

    def merge(self, number: int, head_sha: str) -> str:
        """Merge pull ``number`` at ``head_sha``; return the merge commit, verified as the base's new head."""
        self._call("GET", "pulls/%d" % number)
        data = self._call("PUT", "pulls/%d/merge" % number, {"sha": head_sha, "merge_method": "merge"})
        sha = data.get("sha") if isinstance(data, dict) else None
        if not isinstance(data, dict) or data.get("merged") is not True or not _sha(sha):
            raise ApiError(None, "merge response without merged true and a sha")
        base = self.guard.pulls[number]["base"]
        if self.head(base) != sha:
            raise ApiError(None, "merge %s is not the head of %s" % (sha, base))
        return sha

    def revert(self, branch: str, merge: str, revert_branch: str, title: str) -> dict:
        """Revert ``merge``, the head of ``branch``, through a pull request from ``revert_branch``."""
        head = self.head(branch)
        commits: dict = {}
        if merge == head:
            commits[merge] = self.read_commit(merge)
            parents = commits[merge]["parents"]
            if len(parents) == 2:
                commits[parents[0]] = self.read_commit(parents[0])
        reasons, spec = revert_commit(commits, head, merge)
        if reasons:
            raise Refused(reasons)
        sha = self.commit(title, spec["tree"], spec["parents"])
        self.create_branch(revert_branch, sha)
        number = self.open_pull(revert_branch, branch, title)
        return {"commit": sha, "tree": spec["tree"], "pull": number}


# ---------------------------------------------------------------- transport

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib's signature
        return None


class HttpTransport:
    """GitHub REST over HTTPS with a token; no redirect is followed."""

    def __init__(self, token: str, handlers: tuple = (), timeout: float = 30.0):
        if not isinstance(token, str) or not token or any(c in token for c in "\r\n"):
            raise Unusable("token must be one non-empty line")
        self.token = token
        self.timeout = timeout
        self.opener = urllib.request.build_opener(_NoRedirect, *handlers)

    def __call__(self, method: str, path: str, body: Any) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(API + path, data=data, method=method)
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                status, raw = resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            raise ApiError(exc.code, "%s %s" % (method, path)) from None
        try:
            return status, (json.loads(raw) if raw else None)
        except ValueError:
            raise ApiError(status, "response is not JSON") from None


# ---------------------------------------------------------------- command line

def guard_plan(plan: Any) -> dict:
    if not isinstance(plan, dict) or not isinstance(plan.get("requests"), list):
        raise Unusable("PLAN must be {repo, pulls?, requests: []}")
    pulls = {}
    for key, pull in (plan.get("pulls") or {}).items():
        if not re.fullmatch(_N, str(key)) or not isinstance(pull, dict):
            raise Unusable("pulls must map a number to {base, head, head_sha, state}")
        pulls[int(key)] = pull
    guard = Guard(plan.get("repo"), pulls)
    reasons: list[str] = []
    refs: set[str] = set()
    for i, req in enumerate(plan["requests"]):
        if not isinstance(req, dict) or not set(req) <= {"method", "path", "body"}:
            raise Unusable("request %d must be {method, path, body?}" % i)
        why, wrote = guard.check(req.get("method"), req.get("path"), req.get("body"))
        reasons += ["%d:%s" % (i, r) for r in why]
        refs.update(wrote)
    return {"ok": not reasons, "reasons": reasons, "refs": sorted(refs)}


def revert_state(state: Any) -> dict:
    if not isinstance(state, dict) or not isinstance(state.get("commits"), dict) \
            or not _sha(state.get("head")) or not _sha(state.get("merge")):
        raise Unusable("STATE must be {head, merge, commits: {sha: {tree, parents}}}")
    reasons, spec = revert_commit(state["commits"], state["head"], state["merge"])
    return {"ok": not reasons, "reasons": reasons, "commit": spec}


USAGE = "usage: python -m target.write guard PLAN | revert STATE"


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2 or argv[0] not in ("guard", "revert"):
            raise Unusable(USAGE)
        with open(argv[1], encoding="utf-8") as fh:
            doc = json.load(fh)
        result = guard_plan(doc) if argv[0] == "guard" else revert_state(doc)
        _emit(result)
        return 0 if result["ok"] else 1
    except (Unusable, ValueError, OSError, RecursionError) as exc:
        _emit({"ok": False, "error": "unusable input: %s" % exc})
        return 2
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a reason
        _emit({"ok": False, "error": "internal error: %s: %s" % (type(exc).__name__, exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
