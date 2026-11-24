#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A6 — 도달 표: 모든 이벤트가 어떤 경로로든 뜰 수 있나, 못 뜨는 것은 이유가 있나.

두 가지를 나눠 본다.
  (가) 정적 도달 닫힘 — 트리거 갈래를 닫아 「뜰 수 있나」만.
  (나) 달력 시뮬레이션 — 「언제 뜨나」. 던전 안 걷기·회상 모드는 플레이 입력이라
       모형이 없으므로 여기서 안 뜨는 것은 결함이 아니다. 범주별로 갈라 적는다.

통과 조건: (가)에서 도달 못 하는 이벤트가 전부 `unresolved` 에 이유가 있다.

  python compare_a6.py [--selftest]
"""
import sys, os, io, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C
import simulate


def run(inject=False):
    sch = C.load_graph("schedule.json")
    simulate.POOLS = C.load_graph("pools.json")["pools"]
    if inject:
        # 결함 심기: 한 이벤트의 트리거를 지운다 → 도달 불가가 늘어야 한다
        for e in sch["events"]:
            if e["id"] == 10001:
                e["triggers"] = []
            for t in e["triggers"]:
                if t.get("from") == 10001:
                    t["from"] = -1
    reach = simulate.static_reach(sch)
    ev = {e["id"]: e for e in sch["events"]}
    unres = {u.get("event") for u in sch.get("unresolved", [])}
    bad = []
    unreach = [i for i in ev if i not in reach]
    for i in unreach:
        if i not in unres:
            bad.append((i, f"도달 불가인데 unresolved 에 이유가 없다 ({ev[i]['category']})"))
    return sch, reach, unreach, bad


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sch, reach, unreach, bad = run(inject=True)
        ok = len(bad) > 0
        print("SELFTEST", "PASS" if ok else "FAIL", f"({len(bad)}건 걸림)")
        for b in bad[:3]:
            print("   ", b)
        sch, reach, unreach, bad = run()
        print("결함 없는 원본:", "문제 0건" if not bad else f"문제 {len(bad)}건 — 자체시험 무효")
        sys.exit(0 if ok and not bad else 1)
    sch, reach, unreach, bad = run()
    ev = {e["id"]: e for e in sch["events"]}
    print(f"A6: 이벤트 {len(ev)}개 중 도달 {len(reach)}개, 도달 불가 {len(unreach)}개, 문제 {len(bad)}건")
    print("   도달 불가 범주:", dict(collections.Counter(ev[i]["category"] for i in unreach)))
    print("   도달 불가 목록:", sorted(unreach))
    kinds = collections.Counter()
    for e in sch["events"]:
        for t in e["triggers"]:
            kinds[t["kind"]] += 1
    print("   트리거 종류별 개수:", dict(kinds))
    for b in bad[:40]:
        print("   ", b)
    sys.exit(1 if bad else 0)
