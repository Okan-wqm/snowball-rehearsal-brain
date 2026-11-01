"""D1 (asama-0/01), MF17's cek: ``loop.accepted``, the bootstrap referee's signed state and the import it must match.

- ``choose``: the newest unexpired ``bootstrap-state`` of a run of the repository's own ``main`` (tohum/29b "Durum"),
  whatever the listing's order; every other artifact is passed over; a malformed entry stops the read;
- ``unpack``: exactly the two files; ``verify_argv``: 29b's ``sigstore verify identity`` command, byte for byte;
- ``open_state``: the verifier sees the two files' bytes and runs before anything is parsed; ``state_unverified``,
  ``state_invalid``; ``run_verifier`` with a real program (its exit code; 127 when it cannot start);
- ``list_artifacts`` over pages, ``read_state`` end to end with a fake API; ``ActionsHttp``: the token goes to the API
  only, never to the location a 302 names, and nothing is followed by urllib;
- ``last_import``: a chained ``setup/imports.jsonl`` (tohum/26c), broken, empty, invalid; ``check_tree``: equal,
  different, refused.
"""

from __future__ import annotations

import io
import json
import os
import stat
import sys
import tempfile
import unittest
import zipfile

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ledger import chain as C  # noqa: E402
from loop import accepted as A  # noqa: E402
from loop import treehash as T  # noqa: E402
import git_store as S  # noqa: E402
from test_write import _FakeHttps  # noqa: E402

REPO = "snowball-org/referee"
SHA = "a" * 40


def artifact(id_, created, name="bootstrap-state", expired=False, branch="main", repo_id=7, head_repo_id=7) -> dict:
    return {"id": id_, "name": name, "expired": expired, "created_at": created,
            "workflow_run": {"id": 1, "repository_id": repo_id, "head_repository_id": head_repo_id,
                             "head_branch": branch, "head_sha": "b" * 40}}


def zip_of(files: dict[str, bytes], dirs=()) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for d in dirs:
            zf.writestr(zipfile.ZipInfo(d), b"")
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def result(sha=SHA, **extra) -> bytes:
    return json.dumps({"verdict": "accepted", "state": dict({"last_accepted_sha": sha}, **extra)}).encode()


GOOD_ZIP = {"result.json": result(), "result.json.sigstore.json": b'{"bundle": 1}'}


def chained(rows: list[dict]) -> bytes:
    prev, out = C.ZERO_HASH, []
    for row in rows:
        row = dict(row, prev_hash=prev)
        row["row_hash"] = C.row_hash(row)
        prev = row["row_hash"]
        out.append(json.dumps(row))
    return ("\n".join(out) + "\n").encode() if out else b""


def import_row(tree: str, brain_sha: str = SHA) -> dict:
    return {"ts": "2026-11-01T00:00:00Z", "stage": 0, "brain_sha": brain_sha, "referee_tree_sha256": tree,
            "result_sha256": "c" * 64}


class Choose(unittest.TestCase):
    def test_the_newest_whatever_the_order(self):
        items = [artifact(1, "2026-11-01T01:00:00Z"), artifact(3, "2026-11-01T03:00:00Z"),
                 artifact(2, "2026-11-01T02:00:00Z")]
        for order in (items, list(reversed(items)), items[1:] + items[:1]):
            self.assertEqual(A.choose(order)["id"], 3)

    def test_a_tie_takes_the_larger_id(self):
        tie = [artifact(9, "2026-11-01T01:00:00Z"), artifact(4, "2026-11-01T01:00:00Z")]
        self.assertEqual(A.choose(tie)["id"], 9)
        self.assertEqual(A.choose(list(reversed(tie)))["id"], 9)

    def test_others_are_passed_over(self):
        newer = "2026-11-02T00:00:00Z"
        base = artifact(1, "2026-11-01T00:00:00Z")
        for other in (artifact(2, newer, expired=True), artifact(2, newer, name="bootstrap-state-x"),
                      artifact(2, newer, name="Bootstrap-State"), artifact(2, newer, branch="dev"),
                      artifact(2, newer, branch=None), artifact(2, newer, head_repo_id=8)):
            with self.subTest(other=other):
                self.assertEqual(A.choose([base, other])["id"], 1)
                with self.assertRaises(A.StateError) as ctx:
                    A.choose([other])
                self.assertEqual(ctx.exception.reasons, ["state_absent"])

    def test_none(self):
        with self.assertRaises(A.StateError) as ctx:
            A.choose([])
        self.assertEqual(ctx.exception.reasons, ["state_absent"])

    def test_a_malformed_entry_stops_the_read(self):
        good = artifact(1, "2026-11-01T00:00:00Z")
        bad = []
        for key, value in (("id", "1"), ("id", True), ("expired", "false"), ("created_at", "2026-11-01 00:00:00"),
                           ("created_at", "2026-11-01T00:00:00.123Z"), ("name", None), ("workflow_run", None)):
            bad.append(dict(good, **{key: value}))
        bad.append(dict(good, workflow_run={"head_branch": "main", "repository_id": 7}))
        bad.append("x")
        for entry in bad:
            with self.subTest(entry=entry):
                with self.assertRaises(A.StateError) as ctx:
                    A.choose([good, entry])
                self.assertEqual(ctx.exception.reasons, ["actions_unreadable"])
        with self.assertRaises(A.StateError):
            A.choose({"artifacts": []})


