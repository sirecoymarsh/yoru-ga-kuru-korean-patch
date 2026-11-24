#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A3 — EX `ランダムシナリオデータ` 풀 ↔ 추출 `pools.json` + 실제로 그 풀을 읽는 코드.

세 가지를 본다.
 1) 풀 원소마다 이벤트 함수가 있나 (항목별).
 2) 풀을 그 조건에서 뽑는 코드가 있나:
    - `特訓後<인물><월>月` / `特訓後<인물>惚れ` → `L_RandomScenario::PrepareAfterTraining`
      이 `ランダムシナリオデータ.データ.` + fmt(노드꼴, 인물이름) 으로 읽는다.
    - `ダンジョン内…` → `L_RandomScenario::CallWalkDungeon` 의 switch 라벨.
    - `特訓誘い…` / `ダンジョン初…` → **아무 코드도 안 읽는다**(잔재).
      대신 같은 번호가 `C_SceneTraining@PlaySelPartnerAction`(특훈 유혹)과
      `C_SceneDungeon@CheckEventOnEnter`(던전 첫 동행)에 박혀 있다 — 그걸 대조한다.
 3) 풀 종류·인물·월이 추출 결과와 같나.

  python compare_a3.py [--selftest]
"""
import sys, os, re, io, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

NAMES = {"いずみ": 2, "鏡花": 3, "真言美": 4, "マコト": 5,
         "新開": 6, "星川": 7, "百瀬": 8, "亮": 1}


def ex_pools():
    out = {}
    inside = False
    depth = 0
    with io.open(C.EXX, encoding="utf-8", errors="replace") as fp:
        for ln in fp:
            s = ln.rstrip("\n")
            if not inside:
                if re.match(r"^tree\s+ランダムシナリオデータ\s*=\s*\{", s):
                    inside = True
                    depth = 1
                continue
            depth += s.count("{") - s.count("}")
            if depth <= 0:
                break
            m = re.match(r"^\s*(\S+)\s*=\s*\(list\)\s*\{(.*)\}\s*,?\s*$", s)
            if m:
                out[m.group(1)] = [int(x) for x in re.findall(r"-?\d+", m.group(2))]
    return out


def jam_int_table(fn):
    """함수 본문의 `PUSH <정수>` 를 순서대로."""
    return [int(l.strip()[5:]) for l in C.jam_body(fn)
            if re.match(r"^PUSH -?\d+$", l.strip())]


def run(inject=None):
    ex = ex_pools()
    if inject:
        ex = dict(ex)
        ex[inject] = ex[inject][:-1]          # 원소 하나 빼기
    pools = {p["name"]: p for p in C.load_graph("pools.json")["pools"]}
    sch = C.load_graph("schedule.json")
    have = {e["id"] for e in sch["events"]}
    bad = []

    # (1)(3)
    for name, nums in ex.items():
        p = pools.get(name)
        if p is None:
            bad.append((name, "추출 결과에 이 풀이 없다"))
            continue
        if p["events"] != nums:
            bad.append((name, f"원소 목록이 다르다 {nums} != {p['events']}"))
        for n in nums:
            if n and n not in have:
                bad.append((name, f"원소 {n} 의 이벤트 함수가 없다"))
        m = re.match(r"^特訓後(.+?)(\d\d)月$", name)
        if m:
            if p["kind"] != "after_training" or p["person"] != NAMES.get(m.group(1)) \
                    or p["month"] != int(m.group(2)):
                bad.append((name, f"풀 종류/인물/월 틀림 {p['kind']}/{p['person']}/{p['month']}"))
        m = re.match(r"^ダンジョン内(.+?)／(.+)$", name)
        if m:
            if p["kind"] != "dungeon_walk" or p["person"] != NAMES.get(m.group(1)) \
                    or p["person2"] != NAMES.get(m.group(2)):
                bad.append((name, f"던전 짝 틀림 {p['person']}/{p['person2']}"))
    for name in pools:
        if name not in ex:
            bad.append((name, "EX 에 없는 풀이 추출 결과에 있다"))

    # (2) 특훈후 풀을 읽는 코드
    prep = "\n".join(C.jam_body("L_RandomScenario::PrepareAfterTraining"))
    for key in ("特訓後%s04月", "特訓後%s11月", "特訓後%s惚れ"):
        if ('S_PUSH "%s"' % key) not in prep:
            bad.append((key, "PrepareAfterTraining 이 이 노드꼴을 읽지 않는다"))
    for jp in ("いずみ", "鏡花", "真言美", "マコト", "新開", "星川", "百瀬"):
        if ('S_PUSH "%s"' % jp) not in prep:
            bad.append((jp, "PrepareAfterTraining 의 인물 목록에 없다"))

    # (2) 던전 걷기 풀을 읽는 코드
    walk = "\n".join(C.jam_body("L_RandomScenario::CallWalkDungeon"))
    for name in ex:
        if name.startswith("ダンジョン内"):
            if ('S_PUSH "%s"' % name) not in walk:
                bad.append((name, "CallWalkDungeon 이 이 풀 이름을 쓰지 않는다"))

    # (2) 특훈 유혹: EX 목록 vs 하드코딩 표
    t = jam_int_table("C_SceneTraining@PlaySelPartnerAction")
    base = None
    rank = None
    for i in range(len(t) - 6):
        if t[i:i + 7] == [1001, 1081, 1021, 1031, 1041, 1051, 1061]:
            base = t[i:i + 7]
        if t[i] == 1002 and t[i:i + 5] == [1002, 1003, 1004, 1005, 1006]:
            rank = t[i:i + 35]
    if base is None:
        bad.append(("特訓誘い", "PlaySelPartnerAction 의 기본 이벤트 표를 못 찾았다"))
    else:
        for jp, b in zip(("いずみ", "鏡花", "真言美", "マコト", "新開", "星川", "百瀬"),
                         [1001, 1081, 1021, 1031, 1041, 1051, 1061]):
            key = "特訓誘い" + jp
            if key in ex and ex[key][0] != b:
                bad.append((key, f"EX 첫 원소 {ex[key][0]} != 코드 표 {b}"))
    if rank is not None:
        for k, jp in enumerate(("いずみ", "鏡花", "真言美", "マコト", "新開", "星川", "百瀬")):
            key = "特訓誘い" + jp
            code = rank[k * 5:(k + 1) * 5]
            if key in ex and ex[key][1:6] != code:
                bad.append((key, f"EX 2~6번째 {ex[key][1:6]} != 코드 표 {code}"))

    # (2) 던전 첫 동행
    enter = "\n".join(C.jam_body("C_SceneDungeon@CheckEventOnEnter"))
    for jp, n in (("いずみ", 5001), ("鏡花", 5002), ("新開", 5003), ("星川", 5004)):
        key = "ダンジョン初" + jp
        if key in ex:
            if ex[key] != [n]:
                bad.append((key, f"EX {ex[key]} != 기대 [{n}]"))
            if ('S_PUSH "E%05d"' % n) not in enter:
                bad.append((key, f"CheckEventOnEnter 에 E{n:05d} 가 없다"))
    return ex, bad


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ex, bad = run(inject="特訓後いずみ04月")
        ok = len(bad) > 0
        print("SELFTEST", "PASS" if ok else "FAIL", f"({len(bad)}건 걸림)")
        for b in bad[:3]:
            print("   ", b)
        ex, bad = run()
        print("결함 없는 원본:", "문제 0건" if not bad else f"문제 {len(bad)}건 — 자체시험 무효")
        sys.exit(0 if ok and not bad else 1)
    ex, bad = run()
    print(f"A3: 풀 {len(ex)}개 / 원소 {sum(len(v) for v in ex.values())}개 대조, 문제 {len(bad)}건")
    for b in bad[:40]:
        print("   ", b)
    sys.exit(1 if bad else 0)
