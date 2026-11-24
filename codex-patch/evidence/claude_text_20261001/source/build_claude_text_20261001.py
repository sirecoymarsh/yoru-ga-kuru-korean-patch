# -*- coding: utf-8 -*-
"""밤이 온다! 검수 교정 반입 + 용어 표기 설정 표 재생성 (2026-10-01, Claude).
입력: 설치본 AIN(fae56fb7…), claude_qa_20261001/final/final_map_20261001.jsonl + extra_edits.jsonl
산출: staging/claude_text_20261001/NightRemaster.ain
  1) MSG1 만 바꾼다(09-23 Codex 반입기의 페이지 재배치·폭 검사 그대로: FNL 실측, Face 668 / Text·All 884).
  2) 용어 표기 설정: 새 본문으로 KR_T9Msg{g}·KR_T9Message 를 만들어 붙이고(기존 KR_T8Message 로 폴백),
     KR_TermMessage(원래 트램펄린 → KR_T8Message) 를 KR_T9Message 로 돌린다. 호출자 코드는 손대지 않는다(세이브 스택 안전).
"""
import sys, os, json, re, struct, collections, functools, shutil
sys.stdout.reconfigure(encoding='utf-8')
OD = r'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화'
sys.path.insert(0, OD); os.chdir(OD)
from pathlib import Path
import build_term_switch_20260923 as b
import publish_cheat_menu_20260915 as p
a = b.a
R = a.R; Q = R / 'claude_qa_20261001'; O = R / 'staging/claude_text_20261001'
EXPECTED = 'fae56fb70c8d9c0c8a6bc23c22ef4b76f6e569a7adbd304e4f2d3b639e8353d8'
AUTHOR = 'Claude Fable 5.1 (claude-fable-5-1) with Claude Opus 5.5 reviewers'
TERMS8 = [('히카리', ['히카리', '광수', '빛잡이'], 108), ('카샤', ['카샤', '화자', '불지기'], 108), ('치로', ['치로', '쉭쉭이'], 108),
          ('틈새', ['틈새', '하자마', '틈'], 108), ('얼어붙은 밤', ['얼어붙은 밤', '토야', '동야'], 192),
          ('참된 달', ['참된 달', '진월', '신게츠'], 120), ('참된 밤', ['참된 밤', '진야', '신야'], 120), ('호무라', ['호무라', '화군', '불무리'], 108)]