class Unpack(unittest.TestCase):
    def refused(self, data: bytes) -> None:
        with self.assertRaises(A.StateError) as ctx:
            A.unpack(data)
        self.assertEqual(ctx.exception.reasons, ["state_unreadable"])

    def test_the_two_files(self):
        self.assertEqual(A.unpack(zip_of(GOOD_ZIP)), (GOOD_ZIP["result.json"], b'{"bundle": 1}'))

    def test_anything_else(self):
        self.refused(zip_of({"result.json": b"{}"}))
        self.refused(zip_of(dict(GOOD_ZIP, **{"extra.txt": b""})))
        self.refused(zip_of(dict(GOOD_ZIP), dirs=("d/",)))
        self.refused(zip_of({"x/result.json": b"{}", "result.json.sigstore.json": b"{}"}))
        self.refused(b"not a zip")
        self.refused(b"")

    def test_a_file_over_the_limit(self):
        saved = A.MAX_FILE
        A.MAX_FILE = 10
        try:
            self.refused(zip_of({"result.json": b"x" * 11, "result.json.sigstore.json": b"{}"}))
            self.assertEqual(A.unpack(zip_of({"result.json": b"x" * 10, "result.json.sigstore.json": b"{}"}))[0],
                             b"x" * 10)
        finally:
            A.MAX_FILE = saved


class Verify(unittest.TestCase):
    def test_the_command(self):
        self.assertEqual(A.verify_argv("sigstore", REPO, "/d"), [
            "sigstore", "verify", "identity", "--bundle", "/d/result.json.sigstore.json",
            "--cert-identity", "https://github.com/snowball-org/referee/.github/workflows/bootstrap.yml@refs/heads/main",
            "--cert-oidc-issuer", "https://token.actions.githubusercontent.com", "/d/result.json"])

    def test_an_unsafe_repository_name(self):
        for repo in ("", "a", "a/b/c", "a/..", "-a/b", "a b/c", "a/b?x", "a/b\n", None, "https://github.com/a/b"):
            with self.subTest(repo=repo):
                with self.assertRaises(A.StateError) as ctx:
                    A.verify_argv("sigstore", repo, "/d")
                self.assertEqual(ctx.exception.reasons, ["repo_unsafe"])
                with self.assertRaises(A.StateError):
                    A.repo_url(repo)
        self.assertEqual(A.repo_url("o/brain.x"), "https://github.com/o/brain.x")

    def test_the_verifier_sees_both_files_first(self):
        seen = []

        def verifier(argv):
            files = {}
            for path in (argv[4], argv[-1]):
                with open(path, "rb") as fh:
                    files[os.path.basename(path)] = fh.read()
            seen.append((argv, files))
            return 0

        out = A.open_state(GOOD_ZIP["result.json"], b"B", REPO, "sg", verifier)
        self.assertEqual(out["last_accepted_sha"], SHA)
        self.assertEqual(len(out["result_sha256"]), 64)
        argv, files = seen[0]
        self.assertEqual(argv[:3], ["sg", "verify", "identity"])
        self.assertEqual(files, {"result.json": GOOD_ZIP["result.json"], "result.json.sigstore.json": b"B"})
        self.assertFalse(os.path.exists(os.path.dirname(argv[-1])))  # the directory is removed after

    def test_an_unverified_result_is_not_parsed(self):
        for body in (result(), b"not json"):
            with self.assertRaises(A.StateError) as ctx:
                A.open_state(body, b"B", REPO, verifier=lambda argv: 1)
            self.assertEqual(ctx.exception.reasons, ["state_unverified"])

    def test_an_invalid_result(self):
        for body in (b"not json", b"\xff", b"[]", b'{"state": 1}', b'{"state": {}}', result(sha=SHA.upper()),
                     result(sha="a" * 39), result(sha=None), json.dumps({"last_accepted_sha": SHA}).encode()):
            with self.subTest(body=body):
                with self.assertRaises(A.StateError) as ctx:
                    A.open_state(body, b"B", REPO, verifier=lambda argv: 0)
                self.assertEqual(ctx.exception.reasons, ["state_invalid"])

    def test_the_default_verifier_runs_a_program(self):
        with tempfile.TemporaryDirectory() as tmp:
            prog = os.path.join(tmp, "sigstore")
            with open(prog, "w") as fh:
                fh.write("#!%s\nimport sys\nsys.exit(0 if sys.argv[1:4] == ['verify', 'identity', '--bundle'] else 3)\n"
                         % sys.executable)
            os.chmod(prog, os.stat(prog).st_mode | stat.S_IXUSR)
            self.assertEqual(A.open_state(result(), b"B", REPO, prog)["last_accepted_sha"], SHA)
            self.assertEqual(A.run_verifier([prog, "other"]), 3)
            self.assertEqual(A.run_verifier([os.path.join(tmp, "absent")]), 127)
            with self.assertRaises(A.StateError) as ctx:
                A.open_state(result(), b"B", REPO, os.path.join(tmp, "absent"))
            self.assertEqual(ctx.exception.reasons, ["state_unverified"])


