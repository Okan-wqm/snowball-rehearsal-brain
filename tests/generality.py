"""The brain's own reading of asama-0/10 #genellik over ``referee/``, run before the referee's: no name of a target
in ``referee/``'s text, and every file there text.

Why: the exit request on 7d969ad was rejected (result on a931320: ``target_name_in_referee`` for three files of
``referee/tests``, ``referee_file_not_text`` for a fourth) and no test of this brain read ``referee/`` for
either (founder ledger f1019, f1021): the condition is judged only at an exit, and the list it is judged against
(``setup/summary.json`` ``targets[].identifiers``, tohum/26c) is in the referee repository, which a session does
not read. So the brain keeps the names it can read from a target itself, as data outside ``referee/``, and test 14
runs this check on every push. Run from anywhere:
``python3 tests/generality.py check [--root DIR]`` and ``python3 tests/generality.py names CHECKOUT --repo URL
--commit SHA``.

``check`` follows the referee's reading as tohum/29e:55-65 ("Genellik okuması") states it, each rule bound by
``tests/test_generality.py``:

- **Files read**: every regular file under ``ROOT/referee``, found by walking the directory, in path order. A
  directory named ``__pycache__`` is not entered (python writes its cache there while the tests run and
  ``.gitignore`` keeps it out of a commit). A symbolic link is neither followed nor read.
- **Compared** (``fold``): a name and the place it is searched in are read the same way, in the page's order: NFKD,
  then casefold, then every character with a combining class dropped, then dotless ``ı`` read as ``i``. A name is
  found when its folded form is a substring of the folded place.
- **Path first** (``target_name_in_referee:sha256:<16 hex>``): the place searched first is the file's path after
  ``referee/`` (``/`` separated). A file with a name in its path is not opened: it gets this one reason, whatever
  its bytes are, and it is shown as ``sha256:`` and the first 16 hex characters of the sha256 of its path
  (``referee/...``, as UTF-8; a name the directory holds in other bytes, by those bytes), not as the path.
- **Text** (``referee_file_not_text:<path>``): a file is text when its bytes decode as strict UTF-8 and hold no NUL
  (U+0000); every other control character is text. A file that is not text gets this reason and nothing more.
- **Names** (``target_name_in_referee:<path>``): a name in the text of a file whose path holds none. The names are
  those of ``ROOT/targets/names.json`` (below).
- The answer is one JSON line: ``ok``, ``files`` (how many were found), ``reasons`` (sorted, each once) and ``why``
  (per named file, under the path as its reason shows it, which entries matched, as ``targets[i].names[j]``: the
  index, not the name). Exit 0 when there is no reason, 1 when there is one, 2 when the names file or
  ``ROOT/referee`` cannot be used (``{"ok": false, "reason": ...}``): a missing or malformed list is not an empty
  list.

``targets/names.json`` (``load_names``): ``{"targets": [{"repo", "commit", "names": [{"name", "from"}]}]}``, exactly
these keys, every value a non-empty string, ``names`` a list (it may be empty); a name that ``fold`` leaves nothing
of (combining marks alone) is refused too, it would be found in every file. One entry per target a session has
had a checkout of; ``names`` prints a names file holding the one entry of the checkout it is given:

- ``repository``: the last segment of the repository URL's path, a final ``.git`` cut off;
- ``package.json``, ``Cargo.toml``, ``pyproject.toml``: the name the manifest at the checkout's root gives its
  package (``name``, ``[package].name``, ``[project].name``), when the file is there and the value is a non-empty
  string. A manifest that is there and cannot be parsed stops the command (exit 2): the list is not written short.
- a name found twice is listed once, under its first source, in the order above.

Not checked, stated: whether these are the names the referee holds (``setup/summary.json``
``targets[].identifiers`` is the operator's list and decides; 29e: neither the list nor its length is given to a
session, so a name there that no rule above derives is seen only in the referee's verdict, and passing here is not
passing there); whether the referee's code folds as ``fold`` does where the page leaves room (casefold before NFKD
gives another result on 637 code points of Unicode 15.0, e.g. U+03D2; another Unicode version another table) and
which bytes of a path it hashes (its code is not read: the 16 hex characters of a path hit are this tool's
reading of the page's sentence and may differ from the referee's); files of the archive
against files of the directory (the referee reads the pushed commit's archive, this walk reads what is on disk,
an uncommitted file included); the account that owns a target's repository (it owns this brain's and the
referee's too, and the verdict on a931320 did not name the files that carry it alone); words inside a name,
workspace package names and scopes, directory and file names of a target (``tests/fixtures`` builds trees with
common ones); a target no session has a checkout of (the toy's repository); a name written so that the folded text
does not hold it (split, encoded); links and special files under ``referee/`` (``loop.treehash`` refuses a tree
that has one). 29e's last sentence holds for this check as well: passing it is not proof of generality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
import unicodedata
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFEREE = "referee"
NAMES = "targets/names.json"
SKIP_DIRS = ("__pycache__",)
SHOWN_HEX = 16
ENTRY_KEYS = {"repo", "commit", "names"}
NAME_KEYS = {"name", "from"}
# the manifests read at a checkout's root: file, parser, the keys down to the package's name
ROOT_MANIFESTS = (
    ("package.json", json.loads, ("name",)),
    ("Cargo.toml", tomllib.loads, ("package", "name")),
    ("pyproject.toml", tomllib.loads, ("project", "name")),
)


class Unreadable(Exception):
    """The names file, the tree or a manifest cannot be used; the command exits 2."""


def _string(value: object) -> bool:
    return isinstance(value, str) and value != ""


def load_names(path: str) -> list[tuple[str, str]]:
    """``[(label, name)]`` of a names file, ``label`` being ``targets[i].names[j]``."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, RecursionError) as e:
        raise Unreadable("names_unreadable: %s" % type(e).__name__) from e
    if not isinstance(doc, dict) or set(doc) != {"targets"} or not isinstance(doc["targets"], list):
        raise Unreadable("names_invalid: top")
    out = []
    for i, entry in enumerate(doc["targets"]):
        if (not isinstance(entry, dict) or set(entry) != ENTRY_KEYS or not _string(entry["repo"])
                or not _string(entry["commit"]) or not isinstance(entry["names"], list)):
            raise Unreadable("names_invalid: targets[%d]" % i)
        for j, item in enumerate(entry["names"]):
            label = "targets[%d].names[%d]" % (i, j)
            if not isinstance(item, dict) or set(item) != NAME_KEYS or not all(_string(v) for v in item.values()):
                raise Unreadable("names_invalid: %s" % label)
            if not fold(item["name"]):
                raise Unreadable("names_invalid: %s" % label)
            out.append((label, item["name"]))
    return out


