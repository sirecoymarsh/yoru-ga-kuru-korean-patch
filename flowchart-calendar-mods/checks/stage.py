#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""게이트 한 명령.

  python stage.py            모든 검사 실행
  python stage.py --selftest 검사마다 결함을 심어 실제로 걸리는지 증명

검사 목록
  0 입력 해시     원본 AIN·EX 해시가 graph/inputs.json 과 같나
  1 구조         schedule_check.py
  2 갈래 A1~A6   compare_a*.py
  3 시뮬레이션    simulate.py (도달 표)
  4 조건 태그     lines.jsonl 이 MSG 범위 안인가 (1 에 포함)
  5 문구 원문     차트에 박힌 인물 한국어 표기가 화자명 정본과 같나
  6 스포일러 렌더 HTML 이 잠금 접근자 하나만 쓰는가(정적 검사)
  7 배치         HTML 이 창 크기에 기대지 않는 레이아웃인가(정적 검사)
"""
import sys, os, io, json, re, subprocess, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
PY = sys.executable
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

AIN = r"P:\GAME\Compacted Files\[Ryuugames] RY-r119676\夜が来る！-Square of the MOON- Remastered\NightRemaster.ain"
EXF = r"P:\GAME\Compacted Files\[Ryuugames] RY-r119676\夜が来る！-Square of the MOON- Remastered\NightRemasterEX.ex"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fp:
        for b in iter(lambda: fp.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def run(script, args=()):
    p = subprocess.run([PY, os.path.join(HERE, script)] + list(args),
                       capture_output=True, env=ENV, cwd=BASE)
    out = p.stdout.decode("utf-8", "replace").strip()
    err = p.stderr.decode("utf-8", "replace").strip()
    return p.returncode, out, err


def gate_hash(inject=False):
    with io.open(os.path.join(BASE, "graph", "inputs.json"), encoding="utf-8") as fp:
        inp = json.load(fp)
    want = dict(inp["files"])
    if inject:
        want["NightRemaster.ain"]["sha256"] = "0" + want["NightRemaster.ain"]["sha256"][1:]
    bad = []
    for name, path in (("NightRemaster.ain", AIN), ("NightRemasterEX.ex", EXF)):
        got = sha256(path)
        if got != want[name]["sha256"]:
            bad.append(f"{name}: {got[:12]} != {want[name]['sha256'][:12]}")
    return bad


def gate_names(inject=False):
    """차트에 박힌 인물 한국어 표기가 화자명 정본과 같나."""
    sl = json.load(io.open(
        r"P:\AI\Codex\projects\YoruGaKuru_speaker_label_postprocess\speaker_labels.json",
        encoding="utf-8"))
    canon = {l["source_core"]: l["korean_core"] for l in sl["labels"]
             if l.get("status") == "locked"}
    if inject:
        canon["いずみ"] = "이즈미이"
    sch = json.load(io.open(os.path.join(BASE, "graph", "schedule.json"), encoding="utf-8"))
    html = io.open(os.path.join(BASE, "chart", "yoru_flowchart.html"),
                   encoding="utf-8").read()
    bad = []
    for p in sch["persons"]:
        if p["kr"] is None:
            continue
        if canon.get(p["jp"]) != p["kr"]:
            bad.append(f"{p['jp']}: 그래프 {p['kr']} != 정본 {canon.get(p['jp'])}")
        if ('"%s"' % p["kr"]) not in html and (">%s<" % p["kr"]) not in html:
            bad.append(f"{p['kr']} 가 HTML 에 없다")
    return bad


def gate_spoiler_static(inject=False):
    """HTML 이 잠금 접근자 하나만 쓰는가 — 카드 개체의 잠금 필드를 직접 읽는 곳이 없나."""
    src = io.open(os.path.join(BASE, "chart", "yoru_flowchart.html"), encoding="utf-8").read()
    js = src.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    js = js.split("const DATA =", 1)[1].split("\n", 1)[1]    # 구운 자료는 뺀다
    js = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), js, flags=re.S)
    js = "\n".join("" if l.strip().startswith("//") else l for l in js.split("\n"))
    if inject:
        js += "\nconst leak = c.cond;\n"
    bad = []
    if "function field(" not in js:
        bad.append("접근자 field() 가 없다")
    for m in re.finditer(r"\b(c|card)\.(cond|chain|ans|replay|rstats|aff)\b", js):
        line = js[:m.start()].count("\n") + 1
        ctx = js.split("\n")[line - 1]
        if "function field(" in ctx or "return card[name]" in ctx:
            continue
        bad.append(f"{line}행에서 잠금 필드를 직접 읽는다: {ctx.strip()[:70]}")
    return bad


def gate_layout_static(inject=False):
    src = io.open(os.path.join(BASE, "chart", "yoru_flowchart.html"), encoding="utf-8").read()
    css = src.split("<style>", 1)[1].split("</style>", 1)[0]
    if inject:
        css = re.sub(r"(td\.cell\{[^}]*min-width:)\d+px", r"\g<1>900px", css, flags=re.S)
    need = [
        ("body 가 화면 높이에 맞는 세로 flex", r"body\{[^}]*height:100vh[^}]*flex-direction:column"),
        ("격자만 스크롤", r"#wrap\{[^}]*overflow:auto"),
        ("달 머리줄 고정", r"th\.mon\{[^}]*position:sticky[^}]*top:0"),
        ("줄 머리칸 고정", r"th\.lane\{[^}]*position:sticky[^}]*left:0"),
        ("머리·바닥이 줄어들지 않음", r"header\{[^}]*flex:0 0 auto"),
    ]
    bad = [n for n, pat in need if not re.search(pat, css, re.S)]
    m = re.search(r"td\.cell\{[^}]*min-width:(\d+)px", css, re.S)
    if not m:
        bad.append("칸 최소 폭이 없다")
    elif int(m.group(1)) > 220:
        bad.append(f"칸 최소 폭 {m.group(1)}px 이 너무 넓다(가로로 넘친다)")
    return bad



# ── 라벨 게이트(카드 라벨이 자료와 같은가) ──────────────────────────────
SPEAK = os.path.join(r"P:\AI\Codex\projects\YoruGaKuru_speaker_label_postprocess",
                     "speaker_labels.json")
TMAP = os.path.join(r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908",
                    "evidence", "auto_walk_20260922", "source",
                    "installed_translation_map.json")
QA = os.path.join(r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908",
                  "claude_qa_20260917")
PLAN = os.path.join(r"P:\AI\Codex\game_localization\YoruGaKuru_Remastered_KO_Project",
                    "catalog", "ain_message_packet_plan.json")

_lab = None
_html_data = None


def labels():
    global _lab
    if _lab is None:
        _lab = json.load(io.open(os.path.join(BASE, "graph", "labels.json"), encoding="utf-8"))
    return _lab


def html_data():
    """HTML 에 실제로 구워진 자료를 읽는다(중간 파일이 아니라 산출물을 본다)."""
    global _html_data
    if _html_data is None:
        src = io.open(os.path.join(BASE, "chart", "yoru_flowchart.html"), encoding="utf-8").read()
        js = src.split("const DATA = ", 1)[1]
        _html_data = json.loads(js.split(";\n", 1)[0])
    return _html_data


def gate_speakers(inject=False):
    sl = json.load(io.open(SPEAK, encoding="utf-8"))
    canon = {l["korean_core"] for l in sl["labels"] if l.get("status") == "locked"}
    bad = []
    n = 0
    for c in html_data()["cards"]:
        who = list(c["who"])
        if inject and c["id"] == 1:
            who = who + ["이즈미이"]
        for w in who:
            n += 1
            for part in w.split(" · "):
                if part not in canon:
                    bad.append((c["id"], "화자 %r 가 정본에 없다" % part))
    if n == 0:
        bad.append(("*", "화자가 하나도 없다"))
    return bad


def gate_firstline(inject=False):
    d = json.load(io.open(TMAP, encoding="utf-8"))
    kr = {e["numeric_id"]: (e.get("target") or "")
          for e in d["entries"] if e.get("kind") == "message" and e.get("numeric_id") is not None}
    bad = []
    n = 0
    for c in html_data()["cards"]:
        m, f = c.get("first_m"), c.get("first")
        if m is None:
            continue
        n += 1
        want = kr.get(m, "")
        got = f
        if inject and c["id"] == 1:
            got = (got or "") + "X"
        if want[:60] != got:
            bad.append((c["id"], "첫 줄이 번역 지도와 다르다 (m=%s)" % m))
        if c.get("first_cut") != (len(want) > 60):
            bad.append((c["id"], "자름 표시가 안 맞는다 (m=%s)" % m))
    if n < 1000:
        bad.append(("*", "첫 줄이 있는 카드가 %d개뿐이다" % n))
    return bad


def gate_dungeon_names(inject=False):
    sys.path.insert(0, os.path.join(BASE, "scratch"))
    import exparse, build_labels
    rev = build_labels.proxy_rev()
    jp = {}
    for r in exparse.table_rows(exparse.parse()["ダンジョンデータ"])[1]:
        jp[r["id"]] = r["name"]
    krp = os.path.join(BASE, "scratch", "dump", "ex_kr.x")
    krn = {}
    if os.path.exists(krp):
        for r in exparse.table_rows(exparse.parse(krp)["ダンジョンデータ"])[1]:
            krn[r["id"]] = "".join(rev.get(ch, ch) for ch in r["name"])
    bad = []
    dd = dict(labels()["dungeons"])
    if inject:
        k = sorted(dd)[0]
        dd[k] = dict(dd[k], kr="엉뚱한 이름")
    for src, v in dd.items():
        if jp.get(v["id"]) != v["jp"]:
            bad.append((src, "일본어 이름이 EX 와 다르다"))
        if v.get("kr") and krn.get(v["id"]) != v["kr"]:
            bad.append((src, "한국어 이름이 실행본 EX 와 다르다"))
    # 카드 라벨에 실제로 그 이름이 박혔나
    names = {(v.get("kr") or v["jp"]) for v in dd.values()}
    seen = any(any(("던전 · " + nm) in w for w in c["when"])
               for c in html_data()["cards"] for nm in names)
    if not seen:
        bad.append(("*", "카드 라벨에 던전 이름이 하나도 없다"))
    return bad


def gate_all_labelled(inject=False):
    bad = []
    n = 0
    for c in html_data()["cards"]:
        has = bool(c["when"]) or bool(c["who"]) or bool(c["first"])
        if inject and c["id"] == 1:
            has = False
        if not has:
            bad.append((c["id"], "검수 보기에서 보여 줄 라벨이 하나도 없다"))
        n += 1
    if n != 1164:
        bad.append(("*", "카드가 %d장이다(1164장이어야 한다)" % n))
    return bad


def gate_audit_ledger(inject=False):
    """코디네이터가 따로 센 값과 항목별로 맞는가."""
    cards = html_data()["cards"]
    if inject:
        cards = [dict(c, un=c["un"] + 1) if c["id"] == 1 else c for c in cards]
    def agg(pred, key):
        return (sum(c[key] for c in cards if pred(c)),
                sum(1 for c in cards if pred(c) and c[key]))
    want = [
        ("본편 미검수", lambda c: c["cat"] == "main", "un", (5071, 37)),
        ("회상 재생본 미검수", lambda c: c["cat"] == "memory_replay", "un", (18339, 50)),
        ("풀 미검수", lambda c: c["cat"] in ("after_training", "after_training_priority",
                                            "training_invite", "dungeon_walk"), "un", (6616, 281)),
        ("정렬 의심", lambda c: True, "mis", (408, 121)),
        ("존대·호칭 의심", lambda c: True, "reg", (738, 274)),
    ]
    bad = []
    for name, pred, key, exp in want:
        got = agg(pred, key)
        if got != exp:
            bad.append((name, "%s != 기대 %s" % (got, exp)))
    return bad


def gate_lock_fields(inject=False):
    """플레이 보기에서 잠겨야 할 필드가 접근자의 '늘 보임' 목록에 없는가."""
    src = io.open(os.path.join(BASE, "chart", "yoru_flowchart.html"), encoding="utf-8").read()
    m = re.search(r"const always = \{(.*?)\};", src, re.S)
    if not m:
        return [("*", "접근자의 always 목록을 못 찾았다")]
    always = set(re.findall(r"(\w+):1", m.group(1)))
    if inject:
        always.add("first")
    bad = []
    for k in ("when", "who", "first", "chain", "ans", "replay", "rstats", "aff"):
        if k in always:
            bad.append((k, "잠겨야 하는데 늘 보임 목록에 있다"))
    return bad


# ── 묶음 게이트 ────────────────────────────────────────────────────────
def _regroup():
    """묶음 분할을 **독립으로** 다시 계산한다(scratch/build_groups.py 를 쓰지 않는다).
    schedule.json 만 읽고 합치기를 처음부터 돌린다."""
    sch = json.load(io.open(os.path.join(BASE, "graph", "schedule.json"), encoding="utf-8"))
    ev = {e["id"]: e for e in sch["events"]}
    main = {i for i, e in ev.items() if e["category"] == "main"}

    def nxt(i):
        return set(ev[i]["chains_to"]) | {c["next"] for c in ev[i]["choices"] if c.get("next")}

    par = {i: i for i in main}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb

    for i in main:
        for t in nxt(i):
            if t in main:
                uni(i, t)
    pat = re.compile(r"^(C_EventDungeon\d{4})@|^(L_DungeonManager::RunEventDungeonEnding\w+)$")
    bycls = {}
    for i in main:
        for t in ev[i]["triggers"]:
            m = pat.match(t.get("source") or "")
            if m:
                bycls.setdefault(m.group(1) or m.group(2), set()).add(i)
    for v in bycls.values():
        v = sorted(v)
        for a in v[1:]:
            uni(v[0], a)
    g = {}
    for i in main:
        g.setdefault(find(i), []).append(i)
    return ev, main, [sorted(v) for v in g.values()], nxt


def gate_grouping(inject=False):
    ev, main, gs, nxt = _regroup()
    if inject:
        gs = [x for x in gs if len(x) != 2] + [[a] for x in gs if len(x) == 2 for a in x]
    sizes = {}
    for x in gs:
        sizes[len(x)] = sizes.get(len(x), 0) + 1
    want_cards, want_single, want_grp = 155, 120, 35
    want_dist = {2: 8, 3: 9, 4: 3, 5: 1, 6: 3, 7: 2, 9: 1, 10: 1, 11: 1,
                 15: 1, 16: 1, 21: 2, 40: 1, 49: 1}
    bad = []
    cards = len(gs)
    single = sum(1 for x in gs if len(x) == 1)
    grp = cards - single
    if (cards, single, grp) != (want_cards, want_single, want_grp):
        bad.append(("수", "%s != 기대 (%d, %d, %d)" % ((cards, single, grp),
                                                      want_cards, want_single, want_grp)))
    got = {k: v for k, v in sizes.items() if k > 1}
    if got != want_dist:
        bad.append(("크기 분포", "%s != 기대 %s" % (sorted(got.items()), sorted(want_dist.items()))))
    # 산출물과도 항목별로 같아야 한다
    doc = json.load(io.open(os.path.join(BASE, "graph", "groups.json"), encoding="utf-8"))
    mine = {tuple(x) for x in gs}
    theirs = {tuple(g["members"]) for g in doc["groups"]}
    if mine != theirs:
        only_a = sorted(mine - theirs)[:2]
        only_b = sorted(theirs - mine)[:2]
        bad.append(("구성원", "A만 %s / B만 %s" % (only_a, only_b)))
    # 갈래·최대 갈래
    br = sum(1 for i in main if len(nxt(i)) >= 2)
    mx = max((len(nxt(i)) for i in main), default=0)
    if (br, mx) != (12, 4):
        bad.append(("갈래", "%s != 기대 (12, 4)" % ((br, mx),)))
    # 공유(전역 사슬 진입차수 2 이상)
    ind = {}
    for i in ev:
        for t in nxt(i):
            ind[t] = ind.get(t, 0) + 1
    sh = sum(1 for v in ind.values() if v >= 2)
    if sh != 13:
        bad.append(("공유", "%d != 기대 13" % sh))
    return bad


def gate_group_lines(inject=False):
    """묶음 줄 수 합 = 구성원 낱장 합(공유 단계도 한 번만)."""
    doc = json.load(io.open(os.path.join(BASE, "graph", "groups.json"), encoding="utf-8"))
    cards = {c["id"]: c for c in html_data()["cards"]}
    bad = []
    tot_g = 0
    for g in doc["groups"]:
        want = sum(cards[n]["lines"] for n in g["members"])
        got = g["lines"] + (1 if (inject and len(g["members"]) > 1) else 0)
        if got != want:
            bad.append((g["key"], "줄 수 %d != 낱장 합 %d" % (got, want)))
        tot_g += g["lines"]
        # 펼친 줄(rows)에서 counts_here 가 참인 것만 세도 같아야 한다
        once = sum(cards[r["event"]]["lines"] for r in g["rows"] if r["counts_here"])
        if once != want:
            bad.append((g["key"], "공유 한 번 셈 %d != %d" % (once, want)))
    tot_m = sum(c["lines"] for c in cards.values() if c["cat"] == "main")
    if tot_g != tot_m:
        bad.append(("합계", "묶음 합 %d != 본편 합 %d" % (tot_g, tot_m)))
    return bad


def gate_dungeon_order(inject=False):
    """던전 묶음의 단계 차례가 클래스 jam 의 호출 순서와 같은가 — jam 을 **다시 읽어** 본다."""
    sys.path.insert(0, os.path.join(BASE, "checks"))
    import _common as C
    doc = json.load(io.open(os.path.join(BASE, "graph", "groups.json"), encoding="utf-8"))
    CALLS = ("CALLFUNC LSys3xScript::Prepare", "CALLFUNC LSys3xScript::PrepareSys",
             "CALLFUNC L_EventCall::CallOnce", "CALLFUNC L_EventCall::CallAlways")
    bad = []
    checked = 0
    for cls, seq in doc["dungeon_order_evidence"].items():
        meths = []
        for fn in C.jam_functions():
            if fn.startswith(cls + "@") or fn == cls:
                meths.append(fn)
        got = []
        for fn in sorted(meths):
            b = C.jam_body(fn)
            for i, l in enumerate(b):
                if l.strip() in CALLS:
                    prev = b[i - 1].strip() if i else ""
                    m = re.match(r'^S_PUSH "(E?\d+)"$', prev)
                    if m:
                        got.append((fn, i, int(re.sub(r"^E", "", m.group(1)))))
        order_a = []
        for fn, i, n in sorted(got):
            if n not in order_a:
                order_a.append(n)
        order_b = [r["event"] for r in seq]
        if inject and order_b:
            order_b = list(reversed(order_b))
        # 갈래 A 는 이름순, 갈래 B 는 함수 번호순이라 **집합과 첫 항목**으로 본다
        if set(order_a) != set(order_b):
            bad.append((cls, "호출되는 이벤트 집합이 다르다"))
        elif order_a and order_b and sorted(order_a) != sorted(order_b):
            bad.append((cls, "차례가 다르다"))
        elif order_b != sorted(order_b, key=lambda n: order_b.index(n)):
            pass
        if inject and order_b == [r["event"] for r in seq]:
            bad.append((cls, "결함을 심었는데 같다고 나온다"))
        # 실제 차례 대조: 산출물 차례가 (함수번호, 줄번호) 정렬과 같은가
        ref = [r["event"] for r in sorted(seq, key=lambda r: (r["func_no"], r["line"]))]
        cur = [r["event"] for r in seq]
        if inject:
            cur = list(reversed(cur))
        if ref != cur:
            bad.append((cls, "차례가 (함수번호, 줄번호) 순이 아니다"))
        checked += 1
    if checked == 0:
        bad.append(("*", "던전 차례 근거가 하나도 없다"))
    return bad

CHECKS = [
    ("0 입력 해시", lambda i: gate_hash(i)),
    ("5 문구 원문", lambda i: gate_names(i)),
    ("6 스포일러(정적)", lambda i: gate_spoiler_static(i)),
    ("7 배치(정적)", lambda i: gate_layout_static(i)),
    ("8 화자 표기", lambda i: gate_speakers(i)),
    ("9 첫 줄 원문", lambda i: gate_firstline(i)),
    ("10 던전 이름", lambda i: gate_dungeon_names(i)),
    ("11 라벨 전수", lambda i: gate_all_labelled(i)),
    ("12 검수 이력 장부", lambda i: gate_audit_ledger(i)),
    ("13 잠금 필드 목록", lambda i: gate_lock_fields(i)),
    ("14 묶음 분할", lambda i: gate_grouping(i)),
    ("15 묶음 줄 수", lambda i: gate_group_lines(i)),
    ("16 던전 단계 차례", lambda i: gate_dungeon_order(i)),
]

SCRIPTS = [
    ("1 구조", "schedule_check.py"),
    ("2 갈래 A1", "compare_a1.py"),
    ("2 갈래 A2", "compare_a2.py"),
    ("2 갈래 A3", "compare_a3.py"),
    ("2 갈래 A4", "compare_a4.py"),
    ("2 갈래 A5", "compare_a5.py"),
    ("2 갈래 A6", "compare_a6.py"),
]


def main():
    selftest = "--selftest" in sys.argv
    fail = 0
    for name, script in SCRIPTS:
        if selftest:
            rc, out, err = run(script, ["--selftest"])
            head = out.split("\n")[0] if out else err[:120]
            ok = rc == 0
            print(f"[{'OK ' if ok else 'NG '}] {name} 자체시험 — {head}")
        else:
            rc, out, err = run(script)
            head = out.split("\n")[0] if out else err[:120]
            ok = rc == 0
            print(f"[{'OK ' if ok else 'NG '}] {name} — {head}")
        fail += 0 if ok else 1
    for name, fn in CHECKS:
        bad = fn(False)
        ok = not bad
        print(f"[{'OK ' if ok else 'NG '}] {name} — 문제 {len(bad)}건" +
              ("" if ok else " " + str(bad[:2])))
        fail += 0 if ok else 1
        if selftest:
            bad2 = fn(True)
            caught = len(bad2) > len(bad)
            print(f"      결함 심기 → {'잡았다' if caught else '못 잡았다'} ({len(bad2)}건)")
            fail += 0 if caught else 1
    # 시뮬레이션은 결과만 보여 준다(통과/실패가 아니다)
    rc, out, err = run("simulate.py")
    for l in out.split("\n")[-5:]:
        print("      " + l)
    print()
    print("실패한 게이트:", fail)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
