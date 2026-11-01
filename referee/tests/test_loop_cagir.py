"""Test 46 (asama-0/09), MF17, D4: the ``cagir`` job (``loop.job run cagir``, ``loop.cagir``), MF15's call on the
``pulled`` artifact, with the fake ``claude`` CLI (``fake_claude.py``, test 37's).

- the call: one process, the referee's own template with the target's id as typed input (the prompt on stdin, the
  id in its RFC 8785 form), the model and pin of the job's environment, ``--max-budget-usd`` the canary's
  ``canary_usd`` less what ``state/ledger.jsonl``'s cost rows spent (an integer and a fraction of USD, exact);
- the response: written whatever the outcome (``ok``, a served model that is not the requested one), its one
  ``cost`` row with the run's ``row_id``, the clock's ``ts`` and ``brain/integration``'s head, appended by
  ``ledger.append`` onto the ledger ``pulled`` carries (D6's input); the job ends ``ok`` with ``done`` ``["D4"]``;
- not sent, response written without a row: the stage brake (the ledger's spend at the cap), a secret pattern in the
  prompt (a target id shaped like a token);
- nothing started and nothing written: a refused ``pulled`` (``pulled_invalid``, exit 1); a ``canary_usd`` that is
  absent, ``true``, a string or negative, a ledger in ``pulled`` that is not a chain, a CLI that is not the pinned
  one, no CLI on ``PATH``, an unset variable and an existing ``out/response`` (no verdict, exit 2).
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fake_claude  # noqa: E402
from dispatcher import llm_call as L  # noqa: E402
from ledger import append  # noqa: E402
from loop import cagir as CG  # noqa: E402
from loop import job as J  # noqa: E402
from test_kos import operating  # noqa: E402
from test_loop_kos import HEADS, Base, state_files  # noqa: E402

from test_llm_call import MODEL, TOKEN  # noqa: E402  (test 37's model and token-shaped value, one source)

NOW = datetime.datetime(2026, 11, 1, 13, 30, 5, tzinfo=datetime.timezone.utc)
OUTPUT = {"echo": "t1"}


def result(**over) -> str:
    base = {"type": "result", "subtype": "success", "is_error": False, "result": "", "stop_reason": "end_turn",
            "total_cost_usd": 0.0123451, "modelUsage": {MODEL: {"costUSD": 0.0123451}}, "structured_output": OUTPUT}
    base.update(over)
    return json.dumps(base)


def policy(canary: str = "1") -> bytes:
    """``policy.json`` with ``canary_usd`` written as the JSON text ``canary`` (so ``0.5`` is a JSON fraction)."""
    return ('{"operating": %s, "stage_budgets": {"asama_0": {"canary_usd": %s}}}'
            % (json.dumps(operating()), canary)).encode()


def ledger_with_costs(*costs: int) -> list[dict]:
    rows = [{"row_id": "g1", "part": "genesis", "kind": "genesis", "payload": {}}]
    return rows + [{"row_id": "c%d" % i, "part": "cost", "kind": "cost", "payload": {"usd_micros": c}}
                   for i, c in enumerate(costs)]


class CagirJob(Base):
    def setUp(self) -> None:
        super().setUp()
        self.bin = os.path.join(self.base, "bin")
        os.makedirs(self.bin)
        self.claude = fake_claude.install(self.bin)
        fake_claude.behave(self.bin, result())
        self.env = {"RUNNER_TEMP": self.temp, "CLAUDE_CODE_OAUTH_TOKEN": TOKEN, "LOOP_CANARY_MODEL": MODEL,
                    "LOOP_CLAUDE_SHA512": L.sha512_file(self.claude), "GITHUB_RUN_ID": "77",
                    "GITHUB_RUN_ATTEMPT": "2", "PATH": self.bin + os.pathsep + os.environ.get("PATH", "")}

    def write(self, canary: str = "1", ledger: list[dict] | None = None, **kw) -> None:
        state = state_files(ledger) if ledger is not None else None
        self.write_pulled(policy=policy(canary), state=state, **kw)

    def run_cagir(self, **env) -> dict:
        environ = {k: v for k, v in dict(self.env, **env).items() if v is not None}
        return J.run("cagir", environ, now=lambda: NOW)

    @property
    def out(self) -> str:
        return os.path.join(self.temp, "out", "response")

    def response(self) -> dict:
        with open(os.path.join(self.out, CG.RESPONSE)) as fh:
            return json.load(fh)

    def calls(self) -> list[dict]:
        return fake_claude.calls(self.bin)

    def assert_nothing(self) -> None:
        self.assertEqual(self.calls(), [])
        self.assertFalse(os.path.lexists(self.out))

    def no_verdict(self, **env) -> None:
        with self.assertRaises(J.Unusable):
            self.run_cagir(**env)
        self.assert_nothing()

    def test_the_canary_call_and_its_response(self):
        ledger = ledger_with_costs(200_000, 50_000)
        self.write(ledger=ledger)
        out = self.run_cagir()
        self.assertEqual((out["ok"], out["done"], out["job"]), (True, ["D4"], "cagir"))
        self.assertEqual(out["call"], {"outcome": "ok", "reason": None, "sent": True, "models_served": [MODEL],
                                       "cost_usd_micros": 12346})
        [call] = self.calls()
        # the prompt, written out by hand: the template's text with the id in its JSON form, on stdin only
        prompt = ('This is the canary call of the Snowball loop for the target "t1". Reply only with the '
                  'structured output: echo is the target\'s name as given, without quotes.')
        self.assertEqual(call["stdin"], prompt)
        self.assertNotIn(prompt, " ".join(call["argv"]))
        argv = call["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], MODEL)
        # canary_usd 1 USD, the ledger's cost rows spent 0.25 of it: the call may spend the rest
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.750000")
        self.assertEqual(call["env"]["CLAUDE_CODE_OAUTH_TOKEN"], TOKEN)
        got = self.response()
        [row] = got["rows"]
        self.assertEqual({k: got[k] for k in ("schema", "target", "heads", "outcome", "reason", "sent", "run_valid",
                                              "output", "models_served", "cost_usd_micros", "dropped")},
                         {"schema": "snowball-response/1", "target": "t1", "heads": HEADS, "outcome": "ok",
                          "reason": None, "sent": True, "run_valid": True, "output": OUTPUT,
                          "models_served": [MODEL], "cost_usd_micros": 12346, "dropped": []})
        self.assertEqual((row["row_id"], row["ts"], row["snapshot_id"], row["part"], row["kind"]),
                         ("cagir-77-2", "2026-11-01T13:30:05Z", HEADS["brain/integration"], "cost", "cost"))
        self.assertEqual((row["payload"]["usd_micros"], row["payload"]["cap_usd_micros"],
                          row["payload"]["model_requested"], row["payload"]["prompt_sha256"]),
                         (12346, 750_000, MODEL, got["prompt_sha256"]))
        # D6's input: the rows go onto the ledger pulled carries, through ledger.append's own rules
        led = state_files(ledger)["ledger.jsonl"]
        cycle = append.plan_cycle(led, led, lambda: json.dumps({"rows": got["rows"]}).encode())
        self.assertEqual(len(cycle.row_hashes), 1)
        self.assertEqual(L.spent_micros([json.loads(x) for x in cycle.content.splitlines()]), 262_346)

    def test_a_fraction_of_a_dollar_is_exact(self):
        # the JSON text's exact value rounded up to a micro-USD (llm_call.to_micros), never through a float
        for canary, cap in (("0.5", "0.500000"), ("0.0000005", "0.000001"), ("5e-1", "0.500000")):
            with self.subTest(canary=canary):
                shutil.rmtree(self.temp, ignore_errors=True)
                if self.calls():
                    os.remove(os.path.join(self.bin, "calls.jsonl"))
                self.write(canary=canary)
                self.run_cagir()
                argv = self.calls()[0]["argv"]
                self.assertEqual(argv[argv.index("--max-budget-usd") + 1], cap)

    def test_another_served_model_is_written_and_not_ok(self):
        fake_claude.behave(self.bin, result(modelUsage={"claude-haiku-5-5": {"costUSD": 0.001}}))
        self.write()
        out = self.run_cagir()
        self.assertEqual((out["ok"], out["done"]), (True, ["D4"]))
        got = self.response()
        self.assertEqual((got["outcome"], got["reason"], got["run_valid"]), ("unresolved", "model_mismatch", False))
        self.assertEqual([r["payload"]["models_served"] for r in got["rows"]], [["claude-haiku-5-5"]])

    def test_the_brake_sends_nothing_and_writes_no_row(self):
        self.write(ledger=ledger_with_costs(600_000, 400_000))
        out = self.run_cagir()
        self.assertEqual((out["ok"], out["call"]["outcome"], out["call"]["sent"]), (True, "brake", False))
        self.assertEqual(self.calls(), [])
        self.assertEqual((self.response()["rows"], self.response()["reason"]), ([], "stage_brake"))

    def test_a_secret_in_the_prompt_is_not_sent(self):
        self.write(target={"id": "ghp_" + "A1b2C3d4" * 4 + "Zz9Y", "kind": "toy", "excluded_paths": [],
                           "unit_candidates": []})
        out = self.run_cagir()
        self.assertEqual((out["call"]["outcome"], out["call"]["sent"]), ("secret", False))
        self.assertEqual((self.calls(), self.response()["rows"]), ([], []))

    def test_a_refused_pulled_starts_nothing(self):
        self.write()
        with open(os.path.join(self.pulled, "state", "ledger.jsonl"), "ab") as fh:
            fh.write(b"\n")
        out = self.run_cagir()
        self.assertEqual((out["ok"], out["reason"], out["reasons"]), (False, "pulled_invalid",
                                                                      ["hash_mismatch:state/ledger.jsonl"]))
        self.assert_nothing()

    def test_a_canary_budget_that_is_no_amount_is_no_verdict(self):
        for canary in ("true", '"1"', "-1", "null"):
            with self.subTest(canary=canary):
                shutil.rmtree(self.pulled, ignore_errors=True)
                self.write(canary=canary)
                self.no_verdict()
        shutil.rmtree(self.pulled)
        self.write_pulled(policy={"operating": operating()})
        self.no_verdict()

    def test_a_ledger_that_is_not_a_chain_is_no_verdict(self):
        state = state_files(ledger_with_costs(1))
        state["ledger.jsonl"] = state["ledger.jsonl"].replace(b'"usd_micros": 1', b'"usd_micros": 0')
        self.write_pulled(policy=policy(), state=state)
        self.no_verdict()

    def test_the_pin_the_path_and_the_environment(self):
        self.write()
        self.no_verdict(LOOP_CLAUDE_SHA512="0" * 128)
        self.no_verdict(PATH=os.path.join(self.base, "nowhere"))
        for name in J.CAGIR_ENV:
            with self.subTest(unset=name):
                self.no_verdict(**{name: None})
        os.makedirs(self.out)
        with self.assertRaises(J.Unusable):
            self.run_cagir()
        self.assertEqual((self.calls(), os.listdir(self.out)), ([], []))


if __name__ == "__main__":
    unittest.main()
