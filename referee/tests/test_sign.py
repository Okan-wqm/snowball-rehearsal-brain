"""Test 40 (asama-0/09, MF11's signature): ``loop.sign.SigstoreSigner``, the cycle root's real signer.

- a real bundle of ``sigstore sign`` (``fixtures/rekor-entry.json`` ``published``) over the file it signed
  (``fixtures/sigstore-signed-payload``): the answer is ``{uuid: the body's leaf hash, identity: pin}`` and the uuid
  is the one Rekor serves the entry under; the two runs are ``sign --rekor-version 1 --bundle`` of the payload file
  (holding exactly the payload) and ``verify identity`` of that bundle with the pin;
- each refusal alone, each ``Unsignable`` (a hard stop): sign exits non-zero, no bundle, a bundle too large, not
  JSON, with no or two tlog entries, recording another digest, of another kind or of ``0.0.2`` (Rekor v2's), the
  verifier refusing the pin; a refusal before the verifier runs nothing more, and none of them but a ``sign``
  that exits 1 is run again;
- ``sign`` again: exit 1 is run again after 2 and then 4 seconds, three runs at most, each in its own directory
  (a bundle a failed run left is not the next run's); the first run that exits 0 is the one answered and verified;
  exit 2 and 127 are final at once; the message names the runs, the last exit code and the last run's signs
  (``loop.program``'s; ``no sign`` for none and for a runner answering a plain ``int``);
- every run named (``Calls``): ``calls`` holds one ``{exit, signs, result}`` per run of ``sign``, in order, appended
  when the run returns: the failed runs before the one that signs, all three when none signs, one for a final
  exit, the refusal's fixed message for a run that exited 0 and was refused at step 2 or 3, and the runs of two
  ``sign`` calls of one signer; the verify run is no entry;
- the job's count (``JobCount``; tohum/13: at most 3 calls in one ``yaz`` job): the runs are counted in ``calls``
  over every ``sign`` of one signer and over signers given one list, the runs that signed too: a ``sign`` left one
  run makes one and does not pause after it, a ``sign`` left none makes none and says so; signers with lists of
  their own are counted apart; ``rooted_program`` is the same count's fake program on disk (``test_loop_write``);
- round trip: ``ledger.anchor.anchor`` with this signer gives the entry that ``loop.rekor.entry_reasons`` (the next
  D1) finds and accepts for the same root, and a root of another ledger is refused there;
- the default runner on a real process: a fake ``sigstore`` program on disk; one that cannot start is unsignable
  at once; one that raises on its first run and signs on its second is answered, one that raises on every run is
  unsignable with the raised type's name and none of its message.

Real ``sigstore`` 4.5.1 on the two fixtures (session of 2026-11-01): ``verify identity`` exits 0 with the fixture's
identity and 1 with another (``tests/fixtures/rekor-entry.json`` ``verdicts`` records the same on the bundle
``loop.rekor`` makes); ``sigstore sign --help`` names ``--rekor-version`` (1 or 2, default the highest available).
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REFEREE)
sys.path.insert(0, HERE)

from ledger import anchor as AN  # noqa: E402
from loop import accepted as A  # noqa: E402
from loop import program as PG  # noqa: E402
from loop import rekor as R  # noqa: E402
from loop import sign as S  # noqa: E402
from test_anchor import LEDGER  # noqa: E402
from test_rekor import REAL, REAL_ENTRY  # noqa: E402

PIN = "https://github.com/acme/referee/.github/workflows/loop.yml@refs/heads/main"
with open(os.path.join(HERE, "fixtures", "sigstore-signed-payload"), "rb") as _fh:
    SIGNED = _fh.read()


def bundle_for(digest: str | None = None, kind: str = "hashedrekord", version: str = "0.0.1",
               entries: int = 1) -> dict:
    """The real published bundle; with ``digest``, ``kind`` or ``version`` its body rewritten (no signature here is
    valid then: the verifier is a fake)."""
    made = copy.deepcopy(REAL["published"])
    tlog = made["verificationMaterial"]["tlogEntries"]
    if digest is not None or kind != "hashedrekord" or version != "0.0.1":
        body = json.loads(base64.b64decode(tlog[0]["canonicalizedBody"]))
        body["kind"], body["apiVersion"] = kind, version
        if digest is not None:
            body["spec"]["data"]["hash"]["value"] = digest
        tlog[0]["canonicalizedBody"] = base64.b64encode(json.dumps(body).encode()).decode()
    made["verificationMaterial"]["tlogEntries"] = (tlog * entries)[:entries]
    return made


def leaf(body_b64: str) -> str:
    return hashlib.sha256(b"\x00" + base64.b64decode(body_b64)).hexdigest()


class Program:
    """A fake ``run``: ``sign`` writes ``bundle`` (bytes, or None for nothing) and exits ``sign_exit`` (a list: its
    next entry, the last one for every later run); ``verify`` exits ``verify_exit``. Keeps every argv, the payload
    file's bytes at sign time and the pauses asked of ``sleep``."""

    def __init__(self, bundle, sign_exit=0, verify_exit=0):
        self.bundle, self.verify_exit = bundle, verify_exit
        self.sign_exits = list(sign_exit) if isinstance(sign_exit, list) else [sign_exit]
        self.argvs, self.signed, self.pauses = [], None, []

    def sleep(self, seconds):
        self.pauses.append(seconds)

    def signer(self, pin=PIN, sigstore=("sigstore",)):
        return S.SigstoreSigner(pin, sigstore, self, self.sleep)

    def __call__(self, argv):
        self.argvs.append(list(argv))
        if next(a for a in argv if a in ("sign", "verify")) == "sign":
            with open(argv[-1], "rb") as fh:
                self.signed = fh.read()
            if self.bundle is not None:
                with open(argv[argv.index("--bundle") + 1], "wb") as fh:
                    fh.write(self.bundle if isinstance(self.bundle, bytes) else json.dumps(self.bundle).encode())
            return self.sign_exits.pop(0) if len(self.sign_exits) > 1 else self.sign_exits[0]
        return self.verify_exit


