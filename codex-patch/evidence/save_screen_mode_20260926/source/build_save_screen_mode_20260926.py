"""Dual native save screens over the current cumulative build; display-only mode selection."""
from pathlib import Path
import copy,collections,json,re,shutil,struct
import build_pinned_autosave_20260926 as base
import build_save_slots_20260925 as cards
import build_mod_tab_20260915 as mt
from build_remaster_multiplier_20260915 import rename
b=base.b;p=base.p;q=base.q;a=base.a;n=base.n;R=base.R;HERE=Path(__file__).parent;AUTHOR='Codex internal'
O=R/'staging/save_screen_mode_20260926';S=O/'source'
h=base.h;clean=base.clean;textdump=base.textdump;wrapper=base.wrapper
EXPECTED='92f2f7801ce17402486b835fc416c35d4a86dc0bdffa63cf4c09d2e3e58e80e4'
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def begin(body,ops):return re.sub(r'(^FUNC \d+\n)',lambda m:m[0]+ops,body,count=1,flags=re.M)
def once(body,old,new):assert body.count(old)==1,(old,body.count(old));return body.replace(old,new)

def assets():
    d=n.ex.decode_ex(S/'pact_185.pactex');root=n.part(d,'ルートパーツ');mt.ORDER=copy.deepcopy(n.val(root,'子パーツリスト').items[0])
    button=copy.deepcopy(n.part(d,'KR_ItemConfigButton'));rename(button,'KR_SaveStyleButton');n.setlist(button,'座標',[563,34,260]);mt.add(root,button)
    label=copy.deepcopy(n.part(d,'KR_ItemConfigLabel'));rename(label,'KR_SaveStyleLabel');n.setlist(label,'座標',[595,39,261]);n.ss(n.txt_info(label),'テキスト','저장 화면 설정',True);mt.add(root,label)
    dst=O/'pact_185.pactex';dst.write_bytes(n.ex.encode_ex(d.header,d.serialize_payload()))
    mt.remove(root,'KR_SaveStyleButton');mt.remove(root,'KR_SaveStyleLabel');assert d.serialize_payload()==n.ex.decode_ex(S/'pact_185.pactex').serialize_payload()
    # These are the Korean original-family cards before the save-card redesign, not an old AIN.
    for index in [168,169]:
        frozen=R/f'staging/save_slots_20260925/pact_{index}.pactex';assert h(S/f'original_{index}.pactex')==h(frozen)
    result=n.rebuild(S/'NightRemasterPact.afa',O/'NightRemasterPact.afa',{185:dst},[
        ('Asra/SaveOriginalCell.pactex',S/'original_168.pactex'),('Asra/SaveOriginalScene.pactex',S/'original_169.pactex')])
    return dict(archive=result,changed=[185],original_assets_exact={str(i):h(S/f'original_{i}.pactex') for i in [168,169]},
        existing_alternative_assets_exact=True,mods_button=[563,34,192,30],mods_label='저장 화면 설정',reverse_exact=True)

