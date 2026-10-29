"""Test 38 (asama-0/09): a fake secret embedded in a diff, a ledger row and a prompt is caught; a match
invalidates the run and the prompt is not sent.

Every command case drives ``python -m gate.secrets`` from ``referee/`` in a subprocess, the way the
referee runs it; input goes through stdin or a pipe (``/dev/fd/N``), so nothing is written to disk and
the suite runs in a read-only container. No fake secret is written literally in this file: each is
assembled at run time from split parts, so the file itself (and the diff that carries it to the
rival's prompt) holds no secret-shaped text. Expected fingerprints are computed here with hashlib.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAIN = os.path.dirname(REFEREE)
ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
UPPER32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def body(seed: str, n: int, alphabet: str = ALNUM) -> str:
    """A deterministic random-looking string of ``n`` characters from ``alphabet``."""
    out, counter = [], 0
    while len(out) < n:
        for byte in hashlib.sha256(("%s/%d" % (seed, counter)).encode()).digest():
            out.append(alphabet[byte % len(alphabet)])
        counter += 1
    return "".join(out[:n])


def j(*parts: str) -> str:
    return "".join(parts)


# rule name -> a fake token of that shape (assembled, never literal)
FAKES = {
    "anthropic-key": j("sk-", "ant-", "oat01-", body("ant", 60, ALNUM + "_-")),
    "github-token": j("gh", "p_", body("ghp", 36)),
    "github-pat": j("github", "_pat_", body("pat", 82, ALNUM + "_")),
    "aws-access-key-id": j("AK", "IA", body("aws", 16, UPPER32)),
    "google-api-key": j("AI", "za", body("goog", 35, ALNUM + "_-")),
    "slack-token": j("xo", "xb-", body("slack", 24, ALNUM + "-")),
    "stripe-key": j("sk", "_live_", body("stripe", 24)),
    "npm-token": j("np", "m_", body("npm", 36)),
    "gitlab-token": j("gl", "pat-", body("gitlab", 20)),
    "openai-key": j("sk-", "proj-", body("oa1", 24), "T3Blbk", "FJ", body("oa2", 24)),
    "private-key": j("-----", "BEGIN RSA ", "PRIVATE KEY", "-----"),
    "jwt": j("ey", "J", body("jwt1", 20), ".ey", "J", body("jwt2", 20), ".", body("jwt3", 30)),
}
AWS_SECRET_VALUE = body("awssecret", 40, ALNUM + "/+")
ASSIGNED_VALUE = body("assigned", 32)
URL_PASSWORD = body("urlpw", 14)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_secrets(args: list, stdin: bytes = b"", env_extra: dict | None = None):
    """Run ``python -m gate.secrets`` from referee/; each bytes value in ``args`` is served as a pipe."""
    fds, writers, argv = [], [], []
    for arg in args:
        if isinstance(arg, bytes):
            r, w = os.pipe()
            fds.append(r)
            writers.append((w, arg))
            argv.append("/dev/fd/%d" % r)
        else:
            argv.append(arg)

    def feed(fd: int, data: bytes) -> None:
        with os.fdopen(fd, "wb") as fh:
            try:
                fh.write(data)
            except BrokenPipeError:
                pass

    threads = [threading.Thread(target=feed, args=wd) for wd in writers]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **(env_extra or {}))
    proc = subprocess.Popen([sys.executable, "-m", "gate.secrets", *argv], cwd=REFEREE, env=env,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            pass_fds=fds)
    for fd in fds:
        os.close(fd)
    for t in threads:
        t.start()
    out, err = proc.communicate(stdin, timeout=60)
    for t in threads:
        t.join()
    lines = out.decode().splitlines()
    result = json.loads(lines[0]) if len(lines) == 1 else None
    return proc.returncode, result, out + err


def scan(kind: str, text: str, **kw):
    return run_secrets(["scan", "--kind", kind], stdin=text.encode("utf-8"), **kw)


def diff_with(line: str, sign: str = "+", path: str = "app/config.py") -> str:
    return "\n".join([
        "diff --git a/%s b/%s" % (path, path),
        "index 1111111..2222222 100644",
        "--- a/%s" % path,
        "+++ b/%s" % path,
        "@@ -1,3 +1,4 @@",
        " import os",
        "%s%s" % (sign, line),
        " DEBUG = False",
        "",
    ])


def row_with(text: str) -> str:
    row = {"row_id": "f1", "ts": "2026-10-29T00:00:00Z", "part": "founder", "kind": "decision",
           "payload": {"summary": text, "refs": []}, "derivation": "llm_inference", "trust": "inferred",
           "snapshot_id": "s0", "evidence_refs": [], "prev_hash": "0" * 64, "row_hash": sha("x")}
    return json.dumps(row, separators=(",", ":"))


def prompt_with(text: str) -> str:
    return "You review a diff.\n\nContext:\n%s\n\nAnswer with a verdict.\n" % text


SENDER = ("import sys; data = sys.stdin.read(); "
          "sys.stdout.write('SENDER-RAN bytes=%d\\n' % len(data.encode('utf-8')))")


class Detection(unittest.TestCase):
    def assert_caught(self, kind: str, text: str, rule: str, value: str, line: int | None = None):
        code, result, raw = scan(kind, text)
        self.assertEqual(code, 1, raw)
        self.assertFalse(result["clean"])
        self.assertFalse(result["run_valid"])
        self.assertEqual(result["kind"], kind)
        hits = [m for m in result["matches"] if m["rule"] == rule]
        self.assertTrue(hits, "%s not reported for %s: %s" % (rule, kind, result))
        self.assertIn(sha(value), {m["sha256"] for m in hits})
        if line is not None:
            self.assertIn(line, {m["line"] for m in hits})
        self.assertNotIn(value.encode(), raw, "the secret value leaked into the output")
        return result

    def test_every_rule_in_diff_row_and_prompt(self):
        for rule, token in FAKES.items():
            with self.subTest(rule=rule, kind="diff"):
                self.assert_caught("diff", diff_with('KEY = "%s"' % token), rule, token, line=7)
            with self.subTest(rule=rule, kind="row"):
                self.assert_caught("row", row_with("found %s in config" % token), rule, token, line=1)
            with self.subTest(rule=rule, kind="prompt"):
                self.assert_caught("prompt", prompt_with("value: %s" % token), rule, token, line=4)

    def test_aws_secret_assignment_url_credentials_and_quoted_assignment(self):
        line = "aws_secret_access_key = %s" % AWS_SECRET_VALUE
        code, result, raw = scan("diff", diff_with(line))
        self.assertEqual(code, 1, raw)
        self.assertIn("aws-secret-key", {m["rule"] for m in result["matches"]})
        self.assertNotIn(AWS_SECRET_VALUE.encode(), raw)

        url = j("postgres://admin:", URL_PASSWORD, "@db.internal:5432/app")
        code, result, raw = scan("prompt", prompt_with(url))
        self.assertEqual(code, 1, raw)
        self.assertIn("url-credentials", {m["rule"] for m in result["matches"]})
        self.assertNotIn(URL_PASSWORD.encode(), raw)

        self.assert_caught("diff", diff_with('client_secret = "%s"' % ASSIGNED_VALUE), "secret-assignment",
                           ASSIGNED_VALUE, line=7)

    def test_diff_reports_path_and_scans_removed_lines(self):
        token = FAKES["github-token"]
        result = self.assert_caught("diff", diff_with('T = "%s"' % token, sign="-", path="svc/old.py"),
                                    "github-token", token, line=7)
        self.assertEqual({m.get("path") for m in result["matches"]}, {"svc/old.py"})

    def test_hidden_spellings_are_caught(self):
        token = FAKES["github-token"]
        escaped = "".join("\\u%04x" % ord(c) for c in token)
        # JSON escapes in a row: the raw text has no token, the decoded string does
        code, result, raw = scan("row", '{"row_id":"f1","payload":{"summary":"%s"}}' % escaped)
        self.assertEqual(code, 1, raw)
        self.assertIn(sha(token), {m["sha256"] for m in result["matches"]})
        # zero-width space inside the token
        hidden = token[:10] + "\u200b" + token[10:]
        self.assert_caught("prompt", prompt_with(hidden), "github-token", token)
        # full-width letters fold to ASCII under NFKC
        wide = "".join(chr(ord(c) + 0xFEE0) if c.isalnum() else c for c in token)
        self.assert_caught("prompt", prompt_with(wide), "github-token", token)

    def test_invalid_utf8_around_a_secret_is_still_scanned(self):
        token = FAKES["aws-access-key-id"]
        data = b"\xff\xfe junk " + token.encode() + b" \xc3\x28\n"
        code, result, raw = run_secrets(["scan", "--kind", "prompt"], stdin=data)
        self.assertEqual(code, 1, raw)
        self.assertIn(sha(token), {m["sha256"] for m in result["matches"]})

    def test_file_argument(self):
        token = FAKES["npm-token"]
        code, result, raw = run_secrets(["scan", "--kind", "diff", diff_with(token).encode()])
        self.assertEqual(code, 1, raw)
        self.assertEqual(result["matches"][0]["rule"], "npm-token")

    def test_known_values_from_the_environment(self):
        value = body("referee-own-secret", 40)
        env = {"SB_TEST_KNOWN": value, "SB_TEST_SHORT": "abc"}
        code, result, raw = run_secrets(["scan", "--kind", "prompt", "--known-env", "SB_TEST_KNOWN",
                                         "--known-env", "SB_TEST_SHORT"],
                                        stdin=prompt_with("plain words %s abc" % value).encode(), env_extra=env)
        self.assertEqual(code, 1, raw)
        self.assertEqual({m["rule"] for m in result["matches"]}, {"known:SB_TEST_KNOWN"})
        self.assertNotIn(value.encode(), raw)
        # without naming the variable the plain value is not a pattern match
        code, result, raw = run_secrets(["scan", "--kind", "prompt"],
                                        stdin=prompt_with("plain words %s" % value).encode(), env_extra=env)
        self.assertEqual((code, result["matches"]), (0, []), raw)


class Clean(unittest.TestCase):
    def assert_clean(self, kind: str, text: str):
        code, result, raw = scan(kind, text)
        self.assertEqual(code, 0, raw)
        self.assertEqual(result, {"clean": True, "kind": kind, "run_valid": True, "matches": []})

    def test_one_changed_byte_is_no_longer_a_token(self):
        """The changed input of each fake (one character cut, or prefix broken) gives no match."""
        changed = {
            "github-token": FAKES["github-token"][:-1],
            "aws-access-key-id": FAKES["aws-access-key-id"][:-1],
            "google-api-key": FAKES["google-api-key"][:-1],
            "npm-token": FAKES["npm-token"][:-1],
            "stripe-key": FAKES["stripe-key"].replace("_live_", "_lime_"),
            "anthropic-key": FAKES["anthropic-key"].replace("sk-ant", "sk-and"),
            "private-key": FAKES["private-key"].replace("PRIVATE", "PUBLIC"),
        }
        for rule, text in changed.items():
            with self.subTest(rule=rule):
                self.assert_clean("prompt", prompt_with("value %s" % text))

    def test_ordinary_code_and_placeholders(self):
        lines = [
            "token = get_token(request)",
            'password = "<placeholder>"',
            'api_key = os.environ["API_KEY"]',
            'secret = "${SECRET_FROM_ENV}"',
            'token = "aaaaaaaaaaaaaaaaaaaaaaaa"',
            "url = 'https://user:password@example.com/'",
            "commit 632a84cc3e7e70741607457a4060e375caa0e3a4",
            "row_hash 3bae91580aca99362572e9f5f41b3e46c2bc0c29236f72e867faa5cd46ca603a",
            "id 123e4567-e89b-12d3-a456-426614174000",
            "-----BEGIN PUBLIC KEY-----",
        ]
        self.assert_clean("diff", diff_with("\n+".join(lines)))
        self.assert_clean("prompt", prompt_with("\n".join(lines)))
        self.assert_clean("prompt", "")

    def test_the_real_ledger_and_this_push_are_clean(self):
        for rel in ("founder-ledger.jsonl", "referee/gate/secrets.py", "referee/tests/test_secrets.py",
                    "referee/ledger/chain.py", "snowball-tests.json"):
            with self.subTest(path=rel):
                with open(os.path.join(BRAIN, rel), encoding="utf-8") as fh:
                    text = fh.read()
                kind = "row" if rel.endswith(".jsonl") else "prompt"
                self.assert_clean(kind, text)


class Send(unittest.TestCase):
    def test_clean_prompt_is_sent(self):
        prompt = prompt_with("nothing secret here")
        code, result, raw = run_secrets(["send", "--", sys.executable, "-c", SENDER], stdin=prompt.encode())
        self.assertEqual(code, 0, raw)
        self.assertEqual(result, {"clean": True, "run_valid": True, "sent": True, "sender_exit": 0, "matches": []})
        self.assertIn(b"SENDER-RAN bytes=%d" % len(prompt.encode()), raw)

    def test_prompt_with_secret_is_not_sent_and_run_is_invalid(self):
        for rule in ("anthropic-key", "github-token", "private-key"):
            with self.subTest(rule=rule):
                prompt = prompt_with("leak %s" % FAKES[rule])
                code, result, raw = run_secrets(["send", "--", sys.executable, "-c", SENDER], stdin=prompt.encode())
                self.assertEqual(code, 1, raw)
                self.assertFalse(result["sent"])
                self.assertFalse(result["run_valid"])
                self.assertIsNone(result["sender_exit"])
                self.assertEqual({m["rule"] for m in result["matches"]}, {rule})
                self.assertNotIn(b"SENDER-RAN", raw)

    def test_known_env_value_blocks_send(self):
        value = body("oauth", 48)
        code, result, raw = run_secrets(["send", "--known-env", "SB_TEST_OAUTH", "--", sys.executable, "-c", SENDER],
                                        stdin=prompt_with(value).encode(), env_extra={"SB_TEST_OAUTH": value})
        self.assertEqual((code, result["sent"]), (1, False), raw)
        self.assertNotIn(b"SENDER-RAN", raw)


class Library(unittest.TestCase):
    """The in-process API the callers (llm.call, gate.check, ledger.append) use."""

    def setUp(self):
        sys.path.insert(0, REFEREE)
        self.addCleanup(sys.path.remove, REFEREE)
        from gate import secrets
        self.secrets = secrets

    def test_send_if_clean_never_calls_send_on_a_match(self):
        calls = []
        with self.assertRaises(self.secrets.SecretFound) as ctx:
            self.secrets.send_if_clean(prompt_with(FAKES["jwt"]), calls.append)
        self.assertEqual(calls, [])
        self.assertEqual(ctx.exception.matches[0]["rule"], "jwt")
        self.assertEqual(self.secrets.send_if_clean("hello", lambda p: p.upper()), "HELLO")

    def test_require_clean_and_bad_kind(self):
        self.secrets.require_clean(row_with("fine"), "row")
        with self.assertRaises(self.secrets.SecretFound):
            self.secrets.require_clean(row_with(FAKES["slack-token"]), "row")
        with self.assertRaises(self.secrets.ScanError):
            self.secrets.scan("x", "email")


class Usage(unittest.TestCase):
    def test_unusable_input_is_exit_2_never_clean(self):
        cases = [
            ["scan"],
            ["scan", "--kind", "email"],
            ["scan", "--kind", "diff", "/nonexistent/secrets-input"],
            ["send"],
            ["send", "--", "/nonexistent/sender"],
            ["frobnicate"],
        ]
        for args in cases:
            with self.subTest(args=args):
                code, result, raw = run_secrets(args, stdin=b"hello\n")
                self.assertEqual(code, 2, raw)
                self.assertIn("error", result)
                self.assertNotIn("clean", result)


if __name__ == "__main__":
    unittest.main()
