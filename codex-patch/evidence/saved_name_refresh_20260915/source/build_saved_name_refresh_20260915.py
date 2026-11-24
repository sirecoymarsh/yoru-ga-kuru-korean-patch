"""Read current display tables rather than translated strings serialized in older saves."""
from pathlib import Path
import copy,json,re,struct,subprocess,hashlib,datetime
from integrate_ui_opening_20260913 import read_meta
from repair_ui_runtime_weapon_text_20260913 import unpack,strings
from publish_training_fix_20260915 import read,sha

O=Path('saved_name_refresh_20260915')
R=Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908')
A=R.parent/'YoruGaKuru_KR_rebuild_20260830_compat_v2/tools/alice-tools-0.13.0/alice.exe'
ROWS=[(26155,'C_Monster','<sName>','monster',7,'name'),(26156,'C_Monster','<sName>','monster',7,'name'),
 (26810,'C_Weapon','<name>','武器データ',39,'name'),(26811,'C_Weapon','<name>','武器データ',39,'name'),
 (26756,'C_EquipItem','<sName>','装備アイテムデータ',48,'name'),(26757,'C_EquipItem','<sName>','装備アイテムデータ',48,'name')]
for f,member,field in [(26786,'<sName>','name'),(26789,'<sCommentS>','simpleName'),(26792,'<sComment1>','desc1'),(26795,'<sComment2>','desc2'),(26798,'<sComment3>','desc3')]:
    for i in [f,f+1]:ROWS.append((i,'C_Skill',member,'スキルデータ',6,field))

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def cmd(*args):
    q=subprocess.run([str(A),*map(str,args)],capture_output=True,timeout=60)
    assert q.returncode==0,(args,q.stderr.decode('utf8','replace'));return q.stdout.decode('utf8')
def symbol(meta,fid):
    name=meta['functions'][fid]['name'];prior=sum(f['name']==name for f in meta['functions'][:fid]);return name+('#'+str(prior) if prior else '')

