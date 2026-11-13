"""UNFINISHED (wip/kilit-provasi; founder ledger f1109, f1112): no test of its own, not in snowball-tests.json.

asama-0/14's module-less red for every MF of the page's table, run with
tests/run_like_referee.py's own functions. For each MF row: each test of the row runs on the commit's file list
minus referee/<module>; a run that stays green is listed."""
import concurrent.futures
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_like_referee as R  # noqa: E402

ROOT = R.ROOT
PAGE = ROOT + "/spec/asama-0/14-sirali-mikro-ozellikler.md"


def table():
    rows = []
    for line in open(PAGE, encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and re.fullmatch(r"\d+", cells[0]):
            module = re.fullmatch(r"`([^`]+)`", cells[4]).group(1)
            tests = ["T" + t for t in re.findall(r"\d+", cells[2])]
            rows.append((int(cells[0]), tests, module))
    return rows


def main():
    rows = table()
    assert [r[0] for r in rows] == list(range(1, 19)), rows
    names = R.files(ROOT)
    by_id = {t["id"]: t for t in R.manifest(ROOT)}
    work = tempfile.mkdtemp(prefix="module-less-")
    path = R.bindir(work + "/bin")
    jobs = []
    for mf, tests, module in rows:
        gone = "referee/" + module
        assert gone in names, gone
        left = [n for n in names if n != gone]
        for t in tests:
            jobs.append((mf, module, by_id[t], left))
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        results = list(pool.map(lambda j: (j, R.run_one(j[2], ROOT, j[3], path, work, 1800.0)), jobs))
    green = []
    for (mf, module, test, _), r in results:
        print(json.dumps({"mf": mf, "module": module, "test": test["id"], "exit": r["exit"],
                          "timed_out": r["timed_out"], "duration_ms": r["duration_ms"],
                          "tail": r["tail"][-160:]}))
        if r["exit"] == 0 or r["timed_out"]:
            green.append([mf, test["id"]])
    R.remove(work)
    print(json.dumps({"runs": len(results), "green_or_timed_out": green}))
    return 1 if green else 0


if __name__ == "__main__":
    sys.exit(main())
