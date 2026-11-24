# -*- coding: utf-8 -*-
"""findings jsonl 검증기 v3 (2026-10-01). 사용: python verify_v3.py <findings.jsonl>  /  --selftest
기각(REJECT)은 반입 금지, 경고(WARN)는 사람이 본다. 종료 코드 1 = 기각 항목 있음.

v2(claude_qa_20260923/pending_merge/verify_meaning_fixes_v2.py) 를 바탕으로:
  * 기준은 claude_qa_20261001/review_base/base_lines.jsonl (설치본 전체 96,470줄) 과 terms_bundle_v2.json
  * 레코드 종류: 교정 {m_id, issue_type, evidence_jp, current, proposed, note?, confidence?}
               검수 완료 표시 {packet, checked, lines}
               질문 {question, m_id?}  (검증 안 함, 집계만)
               반증 결과(verified 파일)는 교정 레코드에 verdict(keep|amend|drop)·reason 이 더 붙는다. drop 은 검증하지 않는다
  * 새 기각: empty_line(kr 이 빈 줄), silence_line(・・・ 침묵 줄), issue_type 없음/모르는 값, proposed 에 【】 포함
  * 호칭 규칙 갱신: 료→이즈미 누나/신카이 형, 모모세→이즈미 선배·쿄카 누나, 마나미 선배(선배님 금지), 쿄카→신카이 신 선배(경고)
  * 용어 경고: 금지 표기(진월·진야·토야·하자마·블루마·음렬·양관/양옥·모의점) 가 proposed 에 새로 들어오면 기각(forbidden_variant)
"""
import sys, json, re, os, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(HERE, 'review_base')
base = {}
for line in open(os.path.join(BASE_DIR, 'base_lines.jsonl'), encoding='utf-8'):
    r = json.loads(line); base[r['m_id']] = r
bundle = json.load(open(os.path.join(BASE_DIR, 'terms_bundle_v2.json'), encoding='utf-8'))
GL = [(e['source'], e['target']) for e in bundle['glossary'] if e['category'] not in ('character', 'title', 'common', 'parody', 'item', 'h_term')]
FORBID = [(e['source'], v) for e in bundle['glossary'] for v in (e.get('forbidden_or_deprecated_variants') or []) if '(' not in v]
ISSUE_TYPES = {'other_sentence', 'shift', 'mistranslation', 'omission', 'addition', 'term', 'address', 'register', 'artifact'}
POL = re.compile(r'(요|니다|세요|십시오|죠|습니까)(?=[^가-힣]|$)')
DIA = re.compile(r'^\s*[「『（]|^　')
def brackets(s): return ''.join(c for c in s if c in '「」『』（）')
def paren_norm(s): return s.replace('(', '（').replace(')', '）')
def half_parens(s): return s.count('(') + s.count(')')
def strip_title(s): return s.replace('『', '').replace('』', '')
def title_restored(cur, new):
    """작은따옴표 등으로 풀린 『』를 되살리는 교정: 『』를 뺀 괄호 구성이 같고, 새 줄 안에서 『 와 』 가 짝이 맞으며(수 같음), 현재 줄엔 『』가 없을 때만"""
    if '『' in cur or '』' in cur: return False
    if new.count('『') == 0 or new.count('『') != new.count('』'): return False
    return brackets(strip_title(new)) == brackets(cur) or (brackets(paren_norm(strip_title(new))) == brackets(paren_norm(cur)) and half_parens(new) < half_parens(cur))
def bracket_changed(cur, new):
    if brackets(new) == brackets(cur): return False
    if brackets(paren_norm(new)) == brackets(paren_norm(cur)) and half_parens(new) < half_parens(cur): return False
    return not title_restored(cur, new)
