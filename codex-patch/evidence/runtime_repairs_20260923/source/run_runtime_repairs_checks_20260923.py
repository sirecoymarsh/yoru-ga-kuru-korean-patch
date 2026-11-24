from pathlib import Path
import json,shutil,subprocess,sys
from PIL import Image
import build_runtime_repairs_20260923 as e
D=e.R/'staging/auto_explore_fix_20260923/real_scene_probe'; N=e.O/'native'
def save_case(name,kind):
    log=D/('click_probe.txt' if kind=='walk' else 'weapon_probe.txt')
    manifest=D/('click_probe_manifest.json' if kind=='walk' else 'weapon_probe_manifest.json')
    for source,suffix in [(log,'log.txt'),(manifest,'manifest.json'),(e.HERE/'native_error_capture_20260923.json','capture.json')]:shutil.copy2(source,N/(name+'_'+suffix))
    cap=json.loads((N/(name+'_capture.json')).read_text('utf8'));man=json.loads(manifest.read_text('utf8'))
    assert cap.get('exit_code')==0 and not cap['events'] and not cap.get('message') and not cap.get('vm_error'),cap
    assert cap['ain_sha256']==man['probe_sha256'] and man['source_sha256']==e.h(e.O/'NightRemaster.ain')
    text=log.read_bytes().decode('cp932',errors='replace');assert 'FAIL ' not in text,text
    print(name,text[-1800:],flush=True);return text
def run(name,kind,args):
    builder='build_walk_segment_probe_20260923.py' if kind=='walk' else 'build_weapon_cancel_probe_20260923.py'
    subprocess.run([sys.executable,str(e.HERE/builder),str(e.O/'NightRemaster.ain'),*args],check=True)
    subprocess.run([sys.executable,str(e.HERE/'trace_native_error_20260923.py'),'--long'],check=True)
    return save_case(name,kind)
def main():
    if '--others' in sys.argv:
        run('prefs_domain','weapon',['--prefs','--input-domain'])
        run('prefs_reload','weapon',['--prefs-reload'])
    if '--remaining' not in sys.argv:
        assert 'PASS preference reloaded in fresh native process' in save_case('prefs_reload','weapon')
        assert 'PASS native result Run/Clearup' in run('result','weapon',['--result'])
        log=run('weapon','weapon',[])
        for key in ['destroy_weapon_view','destroy_memory_view','RETURN weapon controller','END']:assert key in log,key
        for name in ['dialog_2','memory_before_cancel','returned_home']:
            Image.open(D/('weapon_probe_'+name+'.bmp')).save(N/('weapon_'+name+'.png'))
    if '--others' in sys.argv:
        assert 'STOPPED through second click' in run('walk_regression','walk',[])
    else:
        log=run('battle_walk','walk',['--battle'])
        assert 'PASS moved after native battle result' in log,log
if __name__=='__main__':main()
