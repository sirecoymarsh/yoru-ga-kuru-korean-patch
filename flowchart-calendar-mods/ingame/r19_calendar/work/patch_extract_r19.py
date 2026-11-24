"""r19 (Claude Opus 5.5, 2026-09-27): one-off patch of scratch/extract.py (the graph/schedule.json builder).

Adds the affinity gates the game code checks (rule 11 of the r19 requirement) as a new trigger field `feeling_gate`
(a list of {person, op, value} / {person, op: "highest", among}) so the PC chart v2 and the in-game calendar read the
same values:
  * conditional triggers (L_EventCall::ConditionalCall's nPersonID / nFeeling: `GetFeeling() < nFeeling` -> not called)
  * after_training_priority triggers (L_RandomScenario::GetAfterTrainingEvent: `pa->C_Ability@GetFeeling() >= n`)
  * scheduled_special triggers of the L_EventCall::E#### branch functions: guards from guarded_rules() (E30152:
    `GetFeeling() < 50` / its negation), and the highest-affinity dispatch of L_EventCall::E10501 (no route decided,
    the person with the largest GetFeeling() among 2..5 -> their event) with `no_route: true`
Adds `--out DIR` (write the graph files somewhere else, for a diff before replacing graph/). Nothing else changes.
"""
import io, sys
from pathlib import Path

P = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\scratch\extract.py')
src = P.read_text(encoding='utf-8')
assert 'feeling_gate' not in src, 'already patched'


def rep(old, new, count=1):
    global src
    assert src.count(old) == count, (old[:80], src.count(old))
    src = src.replace(old, new)


# 1. --out
rep('GRAPH = os.path.join(BASE, "graph")\nos.makedirs(GRAPH, exist_ok=True)\n',
    'GRAPH = os.path.join(BASE, "graph")\n'
    'if "--out" in sys.argv:                      # r19: 시험 출력(graph/ 를 바꾸기 전에 비교)\n'
    '    GRAPH = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])\n'
    'os.makedirs(GRAPH, exist_ok=True)\n')

# 2. parsers (before the assembly section)
rep('# ────────────── 조립 ──────────────\n',
    r'''# ────────────── 친밀도 조건(r19 규칙 11) ──────────────
# 게임은 친밀도를 C_Ability@GetFeeling() (= m_nFeeling / 인물별 비율) 로 비교한다. 상태 창의 친밀도 쪽(C_FeelingView)도
# 같은 값을 그린다. 그래서 여기 적는 v 는 GetFeeling() 단위 그대로다.
FEEL_RE = re.compile(r"^LAbility::At\((\d+)\)->C_Ability@GetFeeling\(\) (<|<=|>|>=) (\d+)$")
FEEL_NEG = {"<": ">=", ">=": "<", ">": "<=", "<=": ">"}


def _unparen(s):
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        for i, ch in enumerate(s):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and i < len(s) - 1:
                return s
        s = s[1:-1].strip()
    return s


def feeling_gates_of(guards):
    """guarded_rules() 의 가드 문자열에서 친밀도 비교만 뽑는다: [{person, op, value}] (부정은 뒤집는다)."""
    out = []
    for g in guards:
        s = g.strip()
        neg = s.startswith("!(") and s.endswith(")")
        if neg:
            s = s[2:-1]
        m = FEEL_RE.match(_unparen(s))
        if not m:
            continue
        op = FEEL_NEG[m.group(2)] if neg else m.group(2)
        out.append({"person": int(m.group(1)), "op": op, "value": int(m.group(3))})
    return out


def highest_feeling_rules(funcname):
    """L_EventCall::E10501 꼴: 누구도 반하지 않았을 때(IsTurning 이 하나라도 참이면 return 0) 2~5 중 GetFeeling() 이
    가장 큰 인물(> 0, 먼저 나온 쪽이 동점 승)의 사건을 부른다 → {사건: 인물}. 꼴이 다르면 빈 사전."""
    txt = pseudo.render(funcname)
    if "nMaxFeeling" not in txt or "switch(nPerson)" not in txt or "C_Ability@GetFeeling() >= 1" not in txt:
        return {}, False
    if not re.search(r"if \(!\(i <= 5\)\) goto", txt) or "C_Ability@IsTurning()" not in txt:
        return {}, False
    if not re.search(r"if \(\(nFeeling > nMaxFeeling\)\) goto", txt):
        return {}, False
    out = {}
    lines = [l.strip() for l in txt.split("\n")]
    for i, l in enumerate(lines):
        m = re.match(r"^case \d+:\d+ (\d+):$", l)
        if m and i + 1 < len(lines):
            m2 = re.match(r"^return L_EventCall::Call\((\d+)\)$", lines[i + 1])
            if m2:
                out[int(m2.group(1))] = int(m.group(1))
    return out, True


# ────────────── 조립 ──────────────
''')

