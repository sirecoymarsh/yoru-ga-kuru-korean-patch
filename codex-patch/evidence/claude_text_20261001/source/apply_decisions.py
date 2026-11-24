# -*- coding: utf-8 -*-
"""사용자 결정(2026-10-01 「대부분 반영. 드림캐스트 같은 건 그대로」)을 교정 지도에 얹어 최종 반입 지도를 만든다.
입력: final/corrections_20261001.jsonl (검수 교정 1,071), review_base/base_lines.jsonl, final/bracket_mismatch.jsonl
출력: final/final_map_20261001.jsonl (한 m_id 한 줄, verify_v3 기각 0), final/extra_edits.jsonl (검증기 범위 밖 2줄), final/decision_log.md
규칙: 실제 상표·작품명으로 옮겨진 패러디(드림캐스트·타레판다·피카츄·모무스…)는 **그대로** — 그쪽 교정 47건은 뺀다.
"""
import json, os, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import verify_v3 as V
F = os.path.join(HERE, 'final')
base = V.base
recs = {}
for l in open(os.path.join(F, 'corrections_20261001.jsonl'), encoding='utf-8'):
    r = json.loads(l); recs[r['m_id']] = r
log = []
def cur_text(i): return recs[i]['proposed'] if i in recs else base[i]['kr']
def put(i, new, why, issue='term', conf='high', src='D'):
    old = cur_text(i)
    if new == old: return
    if i in recs:
        r = recs[i]; r['proposed'] = new; r['note'] = ((r.get('note') or '') + ' | 결정: ' + why).strip(' |'); r['source'] = (r.get('source') or '') + src
    else:
        recs[i] = {'m_id': i, 'issue_type': issue, 'evidence_jp': base[i]['jp'], 'current': base[i]['kr'], 'proposed': new, 'note': '결정: ' + why, 'confidence': conf, 'verdict': 'keep', 'source': src}
    log.append((i, why, old, new))
def sub_all(pred, old, new, why, josa=None, issue='term'):
    n = 0
    for i, b in base.items():
        if b['type'] not in ('quote', 'narr'): continue
        if not pred(b): continue
        t = cur_text(i)
        if old not in t: continue
        t2 = t.replace(old, new)
        if josa:
            for a, c in josa: t2 = t2.replace(new + a, new + c)
        put(i, t2, why, issue); n += 1
    return n

# ---- C. 패러디·상표: 실제 이름 그대로 (검수 교정 되돌림) ----
BRAND = ['나이키', '네이키', '아디다스', '아베다스', '유니클로', '우니클로', '맥도날드', '와크도날드', '왁도날드', '소니', '써니', '코코', 'KOKO', '제니', '제미', 'SHOCK', '카이요도', '산요도',
         '데카비타', '데카피타', '드림캐스', 'PSO', '푸소', '타레판다', '마른 판다', '점프', '존프', '헌터', '번터', '건담', '칸담', '건프라', '칸프라', '후르츠', '울트라맨', '브리트라맨',
         '스폰', '누폰', '북두', '복두', '보쿠토', '포켓몬', '호게몬', '피카', '비카', '비가', '빗가', '모닝구', '워닝', '모무스', '워무스', '워~ 무~', '모~ 무~', '신일']
reverted = [i for i, r in recs.items() if any(n in r['current'] or n in r['proposed'] for n in BRAND)]
for i in reverted: log.append((i, 'C 패러디·상표 그대로(교정 제외)', recs[i]['proposed'], base[i]['kr'])); del recs[i]

# ---- A. 호칭·존대 ----
sub_all(lambda b: b['speaker'] == '료', '미사토 누나', '미사토 씨', 'A1 료→미사토 「미사토 씨」', issue='address')
put(994, '「여기 계셨네요. 어느 틈에 사라지셔서 깜짝 놀랐어요」', 'A1 료→미사토 존댓말', 'register'); put(1381, '「여기 계셨네요. 어느 틈에 사라지셔서 깜짝 놀랐어요」', 'A1 료→미사토 존댓말', 'register')
put(1020, '　그렇게 생각하지 않아요?」', 'A1 료→미사토 존댓말', 'register'); put(1407, '　그렇게 생각하지 않아요?」', 'A1 료→미사토 존댓말', 'register')
sub_all(lambda b: b['speaker'] == '이즈미', '미사토 언니', '미사토 씨', 'A2 이즈미→미사토 「미사토 씨」', issue='address')
# A3 쿄카→마나미: 「마나」로 통일 (マナちゃん 줄만)
for i, b in base.items():
    if b['speaker'] == '쿄카' and b['type'] == 'quote' and 'マナちゃん' in b['jp']:
        t = cur_text(i); t2 = t.replace('마나 짱', '마나').replace('마나미', '마나')
        put(i, t2, 'A3 쿄카→마나미 애칭 「마나」 통일', 'address')
