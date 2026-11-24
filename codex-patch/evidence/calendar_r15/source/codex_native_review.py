"""Codex internal review: native settings -> Mods ClickEvent -> calendar -> deferred replay -> home.
Private muted copy only. The candidate and Fable evidence are not modified.
"""
from pathlib import Path
import sys, struct, json
sys.dont_write_bytecode=True
D=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar')
R=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import r15lib as L
import probe_calendar_r15 as q
import publish_calendar_r15 as p
assert not p.processes(), 'Do not overlap any player/diagnostic game'
q.PROBE=R/'native_config';q.PROBE.mkdir(exist_ok=True);q.RUN=q.PROBE/'run';L.EVID=q.PROBE/'evidence';L.EVID.mkdir(exist_ok=True)
s=q.PROBE_JAF
beg=s.index('        KR_CPSet("Person"')
end=s.index('        return;',beg)+len('        return;')
s=s[:beg]+'''        KR_CPSet("Stage", "config");
        KR_CPEnd(4);
        return;'''+s[end:]
needle='    if (stage == "charwin") {'
extra='''    if (stage == "playerinfo") {
        KR_ClaudeProbeLog("PLAYER INFO ctx="+KR_T9Get("Ctx"));
        KR_CPSet("Stage","charlist");KR_CPEnd(3);return;
    }
    if (stage == "charlist") {
        KR_ClaudeShot("cal_charlist.bmp");
        KR_CPSet("Stage","month");KR_CPSet("Month","%d"%KR_T9NowMonth());
        KR_CPEnd(1);return;
    }
    if(stage=="replay" && !home) {
        string cpTitle=KR_CPTitle(); if(cpTitle.Find("플레이 정보")==0) {
            KR_ClaudeProbeLog("CLOSE PLAYER INFO after calendar request");KR_CPEnd(0);return;
        }
    }
'''
assert s.count(needle)==1;s=s.replace(needle,extra+needle)
needle='int KR_CalProbeWait(FTPARTS_WaitForClickCallback func, bool cancel) {'
s=s.replace(needle,needle+'''
    if(KR_CPGet("Stage")=="replay" && KR_T9Get("Req")!="") {
        KR_ClaudeProbeLog("CONFIG RESERVATION NOTE Req="+KR_T9Get("Req"));
        KR_ClaudeShot("cal_config_notice.bmp");return 1;
    }
''')
s+='''
void KR_CalReviewConfigTick(ref C_ConfigView conf,string act) {
    if(KR_CPGet("Stage")!="config") return;
    if(KR_CPGet("ConfigAct")!=act) { KR_CPSet("ConfigAct",act); KR_ClaudeProbeLog("CONFIG ACT "+act+" ctx="+KR_T9Get("Ctx")); KR_ClaudeShot("cal_config_activity.bmp"); }
    if(!AFL_Activity_IsExistPartsByName(act,"KR_PlayerInfoButton")) return;
    int frames=KR_CPNum("ConfigFrames")+1;KR_CPSet("ConfigFrames","%d"%frames);
    if(frames<12)return;
    if(KR_T9Get("Ctx")!="C")system.Exit(81);
    KR_CPSet("Stage","playerinfo");KR_CPSet("Frames","0");
    KR_ClaudeProbeLog("NATIVE MODS CONFIG OPEN context=C");KR_ClaudeShot("cal_mods.bmp");
    conf.ClickEvent(AFL_Activity_GetPartsNumber(act,"KR_PlayerInfoButton"),0,0);
    if(KR_T9Get("Req")=="" || KR_T9Get("Play")!="")system.Exit(82);
    KR_ClaudeProbeLog("CONFIG REQUEST STILL DEFERRED req="+KR_T9Get("Req"));
    AFL_Activity_End();
}
'''
q.PROBE_JAF=s
orig=q.build_probe

def build(source,key,save,test,work,where=False):
    info=orig(source,key,save,test,work,where)
    # Diagnostic-only callback, reached by the real config activity update.
    m=L.read_meta(work/'probe_declared_meta.json')
    fn='C_ConfigView@EventConfAsraDataForParts'; fid=L.fid_of(m,fn)
    src=q.RUN/'NightRemaster.ain';old=work/'config_update.jam';L.cmd('ain','dump','--function',fn,'-o',old,src)
    patch=L.begin(L.clean(old.read_text('utf8'),fn),'\tPUSHSTRUCTPAGE\n\t.LOCALREF ActivityName\n\tCALLFUNC KR_CalReviewConfigTick\n')
    # Only choose initial Mods page; config begin/end and actual activity loop remain native.
    patch+='\nFUNC 29895\n\tPUSH 8\n\tCALLFUNC config::detail::OpenConfigWithStartPage\n\tRETURN\nENDFUNC Ｓ＿コンフィグ／標準\n'
    jam=work/'config_dispatch.jam';jam.write_text(patch,'utf8');out=work/'config_observed.ain'
    L.cmd('ain','edit','--jam',jam,'-o',out,src)
    raw=bytearray(L.unpack(out.read_bytes()));sz=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+sz,m['functions'][0]['address'])
    L.cmd('ain','dump','-j','-o',work/'final_meta.json',out);fm=L.read_meta(work/'final_meta.json')
    # Old serialized delegates may resume prior callback bodies; redirect only this diagnostic callback.
    for v in L.versions(L.WORK/'build/candidate_raw_code.jam').get(fid,[]):
        struct.pack_into('<HI',raw,16+v['start'],0x2c,fm['functions'][fid]['address'])
    src.write_bytes(L.pack(raw,out.read_bytes()[:8]))
    info['probe_sha256']=L.sha(src);return info
q.build_probe=build
launch_original=q.launch
q.launch=lambda timeout=180:launch_original(min(timeout,120))
sys.argv=['probe_review.py','NightR47.asd'];q.main()
res=L.readj(L.EVID/'probe_result.json')
assert res.get('exit_code')==0 and res['log'][-1]=='END' and not res['events'] and not res.get('vm_error') and not res.get('message'),res
assert any(x.startswith('CONFIG REQUEST STILL DEFERRED') for x in res['log'])
assert any(x.startswith('BACK TO HOME') for x in res['log'])
print('CODEX_NATIVE_CONFIG_CALENDAR_REPLAY_PASS')
