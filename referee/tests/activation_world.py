"""A toy target for activation tests (tests 45 and 14): the in-process GitHub with ``main`` and the facts genesis
reads (tohum/29o: the writer App, its installation, the three branches' rules and their rulesets, the toy's
workflows or the copy's Actions permission, answered as ``overrides``), the operator files, the referee's base run
and five ready candidates, the good one and asama-0/08's four bad ones (outside the fix
range, a ratchet increase, a broken test, a forbidden path). Every input is written here by hand; hashes the
tests expect are computed from these bytes, not by ``activate``.
"""

from __future__ import annotations

import hashlib
import json

from fake_github import FakeGitHub
from ledger import anchor, chain

REPO = "acme/toy"
GATE = "snowball/gate"
CYCLE = "41000000001"
TS = "2026-10-30T12:00:00Z"
SNAP = "s-activation"

SOURCE = b"// toy\nvar x = 1;\nvar y = 2;\nmodule.exports = { x, y };\n"
TEST = b"const t = require('node:test');\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def chained(rows: list[dict]) -> bytes:
    out, prev = [], chain.ZERO_HASH
    for row in rows:
        row = dict(row, prev_hash=prev)
        row["row_hash"] = prev = chain.row_hash(row)
        out.append(chain.canonical(row) + b"\n")
    return b"".join(out)


def run_file(record: dict, lines: int = 3) -> bytes:
    line = json.dumps(record, sort_keys=True).encode("utf-8") + b"\n"
    return line * lines


def violation(line: int, rule: str = "no-var", path: str = "src/a.js", fix=None) -> dict:
    return {"rule_id": rule, "path": path, "line": line, "fix": [line, line] if fix is None else fix}


BASE_RUN = run_file({"tool": "eslint", "violations": [violation(2), violation(3)]})
CHECKS_GREEN = json.dumps({"tests": [{"id": "test/a.test.js", "status": "pass"}], "red_control": "fail"}).encode()
CHECKS_RED = json.dumps({"tests": [{"id": "test/a.test.js", "status": "fail"}], "red_control": "fail"}).encode()


def diff(path: str, old_start: int, removed: list[str], added: list[str]) -> bytes:
    head = "diff --git a/%s b/%s\nindex 1111111..2222222 100644\n--- a/%s\n+++ b/%s\n" % (path, path, path, path)
    hunk = "@@ -%d,%d +%d,%d @@\n" % (old_start, len(removed), old_start, len(added))
    body = "".join("-%s\n" % r for r in removed) + "".join("+%s\n" % a for a in added)
    return (head + hunk + body).encode("utf-8")


def candidate(cid: str, patch: bytes, cand_run: bytes, checks: bytes, line: int = 2, path: str = "src/a.js") -> dict:
    files = {"finding.json": json.dumps({"rule_id": "no-var", "path": path, "line": line, "fix_range": [line, line],
                                         "tool_output_sha256": sha(BASE_RUN)}).encode(),
             "diff.patch": patch, "cand.jsonl": cand_run, "checks.json": checks}
    files["hashes.json"] = json.dumps({"base.jsonl": sha(BASE_RUN), "cand.jsonl": sha(cand_run),
                                       "checks.json": sha(checks)}).encode()
    return dict(files, id=cid)


def candidates() -> list[dict]:
    fixed = run_file({"tool": "eslint", "violations": [violation(3)]})
    return [
        # good: line 2 fixed inside its fix range, nothing else changes
        candidate("good", diff("src/a.js", 2, ["var x = 1;"], ["let x = 1;"]), fixed, CHECKS_GREEN),
        # outside the fix range: changes line 3 as well (scope_violation)
        candidate("bad-scope", diff("src/a.js", 2, ["var x = 1;", "var y = 2;"], ["let x = 1;", "let y = 2;"]),
                  run_file({"tool": "eslint", "violations": []}), CHECKS_GREEN),
        # ratchet: fixes line 2 but its tree has one more violation of the tool
        candidate("bad-ratchet", diff("src/a.js", 2, ["var x = 1;"], ["let x = 1;"]),
                  run_file({"tool": "eslint", "violations": [violation(3), violation(4, "eqeqeq"),
                                                             violation(4, "no-undef")]}), CHECKS_GREEN),
        # a broken test
        candidate("bad-test", diff("src/a.js", 2, ["var x = 1;"], ["let x = 1;"]), fixed, CHECKS_RED),
        # a forbidden path: the lint configuration
        candidate("bad-path", diff("eslint.config.js", 1, ["module.exports = [];"], ["module.exports = [{}];"]),
                  fixed, CHECKS_GREEN),
    ]


EXPECTED_REJECTS = {
    "bad-scope": ("scope_violation", "scope_violation"),
    "bad-ratchet": ("ratchet_increase", "lint_regression"),
    "bad-test": ("tests_red", "test_regression"),
    "bad-path": ("config:eslint.config.js", "scope_violation"),
}