class RealBundle(unittest.TestCase):
    def test_answers_the_leaf_hash_and_the_pin(self):
        written = json.dumps(REAL["published"], indent=1).encode() + b"\n"
        run = Program(written)
        answer = run.signer(sigstore=("/opt/python", "-m", "sigstore")).sign(SIGNED)
        # the bundle is the file's bytes as the program wrote them, not a rewriting of them
        self.assertEqual(answer, {"uuid": REAL["uuid"][-64:], "identity": PIN, "bundle": written})
        self.assertEqual(R.checked_answer(answer["uuid"], json.loads(REAL["answer"])), REAL_ENTRY)  # Rekor's entry
        sign, verify = run.argvs
        bundle, payload = sign[7], sign[8]
        # the program is an argv prefix: the sigstore step's venv as ``python -m sigstore`` (tohum/29s)
        self.assertEqual(sign, ["/opt/python", "-m", "sigstore", "sign", "--rekor-version", "1", "--bundle", bundle,
                                payload])
        self.assertEqual(verify, A.identity_argv(("/opt/python", "-m", "sigstore"), bundle, PIN, payload))
        self.assertEqual(run.signed, SIGNED)
        self.assertNotEqual(bundle, payload)
        self.assertFalse(os.path.exists(bundle))  # the fresh directory is gone
        self.assertEqual(run.pauses, [])

    def test_empty_pin_is_refused(self):
        for bad in ("", None):
            with self.assertRaises(ValueError):
                S.SigstoreSigner(bad, ("sigstore",))


