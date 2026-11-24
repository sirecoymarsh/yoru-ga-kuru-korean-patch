"""Hash-bound, style-only release checks; no native gameplay claim."""
from pathlib import Path
import copy, json, struct
from cheat_support_20260915 import sha, savej, read_meta, cmd
from build_mod_menu_style_20260917 import O, TYPE, YELLOW
from build_remaster_multiplier_20260915 import ex, read_afa3, part, child, txt_info, val, setlist, decode
from repair_ui_runtime_weapon_text_20260913 import unpack, strings
import verify_mod_menu_style_20260917 as v


def main():
    ev = json.loads((O/'build_evidence.json').read_text(encoding='utf8'))
    rt = Path(ev['source_pointer']['runtime'])
    assert all(sha(O/n) == h for n,h in ev['files'].items())
    assert all(sha(rt/n) == h for n,h in ev['source_files'].items())
    cmd('ain','dump','-j','-o',O/'release_source_meta.json',rt/'NightRemaster.ain')
    oldmeta = read_meta(O/'release_source_meta.json')
    newmeta = read_meta(O/'candidate_meta.json')
    expected = copy.deepcopy(oldmeta)
    expected['functions'][27936]['address'] = newmeta['functions'][27936]['address']
    assert expected == newmeta
    a,b = [unpack(p.read_bytes()) for p in [rt/'NightRemaster.ain',O/'NightRemaster.ain']]
    size = struct.unpack_from('<I',a,12)[0]
    assert a[16:16+size] == b[16:16+size]
    assert strings(b)[2][:len(strings(a)[2])] == strings(a)[2]
    assert a[a.index(b'MSG1'):a.index(b'SWI0')] == b[b.index(b'MSG1'):b.index(b'SWI0')]
    assert all(sha(rt/n) == h for n,h in ev['unchanged_files'].items())
    source,target = rt/'NightRemasterPact.afa',O/'NightRemasterPact.afa'
    old,new = read_afa3(source),read_afa3(target)
    assert len(old.entries) == len(new.entries) == 187
    labels = {153:'KR_AutoEquipButtonLabel',154:'KR_AutoStoneButtonLabel',161:'KR_SweepButtonLabel'}
    changed = []
    with source.open('rb') as af,target.open('rb') as bf:
        for i,(x,y) in enumerate(zip(old.entries,new.entries)):
            assert (x.no,x.name,x.unknown0,x.unknown1) == (y.no,y.name,y.unknown0,y.unknown1)
            af.seek(x.absolute_offset); bf.seek(y.absolute_offset)
            ab,bb = af.read(x.size),bf.read(y.size)
            if ab == bb: continue
            changed.append(i)
            assert i in labels
            op,np = O/f'original_pact_{i}.pactex',O/f'pact_{i}_yellow.pactex'
            assert ab == op.read_bytes() and bb == np.read_bytes()
            od,nd = ex.decode_ex(op),ex.decode_ex(np)
            # Only the compressed DATA length changes when the color is encoded.
            assert od.header[:24] == nd.header[:24] and od.header[28:] == nd.header[28:]
            assert struct.unpack_from('<I',nd.header,24)[0] == len(bb)-len(nd.header)
            oc = child(txt_info(part(od,labels[i])),'テキスト装飾')
            nc = child(txt_info(part(nd,labels[i])),'テキスト装飾')
            ints = lambda d:[struct.unpack('<i',z.value.payload.raw)[0] for z in val(d,'フォント色').items]
            assert ints(nc) == list(YELLOW[:3])
            setlist(nc,'フォント色',ints(oc))
            assert nd.serialize_payload() == od.serialize_payload()
    assert changed == [153,154,161]
    # Real shipped names, rather than only short placeholder labels.
    v.FONT = v.Font(rt/'NightRemasterFont.fnl')
    items = ex.decode_ex(rt/'NightRemasterEX.ex').blocks[48].payload.rows
    names = [decode(row[2].payload.value) for row in items]
    width = lambda s:v.FONT.metrics(s,20)[0]
    longest = max(names,key=width)
    labels = ['균형 추천','공격 추천','생존 추천','유틸리티 추천'] + [f'{i}번 [유지] {longest}' for i in range(1,5)] + ['취소']
    preview = '자동 장착 · 유틸리티 추천\n' + '\n'.join(f'{i}번: {longest} → {longest}' for i in range(1,5)) + '\n비용 없음 · 다른 캐릭터의 장비는 변경하지 않습니다.'
    geometry = []
    for title,choices in [('자동 장착 · 현재 캐릭터의 장비만 추천\n　유지할 슬롯을 선택한 뒤 추천 기준을 고르세요.',labels),(preview,['취소','장착 적용'])]:
        vm = v.VM(O/'built_27936.jam',TYPE,title,choices,size=20,gap=8); vm.run()
        assert vm.locals[19] <= 1280 and vm.locals[20] <= 720
        for info in vm.obj[4]:
            assert width(info[2])+20 <= info['width'] and info['height'] == 48
        for line in title.splitlines(): assert width(line)+56 <= vm.locals[19]
        geometry.append([vm.locals[19],vm.locals[20]])
    verify = json.loads((O/'verification.json').read_text(encoding='utf8'))
    assert verify['files'] == ev['files'] and verify['status'] == 'MOD_MENU_STYLE_FIXTURES_PASS'
    report = dict(status='RELEASE_STATIC_PASS',files=ev['files'],changed_functions=[27936],
                  old_CODE_STR0_MSG1_exact=True,metadata_only_one_address=True,
                  changed_archive_entries=changed,other_archive_entries_exact=184,
                  only_pact_FontColor_changed=True,longest_item_name=longest,
                  real_name_layout_sizes=geometry,proofs={p.name:sha(p) for p in O.glob('*proof.png')},
                  native_gameplay_verified=False)
    savej(O/'release_checks.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
