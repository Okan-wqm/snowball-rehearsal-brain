"""Test 46 (asama-0/09), MF17: the loop workflow ``referee/.github/workflows/loop.yml``.

The rules are read from the spec, not from ``loop.job`` (``violations`` below does not import it), so a mistake
in the registry or the emitter shows as a violation of the committed file:

- ``top_permissions``: the top-level ``permissions`` is ``{}``; ``workflow_env``/``job_env``: no ``env`` above a
  step (a secret there would reach every step);
- ``trigger``: ``on`` is only ``schedule`` and ``workflow_dispatch`` (so never ``pull_request_target``,
  ``workflow_run``, ``issue_comment``, ``push``, ``pull_request``);
- ``job_set``: exactly the five jobs of tohum/08 (``cek``, ``getir``, ``kos``, ``cagir``, ``yaz``);
- ``job_not_main``: every job's ``if`` is exactly ``github.ref == 'refs/heads/main'``;
- ``first_step_control``: every job's first step has id ``control``, no ``uses`` and no ``if``, and runs the
  seed's ``python3 -m snowball_bootstrap control``; ``control_elsewhere``: no later step runs it;
- ``step_not_gated``: every later step's ``if`` is exactly ``steps.control.outputs.go == 'true'``, and
  ``continue_on_error``: nothing continues on error, so a failing ``control`` (kill switch) stops the job;
- ``github_expr_in_run``: no ``${{`` holding ``github`` in any ``run:`` (``expr_in_run``: no ``${{`` at all);
- ``unpinned_action``: every ``uses`` is ``owner/repo@<40 hex>``; ``persist_credentials``: every checkout has
  ``persist-credentials: false``;
- ``permissions_missing``: every job states its permissions; ``code_job_permissions`` and
  ``secret_in_code_job``: ``getir`` and ``kos`` (the jobs that run code) have ``permissions: {}`` and no
  ``secrets.``/``github.token`` expression; ``secret_outside``: secrets appear only in ``cagir``
  (``CLAUDE_CODE_OAUTH_TOKEN`` only) and ``yaz``;
- ``secret_job_runs_code``: a job holding a secret or a permission uses only checkout of its own commit
  (``foreign_checkout`` otherwise), the artifact actions and (``yaz``) the App token action, and runs only
  ``control`` and its ``python3 -m loop.job run <job>``; ``unknown_run``: the same for the code jobs.

Each rule is shown to fire on a mutated copy of the committed file and not on the file itself. Also: the file
is ``loop.job.render()`` byte for byte (and the CLI's output); the parser's subset refusals; the registry covers
D1-D8 and the step table's MFs; the gating, run under a model of Actions' step and job conditions, stops every
job at a failing ``control`` and ends a paused job green with nothing run; ``python -m loop.job run``'s refusal
of a secret in a code job and its ``cycle_not_wired`` stop (``kos``'s, after D3, in ``test_loop_kos.py``).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_yaml import Unparseable, parse  # noqa: E402

WORKFLOW = os.path.join(REFEREE, ".github", "workflows", "loop.yml")

JOBS = ("cek", "getir", "kos", "cagir", "yaz")         # tohum/08 item 1
CODE_JOBS = ("getir", "kos")                            # run code: no secret, no permission
SECRETS_ALLOWED = {"cagir": {"CLAUDE_CODE_OAUTH_TOKEN"}, "yaz": None}  # None: any (writer App, OIDC)
MAIN = "github.ref == 'refs/heads/main'"
GATE = "steps.control.outputs.go == 'true'"
CONTROL = re.compile(r"(?m)^python3 -m snowball_bootstrap control( |$)")
PIN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(/[A-Za-z0-9_./-]+)?@[0-9a-f]{40}")
SECRET_EXPR = re.compile(r"\$\{\{\s*(secrets\.([A-Za-z0-9_]+)|github\.token)")
SECRET_JOB_ACTIONS = ("actions/checkout@", "actions/download-artifact@", "actions/upload-artifact@")
APP_ACTION = "actions/create-github-app-token@"


def committed() -> str:
    with open(WORKFLOW, encoding="utf-8") as fh:
        return fh.read()


def _strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def violations(doc: dict) -> list[str]:
    out: list[str] = []
    if doc.get("permissions") != {}:
        out.append("top_permissions")
    if "env" in doc:
        out.append("workflow_env")
    triggers = doc.get("on")
    if not isinstance(triggers, dict) or not triggers or set(triggers) - {"schedule", "workflow_dispatch"}:
        out.append("trigger")
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict) or tuple(sorted(jobs)) != tuple(sorted(JOBS)):
        out.append("job_set")
    for name, job in (jobs or {}).items():
        where = ":" + name
        if not isinstance(job, dict):
            out.append("job_set" + where)
            continue
        if job.get("if") != MAIN:
            out.append("job_not_main" + where)
        if "env" in job:
            out.append("job_env" + where)
        if "continue-on-error" in job:
            out.append("continue_on_error" + where)
        if "permissions" not in job:
            out.append("permissions_missing" + where)
        perms = job.get("permissions")
        secrets = {m.group(2) or "github.token" for s in _strings(job) for m in SECRET_EXPR.finditer(s)}
        holds_secret = bool(secrets) or perms not in ({}, None)
        if name in CODE_JOBS:
            if perms != {}:
                out.append("code_job_permissions" + where)
            if secrets:
                out.append("secret_in_code_job" + where)
        elif secrets:
            allowed = SECRETS_ALLOWED.get(name, set())
            if allowed is not None and not secrets <= allowed:
                out.append("secret_outside" + where)
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            out.append("first_step_control" + where)
            continue
        first = steps[0]
        if not (isinstance(first, dict) and first.get("id") == "control" and "uses" not in first
                and "if" not in first and isinstance(first.get("run"), str) and CONTROL.search(first["run"])):
            out.append("first_step_control" + where)
        for index, step in enumerate(steps):
            at = "%s:%d" % (where, index)
            if not isinstance(step, dict):
                out.append("step_shape" + at)
                continue
            if "continue-on-error" in step:
                out.append("continue_on_error" + at)
            run, uses = step.get("run"), step.get("uses")
            if isinstance(run, str) and "${{" in run:
                out.append(("github_expr_in_run" if re.search(r"\$\{\{[^}]*github", run) else "expr_in_run") + at)
            if index == 0:
                continue
            if step.get("if") != GATE:
                out.append("step_not_gated" + at)
            if isinstance(run, str):
                if CONTROL.search(run):
                    out.append("control_elsewhere" + at)
                if run != "python3 -m loop.job run %s\n" % name:
                    out.append(("secret_job_runs_code" if holds_secret else "unknown_run") + at)
            if uses is not None:
                if not isinstance(uses, str) or not PIN.fullmatch(uses):
                    out.append("unpinned_action" + at)
                    continue
                allowed_actions = SECRET_JOB_ACTIONS + ((APP_ACTION,) if name == "yaz" else ())
                if holds_secret and not uses.startswith(allowed_actions):
                    out.append("secret_job_runs_code" + at)
                if uses.startswith("actions/checkout@"):
                    given = step.get("with") or {}
                    if given.get("persist-credentials") != "false":
                        out.append("persist_credentials" + at)
                    if set(given) - {"persist-credentials"}:
                        out.append("foreign_checkout" + at)
    return out


def rules(text: str) -> set[str]:
    return {v.split(":")[0] for v in violations(parse(text))}


class Committed(unittest.TestCase):
    def test_file_is_the_registry_rendered(self):
        from loop import job
        self.assertEqual(committed(), job.render())
        self.assertEqual(parse(committed()), job.workflow())

    def test_cli_render_is_the_file(self):
        proc = subprocess.run([sys.executable, "-m", "loop.job", "render"], cwd=REFEREE, capture_output=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.decode("utf-8"), committed())

    def test_file_keeps_every_rule(self):
        self.assertEqual(violations(parse(committed())), [])

    def test_file_shape(self):
        doc = parse(committed())
        self.assertEqual(set(doc["on"]), {"schedule", "workflow_dispatch"})
        for name in JOBS:
            steps = doc["jobs"][name]["steps"]
            self.assertEqual(steps[0]["id"], "control")
            self.assertEqual(steps[0]["env"], {"LOOP_JOB": name})
            self.assertIn({"name": name, "if": GATE, "run": "python3 -m loop.job run %s\n" % name},
                          [{k: s[k] for k in ("name", "if", "run") if k in s} for s in steps])
        self.assertEqual(doc["jobs"]["kos"]["permissions"], {})
        self.assertEqual(doc["jobs"]["yaz"]["permissions"], {"id-token": "write", "contents": "read"})


def _sub(text: str, old: str, new: str, count: int = 1) -> str:
    assert old in text, old
    return text.replace(old, new, count)


def _job(text: str, name: str) -> tuple[int, int]:
    start = text.index("\n  %s:\n" % name) + 1
    nxt = re.search(r"\n  [a-z]+:\n", text[start + 1:])
    return start, (start + 1 + nxt.start() + 1) if nxt else len(text)


def _in_job(text: str, name: str, old: str, new: str) -> str:
    start, end = _job(text, name)
    return text[:start] + _sub(text[start:end], old, new) + text[end:]


class EachRuleFires(unittest.TestCase):
    """Each mutation breaks one rule of test 46; the rule must fire and the committed file must not."""

    def fires(self, rule: str, text: str):
        self.assertNotIn(rule, rules(committed()))
        self.assertIn(rule, rules(text), text if len(text) < 400 else rule)

    def test_top_permissions(self):
        self.fires("top_permissions", _sub(committed(), "permissions: {}\nconcurrency",
                                           "permissions:\n  contents: write\nconcurrency"))
        self.fires("top_permissions", _sub(committed(), "permissions: {}\nconcurrency", "concurrency"))

    def test_env_above_steps(self):
        self.fires("workflow_env", _sub(committed(), "permissions: {}\n",
                                        "permissions: {}\nenv:\n  T: ${{ secrets.T }}\n"))
        self.fires("job_env", _in_job(committed(), "cek", "    runs-on:", "    env:\n      A: b\n    runs-on:"))

    def test_triggers(self):
        for event in ("pull_request_target", "workflow_run", "issue_comment", "push", "pull_request"):
            with self.subTest(event=event):
                self.fires("trigger", _sub(committed(), "  workflow_dispatch: {}\n",
                                           "  workflow_dispatch: {}\n  %s: {}\n" % event))

    def test_job_set(self):
        self.fires("job_set", committed() + "  extra:\n    if: x\n    steps: []\n")
        start, end = _job(committed(), "cagir")
        self.fires("job_set", committed()[:start] + committed()[end:])

    def test_job_only_on_main(self):
        self.fires("job_not_main", _in_job(committed(), "yaz", "    if: github.ref == 'refs/heads/main'\n",
                                           "    if: always()\n"))
        self.fires("job_not_main", _in_job(committed(), "getir", "    if: github.ref == 'refs/heads/main'\n", ""))

    def test_first_step_is_control(self):
        text = committed()
        start, end = _job(text, "kos")
        block = text[start:end]
        control = block[block.index("      - name: control\n"):block.index("      - name: checkout\n")]
        checkout = block[block.index("      - name: checkout\n"):block.index("      - name: download pulled\n")]
        swapped = block.replace(control + checkout, checkout + control)
        self.fires("first_step_control", text[:start] + swapped + text[end:])
        self.fires("first_step_control", _in_job(text, "cagir", "python3 -m snowball_bootstrap control",
                                                 "python3 -m snowball_bootstrap status"))
        self.fires("first_step_control", _in_job(text, "cek", "        id: control\n",
                                                 "        id: control\n        if: always()\n"))

    def test_control_only_first(self):
        self.fires("control_elsewhere", _in_job(committed(), "kos", "python3 -m loop.job run kos\n",
                                                "python3 -m loop.job run kos\n          python3 -m snowball_bootstrap control\n"))

    def test_later_steps_gated_and_nothing_continues(self):
        self.fires("step_not_gated", _in_job(committed(), "yaz", "      - name: checkout\n        if: steps.control.outputs.go == 'true'\n",
                                             "      - name: checkout\n"))
        self.fires("step_not_gated", _in_job(committed(), "kos", "      - name: kos\n        if: steps.control.outputs.go == 'true'\n",
                                             "      - name: kos\n        if: always()\n"))
        self.fires("continue_on_error", _in_job(committed(), "cek", "        id: control\n",
                                                "        id: control\n        continue-on-error: true\n"))
        self.fires("continue_on_error", _in_job(committed(), "kos", "    timeout-minutes: 60\n",
                                                "    timeout-minutes: 60\n    continue-on-error: true\n"))

    def test_no_github_expression_in_run(self):
        for expr in ("${{ github.event.inputs.x }}", "${{ github.head_ref }}", "${{github.event.issue.title}}"):
            with self.subTest(expr=expr):
                self.fires("github_expr_in_run", _in_job(committed(), "kos", "python3 -m loop.job run kos\n",
                                                         "python3 -m loop.job run kos\n          echo %s\n" % expr))
        self.fires("expr_in_run", _in_job(committed(), "cek", "cd \"$RUNNER_TEMP/control/bootstrap\"\n",
                                          "cd \"${{ runner.temp }}/control/bootstrap\"\n"))

    def test_actions_pinned(self):
        sha = "3d3c42e5aac5ba805825da76410c181273ba90b1"
        for ref in ("v7.0.1", "main", sha[:12], sha.upper()):
            with self.subTest(ref=ref):
                self.fires("unpinned_action", _sub(committed(), "actions/checkout@" + sha, "actions/checkout@" + ref))
        self.fires("unpinned_action", _sub(committed(), "actions/checkout@" + sha, "./local-action"))
        self.fires("unpinned_action", _sub(committed(), "actions/checkout@" + sha, "docker://alpine:3"))

    def test_persist_credentials(self):
        self.fires("persist_credentials", _sub(committed(), "persist-credentials: false", "persist-credentials: true"))
        self.fires("persist_credentials", _in_job(committed(), "getir", "        with:\n          persist-credentials: false\n", ""))

    def test_permissions_stated(self):
        self.fires("permissions_missing", _in_job(committed(), "cagir", "    permissions: {}\n", ""))

    def test_code_jobs_hold_nothing(self):
        self.fires("code_job_permissions", _in_job(committed(), "kos", "    permissions: {}\n",
                                                   "    permissions:\n      contents: read\n"))
        self.fires("secret_in_code_job", _in_job(committed(), "kos", "          LOOP_DEPS_DIGEST:",
                                                 "          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}\n          LOOP_DEPS_DIGEST:"))
        self.fires("secret_in_code_job", _in_job(committed(), "getir", "          LOOP_PULLED_DIGEST:",
                                                 "          GH: ${{ github.token }}\n          LOOP_PULLED_DIGEST:"))

    def test_secrets_only_where_the_table_puts_them(self):
        self.fires("secret_outside", _in_job(committed(), "cek", "      - name: cek\n        if: steps.control.outputs.go == 'true'\n",
                                             "      - name: cek\n        if: steps.control.outputs.go == 'true'\n        env:\n          K: ${{ secrets.WRITER_APP_PRIVATE_KEY }}\n"))
        self.fires("secret_outside", _in_job(committed(), "cagir", "          CLAUDE_CODE_OAUTH_TOKEN:",
                                             "          W: ${{ secrets.WRITER_APP_ID }}\n          CLAUDE_CODE_OAUTH_TOKEN:"))

    def test_secret_jobs_run_no_code(self):
        self.fires("secret_job_runs_code", _in_job(committed(), "yaz", "python3 -m loop.job run yaz\n",
                                                   "python3 -m loop.job run yaz\n          npm test\n"))
        self.fires("secret_job_runs_code", _in_job(committed(), "cagir", "python3 -m loop.job run cagir\n",
                                                   "python3 -m loop.job run kos\n"))
        pinned = "actions/setup-node@" + "0" * 40
        self.fires("secret_job_runs_code", _in_job(committed(), "cek", "uses: actions/checkout@",
                                                   "uses: %s\n        with:\n          x: y\n      - name: c2\n        if: steps.control.outputs.go == 'true'\n        uses: actions/checkout@" % pinned))
        self.fires("secret_job_runs_code", _in_job(committed(), "cagir", "uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333",
                                                   "uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510"))
        self.fires("foreign_checkout", _in_job(committed(), "cagir", "          persist-credentials: false\n",
                                               "          persist-credentials: false\n          repository: someone/brain\n"))
        self.fires("foreign_checkout", _in_job(committed(), "yaz", "          persist-credentials: false\n",
                                               "          persist-credentials: false\n          ref: brain/c/1\n"))

    def test_code_jobs_run_only_their_entry(self):
        self.fires("unknown_run", _in_job(committed(), "kos", "python3 -m loop.job run kos\n",
                                          "python3 -m loop.job run kos\n          bash ./in/pulled/x.sh\n"))


class Subset(unittest.TestCase):
    def test_accepted(self):
        self.assertEqual(parse("# c\na: b\nc:\n  - d\n  - e: 'it''s'\n    f: |\n      x\n\n      y\n  # c\ng: {}\nh: []\n"),
                         {"a": "b", "c": ["d", {"e": "it's", "f": "x\n\ny\n"}], "g": {}, "h": []})
        self.assertEqual(parse("a: true\nb: 60\n"), {"a": "true", "b": "60"})

    def test_refused(self):
        for text in ("a:\tb\n\tc: d\n", "---\na: b\n", "a: &x b\n", "a: *x\n", "a: !!str b\n", "a: [b, c]\n",
                     "a: {b: c}\n", "a: \"b\"\n", "a: >\n  b\n", "? a\n: b\n", "a: b\na: c\n", "a: b: c\n",
                     "a: b #c\n", "a: b:\n", "a:\n    b: c\n  d: e\n", "a: 'b\n", "a: 'b'c'\n", "a.b: c\n",
                     "- a\n", "", "a: b\n...\n", "a:\n", " a: b\n", "a: |\n", "a:\n  - b\n   c: d\n"):
            with self.subTest(text=text):
                with self.assertRaises(Unparseable):
                    parse(text)


class Emitter(unittest.TestCase):
    def test_scalars_the_plain_form_cannot_hold_are_quoted_and_read_back(self):
        from loop import job
        values = ["a: b", "x #y", "'q", "it's", "-x", "- x", "end:", "*a", "&a", "!t", "{}", "[]", "|", ">", "%d",
                  "@u", "`c`", ",", "?", "#c", " lead", "trail ", "\"q\"", "", "plain", "${{ x }}", "a:b", "x#y"]
        out: list[str] = []
        job._emit({"k%d" % i: v for i, v in enumerate(values)}, 0, out)
        self.assertEqual(parse("\n".join(out) + "\n"), {"k%d" % i: v for i, v in enumerate(values)})
        for plain in ("plain", "${{ x }}", "a:b", "x#y"):
            self.assertIn("k%d: %s" % (values.index(plain), plain), out)

    def test_literal_blocks_outside_the_subset_are_refused(self):
        from loop import job
        for text in ("a\n\n", " a\n", "a \n", "a\n\nb\n"):
            with self.subTest(text=text):
                with self.assertRaises(job.Unusable):
                    job._emit({"run": text}, 0, [])
        with self.assertRaises(job.Unusable):
            job._emit({"a.b": "c"}, 0, [])


class Registry(unittest.TestCase):
    def test_steps_and_mfs_covered(self):
        from loop import job
        self.assertEqual(sorted({s for j in job.JOBS.values() for s in j.steps}), ["D%d" % i for i in range(1, 9)])
        # asama-0/01's judge column names MFs 1-16; 17 is this workflow and 18 runs in (B) by hand
        self.assertEqual(sorted({m for j in job.JOBS.values() for m in j.mfs}), list(range(1, 17)))
        self.assertEqual(tuple(job.JOBS), JOBS)
        self.assertEqual({n for n, j in job.JOBS.items() if j.runs_code}, set(CODE_JOBS))

    def test_a_reader_without_its_producer_is_refused(self):
        from loop import job
        saved = job.JOBS["getir"]
        try:
            job.JOBS["getir"] = saved._replace(needs=())
            with self.assertRaises(job.Unusable):
                job.render()
        finally:
            job.JOBS["getir"] = saved


def simulate(doc: dict, control: dict[str, tuple[int, str]]) -> dict[str, tuple[str, list[str]]]:
    """Actions' conditions for the two forms this workflow uses: a job runs when its ``if`` holds and every job it
    needs succeeded; a step runs when the steps before it succeeded and its ``if`` holds; a failed step fails the
    job. ``control[job]`` is the control step's (exit, go). Any other condition is refused."""
    result: dict[str, tuple[str, list[str]]] = {}
    for name, job in doc["jobs"].items():
        needs = job.get("needs", [])
        if job["if"] != MAIN or any(result[n][0] != "success" for n in needs):
            result[name] = ("skipped", [])
            continue
        ran, failed, outputs = [], False, {}
        for step in job["steps"]:
            cond = step.get("if")
            if cond is None:
                go = not failed
            elif cond == GATE:
                go = not failed and outputs.get("go") == "true"
            else:
                raise AssertionError("condition outside the model: %r" % cond)
            if not go:
                continue
            ran.append(step["name"])
            if step.get("id") == "control":
                code, flag = control[name]
                if code != 0:
                    failed = True
                else:
                    outputs["go"] = flag
        result[name] = ("failure" if failed else "success", ran)
    return result