class Refusals(unittest.TestCase):
    def refused(self, run, payload=SIGNED, runs=2, pauses=()):
        with self.assertRaises(AN.Unsignable) as ctx:
            run.signer().sign(payload)
        self.assertEqual(len(run.argvs), runs)
        self.assertEqual(run.pauses, list(pauses))
        self.assertTrue(issubclass(AN.Unsignable, AN.append.HardStop))
        return str(ctx.exception)

    def test_sign_fails(self):
        run = Program(REAL["published"], sign_exit=1)
        self.assertEqual(self.refused(run, runs=3, pauses=(2, 4)), "sigstore sign failed (runs 3; exit 1; no sign)")
        self.assertEqual([argv[1] for argv in run.argvs], ["sign"] * 3)
        self.assertEqual(len({argv[argv.index("--bundle") + 1] for argv in run.argvs}), 3)  # a directory each

    def test_sign_fails_otherwise(self):
        for code in (2, 3, 127, -9, 256 + 1):
            with self.subTest(code=code):
                self.assertEqual(self.refused(Program(REAL["published"], sign_exit=code), runs=1),
                                 "sigstore sign failed (runs 1; exit %d; no sign)" % code)
        # the second run's exit is final when it is not 1
        self.assertEqual(self.refused(Program(REAL["published"], sign_exit=[1, 2]), runs=2, pauses=(2,)),
                         "sigstore sign failed (runs 2; exit 2; no sign)")

    def test_the_message_names_the_last_run_s_signs(self):
        exits = [PG.Exit(1, ("network",)), PG.Exit(1, ()), PG.Exit(1, ("tuf_refresh", "raised:a.BError"))]
        self.assertEqual(self.refused(Program(None, sign_exit=exits), runs=3, pauses=(2, 4)),
                         "sigstore sign failed (runs 3; exit 1; tuf_refresh, raised:a.BError)")
        self.assertEqual(self.refused(Program(None, sign_exit=PG.Exit(127)), runs=1),
                         "sigstore sign failed (runs 1; exit 127; no sign)")

    def test_a_later_run_signs(self):
        for exits, pauses in (([1, 0], [2]), ([1, 1, 0], [2, 4])):
            with self.subTest(exits=exits):
                run = Program(REAL["published"], sign_exit=list(exits))
                answer = run.signer().sign(SIGNED)
                self.assertEqual((answer["uuid"], run.pauses), (REAL["uuid"][-64:], pauses))
                self.assertEqual([argv[1] for argv in run.argvs], ["sign"] * len(exits) + ["verify"])
                last, verify = run.argvs[-2], run.argvs[-1]
                bundle = last[last.index("--bundle") + 1]
                self.assertEqual(verify, A.identity_argv(("sigstore",), bundle, PIN, last[-1]))  # the run that signed

    def test_a_failed_run_s_bundle_is_not_the_next_run_s(self):
        class Leaves(Program):
            def __call__(self, argv):
                code = super().__call__(argv)
                self.bundle = None  # only the first run writes one
                return code
        self.assertEqual(self.refused(Leaves(REAL["published"], sign_exit=[1, 0]), runs=2, pauses=(2,)),
                         "sigstore wrote no bundle")

    def test_no_fourth_run(self):
        self.assertEqual((S.RUNS, S.PAUSES, S.AGAIN), (3, (2, 4), 1))
        self.refused(Program(REAL["published"], sign_exit=[1, 1, 1, 0]), runs=3, pauses=(2, 4))

    def test_no_bundle(self):
        self.refused(Program(None), runs=1)

    def test_bundle_too_large(self):
        self.refused(Program(json.dumps(REAL["published"]).encode().ljust(R.MAX_ANSWER + 1)), runs=1)  # valid JSON
        Program(json.dumps(REAL["published"]).encode().ljust(R.MAX_ANSWER)).signer().sign(SIGNED)

    def test_bundle_not_json(self):
        self.refused(Program(b"{"), runs=1)

    def test_tlog_entries_not_one(self):
        for n in (0, 2):
            self.refused(Program(bundle_for(entries=n)), runs=1)
        self.refused(Program({"verificationMaterial": {"tlogEntries": {"0": {}}}}), runs=1)

    def test_another_digest(self):
        self.refused(Program(REAL["published"]), payload=SIGNED + b"\n", runs=1)
        self.refused(Program(bundle_for(digest="0" * 64)), runs=1)

    def test_another_kind_or_rekor_v2(self):
        self.refused(Program(bundle_for(kind="dsse")), runs=1)
        self.refused(Program(bundle_for(version="0.0.2")), runs=1)

    def test_verifier_refuses_the_pin(self):
        self.assertEqual(self.refused(Program(REAL["published"], verify_exit=1), runs=2),
                         "the bundle is not verified for the pinned identity")


class Rooted(Program):
    """A ``Program`` whose ``sign`` writes the published bundle rewritten to record the payload file's own sha256
    (any payload is signed; ``bundle`` None still writes nothing)."""

    def __call__(self, argv):
        if "sign" in argv and self.bundle is not None:
            with open(argv[-1], "rb") as fh:
                self.bundle = bundle_for(digest=hashlib.sha256(fh.read()).hexdigest())
        return super().__call__(argv)


