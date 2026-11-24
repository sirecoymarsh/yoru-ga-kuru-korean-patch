# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-16): native effect probes for the Mods page options inside dungeons and battles.

User (10-15 night): 「모드 옵션 … 모든 기능이 제대로 동작하나 체크좀」. The Mods-tab layer (mods_tab_20261015) proved every
control reaches its setting (37/37) but nobody had seen the options act inside a dungeon or a battle. This script runs the
candidate AIN + PACT of that layer (read only) in an isolated copy, resumed from a dungeon save copied out of the user's save
folder (read only), muted, hidden, with the user's input cut off, and logs what each option does there.

  python probe_effects.py SCENARIO [--save NightR36.asd] [--timeout 600]

Everything is written under mods_effects_20261016/ on P: (probe/run = isolated runtime copy; big assets hard-linked and never
written; saves inside run/). The launcher is the one of probe_mods.py (09-24 probe_autonav lineage): hidden window,
MessageBoxA and the VM error handler break-pointed, nothing sent to the window.
The probe AIN = the candidate + probe-only code (never shipped): the dungeon move-key read (C_SceneDungeon@CheckMoveKey) is
replaced by the scenario stage machine, which walks the party by returning a direction; battle begin/end, the per-frame
battle update, the enhanced-auto and auto-item calls are wrapped by loggers; waits outside the live list end the run.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import argparse, datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent                       # ...\ingame\mods_effects_20261016
MT = HERE.parent / 'mods_tab_20261015'                       # read only (candidate, meta, mdlib)
sys.path.insert(0, str(MT))
import mdlib as L

O = MT / 'candidate'
CAND_META = MT / 'work' / 'build' / 'candidate_meta.json'
CAND_RAW = MT / 'work' / 'build' / 'candidate_raw_code.jam'
LAYER = 'mods'
BP = HERE.parent / 'battle_pace_20261016'      # the battle-pace candidate (10-16), selected with --layer pace
PACT = MT / 'NightRemasterPact.afa'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
EVID = HERE / '증거'
TMP = HERE / 'tmp'
BOOT = 'NightRemasterEffectsProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
SAVE_TYPE = 2
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>',
              'C_SceneDungeon@Run')
for d in (PROBE, EVID, TMP):
    d.mkdir(parents=True, exist_ok=True)


_base_env = L.env


def env():
    """alice and the game keep their temp files in this folder (P:)."""
    e = _base_env()
    e['TEMP'] = e['TMP'] = str(TMP)
    return e


L.env = env   # mdlib.cmd looks env up at call time


MUTE_JAF = '''
void KR_DiagnosticMute() {
    if (!KiwiSoundEngine.SetMixerMute(0, true) ||
        !config::detail::GetMasterMute()) {
        system.Exit(91);
        return;
    }
}
'''

from probe_jaf import PROBE_JAF, BRIDGES, SCENARIOS, scenario_steps


def ids_of(m):
    f = lambda n: L.fid_of(m, n)
    first = lambda n: min(x['index'] for x in m['functions'] if L.raw_symbol(m, x['index']) == n)
    return dict(
        DUNGEON_ID=first('C_SceneDungeon@NowDungeonId::get'), MAP_NO=first('C_MapInfo@NowMapNo::get'),
        CELL_AT=f('C_MapInfo@GetCellInfoFromGridXY'),
        AB_ID=f('C_Ability@GetID'), AB_LV=f('C_Ability@GetLevel'), AB_HP=f('C_Ability@GetCurHP'), AB_MHP=f('C_Ability@GetMaxHPRevised'),
        AB_EXP=f('C_Ability@GetExp'), AB_TR=f('C_Ability@GetTraining'), AB_MONEY=f('C_Ability@GetMoney'),
        FL_MAPID=first('C_GameFlags@NowMapId::get'), FL_X=first('C_GameFlags@NowMapX::get'), FL_Y=first('C_GameFlags@NowMapY::get'),
        C_OBJ=first('C_MapCellInfo@ObjectId::get'), C_SUB=first('C_MapCellInfo@ObjectSubId::get'), C_REMOVED=first('C_MapCellInfo@IsRemoved::get'),
        C_SHOW=first('C_MapCellInfo@IsShowObject::get'), C_SEEN=first('C_MapCellInfo@IsSeen::get'), C_EV=first('C_MapCellInfo@IsEventDungeon::get'),
        C_WALK=f('C_MapCellInfo@PossibleToWalk'), C_STEPPED=first('C_MapCellInfo@IsSteppedOn::get'),
        FL_BRESULT=first('C_GameFlags@BattleResult::get'), FL_BTIME=first('C_GameFlags@BattlePassedTime::get'),
    )


