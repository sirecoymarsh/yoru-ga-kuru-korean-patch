"""Claude Opus 5.5 (2026-09-24): isolated, muted native probe of the claude_term_rate candidate.

Builds a probe AIN (candidate + Codex audio mute + scripted-input guard + one same-length call swap in
InitializeStartup), runs it hidden in its own folder with its own SaveFolder, and captures the log.
The user's saves are only read (global record files are copied into the probe save folder).
The debugger capture follows trace_native_error_20260923.py (Codex) with this probe's paths.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib,json,os,re,shutil,struct,sys,time
import build_claude_term_rate_20260924 as e
import diagnostic_audio_20260923 as audio
b=e.b;p=e.p;q=e.q;a=e.a;O=e.O
ROOT=O/'native_probe';BOOT='NightRemasterClaudeProbe';SAVEDIR='SaveData_KR_ClaudeTermRate_20260924'
SAVES=p.SAVE.parent/SAVEDIR
COPY_GLOBAL=['NightRMsgSkip.msk','NightRAFCGMode.asd','NightRAFMemMode.asd','NightRAFBGMMode.asd','NightRAFCommon.asd','NightRAFInfo.asd',
             'CommonGameData.asd','CommonSystemData.sav','Volume.sav','AFConfig.asd','3DConfig.vsf','MouseCursorSetting.sav','ShowDPSetting.sav',
             'YoruKR_Terms.dat','YoruKR_Terms.backup']
PROBE_JAF=r'''
void KR_ClaudeProbeLog(string text) {
    string all=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Log")+text+"\n";
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Log",all);
    TextFile.WriteAll("claude_probe.txt",all);
}
string KR_ClaudeProbeTerms() {
    string s="";
    for(int i=0;i<8;i++) { if(i>0) s=s+","; s=s+KR_TermGet(i); }
    return s;
}
void KR_ClaudeProbe() {
    KR_DiagnosticMute();
    KR_TermLoad();
    KR_ClaudeProbeLog("LOADED "+KR_ClaudeProbeTerms()+" ACTIVE "+SystemService.SystemVariable_Get("YoruKR.Term.Active"));
    string main=KR_TermFile("YoruKR_Terms.dat");string backup=KR_TermFile("YoruKR_Terms.backup");string pending=KR_TermFile("YoruKR_Terms.pending");
    KR_ClaudeProbeLog("SAVE_FOLDER "+system.GetSaveFolderName());
    KR_ClaudeProbeLog("DUNGEON "+KR_TermDisplay("화군 라이코 동굴 최심층⑩")+" | "+KR_TermDisplay("수수께끼의 틈 1")+" | "+KR_TermDisplay("서양관 내부　틈 5"));
    KR_ClaudeProbeLog("SENSE "+KR_T8SenseFormat());
    KR_ClaudeProbeLog("BATTLE "+KR_T8BattleText("히카리를 모두 쓰러뜨렸다"));
    KR_ClaudeProbeLog("COMMENT "+KR_TermDisplay("용에게 효과적인 검이지만,\n히카리에게 얼마나 통할지는\n알 수 없습니다."));
    KR_ClaudeProbeLog("MOLD "+KR_TermDisplay("카샤의 영약"));
    KR_ClaudeProbeLog("MSG17397 "+KR_TermMessage(17397,"　호무라는 작년부터"));
    if(!KR_TermSave()) { KR_ClaudeProbeLog("FAIL save");system.Exit(22); }
    string disk="";TextFile.ReadAll(main,disk);
    if(disk.Find("YoruKR.Terms.3")!=0) { KR_ClaudeProbeLog("FAIL header v3");system.Exit(23); }
    string bak="";TextFile.ReadAll(backup,bak);
    if(bak.Find("YoruKR.Terms.2")==0) KR_ClaudeProbeLog("PASS v2 file upgraded to v3, v2 kept as backup");
    else KR_ClaudeProbeLog("NOTE backup header "+bak);
    string want="";
    for(int i=0;i<8;i++) { SystemService.SystemVariable_Set(KR_TermKey(i),KR_TermPreset(i,1)); if(i>0) want=want+","; want=want+KR_TermPreset(i,1); }
    KR_TermRefresh();
    if(!KR_TermSave()) { KR_ClaudeProbeLog("FAIL changed save");system.Exit(24); }
    for(int i=0;i<8;i++) SystemService.SystemVariable_Set(KR_TermKey(i),"");
    KR_TermLoad();
    if(KR_ClaudeProbeTerms()!=want) { KR_ClaudeProbeLog("FAIL readback "+KR_ClaudeProbeTerms());system.Exit(25); }
    KR_ClaudeProbeLog("PASS eight-term roundtrip "+want);
    KR_ClaudeProbeLog("DUNGEON2 "+KR_TermDisplay("화군 라이코 동굴 최심층⑩")+" | "+KR_TermDisplay("수수께끼의 틈 1"));
    string m1="";TextFile.ReadAll(main,m1);
    if(!FileOperation.CreateFolder(pending)) { KR_ClaudeProbeLog("FAIL rejection fixture");system.Exit(26); }
    SystemService.SystemVariable_Set(KR_TermKey(7),"불무리");
    bool denied=!KR_TermSave();FileOperation.DeleteFolder(pending);
    string m2="";TextFile.ReadAll(main,m2);
    if(!denied || m1!=m2) { KR_ClaudeProbeLog("FAIL rejected save changed main");system.Exit(27); }
    KR_ClaudeProbeLog("PASS rejected preference write preserves main");
    TextFile.WriteAll(main,"truncated\n");KR_TermLoad();
    KR_ClaudeProbeLog("AFTER_DAMAGE "+KR_ClaudeProbeTerms()+" VALIDMAIN "+SystemService.SystemVariable_Get("YoruKR.Term.ValidMain"));
    int t0=system.GetTime();int read=KR_T8ReadCount();int t1=system.GetTime();
    int cg=KR_T8CgCount();int t2=system.GetTime();int sc=KR_T8SceneCount();int t3=system.GetTime();
    string ed=KR_T8EndingText();int t4=system.GetTime();
    KR_ClaudeProbeLog("READ "+("%d"%read)+" MS "+("%d"%(t1-t0)));
    KR_ClaudeProbeLog("CG "+("%d"%cg)+" MS "+("%d"%(t2-t1)));
    KR_ClaudeProbeLog("SCENE "+("%d"%sc)+" MS "+("%d"%(t3-t2)));
    KR_ClaudeProbeLog("ENDING "+ed+" MS "+("%d"%(t4-t3)));
    KR_ClaudeProbeLog("END");
    system.Exit(0);
}
'''

def build_probe():
    ROOT.mkdir(exist_ok=True);src=O/'NightRemaster.ain';m=b.read_meta(O/'candidate_meta.json')
    jaf=audio.JAF+'\n'+PROBE_JAF
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('가'<=c<='힣' or c in '·…「」【】　⑩' for c in json.loads(z[0])) else z[0],jaf)
    (ROOT/'probe.jaf').write_text(jaf,'utf8');decl=ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    for f in added:
        path=ROOT/f"probe_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')),f['name']))
    (ROOT/'probe.jam').write_text('\n'.join(patch),'utf8');out=ROOT/'NightRemaster.ain';b.cmd('ain','edit','--jam',ROOT/'probe.jam','-o',out,decl)
    raw=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
    load=next(f['index'] for f in m['functions'] if f['name']=='KR_TermLoad');start=m['functions'][28133]['address']
    pat=struct.pack('<Hi',0x30,load);assert raw[16+start:16+start+6]==pat,raw[16+start:16+start+6].hex()
    struct.pack_into('<Hi',raw,16+start,0x30,ids['KR_ClaudeProbe'])
    out.write_bytes(b.pack(bytes(raw),src.read_bytes()[:8]))
    (ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(src),source_sha256=e.h(src),probe_sha256=e.h(out),audio=audio.POLICY,
        input='No input is scripted; C_UserInputManager::Is* return 0. The probe exits from InitializeStartup.',author=e.AUTHOR),indent=2),'utf8')
    return e.h(out)

def setup_folder():
    rt=Path(a.readj(O/'source_pointer.json')['runtime'])
    for n in ['NightRemaster.exe','winmm.dll','Version.txt','NightRemasterEX.ex']:shutil.copy2(rt/n,ROOT/n)
    if not (ROOT/'Data').exists():shutil.copytree(rt/'Data',ROOT/'Data')
    shutil.copy2(O/'NightRemasterPact.afa',ROOT/'NightRemasterPact.afa')
    for n in ['NightRemasterCG.afa','NightRemasterFont.fnl','NightRemasterSound.afa','NightRemasterVoice.afa']:
        for name in [n,n.replace('NightRemaster',BOOT,1)]:
            t=ROOT/name
            if not t.exists():os.link(rt/n,t)
            assert os.path.samefile(t,rt/n)
    for n in ['NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(ROOT/n,ROOT/n.replace('NightRemaster',BOOT,1))
    if not (ROOT/'Movie').exists():
        (ROOT/'Movie').mkdir()
        for f in (rt/'Movie').iterdir():os.link(f,ROOT/'Movie'/f.name)
    ini=(rt/'AliceStart.ini').read_bytes()
    ini=re.sub(rb'BootName\t= "NightRemaster"',('BootName\t= "'+BOOT+'"').encode(),ini)
    ini=re.sub(rb'SaveFolder\t= "[^"]*"',('SaveFolder\t= "'+SAVEDIR+'"').encode(),ini)
    assert BOOT.encode() in ini and SAVEDIR.encode() in ini;(ROOT/'AliceStart.ini').write_bytes(ini)
    SAVES.mkdir(exist_ok=True);assert SAVES.resolve()!=p.SAVE.resolve()
    for n in COPY_GLOBAL:
        if (p.SAVE/n).exists():shutil.copy2(p.SAVE/n,SAVES/n)
    for f in list(SAVES.glob('YoruKR_Terms.pending')):
        f.rmdir() if f.is_dir() else f.unlink()
    log=ROOT/'claude_probe.txt'
    if log.exists():log.unlink()

K=C.WinDLL('kernel32',use_last_error=True)
K.WaitForDebugEvent.argtypes=[C.c_void_p,W.DWORD];K.ContinueDebugEvent.argtypes=[W.DWORD,W.DWORD,W.DWORD]
K.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
K.WriteProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
K.VirtualProtectEx.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)]
K.OpenThread.argtypes=[W.DWORD,W.BOOL,W.DWORD];K.OpenThread.restype=W.HANDLE
K.Wow64GetThreadContext.argtypes=[W.HANDLE,C.c_void_p];K.CloseHandle.argtypes=[W.HANDLE];K.TerminateProcess.argtypes=[W.HANDLE,W.UINT]
class Context(C.Structure):
    _fields_=[(n,W.DWORD) for n in 'ContextFlags Dr0 Dr1 Dr2 Dr3 Dr6 Dr7'.split()]+[('FloatSave',C.c_byte*112)]+[(n,W.DWORD) for n in 'SegGs SegFs SegEs SegDs Edi Esi Ebx Edx Ecx Eax Ebp Eip SegCs EFlags Esp SegSs'.split()]+[('ExtendedRegisters',C.c_byte*512)]

def launch(timeout=150):
    import pefile,win32process
    policy=audio.require_silent_probe(ROOT);exe=ROOT/'NightRemaster.exe';data=exe.read_bytes()
    assert hashlib.sha256(data).hexdigest()=='7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
    pe=pefile.PE(data=data);imp=next(x.address for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name==b'MessageBoxA')
    needle=b'\xff\x15'+struct.pack('<I',imp);sites=[0x6696f0-0x400000];off=0
    while (off:=data.find(needle,off))>=0:sites.append(pe.get_rva_from_offset(off));off+=1
    startup=win32process.STARTUPINFO();startup.dwFlags=1;startup.wShowWindow=0
    hp,ht,pid,tid=win32process.CreateProcess(str(exe),None,None,None,False,2,None,str(ROOT),startup);handle=int(hp)
    result={'pid':pid,'audio':policy,'ain_sha256':e.h(ROOT/'NightRemaster.ain'),'events':[]}
    def read(addr,n):
        buf=C.create_string_buffer(n);got=C.c_size_t()
        if not K.ReadProcessMemory(handle,addr,buf,n,C.byref(got)):raise C.WinError(C.get_last_error())
        return buf.raw[:got.value]
    def cstr(addr):
        out=bytearray()
        for n in range(8192):
            v=read(addr+n,1)
            if v==b'\0':return bytes(out)
            out+=v
        return bytes(out)
    try:
        bp={};deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            event=C.create_string_buffer(200)
            if not K.WaitForDebugEvent(event,1000):continue
            raw=event.raw;code,epid,etid=struct.unpack_from('<III',raw);status=0x10002
            if code==3:
                base=struct.unpack_from('<Q',raw,40)[0]
                for rva in sites:
                    addr=base+rva;bp[addr]=read(addr,1);old=W.DWORD();num=C.c_size_t()
                    if not K.VirtualProtectEx(handle,addr,1,0x40,C.byref(old)):raise C.WinError(C.get_last_error())
                    if not K.WriteProcessMemory(handle,addr,b'\xcc',1,C.byref(num)):raise C.WinError(C.get_last_error())
                    tmp=W.DWORD();K.VirtualProtectEx(handle,addr,1,old.value,C.byref(tmp))
            elif code==1:
                exc=struct.unpack_from('<I',raw,16)[0];addr=struct.unpack_from('<Q',raw,32)[0]
                if exc in (0x80000003,0x4000001f) and addr in bp:
                    thread=K.OpenThread(0x58,False,etid)
                    try:
                        ctx=Context();ctx.ContextFlags=0x10007
                        if not K.Wow64GetThreadContext(thread,C.byref(ctx)):raise C.WinError(C.get_last_error())
                        if addr==base+0x6696f0-0x400000:
                            ret,op,msg=struct.unpack('<III',read(ctx.Esp,12));buf=read(msg,24);length,capacity=struct.unpack_from('<II',buf,16)
                            ptr=struct.unpack_from('<I',buf)[0] if capacity>=16 else msg
                            result['vm_error']={'command':cstr(op).decode('cp932','replace'),'message':read(ptr,min(length,8192)).decode('cp932','replace')}
                        else:
                            args=struct.unpack('<IIII',read(ctx.Esp,16));result['message']={'cp932':cstr(args[1]).decode('cp932','replace')}
                    finally:K.CloseHandle(thread)
                    K.TerminateProcess(handle,99);K.ContinueDebugEvent(epid,etid,status);break
                if exc not in (0x80000003,0x4000001f):result['events'].append({'exception':hex(exc),'address':hex(addr)});status=0x80010001
            elif code==5:
                result['exit_code']=struct.unpack_from('<I',raw,16)[0];K.ContinueDebugEvent(epid,etid,status);break
            K.ContinueDebugEvent(epid,etid,status)
        else:result['timeout']=True
    finally:K.TerminateProcess(handle,99)
    return result

def main():
    before=p.snapshot_saves()
    probe=build_probe();setup_folder();result=launch()
    log=(ROOT/'claude_probe.txt').read_bytes() if (ROOT/'claude_probe.txt').exists() else b''
    text=b.decode(log);result['log']=text.splitlines();result['probe_sha256']=probe;result['source_sha256']=e.h(O/'NightRemaster.ain')
    assert p.snapshot_saves()==before,'user save folder changed'
    result['user_saves_unchanged']=len(before)
    (O/'native_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({k:v for k,v in result.items()},ensure_ascii=False,indent=1))
if __name__=='__main__':main()
