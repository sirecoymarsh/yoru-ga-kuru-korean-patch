#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""차트 v2 게이트 8개 — 산출물 chart/yoru_flowchart_v2.html 자체를 본다.

  python stage_v2.py              게이트 8개
  python stage_v2.py --selftest   게이트마다 결함을 심은 사본(scratch/v2/inject/*.html)을 만들어
                                  그 게이트가 실제로 기각하는지 확인한다

  1 카드 한 번    카드 155장이 정확히 한 페이지(시작 달 또는 회상)에 한 번 — 자료 + 실제 DOM(레인·달력)
  2 사건 한 번    사건 1,164장 전부 카드 또는 서랍에(누락 0·중복 0) — 자료 + 실제 DOM(접힘·전부 펼침)
  3 셈           달별 카드 합 155, 서랍 칩 합 = 카드 밖 사건 수, 칩 숫자 = 펼친 줄 수, 요약 띠 = 실제 DOM
  4 사슬         연결선 + 달 이동 표지 (+ 접힌 묶음 안) = chains_to ∪ choices.next — 자료 + 실제 DOM
  5 라벨         언제·누구·첫 줄 누락 0(자리표는 근거가 있을 때만), 첫 줄은 원자료와 같다 — 자료 + DOM
  6 교정 배지     배지 합 = 최종 지도에서 카드 범위에 든 줄 수, 사건·카드·쪽마다 독립 재계산과 같다 — 자료 + DOM
  7 구조         HTML·JSON 파싱, 외부 URL 0, 크기 상한 30MB, file:// 로 열려 JS 오류 0
  8 플레이 보기   첫 줄·대사 전문(원문·한국어)·답 문구·교정 문안이 DOM 에 없다
                (#play 로 처음 연 상태 · 쪽·상태 전부 · 옆 패널 전부 · 검수→플레이 전환 뒤)

기대값은 원자료(graph/schedule.json·groups.json·lines_kr.jsonl, scratch/dump/messages.txt, 09-23 최종 지도)에서
여기서 **따로** 다시 계산한다. build_chart_v2.py 를 불러 쓰지 않는다(같은 코드를 쓰면 맹점까지 물려받는다).
DOM 은 헤드리스 Chrome 으로 file:// 를 열어 뜬다(서버 없음). 페이지의 자체 시험(#selftest=…)은 쪽·상태마다
#page 의 outerHTML 만 적어 내고, 셈은 전부 여기서 한다.
"""
import sys, os, io, json, re, html, subprocess, collections, time, hashlib
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ART = os.path.join(BASE, "chart", "yoru_flowchart_v2.html")
INJ = os.path.join(BASE, "scratch", "v2", "inject")
PROFILE = os.path.join(BASE, "scratch", "v2", "chrome-prof-gate")
TMP = os.path.join(BASE, "scratch", "v2", "tmp")
FINAL = (r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\claude_qa_20260923"
         r"\pending_merge\final_map_20260923.jsonl")
SIZE_CAP = 30 * 1024 * 1024
CHROMES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
MONTH_PAGES = [str(m) for m in range(4, 12)]
ALL_PAGES = MONTH_PAGES + ["mem"]


# ═══ 원자료(독립 계산) ═══════════════════════════════════════════════
class Source:
    def __init__(self):
        g = os.path.join(BASE, "graph")
        self.sch = json.load(io.open(os.path.join(g, "schedule.json"), encoding="utf-8"))
        self.ev = {e["id"]: e for e in self.sch["events"]}
        self.groups = json.load(io.open(os.path.join(g, "groups.json"), encoding="utf-8"))["groups"]
        self.lines = {}
        with io.open(os.path.join(g, "lines_kr.jsonl"), encoding="utf-8") as fp:
            for ln in fp:
                r = json.loads(ln)
                self.lines[r["event"]] = r["seq"]
        with io.open(os.path.join(BASE, "scratch", "dump", "messages.txt"), encoding="utf-8") as fp:
            self.msgs = fp.read().split("\n")
        self.fm = [json.loads(l) for l in io.open(FINAL, encoding="utf-8") if l.strip()]

    # 사슬
    def edges(self):
        out = set()
        for e in self.sch["events"]:
            for d in e["chains_to"]:
                out.add((e["id"], d))
            for c in e["choices"]:
                if c.get("next"):
                    out.add((e["id"], c["next"]))
        return out

    # 카드(묶음) — 키는 가장 작은 구성원 번호
    def cards(self):
        return {"G%05d" % min(g["members"]): g for g in self.groups}

    def card_entry(self, g):
        return g["entries"][0] if g["entries"] else g["members"][0]

    # 시작 달 — 트리거 날짜 중 가장 이른 것, 없으면 EX 발생월
    def start_month(self, e):
        ms = []
        for t in e["triggers"]:
            d = t.get("date")
            if d and d[0]:
                ms.append(tuple(d))
            if t.get("date_from"):
                ms.append(tuple(t["date_from"]))
            if t["kind"] == "conditional" and t["raw_args"][0] != -1:
                ms.append((t["raw_args"][0], t["raw_args"][1]))
            if t["kind"] == "pool" and t.get("month"):
                ms.append((t["month"], 0))
            for gd in t.get("guards") or []:
                if gd.startswith("!("):
                    continue
                mm = re.search(r"m_nMonth == (\d+)", gd)
                if mm:
                    dd = re.search(r"m_nDay == (\d+)", gd)
                    ms.append((int(mm.group(1)), int(dd.group(1)) if dd else 0))
            src = t.get("source") or ""
            if src == "呼出／オープニング":
                ms.append((4, 9))
            if src == "呼出／エンディング実行":
                ms.append((11, 17))
            for mt in re.finditer(r"(!\()?L_Calendar::(IsTodayOrAfter|IsDay)\((\d+), (\d+)\)",
                                  t.get("condition_expr") or ""):
                if not mt.group(1):
                    ms.append((int(mt.group(3)), int(mt.group(4))))
        if ms:
            return min(ms)[0]
        mr = e.get("month_range") or []
        return mr[0] if mr else None

    # 교정 — m → 사건(메시지 범위), 분류는 설계 문서의 정의
    def fix(self):
        m2e = {}
        for e in self.sch["events"]:
            ms = e["messages"]
            if ms["count"]:
                for m in range(ms["first_m"], ms["last_m"] + 1):
                    m2e[m] = e["id"]
        per = collections.defaultdict(lambda: [0, 0, 0, 0])
        inr = 0
        for r in self.fm:
            i = m2e.get(r["m_id"])
            if i is None:
                continue
            inr += 1
            s = r["sources"]
            if any(x == "claude" or x.startswith("opus_") for x in s):
                k = 1
            elif any(x.startswith("pending:") for x in s):
                k = 2
            else:
                k = 3
            per[i][0] += 1
            per[i][k] += 1
        return per, inr

    # 첫 줄 — 화자 줄이 아닌 첫 비어 있지 않은 한국어 줄(60자에서 자름)
    def first(self, i):
        for s in self.lines[i]:
            if s["sp"] is None and (s.get("kr") or "").strip():
                return s["kr"][:60], len(s["kr"]) > 60, s["kr"]
        return None, False, None

    def speakers(self, i):
        out = set()
        for s in self.lines[i]:
            if s["sp"]:
                out |= set(s["sp"].split(" · "))
        return out

    # 플레이 보기에서 DOM 에 있으면 안 되는 문자열
    def forbidden(self):
        firsts, longs = set(), set()
        for i in self.ev:
            f, cut, full = self.first(i)
            if f:
                firsts.add(f)
                firsts.add(full)
        for i, seq in self.lines.items():
            for s in seq:
                if s["sp"] is None:
                    k = (s.get("kr") or "").strip()
                    if len(k) >= 8:
                        longs.add(k)
                    j = self.msgs[s["m"]].strip()
                    if len(j) >= 8:
                        longs.add(j)
        for g in self.groups:
            for r in g["rows"]:
                v = r["via"]
                if v.get("kind") == "answer" and v.get("text_kr"):
                    (longs if len(v["text_kr"]) >= 8 else firsts).add(v["text_kr"])
        for e in self.sch["events"]:
            for c in e["choices"]:
                t = (c.get("text_jp") or "").strip()
                if t:
                    (longs if len(t) >= 8 else firsts).add(t)
        for r in self.fm:
            p = (r.get("proposed") or "").strip()
            if len(p) >= 8:
                longs.add(p)
        return firsts, longs


_SRC = None


def S():
    global _SRC
    if _SRC is None:
        _SRC = Source()
    return _SRC


# ═══ 산출물 읽기 ═══════════════════════════════════════════════════════
BLOCK = r'<script type="application/json" id="%s">(.*?)</script>'


def read_blocks(text):
    m = re.search(BLOCK % "yoru-data", text, re.S)
    m2 = re.search(BLOCK % "yoru-dialogue", text, re.S)
    if not m or not m2:
        raise ValueError("자료 블록이 없다")
    return json.loads(m.group(1)), json.loads(m2.group(1))


def js_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def with_data(text, fn):
    m = re.search(BLOCK % "yoru-data", text, re.S)
    d = json.loads(m.group(1))
    fn(d)
    return text[:m.start(1)] + js_json(d) + text[m.end(1):]


# ═══ Chrome(file://, 서버 없음) ═════════════════════════════════════════
def chrome():
    for p in CHROMES:
        if os.path.exists(p):
            return p
    raise SystemExit("Chrome/Edge 가 없다")


def file_url(path, h):
    return "file:///" + os.path.abspath(path).replace("\\", "/") + h


_DOM = {}


def dump(path, h):
    st = os.stat(path)
    key = (os.path.abspath(path), st.st_size, st.st_mtime_ns, h)
    if key in _DOM:
        return _DOM[key]
    os.makedirs(PROFILE, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    env = dict(os.environ, TEMP=TMP, TMP=TMP)
    args = [chrome(), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--disable-extensions", "--disable-sync", "--disable-background-networking",
            "--disable-component-update", "--user-data-dir=" + PROFILE, "--window-size=1600,1000",
            "--virtual-time-budget=30000", "--dump-dom", file_url(path, h)]
    t = time.time()
    p = subprocess.run(args, capture_output=True, env=env, timeout=600)
    out = p.stdout.decode("utf-8", "replace")
    _DOM[key] = out
    print("      · Chrome %s%s %.1fs %.1fMB" % (os.path.basename(path), h, time.time() - t,
                                               len(out) / 1e6), flush=True)
    return out


def selftest_out(path, mode):
    d = dump(path, "#selftest=" + mode)
    m = re.search(r'<pre id="selftest-out">(.*?)</pre>', d, re.S)
    if not m or not m.group(1).strip():
        return None, d
    return json.loads(html.unescape(m.group(1))), d


# ═══ 작은 DOM(파이썬 html.parser) ══════════════════════════════════════
VOID = {"br", "img", "input", "meta", "link", "hr", "area", "base", "col", "embed", "source", "track", "wbr"}


class Node:
    __slots__ = ("tag", "attrs", "kids", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.kids, self.parent = tag, attrs, [], parent

    def text(self):
        return _text(self)

    def iter(self):
        st = [self]
        while st:
            n = st.pop()
            yield n
            for k in reversed(n.kids):
                if not isinstance(k, str):
                    st.append(k)


def _text(n):
    out = []

    def rec(x):
        for k in x.kids:
            if isinstance(k, str):
                out.append(k)
            else:
                rec(k)
    rec(n)
    return "".join(out)


class TB(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        n = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.kids.append(n)

    def handle_endtag(self, tag):
        x = self.cur
        while x is not None and x.tag != tag:
            x = x.parent
        if x is not None and x.parent is not None:
            self.cur = x.parent

    def handle_data(self, d):
        self.cur.kids.append(d)


def parse(h):
    t = TB()
    t.feed(h)
    t.close()
    return t.root


def by_attr(root, name):
    return [n for n in root.iter() if name in n.attrs]


def cls(n):
    return n.attrs.get("class", "").split()


# ═══ 게이트 ══════════════════════════════════════════════════════════════
class Art:
    """산출물 하나(진짜 또는 결함 심은 사본)."""
    _cache = {}

    def __new__(cls_, path):
        k = os.path.abspath(path)
        if k not in cls_._cache:
            o = super().__new__(cls_)
            o.path = path
            o.text = io.open(path, encoding="utf-8").read()
            o.data, o.dlg = read_blocks(o.text)
            o._rev = o._play = None
            cls_._cache[k] = o
        return cls_._cache[k]

    def review(self):
        if self._rev is None:
            out, raw = selftest_out(self.path, "review")
            if out is None:
                raise RuntimeError("자체 시험 결과가 없다(JS 오류?): " +
                                   (re.search(r'<pre id="errors">(.*?)</pre>', raw, re.S) or [None, "?"])[1][:300])
            self._rev = out
            self._states = collections.defaultdict(dict)
            for s in out["states"]:
                self._states[s["state"]][s["page"]] = s
        return self._rev

    def state(self, name):
        self.review()
        return self._states[name]

    def play(self):
        if self._play is None:
            out, raw = selftest_out(self.path, "play")
            if out is None:
                raise RuntimeError("플레이 자체 시험 결과가 없다")
            self._play = (out, raw)
        return self._play


def gate_cards(path):
    """1 카드 155장이 정확히 한 페이지에 한 번."""
    a, src = Art(path), S()
    bad = []
    want = src.cards()
    keys = [c["key"] for c in a.data["cards"]]
    if len(want) != 155:
        bad.append("원자료 카드 수가 %d" % len(want))
    dup = [k for k, n in collections.Counter(keys).items() if n > 1]
    if dup:
        bad.append("자료에 두 번 나오는 카드 %s" % dup[:3])
    if set(keys) != set(want):
        bad.append("자료 카드 집합이 groups.json 과 다르다: 빠짐 %s 더함 %s" % (
            sorted(set(want) - set(keys))[:3], sorted(set(keys) - set(want))[:3]))
    exp_page = {}
    for k, g in want.items():
        e = src.ev[src.card_entry(g)]
        exp_page[k] = str(src.start_month(e))
        mins = min(src.start_month(src.ev[x]) for x in (g["entries"] or g["members"]))
        if str(mins) != exp_page[k]:
            bad.append("%s 진입점 중 더 이른 달이 있다(%s < %s)" % (k, mins, exp_page[k]))
    for c in a.data["cards"]:
        if c["key"] in exp_page and c["page"] != exp_page[c["key"]]:
            bad.append("%s 자료상 %s 페이지, 기대 %s" % (c["key"], c["page"], exp_page[c["key"]]))
        if c["key"] in want and sorted(c["members"]) != sorted(want[c["key"]]["members"]):
            bad.append("%s 구성원이 groups.json 과 다르다" % c["key"])
    # DOM — 레인·달력, 접힘·펼침
    for state in ("lane:fold:closed", "cal:fold:closed", "lane:exp:open", "cal:exp:open"):
        seen = collections.defaultdict(list)
        for pg, s in a.state(state).items():
            for n in by_attr(parse(s["html"]), "data-card"):
                seen[n.attrs["data-card"]].append(pg)
        for k in want:
            pl = seen.get(k, [])
            if len(pl) != 1:
                bad.append("%s: %s 가 DOM 에 %d번 %s" % (state, k, len(pl), pl[:3]))
            elif pl[0] != exp_page[k]:
                bad.append("%s: %s 가 %s 페이지(기대 %s)" % (state, k, pl[0], exp_page[k]))
        extra = set(seen) - set(want)
        if extra:
            bad.append("%s: 모르는 카드 %s" % (state, sorted(extra)[:3]))
    return bad


def gate_events(path):
    """2 사건 1,164장 전부 카드 또는 서랍에 한 번."""
    a, src = Art(path), S()
    bad = []
    allid = set(src.ev)
    in_card = collections.Counter(n for g in src.groups for n in g["members"])
    # 자료
    cnt = collections.Counter()
    for c in a.data["cards"]:
        cnt.update(c["members"])
    for ch in a.data["chips"]:
        cnt.update(ch["entries"])
    miss = allid - set(cnt)
    dup = [i for i, n in cnt.items() if n > 1]
    if miss:
        bad.append("자료: 어디에도 없는 사건 %d장 %s" % (len(miss), sorted(miss)[:5]))
    if dup:
        bad.append("자료: 두 곳에 있는 사건 %s" % sorted(dup)[:5])
    if set(cnt) - allid:
        bad.append("자료: 모르는 사건 %s" % sorted(set(cnt) - allid)[:5])
    # DOM — 전부 펼침: data-ev 하나하나가 사건 하나
    for state in ("lane:exp:open", "cal:exp:open"):
        seen = collections.Counter()
        for pg, s in a.state(state).items():
            for n in by_attr(parse(s["html"]), "data-ev"):
                seen[int(n.attrs["data-ev"])] += 1
        miss = allid - set(seen)
        dup = [i for i, n in seen.items() if n > 1]
        if miss:
            bad.append("%s: DOM 에 없는 사건 %d장 %s" % (state, len(miss), sorted(miss)[:5]))
        if dup:
            bad.append("%s: DOM 에 두 번 나오는 사건 %s" % (state, sorted(dup)[:5]))
    # DOM — 묶음 접힘 + 서랍 펼침: 낱장·줄의 data-ev + 묶음 알약의 data-members
    for state in ("lane:fold:open", "cal:fold:open"):
        seen = collections.Counter()
        for pg, s in a.state(state).items():
            root = parse(s["html"])
            for n in root.iter():
                if "data-ev" in n.attrs:
                    seen[int(n.attrs["data-ev"])] += 1
                if "data-members" in n.attrs:
                    seen.update(int(x) for x in n.attrs["data-members"].split(","))
        miss = allid - set(seen)
        dup = [i for i, n in seen.items() if n > 1]
        if miss or dup:
            bad.append("%s: 없는 %d · 겹침 %d %s" % (state, len(miss), len(dup), (sorted(miss) + sorted(dup))[:5]))
    return bad


def gate_counts(path):
    """3 달별 카드 합 155 · 서랍 칩 합 = 카드 밖 사건 수 · 칩 숫자 = 펼친 줄 · 요약 띠 = 실제."""
    a, src = Art(path), S()
    bad = []
    outside = len(src.ev) - len({n for g in src.groups for n in g["members"]})
    pages = {p["key"]: p for p in a.data["pages"]}
    if sum(p["sum"]["cards"] for p in pages.values()) != 155:
        bad.append("자료: 쪽별 카드 합 %d != 155" % sum(p["sum"]["cards"] for p in pages.values()))
    if sum(p["sum"]["entries"] for p in pages.values()) != outside:
        bad.append("자료: 쪽별 서랍 합 %d != 카드 밖 사건 %d" % (sum(p["sum"]["entries"] for p in pages.values()), outside))
    if sum(len(ch["entries"]) for ch in a.data["chips"]) != outside:
        bad.append("자료: 칩 합 %d != %d" % (sum(len(ch["entries"]) for ch in a.data["chips"]), outside))
    dom_cards = dom_entries = 0
    for pg, s in a.state("lane:fold:closed").items():
        root = parse(s["html"])
        band = parse(s["band"])
        cell = [n for n in by_attr(band, "data-goto") if n.attrs["data-goto"] == pg]
        if len(cell) != 1:
            bad.append("요약 띠에 %s 칸이 %d개" % (pg, len(cell)))
            continue
        cell = cell[0]
        nc = len(by_attr(root, "data-card"))
        chips = [n for n in by_attr(root, "data-chip")]
        ne = sum(int(n.attrs["data-count"]) for n in chips)
        dom_cards += nc
        dom_entries += ne
        sc, se = int(cell.attrs["data-sum-cards"]), int(cell.attrs["data-sum-entries"])
        vis = _text(cell)
        mv = re.search(r"카드 (\d+) · 서랍 (\d+)", vis) or re.search(r"서랍 (\d+)", vis)
        shown = (int(mv.group(1)), int(mv.group(2))) if mv and mv.lastindex == 2 else (0, int(mv.group(1)) if mv else -1)
        if (sc, se) != (nc, ne):
            bad.append("%s 요약 띠 (카드 %d, 서랍 %d) != DOM (%d, %d)" % (pg, sc, se, nc, ne))
        if shown != (sc, se):
            bad.append("%s 요약 띠 글자 %s != 속성 %s" % (pg, shown, (sc, se)))
        # 칩 글자 숫자 = data-count
        for n in chips:
            b = [k for k in n.kids if not isinstance(k, str) and k.tag == "b"]
            if not b or _text(b[0]).strip() != n.attrs["data-count"]:
                bad.append("%s 칩 %s 글자 숫자가 data-count 와 다르다" % (pg, n.attrs["data-chip"]))
    if dom_cards != 155:
        bad.append("DOM 카드 합 %d != 155" % dom_cards)
    if dom_entries != outside:
        bad.append("DOM 서랍 칩 합 %d != %d" % (dom_entries, outside))
    # 칩 숫자 = 펼친 목록의 줄 수(공유로 한 번 더 나온 줄은 data-ref 라 안 센다)
    for pg, s in a.state("lane:fold:open").items():
        root = parse(s["html"])
        rows = collections.Counter(n.attrs["data-owner"] for n in by_attr(root, "data-owner") if "data-ev" in n.attrs)
        for n in by_attr(root, "data-chip"):
            k = "d:" + n.attrs["data-chip"]
            if rows.get(k, 0) != int(n.attrs["data-count"]):
                bad.append("%s 칩 %s: 숫자 %s != 펼친 줄 %d" % (pg, n.attrs["data-chip"], n.attrs["data-count"], rows.get(k, 0)))
    return bad


def gate_edges(path):
    """4 연결선 + 달 이동 표지 (+ 접힌 묶음 안) = chains_to ∪ choices.next."""
    a, src = Art(path), S()
    bad = []
    want = src.edges()
    got = [(x[0], x[1]) for x in a.data["edges"]]
    if set(got) != want or len(got) != len(want):
        bad.append("자료 사슬 %d != 원자료 %d (빠짐 %s)" % (len(got), len(want), sorted(want - set(got))[:3]))
    grp_of = {}
    for g in src.groups:
        for n in g["members"]:
            grp_of[n] = "G%05d" % min(g["members"])
    inb = {(s, d) for (s, d) in want if s in grp_of and grp_of.get(d) == grp_of[s]}
    home = {int(k): v["home"] for k, v in a.data["ev"].items()}

    def collect(state):
        seen = collections.Counter()
        kinds = {}
        for pg, s in a.state(state).items():
            for n in by_attr(parse(s["html"]), "data-edge"):
                ek = n.attrs.get("data-ek")
                if ek not in ("line", "jump"):
                    continue
                sd = tuple(int(x) for x in n.attrs["data-edge"].split(">"))
                seen[sd] += 1
                kinds[sd] = (ek, pg)
        return seen, kinds

    for state in ("lane:exp:open", "cal:exp:open"):
        seen, kinds = collect(state)
        if set(seen) != want:
            bad.append("%s: DOM 사슬 %d != %d (빠짐 %s · 더함 %s)" % (state, len(seen), len(want),
                       sorted(want - set(seen))[:3], sorted(set(seen) - want)[:3]))
        dup = [k for k, n in seen.items() if n > 1]
        if dup:
            bad.append("%s: 두 번 그린 사슬 %s" % (state, dup[:3]))
        for sd, (ek, pg) in kinds.items():
            tp = home.get(sd[1])
            if ek == "line" and tp != pg:
                bad.append("%s: %s 는 연결선인데 대상이 %s 페이지" % (state, sd, tp))
            if ek == "jump" and tp == pg:
                bad.append("%s: %s 는 달 이동인데 대상이 같은 페이지" % (state, sd))
        n_line = sum(1 for v in kinds.values() if v[0] == "line")
        n_jump = sum(1 for v in kinds.values() if v[0] == "jump")
        if n_line + n_jump != len(want):
            bad.append("%s: 연결선 %d + 달 이동 %d != %d" % (state, n_line, n_jump, len(want)))
    for state in ("lane:fold:open", "cal:fold:open"):
        seen, kinds = collect(state)
        if set(seen) & inb:
            bad.append("%s: 접힌 묶음 안 사슬이 페이지에 그려졌다 %s" % (state, sorted(set(seen) & inb)[:3]))
        if set(seen) | inb != want or len(seen) + len(inb) != len(want):
            bad.append("%s: 연결선·표지 %d + 묶음 안 %d != %d" % (state, len(seen), len(inb), len(want)))
    return bad


def gate_labels(path):
    """5 라벨(언제·누구·첫 줄) 누락 0."""
    a, src = Art(path), S()
    bad = []
    for k, e in a.data["ev"].items():
        i = int(k)
        se = src.ev[i]
        when, who, first = e.get("when") or [], e.get("who") or [], e.get("first")
        if not when or not (when[0] or "").strip():
            bad.append((i, "언제 없음"))
        elif when == ["부르는 자리 없음"] and se["triggers"]:
            bad.append((i, "트리거가 있는데 「부르는 자리 없음」"))
        if not who or not all((w or "").strip() for w in who):
            bad.append((i, "누구 없음"))
        else:
            sp = src.speakers(i)
            if e.get("psrc") == "tag" and not set(who) <= sp:
                bad.append((i, "누구가 대사 속 화자가 아니다 %s" % who))
            if e.get("psrc") != "tag" and sp:
                bad.append((i, "화자 태그가 있는데 자리표를 썼다"))
            if e.get("psrc") == "none" and (se["person"] or se["person2"]):
                bad.append((i, "인물이 있는데 「화자 표시 없음」"))
        if not first or not first.strip():
            bad.append((i, "첫 줄 없음"))
        else:
            f, cut, full = src.first(i)
            if f is None:
                if se["messages"]["count"] == 0 and first != "(대사 없음)":
                    bad.append((i, "대사가 없는데 자리표가 다르다"))
                if se["messages"]["count"] and first != "(한국어 줄 없음)":
                    bad.append((i, "한국어 줄이 없는데 자리표가 다르다"))
            elif first != f or bool(e.get("fcut")) != cut:
                bad.append((i, "첫 줄이 lines_kr 와 다르다"))
    if len(a.data["ev"]) != len(src.ev):
        bad.append(("*", "사건 기록 %d != %d" % (len(a.data["ev"]), len(src.ev))))
    # DOM — 검수 보기, 서랍 펼침: 줄마다 언제·누구·첫 줄 칸이 비어 있지 않다
    for pg, s in a.state("lane:exp:open").items():
        root = parse(s["html"])
        for n in root.iter():
            if n.tag != "div" or "row" not in cls(n):
                continue
            parts = {}
            for x in n.iter():
                for c in ("lw", "lp", "lf2"):
                    if c in cls(x):
                        parts[c] = _text(x).strip()
            miss = [c for c in ("lw", "lp", "lf2") if not parts.get(c)]
            if miss:
                bad.append((n.attrs.get("data-ev") or n.attrs.get("data-ref"), "%s DOM 줄에 %s 비었다" % (pg, miss)))
        for n in root.iter():
            if n.tag == "button" and ("pill" in cls(n) or "upill" in cls(n)):
                parts = {c: "" for c in ("dt", "l2", "l3")}
                for x in n.iter():
                    for c in parts:
                        if c in cls(x):
                            parts[c] = _text(x).strip()
                miss = [c for c, v in parts.items() if not v]
                if miss:
                    bad.append((n.attrs.get("data-card"), "%s 알약에 %s 비었다" % (pg, miss)))
    return bad


def gate_badges(path):
    """6 교정 배지 합 = 최종 지도에서 카드 범위에 든 줄 수."""
    a, src = Art(path), S()
    bad = []
    per, inr = src.fix()
    tot = 0
    for k, e in a.data["ev"].items():
        i = int(k)
        w = per.get(i, [0, 0, 0, 0])
        if e["fix"] != w:
            bad.append((i, "배지 %s != 재계산 %s" % (e["fix"], w)))
        tot += e["fix"][0]
    if tot != inr:
        bad.append(("합", "사건 배지 합 %d != 지도에서 범위 안 %d" % (tot, inr)))
    evfix = {int(k): v["fix"][0] for k, v in a.data["ev"].items()}
    for c in a.data["cards"]:
        s = sum(per.get(n, [0])[0] for n in c["members"])
        if c["fix"][0] != s:
            bad.append((c["key"], "카드 배지 %d != 구성원 합 %d" % (c["fix"][0], s)))
    ptot = 0
    for p in a.data["pages"]:
        s = sum(sum(per.get(n, [0])[0] for n in c["members"]) for c in a.data["cards"] if c["page"] == p["key"])
        s += sum(per.get(n, [0])[0] for ch in a.data["chips"] if ch["page"] == p["key"] for n in ch["entries"])
        if p["sum"]["fix"] != s:
            bad.append((p["key"], "쪽 배지 %d != %d" % (p["sum"]["fix"], s)))
        ptot += p["sum"]["fix"]
    if ptot != inr:
        bad.append(("합", "쪽 배지 합 %d != %d" % (ptot, inr)))
    # DOM — 쪽마다 카드 data-fix + 칩 data-fix 합 = 요약 띠(속성·글자)
    for pg, s in a.state("lane:fold:closed").items():
        root = parse(s["html"])
        band = parse(s["band"])
        cell = [n for n in by_attr(band, "data-goto") if n.attrs["data-goto"] == pg][0]
        dom = sum(int(n.attrs.get("data-fix", 0)) for n in by_attr(root, "data-card"))
        dom += sum(int(n.attrs.get("data-fix", 0)) for n in by_attr(root, "data-chip"))
        want = sum(sum(per.get(n, [0])[0] for n in c["members"]) for c in a.data["cards"] if c["page"] == pg)
        want += sum(per.get(n, [0])[0] for ch in a.data["chips"] if ch["page"] == pg for n in ch["entries"])
        shown = re.search(r"✎ (\d+)", _text(cell))
        if dom != want:
            bad.append((pg, "DOM 배지 합 %d != 재계산 %d" % (dom, want)))
        if int(cell.attrs["data-sum-fix"]) != want or not shown or int(shown.group(1)) != want:
            bad.append((pg, "요약 띠 배지 %s/%s != %d" % (cell.attrs["data-sum-fix"], shown and shown.group(1), want)))
    return bad


EXT_PATTERNS = [
    (r"(?i)\b(?:https?|ftp|wss?)://", "URL"),
    (r"(?i)\b(?:src|href|action|poster)\s*=\s*[\"']?\s*//", "프로토콜 상대 주소"),
    (r"(?i)<(?:link|iframe|img|video|audio|object|embed|base|frame)\b", "외부 자원 태그"),
    (r"(?i)<script\b[^>]*\bsrc\s*=", "script src"),
    (r"(?i)@import\b|url\s*\(", "CSS 외부 자원"),
    (r"\bfetch\s*\(|XMLHttpRequest|\bimport\s*\(|importScripts|WebSocket|EventSource|sendBeacon|serviceWorker", "네트워크 API"),
]


