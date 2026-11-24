#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""갈래 A(대조) 쪽에서 쓰는 최소 도구.

**추출기(scratch/extract.py, exparse.py, jamindex.py)를 쓰지 않는다.**
원문 덤프 텍스트를 정규식으로 다시 읽는다 — 같은 파서를 쓰면 그 파서의
맹점까지 물려받기 때문이다([[qa-must-not-share-the-extractor]]).
"""
import io, os, re, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(BASE, "scratch", "dump")
GRAPH = os.path.join(BASE, "graph")

EXX = os.path.join(DUMP, "ex.x")
CODE = os.path.join(DUMP, "code.jam")

if not (os.path.exists(EXX) and os.path.exists(CODE)):
    raise SystemExit(
        "원본 덤프가 없다: %s\n"
        "  PYTHONUTF8=1 python scratch/rebuild_all.py --dump-only\n"
        "로 다시 만든 뒤 검사하라(원본 AIN·EX 만 읽는다)." % DUMP)


def load_graph(name):
    with io.open(os.path.join(GRAPH, name), encoding="utf-8") as fp:
        return json.load(fp)


# ── EX 원문을 줄 단위 정규식으로 읽는다 ──────────────────────────────

def ex_block(name):
    """`table X = { … };` / `tree X = { … };` 의 본문 줄 목록."""
    out = []
    inside = False
    depth = 0
    with io.open(EXX, encoding="utf-8", errors="replace") as fp:
        for ln in fp:
            s = ln.rstrip("\n")
            if not inside:
                if re.match(r"^(table|tree|list)\s+%s\s*=\s*\{" % re.escape(name), s):
                    inside = True
                    depth = 1
                continue
            depth += s.count("{") - s.count("}")
            if depth <= 0:
                break
            out.append(s)
    return out


ROW = re.compile(r'^\s*\{\s*(.*?)\s*\}\s*,?\s*$')


def ex_rows(name):
    """`{ a, b, c }` 꼴 줄을 값 리스트로. 머리 정의줄(타입 이름이 든 줄)은 건너뛴다."""
    rows = []
    for s in ex_block(name):
        m = ROW.match(s)
        if not m:
            continue
        body = m.group(1)
        if re.search(r"\b(indexed |int |string |float |bool )", body):
            continue
        vals = []
        for tok in re.findall(r'"(?:[^"\\]|\\.)*"|-?\d+', body):
            if tok.startswith('"'):
                vals.append(tok[1:-1])
            else:
                vals.append(int(tok))
        rows.append(vals)
    return rows


# ── jam 원문을 함수 이름으로 잘라 읽는다(색인 모듈을 쓰지 않는다) ─────

_FN = None


def jam_functions():
    """{함수이름: [줄…]}  — `; <이름>` 주석 + `FUNC n` 으로 자른다.
    람다가 끼어 있어도 바깥 함수가 끊기지 않도록, 다음 `; <이름>` 주석이
    람다(`<lambda`)이면 계속 이어 붙인다."""
    global _FN
    if _FN is not None:
        return _FN
    txt = io.open(CODE, encoding="utf-8", errors="replace").read().split("\n")
    out = {}
    cur = None
    buf = []
    i = 0
    while i < len(txt):
        s = txt[i]
        prev_is_comment = i > 0 and txt[i - 1].startswith(";")
        if s.startswith("; ") and not prev_is_comment:
            # 주석 덩어리 전체를 보고, 그 끝이 FUNC 면 첫 줄이 함수 이름이다
            j = i
            while j < len(txt) and txt[j].startswith(";"):
                j += 1
            if j < len(txt) and txt[j].startswith("FUNC "):
                nm = s[2:].strip().strip('"')
                if "<lambda" in nm:
                    # 람다는 바깥 함수 안에 끼어 있다 — 계속 이어 붙인다
                    if cur is not None:
                        buf.extend(txt[i:j])
                    i = j
                    continue
                if cur is not None:
                    out.setdefault(cur, buf)
                cur = nm
                buf = []
                i = j
                continue
        if cur is not None:
            buf.append(s)
        i += 1
    if cur is not None:
        out.setdefault(cur, buf)
    _FN = out
    return out


def jam_body(name):
    return jam_functions().get(name, [])