class Gating(unittest.TestCase):
    def test_kill_switch_stops_every_job(self):
        doc = parse(committed())
        out = simulate(doc, {n: (1, "") for n in JOBS})
        self.assertEqual(out["cek"], ("failure", ["control"]))
        for name in JOBS[1:]:
            self.assertEqual(out[name], ("skipped", []))
        for name in JOBS:  # the switch turned on between jobs: the job that reads it runs nothing else
            flags = {n: (0, "true") for n in JOBS}
            flags[name] = (1, "")
            self.assertEqual(simulate(doc, flags)[name], ("failure", ["control"]))

    def test_paused_is_green_and_runs_nothing(self):
        out = simulate(parse(committed()), {n: (0, "false") for n in JOBS})
        self.assertEqual(out, {n: ("success", ["control"]) for n in JOBS})

    def test_go_runs_every_step(self):
        doc = parse(committed())
        out = simulate(doc, {n: (0, "true") for n in JOBS})
        for name in JOBS:
            self.assertEqual(out[name], ("success", [s["name"] for s in doc["jobs"][name]["steps"]]))


def run_job(name: str, env: dict[str, str]) -> tuple[int, dict]:
    base = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "SYSTEMROOT")}
    proc = subprocess.run([sys.executable, "-m", "loop.job", "run", name], cwd=REFEREE, env=dict(base, **env),
                          capture_output=True)
    return proc.returncode, json.loads(proc.stdout.decode("utf-8"))


