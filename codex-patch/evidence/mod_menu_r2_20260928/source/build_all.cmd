@echo off
rem Claude 2026-09-27: build the chart-menu hook in both profiles (no pwsh on this machine).
rem usage: build_all.cmd <hangul_rows>
setlocal
if "%~1"=="" (
  echo usage: build_all.cmd ^<hangul_rows^>
  exit /b 2
)
set "HANGUL_EXPECTED_ROWS=%~1"
set "ROOT=%~dp0"
for %%P in (diagnostic release) do (
  call :one %%P
  if errorlevel 1 exit /b 1
)
echo ALL_BUILDS_OK
exit /b 0

:one
set "PROFILE=%~1"
set "IME_HOOK_BUILD_DIR=%ROOT%build_%PROFILE%"
if "%PROFILE%"=="diagnostic" (set "IME_HOOK_DIAGNOSTICS=1") else (set "IME_HOOK_DIAGNOSTICS=0")
if not exist "%IME_HOOK_BUILD_DIR%" mkdir "%IME_HOOK_BUILD_DIR%"
echo === %PROFILE% -^> %IME_HOOK_BUILD_DIR%
cmd.exe /c ""%ROOT%src\build_x86.cmd"" > "%IME_HOOK_BUILD_DIR%\build.log" 2>&1
set "CODE=%ERRORLEVEL%"
echo %PROFILE% exit=%CODE%
if not "%CODE%"=="0" (
  findstr /i /c:"error" /c:"warning" "%IME_HOOK_BUILD_DIR%\build.log"
  exit /b 1
)
exit /b 0
