"""``unit.verify``: a unit recipe is checked statically, then its lint and service-free tests run 3/3 at
HEAD with only the recipe's ``inputs`` and the fetched dependencies, contained and without network
(stage 0, MF6).

Rules: tohum/14 and 26c (the recipe ``{unit_id, path, inputs[], toolchain, env_image (@sha256),
lockfiles[], install_scripts_required[], lint_cmd[], test_cmd[], affected_test_cmd[], services: [],
limits{}}``; ``inputs`` are proven sufficient only by a 3/3 green run with those inputs alone; the image
is the official toolchain image of the version in the repository's version file; ``services`` empty in
stage 0), tohum/26a (``unit.verify``: recipe, tree and ``deps`` in; verified recipe or refusal and the
3/3 results out; ``limit_hit:<key>``), asama-0/06 (only the unit's ``inputs`` enter the worktree; the
container installs the dependencies without network and without scripts; a marked package's script runs
in ``koş`` without network), asama-0/08 criterion 6 and unit criteria 4 and 5, asama-0/09 test 48, tohum/18a
(``operating{}``), tohum/29d and 29g (group ``recipe``: ``vector_check`` below). It calls
``runner.lint_record`` (step 6), MF3 (``runner.contained``), MF5 (``runner.deps_npm``) and MF4
(``profile.derive``: the recipe's path and inputs against the derivation, the exclusions while the inputs are
copied, and criterion 5's coverage).

``verify``'s static check (``check_recipe``; every reason listed):

- Fields: every recipe field is required (``missing:<field>``), no other field is allowed
  (``field_not_in_recipe:<field>``).
- ``unit_id`` ``[A-Za-z0-9][A-Za-z0-9._-]{0,127}``; ``path`` and every input a relative path inside the
  tree (``invalid:<field>``); some input covers ``path`` (``inputs_miss_unit_path``); no input is or holds
  ``.snowball``, the verifier's own directory in the worktree (``reserved_path``).
- ``toolchain`` is exactly ``node@X.Y.Z`` (stage 0 has one ecosystem, npm; ``invalid:toolchain``).
- ``env_image`` is pinned by digest as ``run.contained`` requires (``image_not_pinned``), its repository is
  the official one, ``node`` or ``docker.io/library/node`` (``image_not_official``), and its tag is
  ``X.Y.Z`` or ``X.Y.Z-<variant>`` with the toolchain's version (``image_version_mismatch``).
- ``lockfiles`` is exactly one path named ``package-lock.json`` or ``npm-shrinkwrap.json``
  (``invalid:lockfiles``), covered by an input (``lockfile_not_in_inputs``), in the unit's directory or
  one of its ancestors (``lockfile_not_for_unit``).
- ``install_scripts_required`` a list of strings (their form is MF5's: exact lock key or ``name@version``).
- ``lint_cmd``, ``test_cmd`` and ``affected_test_cmd`` non-empty lists of non-empty strings without NUL
  (``invalid:<field>``; an empty ``affected_test_cmd`` is refused as group ``recipe`` refuses it,
  tohum/29g). ``affected_test_cmd`` is not run here (stage 0's affected set is the unit's whole
  service-free test set, asama-0/08 item 6).
- ``services`` is ``[]`` (``services_not_empty``).
- ``limits`` an object whose keys are ``operating{}`` keys (``limit_key_unknown:<key>``) and whose values are
  positive integers (``invalid:limits.<key>``); given the policy's ``operating``, a value may tighten the
  operator's value but not loosen it (``limit_above_operating:<key>``) and stays inside the band
  (``limit_below_band:<key>``). The run uses the smaller of the two.
- With the tree: ``profile.derive check`` of ``{units: [recipe]}`` (reasons prefixed ``profile:``: the path
  is an eligible candidate, inputs not excluded, present, not behind a symlink); the version file
  nearest to the unit's directory (walking up to the root; in one directory ``.nvmrc``, then
  ``.node-version``, then a ``node``/``nodejs`` line of ``.tool-versions``) must exist
  (``version_file_missing``), name an exact ``X.Y.Z`` with an optional leading ``v``
  (``version_file_not_exact``) and equal the toolchain's (``toolchain_version_mismatch``); the lock must be
  a regular file with no symlink on its way (``lockfile_missing``) and pass MF5's static check with the
  recipe's marks (``lock:<reason>``).

The run (``verify``), only when the static check passes:

1. Worktree. The inputs are copied from the tree into a fresh staging directory, topmost input first,
   without following symlinks (a symlink is copied as a symlink; its target is not; a FIFO, socket or
   device is not copied); an entry the
   derivation excludes (agent configuration, excluded directory names such as ``node_modules``, the
   operator's ``excluded_paths``) and ``.git`` are left out even under an input such as ``.``. Their
   regular files' bytes above ``unit_inputs_bytes`` stop the run (``limit_hit:unit_inputs_bytes``).
2. Dependencies. The ``deps`` artifact is taken by its address (MF5 ``verify``); its lock must be the
   tree's lock byte for byte (``deps_lock_mismatch``). Each manifest row's tarball is unpacked, by the
   referee and without running anything, into ``<lock dir>/<lock key>/`` with its first path component
   dropped: directories and regular files only (files 0644, or 0755 when the member has an execute
   bit); symbolic and hard links and other member types are skipped, as npm does; a member name that is
   absolute or holds ``..``, or a destination with a symlink or a non-directory on its way, refuses the
   artifact (``deps_unpack_unsafe:<key>``); unpacked bytes are bounded by ``worktree_bytes``. Then for
   each package whose ``package.json`` has ``bin`` (a string, named after the package's bare name, or an
   object), a relative symlink ``<parent node_modules>/.bin/<name>`` to the target inside the package is
   made, the first in lock-key order winning; a bin name outside ``[A-Za-z0-9._-]`` or a target leaving
   the package is skipped. Out of scope: ``directories.bin``, man pages, npm's own install logic, and a
   bound on the number of members (only their bytes are bounded; time is bounded by the job's clock). A lock
   with no package needs no artifact; one with packages and no artifact is unusable input.
3. Install scripts. When a row is flagged ``install_script`` (marked in the recipe, checked by MF5), one
   contained run of ``npm --prefix /work/<lock dir> rebuild --offline --foreground-scripts <names>``
   precedes the runs, and its worktree is the start of every run; it must exit 0
   (``install_scripts_failed``). Whether npm and node-gyp succeed in the real image is not proven here
   (no node in the referee's sandbox); its proof is asama-0/10a #birim.
4. 3/3. Three attempts, each running ``lint_cmd`` and then ``test_cmd``, every command in its own fresh
   contained run (MF3: no network, read-only root, the image, limits) of the same worktree, working
   directory ``/work`` (the tree's root), with ``HOME`` and ``TMPDIR`` under ``/work/.snowball``,
   ``CI=true``, ``npm_config_offline=true``, and the caller's red control in the same image. Tests are
   green when the exit code is 0 (``test_red:<attempt>``). Lint is green when the exit code is 0 or 1
   (ESLint's: 1 means findings, which asama-0/08 criterion 5 requires; 2 and others are failures,
   ``lint_failed:<attempt>``) and the three runs give the same exit code and the same stdout bytes
   (``lint_not_deterministic``). An insufficient ``inputs`` closure shows here, as a red or failing
   run; the verifier does not tell it apart from a failing test.
5. Limits. ``test_total_s`` caps the wall clock of each attempt's ``test_cmd``: the runner's timeout is the
   smaller of it and ``kos_wall_s``, and a test command stopped by that cap is ``limit_hit:test_total_s``.
   ``run.contained``'s own limits apply to every run (``limit_hit:kos_wall_s``, ``worktree_bytes``,
   ``output_bytes``; container memory).
6. The lint output, only when 1-5 left no reason (asama-0/08's unit selection, bold criteria 4 and 5). Each
   lint run's stdout, with the worktree it read, becomes a run record (``runner.lint_record``: ESLint's
   ``--format json`` only; its refusals are ``lint_output:<reason>``, e.g. a parse error ``fatal:<path>``).
   Criterion 5: some violation of the first record has a ``fix`` and a path that a ``security_paths``,
   ``excluded_dirs`` or ``excluded_paths`` entry of the derivation does not cover and an ``inputs`` entry
   does (29f coverage, as written); else ``no_fixable_violation``. Configuration, manifest and lock files
   count here although the gate refuses a candidate that changes them (MF7's rule, not called here).

Verdicts: ``verified`` (the recipe, its sha256 over canonical JSON, the deps address, every run's
results, and ``lint_records``: the three runs' records, the ratchet base's run file once written by
``lint_record.run_file``); ``refused`` (a reason about the recipe or the unit: static reasons, ``lock:``,
``install_scripts_failed``, ``test_red``, ``lint_failed``, ``lint_not_deterministic``, ``lint_output:``,
``no_fixable_violation``); ``no_verdict``
(nothing is learned about the recipe: ``limit_hit:<key>`` -- a limit is the operator's, not counted to the
Founder, tohum/18a --, an invalid contained run such as ``red_control_green``, ``red_control_fault``,
``runner_fault``, ``breach:in_changed``, ``unreadable_output``, or a ``deps`` artifact that does not verify,
``deps:<reason>``, or does not belong to the tree's lock, or cannot be unpacked safely). Out of scope:
asama-0/08 unit criterion 7 (churn) and whether the tests are "well tested".

Group ``recipe``'s check (``vector_check``, tohum/29g; no tree, nothing run) is a separate, narrower
check than ``check_recipe``: it emits only these reasons, every applicable one, sorted in code point
order, ``<input>`` and ``<key>`` as written in the recipe:

- ``image_not_pinned``: ``env_image`` (any value, missing included) is not ``<ref>@sha256:<64 lowercase
  hex>`` (``run.contained``'s image rule);
- ``inputs_missing_unit``: no input covers ``path`` (tohum/29f coverage: ``p == e.rstrip('/')`` or ``p``
  starts with ``e.rstrip('/') + '/'``, case-sensitive, as written);
- ``input_not_plain:<input>``: the input is absolute, holds ``\\`` or has a ``.`` or ``..`` component
  (``.`` itself included);
- ``input_excluded:<input>``: the input itself is agent configuration (tohum/29f, case-insensitive: a
  component ``.claude``, ``.vscode`` or ``.devcontainer``, or the last component, trailing ``/`` ignored,
  ``CLAUDE.md``, ``AGENTS.md``, ``.mcp.json`` or ``.envrc``);
- ``cmd_empty:<field>``: ``lint_cmd``, ``test_cmd`` or ``affected_test_cmd`` is missing, not a list, empty,
  or holds a non-string or an empty string;
- ``limit_key_unknown:<key>``: a ``limits`` key is not a key of ``policy.operating`` (values not looked at);
- ``services_not_empty``: ``services`` is not ``[]`` (missing included).

Unusable input there (exit 2): a file missing or not JSON, ``recipe`` not an object, ``policy`` not
``{operating: {...}}``, ``path`` not a string, ``inputs`` not a list of strings, ``limits`` not an
object. Other recipe fields are not looked at.

Command line, run from ``referee/``, no stdin; the last stdout line is one JSON line. ``check``: ``{ok,
reasons}``, exit 0 when ``reasons`` is empty, else 1. ``verify``: the report, exit 0 verified, 1 refused, 2
no verdict. Unusable input (missing or non-JSON files, JSON nested too deeply, wrong shapes, a policy
without the needed ``operating`` keys) and, as a last resort, any other exception (``internal error:
<type>``) are exit 2 with ``{ok: false, error}``. Out of scope: signals and the interpreter being killed.

    python -m profile.unit_verify check RECIPE POLICY
    python -m profile.unit_verify verify FILE

``FILE`` is ``{recipe, tree, policy, red_control: {cmd}, deps?, target?, base?}``: ``recipe`` and
``policy`` objects, ``tree`` the HEAD tree, ``deps`` an MF5 artifact directory (its name is its address),
``target`` the ``targets[]`` entry, ``base`` where fresh run directories go. It runs docker.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import time
import zlib
from typing import Any

from profile import derive as D
from runner import contained as C
from runner import deps_npm as N
from runner import lint_record as R

RECIPE_FIELDS = D.RECIPE_FIELDS
OPERATING_NAMES = ("unit_inputs_bytes", "deps_bytes", "worktree_bytes", "container_mem_bytes", "kos_wall_s",
                  "test_total_s", "output_bytes")
RUN_LIMIT_NAMES = ("unit_inputs_bytes", "worktree_bytes", "container_mem_bytes", "kos_wall_s", "test_total_s",
            "output_bytes")
UNIT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
TOOLCHAIN = re.compile(r"node@([0-9]+\.[0-9]+\.[0-9]+)")
VERSION_TEXT = re.compile(r"v?([0-9]+\.[0-9]+\.[0-9]+)")
OFFICIAL_REPOS = ("node", "docker.io/library/node")
IMAGE_SHAPE = re.compile(r"(?P<repo>[^@]+?)(?::(?P<tag>[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}))?@sha256:[0-9a-f]{64}")
CMD_FIELDS = ("lint_cmd", "test_cmd", "affected_test_cmd")
BIN_NAME = re.compile(r"[A-Za-z0-9._-]+")
RESERVED = ".snowball"
ATTEMPTS = 3
LINT_OK_EXITS = (0, 1)
ENV = {"HOME": "/work/.snowball/home", "TMPDIR": "/work/.snowball/tmp", "CI": "true",
       "npm_config_offline": "true"}
NO_VERDICT_PREFIXES = ("limit_hit:", "deps:", "deps_lock_mismatch", "deps_unpack_unsafe", "red_control_",
                       "runner_fault", "breach:", "unreadable_output")


class VerifyError(ValueError):
    """Unusable input: no verdict (exit 2)."""


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


# ---------------------------------------------------------------- static check

def _argv_ok(value: Any) -> bool:
    return (isinstance(value, list) and bool(value)
            and all(isinstance(v, str) and v and "\x00" not in v for v in value))


def _operating(policy: Any, keys) -> dict:
    """``{key: (value, band)}`` for ``keys`` from ``policy.operating``; each must be valid (MF3's rule)."""
    operating = policy.get("operating") if isinstance(policy, dict) else None
    try:
        values = C.limits(operating, tuple(keys))
    except C.ContainmentError as exc:
        raise VerifyError("policy: %s" % exc) from None
    return {k: (values[k], operating[k]["band"]) for k in keys}


def vector_check(recipe: Any, policy: Any) -> list[str]:
    """Group ``recipe``'s static check (tohum/29g): the sorted reasons; see ``check`` in the module docstring.

    Raises ``VerifyError`` (unusable input) when ``recipe`` or ``policy.operating`` is not an object, or
    ``path``, ``inputs`` (a list of strings) or ``limits`` (an object) is missing or of another type."""
    if not isinstance(recipe, dict):
        raise VerifyError("recipe is not an object")
    operating = policy.get("operating") if isinstance(policy, dict) else None
    if not isinstance(operating, dict):
        raise VerifyError("policy must be {operating: {key: {value, band}}}")
    path, inputs, limits = recipe.get("path"), recipe.get("inputs"), recipe.get("limits")
    if not isinstance(path, str):
        raise VerifyError("recipe.path must be a string")
    if not (isinstance(inputs, list) and all(isinstance(e, str) for e in inputs)):
        raise VerifyError("recipe.inputs must be a list of strings")
    if not isinstance(limits, dict):
        raise VerifyError("recipe.limits must be an object")
    reasons = set()
    image = recipe.get("env_image")
    if not (isinstance(image, str) and C.IMAGE.match(image)):
        reasons.add("image_not_pinned")
    if not any(D.covers_as_written(e, path) for e in inputs):
        reasons.add("inputs_missing_unit")
    for e in inputs:
        if e.startswith("/") or "\\" in e or any(p in (".", "..") for p in e.split("/")):
            reasons.add("input_not_plain:%s" % e)
        if D.agent_config_as_written(e):
            reasons.add("input_excluded:%s" % e)
    for field in CMD_FIELDS:
        value = recipe.get(field)
        if not (isinstance(value, list) and value and all(isinstance(v, str) and v for v in value)):
            reasons.add("cmd_empty:%s" % field)
    reasons.update("limit_key_unknown:%s" % k for k in limits if k not in operating)
    if recipe.get("services") != []:
        reasons.add("services_not_empty")
    return sorted(reasons)


def check_recipe(recipe: Any, policy: Any = None, tree: str | None = None, target: Any = None) -> list[str]:
    """Every static reason against ``recipe`` (empty when it passes); see the module docstring."""
    if not isinstance(recipe, dict):
        return ["malformed:recipe"]
    reasons = ["missing:%s" % f for f in RECIPE_FIELDS if f not in recipe]
    reasons += ["field_not_in_recipe:%s" % f for f in sorted(recipe) if f not in RECIPE_FIELDS]
    get = recipe.get
    if "unit_id" in recipe and not (isinstance(get("unit_id"), str) and UNIT_ID.fullmatch(get("unit_id"))):
        reasons.append("invalid:unit_id")
    path = D.norm_path(get("path"))
    if "path" in recipe and path is None:
        reasons.append("invalid:path")
    inputs = []
    if "inputs" in recipe:
        raw = get("inputs")
        inputs = [D.norm_path(p) for p in raw] if D._str_list(raw) and raw else [None]
        if None in inputs:
            reasons.append("invalid:inputs")
            inputs = [p for p in inputs if p is not None]
        if path is not None and not any(D.covers(p, path) for p in inputs):
            reasons.append("inputs_miss_unit_path")
        if any(D.covers(p, RESERVED) or D.covers(RESERVED, p) for p in inputs if p != "."):
            reasons.append("reserved_path")
    version = None
    if "toolchain" in recipe:
        m = TOOLCHAIN.fullmatch(get("toolchain")) if isinstance(get("toolchain"), str) else None
        if m is None:
            reasons.append("invalid:toolchain")
        else:
            version = m.group(1)
    if "env_image" in recipe:
        reasons += _image_reasons(get("env_image"), version)
    lock = None
    if "lockfiles" in recipe:
        locks = get("lockfiles")
        lock = D.norm_path(locks[0]) if D._str_list(locks) and len(locks) == 1 else None
        if lock is None or posixpath.basename(lock) not in N.LOCK_NAMES:
            reasons.append("invalid:lockfiles")
            lock = None
        else:
            if not any(D.covers(p, lock) for p in inputs):
                reasons.append("lockfile_not_in_inputs")
            if path is not None and not D.covers(posixpath.dirname(lock) or ".", path):
                reasons.append("lockfile_not_for_unit")
    if "install_scripts_required" in recipe and not D._str_list(get("install_scripts_required")):
        reasons.append("invalid:install_scripts_required")
    for field in CMD_FIELDS:
        if field in recipe and not _argv_ok(get(field)):
            reasons.append("invalid:%s" % field)
    if "services" in recipe and get("services") != []:
        reasons.append("services_not_empty")
    if "limits" in recipe:
        reasons += _limit_reasons(get("limits"), policy)
    if tree is not None and not reasons:
        reasons += _tree_reasons(recipe, path, lock, version, tree, target, policy)
    return reasons


def _image_reasons(image: Any, version: str | None) -> list[str]:
    if not (isinstance(image, str) and C.IMAGE.match(image)):
        return ["image_not_pinned"]
    m = IMAGE_SHAPE.fullmatch(image)
    if m is None or m.group("repo") not in OFFICIAL_REPOS:
        return ["image_not_official"]
    tag = m.group("tag") or ""
    if version is None or not (tag == version or tag.startswith(version + "-")):
        return ["image_version_mismatch"]
    return []


def _limit_reasons(limits: Any, policy: Any) -> list[str]:
    if not isinstance(limits, dict):
        return ["invalid:limits"]
    reasons = []
    operating = policy.get("operating") if isinstance(policy, dict) else None
    for key in sorted(limits):
        value = limits[key]
        if key not in OPERATING_NAMES:
            reasons.append("limit_key_unknown:%s" % key)
        elif not C._posint(value):
            reasons.append("invalid:limits.%s" % key)
        elif operating is not None:
            (op_value, band), = _operating(policy, (key,)).values()
            if value > op_value:
                reasons.append("limit_above_operating:%s" % key)
            elif value < band[0]:
                reasons.append("limit_below_band:%s" % key)
    return reasons


def nearest_version(tree: str, path: str) -> tuple[str | None, str | None]:
    """``(file, text)`` of the version file nearest to ``path``; ``(None, None)`` when there is none."""
    for d in D._ancestors(path):
        for name in (".nvmrc", ".node-version"):
            data = D._read_regular(tree, posixpath.join(d, name))
            if data is not None and data.strip():
                return posixpath.join(d, name), data.decode("utf-8", "replace").strip()
        data = D._read_regular(tree, posixpath.join(d, ".tool-versions"))
        if data is not None:
            for line in data.decode("utf-8", "replace").splitlines():
                words = line.split()
                if len(words) > 1 and words[0] in ("node", "nodejs"):
                    return posixpath.join(d, ".tool-versions"), words[1]
    return None, None


def _tree_reasons(recipe: dict, path: str, lock: str, version: str, tree: str, target: Any,
                  policy: Any) -> list[str]:
    reasons = []
    derived = D.derive(tree, target, policy if isinstance(policy, dict) and "constitutional" in policy else None)
    reasons += ["profile:%s" % r for r in D.check(derived, {"units": [recipe]}, tree)["reasons"]]
    _, text = nearest_version(tree, path)
    if text is None:
        reasons.append("version_file_missing")
    else:
        m = VERSION_TEXT.fullmatch(text)
        if m is None:
            reasons.append("version_file_not_exact")
        elif m.group(1) != version:
            reasons.append("toolchain_version_mismatch")
    data = D._read_regular(tree, lock)
    if data is None:
        reasons.append("lockfile_missing")
    else:
        try:
            parsed = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            parsed = None
        report = N.check(parsed, N.DEFAULT_REGISTRIES, recipe["install_scripts_required"])
        reasons += ["lock:%s" % r for r in report["reasons"]]
    return reasons


# ---------------------------------------------------------------- worktree

def _effective(policy: Any, limits: dict) -> tuple[dict, dict]:
    """``(values, operating)``: per run key the smaller of the operator's value and the recipe's."""
    found = _operating(policy, RUN_LIMIT_NAMES)
    values, operating = {}, {}
    for key, (value, band) in found.items():
        values[key] = min(value, limits.get(key, value))
        operating[key] = {"value": values[key], "band": band}
    return values, operating


def copy_inputs(tree: str, inputs: list[str], derived: dict, staging: str, limit: int) -> int:
    """Copy the inputs' closure into ``staging``; returns its regular-file bytes (stops above ``limit``)."""
    total = 0
    tops = D.minimal(D.norm_path(p) for p in inputs)
    for top in tops:
        if top != "." and D.excluded(derived, top):
            continue
        stack = [top]
        while stack:
            rel = stack.pop()
            src = tree if rel == "." else os.path.join(tree, rel)
            dst = staging if rel == "." else os.path.join(staging, rel)
            st = os.lstat(src)
            if rel != ".":
                os.makedirs(os.path.dirname(dst), exist_ok=True)
            if stat.S_ISLNK(st.st_mode):
                os.symlink(os.readlink(src), dst)
            elif stat.S_ISDIR(st.st_mode):
                os.makedirs(dst, exist_ok=True)
                for name in sorted(os.listdir(src), reverse=True):
                    child = name if rel == "." else rel + "/" + name
                    if name != ".git" and not D.excluded(derived, child):
                        stack.append(child)
            elif stat.S_ISREG(st.st_mode):
                shutil.copy2(src, dst, follow_symlinks=False)
                total += st.st_size
                if total > limit:
                    return total
    return total


def _safe_dir(root: str, rel: str) -> str | None:
    """Create ``root/rel`` component by component; None when a symlink or a non-directory is on the way."""
    cur = root
    for part in [p for p in rel.split("/") if p]:
        cur = os.path.join(cur, part)
        try:
            st = os.lstat(cur)
        except FileNotFoundError:
            os.mkdir(cur)
            continue
        if not stat.S_ISDIR(st.st_mode):
            return None
    return cur


class _Unsafe(Exception):
    pass


class _TooBig(Exception):
    pass


def unpack(data: bytes, root: str, dest: str, budget: int) -> tuple[int, int]:
    """Unpack an npm tarball under ``root/dest``; returns ``(bytes, skipped members)``; see the docstring."""
    written = skipped = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar:
            if member.name.startswith("/") or ".." in member.name.split("/"):
                raise _Unsafe(member.name)
            parts = [p for p in member.name.split("/") if p not in ("", ".")]
            if len(parts) < 2:
                continue
            rel = "/".join(parts[1:])
            if member.isdir():
                if _safe_dir(root, dest + "/" + rel) is None:
                    raise _Unsafe(member.name)
                continue
            if not member.isfile():
                skipped += 1
                continue
            parent = _safe_dir(root, dest + "/" + posixpath.dirname(rel))
            if parent is None:
                raise _Unsafe(member.name)
            target = os.path.join(parent, parts[-1])
            if os.path.lexists(target):
                if not stat.S_ISREG(os.lstat(target).st_mode):
                    raise _Unsafe(member.name)
                os.unlink(target)
            written += member.size
            if written > budget:
                raise _TooBig()
            fh = tar.extractfile(member)
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o755 if member.mode & 0o111 else 0o644)
            with os.fdopen(fd, "wb") as out:
                shutil.copyfileobj(fh, out)
            os.chmod(target, 0o755 if member.mode & 0o111 else 0o644)
    return written, skipped


