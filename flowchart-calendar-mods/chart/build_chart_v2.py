#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""밤이 온다! 이벤트 차트 v2 — 월별 레인 (설계: chart/설계_v2_월별레인.md)

  python build_chart_v2.py                 chart/yoru_flowchart_v2.html 을 만든다
  python build_chart_v2.py --out 경로      다른 곳에 만든다(시험용)

손으로 HTML 을 고치지 않는다 — 언제나 이 스크립트가 만든다. 다시 돌려도 같은 결과가 나온다
(만든 시각 한 줄만 바뀐다).

재사용 — 1판 `build_chart.py` 를 모듈로 불러 그대로 쓴다
  자료 적재 load · 「언제」 라벨 when_texts · 조건식 풀이 plain_cond · 풀 이름 pool_kr ·
  던전 이름 dungeon_label · 가드 날짜 guard_date · 달 계산 month_of · 레인 lane_of · 범주 이름 CATKR
  「누구」「첫 줄」「의심」은 graph/labels.json(2차 산출)을, 묶음은 graph/groups.json(3차 산출)을 그대로 읽는다.
새로 계산하는 것
  · 일 단위 자리(날·기간 띠·달만) — 트리거 중 가장 이른 날짜, 1판 month_of 와 달이 같은지 검산
  · 카드 → 페이지(시작 달), 서랍 배정(장면마다 집 달 한 곳), 다른 달의 참조 칩
  · 사슬 분류 — 묶음·서랍 안(자식 줄 연결 표지) / 같은 쪽(원본 쪽 연결) / 다른 달(→ n월)
  · 09-23 교정 배지 — final_map_20260923.jsonl(읽기 전용)을 메시지 범위로 카드에 매단다
  · 대사 전문 — 원문(scratch/dump/messages.txt)·한국어(graph/lines_kr.jsonl)를 문자열 표로 중복 제거해 내장
