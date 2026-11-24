from pathlib import Path
import sys,json,struct,shutil
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
R=L.CODEX;O=R/'staging/claude_fixes_20260928';W=O/'work/build';W.mkdir(parents=True,exist_ok=True)
L.TMP=O/'work/tmp';L.TMP.mkdir(exist_ok=True)
src=O/'source/r24.ain';out=O/'candidate/NightRemaster.ain'
m=L.read_meta(O/'source/r24_candidate_meta.json');vs=L.versions(O/'source/r24_candidate_raw_code.jam')
ids0={L.raw_symbol(m,f['index']):f['index'] for f in m['functions']}
fid=lambda n:ids0[n]
jaf=(HERE/'claude_fixes_20260928.jaf').read_text('utf8')
(W/'helpers_readable.jaf').write_text(jaf,'utf8')
(W/'helpers.jaf').write_text(L.jaf_literal_encode(L.strip_comments(jaf)),'utf8')
decl=W/'declared.ain';L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
# The JAF front-end emits legacy ref types (20/80). This System4 build uses
# native boxed refs (82); use the exact callee ABI before expanding .LOCALREF.
def type_bytes(t):
    return struct.pack('<iii',*t[:3])+(type_bytes(t[3]) if t[3] is not None else b'')
dr=bytearray(L.unpack(decl.read_bytes()));codeend=16+struct.unpack_from('<I',dr,12)[0]
for new,oldname in [('KR_F28Snapshot','_system::detail::InputSnapshotFileName'),('KR_F28Loaded','gamesave::detail::セーブ実行_ロード後復帰処理')]:
    start=dr.index(new.encode()+b'\0',codeend)
    end=dr.index(dm['functions'][ids[new]+1]['name'].encode()+b'\0',start+1)-4
    block=bytes(dr[start:end])
    for a,b in zip(dm['functions'][ids[new]]['arguments'],m['functions'][fid(oldname)]['arguments']):
        needle=a['name'].encode()+b'\0\0'+type_bytes(a['type'])
        replacement=a['name'].encode()+b'\0\0'+type_bytes(b['type'])
        assert block.count(needle)==1,(new,a['name'])
        block=block.replace(needle,replacement);a['type']=b['type']
    dr[start:end]=block
native=W/'native_declared.ain';native.write_bytes(L.pack(bytes(dr),decl.read_bytes()[:8]))
decl=native
patch=[]
for f in added:
    n=f['name'];i=f['index']
    if n=='KR_F28ExecSave':
        body=f'''FUNC {i}
 CALLFUNC KR_F28SaveBlocked
 IFZ KR_F28ExecSave_normal
 PUSH 0
 RETURN
KR_F28ExecSave_normal:
 PUSHSTRUCTPAGE
 PUSH {fid('C_SceneSaveLoad@ExecSave')}
 .LOCALREF saveNo
 .LOCALREF isAuto
 CALLMETHOD 2
 RETURN
ENDFUNC {n}
'''
    else:
        p=W/(n+'.jam');L.cmd('ain','dump','--function',n,'-o',p,decl)
        body=L.clean(L.native_lower(p.read_text('utf8')).replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),n)
    patch.append(body)
# Only the unpinned no-argument failure sink is metadata-forwarded.
patch.append(f"FUNC {fid('KR_T18ClearPrev')}\n CALLFUNC KR_F28RejectReplay\n RETURN\nENDFUNC KR_T18ClearPrev\n")
(W/'patch.jam').write_text('\n'.join(patch),'utf8')
L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
old=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);sites=[]
def swap(owner,original,target,op='CALLFUNC',count=1):
    oi=fid(original);ni=ids[target]
    oldf=m['functions'][oi];newf=dm['functions'][ni]
    assert oldf['return-type']==newf['return-type'],(original,'return')
    assert [a['type'] for a in oldf['arguments']]==[a['type'] for a in newf['arguments']],(original,'signature')
    hits=[ad for ad,o in L.live_version(m,vs,fid(owner))['ops'] if o==f'{op} 0x{oi:x}']
    assert len(hits)==count,(owner,original,hits)
    for ad in hits:
        before=struct.pack('<Hi',0x30 if op=='CALLFUNC' else 0,oi);after=struct.pack('<Hi',0x30 if op=='CALLFUNC' else 0,ni)
        assert raw[16+ad:22+ad]==old[16+ad:22+ad]==before
        raw[16+ad:22+ad]=after
        sites.append(dict(owner=owner,site=ad,before=before.hex(),after=after.hex(),original=original,replacement=target))
swap('C_SysButton@IsAbleSave','Ａ＿回想モード実行中確認','KR_F28SaveBlocked')
for n in ['C_SceneSaveLoad@RunCommon','C_SceneSaveLoad@RunAutoSave']:
    swap(n,'C_SceneSaveLoad@ExecSave','KR_F28ExecSave','PUSH')
swap('message::detail::仮メッセージウィンドウ読込','Ｓ＿簡易セーブ','KR_F28QuickSave','PUSH')
swap('_system::detail::ProcessSystemMessage','_system::detail::InputSnapshotFileName','KR_F28Snapshot')
swap('gamesave::detail::セーブ実行','gamesave::detail::セーブ実行_ロード後復帰処理','KR_F28Loaded')
swap('KR_T18RestorePrepared','KR_T18ClearPrev','KR_F28ClearPrev')
swap('KR_CReplayRun','AFL_MemoryModeEvent_Begin','KR_F28MemoryBegin')
swap('KR_CReplayRun','AFL_MemoryModeEvent_End','KR_F28MemoryEnd')
swap('KR_C24Draw','KR_CDrawFrame','KR_F28ChartFrame')
oldn=struct.unpack_from('<I',old,12)[0];check=bytearray(raw[16:16+oldn])
for s in sites:check[s['site']:s['site']+6]=bytes.fromhex(s['before'])
assert check==old[16:16+oldn]
out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json')
changes=[i for i,(f,g) in enumerate(zip(m['functions'],nm['functions'])) if f!=g]
assert changes==[fid('KR_T18ClearPrev')],changes
for k in m:
    if k!='functions':assert m[k]==nm[k],k
assert L.strings(raw)[2][:len(L.strings(old)[2])]==L.strings(old)[2]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
for n in L.PINNED_ALL:
    i=fid(n);v=L.live_version(m,vs,i);end=v['ops'][-1][0]+6
    assert nm['functions'][i]==m['functions'][i] and raw[16+v['start']:16+end]==old[16+v['start']:16+end],n
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
rt=Path(L.readj(O/'source_pointer.json')['runtime'])
audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe')
assert audit['all_active_opcodes_supported'];L.writej(W/'native_opcode_audit.json',audit)
L.writej(O/'candidate/manifest.json',dict(status='STAGED_NATIVE_PENDING',files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ['NightRemaster.ain','winmm.dll']},base=L.sha(src),same_length_sites=sites,added_functions=ids,forwarded=['KR_T18ClearPrev'],pinned_exact=L.PINNED_ALL,new_globals=0,serialized_schema_changes=0,translator_model='Codex internal'))
print('BUILT',L.sha(out),len(ids),'helpers',len(sites),'sites')
