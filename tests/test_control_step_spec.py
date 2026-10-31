"""Binds test 46's copy of the control step (``referee/tests/test_loop_workflow.py`` ``control_step``) to its source,
the YAML block under "Adım" in ``spec/tohum/29p-kontrol-komutu.md``: the block, with ``<iş>`` read as a job's name,
parses to the same step. The block is found as the only ``yaml`` fence of the page; a page with none or several
fails here rather than being guessed at. Run from the brain's root (the spec is not in ``referee/``)."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))
sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))

from test_loop_workflow import JOBS, control_step  # noqa: E402
from workflow_yaml import parse  # noqa: E402

PAGE = os.path.join(ROOT, "spec", "tohum", "29p-kontrol-komutu.md")


def spec_step(job: str, page: str = PAGE) -> dict:
    with open(page, encoding="utf-8") as fh:
        blocks = re.findall(r"(?ms)^```yaml\n(.*?)^```$", fh.read())
    if len(blocks) != 1:
        raise AssertionError("29p has %d yaml blocks, expected 1" % len(blocks))
    steps = parse("steps:\n" + blocks[0].replace("<iş>", job))["steps"]
    if len(steps) != 1:
        raise AssertionError("29p's block has %d steps, expected 1" % len(steps))
    return steps[0]


class ControlStepIsTheSpecs(unittest.TestCase):
    def test_copy_equals_the_page(self):
        for job in JOBS:
            with self.subTest(job=job):
                self.assertEqual(control_step(job), spec_step(job))

    def _page(self, text: str) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, fh.name)
        with fh:
            fh.write(text)
        return fh.name

    def test_a_changed_page_is_seen(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        for old, new in (("--depth 1", "--depth 2"), ("LOOP_JOB: <iş>", "LOOP_JOB: <iş>\n          X: y"),
                         ("        id: control\n", "        id: control\n        shell: bash\n")):
            with self.subTest(change=new):
                self.assertIn(old, text)
                self.assertNotEqual(control_step("cek"), spec_step("cek", self._page(text.replace(old, new, 1))))
        self.assertNotEqual(control_step("cek"), spec_step("kos"))

    def test_block_not_guessed(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        block = re.search(r"(?ms)^```yaml\n.*?^```$", text).group(0)
        for page in (text.replace(block, ""), text + "\n" + block + "\n"):
            with self.assertRaises(AssertionError):
                spec_step("cek", self._page(page))

if __name__ == "__main__":
    unittest.main()