def main():
    ptr=p.read(O/'source_pointer.json');rt=Path(ptr['runtime']);assert ptr==p.read(R/'ui_cumulative/current.json')
    assert h(rt/'NightRemaster.ain')==h(S/'NightRemaster.ain')==EXPECTED
    p.exact_tree(rt,p.read(Path(ptr['manifest']))['files'])
    src=S/'NightRemaster.ain';m=b.read_meta(S/'candidate_meta.json');ids={f['name']:f['index'] for f in m['functions']}
    jaf=cards.korean((HERE/'save_screen_mode_20260926.jaf').read_text('utf8'))
    (O/'helpers.jaf').write_text(jaf,'utf8');decl=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json')
    added=dm['functions'][len(m['functions']):];added_ids={f['name']:f['index'] for f in added}
    patch=[b.clean(b.native_lower(textdump(dm,f['index'],decl)),f['name']) for f in added];relocated=[]
    def change(fid,body):patch.append(body);relocated.append(fid)
    for name,value in [('KR_SaveRows',5),('KR_SavePitch',101)]:
        fid=ids[name];change(fid,begin(clean(m,fid,src),f'\tCALLFUNC KR_SaveViewAlt\n\tIFNZ style_alt_{fid}\n\tPUSH {value}\n\tRETURN\nstyle_alt_{fid}:\n'))
    fid=ids['KR_SaveSlot'];change(fid,begin(clean(m,fid,src),'''\tCALLFUNC KR_SaveViewAlt
\tIFNZ style_slot_alt
\t.LOCALREF page
\tPUSH 0
\tEQUALE
\t.LOCALREF row
\tPUSH 0
\tEQUALE
\tAND
\tIFZ style_slot_manual
\tPUSH 999
\tRETURN
style_slot_manual:
\t.LOCALREF page
\tPUSH 5
\tMUL
\t.LOCALREF row
\tADD
\tRETURN
style_slot_alt:
'''))
    fid=ids['KR_SaveRow'];change(fid,begin(clean(m,fid,src),'''\tCALLFUNC KR_SaveViewAlt
\tIFNZ style_row_alt
\t.LOCALREF slot
\tPUSH 999
\tEQUALE
\tIFZ style_row_manual
\tPUSH 0
\tRETURN
style_row_manual:
\t.LOCALREF slot
\tPUSH 5
\tMOD
\tRETURN
style_row_alt:
'''))
    fid=ids['KR_SavePaint'];change(fid,begin(clean(m,fid,src),'\tCALLFUNC KR_SaveViewAlt\n\tIFNZ style_paint_alt\n\tRETURN\nstyle_paint_alt:\n'))
    fid=29600;body=clean(m,fid,src);needle='\tS_PUSH "KR_SaveBackground"\n';assert body.count(needle)==2
    body=body.replace(needle,'\tPUSH 1\n\tCALLFUNC KR_SaveBaseName\n',1).replace(needle,'\tPUSH 0\n\tCALLFUNC KR_SaveBaseName\n',1);change(fid,body)
    for fid,name,helper in [(29571,'SceneSaveLoad','KR_SaveSceneAsset'),(29601,'SaveLoadCell','KR_SaveCellAsset')]:
        body=clean(m,fid,src);needle='\tS_PUSH '+json.dumps('Game\\Scenes\\8000SaveLoad\\'+name+'.pact')+'\n'
        body=once(body,needle,'\tCALLFUNC '+helper+'\n')
        if fid==29571:body=begin(body,'\tCALLFUNC KR_SaveStyleCapture\n')
        change(fid,body)
    relocated.extend(list(range(31683,31694))+[31695,31696,31697])
    change(29815,begin(clean(m,29815,src),'\tPUSHSTRUCTPAGE\n\tPUSH 29822\n\t.LOCALREF ActivityName\n\tA_REF\n\tS_PUSH "KR_SaveStyleButton"\n\tCALLMETHOD 2\n'))
    change(29823,begin(clean(m,29823,src),f'\tPUSHSTRUCTPAGE\n\tPUSH 29824\n\t.LOCALREF number\n\tS_PUSH "KR_SaveStyleButton"\n\tPUSH -1\n\tPUSH {added_ids["KR_SaveStyleMenu"]}\n\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 3\n'))
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    raw=bytearray(b.unpack(out.read_bytes()));oldraw=b.unpack(src.read_bytes());size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(b.pack(raw,src.read_bytes()[:8]))
    oldsize=struct.unpack_from('<I',oldraw,12)[0];assert raw[16:16+oldsize]==oldraw[16:16+oldsize]
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    assert len(nm['functions'])==len(m['functions'])+len(added)
    for f,g in zip(m['functions'],nm['functions']):
        expect=dict(f)
        if f['index'] in relocated:expect['address']=g['address']
        assert expect==g,f['index']
    for key in m:
        if key!='functions':assert m[key]==nm[key],key
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    ss=b.strings(oldraw)[2];assert b.strings(raw)[2][:len(ss)]==ss
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported'];save('native_opcode_audit.json',audit)
    layout=assets();save('layout.json',layout);shutil.copy2(S/'NightRemasterEX.ex',O/'NightRemasterEX.ex')
    vs=q.versions(S/'native_raw_code.jam');sig=collections.defaultdict(list)
    for f in m['functions']:sig[f['crc']&0xffffffff].append(f)
    before=p.snapshot_saves();frames=[];saves=[]
    for path in sorted(p.SAVE.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
        records=q.records(path);assert records is not None;saves.append(path.name)
        for rec in [records['ip']]+records['returns']:
            if rec['address']==-1:continue
            choices=[f for f in sig[rec['crc']] if rec['name'].startswith(b.raw_symbol(m,f['index'])+'(') and any(v['start']==rec['address']-rec['offset'] for v in vs[f['index']])]
            assert len(choices)==1;f=choices[0];assert f['index'] not in relocated
            ad=f['address']+rec['offset'];assert oldraw[16+ad:18+ad]==raw[16+ad:18+ad];frames.append(dict(save=path.name,fid=f['index'],offset=rec['offset']))
    assert before==p.snapshot_saves();save('save_frames.json',dict(saves=saves,frames=frames))
    save('build_evidence.json',dict(status='STAGED_NATIVE_PENDING',source_pointer=ptr,files={name:h(O/name) for name in ['NightRemaster.ain','NightRemasterPact.afa']},relocated=sorted(relocated),added_functions=added_ids,
        old_CODE_exact=True,serialized_schema_changes=0,MSG1_exact=True,STR0_prefix_exact=True,existing_resume_saves=len(saves),saved_return_frames=len(frames),
        translator_model=AUTHOR,default_mode='alternative',preference_file='YoruKR_OriginalSaveScreen.dat',preference_scope='Installation save folder; not a playthrough',
        weekly_daily_save_writers_unchanged=True,original_mode_slots='daily999 and manual1..49; weekly998 remains available in alternative mode'))
    print('BUILT',len(saves),'compatible saves;',len(frames),'saved frames')

if __name__=='__main__':main()