def files(root: str) -> list[str]:
    """The regular files under ``root/referee``, as paths relative to ``root``, in path order."""
    top = os.path.join(root, REFEREE)
    if not os.path.isdir(top) or os.path.islink(top):
        raise Unreadable("referee_unreadable")
    found = []
    for base, dirs, names in os.walk(top):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = os.path.join(base, name)
            if os.path.isfile(path) and not os.path.islink(path):
                found.append(os.path.relpath(path, root).replace(os.sep, "/"))
    return sorted(found)


def fold(value: str) -> str:
    """A name or the place it is searched in, as the two are compared."""
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(ch for ch in value if not unicodedata.combining(ch)).replace("\u0131", "i")


def text(data: bytes) -> str | None:
    """The file's text, or ``None`` when it is not text."""
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return None if "\x00" in decoded else decoded


def shown(rel: str) -> str:
    """How a path that holds a name is printed."""
    return "sha256:" + hashlib.sha256(rel.encode("utf-8", "surrogateescape")).hexdigest()[:SHOWN_HEX]


def check(root: str, names_path: str | None = None) -> dict:
    names = [(label, fold(name))
             for label, name in load_names(os.path.join(root, NAMES) if names_path is None else names_path)]
    rels = files(root)
    reasons, why = [], {}
    for rel in rels:
        place, key = fold(rel[len(REFEREE) + 1:]), shown(rel)
        if not any(name in place for _, name in names):
            with open(os.path.join(root, rel), "rb") as fh:
                body = text(fh.read())
            if body is None:
                reasons.append("referee_file_not_text:%s" % rel)
                continue
            place, key = fold(body), rel
        hits = [label for label, name in names if name in place]
        if hits:
            reasons.append("target_name_in_referee:%s" % key)
            why[key] = hits
    return {"ok": not reasons, "files": len(rels), "reasons": sorted(reasons), "why": why}


def repository_name(url: str) -> str:
    segments = [s for s in urllib.parse.urlsplit(url).path.split("/") if s]
    name = segments[-1] if segments else ""
    name = name[:-len(".git")] if name.endswith(".git") else name
    if not name:
        raise Unreadable("repo_unreadable")
    return name


def derive(checkout: str, repo: str, commit: str) -> dict:
    """One ``targets[]`` entry of the names file, from a checkout's root manifests and its repository URL."""
    if not _string(commit):
        raise Unreadable("commit_unreadable")
    found = [(repository_name(repo), "repository")]
    for manifest, parse, keys in ROOT_MANIFESTS:
        path = os.path.join(checkout, manifest)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                value = parse(fh.read())
        except (OSError, ValueError, RecursionError) as e:
            raise Unreadable("manifest_unreadable: %s" % manifest) from e
        for key in keys:
            value = value.get(key) if isinstance(value, dict) else None
        if _string(value):
            found.append((value, manifest))
    names, seen = [], set()
    for name, source in found:
        if name not in seen:
            seen.add(name)
            names.append({"name": name, "from": source})
    return {"repo": repo, "commit": commit, "names": names}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check")
    c.add_argument("--root", default=ROOT)
    n = sub.add_parser("names")
    n.add_argument("checkout")
    n.add_argument("--repo", required=True)
    n.add_argument("--commit", required=True)
    args = ap.parse_args(argv)
    try:
        if args.command == "names":
            print(json.dumps({"targets": [derive(args.checkout, args.repo, args.commit)]}, indent=1))
            return 0
        answer = check(args.root)
    except Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(answer, sort_keys=True))
    return 0 if answer["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