def h(path): return a.sha(path)
def save(name, value): (O / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf8')
def quote(s): return json.dumps(s, ensure_ascii=False)
def readjl(path): return [json.loads(l) for l in Path(path).read_text('utf8').splitlines() if l.strip()]

def main():
    O.mkdir(parents=True, exist_ok=True)
    ptr = a.readj(R / 'ui_cumulative/current.json'); rt = Path(ptr['runtime']); src = rt / 'NightRemaster.ain'
    assert h(src) == EXPECTED, ('runtime AIN moved', h(src))
    assert h(Path(ptr['manifest'])) == ptr['manifest_sha256']
    p.exact_tree(rt, a.readj(Path(ptr['manifest']))['files'])
    save('source_pointer.json', ptr); save('save_hashes_before_build.json', p.snapshot_saves()); shutil.copy2(src, O / 'baseline_NightRemaster.ain')
    # ---------- 1. MSG1 ----------
    bs = src.read_bytes(); plain, start, end, raw = b.raw_messages(bs)
    baseline = [b.decode(x) for x in raw]; text = list(baseline)
    assert len(raw) == 100944
    fmap = readjl(Q / 'final/final_map_20261001.jsonl'); extra = readjl(Q / 'final/extra_edits.jsonl')
    seen = set()
    for x in fmap + extra:
        i = x['m_id']; assert i not in seen; seen.add(i)
        assert x['current'] == baseline[i], (i, x['current'], baseline[i])
        assert x['proposed'] and x['proposed'] != baseline[i]
        text[i] = x['proposed']
    prelayout = list(text)
    _, faces = a.parse_fnl_font(rt / 'NightRemasterFont.fnl', 0); face, den, _ = a.select_fnl_face(faces, 60)
    proxy = a.readj(a.PROXY); indices, _ = a.load_proxy_indices(proxy, len(face.widths)); meter = a.WidthMeasurer(face, den, indices, -2., 2., 0.)
    @functools.lru_cache(maxsize=200000)
    def width(s): return meter.measure(s, True)['max_width_px']
    pages = a.readj(a.HERE / 'message_page_groups.json')['pages']
    uses = collections.Counter(i for pg in pages for i in pg['body_message_ids'])
    cs = plain.index(b'CODE'); code = plain[cs + 8:cs + 8 + struct.unpack_from('<I', plain, cs + 4)[0]]
    records = []; failures = []; chain_counts = collections.Counter()
    for pg in pages:
        ids = pg['body_message_ids']; budget = 668 if pg['window_type'] == 'Face' else 884
        if not any(text[i] != baseline[i] for i in ids): continue
        if not any(width(text[i]) > budget for i in ids): continue
        assert pg['complete'] and pg['window_type'] in ('Text', 'Face', 'All') and pg['font_command'] == 0
        assert len(pg['speaker_message_ids']) <= 1 and all(uses[i] == 1 for i in ids)
        chain = b''.join(struct.pack('<HIHI', 0x59, r['message_id'], 0x30, 6972 if r['terminator'] == 'R' else 6973) for r in pg['messages'])
        n = code.count(chain); assert n >= 1, ('native page chain missing', pg['page_id']); chain_counts[n] += 1
        vals = [text[i] for i in ids]; nonempty = [s for s in vals if s.strip()]
        assert all(not re.search(r'[\x00-\x1f\x7f]|\$\{|%[0-9$.]*[sdif]', s) for s in vals)
        quoted = nonempty[0].startswith(('「', '（')); indent = '　' if quoted else ''
        combined = ' '.join(s.strip('　 ') for s in nonempty); combined = re.sub(r' (?=[」』）】!?！？.,、。])', '', combined)
        lines = []; rest = combined
        while rest:
            prefix = indent if lines else ''
            if width(prefix + rest) <= budget: lines.append(prefix + rest); break
            splits = [k for k, c in enumerate(rest) if c == ' ' and k > 0 and width(prefix + rest[:k]) <= budget and rest[k + 1:k + 2] not in '」』）】!?！？.,、。']
            if not splits: break
            pos = max(splits); lines.append(prefix + rest[:pos]); rest = rest[pos + 1:]
        else: rest = ''
        if not lines or width(lines[-1]) > budget or ''.join(lines).replace(' ', '').replace('　', '') != combined.replace(' ', '') or len(lines) > len(ids):
            failures.append(dict(page_id=pg['page_id'], ids=ids, window=pg['window_type'], budget=budget, before=vals, attempt=lines)); continue
        while len(lines) > 1 and width(lines[-1]) < budget * .18:
            previous = lines[-2]; cut = previous.rfind(' ')
            if cut < 1: break
            move = indent + previous[cut + 1:] + ' ' + lines[-1].lstrip('　')
            if width(move) > budget or not previous[:cut].strip('　 '): break
            lines[-2] = previous[:cut]; lines[-1] = move
        final = lines + [''] * (len(ids) - len(lines))
        assert re.sub(r'\s', '', ''.join(vals)) == re.sub(r'\s', '', ''.join(final))
        assert all(width(s) <= budget for s in final)
        for i, s in zip(ids, final): text[i] = s
        records.append(dict(page_id=pg['page_id'], ids=ids, window=pg['window_type'], budget=budget, before=vals, after=final, widths=[width(s) for s in final]))
    changes = {i: s for i, s in enumerate(text) if s != baseline[i]}
    classes = {x['message_id']: x for x in a.readj(a.HERE / 'message_window_classification.json')['rows']}
    unresolved = []; unsupported = []
    for i, s in changes.items():
        c = classes.get(i)
        if not c or c['ambiguous'] or c['font_commands'] != [0] or c['message_roles'] != ['Body']: unsupported.append(dict(m_id=i, cls=c, text=s)); continue
        budget = 668 if c['window_types'] == ['Face'] else 884
        if width(s) > budget: unresolved.append(dict(m_id=i, width=width(s), budget=budget, text=s))
        assert b.decode(b.encode(s)) == s, i
        assert re.findall(r'[\x00-\x1f\x7f]', baseline[i]) == re.findall(r'[\x00-\x1f\x7f]', s)
    save('layout_records.json', records); save('layout_failures.json', failures); save('unresolved_width.json', unresolved); save('unsupported_window.json', unsupported)
    if failures or unresolved:
        print(json.dumps(dict(status='LAYOUT_NEEDS_MANUAL', failures=len(failures), unresolved=unresolved[:20], f=failures[:5]), ensure_ascii=False, indent=1)[:6000]); raise SystemExit(2)
    out_raw = list(raw)
    for i, s in changes.items(): out_raw[i] = b.encode(s)
    body = b''.join(struct.pack('<I', len(x)) + bytes((c + n + 0x60) & 255 for n, c in enumerate(x)) for x in out_raw)
    newplain = plain[:start + 12] + body + plain[end:]
    ain_a = O / 'msg_only.ain'; ain_a.write_bytes(b.pack(newplain, bs[:8]))
    check, s2, e2, decoded = b.raw_messages(ain_a.read_bytes())
    assert check[:s2 + 12] == plain[:start + 12] and check[e2:] == plain[end:] and len(decoded) == 100944
    assert [b.decode(x) for x in decoded] == text
    save('final_edits.json', {str(i): s for i, s in changes.items()})
    print('MSG1 done: changed', len(changes), 'reflow pages', len(records), 'layout-only', sum(text[i] != prelayout[i] for i in range(len(text))), 'chain counts', dict(chain_counts))
    # ---------- 2. 용어 표 ----------
    b.TERMS[:] = TERMS8
    jp = {r['m_id']: r['jp'] for r in readjl(Q / 'review_base/base_lines.jsonl')}
    fire_ids = set()
    for pg in pages:
        ids = pg['body_message_ids']; j = ''.join(jp.get(i, '') for i in ids)
        if '火群' in j: assert '穂群' not in j, ids; fire_ids.update(ids)
    for i, s in enumerate(text):
        if '호무라' in s and i not in fire_ids:
            pg = next((pg for pg in pages if i in pg['body_message_ids']), None); j = ''.join(jp.get(k, '') for k in (pg['body_message_ids'] if pg else [i]))
            assert '穂群' in j and '火群' not in j, (i, s)
    def tokens_for(i, s):
        ts = b.tokens(s)
        if any(k == 't' and v == 7 for k, v in ts) and i not in fire_ids:
            b.TERMS[:] = TERMS8[:7]; ts = b.tokens(s); b.TERMS[:] = TERMS8
        return ts
    entries = {}
    for i, s in enumerate(text):
        ts = tokens_for(i, s)
        if any(k == 't' for k, v in ts): entries[i] = ts
    assert all(b.render(t) == text[i] for i, t in entries.items()), 'default must roundtrip exactly'
    dynamic = {}; drec = []; dfail = []
    for pg in pages:
        ids = pg['body_message_ids']; hit = [i for i in ids if i in entries]
        if not hit: continue
        budget = 716 if pg['window_type'] == 'Face' else 932
        if all(b.width(b.render(entries.get(i, [('s', text[i])]), worst=True)) <= budget for i in ids): continue
        assert pg['complete'] and pg['font_command'] == 0 and pg['window_type'] in ['Face', 'Text', 'All'], pg['page_id']
        nonempty = [text[i] for i in ids if text[i].strip()]; quoted = nonempty[0].startswith(('「', '（'))
        full = ' '.join(t.strip('　 ') for t in nonempty); full = re.sub(r' (?=[」』）】!?！？.,、。])', '', full)
        ts = tokens_for(ids[0], full); worst = b.render(ts, worst=True); lines = b.wrap(worst, budget, quoted)
        if lines is None or len(lines) > len(ids): dfail.append(dict(ids=ids, budget=budget, text=full, lines=lines)); continue
        for pos, i in enumerate(ids): dynamic[i] = f'KR_TermWrapLine({b.expr(ts)}, {budget}, {pos}, {str(quoted).lower()})'
        drec.append(dict(ids=ids, budget=budget, worst=lines, quoted=quoted, source=full))
    save('term_dynamic_pages.json', drec); save('term_layout_failures.json', dfail)
    assert not dfail, ('term page capacity', len(dfail))
    bodies = collections.defaultdict(list); coverage = []
    for i in sorted(set(entries) | set(dynamic)):
        expression = dynamic.get(i, b.expr(entries[i]) if i in entries else quote(text[i]))
        bodies[i // 1000].append(f'if (id == {i} && text == {quote(text[i])}) return {expression};')
        coverage.append(dict(id=i, text=text[i], tokens=entries.get(i), dynamic_page=i in dynamic, changed=i in changes))
    save('term_coverage.json', coverage)
    code = []
    for g, body in sorted(bodies.items()): code.append(f'string KR_T9Msg{g}(int id, string text) {{\n' + '\n'.join(body) + '\nreturn KR_T8Message(id, text);\n}')
    code.append('string KR_T9Message(int id, string text) {\nif (SystemService.SystemVariable_Get("YoruKR.Term.Active") != "1") return text;\n'
                + '\n'.join(f'if (id >= {g*1000} && id < {(g+1)*1000}) return KR_T9Msg{g}(id, text);' for g in sorted(bodies)) + '\nreturn KR_T8Message(id, text);\n}')
    jaf = '\n'.join(code) + '\n'
    (O / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    jaf_p = re.sub(r'"(?:[^"\\]|\\.)*"', lambda z: json.dumps(b.encode(json.loads(z[0])).decode('cp932'), ensure_ascii=False) if any('\uac00' <= c <= '\ud7a3' or c in '·…「」【】　' for c in json.loads(z[0])) else z[0], jaf)
    (O / 'helpers.jaf').write_text(jaf_p, 'utf8')
    b.cmd('ain', 'dump', '-j', '-o', O / 'base_meta.json', ain_a); m = b.read_meta(O / 'base_meta.json'); byname = {f['name']: f['index'] for f in m['functions']}
    for n in ['KR_TermMessage', 'KR_T8Message', 'KR_TermWrapLine', 'KR_TermGet', 'KR_TermParticle']: assert n in byname, n
    assert 'KR_T9Message' not in byname
    decl = O / 'declared.ain'; b.cmd('ain', 'edit', '--jaf', O / 'helpers.jaf', '-o', decl, ain_a)
    b.cmd('ain', 'dump', '-j', '-o', O / 'declared_meta.json', decl); dm = b.read_meta(O / 'declared_meta.json'); added = dm['functions'][len(m['functions']):]; ids = {f['name']: f['index'] for f in added}
    assert set(ids) == {f'KR_T9Msg{g}' for g in bodies} | {'KR_T9Message'}, sorted(ids)
    patch = []
    for f in added:
        path = O / f"jaf_{f['index']}.jam"; b.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(b.clean(b.native_lower(path.read_text('utf8')), f['name']))
    tm = byname['KR_TermMessage']
    b.cmd('ain', 'dump', '--function', 'KR_TermMessage', '-o', O / 'original_KR_TermMessage.jam', ain_a)
    orig = (O / 'original_KR_TermMessage.jam').read_text('utf8'); assert 'CALLFUNC KR_T8Message' in orig and orig.count('CALLFUNC') == 1, orig
    patch.append(f'FUNC {tm}\n\t.LOCALREF id\n\t.LOCALREF text\n\tA_REF\n\tCALLFUNC KR_T9Message\n\tRETURN\nENDFUNC KR_TermMessage\n')
    (O / 'patch.jam').write_text('\n'.join(patch), 'utf8'); out = O / 'NightRemaster.ain'; b.cmd('ain', 'edit', '--jam', O / 'patch.jam', '-o', out, decl)
    old = b.unpack(ain_a.read_bytes()); rawb = bytearray(b.unpack(out.read_bytes())); oldn = struct.unpack_from('<I', old, 12)[0]; newn = struct.unpack_from('<I', rawb, 12)[0]
    struct.pack_into('<I', rawb, 24 + newn, m['functions'][0]['address']); assert rawb[16:16 + oldn] == old[16:16 + oldn]
    out.write_bytes(b.pack(bytes(rawb), src.read_bytes()[:8]))
    b.cmd('ain', 'dump', '-j', '-o', O / 'candidate_meta.json', out); nm = b.read_meta(O / 'candidate_meta.json')
    for f, g in zip(m['functions'], nm['functions']):
        t = dict(f)
        if f['index'] == tm: t['address'] = g['address']
        assert t == g, f['index']
    for k in m:
        if k != 'functions': assert m[k] == nm[k], k
    new = b.unpack(out.read_bytes()); assert new[16:16 + oldn] == old[16:16 + oldn], 'CODE prefix changed'
    assert [b.decode(x) for x in b.raw_messages(out.read_bytes())[3]] == text
    assert b.strings(new)[2][:len(b.strings(old)[2])] == b.strings(old)[2]
    for fid in [tm] + list(ids.values()): b.cmd('ain', 'dump', '--function', b.symbol(nm, fid), '-o', O / f'built_{fid}.jam', out)
    built = (O / f'built_{tm}.jam').read_text('utf8'); assert 'CALLFUNC KR_T9Message' in built and built.count('CALLFUNC') == 1
    b.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', O / 'native_raw_code.jam', out)
    audit = b.audit(out, O / 'candidate_meta.json', O / 'native_raw_code.jam', rt / 'NightRemaster.exe'); save('native_opcode_audit.json', audit); assert audit['all_active_opcodes_supported']
    # 원래 CODE 안의 message 훅이 KR_TermMessage 를 부르는지(호출자 불변) 확인
    msgfn = (O / 'built_6971.jam'); b.cmd('ain', 'dump', '--function', b.symbol(nm, 6971), '-o', msgfn, out); assert 'CALLFUNC KR_TermMessage' in msgfn.read_text('utf8')
    ev = dict(status='CLAUDE_TEXT_STAGED', author=AUTHOR, source_pointer=ptr, source_files={'NightRemaster.ain': EXPECTED}, files={'NightRemaster.ain': h(out)},
              msg_only_sha256=h(ain_a), changed_fields=len(changes), changed_ids=sorted(changes), map_rows=len(fmap), extra_rows=len(extra), reflow_pages=len(records),
              layout_only_fields=sum(text[i] != prelayout[i] for i in range(len(text))), chain_counts=dict(chain_counts), unsupported_window=len(unsupported),
              term_rows=len(coverage), term_rows_changed=sum(1 for c in coverage if c['changed']), term_dynamic_pages=len(drec), added_functions=ids, relocated=[tm],
              CODE_prefix_exact=True, STR0_prefix_exact=True, MSG1_exact=False, MSG_count=100944, save_schema_changes=0, native_tested=False, terms=[t[0] for t in TERMS8])
    save('build_evidence.json', ev); print('STAGED', O, h(out), json.dumps({k: v for k, v in ev.items() if k not in ('changed_ids', 'source_pointer')}, ensure_ascii=False)[:1500])

if __name__ == '__main__':
    try: main()
    except AssertionError as ex: print('ASSERT', str(ex)[-3000:]); raise SystemExit(1)