def main():
    O.mkdir(exist_ok=True);p=read(R/'ui_cumulative/current.json');m=read(Path(p['manifest']));assert sha(Path(p['manifest']))==p['manifest_sha256']
    assert p['status']=='REMASTER_MULTIPLIERS_STATIC_PASS_NATIVE_PENDING'
    rt=Path(p['runtime']);src=rt/'NightRemaster.ain';assert sha(src)=='cf249bab7f5db4db247a0cfff43b8a73fda5a9616bd1ddf12639daeca4debe6d'
    write(O/'source_pointer.json',p);(O/'source.ain').write_bytes(src.read_bytes());(O/'source.ex').write_bytes((rt/'NightRemasterEX.ex').read_bytes())
    cmd('ain','dump','-j','-o',O/'source_meta.json',src);meta=read_meta(O/'source_meta.json');code=[]
    for fid,cls,member,node,block,field in ROWS:
        name=symbol(meta,fid);s=cmd('ain','dump','--function',name,src);assert s and f'.STRUCTREF {cls} {member}\n\tA_REF\n\tRETURN' in s
        (O/f'original_{fid}.jam').write_text(s,encoding='utf8')
        label=f'kr_saved_name_fallback_{fid}'
        ops=[f'FUNC {fid}',f'\t.STRUCTREF {cls} <nID>','\tPUSH 0','\tLT',f'\tIFNZ {label}']
        if node=='monster':
            key=['\tS_PUSH "モンスターデータ.%03d"',f'\t.STRUCTREF {cls} <nID>','\tS_MOD 2']
            ops+=key+['\tPUSH 2','\tPUSH 0','\tCALLFUNC EX_IsExistA',f'\tIFZ {label}']
            ops+=key+['\tPUSH 2',f'\t.STRUCTREF {cls} {member}','\tA_REF','\tPUSH 0','\tCALLFUNC EX_AString','\tRETURN']
        else:
            key=[f'\tS_PUSH "{node}"',f'\t.STRUCTREF {cls} <nID>',f'\tS_PUSH "{field}"']
            ops+=key+['\tPUSH 0','\tCALLFUNC EX_IsExistIA2',f'\tIFZ {label}']
            ops+=key+[f'\t.STRUCTREF {cls} {member}','\tA_REF','\tPUSH 0','\tCALLFUNC EX_IA2String','\tRETURN']
        ops+=[label+':',f'\t.STRUCTREF {cls} {member}','\tA_REF','\tRETURN',f'ENDFUNC {name}']
        code.append('\n'.join(ops))
    # This routine updates only weapon-description strings. It does NOT call
    # LoadData/Create and cannot reset known weapons, inventory, modifiers or stats.
    old=cmd('ain','dump','--function','C_SceneSaveLoad@ExecAfterLoad',src);(O/'original_29556.jam').write_text(old,encoding='utf8')
    assert 'CALLFUNC MemModeInfo::Load\n\tCALLFUNC SystemFlagManager::Load\n\tRETURN' in old
    code.append('FUNC 29556\n\tCALLFUNC MemModeInfo::Load\n\tCALLFUNC SystemFlagManager::Load\n\tCALLFUNC L_Weapon::LoadComment\n\tPOP\n\tRETURN\nENDFUNC C_SceneSaveLoad@ExecAfterLoad')
    jam=O/'refresh_patch.jam';jam.write_text('\n\n'.join(code)+'\n',encoding='utf8')
    out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,src)
    cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);after=read_meta(O/'candidate_meta.json');patched=sorted([x[0] for x in ROWS]+[29556])
    assert len(after['functions'])==len(meta['functions'])
    changed=[]
    for before,new in zip(meta['functions'],after['functions']):
        b=copy.deepcopy(before);n=copy.deepcopy(new);ba=b.pop('address');na=n.pop('address');assert b==n,before['index']
        if ba!=na:changed.append(before['index'])
    assert changed==patched,(changed,patched)
    for k in meta:
        if k!='functions':assert meta[k]==after[k],k
    before=unpack(src.read_bytes());new=unpack(out.read_bytes());n=struct.unpack_from('<I',before,12)[0]
    assert new[16:16+n]==before[16:16+n]
    bs=strings(before)[2];ns=strings(new)[2];assert ns[:len(bs)]==bs
    assert before[before.index(b'MSG1'):before.index(b'STR0')]==new[new.index(b'MSG1'):new.index(b'STR0')]
    for fid in patched:
        s=cmd('ain','dump','--function',symbol(after,fid),out);assert s and f'FUNC {fid}\n' in s
        (O/f'built_{fid}.jam').write_text(s,encoding='utf8')
    ev=dict(status='STAGED_STATIC_BUILD_PASS_REVIEW_PENDING',time=datetime.datetime.now().astimezone().isoformat(),source_pointer=p,
        source_files={'NightRemaster.ain':sha(src),'NightRemasterEX.ex':sha(rt/'NightRemasterEX.ex')},files={'NightRemaster.ain':sha(out)},
        patched_function_ids=patched,new_function_count=0,getter_rows=ROWS,globals_structures_and_all_function_signatures_exact=True,
        unchanged_all_other_metadata=True,original_CODE_prefix_exact=True,all_100944_MSG1_exact=True,original_STR0_prefix_exact=True,
        added_STR0_entries=len(ns)-len(bs),multiplier_callbacks_and_calc_addresses_exact=True,EX_and_PACT_unchanged=True,
        display_strategy='Known stable IDs use current native MainEXFile fields. Negative or missing IDs/fields return original stored string without indexing mutable arrays.',
        after_load_strategy='Existing ExecAfterLoad additionally invokes original L_Weapon::LoadComment, updating only weapon-description strings, not LoadData or game state.',
        native_verified=False,game_or_save_modified=False,translator_model='Codex internal (no new semantic translations)')
    write(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
