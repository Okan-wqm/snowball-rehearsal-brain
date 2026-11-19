"""The copy target's ready candidates (``candidates/copy/<cid>/``) against what the loop published for the copy
and against the referee's own gate rules that read only the candidate and the base (asama-0/08 cycle order row 7,
25a row 8, tohum/26c's ready candidate).

What is proven here, for every candidate directory:

- its files are tohum/26c's three, ``finding.json`` with exactly 26c's fields and ``expect.json`` one of the
  shapes this stage uses (``good``: ``{decision: merge}``; ``bad-test``: ``{decision: reject, reason:
  tests_red}``);
- ``finding.json`` is, field for field, one ``fixable`` entry of the ``events/observation`` row the copy's
  genesis published (``tests/fixtures/copy-candidates/state-ledger.jsonl``: the copy's ``brain/state``
  ``.brain/ledger.jsonl`` at 6e1f04a3, cycle 44421577691-1, its hash chain verified by ``ledger.chain``), and its
  ``tool_output_sha256`` is that row's ``base_run_sha256``, which is also the ``ratchet_base`` row's;
- ``diff.patch`` parses (``gate.diffguard.parse``), changes only the finding's path in place, has no criterion 1
  path reason (``gate.diffguard.check`` with the guard profile ``profile.unit_verify.guard_profile`` derives, with
  the seed's keyword list, for a tree holding the unit's ``src`` file names; the copy's live policy names the
  same kind of list) and no ``scope_violation`` for the published ``fix_range`` (``gate.check``), no secret
  (``gate.secrets`` in its ``diff`` meaning), and applies (``gate.diffguard.apply``) to the base file
  (``tests/fixtures/copy-candidates/outbox-notify-listener.service.ts``, the base's blob, git object
  34d1f33a0cb5..., the ``index`` line of each patch);
- the good candidate's patched file is the base with exactly the type assertion of the target line removed (the
  rule's fix: the text from the end of the asserted expression to the end of the assertion), and no other byte;
- the bad candidate's change is confined to its target line and removes that line's assertion, so its rule
  cannot report the same assertion there (the gate's ``not_distinguished``).

Not proven here, and why: that ``koş``'s contained runs give the decisions of ``expect.json`` (the gate's
``tests_red``, ``ratchet_increase``, ``not_distinguished`` and ``zero_tests`` read ``koş``'s results, and the
copy's lint configuration and tests are the target's code, which runs only in ``koş``, asama-0/08); the bad
candidate's ``tests_red`` rests on ts-jest's type check (the recipe's ``test_cmd``, ts-jest 29.4.6 with no
``isolatedModules``) reporting the type error of the module ``outbox.module`` imports, which asama-0/10a #ret
measures.

Run from the brain root: ``python -m unittest discover -s tests -p 'test_copy_candidates.py'``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from gate import check as C  # noqa: E402
from gate import diffguard  # noqa: E402
from gate import secrets  # noqa: E402
from ledger import chain  # noqa: E402
from profile import unit_verify as V  # noqa: E402

CANDIDATES = os.path.join(ROOT, "candidates", "copy")
FIXTURES = os.path.join(ROOT, "tests", "fixtures", "copy-candidates")
STATE_LEDGER = os.path.join(FIXTURES, "state-ledger.jsonl")
BASE_PATH = "platform/libs/outbox/src/outbox-notify-listener.service.ts"
BASE_FILE = os.path.join(FIXTURES, "outbox-notify-listener.service.ts")
BASE_BLOB = "34d1f33a0cb561ef9f6a0df1d0a2e309baa1fe38"
# the names of the unit's src directory at the base (4f479013a42f), for the guard profile's keyword rule
UNIT_SRC = ["constants.ts", "index.ts", "outbox-entity.base.ts", "outbox-metrics.service.ts", "outbox-migration.ts",
            "outbox-notify-listener.service.ts", "outbox-publisher.service.ts", "outbox-routing.ts",
            "outbox-worker.service.ts", "outbox.module.ts", "tenant-integrity.ts"]
FILES = {"finding.json", "diff.patch", "expect.json"}
FINDING_FIELDS = {"rule_id", "path", "line", "fix_range", "tool_output_sha256"}
EXPECT = {"good": {"decision": "merge"}, "bad-test": {"decision": "reject", "reason": "tests_red"}}


def raw(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def load(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def published() -> dict:
    """The observation and ratchet_base rows of the copy's published state ledger, its chain verified."""
    data = raw(STATE_LEDGER)
    verdict = chain.verify_bytes(data)
    if not verdict["valid"]:
        raise AssertionError("state ledger chain: %r" % verdict)
    rows = [json.loads(line) for line in data.decode("utf-8").splitlines()]
    by_kind = {}
    for row in rows:
        by_kind.setdefault(row["kind"], []).append(row)
    return {kind: by_kind[kind] for kind in ("observation", "ratchet_base", "genesis")}