put(54135, '「신 선배뿐만 아니라,', 'A7 쿄카→신카이 「신 선배」', 'address'); put(68657, '「신 선배뿐만 아니라,', 'A7 쿄카→신카이 「신 선배」', 'address')
put(33305, '「설마, 이즈미인가!?」', 'A8 쿄카→이즈미 이름만', 'address')
sub_all(lambda b: True, '고토 씨', '고토 양', 'A10 後藤さん 「고토 양」 통일(다수형)', issue='address')
for i, new in {17961: '　시간이야!」', 18013: '「왜 내가 네 빵까지, 사줘야 하는', 18014: '　건데에…」', 18019: '「대여섯 개는, 고작이라고 안 해…」',
               18051: '「그렇지 않단 말이야! 정보로는', 18057: '「그렇지 않다니까!」', 18060: '　그렇게까지 해?」', 18066: '「뭐야 자꾸 안 된다 안 된다는 건….'}.items():
    put(i, new, 'A11 마나미→키라라 반말', 'register')
put(23478, '「어라, 안 기뻐?」', 'A12 마나미→모모세 반말(다음 줄 모모세가 답함)', 'register')
put(18156, '「응?」', 'A20 료→신부 반말', 'register'); put(18253, '「저, 저기… 내가 무슨 문제라도?」', 'A20 료→신부 반말', 'register')
put(94128, '　부장님이 사령관이랍니다♪」', 'A21 마나미→이즈미 「부장님」', 'address')
put(74896, '『저… 선배가 바라는 거라면 뭐든지………', 'A16 에미 존댓말 1인칭 「저」', 'register'); put(74939, '　넣어주세요… 봐요 저… 뒤쪽도… 네?』', 'A16 에미 존댓말 1인칭 「저」', 'register')
for i, new in {1521: '「그런 소릴 해도, 놀이공원은 처음인데 우짜라고…」', 1639: '「그런 소릴 해도, 놀이공원은 처음인데 우짜라고…」',
               1526: '「뭐 어떻노. 어떤 차림으로 말하든…」', 1644: '「뭐 어떻노. 어떤 차림으로 말하든…」',
               1558: '「그나저나 오빠, 내 입학식 어땠노?」', 1674: '「그나저나 오빠, 내 입학식 어땠노?」'}.items():
    put(i, new, 'A19 키라라 사투리 맞춤', 'register')

# ---- B. 용어 ----
JOSA_YEONG_TO_JA = [('이', '가'), ('을', '를'), ('은', '는'), ('과', '와')]   # 인영(받침) → 사람 그림자(받침 없음)
for i in (3677, 4217, 4786, 74741):
    t = cur_text(i); t2 = t.replace('인영', '사람 그림자')
    for a, c in JOSA_YEONG_TO_JA: t2 = t2.replace('사람 그림자' + a + ' ', '사람 그림자' + c + ' ').replace('사람 그림자' + a + '」', '사람 그림자' + c + '」')
    t2 = re.sub(r'사람 그림자이(?=[^가-힣]|$)', '사람 그림자가', t2); t2 = re.sub(r'사람 그림자은(?=[^가-힣]|$)', '사람 그림자는', t2)
    put(i, t2, 'B2 人影 지문 「사람 그림자」')
put(25312, '「광기(光器)를 꺼내 두는 편이', 'B4 光器 한자 병기'); put(83614, '「광기(光器)를 꺼내 두는 편이', 'B4 光器 한자 병기')
put(33084, '「히카리에 씐 자가 늘면 지상을 비추는', 'B5 光狩憑き 「히카리에 씐 자」'); put(33087, '「하지만 히카리에 씐 자가 늘어난 건 마을 사람들도 알고', 'B5 光狩憑き 「히카리에 씐 자」')
put(31631, '「3년 전, 히카리에 씐 자에게 습격당하던 내 앞에', 'B5 光狩憑き 「히카리에 씐 자」')
sub_all(lambda b: True, '소고기덮밥', '규동', 'B6 牛丼 「규동」')
put(76628, '「히어로는, 될 수 없겠다고 생각했어요」', 'B7 ヒーロー 「히어로」'); put(76635, '「공주님… 히어로… 노인, 아이…」', 'B7 ヒーロー 「히어로」')
sub_all(lambda b: True, '뱀 여편네', '뱀 여자', 'B8 ヘビ女 「뱀 여자」')
sub_all(lambda b: True, '다카츠키', '타카츠키', 'B11 高槻 「타카츠키」')
put(8365, '삐로리라라', 'B12 착신음 통일', 'artifact'); put(8428, '삐로리라라!', 'B12 착신음 통일', 'artifact')

