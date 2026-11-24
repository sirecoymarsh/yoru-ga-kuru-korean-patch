#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""달력 시뮬레이션 — 정책별로 어떤 이벤트가 언제 처음 발화하나.

**이 시뮬레이션은 모형이다. 엔진의 사실이 아닌 부분을 아래에 밝힌다.**

확인된 것(원본 jam 근거):
  · 달력: 4/9 (주=1, 월요일) 시작, 11/17 (주=6) 끝. 한 달 길이는
    `C_GameDate@GetMaxDay`(2월28, 4·6·9·11월30, 나머지31). 223일.
  · 요일 분기: `呼出／１日の始まり` 의 switch(GetDayOfWeek) — 0 일요일,
    1 월요일, 2~5 화~금, 6 토요일.
  · 시간대(timeID) 호출 차례:
      월요일/화~금  : 1, 2
      토요일        : 1, (특훈 상대 선택 뒤 3), 4, 2
      일요일        : 1, 3, 4
      11/11         : 1, 2  (`呼出／１日の始まり` 안에서 직접)
  · 특별한 날: 5/15, 7/23, 10/21 은 요일 분기 대신 전용 경로.
  · 루트 확정: 10/15 timeID 1 에 `L_EventCall::Check` 안에서 한 번.
    인물 2~5 중 친밀도 60 이상·최고·선행조건 충족자 1명 `SetTurning`.
  · 친밀도: 화면값 = 내부값 ÷ 비율(2·3·8→420, 4→370, 5→290, 6→540, 7→500).
    내부값이 느는 자리 — 이벤트 안 `■親密度上昇X{1,2}`(값×300),
    특훈 상대 선택 뒤 `AddFeeling(250)`, 일요일 던전 뒤
    `AddFeelAtRemainTime`(2인 동행이면 3×남은시간, 3인이면 각 2×남은시간).

모형인 것(엔진에서 정해지지 않는다):
  · **일요일 던전에서 얼마가 남는가**는 플레이에 달렸다. 여기서는 정책
    손잡이 `remain`(0 / 150 / 300)로 둔다. 이 값이 결론을 좌우한다.
  · 전투·시간 소모·파티 편성은 흉내 내지 않는다.
  · 선택지는 「어느 답이든 고를 수 있다」로 보고, 갈래마다 따로 세지 않고
    사슬 전부를 도달 가능으로 표시한다(도달 여부만 따지는 표라서).

  python simulate.py            → reach.csv 와 요약
