"""The cycle root's real signer: ``sigstore sign`` in ``yaz`` (D6; stage 0, MF11's signature, the counterpart of
``ledger.anchor.FakeSigner``).

Rules: asama-0/14 row 11 (the root is signed with Sigstore, the next D1 verifies it), tohum/01a (``yaz`` holds the
Sigstore OIDC identity), tohum/13 (a root that cannot be written to Rekor is a hard stop), ``ledger.anchor`` (the
signer's contract: ``sign(payload) -> {uuid, identity, bundle}``, or ``Unsignable``; the payload is the root's
preimage, so ``sha256(payload)`` is the root), ``loop.rekor`` (how the next D1 reads and judges the entry: through
Rekor's v1 API, a ``hashedrekord`` ``0.0.1`` body, the uuid as its leaf hash), tohum/26d "Kök" (the record's
``spec.data.hash`` is the root itself; ``sign`` takes files only, so the file signed is the preimage) and "Yer" (the
bundle is kept in ``brain/state``'s commit beside the root row: ``ledger.cycle`` puts the bytes answered here there).

``SigstoreSigner(pin).sign(payload)``, each run of step 1 in a fresh directory:

1. writes ``payload`` to a file and runs ``sigstore sign --rekor-version 1 --bundle <bundle> <file>``
   (``sign_argv``). ``sigstore`` 4.5.1 otherwise logs to the highest Rekor version its trust root offers, whose
   entries the v1 API does not serve, so the next D1 would find no entry. The OIDC token is the ambient one of
   the job (GitHub Actions' ``id-token``); this module passes none;
2. reads the bundle (at most ``loop.rekor.MAX_ANSWER`` bytes, one JSON object) and its one ``tlogEntries`` entry;
   its ``canonicalizedBody`` must be what ``loop.rekor.body_of`` accepts and record ``sha256(payload)``;
3. runs ``sigstore verify identity`` of that bundle against the payload file with ``pin`` and GitHub Actions'
   issuer (``loop.accepted.identity_argv``, the form both of the loop's Sigstore checks run): the entry was signed
   by the identity the next D1 will pin, not merely by whichever token the job had;
4. answers ``{uuid: the leaf hash of the body (64 hex, loop.rekor), identity: pin, bundle: the bundle file's bytes
   as ``sigstore`` wrote them}``: the bytes step 2 read and step 3 verified, read once.

**Step 1 again** (``RUNS``, ``PAUSES``). When ``sigstore sign`` exits 1, step 1 runs again, in another fresh
directory (``sigstore`` refuses to write over a bundle), after a pause of ``PAUSES`` seconds (2 before this
``sign``'s second run, 4 before its third), while the job's count allows a run ("The job's count" below); the first
run that exits 0 goes on to step 2. Exit 1 is what ``sigstore`` 4.5.0's
``sign`` exits with in each of the four real failures of ``tests/fixtures/sigstore-sign-failures.json`` (a party
it needs did not answer); any other exit (its argument error's 2, a program that cannot start: 127) is final at
once. Nothing after step 1 is run again: once ``sign`` exits 0 an entry may be in Rekor's log, and another run
would make another. A run that exits 1 after its entry was logged is not told apart from one that logged nothing:
the next run then logs a second entry for the same root, and the one answered is the last run's (the next D1
reads the entry by the uuid in the root row; the other stays in the log, named by no row). The pauses 2 and 4 are
this module's choice (no page gives a pause).

**The job's count** (``RUNS``, ``calls``; tohum/13 "Rekor'a yazılamama": in one ``yaz`` job the loop may call the
signing program at most 3 times). The count is the length of ``calls``, the one list that also names the runs: a
run of step 1 is made only while ``calls`` holds fewer than ``RUNS`` (3) entries, and every run made adds one. The
list is the signer's own when none is given, so one signer object makes at most 3 runs over all of its ``sign``
calls; signers given the same list (``loop.job`` gives every signer it makes in one job the job's list) make at
most 3 runs between them. The runs of ``sign`` that succeed count too: a job's first root signed on its third run
leaves no run for its second, which is then unsignable with no run made, and a job of more than 3 roots cannot
sign them all (``reports/seed-079``: the page gives no other count for such a job). The count is of the list
given, nothing else: two signers with lists of their own, or two processes, are counted apart.

A ``sign`` that exits non-zero on its last run is ``ledger.anchor.Unsignable`` ``sigstore sign failed (runs <n>;
exit <code>; <signs>)``: ``<n>`` the runs this ``sign`` made, ``<code>`` the last run's exit code and ``<signs>``
what ``loop.program`` names of the last run's output, joined by ``, `` (``no sign`` when it names nothing, or when
``run`` answers a plain ``int``). A ``sign`` that finds the count already used makes no run and is ``Unsignable``
``sigstore sign not run (the job's 3 runs are made)``. A missing, oversized or unreadable bundle, a bundle without
exactly one tlog entry, a body of another kind, version or digest, and a non-zero exit or a program that cannot
start at 3 are ``Unsignable`` too, each with its own fixed message (a hard stop: no ``brain/state`` row is written; what
``yaz`` already wrote to the target before signing stays written, ``loop.write_cycle``).
``tests/fixtures/rekor-entry.json`` ``published`` is a real bundle of ``sigstore sign`` and
``tests/fixtures/sigstore-signed-payload`` the file it signed; real ``sigstore`` 4.5.1's exits on them are recorded
in ``tests/test_sign.py``.

**Every run named** (``calls``; tohum/13 "Rekor'a yazılamama": each call's result is named in ``yaz``'s output).
Each run of step 1 made by this signer, or by another signer given the same list, in the order made and over
every ``sign``, is one entry of ``calls``: ``{exit, signs, result}``, ``exit`` the run's exit code, ``signs`` what
``loop.program`` names of its output (empty when ``run`` answers a plain ``int``), ``result`` ``signed`` (the run
exited 0 and steps 2 to 4 answered), ``exit`` (it exited non-zero, whether or not another run followed) or the
fixed message of the ``Unsignable`` step 2 or 3 raised on its bundle. The entry is appended when the run returns;
the runs of step 3 are not entries (they sign nothing). ``loop.job`` puts each target's part of the list in that
target's line of ``yaz`` (``sign_calls``).

The program is the caller's ``sigstore`` argv prefix: in ``yaz``, the one the ``sigstore`` step installs
(``loop.inputs.sigstore``, tohum/29s: ``sigstore==4.5.0``). The recorded exits above are 4.5.1's, the version the
fixtures were captured with; no exit of 4.5.0 on them is recorded here.

Out of scope, stated: whether the entry is
in Rekor's log beyond what ``sigstore verify identity`` checks of the bundle (the next D1 reads it from Rekor);
the pin's source (``loop.accepted.workflow_identity`` of the referee repository's ``loop.yml``, the caller's);
why a run failed (the signs are ``loop.program``'s reading of its output, not a cause shown); whether a failure
that exits 1 would pass on a later run (an expired or missing identity exits 1 too and is run again); a failure
that outlasts the runs the count allows (a hard stop, as before); the target left written when the root is not signed.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import time
from typing import Callable, Sequence

import cli
from ledger.anchor import Unsignable
from loop import accepted as A
from loop import program as PG
from loop import rekor as R

RUNS = 3
PAUSES = (2, 4)
AGAIN = 1
SIGNED, EXIT = "signed", "exit"
PAYLOAD = "root"
BUNDLE = "root.sigstore.json"


def sign_argv(sigstore: Sequence[str], bundle: str, payload: str) -> list[str]:
    return [*sigstore, "sign", "--rekor-version", "1", "--bundle", bundle, payload]


def _bundle_body(path: str, digest: str) -> tuple[bytes, str]:
    """The bundle's bytes and its one ``canonicalizedBody``, checked by the rules above; ``Unsignable``."""
    try:
        with open(path, "rb") as fh:
            data = fh.read(R.MAX_ANSWER + 1)
    except OSError:
        raise Unsignable("sigstore wrote no bundle") from None
    if len(data) > R.MAX_ANSWER:
        raise Unsignable("bundle too large")
    try:
        made = cli.loads(data)
        entries = made["verificationMaterial"]["tlogEntries"]
        body = entries[0]["canonicalizedBody"] if isinstance(entries, list) and len(entries) == 1 else None
    except (ValueError, RecursionError, KeyError, TypeError, IndexError):
        raise Unsignable("bundle unreadable") from None
    record = R.body_of({"body": body}) if isinstance(body, str) else None
    if record is None or record["spec"]["data"]["hash"]["value"] != digest:
        raise Unsignable("bundle records no hashedrekord 0.0.1 of the payload")
    return data, body