def check(recs):
    rej = collections.Counter(); warn = collections.Counter(); seen = set(); out = []
    for r in recs:
        if 'packet' in r or 'question' in r: continue
        if r.get('verdict') == 'drop': continue
        i = r.get('m_id'); prob = []; w = []
        if i not in base: prob.append('scope'); out.append((i, prob, w)); rej['scope'] += 1; continue
        b = base[i]; cur, new = b['kr'], r.get('proposed', '')
        if i in seen: prob.append('duplicate')
        seen.add(i)
        if r.get('issue_type') not in ISSUE_TYPES: prob.append('issue_type')
        if (r.get('evidence_jp') or '').strip() != b['jp'].strip(): prob.append('evidence_mismatch')
        if (r.get('current') or '') != cur: prob.append('stale_current')
        if b['type'] == 'empty': prob.append('empty_line')
        if b['type'] == 'silence': prob.append('silence_line')
        if b['type'] == 'label' or re.fullmatch(r'\s*【.+】\s*', cur): prob.append('label_line')
        if not new or new == cur: prob.append('no_change')
        if '\n' in new: prob.append('newline')
        if '【' in new or '】' in new: prob.append('label_in_text')
        if len(new) > max(len(cur), 32): prob.append('too_long')
        closer_appended = 'B' in (r.get('source') or '') and bool(new) and ((new[-1] in '」』）' and not bracket_changed(cur, new[:-1])) or r.get('block_balanced') is True)
        if bracket_changed(cur, new) and not closer_appended: prob.append('bracket_structure')
        elif brackets(new) != brackets(cur) and '『' in new and not closer_appended: w.append('title_brackets_restored')
        elif closer_appended: w.append('closer_appended')
        if cur.startswith('　') != new.startswith('　'): prob.append('leading_space')
        if '료　　　　' in cur and '료　　　　' not in new: prob.append('sentinel')
        if re.search(r'[가-힣]', cur) and not re.search(r'[가-힣]', new): prob.append('no_hangul')
        if re.search(r'[ぁ-んァ-ン]', new): prob.append('kana_left')
        if DIA.match(new) and re.search(r'그녀|(^|[\s「『（])그(는|가|의|를|에게)', new): prob.append('third_person_in_dialogue')
        if re.search(r'(마나미|쿄카|키라라|이즈미)\s?(짱|쨩)', new): prob.append('chan_suffix')
        for s, v in FORBID:
            if v in new and v not in cur: prob.append('forbidden_variant:' + v)
        sp = b.get('speaker')
        if sp == '료' and re.search(r'이즈미\s?(선배|씨|누님)|신카이\s?(선배|씨)', new): prob.append('address_table')
        if sp == '모모세' and re.search(r'이즈미\s?(씨|누나|누님)|쿄카\s?누님', new): prob.append('address_table')
        if sp == '마나미' and '선배님' in new: prob.append('address_table')
        if sp == '쿄카' and re.search(r'신카이\s?(선배|씨)', new) and not re.search(r'신카이\s?(선배|씨)', cur): w.append('kyoka_shinkai_address')
        for s, t in GL:
            if s in b['jp'] and t not in new and t in cur: w.append(f'glossary_dropped:{s}->{t}')
        if sp in ('료', '이즈미', '쿄카', '마코토', '신카이', '호시카와', '모모세') and DIA.match(new) and POL.search(re.sub(r'[」』）…!?.！？。\s]+$', '', new)):
            if not (sp == '료' and re.search(r'사카키|미사토|선생|아저씨|어머니|아주머니|신부|어르신|할머니', new)): w.append('polite_ending_for_banmal_speaker')
        if r.get('confidence') == 'low': w.append('low_confidence')
        if r.get('verdict') == 'amend' and not r.get('reason'): w.append('amend_without_reason')
        for p in prob: rej[p.split(':')[0]] += 1
        for x in w: warn[x.split(':')[0]] += 1
        out.append((i, prob, w))
    return rej, warn, out
def main(path):
    recs = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
    checked = {r['packet'] for r in recs if 'packet' in r}
    qs = sum(1 for r in recs if 'question' in r)
    rej, warn, out = check(recs)
    n = sum(1 for r in recs if 'packet' not in r and 'question' not in r and r.get('verdict') != 'drop')
    dropped = sum(1 for r in recs if r.get('verdict') == 'drop')
    print(f'교정 항목 {n} (drop {dropped}), 검수 완료 표시 패킷 {len(checked)}, 질문 {qs}')
    print('REJECT', dict(rej)); print('WARN', dict(warn))
    with open(path + '.report.tsv', 'w', encoding='utf-8') as f:
        f.write('m_id\treject\twarn\n')
        for i, p, w in out: f.write(f'{i}\t{";".join(p)}\t{";".join(w)}\n')
    bad = sum(1 for i, p, w in out if p)
    print('기각 항목', bad, '/ 보고서', path + '.report.tsv')
    return 1 if bad else 0
