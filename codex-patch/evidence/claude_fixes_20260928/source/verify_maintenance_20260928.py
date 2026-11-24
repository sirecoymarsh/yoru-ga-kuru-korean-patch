from pathlib import Path
import subprocess, json, shutil, os, hashlib
R=Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908/staging/claude_fixes_20260928')
O=R/'evidence/maintenance';O.mkdir(parents=True,exist_ok=True)
EXE=R/'hook_build/maintenance_harness.exe'
names=['NightRAFInfo.asd','NightRAFCGMode.asd','NightRAFMemMode.asd','NightRAFBGMMode.asd','NightRAFCommon.asd','NightRMsgSkip.msk','CommonGameData.asd']
def wipe(p):
    assert p.resolve().is_relative_to(O.resolve()) and p.resolve()!=O.resolve()
    if p.exists():shutil.rmtree(p)
def state(p):return {n:(p/n).read_bytes() if (p/n).exists() else None for n in names}
def protected(p):return {n:(p/n).read_bytes() for n in ['NightR00.asd','NightR00.vsf','YoruKR_Terms.dat','NightRAFConfig.asd']}
def setup(p):
    p.mkdir(); (p/'KRMenu').mkdir()
    for i,n in enumerate(names):
        if i%3!=2:(p/n).write_bytes(bytes([i+1])*1031)
    for n in ['NightR00.asd','NightR00.vsf','YoruKR_Terms.dat','NightRAFConfig.asd']:(p/n).write_bytes(b'untouchable:'+n.encode())
def run(p,mode,fail=0,crash=0,deny=None):
    env=os.environ.copy()
    if deny:env['KR_DENY']=deny
    r=subprocess.run([str(EXE),mode,str(p),str(p/'KRMenu'),str(fail),str(crash)],capture_output=True,env=env)
    if r.returncode==90:return {'result':90}
    d=json.loads(r.stdout);assert d['result']==r.returncode,(r.returncode,r.stderr);return d
base=O/'base';wipe(base);setup(base);initial=state(base);guards=protected(base)
r=run(base,'reset');assert r['result']==0,r;reset_steps=r['steps']
assert state(base)==dict.fromkeys(names)
# A newer but partial legacy folder must not hide the valid reset.
bad=base/'Backup/KR_reset_99999999_999999';bad.mkdir();(bad/names[0]).write_bytes(b'partial')
# New records created after reset, including originally absent files.
for i,n in enumerate(names):(base/n).write_bytes(bytes([60+i])*2049)
before_restore=state(base)
for mode in ['reset','restore']:
    trial=O/'success';wipe(trial)
    if mode=='reset':setup(trial)
    else:shutil.copytree(base,trial)
    before=state(trial);result=run(trial,mode);assert result['result']==0,result
    after=state(trial);steps=result['steps']
    assert after==(dict.fromkeys(names) if mode=='reset' else initial)
    assert protected(trial)==guards
    outcomes={'unchanged':0,'rolled_back':0,'recovered':0,'committed':0}
    for kind in ['fail','crash']:
        for i in range(1,steps+1):
            case=O/'case';wipe(case)
            if mode=='reset':setup(case)
            else:shutil.copytree(base,case)
            old=state(case)
            r=run(case,mode,fail=i if kind=='fail' else 0,crash=i if kind=='crash' else 0)
            recovered=run(case,'recover');assert recovered['result']==0,(mode,kind,i,r,recovered)
            got=state(case)
            assert got in [old,after],(mode,kind,i,'mixed state',r)
            assert protected(case)==guards,(mode,kind,i,'protected files changed')
            assert not (case/'YoruKR_maintenance.pending').exists()
            assert run(case,'recover')['result']==0
            outcomes['committed' if got==after else 'recovered' if kind=='crash' else 'rolled_back' if r['result']==2 else 'unchanged']+=1
    print(mode,steps,outcomes,flush=True)
    (O/(mode+'.json')).write_text(json.dumps({'steps':steps,'single_failures':steps,'crash_boundaries':steps,'outcomes':outcomes},indent=2),'utf8')
# A persistent denial leaves the durable journal and blocks engine startup;
# once the external condition clears, a new process recovers the exact bytes.
case=O/'persistent';wipe(case);shutil.copytree(base,case)
old=state(case);r=run(case,'restore',deny='replace')
assert r['result'] in [2,3]
# Trigger a crash after the first destination change, by seeking an intermediate state.
found=False
for i in range(1,300):
    wipe(case);shutil.copytree(base,case)
    r=run(case,'restore',crash=i)
    if r['result']==90 and state(case) not in [old,initial]:
        blocked=run(case,'recover',deny='replace');assert blocked['result']==3
        assert (case/'YoruKR_maintenance.pending').exists()
        assert run(case,'recover')['result']==0 and state(case)==old
        found=True;break
assert found
# Tamper a full-sized file: SHA-256 rejects it, no live records changed.
case=O/'tamper';wipe(case);shutil.copytree(base,case)
valid=[p for p in (case/'Backup').iterdir() if (p/'committed.bin').exists()][0]
f=valid/names[0];f.write_bytes(b'X'*len(f.read_bytes()))
old=state(case);assert run(case,'restore')['result']==1 and state(case)==old
# Real Windows sharing violation, not just the injected errno.
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.restype=ctypes.c_void_p
k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
k.CloseHandle.argtypes=[ctypes.c_void_p]
case=O/'locked';wipe(case);setup(case)
handle=k.CreateFileW(str(case/names[0]),0x80000000,0,None,3,0,None)
assert handle not in [None,ctypes.c_void_p(-1).value]
try:
    old=state(case) if False else initial
    r=run(case,'reset');assert r['result']==1,r
finally:k.CloseHandle(handle)
assert state(case)==old
unit=subprocess.run([str(R/'hook_build/unit_harness.exe'),str(R/'candidate/winmm.dll'),'2364'],capture_output=True)
(O/'ime_harness.txt').write_bytes(unit.stdout+unit.stderr);assert unit.returncode==0,(unit.returncode,unit.stdout,unit.stderr)
(O/'summary.json').write_text(json.dumps({'status':'PASS','protected_files_unchanged':True,'persistent_denial_blocks':True,'restart_recovery_idempotent':True,'same_size_tamper_rejected':True,'partial_backup_skipped':True,'real_sharing_violation_unchanged':True,'ime_harness':True},indent=2),'utf8')
print('PASS all native transaction and IME checks')
