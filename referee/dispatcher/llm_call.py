"""``llm.call``: one tool-less model call through the pinned ``claude`` CLI, from typed input, with its ``cost``
row (stage 0, MF15).

Rules: asama-0/14 row 15, asama-0/09 test 37, asama-0/12 (the canary's stage brake, ``canary_usd``), tohum/24
("Araçsız çağrı", "Kaçış": 429 and other outages are not rejections, no silent retry inside a run), tohum/26a
(``llm.call``: typed input, template, model, per-call cap -> structured output, served model, cost; writes the
``cost`` row), tohum/06 (the cost is the CLI's list-price estimate; on a timeout the per-call cap is written),
tohum/08 item 11 (a prompt is scanned, a match is not sent), tohum/29d (group ``prompt``).

**Types** (``TYPES``, one checker for input and output): a type is ``{field: kind}``, at least one field, field
names ``[a-z][a-z0-9_]*``, kind one of ``string``, ``integer`` (a JSON integer within +-(2^53-1); ``true`` is
not one), ``boolean``, ``strings`` (an array of strings). A value has exactly the type's fields: a missing
field, a field outside the type and a value of another kind are refused (``Unusable``), never dropped.

**Template**: exactly ``{name, system, body, input, output}``; ``name`` a non-empty string, ``system`` and
``body`` strings, ``input`` and ``output`` types. In ``body``, ``{field}`` is a placeholder, ``{{`` and ``}}``
are literal braces, and any other brace is refused; every placeholder is an ``input`` field and every
``input`` field is used. The prompt is ``body`` with each placeholder replaced, in one pass, by the RFC 8785
form of the field's value (``ledger.chain.canonical``): a string arrives quoted with its quotes, backslashes
and line breaks escaped, so a value cannot add template text, close its own quotes or expand another
placeholder. ``prompt_sha256`` is the sha256 of the prompt's UTF-8 bytes, ``system_sha256`` of ``system``'s.

**A call** (``call``), in this order; steps 1-4 start no process and write no row:

1. The template, the input, the model (a non-empty string), the cap (integer micro-USD > 0) and the budget
   are checked; the prompt is built.
2. The CLI file's sha512 must equal the pin (``Unusable`` otherwise). The file is hashed, then executed by
   path: a file swapped between the two is out of reach of this check.
3. The system text and the prompt are scanned (``gate.secrets.scan``, kind ``prompt``) with the provider
   token as a known value: a match is outcome ``secret``, not sent.
4. The stage brake (``CostBook``): when the cost already recorded under the budget name plus this call's
   cap exceeds the budget, the outcome is ``brake``, not sent (the caller's cycle then fails closed).
5. One process, no retry: ``claude -p`` with ``ARGS`` (no built-in tool, no setting source, no MCP server,
   no slash command, no session persistence, ``--max-budget-usd`` the cap, ``--model``, ``--system-prompt``,
   ``--json-schema`` from ``output``, JSON output); the prompt on stdin, never in argv; the working
   directory a fresh empty directory; the environment exactly ``PATH`` (inherited), ``HOME`` and
   ``CLAUDE_CONFIG_DIR`` (fresh empty directories), ``CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`` and
   ``CLAUDE_CODE_OAUTH_TOKEN`` when given. Nothing else of the caller's environment reaches it.
6. The result is classified (``classify``, the first rule that holds):

   - the process ran past ``timeout_s``: ``outage`` / ``timeout``, cost = cap;
   - stdout is not one JSON object with ``type: result``, a ``total_cost_usd`` number >= 0 (at most 2^53-1
     micro-USD once rounded up) and a ``modelUsage`` object: ``unresolved`` / ``malformed_result``, cost = cap;
   - otherwise the cost is ``total_cost_usd`` rounded up to a micro-USD, computed exactly from the number's
     JSON text (``to_micros``: never a float, no decimal context, any exponent), and the served models are
     ``modelUsage``'s keys;
   - ``subtype: error_max_budget_usd``: ``unresolved`` / ``over_budget``;
   - ``is_error`` anything but ``false``, or another ``subtype``: by the status in ``API Error: NNN`` of ``result``: 429
     ``outage`` / ``quota``; 401 and 403 ``outage`` / ``identity``; 5xx ``outage`` / ``server``; 400, 404, 413,
     422 ``request_rejected`` / ``http_NNN``; any other status, or none, ``unresolved`` / ``cli_error``;
   - the cost is above the cap: ``unresolved`` / ``over_budget``;
   - ``stop_reason: refusal``: ``unresolved`` / ``refusal``;
   - the served models are not exactly the requested one: ``unresolved`` / ``model_mismatch``;
   - ``structured_output`` is not a value of the ``output`` type: ``unresolved`` / ``malformed_output``;
   - else ``ok``, the run is valid, and ``output`` is ``structured_output``.

7. Every started process gives one ``cost`` row (part ``cost``, kind ``cost``), recorded in the ``CostBook``
   before ``call`` returns, whatever the outcome; the book's ``request()`` is the cycle's ``ledger.append``
   input (calls 10 -> 15: one ``brain/state`` commit per cycle, not one per call). The row holds no float and
   no free text from the CLI but the served model names; its budget field is ``budget``, not ``budget_key``:
   ``ledger.append``'s scan (MF2) reads a ``*_key`` field holding 8 or more characters as an assigned secret.

**The book** (``CostBook``) reads the ledger only once it is a valid chain extending ``previous``
(``ledger.chain.verify_bytes``) or raises ``ledger.append.HardStop``. Spent under a key is the sum of
``payload.cost_usd_micros`` over ``part: cost, kind: cost`` rows with that ``payload.budget``, in the ledger
and recorded since; such a row with a cost that is not an integer >= 0 is ``Unusable`` (the brake cannot be
computed, so no call).

Out of scope, stated: whether the real CLI's JSON matches the shapes above (the fake here follows them; the real
call is asama-0/10a ``#model``); a network error without a status (``cli_error``, not ``outage``); the API-key
path for sale (tohum/24); where the template, model, cap and budget come from (``policy.json``, the caller).

Command line, run from ``referee/``, one JSON line on stdout, the cause of an error on stderr::

    python -m dispatcher.llm_call prompt   stdin {template, input}   -> {prompt_sha256, system_sha256}
    exit 0; 2 unusable input (both fields null).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

from gate import secrets
from ledger import append, chain

TYPES = ("string", "integer", "boolean", "strings")
FIELD = re.compile(r"[a-z][a-z0-9_]*\Z")
TEMPLATE = {"name", "system", "body", "input", "output"}
TOKEN_ENV = "CLAUDE_CODE_OAUTH_TOKEN"
ARGS = ("-p", "--output-format", "json", "--tools", "", "--setting-sources", "", "--strict-mcp-config",
        "--disable-slash-commands", "--no-session-persistence")
PART = KIND = "cost"
OUTCOMES = ("ok", "outage", "request_rejected", "unresolved", "secret", "brake")
OUTAGE_STATUS = {429: "quota", 401: "identity", 403: "identity"}
REJECTED_STATUS = (400, 404, 413, 422)
API_STATUS = re.compile(r"API Error: (\d{3})\b")
HEX = set("0123456789abcdef")


class Unusable(ValueError):
    pass


# ---------------------------------------------------------------- types and the prompt

def check_type(spec: Any, what: str) -> dict:
    if not isinstance(spec, dict) or not spec:
        raise Unusable("%s must be a non-empty object {field: kind}" % what)
    for name, kind in spec.items():
        if not isinstance(name, str) or not FIELD.match(name):
            raise Unusable("%s: field name %r must match [a-z][a-z0-9_]*" % (what, name))
        if kind not in TYPES:
            raise Unusable("%s: field %s has kind %r, not one of %s" % (what, name, kind, ", ".join(TYPES)))
    return spec


def _of_kind(value: Any, kind: str) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return type(value) is int and abs(value) <= chain.MAX_SAFE_INT
    if kind == "boolean":
        return type(value) is bool
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def check_value(spec: dict, value: Any, what: str) -> dict:
    """``value`` has exactly ``spec``'s fields, each of its kind; otherwise ``Unusable``."""
    if not isinstance(value, dict):
        raise Unusable("%s must be an object" % what)
    if set(value) != set(spec):
        extra, missing = sorted(set(value) - set(spec)), sorted(set(spec) - set(value))
        raise Unusable("%s: fields outside the type %s, missing %s" % (what, extra, missing))
    for name, kind in spec.items():
        if not _of_kind(value[name], kind):
            raise Unusable("%s: field %s is not a %s" % (what, name, kind))
    return value