def gate_structure(path):
    """7 HTML·JSON 파싱, 외부 URL 0, 크기 상한, file:// 로 열려 JS 오류 0."""
    bad = []
    size = os.path.getsize(path)
    if size > SIZE_CAP:
        bad.append("크기 %d > %d" % (size, SIZE_CAP))
    text = io.open(path, encoding="utf-8").read()
    try:
        root = parse(text)
    except Exception as ex:
        bad.append("HTML 파싱 실패: %s" % ex)
        root = None
    scripts = [n for n in root.iter() if n.tag == "script"] if root else []
    js_blocks = [n for n in scripts if n.attrs.get("type") == "application/json"]
    code = [n for n in scripts if "type" not in n.attrs]
    if len(js_blocks) != 2 or len(code) != 1:
        bad.append("script 구성: JSON %d · 코드 %d (기대 2 · 1)" % (len(js_blocks), len(code)))
    # 브라우저 없이 — 화면 뼈대 요소가 한 번씩 있나
    ids = collections.Counter(n.attrs.get("id") for n in root.iter()) if root else collections.Counter()
    for need in ("page", "side", "cells", "filters", "warn", "band", "prev", "next", "mReview", "mPlay",
                 "vLane", "vCal", "q", "qGo", "errors", "selftest-out", "yoru-data", "yoru-dialogue"):
        if ids.get(need) != 1:
            bad.append("요소 #%s 가 %d개" % (need, ids.get(need, 0)))
    for n in js_blocks:
        try:
            json.loads(_text(n))
        except Exception as ex:
            bad.append("JSON 파싱 실패(%s): %s" % (n.attrs.get("id"), str(ex)[:80]))
    # 외부 요청 — 자료 블록 안의 글자까지 포함해 파일 전체를 본다
    for pat, nm in EXT_PATTERNS:
        hits = re.findall(pat, text)
        if hits:
            bad.append("외부 자원 흔적 %s %d건 %s" % (nm, len(hits), hits[:2]))
    # file:// 로 열기
    d = dump(path, "")
    if 'data-ready="1"' not in d:
        bad.append("file:// 로 열었을 때 준비 표시가 없다")
    m = re.search(r'<pre id="errors">(.*?)</pre>', d, re.S)
    if m and m.group(1).strip():
        bad.append("JS 오류: %s" % html.unescape(m.group(1))[:200])
    if 'id="yoru-data"' in d or 'id="yoru-dialogue"' in d:
        bad.append("자료 블록이 DOM 에 남았다")
    if 'data-page="4"' not in d:
        bad.append("첫 표시가 4월이 아니다")
    return bad


