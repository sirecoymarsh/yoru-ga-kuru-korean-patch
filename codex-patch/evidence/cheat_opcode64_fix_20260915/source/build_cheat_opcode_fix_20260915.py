"""Compatibility-only correction of three helpers; all visible assets unchanged."""
from pathlib import Path
import json,copy,struct,shutil,datetime
from cheat_support_20260915 import cmd,read_meta,R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=Path('cheat_opcode64_fix_20260915');OLD=Path('cheat_menu_20260915');IDS=[31852,31853,31860]
def main():
    O.mkdir(exist_ok=True);p=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);src=rt/'NightRemaster.ain'
    assert sha(src)=='e103f27fed0474d830842a017718d0b3aa60955b3880013332654aa0e07eff68'
    assert sha(src)==sha(OLD/'NightRemaster.ain');savej(O/'source_pointer.json',p)
    meta=read_meta(OLD/'candidate_meta.json');parts=[]
    for i in IDS:
        s=(OLD/f'built_{i}.jam').read_text(encoding='utf8');t=native_lower(s);assert t!=s
        (O/f'original_{i}.jam').write_text(s,encoding='utf8');parts.append(t)
    (O/'opcode_fix.jam').write_text('\n'.join(parts),encoding='utf8')
    dest=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'opcode_fix.jam','-o',dest,src)
    cmd('ain','dump','-j','-o',O/'candidate_meta.json',dest);after=read_meta(O/'candidate_meta.json');changed=[]
    for a,b in zip(meta['functions'],after['functions']):
        aa=dict(a);bb=dict(b);x=aa.pop('address');y=bb.pop('address');assert aa==bb
        if x!=y:changed.append(a['index'])
    assert changed==IDS and len(meta['functions'])==len(after['functions'])
    for k in meta:
        if k!='functions':assert meta[k]==after[k],k
    b=unpack(src.read_bytes());a=unpack(dest.read_bytes());n=struct.unpack_from('<I',b,12)[0]
    assert a[16:16+n]==b[16:16+n]
    assert a[a.index(b'MSG1'):]==b[b.index(b'MSG1'):]
    for f in OLD.glob('built_*.jam'):shutil.copy2(f,O/f.name)
    for i in IDS:cmd('ain','dump','--function',meta['functions'][i]['name'],'-o',O/f'built_{i}.jam',dest)
    cmd('ain','dump','--raw-code','--no-macros','-o',O/'after_raw_code.jam',dest)
    owned=set(json.loads((OLD/'build_evidence.json').read_text())['AIN']['patched_existing'])|set(range(31836,31861))
    before=audit(src,OLD/'candidate_meta.json',O/'before_raw_code.jam',rt/'NightRemaster.exe',owned)
    full=audit(dest,O/'candidate_meta.json',O/'after_raw_code.jam',rt/'NightRemaster.exe')
    fixed=audit(dest,O/'candidate_meta.json',O/'after_raw_code.jam',rt/'NightRemaster.exe',owned)
    assert [r['opcode'] for r in before['unsupported']]==[64]*6+[130,129,130,129]
    assert fixed['all_active_opcodes_supported'] and full['all_active_opcodes_supported'],full['unsupported'][:20]
    savej(O/'native_opcode_audit.json',dict(before_owned=before,after_owned=fixed,after_all=full))
    ev=dict(status='NATIVE_OPCODE_STATIC_PASS',time=datetime.datetime.now().astimezone().isoformat(),source_pointer=p,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(dest)},patched_function_ids=IDS,
        changes={'float_literals':'6 F_PUSH->PUSH raw IEEE754 bits','route_local_structs':'2 SH_LOCALDELETE/CREATE pairs->native .LOCALCREATE deletion/allocation sequence'},
        metadata_except_three_function_addresses_exact=True,old_CODE_prefix_exact=True,all_MSG1_STR0_and_post_MSG1_sections_exact=True,no_semantic_translation_or_UI_change=True,all_active_native_opcode_dispatch_supported=True,native_gameplay_verified=False)
    savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