def build_probe(key, work, scen):
    src = O / 'NightRemaster.ain'
    m = L.read_meta(CAND_META)
    nums = ids_of(m)
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@STEPS@@', scenario_steps(SCENARIOS[scen])).replace('@@KEY@@', key).replace('@@SCEN@@', scen)
    jaf = jaf.replace('@@NOSHOTS@@', '1' if scen == 'story' else '0')
    for k, v in nums.items():
        jaf = jaf.replace('@@' + k + '@@', str(v))
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    jaf = L.jaf_literal_encode(jaf)
    work.mkdir(parents=True, exist_ok=True)
    (work / 'probe.jaf').write_text(jaf, 'utf8')
    decl = work / 'probe_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'probe.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'probe_declared_meta.json', decl)
    dm = L.read_meta(work / 'probe_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    for g in added:
        if g['name'] in BRIDGES:
            body = BRIDGES[g['name']].format(**nums)
            patch.append(f"FUNC {g['index']}\n{body}ENDFUNC {g['name']}\n")
            continue
        path = work / f"probe_{g['index']}.jam"
        L.cmd('ain', 'dump', '--function', g['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), g['name']))
    for owner, call in PREPENDS:
        fid = L.fid_of(m, owner)
        path = work / f'original_{fid}.jam'
        L.cmd('ain', 'dump', '--function', owner, '-o', path, src)
        code = call if call.startswith('\t') else f'\tCALLFUNC {call}\n'
        patch.append(L.begin(L.clean(path.read_text('utf8'), owner), code))
    # Ａ＿全表示(effect, ms): the same body, with the requested transition time counted first (probe only)
    zen = L.fid_of(m, 'Ａ＿全表示')
    patch.append(f"FUNC {zen}\n\tPUSHLOCALPAGE\n\tPUSH 1\n\tX_REF 1\n\tCALLFUNC KR_PBTrans\n"
                 "\tPUSHLOCALPAGE\n\tPUSH 0\n\tX_REF 1\n\tPUSHLOCALPAGE\n\tPUSH 1\n\tX_REF 1\n\tPUSHGLOBALPAGE\n\tPUSH 176\n\tX_REF 1\n"
                 "\tPUSHGLOBALPAGE\n\tPUSH 177\n\tX_REF 1\n\tPUSH 1\n\tCALLFUNC view::detail::画面更新\n\tRETURN\nENDFUNC Ａ＿全表示\n")
    cmk = L.fid_of(m, 'C_SceneDungeon@CheckMoveKey')
    patch.append(f"FUNC {cmk}\n\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_PETick\n\tRETURN\nENDFUNC C_SceneDungeon@CheckMoveKey\n")
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    RUN.mkdir(parents=True, exist_ok=True)
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_PEMain'])
    raw_code = CAND_RAW

    def swap(owner, old, new, expect=1):
        fid = L.fid_of(m, owner)
        oldid = L.fid_of(m, old)
        newid = ids[new] if new in ids else L.fid_of(m, new)
        ops = L.region_ops(raw_code, m, fid)
        key2 = f'CALLFUNC 0x{oldid:x}'
        hits = [i for i, (_, op) in enumerate(ops) if op == key2]
        assert len(hits) == expect, (owner, old, len(hits))
        for h in hits:
            ad = ops[h][0]
            assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, oldid), (owner, hex(ad))
            struct.pack_into('<Hi', raw, 16 + ad, 0x30, newid)
        return dict(owner=owner, old=old, new=new, sites=len(hits))
    sites = []
    for owner, old, new, n in SWAPS:
        sites.append(swap(owner, old, new, n))
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(raw_code)
    waits = []
    for g in m['functions']:
        name = L.raw_symbol(m, g['index'])
        for v in [v for v in vers.get(g['index'], []) if v['start'] == g['address']]:
            for ad, op in v['ops']:
                if op != f'CALLFUNC 0x{wait:x}':
                    continue
                assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, wait)
                if name in LIVE_WAITS:
                    waits.append((name, 'live'))
                    continue
                target = ids['KR_PEMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_PEWaitExit']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target)
                waits.append((name, 'message click-through' if target == ids['KR_PEMsgWait'] else 'exit'))
    live = sorted(n for n, k in waits if k == 'live')
    assert live == sorted(LIVE_WAITS), live
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(scenario=scen, sites=sites, waits=len(waits), probe_sha256=L.sha(out), ids=nums)