class Calls(unittest.TestCase):
    """tohum/13 "Rekor'a yazılamama": every run of ``sign`` is named, ``{exit, signs, result}``, in order."""

    def test_one_run_that_signs(self):
        run = Program(REAL["published"])
        signer = run.signer()
        self.assertEqual(signer.calls, [])
        signer.sign(SIGNED)
        self.assertEqual(signer.calls, [{"exit": 0, "signs": [], "result": "signed"}])
        self.assertEqual(len(run.argvs), 2)  # the verify run is no entry

    def test_failed_runs_before_the_one_that_signs_keep_their_exit_and_signs(self):
        run = Program(REAL["published"], sign_exit=[PG.Exit(1, ("network",)), 1, PG.Exit(0)])
        signer = run.signer()
        signer.sign(SIGNED)
        self.assertEqual(signer.calls, [{"exit": 1, "signs": ["network"], "result": "exit"},
                                        {"exit": 1, "signs": [], "result": "exit"},
                                        {"exit": 0, "signs": [], "result": "signed"}])
        self.assertTrue(all(type(c["exit"]) is int and type(c["signs"]) is list for c in signer.calls))
        json.dumps(signer.calls)

    def test_no_run_signs(self):
        exits = [PG.Exit(1, ("network",)), PG.Exit(1, ()), PG.Exit(1, ("tuf_refresh", "raised:a.BError"))]
        signer = Program(None, sign_exit=exits).signer()
        with self.assertRaises(AN.Unsignable):
            signer.sign(SIGNED)
        self.assertEqual(signer.calls, [{"exit": 1, "signs": ["network"], "result": "exit"},
                                        {"exit": 1, "signs": [], "result": "exit"},
                                        {"exit": 1, "signs": ["tuf_refresh", "raised:a.BError"], "result": "exit"}])
        self.assertEqual(len(signer.calls), S.RUNS)

    def test_a_final_exit_is_one_entry(self):
        signer = Program(REAL["published"], sign_exit=[2, 0]).signer()
        with self.assertRaises(AN.Unsignable):
            signer.sign(SIGNED)
        self.assertEqual(signer.calls, [{"exit": 2, "signs": [], "result": "exit"}])

    def test_a_run_that_exits_0_and_is_refused_names_the_refusal(self):
        for run, message in ((Program(None), "sigstore wrote no bundle"),
                             (Program(b"{"), "bundle unreadable"),
                             (Program(bundle_for(digest="0" * 64)),
                              "bundle records no hashedrekord 0.0.1 of the payload"),
                             (Program(REAL["published"], verify_exit=1),
                              "the bundle is not verified for the pinned identity")):
            with self.subTest(message=message):
                signer = run.signer()
                with self.assertRaises(AN.Unsignable) as ctx:
                    signer.sign(SIGNED)
                self.assertEqual(str(ctx.exception), message)
                self.assertEqual(signer.calls, [{"exit": 0, "signs": [], "result": message}])

    def test_the_entry_is_there_when_the_run_returns(self):
        seen = []

        class Watching(Program):
            def __call__(self, argv):
                seen.append(len(signer.calls))
                return super().__call__(argv)
        signer = Watching(REAL["published"], sign_exit=[1, 0]).signer()
        signer.sign(SIGNED)
        self.assertEqual(seen, [0, 1, 2])  # sign, sign, verify

    def test_two_signs_of_one_signer_are_kept_in_order(self):
        signer = Rooted(REAL["published"], sign_exit=[1, 0, 2]).signer()
        signer.sign(SIGNED)
        with self.assertRaises(AN.Unsignable):
            signer.sign(SIGNED + b"more")
        self.assertEqual([(c["exit"], c["result"]) for c in signer.calls], [(1, "exit"), (0, "signed"), (2, "exit")])
        other = Rooted(REAL["published"]).signer()
        other.sign(SIGNED + b"more")  # a rewritten bundle for another payload is signed too
        self.assertEqual(other.calls, [{"exit": 0, "signs": [], "result": "signed"}])


