"""Test 46 (asama-0/09), MF17: every artifact hand-over of ``loop.yml``, each edge proven or stated.

The edges are not listed by hand: ``edges(JOBS)`` derives them from ``loop.job.JOBS`` (a job that uploads an
artifact and a job that downloads it), the one source the workflow is rendered from. ``HANDOVER`` gives each edge
exactly one status, and ``problems`` checks it against what the code does:

- ``handover`` (a test id): the named test passes, and while it runs ``loop.job.run`` is called for the producer,
  which leaves ``$RUNNER_TEMP/out/<artifact>``, and later for the consumer, which finds ``$RUNNER_TEMP/in/<artifact>``
  with the same content (``digest``: every path, its kind and its bytes or link target) and returns ``done`` steps.
  So the test runs both jobs on the artifact as the upload and download hand it over, not each on its own fixture;
- ``unread`` (a test id): the named test passes and the consumer returns ``done`` steps while
  ``in/<artifact>`` is absent, so the consumer's wired steps do not read the download (a stated gap, with its why);
- ``unwired`` (a why): the producer, run on an empty ``$RUNNER_TEMP``, stops at once with ``cycle_not_wired``, no
  ``done`` step and no ``out/<artifact>``: nothing reaches the consumer in a real run.

A register missing a derived edge, or naming one that is not derived, is a problem; so wiring a producer turns its
``unwired`` edges red until each names a hand-over test, and a new download needs a status in the same push.

Out of scope, stated: what the pinned upload and download actions do to the bytes (the copy here is
``shutil.copytree`` or a move; the actions' real transfer is asama-0/10a's live run), the digests the workflow
passes between jobs (``LOOP_<ARTIFACT>_DIGEST``, test_loop_workflow), and whether a consumer judges the artifact
correctly (each job's own tests).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import unittest
from typing import Any

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import job as J  # noqa: E402
from profile_tree import write_tree  # noqa: E402

GETIR_TO_KOS = "test_loop_getir.HandOver.test_kos_installs_what_getir_fetched"
KOS_TO_YAZ = "test_loop_yaz.YazJob.test_the_job_runs_d5_and_merges_nothing_without_the_state"

# (artifact, consumer) -> (status, test id | why)
HANDOVER: dict[tuple[str, str], tuple[str, str]] = {
    ("pulled", "getir"): ("unwired", "cek stops with cycle_not_wired: D1's reads are not written (loop.cek)"),
    ("pulled", "kos"): ("unwired", "cek stops with cycle_not_wired: D1's reads are not written (loop.cek)"),
    ("pulled", "cagir"): ("unwired", "cek stops with cycle_not_wired: D1's reads are not written (loop.cek)"),
    ("pulled", "yaz"): ("unwired", "cek stops with cycle_not_wired: D1's reads are not written (loop.cek)"),
    ("deps", "kos"): ("handover", GETIR_TO_KOS),
    ("deps", "yaz"): ("unread", KOS_TO_YAZ),  # D5 reads D3's and D4's artifacts (asama-0/01); no wired step reads deps
    ("results", "yaz"): ("handover", KOS_TO_YAZ),
    ("response", "yaz"): ("unwired", "cagir stops with cycle_not_wired: D4 is not wired (spec-036)"),
}
STATUSES = ("handover", "unread", "unwired")


def edges(jobs: dict[str, J.Job]) -> dict[tuple[str, str], str]:
    """``{(artifact, consumer): producer}`` for every download of every job."""
    producers = {job.upload: name for name, job in jobs.items() if job.upload}
    return {(artifact, name): producers[artifact] for name, job in jobs.items() for artifact in job.downloads}


def digest(path: str) -> str | None:
    """The content of a directory tree (relative paths, kinds, bytes, link targets), or ``None`` when absent."""
    if not os.path.isdir(path):
        return None
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(dirs + files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, path).encode()
            if os.path.islink(full):
                h.update(b"L%d:%s%s" % (len(rel), rel, os.readlink(full).encode()))
            elif os.path.isdir(full):
                h.update(b"D%d:%s" % (len(rel), rel))
            else:
                with open(full, "rb") as fh:
                    data = fh.read()
                h.update(b"F%d:%s%d:%s" % (len(rel), rel, len(data), data))
    return h.hexdigest()


class Call(dict):
    pass


def recorded(test_id: str, jobs: dict[str, J.Job]) -> tuple[bool, list[Call]]:
    """Run one test with ``loop.job.run`` wrapped: whether it passed, and every call that returned, in order, with
    its job, its downloads' digests before the call, its result and its upload's digest after the call."""
    calls: list[Call] = []
    real = J.run

    def run(name: str, environ: dict[str, str], *args: Any, **kwargs: Any) -> dict[str, Any]:
        temp = environ.get("RUNNER_TEMP") or ""
        job = jobs.get(name)
        seen = {a: digest(os.path.join(temp, "in", a)) for a in (job.downloads if job else ())}
        out = real(name, environ, *args, **kwargs)
        upload = digest(os.path.join(temp, "out", job.upload)) if job and job.upload else None
        calls.append(Call(job=name, seen=seen, out=out, upload=upload))
        return out

    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
    except (ImportError, AttributeError):
        return False, []
    result = unittest.TestResult()
    J.run = run
    try:
        suite.run(result)
    finally:
        J.run = real
    return result.testsRun == 1 and result.wasSuccessful() and not result.skipped, calls


def _handed_over(calls: list[Call], artifact: str, producer: str, consumer: str) -> bool:
    for i, made in enumerate(calls):
        if made["job"] != producer or made["upload"] is None:
            continue
        for took in calls[i + 1:]:
            if took["job"] == consumer and took["seen"].get(artifact) == made["upload"] and took["out"].get("done"):
                return True
    return False


def _unread(calls: list[Call], artifact: str, consumer: str) -> bool:
    return any(c["job"] == consumer and c["seen"].get(artifact, "") is None and c["out"].get("done") for c in calls)


def _stops_at_once(producer: str, jobs: dict[str, J.Job]) -> bool:
    temp = tempfile.mkdtemp(prefix="t-handover-")
    try:
        try:
            out = J.run(producer, {"RUNNER_TEMP": temp})
        except J.Unusable:
            return False
        upload = jobs[producer].upload
        return (out.get("reason") == "cycle_not_wired" and not out.get("done") and not out.get("ok")
                and not os.path.lexists(os.path.join(temp, "out", upload)))
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def problems(register: dict[tuple[str, str], tuple[str, str]], jobs: dict[str, J.Job]) -> list[str]:
    derived = edges(jobs)
    found = ["unregistered:%s->%s" % e for e in sorted(set(derived) - set(register))]
    found += ["not_an_edge:%s->%s" % e for e in sorted(set(register) - set(derived))]
    runs: dict[str, tuple[bool, list[Call]]] = {}
    for (artifact, consumer), (status, ref) in sorted(register.items()):
        if (artifact, consumer) not in derived:
            continue
        producer = derived[(artifact, consumer)]
        edge = "%s:%s->%s" % (artifact, producer, consumer)
        if status not in STATUSES or not (isinstance(ref, str) and ref):
            found.append("bad_status:%s" % edge)
        elif status == "unwired":
            if not _stops_at_once(producer, jobs):
                found.append("producer_wired:%s" % edge)
        else:
            if ref not in runs:
                runs[ref] = recorded(ref, jobs)
            passed, calls = runs[ref]
            if not passed:
                found.append("test_failed:%s:%s" % (edge, ref))
            elif status == "handover" and not _handed_over(calls, artifact, producer, consumer):
                found.append("not_handed_over:%s:%s" % (edge, ref))
            elif status == "unread" and not _unread(calls, artifact, consumer):
                found.append("not_unread:%s:%s" % (edge, ref))
    return found


class Register(unittest.TestCase):
    def test_every_edge_of_the_workflow_holds_its_status(self):
        self.assertEqual(problems(HANDOVER, J.JOBS), [])

    def test_the_edges_are_the_workflows_downloads(self):
        self.assertEqual(edges(J.JOBS), {
            ("pulled", "getir"): "cek", ("pulled", "kos"): "cek", ("pulled", "cagir"): "cek",
            ("pulled", "yaz"): "cek", ("deps", "kos"): "getir", ("deps", "yaz"): "getir",
            ("results", "yaz"): "kos", ("response", "yaz"): "cagir"})

    def test_a_missing_or_extra_edge(self):
        register = dict(HANDOVER)
        del register[("response", "yaz")]
        register[("results", "cagir")] = ("unwired", "x")
        self.assertEqual(problems(register, J.JOBS)[:2], ["unregistered:response->yaz", "not_an_edge:results->cagir"])

    def test_a_new_download_needs_a_status(self):
        jobs = dict(J.JOBS)
        jobs["cagir"] = jobs["cagir"]._replace(needs=("cek", "getir"), downloads=("pulled", "deps"))
        self.assertIn("unregistered:deps->cagir", problems(HANDOVER, jobs))

    def test_a_bad_status(self):
        for entry in (("done", KOS_TO_YAZ), ("handover", ""), ("unwired", None)):
            with self.subTest(entry=entry):
                register = dict(HANDOVER)
                register[("response", "yaz")] = entry
                self.assertEqual(problems(register, J.JOBS), ["bad_status:response:cagir->yaz"])


class Proofs(unittest.TestCase):
    def check(self, key: tuple[str, str], entry: tuple[str, str]) -> list[str]:
        return problems(dict(HANDOVER) | {key: entry}, J.JOBS)

    def test_a_wired_producer_is_not_unwired(self):
        # getir runs D2 (on an empty RUNNER_TEMP it refuses the missing pulled, it does not stop as unwired)
        self.assertEqual(self.check(("deps", "kos"), ("unwired", "x")), ["producer_wired:deps:getir->kos"])

    def test_kos_is_not_unwired_either(self):
        # kos ends cycle_not_wired after D3, but on an empty RUNNER_TEMP its first refusal is the missing pulled
        self.assertEqual(self.check(("results", "yaz"), ("unwired", "x")), ["producer_wired:results:kos->yaz"])

    def test_the_consumer_without_the_artifact_is_not_a_hand_over(self):
        # getir then kos with no copy of out/deps: kos raises Unusable, so no consumer call returned
        name = "test_loop_getir.HandOver.test_without_the_artifact_kos_has_no_verdict"
        self.assertEqual(self.check(("deps", "kos"), ("handover", name)),
                         ["not_handed_over:deps:getir->kos:%s" % name])

    def test_a_changed_copy_is_not_a_hand_over(self):
        # kos runs (done D3) on a copy whose tarball byte was flipped: not the content getir wrote
        name = "test_loop_getir.HandOver.test_a_changed_tarball_byte_after_the_hand_over"
        self.assertEqual(self.check(("deps", "kos"), ("handover", name)),
                         ["not_handed_over:deps:getir->kos:%s" % name])

    def test_a_consumer_on_its_own_fixture_is_not_a_hand_over(self):
        # yaz's own tests write in/results through kos; a test of decide alone never calls the yaz job
        name = "test_loop_yaz.OneCycle.test_good_merges_bad_rejected_for_their_reasons"
        self.assertEqual(self.check(("results", "yaz"), ("handover", name)),
                         ["not_handed_over:results:kos->yaz:%s" % name])

    def test_an_artifact_the_consumer_had_is_not_unread(self):
        self.assertEqual(self.check(("deps", "kos"), ("unread", GETIR_TO_KOS)),
                         ["not_unread:deps:getir->kos:%s" % GETIR_TO_KOS])

    def test_an_unknown_or_failing_test(self):
        unknown = "test_loop_getir.HandOver.test_no_such_test"
        self.assertEqual(self.check(("deps", "kos"), ("handover", unknown)),
                         ["test_failed:deps:getir->kos:%s" % unknown])
        failing = "test_loop_handover.Failing.deliberately_fails"
        self.assertEqual(self.check(("deps", "kos"), ("handover", failing)),
                         ["test_failed:deps:getir->kos:%s" % failing])

    def test_a_class_name_is_not_one_test(self):
        name = "test_loop_getir.HandOver"
        self.assertEqual(self.check(("deps", "kos"), ("handover", name)), ["test_failed:deps:getir->kos:%s" % name])

    def test_digest_sees_bytes_names_kinds_and_links(self):
        base = tempfile.mkdtemp(prefix="t-handover-")
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        root = os.path.join(base, "a")
        os.makedirs(os.path.join(root, "d"))
        with open(os.path.join(root, "d", "f"), "wb") as fh:
            fh.write(b"x")
        os.symlink("d/f", os.path.join(root, "l"))
        first = digest(root)
        self.assertEqual(digest(os.path.join(base, "none")), None)
        copy = os.path.join(base, "b")
        shutil.copytree(root, copy, symlinks=True)
        self.assertEqual(digest(copy), first)
        changes = {
            "byte": lambda r: write_tree(r, {"d/f": "y"}),
            "name": lambda r: os.rename(os.path.join(r, "d", "f"), os.path.join(r, "d", "g")),
            "link": lambda r: (os.remove(os.path.join(r, "l")), os.symlink("d", os.path.join(r, "l"))),
            "empty dir": lambda r: os.makedirs(os.path.join(r, "e")),
            "link to file": lambda r: (os.remove(os.path.join(r, "l")), shutil.copy(os.path.join(r, "d", "f"),
                                                                                  os.path.join(r, "l"))),
        }
        for label, change in changes.items():
            with self.subTest(change=label):
                other = os.path.join(base, label.replace(" ", "-"))
                shutil.copytree(root, other, symlinks=True)
                change(other)
                self.assertNotEqual(digest(other), first)


class Failing(unittest.TestCase):
    """Run by name only, from ``Proofs.test_an_unknown_or_failing_test``: its method is not ``test_*``, so
    discovery does not collect it."""

    def deliberately_fails(self):
        self.fail("deliberately")


if __name__ == "__main__":
    unittest.main()