# probe-only body prepends (none of these functions is on the NightR36 resume stack)
PREPENDS = [('C_SelectDialog@_Update', 'KR_PEDlgTick'), ('AFL_View_Update', 'KR_PEFrame'),
            ('C_SceneDungeon@Trap', 'KR_PBTrap'), ('L_Dungeon::RelieveTrap', 'KR_PBRelieve'),
            ('C_SceneBattle@_Update', '\t.LOCALREF time\n\t.LOCALREF scaledTime\n\tCALLFUNC KR_PBUpdArgs\n'),
            ('KR_SweepReport', '\t.LOCALREF txt\n\tA_REF\n\tCALLFUNC KR_PBSweepText\n'),
            ('C_BattleProgress@ChangePlayerWeapon', '\t.LOCALREF memIdx\n\tCALLFUNC KR_PBChangeWeapon\n')]
# probe-only same-length CALLFUNC operand swaps: the wrapper logs and calls the original
SWAPS = [('C_SceneBattle@Run', 'KR_BeginQuick', 'KR_PBBegin', 1), ('C_SceneBattle@Run', 'KR_EndQuick', 'KR_PBEnd', 1),
         ('C_BattleProgress@SetFriendActionAuto', 'KR_SmartRun', 'KR_PBSmart', 1),
         ('C_BattleProgress@CheckAction', 'KR_ItemsTry', 'KR_PBItems', 2),
         ('KR_NoticeInstant', 'KR_NoticeShow', 'KR_PBNoticeShow', 1),
         ('KR_T8NoticeInstant', 'KR_T8TrapNotice', 'KR_PBTrapNotice', 1),
         ('C_SceneDungeon@StepedOnCell', '■シンプルダイアログ', 'KR_PBSimple', 2),
         ('C_SceneDungeon@Run', 'KR_SweepExecute', 'KR_PBSweep', 1),
         # wait-for-cancel screens: the probe advances them through the auto-explore hook site (input is cut off)
         ('C_BattleResultView@Run', 'KR_ExploreResultEnter', 'KR_PBResultEnter', 1),
         ('C_MessageDialog@Run', 'KR_ExploreLevelEnter', 'KR_PBMsgDlgEnter', 1),
         ('L_BattleIncome::Settle', 'L_CasualMode::CalcExp', 'KR_PBCalcExp', 1),
         ('L_BattleIncome::Settle', 'L_CasualMode::CalcTrainging', 'KR_PBCalcTr', 1),
         ('L_BattleIncome::Settle', 'L_CasualMode::CalcMoney', 'KR_PBCalcMoney', 1)]


def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    for name in ['NightRemasterPact.afa', BOOT + 'Pact.afa']:
        shutil.copy2(PACT, RUN / name)
    for name in ['NightRemasterEX.ex', BOOT + 'EX.ex']:
        shutil.copy2(rt / 'NightRemasterEX.ex', RUN / name)
    for n in ['NightRemasterCG.afa', 'NightRemasterFont.fnl', 'NightRemasterSound.afa', 'NightRemasterVoice.afa']:
        for name in [n, n.replace('NightRemaster', BOOT, 1)]:
            t = RUN / name
            if not t.exists():
                os.link(rt / n, t)
            assert os.path.samefile(t, rt / n)
    if not (RUN / 'Movie').exists():
        (RUN / 'Movie').mkdir()
        for f in (rt / 'Movie').iterdir():
            os.link(f, RUN / 'Movie' / f.name)
    ini = (rt / 'AliceStart.ini').read_bytes()
    ini = re.sub(rb'BootName\t= "NightRemaster"', ('BootName\t= "' + BOOT + '"').encode(), ini)
    assert BOOT.encode() in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    return rt