def guard_profile() -> dict:
    tree = tempfile.mkdtemp()
    try:
        src = os.path.join(tree, os.path.dirname(BASE_PATH))
        os.makedirs(src)
        for name in UNIT_SRC:
            with open(os.path.join(src, name), "w", encoding="utf-8") as fh:
                fh.write("\n")
        return V.guard_profile(tree, {"id": "copy", "kind": "copy"}, None)
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def recipe() -> dict:
    return load(os.path.join(ROOT, "targets", "copy", "units.json"))["units"][0]


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def candidate(cid: str) -> dict:
    d = os.path.join(CANDIDATES, cid)
    return {"finding": load(os.path.join(d, "finding.json")), "expect": load(os.path.join(d, "expect.json")),
            "diff": raw(os.path.join(d, "diff.patch")).decode("utf-8")}


def judge(finding: dict, diff_text: str, fixable: list, base_run_sha256: str, profile: dict, unit: dict,
          base: bytes) -> list[str]:
    """Every rule of the module docstring that a candidate breaks, by name (empty: none)."""
    broken = []
    if set(finding) != FINDING_FIELDS:
        broken.append("finding_fields")
    if {k: finding.get(k) for k in ("rule_id", "path", "line", "fix_range")} not in fixable:
        broken.append("not_published")
    if finding.get("tool_output_sha256") != base_run_sha256:
        broken.append("tool_output_sha256")
    blocks = diffguard.parse(diff_text)
    if diffguard.check(diff_text, profile, unit):
        broken.append("guard")
    if C.scope_violation(blocks, finding["path"], finding["fix_range"]):
        broken.append("scope_violation")
    if secrets.scan(diff_text, "diff"):
        broken.append("secret")
    if len(blocks) != 1 or blocks[0]["old"] != BASE_PATH:
        broken.append("not_the_base_file")
    else:
        try:
            diffguard.apply(blocks[0], base)
        except diffguard.DiffError:
            broken.append("does_not_apply")
    return broken


def patched(diff_text: str, base: bytes) -> bytes:
    return diffguard.apply(diffguard.parse(diff_text)[0], base)


class Fixtures(unittest.TestCase):
    def test_base_file_is_the_patches_blob(self):
        base = raw(BASE_FILE)
        self.assertEqual(git_blob(base), BASE_BLOB)
        for cid in sorted(os.listdir(CANDIDATES)):
            self.assertIn("index %s.." % BASE_BLOB[:7], candidate(cid)["diff"])

    def test_published_rows(self):
        rows = published()
        self.assertEqual(len(rows["observation"]), 1)
        obs, ratchet = rows["observation"][0]["payload"], rows["ratchet_base"][0]["payload"]
        self.assertEqual(obs["base_run_sha256"], ratchet["base_run_sha256"])
        self.assertEqual(rows["genesis"][0]["payload"]["base_sha"], "4f479013a42f4b750e0784cc2500bd17d932af1a")

    def test_a_changed_row_breaks_the_chain(self):
        data = raw(STATE_LEDGER).replace(b'"line":300', b'"line":301', 1)
        self.assertNotEqual(data, raw(STATE_LEDGER))
        self.assertFalse(chain.verify_bytes(data)["valid"])


class Candidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = published()
        cls.fixable = rows["observation"][0]["payload"]["fixable"]
        cls.base_run = rows["observation"][0]["payload"]["base_run_sha256"]
        cls.profile = guard_profile()
        cls.unit = recipe()
        cls.base = raw(BASE_FILE)

    def judge(self, finding: dict, diff_text: str) -> list[str]:
        return judge(finding, diff_text, self.fixable, self.base_run, self.profile, self.unit, self.base)

    def test_the_set_of_candidates(self):
        self.assertEqual(sorted(os.listdir(CANDIDATES)), sorted(EXPECT))
        for cid in EXPECT:
            self.assertEqual(set(os.listdir(os.path.join(CANDIDATES, cid))), FILES)
            self.assertEqual(candidate(cid)["expect"], EXPECT[cid])

    def test_each_candidate_breaks_no_rule(self):
        for cid in EXPECT:
            c = candidate(cid)
            self.assertEqual(self.judge(c["finding"], c["diff"]), [], cid)

    def test_the_guard_profile_reads_the_keywords(self):
        # the keyword rule is live here: the unit's tenant-integrity.ts is a security path, the target file is not
        self.assertIn("platform/libs/outbox/src/tenant-integrity.ts", self.profile["security_paths"])
        self.assertNotIn(BASE_PATH, self.profile["security_paths"])

    def test_good_is_the_rules_fix(self):
        c = candidate("good")
        line = c["finding"]["line"]
        base_lines = self.base.split(b"\n")
        target = base_lines[line - 1]
        self.assertIn(b" as ", target)
        fixed = target[:target.index(b" as ")] + target[target.rindex(b","):]
        expected = b"\n".join(base_lines[:line - 1] + [fixed] + base_lines[line:])
        self.assertEqual(patched(c["diff"], self.base), expected)

    def test_bad_changes_only_its_line_and_drops_the_assertion(self):
        c = candidate("bad-test")
        line = c["finding"]["line"]
        base_lines, new_lines = self.base.split(b"\n"), patched(c["diff"], self.base).split(b"\n")
        self.assertEqual(len(base_lines), len(new_lines))
        changed = [i + 1 for i, (a, b) in enumerate(zip(base_lines, new_lines)) if a != b]
        self.assertEqual(changed, [line])
        self.assertIn(b" as ", base_lines[line - 1])
        self.assertNotIn(b" as ", new_lines[line - 1])

    # ---- each rule catches its own break

    def test_a_finding_not_published_is_caught(self):
        c = candidate("good")
        for change in ({"line": 301}, {"fix_range": [299, 300]}, {"rule_id": "import/order"},
                       {"path": "platform/libs/outbox/src/outbox.module.ts"}):
            self.assertIn("not_published", self.judge(dict(c["finding"], **change), c["diff"]), change)

    def test_a_wrong_tool_output_hash_is_caught(self):
        c = candidate("good")
        self.assertEqual(self.judge(dict(c["finding"], tool_output_sha256="0" * 64), c["diff"]),
                         ["tool_output_sha256"])

    def test_a_missing_or_extra_field_is_caught(self):
        c = candidate("good")
        less = {k: v for k, v in c["finding"].items() if k != "tool_output_sha256"}
        self.assertIn("finding_fields", self.judge(less, c["diff"]))
        self.assertIn("finding_fields", self.judge(dict(c["finding"], cause="x"), c["diff"]))

    def test_a_diff_outside_the_range_is_caught(self):
        # the good finding with the bad diff: line 292 is outside [300, 300]
        good, bad = candidate("good"), candidate("bad-test")
        self.assertEqual(self.judge(good["finding"], bad["diff"]), ["scope_violation"])

    def test_a_security_path_is_caught(self):
        c = candidate("good")
        path = "platform/libs/outbox/src/tenant-integrity.ts"
        diff = c["diff"].replace(BASE_PATH, path)
        broken = self.judge(dict(c["finding"], path=path), diff)
        self.assertIn("guard", broken)

    def test_a_patch_that_does_not_apply_is_caught(self):
        c = candidate("good")
        diff = c["diff"].replace("       user: pgOptions.username,", "       user: pgOptions.user,", 1)
        self.assertNotEqual(diff, c["diff"])
        self.assertEqual(self.judge(c["finding"], diff), ["does_not_apply"])


if __name__ == "__main__":
    unittest.main()
