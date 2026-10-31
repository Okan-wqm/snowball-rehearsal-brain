"""``rekor.anchor``: the cycle's root, its signature, and the next D1's check of it (stage 0, MF11).

Rules: asama-0/14 row 11, asama-0/09 test 40, tohum/29j (group ``root``), tohum/13 (root and external log; a
chain break or a root that cannot be written to Rekor is a hard stop), tohum/26 (part -> file; roots in
``chain/root.jsonl``), tohum/27a (``chain/root.jsonl`` rows), tohum/28 (hard stop).

- **Root** (``tips``, ``root_of``): the ledger must be a valid chain (``ledger.chain.verify_bytes``, the one
  verifier) and every row must carry a non-empty string ``part``; otherwise ``Unusable``. ``tips`` maps each part
  that has a row to the stored ``row_hash`` of that part's last row in file order; ``root`` is the lowercase hex
  sha256 of the RFC 8785 bytes of ``tips`` (``ledger.chain.canonical``). An empty ledger has no tip and is
  ``Unusable``: there is nothing to anchor.
- **Anchor** (``anchor``): the signer signs the root's 64 hex characters (ASCII) as its payload and answers
  ``{uuid, identity}``; the entry is ``{uuid, hash: root, identity}``. A signer that cannot sign raises
  ``Unsignable``, which is a ``HardStop``: no entry, nothing written. Only ``FakeSigner`` exists here: it stands
  in for a verified Sigstore bundle (asama-0/14 "Kum", tohum/29j) and does no cryptography; a real Sigstore
  signer and the seed's pins are not part of this module (asama-0/10a #kok).
- **Verify** (``verify``, the next cycle's D1): reads the ledger's root, only the last line of
  ``chain/root.jsonl`` (``root`` 64 lowercase hex, ``rekor_uuid`` a non-empty string) and the recorded Rekor
  entries ``{entries: {uuid: {hash, identity}}}``. Reasons, in this order: ``root_mismatch`` (the ledger's root
  is not the recorded root); ``entry_missing`` (no entry under ``rekor_uuid``; then the other two are not
  judged); ``entry_root_mismatch`` (the entry's ``hash`` is not the recorded root); ``identity_mismatch`` (the
  entry's ``identity`` is not the pin). Valid only with no reason. Not judged here: the chain of
  ``chain/root.jsonl`` itself (``ledger.chain verify`` reads it, tohum/27a) and how the entries were fetched
  from Rekor.
- **The cycle** (``anchor_cycle``, calls 10 -> 11): ``chain/root.jsonl`` is checked as an append-only valid chain
  of its previous version, then ``ledger.append.plan_cycle`` (which checks the ledger before it reads the
  request), then the root of the new ledger is signed, then one chained root row ``{row_id, ts, root,
  rekor_uuid, prev_hash, row_hash}`` is appended, and both files go to the state writer in one
  ``commit_files`` call: the signed root is in the cycle's one ``brain/state`` commit. A hard stop at any step
  commits nothing. Writing the hard-stop row itself (tohum/28) is the caller's.

Command line (tohum/29j), run from ``referee/``, one JSON line on stdout, the cause on stderr::

    python -m ledger.anchor root LEDGER                  -> {tips, root}                       exit 0
    python -m ledger.anchor anchor SIGNER  stdin {"root"} -> {ok, hard_stop, entry}             exit 0, 1 unsignable
    python -m ledger.anchor verify LEDGER ROOTS REKOR  stdin {"identity"} -> {valid, reasons}   exit 0 valid, 1 not
    exit 2 in all three: unusable input (the line then carries null or empty fields).

The stdin requests take exactly the named key. ``SIGNER`` ``{available, identity, uuid}``: ``available`` a
boolean; when true, ``identity`` and ``uuid`` non-empty strings. Other keys of the signer file, of the Rekor
record and of its entries are records of an outside system and are ignored.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

from ledger import append, chain
import cli

LEDGER_PATH = "ledger.jsonl"
ROOTS_PATH = "chain/root.jsonl"
REASONS = ("root_mismatch", "entry_missing", "entry_root_mismatch", "identity_mismatch")


class Unusable(ValueError):
    pass


class Unsignable(append.HardStop):
    """The root cannot be signed: a hard stop (tohum/13, tohum/28), nothing is written."""


# ---------------------------------------------------------------- root

def tips(ledger: bytes) -> dict[str, str]:
    verdict = chain.verify_bytes(ledger)
    if not verdict["valid"]:
        raise Unusable("ledger is not a valid chain: %s (%s)" % (verdict["reason"], verdict["broken_row"]))
    out: dict[str, str] = {}
    for lineno, line in enumerate(chain._lines(ledger), 1):
        row = chain.parse_row(line.decode("utf-8"))
        part = row.get("part")
        if not isinstance(part, str) or not part:
            raise Unusable("line %d has no part" % lineno)
        out[part] = row["row_hash"]
    if not out:
        raise Unusable("empty ledger: no tip to anchor")
    return out


def root_of(tip_map: dict[str, str]) -> str:
    return hashlib.sha256(chain.canonical(tip_map)).hexdigest()


# ---------------------------------------------------------------- signing

@dataclass
class FakeSigner:
    """``{available, identity, uuid}``: answers with its uuid and identity, or cannot sign. Keeps the payloads."""

    available: bool
    identity: str | None = None
    uuid: str | None = None
    payloads: list[bytes] = field(default_factory=list)

    @classmethod
    def from_json(cls, obj: Any) -> "FakeSigner":
        if not isinstance(obj, dict) or type(obj.get("available")) is not bool:
            raise Unusable("signer: available must be a boolean")
        if obj["available"]:
            for key in ("identity", "uuid"):
                if not isinstance(obj.get(key), str) or not obj[key]:
                    raise Unusable("signer: %s must be a non-empty string" % key)
        return cls(obj["available"], obj.get("identity"), obj.get("uuid"))

    def sign(self, payload: bytes) -> dict:
        if not self.available:
            raise Unsignable("signer unavailable")
        self.payloads.append(payload)
        return {"uuid": self.uuid, "identity": self.identity}


def _root_text(value: Any) -> str:
    if not isinstance(value, str) or not chain.HEX64.match(value):
        raise Unusable("root must be 64 lowercase hex characters")
    return value


def anchor(root: str, signer: Any) -> dict:
    """Sign ``root`` and return the entry ``{uuid, hash, identity}``; ``Unsignable`` if it cannot be signed."""
    root = _root_text(root)
    answer = signer.sign(root.encode("ascii"))
    if not isinstance(answer, dict) or not all(isinstance(answer.get(k), str) and answer[k] for k in ("uuid", "identity")):
        raise Unsignable("signer gave no entry")
    return {"uuid": answer["uuid"], "hash": root, "identity": answer["identity"]}


# ---------------------------------------------------------------- verify (next D1)

def _last_root_row(roots: bytes) -> dict:
    lines = chain._lines(roots)
    if not lines:
        raise Unusable("root file has no row")
    try:
        row = chain.parse_row(lines[-1].decode("utf-8"))
    except (UnicodeDecodeError, chain.ChainError) as exc:
        raise Unusable("last root row: %s" % exc) from None
    _root_text(row.get("root"))
    if not isinstance(row.get("rekor_uuid"), str) or not row["rekor_uuid"]:
        raise Unusable("last root row: rekor_uuid must be a non-empty string")
    return row


def _entries(rekor: Any) -> dict:
    entries = rekor.get("entries") if isinstance(rekor, dict) else None
    if not isinstance(entries, dict):
        raise Unusable("rekor record: entries must be an object")
    for uuid, entry in entries.items():
        if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) for k in ("hash", "identity")):
            raise Unusable("rekor entry %r: hash and identity must be strings" % uuid)
    return entries


def verify(ledger: bytes, roots: bytes, rekor: Any, pin: str) -> dict:
    if not isinstance(pin, str) or not pin:
        raise Unusable("identity pin must be a non-empty string")
    current = root_of(tips(ledger))
    last = _last_root_row(roots)
    entries = _entries(rekor)
    reasons = []
    if current != last["root"]:
        reasons.append("root_mismatch")
    entry = entries.get(last["rekor_uuid"])
    if entry is None:
        reasons.append("entry_missing")
    else:
        if entry["hash"] != last["root"]:
            reasons.append("entry_root_mismatch")
        if entry["identity"] != pin:
            reasons.append("identity_mismatch")
    return {"valid": not reasons, "reasons": reasons}


# ---------------------------------------------------------------- the cycle (calls 10 -> 11)

def root_row(roots: bytes, row_id: str, ts: str, root: str, rekor_uuid: str) -> bytes:
    """``roots`` with one chained root row appended (RFC 8785 line, ``ledger.chain``)."""
    old = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(roots)]
    if not isinstance(row_id, str) or not row_id or any(r.get("row_id") == row_id for r in old):
        raise Unusable("root row_id must be a new non-empty string")
    if not isinstance(ts, str) or not ts:
        raise Unusable("root ts must be a non-empty string")
    row = {"row_id": row_id, "ts": ts, "root": _root_text(root), "rekor_uuid": rekor_uuid,
           "prev_hash": old[-1]["row_hash"] if old else chain.ZERO_HASH}
    row["row_hash"] = chain.row_hash(row)
    joint = b"\n" if roots and not roots.endswith(b"\n") else b""
    return roots + joint + chain.canonical(row) + b"\n"


def anchor_cycle(ledger: bytes, previous: bytes, roots: bytes, previous_roots: bytes,
                 read_request: Callable[[], bytes], signer: Any, state: Any, row_id: str, ts: str,
                 message: str = "ledger: one cycle, anchored root") -> dict:
    """One anchored cycle, one ``state.commit_files`` call; returns ``{row_hashes, root, entry}``."""
    verdict = chain.verify_bytes(roots, previous_roots)
    if not verdict["valid"]:
        raise append.HardStop("roots: %s (%s)" % (verdict["reason"], verdict["broken_row"]))
    cycle = append.plan_cycle(ledger, previous, read_request)
    root = root_of(tips(cycle.content))
    entry = anchor(root, signer)
    new_roots = root_row(roots, row_id, ts, root, entry["uuid"])
    state.commit_files({LEDGER_PATH: cycle.content, ROOTS_PATH: new_roots}, message)
    return {"row_hashes": cycle.row_hashes, "root": root, "entry": entry}


# ---------------------------------------------------------------- command line

USAGE = ("usage: python -m ledger.anchor root LEDGER | anchor SIGNER < {\"root\"} | "
         "verify LEDGER ROOTS REKOR < {\"identity\"}")
EMPTY = {"root": {"tips": None, "root": None},
         "anchor": {"ok": False, "hard_stop": False, "entry": None},
         "verify": {"valid": False, "reasons": []}}


def _read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def _json(data: bytes, what: str) -> Any:
    try:
        return chain.parse_row(data.decode("utf-8"))
    except (UnicodeDecodeError, chain.ChainError) as exc:
        raise Unusable("%s: %s" % (what, exc)) from None


def _stdin_value(key: str) -> Any:
    request = _json(sys.stdin.buffer.read(), "stdin")
    if set(request) != {key}:
        raise Unusable('stdin must be {"%s": ...} and nothing else' % key)
    return request[key]


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def main(argv: list[str]) -> int:
    command = argv[0] if argv else ""
    try:
        if command == "root" and len(argv) == 2:
            tip_map = tips(_read(argv[1]))
            _emit({"tips": tip_map, "root": root_of(tip_map)})
            return 0
        if command == "anchor" and len(argv) == 2:
            signer = FakeSigner.from_json(_json(_read(argv[1]), "signer"))
            root = _root_text(_stdin_value("root"))
            try:
                entry = anchor(root, signer)
            except Unsignable as exc:
                sys.stderr.write("hard stop: %s\n" % exc)
                _emit({"ok": False, "hard_stop": True, "entry": None})
                return 1
            _emit({"ok": True, "hard_stop": False, "entry": entry})
            return 0
        if command == "verify" and len(argv) == 4:
            ledger, roots, rekor = _read(argv[1]), _read(argv[2]), _json(_read(argv[3]), "rekor record")
            result = verify(ledger, roots, rekor, _stdin_value("identity"))
            _emit(result)
            return 0 if result["valid"] else 1
        command = ""
        raise Unusable(USAGE)
    except (Unusable, OSError, UnicodeDecodeError, chain.ChainError) as exc:
        sys.stderr.write("unusable input: %s\n" % exc)
    except Exception as exc:  # noqa: BLE001 - never a traceback, never exit 1 without a reason
        sys.stderr.write("internal error: %s: %s\n" % (type(exc).__name__, exc))
    _emit(EMPTY.get(command, {"error": "usage"}))
    return 2


def FAULT_LINE(argv: list[str]) -> dict:  # noqa: N802 - cli.run's fault line, by command
    return EMPTY.get(argv[0] if argv else "", {"error": "usage"})


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