def _pieces(body: str) -> list[tuple[str, str]]:
    """``body`` as ``("text", s)`` and ``("field", name)`` pieces; a brace that is neither ``{{``, ``}}`` nor
    ``{name}`` is refused."""
    pieces, text, i = [], [], 0
    while i < len(body):
        ch = body[i]
        if ch in "{}" and body[i:i + 2] == ch * 2:
            text.append(ch)
            i += 2
        elif ch == "{":
            end = body.find("}", i)
            name = body[i + 1:end] if end > 0 else ""
            if not FIELD.match(name):
                raise Unusable("template body: a brace at %d is not {{, }} or {field}" % i)
            pieces += [("text", "".join(text)), ("field", name)]
            text, i = [], end + 1
        elif ch == "}":
            raise Unusable("template body: a lone } at %d" % i)
        else:
            text.append(ch)
            i += 1
    return pieces + [("text", "".join(text))]


def check_template(tmpl: Any) -> dict:
    if not isinstance(tmpl, dict) or set(tmpl) != TEMPLATE:
        raise Unusable("template must be {%s} and nothing else" % ", ".join(sorted(TEMPLATE)))
    if not isinstance(tmpl["name"], str) or not tmpl["name"]:
        raise Unusable("template name must be a non-empty string")
    if not isinstance(tmpl["system"], str) or not isinstance(tmpl["body"], str):
        raise Unusable("template system and body must be strings")
    fields = check_type(tmpl["input"], "template input")
    check_type(tmpl["output"], "template output")
    used = {name for kind, name in _pieces(tmpl["body"]) if kind == "field"}
    if used != set(fields):
        raise Unusable("template body: placeholders outside the input type %s, input fields unused %s"
                       % (sorted(used - set(fields)), sorted(set(fields) - used)))
    return tmpl


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render(tmpl: Any, value: Any) -> dict:
    """``{prompt, prompt_sha256, system_sha256}`` from a template and a value of its input type."""
    check_template(tmpl)
    check_value(tmpl["input"], value, "input")
    out = []
    for kind, piece in _pieces(tmpl["body"]):
        if kind == "text":
            out.append(piece)
        else:
            try:
                out.append(chain.canonical(value[piece]).decode("utf-8"))
            except chain.ChainError as exc:
                raise Unusable("input field %s: %s" % (piece, exc)) from None
    try:
        prompt = "".join(out)
        return {"prompt": prompt, "prompt_sha256": _sha256(prompt), "system_sha256": _sha256(tmpl["system"])}
    except UnicodeEncodeError:
        raise Unusable("template text is not encodable as UTF-8") from None


