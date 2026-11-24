from pathlib import Path
import sys,shutil,datetime,json
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import probe_calendar_tour_r24 as P
L=P.L;O=L.CODEX/'staging/claude_fixes_20260928'
L.WORK=O/'work';L.EVID=O/'evidence';L.TMP=O/'work/tmp'
P.O=O/'candidate';P.PROBE=O/'probe_cal';P.RUN=P.PROBE/'run'
old=L.readj(F/'증거/probe_result.json')
before=P.user_state()
P.setup_folder();shutil.copy2(P.O/'winmm.dll',P.RUN/'winmm.dll')
jaf='int KR_F28ProbeBool(bool v) { if (v) return 1; return 0; }\n'+P.PROBE_JAF
jaf=jaf.replace('void KR_CalProbeTick() {','''void KR_CalProbeTick() {
    if (_■関数実行中確認("KR_F28RejectReplay")) {
        KR_ClaudeProbeLog("FIX28 REJECTED " + KR_CPPhase());
        KR_ClaudeShot("replay_save_rejected.bmp");
        TextFile.WriteAll("fix28_reset_expected.txt","1");
        AFL_Parts_EndWaitForClick(1);
        return;
    }
''')
jaf=jaf.replace('int KR_ClaudeProbeMain() {','''int KR_ClaudeProbeMain() {
    if (KR_CPRead("fix28_reset_expected.txt") == "1") {
        KR_ClaudeProbeLog("FIX28 RESET REACHED; no replay state saved; END");
        system.Exit(0); return 0;
    }
''')
jaf=jaf.replace('if (n == 1) {','''if (n == 1) {
    string fname="blocked_snapshot";
    bool blocked=KR_F28SaveBlocked();
    bool a=KR_F28ExecSave(89,false);
    bool b=KR_F28ExecSave(89,true);
    bool c=KR_F28Snapshot(fname);
    KR_F28QuickSave();
    KR_ClaudeProbeLog("FIX28 BLOCKED="+("%d" % KR_F28ProbeBool(blocked))+" manual="+("%d" % KR_F28ProbeBool(a))+" auto="+("%d" % KR_F28ProbeBool(b))+" snapshot="+("%d" % KR_F28ProbeBool(c)));
    if(!blocked||a||b||c) system.Exit(28);
''')
P.PROBE_JAF=jaf
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
work=P.PROBE/('build_'+stamp);work.mkdir(parents=True)
save=old['save'];key=L.save_records(L.save_path(save))['key']
info=P.build_probe(P.O,key,work,'full',old['target'],old['name_pages'])
# New test file is isolated to this run, never a user file.
for p in [P.RUN/'fix28_reset_expected.txt']:
    if p.exists():p.unlink()
r=P.run_one(save,'full',info,stamp);r['shots']=P.collect_shots('full')
r['candidate_sha256']=L.sha(P.O/'NightRemaster.ain')
r['user_save_unchanged']=P.user_state()==before
L.writej(L.EVID/'replay_safety.json',r)
for s in r['log']:
    if s.startswith(('FIX28','BACK TO HOME','LOADING','STATE ','REPLAY','UNEXPECTED')):print(s)
print('exit',r.get('exit_code'),r.get('vm_error'),r.get('message'),r.get('seconds'))
assert r.get('exit_code')==0 and not r.get('vm_error') and not r.get('message'),r
assert any(s.startswith('FIX28 RESET REACHED') for s in r['log'])
assert r['user_save_unchanged']
blocks=P.blocks(r['log'])
comparison=P.compare_states(P.parse_state(blocks[('STATE','HOME')]),P.parse_state(blocks[('STATE','AFTER')]))
L.writej(L.EVID/'replay_state_comparison.json',comparison)
print('restoration',comparison)