def _bins(manifest: Any, name: str) -> dict:
    if not isinstance(manifest, dict):
        return {}
    value = manifest.get("bin")
    if isinstance(value, str):
        return {name.split("/")[-1]: value}
    if isinstance(value, dict):
        return {k: v for k, v in value.items() if isinstance(v, str)}
    return {}


def link_bins(staging: str, lock_dir: str, rows: list[dict]) -> list[str]:
    """Make ``.bin`` symlinks for every package with ``bin``; returns the links made (relative paths)."""
    made: list[str] = []
    for row in sorted(rows, key=lambda r: r["key"]):
        pkg = posixpath.join(lock_dir, row["key"]) if lock_dir != "." else row["key"]
        pkg_json = D._read_regular(staging, pkg + "/package.json")
        try:
            manifest = json.loads(pkg_json.decode("utf-8")) if pkg_json is not None else None
        except (UnicodeDecodeError, ValueError, RecursionError):
            manifest = None
        parent = pkg[: pkg.rindex("node_modules/") + len("node_modules")]
        for bin_name, target in sorted(_bins(manifest, row["name"]).items()):
            inner = D.norm_path(target)
            if not BIN_NAME.fullmatch(bin_name) or bin_name in (".", "..") or inner is None:
                continue
            bin_dir = _safe_dir(staging, parent + "/.bin")
            link = parent + "/.bin/" + bin_name
            if bin_dir is None or os.path.lexists(os.path.join(staging, link)):
                continue
            os.symlink(posixpath.relpath(pkg + "/" + inner, parent + "/.bin"), os.path.join(staging, link))
            full = os.path.join(staging, pkg, inner)
            if os.path.isfile(full) and not os.path.islink(full):
                os.chmod(full, 0o755)
            made.append(link)
    return made


