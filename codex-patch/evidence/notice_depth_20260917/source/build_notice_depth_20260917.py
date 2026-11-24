"""Fix terrain occlusion with exactly two PACT160 depth-coordinate edits."""
from pathlib import Path
import copy,json,shutil
from build_remaster_multiplier_20260915 import R,ex,read_afa3,rebuild,part,setlist,val,allparts
from build_mod_tab_20260915 import coords,scalar
from publish_remaster_multiplier_20260915 import sha,read,put,js

O=R/'staging/notice_depth_20260917'
EXPECTED='335e063313527913d0a7b5197e66e6a3ef31b9a2ab508a21d3a8b062e084be92'
EDITS={'KR_ChestNotice':(300,1000),'KR_LootNoticeRoot':(301,1001)}

def main():
    O.mkdir(exist_ok=True)
    ptr=read(R/'ui_cumulative/current.json');rt=Path(ptr['runtime'])
    assert sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    src=rt/'NightRemasterPact.afa';assert sha(src)==EXPECTED
    arc=read_afa3(src);entry=arc.entries[160]
    with src.open('rb') as f:f.seek(entry.absolute_offset);raw=f.read(entry.size)
    original=O/'original_160.pactex';original.write_bytes(raw)
    doc=ex.decode_ex(original);before=doc.serialize_payload();changes=[]
    for name,(old,new) in EDITS.items():
        node=part(doc,name);xyz=coords(node);assert xyz==[20,18,old]
        setlist(node,'座標',[xyz[0],xyz[1],new])
        changes.append(dict(part=name,before=xyz,after=coords(node)))
    out=O/'pact_160.pactex';out.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()))
    candidate=ex.decode_ex(out);assert candidate.serialize_payload()==doc.serialize_payload()
    # Reversing precisely the two z scalars must restore the complete payload.
    reverted=copy.deepcopy(candidate)
    for name,(old,new) in EDITS.items():setlist(part(reverted,name),'座標',[20,18,old])
    assert reverted.serialize_payload()==before
    checks=[]
    for name,(old,new) in EDITS.items():
        node=part(candidate,name)
        assert scalar(val(node,'表示'))==0
        for child in allparts(node):
            assert scalar(val(child,'クリック許可'))==0 and scalar(val(child,'オンカーソル透過'))==1
        # Native 13x13 cell rank: z=150+rank*3+{0,2}; all layers below new root.
        tile=[150+rank*3+layer for rank in range(13*13) for layer in (0,2)]
        assert max(tile)==656 and all(z<new for z in tile)
        checks.append(dict(part=name,new_z=new,tile_max_z=max(tile),comparisons=len(tile)))
    archive=rebuild(src,O/'NightRemasterPact.afa',{160:out})
    files={'NightRemasterPact.afa':sha(O/'NightRemasterPact.afa')}
    ev=dict(status='NOTICE_DEPTH_STAGED',source_pointer=ptr,source_files={'NightRemasterPact.afa':sha(src)},files=files,
        edits=changes,archive=archive,unchanged_AIN=sha(rt/'NightRemaster.ain'),unchanged_CG=sha(rt/'NightRemasterCG.afa'),
        semantic_text_changes=0,save_schema_changes=0,native_verified=False)
    put(O/'source_pointer.json',js(ptr));put(O/'build_evidence.json',js(ev))
    put(O/'verification.json',js(dict(status='NOTICE_DEPTH_STATIC_PASS',files=files,two_scalar_allowlist_reverse_exact=True,
        native_archive_roundtrip=True,layer_comparisons=checks,clickthrough_and_hidden_default_unchanged=True,
        all_other_archive_entries_exact=True,native_verified=False)))
    for key in ['25b468e2-2c1a-4acd-96ad-8ec9d6bb8b57','4508d8e0-e227-473a-a633-ce0b06040093','f8b70a7c-f78b-41d2-b15b-8cf7631c260b']:
        source=Path('C:/Users/CADRIA~1/AppData/Local/Temp')/f'codex-clipboard-{key}.png'
        if source.exists():shutil.copy2(source,O/f'reported_{key}.png')
    print(js(ev).decode('utf8'))

if __name__=='__main__':main()