# ---- D. 부호·표기 ----
n_fw = 0
for i, b in base.items():
    if b['type'] not in ('quote', 'narr'): continue
    t = cur_text(i)
    if '！' in t or '？' in t:
        put(i, t.replace('！', '!').replace('？', '?'), 'D1 전각 ！？ → 반각', 'artifact'); n_fw += 1
put(14189, '『………』', 'D2 가운뎃점 → 말줄임', 'artifact')
put(93190, '「감사해요, 선배. 감사, 감사예요!」', 'D4 말버릇 꼴 유지', 'register')
sub_all(lambda b: True, '라저', '라져', 'D7 了解 「라져」(09-23 결정)')

# ---- E2. 괄호 기계 수리(블록 단위 검증) ----
PAIRS = [('「', '」'), ('『', '』'), ('（', '）')]
bfix = []
def counts(s): return {ch: s.count(ch) for o, c in PAIRS for ch in (o, c)}
for l in open(os.path.join(F, 'bracket_mismatch.jsonl'), encoding='utf-8'):
    m = json.loads(l); lines = m['lines']
    if all(k in '（）' for k in m['diff']): continue
    jp_all = ''.join(x['jp'] for x in lines); kr_lines = {x['m_id']: cur_text(x['m_id']).replace('(', '（').replace(')', '）') for x in lines}
    if counts(jp_all) == counts(''.join(kr_lines.values())): continue   # 교정 지도로 이미 맞음
    new = dict(kr_lines); changed = []
    for o, c in PAIRS:
        jc, kc = counts(jp_all), counts(''.join(new.values()))
        if jc[o] > kc[o]:   # 여는 괄호 부족: 원문 줄이 o 로 시작하는데 한국어 줄이 시작하지 않는 첫 줄에 붙인다
            for x in lines:
                i = x['m_id']; k = new[i]
                if x['jp'].lstrip('　 ').startswith(o) and k.strip() and not k.lstrip('　 ').startswith(('「', '『', '（')):
                    new[i] = (o + k.lstrip('　')) if k.startswith('　') else (o + k); changed.append(i); break
        jc, kc = counts(jp_all), counts(''.join(new.values()))
        if kc[c] > jc[c]:   # 닫는 괄호 남음: 원문 줄에 c 가 없는데 한국어 줄 끝이 c 인 줄에서 하나 뗀다
            for x in lines:
                i = x['m_id']; k = new[i]
                if c not in x['jp'] and k.rstrip().endswith(c):
                    new[i] = k.rstrip()[:-1] + k[len(k.rstrip()):]; changed.append(i); break
        jc, kc = counts(jp_all), counts(''.join(new.values()))
        if jc[c] > kc[c]:   # 닫는 괄호 부족: 원문 줄이 c 로 끝나는데 한국어 줄이 안 끝나는 마지막 줄에 붙인다
            for x in reversed(lines):
                i = x['m_id']; k = new[i]
                if x['jp'].rstrip().endswith(c) and k.strip() and not k.rstrip().endswith(c):
                    new[i] = k + c; changed.append(i); break
    if counts(jp_all) == counts(''.join(new.values())) and changed:
        for i in sorted(set(changed)):
            if new[i] != kr_lines[i]:
                orig = cur_text(i); t2 = new[i] if '(' not in orig and ')' not in orig else new[i]
                if i in recs:
                    recs[i]['proposed'] = t2; recs[i]['source'] = (recs[i].get('source') or '') + 'B'; recs[i]['block_balanced'] = True; recs[i]['note'] = ((recs[i].get('note') or '') + ' | 괄호 블록 수리').strip(' |')
                else:
                    recs[i] = {'m_id': i, 'issue_type': 'artifact', 'evidence_jp': base[i]['jp'], 'current': base[i]['kr'], 'proposed': t2, 'note': f'괄호 블록 수리 {m["first"]}~{m["last"]}', 'confidence': 'high', 'verdict': 'keep', 'source': 'B', 'block_balanced': True}
                bfix.append((i, orig, t2))
    else:
        bfix.append((m['first'], 'UNRESOLVED', m['diff']))

# ---- 범위 밖 2줄 (검증기 밖: 반입 스크립트가 직접 적용) ----
extra = [{'m_id': 7115, 'current': '「YES。 히카리를 찾아냈거든」', 'proposed': '「YES. 히카리를 찾아냈거든」', 'why': 'D3 일본식 마침표'},
         {'m_id': 79421, 'current': '←【그 녀석】', 'proposed': '←【저 녀석】', 'why': 'D8 앞줄·다른 루트와 통일'}]
with open(os.path.join(F, 'extra_edits.jsonl'), 'w', encoding='utf-8') as f:
    for e in extra: f.write(json.dumps(e, ensure_ascii=False) + '\n')

