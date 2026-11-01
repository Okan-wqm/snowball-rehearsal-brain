"""``profile.fit``: for each unit candidate of a tree, the stage-0 recipe its own npm scripts give, judged by
``unit_verify.check_recipe``; the first candidate that passes is the brain's ``units.json`` proposal (stage 0).

Rules: asama-0/08 "Birim seçimi" (the operator names the candidate units in order in ``targets[]``; MF4 and MF6
check the bold criteria mechanically; when a candidate fails, the next one is tried), tohum/26c (the recipe; the
brain proposes ``targets/<target>/units.json``, which ``çek`` reads: ``loop.cek``), MF4 (``profile.derive``: the
candidates, in the operator's order when ``targets[]`` names them, else every ``package.json`` directory, sorted)
and MF6 (``unit_verify.check_recipe`` with the tree is the one judge; this module adds no reason of its own).

**The composed recipe** (``compose``) for candidate ``path``:

- ``unit_id``: ``path`` with every character outside ``[A-Za-z0-9._-]`` written ``-`` and a leading ``.``,
  ``_`` or ``-`` dropped; ``root`` for ``.``; at most 128 characters.
- ``lockfiles``: ``[derive.nearest_lock]`` (the lock MF4 reads for the candidate), ``[]`` when there is none.
- ``toolchain``: ``node@<text>`` of ``unit_verify.nearest_version`` with a leading ``v`` dropped (``node@`` when
  there is no version file); ``env_image``: ``images[<that text>]`` when given, else ``""``.
- ``inputs``: ``path``, the lock and the version file, the ones another covers left out (``derive.minimal``). No
  shared library or root configuration is added: their need shows only in ``verify``'s 3/3 run.
- ``install_scripts_required``: the lock keys whose entry says ``hasInstallScript: true`` (MF5's lock reading),
  sorted. A script only a tarball declares is not known before the fetch (MF5 refuses it then).
- ``lint_cmd``: ``npm --prefix <path> run --silent lint -- --format json``; ``test_cmd`` and
  ``affected_test_cmd``: ``npm --prefix <path> run --silent test`` (stage 0's affected set is the unit's whole
  test set, asama-0/08 item 6). npm runs the owner's own script in ``<path>`` with ``<path>/node_modules/.bin``
  and every directory above it on ``PATH``, writes nothing of its own to stdout with ``--silent`` and exits with
  the script's code (npm 10.9.9, measured). ``check_recipe`` judges such a command's script and programs
  (``script_missing``, ``script_not_installed``). Not judged here: whether the lint tool is ESLint and takes
  ``--format json`` (``verify``'s ``lint_output:`` shows it), whether the tests need services, and anything
  else only a run shows.
- ``services``: ``[]``; ``limits``: ``{}`` (the operator's values apply).

**Result** (``fit``): ``{candidates, fit, rows}``: one row ``{path, reasons, recipe}`` per candidate of the
derivation, in its order, ``reasons`` being ``check_recipe``'s (an ineligible candidate shows as
``profile:units[0]:unit_not_eligible:<path>``); ``fit`` lists the paths with no reason. Passing this static
check is not verification: ``verify`` (3/3 at HEAD, contained) is.

Command line, no stdin; one JSON line on stdout::

    python -m profile.fit TREE [--target TARGET.json] [--policy POLICY.json] [--images IMAGES.json] [--units OUT]

``TREE`` a directory, read only; ``TARGET`` the ``targets[]`` entry; ``POLICY`` the referee's ``policy.json``;
``IMAGES`` a JSON object from a version (``X.Y.Z``) to an image reference. With ``--units``, ``OUT`` is written
as ``{"units": [<the first passing recipe>]}`` when one passes (stage 0 runs exactly one unit) and is not
touched otherwise. Exit 0 when a candidate passes, 1 when none does, 2 on unusable input (``{ok: false,
error}``).
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
from typing import Any

from profile import derive as D
from profile import unit_verify as U
from runner import deps_npm as N
import cli

LINT_CMD = ("run", "--silent", "lint", "--", "--format", "json")
TEST_CMD = ("run", "--silent", "test")
UNSAFE_ID = re.compile(r"[^A-Za-z0-9._-]")


def unit_id(path: str) -> str:
    if path == ".":
        return "root"
    return UNSAFE_ID.sub("-", path).lstrip("._-")[:128] or "root"


def install_marks(tree: str, lock: str | None) -> list[str]:
    _, parsed = D._json(tree, lock) if lock else (False, None)
    return sorted(row["key"] for row in N.entries(parsed)[1] if row["entry"].get("hasInstallScript") is True)


def compose(tree: str, path: str, images: dict | None = None) -> dict:
    """The recipe of candidate ``path`` (module docstring)."""
    lock = D.nearest_lock(tree, path)
    version_file, text = U.nearest_version(tree, path)
    version = text[1:] if text and text.startswith("v") else (text or "")
    image = (images or {}).get(version)
    return {
        "unit_id": unit_id(path),
        "path": path,
        "inputs": D.minimal([p for p in (path, lock, version_file) if p]),
        "toolchain": "node@" + version,
        "env_image": image if isinstance(image, str) else "",
        "lockfiles": [lock] if lock else [],
        "install_scripts_required": install_marks(tree, lock),
        "lint_cmd": ["npm", "--prefix", path] + list(LINT_CMD),
        "test_cmd": ["npm", "--prefix", path] + list(TEST_CMD),
        "affected_test_cmd": ["npm", "--prefix", path] + list(TEST_CMD),
        "services": [],
        "limits": {},
    }


def fit(tree: str, target: Any = None, policy: Any = None, images: dict | None = None) -> dict:
    """Every candidate's composed recipe and ``check_recipe``'s reasons (module docstring)."""
    derived = U.derived_profile(tree, target, policy)
    rows = []
    for candidate in derived["unit_candidates"]:
        if D.norm_path(candidate["path"]) is None:
            rows.append({"path": candidate["path"], "reasons": ["invalid:path"], "recipe": None})
            continue
        recipe = compose(tree, candidate["path"], images)
        rows.append({"path": candidate["path"], "reasons": U.check_recipe(recipe, policy, tree, target, derived),
                     "recipe": recipe})
    return {"candidates": len(rows), "fit": [r["path"] for r in rows if not r["reasons"]], "rows": rows}


def _load(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except RecursionError:
        raise ValueError("%s: JSON nested too deeply" % path) from None


USAGE = ("usage: python -m profile.fit TREE [--target TARGET.json] [--policy POLICY.json] [--images IMAGES.json]"
         " [--units OUT]")
OPTIONS = ("--target", "--policy", "--images", "--units")


def main(argv: list[str]) -> int:
    try:
        if not argv or len(argv) % 2 != 1 or argv[0].startswith("-"):
            raise ValueError(USAGE)
        opts = dict(zip(argv[1::2], argv[2::2]))
        if any(k not in OPTIONS for k in opts) or len(opts) != len(argv) // 2:
            raise ValueError(USAGE)
        target = _load(opts["--target"]) if "--target" in opts else None
        policy = _load(opts["--policy"]) if "--policy" in opts else None
        images = _load(opts["--images"]) if "--images" in opts else None
        if target is not None and not isinstance(target, dict):
            raise ValueError("target is not an object")
        if images is not None and not isinstance(images, dict):
            raise ValueError("images is not an object")
        report = fit(argv[0], target, policy, images)
    except (D.DeriveError, U.VerifyError, ValueError, OSError) as exc:
        _emit({"ok": False, "error": "unusable input: %s" % cli.cause(exc)})
        return 2
    passing = [r["recipe"] for r in report["rows"] if not r["reasons"]]
    if passing and "--units" in opts:
        with open(opts["--units"], "w", encoding="utf-8") as fh:
            json.dump({"units": passing[:1]}, fh, indent=2, sort_keys=True)
            fh.write("\n")
    _emit(dict(report, ok=bool(passing)))
    return 0 if passing else 1


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")


def FAULT_LINE(argv: list[str]) -> dict:  # noqa: N802 - cli.run's fault line
    return {"ok": False, "error": "internal error"}


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