def set_savefolder(savename):
    ini = (RUN / 'AliceStart.ini').read_bytes()
    folder = b'SaveFolder\t= "' + savename.encode('cp932') + b'"'
    ini = re.sub(rb'SaveFolder\t= "[^"]*"', lambda z: folder, ini)
    assert folder in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    (RUN / 'InstallInfo').mkdir(exist_ok=True)
    (RUN / 'InstallInfo' / 'SaveFolderSetting.ini').write_bytes(b'SFSF' + struct.pack('<ii', 0, SAVE_TYPE))
    for n in ['claude_effects.txt', 'claude_effects_save.txt']:
        if (RUN / n).exists():
            (RUN / n).unlink()
    for b in RUN.glob('pe_*.bmp'):
        b.unlink()


# ---- the 09-24 probe launcher (as probe_mods.py): hidden window, MessageBoxA and the VM error handler break-pointed
K = C.WinDLL('kernel32', use_last_error=True)
K.WaitForDebugEvent.argtypes = [C.c_void_p, W.DWORD]
K.ContinueDebugEvent.argtypes = [W.DWORD, W.DWORD, W.DWORD]
K.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
K.WriteProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
K.VirtualProtectEx.argtypes = [W.HANDLE, C.c_void_p, C.c_size_t, W.DWORD, C.POINTER(W.DWORD)]
K.OpenThread.argtypes = [W.DWORD, W.BOOL, W.DWORD]
K.OpenThread.restype = W.HANDLE
K.Wow64GetThreadContext.argtypes = [W.HANDLE, C.c_void_p]
K.CloseHandle.argtypes = [W.HANDLE]
K.TerminateProcess.argtypes = [W.HANDLE, W.UINT]


class Context(C.Structure):
    _fields_ = ([(n, W.DWORD) for n in 'ContextFlags Dr0 Dr1 Dr2 Dr3 Dr6 Dr7'.split()] + [('FloatSave', C.c_byte * 112)]
                + [(n, W.DWORD) for n in 'SegGs SegFs SegEs SegDs Edi Esi Ebx Edx Ecx Eax Ebp Eip SegCs EFlags Esp SegSs'.split()]
                + [('ExtendedRegisters', C.c_byte * 512)])


