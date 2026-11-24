#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A4 — 인물별 친밀도 도우미 호출 ↔ 추출한 `person`.

갈래 A: 원본 jam 에서 `■親密度上昇/下降<인물><수>` 를 직접 긁고, 그 도우미가
정말 그 인물 번호로 `■親密度上昇(id, value)` 를 부르는지 도우미 본문에서 확인한다.
이름만 보고 단정하지 않는다(설계도 10-3).

  python compare_a4.py [--selftest]
"""
import sys, os, re, io, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

NAMES = {"いずみ": 2, "鏡花": 3, "真言美": 4, "マコト": 5,
         "新開": 6, "星川": 7, "百瀬": 8}
# 이벤트 번호 첫 자리 → 인물(관례). 이 관례 자체도 검사 대상이다.
FAMILY = {1: 2, 2: 3, 3: 4, 4: 5}


def helper_map():
    """도우미 이름 → (인물번호, 증감) — 도우미 **본문**에서 읽는다."""
    out = {}
    for name, body in C.jam_functions().items():
        if not re.match(r"^■親密度(上昇|下降).+$", name) or name in ("■親密度上昇", "■親密度下降"):
            continue
        pushes = [int(l.strip()[5:]) for l in body if re.match(r"^PUSH -?\d+$", l.strip())]
        callee = [l.strip()[9:] for l in body if l.strip().startswith("CALLFUNC ")]
        if len(pushes) >= 2 and callee:
            sign = -1 if callee[0] == "■親密度下降" else 1
            out[name] = (pushes[0], sign * pushes[1], callee[0])
    return out


def run(inject=None):
    hm = helper_map()
    bad = []
    # (a) 도우미 이름 속 인물 이름과 본문 인수가 맞나
    for name, (pid, delta, base) in hm.items():
        m = re.match(r"^■親密度(?:上昇|下降)(.+?)([０-９1-9])$", name)
        if not m:
            bad.append((name, "이름꼴을 못 읽음"))
            continue
        want = NAMES.get(m.group(1))
        if want is None:
            bad.append((name, f"인물 이름 {m.group(1)} 을 모른다"))
        elif want != pid:
            bad.append((name, f"이름은 {m.group(1)}({want}) 인데 본문 인수는 {pid}"))

    # (b) 이벤트마다: 타입에서 나온 person ↔ 도우미 인물
    sch = C.load_graph("schedule.json")
    checked = 0
    for e in sch["events"]:
        fn = e["fn"]
        body = C.jam_body(fn)
        calls = [l.strip()[9:] for l in body if l.strip().startswith("CALLFUNC ■親密度")]
        if inject and e["id"] == inject:
            calls = ["■親密度上昇星川１"]
        got = sorted({hm[c][0] for c in calls if c in hm})
        ext = sorted({a["person"] for a in e["effects"]["affection"]})
        if not inject and got != ext:
            bad.append((e["id"], f"jam 친밀도 인물 {got} != 추출 {ext}"))
        if inject and e["id"] == inject and got == ext:
            bad.append((e["id"], "결함을 심었는데 같다고 나온다"))
        if not got:
            continue
        checked += 1
        if e["person"] is not None and e["category"] in (
                "after_training_priority", "after_training", "training_invite"):
            if any(p != e["person"] for p in got):
                bad.append((e["id"], f"타입 인물 {e['person']} != 도우미 인물 {got}"))
        fam = FAMILY.get(e["id"] // 10000)
        if fam is not None and e["category"] == "after_training_priority":
            if any(p != fam for p in got):
                bad.append((e["id"], f"번호대 인물 {fam} != 도우미 인물 {got}"))
    return checked, bad


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        checked, bad = run(inject=10001)
        ok = len(bad) > 0
        print("SELFTEST", "PASS" if ok else "FAIL", f"({len(bad)}건 걸림)")
        for b in bad[:3]:
            print("   ", b)
        checked, bad = run()
        print("결함 없는 원본:", "문제 0건" if not bad else f"문제 {len(bad)}건 — 자체시험 무효")
        sys.exit(0 if ok and not bad else 1)
    checked, bad = run()
    hm = helper_map()
    print(f"A4: 친밀도 도우미 {len(hm)}개, 도우미를 부르는 이벤트 {checked}개 대조, 문제 {len(bad)}건")
    for b in bad[:40]:
        print("   ", b)
    sys.exit(1 if bad else 0)