def _scan(text, firsts, longs, k=8):
    """text 에 금지 문자열이 있나. 긴 것은 앞 k 글자 창으로 후보를 찾고 전체를 대조한다."""
    hits = collections.Counter()
    pref = collections.defaultdict(list)
    for s in longs:
        pref[s[:k]].append(s)
    for i in range(len(text) - k + 1):
        c = pref.get(text[i:i + k])
        if c:
            for s in c:
                if text.startswith(s, i):
                    hits[s] += 1
    # 짧은 첫 줄(8자 미만)은 글자 마디·속성값 한 줄이 통째로 같을 때만
    segs = set()
    for seg in re.split(r"[<>\n\"]", text):
        seg = seg.strip()
        if seg:
            segs.add(seg)
    for s in firsts:
        if len(s) < k and s in segs:
            hits[s] += 1
        elif len(s) >= k and s not in hits and s in text:
            hits[s] += 1
    return hits


def strip_code(t):
    """앱 코드(<script> — 속성 없는 것)만 뺀다. 자료 블록(type=application/json)은 남아 있으면 잡혀야 하므로 둔다."""
    return re.sub(r"<script>.*?</script>", "", t, flags=re.S)


def gate_play(path):
    """8 플레이 보기 DOM 에 첫 줄·대사 전문·답 문구·교정 문안이 없다."""
    a, src = Art(path), S()
    bad = []
    firsts, longs = src.forbidden()
    # 산출물 자신이 가진 본문도 — 답 문구(한국어 포함), 대사 문자열 표의 글 줄·교정 문안·메모(화자 이름 제외)
    for v in a.data["ev"].values():
        for x in v.get("ans") or []:
            t = (x[2] or "").strip()
            if t:
                (longs if len(t) >= 8 else firsts).add(t)
    spk = set()
    for rows in a.dlg["ev"].values():
        for i in range(0, len(rows), 2):
            if rows[i] < 0:
                spk.add(-rows[i] - 1)
                spk.add(rows[i + 1])
    for idx, t in enumerate(a.dlg["strs"]):
        t = t.strip()
        if idx not in spk and len(t) >= 8:
            longs.add(t)
    # 플레이 보기에서도 보여 주기로 한 라벨(언제·누구)과 글자가 같으면 누출이 아니다 — 따로 센다
    label_blob = "\n".join("\n".join(v["when"]) + "\n" + " · ".join(v["who"]) for v in a.data["ev"].values())
    texts = []
    # (1) 주소 끝 #play 로 처음 연 상태 — 아무 것도 누르지 않은 DOM 전체
    d0 = dump(path, "#play")
    if 'data-ready="1"' not in d0:
        bad.append("#play 로 열었을 때 준비 표시가 없다")
    texts.append(("#play 처음", html.unescape(strip_code(d0))))
    # (2) 자체 시험(플레이): 쪽·상태 전부 · 옆 패널 전부 · 검수→플레이 전환 뒤 + 그 DOM 전체
    out, raw = a.play()
    texts.append(("자체 시험 처음", html.unescape(strip_code(out.get("initial", "")))))
    texts.append(("쪽·상태", html.unescape("\n".join(s["html"] + s["band"] for s in out["states"]))))
    texts.append(("옆 패널 %d개" % len(out["panels"]), html.unescape("\n".join(out["panels"]))))
    texts.append(("전환 뒤", html.unescape(strip_code(out.get("after_switch", "")))))
    rawdom = strip_code(re.sub(r'<pre id="selftest-out">.*?</pre>', "", raw, flags=re.S))
    texts.append(("시험 뒤 DOM", html.unescape(rawdom)))
    if len(out["panels"]) != len(a.data["cards"]) + len(a.data["ev"]):
        bad.append("옆 패널을 다 열지 못했다: %d" % len(out["panels"]))
    if len(out["states"]) != 6 * len(ALL_PAGES):
        bad.append("쪽·상태 수 %d != %d" % (len(out["states"]), 6 * len(ALL_PAGES)))
    overlap = set()
    for nm, t in texts:
        h = _scan(t, firsts, longs)
        for s in list(h):
            if s in label_blob:
                overlap.add(s)
                del h[s]
        if h:
            # 콘솔에는 개수만(사용자가 플레이 중이다). 예시는 스포일러 표시를 단 scratch 파일로.
            exf = os.path.join(BASE, "scratch", "v2", "play_leak_examples.txt")
            with io.open(exf, "a", encoding="utf-8") as fp:
                fp.write("⚠ 스포일러 — %s · %s\n" % (os.path.basename(path), nm))
                for x in sorted(h, key=len, reverse=True)[:5]:
                    fp.write("   " + x[:40] + "\n")
            bad.append("%s: 금지 문자열 %d종 (예시는 scratch/v2/play_leak_examples.txt)" % (nm, len(h)))
        for mark in ('class="l3', 'class="lf2"', 'class="dl"', 'class="fixlist"', 'class="fixr"'):
            if mark in t:
                bad.append("%s: 플레이 보기에 %s 요소가 있다" % (nm, mark))
    # 검출기가 헛돌지 않는다 — 같은 검사를 검수 보기 DOM 에 걸면 잡혀야 한다
    rv = html.unescape("\n".join(s["html"] for s in a.review()["states"] if s["state"] == "lane:fold:open"))
    nrv = len(_scan(rv, firsts, longs))
    if nrv == 0:
        bad.append("검출기 확인 실패: 검수 보기 DOM 에서도 0건")
    gate_play.review_hits = nrv
    gate_play.label_overlap = sorted(overlap)
    gate_play.forbidden = (len(firsts), len(longs))
    return bad


