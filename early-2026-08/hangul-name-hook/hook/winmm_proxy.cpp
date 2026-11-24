#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define _WINMM_
#include <windows.h>
#include <imm.h>
#include <mmsystem.h>

#include <cstddef>
#include <cstdint>

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

LRESULT CALLBACK HookWndProc(HWND window, UINT message, WPARAM wparam,
                             LPARAM lparam) {
    if (!g_game_window) {
        g_game_window = window;
        LogLine("hook_wndproc_first_window", message, wparam, lparam,
                "registered ANSI class hook active");
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
