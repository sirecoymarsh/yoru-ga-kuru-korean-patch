"""Pinned auto-save rows on every page; compact native card geometry, no save schema changes."""
from pathlib import Path
import collections,json,re,shutil,struct
import build_save_page_restore_20260926 as base
from audit_dynamic_ui_20260915 import encode
b=base.b;p=base.p;q=base.q;a=base.a;n=base.n;R=base.R;HERE=Path(__file__).parent;AUTHOR='Codex internal'
O=R/'staging/pinned_autosave_20260926';S=O/'source'
h=base.h;clean=base.clean;textdump=base.textdump;wrapper=base.wrapper
EXPECTED='a7d680e7774e7e7ca438bd8b26f3e4b9698065215921342ff8843cc71c4a74b2'
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def pact():
    arc=n.read_afa3(S/'NightRemasterPact.afa');replacements={};changes=[]
    for index in [168,169]:
        entry=arc.entries[index]
        with (S/'NightRemasterPact.afa').open('rb') as f:f.seek(entry.absolute_offset);raw=f.read(entry.size)
        src=O/f'pact_{index}.pactex';src.write_bytes(raw);d=n.ex.decode_ex(src)
        if index==168:
            root=n.part(d,'矩形_000');state=n.txt_info(root)
            # Native rectangle controls hit testing independently from background drawing.
            for key in ['左下','右下']:
                v=n.val(state,key);x=struct.unpack('<f',v.items[0].value.payload.raw)[0];n.setlist(state,key,[x,70.0])
            n.setlist(n.part(d,'KR_SaveBackground'),'拡大縮小',[1.0,0.875])
            for key,x,y in [('Label',20,9),('Kind',16,44),('Headline',118,3),('Party',118,25),('Progress',584,25),('Stamp',118,48),('Detail',584,48)]:
                part=n.part(d,'KR_Save'+key);n.setlist(part,'座標',[x,y,81])
        else:
            # Original glow has margins around the row; shrink vertically to match the compact card.
            n.setlist(n.part(d,'ＣＧ_オンカーソル'),'拡大縮小',[1.0,0.875])
        out=O/f'new_pact_{index}.pactex';out.write_bytes(n.ex.encode_ex(d.header,d.serialize_payload()))
        after=n.ex.decode_ex(out);before=n.ex.decode_ex(src)
        assert n.ex.structure_signature(before)==n.ex.structure_signature(after)
        assert all(node.content==after.strings[path].content for path,node in before.strings.items())
        diffs=[dict(path=list(path),before=node.raw.hex(),after=after.scalars[path].raw.hex()) for path,node in before.scalars.items() if node.raw!=after.scalars[path].raw]
        assert len(diffs)==(10 if index==168 else 1),(index,len(diffs))
        changes.append(dict(index=index,scalars=diffs));replacements[index]=out
    result=n.rebuild(S/'NightRemasterPact.afa',O/'NightRemasterPact.afa',replacements)
    return dict(archive=result,changes=changes,card_height=70,pitch=72,autosave_positions=[0,72],manual_start_y=144)