"""
import sys, os, io, json, re, collections, datetime, argparse, hashlib
sys.dont_write_bytecode = True     # 1판·3차 모듈을 불러도 chart/·scratch/ 에 캐시를 남기지 않는다

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
GRAPH = os.path.join(BASE, "graph")
sys.path.insert(0, HERE)
import build_chart as V1          # 1판 — 적재·라벨·달 계산 재사용

FINAL = (r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\claude_qa_20260923"
         r"\pending_merge\final_map_20260923.jsonl")
MESSAGES = os.path.join(BASE, "scratch", "dump", "messages.txt")
OUT = os.path.join(HERE, "yoru_flowchart_v2.html")

MONTHS = [4, 5, 6, 7, 8, 9, 10, 11]
MLEN = {4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30}   # C_GameDate@GetMaxDay
CAL_START, CAL_END = (4, 9), (11, 17)                              # 呼出／オープニング · エンディング実行
WEEK0 = 1        # C_GameDate@0: 4/9 의 _week=1. 0=일요일 … 6=토요일(呼出／１日の始まり 분기)
SPECIAL_DATES = {"呼出／オープニング": (4, 9),        # SetDate(4, 9, 1)
                 "呼出／エンディング実行": (11, 17)}   # SetDate(11, 17, 6)
SIZE_CAP = 30 * 1024 * 1024

KIND_LABEL = collections.OrderedDict([
    ("prio", "우선 대화"), ("after", "특훈 뒤 대화"), ("turned", "반한 뒤"),
    ("invite", "초대"), ("walk", "던전 동행"), ("etc", "그 밖"),
    ("mem", "회상"), ("unused", "쓰이지 않음"), ("memref", "재생본")])
TYPE_LABEL = {"main": "본편", "person": "인물", "dungeon": "던전", "pool": "풀", "mem": "회상"}


def doy(m, d):
    return sum(MLEN[x] for x in range(4, m)) + d - 9


def weekday(m, d):
    return (WEEK0 + doy(m, d)) % 7


def jload(path):
    with io.open(path, encoding="utf-8") as fp:
        return json.load(fp)


# ── 일 단위 자리 ───────────────────────────────────────────────────────
def dated_candidates(e):
    """트리거에서 (시작, 끝 또는 None, 시간대) 후보. 날짜가 없는 트리거는 넣지 않는다."""
    out = []
    for t in e["triggers"]:
        k = t["kind"]
        if k == "scheduled":
            out.append((tuple(t["date"]), None, t.get("time_id")))
        elif k == "conditional":
            a = t["raw_args"]
            s = (a[0], a[1]) if a[0] != -1 else CAL_START
            f = (a[2], a[3]) if a[2] != -1 else CAL_END
            out.append((s, None if s == f else f, a[4]))
        elif k == "scheduled_special":
            d, ti = t.get("date"), t.get("time_id")
            if not (d and d[0]):
                d, ti = V1.guard_date(t.get("guards") or [])
            if d:
                out.append((tuple(d), None, ti))
        elif k == "special_day":
            d = t.get("date") or SPECIAL_DATES.get(t.get("source"))
            if d:
                out.append((tuple(d), None, None))
    return out


def place_main(e):
    """가장 이른 날짜 후보. 날짜가 없으면 1판 month_of 의 달만."""
    c = dated_candidates(e)
    if c:
        s, f, ti = min(c, key=lambda x: (x[0], x[1] or x[0]))
        r = {"m": s[0], "d": s[1]}
        if ti:
            r["slot"] = ti
        if f:
            r["m2"], r["d2"] = f
        return r
    md = V1.month_of(e)
    return {"m": md[0]} if md else None


CAL_RE = re.compile(r"(!\()?L_Calendar::(IsTodayOrAfter|IsTodayOrBefore|IsDay)\((\d+), (\d+)\)")


def atp_window(expr):
    """특훈 뒤 우선 이벤트 조건식의 날짜 창(띠). 부정(!)된 조각은 쓰지 않는다."""
    s = f = None
    for m in CAL_RE.finditer(expr or ""):
        if m.group(1):
            continue
        a = (int(m.group(3)), int(m.group(4)))
        if m.group(2) == "IsTodayOrAfter":
            s = a
        elif m.group(2) == "IsTodayOrBefore":
            f = a
        else:
            s = f = a
    if s is None and f is None:
        return None
    return (s or CAL_START, f or CAL_END)


def fix_cat(sources):
    """교정 출처 → 의미(claude·opus_*) / 호칭·문체·용어(pending:*) / 그 밖(괄호·수동·사용자 결정)."""
    if any(s == "claude" or s.startswith("opus_") for s in sources):
        return "mean"
    if any(s.startswith("pending:") for s in sources):
        return "term"
    return "other"


def pad(i):
    return "E%05d" % i


# ── r19: 친밀도 조건(규칙 11) ──────────────────────────────────────────
# schedule.json 트리거의 feeling_gate(scratch/extract.py 가 게임 코드에서 뽑는다). 값은 C_Ability@GetFeeling() 단위 —
# 게임이 조건을 비교하는 값이자 상태 창 친밀도 쪽(C_FeelingView: 하트 하나 = 60)이 그리는 값이다.
def feeling_text(g, persons, short=False):
    who = persons.get(str(g["person"]), str(g["person"]))
    op, v = g["op"], g.get("value")
    if op == ">":
        op, v = ">=", v + 1
    elif op == "<=":
        op, v = "<", v + 1
    if op == ">=":
        return ("%s %d+" % (who, v)) if short else ("%s 친밀도 %d 이상" % (who, v))
    if op == "<":
        return ("%s %d 미만" % (who, v)) if short else ("%s 친밀도 %d 미만" % (who, v))
    if op == "range":
        return ("%s %d～%d" % (who, g["lo"], g["hi"])) if short else ("%s 친밀도 %d～%d" % (who, g["lo"], g["hi"]))
    if op == "highest":
        return ("%s 최고" % who) if short else ("%s 친밀도 가장 높음" % who)
    raise SystemExit("모르는 친밀도 조건: %s" % g)


def feeling_gates(gates):
    """같은 인물의 이상·미만 둘이면 범위 하나로(v～w, 둘 다 포함)."""
    out, by = [], collections.OrderedDict()
    for g in gates:
        by.setdefault(g["person"], []).append(g)
    for p, gs in by.items():
        lo = [g["value"] + (1 if g["op"] == ">" else 0) for g in gs if g["op"] in (">=", ">")]
        hi = [g["value"] - (1 if g["op"] == "<" else 0) for g in gs if g["op"] in ("<", "<=")]
        if lo and hi and len(gs) == 2:
            out.append({"person": p, "op": "range", "lo": max(lo), "hi": min(hi)})
        else:
            out += gs
    return out


def feeling_tokens(t, persons, short=False):
    toks = ["루트 미정"] if t.get("no_route") else []
    return toks + [feeling_text(g, persons, short) for g in feeling_gates(t.get("feeling_gate") or [])]


def when_with_feeling(e, persons, dungeons):
    """1판 when_texts 에 친밀도 조건을 「<인물> 친밀도 v 이상」 꼴로 넣는다(PC 차트 · 게임 안 공통)."""
    base = V1.when_texts(e, persons, dungeons)
    for t in e["triggers"]:
        if not t.get("feeling_gate"):
            continue
        one = V1.when_texts(dict(e, triggers=[t]), persons, dungeons)
        if len(one) != 1 or one[0] not in base:
            raise SystemExit("친밀도 조건을 붙일 언제 줄을 못 찾았다: %s" % e["id"])
        one = one[0]
        texts = feeling_tokens(t, persons)
        if t["kind"] == "conditional":
            new = one                  # 1판이 raw_args 로 이미 「<인물> 친밀도 v 이상」을 쓴다
        elif t["kind"] == "after_training_priority":
            new = one
            for g in t["feeling_gate"]:
                new, n = re.subn(r"(^| · )친밀도 %d 이상" % g["value"],
                                 lambda z: z.group(1) + feeling_text(g, persons), new, count=1)
                if n != 1:
                    raise SystemExit("우선 대화 조건에 친밀도 조각이 없다: %s" % e["id"])
        else:
            new = one + " · " + " · ".join(texts)
        if not all(x in new for x in texts):
            raise SystemExit("친밀도 문구가 빠졌다: %s %s" % (e["id"], new))
        base = [new if w == one else w for w in base]
    return base


# ── r19: 사람이 읽는 이름(게임 안 달력의 E번호 대신 · PC 차트는 E번호 옆에) ─────────────────
# 규칙은 ingame/설계_v3_글메뉴판.md 「r19 요구」 1~10. 첫 줄 · 대사 · 선택지 문구는 쓰지 않는다(언제 · 누구 · 순번 · 자리만).
# 게임 안 빌드(ingame/r19_calendar)는 이 값을 그대로 굽는다 — 이름을 다시 계산하지 않는다.
NAME_SLOT = {1: "아침", 2: "밤", 3: "낮", 4: "저녁"}
NAME_KIND = {"prio": "우선 대화", "after": "특훈 뒤 대화", "turned": "반한 뒤 대화", "invite": "초대"}   # = 게임 안 서랍 이름
ENDING_PLACE = {"School": "학교", "CenterBuilding": "센터 빌딩", "NewTown": "뉴타운"}
NAME_LIMIT = 37              # 게임 안 제목 한 줄 38자 - 첫 색 표식 1자
PARTY = range(2, 9)          # 이즈미 · 쿄카 · 마나미 · 마코토 · 신카이 · 호시카와 · 모모세


def josa_wa(name):
    c = name[-1]
    if "가" <= c <= "힣" and (ord(c) - 0xAC00) % 28:
        return name + "과"
    return name + "와"


def dungeon_suffix(xx):
    """C_EventDungeonNNNN@RunEventXX 의 XX → 이름 조각. B1..Bn 사건 n · R1 보스 · Exit 출구 · Entrance 입구.
    번호 없는 R · B(nEventID 로 여러 장면을 부르는 분기 함수)는 내부 표식이라 쓰지 않는다: B 는 「사건」, R 는 없음."""
    m = re.match(r"^B(\d+)$", xx)
    if m:
        return "사건 %d" % int(m.group(1))
    if xx == "R1":
        return "보스"
    return {"Exit": "출구", "Entrance": "입구", "B": "사건", "R": ""}.get(xx, xx)


def dungeon_place(e, dungeons):
    """던전 사건의 (자리, 조각). 트리거 차례대로 RunEvent* 를 먼저(InspectAt* 는 같은 사건의 조사 자리)."""
    srcs = [t["source"] for t in e["triggers"] if t["kind"] == "dungeon"]
    srcs = [s for s in srcs if "@RunEvent" in s] + [s for s in srcs if "@RunEvent" not in s]
    for s in srcs:
        m = re.match(r"^L_DungeonManager::RunEventDungeonEnding(\w+)$", s)
        if m:
            return ENDING_PLACE[m.group(1)], "최종장"
        m = re.match(r"^C_EventDungeon\d{4}@(?:RunEvent|InspectAtEvent)(\w+)$", s)
        if m and s in dungeons:
            return (dungeons[s].get("kr") or dungeons[s]["jp"]), dungeon_suffix(m.group(1))
    return None


def event_names(E, cards, chips, ev, persons, lane_label, cardlab, dungeons):
    """게임 안 달력과 PC 차트가 같이 쓰는 이름. 적는 곳:
      cards[i]: nm 카드 쪽 제목 첫 줄(색 표식 없이) · tail 레인 줄 꼬리(규칙 3, 없으면 "") · ref 다른 장면에서 가리킬 때
      E[id]:    nm 장면 쪽 제목 첫 줄 · ns 목록 줄(단계 목록 「2. 이즈미와」, 서랍 장면 목록 「3번째」, 표식 없이)
                nr 다른 장면의 「언제」에서 가리킬 때 · nk 묶음 안 단계 이름(「2단계」, 카드 밖이면 없음)"""
    party = {persons[str(p)] for p in PARTY}

    def speakers(no):
        out = []
        for s in cardlab[str(no)].get("speakers") or []:
            out += [p.strip("\u3000 ") for p in s.split("＆")]
        return out

    def companion(no):
        """함께한 인물: 화자 차례로 주인공(료)을 뺀 첫 동료(이름 없는 화자 — 목소리 · 인영 · 여학생 — 는 건너뛴다)."""
        for p in speakers(no):
            if p in party:
                return p
        return None

    def alone(no):
        return speakers(no) == [persons["1"]]

    def fit(parts, drop):
        """parts: [(글자, 떨굴 순서 or None)]; 한도를 넘으면 순서대로 뺀다."""
        cur = list(parts)
        for d in drop:
            if len(" · ".join(t for t, _ in cur)) <= NAME_LIMIT:
                break
            cur = [(t, o) for t, o in cur if o != d]
        text = " · ".join(t for t, _ in cur if t)
        if len(text) > NAME_LIMIT:
            raise SystemExit("이름이 한 줄을 넘는다: %s" % text)
        return text

    # ── 카드: 머리(언제 · 유형 · 이름), 겹치는 카드의 꼬리(규칙 3)
    for c in cards:
        pl = c["pl"]
        when = ("%d/%d" % (pl["m"], pl["d"])) if "d" in pl else ("%d월 중" % pl["m"])
        if pl.get("slot"):
            when += " " + NAME_SLOT[pl["slot"]]
        lane = c["lane"]
        ctype = "본편" if lane == "main" else ("던전" if lane == "dungeon" else "인물 · " + lane_label[lane])
        dp = dungeon_place(ev[c["entry"]], dungeons) if lane == "dungeon" else None
        c["_when"], c["_type"], c["_dp"] = when, ctype, dp
        c["_head0"] = " · ".join([when, ctype] + ([dp[0]] + ([dp[1]] if dp[1] else []) if dp else [])
                                 + (["%d단계" % c["n"]] if c["n"] > 1 else []))
    groups = collections.defaultdict(list)
    for c in cards:
        groups[(c["page"], c["lane"], c["_head0"])].append(c)
    for key, cs in groups.items():
        # 규칙 3: 같은 달 · 레인에서 카드 머리가 겹치면 함께한 인물 + 순번(그 인물 안에서 이벤트 번호 순).
        # 동료가 없으면 주인공만 말할 때 「혼자 n」, 그 밖은 「장면 n」.
        seenk = collections.Counter()
        for c in sorted(cs, key=lambda x: x["entry"]):
            if len(cs) < 2:
                c["tail"] = ""
                continue
            who = companion(c["entry"])
            pre = josa_wa(who) if who else ("혼자" if alone(c["entry"]) else "장면")
            seenk[pre] += 1
            c["tail"] = "%s %d" % (pre, seenk[pre])
    for c in cards:
        when, ctype, dp = c["_when"], c["_type"], c["_dp"]
        parts = [when, ctype] + ([dp[0]] + ([dp[1]] if dp[1] else []) if dp else []) + ([c["tail"]] if c["tail"] else [])
        c["nm"] = " · ".join(parts + (["%d단계" % c["n"]] if c["n"] > 1 else []))
        if len(c["nm"]) > NAME_LIMIT:
            raise SystemExit("카드 이름이 한 줄을 넘는다: %s" % c["nm"])
        lane = c["lane"]
        short_lane = "본편" if lane == "main" else ("" if lane == "dungeon" else lane_label[lane])
        ref = [when, short_lane] if not dp else [dp[0]] + ([dp[1]] if dp[1] else [])
        c["ref"] = " ".join(x for x in ref if x) + (" (%s)" % c["tail"] if c["tail"] else "")     # 「10/11 아침 마나미 (마나미와 2)」
    heads = collections.Counter((c["page"], c["lane"], c["nm"]) for c in cards)
    if max(heads.values()) > 1:
        raise SystemExit("같은 달 · 레인에 같은 카드 이름: %s" % [k for k, n in heads.items() if n > 1])

    # ── 카드 안 단계(규칙 2)
    for c in cards:
        stages = [r for r in c["rows"] if r[6]]
        slot0 = c["pl"].get("slot")
        for k, r in enumerate(stages, start=1):
            no = r[0]
            e = ev[no]
            via = r[3] if r[2] == "answer" else None
            who = companion(no)
            sd = None
            if c["_dp"]:
                own = dungeon_place(e, dungeons)
                if own and own[1]:
                    sd = own[1]
            slots = {t.get("time_id") for t in e["triggers"] if t["kind"] in ("scheduled", "conditional") and t.get("time_id")}
            slot = NAME_SLOT[min(slots)] if (k > 1 and len(slots) == 1 and min(slots) != slot0) else None
            first = "%d단계" % k + (" 갈래 %d" % via if via else "")
            stage = [(first, None)] + ([(sd, 3)] if sd else []) + ([(josa_wa(who), 2)] if who else []) + ([(slot, 1)] if slot else [])
            if c["n"] > 1:
                E[no]["nk"] = " · ".join(t for t, _ in stage)
                short = ("갈래 %d" % via if via else "")
                if who:
                    short = (short + " " if short else "") + josa_wa(who)
                if not short:
                    short = sd or ("혼자" if alone(no) else ("이어서" if r[1] > 0 else "시작"))
                E[no]["ns"] = ("%d. " % k + short).strip()
                base = [(c["_when"], None), (c["_type"], 5)] + ([(c["_dp"][0], None)] if c["_dp"] else []) \
                    + ([(c["tail"], None)] if c["tail"] else [])
                E[no]["nm"] = fit(base + stage, [1, 5, 2, 3])     # 시간대 → 유형(던전은 자리가 말한다) → 인물 → 던전 조각
                E[no]["nr"] = c["ref"] + " " + first
            else:
                E[no]["ns"] = "1. " + (josa_wa(who) if who else (sd or ("혼자" if alone(no) else "시작")))
                E[no]["nm"] = c["nm"]
                E[no]["nr"] = c["ref"]

    # ── 서랍 장면(규칙 5~8)
    for ch in chips:
        kind, lane = ch["kind"], ch["lane"]
        ents = sorted(ch["entries"])
        month = None if ch["page"] == "mem" else "%s월" % ch["page"]
        if kind in NAME_KIND:
            for k, no in enumerate(ents, start=1):
                nm = "%s %d번째" % (NAME_KIND[kind], k)
                E[no].update(ns="%d번째" % k, nm=" · ".join([month, lane_label[lane], nm]), nr=" ".join([month, lane_label[lane], nm]))
        elif kind == "walk":
            seen = collections.Counter()
            for no in ents:
                e = ev[no]
                me = int(lane[1:]) if lane.startswith("p") else None
                other = [x for x in (e["person"], e["person2"]) if x and x != me and x != 1]
                if other:
                    who = josa_wa(persons[str(other[0])])
                elif lane.startswith("p"):
                    who = "단둘이"
                else:
                    who = "혼자"
                seen[who] += 1
                nm = "%s 동행 %d번째" % (who, seen[who])
                E[no].update(ns="%s %d번째" % (who, seen[who]), nm=" · ".join([month, lane_label[lane], nm]),
                             nr=" ".join([month, lane_label[lane], nm]))
        elif kind == "etc":
            for no in ents:
                if not any(t.get("source") == "残時間終わり処理／日曜" for t in ev[no]["triggers"]):
                    raise SystemExit("그 밖 서랍의 모르는 장면: %d" % no)
                E[no].update(ns="일요일 시간 끝 처리", nm=" · ".join([month, lane_label[lane], "일요일 시간 끝 처리"]),
                             nr="일요일 시간 끝 처리")
        elif kind == "unused":
            for k, no in enumerate(ents, start=1):
                E[no].update(ns="미사용 %d" % k, nm="회상 · 그 밖 · 미사용 %d" % k, nr="미사용 %d" % k)
        elif kind == "mem":
            pg = int(lane[3:])
            parent = {x[0]: (x[2], x[3]) for x in ch["order"] if x[4]}

            def root(no):
                seen_ = set()
                while str(no) not in ch["slots"]:
                    if no in seen_ or parent.get(no, (None,))[0] is None:
                        raise SystemExit("회상 재생본의 칸을 못 찾았다: %d" % no)
                    seen_.add(no)
                    no = parent[no][0]
                return no
            for no in ents:
                if str(no) in ch["slots"]:
                    base = "회상 %d쪽 %d번" % (pg, ch["slots"][str(no)])
                    src = ev[no].get("replay_of")
                    date = ""
                    if src and E[src].get("unit", "").startswith("c:"):
                        cc = next(x for x in cards if x["key"] == E[src]["unit"][2:])
                        if "d" in cc["pl"]:
                            date = " (%d/%d)" % (cc["pl"]["m"], cc["pl"]["d"])
                    nm = base + date
                else:
                    r0 = root(no)
                    via = parent[no][1]
                    base = "회상 %d쪽 %d번" % (pg, ch["slots"][str(r0)]) + (" 갈래 %d" % via if via else " 이어서")
                    nm = base
                E[no].update(ns=nm[len("회상 %d쪽 " % pg):], nm="회상 · 그 밖 · " + nm, nr=base)
        else:
            raise SystemExit("이름 규칙이 없는 서랍: %s" % ch["id"])

    # ── 검산: 모든 장면에 이름, 전체 · 쪽 안 유일
    miss = [i for i, x in E.items() if not (x.get("nm") and x.get("ns") and x.get("nr"))]
    if miss:
        raise SystemExit("이름이 없는 장면: %s" % miss[:5])
    # 같은 쪽(단계 목록 · 서랍 장면 목록) 안에서는 목록 줄도 장면 쪽 제목도 유일해야 한다. 다른 카드끼리는 카드 이름이
    # 다르므로(위 검산) 같은 장면 이름이 있어도 된다(예: 5월 백화점 서관 2층 21단계 · 4단계 카드의 1단계).
    for c in cards:
        st = [r[0] for r in c["rows"] if r[6]]
        for f in ("ns", "nm"):
            ss = [E[n][f] for n in st]
            if len(ss) != len(set(ss)):
                raise SystemExit("단계 목록이 겹친다(%s): %s" % (f, c["key"]))
    for ch in chips:
        for f in ("ns", "nm"):
            ss = [E[n][f] for n in ch["entries"]]
            if len(ss) != len(set(ss)):
                raise SystemExit("서랍 장면 목록이 겹친다(%s): %s" % (f, ch["id"]))
    for c in cards:
        for k in ("_when", "_type", "_dp", "_head0"):
            del c[k]
    return E, cards


def build(out_path):
    sch = V1.load("schedule.json")
    grp = V1.load("groups.json")
    lab = V1.load("labels.json")
    pools = V1.load("pools.json")["pools"]
    memt = V1.load("memory.json")
    persons = {str(p["no"]): (p["kr"] or p["jp"]) for p in sch["persons"]}   # 1판과 같은 표기
    jp2no = {p["jp"]: p["no"] for p in sch["persons"]}
    dungeons = lab["dungeons"]
    cardlab = lab["cards"]
    evs = sch["events"]
    ev = {e["id"]: e for e in evs}

    lines_kr = {}
    with io.open(os.path.join(GRAPH, "lines_kr.jsonl"), encoding="utf-8") as fp:
        for ln in fp:
            r = json.loads(ln)
            lines_kr[r["event"]] = r["seq"]
    if not os.path.exists(MESSAGES):
        raise SystemExit("원문 덤프가 없다: %s\n  PYTHONUTF8=1 python scratch/rebuild_all.py --dump-only"
                         % MESSAGES)
    with io.open(MESSAGES, encoding="utf-8") as fp:
        jp_lines = fp.read().split("\n")
    fm = [json.loads(l) for l in io.open(FINAL, encoding="utf-8") if l.strip()]

    lane_keys = ["main", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "dungeon"]
    lane_label = {"main": "본편", "dungeon": "던전"}
    for k in lane_keys:
        if k.startswith("p"):
            lane_label[k] = persons[k[1:]]

    # 합류 날짜 — EX 日付テスト実行データ 표식 「＞＞이름IN」. 표식이 없으면 첫날부터.
    join = {k: CAL_START for k in lane_keys}
    for mk in sch["calendar"]["marks"]:
        mm = re.match(r"^＞＞(.+)IN$", mk["text_jp"])
        if mm and mm.group(1) in jp2no:
            join["p%d" % jp2no[mm.group(1)]] = tuple(mk["date"])

    def lane_join_month(lane):
        return join.get(lane, CAL_START)[0]

    # ── 원문 정렬 검산: lines_kr 의 raw·화자 태그와 messages.txt 가 같은 m 에서 맞아야 한다
    align_bad = []
    for i, seq in lines_kr.items():
        for s in seq:
            j = jp_lines[s["m"]] if s["m"] < len(jp_lines) else None
            if s["sp"] is not None:
                if not (j and j.startswith("【")):
                    align_bad.append((i, s["m"], "화자 줄인데 원문이 【】 가 아님"))
            elif s.get("raw") is not None and s["raw"] != j:
                align_bad.append((i, s["m"], "raw 가 원문과 다름"))
    if align_bad:
        raise SystemExit("원문 줄 번호가 어긋났다: %d건 %s" % (len(align_bad), align_bad[:3]))

    # ── 09-23 교정 지도 → m → (이벤트, 분류)
    m2e = {}
    for e in evs:
        ms = e["messages"]
        if ms["count"]:
            for m in range(ms["first_m"], ms["last_m"] + 1):
                m2e[m] = e["id"]
    fix = collections.defaultdict(lambda: [0, 0, 0, 0])      # 합 · 의미 · 호칭문체용어 · 그 밖
    fix_rows = {}
    fix_outside = []
    for r in fm:
        i = m2e.get(r["m_id"])
        if i is None:
            fix_outside.append(r["m_id"])
            continue
        c = fix_cat(r["sources"])
        f = fix[i]
        f[0] += 1
        f[{"mean": 1, "term": 2, "other": 3}[c]] += 1
        fix_rows[r["m_id"]] = (r["proposed"], c, r.get("note") or "", "+".join(r["sources"]))

    # ── 사슬(chains_to ∪ choices.next)
    edges = collections.OrderedDict()
    for e in evs:
        for d in e["chains_to"]:
            edges[(e["id"], d)] = None
        for c in e["choices"]:
            if c.get("next"):
                edges[(e["id"], c["next"])] = c["no"]
    for (s, d) in edges:
        if d not in ev:
            raise SystemExit("사슬 대상이 없다: %s → %s" % (s, d))
    parents_of = collections.defaultdict(list)
    kids_of = collections.defaultdict(list)
    for (s, d), via in edges.items():
        parents_of[d].append(s)
        kids_of[s].append((d, via))

    # 선택지 답 문구 — 본편 답은 groups.json 행의 설치된 한국어, 그 밖은 같은 일본어 문구로 찾는다
    ans_kr = {}
    for g in grp["groups"]:
        for r in g["rows"]:
            v = r["via"]
            if v.get("kind") == "answer" and v.get("text_kr"):
                ans_kr[(None, r["event"], v["no"])] = v["text_kr"]
    jp2kr_ans = {}
    for e in evs:
        for c in e["choices"]:
            k = (None, c.get("next"), c["no"])
            if k in ans_kr and c.get("text_jp"):
                jp2kr_ans[c["text_jp"]] = ans_kr[k]

    sys.path.insert(0, os.path.join(BASE, "scratch"))
    import build_groups as BG      # 3차 — 실행본 문자열 표에서 답 문구 한국어(색인이 하나일 때만)
    bg_tables = BG.korean_strings()

    def answer_text(e, c):
        k = (None, c.get("next"), c["no"])
        if k in ans_kr:
            return ans_kr[k], "kr"
        t = c.get("text_jp") or ""
        if t in jp2kr_ans:
            return jp2kr_ans[t], "kr"
        a, why = BG.answer_kr(t, *bg_tables)
        if a:
            return a, "kr"
        return t, "jp"

    # ── 이벤트 기록(라벨·조건·배지)
    E = {}
    label_src = collections.Counter()
    for e in evs:
        L = cardlab[str(e["id"])]
        when = when_with_feeling(e, persons, dungeons)          # r19 규칙 11: 친밀도 조건
        wsrc = "trig"
        if not when:
            when, wsrc = ["부르는 자리 없음"], "none"
        who = list(L.get("speakers") or [])
        wmore = L.get("speakers_more", 0)
        psrc = "tag"
        if not who:
            ps = [persons[str(x)] for x in (e["person"], e["person2"]) if x and str(x) in persons]
            if ps:
                who, psrc = ps, "person"
            else:
                who, psrc = ["화자 표시 없음"], "none"
        first, fcut, fsrc = L.get("first_kr"), bool(L.get("first_truncated")), "line"
        if not first:
            if e["messages"]["count"] == 0:
                first, fsrc = "(대사 없음)", "none"
            else:
                first, fsrc = "(한국어 줄 없음)", "empty"
        label_src[("when", wsrc)] += 1
        label_src[("who", psrc)] += 1
        label_src[("first", fsrc)] += 1
        rec = {
            "id": e["id"], "fn": e["fn"], "cat": e["category"],
            "p": e["person"], "p2": e["person2"],
            "lines": e["messages"]["count"], "m0": e["messages"]["first_m"] if e["messages"]["count"] else None,
            "voice": bool(e["voice"]), "choice": bool(e["has_choice"]),
            "battle": bool(e["effects"]["event_battle"]),
            "when": when, "wsrc": wsrc, "who": who, "wmore": wmore, "psrc": psrc,
            "first": first, "fcut": fcut, "fsrc": fsrc,
            "fix": list(fix[e["id"]]) if e["id"] in fix else [0, 0, 0, 0],
            "sus": [L.get("misalign", 0), L.get("register", 0)],
            "ans": [],
            "aff": [[a["person"], a["delta"]] for a in e["effects"]["affection"]],
        }
        for c in e["choices"]:
            t, src = answer_text(e, c)
            rec["ans"].append([c["no"], c.get("next"), t, src])
        if e.get("replay_of"):
            rec["replay_of"] = e["replay_of"]
            rec["replay"] = e.get("replay_text")
        E[e["id"]] = rec

    # ── 본편 카드(묶음 155장)
    in_card = {}
    cards = []
    month_check_bad = []
    for g in grp["groups"]:
        entry = ev[g["entries"][0]] if g["entries"] else ev[g["members"][0]]
        pl = place_main(entry)
        mo = V1.month_of(entry)
        if not pl or not mo or pl["m"] != mo[0]:
            month_check_bad.append((g["key"], pl, mo))
        isd = bool(g["dungeon_classes"]) or any(t["kind"] == "dungeon" for t in entry["triggers"])
        base_lane = V1.lane_of(entry)
        lane = "dungeon" if isd else (base_lane if base_lane in lane_keys else "main")
        ctype = "dungeon" if lane == "dungeon" else ("person" if lane.startswith("p") else "main")
        ptag = persons.get(base_lane[1:]) if (isd and base_lane.startswith("p")) else None
        rows = []
        stack = []                     # depth → 부모 id
        for r in g["rows"]:
            dep = r["depth"]
            stack = stack[:dep]
            parent = stack[dep - 1] if dep > 0 else None
            v = r["via"]
            rows.append([r["event"], dep, v.get("kind"), v.get("no"),
                         v.get("text_kr") if v.get("kind") == "answer" else None,
                         bool(r["shared"]), bool(r["counts_here"]), parent])
            stack.append(r["event"])
        # 행의 (부모 → 자식) = 묶음 안 사슬과 같아야 한다
        row_edges = {(x[7], x[0]) for x in rows if x[7] is not None}
        mem = set(g["members"])
        want = {(s, d) for (s, d) in edges if s in mem and d in mem}
        if row_edges != want or len([x for x in rows if x[7] is not None]) != len(want):
            raise SystemExit("묶음 %s 의 행과 사슬이 다르다" % g["key"])
        fx = [sum(E[n]["fix"][k] for n in g["members"]) for k in range(4)]
        card = {"key": g["key"], "entry": entry["id"], "members": g["members"], "n": len(g["members"]),
                "rows": rows, "lane": lane, "type": ctype, "ptag": ptag,
                "page": str(pl["m"]), "pl": pl, "fix": fx,
                "sus": [g["mis"], g["reg"]], "lines": g["lines"], "branches": g["branches"],
                "entry_more": max(0, len(g["entries"]) - 1)}
        cards.append(card)
        for n in g["members"]:
            if n in in_card:
                raise SystemExit("사건 %d 가 묶음 두 곳에 있다" % n)
            in_card[n] = g["key"]
            E[n]["unit"] = "c:" + g["key"]
            E[n]["home"] = card["page"]
    if month_check_bad:
        raise SystemExit("1판 month_of 와 달이 다른 카드: %s" % month_check_bad[:5])

    # ── 서랍(카드 밖 760장) — 장면마다 집 한 곳
    pool_of = collections.defaultdict(list)
    for p in pools:
        for n in p["events"]:
            if n:
                pool_of[n].append(p)

    def month_of_m(e):
        mo = V1.month_of(e)
        return mo[0] if mo else None

    drawer = {}          # id → (page, lane, kind, why)
    adjust = collections.Counter()
    mem_slot = {}        # 회상 재생 id → (쪽, 칸)
    for x in memt["entries"]:
        mem_slot[x["play"]] = (x["page"], x["id"], x["need"])
    for e in evs:
        i = e["id"]
        if i in in_card:
            continue
        cat = e["category"]
        kinds = {t["kind"] for t in e["triggers"]}
        pl_ = pool_of.get(i, [])
        if cat == "memory_replay" or cat == "unknown":
            continue               # 회상 · 그 밖 페이지에서 따로 배정
        if cat == "after_training":
            lane = "p%d" % e["person"]
            months = sorted({p["month"] for p in pl_ if p["kind"] == "after_training"})
            if not months:
                raise SystemExit("특훈 뒤 장면인데 달 풀이 없다: %d" % i)
            jm = lane_join_month(lane)
            ok = [m for m in months if m >= jm]
            home = ok[0] if ok else months[0]
            if home != months[0]:
                adjust["after: 합류 전 풀 달 건너뜀"] += 1
            if home != month_of_m(e):
                adjust["after: 1판 달과 다름"] += 1
            drawer[i] = (str(home), lane, "after")
        elif cat == "training_invite":
            lane = "p%d" % e["person"]
            home = max(month_of_m(e), lane_join_month(lane))
            if home != month_of_m(e):
                adjust["invite: 합류 달로 옮김"] += 1
            drawer[i] = (str(home), lane, "invite")
        elif cat == "dungeon_walk":
            ps = [x for x in (e["person"], e["person2"]) if x]
            lanes = ["p%d" % x for x in ps if "p%d" % x in lane_keys]
            lane = lanes[0] if lanes else "dungeon"
            home = max([month_of_m(e)] + [lane_join_month(l) for l in lanes])
            if home != month_of_m(e):
                adjust["walk: 합류 달로 옮김"] += 1
            drawer[i] = (str(home), lane, "walk")
        elif cat == "after_training_priority":
            lane = "p%d" % e["person"]
            if any(t["kind"] == "pool" and t.get("pool_kind") == "after_training_turned"
                   for t in e["triggers"]):
                kind = "turned"
            elif "invitation" in kinds:
                kind = "invite"
            else:
                kind = "prio"
            home = month_of_m(e)
            if kind == "invite":
                h2 = max(home, lane_join_month(lane))
                if h2 != home:
                    adjust["invite: 합류 달로 옮김"] += 1
                home = h2
            drawer[i] = (str(home), lane, kind)
        elif cat == "system":
            drawer[i] = (str(month_of_m(e)), "dungeon", "etc")
        else:
            raise SystemExit("배정 규칙이 없는 범주: %s %s" % (i, cat))

    # 회상 · 그 밖: 쪽마다 한 칩, 사슬로만 오는 재생본은 부모의 쪽
    mem_page_of = {}
    for i, (pg, slot, need) in mem_slot.items():
        if ev[i]["category"] == "memory_replay":
            mem_page_of[i] = pg
    changed = True
    while changed:
        changed = False
        for e in evs:
            i = e["id"]
            if e["category"] == "memory_replay" and i not in mem_page_of:
                ps = [s for s in parents_of[i] if s in mem_page_of]
                if ps:
                    mem_page_of[i] = min(mem_page_of[s] for s in ps)
                    changed = True
    for e in evs:
        i = e["id"]
        if e["category"] == "memory_replay":
            if i not in mem_page_of:
                raise SystemExit("회상 재생본의 쪽을 못 정했다: %d" % i)
            drawer[i] = ("mem", "mem%d" % mem_page_of[i], "mem")
        elif e["category"] == "unknown":
            drawer[i] = ("mem", "unused", "unused")

    if set(in_card) & set(drawer) or len(in_card) + len(drawer) != len(evs):
        raise SystemExit("카드 %d + 서랍 %d != 사건 %d (겹침 %d)" % (
            len(in_card), len(drawer), len(evs), len(set(in_card) & set(drawer))))

    # ── 서랍 칩
    chips = collections.OrderedDict()
    for i in sorted(drawer):
        page, lane, kind = drawer[i]
        cid = "%s:%s:%s" % (page, lane, kind)
        if cid not in chips:
            chips[cid] = {"id": cid, "page": page, "lane": lane, "kind": kind,
                          "label": KIND_LABEL[kind], "entries": [], "refs": []}
        chips[cid]["entries"].append(i)
        E[i]["unit"] = "d:" + cid
        E[i]["home"] = page
    lane_rank = {k: n for n, k in enumerate(lane_keys + ["mem%d" % x for x in range(1, 8)] + ["unused"])}
    kind_rank = {k: n for n, k in enumerate(KIND_LABEL)}
    chips = collections.OrderedDict(sorted(
        chips.items(), key=lambda kv: ((int(kv[1]["page"]) if kv[1]["page"].isdigit() else 99),
                                       lane_rank[kv[1]["lane"]], kind_rank[kv[1]["kind"]])))
    # 칩 안 줄 차례 — 칩 안 사슬은 자식 줄로(공유면 한 번 더, 흐리게)
    for ch in chips.values():
        ent = set(ch["entries"])
        if ch["kind"] == "mem":
            slot_pos = {i: mem_slot[i][1] for i in ch["entries"] if i in mem_slot}
            roots = sorted([i for i in ch["entries"] if not any(p in ent for p in parents_of[i])],
                           key=lambda i: (slot_pos.get(i, 99), i))
        else:
            roots = sorted([i for i in ch["entries"] if not any(p in ent for p in parents_of[i])])
        order, drawn = [], set()

        def walk(n, depth, parent, via, stack):
            first = n not in drawn
            order.append([n, depth, parent, via, first])
            drawn.add(n)
            if not first or n in stack:
                return
            for d, v in kids_of.get(n, []):
                if d in ent:
                    walk(d, depth + 1, n, v, stack | {n})

        for r in roots:
            walk(r, 0, None, None, frozenset())
        for n in ch["entries"]:
            if n not in drawn:
                walk(n, 0, None, None, frozenset())
        ch["order"] = order
        want = {(s, d) for (s, d) in edges if s in ent and d in ent}
        got = {(x[2], x[0]) for x in order if x[2] is not None}
        if want != got or len([x for x in order if x[2] is not None]) != len(want):
            raise SystemExit("칩 %s 의 줄과 칩 안 사슬이 다르다" % ch["id"])
        ch["fix"] = sum(E[i]["fix"][0] for i in ch["entries"])
        if ch["kind"] == "mem":
            pg = int(ch["lane"][3:])
            ch["label"] = "%d쪽" % pg
            # 회상 칸이 본편 사건을 바로 부르는 경우(카드에 집이 있다) — 참조
            ch["slots"] = {str(i): mem_slot[i][1] for i in ch["entries"] if i in mem_slot}
            ch["refs"] = [x["play"] for x in memt["entries"]
                          if x["page"] == pg and x["play"] in in_card]
            ch["refslots"] = {str(x["play"]): x["id"] for x in memt["entries"]
                              if x["page"] == pg and x["play"] in in_card}
        elif ch["kind"] == "unused":
            ch["label"] = "쓰이지 않는 장면"
        # 그 달 풀에 들어 있으나 다른 곳에 집이 있는 장면(참조)
        if ch["kind"] == "after":
            m = int(ch["page"])
            pno = int(ch["lane"][1:])
            refs = set()
            for p in pools:
                if p["kind"] == "after_training" and p["person"] == pno and p["month"] == m:
                    refs |= {n for n in p["events"] if n and n not in ent}
            ch["refs"] = sorted(refs)
        if ch["kind"] == "invite":
            pno = int(ch["lane"][1:])
            refs = set()
            for p in pools:
                if p["kind"] == "training_invite" and p["person"] == pno:
                    refs |= {n for n in p["events"] if n and n in in_card}
            ch["refs"] = sorted(refs)

    # 다른 달의 참조 칩 — 「아무 때나」 풀(초대·던전 동행·반한 뒤·그 밖)은 집 달 뒤로 이어진다
    refchips = collections.OrderedDict()
    for ch in chips.values():
        if ch["kind"] not in ("invite", "walk", "turned", "etc"):
            continue
        start = int(ch["page"])
        for m in MONTHS:
            if m <= start:
                continue
            rid = "r:%d:%s:%s" % (m, ch["lane"], ch["kind"])
            if rid not in refchips:
                refchips[rid] = {"id": rid, "page": str(m), "lane": ch["lane"], "kind": ch["kind"],
                                 "label": KIND_LABEL[ch["kind"]], "refs": [], "from": []}
            refchips[rid]["refs"] += ch["entries"]
            refchips[rid]["from"].append(ch["page"])
    # 달 페이지의 「회상」 레인 — 이 달에 집이 있는 장면의 재생본(참조)
    for x in memt["entries"]:
        play, need = x["play"], x["need"]
        if play in in_card or need not in E or "home" not in E[need]:
            continue
        hp = E[need]["home"]
        if hp == "mem":
            continue
        rid = "r:%s:mem:memref" % hp
        if rid not in refchips:
            refchips[rid] = {"id": rid, "page": hp, "lane": "mem", "kind": "memref",
                             "label": KIND_LABEL["memref"], "refs": [], "from": ["mem"]}
        refchips[rid]["refs"].append(play)
    for rc in refchips.values():
        rc["refs"] = sorted(set(rc["refs"]))
        rc["from"] = sorted(set(rc["from"]), key=lambda s: (s == "mem", int(s) if s.isdigit() else 0))

    # ── 띠(기간) — 본편 기간 카드 + 우선 대화 창. 띠는 화면 표시일 뿐 셈에 넣지 않는다
    bands = []
    for c in cards:
        pl = c["pl"]
        if "m2" in pl:
            bands.append({"ev": c["entry"], "unit": "c:" + c["key"], "lane": c["lane"], "type": c["type"],
                          "s": [pl["m"], pl["d"]], "f": [pl["m2"], pl["d2"]]})
    for e in evs:
        if e["category"] != "after_training_priority" or e["id"] in in_card:
            continue
        if drawer[e["id"]][2] != "prio":
            continue
        for t in e["triggers"]:
            if t["kind"] == "after_training_priority":
                w = atp_window(t.get("condition_expr"))
                if w:
                    bands.append({"ev": e["id"], "unit": E[e["id"]]["unit"], "lane": drawer[e["id"]][1],
                                  "type": "pool", "s": list(w[0]), "f": list(w[1])})
                    if str(w[0][0]) != drawer[e["id"]][0]:
                        raise SystemExit("우선 대화 %d 의 창 시작 달과 집 달이 다르다" % e["id"])
                break

    # ── 사슬 분류
    def unit(i):
        return E[i]["unit"]

    def page(i):
        return E[i]["home"]

    edge_list = []
    ek = collections.Counter()
    for (s, d), via in edges.items():
        us, ud = unit(s), unit(d)
        if us == ud:
            kf, ko, where = ("inb", "line", "row") if us.startswith("c:") else ("line", "line", "row")
        elif page(s) == page(d):
            kf, ko, where = "line", "line", "src"
        else:
            kf, ko, where = "jump", "jump", "src"
        edge_list.append([s, d, via, kf, ko, page(s), page(d), where])
        ek[(kf, ko, where)] += 1

    # ── 페이지
    pages = []
    for m in MONTHS:
        k = str(m)
        pc = [c for c in cards if c["page"] == k]
        pch = [ch for ch in chips.values() if ch["page"] == k]
        ent = [i for ch in pch for i in ch["entries"]]
        types = collections.Counter(c["type"] for c in pc)
        types["pool"] += len(ent)
        pages.append({"key": k, "label": "%d월" % m, "m": m, "mlen": MLEN[m],
                      "w1": weekday(m, 1),
                      "sum": {"cards": len(pc), "undated": sum(1 for c in pc if "d" not in c["pl"]),
                              "entries": len(ent), "chips": len(pch),
                              "fix": sum(c["fix"][0] for c in pc) + sum(E[i]["fix"][0] for i in ent),
                              "types": {t: types.get(t, 0) for t in ("main", "person", "dungeon", "pool", "mem")}}})
    pch = [ch for ch in chips.values() if ch["page"] == "mem"]
    ent = [i for ch in pch for i in ch["entries"]]
    pages.append({"key": "mem", "label": "회상 · 그 밖", "m": None,
                  "sum": {"cards": 0, "undated": 0, "entries": len(ent), "chips": len(pch),
                          "fix": sum(E[i]["fix"][0] for i in ent),
                          "types": {"main": 0, "person": 0, "dungeon": 0, "pool": 0, "mem": len(ent)}}})

    # 표식(검수 보기에서만 머리글에) — 개발 시험 표의 원문 그대로
    marks = [{"m": mk["date"][0], "d": mk["date"][1], "jp": mk["text_jp"]} for mk in sch["calendar"]["marks"]]

    # ── 풀 소속(옆 패널용)
    for i, ps in pool_of.items():
        out = []
        for p in ps:
            nm = V1.pool_kr(p["kind"], p["person"], p["person2"], p["month"], persons)
            if p["kind"] == "after_training" and p["month"] and p["month"] < lane_join_month("p%d" % p["person"]):
                nm += " (합류 전 달)"
            out.append(nm)
        E[i]["pools"] = out

    # ── 대사 전문 — 문자열 표(중복 제거). 화자 줄은 [-(한국어 화자+1), 원문 태그], 글 줄은 [원문, 한국어]
    strs, sidx = [], {}

    def S(s):
        if s not in sidx:
            sidx[s] = len(strs)
            strs.append(s)
        return sidx[s]

    dlg_ev = {}
    for i, seq in lines_kr.items():
        flat = []
        for s in seq:
            j = jp_lines[s["m"]]
            if s["sp"] is not None:
                flat += [-(S(s["sp"]) + 1), S(j)]
            else:
                k = s.get("kr") or ""
                if k == "" and s.get("raw") is not None:
                    flat += [S(j), -1]          # 번역 대상이 아닌 줄(원문 그대로 나온다)
                else:
                    flat += [S(j), S(k)]
        dlg_ev[str(i)] = flat
    dfix = {}
    for m, (prop, c, note, srcs) in fix_rows.items():
        dfix[str(m)] = [S(prop), {"mean": 1, "term": 2, "other": 3}[c], S(note), S(srcs)]
    dialogue = {"schema": "yoru-flowchart-v2.dialogue.v1",
                "warning": "줄거리 전문 — 아직 안 본 장면이 들어 있다",
                "strs": strs, "ev": dlg_ev, "fix": dfix}

    event_names(E, cards, list(chips.values()), ev, persons, lane_label, cardlab, dungeons)     # r19 이름
    persons_out = {k: v for k, v in persons.items()}
    data = {
        "schema": "yoru-flowchart-v2.data.v1",
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ain": sch["game"]["ain_sha256_original"][:16],
        "persons": persons_out,
        "lanes": [[k, lane_label[k]] for k in lane_keys],
        "join": {k: list(v) for k, v in join.items() if v != CAL_START},
        "cal": {"start": list(CAL_START), "end": list(CAL_END), "months": MONTHS, "week0": WEEK0,
                "slots": {"1": "아침", "2": "밤", "3": "낮", "4": "저녁"}},
        "marks": marks,
        "types": TYPE_LABEL,
        "kinds": KIND_LABEL,
        "pages": pages,
        "cards": cards,
        "chips": list(chips.values()),
        "refchips": list(refchips.values()),
        "bands": bands,
        "edges": edge_list,
        "ev": {str(k): v for k, v in E.items()},
        "counts": {
            "events": len(evs), "cards": len(cards), "in_cards": len(in_card),
            "drawer": len(drawer), "edges": len(edge_list),
            "fix_in_events": sum(v[0] for v in fix.values()), "fix_outside": len(fix_outside),
            "fix_map_lines": len(fm),
            "fix_by_cat": {c: sum(v[k] for v in fix.values()) for c, k in (("mean", 1), ("term", 2), ("other", 3))},
            "lines": sum(e["messages"]["count"] for e in evs),
        },
        "sources": {"final_map": FINAL, "messages": "scratch/dump/messages.txt",
                    "lines_kr": "graph/lines_kr.jsonl", "labels": "graph/labels.json",
                    "groups": "graph/groups.json", "schedule": "graph/schedule.json"},
    }

    def js(obj):
        # <script type="application/json"> 안에서 안전하게: '<' 를 \u003c 로(유효한 JSON 이스케이프)
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    data_js = js(data)
    dlg_js = js(dialogue)
    html = (TEMPLATE.replace("__DATA_JSON__", data_js, 1)
                    .replace("__DIALOGUE_JSON__", dlg_js, 1))
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(html)
    size = os.path.getsize(out_path)
    if size > SIZE_CAP:
        raise SystemExit("파일이 상한(30MB)을 넘었다: %d" % size)

    # ── 요약(보고용)
    print("wrote", out_path, size, "bytes  (자료 %d · 대사 %d · 코드 %d)" % (
        len(data_js.encode("utf-8")), len(dlg_js.encode("utf-8")),
        size - len(data_js.encode("utf-8")) - len(dlg_js.encode("utf-8"))))
    print("대사 전문: 줄 %d · 서로 다른 문자열 %d" % (sum(len(v) // 2 for v in dlg_ev.values()), len(strs)))
    print("카드 %d (묶음 안 사건 %d) · 서랍 %d · 사건 합 %d" % (len(cards), len(in_card), len(drawer),
                                                        len(in_card) + len(drawer)))
    print("라벨 출처", dict(label_src))
    print("서랍 집 달 조정", dict(adjust))
    print("사슬", len(edge_list), dict(ek))
    print("교정: 지도 %d줄 · 사건 범위 안 %d · 밖 %d %s · 분류 %s" % (
        len(fm), data["counts"]["fix_in_events"], len(fix_outside), fix_outside[:5], data["counts"]["fix_by_cat"]))
    print("%-8s %5s %5s %5s %5s %5s %6s" % ("쪽", "카드", "달만", "서랍", "칩", "참조칩", "교정"))
    for p in pages:
        s = p["sum"]
        nrc = sum(1 for rc in refchips.values() if rc["page"] == p["key"])
        print("%-8s %5d %5d %5d %5d %5d %6d" % (p["label"], s["cards"], s["undated"], s["entries"],
                                               s["chips"], nrc, s["fix"]))
    tot = {k: sum(p["sum"][k] for p in pages) for k in ("cards", "undated", "entries", "chips", "fix")}
    print("%-8s %5d %5d %5d %5d %5s %6d" % ("합", tot["cards"], tot["undated"], tot["entries"],
                                           tot["chips"], "", tot["fix"]))
    print("띠", len(bands), "· 참조 칩", len(refchips))
    return data


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>밤이 온다! 이벤트 차트 v2</title>
<style>
:root{
  --page:#f9f9f7; --surface:#ffffff; --surface2:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --hair:#e1e0d9; --axis:#c3c2b7; --wash:#f0efec; --wash2:#e9e8e3;
  --t-main:#6b6a65; --t-person:#4a3aa7; --t-dungeon:#1baf7a; --t-pool:#eb6834; --t-mem:#6b6a65;
  --tint-main:rgba(107,106,101,.07); --tint-person:rgba(74,58,167,.07);
  --tint-dungeon:rgba(27,175,122,.09); --tint-pool:rgba(235,104,52,.07); --tint-mem:rgba(107,106,101,.05);
  --fix-bg:#fff4d6; --fix-ink:#6b4a00; --fix-edge:#fab219;
  --sus-bg:#fdecec; --sus-ink:#9e2a2a;
  --sat:#2a5fb0; --sun:#b03a3a; --sat-bg:#f1f4fa; --sun-bg:#faf1f1;
  --sel:#2a78d6; --flash:#ffe9a8;
  --labelw:96px;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--page);color:var(--ink);
  font:12px/1.45 "Malgun Gothic","맑은 고딕",system-ui,-apple-system,"Segoe UI",sans-serif;
  display:flex;flex-direction:column;overflow:hidden}
button{font:inherit;color:inherit}
header{flex:0 0 auto;background:var(--surface);border-bottom:1px solid var(--hair);padding:6px 12px 0}
.r1{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
h1{font-size:15px;margin:0;font-weight:700;letter-spacing:-.01em}
h1 small{font-weight:400;color:var(--muted);font-size:11px;margin-left:6px}
.seg{display:inline-flex;border:1px solid var(--axis);border-radius:6px;overflow:hidden}
.seg button{border:0;background:var(--surface);padding:3px 10px;cursor:pointer;color:var(--ink2)}
.seg button+button{border-left:1px solid var(--axis)}
.seg button.on{background:var(--ink);color:#fff}
.find{display:inline-flex;gap:4px;align-items:center}
.find input{width:92px;border:1px solid var(--axis);border-radius:6px;padding:3px 6px;font:inherit}
.r2{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:6px 0}
.r2 .lbl{color:var(--muted);font-size:11px;margin-left:6px}
.tg{border:1px solid var(--hair);background:var(--surface);border-radius:999px;padding:1px 9px;cursor:pointer;color:var(--muted)}
.tg.on{border-color:var(--ink2);color:var(--ink);background:var(--surface2)}
.tg .sw{display:inline-block;width:3px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.ck{display:inline-flex;align-items:center;gap:4px;cursor:pointer;color:var(--ink2);margin-left:6px}
.ck input{margin:0}
#band{display:flex;align-items:stretch;gap:6px;padding:6px 0 8px}
#band .nav{border:1px solid var(--hair);background:var(--surface);border-radius:8px;width:30px;cursor:pointer;color:var(--ink2);font-size:14px}
#band .cells{display:flex;gap:6px;flex:1 1 auto;min-width:0}
.bcell{flex:1 1 0;min-width:0;border:1px solid var(--hair);background:var(--surface);border-radius:8px;
  padding:4px 8px 5px;text-align:left;cursor:pointer;display:flex;flex-direction:column;gap:2px}
.bcell:hover{border-color:var(--axis)}
.bcell.cur{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}
.bcell .bm{font-weight:700;font-size:13px;white-space:nowrap}
.bcell .bs{color:var(--ink2);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bcell .bbar{display:flex;gap:2px;height:4px;margin:1px 0}
.bcell .bbar i{display:block;border-radius:2px;min-width:2px}
.bfx{font-size:11px;white-space:nowrap}
.t-main{--tc:var(--t-main);--tt:var(--tint-main)} .t-person{--tc:var(--t-person);--tt:var(--tint-person)}
.t-dungeon{--tc:var(--t-dungeon);--tt:var(--tint-dungeon)} .t-pool{--tc:var(--t-pool);--tt:var(--tint-pool)}
.t-mem{--tc:var(--t-mem);--tt:var(--tint-mem)}
i.t-main,i.t-person,i.t-dungeon,i.t-pool,i.t-mem{background:var(--tc)}
#warn{flex:0 0 auto;font-size:11px;padding:3px 12px;border-bottom:1px solid var(--hair)}
#warn.rv{background:#fff8e6;color:#6b4a00}
#warn.pl{background:#eef5ee;color:#1f5a1f}
#main{flex:1 1 auto;min-height:0;display:flex}
#scroller{flex:1 1 auto;min-width:0;overflow:auto;position:relative;background:var(--page)}
#side{flex:0 0 380px;width:380px;overflow:auto;border-left:1px solid var(--hair);background:var(--surface);padding:12px 14px 40px}
.ptitle{display:flex;align-items:baseline;gap:10px;padding:10px 14px 4px;position:sticky;left:0}
.ptitle h2{margin:0;font-size:17px}
.ptitle .pn{color:var(--muted);font-size:11px}
/* ── 레인 보기 ── */
.dayhead{position:sticky;top:0;z-index:6;display:flex;background:var(--surface);border-bottom:1px solid var(--axis);height:34px}
.dayhead .corner{position:sticky;left:0;z-index:7;width:var(--labelw);flex:0 0 var(--labelw);background:var(--surface);
  border-right:1px solid var(--hair);font-size:10px;color:var(--muted);padding:3px 6px}
.dayhead .days{position:relative;flex:0 0 auto}
.dh{position:absolute;top:0;height:34px;text-align:center;font-size:11px;line-height:1.1;padding-top:3px;color:var(--ink2)}
.dh .wd{display:block;font-size:9.5px;color:var(--muted)}
.dh.sat{color:var(--sat)} .dh.sat .wd{color:var(--sat)}
.dh.sun{color:var(--sun)} .dh.sun .wd{color:var(--sun)}
.dh.out{color:#c9c8c1} .dh.out .wd{color:#d6d5cf}
.dh .mk{position:absolute;right:1px;top:1px;width:6px;height:6px;border-radius:50%;background:var(--ink2)}
.lanewrap{position:relative}
.cols{position:absolute;top:0;bottom:0;left:var(--labelw);z-index:0;pointer-events:none}
.col{position:absolute;top:0;bottom:0;border-left:1px solid #efeee9}
.col.sat{background:var(--sat-bg)} .col.sun{background:var(--sun-bg)}
.col.out{background:var(--wash)}
.lane{position:relative;z-index:1;display:grid;grid-template-columns:var(--labelw) auto;border-bottom:1px solid var(--hair)}
.lane .lh{grid-row:1 / span 3;position:sticky;left:0;z-index:5;background:var(--surface);border-right:1px solid var(--hair);
  padding:6px 8px;font-weight:700;font-size:12.5px}
.lane .lh small{display:block;font-weight:400;color:var(--muted);font-size:10.5px}
.lane .lh .sw{display:inline-block;width:3px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.lb{position:relative;min-height:40px}
.lf{background:var(--surface2);border-top:1px dashed transparent;display:flex;flex-wrap:wrap;gap:5px;align-items:center;padding:5px 8px;min-height:0}
.lf:empty{display:none}
.lf .fl{color:var(--muted);font-size:10.5px;margin-right:2px}
.lists{background:var(--surface2)}
.lists:empty{display:none}
.prejoin{position:absolute;top:0;bottom:0;left:0;background:repeating-linear-gradient(0deg,rgba(240,239,236,.86),rgba(240,239,236,.86));
  z-index:2;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:11px;border-right:2px solid var(--axis)}
.lane.dim .lh{color:var(--muted)}
.pill{position:absolute;z-index:3;display:block;text-align:left;border:1px solid rgba(11,11,11,.10);border-left:3px solid var(--tc);
  background:linear-gradient(var(--tt),var(--tt)),var(--surface);border-radius:6px;padding:3px 6px 3px 6px;cursor:pointer;overflow:hidden}
.pill:hover{border-color:rgba(11,11,11,.30);border-left-color:var(--tc)}
.pill .l1,.upill .l1{display:flex;gap:5px;align-items:baseline;white-space:nowrap}
.upill .dt{font-weight:700;font-size:11px}
.upill .no{color:var(--muted);font-size:10px}
.pill .dt{font-weight:700;font-size:11px}
.pill .no{color:var(--muted);font-size:10px}
.pill .l2,.pill .l3{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px}
.pill .l2{color:var(--ink2)}
.pill .l3{color:var(--ink)}
.pill .tick{position:absolute;left:-1px;top:-1px;width:0;height:0}
.bn{font-size:10.5px;font-weight:700;color:var(--ink2);background:var(--wash2);border-radius:4px;padding:0 4px}
.ptag{font-size:10px;color:var(--t-person);border:1px solid rgba(74,58,167,.35);border-radius:4px;padding:0 3px}
.fx{font-size:10.5px;color:var(--fix-ink);background:var(--fix-bg);border:1px solid var(--fix-edge);border-radius:4px;padding:0 4px;white-space:nowrap}
.fx0{font-size:10.5px;color:var(--muted)}
.sus{font-size:10.5px;color:var(--sus-ink);background:var(--sus-bg);border-radius:4px;padding:0 4px;white-space:nowrap}
.ml{margin-left:auto}
.sel{outline:2px solid var(--sel);outline-offset:1px}
.flash{animation:fl 1.6s ease-out 1}
@keyframes fl{0%{box-shadow:0 0 0 4px var(--flash)}100%{box-shadow:0 0 0 0 rgba(0,0,0,0)}}
.band{position:absolute;z-index:3;height:7px;border-radius:4px;background:var(--tc);opacity:.55;cursor:pointer;border:0;padding:0}
.band:hover{opacity:.9}
.band.cont{opacity:.28}
.upill{position:relative;display:inline-block;text-align:left;border:1px solid rgba(11,11,11,.10);border-left:3px solid var(--tc);
  background:linear-gradient(var(--tt),var(--tt)),var(--surface);border-radius:6px;padding:2px 6px;cursor:pointer;max-width:260px;vertical-align:top}
.upill .l2,.upill .l3{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px}
.upill .l2{color:var(--ink2)}
.chip{border:1px solid var(--axis);background:var(--surface);border-radius:999px;padding:1px 9px;cursor:pointer;font-size:11px;white-space:nowrap}
.chip b{font-weight:700;margin-left:2px}
.chip:hover{border-color:var(--ink2)}
.chip.open{background:var(--ink);color:#fff;border-color:var(--ink)}
.chip.open .fx{background:#fff4d6}
.chip.ref{border-style:solid;border-color:var(--hair);color:var(--muted);background:transparent}
.chip.ref.open{background:var(--wash2);color:var(--ink);border-color:var(--axis)}
.chip .dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--t-pool);margin-right:5px;vertical-align:1px}
.clist{border-top:1px solid var(--hair);padding:6px 8px 8px calc(var(--labelw) + 8px)}
.clist h4{margin:0 0 4px;font-size:11.5px;color:var(--ink2);font-weight:700}
.clist h4 small{font-weight:400;color:var(--muted);margin-left:6px}
.rows{display:flex;flex-direction:column;gap:2px}
.row{display:flex;align-items:flex-start;gap:6px;padding-left:calc(var(--d,0) * 18px)}
.row .rb{flex:1 1 auto;min-width:0;display:grid;grid-template-columns:62px minmax(96px,1.1fr) minmax(70px,.9fr) minmax(90px,1.5fr) auto;gap:8px;align-items:baseline;
  text-align:left;border:1px solid transparent;border-left:3px solid var(--tc);background:linear-gradient(var(--tt),var(--tt)),var(--surface);
  border-radius:5px;padding:2px 6px;cursor:pointer}
.row .rb:hover{border-color:rgba(11,11,11,.25);border-left-color:var(--tc)}
.row .rb{overflow:hidden}
.row .rb > span{min-width:0}
.bbox .row .via{max-width:48%;overflow:hidden;text-overflow:ellipsis}
.bbox .row .rb{flex:1 1 40%}
.row.rep .rb{opacity:.55}
.row .rid{font-weight:700;font-size:11px}
.row .lw,.row .lp,.row .lf2{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px}
.row .lw{color:var(--ink2)} .row .lp{color:var(--ink2)}
.row.play .rb{grid-template-columns:62px minmax(110px,1.2fr) minmax(80px,1fr) auto}
.row .via,.row .edge{flex:0 0 auto;font-size:10.5px;color:var(--ink2);white-space:nowrap;padding-top:3px}
.edge{border:0;background:transparent;cursor:pointer;font-size:10.5px;white-space:nowrap;padding:2px 4px;border-radius:4px}
.edge.line{color:var(--ink2)} .edge.jump{color:var(--sel);font-weight:700}
.edge:hover{background:var(--wash)}
.via.edge{color:var(--ink2);font-weight:400}
.row{position:relative}
.row.child::before{content:"";position:absolute;left:calc(var(--d,0) * 18px - 12px);top:-3px;height:calc(50% + 3px);width:9px;
  border-left:1px solid var(--axis);border-bottom:1px solid var(--axis);border-bottom-left-radius:3px;pointer-events:none}
.bbox .row.child::before{top:0;height:50%}
.refs{margin-top:4px;font-size:10.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.refs .rf{border:1px solid var(--hair);background:var(--surface);border-radius:4px;padding:0 5px;cursor:pointer;color:var(--ink2);font-size:10.5px}
.bbox{position:absolute;z-index:4;background:var(--surface);border:1px solid var(--axis);border-left:3px solid var(--tc);border-radius:6px;padding:4px 6px 6px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.bbox .bh{display:flex;gap:6px;align-items:baseline;cursor:pointer;font-size:11px;margin-bottom:3px;white-space:nowrap}
.bbox .row .rb{grid-template-columns:58px minmax(90px,1fr) auto}
.bbox .row .lp,.bbox .row .lf2{display:none}
.bbox .rows{gap:2px}
.bbox .row{height:21px;overflow:hidden;white-space:nowrap}
.bbox .row .rb{padding:1px 6px}
.row.hasslot .rb{grid-template-columns:100px minmax(96px,1.1fr) minmax(70px,.9fr) minmax(90px,1.5fr) auto}
.row.hasslot.play .rb{grid-template-columns:100px minmax(110px,1.2fr) minmax(80px,1fr) auto}
/* ── 달력 보기 ── */
.calgrid{display:grid;grid-template-columns:repeat(7,minmax(120px,1fr));gap:1px;background:var(--hair);border:1px solid var(--hair);margin:4px 14px 10px}
.calgrid .wh{background:var(--surface);text-align:center;font-weight:700;font-size:11px;padding:3px 0;color:var(--ink2)}
.calgrid .wh.sat{color:var(--sat)} .calgrid .wh.sun{color:var(--sun)}
.cd{background:var(--surface);min-height:88px;padding:3px 4px;display:flex;flex-direction:column;gap:2px;min-width:0}
.cd.sat{background:var(--sat-bg)} .cd.sun{background:var(--sun-bg)} .cd.out{background:var(--wash)} .cd.pad{background:var(--page)}
.cd .dn{font-size:11px;font-weight:700;color:var(--ink2);display:flex;gap:4px;align-items:baseline}
.cd.sat .dn{color:var(--sat)} .cd.sun .dn{color:var(--sun)} .cd.out .dn{color:#c9c8c1}
.cd .mkx{font-size:9.5px;font-weight:400;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cchip{display:block;width:100%;text-align:left;border:1px solid rgba(11,11,11,.10);border-left:3px solid var(--tc);
  background:linear-gradient(var(--tt),var(--tt)),var(--surface);border-radius:5px;padding:1px 5px;cursor:pointer;font-size:10.5px;overflow:hidden}
.cchip .l1{display:flex;gap:4px;white-space:nowrap}
.cchip .l2,.cchip .l3{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cchip .l2{color:var(--ink2)}
.cchip.win{border-left-style:solid;opacity:.8}
.calfoot{margin:0 14px 16px;border:1px solid var(--hair);background:var(--surface)}
.cfl{display:grid;grid-template-columns:var(--labelw) 1fr;border-bottom:1px solid var(--hair)}
.cfl .lh{padding:6px 8px;font-weight:700;border-right:1px solid var(--hair)}
.cfl .lf{background:var(--surface)}
.cfl .clist{padding-left:8px}
/* ── 회상 · 그 밖 ── */
.memgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(520px,1fr));gap:10px;padding:6px 14px 20px}
.memsec{border:1px solid var(--hair);background:var(--surface);border-radius:8px;padding:8px 10px}
.memsec h3{margin:0 0 6px;font-size:13px;display:flex;gap:8px;align-items:baseline}
.memsec h3 small{font-weight:400;color:var(--muted);font-size:11px}
.slot{display:inline-block;width:34px;color:var(--muted);font-size:10.5px}
/* ── 옆 패널 ── */
#side h2{font-size:16px;margin:0 0 2px;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
#side .sub{color:var(--ink2);font-size:11.5px;margin-bottom:6px}
#side .k{color:var(--muted);font-size:10.5px;margin-top:10px;letter-spacing:.02em}
#side .v{font-size:12px;word-break:keep-all;overflow-wrap:anywhere}
#side ul{margin:3px 0;padding-left:16px}
#side li{margin:1px 0}
#side .btns{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}
#side .btn{border:1px solid var(--axis);background:var(--surface);border-radius:6px;padding:3px 10px;cursor:pointer}
#side .btn.pri{background:var(--ink);color:#fff;border-color:var(--ink)}
#side .lnk{border:0;background:none;color:var(--sel);cursor:pointer;padding:0;font:inherit}
#side details{margin-top:10px;border-top:1px solid var(--hair);padding-top:6px}
#side summary{cursor:pointer;font-size:12px;font-weight:700}
#side .mrow{display:flex;gap:6px;align-items:baseline;padding:1px 0;padding-left:calc(var(--d,0)*14px);font-size:11.5px}
#side .mrow button{border:0;background:none;cursor:pointer;padding:0;text-align:left;font:inherit}
#side .mrow .rid{font-weight:700}
#side .mrow.rep{opacity:.55}
#side .mrow .w{color:var(--ink2)}
table.dl{width:100%;border-collapse:collapse;margin-top:6px;font-size:11.5px;table-layout:fixed}
table.dl td{vertical-align:top;padding:2px 4px;border-bottom:1px solid #f1f0ec;word-break:break-all}
table.dl td.jp{color:var(--ink2);width:46%}
table.dl tr.sp td{color:var(--t-person);font-weight:700;padding-top:6px;border-bottom:0}
table.dl tr.fixr td{background:var(--fix-bg);color:var(--fix-ink)}
table.dl td.kr.raw{color:var(--muted)}
table.dl td.kr.nil{color:#c9c8c1}
.fixlist{margin:4px 0 0;padding:0;list-style:none}
.fixlist li{border-left:3px solid var(--fix-edge);background:var(--fix-bg);padding:3px 6px;margin:3px 0;font-size:11.5px}
.fixlist .cur{color:var(--ink2);text-decoration:line-through;text-decoration-color:rgba(0,0,0,.25)}
.fixlist .src{color:var(--muted);font-size:10px}
.legend{display:grid;grid-template-columns:118px 1fr;gap:4px 10px;align-items:center;font-size:11.5px;margin-top:6px}
.legend > :nth-child(odd){justify-self:start}
.legend .sw{display:inline-block;width:3px;height:14px;border-radius:2px}
.empty{color:var(--muted);font-size:11px;padding:6px 0}
.note{color:var(--muted);font-size:11px}
footer{flex:0 0 auto;border-top:1px solid var(--hair);background:var(--surface);color:var(--muted);font-size:10.5px;padding:3px 12px}
#errors:empty,#selftest-out:empty{display:none}
#errors{position:fixed;bottom:0;left:0;right:0;background:#fdecec;color:#9e2a2a;font-size:11px;margin:0;padding:4px 10px;z-index:60;max-height:30vh;overflow:auto}
#selftest-out{display:none}
</style>
</head>
<body>
<header>
  <div class="r1">
    <h1>밤이 온다! 이벤트 차트 <small id="hdr"></small></h1>
    <span class="seg" role="group" aria-label="보기 모드"><button type="button" id="mReview" class="on">검수 보기</button><button type="button" id="mPlay">플레이 보기</button></span>
    <span class="seg" role="group" aria-label="모양"><button type="button" id="vLane" class="on">레인</button><button type="button" id="vCal">달력으로 보기</button></span>
    <span class="find"><input id="q" placeholder="E번호로 찾기" aria-label="E번호로 찾기"><button type="button" id="qGo" class="tg">가기</button></span>
  </div>
  <div class="r2" id="filters"></div>
  <div id="band"><button type="button" class="nav" id="prev" aria-label="이전 달">‹</button><div class="cells" id="cells"></div><button type="button" class="nav" id="next" aria-label="다음 달">›</button></div>
</header>
<div id="warn"></div>
<div id="main">
  <div id="scroller"><div id="page"></div></div>
  <aside id="side"></aside>
</div>
<footer id="foot"></footer>
<pre id="errors"></pre>
<pre id="selftest-out"></pre>
<script type="application/json" id="yoru-data">__DATA_JSON__</script>
<script type="application/json" id="yoru-dialogue">__DIALOGUE_JSON__</script>
<script>
'use strict';
window.addEventListener('error', function(ev){
  var el = document.getElementById('errors');
  if (el) el.textContent += 'JS 오류: ' + (ev.message || ev) + ' @' + (ev.lineno || '') + '\n';
});
/* ── 자료 ─ 읽고 나면 자료 블록은 DOM 에서 뺀다(화면 DOM 에 자료 원문이 남지 않는다) ── */
const D = (function(){ const el = document.getElementById('yoru-data'); const t = el.textContent; el.remove(); return JSON.parse(t); })();
let DLG_TEXT = (function(){ const el = document.getElementById('yoru-dialogue'); if (!el) return null; const t = el.textContent; el.remove(); return t; })();
let DLG = null;
function dlg(){ if (!DLG && DLG_TEXT){ DLG = JSON.parse(DLG_TEXT); DLG_TEXT = null; } return DLG; }

const EV = D.ev;
const CARD = {}; D.cards.forEach(c => CARD[c.key] = c);
const CHIP = {}; D.chips.forEach(c => CHIP[c.id] = c);
const RCHIP = {}; D.refchips.forEach(c => RCHIP[c.id] = c);
const PAGE = {}; D.pages.forEach(p => PAGE[p.key] = p);
const LANE = {}; D.lanes.forEach(l => LANE[l[0]] = l[1]);
const OUT = {}, INC = {};
D.edges.forEach(x => { (OUT[x[0]] = OUT[x[0]] || []).push(x); (INC[x[1]] = INC[x[1]] || []).push(x); });
const TYPES = ['main','person','dungeon','pool','mem'];
const PILL_W = 176, GAP = 4;

const ST = {
  page: '4', view: 'lane', review: true, expand: false, fixOnly: false,
  lanes: new Set(D.lanes.map(l => l[0])), types: new Set(TYPES),
  open: new Set(), sel: null, flash: null, selftest: false
};
try { const p = JSON.parse(localStorage.getItem('yoru-v2-prefs') || '{}'); if (p.view === 'cal' || p.view === 'lane') ST.view = p.view; } catch(e) {}
function savePrefs(){ try { localStorage.setItem('yoru-v2-prefs', JSON.stringify({view: ST.view})); } catch(e) {} }

/* ── 작은 도구 ── */
function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function pad(i){ return 'E' + String(i).padStart(5, '0'); }
function showFirst(){ return ST.review; }          // 첫 줄은 검수 보기에서만 DOM 에 넣는다
function showText(){ return ST.review; }           // 대사 전문·답 문구·교정 문안도 검수 보기에서만
function slotName(s){ return (D.cal.slots || {})[String(s)] || ''; }
function pageOfEv(id){ return EV[id].home; }
function unitOfEv(id){ return EV[id].unit; }
function cardOfEv(id){ const u = EV[id].unit; return u.startsWith('c:') ? CARD[u.slice(2)] : null; }
function chipOfEv(id){ const u = EV[id].unit; return u.startsWith('d:') ? CHIP[u.slice(2)] : null; }
function typeOfEv(id){ const c = cardOfEv(id); if (c) return c.type; return EV[id].home === 'mem' ? 'mem' : 'pool'; }
function laneOfEv(id){ const c = cardOfEv(id); return c ? c.lane : chipOfEv(id).lane; }
function pageLabel(k){ return PAGE[k] ? PAGE[k].label : k; }
function whoText(e){ return e.who.join(' · ') + (e.wmore ? ' 외 ' + e.wmore : ''); }
function firstText(e){ return e.first + (e.fcut ? '…' : ''); }
function fixTag(n){ return n ? '<span class="fx" title="09-23 교정 예정 ' + n + '건">✎' + n + '</span>' : ''; }
function dateText(pl){
  if (!pl) return '날짜 없음';
  if (pl.d === undefined) return pl.m + '월 중';
  let s = pl.m + '/' + pl.d;
  if (pl.m2 !== undefined) return s + '~' + pl.m2 + '/' + pl.d2;
  if (pl.slot) s += ' ' + slotName(pl.slot);
  return s;
}
function weekdayOf(m, d){
  let n = 0; for (let x = 4; x < m; x++) n += PAGE[String(x)].mlen;
  n += d - 9; return ((D.cal.week0 + n) % 7 + 7) % 7;
}
function inCal(m, d){ const a = m * 100 + d; return a >= D.cal.start[0]*100 + D.cal.start[1] && a <= D.cal.end[0]*100 + D.cal.end[1]; }
function joinOf(lane){ return D.join[lane] || null; }
function typeVisible(t){ return ST.types.has(t); }
function evVisible(id){ return !ST.fixOnly || EV[id].fix[0] > 0; }
function cardVisible(c){ return typeVisible(c.type) && (!ST.fixOnly || c.fix[0] > 0); }
function isSel(kind, key){ return ST.sel && ST.sel.k === kind && String(ST.sel.key) === String(key); }
function selCls(kind, key){ return isSel(kind, key) ? ' sel' : ''; }

/* ── 사슬 표지 ── 원본 쪽(같은 쪽이지만 다른 묶음·서랍 / 다른 달) */
function edgeKind(x){ return ST.expand ? x[4] : x[3]; }
function srcEdgesHTML(id){
  const xs = (OUT[id] || []).filter(x => x[7] === 'src');
  return xs.map(x => {
    const k = edgeKind(x), via = x[2] ? '답 ' + x[2] + ' ' : '';
    if (k === 'jump') return '<button type="button" class="edge jump" data-edge="' + x[0] + '>' + x[1] + '" data-ek="jump" data-go="' + x[1] + '" title="다른 달로 이어진다">→ ' + esc(pageLabel(x[6])) + ' ' + via + pad(x[1]) + '</button>';
    return '<button type="button" class="edge line" data-edge="' + x[0] + '>' + x[1] + '" data-ek="line" data-go="' + x[1] + '" title="같은 쪽의 다른 칸으로 이어진다">↳ ' + via + pad(x[1]) + '</button>';
  }).join('');
}
function viaHTML(parent, child, viaNo, viaText, kindAttr){
  // 묶음·서랍 안 사슬 = 자식 줄의 연결 표지(사슬 하나에 하나)
  if (parent == null) return '';
  const k = kindAttr || 'line';
  let t = viaNo ? '답 ' + viaNo : '↳ 이어서';
  if (viaNo && viaText && showText()) t += ' ' + esc(quoteAns(viaText));
  return '<span class="via edge line" data-edge="' + parent + '>' + child + '" data-ek="' + k + '">' + t + '</span>';
}

/* ── 줄(서랍·회상·펼친 묶음) ── */
function rowHTML(id, depth, opt){
  opt = opt || {};
  const e = EV[id], t = opt.type || typeOfEv(id);
  const rep = opt.rep;
  const attr = (rep ? ' data-ref="' + id + '"' : ' data-ev="' + id + '"') + (opt.owner ? ' data-owner="' + opt.owner + '"' : '');
  let h = '<div class="row' + (rep ? ' rep' : '') + (opt.via ? ' child' : '') + (ST.review ? '' : ' play') + (opt.slot ? ' hasslot' : '') + '"' + attr + ' style="--d:' + (depth || 0) + '">';
  h += '<button type="button" class="rb t-' + t + selCls('e', id) + '" data-pick="e:' + id + '">';
  h += '<span class="rid">' + (opt.slot ? '<span class="slot">' + opt.slot + '칸</span>' : '') + pad(id) + '</span>';
  h += '<span class="lw">' + esc(e.when[0]) + '</span>';
  h += '<span class="lp">' + esc(whoText(e)) + '</span>';
  if (showFirst()) h += '<span class="lf2">' + esc(firstText(e)) + '</span>';
  h += '<span class="ml">' + (rep ? '<span class="note">공유 · 위에 있음</span>' : fixTag(e.fix[0])) + '</span>';
  h += '</button>';
  if (opt.via) h += opt.via;
  if (!rep) h += srcEdgesHTML(id);
  return h + '</div>';
}

/* ── 카드 알약 ── */
function cardLabelTitle(c){
  const e = EV[c.entry];
  let s = pad(c.entry) + (c.n > 1 ? ' 외 ' + (c.n - 1) + '단계' : '') + '\n' + e.when.join(' / ') + '\n' + whoText(e);
  if (showFirst()) s += '\n' + firstText(e);
  return s;
}
function pillInner(c){
  const e = EV[c.entry];
  let h = '<span class="l1"><span class="dt">' + esc(dateText(c.pl)) + '</span><span class="no">' + pad(c.entry) + '</span>';
  if (c.n > 1) h += '<span class="bn" title="묶음 ' + c.n + '단계">▸' + c.n + '</span>';
  if (c.ptag) h += '<span class="ptag">' + esc(c.ptag) + '</span>';
  h += '<span class="ml">' + fixTag(c.fix[0]) + '</span></span>';
  h += '<span class="l2 lp">' + esc(whoText(e)) + '</span>';
  if (showFirst()) h += '<span class="l3 lf">' + esc(firstText(e)) + '</span>';
  return h;
}
function pillAttrs(c){
  let a = ' data-card="' + c.key + '" data-pick="c:' + c.key + '"';
  if (c.n === 1) a += ' data-ev="' + c.entry + '"'; else a += ' data-members="' + c.members.join(',') + '"';
  return a + ' data-fix="' + c.fix[0] + '" title="' + esc(cardLabelTitle(c)) + '"';
}
function pillH(){ return ST.review ? 58 : 40; }
function bundleRows(c){
  let h = '<div class="rows">';
  c.rows.forEach(r => {
    const [id, dep, vk, vno, vtext, shared, counts, parent] = r;
    const via = parent != null ? viaHTML(parent, id, vno, vtext, 'line') : '';
    h += rowHTML(id, dep, {rep: !counts, via: via, type: c.type, owner: 'c:' + c.key});
  });
  return h + '</div>';
}
function bundleBox(c, x, y, w){
  let h = '<div class="bbox t-' + c.type + selCls('c', c.key) + '" data-card="' + c.key + '" data-fix="' + c.fix[0] + '" style="left:' + x + 'px;top:' + y + 'px;width:' + w + 'px">';
  h += '<div class="bh" data-pick="c:' + c.key + '"><b>' + esc(dateText(c.pl)) + '</b> <span class="bn">▸' + c.n + '</span> 묶음 ' + pad(c.entry) + (c.ptag ? ' <span class="ptag">' + esc(c.ptag) + '</span>' : '') + ' <span class="ml">' + fixTag(c.fix[0]) + '</span></div>';
  return h + bundleRows(c) + '</div>';
}

/* ── 배치(겹치지 않게 아래로 쌓는다) ── */
function pack(items){
  const placed = [];
  items.forEach(it => {
    let y = 0, guard = 0;
    for (;;){
      const hit = placed.find(p => p.x < it.x + it.w + GAP && it.x < p.x + p.w + GAP && p.y < y + it.h + GAP && y < p.y + p.h + GAP);
      if (!hit || ++guard > 500) break;
      y = hit.y + hit.h + GAP;
    }
    it.y = y; placed.push(it);
  });
  return placed.reduce((m, p) => Math.max(m, p.y + p.h), 0);
}

/* ── 레인 보기 ── */
function dayWidth(p){
  const sc = document.getElementById('scroller');
  const W = (sc && sc.clientWidth) ? sc.clientWidth : 1200;
  const lw = 96;
  return Math.max(26, Math.min(46, Math.floor((W - lw - PILL_W - 24) / (p.mlen - 1))));
}
function laneChips(pk, lane){
  return D.chips.filter(ch => ch.page === pk && ch.lane === lane);
}
function laneRefChips(pk, lane){
  return D.refchips.filter(ch => ch.page === pk && ch.lane === lane);
}
function chipVisibleEntries(ch){
  return ch.entries.filter(id => evVisible(id) && typeVisible(ch.page === 'mem' ? 'mem' : 'pool'));
}
function chipHTML(ch){
  const vis = chipVisibleEntries(ch), n = ch.entries.length;
  const fx = vis.reduce((a, id) => a + EV[id].fix[0], 0);
  const open = ST.open.has(ch.id);
  return '<button type="button" class="chip' + (open ? ' open' : '') + '" data-chip="' + ch.id + '" data-count="' + vis.length + '" data-fix="' + fx + '" aria-expanded="' + open + '"><span class="dot" style="background:var(--t-' + (ch.page === 'mem' ? 'mem' : 'pool') + ')"></span>' + esc(ch.label) + ' <b>' + (vis.length === n ? n : vis.length + '/' + n) + '</b>' + (fx ? ' <span class="fx">✎' + fx + '</span>' : '') + '</button>';
}
function refChipHTML(rc){
  const open = ST.open.has(rc.id);
  const from = rc.from.map(k => pageLabel(k)).join('·');
  return '<button type="button" class="chip ref' + (open ? ' open' : '') + '" data-refchip="' + rc.id + '" data-refcount="' + rc.refs.length + '" title="집은 ' + esc(from) + ' 서랍 — 이 달에도 나올 수 있다">' + esc(rc.label) + ' ' + rc.refs.length + ' · ' + esc(from) + (rc.kind === 'memref' ? '' : '부터') + '</button>';
}
function chipListHTML(ch){
  const vis = new Set(chipVisibleEntries(ch));
  const who = LANE[ch.lane] || (ch.kind === 'mem' ? '' : '');
  let h = '<div class="clist" data-chiplist="' + ch.id + '"><h4>' + esc(ch.label) + (who ? ' · ' + esc(who) : '') + ' <small>' + ch.entries.length + '장 · 집은 이 서랍</small></h4><div class="rows">';
  ch.order.forEach(r => {
    const [id, dep, parent, vno, first] = r;
    if (!vis.has(id) && first) return;
    const via = parent != null ? viaHTML(parent, id, vno, viaAnswer(parent, vno), 'line') : '';
    h += rowHTML(id, dep, {rep: !first, via: via, type: ch.page === 'mem' ? 'mem' : 'pool', slot: ch.slots ? ch.slots[String(id)] : null, owner: 'd:' + ch.id});
  });
  h += '</div>';
  if (ch.refs && ch.refs.length){
    h += '<div class="refs"><span>' + (ch.kind === 'mem' ? '본편 카드를 바로 부르는 칸:' : '이 풀에도 들어 있으나 집이 다른 곳:') + '</span>';
    ch.refs.forEach(id => { h += '<button type="button" class="rf" data-ref="' + id + '" data-go="' + id + '">' + (ch.refslots && ch.refslots[String(id)] ? ch.refslots[String(id)] + '칸 ' : '') + pad(id) + ' → ' + esc(pageLabel(pageOfEv(id))) + '</button>'; });
    h += '</div>';
  }
  return h + '</div>';
}
function quoteAns(t){ return /^[『「]/.test(t) ? t : '『' + t + '』'; }
function viaAnswer(parent, vno){
  if (!vno) return null;
  const a = (EV[parent].ans || []).find(x => x[0] === vno);
  return a ? a[2] : null;
}
function refListHTML(rc){
  let h = '<div class="clist" data-reflist="' + rc.id + '"><h4>' + esc(rc.label) + ' · ' + esc(LANE[rc.lane] || '회상') + ' <small>참조 ' + rc.refs.length + '장 — 집은 ' + esc(rc.from.map(pageLabel).join('·')) + ' 서랍(셈에 넣지 않음)</small></h4><div class="refs">';
  rc.refs.forEach(id => {
    const e = EV[id];
    h += '<button type="button" class="rf" data-ref="' + id + '" data-pick="e:' + id + '" title="' + esc(e.when[0] + ' / ' + whoText(e)) + '">' + pad(id) + ' · ' + esc(whoText(e)) + ' (' + esc(pageLabel(e.home)) + ')</button>';
  });
  return h + '</div></div>';
}
function undatedPillHTML(c){
  return '<button type="button" class="upill t-' + c.type + selCls('c', c.key) + '"' + pillAttrs(c) + ' style="width:' + PILL_W + 'px">' + pillInner(c) + '</button>';
}
function renderLane(pk){
  const p = PAGE[pk], m = p.m, dw = dayWidth(p);
  const tw = dw * p.mlen + (PILL_W - dw) + 16;
  const lw = 96;
  let h = '<div class="ptitle"><h2>' + esc(p.label) + '</h2><span class="pn">' + pageNote(p) + '</span></div>';
  // 날짜 머리글
  h += '<div class="dayhead" style="width:' + (lw + tw) + 'px"><div class="corner">레인 · 날짜</div><div class="days" style="width:' + tw + 'px">';
  for (let d = 1; d <= p.mlen; d++){
    const w = weekdayOf(m, d), cls = (w === 6 ? ' sat' : w === 0 ? ' sun' : '') + (inCal(m, d) ? '' : ' out');
    const mk = ST.review ? D.marks.filter(x => x.m === m && x.d === d) : [];
    h += '<div class="dh' + cls + '" style="left:' + ((d - 1) * dw) + 'px;width:' + dw + 'px"' + (mk.length ? ' title="' + esc(mk.map(x => x.jp).join(' / ')) + ' (개발 시험 표 표식)"' : '') + '>' + d + '<span class="wd">' + '일월화수목금토'[w] + '</span>' + (mk.length ? '<span class="mk"></span>' : '') + '</div>';
  }
  h += '</div></div>';
  h += '<div class="lanewrap" style="width:' + (lw + tw) + 'px"><div class="cols" style="width:' + tw + 'px">';
  for (let d = 1; d <= p.mlen; d++){
    const w = weekdayOf(m, d), cls = !inCal(m, d) ? ' out' : (w === 6 ? ' sat' : w === 0 ? ' sun' : '');
    h += '<div class="col' + cls + '" style="left:' + ((d - 1) * dw) + 'px;width:' + dw + 'px"></div>';
  }
  h += '</div>';
  const lanes = D.lanes.map(l => l[0]).concat(['mem']);
  lanes.forEach(lane => {
    if (lane !== 'mem' && !ST.lanes.has(lane)) return;
    if (lane === 'mem' && !typeVisible('mem')) return;
    const cs = D.cards.filter(c => c.page === pk && c.lane === lane && cardVisible(c));
    const dated = cs.filter(c => c.pl.d !== undefined), undated = cs.filter(c => c.pl.d === undefined);
    const chips = lane === 'mem' ? [] : laneChips(pk, lane).filter(ch => typeVisible('pool'));
    const rcs = laneRefChips(pk, lane).filter(ch => typeVisible(lane === 'mem' ? 'mem' : 'pool'));
    const bands = D.bands.filter(b => b.lane === lane && typeVisible(b.type) && (b.s[0] <= m && b.f[0] >= m) && (!ST.fixOnly || EV[b.ev].fix[0] > 0));
    if (lane === 'mem' && !rcs.length) return;
    // 배치: 띠 줄 → 알약
    const bitems = bands.map(b => {
      const sd = b.s[0] < m ? 1 : b.s[1], fd = b.f[0] > m ? p.mlen : b.f[1];
      return {b: b, x: (sd - 1) * dw, w: Math.max(dw * (fd - sd + 1) - 2, 8), h: 7, cont: b.s[0] < m, more: b.f[0] > m};
    });
    const bh = bitems.length ? pack(bitems) + 6 : 0;
    const ph = pillH();
    const items = dated.map(c => {
      if (ST.expand && c.n > 1){
        const rows = c.rows.length;
        return {c: c, x: (c.pl.d - 1) * dw, w: Math.min(PILL_W * 2, tw - (c.pl.d - 1) * dw - 4), h: 26 + rows * 23, box: true};
      }
      return {c: c, x: (c.pl.d - 1) * dw, w: PILL_W, h: ph};
    });
    const hh = items.length ? pack(items) : 0;
    const body = Math.max(bh + hh + 8, 30);
    const j = joinOf(lane);
    const beforeJoin = j && (m < j[0]);
    h += '<div class="lane' + (beforeJoin ? ' dim' : '') + '" data-lane="' + lane + '">';
    const lt = lane === 'mem' ? 'mem' : (lane === 'dungeon' ? 'dungeon' : (lane === 'main' ? 'main' : 'person'));
    h += '<div class="lh"><span class="sw" style="background:var(--t-' + lt + ')"></span>' + esc(lane === 'mem' ? '회상' : LANE[lane]) + '<small>' + laneNote(pk, lane, cs, chips) + '</small></div>';
    h += '<div class="lb" style="height:' + body + 'px;width:' + tw + 'px">';
    if (j && (m < j[0] || m === j[0])){
      const upto = m < j[0] ? p.mlen : j[1] - 1;
      if (upto > 0) h += '<div class="prejoin" style="width:' + (upto * dw) + 'px">' + (m < j[0] ? '합류 전 (' + j[0] + '/' + j[1] + ' 합류)' : '합류 전') + '</div>';
    }
    bitems.forEach(it => {
      const b = it.b, e = EV[b.ev];
      const tt = pad(b.ev) + ' · ' + b.s[0] + '/' + b.s[1] + '~' + b.f[0] + '/' + b.f[1] + '\n' + e.when[0];
      h += '<button type="button" class="band t-' + b.type + (it.cont ? ' cont' : '') + '" data-band="' + b.ev + '" data-pick="' + (b.unit.startsWith('c:') ? 'c:' + b.unit.slice(2) : 'e:' + b.ev) + '" style="left:' + it.x + 'px;top:' + (it.y + 3) + 'px;width:' + it.w + 'px" title="' + esc(tt) + '" aria-label="' + esc(tt) + '"></button>';
    });
    items.forEach(it => {
      const c = it.c, y = bh + it.y + 4;
      if (it.box) h += bundleBox(c, it.x, y, it.w);
      else h += '<button type="button" class="pill t-' + c.type + selCls('c', c.key) + '"' + pillAttrs(c) + ' style="left:' + it.x + 'px;top:' + y + 'px;width:' + it.w + 'px;height:' + it.h + 'px">' + pillInner(c) + '</button>';
    });
    h += '</div>';
    // 아래 줄: 이달 중(날짜 미상) 카드 + 서랍 칩 + 참조 칩
    let foot = '';
    if (undated.length){
      foot += '<span class="fl">이달 중(날짜 미상)</span>';
      undated.forEach(c => { foot += (ST.expand && c.n > 1) ? '' : undatedPillHTML(c); });
    }
    if (chips.length || rcs.length){
      foot += '<span class="fl" style="margin-left:6px">이달의 서랍</span>';
      chips.forEach(ch => foot += chipHTML(ch));
      rcs.forEach(rc => foot += refChipHTML(rc));
    }
    h += '<div class="lf">' + foot + '</div>';
    let lists = '';
    if (ST.expand) undated.filter(c => c.n > 1).forEach(c => {
      lists += '<div class="clist" data-cardlist="' + c.key + '">' + bundleHeader(c) + bundleRows(c) + '</div>';
    });
    chips.forEach(ch => { if (ST.open.has(ch.id)) lists += chipListHTML(ch); });
    rcs.forEach(rc => { if (ST.open.has(rc.id)) lists += refListHTML(rc); });
    h += '<div class="lists">' + lists + '</div>';
    h += '</div>';
  });
  h += '</div>';
  return h;
}
function bundleHeader(c){
  return '<h4 data-card="' + c.key + '" data-fix="' + c.fix[0] + '" data-pick="c:' + c.key + '" style="cursor:pointer">' + esc(dateText(c.pl)) + ' · 묶음 ' + pad(c.entry) + ' ▸' + c.n + (c.ptag ? ' · ' + esc(c.ptag) : '') + ' ' + fixTag(c.fix[0]) + '</h4>';
}
function laneNote(pk, lane, cs, chips){
  if (lane === 'mem') return '재생본 참조';
  const n = cs.length, e = chips.reduce((a, ch) => a + ch.entries.length, 0);
  return (n ? '카드 ' + n : '') + (n && e ? ' · ' : '') + (e ? '서랍 ' + e : '') || '—';
}
function pageNote(p){
  const s = p.sum;
  if (p.key === 'mem') return '서랍 ' + s.entries + '장 · 교정 ' + s.fix + '줄 · 날짜가 없어 달력 보기가 없다';
  return '카드 ' + s.cards + '장(이달 중 ' + s.undated + ') · 서랍 ' + s.entries + '장 · 교정 ' + s.fix + '줄';
}

/* ── 달력 보기 ── */
function renderCal(pk){
  const p = PAGE[pk], m = p.m;
  let h = '<div class="ptitle"><h2>' + esc(p.label) + '</h2><span class="pn">' + pageNote(p) + '</span></div>';
  h += '<div class="calgrid">';
  '일월화수목금토'.split('').forEach((w, i) => { h += '<div class="wh' + (i === 6 ? ' sat' : i === 0 ? ' sun' : '') + '">' + w + '</div>'; });
  const w1 = weekdayOf(m, 1);
  for (let i = 0; i < w1; i++) h += '<div class="cd pad"></div>';
  const vis = D.cards.filter(c => c.page === pk && cardVisible(c) && ST.lanes.has(c.lane));
  for (let d = 1; d <= p.mlen; d++){
    const w = weekdayOf(m, d), cls = !inCal(m, d) ? ' out' : (w === 6 ? ' sat' : w === 0 ? ' sun' : '');
    const mk = ST.review ? D.marks.filter(x => x.m === m && x.d === d) : [];
    h += '<div class="cd' + cls + '" data-day="' + d + '"><div class="dn">' + d + (mk.length ? '<span class="mkx" title="개발 시험 표 표식">' + esc(mk.map(x => x.jp).join(' / ')) + '</span>' : '') + '</div>';
    vis.filter(c => c.pl.d === d).sort((a, b) => laneIdx(a.lane) - laneIdx(b.lane)).forEach(c => {
      if (ST.expand && c.n > 1){
        h += '<div class="clist" style="padding:2px 0" data-cardlist="' + c.key + '">' + bundleHeader(c) + bundleRows(c) + '</div>';
      } else {
        const e = EV[c.entry];
        h += '<button type="button" class="cchip t-' + c.type + selCls('c', c.key) + '"' + pillAttrs(c) + '><span class="l1"><b>' + pad(c.entry) + '</b>' + (c.n > 1 ? '<span class="bn">▸' + c.n + '</span>' : '') + (c.pl.m2 !== undefined ? '<span class="no">~' + c.pl.m2 + '/' + c.pl.d2 + '</span>' : '') + '<span class="ml">' + fixTag(c.fix[0]) + '</span></span><span class="l2">' + esc((LANE[c.lane] || '') + ' · ' + whoText(e)) + '</span>' + (showFirst() ? '<span class="l3">' + esc(firstText(e)) + '</span>' : '') + '</button>';
      }
    });
    D.bands.filter(b => b.s[0] === m && b.s[1] === d && !b.unit.startsWith('c:') && typeVisible(b.type) && ST.lanes.has(b.lane) && (!ST.fixOnly || EV[b.ev].fix[0] > 0)).forEach(b => {
      h += '<button type="button" class="cchip win t-pool" data-band="' + b.ev + '" data-pick="e:' + b.ev + '" title="우선 대화 창(서랍에 있다)"><span class="l1">' + pad(b.ev) + ' <span class="no">창 ~' + b.f[0] + '/' + b.f[1] + '</span></span><span class="l2">' + esc(LANE[b.lane] + ' · 우선 대화') + '</span></button>';
    });
    h += '</div>';
  }
  const tail = (7 - (w1 + p.mlen) % 7) % 7;
  for (let i = 0; i < tail; i++) h += '<div class="cd pad"></div>';
  h += '</div>';
  // 달력 아래: 레인별 이달 중 + 서랍
  h += '<div class="calfoot">';
  D.lanes.map(l => l[0]).concat(['mem']).forEach(lane => {
    if (lane !== 'mem' && !ST.lanes.has(lane)) return;
    const undated = D.cards.filter(c => c.page === pk && c.lane === lane && c.pl.d === undefined && cardVisible(c));
    const chips = lane === 'mem' ? [] : laneChips(pk, lane).filter(ch => typeVisible('pool'));
    const rcs = laneRefChips(pk, lane).filter(ch => typeVisible(lane === 'mem' ? 'mem' : 'pool'));
    if (!undated.length && !chips.length && !rcs.length) return;
    const j = joinOf(lane);
    h += '<div class="cfl" data-lane="' + lane + '"><div class="lh">' + esc(lane === 'mem' ? '회상' : LANE[lane]) + (j && m < j[0] ? '<div class="note">합류 전</div>' : '') + '</div><div>';
    let foot = '';
    if (undated.length){
      foot += '<span class="fl">이달 중(날짜 미상)</span>';
      undated.forEach(c => { foot += (ST.expand && c.n > 1) ? '' : undatedPillHTML(c); });
    }
    if (chips.length || rcs.length){
      foot += '<span class="fl" style="margin-left:6px">이달의 서랍</span>';
      chips.forEach(ch => foot += chipHTML(ch));
      rcs.forEach(rc => foot += refChipHTML(rc));
    }
    h += '<div class="lf">' + foot + '</div>';
    let lists = '';
    if (ST.expand) undated.filter(c => c.n > 1).forEach(c => { lists += '<div class="clist" data-cardlist="' + c.key + '">' + bundleHeader(c) + bundleRows(c) + '</div>'; });
    chips.forEach(ch => { if (ST.open.has(ch.id)) lists += chipListHTML(ch); });
    rcs.forEach(rc => { if (ST.open.has(rc.id)) lists += refListHTML(rc); });
    h += '<div class="lists">' + lists + '</div></div></div>';
  });
  h += '</div>';
  return h;
}
function laneIdx(l){ return D.lanes.findIndex(x => x[0] === l); }

/* ── 회상 · 그 밖 ── */
function renderMem(){
  const p = PAGE.mem;
  let h = '<div class="ptitle"><h2>' + esc(p.label) + '</h2><span class="pn">' + pageNote(p) + '</span></div>';
  h += '<div class="memgrid">';
  D.chips.filter(ch => ch.page === 'mem').forEach(ch => {
    if (!typeVisible('mem')) return;
    const vis = chipVisibleEntries(ch);
    const fx = vis.reduce((a, id) => a + EV[id].fix[0], 0);
    h += '<section class="memsec"><h3><button type="button" class="chip open" data-chip="' + ch.id + '" data-count="' + vis.length + '" data-fix="' + fx + '" data-fixed-open="1">' + esc(ch.label) + ' <b>' + vis.length + '</b>' + (fx ? ' <span class="fx">✎' + fx + '</span>' : '') + '</button><small>' + (ch.kind === 'mem' ? '회상 모드 ' + ch.label + ' · 칸 차례, 사슬로만 오는 재생본은 부모 밑' : '부르는 자리가 없는 장면(개발용으로 보인다)') + '</small></h3>';
    h += chipListHTML(ch).replace('class="clist"', 'class="clist" style="padding-left:0;border-top:0"');
    h += '</section>';
  });
  h += '</div>';
  return h;
}

/* ── 요약 띠 ── */
function renderBand(){
  let h = '';
  D.pages.forEach(p => {
    const s = p.sum, cur = p.key === ST.page;
    const segs = TYPES.filter(t => s.types[t]).map(t => '<i class="t-' + t + '" style="flex:' + s.types[t] + '" title="' + D.types[t] + ' ' + s.types[t] + '"></i>').join('');
    h += '<button type="button" class="bcell' + (cur ? ' cur' : '') + '" data-goto="' + p.key + '" data-sum-cards="' + s.cards + '" data-sum-entries="' + s.entries + '" data-sum-fix="' + s.fix + '" aria-current="' + (cur ? 'page' : 'false') + '">';
    h += '<span class="bm">' + esc(p.label) + '</span><span class="bs">' + (p.key === 'mem' ? '서랍 ' + s.entries : '카드 ' + s.cards + ' · 서랍 ' + s.entries) + '</span>';
    h += '<span class="bbar">' + segs + '</span>';
    h += '<span class="bfx">' + (s.fix ? '<span class="fx">✎ ' + s.fix + '</span>' : '<span class="fx0">✎ 0</span>') + '</span></button>';
  });
  document.getElementById('cells').innerHTML = h;
}

/* ── 필터 줄 ── */
function renderFilters(){
  let h = '<span class="lbl">인물</span>';
  D.lanes.forEach(([k, v]) => {
    const t = k === 'main' ? 'main' : k === 'dungeon' ? 'dungeon' : 'person';
    h += '<button type="button" class="tg' + (ST.lanes.has(k) ? ' on' : '') + '" data-lanef="' + k + '" aria-pressed="' + ST.lanes.has(k) + '"><span class="sw" style="background:var(--t-' + t + ')"></span>' + esc(v) + '</button>';
  });
  h += '<span class="lbl">유형</span>';
  TYPES.forEach(t => {
    h += '<button type="button" class="tg' + (ST.types.has(t) ? ' on' : '') + '" data-typef="' + t + '" aria-pressed="' + ST.types.has(t) + '"><span class="sw" style="background:var(--t-' + t + ')"></span>' + esc(D.types[t]) + '</button>';
  });
  h += '<label class="ck"><input type="checkbox" id="fFix"' + (ST.fixOnly ? ' checked' : '') + '>교정 있는 카드만</label>';
  h += '<label class="ck"><input type="checkbox" id="fExp"' + (ST.expand ? ' checked' : '') + '>묶음 펼치기</label>';
  h += '<button type="button" class="tg" id="openAll">서랍 모두 펼치기</button><button type="button" class="tg" id="closeAll">모두 접기</button>';
  document.getElementById('filters').innerHTML = h;
}

/* ── 옆 패널 ── */
function renderSide(){
  const s = document.getElementById('side');
  if (!ST.sel){ s.innerHTML = sideHelp(); return; }
  if (ST.sel.k === 'c') s.innerHTML = sideCard(CARD[ST.sel.key]);
  else s.innerHTML = sideEvent(+ST.sel.key);
}
function sideHelp(){
  const p = PAGE[ST.page];
  let h = '<h2>' + esc(p.label) + '</h2><div class="sub">' + pageNote(p) + '</div>';
  h += '<div class="k">읽는 법</div><div class="legend">';
  TYPES.forEach(t => { h += '<span class="sw" style="background:var(--t-' + t + ')"></span><span>' + esc(D.types[t]) + (t === 'pool' ? ' — 서랍(날짜 없는 장면)' : t === 'mem' ? ' — 회상 · 그 밖 쪽' : ' 카드') + '</span>'; });
  h += '<span class="fx">✎3</span><span>09-23 교정 예정 줄 수(미반입 — 본문은 지금 텍스트)</span>';
  h += '<span class="sus">△</span><span>09-17 의심(정렬·존대) — 옆 패널에만</span>';
  h += '<span class="bn">▸5</span><span>연속 이벤트 묶음(누르면 안의 단계가 옆에)</span>';
  h += '<span class="edge jump" style="padding:0">→ 7월</span><span>사슬이 다른 달로 이어진다(누르면 그 달로)</span>';
  h += '<span class="edge line" style="padding:0">↳ 이어서</span><span>같은 쪽 안 사슬</span>';
  h += '<span class="chip" style="font-size:10.5px">초대 7</span><span>이달의 서랍(집이 이 달인 장면)</span>';
  h += '<span class="chip ref" style="font-size:10.5px">초대 7 · 4월부터</span><span>참조 — 집은 다른 달 서랍(셈에 넣지 않음)</span>';
  h += '</div>';
  h += '<div class="k">조작</div><div class="v note">← → 로 달을 옮긴다. 카드·줄을 누르면 여기 자세히. 「다음 교정 있는 카드로」로 교정 줄이 있는 카드를 차례로 돈다.</div>';
  h += '<div class="btns"><button type="button" class="btn pri" data-nextfix="1">다음 교정 있는 카드로 ▶</button></div>';
  return h;
}
function badgeBlock(fix, sus){
  let h = '<div class="k">배지</div><div class="v">';
  h += fix[0] ? '<span class="fx">✎ 09-23 교정 ' + fix[0] + '건</span> <span class="note">의미 ' + fix[1] + ' · 호칭·문체·용어 ' + fix[2] + ' · 그 밖 ' + fix[3] + ' — 교정 예정(미반입)</span>' : '<span class="fx0">09-23 교정 없음</span>';
  if (sus[0] || sus[1]) h += '<br><span class="sus">△ 09-17 의심 · 정렬 ' + sus[0] + ' · 존대 ' + sus[1] + '</span>';
  return h + '</div>';
}
function chainBlock(id){
  const out = OUT[id] || [], inc = INC[id] || [];
  if (!out.length && !inc.length) return '';
  let h = '<div class="k">사슬</div><div class="v">';
  const lk = (x, to) => {
    const t = to ? x[1] : x[0];
    const pg = pageOfEv(t), here = pg === ST.page;
    return '<button type="button" class="lnk" data-go="' + t + '">' + pad(t) + '</button>' + (x[2] ? ' (답 ' + x[2] + ')' : '') + (here ? '' : ' · ' + esc(pageLabel(pg)));
  };
  if (inc.length) h += '앞: ' + inc.map(x => lk(x, false)).join(', ') + '<br>';
  if (out.length) h += '뒤: ' + out.map(x => lk(x, true)).join(', ');
  return h + '</div>';
}
function condBlock(e){
  let h = '<div class="k">발화 조건</div><ul>' + e.when.map(w => '<li>' + esc(w) + '</li>').join('') + '</ul>';
  if (e.pools && e.pools.length) h += '<div class="k">풀</div><div class="v">' + e.pools.map(esc).join('<br>') + '</div>';
  if (e.aff && e.aff.length) h += '<div class="k">친밀도 변화</div><div class="v">' + e.aff.map(a => esc((D.persons[String(a[0])] || a[0]) + ' ' + (a[1] > 0 ? '+' : '') + a[1])).join(', ') + '</div>';
  if (e.choice && e.ans.length){
    h += '<div class="k">선택지</div><ul>' + e.ans.map(a => '<li>답 ' + a[0] + (showText() ? ' ' + esc(quoteAns(a[2])) + (a[3] === 'jp' ? ' <span class="note">(원문)</span>' : '') : '') + ' → ' + (a[1] ? '<button type="button" class="lnk" data-go="' + a[1] + '">' + pad(a[1]) + '</button>' : '없음') + '</li>').join('') + '</ul>';
  }
  if (e.replay_of) h += '<div class="k">회상 재생본</div><div class="v">원본 <button type="button" class="lnk" data-go="' + e.replay_of + '">' + pad(e.replay_of) + '</button> · ' + esc(({redirect:'원본을 그대로 부른다', same_as_source:'원본과 글자가 같다', same_as_source_chain:'원본 사슬과 글자가 같다', different:'원본과 다르다'})[e.replay] || e.replay || '') + '</div>';
  return h;
}
/* r19: 게임 안 달력의 이름(E번호 대신 쓰는 것) — data-nm 이 붙은 요소만 더했다 */
function nameBlock(nm){ return nm ? '<div class="k" data-nm="k">게임 안 이름</div><div class="v" data-nm="v">' + esc(nm) + '</div>' : ''; }
function stageName(x){ return x.nk ? '<span class="note" data-nm="s">' + esc(x.nk) + '</span> ' : ''; }
function labelBlock(e){
  let h = '<div class="k">언제</div><div class="v">' + esc(e.when[0]) + (e.when.length > 1 ? ' <span class="note">외 ' + (e.when.length - 1) + '</span>' : '') + '</div>';
  h += '<div class="k">누구</div><div class="v">' + esc(whoText(e)) + (e.psrc === 'person' ? ' <span class="note">(화자 태그 없음 — 풀 인물)</span>' : '') + '</div>';
  if (showFirst()) h += '<div class="k">첫 줄</div><div class="v">' + esc(firstText(e)) + '</div>';
  return h;
}
function fixListBlock(id){
  if (!showText()) return '';
  const e = EV[id];
  if (!e.fix[0]) return '';
  const d = dlg(); if (!d) return '';
  let h = '<details><summary>교정 예정 ' + e.fix[0] + '줄 보기</summary><ul class="fixlist">';
  const rows = d.ev[String(id)];
  for (let i = 0; i < rows.length; i += 2){
    const m = e.m0 + i / 2, f = d.fix[String(m)];
    if (!f) continue;
    const cur = rows[i + 1] >= 0 ? d.strs[rows[i + 1]] : '';
    h += '<li><span class="src">m' + m + ' · ' + ['', '의미', '호칭·문체·용어', '그 밖'][f[1]] + ' · ' + esc(d.strs[f[3]]) + '</span><br><span class="cur">' + esc(cur) + '</span><br>→ ' + esc(d.strs[f[0]]) + (d.strs[f[2]] ? '<br><span class="src">' + esc(d.strs[f[2]]) + '</span>' : '') + '</li>';
  }
  return h + '</ul></details>';
}
function dialogueBlock(id){
  if (!showText()) return '<div class="k">대사 전문</div><div class="v note">플레이 보기에서는 넣지 않는다.</div>';
  const e = EV[id];
  if (!e.lines) return '<div class="k">대사 전문</div><div class="v note">대사가 없는 장면이다.</div>';
  return '<details data-dlg="' + id + '"><summary>대사 전문 ' + e.lines + '줄 (원문 · 한국어)</summary><label class="ck" style="margin:4px 0 0"><input type="checkbox" data-dlgfix="' + id + '">교정 있는 줄만</label><div class="dlgbody"></div></details>';
}
function dialogueTable(id, fixOnly){
  const d = dlg(), e = EV[id], rows = d.ev[String(id)];
  let h = '<table class="dl"><tbody>';
  for (let i = 0; i < rows.length; i += 2){
    const a = rows[i], b = rows[i + 1], m = e.m0 + i / 2;
    const f = d.fix[String(m)];
    if (fixOnly && !f) continue;
    if (a < 0){ h += '<tr class="sp"><td>' + esc(d.strs[b]) + '</td><td>' + esc(d.strs[-a - 1]) + '</td></tr>'; continue; }
    const kr = b >= 0 ? d.strs[b] : null;
    h += '<tr data-m="' + m + '"><td class="jp">' + esc(d.strs[a]) + '</td><td class="kr' + (kr === null ? ' raw' : kr === '' ? ' nil' : '') + '">' + (kr === null ? esc(d.strs[a]) : kr === '' ? '(빈 줄)' : esc(kr)) + '</td></tr>';
    if (f) h += '<tr class="fixr"><td colspan="2">✎ 교정 예정(' + ['', '의미', '호칭·문체·용어', '그 밖'][f[1]] + ') → ' + esc(d.strs[f[0]]) + '</td></tr>';
  }
  return h + '</tbody></table>';
}
function sideEvent(id){
  const e = EV[id], c = cardOfEv(id), ch = chipOfEv(id), t = typeOfEv(id);
  let h = '<h2><span class="sw" style="display:inline-block;width:3px;height:14px;border-radius:2px;background:var(--t-' + t + ')"></span>' + pad(id) + ' <span class="note">' + esc(D.types[t]) + '</span></h2>';
  let where = '';
  if (c) where = (c.n > 1 ? '묶음 <button type="button" class="lnk" data-pickc="' + c.key + '">' + pad(c.entry) + ' ▸' + c.n + '</button> 안' : '카드') + ' · ' + esc(pageLabel(c.page)) + ' · ' + esc(LANE[c.lane]);
  else where = '서랍 「' + esc(ch.label) + '」 · ' + esc(pageLabel(ch.page)) + (LANE[ch.lane] ? ' · ' + esc(LANE[ch.lane]) : '');
  h += '<div class="sub">' + where + ' · ' + e.lines + '줄' + (e.voice ? ' · 음성' : '') + (e.battle ? ' · 전투' : '') + '</div>';
  h += nameBlock(e.nm);
  h += labelBlock(e) + badgeBlock(e.fix, e.sus) + condBlock(e) + chainBlock(id);
  h += '<div class="k">엔진 함수</div><div class="v note">' + esc(e.fn) + '</div>';
  h += fixListBlock(id) + dialogueBlock(id);
  h += '<div class="btns"><button type="button" class="btn" data-goto-home="' + id + '">' + esc(pageLabel(e.home)) + '에서 보기</button><button type="button" class="btn pri" data-nextfix="1">다음 교정 있는 카드로 ▶</button></div>';
  return h;
}
function sideCard(c){
  const e = EV[c.entry];
  let h = '<h2><span class="sw" style="display:inline-block;width:3px;height:14px;border-radius:2px;background:var(--t-' + c.type + ')"></span>' + pad(c.entry) + (c.n > 1 ? ' <span class="bn">▸' + c.n + '</span>' : '') + ' <span class="note">' + esc(D.types[c.type]) + (c.ptag ? ' · ' + esc(c.ptag) : '') + '</span></h2>';
  h += '<div class="sub">' + esc(pageLabel(c.page)) + ' · ' + esc(LANE[c.lane]) + ' · ' + esc(dateText(c.pl)) + ' · ' + c.lines + '줄' + (c.n > 1 ? ' · ' + c.n + '단계' + (c.branches ? ' · 갈래 ' + c.branches : '') : '') + '</div>';
  h += nameBlock(c.nm);
  h += labelBlock(e) + badgeBlock(c.fix, c.sus);
  if (c.n > 1){
    h += '<div class="k">묶음 단계 (눌러서 고르기)' + (c.entry_more ? ' · 진입 ' + (c.entry_more + 1) + '곳' : '') + '</div><div class="mtree">';
    c.rows.forEach(r => {
      const [id, dep, vk, vno, vtext, shared, counts, parent] = r;
      const x = EV[id];
      const via = parent == null ? '' : (vno ? '답 ' + vno + (showText() && vtext ? ' ' + esc(quoteAns(vtext)) : '') + ' ' : '↳ ');
      h += '<div class="mrow' + (counts ? '' : ' rep') + '" style="--d:' + dep + '"><span class="note">' + via + '</span><button type="button" data-pick="e:' + id + '"><span class="rid">' + pad(id) + '</span> ' + stageName(x) + '<span class="w">' + esc(x.when[0]) + '</span> ' + fixTag(x.fix[0]) + (counts ? '' : ' <span class="note">공유</span>') + '</button></div>';
    });
    h += '</div>';
    h += condBlock(e) + chainBlock(c.entry);
  } else {
    h += condBlock(e) + chainBlock(c.entry);
    h += '<div class="k">엔진 함수</div><div class="v note">' + esc(e.fn) + '</div>';
    h += fixListBlock(c.entry) + dialogueBlock(c.entry);
  }
  h += '<div class="btns">' + (c.page !== ST.page ? '<button type="button" class="btn" data-pickc="' + c.key + '">' + esc(pageLabel(c.page)) + '에서 보기</button>' : '') + '<button type="button" class="btn pri" data-nextfix="1">다음 교정 있는 카드로 ▶</button></div>';
  return h;
}

/* ── 차례(다음 교정) ── */
let ORDER = null;
function unitOrder(){
  if (ORDER) return ORDER;
  const o = [];
  D.pages.forEach(p => {
    D.cards.filter(c => c.page === p.key).sort((a, b) => ((a.pl.d || 99) - (b.pl.d || 99)) || (laneIdx(a.lane) - laneIdx(b.lane)) || (a.entry - b.entry)).forEach(c => o.push({k: 'c', key: c.key, fix: c.fix[0], page: p.key}));
    D.chips.filter(ch => ch.page === p.key).sort((a, b) => (laneIdx(a.lane) - laneIdx(b.lane))).forEach(ch => ch.order.forEach(r => { if (r[4]) o.push({k: 'e', key: r[0], fix: EV[r[0]].fix[0], page: p.key}); }));
  });
  ORDER = o; return o;
}
function nextFix(){
  const o = unitOrder();
  let i = -1;
  if (ST.sel){
    if (ST.sel.k === 'c') i = o.findIndex(u => u.k === 'c' && u.key === ST.sel.key);
    else {
      const c = cardOfEv(+ST.sel.key);
      i = c ? o.findIndex(u => u.k === 'c' && u.key === c.key) : o.findIndex(u => u.k === 'e' && u.key === +ST.sel.key);
    }
  } else {
    i = o.findIndex(u => u.page === ST.page) - 1;
  }
  for (let s = 1; s <= o.length; s++){
    const u = o[(i + s + o.length) % o.length];
    if (u.fix > 0){ goUnit(u); return; }
  }
}
function goUnit(u){
  if (u.k === 'c') focusCard(u.key);
  else focusEv(u.key, true);
}

/* ── 이동 ── */
function focusCard(key){
  const c = CARD[key];
  ST.page = c.page; ST.sel = {k: 'c', key: key}; ST.flash = '[data-card="' + key + '"]';
  renderAll();
}
function focusEv(id, sel){
  id = +id;
  const c = cardOfEv(id), ch = chipOfEv(id);
  ST.page = EV[id].home;
  if (ch) ST.open.add(ch.id);
  ST.sel = sel === false ? ST.sel : {k: 'e', key: id};
  ST.flash = c ? (ST.expand ? '[data-ev="' + id + '"]' : '[data-card="' + c.key + '"]') : '[data-ev="' + id + '"]';
  renderAll();
}
function gotoPage(k){ if (!PAGE[k]) return; ST.page = k; renderAll(); document.getElementById('scroller').scrollTop = 0; }
function stepPage(dx){ const ks = D.pages.map(p => p.key); const i = ks.indexOf(ST.page); gotoPage(ks[Math.max(0, Math.min(ks.length - 1, i + dx))]); }

/* ── 그리기 ── */
function renderPage(){
  const el = document.getElementById('page');
  let h;
  if (ST.page === 'mem') h = renderMem();
  else h = (ST.view === 'cal') ? renderCal(ST.page) : renderLane(ST.page);
  el.innerHTML = h;
  el.setAttribute('data-page', ST.page);
  el.setAttribute('data-view', ST.page === 'mem' ? 'mem' : ST.view);
  el.setAttribute('data-mode', ST.review ? 'review' : 'play');
}
function renderWarn(){
  const w = document.getElementById('warn');
  if (ST.review){ w.className = 'rv'; w.textContent = '검수 보기 — 아직 안 본 장면의 첫 줄·대사 전문·선택지 문구가 보입니다. 플레이 중이면 「플레이 보기」로 바꾸세요.'; }
  else { w.className = 'pl'; w.textContent = '플레이 보기 — 첫 줄·대사 전문·선택지 문구·교정 문안은 화면에 넣지 않습니다(라벨은 언제·누구만).'; }
  document.getElementById('mReview').classList.toggle('on', ST.review);
  document.getElementById('mPlay').classList.toggle('on', !ST.review);
  document.getElementById('vLane').classList.toggle('on', ST.view === 'lane');
  document.getElementById('vCal').classList.toggle('on', ST.view === 'cal');
}
function renderAll(){
  renderWarn(); renderFilters(); renderBand(); renderPage(); renderSide();
  if (ST.flash && !ST.selftest){
    const el = document.querySelector('#page ' + ST.flash);
    if (el){ el.scrollIntoView({block: 'center', inline: 'center'}); el.classList.add('flash'); }
  }
  ST.flash = null;
}

/* ── 사건 연결 ── */
function onClick(ev){
  const t = ev.target.closest('[data-pick],[data-go],[data-goto],[data-chip],[data-refchip],[data-lanef],[data-typef],[data-nextfix],[data-pickc],[data-goto-home],#openAll,#closeAll,#prev,#next,#mReview,#mPlay,#vLane,#vCal,#qGo');
  if (!t) return;
  if (t.id === 'prev') return stepPage(-1);
  if (t.id === 'next') return stepPage(1);
  if (t.id === 'mReview'){ if (!ST.review && confirm('검수 보기로 바꾸면 아직 안 본 장면의 첫 줄·대사 전문이 보입니다. 바꿀까요?')) setMode(true); return; }
  if (t.id === 'mPlay'){ setMode(false); return; }
  if (t.id === 'vLane'){ ST.view = 'lane'; savePrefs(); return renderAll(); }
  if (t.id === 'vCal'){ ST.view = 'cal'; savePrefs(); return renderAll(); }
  if (t.id === 'qGo') return doFind();
  if (t.id === 'openAll'){ D.chips.concat(D.refchips).forEach(c => { if (c.page === ST.page) ST.open.add(c.id); }); return renderAll(); }
  if (t.id === 'closeAll'){ ST.open.clear(); ST.expand = false; return renderAll(); }
  if (t.dataset.goto) return gotoPage(t.dataset.goto);
  if (t.dataset.lanef){ const k = t.dataset.lanef; if (ST.lanes.has(k)) ST.lanes.delete(k); else ST.lanes.add(k); return renderAll(); }
  if (t.dataset.typef){ const k = t.dataset.typef; if (ST.types.has(k)) ST.types.delete(k); else ST.types.add(k); return renderAll(); }
  if (t.dataset.nextfix) return nextFix();
  if (t.dataset.pickc) return focusCard(t.dataset.pickc);
  if (t.dataset.gotoHome) return focusEv(+t.dataset.gotoHome, true);
  if (t.dataset.chip){ if (t.dataset.fixedOpen) return; const k = t.dataset.chip; if (ST.open.has(k)) ST.open.delete(k); else ST.open.add(k); return renderAll(); }
  if (t.dataset.refchip){ const k = t.dataset.refchip; if (ST.open.has(k)) ST.open.delete(k); else ST.open.add(k); return renderAll(); }
  if (t.dataset.go){ ev.stopPropagation(); return focusEv(+t.dataset.go, true); }
  if (t.dataset.pick){
    const [k, key] = t.dataset.pick.split(':');
    ST.sel = {k: k, key: k === 'c' ? key : +key};
    renderPage(); renderSide();
    return;
  }
}
function setMode(review){
  ST.review = review;
  renderAll();
}
function doFind(){
  const v = document.getElementById('q').value.trim().replace(/^E/i, '');
  const id = parseInt(v, 10);
  if (!EV[id]){ document.getElementById('foot').textContent = '없는 번호: ' + v; return; }
  focusEv(id, true);
}
document.addEventListener('click', onClick);
document.addEventListener('change', ev => {
  const t = ev.target;
  if (t.id === 'fFix'){ ST.fixOnly = t.checked; return renderAll(); }
  if (t.id === 'fExp'){ ST.expand = t.checked; return renderAll(); }
  if (t.dataset && t.dataset.dlgfix){ const box = t.closest('details').querySelector('.dlgbody'); box.innerHTML = dialogueTable(+t.dataset.dlgfix, t.checked); }
});
document.addEventListener('toggle', ev => {
  const t = ev.target;
  if (t.tagName === 'DETAILS' && t.dataset.dlg && t.open){
    const box = t.querySelector('.dlgbody');
    if (box && !box.innerHTML && showText()) box.innerHTML = dialogueTable(+t.dataset.dlg, false);
  }
}, true);
document.addEventListener('keydown', ev => {
  if (ev.target && (ev.target.tagName === 'INPUT' || ev.target.tagName === 'TEXTAREA')){
    if (ev.key === 'Enter' && ev.target.id === 'q') doFind();
    return;
  }
  if (ev.key === 'ArrowLeft'){ stepPage(-1); ev.preventDefault(); }
  else if (ev.key === 'ArrowRight'){ stepPage(1); ev.preventDefault(); }
});
let rsz = null;
window.addEventListener('resize', () => { clearTimeout(rsz); rsz = setTimeout(() => { if (ST.view === 'lane') renderPage(); }, 150); });

/* ── 자체 시험(#selftest=review|play) — 쪽·상태마다 실제 DOM 을 떠서 적는다. 셈은 밖(stage_v2.py)에서 한다 ── */
function selfTest(mode){
  ST.selftest = true;
  const out = {schema: D.schema, mode: mode, states: [], panels: []};
  const pages = D.pages.map(p => p.key);
  const snap = (state) => out.states.push({state: state, page: ST.page, view: document.getElementById('page').getAttribute('data-view'),
      html: document.getElementById('page').outerHTML, band: document.getElementById('band').outerHTML});
  const openAll = () => { ST.open = new Set(D.chips.map(c => c.id).concat(D.refchips.map(c => c.id))); };
  ST.review = (mode !== 'play');
  if (mode === 'play'){
    // 처음 연 상태(아무 것도 안 누름)
    renderAll(); out.initial = document.body.outerHTML;
  }
  ['lane', 'cal'].forEach(view => {
    ST.view = view;
    ST.expand = false; ST.open = new Set();
    pages.forEach(k => { ST.page = k; renderAll(); snap(view + ':fold:closed'); });
    openAll();
    pages.forEach(k => { ST.page = k; renderAll(); snap(view + ':fold:open'); });
    ST.expand = true;
    pages.forEach(k => { ST.page = k; renderAll(); snap(view + ':exp:open'); });
  });
  if (mode === 'play'){
    // 모든 카드·사건의 옆 패널(펼칠 수 있는 곳은 다 펼친다)
    const panel = () => {
      const s = document.getElementById('side');
      s.querySelectorAll('details').forEach(d => { d.open = true; const b = d.querySelector('.dlgbody'); if (b && !b.innerHTML && showText()) b.innerHTML = dialogueTable(+d.dataset.dlg, false); });
      return s.innerHTML;
    };
    D.cards.forEach(c => { ST.sel = {k: 'c', key: c.key}; renderSide(); out.panels.push(panel()); });
    Object.keys(EV).forEach(id => { ST.sel = {k: 'e', key: +id}; renderSide(); out.panels.push(panel()); });
    // 검수 보기로 갔다가(전문을 펼침) 다시 플레이 보기 — 남는 것이 없어야 한다
    ST.review = true; ST.page = '4'; ST.view = 'lane'; ST.sel = {k: 'c', key: D.cards[0].key}; renderAll();
    const s = document.getElementById('side'); s.querySelectorAll('details').forEach(d => { d.open = true; const b = d.querySelector('.dlgbody'); if (b) b.innerHTML = dialogueTable(+d.dataset.dlg, false); });
    setMode(false);
    out.after_switch = document.body.outerHTML;
  }
  ST.selftest = false;
  document.getElementById('selftest-out').textContent = JSON.stringify(out);
}

/* ── 시작 ── */
function init(){
  document.getElementById('hdr').textContent = '사건 ' + D.counts.events + ' · 카드 ' + D.counts.cards + ' · 서랍 ' + D.counts.drawer + ' · 09-23 교정 ' + D.counts.fix_in_events + '줄 · 만든 날 ' + D.generated;
  document.getElementById('foot').textContent = '단일 파일 · 외부 요청 없음 · 자료: graph/schedule·groups·labels·lines_kr, 교정: final_map_20260923.jsonl(읽기 전용) · AIN ' + D.ain + ' · 주소 끝에 #play 를 붙이면 플레이 보기로 열린다';
  const hs = location.hash.replace(/^#/, '');
  const hp = {}; hs.split('&').forEach(kv => { if (!kv) return; const i = kv.indexOf('='); hp[i < 0 ? kv : kv.slice(0, i)] = i < 0 ? '1' : decodeURIComponent(kv.slice(i + 1)); });
  if (hp.play || hp.mode === 'play') ST.review = false;
  if (hp.m && PAGE[hp.m]) ST.page = hp.m;
  if (hp.view === 'cal' || hp.view === 'lane') ST.view = hp.view;
  if (hp.expand) ST.expand = true;
  if (hp.open) D.chips.concat(D.refchips).forEach(c => { if (c.page === ST.page) ST.open.add(c.id); });
  if (hp.sel){ const id = parseInt(hp.sel.replace(/^E/i, ''), 10); if (EV[id]){ ST.sel = {k: 'e', key: id}; } else if (CARD[hp.sel]) ST.sel = {k: 'c', key: hp.sel}; }
  if (hp.selftest){ selfTest(hp.selftest); }
  else {
    renderAll();
    if (hp.dlg && ST.review){      // #sel=E00022&dlg=1 — 그 장면의 대사 전문을 펼친 채로 연다
      document.querySelectorAll('#side details').forEach(d => { d.open = true; const b = d.querySelector('.dlgbody'); if (b && !b.innerHTML) b.innerHTML = dialogueTable(+d.dataset.dlg, false); });
    }
  }
  document.body.setAttribute('data-ready', '1');
}
init();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    build(a.out)