class JobEntry(unittest.TestCase):
    def test_code_job_refuses_a_secret(self):
        for name in CODE_JOBS:
            for var in ("CLAUDE_CODE_OAUTH_TOKEN", "WRITER_TOKEN", "GITHUB_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
                        "ACTIONS_ID_TOKEN_REQUEST_URL"):
                with self.subTest(job=name, var=var):
                    code, out = run_job(name, {var: "x"})
                    self.assertEqual((code, out["ok"], out["reason"]), (1, False, "secret_in_code_job:" + var))

    def test_not_wired_stops_red(self):
        # kos runs D3 first and then stops the same way: test_loop_kos.py
        for name in [n for n in JOBS if n != "kos"]:
            env = {"CLAUDE_CODE_OAUTH_TOKEN": "x"} if name == "cagir" else {"WRITER_TOKEN": "x"} if name == "yaz" else {}
            with self.subTest(job=name):
                code, out = run_job(name, env)
                self.assertEqual((code, out["ok"], out["reason"], out["job"]), (1, False, "cycle_not_wired", name))

    def test_unusable(self):
        for argv in (["run", "nope"], ["run"], [], ["render", "x"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([sys.executable, "-m", "loop.job"] + argv, cwd=REFEREE, capture_output=True)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(json.loads(proc.stdout), {"ok": False, "reason": None})


if __name__ == "__main__":
    unittest.main()