class FakeApi:
    """``json``/``redirect``/``blob`` over pages of artifacts and one zip, recording every call."""

    def __init__(self, artifacts: list, zip_bytes: bytes, per_page: int = 2, total=None):
        self.artifacts, self.zip, self.per_page = artifacts, zip_bytes, per_page
        self.total = len(artifacts) if total is None else total
        self.calls: list = []

    def json(self, path):
        self.calls.append(("json", path))
        page = int(path.rsplit("page=", 1)[1])
        chunk = self.artifacts[(page - 1) * self.per_page:page * self.per_page]
        return {"total_count": self.total, "artifacts": chunk}

    def redirect(self, path):
        self.calls.append(("redirect", path))
        return "https://blob.example/zip"

    def blob(self, url, limit):
        self.calls.append(("blob", url))
        return self.zip


class ReadState(unittest.TestCase):
    def test_every_page_then_the_newest(self):
        arts = [artifact(i, "2026-11-01T0%d:00:00Z" % i) for i in range(1, 6)]
        api = FakeApi(arts, zip_of(GOOD_ZIP))
        out = A.read_state(api, REPO, verifier=lambda argv: 0)
        self.assertEqual(out["artifact_id"], 5)
        self.assertEqual(out["last_accepted_sha"], SHA)
        self.assertEqual([c[0] for c in api.calls], ["json", "json", "json", "redirect", "blob"])
        self.assertTrue(api.calls[0][1].startswith(
            "/repos/snowball-org/referee/actions/artifacts?name=bootstrap-state&per_page=100&page=1"))
        self.assertEqual(api.calls[3][1], "/repos/snowball-org/referee/actions/artifacts/5/zip")

    def test_a_short_listing_or_a_bad_page(self):
        for api in (FakeApi([artifact(1, "2026-11-01T00:00:00Z")], b"", total=3),):
            with self.assertRaises(A.StateError) as ctx:
                A.read_state(api, REPO, verifier=lambda argv: 0)
            self.assertEqual(ctx.exception.reasons, ["actions_unreadable"])

        class Bad(FakeApi):
            def json(self, path):
                return {"artifacts": []}
        with self.assertRaises(A.StateError) as ctx:
            A.read_state(Bad([], b""), REPO, verifier=lambda argv: 0)
        self.assertEqual(ctx.exception.reasons, ["actions_unreadable"])

    def test_too_many_pages(self):
        class Endless(FakeApi):
            def json(self, path):
                return {"total_count": 10 ** 6, "artifacts": [artifact(1, "2026-11-01T00:00:00Z")]}
        with self.assertRaises(A.StateError) as ctx:
            A.list_artifacts(Endless([], b""), REPO)
        self.assertEqual(ctx.exception.reasons, ["actions_unreadable"])

    def test_unverified_stops(self):
        api = FakeApi([artifact(1, "2026-11-01T00:00:00Z")], zip_of(GOOD_ZIP))
        with self.assertRaises(A.StateError) as ctx:
            A.read_state(api, REPO, verifier=lambda argv: 1)
        self.assertEqual(ctx.exception.reasons, ["state_unverified"])