def json_schema(spec: dict) -> dict:
    """The JSON Schema the CLI is asked to answer in: exactly ``spec``'s fields, each of its kind."""
    kinds = {"string": {"type": "string"}, "integer": {"type": "integer"}, "boolean": {"type": "boolean"},
             "strings": {"type": "array", "items": {"type": "string"}}}
    return {"type": "object", "properties": {name: kinds[kind] for name, kind in spec.items()},
            "required": sorted(spec), "additionalProperties": False}


# ---------------------------------------------------------------- money

def usd(micros: int) -> str:
    """Micro-USD as the decimal string ``--max-budget-usd`` takes: 500000 -> ``0.500000``."""
    return "%d.%06d" % divmod(micros, 1_000_000)


NUMBER = re.compile(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?)([0-9]+))?\Z")


class JsonNumber:
    """A JSON number kept as its text (``_strict_json``): a fraction or exponent, or an integer of more than
    ``INT_DIGITS`` digits. It is no ``int`` and no ``str``, so no type check takes it for either."""

    __slots__ = ("text",)

    def __init__(self, text: str):
        self.text = text


INT_DIGITS = 18  # 2^53-1 has 16 digits: a longer integer is outside every range read here


def to_micros(text: str) -> int | None:
    """The JSON number ``text`` (USD) rounded up to a micro-USD, exactly, by integer arithmetic on its digits;
    None when it is negative and not zero, or above 2^53-1 micro-USD. No decimal context: no precision, no
    exponent limit, no rounding before the ceiling; work is bounded by the text's length, whatever the exponent."""
    match = NUMBER.match(text)
    if not match:
        raise Unusable("not a JSON number: %r" % text[:40])
    minus, whole, frac, exp_sign, exp = match.groups()
    frac = frac or ""
    digits = (whole + frac).lstrip("0")
    if not digits:
        return 0
    if minus:
        return None
    exp = (exp or "0").lstrip("0") or "0"
    if len(exp) > INT_DIGITS:  # |exponent| >= 10^18: astronomically large, or below any micro and above zero
        return 1 if exp_sign == "-" else None
    # value = int(digits) * 10^scale micro-USD; its leading digit sits at 10^(len(digits) - 1 + scale)
    scale = (-int(exp) if exp_sign == "-" else int(exp)) - len(frac) + 6
    if len(digits) - 1 + scale >= 16:  # >= 10^16 > 2^53-1
        return None
    if scale >= 0:
        micros = int(digits) * 10 ** scale
    else:
        cut = len(digits) + scale  # digits at or above one micro
        micros = 1 if cut <= 0 else int(digits[:cut]) + (1 if digits[cut:].strip("0") else 0)
    return micros if micros <= chain.MAX_SAFE_INT else None