class JobCount(unittest.TestCase):
    """tohum/13 "Rekor'a yazılamama": at most ``RUNS`` runs of ``sign`` in the list the signer counts in."""

    def test_a_second_sign_has_the_runs_the_first_left(self):
        run = Rooted(REAL["published"], sign_exit=[1, 0, 1, 0])
        signer = run.signer()
        signer.sign(SIGNED)
        with self.assertRaises(AN.Unsignable) as ctx:
            signer.sign(SIGNED + b"second")
        self.assertEqual(str(ctx.exception), "sigstore sign failed (runs 1; exit 1; no sign)")
        self.assertEqual([c["result"] for c in signer.calls], ["exit", "signed", "exit"])
        self.assertEqual(([argv[1] for argv in run.argvs], run.pauses), (["sign", "sign", "verify", "sign"], [2]))

    def test_a_sign_after_the_third_run_runs_nothing(self):
        run = Rooted(REAL["published"], sign_exit=[1, 1, 0, 0])
        signer = run.signer()
        signer.sign(SIGNED)
        before = (list(run.argvs), list(signer.calls), list(run.pauses))
        for _ in range(2):
            with self.assertRaises(AN.Unsignable) as ctx:
                signer.sign(SIGNED + b"second")
            self.assertEqual(str(ctx.exception), "sigstore sign not run (the job's 3 runs are made)")
        self.assertEqual((run.argvs, signer.calls, run.pauses), before)
        self.assertEqual(len(signer.calls), S.RUNS)

    def test_three_runs_that_sign_are_the_count_too(self):
        run = Rooted(REAL["published"])
        signer = run.signer()
        for n in range(S.RUNS):
            signer.sign(SIGNED + bytes([n]))
        with self.assertRaises(AN.Unsignable):
            signer.sign(SIGNED + b"fourth")
        self.assertEqual(([c["result"] for c in signer.calls], run.pauses), (["signed"] * 3, []))

    def test_the_pause_is_by_the_runs_of_this_sign(self):
        run = Rooted(REAL["published"], sign_exit=[0, 1, 0])
        signer = run.signer()
        signer.sign(SIGNED)
        signer.sign(SIGNED + b"second")
        self.assertEqual((run.pauses, len(signer.calls)), ([2], 3))  # 2 before a sign's second run, not 4

    def test_signers_given_one_list_count_together_and_others_apart(self):
        calls = []
        run = Rooted(REAL["published"], sign_exit=[1, 0, 0, 0])
        first, second = (S.SigstoreSigner(PIN, ("sigstore",), run, run.sleep, calls=calls) for _ in range(2))
        self.assertIs(first.calls, calls)
        first.sign(SIGNED)
        second.sign(SIGNED + b"second")
        self.assertEqual([c["result"] for c in calls], ["exit", "signed", "signed"])
        with self.assertRaises(AN.Unsignable) as ctx:
            first.sign(SIGNED + b"third")
        self.assertEqual(str(ctx.exception), "sigstore sign not run (the job's 3 runs are made)")
        apart = S.SigstoreSigner(PIN, ("sigstore",), run, run.sleep)
        apart.sign(SIGNED + b"third")
        self.assertEqual((len(calls), apart.calls), (3, [{"exit": 0, "signs": [], "result": "signed"}]))


def rooted_program(path: str, exits: list[int]) -> str:
    """A fake ``sigstore`` on disk at ``path`` (run as ``<path> [-m sigstore] sign|verify ...``): its n-th ``sign``
    writes the published bundle rewritten to record the payload file's sha256 and exits ``exits[n]`` (the last
    entry for every later run); ``verify`` exits 0. Returns the file whose size is the number of ``sign`` runs."""
    source, count = path + ".bundle.json", path + ".count"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(source, "w") as fh:
        json.dump(REAL["published"], fh)
    with open(path, "w") as fh:
        fh.write("#!%s\nimport base64, hashlib, json, os, sys\nargv = sys.argv[1:]\n"
                 "if 'sign' not in argv:\n    sys.exit(0)\n"
                 "seen = os.path.getsize(%r) if os.path.exists(%r) else 0\n"
                 "open(%r, 'a').write('x')\n"
                 "exits = %r\n"
                 "made = json.load(open(%r))\n"
                 "entry = made['verificationMaterial']['tlogEntries'][0]\n"
                 "body = json.loads(base64.b64decode(entry['canonicalizedBody']))\n"
                 "body['spec']['data']['hash']['value'] = hashlib.sha256(open(argv[-1], 'rb').read()).hexdigest()\n"
                 "entry['canonicalizedBody'] = base64.b64encode(json.dumps(body).encode()).decode()\n"
                 "json.dump(made, open(argv[argv.index('--bundle') + 1], 'w'))\n"
                 "sys.exit(exits[min(seen, len(exits) - 1)])\n"
                 % (sys.executable, count, count, count, list(exits), source))
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    return count


