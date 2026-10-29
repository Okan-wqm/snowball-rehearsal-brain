
import json, sys
def score(findings, cases):
    hits, used = 0, set()
    for case in cases:
        for i, f in enumerate(findings):
            if i in used: continue
            if (f.get("tool") == case.get("tool") and f.get("rule_id") == case.get("rule_id")
                    and any(ref["path"] == tp["path"] and any(h["start"] <= ref["line_start"] <= h["end"]
                            for h in tp["hunks"]) for ref in f["evidence_refs"] for tp in case["touched_paths"])):
                hits += 1; used.add(i); break
    return hits
if __name__ == "__main__":
    print(json.dumps({"hits": score(json.load(open(sys.argv[1])), json.load(open(sys.argv[2])))}))
