"""UNFINISHED (wip/kilit-provasi; founder ledger f1111, f1113): no test of its own, not in snowball-tests.json.

The lock rehearsal: tohum/26d's "stage-open'ın kuralı" read by a second reader, written from the page, on
the final states of test_rehearsal's with-fixtures world (the run that writes the toy's PASS row). Nothing of
referee/'s readers is used to judge: git trees, chained files, canonical JSON, roots are computed here. Each check
prints what was read and whether it holds; what this world cannot show is listed as not_measured."""
import base64
import hashlib
import json
import os
import shutil
import sys

REFEREE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "referee")
sys.path.insert(0, REFEREE)
sys.path.insert(0, REFEREE + "/tests")
os.chdir(REFEREE)

import test_rehearsal as R  # noqa: E402

HEX64 = set("0123456789abcdef")
problems: list = []
not_measured: list = []
notes: dict = {}


def bad(check, why):
    problems.append([check, why])


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def is_hex64(s):
    return isinstance(s, str) and len(s) == 64 and set(s) <= HEX64


def no_dup(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate key")
    return dict(pairs)


def no_const(name):
    raise ValueError("constant " + name)


def chained(name, data):
    """26d 'Zincirli dosya': the rows, or a problem named."""
    rows = []
    if not data.endswith(b"\n") or b"\r" in data:
        bad(name, "lf_or_cr")
    prev = "0" * 64
    form = None
    for n, line in enumerate(data.split(b"\n")[:-1], 1):
        try:
            row = json.loads(line.decode("utf-8"), object_pairs_hook=no_dup, parse_constant=no_const)
            assert isinstance(row, dict)
        except Exception as e:  # noqa: BLE001
            bad(name, "line %d: %s" % (n, e))
            return rows
        if row.get("prev_hash") != prev:
            bad(name, "line %d: prev_hash" % n)
        body = canon({k: v for k, v in row.items() if k != "row_hash"})
        forms = {"hex": hashlib.sha256(body + prev.encode()).hexdigest(),
                 "raw": hashlib.sha256(body + bytes.fromhex(prev)).hexdigest()}
        match = [f for f, h in forms.items() if h == row.get("row_hash")]
        if not match:
            bad(name, "line %d: row_hash" % n)
        elif form is None:
            form = match[0]
        elif form not in match:
            bad(name, "line %d: row_hash form changes" % n)
        prev = row.get("row_hash")
        row["_line"] = line
        rows.append(row)
    notes.setdefault("row_hash_form", {})[name] = form
    return rows


def tree_of(objects, sha, prefix=""):
    """{path: (mode, blob sha)} of a git tree, read from its bytes."""
    kind, data = objects[sha]
    assert kind == "tree", kind
    out, i = {}, 0
    while i < len(data):
        sp = data.index(b" ", i)
        nul = data.index(b"\0", sp)
        mode, name, oid = data[i:sp].decode(), data[sp + 1:nul].decode(), data[nul + 1:nul + 21].hex()
        i = nul + 21
        if mode == "40000":
            out.update(tree_of(objects, oid, prefix + name + "/"))
        else:
            out[prefix + name] = (mode, oid)
    return out


def commit_tree(objects, sha):
    kind, data = objects[sha]
    assert kind == "commit", kind
    head = data.split(b"\n\n", 1)[0].decode()
    tree = [l.split(" ")[1] for l in head.split("\n") if l.startswith("tree ")][0]
    return tree_of(objects, tree)


def own(row):
    """26d: the referee's own row."""
    return ("proposed_by" not in row and row.get("trust") in ("verified", "observed")
            and row.get("derivation") in ("tool", "static_analysis", "test_verified") and row.get("part") == "events")


def proposal(row):
    p = row.get("proposed_by")
    return isinstance(p, str) and p != ""


def read(flow):
    """Everything the judge reads, as bytes: the checkout's three files, each target's state commit, the Rekor."""
    data = {"targets": {}, "rekor": {u: dict(e) for u, e in flow.rekor.entries.items()}}
    for key, path in (("imports", "/setup/imports.jsonl"), ("summary", "/setup/summary.json")):
        with open(flow.work + path, "rb") as fh:
            data[key] = fh.read()
    data["results"] = {}
    rdir = flow.work + "/setup/results"
    for name in os.listdir(rdir):
        with open(os.path.join(rdir, name), "rb") as fh:
            data["results"][name] = fh.read()
    for tid, kind, repo in R.TARGETS:
        hub = flow.hubs[repo]
        head = hub.refs.get(R.B.STATE)
        if head is None:
            data["targets"][kind] = None
            continue
        objects = hub.git_objects([head])
        tree = commit_tree(objects, head)
        data["targets"][kind] = {p: (mode, objects[oid][1]) for p, (mode, oid) in tree.items()}
    return data


def judge(data):
    """26d's rule on ``data``; the problems, and notes of what was read."""
    del problems[:], not_measured[:]
    notes.clear()
    imports = chained("setup/imports.jsonl", data["imports"])
    summary = json.loads(data["summary"])
    last_import = [r for r in imports if "referee_tree_sha256" in r][-1]
    import_line = hashlib.sha256(last_import["_line"]).hexdigest()
    result_bytes = data["results"].get("%s.json" % last_import["result_sha256"])
    if result_bytes is None or hashlib.sha256(result_bytes).hexdigest() != last_import["result_sha256"]:
        bad(1, "result bytes are not result_sha256's")
        result_bytes = next(iter(data["results"].values()))
    result = json.loads(result_bytes)
    not_measured.append("check 1: the referee tree hash of the --referee clone's commit (the world's checkout "
                        "holds no referee/ tree) and that the last import is stage 0's")
    state = {}
    for kind, tree in data["targets"].items():
        if tree is None:
            bad("Yer", "%s: no brain/state" % kind)
            return
        outside = sorted(p for p in tree if not p.startswith(".brain/"))
        notes.setdefault("state_tree", {})[kind] = {
            "files": len(tree), "outside_.brain": outside, "modes": sorted({m for m, _ in tree.values()}),
            "names": sorted(p for p in tree if "sigstore" not in p)}
        if outside:
            bad("Yer", "%s: files outside .brain/: %s" % (kind, outside))
        missing = [p for p in (".brain/ledger.jsonl", ".brain/chain/root.jsonl")
                   if p not in tree or tree[p][0] != "100644"]
        if missing:
            bad("Yer", "%s: %s is no regular file" % (kind, missing))
            return
        for p in [p for p in tree if p.endswith("profile.json")]:
            prof = json.loads(tree[p][1], object_pairs_hook=no_dup)
            if prof.get("state_root") not in (None, ".brain/"):
                bad("Yer", "%s: profile names %r" % (kind, prof.get("state_root")))
        ledger = chained(kind + ":ledger", tree[".brain/ledger.jsonl"][1])
        roots = chained(kind + ":root", tree[".brain/chain/root.jsonl"][1])
        if not ledger or not roots:
            return
        counted = [r for r in ledger if not proposal(r)]
        if ledger[0].get("kind") != "genesis":
            bad(2, "%s: first row is %s" % (kind, ledger[0].get("kind")))
        geneses = [i for i, r in enumerate(counted) if r.get("kind") == "genesis"]
        if not geneses:
            bad(2, "%s: no genesis" % kind)
            return
        g = counted[geneses[-1]]
        state[kind] = {"counted": counted, "g": geneses[-1]}
        entry = [t for t in summary["targets"] if t["kind"] == kind]
        if len(entry) != 1 or g["payload"].get("target") != entry[0]["id"]:
            bad(2, "%s: payload.target" % kind)
        if kind == "copy" and g["payload"].get("base_sha") != entry[0]["base_sha"]:
            bad(2, "copy: base_sha")
        for key, want in (("import_line_sha256", import_line),
                          ("referee_tree_sha256", last_import["referee_tree_sha256"]),
                          ("result_sha256", last_import["result_sha256"])):
            if g["payload"].get(key) != want:
                bad(2, "%s: %s" % (kind, key))
        if not own(g):
            bad(2, "%s: the genesis row is not the referee's own" % kind)
        notes.setdefault("genesis_rows", {})[kind] = len(geneses)
        notes.setdefault("rows", {})[kind] = {
            "ledger": len(ledger), "proposals": len(ledger) - len(counted),
            "proposed_by_null": sum(1 for r in ledger if "proposed_by" in r and r["proposed_by"] is None)}
        last_root = roots[-1]
        tips = {}
        for r in ledger:
            tips[r["part"]] = r["row_hash"]
        root = hashlib.sha256(canon(tips)).hexdigest()
        if last_root.get("root") != root:
            bad(8, "%s: the last root row's root is not the ledger's" % kind)
        bundle = ".brain/chain/%s.sigstore.json" % last_root.get("root")
        if bundle not in tree or tree[bundle][0] != "100644":
            bad(8, "%s: no bundle file of the last root in the commit" % kind)
        uuid = last_root.get("rekor_uuid")
        found = data["rekor"].get(uuid)
        if found is None:
            bad(8, "%s: rekor entry" % kind)
        else:
            raw = base64.b64decode(found["body"], validate=True)
            body = json.loads(raw)
            leaf = hashlib.sha256(b"\x00" + raw).hexdigest()
            if not (uuid == leaf or (len(uuid) == 80 and uuid[16:] == leaf)):
                bad(8, "%s: rekor_uuid is not the leaf hash" % kind)
            if (body.get("kind"), body.get("apiVersion")) != ("hashedrekord", "0.0.1"):
                bad(8, "%s: body %s %s" % (kind, body.get("kind"), body.get("apiVersion")))
            if body["spec"]["data"]["hash"] != {"algorithm": "sha256", "value": root}:
                bad(8, "%s: the entry's data hash is not the root" % kind)
        notes.setdefault("roots", {})[kind] = {"rows": len(roots), "parts": sorted(tips),
                                               "bundles_in_commit": sum(1 for p in tree if p.endswith(".sigstore.json"))}
    not_measured.append("check 8: the bundle's own verification ('sigstore verify identity' of sha256:<root>) and "
                        "the entry read from the bundle: the world's bundle is no Sigstore bundle; the entry was "
                        "read from the world's Rekor instead")
    toy, copy = state["toy"], state["copy"]
    after = toy["counted"][toy["g"] + 1:]
    passes = [i for i, r in enumerate(after)
              if r.get("part") == "events" and isinstance(r.get("payload"), dict)
              and type(r["payload"].get("stage")) is int and r["payload"]["stage"] == 0
              and r["payload"].get("verdict") == "PASS"]
    notes["pass_rows"] = len(passes)
    if not passes:
        bad(3, "no PASS row after the toy's last genesis")
        return
    p = after[passes[0]]
    notes["pass_row"] = {"kind": p["kind"], "payload_keys": sorted(p["payload"])}
    if not own(p):
        bad(4, "the PASS row is not the referee's own")
    merges = [r for r in after[:passes[0]] if r.get("kind") == "merge"]
    if not merges:
        bad(4, "no merge row between the toy's last genesis and the PASS row")
    if any(not own(m) for m in merges):
        bad(4, "a merge row is not the referee's own")
    notes["toy_merge_rows_before_pass"] = len(merges)
    pl = p["payload"]
    if pl.get("import_line_sha256") != import_line or not is_hex64(pl.get("import_line_sha256")):
        bad(5, "import_line_sha256")
    cg = copy["counted"][copy["g"]]
    if pl.get("copy_genesis_row_hash") != cg["row_hash"]:
        bad(6, "copy_genesis_row_hash")
    cm = [r["row_hash"] for r in copy["counted"][copy["g"] + 1:] if r.get("kind") == "merge" and own(r)]
    got = pl.get("copy_merge_row_hashes")
    if not (isinstance(got, list) and got and len(set(got)) == len(got) and set(got) <= set(cm)):
        bad(6, "copy_merge_row_hashes")
    notes["copy_merge_rows"] = {"in_ledger_after_genesis": len(cm), "named": len(got or [])}
    want = result.get("exit", {}).get("owner_exception")
    have = pl.get("owner_exception")
    if (want is None) != (have is None) or (want is not None and canon(want) != canon(have)):
        bad(7, "owner_exception")
    if have is not None:
        keys = {"anchor", "stage", "carry_to", "reason", "carry_commitment", "measured"}
        if [e["anchor"] for e in have] != sorted(e["anchor"] for e in have) or any(set(e) != keys for e in have):
            bad(7, "owner_exception's form")
    notes["owner_exception"] = None if have is None else [e["anchor"] for e in have]


def rechain(data: bytes, edit) -> bytes:
    """The chained file with ``edit(rows)`` applied and every hash written again (the tamperer's own honest chain)."""
    rows = [json.loads(l) for l in data.decode().splitlines()]
    edit(rows)
    prev, out = "0" * 64, []
    for row in rows:
        row["prev_hash"] = prev
        row.pop("row_hash", None)
        row["row_hash"] = prev = hashlib.sha256(canon(row) + prev.encode()).hexdigest()
        out.append(canon(row) + b"\n")
    return b"".join(out)


def with_file(data, kind, path, content):
    out = dict(data, targets={k: dict(v) for k, v in data["targets"].items()})
    if content is None:
        del out["targets"][kind][path]
    else:
        out["targets"][kind][path] = ("100644", content)
    return out


def pass_edit(change):
    def edit(rows):
        for r in rows:
            if r["kind"] == "pass":
                change(r)
    return edit


def tampers(data):
    """name -> (tampered data, the check that must name it)."""
    L, RT = ".brain/ledger.jsonl", ".brain/chain/root.jsonl"
    toy, copy = data["targets"]["toy"], data["targets"]["copy"]
    last_root = json.loads(toy[RT][1].decode().splitlines()[-1])
    out = {}
    out["no_bundle"] = (with_file(data, "toy", ".brain/chain/%s.sigstore.json" % last_root["root"], None), 8)
    moved = with_file(data, "toy", L, None)
    moved["targets"]["toy"]["ledger.jsonl"] = toy[L]
    out["ledger_outside_.brain"] = (moved, "Yer")
    out["pass_proposed_by_null"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r.update(proposed_by=None)))), 4)
    out["pass_proposed"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r.update(proposed_by="player", trust="inferred")))), 3)
    out["pass_other_import"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r["payload"].update(import_line_sha256="a" * 64)))), 5)
    out["pass_stage_true"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r["payload"].update(stage=False)))), 3)
    out["pass_other_copy_genesis"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r["payload"].update(copy_genesis_row_hash="b" * 64)))), 6)
    out["pass_unknown_copy_merge"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r["payload"].update(copy_merge_row_hashes=["c" * 64])))), 6)
    out["pass_exception_reordered"] = (with_file(data, "toy", L, rechain(toy[L][1], pass_edit(
        lambda r: r["payload"]["owner_exception"].reverse()))), 7)

    def other_result(rows):
        [g] = [r for r in rows if r["kind"] == "genesis"]
        g["payload"]["result_sha256"] = "d" * 64
    out["copy_genesis_other_result"] = (with_file(data, "copy", L, rechain(copy[L][1], other_result)), 2)
    out["toy_last_line_without_lf"] = (with_file(data, "toy", L, toy[L][1][:-1]), "toy:ledger")
    out["toy_row_byte_changed"] = (with_file(data, "toy", L, toy[L][1].replace(b'"stage":0', b'"stage":1', 1)
                                             if b'"stage":0' in toy[L][1] else toy[L][1].replace(b'"stage": 0', b'"stage": 1', 1)),
                                   "toy:ledger")
    uuid = last_root["rekor_uuid"]
    body = json.loads(base64.b64decode(data["rekor"][uuid]["body"]))
    body["apiVersion"] = "0.0.2"
    v2 = dict(data, rekor=dict(data["rekor"]))
    v2["rekor"][uuid] = dict(data["rekor"][uuid], body=base64.b64encode(json.dumps(body).encode()).decode())
    out["rekor_v2_body"] = (v2, 8)
    out["tip_moved"] = (with_file(data, "copy", L, rechain(copy[L][1], lambda rows: rows[-1]["payload"].update(x=1)
                                                           if isinstance(rows[-1]["payload"], dict) else None)), 8)
    return out


def main():
    base = R.writable_base("lock-rehearsal-")
    try:
        flow = R.with_fixtures(base)
        records = R.rehearse(flow)
        data = read(flow)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    judge(data)
    clean = {"ok": not problems, "problems": list(problems), "not_measured": list(not_measured),
             "notes": dict(notes, runs=len(records), ended=R.ended(records[-1]))}
    controls, silent = {}, []
    for name, (tampered, check) in tampers(data).items():
        try:
            judge(tampered)
        except Exception as e:  # noqa: BLE001
            problems.append(["crash", "%s: %s" % (type(e).__name__, e)])
        named = sorted({str(c) for c, _ in problems})
        controls[name] = {"expected": str(check), "named": named}
        if str(check) not in named:
            silent.append(name)
    print(json.dumps(clean, indent=1, sort_keys=True))
    print(json.dumps({"controls": controls, "silent_controls": silent}, indent=1, sort_keys=True))
    return 1 if clean["problems"] or silent else 0


if __name__ == "__main__":
    sys.exit(main())
