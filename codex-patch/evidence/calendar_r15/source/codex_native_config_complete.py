from pathlib import Path
import sys,struct,json,shutil
sys.dont_write_bytecode=True
D=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar');sys.path.insert(0,str(D));import r15lib as L
import probe_calendar_r15 as q
import publish_calendar_r15 as p
R=Path(__file__).resolve().parent;q.RUN=R/'native_config/run';E=R/'native_config/config_complete';E.mkdir(exist_ok=True)
assert not p.processes()
src=q.RUN/'NightRemaster.ain'
# Remove the unnecessary legacy callback redirects before disassembly (one crossed an instruction boundary).
raw=bytearray(L.unpack(src.read_bytes()));base=L.unpack((D/'candidate/NightRemaster.ain').read_bytes())
for v in L.versions(L.WORK/'build/candidate_raw_code.jam').get(29817,[]):
 a=16+v['start'];raw[a:a+6]=base[a:a+6]
src.write_bytes(L.pack(raw,src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',E/'before_meta.json',src);m=L.read_meta(E/'before_meta.json')
jaf='''void KR_CalReviewNoticeTick() {
    if(KR_CPGet("Stage")=="replay" && KR_T9Get("Req")!="" && KR_CPTitle()=="") {
        if(KR_CPNum("Frames")<12)return;
        KR_ClaudeProbeLog("RESERVATION NOTICE CONFIRMED (native simple/select dialog)");
        KR_CPEnd(0);
    }
}'''
(E/'notice.jaf').write_text(jaf,'utf8');decl=E/'declared.ain';L.cmd('ain','edit','--jaf',E/'notice.jaf','-o',decl,src)
L.cmd('ain','dump','--function','KR_CalReviewNoticeTick','-o',E/'helper.jam',decl)
fn='C_SelectDialog@_Update';L.cmd('ain','dump','--function',fn,'-o',E/'before_update.jam',decl)
patch=L.clean(L.native_lower((E/'helper.jam').read_text('utf8')),'KR_CalReviewNoticeTick')
patch+='\n'+L.begin(L.clean((E/'before_update.jam').read_text('utf8'),fn),'\tCALLFUNC KR_CalReviewNoticeTick\n')
(E/'patch.jam').write_text(patch,'utf8');out=E/'observed.ain';L.cmd('ain','edit','--jam',E/'patch.jam','-o',out,decl)
raw=bytearray(L.unpack(out.read_bytes()));sz=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+sz,m['functions'][0]['address'])
src.write_bytes(L.pack(raw,out.read_bytes()[:8]));pm=L.readj(q.RUN/'probe_manifest.json');pm['probe_sha256']=L.sha(src);L.writej(q.RUN/'probe_manifest.json',pm)
log=q.RUN/'claude_probe.txt'
if log.exists():shutil.copy2(log,E/'previous_notice_wait_log.txt');log.unlink()
before=p.snapshot_saves();res=q.launch(100);res['log']=L.decode(log.read_bytes()).splitlines() if log.exists() else []
res.update(candidate_sha256=pm['source_sha256'],probe_sha256=L.sha(src),user_save_folder_unchanged=before==p.snapshot_saves(),save_folder=pm['save_folder'])
from PIL import Image
for b in q.RUN.glob('cal_*.bmp'):Image.open(b).save(E/(b.stem+'.png'))
L.writej(E/'result.json',res);print(json.dumps(res,ensure_ascii=False,indent=2))
assert res.get('exit_code')==0 and res['log'][-1]=='END' and not res.get('events') and not res.get('vm_error') and not res.get('message'),res
assert any(x.startswith('CONFIG REQUEST STILL DEFERRED') for x in res['log']) and res['user_save_folder_unchanged']
print('CODEX_NATIVE_CONFIG_CALENDAR_REPLAY_PASS')