class Http(unittest.TestCase):
    def test_the_token_goes_to_the_api_only(self):
        listing = json.dumps({"total_count": 1, "artifacts": [artifact(4, "2026-11-01T00:00:00Z")]}).encode()
        fake = _FakeHttps([(200, listing, {}), (302, b"", {"Location": "https://blob.example/z?sig=1"}),
                           (200, zip_of(GOOD_ZIP), {})])
        out = A.read_state(A.ActionsHttp("tok", handlers=(fake,)), REPO, verifier=lambda argv: 0)
        self.assertEqual(out["artifact_id"], 4)
        urls = [r.full_url for r in fake.seen]
        self.assertEqual(urls[1], "https://api.github.com/repos/snowball-org/referee/actions/artifacts/4/zip")
        self.assertEqual(urls[2], "https://blob.example/z?sig=1")
        self.assertEqual([r.get_header("Authorization") for r in fake.seen], ["Bearer tok", "Bearer tok", None])

    def test_nothing_is_followed(self):
        # a redirect of the listing is not followed (one request), a redirect to plain http is refused
        fake = _FakeHttps([(302, b"", {"Location": "https://elsewhere.example/x"}), (200, b"{}", {})])
        with self.assertRaises(A.StateError) as ctx:
            A.ActionsHttp("tok", handlers=(fake,)).json("/x")
        self.assertEqual((ctx.exception.reasons, len(fake.seen)), (["actions_unreadable"], 1))
        fake = _FakeHttps([(302, b"", {"Location": "http://blob.example/z"})])
        with self.assertRaises(A.StateError):
            A.ActionsHttp("tok", handlers=(fake,)).redirect("/zip")
        fake = _FakeHttps([(200, b"zip", {})])
        with self.assertRaises(A.StateError):  # an answer that is not a redirect has no location
            A.ActionsHttp("tok", handlers=(fake,)).redirect("/zip")
        class Both(_FakeHttps):
            http_open = _FakeHttps.https_open
        fake = Both([(200, b"zip", {})])
        with self.assertRaises(A.StateError):  # a plain http location is not requested at all
            A.ActionsHttp("tok", handlers=(fake,)).blob("http://blob.example/z", 10)
        self.assertEqual(fake.seen, [])

    def test_a_blob_over_the_limit(self):
        fake = _FakeHttps([(200, b"x" * 11, {})])
        with self.assertRaises(A.StateError) as ctx:
            A.ActionsHttp("tok", handlers=(fake,)).blob("https://b.example/z", 10)
        self.assertEqual(ctx.exception.reasons, ["state_unreadable"])

    def test_a_token_that_is_not_one_line(self):
        for token in ("", "a\nb", None):
            with self.assertRaises(A.StateError):
                A.ActionsHttp(token)


class Imports(unittest.TestCase):
    def test_the_last_transfer_row(self):
        data = chained([import_row("1" * 64), import_row("2" * 64)])
        row, line = A.last_import(data)
        self.assertEqual(row["referee_tree_sha256"], "2" * 64)
        self.assertEqual(line, data.split(b"\n")[1])

    def test_a_touch_that_is_no_transfer_is_skipped(self):
        # tohum/29n: every row is a touch; 29o: the import is the last row carrying referee_tree_sha256
        data = chained([import_row("1" * 64), import_row("2" * 64), {"ts": "2026-11-01T01:00:00Z", "stage": 0}])
        row, line = A.last_import(data)
        self.assertEqual(row["referee_tree_sha256"], "2" * 64)
        self.assertEqual(line, data.split(b"\n")[1])

    def refused(self, data: bytes, reason: str) -> None:
        with self.assertRaises(A.StateError) as ctx:
            A.last_import(data)
        self.assertEqual(ctx.exception.reasons, [reason])

    def test_broken_none_invalid(self):
        good = chained([import_row("1" * 64), import_row("2" * 64)])
        self.refused(good.replace(b"1" * 64, b"3" * 64, 1), "imports_broken")
        lines = good.split(b"\n")
        self.refused(lines[1] + b"\n", "imports_broken")          # the first row gone
        self.refused(b"[1]\n", "imports_broken")                 # a row that is not an object
        self.refused(b"", "imports_no_transfer")
        self.refused(chained([{"ts": "x"}]), "imports_no_transfer")
        self.refused(chained([import_row("A" * 64)]), "imports_invalid")
        self.refused(chained([import_row("1" * 64), import_row(None)]), "imports_invalid")


class CheckTree(unittest.TestCase):
    def setUp(self):
        self.objects, self.commit = S.store({"referee/a.py": b"x", "README": b"y"})
        self.hash = T.digest([("referee/a.py", "file", b"x")])

    def test_equal(self):
        self.assertEqual(A.check_tree(self.objects.__getitem__, self.commit, import_row(self.hash)), self.hash)

    def test_different(self):
        with self.assertRaises(A.StateError) as ctx:
            A.check_tree(self.objects.__getitem__, self.commit, import_row("0" * 64))
        self.assertEqual(ctx.exception.reasons, ["referee_tree_mismatch"])

    def test_refused(self):
        objects, commit = S.store({"referee/a.py": b"x", "referee/setup": b"y"})
        with self.assertRaises(A.StateError) as ctx:
            A.check_tree(objects.__getitem__, commit, import_row(self.hash))
        self.assertEqual(ctx.exception.reasons, ["referee_tree_refused", "operator_name:setup"])
        with self.assertRaises(A.StateError) as ctx:
            A.check_tree({}.__getitem__, commit, import_row(self.hash))
        self.assertEqual(ctx.exception.reasons, ["referee_tree_refused", "brain:object_missing:%s" % commit])


if __name__ == "__main__":
    unittest.main()