GATES = [
    ("1 카드 한 번", gate_cards),
    ("2 사건 한 번", gate_events),
    ("3 셈(달별·서랍·요약 띠)", gate_counts),
    ("4 사슬(연결선+달 이동)", gate_edges),
    ("5 라벨 누락 0", gate_labels),
    ("6 교정 배지", gate_badges),
    ("7 구조·외부 URL·크기·file://", gate_structure),
    ("8 플레이 보기 DOM", gate_play),
]


# ═══ 결함 심기 ═══════════════════════════════════════════════════════════
def _write(name, text):
    os.makedirs(INJ, exist_ok=True)
    p = os.path.join(INJ, name + ".html")
    with io.open(p, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(text)
    return p


def inj_cards(text):
    """카드 하나를 다른 달 페이지에 한 번 더 놓는다."""
    def f(d):
        c = dict(d["cards"][0])
        c["page"] = "5" if c["page"] != "5" else "6"
        d["cards"].append(c)
        f.info = (c["key"], c["page"])
    t = with_data(text, f)
    return _write("g1_card_twice", t), "카드 %s 를 %s월에 한 번 더" % f.info


def inj_events(text):
    """서랍 칩 하나에서 사건 하나를 뺀다."""
    def f(d):
        ch = next(c for c in d["chips"] if len(c["entries"]) > 3 and c["page"] != "mem")
        x = ch["entries"].pop()
        ch["order"] = [r for r in ch["order"] if r[0] != x]
        f.info = (ch["id"], x)
    t = with_data(text, f)
    return _write("g2_event_dropped", t), "칩 %s 에서 E%05d 를 뺌" % f.info


def inj_counts(text):
    """요약 띠의 서랍 숫자 하나를 1 늘린다."""
    def f(d):
        d["pages"][2]["sum"]["entries"] += 1
    return _write("g3_band_count", with_data(text, f)), "6월 요약 띠 서랍 수 +1"


def inj_edges(text):
    """사슬 하나를 그리지 않게 자료에서 뺀다."""
    def f(d):
        x = next(e for e in d["edges"] if e[3] == "jump")
        d["edges"].remove(x)
        f.info = (x[0], x[1])
    t = with_data(text, f)
    return _write("g4_edge_dropped", t), "달 이동 사슬 E%05d→E%05d 를 뺌" % f.info


def inj_labels(text):
    """사건 하나의 「누구」를 비운다."""
    def f(d):
        k = next(k for k, v in d["ev"].items() if v["unit"].startswith("d:") and v["home"] == "4")
        d["ev"][k]["who"] = [""]
        f.info = int(k)
    t = with_data(text, f)
    return _write("g5_label_blank", t), "E%05d 의 누구를 비움" % f.info


def inj_badges(text):
    """사건 하나의 교정 배지를 1 늘린다(카드·쪽 합은 그대로)."""
    def f(d):
        k = next(k for k, v in d["ev"].items() if v["fix"][0] > 0)
        d["ev"][k]["fix"][0] += 1
        f.info = int(k)
    t = with_data(text, f)
    return _write("g6_badge_plus1", t), "E%05d 배지 +1" % f.info


def inj_structure(text):
    """외부 스크립트 한 줄을 넣는다."""
    t = text.replace("</head>", '<script src="https://example.invalid/x.js"></script>\n</head>', 1)
    return _write("g7_external_url", t), "<script src=https://…> 한 줄"


def inj_play(text):
    """첫 줄을 플레이 보기에서도 넣게 한 줄 바꾼다."""
    a = "function showFirst(){ return ST.review; }"
    if a not in text:
        raise SystemExit("결함 심을 자리가 없다: showFirst")
    t = text.replace(a, "function showFirst(){ return true; }", 1)
    return _write("g8_first_line_leak", t), "showFirst() 가 늘 참"


INJECT = [inj_cards, inj_events, inj_counts, inj_edges, inj_labels, inj_badges, inj_structure, inj_play]


def main():
    selftest = "--selftest" in sys.argv
    if not os.path.exists(ART):
        raise SystemExit("산출물이 없다: " + ART)
    text = io.open(ART, encoding="utf-8").read()
    fail = 0
    rows = []
    t0 = time.time()
    for (name, fn), inj in zip(GATES, INJECT):
        t = time.time()
        try:
            bad = fn(ART)
        except Exception as ex:
            bad = ["예외: %r" % ex]
        ok = not bad
        fail += 0 if ok else 1
        print("[%s] %s — 문제 %d건%s  (%.1fs)" % ("OK " if ok else "NG ", name, len(bad),
                                               "" if ok else " " + str(bad[:3]), time.time() - t), flush=True)
        if fn is gate_play and hasattr(gate_play, "review_hits"):
            print("      금지 문자열 짧은 %d · 긴 %d종 · 라벨과 글자가 같아 제외 %d종 %s" % (
                gate_play.forbidden[0], gate_play.forbidden[1], len(gate_play.label_overlap),
                [x[:16] for x in gate_play.label_overlap[:4]]))
            print("      검출기 확인: 같은 검사가 검수 보기 DOM 에서 %d종을 잡는다" % gate_play.review_hits)
        row = [name, len(bad)]
        if selftest:
            p, what = inj(text)
            try:
                bad2 = fn(p)
            except Exception as ex:
                bad2 = ["예외: %r" % ex]
            caught = len(bad2) > len(bad)
            fail += 0 if caught else 1
            print("      결함 심기(%s) → %s (%d건: %s)" % (what, "잡았다" if caught else "못 잡았다",
                                                     len(bad2), str(bad2[:2])[:220]), flush=True)
            row += [what, len(bad2), caught]
        rows.append(row)
    print()
    print("실패:", fail, " 걸린 시간 %.0fs" % (time.time() - t0))
    out = os.path.join(BASE, "scratch", "v2", "stage_v2_last.json")
    with io.open(out, "w", encoding="utf-8") as fp:
        json.dump({"when": time.strftime("%Y-%m-%d %H:%M"), "selftest": selftest, "fail": fail,
                   "rows": rows, "artifact_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()},
                  fp, ensure_ascii=False, indent=1)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