def launch(timeout=900):
    import pefile, win32process
    exe = RUN / 'NightRemaster.exe'
    data = exe.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXE_SHA
    pe = pefile.PE(data=data)
    imp = next(x.address for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name == b'MessageBoxA')
    needle = b'\xff\x15' + struct.pack('<I', imp)
    sites = [0x6696f0 - 0x400000]
    off = 0
    while (off := data.find(needle, off)) >= 0:
        sites.append(pe.get_rva_from_offset(off))
        off += 1
    startup = win32process.STARTUPINFO()
    startup.dwFlags = 1
    startup.wShowWindow = 0
    hp, ht, pid, tid = win32process.CreateProcess(str(exe), None, None, None, False, 2, env(), str(RUN), startup)
    handle = int(hp)
    result = {'pid': pid, 'ain_sha256': L.sha(RUN / 'NightRemaster.ain'), 'events': []}

    def read(addr, n):
        buf = C.create_string_buffer(n)
        got = C.c_size_t()
        if not K.ReadProcessMemory(handle, addr, buf, n, C.byref(got)):
            raise C.WinError(C.get_last_error())
        return buf.raw[:got.value]

    def cstr(addr):
        out = bytearray()
        for n in range(8192):
            v = read(addr + n, 1)
            if v == b'\0':
                return bytes(out)
            out += v
        return bytes(out)
    try:
        bp = {}
        base = 0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            event = C.create_string_buffer(200)
            if not K.WaitForDebugEvent(event, 1000):
                continue
            raw = event.raw
            code, epid, etid = struct.unpack_from('<III', raw)
            status = 0x10002
            if code == 3:
                base = struct.unpack_from('<Q', raw, 40)[0]
                for rva in sites:
                    addr = base + rva
                    bp[addr] = read(addr, 1)
                    old = W.DWORD()
                    num = C.c_size_t()
                    if not K.VirtualProtectEx(handle, addr, 1, 0x40, C.byref(old)):
                        raise C.WinError(C.get_last_error())
                    if not K.WriteProcessMemory(handle, addr, b'\xcc', 1, C.byref(num)):
                        raise C.WinError(C.get_last_error())
                    tmp = W.DWORD()
                    K.VirtualProtectEx(handle, addr, 1, old.value, C.byref(tmp))
            elif code == 1:
                exc = struct.unpack_from('<I', raw, 16)[0]
                addr = struct.unpack_from('<Q', raw, 32)[0]
                if exc in (0x80000003, 0x4000001f) and addr in bp:
                    thread = K.OpenThread(0x58, False, etid)
                    try:
                        ctx = Context()
                        ctx.ContextFlags = 0x10007
                        if not K.Wow64GetThreadContext(thread, C.byref(ctx)):
                            raise C.WinError(C.get_last_error())
                        if addr == base + 0x6696f0 - 0x400000:
                            ret, op, msg = struct.unpack('<III', read(ctx.Esp, 12))
                            buf = read(msg, 24)
                            length, capacity = struct.unpack_from('<II', buf, 16)
                            ptr = struct.unpack_from('<I', buf)[0] if capacity >= 16 else msg
                            result['vm_error'] = {'command': cstr(op).decode('cp932', 'replace'), 'message': read(ptr, min(length, 8192)).decode('cp932', 'replace')}
                        else:
                            args = struct.unpack('<IIII', read(ctx.Esp, 16))
                            t = cstr(args[1])
                            result['message'] = {'cp932': t.decode('cp932', 'replace'), 'cp949': t.decode('cp949', 'replace'), 'hex': t.hex()}
                    finally:
                        K.CloseHandle(thread)
                    K.TerminateProcess(handle, 99)
                    K.ContinueDebugEvent(epid, etid, status)
                    break
                if exc not in (0x80000003, 0x4000001f):
                    result['events'].append({'exception': hex(exc), 'address': hex(addr)})
                    status = 0x80010001
            elif code == 5:
                result['exit_code'] = struct.unpack_from('<I', raw, 16)[0]
                K.ContinueDebugEvent(epid, etid, status)
                break
            K.ContinueDebugEvent(epid, etid, status)
        else:
            result['timeout'] = True
    finally:
        K.TerminateProcess(handle, 99)
    return result


def user_state():
    return {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}


def collect_shots(tag):
    from PIL import Image
    dest = EVID / 'shots' / tag
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('pe_*.bmp')):
        png = dest / (b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    return shots


def run(scen, save, timeout):
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    tag = f'{scen}_{stamp}' if LAYER == 'mods' else f'{LAYER}_{scen}_{stamp}'
    before = user_state()
    setup_folder()
    key = L.save_records(L.SAVES / save)['key']
    info = build_probe(key, PROBE / 'work', scen)
    savename = f'SaveData_Effects_{tag}'
    savedir = RUN / savename
    set_savefolder(savename)
    savedir.mkdir(parents=True)
    for n in COPY_GLOBAL:
        if (L.SAVES / n).exists():
            shutil.copy2(L.SAVES / n, savedir / n)
    shutil.copy2(L.SAVES / save, savedir / save)
    (RUN / 'claude_effects_save.txt').write_bytes(save.encode('cp932'))
    t0 = time.time()
    result = launch(timeout=timeout)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_effects.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['shots'] = collect_shots(tag)
    result.update(scenario=scen, save=save, save_folder=str(savedir), probe=info, candidate_ain=L.sha(O / 'NightRemaster.ain'), candidate_pact=L.sha(PACT), layer=LAYER)
    result['fails'] = [x for x in result['log'] if x.startswith('FAIL ')]
    result['oks'] = len([x for x in result['log'] if x.startswith('OK ')])
    result['user_save_folder_unchanged'] = before == user_state()
    (EVID / 'runs').mkdir(parents=True, exist_ok=True)
    L.writej(EVID / 'runs' / f'{tag}.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(result['log'][-150:]))
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('scenario')
    ap.add_argument('--save', default='NightR36.asd')
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--layer', choices=['mods', 'pace'], default='mods')
    a = ap.parse_args()
    if a.layer == 'pace':
        O, CAND_META, CAND_RAW, LAYER = BP / 'candidate', BP / 'work' / 'build' / 'candidate_meta.json', BP / 'work' / 'build' / 'candidate_raw_code.jam', 'pace'
    run(a.scenario, a.save, a.timeout)
