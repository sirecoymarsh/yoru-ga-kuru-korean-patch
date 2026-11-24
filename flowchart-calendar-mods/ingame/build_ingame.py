#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1단계 후보 빌드 — 회상 화면 「검수」 쪽.

  python ingame/build_ingame.py             기본(배포용): 슬롯 80 이 켜져야 보인다
  python ingame/build_ingame.py --open      시험용: 늘 켜진 판을 candidate_test/ 에

무엇을 하나
  1) ingame/base/NightRemaster.ain 을 바탕으로 `alice ain edit --jaf` 로 KR_Chart* 함수를 더한다.
     한국어 글자는 cp932 로 못 옮기므로, Codex 와 같은 방법으로 **FNL 프록시 바이트**로 먼저 바꾸고
     그 바이트를 cp932 로 읽은 글자를 jaf 에 넣는다.
  2) `C_SceneModeScene@Run` 맨 앞에 `CALLFUNC KR_ChartEntry` 한 줄을 끼운다(jam 치환).
  3) 되읽어 원작 함수 본문·MSG1·STR0·전역·구조체가 그대로인지 본다.

실행본 폴더에는 쓰지 않는다. PACT·EX 는 **건드리지 않는다**(이번 단계는 AIN 한 파일).
"""
import os, sys, io, json, re, shutil, struct, hashlib, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scratch"))
sys.path.insert(0, HERE)

ALICE = r"P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe"
BASEDIR = os.path.join(HERE, "base")
BASE_AIN = os.path.join(BASEDIR, "NightRemaster.ain")
WORK = os.path.join(ROOT, "scratch", "ingame_build")
os.makedirs(WORK, exist_ok=True)

PROXY = (r"P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4"
         r"\wansung_build\build_output\fnl_proxy_map_wansung2350.json")

# jaf 안의 자리표 → 화면에 나올 한국어. 쉬운 한국어로, 새 용어를 만들지 않는다.
TEXT = {
    "TXT_MENU_TITLE": "검수 — 장면 재생",
    "TXT_MENU_BYNO": "번호로 장면 재생",
    "TXT_MENU_RECENT": "최근 재생 목록",
    "TXT_MENU_BACK": "회상 화면으로",
    "TXT_NO_EVENT": "그 번호의 장면이 없습니다.",
    "TXT_NO_RECENT": "아직 재생한 장면이 없습니다.",
    "TXT_ASK_RUN": "이 장면을 재생할까요?",
    "TXT_BTN_RUN": "재생",
    "TXT_BTN_STOP": "그만",
    "TXT_NUM_TITLE": "재생할 장면 번호",
    "TXT_NUM_HINT": "E 뒤의 숫자만 (보기: 10001)",
    "TXT_BTN_OK": "확인",
    "TXT_RECENT_TITLE": "최근 재생",
    "TXT_RECENT_BACK": "돌아가기",
    "TXT_SEEN_ONCE": "[본 장면]",
    "TXT_SEEN_TOTAL": "[예전 판에서 봄]",
    "TXT_SEEN_NONE": "[아직]",
    # 2단계 — 게임 안 차트
    "TXT_MENU_CHART": "달·갈래로 찾기",
    "TXT_MONTH_TITLE": "어느 달",
    "TXT_MONTH_SUFFIX": "월",
    "TXT_MONTH_ALL": "달 상관없이",
    "TXT_CAT_TITLE": "어느 갈래",
    "TXT_CAT_MAIN": "본편",
    "TXT_CAT_DUNGEON": "던전 대화",
    "TXT_CAT_MEMORY": "회상 재생본",
    "TXT_LIST_TITLE": "장면 고르기",
    "TXT_PREV": "이전",
    "TXT_NEXT": "다음",
    "TXT_P2": "이즈미",
    "TXT_P3": "쿄카",
    "TXT_P4": "마나미",
    "TXT_P5": "마코토",
    "TXT_P6": "신카이",
    "TXT_P7": "호시카와",
    "TXT_P8": "모모세",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fp:
        for b in iter(lambda: fp.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cmd(*args):
    p = subprocess.run([ALICE] + [str(a) for a in args], capture_output=True, timeout=600)
    if p.returncode != 0:
        err = (p.stderr or b"").decode("utf-8", "replace")
        err = "\n".join(l for l in err.split("\n") if "WARNING" not in l)
        raise SystemExit("alice 실패: %s\n%s" % (args[:3], err[:1500]))
    return p


def proxy_encoder():
    m = json.load(io.open(PROXY, encoding="utf-8"))["mapping"]
    enc = {r["unicode_character"]: bytes.fromhex(r["proxy_sjis_hex"]) for r in m}
    ok = set(enc)

    def encode(t):
        out = []
        missing = []
        for c in t:
            if c in enc:
                out.append(enc[c])
            else:
                try:
                    out.append(c.encode("cp932"))
                except Exception:
                    missing.append(c)
        return b"".join(out), missing

    return encode, ok


def cp932_ok(c):
    try:
        c.encode("cp932")
        return True
    except Exception:
        return False


def strip_comments(src):
    """`//` 줄 주석과 `/* */` 덩어리 주석을 지운다. 따옴표 안은 건드리지 않는다."""
    out = []
    i, n = 0, len(src)
    instr = False
    while i < n:
        c = src[i]
        if instr:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if c == '"':
                instr = False
            i += 1
            continue
        if c == '"':
            instr = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c); i += 1
    return "".join(out)


def prepare_jaf(force_open):
    encode, charset = proxy_encoder()
    src = io.open(os.path.join(HERE, "kr_chart.jaf"), encoding="utf-8").read()
    missing_all = {}
    for k, v in TEXT.items():
        b, miss = encode(v)
        if miss:
            missing_all[k] = miss
        src = src.replace('"%s"' % k, json.dumps(b.decode("cp932"), ensure_ascii=False))
    if missing_all:
        raise SystemExit("글꼴 문자집합에 없는 글자: %s" % missing_all)
    if force_open:
        src = src.replace("    return KR_ChartOn != 0;\n", "    return true;\n")
    # jaf 는 cp932 로 읽힌다. 주석의 한국어는 옮길 수 없으므로 **빌드본에서만** 지운다
    # (읽을 사람을 위한 주석은 원본 ingame/kr_chart.jaf 에 그대로 남는다).
    src = strip_comments(src)
    bad = sorted({c for c in src if not cp932_ok(c)})
    if bad:
        raise SystemExit("cp932 로 못 옮기는 글자가 남았다: %r" % bad[:20])
    out = os.path.join(WORK, "kr_chart.built.jaf")
    io.open(out, "w", encoding="utf-8").write(src)
    return out, missing_all


def func_names(ain):
    """함수 번호 → 이름 (중복 이름은 alice 와 같은 #n 규칙)."""
    p = os.path.join(WORK, "f.txt")
    cmd("ain", "dump", "-f", "-o", p, ain)
    import jamindex
    names, seen = {}, {}
    for l in io.open(p, encoding="utf-8", errors="replace"):
        m = re.match(r"^/\* 0x([0-9a-f]+) \*/\t(.*);\s*$", l.rstrip("\n"))
        if not m:
            continue
        no = int(m.group(1), 16)
        nm = jamindex._name_from_sig(m.group(2))
        c = seen.get(nm, 0)
        seen[nm] = c + 1
        names[no] = nm + ("#%d" % c if c else "")
    return names


HOOK_FN = "C_SceneModeScene@Run"


def build(force_open=False):
    if not os.path.exists(BASE_AIN):
        raise SystemExit("기준 사본이 없다. 먼저 ingame/snapshot_base.py 를 돌려라.")
    outdir = os.path.join(HERE, "candidate_test" if force_open else "candidate")
    os.makedirs(outdir, exist_ok=True)
    jaf, _ = prepare_jaf(force_open)

    # 1) 함수 선언 + 본문 컴파일
    decl = os.path.join(WORK, "decl.ain")
    cmd("ain", "edit", "--jaf", jaf, "-o", decl, BASE_AIN)

    base_names = func_names(BASE_AIN)
    new_names = func_names(decl)
    added = {n: no for no, n in new_names.items() if no not in base_names}
    print("더해진 함수", len(added), sorted(added)[:6], "…")

    # 2) 회상 화면 진입점에 한 줄 끼우기
    hook_jam = os.path.join(WORK, "hook.jam")
    cmd("ain", "dump", "--function", HOOK_FN, "-o", hook_jam, decl)
    body = io.open(hook_jam, encoding="utf-8", errors="replace").read()
    marker = "\t.GLOBALASSIGN N_ModeScene::DbgEnableAll 0\n"
    if body.count(marker) != 1:
        raise SystemExit("%s 안에서 끼울 자리를 못 찾았다" % HOOK_FN)
    patched = body.replace(marker, marker + "\tCALLFUNC KR_ChartEntry\n", 1)
    patch_jam = os.path.join(WORK, "hook.patched.jam")
    io.open(patch_jam, "w", encoding="utf-8", newline="\n").write(patched)

    out_ain = os.path.join(outdir, "NightRemaster.ain")
    cmd("ain", "edit", "--jam", patch_jam, "-o", out_ain, decl)

    # 3) 되읽어 확인
    import shutil as _sh
    _sh.rmtree(os.path.join(ROOT, "scratch", "ingame_verify"), ignore_errors=True)
    checks = verify(BASE_AIN, out_ain, added, outdir)

    man = {
        "schema": "yoru-ingame-candidate.v1",
        "stage": 1,
        "built": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "variant": "test(always on)" if force_open else "release(slot 80 gate)",
        "base": json.load(io.open(os.path.join(BASEDIR, "manifest.json"), encoding="utf-8")),
        "files": {"NightRemaster.ain": {"sha256": sha256(out_ain),
                                        "size": os.path.getsize(out_ain)}},
        "pact_changed": False, "ex_changed": False,
        "patched_functions": [HOOK_FN],
        "added_functions": {n: no for n, no in sorted(added.items(), key=lambda x: x[1])},
        "gate": "KR_Flag(80) != 0 || KR_ChartOn != 0"
                + (" (이 판은 늘 참)" if force_open else ""),
        "entry": "C_SceneModeScene@Run 맨 앞 CALLFUNC KR_ChartEntry 한 줄",
        "screen_text": TEXT,
        "verify": checks,
    }
    with io.open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as fp:
        json.dump(man, fp, ensure_ascii=False, indent=1)
    print("후보", out_ain, man["files"]["NightRemaster.ain"]["sha256"][:16])
    for k, v in checks.items():
        print("   ", k, v)
    return out_ain, man


def verify(base, cand, added, outdir):
    """되읽기 검사는 ingame/verify_ingame.py 하나로 모은다(게이트와 같은 코드)."""
    import verify_ingame as V
    return V.compare(base, cand, [HOOK_FN], sorted(added))


if __name__ == "__main__":
    build("--open" in sys.argv)