# ---- 폭 보정(빌드 1차에서 FNL 실측 폭 초과·쪽 줄 수 부족으로 걸린 17쪽 + 글꼴 지정 줄 1) ----
WIDTH_OVERLAY = {
    2388: '왼쪽 뒤에서 굉음을 내며 뭔가 다가오는 감각이 든다.', 4116: '「그래도 이 녀석, 멋진 『겹치기』야」', 5589: None,
    17366: '「또 카샤가 있다고 했다. 멋대로', 17367: '　움직이지 말라고 못 박아 뒀지만……」',
    32203: '「코이치라는 키라라 친구는……, 사실', 32204: '　코우야라는 히카리의 변신이었어」', 33022: None, 33079: None,
    33375: '「하지만 전 미즈키를 구하고 싶어요…」', 37567: '「자신에겐 없는 힘을 동생이 지녔고…」', 38202: '「자신에겐 없는 힘을 동생이 지녔고…」',
    37779: '「자신에겐 없던 힘을 동생이 지녔고…」', 38414: '「자신에겐 없던 힘을 동생이 지녔고…」', 51227: '「게다가 네 『겹치기』는 적의 움직임에',
    52042: '「그 힘으로 키라라를 지킬 순 있지만,', 52043: '　키라라를 웃게 해 줄 수는 없다」', 53508: '「쓸데없는 지출인 줄은 알지만,', 53509: '　이상하게도 그만둘 마음이 안 드는군」',
    78542: None, 92529: '「항상 자신과 주변의 기척을 읽어라.', 92530: '　싸움에서 부주의는 치명적 결점이다」', 2743: None,
}
for i, new in WIDTH_OVERLAY.items():
    if new is None:
        if i in recs: log.append((i, '폭: 교정 거둠(현재 문안이 창에 꼭 맞음)', recs[i]['proposed'], base[i]['kr'])); del recs[i]
    else:
        put(i, new, '폭 보정(창 폭·쪽 줄 수)', recs[i]['issue_type'] if i in recs else 'artifact', src='W')
# ---- 검증·출력 ----
nochange = [i for i, r in recs.items() if r['proposed'] == base[i]['kr']]
for i in nochange: log.append((i, '결정 적용 뒤 현재와 같아져 제외', recs[i]['proposed'], base[i]['kr'])); del recs[i]
rows = [recs[i] for i in sorted(recs)]
rej, warn, out = V.check(rows)
bad = [(i, p) for i, p, w in out if p]
with open(os.path.join(F, 'final_map_20261001.jsonl'), 'w', encoding='utf-8') as f:
    for r in rows:
        if r['m_id'] in {i for i, p in bad}: continue
        o = {k: r.get(k) for k in ('m_id', 'issue_type', 'evidence_jp', 'current', 'proposed', 'note', 'confidence', 'verdict', 'source', 'block_balanced') if r.get(k) not in (None, '')}
        f.write(json.dumps(o, ensure_ascii=False) + '\n')
with open(os.path.join(F, 'decision_log.md'), 'w', encoding='utf-8') as f:
    f.write('# 결정 반영 기록 (2026-10-01)\n\n')
    f.write(f'- 패러디·상표 교정 제외(그대로): {len(reverted)}줄\n- 전각 ！？ 반각화: {n_fw}줄\n- 괄호 블록 수리: {sum(1 for x in bfix if x[1] != "UNRESOLVED")}줄, 미해결 블록 {sum(1 for x in bfix if x[1] == "UNRESOLVED")}\n- 최종 지도 {len(rows) - len(bad)}줄, 검증기 기각 {len(bad)}\n\n')
    by = collections.Counter(w for _, w, _, _ in log if not w.startswith('D1') and not w.startswith('C '))
    f.write('## 결정별 줄 수\n\n' + '\n'.join(f'- {k}: {v}' for k, v in sorted(by.items())) + '\n\n## 줄별(전각 ！？·패러디 제외)\n\n')
    for i, w, o, n in log:
        if w.startswith('D1') or w.startswith('C '): continue
        f.write(f'- m[{i}] {w}: {o} → {n}\n')
    f.write('\n## 괄호 블록 수리\n\n' + '\n'.join(f'- m[{i}] {o} → {n}' for i, o, n in bfix) + '\n')
print('final map', len(rows) - len(bad), '| reverted brand', len(reverted), '| fullwidth', n_fw, '| bracket fixes', sum(1 for x in bfix if x[1] != 'UNRESOLVED'), 'unresolved', sum(1 for x in bfix if x[1] == 'UNRESOLVED'))
print('REJECT', dict(rej), 'WARN', dict(warn))
for i, p in bad[:20]: print('  bad', i, p, recs[i]['proposed'])
