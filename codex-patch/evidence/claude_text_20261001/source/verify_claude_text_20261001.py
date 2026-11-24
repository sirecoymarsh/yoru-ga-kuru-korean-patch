# -*- coding: utf-8 -*-
"""staging/claude_text_20261001 검증 (2026-10-01).
1) 정적: MSG1 바뀐 칸 = 지도 ∪ 추가 ∪ 쪽 재배치; 지도 줄은 쪽 단위로 글자 보존; CODE 접두·STR0 접두 불변; 메타 함수 불변(KR_TermMessage 주소만).
2) 동적(VM, 컴파일된 JAM 실행): KR_T9Message(id, text) 를 기본값·대체 표기 2벌로 돌려 b.render 기대값과 대조(정적 행 전부 + 동적 쪽 행 전부).
"""
import sys, os, json, re, struct, random, collections
sys.stdout.reconfigure(encoding='utf-8')
OD = r'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화'
sys.path.insert(0, OD); os.chdir(OD)
from pathlib import Path
import build_term_switch_20260923 as b
import verify_claude_term_rate_20260924 as v3
a = b.a; R = a.R; Q = R / 'claude_qa_20261001'; O = R / 'staging/claude_text_20261001'
sys.path.insert(0, str(Q / 'build')); import build_claude_text_20261001 as B
def readjl(path): return [json.loads(l) for l in Path(path).read_text('utf8').splitlines() if l.strip()]
def proxy(s): return b.encode(s).decode('cp932')
def ko(s): return b.decode(s.encode('cp932'))

def main():
    ev = a.readj(O / 'build_evidence.json'); assert ev['status'] == 'CLAUDE_TEXT_STAGED'
    out = O / 'NightRemaster.ain'; src = O / 'baseline_NightRemaster.ain'
    assert a.sha(out) == ev['files']['NightRemaster.ain'] and a.sha(src) == ev['source_files']['NightRemaster.ain']
    base = [b.decode(x) for x in b.raw_messages(src.read_bytes())[3]]; new = [b.decode(x) for x in b.raw_messages(out.read_bytes())[3]]
    assert len(base) == len(new) == 100944
    fmap = {x['m_id']: x for x in readjl(Q / 'final/final_map_20261001.jsonl')}; extra = {x['m_id']: x for x in readjl(Q / 'final/extra_edits.jsonl')}
    records = a.readj(O / 'layout_records.json'); reflow_ids = {i for r in records for i in r['ids']}
    changed = {i for i in range(len(base)) if base[i] != new[i]}
    assert changed == set(ev['changed_ids']) and len(changed) == ev['changed_fields']
    assert changed <= (set(fmap) | set(extra) | reflow_ids), sorted(changed - set(fmap) - set(extra) - reflow_ids)[:10]
    exact = 0
    for i, x in list(fmap.items()) + list(extra.items()):
        assert base[i] == x['current'], i
        if i in reflow_ids: continue
        assert new[i] == x['proposed'], (i, new[i], x['proposed']); exact += 1
    for r in records:   # 쪽 재배치: 공백만 다르고 글자는 같다
        want = re.sub(r'\s', '', ''.join(fmap[i]['proposed'] if i in fmap else (extra[i]['proposed'] if i in extra else base[i]) for i in r['ids']))
        got = re.sub(r'\s', '', ''.join(new[i] for i in r['ids'])); assert want == got, r['page_id']
        assert [new[i] for i in r['ids']] == r['after'], r['page_id']
    old = b.unpack(src.read_bytes()); nw = b.unpack(out.read_bytes()); oldn = struct.unpack_from('<I', old, 12)[0]
    assert nw[16:16 + oldn] == old[16:16 + oldn]
    assert b.strings(nw)[2][:len(b.strings(old)[2])] == b.strings(old)[2]
    m = b.read_meta(O / 'base_meta.json'); nm = b.read_meta(O / 'candidate_meta.json'); tm = ev['relocated'][0]
    for f, g in zip(m['functions'], nm['functions']):
        t = dict(f)
        if f['index'] == tm: t['address'] = g['address']
        assert t == g, f['index']
    assert nm['functions'][tm]['name'] == 'KR_TermMessage' and len(nm['functions']) == len(m['functions']) + len(ev['added_functions'])
    print('static OK: changed', len(changed), 'exact rows', exact, 'reflow pages', len(records))
    # ---- VM ----
    v3.O = O; v3.b = b; v3.e = B
    v = v3.VM()
    b.TERMS[:] = B.TERMS8
    cov = a.readj(O / 'term_coverage.json'); dyn = {i: r for r in a.readj(O / 'term_dynamic_pages.json') for i in r['ids']}
    scenarios = [[t[0] for t in B.TERMS8], [t[1][1] for t in B.TERMS8], [t[1][-1] for t in B.TERMS8]]
    def settings(values):
        v.cache = {'YoruKR.Term.Active': '1'}
        for i, t in enumerate(values): v.cache[f'YoruKR.Term.v1.{i}'] = proxy(t)
    counts = collections.Counter(); mism = []
    rows = [c for c in cov]
    for values in scenarios:
        settings(values)
        for c in rows:
            i = c['id']; text = new[i]; got = ko(v.run('KR_T9Message', [i, proxy(text)]))
            if c['dynamic_page']:   # 쪽 단위 재배치: 엔진 KR_TermWrapLine 과 같은 규칙(b.wrap, 36/12px 셈)
                r = dyn[i]; full_ts = b.tokens(r['source']); lines = b.wrap(b.render(full_ts, values), r['budget'], r['quoted']); pos = r['ids'].index(i)
                want = lines[pos] if lines and pos < len(lines) else ''
            elif c['tokens'] is None: want = text
            else:
                ts = [(k, (vv if k != 'p' else tuple(vv))) for k, vv in c['tokens']]
                want = b.render(ts, values)
            if got == want: counts['ok'] += 1
            else: mism.append(dict(id=i, values=values, got=got, want=want, text=text)); counts['mismatch'] += 1
        # 활성 아님 → 원문 그대로
    v.cache = {'YoruKR.Term.Active': '0'}
    for c in rows[:300]:
        assert ko(v.run('KR_T9Message', [c['id'], proxy(new[c['id']])])) == new[c['id']]
    # 표에 없는 id 는 폴백(KR_T8Message→KR_TermMsg)으로 들어가 원문 그대로 나와야 한다(바뀐 줄 중 용어 없는 줄)
    settings(scenarios[1]); plain = [i for i in sorted(changed) if not any(t[0] in new[i] for t in B.TERMS8)][:200]
    for i in plain: assert ko(v.run('KR_T9Message', [i, proxy(new[i])])) == new[i], i
    (O / 'vm_term_mismatch.json').write_text(json.dumps(mism, ensure_ascii=False, indent=1), 'utf8')
    res = dict(status='VERIFIED' if not mism else 'TERM_MISMATCH', files=ev['files'], changed=len(changed), exact_rows=exact, reflow_pages=len(records),
               term_rows=len(rows), scenarios=len(scenarios), vm_ok=counts['ok'], vm_mismatch=counts['mismatch'], inactive_checked=min(300, len(rows)), fallback_checked=len(plain), vm_steps=v.steps)
    (O / 'verification.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), 'utf8'); print(json.dumps(res, ensure_ascii=False))
    for x in mism[:8]: print('MISMATCH', x)
    return 0 if not mism else 1

if __name__ == '__main__':
    try: raise SystemExit(main())
    except AssertionError as ex:
        import traceback; traceback.print_exc(); raise SystemExit(1)
