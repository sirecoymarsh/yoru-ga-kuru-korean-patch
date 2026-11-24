# NightRemaster Hangul IME WINMM proxy prototype

This directory contains an **x86 diagnostic prototype**, not a release patch.
It was built without copying anything into the game or launching the game.

## Behavior

- Exports and forwards only the four WINMM functions imported by
  `NightRemaster.exe`: `timeGetDevCaps`, `timeGetTime`, `timeBeginPeriod`, and
  `timeEndPeriod`.
- Loads the real DLL by absolute `%SystemRoot%\System32\winmm.dll` path.
- Validates and patches the fixed-base main EXE IAT slots for `RegisterClassA`
  (`0x007BE38C`) and `ImmGetCandidateListA` (`0x007BE06C`) as one prechecked
  transaction with rollback.  The accepted image must have base `0x00400000`,
  PE timestamp `0x65F707F0`, `SizeOfImage=0x00508000`, the expected loader
  import pointers, and the 16-byte code fingerprint at `0x007321F0`.
- `DllMain` only records its module and disables thread notifications.  Each of
  the four exported timer wrappers synchronously calls one shared `InitOnce`
  installer before forwarding to the real WINMM function, so PE validation,
  IAT writes, User32 calls, and logging all occur outside the loader lock.
- Static startup order establishes the no-race boundary for the supported EXE:
  `0x004B4B4E` calls timer init `0x0041B360`, which calls the proxy through
  `timeGetDevCaps` IAT at `0x0041B383` and `timeBeginPeriod` at `0x0041B393`.
  Only afterward does `0x004B4B6F` call window-object constructor
  `0x004BB4B0`, whose class/window path reaches `0x004BB516`,
  `0x007322E0`, and `0x0073243D`.  The first synchronous timer wrapper thus
  completes the IAT transaction before the first supported RegisterClass path.
- Wraps every main-module ANSI class whose original dispatcher is exactly
  `0x007321F0`; the dispatcher pointer is common and preserved once.  This is
  deliberately not a first-class-only heuristic.
- Logs the IME message number, `wParam`, and `lParam` to
  `hangul_ime_hook.log` next to the proxy DLL.
- Under a Korean layout, owns every finalized
  `WM_IME_COMPOSITION/GCS_RESULTSTR`.  It prechecks the entire result, maps
  supported precomposed Hangul, injects printable one-byte CP932/ASCII, and
  swallows the complete result on an unmapped syllable, jamo, Hanja, malformed
  data, or other high-bit/non-ASCII character.  No prefix or raw final result
  reaches the engine.
- As a fallback, on committed `WM_IME_CHAR`, maps a supported CP949 Hangul pair to the exact
  CP932 proxy carrier used by the existing FNL and feeds the carrier to the
  original ANSI window procedure as two `WM_CHAR` bytes.
- Treats fallback `WM_IME_CHAR` as CP949 first because this hook wraps an ANSI
  class; it uses a Unicode interpretation only if the window actually reports
  itself as Unicode.  This avoids confusing packed Wansung bytes such as
  `B7E1` with a numerically similar Unicode syllable.
- Swallows unsupported Hangul commits rather than passing invalid bytes into
  the CP932 game string path.
- Hooks `ImmGetCandidateListA` to return no candidates under a Korean keyboard
  layout.  It does not re-enter the IME with `NI_CLOSECANDIDATE`; candidate
  polling suppression is logged only on its first hit.
- Preserves the engine's internal IME state by routing `WM_IME_STARTCOMPOSITION`,
  interim `WM_IME_COMPOSITION`, `WM_IME_ENDCOMPOSITION`, and `WM_IME_NOTIFY`
  to the original dispatcher.  Only an owned final result and mapped fallback
  `WM_IME_CHAR` are consumed.  The duplicate guard survives END and resets at
  the next START so late `WM_IME_CHAR` delivery cannot insert twice.

## Build

Run `build.ps1`.  It generates `hangul_proxy_table.generated.h` from the pinned
compat-v2 proxy map, invokes the installed VS 2022 Build Tools x86 compiler, and
places the result in `build\winmm.dll`.  The DLL uses the static MSVC runtime so
it does not add a `VCRUNTIME140.dll` deployment requirement.

The build also compiles and runs `unit_harness.cpp`.  The generator-reported
row count is passed to the harness as an argument rather than compiled as a
fixed `1,520` assertion, allowing the table to expand.  The current build
checks all 1,520 rows (including `료`: CP949 `B7E1` to CP932 proxy `E853`),
loads the proxy from an explicit path, resolves exactly the four required
exports, and calls/balances the real WINMM timing APIs.  It does not launch the
game.

## Important limitations

- The hook has not been copied beside the game executable or runtime-tested.
- Candidate polling is intentionally disabled for a Korean layout, so Hanja
  candidate selection is out of scope.
- Only Hangul characters already present in the 1,524-entry project proxy map
  can be entered.  Unsupported Hangul is dropped as a complete commit.
- The startup-order proof is static evidence for the fingerprinted EXE, not an
  in-game observation.  Runtime logs must still confirm `iat_hooks_installed`
  before the first `register_class_a_wrapped` event.
- The RegisterClass hook deliberately recognizes only original WndProc
  `0x007321F0` and wraps every exact matching class.  Auxiliary classes sharing
  that dispatcher therefore also pass through the hook under a Korean layout.
- No save/load or whole-string name-replacement runtime behavior is proven by
  this build.  Those tests remain mandatory after the IME path itself works.
