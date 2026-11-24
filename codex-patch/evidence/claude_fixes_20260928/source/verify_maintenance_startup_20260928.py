from pathlib import Path
import subprocess,shutil,json,struct,os
R=Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908/staging/claude_fixes_20260928')
O=R/'evidence/startup_wrapper';O.mkdir(exist_ok=True)
case=O/'save';case.mkdir(exist_ok=True)
names=['NightRAFInfo.asd','NightRAFCGMode.asd','NightRAFMemMode.asd','NightRAFBGMMode.asd','NightRAFCommon.asd','NightRMsgSkip.msk','CommonGameData.asd']
shutil.copy2(R/'hook_build/unit_harness.exe',O/'unit_harness.exe')
(O/'AliceStart.ini').write_bytes(b'GameName = "Fixture"\r\nSaveFolder = "save"\r\n')
(O/'InstallInfo').mkdir(exist_ok=True)
(O/'InstallInfo/SaveFolderSetting.ini').write_bytes(b'SFSF'+struct.pack('<ii',0,2))
menu=O/'KRMenu';menu.mkdir(exist_ok=True)
original={n:(n*10).encode() for n in names}
for n,v in original.items():(case/n).write_bytes(v)
def unit():
    r=subprocess.run([str(O/'unit_harness.exe'),str(R/'candidate/winmm.dll'),'2364'],capture_output=True)
    assert r.returncode==0,(r.returncode,r.stderr)
    return r.stdout.decode()
(menu/'reset.req').write_text('reset');(case/'YoruKR_reset.marker').write_text('reset')
unit();assert all(not (case/n).exists() for n in names)
for n in names:(case/n).write_bytes(b'new')
(menu/'restore.req').write_text('restore');(case/'YoruKR_reset.marker').write_text('restore')
unit();assert {n:(case/n).read_bytes() for n in names}==original
# Interrupted reset with a missing KRMenu directory: the real startup wrapper
# still finds and rolls back the journal instead of bypassing recovery.
exe=R/'hook_build/maintenance_harness.exe';found=False
for step in range(1,100):
    r=subprocess.run([str(exe),'reset',str(case),str(menu),'0',str(step)],capture_output=True)
    if (case/'YoruKR_maintenance.pending').exists() and any(not (case/n).exists() for n in names):
        found=True;break
    subprocess.run([str(exe),'recover',str(case),str(menu)],capture_output=True,check=True)
assert found
assert menu.resolve().is_relative_to(O.resolve())
shutil.rmtree(menu)
unit();assert {n:(case/n).read_bytes() for n in names}==original
assert not (case/'YoruKR_maintenance.pending').exists()
(O/'result.json').write_text(json.dumps({'status':'PASS','production_dll_sha256':__import__('hashlib').sha256((R/'candidate/winmm.dll').read_bytes()).hexdigest(),'real_startup_reset_restore':True,'missing_menu_pending_recovered':True},indent=2),'utf8')
print('PASS production startup path, reset/restore, interrupted reset with KRMenu absent')
