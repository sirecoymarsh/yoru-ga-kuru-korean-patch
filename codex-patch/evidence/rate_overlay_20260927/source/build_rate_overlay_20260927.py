"""Append-only, save-compatible achievement HUD extension over installed calendar r15."""
from pathlib import Path
import sys,shutil,struct,json,re
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
D=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar')
sys.path.insert(0,str(D))
import r15lib as l
import publish_calendar_r15 as p
R=l.CODEX;O=R/'staging/rate_overlay_20260927';S=O/'source'
EXPECTED='d81ddd5ad383ef870f96eca0c4da763a6cf475445d71f029ffb1f2c692037963'
FILES=['NightRemaster.ain','NightRemasterPact.afa']
def save(n,x):l.writej(O/n,x)
def dump(m,f,src):return l.clean(l.cmd('ain','dump','--function',l.symbol(m,f),src).stdout.decode('utf8'),l.symbol(m,f))
def main():
    O.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=True)
    ptr=l.readj(l.CURRENT);rt=Path(ptr['runtime'])
    assert l.sha(rt/'NightRemaster.ain')==EXPECTED
    assert l.sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    p.exact_tree(rt,l.readj(Path(ptr['manifest']))['files'])
    save('source_pointer.json',ptr);save('save_hashes_before.json',p.snapshot_saves())
    for n in FILES+['NightRemasterEX.ex']:shutil.copy2(rt/n,S/n)
    src=S/'NightRemaster.ain'
    l.cmd('ain','dump','-j','-o',S/'candidate_meta.json',src)
    l.cmd('ain','dump','--raw-code','--no-macros','-o',S/'candidate_raw_code.jam',src)
    m=l.read_meta(S/'candidate_meta.json');vs=l.versions(S/'candidate_raw_code.jam');fid=lambda name:l.fid_of(m,name)
    jaf=(HERE/'rate_overlay_20260927.jaf').read_text('utf8')
    (O/'helpers_readable.jaf').write_text(jaf,'utf8');(O/'helpers.jaf').write_text(l.jaf_literal_encode(jaf),'utf8')
    decl=O/'declared.ain';l.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
    l.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=l.read_meta(O/'declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[]
    for f in added:
        if f['name']=='KR_RateText':
            body=dump(m,fid('KR_T8HomeRateText'),src)
            body=re.sub(r'^FUNC \d+',f"FUNC {f['index']}",body,flags=re.M).replace('ENDFUNC KR_T8HomeRateText','ENDFUNC KR_RateText')
            old=json.dumps(l.encode('\n전체 이벤트　').decode('cp932'),ensure_ascii=False)
            new=json.dumps(l.encode('\n전체　　').decode('cp932'),ensure_ascii=False)
            assert body.count(old)==1;body=body.replace(old,new)
        else:body=l.native_lower(dump(dm,f['index'],decl))
        patch.append(body)
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain'
    l.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    base=l.unpack(src.read_bytes());raw=bytearray(l.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
    sites=[]
    def swap(owner,old,new):
        f=fid(owner);oldid=fid(old);hits=[ad for ad,op in l.live_version(m,vs,f)['ops'] if op==f'CALLFUNC 0x{oldid:x}']
        assert len(hits)==1,(owner,old,hits)
        ad=hits[0];before=struct.pack('<Hi',0x30,oldid);after=struct.pack('<Hi',0x30,ids[new])
        assert base[16+ad:22+ad]==raw[16+ad:22+ad]==before
        assert m['functions'][oldid]['return-type']==dm['functions'][ids[new]]['return-type']
        assert [x['type'] for x in m['functions'][oldid]['arguments']]==[x['type'] for x in dm['functions'][ids[new]]['arguments']]
        raw[16+ad:22+ad]=after;sites.append(dict(owner=owner,site=ad,before=before.hex(),after=after.hex(),original=old,replacement=new))
    swap('view::detail::View_Update','time::detail::PlayTime_Update','KR_RateViewUpdate')
    for owner in ['KR_T8HomeEnter','KR_T8HomeLeave']:swap(owner,'KR_T8HomeShow','KR_RateRender')
    swap('KR_T8EventEnd','LSys3xScript::ForceReleaseSkipAutpState','KR_RateEventReleased')
    loadid=fid('KR_ExploreAfterLoad')
    loadop=f'CALLFUNC 0x{loadid:x}'
    for f in m['functions']:
        live=[v for v in vs.get(f['index'],[]) if v['start']==f['address']]
        if not live:continue  # The source contains declaration-only/alias entries, not executable bodies.
        assert len(live)==1
        ops=live[0]['ops']
        if any(op==loadop for ad,op in ops):swap(l.raw_symbol(m,f['index']),'KR_ExploreAfterLoad','KR_RateAfterLoad')
    assert 4<len(sites)<10
    restored=bytearray(raw[16:16+struct.unpack_from('<I',base,12)[0]])
    for site in sites: restored[site['site']:site['site']+6]=bytes.fromhex(site['before'])
    assert restored==base[16:16+len(restored)]
    out.write_bytes(l.pack(raw,src.read_bytes()[:8]))
    l.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=l.read_meta(O/'candidate_meta.json')
    assert m['functions']==nm['functions'][:len(m['functions'])]
    for key in m:
        if key!='functions':assert m[key]==nm[key],key
    assert l.strings(base)[2]==l.strings(raw)[2][:len(l.strings(base)[2])]
    assert l.raw_messages(src.read_bytes())[3]==l.raw_messages(out.read_bytes())[3]
    l.cmd('ain','dump','--raw-code','--no-macros','-o',O/'candidate_raw_code.jam',out)
    audit=l.audit(out,O/'candidate_meta.json',O/'candidate_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported'];save('native_opcode_audit.json',audit)
    # Only the existing checkbox display label is edited. Every other archive member stays exact.
    import build_remaster_multiplier_20260915 as n
    import build_mod_tab_20260915 as mt
    arc=n.read_afa3(S/'NightRemasterPact.afa');entry=arc.entries[185]
    with (S/'NightRemasterPact.afa').open('rb') as f:f.seek(entry.absolute_offset);(S/'pact_185.pactex').write_bytes(f.read(entry.size))
    doc=n.ex.decode_ex(S/'pact_185.pactex');part=n.child(n.part(doc,'KR_HomeRateToggle'),'種類別情報')
    oldtext=l.decode(n.val(part,'テキスト').value);assert oldtext.strip()=='본거지에 달성률 표시'
    n.ss(part,'テキスト','    달성률 항상 표시',True)
    patched=O/'pact_185.pactex';patched.write_bytes(n.ex.encode_ex(doc.header,doc.serialize_payload()))
    n.ss(part,'テキスト',oldtext,True);assert doc.serialize_payload()==doc.raw_payload
    ar=n.rebuild(S/'NightRemasterPact.afa',O/'NightRemasterPact.afa',{185:patched})
    frames=[];saves=[]
    for path in sorted(l.SAVES.glob('NightR*.asd')):
        if not path.stem[6:].isdigit():continue
        records=l.save_records(path);assert records is not None;saves.append(path.name)
        frames.extend([dict(save=path.name,**x) for x in [records['ip']]+records['returns'] if x['address']!=-1])
    assert p.snapshot_saves()==l.readj(O/'save_hashes_before.json')
    save('save_frames.json',dict(saves=saves,frames=frames,all_existing_function_metadata_exact=True))
    save('build_evidence.json',dict(status='STAGED_NATIVE_PENDING',source_pointer=ptr,files={n:l.sha(O/n) for n in FILES},added_functions=ids,relocated=[],same_length_sites=sites,PACT=ar,MSG1_exact=True,STR0_prefix_exact=True,serialized_schema_changes=0,existing_resume_saves=len(saves),saved_return_frames=len(frames),translator_model='Codex internal',preference='Existing YoruKR_HomeRate.dat retained; no automatic preference change',refresh='Cached until load, event-end, toggle, or readiness change; lightweight visibility every 100 ms',scope='Gameplay sidebar; hidden in config/title; outside home read-only'))
    print('STAGED',O);print('hooks',sites)
if __name__=='__main__':main()