def main():
    assert not O.exists(),'Do not overwrite frozen sources'
    ptr=p.read(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);assert h(rt/'NightRemaster.ain')==EXPECTED
    assert h(Path(ptr['manifest']))==ptr['manifest_sha256'];S.mkdir(parents=True)
    for name in ['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(rt/name,S/name)
    for name in ['candidate_meta.json','native_raw_code.jam']:shutil.copy2(base.O/name,S/name)
    save('source_pointer.json',ptr);m=b.read_meta(S/'candidate_meta.json');src=S/'NightRemaster.ain'
    ids={f['name']:f['index'] for f in m['functions']};patch=[];relocated=[]
    def change(name,ops):
        fid=ids[name];patch.append(wrapper(m,fid,ops));relocated.append(fid)
    change('KR_SaveRows','\t.LOCALREF page\n\tPUSH 0\n\tEQUALE\n\tIFZ pin_rows_seven\n\tPUSH 6\n\tRETURN\npin_rows_seven:\n\tPUSH 7\n')
    change('KR_SavePitch','\tPUSH 72\n')
    change('KR_SaveSlot','''\t.LOCALREF row
\tPUSH 0
\tEQUALE
\tIFZ pin_slot_weekly
\tPUSH 999
\tRETURN
pin_slot_weekly:
\t.LOCALREF row
\tPUSH 1
\tEQUALE
\tIFZ pin_slot_manual
\tPUSH 998
\tRETURN
pin_slot_manual:
\t.LOCALREF page
\tPUSH 0
\tEQUALE
\tIFZ pin_slot_later
\t.LOCALREF row
\tPUSH 1
\tSUB
\tRETURN
pin_slot_later:
\t.LOCALREF page
\tPUSH 5
\tMUL
\t.LOCALREF row
\tADD
\tPUSH 2
\tSUB
''')
    fid=ids['KR_SaveRow'];body=clean(m,fid,src)
    old='\t.LOCALREF slot\n\tPUSH 5\n\tMOD\n\tRETURN\n'
    new='\t.LOCALREF slot\n\tPUSH 5\n\tMOD\n\t.LOCALREF slot\n\tPUSH 5\n\tGTE\n\tIFZ pin_row_return\n\tPUSH 2\n\tADD\npin_row_return:\n\tRETURN\n'
    assert body.count(old)==1;patch.append(body.replace(old,new));relocated.append(fid)
    fid=ids['KR_ProgressPaint'];body=clean(m,fid,src)
    old='S_PUSH '+json.dumps(encode('자동 저장').decode('cp932'),ensure_ascii=False)
    new='S_PUSH '+json.dumps(encode('오토세이브').decode('cp932'),ensure_ascii=False)
    assert body.count(old)==2;patch.append(body.replace(old,new));relocated.append(fid)
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain'
    b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,src)
    raw=bytearray(b.unpack(out.read_bytes()));oldraw=b.unpack(src.read_bytes());size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(b.pack(raw,src.read_bytes()[:8]))
    oldsize=struct.unpack_from('<I',oldraw,12)[0];assert raw[16:16+oldsize]==oldraw[16:16+oldsize]
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    assert len(m['functions'])==len(nm['functions'])
    for f,g in zip(m['functions'],nm['functions']):
        expect=dict(f)
        if f['index'] in relocated:expect['address']=g['address']
        assert expect==g,f['index']
    for key in m:
        if key!='functions':assert m[key]==nm[key],key
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    os=b.strings(oldraw)[2];ns=b.strings(raw)[2];assert ns[:len(os)]==os and len(ns)-len(os)<=1
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported'];save('native_opcode_audit.json',audit)
    finish()

def finish():
    ptr=p.read(O/'source_pointer.json')
    assert ptr==p.read(R/'ui_cumulative/current.json'),'Live baseline changed'
    assert h(S/'NightRemaster.ain')==EXPECTED
    m=b.read_meta(S/'candidate_meta.json');out=O/'NightRemaster.ain'
    oldraw=b.unpack((S/'NightRemaster.ain').read_bytes());raw=b.unpack(out.read_bytes())
    nm=b.read_meta(O/'candidate_meta.json')
    relocated=[f['index'] for f,g in zip(m['functions'],nm['functions']) if f['address']!=g['address']]
    assert relocated==[32349,32350,32351,32352,32373],relocated
    layout=pact();save('layout.json',layout)
    shutil.copy2(S/'NightRemasterEX.ex',O/'NightRemasterEX.ex')
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
            ad=f['address']+rec['offset'];assert oldraw[16+ad:18+ad]==raw[16+ad:18+ad]
            frames.append(dict(save=path.name,fid=f['index'],offset=rec['offset']))
    assert before==p.snapshot_saves();save('save_frames.json',dict(saves=saves,frames=frames))
    save('build_evidence.json',dict(status='STAGED_NATIVE_PENDING',source_pointer=ptr,files={name:h(O/name) for name in ['NightRemaster.ain','NightRemasterPact.afa']},relocated=relocated,
        old_CODE_exact=True,serialized_schema_changes=0,MSG1_exact=True,STR0_prefix_exact=True,changed_PACT=[168,169],existing_resume_saves=len(saves),saved_return_frames=len(frames),
        translator_model=AUTHOR,last_page_init_unchanged=True,weekly_daily_save_writers_unchanged=True))
    print('BUILT',len(saves),'compatible saves;',len(frames),'saved frames')

if __name__=='__main__':
    import sys
    if '--finish' in sys.argv:finish()
    else:main()
