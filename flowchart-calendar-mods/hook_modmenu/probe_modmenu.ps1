# Claude 2026-09-28: isolated probe of the mod-menu hook (diagnostic build) in the probe game copy.
# ASCII-only script (Korean text built from char codes) so Windows PowerShell 5.1 reads it correctly.
param(
    [string]$Root = 'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\hook_modmenu',
    [string]$Run = 'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\hook_chartmenu\probe\run'
)
$ErrorActionPreference = 'Continue'
$sig = @'
using System; using System.Runtime.InteropServices; using System.Text;
public class W6 {
 [DllImport("user32.dll")] public static extern IntPtr GetMenu(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetSubMenu(IntPtr m, int pos);
 [DllImport("user32.dll")] public static extern int GetMenuItemCount(IntPtr m);
 [DllImport("user32.dll")] public static extern uint GetMenuItemID(IntPtr m, int pos);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetMenuString(IntPtr m, uint id, StringBuilder s, int n, uint f);
 [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindowW(string cls, string title);
}
'@
Add-Type -TypeDefinition $sig
function K([int[]]$codes) { return [string]::Join('', ($codes | ForEach-Object { [char]$_ })) }
$modTitle = (K @(0xBAA8,0xB4DC)) + '(&M)'
$resetTitle = (K @(0xC804,0xCCB4)) + ' ' + (K @(0xB9AC,0xC14B))
$save = Join-Path $Run 'SaveData_ChartMenuProbe'
$menuDir = Join-Path $Run 'KRMenu'
$log = Join-Path $Run 'hangul_ime_hook.log'
$result = [ordered]@{}

function Launch() {
    $probeExe = (Join-Path $Run 'NightRemaster.exe')
    if (Get-Process -Name NightRemaster -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $probeExe }) { throw 'the probe game copy is already running' }
    $p = Start-Process -FilePath (Join-Path $Run 'NightRemaster.exe') -WorkingDirectory $Run -PassThru
    $h = [IntPtr]::Zero
    for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Milliseconds 500; $p.Refresh(); if ($p.MainWindowHandle -ne [IntPtr]::Zero -and $p.MainWindowTitle -like '*Remastered*') { $h = $p.MainWindowHandle; break } }
    if ($h -eq [IntPtr]::Zero) { Stop-Process -Id $p.Id -Force; throw 'no window' }
    Start-Sleep -Seconds 4
    return @($p, $h)
}
function MenuText($m, $i) { $sb = New-Object System.Text.StringBuilder 256; [void][W6]::GetMenuString($m, [uint32]$i, $sb, 256, 0x400); return $sb.ToString() }
function ReadReq() { $f = Join-Path $menuDir 'request.txt'; if (Test-Path $f) { return (Get-Content $f -Raw) } else { return $null } }
$pendingTitle = K @(0xBAA8,0xB4DC)
$script:pendingBoxes = 0
function ClosePendingBox() {
    # the hook shows a "mod" titled MessageBox when the game has not consumed the request within 2.5 s
    Start-Sleep -Seconds 3
    $box = [W6]::FindWindowW('#32770', $pendingTitle)
    if ($box -ne [IntPtr]::Zero) { $script:pendingBoxes++; [void][W6]::PostMessage($box, 0x111, [IntPtr]1, [IntPtr]::Zero); Start-Sleep -Milliseconds 500; return $true }
    return $false
}
function GlobalFiles() { Get-ChildItem $save -File | Where-Object { $_.Name -match '^(NightRAF.*\.asd|NightRMsgSkip\.msk|CommonGameData\.asd|YoruKR_HomeRate\.dat)$' } | Select-Object -ExpandProperty Name | Sort-Object }

# --- prepare ---
Copy-Item (Join-Path $Root 'build_diagnostic\winmm.dll') (Join-Path $Run 'winmm.dll') -Force
if (Test-Path $log) { Move-Item $log ($log + '.old3') -Force }
if (Test-Path $menuDir) { Get-ChildItem $menuDir -File | Remove-Item -Force }
$result.global_files_before = @(GlobalFiles)