APP_ID = 4242


def facts(kind: str) -> dict:
    """The GitHub answers genesis reads when every precondition holds (``{(method, path): (status, body)}``)."""
    p = "/repos/%s" % REPO
    rule = lambda kind_, ruleset, **params: dict({"type": kind_, "ruleset_id": ruleset},  # noqa: E731
                                                 **({"parameters": params} if params else {}))
    out = {
        "/app": {"id": APP_ID, "slug": "snowball-writer"},
        "/installation/repositories": {"total_count": 1, "repositories": [{"full_name": REPO}]},
        p + "/rules/branches/brain/state": [rule("deletion", 1), rule("non_fast_forward", 1)],
        p + "/rules/branches/brain/integration": [
            rule("deletion", 2), rule("non_fast_forward", 2), rule("pull_request", 2, required_approving_review_count=0),
            rule("required_status_checks", 2, strict_required_status_checks_policy=True,
                 required_status_checks=[{"context": GATE, "integration_id": APP_ID}])],
        p + "/rules/branches/main": [rule("deletion", 3), rule("pull_request", 3, required_approving_review_count=1)],
    }
    for n in (1, 2, 3):
        out[p + "/rulesets/%d" % n] = {"id": n, "current_user_can_bypass": "never"}
    if kind == "toy":
        out[p + "/actions/workflows"] = {"total_count": 0, "workflows": []}
    else:
        out[p + "/actions/permissions"] = {"enabled": False}
    return {("GET", path): (200, body) for path, body in out.items()}


class World:
    """The target and the inputs; each test may change any of them before calling ``run``."""

    def __init__(self, kind: str = "toy", create_denied=()):
        self.gh = FakeGitHub(REPO, required_check=GATE, create_denied=create_denied)
        self.main = self.gh.seed_commit("toy-main", files={
            "src/a.js": SOURCE, "test/a.test.js": TEST, "eslint.config.js": b"module.exports = [];\n",
            "package.json": b"{}\n"})
        self.gh.refs["main"] = self.main
        self.gh.overrides.update(facts(kind))
        self.imports = chained([{"ts": "2026-10-30T09:00:00Z", "stage": 0, "brain_sha": "b" * 40,
                                 "referee_tree_sha256": "e" * 64, "result_sha256": "d" * 64,
                                 "toy_tree_sha256": "f" * 64},
                                {"ts": "2026-10-30T10:00:00Z", "stage": 0}])  # a touch that is no transfer
        self.summary = json.dumps({
            "seed_epochs": [{"commit": "1" * 40, "spec_tohum_sha256": "2" * 64, "seed_sha256": "3" * 64,
                             "bootstrap_sha256": "4" * 64}],
            "targets": [{"id": "toy", "repo": REPO, "kind": kind, "base_sha": self.main, "identifiers": [],
                         "excluded_paths": [], "unit_candidates": []}]}).encode()
        self.profile = json.dumps({"security_paths": ["src/auth/"], "excluded_dirs": ["vendor/"]}).encode()
        self.recipe = json.dumps({"unit_id": "toy", "inputs": ["src/", "test/", "eslint.config.js",
                                                               "package.json"]}).encode()
        self.security = chained([{"row_id": "sec-1", "part": "security", "kind": "note", "payload": {}}])
        self.files = {"summary.json": self.summary, "imports.jsonl": self.imports, "policy.json": b'{"p": 1}\n',
                      "security-ledger.jsonl": self.security, "profile.json": self.profile,
                      "recipe.json": self.recipe, "base.jsonl": BASE_RUN}
        self.candidates = candidates()
        self.signer = anchor.FakeSigner(True, "referee@example", "rekor-1")
        self.control = {"kill_switch": False, "merge_paused": False}
        self.canary_cap = 220000000

    def request(self) -> dict:
        return {"target_id": "toy", "base_run_sha256": sha(self.files["base.jsonl"]), "cycle_id": CYCLE, "ts": TS,
                "snapshot_id": SNAP, "candidates": sorted(c["id"] for c in self.candidates)}

    def read_base(self, path: str) -> bytes | None:
        """The file in the tree pulled at the base commit (D1's checkout), not at ``main``'s head."""
        blob = self.gh.trees[self.gh.commits[self.main]["tree"]].get(path)
        return None if blob is None else self.gh.blobs[blob]

    def cand(self, cid: str) -> dict:
        return next(c for c in self.candidates if c["id"] == cid)

    def writer(self):
        from target import write
        return write.Writer(REPO, self.gh)

    def run(self, req: dict | None = None):
        import activate
        self.wr = self.writer()
        return activate.activate(self.wr, self.files, self.request() if req is None else req, self.candidates,
                                 self.read_base, self.signer, self.control, GATE, self.canary_cap)

    def writes(self) -> list[tuple]:
        return [(m, p) for m, p, _ in self.gh.requests if m != "GET"]
