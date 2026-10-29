"""Test 38 (asama-0/09): a fake secret embedded in a diff, a ledger row and a prompt is caught; a match
invalidates the run and the prompt is not sent.

Every command case drives ``python -m gate.secrets`` from ``referee/`` in a subprocess, the way the
referee runs it; input goes through stdin or a pipe (``/dev/fd/N``), so nothing is written to disk and
the suite runs in a read-only container. No fake secret is written literally in this file: each is
assembled at run time from split parts, so the file itself (and the diff that carries it to the
rival's prompt) holds no secret-shaped text. Expected fingerprints are computed here with hashlib.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
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

# A broader shape than the scanner's own assignment rule: no template, placeholder or code exclusion,
# and a value cut only at whitespace or a quote. The scanner lets placeholders and code through on
# purpose; the seed keeps any such text out of the rival's prompt (29b:26), so the files this repo
# pushes must not hold it at all.
BROAD = [
    ("assignment", re.compile(
        r"(?i)(?:passw(?:or)?d|passphrase|pwd|secret|token|api[_\-]?key|access[_\-]?key|private[_\-]?key|"
        r"credential|auth)[A-Za-z0-9_\-]*[\"'`]?\]?[ \t]*(?:===?|!==?|:=|=>|[:=])[ \t]*[\"'`]?([^\s\"'`]{8,})")),
    ("url-userinfo", re.compile(r"://[^\s/@\"']+:[^\s/@\"']+@")),
    ("key-block", re.compile(r"BEGIN [A-Z ]*PRIVATE KEY")),
]
PUSHED = ("referee/gate/secrets.py", "referee/tests/test_secrets.py", "referee/ledger/chain.py",
          "referee/tests/test_chain.py", "snowball-tests.json")


def broad_hits(text: str) -> list:
    return [(n, name, m.group(0)[:40]) for n, line in enumerate(text.splitlines(), 1)
            for name, pattern in BROAD for m in pattern.finditer(line)]


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

    def assert_all_caught(self, cases: list, rule: str = "secret-assignment"):
        """One scan per kind holding every case on its own line (one row per line for rows); each value
        must be reported under ``rule`` by its own fingerprint and none may leak into the output."""
        texts = [text for text, _ in cases]
        for kind, wrapped in (("prompt", prompt_with("\n\n".join(texts))),
                              ("row", "\n".join(row_with(text) for text in texts)),
                              ("diff", diff_with("\n+".join(texts)))):
            code, result, raw = scan(kind, wrapped)
            self.assertEqual(code, 1, raw)
            found = {m["sha256"] for m in result["matches"] if m["rule"] == rule}
            for text, value in cases:
                with self.subTest(text=text, kind=kind):
                    self.assertIn(sha(value), found)
                    self.assertNotIn(value.encode(), raw)

    def test_every_rule_in_diff_row_and_prompt(self):
        for rule, token in FAKES.items():
            with self.subTest(rule=rule, kind="diff"):
                self.assert_caught("diff", diff_with('KEY = "%s"' % token), rule, token, line=7)
            with self.subTest(rule=rule, kind="row"):
                self.assert_caught("row", row_with("found %s in config" % token), rule, token, line=1)
            with self.subTest(rule=rule, kind="prompt"):
                self.assert_caught("prompt", prompt_with("value: %s" % token), rule, token, line=4)

    def test_token_glued_to_word_characters_is_caught(self):
        """A token right after or before "_", a letter or a digit has no word boundary; it still leaks.

        Rejection of 1c83fb7 (repro f1a0971b4ed0529f): x_ plus a GitHub token was reported clean.
        """
        glued = [("x_", ""), ("A", ""), ("9", ""), ("", "_x"), ("", "Z"), ("", "7"), ("see_x_", "_end")]
        for rule, token in FAKES.items():
            for before, after in glued:
                with self.subTest(rule=rule, before=before, after=after):
                    text = j(before, token, after)
                    for kind, wrapped in (("prompt", prompt_with("see %s" % text)), ("row", row_with(text)),
                                          ("diff", diff_with('KEY = "%s"' % text))):
                        code, result, raw = scan(kind, wrapped)
                        self.assertEqual(code, 1, raw)
                        self.assertIn(rule, {m["rule"] for m in result["matches"]}, (kind, result))
                        self.assertNotIn(token.encode(), raw)
        url = j("_postgres://admin:", URL_PASSWORD, "@db.internal/app")
        code, result, raw = scan("prompt", prompt_with(url))
        self.assertIn("url-credentials", {m["rule"] for m in result["matches"]}, raw)
        aws = "aws_secret_access_key = %sQ" % AWS_SECRET_VALUE
        code, result, raw = scan("prompt", prompt_with(aws))
        self.assertIn("aws-secret-key", {m["rule"] for m in result["matches"]}, raw)

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
        # no upper length cap: a long random value is still a secret
        long_value = body("assigned-long", 300)
        self.assert_caught("prompt", prompt_with('client_secret = "%s"' % long_value), "secret-assignment",
                           long_value)

    def test_bare_and_weak_assigned_values_are_caught(self):
        """A value after a secret-named key leaks whether it is quoted, bare, random or weak.

        Rejection of 99278a5 (the rival's verdict was withheld for holding a bare assignment): the
        assignment rule only took quoted, random-looking values, so an unquoted one scanned clean. In a
        JSON row the quotes around a value are escaped; they are decoded before the scan.
        """
        pw, tok, sec = j("pass", "word"), j("to", "ken"), j("sec", "ret")
        weak = j("hunter", "22")
        random_value = body("bare", 20)
        cases = [
            ("DB_%s=%s" % (pw.upper(), random_value), random_value),
            ("DB_%s=%s" % (pw.upper(), weak), weak),
            ("x_%s: %s" % (tok, random_value), random_value),
            ('%s = "%s"' % (pw, weak), weak),
            ('{"client_%s": "%s"}' % (sec, weak), weak),
            ("export API_%s=%s;" % (tok.upper(), random_value), random_value),
            ("the %s is %s=%s." % (pw, pw, weak), weak),
            ("%s := `%s`" % (tok, weak), weak),
        ]
        for text, value in cases:
            for kind, wrapped in (("prompt", prompt_with(text)), ("row", row_with(text)),
                                  ("diff", diff_with(text))):
                with self.subTest(text=text, kind=kind):
                    self.assert_caught(kind, wrapped, "secret-assignment", value)

    def test_only_a_whole_template_is_skipped(self):
        """Rejection of 6e29850 (refutation fff7b2af3d2f6053): a value that started with $, <, { or %,
        or held "(", was taken for a template, so a real password beginning with a dollar sign scanned
        clean. Now only a value that is a template as a whole is skipped; a quoted value may hold spaces.
        """
        pw, tok, sec = j("pass", "word"), j("to", "ken"), j("sec", "ret")
        values = [j("$uper", "S3cretVal9"), j("<b>", "Secret99"), j("{x}", "Secret99"), j("%", "Secret99x"),
                  j("f(x)", "Secret9"), j("abc${X}", "def99"), j("Correct.", "Horse9"), j("Correct.", "Horse"),
                  j("correct horse ", "battery staple")]
        for value in values:
            for text in ('%s="%s"' % (pw, value), "%s: '%s'" % (sec, value), '{"client_%s": "%s"}' % (sec, value)):
                for kind, wrapped in (("prompt", prompt_with(text)), ("row", row_with(text)),
                                      ("diff", diff_with(text))):
                    with self.subTest(text=text, kind=kind):
                        self.assert_caught(kind, wrapped, "secret-assignment", value)
        # unquoted: a dollar sign before a lower-case or mixed name is not an environment variable
        bare = j("$uper", "S3cretVal9")
        self.assert_caught("prompt", prompt_with("%s=%s" % (tok, bare)), "secret-assignment", bare)

    def test_value_runs_to_whitespace_not_to_punctuation(self):
        """Rejection of 8265299 (refutation 8d96fe1aafd87a0e): an unquoted value was cut at the first
        , ; ( ) [ ] { }, so a key followed by ab;cd;ef;gh;ij scanned clean. Now an unquoted value runs to
        the first whitespace outside brackets; only one trailing , ; . : and unmatched closers are syntax.
        """
        pw, tok = j("pass", "word"), j("to", "ken")
        values = [j("ab;cd", ";ef;gh;ij"), j("ab,cd", ",ef,gh"), j("Xy7(k9", "!pQ)"), j("ab[cd]", "ef9"),
                  j("ab{cd}", "ef9"), j("ab)cd", "efgh"), j("p@ss;", "w0rd;x")]
        forms = ("%s=%%s" % pw, "%s: %%s" % tok, "export DB_%s=%%s;" % pw.upper(), "f(%s=%%s)" % pw,
                 "{%s: %%s}," % tok)
        # every case has its own value, so one line's match cannot stand in for another's
        cases = [(form % (value + str(n)), value + str(n)) for value in values for n, form in enumerate(forms)]
        self.assert_all_caught(cases)
        # the rival's reproducer, alone, as the referee ran it
        self.assert_caught("prompt", "%s=%s\n" % (pw, values[0]), "secret-assignment", values[0])

    def test_quoted_values_hold_escaped_quotes_glued_tails_and_no_close(self):
        pw, sec = j("pass", "word"), j("sec", "ret")
        cases = [
            ('%s="%s"' % (pw, j("ab\\", '"cdefghij')), j("ab\\", '"cdefghij')),
            ('%s="%s"%s' % (pw, "abc", "defghij"), "abcdefghij"),
            ('%s="%s' % (pw, j("hunter", "22a")), j("hunter", "22a")),
            ("%s = b'%s'" % (sec, j("hunter", "22b")), j("hunter", "22b")),
            ('%s = f"%s{x}"' % (sec, j("hunter", "22c")), j("hunter", "22c{x}")),
        ]
        self.assert_all_caught(cases)

    def test_every_assignment_form_is_caught(self):
        """Forms the old pattern missed: a subscripted key, a comparison, a type annotation, the Go
        string type, a command-line flag, an authorization scheme word, a keyword argument, a JSON array."""
        pw, tok, auth = j("pass", "word"), j("to", "ken"), j("Auth", "orization")

        def weak(n: int) -> str:  # one value per case, so no case is found by another's line
            return j("hunter", "22x", str(n))

        def opaque(n: int) -> str:
            return body("opaque%d" % n, 32)

        cases = [
            ('config["%s"] = "%s"' % (pw, weak(1)), weak(1)),
            ("os.environ['DB_%s'] = '%s'" % (pw.upper(), weak(2)), weak(2)),
            ('if %s == "%s":' % (pw, weak(3)), weak(3)),
            ("if (%s !== '%s') {" % (tok, weak(4)), weak(4)),
            ('%s: str = "%s"' % (pw, weak(5)), weak(5)),
            ('%s: Optional[str] = "%s"' % (pw, weak(6)), weak(6)),
            ('var %s string = "%s"' % (pw, weak(7)), weak(7)),
            ("mysql --%s %s db" % (pw, weak(8)), weak(8)),
            ("curl --oauth2-bearer-%s %s" % (tok, opaque(9)), opaque(9)),
            ("%s: Bearer %s" % (auth, opaque(10)), opaque(10)),
            ('{"%s": "Basic %s"}' % (auth, opaque(11)), opaque(11)),
            ("login(user, %s=%s)" % (pw, weak(12)), weak(12)),
            ('[{"%s": "%s"},{"user": "bob"}]' % (pw, weak(13)), weak(13)),
        ]
        self.assert_all_caught(cases)
        # a URL password of any length (the rule took 6 or more characters)
        for short in (j("ab", "c12"), "ab"):
            with self.subTest(url_password=short):
                code, result, raw = scan("prompt", prompt_with(j("postgres://admin:", short, "@db.internal/app")))
                self.assertEqual(code, 1, raw)
                self.assertIn("url-credentials", {m["rule"] for m in result["matches"]})

    def test_every_secret_named_key_is_caught(self):
        """Each rule of _secret_key on its own value: a part anywhere in a word (DB_PASS, DBPASS), a name
        word, a word ending in key, session id, words split at _ - . and camelCase, PLAIN_WORDS not hiding
        another word, and the R arrow and Dockerfile ENV forms."""
        def value(n: int) -> str:  # one random 12-character value per case, like Zq8xLm2Pv9Rt
            return body("named%d" % n, 12)

        keys = [j("DB_", "PASS"), j("db", "Pass"), j("DB", "PASS"), j("db.", "pass"), j("MYSQL_", "PWD"),
                j("user_", "pin"), j("OTP_", "SEED"), j("app_", "creds"), j("session", "_id"), j("SESSION", "ID"),
                j("STRIPE_", "KEY"), j("api", "Key"), j("master", "key"), j("X-Api", "-Key"), j("jwt.sec", "ret.key"),
                j("spring.datasource.pass", "word"), j("o", "auth_client"), j("COOK", "IE"), j("bypass_", "pass"),
                j("ş", "ifre"), j("par", "ola"), j("kenn", "wort"), j("signing_", "keys"), j("auth", "Token")]
        cases = [("%s=%s" % (key, value(n)), value(n)) for n, key in enumerate(keys)]
        cases += [
            ("%s <- '%s'" % (j("db_", "pass"), value(100)), value(100)),
            ("ENV %s %s" % (j("DB_", "PASS"), value(101)), value(101)),
            ("%s: %s" % (j("X-Api", "-Key"), value(102)), value(102)),
            ("--%s %s" % (j("db-", "pass"), value(103)), value(103)),
        ]
        self.assert_all_caught(cases)

    def test_split_and_encoded_tokens_are_caught(self):
        """A token split over two lines, base64-encoded or percent-encoded still leaks."""
        token = FAKES["github-token"]
        half = len(token) // 2
        split = "see %s\n    %s please" % (token[:half], token[half:])
        self.assert_caught("prompt", prompt_with(split), "github-token", token)
        code, result, raw = scan("diff", diff_with("x = '%s\\\n+%s'" % (token[:half], token[half:])))
        self.assertEqual(code, 1, raw)
        self.assertIn(sha(token), {m["sha256"] for m in result["matches"]})
        for name, encoded in (("base64", base64.b64encode(("t=" + token).encode()).decode()),
                              ("base64url", base64.urlsafe_b64encode(token.encode()).decode().rstrip("=")),
                              ("percent", "".join("%%%02X" % ord(c) for c in token))):
            for kind, wrapped in (("prompt", prompt_with("blob " + encoded)), ("row", row_with(encoded)),
                                  ("diff", diff_with("B = '%s'" % encoded))):
                with self.subTest(name=name, kind=kind):
                    self.assert_caught(kind, wrapped, "github-token", token)
        # a value on the line after its key (YAML), in a prompt and a diff
        pw, weak = j("pass", "word"), j("hunter", "22")
        self.assert_caught("prompt", prompt_with("db:\n  %s:\n    %s\n" % (pw, weak)), "secret-assignment", weak)
        self.assert_caught("diff", diff_with("%s:\n+  %s" % (pw, weak)), "secret-assignment", weak)

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
        # key names are assembled too: a literal quoted value after a secret-named key is the shape the
        # seed keeps out of the rival's prompt, placeholder or not (see BROAD below)
        tok, pw, key, sec = j("to", "ken"), j("pass", "word"), j("api", "_key"), j("sec", "ret")
        lines = [
            "%s = get_%s(request)" % (tok, tok),
            '%s = "<placeholder>"' % pw,
            '%s = os.environ["%s"]' % (key, key.upper()),
            '%s = "${%s_FROM_ENV}"' % (sec, sec.upper()),
            '%s = "%s"' % (tok, "a" * 24),
            "%s = self.%s" % (tok, tok),
            "%s = request.form" % pw,
            "%s = %s_value" % (sec, sec),
            "%s_name = %s" % (tok, j("change", "me")),
            "rejected: %s_in_verdict:generic_assignment." % sec,
            "url = 'https://user" + ":%s@example.com/'" % pw,
            "commit 632a84cc3e7e70741607457a4060e375caa0e3a4",
            "row_hash 3bae91580aca99362572e9f5f41b3e46c2bc0c29236f72e867faa5cd46ca603a",
            "id 123e4567-e89b-12d3-a456-426614174000",
            "-----BEGIN PUBLIC KEY-----",
            # whole templates, quoted or bare
            "%s=${DB_%s}" % (pw, pw.upper()),
            "%s=$DB_%s" % (pw, pw.upper()),
            '%s: "{{ db_%s }}"' % (pw, pw),
            "%s = '%%(%s)s'" % (sec, sec),
            "%s=%%API_%s%%" % (tok, tok.upper()),
            '%s = "<your-api-%s>"' % (tok, tok),
            # consecutive hashes and base64 of plain words: no split or decoded token
            "3bae91580aca99362572e9f5f41b3e46c2bc0c29236f72e867faa5cd46ca603a",
            "640eae94a77d1a73c0676cf52e681cb3aa0593f607f6feab6ca9a43a8f094460",
            base64.b64encode(b"plain words, nothing to hide here").decode(),
            # code on the right of a secret-named key: calls, subscripts, slices, f-strings, templates
            "%s = get_%s(request, scope)" % (tok, tok),
            'headers = {"%s": f"Bearer {%s}"}' % (j("Auth", "orization"), tok),
            '%s = jwt.encode(payload, key, algorithm="HS256")' % tok,
            '%s = os.environ.get("DB_%s", "")' % (pw, pw.upper()),
            "%s = hashlib.sha256(salt + pw).hexdigest()" % tok,
            "%s = (salt + pw).encode()" % tok,
            "%s: Optional[str] = load_%s(path)" % (tok, tok),
            "%s = `Bearer ${%s}`" % (j("au", "th"), tok),
            '"%s": FAKES["x"][:-1],' % tok,
            "%s = load_settings(" % sec,
            "%s = SECRET_KEY" % sec,
            "if %s == expected_%s:" % (tok, tok),
            j("url = 'https://user:", "${DB_%s}" % pw.upper(), "@example.com/'"),
            "the %s budget: unlimited" % tok,

            "the next line starts a word",
            "whatever comes next",
        ]
        self.assert_clean("diff", diff_with("\n+".join(lines)))
        self.assert_clean("prompt", prompt_with("\n".join(lines)))
        self.assert_clean("prompt", "")

    def test_keys_that_are_not_secret_named(self):
        """The stated boundaries and exclusions of _secret_key: the bare word key alone, PLAIN_WORDS, a
        file name, a key none of whose words is secret-named, and a Python if-line ending in a colon
        (only a key that starts its line takes its value from the next line)."""
        def value(n: int) -> str:
            return body("plain%d" % n, 12)

        lines = ["%s=%s" % (key, value(n)) for n, key in enumerate(
            ["key", "KEY", "keys", "compass", "bypass", "author", "tokenizer", "monkey_name", "passenger",
             "DB_CONN", "LOGIN", "pinned", "keyboard"])]
        lines += [
            "sorted(rows, key=%s)" % value(50),
            "%s: %s" % (j("test_sec", "rets.py"), value(51)),
            "%s: %s" % (j("notes/to", "ken.md"), value(52)),
            "if word in %s:" % j("TO", "KENS"),
            "    continue",
        ]
        self.assert_clean("diff", diff_with("\n+".join(lines)))
        self.assert_clean("prompt", prompt_with("\n".join(lines)))

    def test_broad_shape_catches_what_the_scanner_lets_through(self):
        """BROAD is stricter than the scanner: placeholders after a secret-named key are flagged."""
        tok, pw = j("to", "ken"), j("pass", "word")
        for text in ('%s = "%s"' % (tok, "a" * 24), "%s = get_%s(request)" % (tok, tok), '%s: "<placeholder>"' % pw, "%s=%s" % (pw, "hunter22"),
                     j("https://user", ":%s@example.com/" % pw), j("-----BEGIN RSA ", "PRIVATE KEY-----")):
            with self.subTest(text=text):
                self.assertTrue(broad_hits(text))
        for text in ("row_hash: 3bae9158", "key = None", "-----BEGIN PUBLIC KEY-----"):
            with self.subTest(text=text):
                self.assertEqual(broad_hits(text), [])

    def test_pushed_files_hold_no_assignment_shaped_text(self):
        """No pushed file, nor any report, holds text the seed would keep out of the rival's prompt."""
        reports = os.path.join(BRAIN, "reports")
        paths = list(PUSHED) + ["reports/" + n for n in sorted(os.listdir(reports)) if n.endswith(".json")]
        for rel in paths:
            with self.subTest(path=rel):
                with open(os.path.join(BRAIN, rel), encoding="utf-8") as fh:
                    self.assertEqual(broad_hits(fh.read()), [])

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
