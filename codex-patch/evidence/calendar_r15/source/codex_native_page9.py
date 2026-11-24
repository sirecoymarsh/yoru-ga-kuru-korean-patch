from pathlib import Path
import sys,struct,json,shutil
sys.dont_write_bytecode=True
D=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar');sys.path.insert(0,str(D));import r15lib as L
import probe_calendar_r15 as q
import publish_calendar_r15 as p
R=Path(__file__).resolve().parent;q.RUN=R/'native_config/run';E=R/'native_config/corrected_page9';E.mkdir(exist_ok=True)
assert not p.processes(),'Do not overlap player or diagnostic'
source=q.RUN/'NightRemaster.ain';raw=bytearray(L.unpack(source.read_bytes()))
m=L.read_meta(R/'native_config/build_20260927_021806/final_meta.json');at=16+m['functions'][29895]['address']
assert raw[at:at+6]==struct.pack('<Hi',0,8)
struct.pack_into('<i',raw,at+2,9);source.write_bytes(L.pack(raw,source.read_bytes()[:8]))
pm=L.readj(q.RUN/'probe_manifest.json');pm['probe_sha256']=L.sha(source);pm['initial_config_page']=9;L.writej(q.RUN/'probe_manifest.json',pm)
log=q.RUN/'claude_probe.txt'
if log.exists():shutil.copy2(log,E/'previous_page8_log.txt');log.unlink()
before=p.snapshot_saves();res=q.launch(180);res['log']=L.decode(log.read_bytes()).splitlines() if log.exists() else []
res.update(candidate_sha256=pm['source_sha256'],probe_sha256=L.sha(source),user_save_folder_unchanged=before==p.snapshot_saves(),save_folder=pm['save_folder'])
from PIL import Image
for b in q.RUN.glob('cal_*.bmp'):Image.open(b).save(E/(b.stem+'.png'))
L.writej(E/'result.json',res)
print(json.dumps(res,ensure_ascii=False,indent=2))
assert res.get('exit_code')==0 and res['log'][-1]=='END' and not res.get('events') and not res.get('vm_error') and not res.get('message'),res
assert any(x.startswith('CONFIG REQUEST STILL DEFERRED') for x in res['log'])
assert res['user_save_folder_unchanged']
print('CODEX_NATIVE_CONFIG_CALENDAR_REPLAY_PASS')
