"""Test 9 of asama-0/09 (P1 MF5): the harness reaches no model.

**Test 9** (``harness.offline``): ``Static`` binds each reason of ``check`` on small trees and reads the brain's own
tree; ``Guard`` binds ``run`` (each refused event with the real call that raises it, the swallowed event, the nested
run, the guard idle outside); ``Command`` the command's exits; ``Live`` the loop's use of both on the rehearsal's
world (``test_rehearsal.Flow``): a harness that imports the client refuses the target before anything of it is read,
and each of the four judgements, made to open a socket and go on, stops its target with ``harness_online`` and
leaves ``brain/state`` where it was (each in the first run of the rehearsal that makes that judgement).
``CostData`` binds the move that made the brain's tree pass (the cost section's data is ``ledger.cost``'s, the
client only names it).

Out of scope, stated: the machine's network (nothing here closes it; the guard refuses this process's own events);
the real GitHub and model (``fake_github``, ``fake_claude``).
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import unittest
import urllib.request
from fractions import Fraction
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_rehearsal as R  # noqa: E402
from dispatcher import llm_call as LC  # noqa: E402
from harness import offline as OF  # noqa: E402
from harness import stats as ST  # noqa: E402
from ledger import cost as CO  # noqa: E402
from ledger import schema as SC  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from status import block as SB  # noqa: E402
from status import pygraph  # noqa: E402

CLEAN = {"harness/__init__.py": "", "harness/score.py": "import json\nfrom ledger import chain\n",
         "harness/stats.py": "import math\n",
         "ledger/__init__.py": "", "ledger/chain.py": "import hashlib\n",
         "dispatcher/__init__.py": "", "dispatcher/llm_call.py": "import subprocess\nimport anthropic\n",
         "loop/__init__.py": "", "loop/job.py": "from dispatcher import llm_call\nfrom harness import score\n"}
VIA_CHAIN = "client_import:ledger.chain:dispatcher.llm_call"


class Trees(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-offline-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def tree(self, **changed: str | bytes) -> str:
        """``CLEAN`` with ``changed`` (a path without ``.py``, its first ``/`` written ``__``) under a new root."""
        root = os.path.join(self.base, "r%d" % len(os.listdir(self.base)))
        files = dict(CLEAN, **{k.replace("__", "/", 1) + ".py": v for k, v in changed.items()})
        return write_tree(root, files) or root

    def reasons(self, **changed: str | bytes) -> list[str]:
        return OF.check(self.tree(**changed))["reasons"]


class Static(Trees):
    def test_a_harness_that_reaches_no_client_is_clean(self):
        """The client is in the tree and the loop imports it: neither is reached from the harness."""
        self.assertEqual(OF.check(self.tree()),
                         {"roots": ["harness", "harness.score", "harness.stats"], "modules": 5, "reasons": []})

    def test_a_direct_import_of_the_client(self):
        for line in ("from dispatcher import llm_call\n", "import dispatcher.llm_call\n",
                     "import dispatcher.llm_call as c\n", "from dispatcher.llm_call import plan\n",
                     "from dispatcher import llm_call as c\n"):
            self.assertEqual(self.reasons(harness__stats=line), ["client_import:harness.stats:dispatcher.llm_call"],
                             line)

    def test_the_client_package_itself(self):
        self.assertEqual(self.reasons(harness__stats="import dispatcher\n"),
                         ["client_import:harness.stats:dispatcher"])

    def test_an_import_inside_a_function_or_a_branch(self):
        for source in ("def f():\n    from dispatcher import llm_call\n    return llm_call\n",
                       "try:\n    import json\nexcept ImportError:\n    from dispatcher import llm_call\n",
                       "class C:\n    def m(self):\n        import dispatcher.llm_call\n"):
            self.assertEqual(self.reasons(harness__stats=source),
                             ["client_import:harness.stats:dispatcher.llm_call"], source)

    def test_a_client_reached_through_another_module(self):
        self.assertEqual(self.reasons(ledger__chain="from dispatcher import llm_call\n"), [VIA_CHAIN])

    def test_a_client_reached_through_three_modules_and_a_relative_import(self):
        got = self.reasons(harness__stats="from . import deep\n", harness__deep="from ledger import far\n",
                           ledger__far="from . import farther\n",
                           ledger__farther="from dispatcher import llm_call\n")
        self.assertEqual(got, ["client_import:ledger.farther:dispatcher.llm_call"])

    def test_a_client_reached_through_a_package_init(self):
        """Importing ``ledger.chain`` runs ``ledger/__init__.py``."""
        self.assertEqual(self.reasons(ledger____init__="from dispatcher import llm_call\n"),
                         ["client_import:ledger:dispatcher.llm_call"])

    def test_the_harness_init_is_a_harness_module(self):
        self.assertEqual(self.reasons(harness____init__="from dispatcher import llm_call\n"),
                         ["client_import:harness:dispatcher.llm_call"])

    def test_every_importer_is_reported_once_and_sorted(self):
        line = "from dispatcher import llm_call\nfrom dispatcher import llm_call\n"
        self.assertEqual(self.reasons(harness__stats=line, ledger__chain=line),
                         ["client_import:harness.stats:dispatcher.llm_call", VIA_CHAIN])

    def test_the_client_is_not_read_further(self):
        """The client's own lines (``CLEAN``'s imports a foreign name; here it does not parse) give no reason."""
        self.assertEqual(self.reasons(ledger__chain="from dispatcher import llm_call\n",
                                      dispatcher__llm_call="def (:\n"), [VIA_CHAIN])

    def test_a_foreign_import(self):
        for line, name in (("import anthropic\n", "anthropic"), ("from openai.types import x\n", "openai"),
                           ("import requests.sessions as s\n", "requests"),
                           ("def f():\n    import httpx\n", "httpx")):
            self.assertEqual(self.reasons(ledger__chain=line), ["foreign_import:ledger.chain:%s" % name], line)

    def test_the_standard_library_is_not_foreign(self):
        self.assertEqual(self.reasons(ledger__chain="import urllib.request\nimport subprocess, socket\n"
                                                    "from http import client\n"), [])

    def test_a_dynamic_import(self):
        for line, name in (("import importlib\n", "importlib"), ("from importlib import import_module\n", "importlib"),
                           ("import importlib.util\n", "importlib"), ("import runpy\n", "runpy"),
                           ("import pkgutil\n", "pkgutil"), ("import zipimport\n", "zipimport"),
                           ("def f(n):\n    return __import__(n)\n", "__import__"),
                           ("load = __import__\n", "__import__")):
            self.assertEqual(self.reasons(ledger__chain=line), ["dynamic_import:ledger.chain:%s" % name], line)

    def test_the_import_function_named_in_any_place(self):
        """An identifier wherever the grammar has one, and a whole ``str`` or ``bytes`` literal (the referee's
        refutation of 9b7db67 was the second line: an attribute was not read)."""
        for source in ('c = __import__("dispatcher.llm_call")\n',
                       'import builtins\nc = builtins.__import__("dispatcher.llm_call")\n',
                       'c = __builtins__.__import__("dispatcher.llm_call")\n',
                       "from builtins import __import__ as load\n",
                       "from builtins import __import__\n",
                       'import builtins\nc = getattr(builtins, "__import__")("dispatcher.llm_call")\n',
                       'import builtins\nc = getattr(builtins, b"__import__".decode())\n',
                       'c = __builtins__["__import__"]\n',
                       'import builtins\nc = vars(builtins).get(\'__import__\')\n',
                       'import operator, builtins\nc = operator.attrgetter("""__import__""")(builtins)\n',
                       'import builtins\nc = builtins.__\uff49mport__("dispatcher.llm_call")\n',   # NFKC: i
                       "def f():\n    global __import__\n",
                       "def f(__import__):\n    return 1\n",
                       "f = dict(__import__=1)\n",
                       "import builtins\nmatch builtins:\n    case object(__import__=load):\n        pass\n",
                       "class C:\n    def m(self):\n        return [x.__import__ for x in ()]\n"):
            self.assertEqual(self.reasons(ledger__chain=source), ["dynamic_import:ledger.chain:__import__"], source)
            self.assertEqual(self.reasons(harness__stats=source), ["dynamic_import:harness.stats:__import__"],
                             source)

    def test_the_import_functions_name_inside_a_longer_literal_or_a_comment_is_not_a_reason(self):
        """The rule's other edge, stated in the module: only a whole literal, never prose that mentions it."""
        for source in ('"""This module never calls ``__import__``."""\n', "x = 1  # not __import__\n",
                       'x = "see __import__"\n', 'x = b" __import__"\n', "x = '__import__ '\n",
                       "__imports__ = 1\n", "x = '__IMPORT__'\n"):
            self.assertEqual(self.reasons(ledger__chain=source), [], source)

    def test_the_referees_reproducer_on_9b7db67(self):
        """The tree of the refutation, through the command: exit 1, ``ok`` false, the one reason."""
        root = write_tree(os.path.join(self.base, "ofl"), {
            "harness/__init__.py": "", "dispatcher/__init__.py": "", "dispatcher/llm_call.py": "import subprocess\n",
            "harness/score.py": 'import builtins\nc = builtins.__import__("dispatcher.llm_call")\n',
        }) or os.path.join(self.base, "ofl")
        got = subprocess.run([sys.executable, "-m", "harness.offline", root], cwd=REFEREE, capture_output=True,
                             text=True, timeout=60)
        self.assertEqual((got.returncode, got.stderr), (1, ""))
        self.assertEqual(json.loads(got.stdout), {"modules": 2, "ok": False, "roots": ["harness", "harness.score"],
                                                  "reasons": ["dynamic_import:harness.score:__import__"]})

    def test_a_module_that_cannot_be_read_as_python(self):
        for data in ("def (:\n", b"x = '\xff'\n", "x = 1\0\n"):
            self.assertEqual(self.reasons(ledger__chain=data), ["unparsed:ledger/chain.py"], data)
            self.assertEqual(self.reasons(harness__stats=data), ["unparsed:harness/stats.py"], data)

    def test_a_module_outside_the_harness_closure_is_not_judged(self):
        self.assertEqual(self.reasons(loop__job="def (:\n", loop__other="import anthropic, importlib\n"), [])

    def test_a_root_without_the_harness(self):
        root = write_tree(os.path.join(self.base, "none"), {"ledger/chain.py": "import hashlib\n"}) or \
            os.path.join(self.base, "none")
        self.assertEqual(OF.check(root), {"roots": [], "modules": 0, "reasons": ["no_harness_module"]})
        self.assertEqual(OF.check(os.path.join(self.base, "absent"))["reasons"], ["no_harness_module"])

    def test_the_brains_own_harness_is_clean(self):
        got = OF.check(REFEREE)
        self.assertEqual(got["reasons"], [])
        self.assertEqual(got["roots"], ["harness", "harness.offline", "harness.pass_row", "harness.revert_drill",
                                        "harness.score", "harness.stats"])
        self.assertGreater(got["modules"], len(got["roots"]))

    def test_the_brains_own_tree_with_the_client_named_again(self):
        """What this micro feature found and moved: ``ledger.schema`` (which the PASS row's judge reaches) naming
        the client. On a copy of ``referee/``'s Python the same line is a reason."""
        root = os.path.join(self.base, "copy")
        for rel in pygraph.python_modules(REFEREE).values():
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(REFEREE, rel), os.path.join(root, rel))
        self.assertEqual(OF.check(root)["reasons"], [])
        with open(os.path.join(root, "ledger", "schema.py"), "a", encoding="utf-8") as fh:
            fh.write("\nfrom dispatcher import llm_call\n")
        self.assertEqual(OF.check(root)["reasons"], ["client_import:ledger.schema:dispatcher.llm_call"])


