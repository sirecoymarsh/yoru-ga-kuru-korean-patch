"""One muted private native run: all shared labels, read/unread guards, both scene pickers."""
from pathlib import Path
import sys,json,shutil,inspect,re,datetime
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import probe_chart_r24 as P
L=P.L;O=L.CODEX/'staging/calendar_label_particles_20260929_r2'
L.WORK=O/'work';L.EVID=O/'evidence';L.TMP=O/'work/tmp'
shutil.copy2(F/'work/savecopy_manifest.json',L.WORK/'savecopy_manifest.json')
P.O=O/'candidate';P.PROBE=O/'probe';P.RUN=P.PROBE/'run'
L.BASE_WINMM_SHA=L.sha(O/'source/winmm.dll');L.BASE_AIN_SHA=L.sha(O/'source/NightRemaster.ain')
P.LIVE_WAITS+=['KR_P29WaitRaw']
data=L.readj(O/'design/label_patch.json');tables=L.readj(O/'design/expected_tables.json')
spec=[('ev_short','KR_T19EvShort','KR_N29ShortBase'),('ev_head','KR_T19EvHead','KR_N29HeadBase'),
      ('heads','KR_T19CardHead','KR_N29CardHeadBase'),('tails','KR_T19CardTail','KR_N29CardTailBase')]
q=lambda s:json.dumps(s,ensure_ascii=False)
jaf=['''
bool KR_NP29Read(int no) { return KR_CGet("ParticleRead")=="all"; }
void KR_NP29Ensure(bool ok,string note) {
    if(ok)return;
    KR_P22Log("FAIL "+note);KR_P22Shot("label_failed");system.Exit(29);
}
'''];calls=[];count=0
for key,new,old in spec:
    rows=list(tables[key].items())
    for offset in range(0,len(rows),80):
        fn=f'KR_NP29_{key}_{offset}';calls.append(fn+'();');body=['string prior="";string expected="";']
        for n,s in rows[offset:offset+80]:
            body+= [f'prior={old}({n});expected=prior;']
            if n in data['patch'][key]:
                row=data['patch'][key][n]
                body += [f'if(KR_CGet("ParticleRead")=="all") KR_NP29Ensure(prior=={q(row["before"])},{q("source "+key+" "+n)});',
                         f'if(prior=={q(row["before"])}) expected={q(row["after"])};']
            body += [f'KR_NP29Ensure({new}({n})==expected,{q(key+" "+n)});'];count+=1
        jaf.append(f'void {fn}() {{\n'+'\n'.join(body)+'\n}')
cards=L.readj(L.CODEX/'staging/calendar_april_summary_20260929/design/r15_tables.json')['cards']
k=next(c['k'] for c in cards if 25 in c['stages'])
jaf.append('''void KR_NP29Tour() {
    KR_CSet("Open","1");KR_CSet("Ctx","1");KR_CSet("All","1");
    for(int mode=0;mode<2;mode++) {
        if(mode==0)KR_CSet("ParticleRead","all");else KR_CSet("ParticleRead","none");
'''+'\n'.join(calls)+'''
    }
    KR_P22Log("PASS all label entries, preserved choices/actions and read/unread fallbacks");
    KR_CSet("ParticleRead","all");
    KR_CSet("Open","1");KR_CDraw(0,0);KR_CShow(false);
    KR_NP29Ensure(KR_CActive(),"real calendar root exists");
    KR_P22SetPhase("label_calendar");KR_T9StagePage(6,4);
    KR_NP29Ensure(KR_P22Phase()=="label_done","calendar picker cancel");
    KR_CSet("Open","");KR_P22SetPhase("label_achievement");KR_T9StagePage(6,4);
    KR_NP29Ensure(KR_P22Phase()=="label_done","achievement picker cancel");
    KR_P22SetPhase("label_other_names");KR_T9StagePage('''+str(k)+''',5);
    KR_NP29Ensure(KR_P22Phase()=="label_done","other names picker cancel");
    KR_CSet("Open","1");KR_CSet("ParticleRead","none");
    KR_P22SetPhase("label_unread");KR_T9StagePage(6,4);
    KR_NP29Ensure(KR_P22Phase()=="label_done","unread picker cancel");
    KR_CClear();KR_CSet("Open","");KR_CSet("ParticleRead","");KR_CSet("All","");
    KR_P22Shot("label_title_return");KR_P22Log("END");system.Exit(0);
}
''')
tour='\n'.join(jaf);(O/'probe/tour_readable.jaf').write_text(tour,'utf8')
P.PROBE_JAF+=tour;P.PROBE_JAF=P.PROBE_JAF.replace('        @@BOOT@@','        KR_NP29Tour();\n        @@BOOT@@')
anchor='KR_P22Block("DIALOG", ph, title + "\\nITEMS " + KR_P22Get("Items"));'
hook='''
    if(ph=="label_calendar" || ph=="label_achievement" || ph=="label_other_names" || ph=="label_unread") {
        string items=KR_P22Get("Items");
        KR_NP29Ensure(items.Find("이즈미와")<0 && items.Find("쿄카와")<0 && items.Find("호시카와와")<0,"no dangling name particles");
        if(ph=="label_unread") KR_NP29Ensure(items.Find("이즈미")<0 && items.Find("장면 1")>=0,"unread names hidden");
        else KR_NP29Ensure(items.Find("이즈미")>=0,"name retained");
        if(ph=="label_calendar")KR_NP29Ensure(items.Find("E00004")>=0 && items.Find("E00007")>=0 && items.Find("감상 완료")>=0,"IDs states preserved");
        KR_P22Shot(ph);KR_P22SetPhase("label_done");AFL_Parts_EndWaitForClick(0);return;
    }
'''
assert P.PROBE_JAF.count(anchor)==1;P.PROBE_JAF=P.PROBE_JAF.replace(anchor,anchor+hook)
source=inspect.getsource(P.build_probe);anchor="    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')"
insert='''
    patch.append(f"FUNC {L.fid_of(m,'KR_P29Read')}\\n\\t.LOCALREF no\\n\\tCALLFUNC KR_NP29Read\\n\\tRETURN\\nENDFUNC KR_P29Read\\n")
'''
assert source.count(anchor)==1;source=source.replace(anchor,anchor+'\n'+insert)
(O/'probe/build_probe_instrumentation.py').write_text(source,'utf8');exec(compile(source,'private_label_probe','exec'),P.__dict__)
before=P.user_state();rt=P.setup_folder();info=P.build_probe('title')
r=P.one_run('title',datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),timeout=180)
r['probe']=info;r['shots']=P.collect_shots('native_labels');r['candidate_sha256']=L.sha(P.O/'NightRemaster.ain')
r['checked_labels_per_read_mode']=count;r['checked_read_modes']=2
after=P.user_state();r['user_files_changed']=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
r['pass']=r.get('exit_code')==0 and 'END' in r['log'] and not any(line.startswith('FAIL') for line in r['log']) and not any(k in r for k in ('vm_error','message','timeout'))
L.writej(O/'evidence/native_labels_probe.json',r)
print(json.dumps({k:v for k,v in r.items() if k not in ('events','probe')},ensure_ascii=False,indent=2));assert r['pass']
