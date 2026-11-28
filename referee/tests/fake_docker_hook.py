"""Child side of ``fake_docker``: block what the container flags forbid, then run the Python command.

argv: NETWORK READ_ONLY N_RW RW... N_RO RO... SCRIPT [ARG ...] (``fake_docker.hook_argv`` writes it): the
network's name, ``1`` or ``0``, then the writable host directories and the read-only ones, each list after its
count.

Why not JSON and ``runpy``: this file is every fake container's start. ``json`` and ``runpy`` bring ``re``,
``enum``, ``typing`` and ``pkgutil`` with them, and where the standard library has no bytecode (a read-only image
that ships none) each start compiles them again: measured 2026-11-28 on such a home, 136 ms a start with them
against 39 ms where bytecode is kept, and 18 ms without them. What is imported now: ``os`` and ``sys``, which
python has loaded before it reads this file, and ``errno``, which is built into the binary
(``test_contained.StartTest`` holds the list).
"""

import errno
import os
import sys


def _config(argv):
    """``(cfg, rest)`` of the argv above: ``rest`` is SCRIPT and its arguments."""
    network, read_only, rest = argv[0], argv[1] == "1", argv[2:]
    lists = []
    for _ in range(2):
        n = int(rest[0])
        lists.append(rest[1:1 + n])
        rest = rest[1 + n:]
    return {"network": network, "read_only": read_only, "rw": lists[0], "ro": lists[1]}, rest


CFG, REST = _config(sys.argv[1:])
RW = [os.path.realpath(p) for p in CFG["rw"]]
RO = [os.path.realpath(p) for p in CFG["ro"]]
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
PATH_EVENTS = {"os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,), "os.chmod": (0,), "os.truncate": (0,),
               "os.utime": (0,), "os.rename": (0, 1), "os.symlink": (1,), "os.link": (1,), "os.mkfifo": (0,),
               "os.mknod": (0,), "os.chown": (0,)}


def _under(path, roots):
    return any(path == r or path.startswith(r + os.sep) for r in roots)


def _writable(path):
    if isinstance(path, bytes):
        path = os.fsdecode(path)
    real = os.path.realpath(path)
    if _under(real, RO):
        return False
    if _under(real, RW):
        return True
    return not CFG["read_only"]


def _deny(path):
    raise PermissionError(errno.EROFS, "Read-only file system", path)


def hook(event, args):
    if event == "open":
        path, mode, flags = args
        if isinstance(path, int) or path is None:
            return
        wants = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool((flags or 0) & WRITE_FLAGS)
        if wants and not _writable(path):
            _deny(path)
    elif event in PATH_EVENTS:
        for i in PATH_EVENTS[event]:
            if i < len(args) and isinstance(args[i], (str, bytes)) and not _writable(args[i]):
                _deny(args[i])
    elif event == "socket.connect" and CFG["network"] == "none":
        raise OSError(errno.ENETUNREACH, "Network is unreachable")


def _run(path):
    """Run the script at ``path`` as ``__main__``, as ``python path`` names it: ``__name__``, ``__file__``, the
    file's name in tracebacks. Its directory is not put on ``sys.path`` (this process is isolated, ``-I``; nor
    did ``runpy.run_path`` put it there)."""
    with open(path, "rb") as fh:
        code = compile(fh.read(), path, "exec")
    exec(code, {"__name__": "__main__", "__file__": path, "__builtins__": __builtins__})


sys.addaudithook(hook)
sys.argv = REST
_run(sys.argv[0])
