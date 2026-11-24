#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <mmsystem.h>

#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cwchar>

#include "hangul_proxy_table.generated.h"

using TimeGetDevCapsFn = MMRESULT(WINAPI*)(LPTIMECAPS, UINT);
using TimeGetTimeFn = DWORD(WINAPI*)();
using TimePeriodFn = MMRESULT(WINAPI*)(UINT);

bool HasExactlyRequiredExports(HMODULE module) {
    const auto* base = reinterpret_cast<const unsigned char*>(module);
    const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(base);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) {
        return false;
    }
    const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS32*>(
        base + dos->e_lfanew);
    const auto& directory =
        nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    if (!directory.VirtualAddress) {
        return false;
    }
    const auto* exports = reinterpret_cast<const IMAGE_EXPORT_DIRECTORY*>(
        base + directory.VirtualAddress);
    if (exports->NumberOfFunctions != 4 || exports->NumberOfNames != 4) {
        return false;
    }
    const char* required[] = {
        "timeBeginPeriod", "timeEndPeriod", "timeGetDevCaps", "timeGetTime",
    };
    bool found[4] = {};
    const auto* names = reinterpret_cast<const DWORD*>(
        base + exports->AddressOfNames);
    for (DWORD i = 0; i < exports->NumberOfNames; ++i) {
        const char* name = reinterpret_cast<const char*>(base + names[i]);
        for (std::size_t j = 0; j < 4; ++j) {
            if (std::strcmp(name, required[j]) == 0) {
                found[j] = true;
            }
        }
    }
    return found[0] && found[1] && found[2] && found[3];
}

int wmain(int argc, wchar_t** argv) {
    static_assert(sizeof(void*) == 4, "harness must be built as x86");
    static_assert(kHangulProxyRowCount > 0,
                  "generated Hangul proxy table must not be empty");
    if (argc < 3) {
        std::fprintf(stderr, "FAIL: expected DLL path and row-count argument\n");
        return 10;
    }
    wchar_t* count_end = nullptr;
    const unsigned long expected_rows = std::wcstoul(argv[2], &count_end, 10);
    if (!count_end || *count_end != L'\0' || expected_rows == 0 ||
        expected_rows != kHangulProxyRowCount) {
        std::fprintf(stderr,
                     "FAIL: generated rows=%zu expected argument=%lu\n",
                     kHangulProxyRowCount, expected_rows);
        return 11;
    }
    const HangulProxyRow* ryo = nullptr;
    for (std::size_t i = 0; i < kHangulProxyRowCount; ++i) {
        if (i && kHangulProxyRows[i - 1].cp949_packed >=
                     kHangulProxyRows[i].cp949_packed) {
            std::fprintf(stderr, "FAIL: CP949 table is not strictly sorted\n");
            return 12;
        }
        if (kHangulProxyRows[i].unicode_codepoint == 0xB8CC) {
            ryo = &kHangulProxyRows[i];
        }
        const char cp949[2] = {
            static_cast<char>(kHangulProxyRows[i].cp949_packed >> 8),
            static_cast<char>(kHangulProxyRows[i].cp949_packed & 0xFF),
        };
        const char cp932[2] = {
            static_cast<char>(kHangulProxyRows[i].cp932_packed >> 8),
            static_cast<char>(kHangulProxyRows[i].cp932_packed & 0xFF),
        };
        wchar_t decoded949 = 0;
        wchar_t decoded932 = 0;
        if (MultiByteToWideChar(949, MB_ERR_INVALID_CHARS, cp949, 2,
                                &decoded949, 1) != 1 ||
            decoded949 != kHangulProxyRows[i].unicode_codepoint ||
            MultiByteToWideChar(932, MB_ERR_INVALID_CHARS, cp932, 2,
                                &decoded932, 1) != 1 ||
            decoded932 != kHangulProxyRows[i].proxy_wchar) {
            std::fprintf(stderr, "FAIL: codepage roundtrip at row %zu\n", i);
            return 14;
        }
    }
    if (!ryo || ryo->cp949_packed != 0xB7E1 ||
        ryo->cp932_packed != 0xE853) {
        std::fprintf(stderr, "FAIL: expected ryo mapping is absent\n");
        return 13;
    }

    const wchar_t* dll_path = argv[1];
    HMODULE proxy = LoadLibraryW(dll_path);
    if (!proxy) {
        std::fprintf(stderr, "FAIL: LoadLibraryW error=%lu\n", GetLastError());
        return 20;
    }
    if (!HasExactlyRequiredExports(proxy)) {
        std::fprintf(stderr, "FAIL: export set is not exactly the required four\n");
        FreeLibrary(proxy);
        return 21;
    }
    auto get_caps = reinterpret_cast<TimeGetDevCapsFn>(
        GetProcAddress(proxy, "timeGetDevCaps"));
    auto get_time = reinterpret_cast<TimeGetTimeFn>(
        GetProcAddress(proxy, "timeGetTime"));
    auto begin_period = reinterpret_cast<TimePeriodFn>(
        GetProcAddress(proxy, "timeBeginPeriod"));
    auto end_period = reinterpret_cast<TimePeriodFn>(
        GetProcAddress(proxy, "timeEndPeriod"));
    if (!get_caps || !get_time || !begin_period || !end_period) {
        std::fprintf(stderr, "FAIL: one or more required exports are absent\n");
        FreeLibrary(proxy);
        return 22;
    }

    TIMECAPS caps = {};
    if (get_caps(&caps, sizeof(caps)) != TIMERR_NOERROR) {
        std::fprintf(stderr, "FAIL: real timeGetDevCaps was not forwarded\n");
        FreeLibrary(proxy);
        return 23;
    }
    const DWORD before = get_time();
    const MMRESULT begin = begin_period(caps.wPeriodMin);
    const DWORD after = get_time();
    if (begin == TIMERR_NOERROR) {
        if (end_period(caps.wPeriodMin) != TIMERR_NOERROR) {
            std::fprintf(stderr, "FAIL: balanced timeEndPeriod failed\n");
            FreeLibrary(proxy);
            return 24;
        }
    }
    std::printf(
        "PASS: x86 table=%zu ryo=B7E1->E853 caps=%u..%u time=%lu..%lu\n",
        kHangulProxyRowCount, caps.wPeriodMin, caps.wPeriodMax,
        static_cast<unsigned long>(before), static_cast<unsigned long>(after));
    FreeLibrary(proxy);
    return 0;
}
