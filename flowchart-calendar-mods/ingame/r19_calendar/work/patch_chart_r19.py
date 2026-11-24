"""r19 (Claude Opus 5.5, 2026-09-27): patch chart/build_chart_v2.py (the PC chart v2 builder, also the in-game calendar's
data source) with
  1. rule 11: affinity conditions (schedule.json triggers' new `feeling_gate`) written as 「<인물> 친밀도 v 이상 / 미만」
     in the 「언제」 labels (after-training priority talks gain the person; E30152 / E10501 branches gain the condition)
  2. the shared name function event_names(): the in-game calendar's names (rules 1-10 of the r19 requirement) stored in
     the data as ev[*].nm / ns / nr / nk and cards[*].nm / tail / ref - the in-game build reads these (same function)
  3. the template: the PC chart shows the in-game name in the side panel (elements marked data-nm, nothing else changes)
Run once; asserts that every anchor exists exactly once.
"""
from pathlib import Path

P = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\chart\build_chart_v2.py')
src = P.read_text(encoding='utf-8')
assert 'event_names' not in src, 'already patched'


def rep(old, new, count=1):
    global src
    assert src.count(old) == count, (old[:90], src.count(old))
    src = src.replace(old, new)


# ---------------------------------------------------------------- 1 + 2: functions before build()
rep('def pad(i):\n    return "E%05d" % i\n\n\ndef build(out_path):\n',
    'def pad(i):\n    return "E%05d" % i\n\n\n' + r'''# ── r19: 친밀도 조건(규칙 11) ──────────────────────────────────────────
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
        for k, c in enumerate(sorted(cs, key=lambda x: x["entry"]), start=1):
            if len(cs) < 2:
                c["tail"] = ""
                continue
            who = companion(c["entry"])
            c["tail"] = (josa_wa(who) + " " if who else ("혼자 " if alone(c["entry"]) else "")) + "%d" % k
    for c in cards:
        when, ctype, dp = c["_when"], c["_type"], c["_dp"]
        parts = [when, ctype] + ([dp[0]] + ([dp[1]] if dp[1] else []) if dp else []) + ([c["tail"]] if c["tail"] else [])
        c["nm"] = " · ".join(parts + (["%d단계" % c["n"]] if c["n"] > 1 else []))
        if len(c["nm"]) > NAME_LIMIT:
            raise SystemExit("카드 이름이 한 줄을 넘는다: %s" % c["nm"])
        lane = c["lane"]
        short_lane = "본편" if lane == "main" else ("" if lane == "dungeon" else lane_label[lane])
        ref = [when, short_lane] if not dp else [dp[0]] + ([dp[1]] if dp[1] else [])
        c["ref"] = " ".join(x for x in ref + ([c["tail"]] if c["tail"] else []) if x)
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
                    short = sd or ("혼자" if alone(no) else ("이어서" if r[1] > 0 else ""))
                E[no]["ns"] = ("%d. " % k + short).strip()
                base = [(c["_when"], None), (c["_type"], 5)] + ([(c["_dp"][0], None)] if c["_dp"] else []) \
                    + ([(c["tail"], None)] if c["tail"] else [])
                E[no]["nm"] = fit(base + stage, [1, 2, 3, 5])
                E[no]["nr"] = c["ref"] + " " + first
            else:
                E[no]["ns"] = "1. " + (josa_wa(who) if who else "")
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
                E[no].update(ns="%d번째" % k, nm=" · ".join([month, lane_label[lane], nm]), nr=lane_label[lane] + " " + nm)
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
                             nr=lane_label[lane] + " " + nm)
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
    dup = [k for k, n in collections.Counter(x["nm"] for x in E.values()).items() if n > 1]
    if dup:
        raise SystemExit("장면 이름이 겹친다: %s" % dup[:5])
    for c in cards:
        ss = [E[r[0]]["ns"] for r in c["rows"] if r[6]]
        if len(ss) != len(set(ss)):
            raise SystemExit("단계 목록 줄이 겹친다: %s" % c["key"])
    for ch in chips:
        ss = [E[n]["ns"] for n in ch["entries"]]
        if len(ss) != len(set(ss)):
            raise SystemExit("서랍 장면 목록 줄이 겹친다: %s" % ch["id"])
    for c in cards:
        for k in ("_when", "_type", "_dp", "_head0"):
            del c[k]
    return E, cards


def build(out_path):
''')