"""
import sys, os, io, json, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _common as C

RATE = {2: 420, 3: 420, 4: 370, 5: 290, 6: 540, 7: 500, 8: 420, 1: 420}
MAXDAY = {2: 28, 4: 30, 6: 30, 9: 30, 11: 30}
SPECIAL_DAYS = {(5, 15), (7, 23), (10, 21)}


def calendar():
    """[(month, day, week)] 4/9 ~ 11/17."""
    out = []
    m, d, w = 4, 9, 1
    while True:
        out.append((m, d, w))
        if (m, d) == (11, 17):
            break
        d += 1
        w = (w + 1) % 7
        if d > MAXDAY.get(m, 31):
            d = 1
            m += 1
    return out


def slots(m, d, w):
    if (m, d) == (11, 11):
        return [1, 2]
    if (m, d) in SPECIAL_DAYS:
        return []
    if w == 0:
        return [1, 3, 4]
    if w == 6:
        return [1, 3, 4, 2]
    return [1, 2]


class Sim:
    def __init__(self, sch, partner, remain):
        self.sch = sch
        self.partner = partner        # 2~8, 또는 0(아무도 안 고름)
        self.remain = remain
        self.ev = {e["id"]: e for e in sch["events"]}
        self.seen = {}
        self.feel = collections.defaultdict(int)     # 내부값
        self.turning = set()
        self.rules = self._rules()

    def _rules(self):
        out = []
        for e in self.sch["events"]:
            for t in e["triggers"]:
                if t.get("source") == "L_EventCall::Check" and t["kind"] in (
                        "scheduled", "conditional"):
                    out.append((e["id"], t))
        # Check 안의 차례를 지키려면 원래 순서가 필요하다 — 날짜로 정렬해 갈음한다
        out.sort(key=lambda x: (x[1].get("date") or x[1].get("date_from") or [0, 0]))
        return out

    def feeling(self, p):
        return self.feel[p] // RATE.get(p, 420)

    def guard_ok(self, guards):
        for g in guards:
            if "IsTurning" in g:
                pid = int(g.split("At(")[1].split(")")[0])
                want = not g.startswith("!(")
                if (pid in self.turning) != want:
                    return False
            elif "bLoadRestData" in g or "IsUseStartData" in g:
                pass          # 이어하기/스타트데이터 — 보통 플레이는 거짓
            elif "bKYOUKA0227" in g:
                pass          # 같은 날 조건 호출의 결과 — 아래에서 따로 처리
            elif "m_nMonth" in g:
                pass          # 날짜 가드는 아래 fire 에서 본다
        return True

    def fire(self, no, date):
        """이벤트와 그 사슬을 기록한다(선택지는 모든 답을 도달로 본다)."""
        stack = [no]
        seen_local = set()
        while stack:
            n = stack.pop()
            if n in seen_local or n not in self.ev:
                continue
            seen_local.add(n)
            if n not in self.seen:
                self.seen[n] = date
            for a in self.ev[n]["effects"]["affection"]:
                self.feel[a["person"]] += a["delta"] * 300
            stack.extend(self.ev[n]["chains_to"])

    def day(self, m, d, w):
        # 주간 친밀도
        if self.partner and w == 1:
            self.feel[self.partner] += 250
        if self.partner and w == 6:
            self.feel[self.partner] += 250
        if self.partner and w == 0:
            self.feel[self.partner] += 3 * self.remain
        for tid in slots(m, d, w):
            if (m, d, tid) == (10, 15, 1):
                self.lock_route()
            for no, t in self.rules:
                if t["time_id"] != tid:
                    continue
                if no in self.seen:
                    continue
                if not self.guard_ok(t["guards"]):
                    continue
                dg = [g for g in t["guards"] if "m_nMonth" in g]
                if dg:
                    okd = False
                    for g in dg:
                        gm = int(g.split("m_nMonth == ")[1].split(")")[0])
                        gd = int(g.split("m_nDay == ")[1].split(")")[0])
                        if g.startswith("!("):
                            okd = not (m == gm and d == gd)
                        else:
                            okd = (m == gm and d == gd)
                        if not okd:
                            break
                    if not okd:
                        continue
                if t["kind"] == "scheduled":
                    if [m, d] == t["date"]:
                        self.fire(no, (m, d))
                else:
                    a = t["raw_args"]
                    sm, sd, em, ed, _t, pid, feel, need, _e = a
                    if sm != -1 and (m, d) < (sm, sd):
                        continue
                    if em != -1 and (m, d) > (em, ed):
                        continue
                    if pid > 0 and feel >= 0 and self.feeling(pid) < feel:
                        continue
                    if need >= 0 and need not in self.seen:
                        continue
                    self.fire(no, (m, d))
            # 특수 처리 함수
            for e in self.sch["events"]:
                for t in e["triggers"]:
                    if t["kind"] != "scheduled_special" or not t.get("date"):
                        continue
                    if t["date"] == [m, d] and t.get("time_id") == tid:
                        if e["id"] not in self.seen:
                            self.fire(e["id"], (m, d))
        # 특훈 후 우선 이벤트(토요일)
        if w == 6 and self.partner:
            for e in self.sch["events"]:
                for t in e["triggers"]:
                    if t["kind"] != "after_training_priority":
                        continue
                    if t.get("person") != self.partner:
                        continue
                    if e["id"] in self.seen:
                        continue
                    if self.cond_ok(t.get("condition_expr", ""), m, d):
                        self.fire(e["id"], (m, d))
            # 풀에서 하나 — 도달 표에서는 풀 전체를 도달로 본다
            for p in self.sch_pools(m):
                for n in p:
                    if n and n not in self.seen:
                        self.seen[n] = (m, d)

    def sch_pools(self, m):
        out = []
        for p in POOLS:
            if p["kind"] == "after_training" and p["person"] == self.partner \
                    and p["month"] == m:
                out.append(p["events"])
            if p["kind"] == "training_invite" and p["person"] == self.partner:
                out.append(p["events"])
            if p["kind"] == "after_training_turned" and p["person"] == self.partner \
                    and self.partner in self.turning:
                out.append(p["events"])
        return out

    def cond_ok(self, expr, m, d):
        """GetAfterTrainingEvent 의 조건식을 흉내 낸다(유사코드 문자열)."""
        import re
        ok = True
        for mm in re.finditer(r"IsTodayOrAfter\((\d+), (\d+)\)", expr):
            if (m, d) < (int(mm.group(1)), int(mm.group(2))):
                ok = False
        for mm in re.finditer(r"IsTodayOrBefore\((\d+), (\d+)\)", expr):
            if (m, d) > (int(mm.group(1)), int(mm.group(2))):
                ok = False
        for mm in re.finditer(r"IsDay\((\d+), (\d+)\)", expr):
            if (m, d) != (int(mm.group(1)), int(mm.group(2))):
                ok = False
        for mm in re.finditer(r"GetFeeling\(\) >= (\d+)", expr):
            if self.feeling(self.partner) < int(mm.group(1)):
                ok = False
        for mm in re.finditer(r'(!\()?LEventFlag::GetOnce\("E(\d+)"\)', expr):
            neg = bool(mm.group(1))
            n = int(mm.group(2))
            if (n in self.seen) == neg:
                ok = False
        if "IsTurning()" in expr and self.partner not in self.turning:
            ok = False
        return ok

    def lock_route(self):
        best, bestf = -1, -1
        extra = {2: [], 3: [20061, 20081], 4: [30061], 5: [40101]}
        for p in (2, 3, 4, 5):
            f = self.feeling(p)
            if f < 60 or f <= bestf:
                continue
            if any(n not in self.seen for n in extra[p]):
                continue
            best, bestf = p, f
        if best != -1:
            self.turning = {best}

    def run(self):
        for m, d, w in calendar():
            self.day(m, d, w)
        return self.seen, self.turning


POOLS = None


ROOT_KINDS = {"scheduled", "conditional", "scheduled_special", "special_day",
              "dungeon", "pool", "after_training_priority", "invitation", "other"}


def static_reach(sch):
    """트리거 갈래를 닫아 「어떤 경로로든 뜰 수 있나」를 센다.

    달력 시뮬레이션은 본편 스케줄러와 특훈만 흉내 낸다(던전 안 걷기·회상 모드는
    플레이 입력이라 모형이 없다). 그래서 도달 여부는 이 정적 닫힘으로 따로 본다.
    """
    ev = {e["id"]: e for e in sch["events"]}
    reach = set()
    changed = True
    while changed:
        changed = False
        for e in sch["events"]:
            if e["id"] in reach:
                continue
            for t in e["triggers"]:
                k = t["kind"]
                ok = False
                if k in ROOT_KINDS:
                    ok = True
                elif k == "chained":
                    ok = t.get("from") in reach
                elif k == "memory_replay":
                    ok = all(n in reach or n not in ev for n in t.get("requires_events", []))
                if ok:
                    reach.add(e["id"])
                    changed = True
                    break
    return reach


def main():
    global POOLS
    sch = C.load_graph("schedule.json")
    POOLS = C.load_graph("pools.json")["pools"]
    allids = [e["id"] for e in sch["events"]]
    reach = static_reach(sch)
    policies = []
    for partner in (0, 2, 3, 4, 5, 6, 7, 8):
        for remain in (0, 150, 300):
            if partner == 0 and remain != 0:
                continue
            policies.append((partner, remain))
    res = {}
    routes = {}
    for partner, remain in policies:
        s = Sim(sch, partner, remain)
        seen, turning = s.run()
        res[(partner, remain)] = seen
        routes[(partner, remain)] = sorted(turning)
    out = os.path.join(os.path.dirname(HERE), "checks", "reach.csv")
    with io.open(out, "w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        head = ["event", "category", "person", "static_reachable",
                "trigger_kinds"] + ["p%d_r%d" % p for p in policies]
        w.writerow(head)
        byid = {e["id"]: e for e in sch["events"]}
        for i in allids:
            e = byid[i]
            kinds = "|".join(sorted({t["kind"] for t in e["triggers"]}))
            row = [i, e["category"], e["person"] if e["person"] is not None else "",
                   "Y" if i in reach else "N", kinds]
            for p in policies:
                d = res[p].get(i)
                row.append("%d/%d" % d if d else "")
            w.writerow(row)
    union = set()
    for p in policies:
        union |= set(res[p])
    print("정책 수:", len(policies))
    for p in policies:
        print("  상대 %s 남은시간 %3d → 발화 %4d개, 루트 %s"
              % (p[0] or "없음", p[1], len(res[p]), routes[p] or "없음"))
    print("달력 시뮬레이션으로 발화(합집합):", len(union), "/", len(allids))
    miss = [i for i in allids if i not in union]
    print("  시뮬레이션 미발화:", len(miss),
          dict(collections.Counter(byid[i]["category"] for i in miss)))
    unreach = [i for i in allids if i not in reach]
    print("정적 도달 닫힘으로 도달:", len(reach), "/", len(allids))
    print("  도달 불가:", len(unreach), unreach)
    print("  도달 불가 범주:", dict(collections.Counter(byid[i]["category"] for i in unreach)))
    with io.open(os.path.join(os.path.dirname(HERE), "checks", "reach_summary.json"),
                 "w", encoding="utf-8") as fp:
        json.dump({"policies": ["p%d_r%d" % p for p in policies],
                   "routes": {"p%d_r%d" % p: routes[p] for p in policies},
                   "sim_reached_union": len(union), "total": len(allids),
                   "sim_missing": miss,
                   "static_reachable": len(reach),
                   "static_unreachable": unreach},
                  fp, ensure_ascii=False, indent=1)
    return union, miss, reach, unreach


if __name__ == "__main__":
    main()
