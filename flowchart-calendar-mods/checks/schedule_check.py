#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`graph/schedule.json` 구조 검사기 (설계도 4.4 — route_check.py 대체).

보는 것
  1. 스키마 이름·필수 필드
  2. 트리거 없는 이벤트 → `unresolved` 에 이유가 적혀 있나
  3. 없는 이벤트를 요구/등록/사슬로 가리키나
  4. 사슬 순환
  5. 풀 원소인데 함수가 없는 번호
  6. 선택지: 답마다 다음 이벤트가 풀렸나, 답 수와 사슬 수가 맞나
  7. `lines.jsonl` 의 m 이 그 이벤트의 MSG 범위 안인가
  8. 회상 재생본: 짝이 있고, 본문 비교 결과가 적혀 있나
  9. 날짜: 달력 안인가, timeID 가 1~4 인가

  python schedule_check.py
  python schedule_check.py --selftest     결함을 심어 검사기가 잡는지 증명
"""
import sys, os, io, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
GRAPH = os.path.join(BASE, "graph")

MAXDAY = {2: 28, 4: 30, 6: 30, 9: 30, 11: 30}


def load():
    with io.open(os.path.join(GRAPH, "schedule.json"), encoding="utf-8") as fp:
        sch = json.load(fp)
    with io.open(os.path.join(GRAPH, "pools.json"), encoding="utf-8") as fp:
        pools = json.load(fp)["pools"]
    lines = []
    with io.open(os.path.join(GRAPH, "lines.jsonl"), encoding="utf-8") as fp:
        for l in fp:
            if l.strip():
                lines.append(json.loads(l))
    return sch, pools, lines


def check(sch, pools, lines, inject=None):
    P = []          # 문제
    if sch.get("schema") != "yoru-event-schedule.v1":
        P.append(("schema", "스키마 이름이 다르다"))
    ev = {e["id"]: e for e in sch["events"]}
    unres = sch.get("unresolved", [])
    unres_ids = {u.get("event") for u in unres}

    if inject == "trigger":
        ev[10001]["triggers"] = []
    if inject == "chain":
        ev[10021]["chains_to"] = [999999]
    if inject == "cycle":
        ev[10022]["chains_to"] = list(ev[10022]["chains_to"]) + [10021]
        ev[10021]["chains_to"] = [10022]
    if inject == "date":
        for t in ev[121]["triggers"]:
            if t["kind"] == "scheduled":
                t["date"] = [4, 99]
    if inject == "line":
        lines = list(lines)
        for i, l in enumerate(lines):
            if l["event"] == 10001:
                lines[i] = dict(l, m=l["m"] + 500000)
                break

    for e in sch["events"]:
        for k in ("id", "fn", "category", "triggers", "effects", "messages",
                  "chains_to", "choices"):
            if k not in e:
                P.append((e.get("id"), f"필드 {k} 가 없다"))
        if not e["triggers"] and e["id"] not in unres_ids:
            P.append((e["id"], "트리거가 없는데 unresolved 에 이유가 없다"))
        for n in e["chains_to"]:
            if n not in ev:
                P.append((e["id"], f"사슬 대상 {n} 이 없다"))
        for t in e["triggers"]:
            for n in t.get("requires_events", []):
                if n not in ev:
                    P.append((e["id"], f"요구 이벤트 {n} 이 없다"))
            d = t.get("date")
            if d and d[0] is not None:
                if not (4 <= d[0] <= 11) or not (1 <= d[1] <= MAXDAY.get(d[0], 31)):
                    P.append((e["id"], f"날짜가 달력 밖: {d}"))
            ti = t.get("time_id")
            if ti is not None and ti not in (1, 2, 3, 4):
                P.append((e["id"], f"timeID 가 1~4 가 아니다: {ti}"))
        # 선택지
        if e["choices"]:
            for c in e["choices"]:
                if c.get("next") is None:
                    P.append((e["id"], f"선택지 {c['no']} 의 다음 이벤트를 못 풀었다"))
                elif c["next"] not in ev:
                    P.append((e["id"], f"선택지 {c['no']} 가 없는 이벤트 {c['next']} 로 간다"))
            if len(e["choices"]) != len(e["chains_to"]):
                P.append((e["id"],
                          f"답 {len(e['choices'])}개 != 사슬 {len(e['chains_to'])}개"))
        if e.get("replay_of") is not None:
            if e["replay_of"] not in ev:
                P.append((e["id"], f"재생 원본 {e['replay_of']} 이 없다"))
            if e.get("replay_text") is None:
                P.append((e["id"], "재생본 본문 비교 결과가 없다"))

    # 순환
    color = {}

    def dfs(n, path):
        color[n] = 1
        for m in ev.get(n, {}).get("chains_to", []):
            if color.get(m) == 1:
                P.append((n, f"사슬 순환: {' -> '.join(str(x) for x in path + [n, m])}"))
            elif color.get(m) is None:
                dfs(m, path + [n])
        color[n] = 2

    sys.setrecursionlimit(10000)
    for n in ev:
        if color.get(n) is None:
            dfs(n, [])

    # 풀
    for p in pools:
        for n in p["events"]:
            if n and n not in ev:
                P.append((p["name"], f"풀 원소 {n} 의 이벤트가 없다"))

    # lines.jsonl
    byev = collections.defaultdict(list)
    for l in lines:
        byev[l["event"]].append(l["m"])
    for no, ms in byev.items():
        e = ev.get(no)
        if e is None:
            P.append((no, "lines.jsonl 에 있는데 이벤트가 없다"))
            continue
        if len(ms) != e["messages"]["count"]:
            P.append((no, f"lines 수 {len(ms)} != messages.count {e['messages']['count']}"))
        lo, hi = e["messages"]["first_m"], e["messages"]["last_m"]
        if lo is not None:
            out = [m for m in ms if not (lo <= m <= hi)]
            if out:
                P.append((no, f"MSG 범위 밖 {out[:3]}"))
    return P


if __name__ == "__main__":
    sch, pools, lines = load()
    if "--selftest" in sys.argv:
        base = check(sch, pools, lines)
        print("원본 문제:", len(base))
        ok = not base
        for inj in ("trigger", "chain", "cycle", "date", "line"):
            sch, pools, lines = load()
            got = check(sch, pools, lines, inject=inj)
            new = [g for g in got if g not in base]
            print(f"  결함 [{inj}] → 새로 걸린 문제 {len(new)}건",
                  new[:2] if new else "  ← 못 잡았다")
            ok = ok and bool(new)
        print("SELFTEST", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    P = check(sch, pools, lines)
    print(f"구조 검사: 이벤트 {len(sch['events'])}개, 문제 {len(P)}건")
    for p in P[:50]:
        print("   ", p)
    sys.exit(1 if P else 0)
