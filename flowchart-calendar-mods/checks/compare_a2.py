#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2 — EX `回想` 표(need→play) ↔ 추출한 `memory.json` / `replay_of`.

  python compare_a2.py [--selftest]
"""
import sys, os, re, io, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def ex_memory():
    """`tree 回想` 을 페이지별로 직접 읽는다."""
    out = []
    page = 0
    inside = False
    depth = 0
    with io.open(C.EXX, encoding="utf-8", errors="replace") as fp:
        for ln in fp:
            s = ln.rstrip("\n")
            if not inside:
                if re.match(r"^tree\s+回想\s*=\s*\{", s):
                    inside = True
                    depth = 1
                continue
            depth += s.count("{") - s.count("}")
            if depth <= 0:
                break
            if re.match(r"^\s*ページ.+=\s*\(table\)\s*\{", s):
                page += 1
                continue
            m = re.match(r"^\s*\{\s*(\d+),\s*(\d+),\s*(\d+)\s*\}\s*,?\s*$", s)
            if m:
                out.append((page, int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return out


def run(inject=None):
    ref = ex_memory()
    if inject is not None:
        ref = [(p, i, n, (pl + 1 if i == inject else pl)) for (p, i, n, pl) in ref]
    mem = C.load_graph("memory.json")["entries"]
    sch = C.load_graph("schedule.json")
    byid = {e["id"]: e for e in sch["events"]}
    bad = []
    got = {(m["page"], m["id"]): (m["need"], m["play"]) for m in mem}
    for p, i, need, play in ref:
        g = got.get((p, i))
        if g is None:
            bad.append((p, i, "추출 결과에 이 칸이 없다"))
            continue
        if g != (need, play):
            bad.append((p, i, f"표 {need}->{play} != 추출 {g[0]}->{g[1]}"))
            continue
        e = byid.get(play)
        if e is None:
            bad.append((p, i, f"playEvNo {play} 함수가 없다"))
            continue
        if e["replay_of"] != need:
            bad.append((p, i, f"replay_of {e['replay_of']} != {need}"))
        if not any(t["kind"] == "memory_replay" for t in e["triggers"]):
            bad.append((p, i, "memory_replay 트리거가 없다"))
    if len(got) != len(ref):
        bad.append(("*", "*", f"칸 수 {len(ref)} != {len(got)}"))
    # 재생본 64개가 전부 짝이 있나 (E5xxxx)
    replays = [e for e in sch["events"] if 50000 <= e["id"] < 60000]
    for e in replays:
        if e["replay_of"] is None and not any(t["kind"] == "dungeon" or t["kind"] == "special_day"
                                              for t in e["triggers"]):
            bad.append((None, e["id"], "E5xxxx 인데 회상 짝도 던전 호출도 없다"))
    return ref, bad


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ref, bad = run(inject=3)
        ok = len(bad) > 0
        print("SELFTEST", "PASS" if ok else "FAIL", f"({len(bad)}건 걸림)")
        for b in bad[:3]:
            print("   ", b)
        ref, bad = run()
        print("결함 없는 원본:", "문제 0건" if not bad else f"문제 {len(bad)}건 — 자체시험 무효")
        sys.exit(0 if ok and not bad else 1)
    ref, bad = run()
    print(f"A2: 회상 {len(ref)}칸 대조, 문제 {len(bad)}건")
    for b in bad[:40]:
        print("   ", b)
    sys.exit(1 if bad else 0)
