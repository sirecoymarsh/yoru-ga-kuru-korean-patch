#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`graph/*.json` 에서 단독 HTML 차트와 방문 순서 목록을 만든다.

손으로 HTML 을 고치지 않는다 — 언제나 이 스크립트가 만든다.
카드 라벨(언제·누구·첫 줄)은 **기계로** 만든다. 줄거리를 읽고 요약하지 않는다.
대사 전문은 크기 때문에 `chart/dialogue_kr.json` 으로 따로 낸다(검수 보기에서 불러 읽는다).

  python build_chart.py
"""
import sys, os, io, json, re, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
GRAPH = os.path.join(BASE, "graph")

LANES = [
    ("main", "본편"),
    ("p2", "이즈미"),
    ("p3", "쿄카"),
    ("p4", "마나미"),
    ("p5", "마코토"),
    ("p6", "신카이"),
    ("p7", "호시카와"),
    ("p8", "모모세"),
    ("dungeon", "던전"),
    ("memory", "회상"),
    ("etc", "그 밖"),
]

MONTHS = [4, 5, 6, 7, 8, 9, 10, 11]

# 묶음 카드로 접어 둘 범주(설계: 풀 3종 + 특훈 뒤 우선)
FOLDED = {"after_training", "training_invite", "dungeon_walk", "after_training_priority"}


def load(name):
    with io.open(os.path.join(GRAPH, name), encoding="utf-8") as fp:
        return json.load(fp)


def lane_of(e):
    cat, p = e["category"], e["person"]
    if cat == "memory_replay":
        return "memory"
    if cat == "dungeon_walk":
        return "dungeon"
    if cat in ("after_training", "after_training_priority", "training_invite") and p:
        return "p%d" % p
    if cat == "main":
        fam = e["id"] // 10000
        if fam in (1, 2, 3, 4):
            return "p%d" % (fam + 1)
        return "main"
    if cat == "system":
        return "etc"
    return "etc"


def month_of(e):
    dates = []
    for t in e["triggers"]:
        d = t.get("date")
        if d and d[0]:
            dates.append(tuple(d))
        d = t.get("date_from")
        if d:
            dates.append(tuple(d))
        if t["kind"] == "pool" and t.get("month"):
            dates.append((t["month"], 0))
        ce = t.get("condition_expr") or ""
        for tok in ("IsTodayOrAfter(", "IsDay("):
            i = ce.find(tok)
            if i >= 0:
                try:
                    a = ce[i + len(tok):].split(")")[0].split(",")
                    dates.append((int(a[0]), int(a[1])))
                except Exception:
                    pass
    if dates:
        return min(dates)
    mr = e.get("month_range")
    if mr and mr[0] and 4 <= mr[0] <= 11:
        return (mr[0], 0)
    return None


def slot_name(t):
    return {1: "아침", 2: "밤", 3: "낮", 4: "저녁", None: ""}.get(t, "시간대%s" % t)


def dungeon_label(src, dungeons):
    d = dungeons.get(src)
    if not d:
        m = re.match(r"^L_DungeonManager::RunEventDungeonEnding(.*)$", src)
        if m:
            return "최종장 · " + m.group(1)
        if src == "C_SceneDungeon@CheckEventOnEnter":
            return "던전에 들어갈 때"
        return "던전"
    nm = d.get("kr") or d.get("jp")
    return "던전 · " + nm + (" 일대" if d.get("group") else "")


def pool_kr(kind, p1, p2, month, persons):
    a = persons.get(str(p1), persons.get(p1, ""))
    b = persons.get(str(p2), persons.get(p2, ""))
    if kind == "after_training":
        return "%s · %d월 · 특훈 뒤 잡담" % (a, month) if month else "%s · 특훈 뒤 잡담" % a
    if kind == "after_training_turned":
        return "%s · 특훈 뒤 잡담(루트 확정 뒤)" % a
    if kind == "training_invite":
        return "%s · 특훈 권유" % a
    if kind == "dungeon_first":
        return "%s · 첫 던전 동행" % a
    if kind == "dungeon_walk":
        return "던전 안 잡담 · %s%s" % (a, " / " + b if b else "")
    return kind or ""


def plain_cond(expr, self_id=None):
    """유사코드 조건식을 쉬운 한국어로. 못 읽는 조각은 그대로 둔다(지어내지 않는다).

    조사는 붙이지 않는다 — 번호 뒤 은/는·을/를은 읽는 법에 따라 갈려 글자로 박으면 틀린다."""
    parts = []
    for m in re.finditer(r"(!\()?(L_Calendar::IsTodayOrAfter|L_Calendar::IsTodayOrBefore|"
                         r"L_Calendar::IsDay)\((\d+), (\d+)\)", expr):
        neg, fn, a, b = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        word = {"L_Calendar::IsTodayOrAfter": "%d/%d 부터",
                "L_Calendar::IsTodayOrBefore": "%d/%d 까지",
                "L_Calendar::IsDay": "%d/%d 에만"}[fn] % (a, b)
        parts.append(("아닐 때: " if neg else "") + word)
    for m in re.finditer(r"C_Ability@GetFeeling\(\) >= (\d+)", expr):
        parts.append("친밀도 %s 이상" % m.group(1))
    for m in re.finditer(r"(!\()?LEventFlag::GetOnce\(\"E(\d+)\"\)", expr):
        num = int(m.group(2))
        if self_id is not None and num == self_id:
            continue
        parts.append(("아직 E%05d 안 봤을 때" if m.group(1) else "E%05d 본 뒤") % num)
    if "IsTurning()" in expr:
        parts.append("그 인물 루트가 정해진 뒤")
    for m in re.finditer(r"nAlpha[^<]*< (\d+)", expr):
        parts.append("무작위 %s%%" % m.group(1))
    return " · ".join(parts) if parts else expr


def guard_date(guards):
    """`(m_nMonth == 11) && (m_nDay == 13) && (m_nTimeID == 1)` 꼴 가드에서 날짜를 꺼낸다."""
    for g in guards:
        if g.startswith("!("):
            continue
        mm = re.search(r"m_nMonth == (\d+)", g)
        dd = re.search(r"m_nDay == (\d+)", g)
        tt = re.search(r"m_nTimeID == (\d+)", g)
        if mm and dd:
            return [int(mm.group(1)), int(dd.group(1))], int(tt.group(1)) if tt else None
    return None, None


SPECIAL_SRC = {
    "呼出／オープニング": "게임 시작 (4/9)",
    "呼出／デパート実行": "특별한 날 5/15",
    "呼出／ライブハウス実行": "특별한 날 7/23",
    "呼出／洋館実行": "특별한 날 10/21",
    "残時間終わり処理／日曜": "일요일 시간이 다 됐을 때",
}

# 대표값으로 앞에 세울 차례. 회상 재생본에서 이어지는 사슬은 맨 뒤로 민다.
WHEN_ORDER = {"scheduled": 0, "conditional": 1, "scheduled_special": 2, "special_day": 3,
              "after_training_priority": 4, "invitation": 5, "pool": 6, "dungeon": 7,
              "other": 8, "chained": 9, "memory_replay": 10}


def when_texts(e, persons, dungeons):
    """카드의 「언제」 줄. 첫 번째가 대표값이다."""
    out = []
    trigs = sorted(e["triggers"], key=lambda t: (
        WHEN_ORDER.get(t["kind"], 8),
        1 if (t["kind"] == "chained" and 50000 <= (t.get("from") or 0) < 60000) else 0))
    for t in trigs:
        k = t["kind"]
        if k == "scheduled":
            out.append("%d/%d · %s" % (t["date"][0], t["date"][1], slot_name(t["time_id"])))
        elif k == "conditional":
            a = t["raw_args"]
            s = []
            if a[0] != -1 and (a[0], a[1]) == (a[2], a[3]):
                s.append("%d/%d 하루만" % (a[0], a[1]))
            else:
                if a[0] != -1:
                    s.append("%d/%d 부터" % (a[0], a[1]))
                if a[2] != -1:
                    s.append("%d/%d 까지" % (a[2], a[3]))
            s.append(slot_name(a[4]))
            if a[5] > 0 and a[6] >= 0:
                s.append("%s 친밀도 %d 이상" % (persons.get(str(a[5]), a[5]), a[6]))
            if a[7] >= 0:
                s.append("E%05d 본 뒤" % a[7])
            out.append(" · ".join(x for x in s if x))
        elif k == "scheduled_special":
            d = t.get("date")
            if not (d and d[0]):
                d, ti = guard_date(t.get("guards") or [])
            else:
                ti = t.get("time_id")
            bits = ["%d/%d" % (d[0], d[1])] if d and d[0] else []
            if slot_name(ti):
                bits.append(slot_name(ti))
            bits.append("갈래")
            out.append(" · ".join(bits) if bits else "특수 갈래")
        elif k == "special_day":
            d = t.get("date")
            if d:
                out.append("특별한 날 %d/%d" % (d[0], d[1]))
            else:
                out.append(SPECIAL_SRC.get(t.get("source"), "특별한 날"))
        elif k == "dungeon":
            out.append(dungeon_label(t["source"], dungeons))
        elif k == "pool":
            out.append(pool_kr(t.get("pool_kind"), t.get("person"), t.get("person2"),
                               t.get("month"), persons))
        elif k == "after_training_priority":
            who = persons.get(str(t.get("person")), t.get("person"))
            out.append("%s 특훈 뒤 · %s" % (
                who, plain_cond(t.get("condition_expr") or "", e["id"])))
        elif k == "invitation":
            out.append("토요일 초대 대사")
        elif k == "chained":
            out.append("E%05d 뒤%s" % (
                t["from"], " (답 %s)" % t["via_choice"] if t.get("via_choice") else ""))
        elif k == "memory_replay":
            out.append("회상 %d쪽 %d칸 · 원본 E%05d" % (
                t["page"], t["slot"], t["requires_events"][0]))
        else:
            out.append(k)
    seen = []
    for s in out:
        if s and s not in seen:
            seen.append(s)
    return seen


def build():
    sch = load("schedule.json")
    pools = load("pools.json")["pools"]
    lab = load("labels.json")
    persons = {str(p["no"]): (p["kr"] or p["jp"]) for p in sch["persons"]}
    dungeons = lab["dungeons"]
    cardlab = lab["cards"]

    cards = []
    for e in sch["events"]:
        md = month_of(e)
        L = cardlab.get(str(e["id"]), {})
        cards.append({
            "id": e["id"],
            "fn": e["fn"],
            "lane": lane_of(e),
            "m": md[0] if md else None,
            "d": md[1] if md else None,
            "cat": e["category"],
            "person": e["person"],
            "lines": e["messages"]["count"],
            "voice": bool(e["voice"]),
            "choice": bool(e["has_choice"]),
            "ans": [{"no": c["no"], "next": c.get("next")} for c in e["choices"]],
            "chain": e["chains_to"],
            "replay_of": e["replay_of"],
            "replay": e.get("replay_text"),
            # 거르기 전용(내용이 아니라 검수 정보라 늘 보인다). 표시는 replay 로 한다.
            "repdiff": e.get("replay_text") == "different",
            "rstats": e.get("replay_stats"),
            "when": when_texts(e, persons, dungeons),
            "who": L.get("speakers", []),
            "who_more": L.get("speakers_more", 0),
            "first": L.get("first_kr"),
            "first_m": L.get("first_m"),
            "first_cut": bool(L.get("first_truncated")),
            "un": L.get("unaudited_lines", 0),
            "mis": L.get("misalign", 0),
            "reg": L.get("register", 0),
            "battle": bool(e["effects"]["event_battle"]),
            "aff": e["effects"]["affection"],
            "unres": False,
            "grp": None,
        })
    unres_ids = {u.get("event") for u in sch.get("unresolved", [])}
    for c in cards:
        c["unres"] = c["id"] in unres_ids

    pool_cards = [{"name": p["name"], "kind": p["kind"], "person": p["person"],
                   "person2": p["person2"], "month": p["month"],
                   "kr": pool_kr(p["kind"], p["person"], p["person2"], p["month"], persons),
                   "events": [n for n in p["events"] if n]} for p in pools]

    # ── 본편 묶음(연속 이벤트) ─────────────────────────────────────────
    grp = load("groups.json")
    byid = {c["id"]: c for c in cards}
    mgroups = []
    for g in grp["groups"]:
        if len(g["members"]) < 2:
            continue
        home = byid[g["entries"][0]] if g["entries"] else byid[g["members"][0]]
        for n in g["members"]:
            byid[n]["grp"] = g["key"]
        mgroups.append({
            "key": g["key"], "entry": home["id"],
            "entries": g["entries"], "entry_more": max(0, len(g["entries"]) - 1),
            "lane": home["lane"], "m": home["m"], "d": home["d"],
            "members": g["members"], "steps": g["steps"], "branches": g["branches"],
            "shared": g["shared"], "depth": g["depth"],
            "lines": g["lines"], "un": g["un"], "mis": g["mis"], "reg": g["reg"],
            "dungeon": g["dungeon_classes"],
            "rows": [{"e": r["event"], "d": r["depth"], "v": r["via"],
                      "s": r["shared"], "c": r["counts_here"]} for r in g["rows"]],
        })

    data = {
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ain_sha256": sch["game"]["ain_sha256_original"][:16],
        "persons": persons,
        "lanes": LANES,
        "months": MONTHS,
        "folded": sorted(FOLDED),
        "cards": cards,
        "pools": pool_cards,
        "mgroups": mgroups,
        "counts": {
            "events": len(cards),
            "lines": sum(c["lines"] for c in cards),
            "by_cat": dict(collections.Counter(c["cat"] for c in cards)),
            "unaudited_lines": sum(c["un"] for c in cards),
            "misalign": sum(c["mis"] for c in cards),
            "register": sum(c["reg"] for c in cards),
        },
        "sources": {"labels": "graph/labels.json", "dialogue": "chart/dialogue_kr.json"},
    }

    if "--sample" in sys.argv:
        # 같은 템플릿(CSS·JS 그대로)에 카드만 골라 담은 확인용 판.
        # 브라우저에서 배치·잠금을 실측할 때 쓴다. 산출물이 아니다.
        pick, seen_lane, seen_cat = [], collections.Counter(), collections.Counter()
        order = sorted(data["cards"],
                       key=lambda c: -(len(c["first"] or "") + len(" ".join(c["when"]))))
        for c in order:
            if seen_lane[c["lane"]] < 6 and seen_cat[c["cat"]] < 8:
                pick.append(c); seen_lane[c["lane"]] += 1; seen_cat[c["cat"]] += 1
        data = dict(data, cards=pick, pools=[],
                    counts=dict(data["counts"], events=len(pick)))
        html_text = TEMPLATE.replace("/*__DATA__*/",
                                     json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        out = os.path.join(BASE, "scratch", "sample_chart.html")
        with io.open(out, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(html_text)
        print("wrote sample", out, os.path.getsize(out), "bytes,", len(pick), "cards")
        return data

    write_visit_order(data)

    html_text = TEMPLATE.replace("/*__DATA__*/",
                                 json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(HERE, "yoru_flowchart.html")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(html_text)
    print("wrote", out, os.path.getsize(out), "bytes")
    return data


CATKR = {"main": "본편", "after_training": "특훈 뒤", "after_training_priority": "특훈 뒤(우선)",
         "training_invite": "특훈 권유", "dungeon_walk": "던전 대화",
         "memory_replay": "회상 재생본", "system": "시스템", "unknown": "쓰이지 않음"}


def write_visit_order(data):
    cards = data["cards"]
    persons = data["persons"]
    groups = collections.OrderedDict()
    for c in cards:
        t = c["cat"]
        if t == "memory_replay":
            key = ("9 회상 모드", "")
        elif t == "dungeon_walk":
            who = persons.get(str(c["person"]), "")
            who2 = persons.get(str(c.get("person2")), "")
            key = ("8 던전 걷기", f"{who}{' / ' + who2 if who2 else ''}")
        elif t in ("after_training", "after_training_priority", "training_invite"):
            who = persons.get(str(c["person"]), str(c["person"]))
            key = ("%d %s 특훈" % (2 + (c["person"] or 9), who),
                   ("%02d월" % c["m"]) if c["m"] else "99 달 미정")
        elif t == "main":
            key = ("1 본편", ("%02d월" % c["m"]) if c["m"] else "99 달 미정")
        else:
            key = ("9 그 밖", "")
        groups.setdefault(key, []).append(c)
    lines = ["# 방문 순서 (검수용)", ""]
    lines.append("- 만든 날 " + data["generated"] + " · `chart/build_chart.py` 가 만든다. 손으로 고치지 않는다.")
    lines.append("- **진행 파일이 없어 「전부 안 읽음」 기준**이다.")
    lines.append("- 묶음 기준: 같은 문맥(같은 상대·같은 달·같은 던전)끼리 모았다.")
    lines.append("- `미n` = 아직 검수 안 된 줄 수. 줄거리는 적지 않는다.")
    lines.append("")
    total = sum(len(v) for v in groups.values())
    tl = sum(c["lines"] for c in cards)
    un = sum(c["un"] for c in cards)
    lines.append(f"전체 {total}개 장면 / 대사 {tl:,}줄 / 미검수 {un:,}줄 / 묶음 {len(groups)}개")
    lines.append("")
    for (a, b), cs in sorted(groups.items()):
        cs.sort(key=lambda c: ((c["m"] or 99), (c["d"] or 0), c["id"]))
        n = sum(c["lines"] for c in cs)
        u = sum(c["un"] for c in cs)
        bb = (b[1:] if b.startswith("0") else b.replace("99 ", "")) if b else ""
        head = a.split(" ", 1)[1] + (" · " + bb if bb else "")
        lines.append(f"## {head} — {len(cs)}개 / {n:,}줄 / 미검수 {u:,}줄")
        lines.append("")
        row = []
        for c in cs:
            mark = []
            if c["choice"]:
                mark.append("갈래")
            if c["replay_of"]:
                mark.append("재생본")
            if c["battle"]:
                mark.append("전투")
            if c["un"]:
                mark.append("미%d" % c["un"])
            row.append("E%05d(%d줄%s)" % (c["id"], c["lines"],
                                          "·" + "·".join(mark) if mark else ""))
        for i in range(0, len(row), 5):
            lines.append("- " + ", ".join(row[i:i + 5]))
        lines.append("")
    out = os.path.join(HERE, "visit_order.md")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fp:
        fp.write("\n".join(lines))
    print("wrote", out)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>밤이 온다! 이벤트 차트</title>
<style>
  :root{
    --bg:#14161a; --panel:#1b1e24; --line:#2c313a; --fg:#dfe3ea; --dim:#8b93a1;
    --acc:#6ea8fe; --warn:#e0a458; --ok:#5fbf7f; --lock:#3a3f49;
    --card:#20242b; --cardread:#26313f; --red:#e08a8a;
  }
  *{box-sizing:border-box}
  html{height:100%}
  body{margin:0;padding:0;background:var(--bg);color:var(--fg);
    font:13px/1.45 "Malgun Gothic","맑은 고딕",system-ui,sans-serif;
    height:100vh;display:flex;flex-direction:column;overflow:hidden}
  header{flex:0 0 auto;z-index:30;background:var(--panel);
    border-bottom:1px solid var(--line);padding:5px 10px}
  h1{font-size:14px;margin:0 0 4px;font-weight:600}
  h1 span{font-weight:400;color:var(--dim);font-size:11px;margin-left:8px}
  .bar{display:flex;flex-wrap:wrap;gap:5px;align-items:center}
  .bar label{color:var(--dim);font-size:11px}
  input,select,button{background:#0f1115;color:var(--fg);border:1px solid var(--line);
    border-radius:4px;padding:2px 6px;font:inherit;font-size:12px}
  button{cursor:pointer}
  button.on{background:var(--acc);color:#0b0d10;border-color:var(--acc)}
  #warn{flex:0 0 auto;background:#3a2a16;color:#e8c893;font-size:11px;padding:3px 10px;
    border-bottom:1px solid #574026}
  #wrap{flex:1 1 auto;min-height:0;overflow:auto;position:relative}
  table.grid{border-collapse:separate;border-spacing:0;min-width:100%}
  table.grid th.mon{position:sticky;top:0;z-index:10;background:var(--panel);
    border-bottom:1px solid var(--line);padding:3px 8px;font-size:11px;color:var(--dim);
    text-align:left;white-space:nowrap}
  table.grid th.lane{position:sticky;left:0;z-index:12;background:var(--panel);
    border-right:1px solid var(--line);padding:5px 8px;font-size:12px;
    text-align:left;white-space:nowrap;vertical-align:top;min-width:74px}
  table.grid th.corner{position:sticky;left:0;top:0;z-index:20;background:var(--panel);
    border-right:1px solid var(--line);border-bottom:1px solid var(--line);
    font-size:11px;color:var(--dim);padding:3px 8px}
  td.cell{border-bottom:1px solid var(--line);border-right:1px solid var(--line);
    vertical-align:top;padding:3px;min-width:214px;max-width:214px}
  .card{display:block;background:var(--card);border:1px solid var(--line);
    border-radius:5px;padding:4px 6px;margin:3px 0;font-size:11px;cursor:pointer}
  .card.read{background:var(--cardread);border-color:#3c5a7a}
  .card.sel{outline:2px solid var(--acc)}
  .card.grp{background:#1d2530;border-color:#38465a}
  .card.dim{opacity:.55}
  .steps{border-left:2px solid #38465a;margin:0 0 4px 4px;padding-left:4px}
  .steps .via{color:#9ec2ef;font-size:10px;margin-top:2px}
  .steps .step{margin:0}
  .card .hd{display:flex;gap:4px;align-items:baseline;flex-wrap:wrap}
  .card .no{font-weight:600;letter-spacing:.02em}
  .card .ln{color:var(--dim);font-size:10px;margin-left:auto}
  .card .when{color:#9ec2ef;font-size:10.5px;margin-top:1px}
  .card .who{color:#c8b48f;font-size:10.5px}
  .card .first{color:var(--fg);font-size:11px;margin-top:2px;opacity:.92}
  .card .badge{margin-top:2px;font-size:10px;color:var(--dim)}
  .chip{display:inline-block;border-radius:3px;padding:0 3px;font-size:10px;
    background:#2b3038;color:var(--dim)}
  .chip.c{background:#4a3a20;color:#e0a458}
  .chip.v{background:#203a2a;color:var(--ok)}
  .chip.r{background:#33283f;color:#c39ae0}
  .chip.b{background:#3f2828;color:var(--red)}
  .chip.un{background:#42301c;color:#e8b46a}
  .chip.uk{background:#3a2020;color:var(--red)}
  .chip.ok{background:#1e3226;color:var(--ok)}
  .chip.s{background:#2d2438;color:#b79ae0}
  .locked{color:var(--lock)}
  #side{position:fixed;right:0;top:0;bottom:0;width:380px;background:var(--panel);
    border-left:1px solid var(--line);padding:10px;overflow:auto;z-index:40;display:none}
  #side.open{display:block}
  #side h2{font-size:14px;margin:0 0 6px}
  #side .k{color:var(--dim);font-size:11px;margin-top:8px}
  #side .v{font-size:12px;word-break:break-word}
  #side ul{margin:4px 0;padding-left:16px}
  #dlg{margin-top:8px;border-top:1px solid var(--line);padding-top:6px}
  #dlg .sp{color:#c8b48f;font-size:11px;margin-top:6px}
  #dlg .tx{font-size:12px;white-space:pre-wrap}
  #dlg .tx.un{border-left:2px solid #6a4a20;padding-left:5px}
  #dlg .tx.raw{color:var(--dim)}
  .foot{flex:0 0 auto;color:var(--dim);font-size:11px;padding:3px 10px;
    background:var(--panel);border-top:1px solid var(--line);z-index:25}
  .empty{color:var(--lock);font-size:11px}
  @media (max-width:860px){ #side{width:100%} td.cell{min-width:170px;max-width:170px} }
</style>
</head>
<body>
<header>
  <h1>밤이 온다! -Square of the MOON- Remastered · 이벤트 차트
    <span id="hdr"></span></h1>
  <div class="bar">
    <button id="mode" class="on">검수 보기</button>
    <input id="q" placeholder="번호 찾기" size="9">
    <select id="fl"><option value="">전체 줄</option></select>
    <select id="fc"></select>
    <select id="fa">
      <option value="">검수 상태 전체</option>
      <option value="un">검수 안 된 줄이 있는 것</option>
      <option value="sus">의심 줄이 있는 것</option>
    </select>
    <button id="tUnread">안 읽은 것만</button>
    <button id="tExpand">묶음 펼치기</button>
    <label>진행</label><input type="file" id="prog" accept=".json" style="width:118px">
    <label>대사</label><input type="file" id="dlgf" accept=".json" style="width:118px">
    <span id="stat" style="color:var(--dim);font-size:11px"></span>
  </div>
</header>
<div id="warn">⚠ 검수 보기입니다 — 아직 안 본 장면의 조건·화자·첫 줄이 모두 보입니다. 플레이 중이라면 「플레이 보기」로 바꾸세요.</div>
<div id="wrap"></div>
<div class="foot" id="foot"></div>
<div id="side"></div>
<script>
const DATA = /*__DATA__*/;

/* ── 상태 ─────────────────────────────────────────────────────── */
let PROG = {seen_once: [], seen_total: []};
let REVIEW = true;          // 검수 보기가 기본
let ONLY_UNREAD = false;
let EXPAND = false;
let SEL = null;
let DLG = null;             // chart/dialogue_kr.json (검수 보기에서만 쓴다)

function nameToNo(v){
  if (typeof v === 'number') return v;
  const m = String(v).match(/(\d+)\s*$/);
  return m ? parseInt(m[1],10) : null;
}
function seenSet(){
  const s = new Set();
  ['seen_total','seen_once','seen_total_names','seen_once_names'].forEach(k=>{
    (PROG[k]||[]).forEach(x=>{ const n=nameToNo(x); if(n!==null) s.add(n); });
  });
  return s;
}
let SEEN = seenSet();

function isRead(id){ return SEEN.has(id); }
function unlocked(id){ return REVIEW || isRead(id); }
/** 잠길 자료는 이 접근자 하나로만 읽는다. 다른 곳에서 c.when 등을 직접 쓰지 않는다. */
function field(card, name){
  const always = {id:1, lane:1, m:1, d:1, cat:1, lines:1, voice:1, choice:1,
                  person:1, unres:1, battle:1, fn:1, replay_of:1,
                  un:1, mis:1, reg:1, repdiff:1};
  if (always[name]) return card[name];
  if (!unlocked(card.id)) return null;
  return card[name];
}

const LANEMAP = {}; DATA.lanes.forEach(([k,v])=>LANEMAP[k]=v);
const CATKR = {main:"본편", after_training:"특훈 뒤", after_training_priority:"특훈 뒤(우선)",
  training_invite:"특훈 권유", dungeon_walk:"던전 대화", memory_replay:"회상 재생본",
  system:"시스템", unknown:"쓰이지 않음"};
const FOLDED = new Set(DATA.folded);

/* ── 카드 그리기 ───────────────────────────────────────────────── */
function auditChip(c){
  if (!c.lines) return '';
  if (c.un === 0) return '<span class="chip ok">검수 완료</span>';
  if (c.un >= c.lines) return '<span class="chip uk">검수 안 됨 '+c.un+'줄</span>';
  return '<span class="chip un">검수 일부 '+c.un+'줄</span>';
}
function susChip(c){
  const p=[];
  if (c.mis) p.push('정렬 '+c.mis);
  if (c.reg) p.push('존대 '+c.reg);
  return p.length? '<span class="chip s">'+p.join(' · ')+'</span>' : '';
}
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function cardHTML(c, opt){
  opt = opt || {};
  const read = isRead(c.id);
  const chips=[];
  if (c.choice) chips.push('<span class="chip c">갈래</span>');
  if (c.voice) chips.push('<span class="chip v">음성</span>');
  if (c.battle) chips.push('<span class="chip b">전투</span>');
  if (c.replay_of) chips.push('<span class="chip r">재생본</span>');
  if (opt.shared) chips.push('<span class="chip s">공유</span>');
  let h = '<div class="card'+(read?' read':'')+(SEL===c.id?' sel':'')
    + (opt.dim?' dim':'')+'" data-id="'+c.id+'">'
    + '<div class="hd"><span class="no">E'+String(c.id).padStart(5,'0')+'</span>'
    + chips.join('') + '<span class="ln">'+(opt.dim?'':c.lines+'줄')+'</span></div>';
  const when = field(c,'when');
  if (when === null) h += '<div class="when locked">조건 잠김</div>';
  else if (when.length) h += '<div class="when">'+esc(when[0])
       + (when.length>1? ' <span class="ln">+'+(when.length-1)+'</span>':'')+'</div>';
  const who = field(c,'who');
  if (who === null) h += '<div class="who locked">화자 잠김</div>';
  else if (who.length) h += '<div class="who">'+esc(who.join(' · '))
       + (c.who_more? ' 외 '+c.who_more : '')+'</div>';
  const first = field(c,'first');
  if (first === null) h += '<div class="first locked">첫 줄 잠김</div>';
  else if (first) h += '<div class="first">'+esc(first)+(c.first_cut?'…':'')+'</div>';
  const b = auditChip(c)+susChip(c);
  if (b) h += '<div class="badge">'+b+'</div>';
  return h + '</div>';
}

const MG = {};              // 본편 묶음 색인
(DATA.mgroups||[]).forEach(g=>{MG[g.key]=g;});

function readState(ids){
  const r = ids.filter(isRead).length;
  return r===0? ['없음',''] : (r===ids.length? ['전부',' read'] : ['일부 '+r+'/'+ids.length,'']);
}

/** 본편 묶음의 접힌 카드. 라벨은 **진입 단계**의 것을 접근자로 읽는다. */
function mgroupHTML(g){
  const ec = DATA.cards.find(c=>c.id===g.entry);
  const [rs, cls] = readState(g.members);
  const chips=[];
  if (g.branches) chips.push('<span class="chip c">갈래 '+g.branches+'</span>');
  if (g.dungeon.length) chips.push('<span class="chip">한 밤의 던전</span>');
  if (g.shared.length) chips.push('<span class="chip s">공유 '+g.shared.length+'</span>');
  let h = '<div class="card grp'+cls+'" data-mgrp="'+g.key+'">'
    + '<div class="hd"><span class="no">E'+String(g.entry).padStart(5,'0')+' 외 '+(g.steps-1)+'단계</span>'
    + chips.join('') + '<span class="ln">'+g.lines+'줄</span></div>';
  const when = field(ec,'when');
  if (when === null) h += '<div class="when locked">조건 잠김</div>';
  else if (when.length) h += '<div class="when">'+esc(when[0])
       + (g.entry_more? ' <span class="ln">진입 외 '+g.entry_more+'</span>':'')+'</div>';
  const who = field(ec,'who');
  if (who === null) h += '<div class="who locked">화자 잠김</div>';
  else if (who.length) h += '<div class="who">'+esc(who.join(' · '))
       + (ec.who_more? ' 외 '+ec.who_more : '')+'</div>';
  const first = field(ec,'first');
  if (first === null) h += '<div class="first locked">첫 줄 잠김</div>';
  else if (first) h += '<div class="first">'+esc(first)+(ec.first_cut?'…':'')+'</div>';
  const b = groupAuditChip(g)+groupSusChip(g);
  h += '<div class="badge">읽음 '+rs+(b? ' · '+b : '')
     + ' <span class="chip">'+(OPEN.has('M:'+g.key)?'접기':'펼치기')+'</span></div>';
  return h + '</div>';
}
function groupAuditChip(g){
  if (!g.lines) return '';
  if (g.un===0) return '<span class="chip ok">검수 완료</span>';
  if (g.un>=g.lines) return '<span class="chip uk">검수 안 됨 '+g.un+'줄</span>';
  return '<span class="chip un">검수 일부 '+g.un+'줄</span>';
}
function groupSusChip(g){
  const p=[]; if (g.mis) p.push('정렬 '+g.mis); if (g.reg) p.push('존대 '+g.reg);
  return p.length? '<span class="chip s">'+p.join(' · ')+'</span>' : '';
}

/** 펼친 묶음의 단계들. 사슬은 화살표 순, 답 갈래는 문구와 함께 들여쓴다. */
function mgroupRowsHTML(g){
  let out = '';
  g.rows.forEach(r=>{
    const c = DATA.cards.find(x=>x.id===r.e);
    let via = '';
    if (r.v.kind==='answer'){
      const t = r.v.text_kr;
      via = '<div class="via">답 '+r.v.no+(t? ' · '+esc(t) : ' <span class="locked">(문구 못 찾음)</span>')+'</div>';
    } else if (r.v.kind==='chain') via = '<div class="via">↳ 이어서</div>';
    out += '<div class="step" style="margin-left:'+(r.d*12)+'px">'
         + via + cardHTML(c, {shared:r.s, dim:!r.c}) + '</div>';
  });
  return out;
}

function groupHTML(key, cs){
  const n = cs.length, ln = cs.reduce((a,c)=>a+c.lines,0),
        un = cs.reduce((a,c)=>a+c.un,0), rd = cs.filter(c=>isRead(c.id)).length;
  return '<div class="card grp" data-grp="'+esc(key)+'">'
    + '<div class="hd"><span class="no">'+esc(key)+'</span>'
    + '<span class="ln">'+n+'장 '+ln+'줄</span></div>'
    + '<div class="when">읽음 '+rd+'/'+n+(un? ' · 검수 안 된 줄 '+un : ' · 검수 완료')+'</div>'
    + '<div class="badge"><span class="chip">누르면 펼침</span></div></div>';
}

/* ── 거르기 ───────────────────────────────────────────────────── */
let OPEN = new Set();
const VISG = new Set();      // 이번 렌더에서 보이는 본편 묶음
function catSel(){ return document.getElementById('fc').value; }
function visible(c){
  const q = document.getElementById('q').value.trim();
  if (q && String(c.id).indexOf(q)<0) return false;
  const fl = document.getElementById('fl').value;
  if (fl && c.lane!==fl) return false;
  const fa = document.getElementById('fa').value;
  if (fa==='un' && !c.un) return false;
  if (fa==='sus' && !(c.mis||c.reg)) return false;
  if (ONLY_UNREAD && isRead(c.id)) return false;
  const sel = catSel();
  if (sel==='__all') return true;
  if (sel==='__default') return c.cat==='main' || c.repdiff
      || FOLDED.has(c.cat);            // 풀은 묶음 카드로 접어서 보인다
  if (sel==='__mem_diff') return c.cat==='memory_replay' && c.repdiff;
  return c.cat===sel;
}
function groupKey(c){
  if (!FOLDED.has(c.cat)) return null;
  const who = DATA.persons[String(c.person)] || '?';
  const mon = c.m? c.m+'월' : '달 미정';
  return who+' · '+mon+' · '+CATKR[c.cat];
}

function render(){
  const cols = DATA.months.slice();
  let h = '<table class="grid"><tr><th class="corner">줄 \\ 달</th>';
  cols.forEach(m=>{ h += '<th class="mon">'+m+'월</th>'; });
  h += '<th class="mon">달 미정</th></tr>';
  let shown = 0;
  VISG.clear();
  if (!EXPAND) DATA.cards.forEach(c=>{ if (c.grp && visible(c)) VISG.add(c.grp); });
  DATA.lanes.forEach(([key,label])=>{
    const rows = DATA.cards.filter(c=>c.lane===key && visible(c));
    const homes = EXPAND? [] : (DATA.mgroups||[]).filter(g=>g.lane===key && VISG.has(g.key));
    if (!rows.length && !homes.length) return;
    const nCard = rows.filter(c=>EXPAND || !c.grp).length + homes.length;
    shown += nCard;
    h += '<tr><th class="lane">'+label
       + '<div class="ln" style="color:var(--dim);font-size:10px">'+nCard+'</div></th>';
    const draw = (cs, laneKey, mon)=>{
      const groups = new Map(); const single = [];
      cs.forEach(c=>{
        if (c.grp && !EXPAND) return;          // 본편 묶음 구성원은 묶음 카드로만 나온다
        const g = EXPAND? null : groupKey(c);
        if (g===null) single.push(c);
        else { if(!groups.has(g)) groups.set(g,[]); groups.get(g).push(c); }
      });
      // 이 칸이 집인 본편 묶음
      const mine = EXPAND? [] : (DATA.mgroups||[]).filter(g=>
        g.lane===laneKey && (mon===null? !g.m : g.m===mon) && VISG.has(g.key));
      let out = '';
      single.sort((a,b)=>(a.d-b.d)||(a.id-b.id));
      out += single.map(c=>cardHTML(c)).join('');
      mine.sort((a,b)=>(a.d-b.d)||(a.entry-b.entry)).forEach(g=>{
        out += mgroupHTML(g);
        if (OPEN.has('M:'+g.key)) out += '<div class="steps">'+mgroupRowsHTML(g)+'</div>';
      });
      [...groups.entries()].sort().forEach(([g,list])=>{
        if (OPEN.has(g)) out += groupHTML(g,list)
               + list.sort((a,b)=>a.id-b.id).map(c=>cardHTML(c)).join('');
        else out += groupHTML(g,list);
      });
      return out || '<span class="empty">·</span>';
    };
    cols.forEach(m=>{ h += '<td class="cell">'+draw(rows.filter(c=>c.m===m),key,m)+'</td>'; });
    h += '<td class="cell">'+draw(rows.filter(c=>!c.m),key,null)+'</td></tr>';
  });
  h += '</table>';
  document.getElementById('wrap').innerHTML = h;
  const read = DATA.cards.filter(c=>isRead(c.id)).length;
  const top = document.querySelectorAll('#wrap td.cell > .card').length;
  document.getElementById('stat').textContent =
    '화면의 카드 '+top+' (장면 '+shown+') / 전체 장면 '+DATA.counts.events+' · 읽음 '+read;
  document.querySelectorAll('.card[data-id]').forEach(el=>{
    el.addEventListener('click', ()=>{ SEL=+el.dataset.id; showSide(SEL); render(); });
  });
  document.querySelectorAll('.card[data-grp]').forEach(el=>{
    el.addEventListener('click', ()=>{ const g=el.dataset.grp;
      if(OPEN.has(g)) OPEN.delete(g); else OPEN.add(g); render(); });
  });
  document.querySelectorAll('.card[data-mgrp]').forEach(el=>{
    el.addEventListener('click', ()=>{ const k='M:'+el.dataset.mgrp;
      if(OPEN.has(k)) OPEN.delete(k); else OPEN.add(k); render(); });
  });
}

/* ── 옆 패널 ──────────────────────────────────────────────────── */
function showSide(id){
  const c = DATA.cards.find(x=>x.id===id);
  if (!c) return;
  const s = document.getElementById('side');
  let h = '<h2>E'+String(c.id).padStart(5,'0')
        + ' <button id="closeSide" style="float:right">닫기</button></h2>';
  h += '<div class="v">'+(CATKR[c.cat]||c.cat)
     + (c.person? ' · '+(DATA.persons[String(c.person)]||c.person):'')+'</div>';
  h += '<div class="k">대사 줄 / 검수</div><div class="v">'+c.lines+'줄 · '
     + (c.lines? (c.un? (c.un>=c.lines? '검수 안 됨':'검수 일부 '+c.un+'줄 남음') : '검수 완료') : '대사 없음')
     + (c.mis||c.reg? ' · 의심(정렬 '+c.mis+' / 존대 '+c.reg+')':'')+'</div>';
  h += '<div class="k">엔진 함수</div><div class="v">'+field(c,'fn')+'</div>';
  h += '<div class="k">읽음</div><div class="v">'+(isRead(c.id)?'읽음':'아직')+'</div>';
  const who = field(c,'who');
  h += '<div class="k">나오는 사람</div>';
  h += who===null? '<div class="v locked">잠김</div>'
     : '<div class="v">'+(who.length? esc(who.join(' · '))+(c.who_more?' 외 '+c.who_more:'') : '없음')+'</div>';
  const when = field(c,'when');
  h += '<div class="k">뜨는 조건</div>';
  h += when===null? '<div class="v locked">아직 안 읽은 장면 — 잠김</div>'
     : '<ul>'+when.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';
  const ch = field(c,'chain');
  h += '<div class="k">이어지는 장면</div>';
  h += ch===null? '<div class="v locked">잠김</div>'
     : (!ch.length? '<div class="v">없음(여기서 끝)</div>'
        : '<div class="v">'+ch.map(x=>'E'+String(x).padStart(5,'0')).join(', ')+'</div>');
  const ans = field(c,'ans');
  if (ans && ans.length) h += '<div class="k">선택지 갈래</div><ul>'
     + ans.map(a=>'<li>답 '+a.no+' → E'+String(a.next).padStart(5,'0')+'</li>').join('')+'</ul>';
  else if (c.choice && ans===null) h += '<div class="k">선택지 갈래</div><div class="v locked">잠김</div>';
  if (c.replay_of){
    const rs = field(c,'rstats');
    h += '<div class="k">회상 재생본</div>';
    if (rs===null) h += '<div class="v locked">잠김</div>';
    else {
      const r = field(c,'replay');
      h += '<div class="v">원본 E'+String(c.replay_of).padStart(5,'0')+' · '
        + ({redirect:'원본을 그대로 부른다(대사 중복 없음)', same_as_source:'원본과 글자가 같다',
            same_as_source_chain:'원본 사슬과 글자가 같다', different:'원본과 다르다'}[r]||r)
        + (rs.replay_lines? (' · 재생본 '+rs.replay_lines+'줄 중 '+rs.shared_lines+'줄이 원본과 같음'):'')
        + '</div>';
    }
  }
  const aff = field(c,'aff');
  if (aff && aff.length) h += '<div class="k">친밀도</div><div class="v">'
     + aff.map(a=>(DATA.persons[String(a.person)]||a.person)+' '+(a.delta>0?'+':'')+a.delta).join(', ')+'</div>';
  if (c.unres) h += '<div class="k">메모</div><div class="v">부르는 자리를 못 찾았다(개발용으로 보인다)</div>';
  // 대사 전문 — 검수 보기에서만
  h += '<div id="dlg"></div>';
  s.innerHTML = h;
  s.classList.add('open');
  document.getElementById('closeSide').onclick = ()=>{ s.classList.remove('open'); SEL=null; render(); };
  fillDialogue(c);
}

function fillDialogue(c){
  const box = document.getElementById('dlg');
  if (!box) return;
  if (!REVIEW){ box.innerHTML = '<div class="k">대사 전문</div>'
      + '<div class="v locked">플레이 보기에서는 보여 주지 않습니다.</div>'; return; }
  if (!DLG){ box.innerHTML = '<div class="k">대사 전문</div>'
      + '<div class="v locked">위 「대사」에서 <b>chart/dialogue_kr.json</b> 을 고르면 여기에 나옵니다.</div>'; return; }
  const rows = DLG.events[String(c.id)];
  if (!rows){ box.innerHTML = '<div class="k">대사 전문</div><div class="v locked">없음</div>'; return; }
  let h = '<div class="k">대사 전문 ('+rows.length+'줄)</div>';
  rows.forEach(r=>{
    if (r[0]===1) h += '<div class="sp">'+esc(r[1])+'</div>';
    else {
      const t = r[1] || r[2] || '';
      h += '<div class="tx'+(r[1]?'':' raw')+'">'+esc(t)+'</div>';
    }
  });
  box.innerHTML = h;
}

/* ── 조작 ─────────────────────────────────────────────────────── */
function setMode(review){
  REVIEW = review;
  document.getElementById('mode').textContent = REVIEW? '검수 보기' : '플레이 보기';
  document.getElementById('mode').classList.toggle('on', REVIEW);
  document.getElementById('warn').style.display = REVIEW? '' : 'none';
  if (SEL) showSide(SEL);
  render();
}

function init(){
  document.getElementById('hdr').textContent =
    '이벤트 '+DATA.counts.events+'개 · 대사 '+DATA.counts.lines.toLocaleString()+'줄 · '
    + '검수 안 된 줄 '+DATA.counts.unaudited_lines.toLocaleString()+' · '
    + '만든 날 '+DATA.generated+' · AIN '+DATA.ain_sha256;
  const fl = document.getElementById('fl');
  DATA.lanes.forEach(([k,v])=>{ const o=document.createElement('option'); o.value=k; o.textContent=v; fl.appendChild(o); });
  const fc = document.getElementById('fc');
  [['__default','기본(본편 + 원본과 다른 회상)'],['__all','전부'],
   ['__mem_diff','회상 재생본(원본과 다름)']].forEach(([v,t])=>{
    const o=document.createElement('option'); o.value=v; o.textContent=t; fc.appendChild(o); });
  Object.keys(DATA.counts.by_cat).sort().forEach(k=>{
    const o=document.createElement('option'); o.value=k;
    o.textContent=(CATKR[k]||k)+' ('+DATA.counts.by_cat[k]+')'; fc.appendChild(o); });
  fc.value='__default';
  document.getElementById('q').addEventListener('input', render);
  fl.addEventListener('change', render);
  fc.addEventListener('change', ()=>{ OPEN.clear(); render(); });
  document.getElementById('fa').addEventListener('change', render);
  document.getElementById('tUnread').onclick = e=>{ ONLY_UNREAD=!ONLY_UNREAD;
    e.target.classList.toggle('on',ONLY_UNREAD); render(); };
  document.getElementById('tExpand').onclick = e=>{ EXPAND=!EXPAND;
    e.target.classList.toggle('on',EXPAND); render(); };
  document.getElementById('mode').onclick = ()=>{
    if (REVIEW) setMode(false);
    else if (confirm('검수 보기로 바꾸면 아직 안 본 장면의 조건·화자·첫 줄이 모두 보입니다. 바꿀까요?'))
      setMode(true);
  };
  document.getElementById('prog').addEventListener('change', ev=>{
    const f = ev.target.files[0]; if(!f) return;
    const r = new FileReader();
    r.onload = ()=>{ try{ PROG=JSON.parse(r.result); SEEN=seenSet();
        document.getElementById('foot').textContent =
          '진행 파일: '+(PROG.schema||'?')+' · 이번 판 '+((PROG.seen_once||PROG.seen_once_names||[]).length)
          +'개 · 누적 '+((PROG.seen_total||PROG.seen_total_names||[]).length)+'개';
        if (SEL) showSide(SEL); render();
      } catch(e){ alert('진행 파일을 읽지 못했습니다: '+e); } };
    r.readAsText(f);
  });
  document.getElementById('dlgf').addEventListener('change', ev=>{
    const f = ev.target.files[0]; if(!f) return;
    const r = new FileReader();
    r.onload = ()=>{ try{ const d=JSON.parse(r.result);
        if (d.schema!=='yoru-dialogue-kr.v1') throw new Error('다른 파일입니다');
        DLG=d; if (SEL) showSide(SEL);
        document.getElementById('foot').textContent = '대사 전문 불러옴 ('+Object.keys(d.events).length+'개 장면)';
      } catch(e){ alert('대사 파일을 읽지 못했습니다: '+e); } };
    r.readAsText(f);
  });
  document.addEventListener('dragover', e=>e.preventDefault());
  document.addEventListener('drop', e=>{
    e.preventDefault(); const f=e.dataTransfer.files[0]; if(!f) return;
    const r=new FileReader();
    r.onload=()=>{ try{ const d=JSON.parse(r.result);
      if (d.schema==='yoru-dialogue-kr.v1'){ DLG=d; } else { PROG=d; SEEN=seenSet(); }
      if(SEL) showSide(SEL); render(); }catch(err){} };
    r.readAsText(f);
  });
  document.getElementById('foot').textContent =
    '진행 파일이 없으면 전부 「아직 안 읽음」입니다. 카드를 누르면 옆에 자세히 나옵니다. '
    + '대사 전문은 chart/dialogue_kr.json 을 「대사」에서 고르세요.';
  // 같은 폴더에 있으면 알아서 불러온다(file:// 은 막히므로 조용히 실패하고 파일 선택으로 돌아간다)
  fetch('dialogue_kr.json').then(r=>r.ok?r.json():null).then(d=>{
    if (d && d.schema==='yoru-dialogue-kr.v1'){ DLG=d;
      document.getElementById('foot').textContent = '대사 전문을 같은 폴더에서 불러왔습니다.';
      if (SEL) showSide(SEL); }
  }).catch(()=>{});
  setMode(true);
}
init();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