def _micros(value: Any, what: str, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0) or value > chain.MAX_SAFE_INT:
        raise Unusable("%s must be an integer %s" % (what, "> 0" if positive else ">= 0"))
    return value


# ---------------------------------------------------------------- the book and the brake

class CostBook:
    """The cost rows of a verified ledger plus the ones recorded in this cycle; the stage brake reads it."""

    def __init__(self, ledger: bytes, previous: bytes):
        verdict = chain.verify_bytes(ledger, previous)
        if not verdict["valid"]:
            raise append.HardStop("ledger: %s (%s)" % (verdict["reason"], verdict["broken_row"]))
        self.ledger = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(ledger)]
        self.rows: list[dict] = []

    def spent(self, name: str) -> int:
        total = 0
        for row in self.ledger + self.rows:
            payload = row.get("payload")
            if (row.get("part") == PART and row.get("kind") == KIND and isinstance(payload, dict)
                    and payload.get("budget") == name):
                total += _micros(payload.get("cost_usd_micros"), "cost row %r cost_usd_micros" % row.get("row_id"))
        return total

    def record(self, row: dict) -> None:
        self.rows.append(row)

    def request(self) -> bytes:
        """The rows recorded in this cycle as ``ledger.append``'s request."""
        return json.dumps({"rows": self.rows}, sort_keys=True).encode("utf-8")


# ---------------------------------------------------------------- the result

def _json_int(text: str) -> int | JsonNumber:
    return int(text) if len(text.lstrip("-")) <= INT_DIGITS else JsonNumber(text)


def _strict_json(text: str) -> Any:
    return json.loads(text, parse_float=JsonNumber, parse_int=_json_int, object_pairs_hook=chain._no_duplicates,
                      parse_constant=chain._no_constant)


