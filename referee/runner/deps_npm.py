"""``deps.fetch`` for npm: the lock is checked, every tarball is fetched and verified against the lock's
``integrity``, and the result is one content-addressed artifact with a license report (stage 0, MF5).

Rules: asama-0/06 (each tarball verified by ``integrity``; ``resolved`` on an allowed registry; git and
file dependencies refused; content-addressed output that every run takes by its hash; a package that
needs an install script is marked in the recipe), asama-0/09 test 34, tohum/24 and 26a (license report
written; the gate applies only to dependencies that enter the product), tohum/08 4 (scripts off: this
module never installs or runs anything), tohum/18a (``operating.deps_bytes``, ``license_allowlist``,
``license_exceptions``), tohum/29d (group ``npmlock``).

The lock (``check``, before anything is fetched; every reason listed as ``<reason>:<key>``):

- It must be a JSON object with ``lockfileVersion`` 2 or 3 and a ``packages`` object
  (``lock_unparsable``, ``lock_version_unsupported``). The ``dependencies`` section of a version 2 lock is
  not read; an installer that reads it (npm 6) is out of scope.
- The root entry ``""`` is skipped: the target's own package and its scripts are the target's code, run
  in ``koş``, not judged here. Every other key must be a chain of ``node_modules/<name>`` segments with npm
  name characters (``key_not_allowed``); so a workspace member (``packages/a``) is refused in stage 0.
- ``link: true``, a ``resolved`` or ``version`` that starts with ``file:``, or a non-empty ``resolved`` with
  no ``://`` is a file
  dependency (``file_dependency``); one that starts with ``git+``, ``git:``, ``git@``, ``github:``,
  ``gitlab:``, ``bitbucket:`` or ``gist:`` (casefolded) is a git dependency (``git_dependency``); a bundled
  entry (``inBundle: true``) is refused (``bundled_dependency``): its bytes come inside another tarball
  and are not judged on their own here.
- Otherwise ``resolved`` must be exactly ``https://<host><prefix><name>/-/<bare>-<version>.tgz`` for an
  allowed registry (scheme ``https``, an ASCII host ``[A-Za-z0-9.-]`` equal after lowercasing, so no user,
  port, query or fragment; path
  characters ``[A-Za-z0-9._~@/-]`` only, so no ``%``-escapes and no ``..``); ``<name>`` is the entry's
  ``name`` (an alias) or the last name of its key, ``<bare>`` its part after ``/``, ``<version>`` the
  entry's semver ``version``. A missing one is ``resolved_missing``, any other ``resolved_not_allowed``,
  a bad version ``version_invalid``. Allowed registries: ``--registry`` (repeatable; the profile's
  ``registry_egress``), default ``https://registry.npmjs.org/``.
- ``integrity`` is a space-separated SRI list: each token ``sha256-``, ``sha384-`` or ``sha512-`` plus
  strict base64 of the digest's length, or ``sha1-`` which is ignored as weak; any other token is
  ``integrity_malformed``. No strong token is ``integrity_weak``; none at all ``integrity_missing``.
- ``hasInstallScript: true`` needs the package marked in the recipe's ``install_scripts_required``
  (``install_script_not_marked``); a mark is the exact lock key or exactly ``name@version``.

The fetch (``fetch``), only when the lock passes: each distinct ``resolved`` is fetched once and every
strong ``integrity`` token must equal the bytes' digest (``integrity_mismatch``; one changed byte is
caught). A tarball that matches is read in memory, never extracted: it must be gzip tar
(``tarball_unreadable``) with exactly one regular member ``<top>/package.json`` (``tarball_no_package_json``,
``tarball_ambiguous_package_json``; at most 1 MiB, a JSON object, else ``tarball_package_json_unreadable``)
whose ``name`` and ``version`` equal the lock's (``tarball_manifest_mismatch``), and no member under
``<top>/node_modules/`` (``bundled_dependency``, as for a bundled lock entry). A ``preinstall``,
``install`` or ``postinstall`` key in its ``scripts``, or a ``<top>/binding.gyp`` member (npm's implicit
``node-gyp rebuild``), needs the same recipe mark as ``hasInstallScript``. The tarball's decompression
time is bounded only by the job's wall clock. ``operating.deps_bytes`` (from ``--policy``) bounds the
total bytes of distinct tarballs; going over it stops the fetch with ``limit_hit:deps_bytes``.

Licenses: every place in the tarball's ``package.json`` that states one (``license`` as a string or an
object's ``type``; each entry of ``licenses``) is listed in the report; license files are not read, and a
value of another type is listed as ``<unreadable>``. ``license_exceptions["name==version"].expression``
replaces the listed values. Without ``--product`` the report is written and nothing is gated (the
target's dependencies do not enter the product). With ``--product`` a package with no value is
``license_not_found`` and one with a value that is not allowed is ``license_not_allowed``. A value is
allowed when it is an SPDX expression of identifiers joined by ``AND``/``OR`` with parentheses and every
identifier is ASCII ``[A-Za-z0-9.+-]`` and in ``license_allowlist`` after lowercasing (operators are
case-sensitive; ``--policy`` replaces the 18a list): ``OR`` does not
let a listed identifier carry an unlisted one, ``WITH`` and ``+`` are not allowed unless listed as written.

The artifact, written only when nothing is refused: ``OUT/<address>/`` holding the lock under its own
name (``package-lock.json`` or ``npm-shrinkwrap.json``), ``tarballs/<sha512 hex>.tgz`` and
``manifest.json``, the canonical JSON (sorted keys, no spaces, ASCII) of the lock's sha256 and, per key,
name, version, resolved, integrity, sha512, bytes, the listed licenses and the install-script flag.
``address`` is the sha256 of ``manifest.json``'s bytes, so the same lock and tarballs give the same
address and a changed lock byte gives another. ``verify`` takes it by that hash: the manifest bytes must
hash to the address, each tarball must be a regular file with its sha512 and must match its
``integrity``, the lock copy must hash to ``lock_sha256``, and no other file may be there
(``unexpected_file``).

Fetching: ``--mirror DIR`` reads ``DIR/<host>/<path>`` (the referee's fixtures and tests); without it
the tarball is fetched over HTTPS with redirects refused and the read capped. The HTTPS path is not
exercised by the tests here (no network in the sandbox); its proof is asama-0/10a #getir. A tarball that
cannot be fetched is no verdict (exit 2), not a refusal: an outage says nothing about the lock.

Command line, run from ``referee/`` (one JSON line on stdout; exit 0 fine, 1 refused, 2 no verdict). Exit
1 comes only from a report with ``ok`` false; every other failure is exit 2 with an ``error`` line:
unusable input (a missing or non-JSON lock, recipe or policy, JSON nested too deeply, a value of the
wrong shape, a lock file not named as above, a fetch that failed, an existing artifact directory that
does not verify) and, as a last resort, any other exception (``internal error: <type>``). Out of scope:
signals and the interpreter being killed.

    python -m runner.deps_npm check LOCK [--registry URL]... [--recipe FILE]
    python -m runner.deps_npm fetch LOCK OUT [--mirror DIR] [--registry URL]... [--recipe FILE]
                                             [--policy FILE] [--product]
    python -m runner.deps_npm verify ARTIFACT_DIR [--address HEX]

``--recipe`` is a unit recipe (tohum/26c) whose ``install_scripts_required`` is read; ``--policy`` a
``policy.json``.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import os
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zlib
from typing import Any, Callable

DEFAULT_REGISTRIES = ("https://registry.npmjs.org/",)
LICENSE_ALLOWLIST = ("MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "Apache-2.0", "ISC", "PSF-2.0",
                     "Python-2.0", "Unlicense", "CC0-1.0", "Zlib", "MPL-2.0")
LOCK_NAMES = ("package-lock.json", "npm-shrinkwrap.json")
GIT_PREFIXES = ("git+", "git:", "git@", "github:", "gitlab:", "bitbucket:", "gist:")
INSTALL_SCRIPTS = ("preinstall", "install", "postinstall")
STRONG = {"sha256": 32, "sha384": 48, "sha512": 64}
PACKAGE_JSON_MAX = 1 << 20
SCHEMA = "snowball-deps-npm/1"

_SEG = r"[A-Za-z0-9~-][A-Za-z0-9._~-]*"
_NAME = r"(?:@%s/)?%s" % (_SEG, _SEG)
NAME_RE = re.compile(_NAME)
LOCK_PATH_RE = re.compile(r"(?:node_modules/%s/)*node_modules/(%s)" % (_NAME, _NAME))
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")
PATH_CHARS = re.compile(r"[A-Za-z0-9._~@/-]*")
HOST_RE = re.compile(r"[A-Za-z0-9.-]+")
LICENSE_ID = re.compile(r"[A-Za-z0-9.+-]+")
B64_RE = re.compile(r"[A-Za-z0-9+/]+={0,2}")


class DepsError(ValueError):
    """Unusable input or a failed fetch: no verdict (exit 2)."""


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


# ---------------------------------------------------------------- lock

def _registries(urls) -> list[tuple[str, str]]:
    out = []
    for url in urls:
        if not isinstance(url, str):
            raise DepsError("registry is not a string")
        parts = urllib.parse.urlsplit(url)
        if (parts.scheme != "https" or not HOST_RE.fullmatch(parts.netloc) or parts.port is not None
                or parts.query or parts.fragment or "@" in parts.netloc or not PATH_CHARS.fullmatch(parts.path)
                or ".." in parts.path.split("/")):
            raise DepsError("registry not usable: %r" % url)
        prefix = parts.path if parts.path.endswith("/") else parts.path + "/"
        out.append((parts.netloc.lower(), prefix))
    return out


def parse_integrity(value: Any) -> tuple[str | None, list[tuple[str, bytes]]]:
    """``(reason or None, strong (algorithm, digest) pairs)``."""
    if not isinstance(value, str) or not value.strip():
        return "integrity_missing", []
    strong = []
    for word in value.split():
        alg, sep, b64 = word.partition("-")
        if not sep or not B64_RE.fullmatch(b64):
            return "integrity_malformed", []
        if alg == "sha1":
            continue
        if alg not in STRONG:
            return "integrity_malformed", []
        try:
            digest = base64.b64decode(b64, validate=True)
        except (binascii.Error, ValueError):
            return "integrity_malformed", []
        if len(digest) != STRONG[alg]:
            return "integrity_malformed", []
        strong.append((alg, digest))
    if not strong:
        return "integrity_weak", []
    return None, strong


def _marked(marks: list[str], key: str, name: str, version: Any) -> bool:
    return key in marks or (isinstance(version, str) and "%s@%s" % (name, version) in marks)


def _source_reason(entry: dict) -> str | None:
    if entry.get("link") is True:
        return "file_dependency"
    if entry.get("inBundle") is True:
        return "bundled_dependency"
    for field in ("resolved", "version"):
        value = entry.get(field)
        if not isinstance(value, str):
            continue
        low = value.casefold()
        if low.startswith(GIT_PREFIXES):
            return "git_dependency"
        if low.startswith("file:") or (field == "resolved" and value and "://" not in value):
            return "file_dependency"
    return None


def _resolved_reason(entry: dict, name: str, registries: list[tuple[str, str]]) -> str | None:
    resolved = entry.get("resolved")
    if not isinstance(resolved, str) or not resolved:
        return "resolved_missing"
    version = entry["version"]
    parts = urllib.parse.urlsplit(resolved)
    if (parts.scheme != "https" or "?" in resolved or "#" in resolved or not HOST_RE.fullmatch(parts.netloc)
            or not PATH_CHARS.fullmatch(parts.path)):
        return "resolved_not_allowed"
    bare = name.split("/")[-1]
    for host, prefix in registries:
        if parts.netloc.lower() == host and parts.path == "%s%s/-/%s-%s.tgz" % (prefix, name, bare, version):
            return None
    return "resolved_not_allowed"


def entries(lock: Any) -> tuple[list[str], list[dict]]:
    """Lock structure: ``(reasons, [{key, name, version, resolved, integrity, strong, entry}])``."""
    if not isinstance(lock, dict):
        return ["lock_unparsable"], []
    if lock.get("lockfileVersion") not in (2, 3) or isinstance(lock.get("lockfileVersion"), bool):
        return ["lock_version_unsupported"], []
    packages = lock.get("packages")
    if not isinstance(packages, dict):
        return ["lock_version_unsupported"], []
    reasons, out = [], []
    for key in sorted(packages):
        entry = packages[key]
        if key == "":
            continue
        m = LOCK_PATH_RE.fullmatch(key)
        if not m or not isinstance(entry, dict):
            reasons.append("key_not_allowed:%s" % key)
            continue
        name = entry.get("name", m.group(1))
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            reasons.append("key_not_allowed:%s" % key)
            continue
        out.append({"key": key, "name": name, "entry": entry})
    return reasons, out


def check(lock: Any, registries=DEFAULT_REGISTRIES, marks: list[str] | None = None) -> dict:
    """The static check of the lock; nothing is fetched."""
    regs = _registries(registries)
    marks = list(marks or [])
    reasons, items = entries(lock)
    for item in items:
        key, entry = item["key"], item["entry"]
        source = _source_reason(entry)
        if source:
            reasons.append("%s:%s" % (source, key))
            continue
        version = entry.get("version")
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            reasons.append("version_invalid:%s" % key)
            continue
        resolved = _resolved_reason(entry, item["name"], regs)
        if resolved:
            reasons.append("%s:%s" % (resolved, key))
        bad, item["strong"] = parse_integrity(entry.get("integrity"))
        if bad:
            reasons.append("%s:%s" % (bad, key))
        if entry.get("hasInstallScript") is True and not _marked(marks, key, item["name"], version):
            reasons.append("install_script_not_marked:%s" % key)
    return {"ok": not reasons, "reasons": reasons, "items": items}


# ---------------------------------------------------------------- tarball

def integrity_matches(data: bytes, strong: list[tuple[str, bytes]]) -> bool:
    return bool(strong) and all(hashlib.new(alg, data).digest() == digest for alg, digest in strong)


def inspect_tarball(data: bytes) -> tuple[str | None, dict]:
    """``(reason or None, {manifest, binding_gyp})``, read in memory, nothing extracted."""
    found, gyp = [], False
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar:
                parts = [p for p in member.name.split("/") if p not in ("", ".")]
                if len(parts) >= 2 and parts[1] == "node_modules":
                    return "bundled_dependency", {}
                if len(parts) != 2:
                    continue
                if parts[1] == "binding.gyp":
                    gyp = True
                if parts[1] == "package.json":
                    if not member.isfile():
                        return "tarball_no_package_json", {}
                    if member.size > PACKAGE_JSON_MAX:
                        return "tarball_package_json_unreadable", {}
                    fh = tar.extractfile(member)
                    found.append(fh.read(PACKAGE_JSON_MAX + 1) if fh else b"")
    except (tarfile.TarError, EOFError, zlib.error, OSError):
        return "tarball_unreadable", {}
    if not found:
        return "tarball_no_package_json", {}
    if len(found) > 1:
        return "tarball_ambiguous_package_json", {}
    try:
        manifest = json.loads(found[0].decode("utf-8"))
    except (ValueError, RecursionError):
        return "tarball_package_json_unreadable", {}
    if not isinstance(manifest, dict):
        return "tarball_package_json_unreadable", {}
    return None, {"manifest": manifest, "binding_gyp": gyp}


def licenses_of(manifest: dict) -> list[str]:
    out = []
    lic = manifest.get("license")
    if lic is not None:
        if isinstance(lic, str):
            out.append(lic)
        elif isinstance(lic, dict) and isinstance(lic.get("type"), str):
            out.append(lic["type"])
        else:
            out.append("<unreadable>")
    lics = manifest.get("licenses")
    if lics is not None:
        if not isinstance(lics, list):
            out.append("<unreadable>")
        for one in lics if isinstance(lics, list) else []:
            if isinstance(one, str):
                out.append(one)
            elif isinstance(one, dict) and isinstance(one.get("type"), str):
                out.append(one["type"])
            else:
                out.append("<unreadable>")
    return out


def expression_allowed(expr: str, allowlist) -> bool:
    allowed = {a.lower() for a in allowlist}
    words = re.findall(r"\(|\)|[^\s()]+", expr)
    pos = 0

    def term() -> bool:
        nonlocal pos
        if pos >= len(words):
            return False
        word = words[pos]
        pos += 1
        if word == "(":
            if not expression() or pos >= len(words) or words[pos] != ")":
                return False
            pos += 1
            return True
        return (word not in ("AND", "OR", "WITH") and LICENSE_ID.fullmatch(word) is not None
                and word.lower() in allowed)

    def expression() -> bool:
        nonlocal pos
        if not term():
            return False
        while pos < len(words) and words[pos] in ("AND", "OR"):
            pos += 1
            if not term():
                return False
        return True

    if len(words) > 512 or words.count("(") > 64:
        return False
    return expression() and pos == len(words)


def licenses_allowed(values: list[str], allowlist) -> bool:
    return bool(values) and all(expression_allowed(v, allowlist) for v in values)


# ---------------------------------------------------------------- fetch

def mirror_fetcher(root: str) -> Callable[[str, int | None], bytes]:
    def fetch(url: str, cap: int | None) -> bytes:
        parts = urllib.parse.urlsplit(url)
        path = os.path.join(root, parts.netloc.lower(), *[p for p in parts.path.split("/") if p])
        try:
            with open(path, "rb") as fh:
                return fh.read() if cap is None else fh.read(cap + 1)
        except OSError as exc:
            raise DepsError("fetch failed: %s: %s" % (url, exc.strerror or exc)) from None
    return fetch


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DepsError("fetch failed: %s: redirect refused" % req.full_url)


def https_fetcher(url: str, cap: int | None) -> bytes:  # pragma: no cover - needs the network (10a #getir)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(url, timeout=60) as resp:
            if resp.status != 200:
                raise DepsError("fetch failed: %s: HTTP %s" % (url, resp.status))
            return resp.read() if cap is None else resp.read(cap + 1)
    except OSError as exc:
        raise DepsError("fetch failed: %s: %s" % (url, exc)) from None


def _policy_values(policy: Any) -> tuple[list[str], dict, int | None]:
    if policy is None:
        return list(LICENSE_ALLOWLIST), {}, None
    if not isinstance(policy, dict):
        raise DepsError("policy is not an object")
    const = policy.get("constitutional", {})
    operating = policy.get("operating", {})
    if not isinstance(const, dict) or not isinstance(operating, dict):
        raise DepsError("policy constitutional or operating is not an object")
    allow = const.get("license_allowlist", list(LICENSE_ALLOWLIST))
    if not isinstance(allow, list) or not all(isinstance(a, str) for a in allow):
        raise DepsError("license_allowlist is not a list of strings")
    exceptions = const.get("license_exceptions", {})
    if not isinstance(exceptions, dict) or not all(
            isinstance(v, dict) and isinstance(v.get("expression"), str) for v in exceptions.values()):
        raise DepsError("license_exceptions is not {name==version: {expression, evidence}}")
    limit = None
    if "deps_bytes" in operating:
        value = operating["deps_bytes"].get("value") if isinstance(operating["deps_bytes"], dict) else None
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise DepsError("operating.deps_bytes.value is not a non-negative integer")
        limit = value
    return allow, exceptions, limit


def fetch(lock_path: str, out: str, fetcher: Callable[[str, int | None], bytes], registries=DEFAULT_REGISTRIES,
          marks: list[str] | None = None, policy: Any = None, product: bool = False) -> dict:
    name = os.path.basename(lock_path)
    if name not in LOCK_NAMES:
        raise DepsError("lock file must be named %s" % " or ".join(LOCK_NAMES))
    allow, exceptions, limit = _policy_values(policy)
    lock_bytes = _read(lock_path)
    lock = _parse(lock_bytes, lock_path)
    report = check(lock, registries, marks)
    if not report["ok"]:
        return {"ok": False, "reasons": report["reasons"]}
    reasons, blobs, total = [], {}, 0
    for item in report["items"]:
        url = item["entry"]["resolved"]
        if url not in blobs:
            data = fetcher(url, None if limit is None else limit - total)
            total += len(data)
            if limit is not None and total > limit:
                return {"ok": False, "reasons": ["limit_hit:deps_bytes"]}
            blobs[url] = data
        if not integrity_matches(blobs[url], item["strong"]):
            reasons.append("integrity_mismatch:%s" % item["key"])
    if reasons:
        return {"ok": False, "reasons": reasons}
    rows, licenses = [], []
    for item in report["items"]:
        key, entry, data = item["key"], item["entry"], blobs[item["entry"]["resolved"]]
        bad, info = inspect_tarball(data)
        if bad:
            reasons.append("%s:%s" % (bad, key))
            continue
        manifest = info["manifest"]
        if manifest.get("name") != item["name"] or manifest.get("version") != entry["version"]:
            reasons.append("tarball_manifest_mismatch:%s" % key)
            continue
        scripts = manifest.get("scripts")
        script = info["binding_gyp"] or entry.get("hasInstallScript") is True or (
            isinstance(scripts, dict) and any(s in scripts for s in INSTALL_SCRIPTS))
        if script and not _marked(list(marks or []), key, item["name"], entry["version"]):
            reasons.append("install_script_not_marked:%s" % key)
        found = licenses_of(manifest)
        pinned = "%s==%s" % (item["name"], entry["version"])
        values = [exceptions[pinned]["expression"]] if pinned in exceptions else found
        ok = licenses_allowed(values, allow)
        licenses.append({"key": key, "name": item["name"], "version": entry["version"], "license": values,
                         "allowed": ok})
        if product and not ok:
            reasons.append("%s:%s" % ("license_not_allowed" if values else "license_not_found", key))
        rows.append({"key": key, "name": item["name"], "version": entry["version"], "resolved": entry["resolved"],
                     "integrity": entry["integrity"], "sha512": hashlib.sha512(data).hexdigest(),
                     "bytes": len(data), "license": found, "install_script": bool(script)})
    if reasons:
        return {"ok": False, "reasons": reasons}
    manifest_obj = {"schema": SCHEMA, "lock": name, "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
                    "packages": rows}
    manifest_bytes = canonical(manifest_obj)
    address = hashlib.sha256(manifest_bytes).hexdigest()
    _write_artifact(out, address, name, lock_bytes, manifest_bytes, blobs)
    return {"ok": True, "reasons": [], "address": address, "packages": len(rows),
            "bytes": sum(len(b) for b in blobs.values()), "licenses": licenses}


def _write_artifact(out: str, address: str, lock_name: str, lock_bytes: bytes, manifest_bytes: bytes,
                    blobs: dict) -> None:
    final = os.path.join(out, address)
    if os.path.lexists(final):
        if not verify(final, address)["ok"]:
            raise DepsError("existing artifact %s does not verify" % address)
        return
    tmp = tempfile.mkdtemp(prefix=".tmp-", dir=out)
    try:
        os.mkdir(os.path.join(tmp, "tarballs"))
        for data in blobs.values():
            with open(os.path.join(tmp, "tarballs", hashlib.sha512(data).hexdigest() + ".tgz"), "wb") as fh:
                fh.write(data)
        with open(os.path.join(tmp, lock_name), "wb") as fh:
            fh.write(lock_bytes)
        with open(os.path.join(tmp, "manifest.json"), "wb") as fh:
            fh.write(manifest_bytes)
        os.rename(tmp, final)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


# ---------------------------------------------------------------- verify

def _regular(path: str) -> bytes | None:
    try:
        st = os.lstat(path)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def verify(directory: str, address: str | None = None) -> dict:
    """Take an artifact by its hash: ``{ok, reasons, address}``."""
    address = address if address is not None else os.path.basename(os.path.normpath(directory))
    data = _regular(os.path.join(directory, "manifest.json"))
    if data is None:
        return {"ok": False, "reasons": ["manifest_missing"], "address": address}
    if hashlib.sha256(data).hexdigest() != address:
        return {"ok": False, "reasons": ["address_mismatch"], "address": address}
    try:
        manifest = json.loads(data.decode("ascii"))
        lock_name, packages = manifest["lock"], manifest["packages"]
        expected = {"manifest.json", lock_name, "tarballs"}
        if lock_name not in LOCK_NAMES or manifest.get("schema") != SCHEMA:
            raise ValueError
    except (ValueError, KeyError, TypeError, RecursionError):
        return {"ok": False, "reasons": ["manifest_unreadable"], "address": address}
    reasons = []
    lock = _regular(os.path.join(directory, lock_name))
    if lock is None or hashlib.sha256(lock).hexdigest() != manifest.get("lock_sha256"):
        reasons.append("lock_mismatch")
    tarballs = set()
    for row in packages if isinstance(packages, list) else [None]:
        try:
            fname = row["sha512"] + ".tgz"
            if not re.fullmatch(r"[0-9a-f]{128}\.tgz", fname):
                raise ValueError
            _, strong = parse_integrity(row["integrity"])
        except (TypeError, KeyError, ValueError):
            reasons.append("manifest_unreadable")
            continue
        tarballs.add(fname)
        blob = _regular(os.path.join(directory, "tarballs", fname))
        if blob is None or hashlib.sha512(blob).hexdigest() != row["sha512"]:
            reasons.append("tarball_mismatch:%s" % row.get("key"))
        elif not integrity_matches(blob, strong):
            reasons.append("integrity_mismatch:%s" % row.get("key"))
    try:
        present = set(os.listdir(directory))
        extra = sorted(present - expected)
        tdir = os.path.join(directory, "tarballs")
        if os.path.islink(tdir) or not os.path.isdir(tdir):
            reasons.append("unexpected_file:tarballs")
        else:
            extra += sorted("tarballs/" + n for n in set(os.listdir(tdir)) - tarballs)
    except OSError:
        extra = ["<unlistable>"]
    reasons += ["unexpected_file:%s" % n for n in extra]
    return {"ok": not reasons, "reasons": reasons, "address": address}


# ---------------------------------------------------------------- command line

def _read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def _parse(data: bytes, path: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except RecursionError:
        raise DepsError("%s: JSON nested too deeply" % path) from None
    except (UnicodeDecodeError, ValueError) as exc:
        raise DepsError("%s: not JSON: %s" % (path, exc)) from None


def _marks(recipe: Any) -> list[str]:
    if recipe is None:
        return []
    marks = recipe.get("install_scripts_required", []) if isinstance(recipe, dict) else None
    if not isinstance(marks, list) or not all(isinstance(m, str) for m in marks):
        raise DepsError("recipe install_scripts_required is not a list of strings")
    return marks


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


USAGE = ("usage: python -m runner.deps_npm check LOCK [--registry URL]... [--recipe FILE] | fetch LOCK OUT "
         "[--mirror DIR] [--registry URL]... [--recipe FILE] [--policy FILE] [--product] | verify DIR [--address HEX]")


def main(argv: list[str]) -> int:
    try:
        args, opts, regs = [], {}, []
        it = iter(argv)
        for a in it:
            if a in ("--registry", "--recipe", "--policy", "--mirror", "--address"):
                value = next(it, None)
                if value is None:
                    raise DepsError("%s needs a value" % a)
                if a == "--registry":
                    regs.append(value)
                elif a in opts:
                    raise DepsError("%s given twice" % a)
                else:
                    opts[a] = value
            elif a == "--product":
                opts[a] = True
            else:
                args.append(a)
        registries = regs or list(DEFAULT_REGISTRIES)
        recipe = _parse(_read(opts["--recipe"]), opts["--recipe"]) if "--recipe" in opts else None
        policy = _parse(_read(opts["--policy"]), opts["--policy"]) if "--policy" in opts else None
        if len(args) == 2 and args[0] == "check" and not ({"--policy", "--mirror", "--address", "--product"} & set(opts)):
            report = check(_parse(_read(args[1]), args[1]), registries, _marks(recipe))
            _emit({"ok": report["ok"], "reasons": report["reasons"]})
            return 0 if report["ok"] else 1
        if len(args) == 3 and args[0] == "fetch" and "--address" not in opts:
            fetcher = mirror_fetcher(opts["--mirror"]) if "--mirror" in opts else https_fetcher
            report = fetch(args[1], args[2], fetcher, registries, _marks(recipe), policy, "--product" in opts)
            _emit(report)
            return 0 if report["ok"] else 1
        if len(args) == 2 and args[0] == "verify" and set(opts) <= {"--address"} and not regs:
            report = verify(args[1], opts.get("--address"))
            _emit(report)
            return 0 if report["ok"] else 1
        _emit({"error": USAGE})
        return 2
    except (DepsError, ValueError, OSError) as exc:
        _emit({"error": "unusable input: %s" % exc})
        return 2
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a refusal
        _emit({"error": "internal error: %s: %s" % (type(exc).__name__, exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