def install_deps(staging: str, lock: str, deps: str | None, tree_lock: bytes, budget: int) -> tuple[list[str], dict]:
    """Take the artifact by its hash and unpack it; ``(reasons, {address, rows, links, bytes, skipped})``."""
    lock_obj = json.loads(tree_lock.decode("utf-8"))
    has_packages = any(k for k in lock_obj.get("packages", {}))
    if deps is None:
        if has_packages:
            raise VerifyError("the lock has packages and no deps artifact was given")
        return [], {"address": None, "rows": [], "links": [], "bytes": 0, "skipped": 0}
    report = N.verify(deps)
    if not report["ok"]:
        return ["deps:%s" % r for r in report["reasons"]], {}
    with open(os.path.join(deps, "manifest.json"), "rb") as fh:
        manifest = json.loads(fh.read().decode("ascii"))
    if manifest["lock_sha256"] != hashlib.sha256(tree_lock).hexdigest():
        return ["deps_lock_mismatch"], {}
    lock_dir = posixpath.dirname(lock) or "."
    total = skipped = 0
    for row in manifest["packages"]:
        if not N.LOCK_PATH_RE.fullmatch(row.get("key", "")):
            return ["deps_unpack_unsafe:%s" % row.get("key")], {}
        dest = row["key"] if lock_dir == "." else lock_dir + "/" + row["key"]
        with open(os.path.join(deps, "tarballs", row["sha512"] + ".tgz"), "rb") as fh:
            data = fh.read()
        try:
            n, s = unpack(data, staging, dest, budget - total)
        except _Unsafe:
            return ["deps_unpack_unsafe:%s" % row["key"]], {}
        except _TooBig:
            return ["limit_hit:worktree_bytes"], {}
        except (tarfile.TarError, EOFError, zlib.error):
            return ["deps_unpack_unsafe:%s" % row["key"]], {}
        total += n
        skipped += s
    links = link_bins(staging, lock_dir, manifest["packages"])
    return [], {"address": report["address"], "rows": manifest["packages"], "links": links, "bytes": total,
                "skipped": skipped}


