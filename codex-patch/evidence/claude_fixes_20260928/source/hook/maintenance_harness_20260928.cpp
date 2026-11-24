#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cstring>
#include <cwchar>
#include <initializer_list>
#include <cstdlib>
#define KR_MAINT_TEST 1
#include "maintenance_transaction_20260928.h"
namespace krmaint {
int step=0,fail=0,crash=0;
bool TestStep(const char* label) {
    ++step;
    if(crash==step)ExitProcess(90);
    if(fail==step){SetLastError(ERROR_ACCESS_DENIED);return false;}
    // A held-denial simulates recovery blocked by persistent permissions.
    char deny[32]={};GetEnvironmentVariableA("KR_DENY",deny,sizeof(deny));
    if(deny[0]&&strcmp(deny,label)==0)return false;
    return true;
}
}
int wmain(int argc,wchar_t** argv) {
    if(argc<4)return 99;
    if(argc>4)krmaint::fail=_wtoi(argv[4]);
    if(argc>5)krmaint::crash=_wtoi(argv[5]);
    int result;
    if(wcscmp(argv[1],L"recover")==0)result=krmaint::Recover(argv[2],argv[3])?0:3;
    else result=static_cast<int>(krmaint::Run(argv[2],argv[3],wcscmp(argv[1],L"reset")==0));
    printf("{\"result\":%d,\"steps\":%d}\n",result,krmaint::step);
    return result;
}
