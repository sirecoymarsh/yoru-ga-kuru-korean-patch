// Codex internal. Shared by the production hook and the isolated native harness.
// Only the seven global record files are mutable. Snapshots include absences.
#include <bcrypt.h>
#include <cstdio>
#pragma comment(lib, "bcrypt.lib")
namespace krmaint {
static const wchar_t* const names[] = {L"NightRAFInfo.asd",L"NightRAFCGMode.asd",
    L"NightRAFMemMode.asd",L"NightRAFBGMMode.asd",L"NightRAFCommon.asd",
    L"NightRMsgSkip.msk",L"CommonGameData.asd"};
constexpr unsigned count=7;
struct Entry { DWORD present; unsigned char hash[32]; };
struct Manifest { DWORD magic; Entry entries[count]; };
constexpr DWORD magic=0x3354524b; // KRT3
// Test-only failure/crash injection is not exported by the DLL.
#ifdef KR_MAINT_TEST
bool TestStep(const char*);
bool Step(const char* s) { return TestStep(s); }
#else
bool Step(const char*) { return true; }
#endif
bool Path(wchar_t (&out)[MAX_PATH],const wchar_t* a,const wchar_t* b) {
    if(lstrlenW(a)+lstrlenW(b)+2>MAX_PATH)return false;
    lstrcpyW(out,a);lstrcatW(out,L"\\");lstrcatW(out,b);return true;
}
// A permissions failure is never mistaken for an absent file.
int Present(const wchar_t* p) {
    DWORD a=GetFileAttributesW(p);
    if(a!=INVALID_FILE_ATTRIBUTES)return (a&FILE_ATTRIBUTE_DIRECTORY)?-1:1;
    DWORD e=GetLastError();return (e==ERROR_FILE_NOT_FOUND||e==ERROR_PATH_NOT_FOUND)?0:-1;
}
bool Delete(const wchar_t* p) {
    if(!Step("delete"))return false;
    if(DeleteFileW(p))return true;
    DWORD e=GetLastError();return e==ERROR_FILE_NOT_FOUND||e==ERROR_PATH_NOT_FOUND;
}
bool Hash(const wchar_t* p,unsigned char (&out)[32]) {
    if(!Step("hash"))return false;
    HANDLE f=CreateFileW(p,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(f==INVALID_HANDLE_VALUE)return false;
    BCRYPT_ALG_HANDLE a=nullptr;BCRYPT_HASH_HANDLE h=nullptr;
    bool ok=BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0;
    if(ok)ok=BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0)>=0;
    BYTE b[8192];DWORD n=0;
    while(ok) {
        ok=ReadFile(f,b,sizeof(b),&n,nullptr)!=0;
        if(!ok||!n)break;
        ok=BCryptHashData(h,b,n,0)>=0;
    }
    if(ok)ok=BCryptFinishHash(h,out,32,0)>=0;
    if(h)BCryptDestroyHash(h);
    if(a)BCryptCloseAlgorithmProvider(a,0);
    CloseHandle(f);return ok;
}
bool Read(const wchar_t* p,void* b,DWORD n) {
    HANDLE f=CreateFileW(p,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(f==INVALID_HANDLE_VALUE)return false;
    LARGE_INTEGER len={};DWORD got=0;
    bool ok=GetFileSizeEx(f,&len)&&len.QuadPart==n&&ReadFile(f,b,n,&got,nullptr)&&got==n;
    CloseHandle(f);return ok;
}
bool Atomic(const wchar_t* p,const void* b,DWORD n) {
    wchar_t tmp[MAX_PATH]={};if(lstrlenW(p)+5>MAX_PATH)return false;
    lstrcpyW(tmp,p);lstrcatW(tmp,L".tmp");
    if(!Step("write"))return false;
    HANDLE f=CreateFileW(tmp,GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(f==INVALID_HANDLE_VALUE)return false;
    DWORD got=0;bool ok=WriteFile(f,b,n,&got,nullptr)&&got==n&&FlushFileBuffers(f);
    CloseHandle(f);
    if(ok)ok=Step("rename")&&MoveFileExW(tmp,p,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH);
    if(!ok)DeleteFileW(tmp);
    return ok;
}
bool Copy(const wchar_t* src,const wchar_t* dst,const unsigned char (&expected)[32]) {
    if(!Step("copy")||!CopyFileW(src,dst,TRUE))return false;
    // Flush before publishing the manifest/journal which depends on this copy.
    HANDLE f=CreateFileW(dst,GENERIC_WRITE,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    bool ok=f!=INVALID_HANDLE_VALUE;
    if(ok){ok=FlushFileBuffers(f)!=0;CloseHandle(f);}
    unsigned char hash[32]={};return ok&&Hash(dst,hash)&&memcmp(hash,expected,32)==0;
}
bool Check(const wchar_t* dir,const Manifest& m) {
    if(m.magic!=magic)return false;
    for(unsigned i=0;i<count;++i) {
        wchar_t p[MAX_PATH]={};if(!Path(p,dir,names[i]))return false;
        if(m.entries[i].present>1||Present(p)!=static_cast<int>(m.entries[i].present))return false;
        if(m.entries[i].present){unsigned char h[32]={};if(!Hash(p,h)||memcmp(h,m.entries[i].hash,32))return false;}
    }
    return true;
}
bool Load(const wchar_t* dir,const wchar_t* file,Manifest& m) {
    wchar_t p[MAX_PATH]={};return Path(p,dir,file)&&Read(p,&m,sizeof(m))&&Check(dir,m);
}
bool SaveManifest(const wchar_t* dir,const wchar_t* file,const Manifest& m) {
    wchar_t p[MAX_PATH]={};return Path(p,dir,file)&&Atomic(p,&m,sizeof(m));
}
bool Snapshot(const wchar_t* save,const wchar_t* dest,Manifest& m) {
    m={};m.magic=magic;
    for(unsigned i=0;i<count;++i) {
        wchar_t s[MAX_PATH]={},d[MAX_PATH]={};
        if(!Path(s,save,names[i])||!Path(d,dest,names[i]))return false;
        int present=Present(s);if(present<0)return false;
        m.entries[i].present=static_cast<DWORD>(present);
        if(present&&(!Hash(s,m.entries[i].hash)||!Copy(s,d,m.entries[i].hash)))return false;
    }
    return Check(save,m)&&Check(dest,m)&&SaveManifest(dest,L"snapshot.bin",m);
}
bool Mark(const wchar_t* dir,const wchar_t* file) {
    wchar_t p[MAX_PATH]={};return Path(p,dir,file)&&Atomic(p,&magic,sizeof(magic));
}
bool Marked(const wchar_t* dir,const wchar_t* file) {
    wchar_t p[MAX_PATH]={};DWORD m=0;return Path(p,dir,file)&&Read(p,&m,sizeof(m))&&m==magic;
}
bool Apply(const wchar_t* src,const wchar_t* save,const Manifest& m) {
    if(!Check(src,m))return false;
    for(unsigned i=0;i<count;++i) {
        wchar_t s[MAX_PATH]={},d[MAX_PATH]={},tmp[MAX_PATH]={};
        if(!Path(s,src,names[i])||!Path(d,save,names[i])||lstrlenW(d)+8>MAX_PATH)return false;
        lstrcpyW(tmp,d);lstrcatW(tmp,L".krnew");
        if(!Step("apply"))return false;
        if(m.entries[i].present) {
            unsigned char current[32]={};
            if(Present(d)==1&&Hash(d,current)&&memcmp(current,m.entries[i].hash,32)==0)continue;
            if(Present(tmp)!=0&&!Delete(tmp))return false;
            if(!Copy(s,tmp,m.entries[i].hash))return false;
            if(!Step("replace")||!MoveFileExW(tmp,d,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))return false;
        } else if(Present(d)!=0&&!Delete(d))return false;
    }
    return Check(save,m);
}
bool ValidName(const wchar_t* name) {
    // The journal may name only our own one-level Backup directory.
    if(wcsncmp(name,L"KR_reset_",9)!=0&&wcsncmp(name,L"KR_restore_",11)!=0)return false;
    for(const wchar_t* p=name;*p;++p)
        if(!((*p>=L'0'&&*p<=L'9')||(*p>=L'a'&&*p<=L'z')||*p==L'K'||*p==L'R'||*p==L'_'))return false;
    return true;
}
bool Clear(const wchar_t* save,const wchar_t* menu) {
    wchar_t p[MAX_PATH]={};
    for(const wchar_t* n:{L"reset.req",L"restore.req"})
        if(!Path(p,menu,n)||!Delete(p))return false;
    return Path(p,save,L"YoruKR_reset.marker")&&Delete(p);
}
// false means the engine MUST NOT start: recovery could not establish a
// complete state or its durable journal could not be retired.
bool Recover(const wchar_t* save,const wchar_t* menu) {
    wchar_t jp[MAX_PATH]={},name[96]={},root[MAX_PATH]={},dir[MAX_PATH]={};
    if(!Path(jp,save,L"YoruKR_maintenance.pending"))return false;
    int present=Present(jp);if(present==0)return true;if(present<0)return false;
    if(!Read(jp,name,sizeof(name))||name[95]!=0||!ValidName(name)||
       !Path(root,save,L"Backup")||!Path(dir,root,name))return false;
    if(!Marked(dir,L"committed.bin")) {
        Manifest before={};
        if(!Load(dir,L"snapshot.bin",before)||!Apply(dir,save,before)||!Mark(dir,L"aborted.bin"))return false;
    }
    return Clear(save,menu)&&Delete(jp);
}
bool Newest(const wchar_t* root,wchar_t (&out)[MAX_PATH],Manifest& m) {
    wchar_t pattern[MAX_PATH]={},best[MAX_PATH]={};
    if(!Path(pattern,root,L"KR_reset_*"))return false;
    WIN32_FIND_DATAW data={};HANDLE f=FindFirstFileW(pattern,&data);
    if(f==INVALID_HANDLE_VALUE)return false;
    do {
        wchar_t dir[MAX_PATH]={};Manifest test={};
        if((data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)&&!(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)&&
            ValidName(data.cFileName)&&lstrcmpW(data.cFileName,best)>0&&Path(dir,root,data.cFileName)&&
            Marked(dir,L"committed.bin")&&Load(dir,L"complete.bin",test)) {
            lstrcpyW(best,data.cFileName);m=test;
        }
    } while(FindNextFileW(f,&data));
    FindClose(f);return best[0]&&Path(out,root,best);
}
// Legacy folders lack a commit record and cannot be proven complete. They are
// retained, never selected automatically; manual recovery remains possible.
enum Result { Ok, FailedUnchanged, FailedRolledBack, RecoveryRequired };
Result Run(const wchar_t* save,const wchar_t* menu,bool reset) {
    if(!Recover(save,menu))return RecoveryRequired;
    wchar_t root[MAX_PATH]={},name[96]={},dir[MAX_PATH]={},target[MAX_PATH]={},source[MAX_PATH]={},jp[MAX_PATH]={};
    Manifest wanted={},before={};wanted.magic=magic;
    if(!Path(root,save,L"Backup")||(!CreateDirectoryW(root,nullptr)&&GetLastError()!=ERROR_ALREADY_EXISTS))return FailedUnchanged;
    if(!reset&&!Newest(root,source,wanted))return FailedUnchanged;
    SYSTEMTIME t={};GetSystemTime(&t);
    // CREATE_NEW directory, never reuse a same-second previous transaction.
    wsprintfW(name,L"KR_%s_%04u%02u%02u_%02u%02u%02u_%03u_%lu",reset?L"reset":L"restore",
        t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds,GetCurrentProcessId());
    if(!Path(dir,root,name)||!CreateDirectoryW(dir,nullptr)||!Path(target,dir,L"target")||
       !CreateDirectoryW(target,nullptr)||!Snapshot(save,dir,before))return FailedUnchanged;
    if(!reset) {
        for(unsigned i=0;i<count;++i)if(wanted.entries[i].present) {
            wchar_t s[MAX_PATH]={},d[MAX_PATH]={};
            if(!Path(s,source,names[i])||!Path(d,target,names[i])||!Copy(s,d,wanted.entries[i].hash))return FailedUnchanged;
        }
    }
    if(!Check(target,wanted)||!SaveManifest(target,L"snapshot.bin",wanted)||!Check(save,before)||
       !Path(jp,save,L"YoruKR_maintenance.pending")||!Atomic(jp,name,sizeof(name)))return FailedUnchanged;
    bool ok=Apply(target,save,wanted);
    if(ok&&reset)ok=SaveManifest(dir,L"complete.bin",before);
    if(ok)ok=Mark(dir,L"committed.bin");
    if(!ok) {
        if(!Apply(dir,save,before)||!Mark(dir,L"aborted.bin"))return RecoveryRequired;
        if(!Clear(save,menu)||!Delete(jp))return RecoveryRequired;
        return FailedRolledBack;
    }
    if(!Clear(save,menu)||!Delete(jp))return RecoveryRequired;
    return Ok;
}
} // namespace krmaint
