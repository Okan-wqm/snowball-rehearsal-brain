"""Git objects in git's own format, built in Python (tests only): the object source ``loop.gitobj`` reads.

``store(files)`` -> ``(objects, commit)``: ``objects`` maps sha -> (type, content) for a commit whose tree holds
``files`` (path -> bytes for a ``100644`` file, or ``(mode, bytes)``; ``"120000"`` is a link, its bytes the
target); entries are sorted as git sorts them (a tree's name compared with a trailing ``/``). ``RealGit`` checks
that a tree built here has the id real git gave the same files.

``install_git(directory, answers)`` writes an executable ``git`` that speaks ``cat-file --batch``: for each
requested line it writes ``answers[line]`` (raw bytes, given hex-encoded in ``answers.json`` beside it) or
``<line> missing``, and exits after answering a line in ``exit_after``; it appends its argv, environment and
what its stdin and stdout are (``fds``) to ``calls.jsonl`` beside itself. Its ``init`` (the first argument after the options, ``-c`` taking a value)
creates the directory named last and its ``fetch`` does nothing; each exits with ``exits[<command>]`` (0 when
absent): the objects it then answers stand for what a fetch brought.
"""

from __future__ import annotations

import json
import os
import stat
import sys

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from loop.gitobj import object_id  # noqa: E402

AUTHOR = b"A <a@example.org> 1700000000 +0000"


def put(objects: dict, kind: str, data: bytes) -> str:
    sha = object_id(kind, data)
    objects[sha] = (kind, data)
    return sha


def tree(objects: dict, entries: list[tuple[bytes, bytes, str]]) -> str:
    """A tree object from ``(mode, name, sha)`` entries, written in the order given."""
    return put(objects, "tree", b"".join(m + b" " + n + b"\0" + bytes.fromhex(s) for m, n, s in entries))


def commit(objects: dict, tree_sha: str, message: bytes = b"m\n") -> str:
    return put(objects, "commit", b"tree %s\nauthor %s\ncommitter %s\n\n%s" % (
        tree_sha.encode(), AUTHOR, AUTHOR, message))


def _build(objects: dict, files: dict) -> str:
    here: dict[str, tuple[bytes, str]] = {}
    subs: dict[str, dict] = {}
    for path, value in files.items():
        head, _, rest = path.partition("/")
        if rest:
            subs.setdefault(head, {})[rest] = value
        else:
            mode, data = value if isinstance(value, tuple) else ("100644", value)
            here[head] = (mode.encode(), put(objects, "blob", data))
    for name, sub in subs.items():
        here[name] = (b"40000", _build(objects, sub))
    order = sorted(here, key=lambda n: n.encode() + (b"/" if here[n][0] == b"40000" else b""))
    return tree(objects, [(here[n][0], n.encode(), here[n][1]) for n in order])


def store(files: dict) -> tuple[dict, str]:
    objects: dict = {}
    return objects, commit(objects, _build(objects, files))


def from_dir(root: str) -> dict:
    """A directory's regular files as ``store`` input (executable bit kept)."""
    out: dict = {}
    for dirpath, _, names in os.walk(root):
        for n in names:
            p = os.path.join(dirpath, n)
            with open(p, "rb") as fh:
                data = fh.read()
            out[os.path.relpath(p, root).replace(os.sep, "/")] = (
                "100755" if os.access(p, os.X_OK) else "100644", data)
    return out


def parse_batch(stream: bytes) -> dict:
    """``git cat-file --batch`` output -> sha -> (type, content); its own parser, independent of ``GitBatch``."""
    out, i = {}, 0
    while i < len(stream):
        nl = stream.index(b"\n", i)
        sha, kind, size = stream[i:nl].decode().split()
        start = nl + 1
        out[sha] = (kind, stream[start:start + int(size)])
        assert stream[start + int(size):start + int(size) + 1] == b"\n"
        i = start + int(size) + 1
    return out


def batch_record(sha: str, kind: str, data: bytes) -> bytes:
    return b"%s %s %d\n" % (sha.encode(), kind.encode(), len(data)) + data + b"\n"


SCRIPT = '''#!%s
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
with open("/proc/self/environ", "rb") as fh:
    env = dict(item.decode().split("=", 1) for item in fh.read().split(b"\\0") if item)
with open(os.path.join(here, "calls.jsonl"), "a") as fh:
    fh.write(json.dumps({"argv": sys.argv[1:], "env": env,
                         "fds": [os.path.realpath("/proc/self/fd/" + str(fd)) for fd in (0, 1)]}) + "\\n")
with open(os.path.join(here, "answers.json")) as fh:
    doc = json.load(fh)
args, i = sys.argv[1:], 0
while i < len(args) and args[i].startswith("-"):
    i += 2 if args[i] == "-c" else 1
if i < len(args) and args[i] in ("init", "fetch"):
    if args[i] == "init":
        os.makedirs(args[-1])
    sys.exit(doc["exits"].get(args[i], 0))
answers = {k: bytes.fromhex(v) for k, v in doc["answers"].items()}
out = sys.stdout.buffer
for line in sys.stdin.buffer:
    key = line.rstrip(b"\\n").decode()
    out.write(answers.get(key, key.encode() + b" missing\\n"))
    out.flush()
    if key in doc["exit_after"]:
        sys.exit(0)
'''


def install_git(directory: str, answers: dict[str, bytes], exit_after: tuple = (), exits: dict | None = None) -> str:
    path = os.path.join(directory, "git")
    with open(path, "w") as fh:
        fh.write(SCRIPT % sys.executable)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    with open(os.path.join(directory, "answers.json"), "w") as fh:
        json.dump({"answers": {k: v.hex() for k, v in answers.items()}, "exit_after": list(exit_after),
                   "exits": exits or {}}, fh)
    return path


def calls(directory: str) -> list[dict]:
    with open(os.path.join(directory, "calls.jsonl")) as fh:
        return [json.loads(line) for line in fh]