def _cost(value: Any) -> int | None:
    """A JSON number >= 0 (an integer, not ``true``, or a ``JsonNumber``) as micro-USD rounded up; else None."""
    if type(value) is int:
        return to_micros(str(value))
    if isinstance(value, JsonNumber):
        return to_micros(value.text)
    return None


def classify(stdout: bytes | None, model: str, cap: int, output: dict) -> dict:
    """Step 6 of the module docstring: ``{outcome, reason, cost_usd_micros, cost_source, models_served,
    output}``; ``stdout`` None means the process ran past its timeout."""
    def done(outcome, reason, cost=cap, source="cap", served=(), out=None):
        return {"outcome": outcome, "reason": reason, "cost_usd_micros": cost, "cost_source": source,
                "models_served": sorted(served), "output": out}

    if stdout is None:
        return done("outage", "timeout")
    try:
        result = _strict_json(stdout.decode("utf-8").strip())
    except (UnicodeDecodeError, ValueError, chain.ChainError, RecursionError):
        result = None
    measured = _cost(result.get("total_cost_usd")) if isinstance(result, dict) else None
    if (measured is None or result.get("type") != "result" or not isinstance(result.get("modelUsage"), dict)):
        return done("unresolved", "malformed_result")
    usage = result["modelUsage"]
    seen = dict(cost=measured, source="cli_estimate", served=list(usage))
    if result.get("subtype") == "error_max_budget_usd":
        return done("unresolved", "over_budget", **seen)
    if result.get("is_error") is not False or result.get("subtype") != "success":
        text = result.get("result")
        status = API_STATUS.search(text) if isinstance(text, str) else None
        code = int(status.group(1)) if status else None
        if code in OUTAGE_STATUS:
            return done("outage", OUTAGE_STATUS[code], **seen)
        if code is not None and 500 <= code <= 599:
            return done("outage", "server", **seen)
        if code in REJECTED_STATUS:
            return done("request_rejected", "http_%d" % code, **seen)
        return done("unresolved", "cli_error", **seen)
    if measured > cap:
        return done("unresolved", "over_budget", **seen)
    if result.get("stop_reason") == "refusal":
        return done("unresolved", "refusal", **seen)
    if list(usage) != [model]:
        return done("unresolved", "model_mismatch", **seen)
    try:
        out = check_value(output, result.get("structured_output"), "structured_output")
    except Unusable:
        return done("unresolved", "malformed_output", **seen)
    return done("ok", None, out=out, **seen)


# ---------------------------------------------------------------- the call

def sha512_file(path: str) -> str:
    digest = hashlib.sha512()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def command(claude: str, model: str, cap: int, tmpl: dict) -> list[str]:
    """The argv of one call; the prompt is not in it."""
    schema = chain.canonical(json_schema(tmpl["output"])).decode("utf-8")
    return [claude, *ARGS, "--model", model, "--max-budget-usd", usd(cap), "--system-prompt", tmpl["system"],
            "--json-schema", schema]


def _environment(root: str, token: str | None) -> dict:
    env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": os.path.join(root, "home"),
           "CLAUDE_CONFIG_DIR": os.path.join(root, "config"), "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
    for name in ("home", "config", "work"):
        os.mkdir(os.path.join(root, name))
    if token is not None:
        env[TOKEN_ENV] = token
    return env


def cost_row(tmpl: dict, built: dict, model: str, cap: int, budget_name: str, verdict: dict, duration_ms: int,
             row_id: str, ts: str, snapshot_id: str) -> dict:
    payload = {"tool": "llm.call", "template": tmpl["name"], "budget": budget_name, "model_requested": model,
               "models_served": verdict["models_served"], "outcome": verdict["outcome"], "reason": verdict["reason"],
               "cost_usd_micros": verdict["cost_usd_micros"], "cost_source": verdict["cost_source"],
               "cap_usd_micros": cap, "prompt_sha256": built["prompt_sha256"],
               "system_sha256": built["system_sha256"], "duration_ms": duration_ms}
    return {"row_id": row_id, "ts": ts, "part": PART, "kind": KIND, "payload": payload, "derivation": "tool",
            "trust": "observed", "snapshot_id": snapshot_id, "evidence_refs": []}