# ---------------------------------------------------------------- when labels: rule 11
rep('        when = V1.when_texts(e, persons, dungeons)\n',
    '        when = when_with_feeling(e, persons, dungeons)          # r19 규칙 11: 친밀도 조건\n')

# ---------------------------------------------------------------- names into the data
rep('    persons_out = {k: v for k, v in persons.items()}\n    data = {\n',
    '    event_names(E, cards, list(chips.values()), ev, persons, lane_label, cardlab, dungeons)     # r19 이름\n'
    '    persons_out = {k: v for k, v in persons.items()}\n    data = {\n')

# ---------------------------------------------------------------- template: side panel shows the in-game name
rep('''  h += '<div class="sub">' + where + ' · ' + e.lines + '줄' + (e.voice ? ' · 음성' : '') + (e.battle ? ' · 전투' : '') + '</div>';
  h += labelBlock(e) + badgeBlock(e.fix, e.sus) + condBlock(e) + chainBlock(id);''',
    '''  h += '<div class="sub">' + where + ' · ' + e.lines + '줄' + (e.voice ? ' · 음성' : '') + (e.battle ? ' · 전투' : '') + '</div>';
  h += nameBlock(e.nm);
  h += labelBlock(e) + badgeBlock(e.fix, e.sus) + condBlock(e) + chainBlock(id);''')
rep('''  h += '<div class="sub">' + esc(pageLabel(c.page)) + ' · ' + esc(LANE[c.lane]) + ' · ' + esc(dateText(c.pl)) + ' · ' + c.lines + '줄' + (c.n > 1 ? ' · ' + c.n + '단계' + (c.branches ? ' · 갈래 ' + c.branches : '') : '') + '</div>';
  h += labelBlock(e) + badgeBlock(c.fix, c.sus);''',
    '''  h += '<div class="sub">' + esc(pageLabel(c.page)) + ' · ' + esc(LANE[c.lane]) + ' · ' + esc(dateText(c.pl)) + ' · ' + c.lines + '줄' + (c.n > 1 ? ' · ' + c.n + '단계' + (c.branches ? ' · 갈래 ' + c.branches : '') : '') + '</div>';
  h += nameBlock(c.nm);
  h += labelBlock(e) + badgeBlock(c.fix, c.sus);''')
rep('''      h += '<div class="mrow' + (counts ? '' : ' rep') + '" style="--d:' + dep + '"><span class="note">' + via + '</span><button type="button" data-pick="e:' + id + '"><span class="rid">' + pad(id) + '</span> <span class="w">' + esc(x.when[0]) + '</span> ' + fixTag(x.fix[0]) + (counts ? '' : ' <span class="note">공유</span>') + '</button></div>';''',
    '''      h += '<div class="mrow' + (counts ? '' : ' rep') + '" style="--d:' + dep + '"><span class="note">' + via + '</span><button type="button" data-pick="e:' + id + '"><span class="rid">' + pad(id) + '</span> ' + stageName(x) + '<span class="w">' + esc(x.when[0]) + '</span> ' + fixTag(x.fix[0]) + (counts ? '' : ' <span class="note">공유</span>') + '</button></div>';''')
rep('''function labelBlock(e){''',
    '''/* r19: 게임 안 달력의 이름(E번호 대신 쓰는 것) — data-nm 이 붙은 요소만 더했다 */
function nameBlock(nm){ return nm ? '<div class="k" data-nm="k">게임 안 이름</div><div class="v" data-nm="v">' + esc(nm) + '</div>' : ''; }
function stageName(x){ return x.nk ? '<span class="note" data-nm="s">' + esc(x.nk) + '</span> ' : ''; }
function labelBlock(e){''')

P.write_text(src, encoding='utf-8', newline='\n')
print('patched', P)