def swallowed(touch):
    """A call that makes ``touch``'s event, catches whatever comes of it and answers ``"went on"``."""
    def call():
        try:
            touch()
        except BaseException:   # noqa: B036 -- the test's point: the call swallows everything
            pass
        return "went on"
    return call


def open_socket() -> None:
    socket.socket().close()


TOUCHES = {
    "socket.__new__": open_socket,
    "socket.getaddrinfo": lambda: socket.getaddrinfo("localhost", 80),
    "socket.gethostbyname": lambda: socket.gethostbyname("localhost"),
    "subprocess.Popen": lambda: subprocess.run([sys.executable, "-c", "pass"], check=True),
    "os.system": lambda: os.system("true"),
    "os.exec": lambda: os.execv(sys.executable, [sys.executable, "-c", "pass"]),
    "os.posix_spawn": lambda: os.posix_spawn(sys.executable, [sys.executable, "-c", "pass"], {}),
    "os.fork": lambda: os.fork() or os._exit(0),
}


class Guard(unittest.TestCase):
    def test_the_answer_of_a_call_that_stays_in_the_process(self):
        args = (Fraction(59), 60, Fraction(1, 10))
        self.assertEqual(OF.run(lambda: ST.cp_lower(*args)), ST.cp_lower(*args))
        self.assertEqual(OF.run(lambda: os.path.isdir(REFEREE)), True)

    def test_each_refused_event_raises_online_where_it_is_made(self):
        for event, touch in TOUCHES.items():
            with self.assertRaises(OF.Online, msg=event) as caught:
                OF.run(touch)
            self.assertEqual((caught.exception.events, caught.exception.reasons), ([event], ["event:" + event]))

    def test_an_event_the_call_swallowed_still_ends_in_online(self):
        for event, touch in TOUCHES.items():
            with self.assertRaises(OF.Online, msg=event) as caught:
                OF.run(swallowed(touch))
            self.assertEqual(caught.exception.events, [event])

    def test_the_events_of_one_run_are_sorted_and_each_once(self):
        def call():
            for name in ("subprocess.Popen", "socket.__new__", "socket.__new__", "os.system"):
                swallowed(TOUCHES[name])()
        with self.assertRaises(OF.Online) as caught:
            OF.run(call)
        self.assertEqual(caught.exception.events, ["os.system", "socket.__new__", "subprocess.Popen"])

    def test_urllib_cannot_fetch(self):
        with self.assertRaises(OF.Online) as caught:
            OF.run(swallowed(lambda: urllib.request.urlopen("http://127.0.0.1:9/", timeout=1)))
        self.assertTrue(all(e.startswith("socket.") for e in caught.exception.events), caught.exception.events)

    def test_the_guard_is_idle_outside_a_run(self):
        """Before, after a clean run, after a refused one and after a call that raised its own exception."""
        def works():
            open_socket()
            self.assertEqual(subprocess.run([sys.executable, "-c", "pass"]).returncode, 0)
        works()
        OF.run(lambda: None)
        works()
        with self.assertRaises(OF.Online):
            OF.run(open_socket)
        works()
        with self.assertRaises(ZeroDivisionError):
            OF.run(lambda: 1 // 0)
        works()

    def test_an_inner_runs_event_is_the_outer_runs_too(self):
        def outer():
            try:
                OF.run(open_socket)
            except OF.Online:
                pass
            return "went on"
        with self.assertRaises(OF.Online) as caught:
            OF.run(outer)
        self.assertEqual(caught.exception.events, ["socket.__new__"])

    def test_a_clean_inner_run_leaves_the_outer_guard_on(self):
        def outer():
            OF.run(lambda: None)
            swallowed(open_socket)()
        with self.assertRaises(OF.Online):
            OF.run(outer)

    def test_the_client_cannot_start_its_program_inside_a_run(self):
        """``dispatcher.llm_call`` reaches the model by starting a program: the start is what is refused."""
        with self.assertRaises(OF.Online) as caught:
            OF.run(swallowed(lambda: subprocess.Popen(["claude", "--version"])))
        self.assertEqual(caught.exception.events, ["subprocess.Popen"])


class Command(Trees):
    def command(self, *argv: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, "-m", "harness.offline", *argv], cwd=REFEREE, capture_output=True,
                              text=True)
        return proc.returncode, proc.stdout

    def test_exit_0_on_the_brains_own_tree_by_default(self):
        code, out = self.command()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), dict(OF.check(REFEREE), ok=True))

    def test_exit_1_with_the_reasons(self):
        code, out = self.command(self.tree(ledger__chain="from dispatcher import llm_call\n"))
        self.assertEqual((code, json.loads(out)["ok"], json.loads(out)["reasons"]), (1, False, [VIA_CHAIN]))

    def test_exit_2_on_any_other_argument_list(self):
        for argv in (("a", "b"), ("--root", ), ("-h",)):
            self.assertEqual(self.command(*argv), (2, ""), argv)


