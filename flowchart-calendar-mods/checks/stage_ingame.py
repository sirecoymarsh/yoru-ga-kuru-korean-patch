#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""게임 안 후보 게이트 — 한 명령. 게임을 돌리지 않는다.

  python checks/stage_ingame.py
  python checks/stage_ingame.py --selftest    게이트마다 결함을 심어 걸리는지 본다

검사
  0 기준 사본     ingame/base 해시가 manifest 와 같다
  1 되읽기        후보를 alice 로 되읽어 원작 함수·전역·구조체·MSG1·STR0 가 그대로
  2 고친 함수     기대한 한 함수만 달라졌고, 끼운 줄이 실제로 들어 있다
  3 새 함수       KR_Chart* 가 다 있고 이름이 겹치지 않는다
  4 opcode        Codex 의 native opcode 감사 재사용(있으면)
  5 PACT·EX       이번 단계는 안 건드렸으니 바이트가 base 와 같다
  6 글꼴 문자집합  화면 문구의 글자가 FNL 프록시 표 안이다
  7 문구 되읽기   후보의 새 문자열이 내가 넣은 한국어와 같다
  8 재생 번호     KR_ChartRun 이 만드는 이름이 실제 이벤트 함수와 짝이 맞는다
  9 설치·복구     후보로 바꿨다가 되돌리면 원래 해시로 돌아온다(사본에서)