# ---------------------------------------------------------------- runs

class _Timed:
    """Wraps a runner: caps its timeout and records the wall clock of each call by container name."""

    def __init__(self, inner: C.Runner, cap: float | None) -> None:
        self.inner, self.cap, self.calls = inner, cap, {}

    def __call__(self, argv: list, env: dict, timeout: float) -> C.RunnerResult:
        capped = self.cap is not None and self.cap < timeout
        start = time.monotonic()
        res = self.inner(argv, env, self.cap if capped else timeout)
        self.calls[C._flag_value(argv, "--name")] = {"duration_s": round(time.monotonic() - start, 3),
                                                     "capped": capped and res.timed_out, "stdout": res.stdout}
        return res


def _one(job_cmd: list, red_cmd: list, image: str, staging: str, operating: dict, runner: C.Runner,
         base: str | None, cap: float | None = None) -> dict:
    timed = _Timed(runner, cap)
    job = {"image": image, "cmd": job_cmd, "tree": staging, "env": dict(ENV)}
    red = {"image": image, "cmd": red_cmd, "tree": staging, "env": dict(ENV)}
    report = C.run_with_red_control(job, red, operating, timed, base)
    main = report["result"]
    timing = timed.calls.get(C._flag_value(main["argv"], "--name"), {})
    reasons = list(report["reasons"])
    if timing.get("capped"):
        reasons = ["limit_hit:test_total_s" if r == "limit_hit:kos_wall_s" else r for r in reasons]
    return {"valid": report["valid"], "reasons": reasons, "exit": main["exit"], "status": main["status"],
            "stdout_sha256": main.get("stdout_sha256"), "outputs_sha256": main["outputs_sha256"],
            "duration_s": timing.get("duration_s"), "red_control_exit": report["red_control"]["exit"],
            "run_root": main["run_root"], "stdout": timing.get("stdout")}


