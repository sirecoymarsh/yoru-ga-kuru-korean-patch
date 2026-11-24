#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _WINMM_
#include <windows.h>
#include <imm.h>
#include <mmsystem.h>
#include <objbase.h>
#include <shellapi.h>
#include <shlobj.h>

#include <cstddef>
#include <cstdint>
#include <cstring>

#include "hangul_proxy_table.generated.h"

#ifndef IME_HOOK_DIAGNOSTICS
#define IME_HOOK_DIAGNOSTICS 1
#endif

#if IME_HOOK_DIAGNOSTICS
#define DIAG_FORMAT(buffer, format, ...) \
    wsprintfA((buffer), (format), __VA_ARGS__)
#else
#define DIAG_FORMAT(...) ((void)0)
#endif

namespace {

using TimeGetDevCapsFn = MMRESULT(WINAPI*)(LPTIMECAPS, UINT);
using TimeGetTimeFn = DWORD(WINAPI*)();
using TimePeriodFn = MMRESULT(WINAPI*)(UINT);

HMODULE g_self = nullptr;
HMODULE g_real_winmm = nullptr;
INIT_ONCE g_real_init = INIT_ONCE_STATIC_INIT;
INIT_ONCE g_hook_init = INIT_ONCE_STATIC_INIT;
#if IME_HOOK_DIAGNOSTICS
SRWLOCK g_log_lock = SRWLOCK_INIT;
#endif
HWND g_game_window = nullptr;
WNDPROC g_original_wndproc = nullptr;
using RegisterClassAFn = ATOM(WINAPI*)(const WNDCLASSA*);
using ImmGetCandidateListAFn = DWORD(WINAPI*)(HIMC, DWORD, LPCANDIDATELIST, DWORD);
RegisterClassAFn g_real_register_class_a = nullptr;
ImmGetCandidateListAFn g_real_imm_get_candidate_list_a = nullptr;

constexpr std::uintptr_t kExpectedExeBase = 0x00400000u;
constexpr std::uintptr_t kRegisterClassAIat = 0x007BE38Cu;
constexpr std::uintptr_t kImmGetCandidateListAIat = 0x007BE06Cu;
constexpr std::uintptr_t kExpectedGameWndProc = 0x007321F0u;
constexpr DWORD kExpectedExeTimestamp = 0x65F707F0u;
constexpr DWORD kExpectedExeSizeOfImage = 0x00508000u;
constexpr unsigned char kWndProcFingerprint[] = {
    0x83, 0xEC, 0x08, 0x53, 0x56, 0x8B, 0x74, 0x24,
    0x18, 0x57, 0x8B, 0x7C, 0x24, 0x24, 0x81, 0xFE,
};
thread_local bool g_handled_result_in_composition = false;
LONG g_candidate_api_suppression_logged = 0;
LONG g_install_status_logged = 0;
LONG g_install_status = 0;

// --- Mod menu (Claude, 2026-09-28) ---------------------------------------
// On the first WM_INITMENU, when the menu bar has the shipped shape (System,
// Help), a "Mod" popup is inserted between them with five items: Event
// flowchart / Unlock all / Revert unlock / Reset all / Restore reset.  Each
// command writes <exe folder>\KRMenu\request.txt (cmd, seq, time) which the
// game script consumes in its home loop; the two reset commands first ask
// through a native MessageBox.  At the next start (first timer call, before
// the engine reads its global record files) a pending KRMenu\reset.req or
// KRMenu\restore.req is executed only when the save folder also holds
// YoruKR_reset.marker with the matching word: the global record files are
// backed up to <save>\Backup\KR_reset_<time>\ and deleted (reset), or copied
// back from the newest such backup (restore).  Results go to
// KRMenu\last_result.txt (ASCII, one line).  All Korean menu/message text is
// written as UTF-16 code points so this file stays ASCII.
constexpr UINT kModMenuIdFirst = 0x7E10u;
constexpr UINT kModMenuIdLast = 0x7EFFu;
constexpr int kModMenuInsertPosition = 1;          // between System (0) and Help (1)
enum ModCommand { kModChart = 0, kModUnlockAll, kModUnlockRevert, kModResetAll, kModResetRestore, kModCommandCount };
const char* const kModCommandNames[kModCommandCount] = {"chart", "unlock_all", "unlock_revert", "reset_all", "reset_restore"};
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kModMenuText[] = { 0xBAA8, 0xB4DC, L'(', L'&', L'M', L')', 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kModTextChart[] = { 0xC774, 0xBCA4, 0xD2B8, L' ', 0xD50C, 0xB85C, 0xC6B0, L' ', 0xCC28, 0xD2B8, L'(', L'&', L'E', L')', 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kModTextUnlock[] = { 0xC804, 0xCCB4, L' ', 0xAC1C, 0xBC29, L'(', L'&', L'U', L')', 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kModTextRevert[] = { 0xC804, 0xCCB4, L' ', 0xAC1C, 0xBC29, L' ', 0xB418, 0xB3CC, 0xB9AC, 0xAE30, L'(', L'&', L'R', L')', 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kModTextReset[] = { 0xC804, 0xCCB4, L' ', 0xB9AC, 0xC14B, L'(', L'&', L'Z', L')', 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kModTextRestore[] = { 0xC804, 0xCCB4, L' ', 0xB9AC, 0xC14B, L' ', 0xB418, 0xB3CC, 0xB9AC, 0xAE30, L'(', L'&', L'B', L')', 0 };
const wchar_t* const kModItemTexts[kModCommandCount] = { kModTextChart, kModTextUnlock, kModTextRevert, kModTextReset, kModTextRestore };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kResetTitle[] = { 0xC804, 0xCCB4, L' ', 0xB9AC, 0xC14B, 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kResetQuestion[] = {
    0xC804, 0xC5ED, L' ', 0xC9C4, 0xD589, L' ', 0xAE30, 0xB85D, 0xC744, L' ', 0xCD08, 0xAE30, 0xD654, 0xD569, 0xB2C8, 0xB2E4, L'.', L'\n',
    0xBC31, 0xC5C5, 0xC744, L' ', 0xB9CC, 0xB4E0, L' ', 0xB4A4, L' ', 0xAC8C, 0xC784, 0xC744, L' ', 0xC885, 0xB8CC, 0xD569, 0xB2C8, 0xB2E4, L'.', L'\n',
    0xC138, 0xC774, 0xBE0C, L' ', 0xD30C, 0xC77C, 0xACFC, L' ', 0xC124, 0xC815, 0xC740, L' ', 0xB0A8, 0xC2B5, 0xB2C8, 0xB2E4, L'.', L'\n',
    0xACC4, 0xC18D, 0xD560, 0xAE4C, 0xC694, L'?', 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kRestoreTitle[] = { 0xC804, 0xCCB4, L' ', 0xB9AC, 0xC14B, L' ', 0xB418, 0xB3CC, 0xB9AC, 0xAE30, 0 };
// (Korean label as UTF-16 code points; see the English name of the array)
const wchar_t kRestoreQuestion[] = {
    0xCD5C, 0xADFC, L' ', 0xBC31, 0xC5C5, 0xC744, L' ', 0xBCF5, 0xC6D0, 0xD569, 0xB2C8, 0xB2E4, L'.', L'\n',
    0xAC8C, 0xC784, 0xC744, L' ', 0xC885, 0xB8CC, 0xD569, 0xB2C8, 0xB2E4, L'.', L'\n',
    0xACC4, 0xC18D, 0xD560, 0xAE4C, 0xC694, L'?', 0 };
// Global record files (save folder) touched by reset/restore.  Save slots,
// config files and the term/chart settings are never touched.
// (YoruKR_HomeRate.dat is the achievement-panel on/off setting, not a record: never touched.)
const wchar_t* const kGlobalRecordFiles[] = {
    L"NightRAFInfo.asd", L"NightRAFCGMode.asd", L"NightRAFMemMode.asd", L"NightRAFBGMMode.asd",
    L"NightRAFCommon.asd", L"NightRMsgSkip.msk", L"CommonGameData.asd" };
constexpr int kGlobalRecordFileCount = sizeof(kGlobalRecordFiles) / sizeof(kGlobalRecordFiles[0]);
LONG g_mod_menu_state = 0;                         // 0 untried, 2 in progress, 1 installed, -1 skipped
UINT g_mod_menu_ids[kModCommandCount] = {};
LONG g_request_seq = 0;

BOOL CALLBACK LoadRealWinmm(PINIT_ONCE, PVOID, PVOID*) {
    wchar_t path[MAX_PATH] = {};
    const UINT length = GetSystemDirectoryW(path, MAX_PATH);
    if (length == 0 || length >= MAX_PATH - 11) {
        return TRUE;
    }
    lstrcatW(path, L"\\winmm.dll");
    HMODULE loaded = LoadLibraryW(path);
    // Some loader configurations deduplicate modules by basename.  Never let
    // the proxy resolve its exports back to itself and recurse indefinitely.
    g_real_winmm = (loaded && loaded != g_self) ? loaded : nullptr;
    return TRUE;
}

FARPROC ResolveReal(const char* name) {
    InitOnceExecuteOnce(&g_real_init, LoadRealWinmm, nullptr, nullptr);
    return g_real_winmm ? GetProcAddress(g_real_winmm, name) : nullptr;
}

#if IME_HOOK_DIAGNOSTICS
void GetLogPath(wchar_t (&path)[MAX_PATH]) {
    path[0] = L'\0';
    if (!g_self || GetModuleFileNameW(g_self, path, MAX_PATH) == 0) {
        lstrcpyW(path, L"hangul_ime_hook.log");
        return;
    }
    wchar_t* slash = path;
    for (wchar_t* cursor = path; *cursor; ++cursor) {
        if (*cursor == L'\\' || *cursor == L'/') {
            slash = cursor + 1;
        }
    }
    lstrcpyW(slash, L"hangul_ime_hook.log");
}

void LogLine(const char* event_name, UINT message, WPARAM wparam, LPARAM lparam,
             const char* detail = "") {
    char line[640] = {};
    SYSTEMTIME now = {};
    GetLocalTime(&now);
    wsprintfA(line,
              "%04u-%02u-%02u %02u:%02u:%02u.%03u tid=%lu hwnd=0x%08lX "
              "%s msg=0x%04X wParam=0x%08lX lParam=0x%08lX %s\r\n",
              now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute,
              now.wSecond, now.wMilliseconds, GetCurrentThreadId(),
              static_cast<unsigned long>(reinterpret_cast<std::uintptr_t>(g_game_window)),
              event_name, message, static_cast<unsigned long>(wparam),
              static_cast<unsigned long>(lparam), detail);

    wchar_t path[MAX_PATH] = {};
    GetLogPath(path);
    AcquireSRWLockExclusive(&g_log_lock);
    HANDLE file = CreateFileW(path, FILE_APPEND_DATA,
                              FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr,
                              OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file != INVALID_HANDLE_VALUE) {
        DWORD written = 0;
        WriteFile(file, line, static_cast<DWORD>(lstrlenA(line)), &written, nullptr);
        CloseHandle(file);
    }
    ReleaseSRWLockExclusive(&g_log_lock);
}
#else
void LogLine(const char* event_name, UINT message, WPARAM wparam, LPARAM lparam,
             const char* detail = "") {
    (void)event_name;
    (void)message;
    (void)wparam;
    (void)lparam;
    (void)detail;
}
#endif

const char* ImeMessageName(UINT message) {
    switch (message) {
    case WM_IME_STARTCOMPOSITION: return "WM_IME_STARTCOMPOSITION";
    case WM_IME_ENDCOMPOSITION: return "WM_IME_ENDCOMPOSITION";
    case WM_IME_COMPOSITION: return "WM_IME_COMPOSITION";
    case WM_IME_SETCONTEXT: return "WM_IME_SETCONTEXT";
    case WM_IME_NOTIFY: return "WM_IME_NOTIFY";
    case WM_IME_CONTROL: return "WM_IME_CONTROL";
    case WM_IME_COMPOSITIONFULL: return "WM_IME_COMPOSITIONFULL";
    case WM_IME_SELECT: return "WM_IME_SELECT";
    case WM_IME_CHAR: return "WM_IME_CHAR";
    case WM_IME_REQUEST: return "WM_IME_REQUEST";
    case WM_IME_KEYDOWN: return "WM_IME_KEYDOWN";
    case WM_IME_KEYUP: return "WM_IME_KEYUP";
    default: return nullptr;
    }
}

const HangulProxyRow* FindByCp949(std::uint16_t packed) {
    std::size_t low = 0;
    std::size_t high = kHangulProxyRowCount;
    while (low < high) {
        const std::size_t middle = low + (high - low) / 2;
        const auto value = kHangulProxyRows[middle].cp949_packed;
        if (value < packed) {
            low = middle + 1;
        } else {
            high = middle;
        }
    }
    if (low < kHangulProxyRowCount &&
        kHangulProxyRows[low].cp949_packed == packed) {
        return &kHangulProxyRows[low];
    }
    return nullptr;
}

const HangulProxyRow* FindByUnicode(std::uint16_t codepoint) {
    for (std::size_t i = 0; i < kHangulProxyRowCount; ++i) {
        if (kHangulProxyRows[i].unicode_codepoint == codepoint) {
            return &kHangulProxyRows[i];
        }
    }
    return nullptr;
}

bool DecodeCp949Hangul(std::uint16_t packed, wchar_t* decoded) {
    const char bytes[2] = {
        static_cast<char>((packed >> 8) & 0xFF),
        static_cast<char>(packed & 0xFF),
    };
    wchar_t output = 0;
    if (MultiByteToWideChar(949, MB_ERR_INVALID_CHARS, bytes, 2, &output, 1) != 1) {
        return false;
    }
    if (output < 0xAC00 || output > 0xD7A3) {
        return false;
    }
    if (decoded) {
        *decoded = output;
    }
    return true;
}

LRESULT CallOriginal(HWND window, UINT message, WPARAM wparam, LPARAM lparam) {
    WNDPROC original = g_original_wndproc;
    if (!original) {
        return DefWindowProcA(window, message, wparam, lparam);
    }
    return CallWindowProcA(original, window, message, wparam, lparam);
}

LRESULT DeliverProxyCharacter(HWND window, const HangulProxyRow& row,
                              LPARAM original_lparam) {
    const WPARAM lead = static_cast<WPARAM>((row.cp932_packed >> 8) & 0xFF);
    const WPARAM trail = static_cast<WPARAM>(row.cp932_packed & 0xFF);
    CallOriginal(window, WM_CHAR, lead, original_lparam);
    return CallOriginal(window, WM_CHAR, trail, original_lparam);
}

LRESULT DeliverCp932Character(HWND window, std::uint16_t packed,
                              unsigned byte_count, LPARAM char_lparam) {
    if (byte_count == 1) {
        return CallOriginal(window, WM_CHAR, packed & 0xFFu, char_lparam);
    }
    const WPARAM lead = static_cast<WPARAM>((packed >> 8) & 0xFF);
    const WPARAM trail = static_cast<WPARAM>(packed & 0xFF);
    CallOriginal(window, WM_CHAR, lead, char_lparam);
    return CallOriginal(window, WM_CHAR, trail, char_lparam);
}

bool EncodeWideCp932(wchar_t character, std::uint16_t* packed,
                     unsigned* byte_count) {
    char bytes[2] = {};
    BOOL used_default = FALSE;
    const int count = WideCharToMultiByte(932, WC_NO_BEST_FIT_CHARS, &character,
                                          1, bytes, 2, nullptr, &used_default);
    if (used_default || (count != 1 && count != 2)) {
        return false;
    }
    if (count == 1) {
        *packed = static_cast<unsigned char>(bytes[0]);
    } else {
        *packed = static_cast<std::uint16_t>(
            (static_cast<unsigned char>(bytes[0]) << 8) |
            static_cast<unsigned char>(bytes[1]));
    }
    *byte_count = static_cast<unsigned>(count);
    return true;
}

void DeliverCompositionResult(HWND window, LPARAM original_lparam) {
    HIMC context = ImmGetContext(window);
    if (!context) {
        LogLine("composition_result_swallowed", WM_IME_COMPOSITION, 0,
                original_lparam, "ImmGetContext failed");
        return;
    }
    const LONG byte_count =
        ImmGetCompositionStringW(context, GCS_RESULTSTR, nullptr, 0);
    if (byte_count <= 0 || byte_count > 64 * static_cast<LONG>(sizeof(wchar_t)) ||
        byte_count % static_cast<LONG>(sizeof(wchar_t)) != 0) {
        ImmReleaseContext(window, context);
        LogLine("composition_result_swallowed", WM_IME_COMPOSITION,
                static_cast<WPARAM>(byte_count), original_lparam,
                "empty, oversized, or malformed GCS_RESULTSTR");
        return;
    }

    wchar_t result[65] = {};
    const LONG copied = ImmGetCompositionStringW(
        context, GCS_RESULTSTR, result, static_cast<DWORD>(sizeof(result) - sizeof(wchar_t)));
    ImmReleaseContext(window, context);
    if (copied != byte_count) {
        LogLine("composition_result_swallowed", WM_IME_COMPOSITION,
                static_cast<WPARAM>(copied), original_lparam,
                "GCS_RESULTSTR copy length mismatch");
        return;
    }

    const std::size_t count = static_cast<std::size_t>(copied) / sizeof(wchar_t);
    std::uint16_t encoded[64] = {};
    unsigned encoded_lengths[64] = {};
    for (std::size_t i = 0; i < count; ++i) {
        if (result[i] >= 0xAC00 && result[i] <= 0xD7A3) {
            const HangulProxyRow* row =
                FindByUnicode(static_cast<std::uint16_t>(result[i]));
            if (!row) {
                LogLine("unsupported_composition_swallowed", WM_IME_COMPOSITION,
                        static_cast<WPARAM>(result[i]), original_lparam,
                        "GCS_RESULTSTR Hangul has no proxy row");
                return; // Drop the whole mixed result, never a prefix.
            }
            encoded[i] = row->cp932_packed;
            encoded_lengths[i] = 2;
        } else {
            unsigned length = 0;
            std::uint16_t packed = 0;
            if (!EncodeWideCp932(result[i], &packed, &length) || length != 1 ||
                packed < 0x20 || packed > 0x7E) {
                LogLine("unsupported_composition_swallowed",
                        WM_IME_COMPOSITION,
                        static_cast<WPARAM>(result[i]), original_lparam,
                        "non-ASCII, jamo, Hanja, or high-bit result");
                return;
            }
            encoded[i] = packed;
            encoded_lengths[i] = 1;
        }
    }

    for (std::size_t i = 0; i < count; ++i) {
        char detail[96] = {};
        DIAG_FORMAT(detail, "unicode=U+%04X cp932=0x%04X bytes=%u",
                    result[i], encoded[i], encoded_lengths[i]);
        LogLine("composition_hangul_mapped", WM_IME_COMPOSITION,
                static_cast<WPARAM>(result[i]), original_lparam, detail);
        // WM_IME_COMPOSITION flags are not a valid WM_CHAR lParam.  Use a
        // single-repeat synthetic character message instead.
        DeliverCp932Character(window, encoded[i], encoded_lengths[i],
                              static_cast<LPARAM>(1));
    }
}

bool IsKoreanKeyboardLayout() {
    const LANGID language =
        LOWORD(reinterpret_cast<ULONG_PTR>(GetKeyboardLayout(0)));
    return PRIMARYLANGID(language) == LANG_KOREAN;
}

bool ExeDirectory(wchar_t (&dir)[MAX_PATH]) {
    const DWORD length = GetModuleFileNameW(nullptr, dir, MAX_PATH);
    if (length == 0 || length >= MAX_PATH) {
        return false;
    }
    wchar_t* slash = nullptr;
    for (wchar_t* cursor = dir; *cursor; ++cursor) {
        if (*cursor == L'\\' || *cursor == L'/') {
            slash = cursor;
        }
    }
    if (!slash) {
        return false;
    }
    *slash = L'\0';
    return true;
}

bool JoinPath(wchar_t (&out)[MAX_PATH], const wchar_t* dir, const wchar_t* rel) {
    if (lstrlenW(dir) + 1 + lstrlenW(rel) + 1 > MAX_PATH) {
        return false;
    }
    lstrcpyW(out, dir);
    lstrcatW(out, L"\\");
    lstrcatW(out, rel);
    return true;
}

bool FileExists(const wchar_t* path) {
    const DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0;
}

bool DirectoryExists(const wchar_t* path) {
    const DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY) != 0;
}

bool EnsureDirectory(const wchar_t* path) {
    if (DirectoryExists(path)) {
        return true;
    }
    return CreateDirectoryW(path, nullptr) != 0 || GetLastError() == ERROR_ALREADY_EXISTS;
}

bool WriteTextAtomic(const wchar_t* path, const char* text) {
    wchar_t tmp[MAX_PATH] = {};
    if (lstrlenW(path) + 5 > MAX_PATH) {
        return false;
    }
    lstrcpyW(tmp, path);
    lstrcatW(tmp, L".tmp");
    HANDLE file = CreateFileW(tmp, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }
    DWORD written = 0;
    const DWORD length = static_cast<DWORD>(lstrlenA(text));
    const bool ok = WriteFile(file, text, length, &written, nullptr) && written == length && FlushFileBuffers(file);
    CloseHandle(file);
    if (!ok || !MoveFileExW(tmp, path, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        DeleteFileW(tmp);
        return false;
    }
    return true;
}

bool ReadSmallFile(const wchar_t* path, char* buffer, DWORD capacity, DWORD* size) {
    *size = 0;
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }
    DWORD read = 0;
    const bool ok = ReadFile(file, buffer, capacity - 1, &read, nullptr) != 0;
    CloseHandle(file);
    if (!ok) {
        return false;
    }
    buffer[read] = '\0';
    *size = read;
    return true;
}

bool MenuFolder(wchar_t (&dir)[MAX_PATH]) {
    wchar_t exe[MAX_PATH] = {};
    return ExeDirectory(exe) && JoinPath(dir, exe, L"KRMenu") && EnsureDirectory(dir);
}

bool WriteRequest(ModCommand command) {
    wchar_t dir[MAX_PATH] = {};
    wchar_t path[MAX_PATH] = {};
    if (!MenuFolder(dir) || !JoinPath(path, dir, L"request.txt")) {
        return false;
    }
    SYSTEMTIME now = {};
    GetLocalTime(&now);
    const LONG seq = InterlockedIncrement(&g_request_seq);
    char text[160] = {};
    wsprintfA(text, "%s\r\n%ld\r\n%04u-%02u-%02u %02u:%02u:%02u\r\n", kModCommandNames[command], seq,
              now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond);
    return WriteTextAtomic(path, text);
}

void WriteResult(const char* text) {
    wchar_t dir[MAX_PATH] = {};
    wchar_t path[MAX_PATH] = {};
    if (MenuFolder(dir) && JoinPath(path, dir, L"last_result.txt")) {
        WriteTextAtomic(path, text);
    }
}

// Value of `key = "value"` in an ANSI ini (the engine's AliceStart.ini layout).
bool IniQuotedValue(const char* data, const char* key, char* out, int out_size) {
    const int key_length = lstrlenA(key);
    for (const char* line = data; *line; ) {
        const char* end = line;
        while (*end && *end != '\r' && *end != '\n') {
            ++end;
        }
        if (end - line > key_length && memcmp(line, key, static_cast<std::size_t>(key_length)) == 0) {
            const char* p = line + key_length;
            while (p < end && (*p == ' ' || *p == '\t')) ++p;
            if (p < end && *p == '=') {
                ++p;
                while (p < end && (*p == ' ' || *p == '\t')) ++p;
                if (p < end && *p == '"') {
                    ++p;
                    int n = 0;
                    while (p < end && *p != '"' && n < out_size - 1) {
                        out[n++] = *p++;
                    }
                    out[n] = '\0';
                    return n > 0;
                }
            }
        }
        line = end;
        while (*line == '\r' || *line == '\n') {
            ++line;
        }
    }
    return false;
}

bool AnsiToWide(const char* text, wchar_t* out, int out_size) {
    const int n = MultiByteToWideChar(CP_ACP, MB_ERR_INVALID_CHARS, text, -1, out, out_size);
    return n > 0;
}

// The engine's save folder: <exe>\<SaveFolder> when InstallInfo\SaveFolderSetting.ini
// says type 2, otherwise <Documents>\AliceSoft\<GameName>\<SaveFolder>.
bool ResolveSaveFolder(wchar_t (&folder)[MAX_PATH]) {
    wchar_t exe[MAX_PATH] = {};
    wchar_t path[MAX_PATH] = {};
    if (!ExeDirectory(exe) || !JoinPath(path, exe, L"AliceStart.ini")) {
        return false;
    }
    static char ini[8192];
    DWORD size = 0;
    if (!ReadSmallFile(path, ini, sizeof(ini), &size)) {
        return false;
    }
    char save_a[MAX_PATH] = {};
    if (!IniQuotedValue(ini, "SaveFolder", save_a, MAX_PATH)) {
        return false;
    }
    wchar_t save_w[MAX_PATH] = {};
    if (!AnsiToWide(save_a, save_w, MAX_PATH)) {
        return false;
    }
    bool exe_relative = false;
    if (JoinPath(path, exe, L"InstallInfo\\SaveFolderSetting.ini")) {
        char setting[16] = {};
        DWORD n = 0;
        if (ReadSmallFile(path, setting, sizeof(setting), &n) && n >= 12 && memcmp(setting, "SFSF", 4) == 0) {
            std::int32_t kind = 0;
            memcpy(&kind, setting + 8, sizeof(kind));
            exe_relative = kind == 2;
        }
    }
    if (exe_relative) {
        return JoinPath(folder, exe, save_w) && DirectoryExists(folder);
    }
    char game_a[MAX_PATH] = {};
    wchar_t game_w[MAX_PATH] = {};
    if (!IniQuotedValue(ini, "GameName", game_a, MAX_PATH) || !AnsiToWide(game_a, game_w, MAX_PATH)) {
        return false;
    }
    PWSTR documents = nullptr;
    if (FAILED(SHGetKnownFolderPath(FOLDERID_Documents, 0, nullptr, &documents)) || !documents) {
        return false;
    }
    wchar_t base[MAX_PATH] = {};
    const bool ok = JoinPath(base, documents, L"AliceSoft") && JoinPath(path, base, game_w) &&
                    JoinPath(folder, path, save_w) && DirectoryExists(folder);
    CoTaskMemFree(documents);
    return ok;
}

bool MarkerSays(const wchar_t* save, const char* word) {
    wchar_t path[MAX_PATH] = {};
    char text[64] = {};
    DWORD size = 0;
    if (!JoinPath(path, save, L"YoruKR_reset.marker") || !ReadSmallFile(path, text, sizeof(text), &size)) {
        return false;
    }
    const int n = lstrlenA(word);
    return static_cast<int>(size) >= n && memcmp(text, word, static_cast<std::size_t>(n)) == 0 &&
           (text[n] == '\0' || text[n] == '\r' || text[n] == '\n' || text[n] == ' ');
}

bool CopyVerified(const wchar_t* src, const wchar_t* dst) {
    if (!CopyFileW(src, dst, TRUE)) {
        return false;
    }
    WIN32_FILE_ATTRIBUTE_DATA a = {}, b = {};
    return GetFileAttributesExW(src, GetFileExInfoStandard, &a) && GetFileAttributesExW(dst, GetFileExInfoStandard, &b) &&
           a.nFileSizeLow == b.nFileSizeLow && a.nFileSizeHigh == b.nFileSizeHigh;
}

void RemoveMaintenanceFiles(const wchar_t* save, const wchar_t* req) {
    wchar_t path[MAX_PATH] = {};
    if (JoinPath(path, save, L"YoruKR_reset.marker")) {
        DeleteFileW(path);
    }
    DeleteFileW(req);
}

void TimeStamp(wchar_t (&out)[32]) {
    SYSTEMTIME now = {};
    GetLocalTime(&now);
    wsprintfW(out, L"%04u%02u%02u_%02u%02u%02u", now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond);
}

void RunReset(const wchar_t* save, const wchar_t* req) {
    wchar_t stamp[32] = {};
    TimeStamp(stamp);
    wchar_t backup_root[MAX_PATH] = {}, name[64] = {}, backup[MAX_PATH] = {};
    wsprintfW(name, L"KR_reset_%s", stamp);
    if (!JoinPath(backup_root, save, L"Backup") || !EnsureDirectory(backup_root) || !JoinPath(backup, backup_root, name) ||
        !CreateDirectoryW(backup, nullptr)) {
        RemoveMaintenanceFiles(save, req);
        WriteResult("reset failed backup folder\r\n");
        return;
    }
    char manifest[1024] = {};
    int present[kGlobalRecordFileCount] = {};
    for (int i = 0; i < kGlobalRecordFileCount; ++i) {
        wchar_t src[MAX_PATH] = {}, dst[MAX_PATH] = {};
        if (!JoinPath(src, save, kGlobalRecordFiles[i]) || !FileExists(src)) {
            continue;
        }
        if (!JoinPath(dst, backup, kGlobalRecordFiles[i]) || !CopyVerified(src, dst)) {
            RemoveMaintenanceFiles(save, req);
            char text[160] = {};
            wsprintfA(text, "reset failed backup copy %d (nothing deleted)\r\n", i);
            WriteResult(text);
            return;
        }
        present[i] = 1;
        char line[96] = {};
        wsprintfA(line, "%S\r\n", kGlobalRecordFiles[i]);
        lstrcatA(manifest, line);
    }
    wchar_t manifest_path[MAX_PATH] = {};
    if (JoinPath(manifest_path, backup, L"manifest.txt")) {
        WriteTextAtomic(manifest_path, manifest);
    }
    int failed = 0;
    for (int i = 0; i < kGlobalRecordFileCount; ++i) {
        wchar_t src[MAX_PATH] = {};
        if (present[i] && JoinPath(src, save, kGlobalRecordFiles[i]) && !DeleteFileW(src)) {
            ++failed;
        }
    }
    RemoveMaintenanceFiles(save, req);
    char text[160] = {};
    if (failed) {
        wsprintfA(text, "reset partial %d files not deleted (backup %S)\r\n", failed, name);
    } else {
        wsprintfA(text, "reset ok %S\r\n", name);
    }
    WriteResult(text);
}

bool NewestBackup(const wchar_t* backup_root, wchar_t (&out)[MAX_PATH]) {
    wchar_t pattern[MAX_PATH] = {};
    if (!JoinPath(pattern, backup_root, L"KR_reset_*")) {
        return false;
    }
    WIN32_FIND_DATAW data = {};
    HANDLE find = FindFirstFileW(pattern, &data);
    if (find == INVALID_HANDLE_VALUE) {
        return false;
    }
    wchar_t best[MAX_PATH] = {};
    do {
        if ((data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) && lstrcmpW(data.cFileName, best) > 0) {
            lstrcpyW(best, data.cFileName);
        }
    } while (FindNextFileW(find, &data));
    FindClose(find);
    return best[0] != L'\0' && JoinPath(out, backup_root, best);
}

void RunRestore(const wchar_t* save, const wchar_t* req) {
    wchar_t backup_root[MAX_PATH] = {}, backup[MAX_PATH] = {};
    if (!JoinPath(backup_root, save, L"Backup") || !NewestBackup(backup_root, backup)) {
        RemoveMaintenanceFiles(save, req);
        WriteResult("restore failed no backup\r\n");
        return;
    }
    wchar_t stamp[32] = {}, name[64] = {}, keep[MAX_PATH] = {};
    TimeStamp(stamp);
    wsprintfW(name, L"KR_before_restore_%s", stamp);
    if (!JoinPath(keep, backup_root, name) || !CreateDirectoryW(keep, nullptr)) {
        RemoveMaintenanceFiles(save, req);
        WriteResult("restore failed keep folder\r\n");
        return;
    }
    int failed = 0;
    for (int i = 0; i < kGlobalRecordFileCount; ++i) {
        wchar_t src[MAX_PATH] = {}, dst[MAX_PATH] = {}, cur[MAX_PATH] = {}, aside[MAX_PATH] = {};
        if (!JoinPath(src, backup, kGlobalRecordFiles[i]) || !FileExists(src)) {
            continue;
        }
        if (JoinPath(cur, save, kGlobalRecordFiles[i]) && FileExists(cur) && JoinPath(aside, keep, kGlobalRecordFiles[i])) {
            if (!MoveFileExW(cur, aside, MOVEFILE_REPLACE_EXISTING)) {
                ++failed;
                continue;
            }
        }
        if (!JoinPath(dst, save, kGlobalRecordFiles[i]) || !CopyVerified(src, dst)) {
            ++failed;
        }
    }
    RemoveMaintenanceFiles(save, req);
    char text[200] = {};
    const wchar_t* backup_name = backup + lstrlenW(backup_root) + 1;
    if (failed) {
        wsprintfA(text, "restore partial %d files (from %S, previous kept in %S)\r\n", failed, backup_name, name);
    } else {
        wsprintfA(text, "restore ok %S (previous kept in %S)\r\n", backup_name, name);
    }
    WriteResult(text);
}

void RunStartupMaintenance() {
    wchar_t dir[MAX_PATH] = {}, reset_req[MAX_PATH] = {}, restore_req[MAX_PATH] = {};
    if (!MenuFolder(dir) || !JoinPath(reset_req, dir, L"reset.req") || !JoinPath(restore_req, dir, L"restore.req")) {
        return;
    }
    const bool want_reset = FileExists(reset_req);
    const bool want_restore = FileExists(restore_req);
    if (!want_reset && !want_restore) {
        return;
    }
    wchar_t save[MAX_PATH] = {};
    if (!ResolveSaveFolder(save)) {
        DeleteFileW(reset_req);
        DeleteFileW(restore_req);
        WriteResult("maintenance failed save folder unresolved\r\n");
        return;
    }
    if (want_reset) {
        if (MarkerSays(save, "reset")) {
            RunReset(save, reset_req);
        } else {
            DeleteFileW(reset_req);
            WriteResult("reset skipped marker missing\r\n");
        }
    }
    if (want_restore) {
        if (MarkerSays(save, "restore")) {
            RunRestore(save, restore_req);
        } else {
            DeleteFileW(restore_req);
            WriteResult("restore skipped marker missing\r\n");
        }
    }
}

bool MenuIdInUse(HMENU menu, UINT id, int depth) {
    if (!menu || depth > 8) {
        return false;
    }
    const int count = GetMenuItemCount(menu);
    for (int i = 0; i < count; ++i) {
        if (GetMenuItemID(menu, i) == id) {
            return true;
        }
        if (MenuIdInUse(GetSubMenu(menu, i), id, depth + 1)) {
            return true;
        }
    }
    return false;
}

void InstallModMenuOnce(HWND window, HMENU bar) {
    if (InterlockedCompareExchange(&g_mod_menu_state, 2, 0) != 0) {
        return;
    }
    LONG state = -1;
    const char* reason = "";
    UINT ids[kModCommandCount] = {};
    if (!bar || bar != GetMenu(window)) {
        reason = "not the window menu bar";
    } else if (GetMenuItemCount(bar) != 2) {
        reason = "unexpected menu bar shape";
    } else {
        int found = 0;
        for (UINT candidate = kModMenuIdFirst; candidate <= kModMenuIdLast && found < kModCommandCount; ++candidate) {
            if (!MenuIdInUse(bar, candidate, 0)) {
                ids[found++] = candidate;
            }
        }
        if (found < kModCommandCount) {
            reason = "no free command ids";
        } else {
            HMENU popup = CreatePopupMenu();
            if (!popup) {
                reason = "CreatePopupMenu failed";
            } else {
                bool ok = true;
                for (int i = 0; i < kModCommandCount && ok; ++i) {
                    if (i == kModResetAll) {
                        ok = AppendMenuW(popup, MF_SEPARATOR, 0, nullptr) != 0;
                    }
                    if (ok) {
                        ok = AppendMenuW(popup, MF_STRING, ids[i], kModItemTexts[i]) != 0;
                    }
                }
                if (ok) {
                    ok = InsertMenuW(bar, static_cast<UINT>(kModMenuInsertPosition), MF_BYPOSITION | MF_POPUP | MF_STRING,
                                     reinterpret_cast<UINT_PTR>(popup), kModMenuText) != 0;
                }
                if (!ok) {
                    DestroyMenu(popup);
                    reason = "menu insertion failed";
                } else {
                    for (int i = 0; i < kModCommandCount; ++i) {
                        g_mod_menu_ids[i] = ids[i];
                    }
                    DrawMenuBar(window);
                    state = 1;
                    reason = "mod popup inserted";
                }
            }
        }
    }
    InterlockedExchange(&g_mod_menu_state, state);
    char detail[192] = {};
    wsprintfA(detail, "mod menu %s ids=0x%04X..0x%04X (%s)", state == 1 ? "installed" : "skipped",
              ids[0], ids[kModCommandCount - 1], reason);
    LogLine(state == 1 ? "mod_menu_installed" : "mod_menu_skipped", WM_INITMENU, reinterpret_cast<WPARAM>(bar), 0, detail);
}

int ModCommandIndex(UINT id) {
    if (g_mod_menu_state != 1 || id == 0) {
        return -1;
    }
    for (int i = 0; i < kModCommandCount; ++i) {
        if (g_mod_menu_ids[i] == id) {
            return i;
        }
    }
    return -1;
}

void HandleModCommand(HWND window, int index) {
    if (index == kModResetAll || index == kModResetRestore) {
        const bool reset = index == kModResetAll;
        const int answer = MessageBoxW(window, reset ? kResetQuestion : kRestoreQuestion, reset ? kResetTitle : kRestoreTitle,
                                       MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2 | MB_SETFOREGROUND);
        if (answer != IDYES) {
            LogLine("mod_command_cancelled", WM_COMMAND, g_mod_menu_ids[index], 0, kModCommandNames[index]);
            return;
        }
    }
    const bool ok = WriteRequest(static_cast<ModCommand>(index));
    LogLine(ok ? "mod_request_written" : "mod_request_failed", WM_COMMAND, g_mod_menu_ids[index], 0, kModCommandNames[index]);
}

LRESULT CALLBACK HookWndProc(HWND window, UINT message, WPARAM wparam,
                             LPARAM lparam) {
    if (!g_game_window) {
        g_game_window = window;
        LogLine("hook_wndproc_first_window", message, wparam, lparam,
                "registered ANSI class hook active");
    }
    if (message == WM_INITMENU && g_mod_menu_state == 0) {
        InstallModMenuOnce(window, reinterpret_cast<HMENU>(wparam));
    }
    if (message == WM_COMMAND && lparam == 0 && HIWORD(wparam) == 0) {
        const int index = ModCommandIndex(LOWORD(wparam));
        if (index >= 0) {
            HandleModCommand(window, index);
            return 0;
        }
    }
    if (const char* name = ImeMessageName(message)) {
        LogLine(name, message, wparam, lparam);
    }

    const bool korean_layout = IsKoreanKeyboardLayout();
    if (korean_layout && message == WM_IME_STARTCOMPOSITION) {
        g_handled_result_in_composition = false;
        return CallOriginal(window, message, wparam, lparam);
    }
    if (korean_layout && message == WM_IME_COMPOSITION) {
        if ((lparam & GCS_RESULTSTR) != 0) {
            // Under a Korean layout this hook owns every final result.  It is
            // either atomically injected after a complete precheck or wholly
            // swallowed; raw UTF-16/CP949 never falls through to the engine.
            DeliverCompositionResult(window, lparam);
            g_handled_result_in_composition = true;
            return 0;
        }
        return CallOriginal(window, message, wparam, lparam);
    }
    if (korean_layout && message == WM_IME_ENDCOMPOSITION) {
        // Keep the duplicate guard set beyond END: some IMEs post WM_IME_CHAR
        // late.  The next STARTCOMPOSITION begins a new generation.
        return CallOriginal(window, message, wparam, lparam);
    }

    if (korean_layout && message == WM_IME_NOTIFY) {
        // The original procedure owns its internal +0x195 IME state.  Only
        // the imported candidate-list read is suppressed by our IAT wrapper.
        return CallOriginal(window, message, wparam, lparam);
    }

    if (korean_layout && message == WM_IME_CHAR) {
        if (g_handled_result_in_composition) {
            LogLine("duplicate_ime_char_swallowed", message, wparam, lparam,
                    "GCS_RESULTSTR already injected");
            return 0;
        }
        const std::uint16_t raw = static_cast<std::uint16_t>(wparam & 0xFFFFu);
        const HangulProxyRow* row = nullptr;

        // This hook replaces an ANSI WNDCLASSA procedure, so a two-byte
        // WM_IME_CHAR is CP949 first.  Many packed Wansung byte pairs happen
        // to fall numerically inside U+AC00..U+D7A3; testing Unicode first
        // would silently map those commits as the wrong syllable.
        // WM_IME_CHAR documents the lead byte in the high byte.  Never try a
        // byte-swapped interpretation: a valid non-Hangul DBCS character can
        // otherwise collide with a reversed CP949 Hangul carrier.
        row = FindByCp949(raw);
        if (!row) {
            wchar_t decoded = 0;
            if (DecodeCp949Hangul(raw, &decoded)) {
                LogLine("unsupported_hangul_swallowed", message, wparam,
                        lparam, "CP949 WM_IME_CHAR");
                return 0;
            }
            // Defensive only: the exact hooked class is ANSI, but do not
            // mis-handle a future Unicode-class adaptation of this prototype.
            if (IsWindowUnicode(window) && raw >= 0xAC00 && raw <= 0xD7A3) {
                row = FindByUnicode(raw);
                if (!row) {
                    LogLine("unsupported_hangul_swallowed", message, wparam,
                            lparam, "unicode WM_IME_CHAR");
                    return 0;
                }
            }
            if (!row && raw >= 0x80) {
                LogLine("unsupported_ime_char_swallowed", message, wparam,
                        lparam,
                        "non-mapped high-bit, jamo, or Hanja WM_IME_CHAR");
                return 0;
            }
        }

        if (row) {
            char detail[128] = {};
            DIAG_FORMAT(detail,
                        "cp949=0x%04X unicode=U+%04X cp932=0x%04X",
                        row->cp949_packed, row->unicode_codepoint,
                        row->cp932_packed);
            LogLine("hangul_mapped", message, wparam, lparam, detail);
            return DeliverProxyCharacter(window, *row, lparam);
        }
    }

    return CallOriginal(window, message, wparam, lparam);
}

ATOM WINAPI HookRegisterClassA(const WNDCLASSA* window_class) {
    if (!g_real_register_class_a || !window_class) {
        return 0;
    }
    WNDCLASSA patched = *window_class;
    if (reinterpret_cast<std::uintptr_t>(patched.lpfnWndProc) ==
            kExpectedGameWndProc &&
        patched.hInstance == GetModuleHandleW(nullptr)) {
        // 0x007321F0 is a generic dispatcher shared by several game classes.
        // Every exact match is wrapped; all of them have the same preserved
        // original procedure, so a single immutable pointer is sufficient.
        if (!g_original_wndproc) {
            g_original_wndproc = patched.lpfnWndProc;
        }
        patched.lpfnWndProc = HookWndProc;
        LogLine("register_class_a_wrapped", 0,
                reinterpret_cast<WPARAM>(g_original_wndproc), 0,
                "exact expected WndProc matched");
    }
    return g_real_register_class_a(&patched);
}

DWORD WINAPI HookImmGetCandidateListA(HIMC context, DWORD index,
                                      LPCANDIDATELIST candidates,
                                      DWORD buffer_length) {
    if (IsKoreanKeyboardLayout()) {
        // The engine may poll this import every frame.  Keep the release-sized
        // diagnostic useful without allowing one suppression site to grow the
        // log without bound.
        if (InterlockedCompareExchange(&g_candidate_api_suppression_logged,
                                       1, 0) == 0) {
            LogLine("candidate_list_a_suppressed", WM_IME_NOTIFY, index,
                    static_cast<LPARAM>(buffer_length),
                    "Korean keyboard layout; later polls omitted");
        }
        return 0;
    }
    return g_real_imm_get_candidate_list_a
               ? g_real_imm_get_candidate_list_a(context, index, candidates,
                                                  buffer_length)
               : 0;
}

bool ValidateTargetImage() {
    const auto main_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    if (main_base != kExpectedExeBase) {
        return false;
    }
    const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(main_base);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
        dos->e_lfanew > 0x1000) {
        return false;
    }
    const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS32*>(
        main_base + static_cast<std::uintptr_t>(dos->e_lfanew));
    if (nt->Signature != IMAGE_NT_SIGNATURE ||
        nt->FileHeader.Machine != IMAGE_FILE_MACHINE_I386 ||
        nt->FileHeader.TimeDateStamp != kExpectedExeTimestamp ||
        nt->OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR32_MAGIC ||
        nt->OptionalHeader.ImageBase != kExpectedExeBase ||
        nt->OptionalHeader.SizeOfImage != kExpectedExeSizeOfImage) {
        return false;
    }
    const auto* code = reinterpret_cast<const unsigned char*>(kExpectedGameWndProc);
    for (std::size_t i = 0; i < sizeof(kWndProcFingerprint); ++i) {
        if (code[i] != kWndProcFingerprint[i]) {
            return false;
        }
    }
    return true;
}

LONG InstallMainExeIatHooksAtomic() {
    if (!ValidateTargetImage()) {
        return -1;
    }
    HMODULE user32 = GetModuleHandleW(L"user32.dll");
    HMODULE imm32 = GetModuleHandleW(L"imm32.dll");
    if (!user32 || !imm32) {
        return -2;
    }
    void* expected_register =
        reinterpret_cast<void*>(GetProcAddress(user32, "RegisterClassA"));
    void* expected_candidate =
        reinterpret_cast<void*>(GetProcAddress(imm32, "ImmGetCandidateListA"));
    if (!expected_register || !expected_candidate) {
        return -3;
    }

    void** register_slot = reinterpret_cast<void**>(kRegisterClassAIat);
    void** candidate_slot = reinterpret_cast<void**>(kImmGetCandidateListAIat);
    MEMORY_BASIC_INFORMATION register_memory = {};
    MEMORY_BASIC_INFORMATION candidate_memory = {};
    if (VirtualQuery(register_slot, &register_memory, sizeof(register_memory)) !=
            sizeof(register_memory) ||
        VirtualQuery(candidate_slot, &candidate_memory, sizeof(candidate_memory)) !=
            sizeof(candidate_memory) ||
        register_memory.AllocationBase != reinterpret_cast<void*>(kExpectedExeBase) ||
        candidate_memory.AllocationBase != reinterpret_cast<void*>(kExpectedExeBase)) {
        return -4;
    }

    // Precheck both slots before changing either.  The timestamp, image size,
    // code fingerprint, and exact loader-resolved function pointers must all
    // agree with the one supported executable build.
    if (*register_slot != expected_register ||
        *candidate_slot != expected_candidate) {
        return -5;
    }

    const auto low = reinterpret_cast<void*>(kImmGetCandidateListAIat);
    const SIZE_T span = kRegisterClassAIat - kImmGetCandidateListAIat +
                        sizeof(void*);
    DWORD old_protect = 0;
    if (!VirtualProtect(low, span, PAGE_READWRITE, &old_protect)) {
        return -6;
    }

    // Publish both preserved originals before either hook can be observed.
    g_real_register_class_a =
        reinterpret_cast<RegisterClassAFn>(expected_register);
    g_real_imm_get_candidate_list_a =
        reinterpret_cast<ImmGetCandidateListAFn>(expected_candidate);

    // Install the candidate hook first and the class-registration hook last.
    // Once RegisterClassA is observable, both hooks are already present.
    void* previous_candidate = InterlockedExchangePointer(
        candidate_slot, reinterpret_cast<void*>(HookImmGetCandidateListA));
    if (previous_candidate != expected_candidate) {
        InterlockedExchangePointer(candidate_slot, previous_candidate);
        g_real_register_class_a = nullptr;
        g_real_imm_get_candidate_list_a = nullptr;
        DWORD ignored = 0;
        VirtualProtect(low, span, old_protect, &ignored);
        return -7;
    }
    void* previous_register = InterlockedExchangePointer(
        register_slot, reinterpret_cast<void*>(HookRegisterClassA));
    if (previous_register != expected_register) {
        // Roll back both slots while the IAT page is still writable.
        InterlockedExchangePointer(register_slot, previous_register);
        InterlockedExchangePointer(candidate_slot, previous_candidate);
        g_real_register_class_a = nullptr;
        g_real_imm_get_candidate_list_a = nullptr;
        DWORD ignored = 0;
        VirtualProtect(low, span, old_protect, &ignored);
        return -8;
    }

    DWORD ignored = 0;
    if (!VirtualProtect(low, span, old_protect, &ignored)) {
        // Protection restoration is part of the transaction.  Roll back both
        // hooks, then make a best-effort second restoration attempt.
        InterlockedExchangePointer(register_slot, previous_register);
        InterlockedExchangePointer(candidate_slot, previous_candidate);
        g_real_register_class_a = nullptr;
        g_real_imm_get_candidate_list_a = nullptr;
        VirtualProtect(low, span, old_protect, &ignored);
        return -9;
    }
    FlushInstructionCache(GetCurrentProcess(), low, span);
    return 1;
}

void LogInstallStatus(LONG status) {
    if (InterlockedCompareExchange(&g_install_status_logged, 1, 0) != 0) {
        return;
    }
    char detail[160] = {};
    if (status == 1) {
        DIAG_FORMAT(detail,
                    "atomic pair installed; ts=0x%08lX size=0x%08lX fp=16",
                    kExpectedExeTimestamp, kExpectedExeSizeOfImage);
        LogLine("iat_hooks_installed", 0, kRegisterClassAIat,
                kImmGetCandidateListAIat, detail);
    } else {
        DIAG_FORMAT(detail, "atomic install refused status=%ld", status);
        LogLine("iat_hooks_refused", 0, 0, 0, detail);
    }
}

BOOL CALLBACK InstallHooksOnce(PINIT_ONCE, PVOID, PVOID*) {
    // Pending reset/restore runs first: this is the first timer call, before
    // the engine has read its global record files.
    RunStartupMaintenance();
    const LONG status = InstallMainExeIatHooksAtomic();
    InterlockedExchange(&g_install_status, status);
    LogInstallStatus(status);
    // A fingerprint or transaction refusal is final for this process; do not
    // retry a partially incompatible executable on every timer call.
    return TRUE;
}

void EnsureIatHooks() {
    InitOnceExecuteOnce(&g_hook_init, InstallHooksOnce, nullptr, nullptr);
}

} // namespace

extern "C" MMRESULT WINAPI timeGetDevCaps(LPTIMECAPS caps, UINT size) {
    EnsureIatHooks();
    auto function = reinterpret_cast<TimeGetDevCapsFn>(ResolveReal("timeGetDevCaps"));
    return function ? function(caps, size) : TIMERR_NOCANDO;
}

extern "C" DWORD WINAPI timeGetTime() {
    EnsureIatHooks();
    auto function = reinterpret_cast<TimeGetTimeFn>(ResolveReal("timeGetTime"));
    return function ? function() : GetTickCount();
}

extern "C" MMRESULT WINAPI timeBeginPeriod(UINT period) {
    EnsureIatHooks();
    auto function = reinterpret_cast<TimePeriodFn>(ResolveReal("timeBeginPeriod"));
    return function ? function(period) : TIMERR_NOCANDO;
}

extern "C" MMRESULT WINAPI timeEndPeriod(UINT period) {
    EnsureIatHooks();
    auto function = reinterpret_cast<TimePeriodFn>(ResolveReal("timeEndPeriod"));
    return function ? function(period) : TIMERR_NOCANDO;
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        static_assert(sizeof(void*) == 4, "This prototype must be built as x86");
        g_self = instance;
    }
    return TRUE;
}