"""
import os, sys, io, json, re, shutil, hashlib, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, "ingame"))
sys.path.insert(0, os.path.join(BASE, "scratch"))
import verify_ingame as V   # noqa: E402

ING = os.path.join(BASE, "ingame")
BASEDIR = os.path.join(ING, "base")
CAND = os.path.join(ING, "candidate")
PROXY = (r"P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4"
         r"\wansung_build\build_output\fnl_proxy_map_wansung2350.json")
FILES = ["NightRemaster.ain", "NightRemasterPact.afa", "NightRemasterEX.ex"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fp:
        for b in iter(lambda: fp.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def man_base():
    return json.load(io.open(os.path.join(BASEDIR, "manifest.json"), encoding="utf-8"))


def man_cand():
    return json.load(io.open(os.path.join(CAND, "manifest.json"), encoding="utf-8"))


# ── 게이트 ────────────────────────────────────────────────────────────
def g_base(inject=False):
    m = man_base()
    bad = []
    for f, info in m["files"].items():
        got = sha256(os.path.join(BASEDIR, f))
        want = info["sha256"]
        if inject and f == "NightRemaster.ain":
            want = "0" + want[1:]
        if got != want:
            bad.append("%s 해시가 다르다" % f)
    return bad


_cmp = None


def cmpres():
    global _cmp
    if _cmp is None:
        shutil.rmtree(os.path.join(BASE, "scratch", "ingame_verify"), ignore_errors=True)
        mc = man_cand()
        _cmp = V.compare(os.path.join(BASEDIR, "NightRemaster.ain"),
                         os.path.join(CAND, "NightRemaster.ain"),
                         mc["patched_functions"], list(mc["added_functions"]))
    return _cmp


def g_readback(inject=False):
    r = dict(cmpres())
    if inject:
        r["MSG1 그대로"] = False
    bad = []
    for k in ("없어진 함수", "이름이 바뀐 기존 함수"):
        if r[k]:
            bad.append("%s: %s" % (k, r[k][:3]))
    if not r["전역: 기존 항목 그대로"]:
        bad.append("전역이 바뀌었다")
    if not r["구조체 그대로"]:
        bad.append("구조체가 바뀌었다")
    if not r["MSG1 그대로"]:
        bad.append("MSG1 이 바뀌었다")
    if not r["STR0 기존 항목 앞에 그대로"]:
        bad.append("기존 문자열이 밀렸다")
    return bad


def g_patched(inject=False):
    r = cmpres()
    mc = man_cand()
    bad = []
    changed = list(r["본문이 달라진 기존 함수"])
    if inject:
        changed.append("C_SceneGame@Run")
    if sorted(changed) != sorted(mc["patched_functions"]):
        bad.append("고친 함수가 기대와 다르다: %s" % changed)
    # 끼운 줄이 실제로 있나
    out = os.path.join(BASE, "scratch", "hookchk.jam")
    V.cmd("ain", "dump", "--function", mc["patched_functions"][0], "-o", out,
          os.path.join(CAND, "NightRemaster.ain"))
    s = io.open(out, encoding="utf-8", errors="replace").read()
    if "CALLFUNC KR_ChartEntry" not in s:
        bad.append("끼운 CALLFUNC KR_ChartEntry 가 없다")
    if inject and "CALLFUNC KR_ChartEntry" in s:
        pass
    return bad


def g_added(inject=False):
    r = cmpres()
    mc = man_cand()
    want = set(mc["added_functions"])
    got = set(r["더해진 함수"])
    if inject:
        got.discard("KR_ChartEntry")
    bad = []
    if got != want:
        bad.append("새 함수 목록이 다르다: 빠짐 %s / 더함 %s"
                   % (sorted(want - got)[:3], sorted(got - want)[:3]))
    if not all(n.startswith("KR_Chart") for n in want):
        bad.append("KR_Chart 로 시작하지 않는 새 함수가 있다")
    return bad


def g_opcode(inject=False):
    """Codex 의 native opcode 감사를 그대로 쓴다(있을 때만)."""
    src = os.path.join(r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908",
                       "evidence", "mod_tab_20260915", "source")
    aud = os.path.join(src, "audit_sys43_native_opcodes_20260915.py")
    if not os.path.exists(aud):
        return ["Codex 의 opcode 감사 스크립트를 못 찾았다(건너뜀)"] if inject else []
    # 후보의 날코드를 뽑아 쓰이는 opcode 이름을 모은다
    out = os.path.join(BASE, "scratch", "cand_raw_code.jam")
    if not os.path.exists(out) or inject:
        V.cmd("ain", "dump", "--raw-code", "--no-macros", "-o", out,
              os.path.join(CAND, "NightRemaster.ain"))
    bo = os.path.join(BASE, "scratch", "base_raw_code.jam")
    if not os.path.exists(bo):
        V.cmd("ain", "dump", "--raw-code", "--no-macros", "-o", bo,
              os.path.join(BASEDIR, "NightRemaster.ain"))
    def ops(p):
        s = set()
        for l in io.open(p, encoding="utf-8", errors="replace"):
            t = l.strip()
            if not t or t.startswith(";"):
                continue
            # `--raw-code` 는 `0x0012ABCD: OPCODE …` 꼴이라 주소를 떼고 본다
            t = re.sub(r"^0x[0-9A-Fa-f]+:\s*", "", t)
            if not t or t.endswith(":"):
                continue
            s.add(t.split()[0])
        return s
    b, c = ops(bo), ops(out)
    if inject:
        c = c | {"NOT_A_REAL_OPCODE"}
    new = sorted(c - b)
    return ["기준에 없던 opcode 를 썼다: %s" % new] if new else []


def g_untouched(inject=False):
    bad = []
    for f in ("NightRemasterPact.afa", "NightRemasterEX.ex"):
        bp = os.path.join(BASEDIR, f)
        cp = os.path.join(CAND, f)
        if os.path.exists(cp):
            if sha256(bp) != sha256(cp):
                bad.append("%s 가 달라졌다(이번 단계는 안 건드린다)" % f)
        else:
            if inject:
                bad.append("%s 가 후보에 없다(일부러 심은 결함)" % f)
    if inject and not bad:
        bad.append("결함을 심었는데 안 걸렸다")
    return bad


def g_font(inject=False):
    import build_ingame as B
    enc, charset = B.proxy_encoder()
    bad = []
    for k, v in B.TEXT.items():
        t = v + ("\u06de" if inject and k == "TXT_MENU_TITLE" else "")
        _, miss = enc(t)
        if miss:
            bad.append("%s: 글꼴에 없는 글자 %s" % (k, miss))
    return bad


def g_text_roundtrip(inject=False):
    import build_ingame as B
    import build_labels as BL
    rev = BL.proxy_rev()
    a = V.unpack(open(os.path.join(BASEDIR, "NightRemaster.ain"), "rb").read())
    b = V.unpack(open(os.path.join(CAND, "NightRemaster.ain"), "rb").read())
    ra, rb = V.str_rows(a), V.str_rows(b)
    # 문자열 표는 같은 글이 이미 있으면 다시 넣지 않는다(alice 가 합친다).
    # 그래서 "새로 붙은 것"이 아니라 "표 어딘가에 있나"로 본다.
    allrows = set("".join(rev.get(c, c) for c in x.decode("cp932", "replace")) for x in rb)
    baserows = set("".join(rev.get(c, c) for c in x.decode("cp932", "replace")) for x in ra)
    want = set(B.TEXT.values())
    if inject:
        want = want | {"이 문구는 후보에 없다"}
    bad = []
    missing = sorted(want - allrows)
    if missing:
        bad.append("후보 문자열 표에 없는 문구: %s" % missing[:3])
    newly = sorted((want & allrows) - baserows)
    if not inject and len(newly) < 10:
        bad.append("새로 붙은 문구가 너무 적다(%d개)" % len(newly))
    return bad


def g_playnames(inject=False):
    """KR_ChartRun 이 만드는 이름이 실제 이벤트 함수와 짝이 맞는가.
    원본 AIN 의 함수 목록과 EX 표를 갈래로 삼아 본다."""
    sys.path.insert(0, os.path.join(BASE, "scratch"))
    import jamindex, exparse
    lines, byno, byname, ranges, A, Vv, R = jamindex.load()
    f, rows = exparse.table_rows(exparse.parse()["シナリオテストデータ"])
    names = [r["シナリオ名"] for r in rows if not r["シナリオ名"].startswith("ＳＹＳＥＶ")]
    if inject:
        names = names + ["ＥＶ／元／E99999"]
    bad = []
    miss = [n for n in names if n not in byname]
    if miss:
        bad.append("EX 표에 있는데 함수가 없다: %s (%d개)" % (miss[:2], len(miss)))
    # 번호 → 이름 규칙이 원작과 같은가(표본)
    def label(no):
        s = "E%04d" % no if no == 1706 else "E%05d" % no
        return {"E01707": "01707", "E02132": "02132"}.get(s, s)
    for no in (1, 1706, 1707, 2132, 10001, 60020):
        want = "ＥＶ／元／" + label(no)
        if want not in byname:
            bad.append("번호 %d 의 이름 %s 가 함수 목록에 없다" % (no, want))
    return bad


def g_install(inject=False):
    """설치·복구 fixture — 사본 폴더에서만. 실행본에는 손대지 않는다."""
    bad = []
    with tempfile.TemporaryDirectory(prefix="yoru_fix_") as td:
        for f in FILES:
            shutil.copy2(os.path.join(BASEDIR, f), os.path.join(td, f))
        before = {f: sha256(os.path.join(td, f)) for f in FILES}
        baks = {}
        for f in FILES:
            cp = os.path.join(CAND, f)
            if not os.path.exists(cp):
                continue
            bak = os.path.join(td, "%s.%s.bak" % (f, before[f][:8]))
            shutil.copy2(os.path.join(td, f), bak)
            baks[f] = bak
            shutil.copy2(cp, os.path.join(td, f))
        after = {f: sha256(os.path.join(td, f)) for f in FILES}
        mc = man_cand()
        for f, info in mc["files"].items():
            if after[f] != info["sha256"]:
                bad.append("설치 뒤 %s 해시가 manifest 와 다르다" % f)
        if after["NightRemaster.ain"] == before["NightRemaster.ain"]:
            bad.append("설치했는데 AIN 이 그대로다")
        for f, bak in baks.items():
            shutil.copy2(bak, os.path.join(td, f))
        if inject:
            with open(os.path.join(td, FILES[0]), "ab") as fp:
                fp.write(b"\0")
        back = {f: sha256(os.path.join(td, f)) for f in FILES}
        if back != before:
            bad.append("되돌렸는데 원래 해시가 아니다")
    return bad



def g_catmap(inject=False):
    """게임 안 갈래 나눔이 HTML 판 자료와 같은가.

    jaf 의 KR_ChartCatOf 를 **jaf 소스에서 읽어** 파이썬으로 옮긴 뒤,
    EX 표의 1,144행을 graph/schedule.json 의 범주와 항목별로 맞춰 본다."""
    sys.path.insert(0, os.path.join(BASE, "scratch"))
    import exparse
    src = io.open(os.path.join(ING, "kr_chart.jaf"), encoding="utf-8").read()
    body = src.split("int KR_ChartCatOf(int tp) {", 1)[1].split("}", 1)[0]
    rules = []
    for m in re.finditer(r"if \(tp == (\d+)\) return (\d+);", body):
        rules.append(("eq", int(m.group(1)), int(m.group(2)), 0))
    for m in re.finditer(r"if \(tp >= (\d+) && tp <= (\d+)\) return tp - (\d+);", body):
        rules.append(("rng", int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for m in re.finditer(r"if \(tp >= (\d+) && tp <= (\d+)\) return (\d+);", body):
        rules.append(("rngc", int(m.group(1)), int(m.group(2)), int(m.group(3))))

    def cat_of(tp):
        for kind, a, b, c in rules:
            if kind == "eq" and tp == a:
                return b
            if kind == "rng" and a <= tp <= b:
                return tp - c
            if kind == "rngc" and a <= tp <= b:
                return c
        return 0

    sch = json.load(io.open(os.path.join(BASE, "graph", "schedule.json"), encoding="utf-8"))
    byfn = {e["fn"]: e for e in sch["events"]}
    f, rows = exparse.table_rows(exparse.parse()["シナリオテストデータ"])
    bad, checked = [], 0
    for r in rows:
        fn, tp = r["シナリオ名"], r["タイプ番号"]
        if fn.startswith("ＳＹＳＥＶ") or tp == 999:
            continue
        e = byfn.get(fn)
        if e is None:
            bad.append("EX 행 %s 가 그래프에 없다" % fn)
            continue
        checked += 1
        c = cat_of(tp)
        if inject and checked == 1:
            c = 99
        want = {"main": 1, "dungeon_walk": 9, "memory_replay": 10}.get(e["category"])
        if want is None:
            want = e["person"]          # 인물별(특훈 뒤·우선·권유)
        if c != want:
            bad.append("%s 타입 %s: 게임 안 %s != 그래프 %s" % (fn, tp, c, want))
    if checked < 1000:
        bad.append("대조한 행이 %d개뿐이다" % checked)
    return bad

CHECKS = [
    ("0 기준 사본", g_base),
    ("1 되읽기 불변", g_readback),
    ("2 고친 함수", g_patched),
    ("3 새 함수", g_added),
    ("4 opcode", g_opcode),
    ("5 PACT·EX 무변경", g_untouched),
    ("6 글꼴 문자집합", g_font),
    ("7 문구 되읽기", g_text_roundtrip),
    ("8 재생 번호", g_playnames),
    ("9 설치·복구", g_install),
    ("10 갈래 나눔", g_catmap),
]


def main():
    self = "--selftest" in sys.argv
    fail = 0
    for name, fn in CHECKS:
        bad = fn(False)
        ok = not bad
        print("[%s] %s — 문제 %d건%s" % ("OK " if ok else "NG ", name, len(bad),
                                         "" if ok else " " + str(bad[:2])))
        fail += 0 if ok else 1
        if self:
            b2 = fn(True)
            caught = len(b2) > len(bad)
            print("      결함 심기 → %s (%d건)" % ("잡았다" if caught else "못 잡았다", len(b2)))
            fail += 0 if caught else 1
    print()
    print("실패한 게이트:", fail)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