# --- run 1: menu + requests ---
$lp = Launch; $p = $lp[0]; $h = $lp[1]
$bar = [W6]::GetMenu($h)
# no WM_INITMENU: the popup must already be there right after the window appeared
$result.top_items_before_initmenu = [W6]::GetMenuItemCount($bar)
$top = [W6]::GetMenuItemCount($bar)
$tops = @(); for ($i = 0; $i -lt $top; $i++) { $tops += (MenuText $bar $i) }
$result.top_items = $tops
$modIdx = -1; for ($i = 0; $i -lt $top; $i++) { if ($tops[$i] -eq $modTitle -or $tops[$i] -like '*(&M)') { $modIdx = $i } }
$result.mod_index = $modIdx
$ids = @()
if ($modIdx -ge 0) {
    $pop = [W6]::GetSubMenu($bar, $modIdx); $n = [W6]::GetMenuItemCount($pop)
    $items = @(); for ($j = 0; $j -lt $n; $j++) { $id = [W6]::GetMenuItemID($pop, $j); $items += ('{0:X4}:{1}' -f $id, (MenuText $pop $j)); if ($id -ge 0x7E10 -and $id -le 0x7EFF) { $ids += $id } }
    $result.mod_items = $items
    $help = [W6]::GetSubMenu($bar, $top - 1); $result.help_items = [W6]::GetMenuItemCount($help)
}
$result.command_ids = ($ids | ForEach-Object { '{0:X4}' -f $_ })
if ($ids.Count -eq 5) {
    [void][W6]::PostMessage($h, 0x111, [IntPtr]$ids[0], [IntPtr]::Zero); Start-Sleep -Seconds 1; $result.req_chart = ReadReq; $result.pending_box_chart = ClosePendingBox
    [void][W6]::PostMessage($h, 0x111, [IntPtr]$ids[1], [IntPtr]::Zero); Start-Sleep -Seconds 1; $result.req_unlock = ReadReq; [void](ClosePendingBox)
    [void][W6]::PostMessage($h, 0x111, [IntPtr]$ids[2], [IntPtr]::Zero); Start-Sleep -Seconds 1; $result.req_revert = ReadReq; [void](ClosePendingBox)
    # reset_all -> MessageBox -> No
    [void][W6]::PostMessage($h, 0x111, [IntPtr]$ids[3], [IntPtr]::Zero); Start-Sleep -Seconds 2
    $box = [W6]::FindWindowW('#32770', $resetTitle); $result.reset_box_found = ($box -ne [IntPtr]::Zero)
    if ($box -ne [IntPtr]::Zero) { [void][W6]::PostMessage($box, 0x111, [IntPtr]7, [IntPtr]::Zero); Start-Sleep -Seconds 1 }
    $result.req_after_reset_no = ReadReq; $result.pending_box_after_no = ClosePendingBox
    # reset_all -> Yes
    [void][W6]::PostMessage($h, 0x111, [IntPtr]$ids[3], [IntPtr]::Zero); Start-Sleep -Seconds 2
    $box = [W6]::FindWindowW('#32770', $resetTitle)
    if ($box -ne [IntPtr]::Zero) { [void][W6]::PostMessage($box, 0x111, [IntPtr]6, [IntPtr]::Zero); Start-Sleep -Seconds 1 }
    $result.req_after_reset_yes = ReadReq; [void](ClosePendingBox)
    $result.pending_boxes_total = $script:pendingBoxes
}
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2
$result.log_run1 = @(); if (Test-Path $log) { $result.log_run1 = @(Get-Content $log | Select-String -Pattern 'mod_|iat_hooks' | ForEach-Object { $_.Line.Substring(0, [Math]::Min(150, $_.Line.Length)) }) }

# --- run 2: startup reset (marker + reset.req) ---
if ($env:MODMENU_SKIP_MAINTENANCE -eq '1') { $result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Root 'probe_result_run1.json') -Encoding utf8; $result | ConvertTo-Json -Depth 4; exit 0 }
Get-ChildItem $menuDir -File | Remove-Item -Force
[IO.File]::WriteAllText((Join-Path $save 'YoruKR_reset.marker'), "reset`r`n")
[IO.File]::WriteAllText((Join-Path $menuDir 'reset.req'), "reset`r`n")
$lp = Launch; $p = $lp[0]; Start-Sleep -Seconds 3; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2
$result.reset_result = (Get-Content (Join-Path $menuDir 'last_result.txt') -Raw -ErrorAction SilentlyContinue)
$result.global_files_after_reset = @(GlobalFiles)
$bk = Get-ChildItem (Join-Path $save 'Backup') -Directory -Filter 'KR_reset_*' | Sort-Object Name | Select-Object -Last 1
$result.backup_folder = $(if ($bk) { $bk.Name } else { $null })
$result.backup_files = $(if ($bk) { @(Get-ChildItem $bk.FullName -File | Select-Object -ExpandProperty Name | Sort-Object) } else { @() })
$result.marker_left = Test-Path (Join-Path $save 'YoruKR_reset.marker'); $result.req_left = Test-Path (Join-Path $menuDir 'reset.req')

# --- run 3: startup restore ---
Remove-Item (Join-Path $menuDir 'last_result.txt') -Force -ErrorAction SilentlyContinue
[IO.File]::WriteAllText((Join-Path $save 'YoruKR_reset.marker'), "restore`r`n")
[IO.File]::WriteAllText((Join-Path $menuDir 'restore.req'), "restore`r`n")
$lp = Launch; $p = $lp[0]; Start-Sleep -Seconds 3; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2
$result.restore_result = (Get-Content (Join-Path $menuDir 'last_result.txt') -Raw -ErrorAction SilentlyContinue)
$result.global_files_after_restore = @(GlobalFiles)
$kp = Get-ChildItem (Join-Path $save 'Backup') -Directory -Filter 'KR_before_restore_*' | Sort-Object Name | Select-Object -Last 1
$result.before_restore_folder = $(if ($kp) { $kp.Name } else { $null })
$result.marker_left_after_restore = Test-Path (Join-Path $save 'YoruKR_reset.marker')
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Root 'probe_result.json') -Encoding utf8
$result | ConvertTo-Json -Depth 4