def selftest():
    i = next(k for k, b in sorted(base.items()) if b['speaker'] == '료' and b['type'] == 'quote' and '이즈미 누나' in b['kr'] and len(b['kr']) < 30)
    b = base[i]
    ok = {'m_id': i, 'issue_type': 'mistranslation', 'evidence_jp': b['jp'], 'current': b['kr'], 'proposed': b['kr'][:-1] + '!' + b['kr'][-1]}
    e_i = next(k for k, x in sorted(base.items()) if x['type'] == 'empty')
    s_i = next(k for k, x in sorted(base.items()) if x['type'] == 'silence')
    t_i = next(k for k, x in sorted(base.items()) if x['type'] in ('quote', 'narr') and '참된 달' in x['kr'])
    planted = [
        ('evidence_mismatch', dict(ok, evidence_jp=b['jp'] + 'x')),
        ('stale_current', dict(ok, current=b['kr'] + ' ')),
        ('too_long', dict(ok, proposed=b['kr'] + '가' * 40)),
        ('bracket_structure', dict(ok, proposed=b['kr'].replace('「', '', 1))),
        ('third_person_in_dialogue', dict(ok, proposed='「그녀가 ' + b['kr'][1:])),
        ('address_table', dict(ok, proposed=b['kr'].replace('이즈미 누나', '이즈미 선배'))),
        ('chan_suffix', dict(ok, proposed=b['kr'][:-1] + ' 마나미 짱」')),
        ('newline', dict(ok, proposed=b['kr'][:3] + '\n' + b['kr'][3:])),
        ('scope', dict(ok, m_id=1)),
        ('issue_type', dict(ok, issue_type='style')),
        ('label_in_text', dict(ok, proposed='【료】' + b['kr'][3:])),
        ('empty_line', {'m_id': e_i, 'issue_type': 'omission', 'evidence_jp': base[e_i]['jp'], 'current': '', 'proposed': '추가 문장'}),
        ('silence_line', {'m_id': s_i, 'issue_type': 'omission', 'evidence_jp': base[s_i]['jp'], 'current': base[s_i]['kr'], 'proposed': '……'}),
        ('forbidden_variant', {'m_id': t_i, 'issue_type': 'term', 'evidence_jp': base[t_i]['jp'], 'current': base[t_i]['kr'], 'proposed': base[t_i]['kr'].replace('참된 달', '진월')}),
    ]
    rej, warn, out = check([ok]); assert not out[0][1], ('valid rejected', out[0])
    for name, rec in planted:
        rej, warn, out = check([rec]); assert any(p.split(':')[0] == name for p in out[0][1]), (name, out[0])
    rej, warn, out = check([dict(ok, verdict='drop')]); assert not out, 'drop 레코드는 건너뛰어야 한다'
    # 『』 복원: 현재 줄에 『』가 없고 새 줄 안에서 짝이 맞으면 통과(경고), 짝이 안 맞으면 기각
    q_i = next(k for k, x in sorted(base.items()) if x['type'] == 'quote' and "'" in x['kr'] and '『' not in x['kr'] and x['kr'].count("'") == 2 and len(x['kr']) < 30)
    qk = base[q_i]['kr']; a = qk.find("'"); z = qk.rfind("'")
    restored = qk[:a] + '『' + qk[a + 1:z] + '』' + qk[z + 1:]
    rec_t = {'m_id': q_i, 'issue_type': 'artifact', 'evidence_jp': base[q_i]['jp'], 'current': qk, 'proposed': restored}
    rej, warn, out = check([rec_t]); assert not out[0][1] and 'title_brackets_restored' in out[0][2], ('『』 복원 통과 실패', out[0], qk, restored)
    rej, warn, out = check([dict(rec_t, proposed=restored.replace('』', '', 1))]); assert 'bracket_structure' in out[0][1], ('짝 안 맞는 『 기각 실패', out[0])
    # 닫는 괄호 덧붙이기(기계 수리 source B)만 허용, 같은 교정이라도 source 가 다르면 기각
    o_i = next(k for k, x in sorted(base.items()) if x['type'] == 'quote' and x['kr'].startswith('「') and '」' not in x['kr'] and len(x['kr']) < 31)
    rec_b = {'m_id': o_i, 'issue_type': 'artifact', 'evidence_jp': base[o_i]['jp'], 'current': base[o_i]['kr'], 'proposed': base[o_i]['kr'] + '」', 'source': 'B'}
    rej, warn, out = check([rec_b]); assert not out[0][1] and 'closer_appended' in out[0][2], ('닫는 괄호 덧붙이기 통과 실패', out[0])
    rej, warn, out = check([dict(rec_b, source='M')]); assert 'bracket_structure' in out[0][1], ('source M 의 괄호 추가는 기각돼야 함', out[0])
    rej, warn, out = check([{'packet': 'packet_0001', 'checked': True, 'lines': 3}, {'question': 'x', 'm_id': 5}]); assert not out
    print('selftest OK: 정상 1건 통과, 심은 결함 %d종 전부 기각, drop·packet·question 레코드 건너뜀 확인' % len(planted))
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--selftest': selftest()
    else: sys.exit(main(sys.argv[1]))