class SigstoreSigner:
    """``sign(payload) -> {uuid, identity, bundle}`` by the rules above; ``run(argv) -> exit code`` (with ``signs``
    when it is ``loop.program``'s), ``sleep(seconds)`` the pause between two runs of ``sign``; ``calls`` the list
    the runs of ``sign`` are counted and named in (the signer's own when ``None``)."""

    def __init__(self, pin: str, sigstore: Sequence[str], run: Callable[[list[str]], int] = PG.run,
                 sleep: Callable[[float], None] = time.sleep, calls: list[dict] | None = None):
        if not isinstance(pin, str) or not pin:
            raise ValueError("identity pin must be a non-empty string")
        self.pin, self.sigstore, self.run, self.sleep = pin, sigstore, run, sleep
        self.calls: list[dict] = [] if calls is None else calls

    def _answer(self, bundle: str, path: str, digest: str) -> dict:
        """Steps 2 to 4 on the bundle a ``sign`` that exited 0 wrote."""
        data, body = _bundle_body(bundle, digest)
        if self.run(A.identity_argv(self.sigstore, bundle, self.pin, path)) != 0:
            raise Unsignable("the bundle is not verified for the pinned identity")
        return {"uuid": R._leaf(body), "identity": self.pin, "bundle": data}

    def sign(self, payload: bytes) -> dict:
        digest = hashlib.sha256(payload).hexdigest()
        made = 0
        for _ in range(RUNS):
            if len(self.calls) >= RUNS:
                break
            if made:
                self.sleep(PAUSES[made - 1])
            with tempfile.TemporaryDirectory(prefix="root-sign-") as tmp:
                path, bundle = os.path.join(tmp, PAYLOAD), os.path.join(tmp, BUNDLE)
                with open(path, "wb") as fh:
                    fh.write(payload)
                code = self.run(sign_argv(self.sigstore, bundle, path))
                made += 1
                call = {"exit": int(code), "signs": list(getattr(code, "signs", ())), "result": EXIT}
                self.calls.append(call)
                if code == 0:
                    try:
                        answer = self._answer(bundle, path, digest)
                    except Unsignable as exc:
                        call["result"] = cli.cause(exc)
                        raise
                    call["result"] = SIGNED
                    return answer
            if code != AGAIN:
                break
        if not made:
            raise Unsignable("sigstore sign not run (the job's %d runs are made)" % RUNS)
        signs = ", ".join(getattr(code, "signs", ())) or "no sign"
        raise Unsignable("sigstore sign failed (runs %d; exit %d; %s)" % (made, code, signs))