def _public(run: dict) -> dict:
    return {k: v for k, v in run.items() if k not in ("run_root", "stdout")}


def lint_records(stdouts: list, staging: str, recipe: dict, derived: dict) -> tuple[list[str], list[dict]]:
    """asama-0/08 unit criteria 4 and 5 on the lint runs' stdout: ``(reasons, one run record per run)``."""
    records, reasons = [], []
    for out in stdouts:
        try:
            records.append(R.record(out if isinstance(out, bytes) else b"", staging))
        except R.RecordError as exc:
            reasons += ["lint_output:" + r for r in exc.reasons if "lint_output:" + r not in reasons]
    if reasons:
        return reasons, []
    closed = derived["security_paths"] + derived["excluded_dirs"] + derived["excluded_paths"]
    if not any(v["fix"] is not None and not any(D.covers_as_written(e, v["path"]) for e in closed)
               and any(D.covers_as_written(e, v["path"]) for e in recipe["inputs"])
               for v in records[0]["violations"]):
        return ["no_fixable_violation"], []
    return [], records


def verify(recipe: Any, tree: str, policy: Any, red_control: Any, deps: str | None = None, target: Any = None,
           runner: C.Runner | None = None, base: str | None = None) -> dict:
    """The static check, then the 3/3 run; ``{verdict, ok, reasons, ...}`` (see the module docstring)."""
    runner = runner or C.docker_runner
    if not (isinstance(red_control, dict) and _argv_ok(red_control.get("cmd"))):
        raise VerifyError("red_control must be {cmd: [argv]}")
    if not os.path.isdir(tree) or os.path.islink(tree):
        raise VerifyError("tree is not a directory")
    reasons = check_recipe(recipe, policy, tree, target)
    if reasons:
        return _verdict(reasons)
    values, operating = _effective(policy, recipe["limits"])
    derived = D.derive(tree, target, policy if isinstance(policy, dict) and "constitutional" in policy else None)
    lock = D.norm_path(recipe["lockfiles"][0])
    staging_root = tempfile.mkdtemp(prefix="snowball-unit-", dir=base)
    try:
        staging = os.path.join(staging_root, "tree")
        os.mkdir(staging)
        size = copy_inputs(tree, recipe["inputs"], derived, staging, values["unit_inputs_bytes"])
        if size > values["unit_inputs_bytes"]:
            return _verdict(["limit_hit:unit_inputs_bytes"], inputs_bytes=size)
        if os.path.lexists(os.path.join(staging, RESERVED)):
            return _verdict(["reserved_path"])
        bad, deps_info = install_deps(staging, lock, deps, D._read_regular(tree, lock),
                                      values["worktree_bytes"] - size)
        if bad:
            return _verdict(bad, inputs_bytes=size)
        for sub in ("home", "tmp"):
            os.makedirs(os.path.join(staging, RESERVED, sub))
        result: dict[str, Any] = {"inputs_bytes": size, "deps_address": deps_info["address"],
                                  "deps_bytes_unpacked": deps_info["bytes"], "bin_links": deps_info["links"],
                                  "skipped_members": deps_info["skipped"], "install": None,
                                  "runs": {"lint": [], "test": []}}
        scripted = sorted({r["name"] for r in deps_info["rows"] if r.get("install_script")})
        if scripted:
            prefix = "/work" if posixpath.dirname(lock) in ("", ".") else "/work/" + posixpath.dirname(lock)
            cmd = ["npm", "--prefix", prefix, "rebuild", "--offline", "--foreground-scripts"] + scripted
            run = _one(cmd, red_control["cmd"], recipe["env_image"], staging, operating, runner, staging_root)
            result["install"] = _public(run)
            if not run["valid"]:
                return _verdict(run["reasons"], **result)
            if run["exit"] != 0:
                return _verdict(["install_scripts_failed"], **result)
            staging = os.path.join(run["run_root"], "work")
        reasons, stdouts = [], []
        cap = values["test_total_s"]
        for attempt in range(1, ATTEMPTS + 1):
            lint = _one(recipe["lint_cmd"], red_control["cmd"], recipe["env_image"], staging, operating,
                        runner, staging_root)
            test = _one(recipe["test_cmd"], red_control["cmd"], recipe["env_image"], staging, operating,
                        runner, staging_root, cap)
            result["runs"]["lint"].append(_public(lint))
            stdouts.append(lint["stdout"])
            result["runs"]["test"].append(_public(test))
            for run in (lint, test):
                reasons += [r for r in run["reasons"] if r not in reasons]
            if lint["valid"] and lint["exit"] not in LINT_OK_EXITS:
                reasons.append("lint_failed:%d" % attempt)
            if test["valid"] and test["exit"] != 0:
                reasons.append("test_red:%d" % attempt)
        lints = result["runs"]["lint"]
        if all(r["valid"] for r in lints) and len({(r["exit"], r["stdout_sha256"]) for r in lints}) > 1:
            reasons.append("lint_not_deterministic")
        if not reasons:
            reasons, records = lint_records(stdouts, staging, recipe, derived)
            if not reasons:
                result["lint_records"] = records
        if reasons:
            return _verdict(reasons, **result)
        return dict(_verdict([], **result), recipe=recipe, recipe_sha256=hashlib.sha256(canonical(recipe)).hexdigest())
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def _verdict(reasons: list[str], **extra) -> dict:
    if not reasons:
        verdict = "verified"
    elif any(not r.startswith(NO_VERDICT_PREFIXES) for r in reasons):
        verdict = "refused"
    else:
        verdict = "no_verdict"
    return dict(extra, verdict=verdict, ok=not reasons, reasons=reasons)


