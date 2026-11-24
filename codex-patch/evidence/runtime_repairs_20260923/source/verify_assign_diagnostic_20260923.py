"""Negative/positive control for the diagnostic-only void-setter stack bug."""
import json, shutil, subprocess, sys
import build_runtime_repairs_20260923 as e
import run_runtime_repairs_checks_20260923 as checks

D=checks.D
N=e.O/'native'

def main():
    assert e.p.stopped(D)
    source=e.O/'NightRemaster.ain'
    before=e.h(source)
    for broken in [True,False]:
        flags=['--battle']+(['--unsafe-setter-control'] if broken else [])
        subprocess.run([sys.executable,str(e.HERE/'build_walk_segment_probe_20260923.py'),str(source),*flags],check=True)
        subprocess.run([sys.executable,str(e.HERE/'trace_native_error_20260923.py')],check=True)
        cap=json.loads((e.HERE/'native_error_capture_20260923.json').read_text('utf8'))
        name='assign_negative_control' if broken else 'assign_fixed_control'
        for path,suffix in [(e.HERE/'native_error_capture_20260923.json','capture.json'),(D/'click_probe_manifest.json','manifest.json'),(D/'click_probe.txt','log.txt'),(D/'click_probe.jam','probe.jam')]:
            shutil.copy2(path,N/(name+'_'+suffix))
        if broken:
            assert cap.get('vm_error',{}).get('command')=='Assign',cap
            assert cap['vm_error']['pc_offset']==0xa5b8b2,cap
            # The bad POP consumed index11. X_ASSIGN now mistakes a page id
            # for the index, independently of which page number was reused.
            assert cap['vm_error']['native_caller_locals'][7]!=11,cap
        else:
            log=checks.save_case('battle_walk','walk')
            assert 'PASS moved after native battle result' in log
    assert e.h(source)==before
    report={'status':'DIAGNOSTIC_ASSIGN_CAUSE_FIXED','candidate_sha256':before,'production_changed_for_this_bug':False,
            'cause':'Diagnostic KR_ClickBattleSetup called void setter26611 then POP without preserving a value. The shared operand stack lost pending assignment index11 in ExecMoveDungeon; after battle X_ASSIGN misread page id as index and older data as page.',
            'fix':'Remove POP; assert setter metadata return type is void. Also independently corrected diagnostic KR_ClickPart borrowed string argument using A_REF.',
            'negative_control':'Same candidate/scene/input with only POP reintroduced fails at Assign 0xa5b8b2 before popup.',
            'positive_control':'Same candidate/scene/input without POP closes native battle result, returns to dungeon, and moves beyond the encounter cell; exits0.',
            'audio':'Muted in both controls; original game settings and save files untouched.'}
    (N/'assign_root_cause.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print('PASS diagnostic-only Assign negative/positive controls',flush=True)

if __name__=='__main__':main()
