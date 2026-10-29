
import hashlib, json, sys
def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def row_hash(row):
    body = {k: v for k, v in row.items() if k != "row_hash"}
    return hashlib.sha256(canonical(body) + row["prev_hash"].encode()).hexdigest()

def main(argv):
    if argv[0] == "hash":
        print(json.dumps({"row_hash": row_hash(json.loads(sys.stdin.read()))}))
        return
    prev = "0" * 64
    for line in open(argv[1]).read().splitlines():
        row = json.loads(line)
        if row["prev_hash"] != prev or row_hash(row) != row["row_hash"]:
            print(json.dumps({"valid": False, "broken_row": row["row_id"]}))
            return
        prev = row["row_hash"]
    print(json.dumps({"valid": True}))
if __name__ == "__main__":
    main(sys.argv[1:])
