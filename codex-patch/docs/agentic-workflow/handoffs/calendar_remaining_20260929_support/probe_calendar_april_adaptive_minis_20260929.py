"""Private muted native WI-008 fixture; never install or use live saves for writes."""
from pathlib import Path
import sys, shutil, json, inspect, datetime, re
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F))
import probe_chart_r24 as P
L=P.L;O=L.CODEX/'staging/calendar_april_adaptive_minis_20260929'
L.WORK=O/'work';L.EVID=O/'evidence';L.TMP=O/'work/tmp'
shutil.copy2(F/'work/savecopy_manifest.json',L.WORK/'savecopy_manifest.json')
P.O=O/'candidate';P.PROBE=O/'probe';P.RUN=P.PROBE/'run'
L.BASE_WINMM_SHA=L.sha(O/'source/winmm.dll');L.BASE_AIN_SHA='1a7bd3352132f123f2dd1cf8491b8faf16391b7361a57d6f76585843b4757542'
P.LIVE_WAITS=P.LIVE_WAITS+['KR_P29WaitRaw']
orig=P.setup_folder
def setup():
    assert P.RUN.resolve().is_relative_to(O.resolve())
    assert (P.RUN/'KRMenu').resolve().is_relative_to(O.resolve())
    return orig()
P.setup_folder=setup
P.PROBE_JAF+=(H/'probe_calendar_april_adaptive_minis_20260929.jaf').read_text('utf-8')
P.PROBE_JAF=P.PROBE_JAF.replace('        @@BOOT@@','        KR_A29Tour();\n        @@BOOT@@')
anchor='      KR_P22Block("DIALOG", ph, title + "\\nITEMS " + KR_P22Get("Items"));'
# The source has four-space JAF indentation.
anchor=anchor.lstrip()
addition='''
    if(ph=="april_stage") {
        string items=KR_P22Get("Items");
        KR_A29Ensure(items.Find("E00004")>=0 && items.Find("E00007")>=0,"picker E numbers retained");
        KR_A29Ensure(items.Find("감상 완료")>=0 && items.Find("아직 보지 않음")>=0,"picker mixed state");
        KR_A29Ensure(items.Find("△")<0 && items.Find("●")<0 && title.Find("단계")<0,"picker plain wording");
        KR_P22Shot("april_scene_picker");KR_P22SetPhase("april_continue");AFL_Parts_EndWaitForClick(0);return;
    }
'''
assert P.PROBE_JAF.count(anchor)==1
P.PROBE_JAF=P.PROBE_JAF.replace(anchor,anchor+addition)
source=inspect.getsource(P.build_probe)
anchor="    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')"
insert='''
    path=work/'original_global.jam'
    L.cmd('ain','dump','--function','KR_CGlobal','-o',path,src)
    a=m['functions'][L.fid_of(m,'KR_CGlobal')]
    b=dm['functions'][ids['KR_A29GlobalBase']]
    assert a['arguments']==b['arguments'] and a['variables']==b['variables'], (a,b)
    body=L.clean(path.read_text('utf8'),'KR_CGlobal')
    body=re.sub(r'^FUNC \\d+',f"FUNC {ids['KR_A29GlobalBase']}",body,flags=re.M).replace('ENDFUNC KR_CGlobal','ENDFUNC KR_A29GlobalBase')
    patch=[v for v in patch if 'ENDFUNC KR_A29GlobalBase' not in v]
    patch.append(body)
    for old,new in [('KR_CGlobal','KR_A29Global'),('KR_P29Read','KR_A29Read')]:
        patch.append(f"FUNC {L.fid_of(m,old)}\\n\\t.LOCALREF no\\n\\tCALLFUNC {new}\\n\\tRETURN\\nENDFUNC {old}\\n")
'''
assert source.count(anchor)==1
source=source.replace(anchor,anchor+'\n'+insert)
(O/'probe/build_probe_instrumentation.py').write_text(source,'utf-8')
P.__dict__['re']=re
exec(compile(source,'private_april_summary_probe','exec'),P.__dict__)
before=P.user_state();rt=P.setup_folder()
assert L.sha(rt/'NightRemaster.ain')==L.BASE_AIN_SHA
info=P.build_probe('title')
r=P.one_run('title',datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),timeout=180)
r['probe']=info;r['shots']=P.collect_shots('native_april');r['candidate_sha256']=L.sha(P.O/'NightRemaster.ain')
after=P.user_state();r['user_files_changed']=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
r['pass']=r.get('exit_code')==0 and 'END' in r['log'] and not any(k in r for k in ('vm_error','message','timeout')) and not r['user_files_changed']
L.writej(O/'evidence/native_april_probe.json',r)
print(json.dumps({k:v for k,v in r.items() if k not in ('events','probe')},ensure_ascii=False,indent=2))
assert r['pass']
