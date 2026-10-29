
import json, sys
from harness import drill_judge
if __name__ == "__main__" and sys.argv[1] == "judge":
    out = drill_judge.judge(json.load(open(sys.argv[2])))
    print(json.dumps({"drill": out["drill"], "verdicts": out["verdicts"]}))
