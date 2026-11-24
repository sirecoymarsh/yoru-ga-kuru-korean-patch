from pathlib import Path
import sys,struct,json,shutil
sys.dont_write_bytecode=True
D=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar');sys.path.insert(0,str(D));import r15lib as L
import probe_calendar_r15 as q
import publish_calendar_r15 as p
R=Path(__file__).resolve().parent;q.RUN=R/'native_config/run';E=R/'native_config/config_complete';E.mkdir(exist_ok=True)
assert not p.processes()
src=q.RUN/'NightRemaster.ain';L.cmd('ain','dump','-j','-o',E/'confirm_base_meta.json',src);m=L.read_meta(E/'confirm_base_meta.json')
text='''bool KR_CalReviewConfirmNotice() {
 if(KR_CPGet("Stage")=="replay" && KR_T9Get("Req")!="") {
  KR_ClaudeProbeLog("CONFIRM RESERVATION NOTICE by C_MessageDialog input polling");
  KR_ClaudeShot("cal_config_notice.bmp"); return true;
 }
 return KR_ExploreLevelEnter();
}'''
(E/'confirm.jaf').write_text(text,'utf8');decl=E/'confirm_decl.ain';L.cmd('ain','edit','--jaf',E/'confirm.jaf','-o',decl,src)
L.cmd('ain','dump','--function','KR_CalReviewConfirmNotice','-o',E/'confirm.jam',decl)
(E/'confirm.jam').write_text(L.clean(L.native_lower((E/'confirm.jam').read_text('utf8')),'KR_CalReviewConfirmNotice'),'utf8')
out=E/'confirmed.ain';L.cmd('ain','edit','--jam',E/'confirm.jam','-o',out,decl)
L.cmd('ain','dump','-j','-o',E/'confirmed_meta.json',out);cm=L.read_meta(E/'confirmed_meta.json')
raw=bytearray(L.unpack(out.read_bytes()));sz=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+sz,m['functions'][0]['address'])
old=L.fid_of(m,'KR_ExploreLevelEnter');new=L.fid_of(cm,'KR_CalReviewConfirmNotice');n=0
for v in L.versions(L.WORK/'build/candidate_raw_code.jam')[27776]:
 if v['start']!=m['functions'][27776]['address']:continue
 for at,op in v['ops']:
  if op==f'CALLFUNC 0x{old:x}':
   assert raw[16+at:16+at+6]==struct.pack('<Hi',0x30,old)
   struct.pack_into('<Hi',raw,16+at,0x30,new);n+=1
assert n==1
src.write_bytes(L.pack(raw,out.read_bytes()[:8]));pm=L.readj(q.RUN/'probe_manifest.json');pm['probe_sha256']=L.sha(src);L.writej(q.RUN/'probe_manifest.json',pm)
log=q.RUN/'claude_probe.txt'
if log.exists():shutil.copy2(log,E/'previous_input_disabled_log.txt');log.unlink()
before=p.snapshot_saves();res=q.launch(100);res['log']=L.decode(log.read_bytes()).splitlines() if log.exists() else []
res.update(candidate_sha256=pm['source_sha256'],probe_sha256=L.sha(src),user_save_folder_unchanged=before==p.snapshot_saves(),save_folder=pm['save_folder'])
from PIL import Image
for b in q.RUN.glob('cal_*.bmp'):Image.open(b).save(E/(b.stem+'.png'))
L.writej(E/'result.json',res);print(json.dumps(res,ensure_ascii=False,indent=2))
assert res.get('exit_code')==0 and res['log'][-1]=='END' and not res.get('events') and not res.get('vm_error') and not res.get('message'),res
assert any(x.startswith('CONFIG REQUEST STILL DEFERRED') for x in res['log']) and res['user_save_folder_unchanged']
print('CODEX_NATIVE_CONFIG_CALENDAR_REPLAY_PASS')