class CostData(unittest.TestCase):
    def test_the_client_names_the_ledgers_cost_data(self):
        self.assertIs(LC.Unusable, CO.Unusable)
        self.assertIs(LC.spent_micros, CO.spent_micros)
        self.assertEqual((LC.PART, LC.KIND, LC.OUTCOMES), (CO.PART, CO.KIND, CO.OUTCOMES))

    def test_the_schema_and_the_status_block_do_not_import_the_client(self):
        modules = pygraph.python_modules(REFEREE)
        for module in (SC, SB, CO):
            with open(module.__file__, encoding="utf-8") as fh:
                imported = pygraph.module_imports(fh.read(), module.__name__, False, modules)
            self.assertEqual([m for m in imported if m.startswith("dispatcher")], [], module.__name__)


def touching(real):
    """``real`` after a socket was opened and the refusal swallowed: a judgement that went online and went on."""
    def judgement(*args, **kwargs):
        swallowed(open_socket)()
        return real(*args, **kwargs)
    return judgement


class Live(Trees):
    def stopped(self, flow: R.Flow, run: int = 1) -> dict:
        """``run`` runs of the flow: none before the last is stopped, and the last one's ``stopped``."""
        for n in range(1, run + 1):
            record = R.Flow.record(flow.run())
            if n < run:
                self.assertNotIn("stopped", record, n)
        self.assertIn("stopped", record, record)
        return record["stopped"]

    def test_a_harness_that_imports_the_client_refuses_the_target_before_it_is_read(self):
        root = self.tree(ledger__chain="from dispatcher import llm_call\n")
        flow = R.without_fixtures(os.path.join(self.base, "flow"))
        with mock.patch.object(R.J, "CODE_ROOT", root), \
                mock.patch.object(R.J, "yaz_d5", side_effect=AssertionError("the target was read")):
            stopped = self.stopped(flow)
        self.assertEqual(stopped, {"job": "yaz", "target": "t1", "reason": "harness_online", "reasons": [VIA_CHAIN]})
        self.assertEqual(flow.state_heads, [None])
        self.assertEqual(sorted(flow.hubs["o/toy"].refs), ["main"])

    def test_the_loop_reads_the_code_it_runs(self):
        self.assertEqual(R.J.CODE_ROOT, REFEREE)
        self.assertEqual(R.J.yaz_offline(), OF.check(REFEREE))

    def judged_online(self, holder, name: str, run: int, patched=None) -> None:
        """``holder.name`` (the judgement as its caller names it) going online stops the toy in run ``run`` (the
        first that makes that judgement) with ``harness_online``, and that run does not move ``brain/state``."""
        flow = R.with_fixtures(os.path.join(self.base, "flow"))
        with patched or mock.patch.object(holder, name, touching(getattr(holder, name))):
            stopped = self.stopped(flow, run)
        self.assertEqual(stopped, {"job": "yaz", "target": "t1", "reason": "harness_online",
                                   "reasons": ["event:socket.__new__"]})
        self.assertEqual(flow.state_heads[-1], flow.state_heads[-2] if run > 1 else None)

    def test_the_scorer_going_online_stops_the_genesis(self):
        self.judged_online(R.J.HS, "report", 1)

    def test_the_copys_gate_going_online_stops_the_cycle(self):
        self.judged_online(R.PR, "gate", 2)

    def test_the_drills_judge_going_online_stops_the_cycle(self):
        """Only ``loop.drill``'s own call goes online here (the gate's judge reads ``harness.revert_drill.judge``
        too, inside its own ``run``): ``loop.drill`` sees the module with ``judge`` replaced."""
        class Drill:
            judge = staticmethod(touching(R.RD.judge))

            def __getattr__(self, name):
                return getattr(R.RD, name)
        self.judged_online(None, "judge", 5, mock.patch.object(R.DR, "RD", Drill()))

    def test_the_pass_rows_judge_going_online_stops_the_cycle(self):
        self.judged_online(R.PR, "judge", 13)


if __name__ == "__main__":
    unittest.main()