# ---------------------------------------------------------------- command line

def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def _load(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except RecursionError:
        raise VerifyError("%s: JSON nested too deeply" % path) from None


USAGE = "usage: python -m profile.unit_verify check RECIPE POLICY | verify FILE"
EXIT = {"verified": 0, "refused": 1, "no_verdict": 2}


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 3 and argv[0] == "check":
            reasons = vector_check(_load(argv[1]), _load(argv[2]))
            _emit({"ok": not reasons, "reasons": reasons})
            return 0 if not reasons else 1
        if len(argv) == 2 and argv[0] == "verify":
            req = _load(argv[1])
            if not isinstance(req, dict) or not isinstance(req.get("tree"), str):
                raise VerifyError("verify FILE must be {recipe, tree, policy, red_control, deps?, target?, base?}")
            report = verify(req.get("recipe"), req["tree"], req.get("policy"), req.get("red_control"),
                            req.get("deps"), req.get("target"), base=req.get("base"))
            _emit(report)
            return EXIT[report["verdict"]]
        _emit({"ok": False, "error": USAGE})
        return 2
    except (VerifyError, D.DeriveError, C.ContainmentError, ValueError, KeyError, TypeError, OSError,
            RecursionError) as exc:
        _emit({"ok": False, "error": "unusable input: %s" % exc})
        return 2
    except Exception as exc:  # noqa: BLE001 - no traceback and no exit 1 without a refusal
        _emit({"ok": False, "error": "internal error: %s: %s" % (type(exc).__name__, exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
