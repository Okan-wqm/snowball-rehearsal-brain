"""Binds the copies of tohum/29s's two install steps to their source, ``spec/tohum/29s-dongu-girdileri.md``: test 46's
(``referee/tests/test_loop_workflow.py`` ``install_step``) and the code's (``referee/loop/inputs.py`` ``STEPS``, which
``loop.job`` renders). Each ``yaml`` fence of the page parses to exactly one step; the page must hold exactly the
steps named ``sigstore`` and ``claude``, once each, and each copy must equal the page's step. A page with another
number of fences or other names fails here rather than being guessed at. Run from the brain's root (the spec is not
in ``referee/``)."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))
sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))

from loop import inputs  # noqa: E402
from loop import job  # noqa: E402
from test_loop_workflow import INSTALLS, install_step  # noqa: E402
from workflow_yaml import parse  # noqa: E402

PAGE = os.path.join(ROOT, "spec", "tohum", "29s-dongu-girdileri.md")
NAMES = ("sigstore", "claude")


def spec_steps(page: str = PAGE) -> dict[str, dict]:
    with open(page, encoding="utf-8") as fh:
        blocks = re.findall(r"(?ms)^```yaml\n(.*?)^```$", fh.read())
    found: dict[str, dict] = {}
    for block in blocks:
        steps = parse("steps:\n" + block)["steps"]
        if len(steps) != 1:
            raise AssertionError("a 29s yaml block has %d steps, expected 1" % len(steps))
        name = steps[0].get("name")
        if name in found:
            raise AssertionError("29s names the step %r twice" % name)
        found[name] = steps[0]
    if tuple(sorted(found)) != tuple(sorted(NAMES)):
        raise AssertionError("29s's steps are %r, expected %r" % (sorted(found), sorted(NAMES)))
    return found


class InstallStepsAreTheSpecs(unittest.TestCase):
    def test_copies_equal_the_page(self):
        page = spec_steps()
        for name in NAMES:
            with self.subTest(step=name):
                self.assertEqual(install_step(name), page[name])
                self.assertEqual({"name": name, "if": job.GO, "run": inputs.STEPS[name]}, page[name])

    def test_the_rendered_jobs_carry_them(self):
        page = spec_steps()
        doc = parse(job.render())
        for name, installs in INSTALLS.items():
            with self.subTest(job=name):
                self.assertEqual([s for s in doc["jobs"][name]["steps"] if s.get("name") in NAMES],
                                 [page[i] for i in installs])

    def _page(self, text: str) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, fh.name)
        with fh:
            fh.write(text)
        return fh.name

    def test_a_changed_page_is_seen(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        for old, new, name in (("--require-hashes --only-binary=:all: --no-deps -d", "--only-binary=:all: --no-deps -d",
                                "sigstore"),
                               ("npm ci --prefix", "npm install --prefix", "claude"),
                               ("      - name: claude\n        if:", "      - name: claude\n        env:\n          A: b\n        if:",
                                "claude")):
            with self.subTest(change=new):
                self.assertIn(old, text)
                self.assertNotEqual(install_step(name), spec_steps(self._page(text.replace(old, new, 1)))[name])

    def test_blocks_not_guessed(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        first = re.search(r"(?ms)^```yaml\n.*?^```$", text).group(0)
        for page in (text.replace(first, ""), text + "\n" + first + "\n",
                     text.replace("- name: claude", "- name: cli", 1)):
            with self.assertRaises(AssertionError):
                spec_steps(self._page(page))


if __name__ == "__main__":
    unittest.main()
