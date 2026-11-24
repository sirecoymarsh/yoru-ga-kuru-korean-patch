from pathlib import Path
import shutil, subprocess, json, hashlib
HERE=Path(__file__).resolve().parent
R=Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')
O=R/'staging/claude_fixes_20260928'; H=O/'hook'
for n in ['maintenance_transaction_20260928.h','maintenance_harness_20260928.cpp']: shutil.copy2(HERE/n,H/n)
p=H/'winmm_proxy.cpp'
s=(Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\hook_modmenu\src\winmm_proxy.cpp')).read_text('utf8')
s=s.replace('#include <cstring>','#include <cstring>\n#include <cwchar>\n#include <initializer_list>\n#include "maintenance_transaction_20260928.h"')
start=s.index('bool CopyVerified(');end=s.index('\nbool MenuIdInUse(',start)
s=s[:start]+'''// Codex internal: fail-closed, journalled seven-file maintenance.
void RunStartupMaintenance() {
    wchar_t dir[MAX_PATH]={},exe[MAX_PATH]={},save[MAX_PATH]={},reset[MAX_PATH]={},restore[MAX_PATH]={};
    // Recovery does not depend on recreating the request directory.
    if(!ExeDirectory(exe)||!JoinPath(dir,exe,L"KRMenu")||!JoinPath(reset,dir,L"reset.req")||!JoinPath(restore,dir,L"restore.req"))ExitProcess(ERROR_BAD_PATHNAME);
    if(!ResolveSaveFolder(save)) {
        if(FileExists(reset)||FileExists(restore))WriteResult("maintenance failed save folder unresolved\\r\\n");
        return;
    }
    bool safe=krmaint::Recover(save,dir);
    bool wantReset=FileExists(reset),wantRestore=FileExists(restore);
    if(safe&&(wantReset||wantRestore)) {
        if(wantReset==wantRestore||!MarkerSays(save,wantReset?"reset":"restore")) {
            safe=krmaint::Clear(save,dir);
            WriteResult("maintenance skipped invalid or conflicting request\\r\\n");
        } else {
            krmaint::Result r=krmaint::Run(save,dir,wantReset);
            safe=r!=krmaint::RecoveryRequired;
            if(r==krmaint::FailedUnchanged)safe=krmaint::Clear(save,dir);
            if(r==krmaint::Ok)WriteResult(wantReset?"reset ok verified transaction\\r\\n":"restore ok verified transaction\\r\\n");
            else WriteResult(wantReset?"reset failed changes rolled back\\r\\n":"restore failed changes rolled back or no verified backup\\r\\n");
        }
    }
    if(!safe) {
        WriteResult("maintenance failed recovery required; engine start blocked\\r\\n");
        MessageBoxW(nullptr,L"기록 파일 복구를 완료하지 못했습니다.\\n부분 상태로 게임을 시작하지 않습니다.\\n파일 사용 권한을 확인한 뒤 다시 실행해 주세요.\\n백업과 복구 기록은 보존되어 있습니다.",L"기록 복구",MB_OK|MB_ICONERROR);
        ExitProcess(ERROR_WRITE_FAULT);
    }
}
''' + s[end:]
# Old global allowlist is now owned by the tested transaction implementation.
a=s.index('const wchar_t* const kGlobalRecordFiles[]');b=s.index('LONG g_mod_menu_state',a)
s=s[:a]+s[b:]
p.write_text(s,'utf8')
out=O/'hook_build';out.mkdir(exist_ok=True)
cmd=H/'build_fixes.cmd'
cmd.write_text(r'''@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64
if errorlevel 1 exit /b 1
cd /d "%~dp0"
cl /nologo /std:c++17 /utf-8 /W4 /WX /O2 /GS- /GR- /MT /LD /DUNICODE /D_UNICODE /DIME_HOOK_DIAGNOSTICS=0 winmm_proxy.cpp /Fo"OUT\winmm.obj" /link /OUTPUT:"OUT\winmm.dll" /DEF:winmm_proxy.def user32.lib imm32.lib kernel32.lib shell32.lib ole32.lib uuid.lib
if errorlevel 1 exit /b 2
cl /nologo /std:c++17 /utf-8 /W4 /WX /O2 /EHsc /MT /DUNICODE /D_UNICODE unit_harness.cpp /Fo"OUT\unit.obj" /Fe"OUT\unit_harness.exe" user32.lib kernel32.lib
if errorlevel 1 exit /b 3
cl /nologo /std:c++17 /utf-8 /W4 /WX /O2 /EHsc /MT /DUNICODE /D_UNICODE maintenance_harness_20260928.cpp /Fo"OUT\maintenance.obj" /Fe"OUT\maintenance_harness.exe" user32.lib kernel32.lib
if errorlevel 1 exit /b 4
dumpbin /exports "OUT\winmm.dll" > "OUT\exports.txt"
dumpbin /imports "OUT\winmm.dll" > "OUT\imports.txt"
'''.replace('OUT',str(out)).replace('/'+str(out)+'PUT:', '/OUT:'),encoding='ascii')
r=subprocess.run(['cmd','/c',str(cmd)],capture_output=True)
(out/'build.log').write_bytes(r.stdout+r.stderr)
print((r.stdout+r.stderr).decode('utf8','replace'))
assert r.returncode==0,r.returncode
shutil.copy2(out/'winmm.dll',O/'candidate/winmm.dll')
print('DLL',hashlib.sha256((out/'winmm.dll').read_bytes()).hexdigest())

