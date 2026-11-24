#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A5 — `L_EventCall` 의 특수 처리 함수 9개 + `MAKOTO_ENDING` ↔ 그래프의 트리거.

갈래 A: 원본 jam 을 직접 훑어
  · 각 특수 함수가 요구하는 (월, 일, timeID) — `m_nMonth != N` 꼴 줄에서
  · 각 특수 함수가 부르는 이벤트 번호 — `PUSH n` + `CALLFUNC L_EventCall::Call`
를 뽑고, 추출 결과에 같은 사슬이 있는지 항목별로 본다.
덤으로 `Check` 의 무조건/조건 호출 개수와 인수를 **다시 한 번** 독립으로 센다.

  python compare_a5.py [--selftest]
"""
import sys, os, re, io, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

SPECIALS = ["L_EventCall::D1101", "L_EventCall::E00451", "L_EventCall::E00602",
            "L_EventCall::E00658", "L_EventCall::E05024", "L_EventCall::E10501",
            "L_EventCall::E20164", "L_EventCall::E30152", "L_EventCall::MAKOTO_ENDING"]


def date_gate(body):
    """`.GLOBALREF L_EventCall::m_nMonth / PUSH N / NOTE` 꼴에서 (월, 일, timeID)."""
    out = {}
    for i, l in enumerate(body):
        t = l.strip()
        m = re.match(r"^\.GLOBALREF L_EventCall::m_n(Month|Day|TimeID)$", t)
        if m and i + 1 < len(body):
            m2 = re.match(r"^PUSH (\d+)$", body[i + 1].strip())
            if m2:
                out.setdefault(m.group(1), int(m2.group(1)))
    return out


def calls(body):
    """`PUSH n; CALLFUNC Call` 과 `.LOCALREF v; CALLFUNC Call`(v 에 대입된 상수들) 둘 다."""
    out = []
    assigns = {}
    for l in body:
        m = re.match(r"^\.LOCALASSIGN (\S+) (-?\d+)$", l.strip())
        if m:
            assigns.setdefault(m.group(1), set()).add(int(m.group(2)))
    for i, l in enumerate(body):
        if l.strip() != "CALLFUNC L_EventCall::Call" or i == 0:
            continue
        prev = body[i - 1].strip()
        m = re.match(r"^PUSH (\d+)$", prev)
        if m:
            out.append(int(m.group(1)))
            continue
        m = re.match(r"^\.LOCALREF (\S+)$", prev)
        if m:
            for v in sorted(assigns.get(m.group(1), ())):
                if v:
                    out.append(v)
    return out


def check_table(body):
    """`Check` 의 UnconditionalCall / ConditionalCall 인수 뽑기(상수만)."""
    un, co = [], []
    for i, l in enumerate(body):
        t = l.strip()
        if t == "CALLFUNC L_EventCall::UnconditionalCall":
            a = [body[j].strip() for j in range(i - 4, i)]
            if all(re.match(r"^PUSH -?\d+$", x) for x in a):
                un.append(tuple(int(x[5:]) for x in a))
        elif t == "CALLFUNC L_EventCall::ConditionalCall":
            a = [body[j].strip() for j in range(i - 9, i)]
            if all(re.match(r"^PUSH -?\d+$", x) for x in a):
                co.append(tuple(int(x[5:]) for x in a))
    return un, co


def run(inject=False):
    sch = C.load_graph("schedule.json")
    byid = {e["id"]: e for e in sch["events"]}
    bad = []
    # (a) 특수 함수
    for fn in SPECIALS:
        body = C.jam_body(fn)
        if not body:
            bad.append((fn, "jam 을 못 찾았다"))
            continue
        g = date_gate(body)
        cs = calls(body)
        if not cs:
            bad.append((fn, "이벤트를 하나도 안 부른다"))
        for n in cs:
            e = byid.get(n)
            if e is None:
                bad.append((fn, f"부르는 이벤트 {n} 의 함수가 없다"))
                continue
            srcs = {t.get("source") for t in e["triggers"]}
            if fn not in srcs and "L_EventCall::Check" not in srcs:
                bad.append((n, f"{fn} 이 부르는데 트리거 출처에 없다: {sorted(x for x in srcs if x)}"))
        if "Month" in g and "Day" in g:
            pass    # 날짜 게이트는 아래 표에 기록만
    # (b) Check 표 독립 재계수
    body = C.jam_body("L_EventCall::Check")
    un, co = check_table(body)
    if inject:
        un = un[:-1]
    gun, gco = [], []
    for e in sch["events"]:
        for t in e["triggers"]:
            if t.get("source") != "L_EventCall::Check":
                continue
            if t["kind"] == "scheduled":
                gun.append((t["date"][0], t["date"][1], t["time_id"], e["id"]))
            elif t["kind"] == "conditional":
                gco.append(tuple(t["raw_args"]))
    if sorted(un) != sorted(gun):
        only_a = [x for x in un if x not in gun]
        only_b = [x for x in gun if x not in un]
        bad.append(("Check/Uncond", f"A만 {only_a[:4]} / B만 {only_b[:4]} (A {len(un)} B {len(gun)})"))
    if sorted(co) != sorted(gco):
        only_a = [x for x in co if x not in gco]
        only_b = [x for x in gco if x not in co]
        bad.append(("Check/Cond", f"A만 {only_a[:4]} / B만 {only_b[:4]} (A {len(co)} B {len(gco)})"))
    return len(un), len(co), bad


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        nu, nc, bad = run(inject=True)
        ok = len(bad) > 0
        print("SELFTEST", "PASS" if ok else "FAIL", f"({len(bad)}건 걸림)")
        for b in bad[:3]:
            print("   ", b)
        nu, nc, bad = run()
        print("결함 없는 원본:", "문제 0건" if not bad else f"문제 {len(bad)}건 — 자체시험 무효")
        sys.exit(0 if ok and not bad else 1)
    nu, nc, bad = run()
    print(f"A5: 특수 함수 {len(SPECIALS)}개, Check 무조건 {nu}개·조건 {nc}개 대조, 문제 {len(bad)}건")
    for fn in SPECIALS:
        body = C.jam_body(fn)
        print(f"   {fn}: 게이트 {date_gate(body)} 부르는 이벤트 {calls(body)}")
    for b in bad[:40]:
        print("   ", b)
    sys.exit(1 if bad else 0)
