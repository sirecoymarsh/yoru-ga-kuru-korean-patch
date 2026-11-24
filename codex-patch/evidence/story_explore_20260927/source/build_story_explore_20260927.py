"""Append-only story/rest continuation; no save schema, scenario or reward edits."""
from pathlib import Path
import sys,shutil,struct,json
sys.dont_write_bytecode=True
import build_rate_overlay_20260927 as old
l=old.l;p=old.p;R=l.CODEX;HERE=Path(__file__).resolve().parent
O=R/'staging/story_explore_20260927';S=O/'source';FILES=['NightRemaster.ain']
EXPECTED='3a1567fc0c002275885585e0f181eef657fea4ebaad0b7358bdf6254e4449b25'
dump=old.dump
def main():
    O.mkdir(parents=True,exist_ok=True);S.mkdir(exist_ok=True)
    ptr=l.readj(l.CURRENT);rt=Path(ptr['runtime']);assert l.sha(rt/FILES[0])==EXPECTED
    p.exact_tree(rt,l.readj(Path(ptr['manifest']))['files'])
    l.writej(O/'source_pointer.json',ptr)
    for n in FILES+['NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(rt/n,S/n)
    src=S/FILES[0]
    l.cmd('ain','dump','-j','-o',S/'candidate_meta.json',src)
    l.cmd('ain','dump','--raw-code','--no-macros','-o',S/'candidate_raw_code.jam',src)
    m=l.read_meta(S/'candidate_meta.json');vs=l.versions(S/'candidate_raw_code.jam');fid=lambda name:l.fid_of(m,name)
    jaf=(HERE/'story_explore_20260927.jaf').read_text('utf8');(O/'helpers.jaf').write_text(jaf,'utf8')
    decl=O/'declared.ain';l.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
    l.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=l.read_meta(O/'declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
    patches=[l.native_lower(dump(dm,f['index'],decl)) for f in added]
    (O/'patch.jam').write_text('\n'.join(patches),'utf8');out=O/FILES[0]
    l.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    base=l.unpack(src.read_bytes());raw=bytearray(l.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);sites=[]
    def swap(owner,original,target,count=1):
        oldid=fid(original);newid=ids[target]
        ops=l.live_version(m,vs,fid(owner))['ops'];hits=[ad for ad,op in ops if op==f'CALLFUNC 0x{oldid:x}']
        assert len(hits)==count,(owner,original,hits)
        assert m['functions'][oldid]['return-type']==dm['functions'][newid]['return-type']
        assert [v['type'] for v in m['functions'][oldid]['arguments']]==[v['type'] for v in dm['functions'][newid]['arguments']]
        for ad in hits:
            before=struct.pack('<Hi',0x30,oldid);after=struct.pack('<Hi',0x30,newid)
            assert base[16+ad:22+ad]==raw[16+ad:22+ad]==before;raw[16+ad:22+ad]=after
            sites.append(dict(owner=owner,site=ad,before=before.hex(),after=after.hex(),original=original,replacement=target))
    swap('KR_WalkCellGate','KR_ExploreGate','KR_StoryGate')
    swap('KR_WalkGuard','KR_ExploreGuard','KR_StoryGuard')
    swap('KR_WalkVisible','KR_ExploreVisibleBound','KR_StoryVisible')
    swap('KR_T8EventStart','LSys3xScript::ForceRestoreSkipAutpState','KR_StoryRestoreAuto')
    swap('C_SceneDungeon@AfterStepOnInEventDungeon','AFL_Parts_EndWaitForClick','KR_StoryTransition',3)
    swap('C_SceneDungeon@SteppedOnEnemy','KR_ExploreBattleEnter','KR_StoryBattleEnter')
    for name in ['KR_ExploreTimedEnter','KR_ExploreLevelDialog']:swap(name,'KR_ExploreGet','KR_StoryResultPending')
    swap('C_SceneDungeonView@Hide','KR_WalkPause','KR_StoryPause')
    for name in ['KR_ExploreAfterLoad','KR_ExploreTripBegin']:swap(name,'KR_ExploreClear','KR_StoryResetTrip')
    oldsize=struct.unpack_from('<I',base,12)[0];check=bytearray(raw[16:16+oldsize])
    for s in sites:check[s['site']:s['site']+6]=bytes.fromhex(s['before'])
    assert check==base[16:16+oldsize]
    out.write_bytes(l.pack(raw,src.read_bytes()[:8]))
    l.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=l.read_meta(O/'candidate_meta.json')
    assert m['functions']==nm['functions'][:len(m['functions'])]
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    assert l.strings(base)[2]==l.strings(raw)[2][:len(l.strings(base)[2])]
    assert l.raw_messages(src.read_bytes())[3]==l.raw_messages(out.read_bytes())[3]
    l.cmd('ain','dump','--raw-code','--no-macros','-o',O/'candidate_raw_code.jam',out)
    audit=l.audit(out,O/'candidate_meta.json',O/'candidate_raw_code.jam',rt/'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'];l.writej(O/'native_opcode_audit.json',audit)
    l.writej(O/'build_evidence.json',dict(status='STAGED_NATIVE_PENDING',source_pointer=ptr,files={n:l.sha(O/n) for n in FILES},added_functions=ids,relocated=[],same_length_sites=sites,serialized_schema_changes=0,MSG1_exact=True,STR0_prefix_exact=True,translator_model='Codex internal'))
    print('BUILT',l.sha(out),'hooks',len(sites))
if __name__=='__main__':main()
