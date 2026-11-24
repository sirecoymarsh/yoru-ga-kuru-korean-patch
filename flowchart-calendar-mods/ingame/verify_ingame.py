#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""후보 AIN 을 기준 사본과 항목별로 대조한다(게임 없이).

주소는 코드가 움직이면 바뀐다. 그래서 **명령 차례**만 본다 —
함수 안의 `0x…` 라벨을 나온 차례대로 L0, L1… 로 바꿔 놓고 비교한다.
"""
import os, sys, io, re, json, subprocess, hashlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ALICE = r"P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe"
WORK = os.path.join(ROOT, "scratch", "ingame_verify")
os.makedirs(WORK, exist_ok=True)

_SIG = re.compile(r"^/\* 0x([0-9a-f]+) \*/\t(.*);\s*$")
_ADDR = re.compile(r"0x[0-9a-f]+")


def cmd(*args):
    p = subprocess.run([ALICE] + [str(a) for a in args], capture_output=True, timeout=900)
    if p.returncode != 0:
        err = (p.stderr or b"").decode("utf-8", "replace")
        err = "\n".join(l for l in err.split("\n") if "WARNING" not in l)
        raise SystemExit("alice 실패 %s\n%s" % (args[:3], err[:800]))
    return p


def name_from_sig(sig):
    depth, cut = 0, None
    for i, ch in enumerate(sig):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        elif ch == "(" and depth == 0:
            cut = i
            break
    pre = (sig[:cut] if cut is not None else sig).rstrip()
    if pre.endswith(">"):
        d, j = 0, len(pre) - 1
        while j >= 0:
            if pre[j] == ">":
                d += 1
            elif pre[j] == "<":
                d -= 1
                if d == 0:
                    break
            j -= 1
        k = j - 1
        while k >= 0 and pre[k] not in " \t":
            k -= 1
        return pre[k + 1:]
    p = pre.split()
    return p[-1] if p else pre


def dump(ain, tag):
    os.makedirs(WORK, exist_ok=True)
    f = os.path.join(WORK, tag + "_functions.txt")
    c = os.path.join(WORK, tag + "_code.jam")
    g = os.path.join(WORK, tag + "_globals.txt")
    s = os.path.join(WORK, tag + "_structs.txt")
    if not os.path.exists(f):
        cmd("ain", "dump", "-f", "-o", f, ain)
    if not os.path.exists(c):
        cmd("ain", "dump", "-c", "-o", c, ain)
    if not os.path.exists(g):
        cmd("ain", "dump", "-g", "-o", g, ain)
    if not os.path.exists(s):
        cmd("ain", "dump", "-S", "-o", s, ain)
    return f, c, g, s


def index(funcs_path, code_path):
    """{함수번호: (이름, 정규화된 명령 차례)} — 람다가 끼어 있어도 끊기지 않게 자른다."""
    byno = {}
    for l in io.open(funcs_path, encoding="utf-8", errors="replace"):
        m = _SIG.match(l.rstrip("\n"))
        if m:
            byno[int(m.group(1), 16)] = name_from_sig(m.group(2))
    lines = io.open(code_path, encoding="utf-8", errors="replace").read().split("\n")
    starts = []
    for i, l in enumerate(lines):
        if l.startswith("FUNC "):
            try:
                starts.append((int(l.split()[1]), i))
            except Exception:
                pass
    # 같은 함수 번호가 두 번 나올 수 있다. `ain edit --jam` 은 고친 함수를 CODE 끝에
    # 새로 붙이고 **옛 바이트를 그 자리에 남겨 둔다**. 함수표가 가리키는 것은 새 자리이므로
    # 여러 벌이면 시작 주소가 큰 쪽을 산 것으로 본다(relocated 로 돌려준다).
    allrng = {}
    for k, (fno, i) in enumerate(starts):
        nxt = starts[k + 1][1] if k + 1 < len(starts) else len(lines)
        e = nxt - 1
        while e > i and (lines[e].strip() == "" or lines[e].startswith(";")
                         or lines[e].startswith("EOF ")):
            e -= 1
        allrng.setdefault(fno, []).append((i, e))

    def first_addr(r):
        for j in range(r[0], r[1] + 1):
            m = re.match(r"^(0x[0-9a-f]+):", lines[j].strip())
            if m:
                return int(m.group(1), 16)
        return -1

    rng, relocated = {}, []
    for fno, rs in allrng.items():
        if len(rs) == 1:
            rng[fno] = rs[0]
        else:
            rng[fno] = max(rs, key=first_addr)
            relocated.append(fno)
    # 람다는 바깥 함수 안에 끼어 있다 — 바깥 함수 끝을 늘린다
    parent = None
    for fno, i in sorted(starts, key=lambda x: x[1]):
        nm = byno.get(fno, "")
        if "<lambda" in nm:
            if parent in rng and fno in rng and rng[fno][1] > rng[parent][1]:
                rng[parent] = (rng[parent][0], rng[fno][1])
        else:
            parent = fno
    out = {}
    for fno, (s, e) in rng.items():
        body = [l.strip() for l in lines[s:e + 1]]
        body = [l for l in body if l and not l.startswith(";") and not l.startswith("EOF ")]
        labels, seq = {}, []
        for l in body:
            if l.endswith(":") and l.startswith("0x"):
                labels.setdefault(l[:-1], "L%d" % len(labels))
        for l in body:
            seq.append(_ADDR.sub(lambda m: labels.get(m.group(0), m.group(0)), l))
        out[fno] = (byno.get(fno, "#%d" % fno), "\n".join(seq))
    return byno, out, sorted(relocated)


def compare(base_ain, cand_ain, expect_patched, expect_added):
    bf, bc, bg, bs = dump(base_ain, "base")
    cf, cc, cg, cs = dump(cand_ain, "cand")
    bno, B, brel = index(bf, bc)
    cno, C, crel = index(cf, cc)
    res = {}
    # 기준 사본에도 이미 자리를 옮긴 함수가 많다(Codex 의 앞선 --jam 편집 자취).
    # 이번 빌드가 **새로** 옮긴 것만 본다.
    res["기준에 이미 옮겨져 있던 함수 수"] = len(brel)
    res["이번에 새로 옮긴 함수"] = [cno.get(n, n) for n in sorted(set(crel) - set(brel))]
    res["기존 함수 수"] = len(bno)
    res["후보 함수 수"] = len(cno)
    added = sorted(set(cno) - set(bno))
    res["더해진 함수"] = [cno[n] for n in added]
    res["없어진 함수"] = [bno[n] for n in sorted(set(bno) - set(cno))]
    res["이름이 바뀐 기존 함수"] = [bno[n] for n in bno if cno.get(n) != bno[n]]
    changed = []
    for n in B:
        if n not in C:
            continue
        if B[n][1] != C[n][1]:
            changed.append(B[n][0])
    res["본문이 달라진 기존 함수"] = sorted(changed)
    res["기대한 패치 대상"] = sorted(expect_patched)
    res["패치 대상만 달라졌나"] = sorted(changed) == sorted(expect_patched)
    res["기대한 추가 함수와 같나"] = sorted(res["더해진 함수"]) == sorted(expect_added)
    # 전역·구조체
    def gmap(path):
        d = {}
        for l in io.open(path, encoding="utf-8", errors="replace"):
            m = _SIG.match(l.rstrip("\n"))
            if m:
                d[int(m.group(1), 16)] = m.group(2)
        return d
    GB, GC = gmap(bg), gmap(cg)
    res["전역: 기존 항목 그대로"] = all(GC.get(k) == v for k, v in GB.items())
    res["전역 추가"] = [GC[k] for k in sorted(set(GC) - set(GB))]
    sb = io.open(bs, encoding="utf-8", errors="replace").read()
    sc = io.open(cs, encoding="utf-8", errors="replace").read()
    res["구조체 그대로"] = sb == sc
    # MSG1 / STR0 구간 바이트
    res.update(sections(base_ain, cand_ain))
    return res


def unpack(data):
    """AIN 은 zlib 로 눌려 있다(Codex 의 unpack 과 같은 방법)."""
    import zlib, struct as st
    assert data[:8] == b"AI2\0\0\0\0\0", "AI2 머리가 아니다"
    size, csize = st.unpack_from("<II", data, 8)
    d = zlib.decompressobj()
    p = d.decompress(data[16:]) + d.flush()
    assert len(p) == size
    return p


def sections(base_ain, cand_ain):
    a = unpack(open(base_ain, "rb").read())
    b = unpack(open(cand_ain, "rb").read())
    out = {}
    for tag in (b"MSG1", b"STR0"):
        ia, ib = a.find(tag), b.find(tag)
        if ia < 0 or ib < 0:
            out[tag.decode() + " 구간"] = "못 찾음"
            continue
        # 다음 구간 표까지
        nxt = [t for t in (b"SWI0", b"FNAM", b"OBJG", b"MAIN", b"MSGF", b"HLL0")]
        ea = min([a.find(t, ia) for t in nxt if a.find(t, ia) > 0] or [len(a)])
        eb = min([b.find(t, ib) for t in nxt if b.find(t, ib) > 0] or [len(b)])
        sa, sb2 = a[ia:ea], b[ib:eb]
        if tag == b"MSG1":
            # 대사는 한 글자도 달라지면 안 된다
            out["MSG1 그대로"] = sa == sb2
            out["MSG1 바이트"] = [ea - ia, eb - ib]
    # 문자열 표는 항목 단위로 본다(Codex 의 strings() 와 같은 방법):
    # 기존 항목이 앞에 그대로 있고 새 화면 문구만 뒤에 붙어야 한다.
    ra, rb = str_rows(a), str_rows(b)
    out["STR0 기존 항목 앞에 그대로"] = rb[:len(ra)] == ra
    out["STR0 새로 붙은 항목 수"] = len(rb) - len(ra)
    return out


def str_rows(p):
    import struct as st
    start = p.find(b"STR0")
    count = st.unpack_from("<I", p, start + 4)[0]
    pos = start + 8
    rows = []
    for _ in range(count):
        end = p.index(b"\0", pos)
        rows.append(p[pos:end])
        pos = end + 1
    return rows


if __name__ == "__main__":
    base = os.path.join(HERE, "base", "NightRemaster.ain")
    cand = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "candidate", "NightRemaster.ain")
    man = json.load(io.open(os.path.join(os.path.dirname(cand), "manifest.json"), encoding="utf-8"))
    r = compare(base, cand, man["patched_functions"], list(man["added_functions"]))
    print(json.dumps(r, ensure_ascii=False, indent=1))
