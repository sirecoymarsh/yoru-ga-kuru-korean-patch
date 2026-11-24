"""Actual planner/state VM execution with bounded fake world; no game save/main."""
import json,re,struct,os,shutil
import build_auto_explore_20260923 as e
b=e.b;p=e.p;D=e.O/'native_probe'
STUBS={'KR_GetRoute':'Route','KR_WalkX':'X','KR_WalkY':'Y','KR_WalkOwn':'Own','KR_Poke':'Poke','KR_Flag':'Flag','KR_WalkValid':'Valid','KR_ExploreMap':'Map','KR_ExploreFloor':'Floor','KR_ExploreRemoved':'Removed','KR_ExploreStart':'Start','KR_ExploreStop':'Stop','KR_WalkCount':'Count','KR_ExploreGuidedPlan':'Guided','KR_ExploreRawVisible':'Visible','KR_ExploreCell':'CellRead','■選択ダイアログ／実行':'Dialog'}
def main():
 D.mkdir(exist_ok=True);ev=b.a.readj(e.O/'build_evidence.json');src=e.O/'NightRemaster.ain';assert b.a.sha(src)==ev['files']['NightRemaster.ain']
 bm=b.read_meta(e.O/'candidate_meta.json');ptr=ev['source_pointer'];rt=e.Path(ptr['runtime']);manifest=b.a.readj(e.Path(ptr['manifest']))
 shutil.copy2(e.HERE/'auto_explore_probe_20260923.jaf',D/'probe.jaf');decl=D/'declared.ain';b.cmd('ain','edit','--jaf',D/'probe.jaf','-o',decl,src)
 b.cmd('ain','dump','-j','-o',D/'declared_meta.json',decl);dm=b.read_meta(D/'declared_meta.json');added=dm['functions'][len(bm['functions']):];patch=[]
 for f in added:
  name=f['name'];path=D/f"{f['index']}.jam";b.cmd('ain','dump','--function',name,'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')),name))
 for f in bm['functions']:
  name=b.raw_symbol(bm,f['index']);body=None
  if name in STUBS:
   body=''.join('\tPUSHLOCALPAGE\n'+e.push(i)+'\tX_REF 1\n' for i in range(len(f['arguments'])))+e.cf('KR_EProbe'+STUBS[name])+'\tRETURN\n'
  if name in ['■選択ダイアログ／初期化','■選択ダイアログ／横項目数','■選択ダイアログ／選択肢追加']:body='\tRETURN\n'
  if body is not None:patch.append(f"FUNC {f['index']}\n"+body+f'ENDFUNC {b.symbol(bm,f["index"])}\n')
 (D/'probe.jam').write_text('\n'.join(patch),'utf8');out=D/'NightRemaster.ain';b.cmd('ain','edit','--jam',D/'probe.jam','-o',out,decl)
 raw=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,bm['functions'][0]['address'])
 for f in added:
  for v in f['arguments']+f['variables']:
   if v['name']=='route' and v['type'][0] in [79,80]:
    typ=v['type'][0];start=raw.index(f['name'].encode()+b'\0');off=raw.index(b'route\0\0',start)+7;assert struct.unpack_from('<7i',raw,off)==(typ,13,1,13,514,0,0);struct.pack_into('<7i',raw,off,typ,514,1,13,514,0,0)
 mainfid=next(f['index'] for f in added if f['name']=='KR_AutoExploreProbeMain_20260923');assert raw.count(b'MAIN')==1;struct.pack_into('<I',raw,raw.index(b'MAIN')+4,mainfid);out.write_bytes(b.pack(raw,src.read_bytes()[:8]))
 b.cmd('ain','dump','-j','-o',D/'candidate_meta.json',out);b.cmd('ain','dump','--raw-code','--no-macros','-o',D/'raw.jam',out);audit=b.audit(out,D/'candidate_meta.json',D/'raw.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported']
 for row in manifest['files']:
  rel=e.Path(row['path']);source=(rt/rel).resolve();dst=(D/rel).resolve();assert dst.is_relative_to(D.resolve());dst.parent.mkdir(parents=True,exist_ok=True)
  if rel.name=='NightRemaster.ain':continue
  if rel.name=='AliceStart.ini':
   data,n=re.subn(rb'SaveFolder\s*=\s*"[^"]*"',b'SaveFolder = "SaveData_KR_AutoExploreProbe_20260923"',source.read_bytes());assert n==1;dst.write_bytes(data)
  elif not dst.exists():os.link(source,dst)
  else:assert b.a.sha(source)==b.a.sha(dst)
 e.save('native_probe_manifest.json',dict(status='READY',path=str(D),candidate_sha256=b.a.sha(src),probe_sha256=b.a.sha(out),save_hashes=p.snapshot_saves(),stubs=STUBS,ordinary_game_main=False,claim='compiled planner and state transitions with fake world/dialog; not end-to-end gameplay'))
 print('PROBE_READY',D)
if __name__=='__main__':main()
