#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1 — EX `シナリオテストデータ` 1,144행 ↔ 추출한 범주·인물·월범위·음성·선택지.

갈래 A(기준)는 `ex.x` 원문을 직접 정규식으로 읽고, 타입 번호의 뜻은
`C_TestScenario@Run*` 의 메뉴 문자열에서 **따로** 되뽑아 확인한다.
합계로 넘기지 않고 행마다 본다.

  python compare_a1.py            대조
  python compare_a1.py --selftest 일부러 틀린 값을 넣어 검사기가 잡는지 본다
"""
import sys, os, re, json, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def type_meaning_from_jam():
    """C_TestScenario@Run* 의 `Ａ＿選択肢登録(번호, "이름")` 에서 타입 뜻을 되뽑는다."""
    out = {}
    menus = {
        "C_TestScenario@RunTrainingPri": "after_training_priority",
        "C_TestScenario@RunTraining": "after_training",
        "C_TestScenario@RunTrainingInvite": "training_invite",
        "C_TestScenario@RunDungeon": "dungeon_walk",
        "C_TestScenario@RunMemory": "memory_replay",
    }
    for fn, cat in menus.items():
        body = C.jam_body(fn)
        for i, l in enumerate(body):
            m = re.match(r"^\s*PUSH (\d+)$", l)
            if not m:
                continue
            if i + 1 < len(body) and body[i + 1].strip().startswith('S_PUSH "'):
                lbl = body[i + 1].strip()[8:-1]
                if lbl in ("戻る", ""):
                    continue
                n = int(m.group(1))
                if n in (99, 99999):
                    continue
                out[n] = (cat, lbl)
    # 메인 진행은 RunMain 의 람다가 타입 1·2 를 고른다
    body = C.jam_body("C_TestScenario@RunMain")
    src = "\n".join(body)
    if re.search(r"PUSH 1\s*\n\s*EQUALE", src) and re.search(r"PUSH 2\s*\n\s*EQUALE", src):
        out[1] = ("main", "メイン進行")
        out[2] = ("main", "メイン進行")
    return out


def run(inject=None):
    rows = C.ex_rows("シナリオテストデータ")
    tmean = type_meaning_from_jam()
    sch = C.load_graph("schedule.json")
    byid = {}
    for e in sch["events"]:
        byid[e["fn"]] = e
    if inject:
        # 결함 심기: 한 행의 타입 번호를 바꾼다
        for r in rows:
            if r[0] == inject:
                r[1] = 2 if r[1] != 2 else 1
    bad = []
    seen = 0
    for r in rows:
        fn, tp, m0, m1, voice, choice = r[0], r[1], r[2], r[3], r[4], r[5]
        if fn.startswith("ＳＹＳＥＶ"):
            continue
        e = byid.get(fn)
        if e is None:
            bad.append((fn, "추출 결과에 이 이벤트가 없다"))
            continue
        seen += 1
        if e["test_type"] != tp:
            bad.append((fn, f"타입 {tp} != {e['test_type']}"))
        if e["month_range"] != [m0, m1]:
            bad.append((fn, f"월범위 {[m0, m1]} != {e['month_range']}"))
        if bool(voice) != bool(e["voice"]):
            bad.append((fn, f"음성 {bool(voice)} != {e['voice']}"))
        if bool(choice) != bool(e["has_choice"]):
            bad.append((fn, f"선택지 {bool(choice)} != {e['has_choice']}"))
        # 범주: 타입 뜻을 jam 메뉴에서 되뽑은 것과 맞나
        want = tmean.get(tp, (None, None))[0]
        if want and e["category"] != want:
            bad.append((fn, f"범주 {want} != {e['category']}"))
        # 인물: 메뉴 라벨이 인물 이름이면 그 번호와 맞나
        lbl = tmean.get(tp, (None, None))[1]
        if lbl:
            names = {"いずみ": 2, "鏡花": 3, "真言美": 4, "マコト": 5,
                     "新開": 6, "星川": 7, "百瀬": 8, "亮": 1}
            if lbl in names and e["person"] != names[lbl]:
                bad.append((fn, f"인물 {names[lbl]} != {e['person']}"))
        # 선택지 유무는 jam 의 분기 유무와도 맞아야 한다
        body = C.jam_body(fn)
        branchy = any(l.strip().startswith(("IFZ", "IFNZ")) for l in body)
        if branchy != bool(choice):
            bad.append((fn, f"jam 분기 {branchy} != 표 선택지 {bool(choice)}"))
    return seen, bad, tmean


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        seen, bad, _ = run(inject="ＥＶ／元／E00001")
        ok = len(bad) > 0
        print("SELFTEST", "PASS" if ok else "FAIL",
              f"(결함 하나를 심었더니 {len(bad)}건 걸림)")
        for b in bad[:3]:
            print("   ", b)
        seen, bad, _ = run()
        print("결함 없는 원본:", "문제 0건" if not bad else f"문제 {len(bad)}건 — 자체시험 무효")
        sys.exit(0 if ok and not bad else 1)
    seen, bad, tmean = run()
    print(f"A1: 표 {seen}행 대조, 문제 {len(bad)}건")
    print("타입 뜻(jam 메뉴에서 되뽑음):",
          json.dumps({str(k): v[1] for k, v in sorted(tmean.items())}, ensure_ascii=False))
    for b in bad[:40]:
        print("   ", b)
    sys.exit(1 if bad else 0)
