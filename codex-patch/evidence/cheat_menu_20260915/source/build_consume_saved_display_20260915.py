"""Close the five-consumable legacy-save display lane, preserving all gameplay state."""
from pathlib import Path
import copy,json,re,struct,datetime
from build_saved_name_refresh_20260915 import R,A,cmd,symbol,read,sha,write
from integrate_ui_opening_20260913 import read_meta
from repair_ui_runtime_weapon_text_20260913 import unpack,strings
from audit_dynamic_ui_20260915 import decode,encode

O=Path('consume_saved_display_20260915')
GETTERS=[(26668,'<sName>','name'),(26669,'<sName>','name'),(26671,'<sMoldName>','mold'),(26672,'<sMoldName>','mold'),(26680,'<sDesc>','description'),(26681,'<sDesc>','description')]
MATERIAL_DESCRIPTION='무기 강화 재료'

def main():
    O.mkdir(exist_ok=True);p=read(R/'ui_cumulative/current.json');assert p['status']=='SAVED_DISPLAY_REFRESH_STATIC_PASS_NATIVE_PENDING'
    mp=Path(p['manifest']);assert sha(mp)==p['manifest_sha256'];m=read(mp);rt=Path(p['runtime']);src=rt/'NightRemaster.ain'
    assert sha(src)=='fd2920d8252b6e973b321b35aa654e6e14c9787721e172f6e1412b7c34dc3365'
    write(O/'source_pointer.json',p);(O/'source.ain').write_bytes(src.read_bytes())
    cmd('ain','dump','-j','-o',O/'source_meta.json',src);meta=read_meta(O/'source_meta.json')
    creator=cmd('ain','dump','--function','C_ConsumeItem@Create',src);(O/'original_26687.jam').write_text(creator,encoding='utf8')
    # Recover approved current names, descriptions and original padding from the
    # shipped constructor itself, not from a new translation or a hand-entered table.
    cases=re.split(r'(?m)^\.CASE 370:\d+ (\d+)\n',creator);rows=[]
    approved=read(Path(m['item_skill_name_revision']['display_edits']))['consumables']
    for i in range(1,len(cases),2):
        itemid=int(cases[i]);block=cases[i+1]
        def operand(setter):
            match=re.search(r'PUSH '+str(setter)+r'\n\tS_PUSH ("(?:[^"\\]|\\.)*")',block);assert match,(itemid,setter)
            # JAM can emit literal TAB inside strings; strict=False preserves it.
            return json.loads(match.group(1),strict=False)
        raw_name=operand(26670);raw_desc=operand(26682)
        prefix='\u3000\u3000' if 'PUSH 26673\n\tS_PUSH "　　"' in block else ''
        name=decode(raw_name.encode('cp932'));desc=decode(raw_desc.encode('cp932'))
        ref=next(x for x in approved if x['stable_id']==f'AIN:consume:{itemid}')
        assert name==ref['target'] and desc==ref['description']
        rows.append(dict(id=itemid,name=name,description=desc,mold=prefix+name,padding=prefix,
            raw_name=raw_name,raw_description=raw_desc,raw_mold=prefix+raw_name))
    assert [x['id'] for x in rows]==[1,2,3,4,5]
    write(O/'display_catalog.json',dict(translator_model='Codex internal',semantic_changes=False,source='Current approved C_ConsumeItem@Create constants and display_edits consumables',rows=rows))
    patch=[]
    for fid,member,field in GETTERS:
        name=symbol(meta,fid);original=cmd('ain','dump','--function',name,src)
        assert f'.STRUCTREF C_ConsumeItem {member}\n\tA_REF\n\tRETURN' in original
        (O/f'original_{fid}.jam').write_text(original,encoding='utf8');ops=[f'FUNC {fid}']
        for row in rows:
            label=f'kr_consume_next_{fid}_{row["id"]}'
            ops += ['\t.STRUCTREF C_ConsumeItem <nID>',f'\tPUSH {row["id"]}','\tEQUALE',f'\tIFZ {label}',
                '\tS_PUSH '+json.dumps(row['raw_'+field],ensure_ascii=False),'\tRETURN',label+':']
        ops += [f'\t.STRUCTREF C_ConsumeItem {member}','\tA_REF','\tRETURN',f'ENDFUNC {name}'];patch.append('\n'.join(ops))
    ui_rows=[]
    for fid in [31454,31481]:
        original=cmd('ain','dump','--function',symbol(meta,fid),src)
        needle='S_PUSH "武器強化素材"';assert original.count(needle)==1 and 'PUSH 28000\n\t'+needle+'\n\tCALLMETHOD 1' in original
        (O/f'original_{fid}.jam').write_text(original,encoding='utf8')
        edited=original.replace(needle,'S_PUSH '+json.dumps(encode(MATERIAL_DESCRIPTION).decode('cp932'),ensure_ascii=False))
        patch.append(edited)
        ui_rows.append(dict(stable_id=f'AIN:function:{fid}:material_description',source='武器強化素材',target=MATERIAL_DESCRIPTION,
            consumer='C_SimpleDiscript@SetText(string)',context='Description for element-stone IDs10..13 in consumable/crafting selection',translator_model='Codex internal'))
    write(O/'ui_translation_map.json',dict(translator_model='Codex internal',rows=ui_rows))
    jam=O/'consume_patch.jam';jam.write_text('\n\n'.join(patch)+'\n',encoding='utf8')
    out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,src);cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);after=read_meta(O/'candidate_meta.json')
    ids=sorted([x[0] for x in GETTERS]+[31454,31481]);changed=[];assert len(meta['functions'])==len(after['functions'])
    for old,new in zip(meta['functions'],after['functions']):
        a=copy.deepcopy(old);b=copy.deepcopy(new);aa=a.pop('address');bb=b.pop('address');assert a==b,old['index']
        if aa!=bb:changed.append(old['index'])
    assert changed==ids
    for k in meta:
        if k!='functions':assert meta[k]==after[k],k
    before=unpack(src.read_bytes());plain=unpack(out.read_bytes());n=struct.unpack_from('<I',before,12)[0];assert plain[16:16+n]==before[16:16+n]
    bs=strings(before)[2];ns=strings(plain)[2];assert ns[:len(bs)]==bs
    assert before[before.index(b'MSG1'):before.index(b'STR0')]==plain[plain.index(b'MSG1'):plain.index(b'STR0')]
    for fid in ids:
        s=cmd('ain','dump','--function',symbol(after,fid),out);assert f'FUNC {fid}\n' in s;(O/f'built_{fid}.jam').write_text(s,encoding='utf8')
    for f in [26693,26694,27188,27749,31454,31481]:
        s=cmd('ain','dump','--function',symbol(after,f),out);assert s;(O/f'consumer_{f}.jam').write_text(s,encoding='utf8')
    ev=dict(status='STAGED_CONSUMABLE_DISPLAY_STATIC_PASS_REVIEW_PENDING',time=datetime.datetime.now().astimezone().isoformat(),source_pointer=p,
        source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},patched_function_ids=ids,consumable_ids=[1,2,3,4,5],
        display_fields=['name','padded_mold_name','description'],new_functions=0,existing_signatures_globals_structs_metadata_exact=True,
        original_CODE_prefix_exact=True,MSG1_all100944_exact=True,original_STR0_prefix_exact=True,added_STR0_entries=len(ns)-len(bs),
        original_constructor_and_all_mechanics_exact=True,additional_UI_description_operands=ui_rows,no_inventory_count_rank_found_stat_or_saved_multiplier_writes=True,
        prior16_EX_getters_and_weapon_comment_refresh_exact=True,negative_unknown_ID_fallback='Original corresponding stored field',
        source_catalog_sha256=sha(O/'display_catalog.json'),translator_model='Codex internal',semantic_translation_changes='Two identical adjacent element-stone description display operands only; consumable catalog wording unchanged',
        native_verified=False,game_or_saves_modified=False)
    write(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