class RoundTrip(unittest.TestCase):
    """What the signer answers is what the next D1 reads and accepts."""

    def test_anchor_then_next_d1(self):
        tip_map = AN.tips(LEDGER)
        root = AN.root_of(tip_map)
        made = bundle_for(digest=root)  # tohum/26d "Kök": the record's spec.data.hash is the root itself
        body = made["verificationMaterial"]["tlogEntries"][0]["canonicalizedBody"]
        program = Program(made)
        entry, bundle = AN.anchor(tip_map, program.signer())
        self.assertEqual(entry, {"uuid": leaf(body), "hash": root, "identity": PIN})
        self.assertEqual(hashlib.sha256(program.signed).hexdigest(), root)  # the file sigstore hashed
        self.assertEqual(json.loads(bundle), made)
        rekor = {entry["uuid"]: dict(copy.deepcopy(REAL_ENTRY), body=body)}
        seen = []
        judge = R.entry_reasons(rekor.get, PIN, ("sigstore",), lambda argv: seen.append(argv) or 0)
        self.assertEqual(judge(entry["uuid"], root), [])
        self.assertEqual(seen[0][seen[0].index("--cert-identity") + 1], PIN)
        self.assertEqual(seen[0][-1], "sha256:" + root)  # the digest stage-open verifies the bundle for
        self.assertEqual(judge(entry["uuid"], "cd" * 32), ["entry_root_mismatch"])

    def test_a_record_of_a_digest_of_the_root_is_not_signed(self):
        tip_map = AN.tips(LEDGER)
        of_the_text = hashlib.sha256(AN.root_of(tip_map).encode("ascii")).hexdigest()
        program = Program(bundle_for(digest=of_the_text))
        with self.assertRaises(AN.Unsignable):
            AN.anchor(tip_map, program.signer())
        self.assertEqual(len(program.argvs), 1)  # refused on the bundle's body, before the verifier


class RealProcess(unittest.TestCase):
    def test_default_runner_runs_the_program(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, "bundle.json")
            with open(source, "w") as fh:
                json.dump(REAL["published"], fh)
            program = os.path.join(tmp, "sigstore")
            with open(program, "w") as fh:
                fh.write("#!%s\nimport shutil, sys\nargv = sys.argv[1:]\n"
                         "if argv[0] == 'sign':\n    shutil.copy(%r, argv[argv.index('--bundle') + 1])\n"
                         "sys.exit(0 if argv[0] == 'sign' or %r in argv else 1)\n" % (sys.executable, source, PIN))
            os.chmod(program, os.stat(program).st_mode | stat.S_IXUSR)
            self.assertEqual(S.SigstoreSigner(PIN, (program,)).sign(SIGNED)["uuid"], REAL["uuid"][-64:])
            with self.assertRaises(AN.Unsignable):
                S.SigstoreSigner(PIN + "x", (program,)).sign(SIGNED)
            pauses = []
            with self.assertRaises(AN.Unsignable) as ctx:
                S.SigstoreSigner(PIN, (os.path.join(tmp, "absent"),), sleep=pauses.append).sign(SIGNED)
            self.assertEqual((str(ctx.exception), pauses), ("sigstore sign failed (runs 1; exit 127; no sign)", []))

    def flaky(self, tmp, failures):
        """A program on disk whose ``sign`` raises ``failures`` times (a count kept in a file), then signs."""
        source, count = os.path.join(tmp, "bundle.json"), os.path.join(tmp, "count")
        with open(source, "w") as fh:
            json.dump(REAL["published"], fh)
        program = os.path.join(tmp, "sigstore")
        with open(program, "w") as fh:
            fh.write("#!%s\nimport os, shutil, sys\nargv = sys.argv[1:]\n"
                     "class RegistryError(Exception):\n    pass\n"
                     "if argv[0] == 'sign':\n"
                     "    seen = os.path.getsize(%r) if os.path.exists(%r) else 0\n"
                     "    open(%r, 'a').write('x')\n"
                     "    if seen < %d:\n        raise RegistryError('told-in-the-message')\n"
                     "    shutil.copy(%r, argv[argv.index('--bundle') + 1])\n"
                     % (sys.executable, count, count, count, failures, source))
        os.chmod(program, os.stat(program).st_mode | stat.S_IXUSR)
        return program, count

    def test_a_program_that_raises_once_then_signs(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, count = self.flaky(tmp, 1)
            pauses = []
            answer = S.SigstoreSigner(PIN, (program,), sleep=pauses.append).sign(SIGNED)
            self.assertEqual((answer["uuid"], pauses, os.path.getsize(count)), (REAL["uuid"][-64:], [2], 2))

    def test_a_program_that_raises_every_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, count = self.flaky(tmp, 9)
            pauses = []
            with self.assertRaises(AN.Unsignable) as ctx:
                S.SigstoreSigner(PIN, (program,), sleep=pauses.append).sign(SIGNED)
            self.assertEqual((str(ctx.exception), pauses, os.path.getsize(count)),
                             ("sigstore sign failed (runs 3; exit 1; raised:RegistryError)", [2, 4], 3))


if __name__ == "__main__":
    unittest.main()