def call(tmpl: Any, value: Any, *, claude: str, claude_sha512: str, model: str, cap_micros: int, budget_name: str,
         budget_micros: int, book: CostBook, token: str | None, timeout_s: float, row_id: str, ts: str,
         snapshot_id: str) -> dict:
    """One call (see the module docstring). Returns ``{outcome, reason, sent, run_valid, output, models_served,
    cost_usd_micros, prompt_sha256, row}``; ``row`` is None when nothing was sent."""
    built = render(tmpl, value)
    if not isinstance(model, str) or not model:
        raise Unusable("model must be a non-empty string")
    cap = _micros(cap_micros, "cap_micros", positive=True)
    budget = _micros(budget_micros, "budget_micros")
    if not isinstance(budget_name, str) or not budget_name:
        raise Unusable("budget_name must be a non-empty string")
    if token is not None and not isinstance(token, str):
        raise Unusable("token must be a string or None")
    if not isinstance(claude_sha512, str) or len(claude_sha512) != 128 or not set(claude_sha512) <= HEX:
        raise Unusable("claude_sha512 must be 128 lowercase hex characters")
    if sha512_file(claude) != claude_sha512:
        raise Unusable("the claude CLI at %s is not the pinned one" % claude)
    unsent = {"sent": False, "run_valid": False, "output": None, "models_served": [], "cost_usd_micros": 0,
              "prompt_sha256": built["prompt_sha256"], "row": None}
    known = [(TOKEN_ENV, token)] if token else []
    if secrets.scan(tmpl["system"], "prompt", known) or secrets.scan(built["prompt"], "prompt", known):
        return dict(unsent, outcome="secret", reason="secret_in_prompt")
    if book.spent(budget_name) + cap > budget:
        return dict(unsent, outcome="brake", reason="stage_budget")
    with tempfile.TemporaryDirectory(prefix="llm-call-") as root:
        env = _environment(root, token)
        started = time.monotonic()
        try:
            done = subprocess.run(command(claude, model, cap, tmpl), input=built["prompt"].encode("utf-8"),
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=os.path.join(root, "work"),
                                  env=env, timeout=timeout_s)
            stdout = done.stdout
        except subprocess.TimeoutExpired:
            stdout = None
        duration = int((time.monotonic() - started) * 1000)
    verdict = classify(stdout, model, cap, tmpl["output"])
    row = cost_row(tmpl, built, model, cap, budget_name, verdict, duration, row_id, ts, snapshot_id)
    book.record(row)
    return {"outcome": verdict["outcome"], "reason": verdict["reason"], "sent": True,
            "run_valid": verdict["outcome"] == "ok", "output": verdict["output"],
            "models_served": verdict["models_served"], "cost_usd_micros": verdict["cost_usd_micros"],
            "prompt_sha256": built["prompt_sha256"], "row": row}


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m dispatcher.llm_call prompt < {template, input}"


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def main(argv: list[str]) -> int:
    try:
        if argv != ["prompt"]:
            raise Unusable(USAGE)
        request = chain.parse_row(sys.stdin.buffer.read().decode("utf-8"))
        if set(request) != {"template", "input"}:
            raise Unusable("stdin must be {template, input} and nothing else")
        built = render(request["template"], request["input"])
        _emit({"prompt_sha256": built["prompt_sha256"], "system_sha256": built["system_sha256"]})
        return 0
    except (Unusable, UnicodeDecodeError, chain.ChainError) as exc:
        sys.stderr.write("unusable input: %s\n" % exc)
    except Exception as exc:  # noqa: BLE001 - never a traceback, never an exit without a reason
        sys.stderr.write("internal error: %s: %s\n" % (type(exc).__name__, exc))
    _emit({"prompt_sha256": None, "system_sha256": None})
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
