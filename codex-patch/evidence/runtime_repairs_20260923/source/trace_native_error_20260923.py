"""Capture native diagnostic errors before MessageBoxA, without UI automation.

Only launches the isolated real_scene_probe executable. Never attaches to games.
Uses documented Windows debugger events and WOW64 thread context.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib, json, struct, time, sys
from pathlib import Path
import pefile, win32process

ROOT = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\auto_explore_fix_20260923\real_scene_probe')
READABLE = '--readable' in sys.argv
EXE = ROOT / ('NightRemaster_error_ko.exe' if READABLE else 'NightRemaster.exe')
OUT = Path(__file__).with_name('native_error_readable_capture_20260923.json' if READABLE else 'native_error_capture_20260923.json')
K = C.WinDLL('kernel32', use_last_error=True)
K.WaitForDebugEvent.argtypes = [C.c_void_p, W.DWORD]
K.ContinueDebugEvent.argtypes = [W.DWORD, W.DWORD, W.DWORD]
K.ReadProcessMemory.argtypes = [W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
K.WriteProcessMemory.argtypes = [W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
K.VirtualProtectEx.argtypes = [W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)]
K.OpenThread.argtypes = [W.DWORD,W.BOOL,W.DWORD]; K.OpenThread.restype = W.HANDLE
K.Wow64GetThreadContext.argtypes = [W.HANDLE,C.c_void_p]
K.Wow64SetThreadContext.argtypes = [W.HANDLE,C.c_void_p]
K.CloseHandle.argtypes = [W.HANDLE]
K.TerminateProcess.argtypes = [W.HANDLE,W.UINT]

class Context(C.Structure):
    _fields_ = [(n,W.DWORD) for n in 'ContextFlags Dr0 Dr1 Dr2 Dr3 Dr6 Dr7'.split()] + [('FloatSave',C.c_byte*112)] + [(n,W.DWORD) for n in 'SegGs SegFs SegEs SegDs Edi Esi Ebx Edx Ecx Eax Ebp Eip SegCs EFlags Esp SegSs'.split()] + [('ExtendedRegisters',C.c_byte*512)]
assert C.sizeof(Context)==716

def main():
    from diagnostic_audio_20260923 import require_silent_probe
    audio_policy = require_silent_probe(ROOT)
    data=EXE.read_bytes()
    baseline=(ROOT/'NightRemaster.exe').read_bytes()
    assert hashlib.sha256(baseline).hexdigest()=='7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
    if READABLE:
        jp='ファイル名が登録されていない状態で機能が呼び出されました'.encode('cp932')
        ko='파일명이 등록되지 않은 상태에서 기능이 호출되었습니다.  '.encode('cp949')
        assert len(jp)==len(ko)==56 and baseline.count(jp)==1
        assert data==baseline.replace(jp,ko)
    else: assert data==baseline
    ini=(ROOT/'AliceStart.ini').read_bytes()
    assert b'SaveData_KR_RealSceneProbe_20260923' in ini
    pe=pefile.PE(data=data)
    imp=next(x.address for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name==b'MessageBoxA')
    needle=b'\xff\x15'+struct.pack('<I',imp)
    # Sys43VM uses its own dialog, not MessageBoxA. Capture before the dialog.
    sites=[0x6696f0-0x400000]; off=0
    while (off:=data.find(needle,off))>=0:
        sites.append(pe.get_rva_from_offset(off)); off+=1
    startup=win32process.STARTUPINFO(); startup.dwFlags=1; startup.wShowWindow=0
    hp,ht,pid,tid=win32process.CreateProcess(str(EXE),None,None,None,False,2,None,str(ROOT),startup)
    handle=int(hp)
    result={'pid':pid,'exe':str(EXE),'audio':audio_policy,'ain_sha256':hashlib.sha256((ROOT/'NightRemaster.ain').read_bytes()).hexdigest(),'events':[]}
    print('Diagnostic debugger PID',pid,flush=True)
    def read(addr,n):
        buf=C.create_string_buffer(n); got=C.c_size_t()
        if not K.ReadProcessMemory(handle,addr,buf,n,C.byref(got)): raise C.WinError(C.get_last_error())
        return buf.raw[:got.value]
    def cstr(addr):
        out=bytearray()
        for n in range(8192):
            v=read(addr+n,1)
            if v==b'\0': return bytes(out)
            out+=v
        raise ValueError('unterminated diagnostic text')
    try:
        bp={}; deadline=time.monotonic()+(120 if '--long' in sys.argv else 45)
        while time.monotonic()<deadline:
            event=C.create_string_buffer(200)
            if not K.WaitForDebugEvent(event,1000): continue
            b=event.raw; code,epid,etid=struct.unpack_from('<III',b); status=0x10002
            if code==3:
                base=struct.unpack_from('<Q',b,40)[0]; result['image_base']=hex(base)
                for rva in sites:
                    addr=base+rva; bp[addr]=read(addr,1); old=W.DWORD(); num=C.c_size_t()
                    if not K.VirtualProtectEx(handle,addr,1,0x40,C.byref(old)): raise C.WinError(C.get_last_error())
                    if not K.WriteProcessMemory(handle,addr,b'\xcc',1,C.byref(num)): raise C.WinError(C.get_last_error())
                    temp=W.DWORD(); K.VirtualProtectEx(handle,addr,1,old.value,C.byref(temp))
            elif code==1:
                exc=struct.unpack_from('<I',b,16)[0]; addr=struct.unpack_from('<Q',b,32)[0]
                if exc in (0x80000003,0x4000001f) and addr in bp:
                    thread=K.OpenThread(0x58,False,etid)
                    try:
                        ctx=Context(); ctx.ContextFlags=0x10007
                        if not K.Wow64GetThreadContext(thread,C.byref(ctx)): raise C.WinError(C.get_last_error())
                        if addr==base+0x6696f0-0x400000:
                            ret,op,msg=struct.unpack('<III',read(ctx.Esp,12))
                            buf=read(msg,24);length,capacity=struct.unpack_from('<II',buf,16)
                            ptr=struct.unpack_from('<I',buf)[0] if capacity>=16 else msg
                            raw=read(ptr,min(length,8192))
                            vm=ctx.Ecx;pc=struct.unpack('<I',read(vm+0x288,4))[0]
                            from build_runtime_repairs_20260923 import b as ain_tools
                            ain=ain_tools.unpack((ROOT/'NightRemaster.ain').read_bytes())
                            codebytes=ain[16:16+struct.unpack_from('<I',ain,12)[0]]
                            marker=read(pc-64,128);offset=codebytes.find(marker)
                            assert offset<0 or codebytes.count(marker)==1, 'ambiguous VM instruction address'
                            values,count=struct.unpack('<II',read(vm+0x2b0,8))
                            count=min(count,1000000);n=min(count,64)
                            result['vm_error']={'command':cstr(op).decode('cp932',errors='replace'),'message':raw.decode('cp932',errors='replace'),'native_return':hex(ret),'vm':hex(vm),'pc_offset':offset+64 if offset>=0 else None,'stack_size':count,'stack_tail':list(struct.unpack('<'+str(n)+'i',read(values+(count-n)*4,n*4))),'native_caller_locals':list(struct.unpack('<24i',read(ctx.Ebp-96,96))),'vm_fields':list(struct.unpack('<192I',read(vm,768)))}
                            K.TerminateProcess(handle,98);K.ContinueDebugEvent(epid,etid,status)
                            break
                        args=struct.unpack('<IIII',read(ctx.Esp,16)); raw=cstr(args[1]); title=cstr(args[2])
                        result['message']={'call':hex(addr),'args':list(args),'raw_hex':raw.hex(),'cp932':raw.decode('cp932',errors='replace'),'cp949':raw.decode('cp949',errors='replace'),'title_cp949':title.decode('cp949',errors='replace')}
                        result['stack_words']=[hex(x) for x in struct.unpack('<256I',read(ctx.Esp,1024))]
                        result['ebp_chain']=[]; frame=ctx.Ebp
                        for _ in range(20):
                            try:
                                prev,ret=struct.unpack('<II',read(frame,8)); result['ebp_chain'].append({'frame':hex(frame),'return':hex(ret)})
                                if prev<=frame or prev-frame>0x100000: break
                                frame=prev
                            except OSError: break
                        if READABLE:
                            assert raw.decode('cp949').strip()=='파일명이 등록되지 않은 상태에서 기능이 호출되었습니다.'
                            for site,original in bp.items():
                                old=W.DWORD(); num=C.c_size_t(); temp=W.DWORD()
                                K.VirtualProtectEx(handle,site,1,0x40,C.byref(old))
                                K.WriteProcessMemory(handle,site,original,1,C.byref(num))
                                K.VirtualProtectEx(handle,site,1,old.value,C.byref(temp))
                            ctx.Eip=addr
                            if not K.Wow64SetThreadContext(thread,C.byref(ctx)): raise C.WinError(C.get_last_error())
                    finally: K.CloseHandle(thread)
                    if READABLE:
                        result['native_dialog_resumed']=True
                        K.ContinueDebugEvent(epid,etid,status)
                        bp={}; deadline=time.monotonic()+12
                        continue
                    K.TerminateProcess(handle,99); K.ContinueDebugEvent(epid,etid,status)
                    break
                if exc not in (0x80000003,0x4000001f):
                    result['events'].append({'exception':hex(exc),'address':hex(addr)})
                    status=0x80010001
            elif code==8:
                ptr,unicode,n=struct.unpack_from('<QHH',b,16)
                try: result['events'].append({'debug':read(ptr,min(n*(2 if unicode else 1),8192)).decode('utf-16le' if unicode else 'cp932',errors='replace')})
                except OSError: pass
            elif code==5:
                result['exit_code']=struct.unpack_from('<I',b,16)[0]
                K.ContinueDebugEvent(epid,etid,status); break
            K.ContinueDebugEvent(epid,etid,status)
        else: result['timeout']=True
    finally:
        K.TerminateProcess(handle,99)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='stack_words'},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