# 3. conditional: feeling_gate from nPersonID / nFeeling
rep('''                     "affection": None if (pid <= 0 or feel < 0) else {"person": pid, "min": feel},
                     "requires_events": [] if need < 0 else [need],
                     "guards": g, "source": "L_EventCall::Check"})''',
    '''                     "affection": None if (pid <= 0 or feel < 0) else {"person": pid, "min": feel},
                     "requires_events": [] if need < 0 else [need],
                     "guards": g, "source": "L_EventCall::Check"})
                if pid > 0 and feel >= 0:      # r19: ConditionalCall 은 GetFeeling() < nFeeling 이면 부르지 않는다
                    events[e]["triggers"][-1]["feeling_gate"] = [{"person": pid, "op": ">=", "value": feel}]''')

# 4. specials: guards -> feeling gates, E10501 highest
rep('''        for e in sorted(set(targets)):
            if e in events:
                events[e]["triggers"].append(
                    {"kind": "scheduled_special", "source": sp,
                     "date": [gate.get("Month"), gate.get("Day")] if gate.get("Month") else None,
                     "time_id": gate.get("TimeID"),
                     "condition_expr": "date==%s/%s and time_id==%s (%s 안의 갈래)" % (
                         gate.get("Month"), gate.get("Day"), gate.get("TimeID"),
                         sp.split("::")[-1]),
                     "guards": []})''',
    '''        fgates = {}                  # r19: 사건 → 그 호출을 감싼 친밀도 조건(부르는 자리마다 같아야 한다)
        for r in guarded_rules(sp):
            if r["fn"] != "L_EventCall::Call" or not r["args"].strip().isdigit():
                continue
            fg = feeling_gates_of(r["guards"])
            e0 = int(r["args"])
            if e0 in fgates:
                assert fgates[e0] == fg, (sp, e0, fgates[e0], fg)
            fgates[e0] = fg
        highest, no_route = highest_feeling_rules(sp)
        for e in sorted(set(targets)):
            if e in events:
                events[e]["triggers"].append(
                    {"kind": "scheduled_special", "source": sp,
                     "date": [gate.get("Month"), gate.get("Day")] if gate.get("Month") else None,
                     "time_id": gate.get("TimeID"),
                     "condition_expr": "date==%s/%s and time_id==%s (%s 안의 갈래)" % (
                         gate.get("Month"), gate.get("Day"), gate.get("TimeID"),
                         sp.split("::")[-1]),
                     "guards": []})
                if fgates.get(e):
                    events[e]["triggers"][-1]["feeling_gate"] = fgates[e]
                if e in highest:
                    events[e]["triggers"][-1]["feeling_gate"] = [
                        {"person": highest[e], "op": "highest", "among": sorted(highest.values())}]
                    events[e]["triggers"][-1]["no_route"] = no_route''')

# 5. after-training priority: pa->C_Ability@GetFeeling() >= n
rep('''            events[e]["triggers"].append(
                {"kind": "after_training_priority", "person": r["person"],
                 "condition_expr": r["cond"],
                 "source": "L_RandomScenario::GetAfterTrainingEvent", "guards": []})''',
    '''            events[e]["triggers"].append(
                {"kind": "after_training_priority", "person": r["person"],
                 "condition_expr": r["cond"],
                 "source": "L_RandomScenario::GetAfterTrainingEvent", "guards": []})
            fg = [{"person": r["person"], "op": ">=", "value": int(v)}      # r19: 부정되지 않은 비교만
                  for neg, v in re.findall(r"(!\\()?\\(?pa->C_Ability@GetFeeling\\(\\) >= (\\d+)", r["cond"]) if not neg]
            if fg:
                events[e]["triggers"][-1]["feeling_gate"] = fg''')

P.write_text(src, encoding='utf-8', newline='\n')
print('patched', P)
