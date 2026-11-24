# -*- coding: utf-8 -*-
"""Make publish_pace.py from mods_tab_20261015/publish_mods.py (read only): the same journaled install / restore transaction,
fixture and readiness, with the battle-pace payload (NightRemaster.ain only), evidence checks, contract and notes."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'mods_tab_20261015' / 'publish_mods.py').read_text('utf8')


def func(text, name, new):
    """Replace a top-level def (up to the next top-level def / class / section comment)."""
    m = re.search(r'\ndef %s\(.*?(?=\n\n\n(?:def |class |# -))' % re.escape(name), text, re.S)
    assert m, name
    return text[:m.start()] + '\n' + new.strip('\n') + text[m.end():]


def once(text, a, b):
    assert text.count(a) == 1, a[:80]
    return text.replace(a, b)


DOC = '''"""Claude Opus 5.5 (2026-10-16): install / restore of the battle-pace layer (user, 10-16: 「둘 다 고쳐 줘. 전투 중 화면 전환
대기는 전투 속도만큼 줄이고 이펙트 보지 않기에서는 건너뛰게, 경로 표시 잔상도 없애 줘.」), made from publish_mods.py (same journaled
transaction, same KRMenu scratch rule).

  python publish_pace.py --stage      check candidate/manifest.json against the built AIN (the payload is the AIN only)
  python publish_pace.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_pace.py --contract   write the Codex contract draft required_battle_pace_20261016.json
  python publish_pace.py --fixture    transaction fixture on disposable files under battle_pace_20261016/work (no runtime)
  python publish_pace.py --verify     read-only readiness check (hashes, native probe, scan, fixture, saved stacks, contracts)
  python publish_pace.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_pace.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_BP* layer). PACT/EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction as
publish_mods.py: PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present at
install time (battle_pace_20261016_preserved_by) + new required_battle_pace_20261016.json + latest_worked_translation.json +
progress.md note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back; --restore returns the
exact pre-install state.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import mdlib as L', 'import bplib as L')
for a, b in [('mods_tab_20261015', 'battle_pace_20261016'), ('MODS_TAB_20261015', 'BATTLE_PACE_20261016'), ('.mods-', '.pace-'),
             ('mods-copy.tmp', 'pace-copy.tmp'), ('publish_mods', 'publish_pace')]:
    src = src.replace(a, b)
src = once(src, "FILES = ['NightRemaster.ain', 'NightRemasterPact.afa']\nPACT_SRC = HERE / 'NightRemasterPact.afa'\n",
           "FILES = ['NightRemaster.ain']\n")
src = once(src, "READY = 'BATTLE_PACE_20261016_STATIC_NATIVE_PASS_NOT_INSTALLED'", "READY = 'BATTLE_PACE_20261016_STATIC_NATIVE_PASS_NOT_INSTALLED'")
a = src.index("MSG_TITLE_KO = ")
b = src.index('\n\n\ndef js(')
src = src[:a] + '''NO_RESTORE = ('Codex must never run publish_pace*.py --restore or otherwise remove the battle-pace layer: KR_BP* functions; 20 '
              'Ａ＿全表示 call sites of the battle scene and the encounter transitions (C_Transition::StartBattle / EndBattleOut / '
              'EndBattleIn, C_BattleEffect::RunAdvantage, C_EnemySetView@AppearEffect, C_BattleProgress@*, C_BattleTimerView@Pass, '
              'C_SceneBattle@DispEffect / Run) call KR_BPZen (no wait while the effects are hidden, KR_QuickActive; otherwise the time '
              'divided by KR_Speed); C_SceneSaveLoad@ExecAfterLoad calls KR_BPAfterLoad where it called KR_RateAfterLoad and '
              'C_SceneDungeon@SetMapId calls KR_BPFloorFade where it called N_Map::FadeDefault (both call the original first, then mark '
              'the route line dirty: flags 85/86 = -1, 89 = 1). It is user-requested: when a rebuild needs a clean base, rebase on the '
              'runtime that current.json points to and carry it forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_pace*.py --restore 를 실행하거나 전투 템포 층(KR_BP* 함수; 전투 장면 · 조우 전환의 Ａ＿全表示 호출 20곳 → '
                 'KR_BPZen(이펙트 보지 않기 중엔 대기 없음, 아니면 전투 속도로 나눔); C_SceneSaveLoad@ExecAfterLoad 의 KR_RateAfterLoad · '
                 'C_SceneDungeon@SetMapId 의 N_Map::FadeDefault 호출 → KR_BPAfterLoad · KR_BPFloorFade(원래 함수를 먼저 부른 뒤 경로 선을 '
                 '다시 그리게 표시))을 지우지 않는다. 사용자가 요청한 것이다: 깨끗한 기준이 필요하면 current.json 이 가리키는 실행본 위에서 '
                 '다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude battle-pace layer (2026-10-16, user request: battle screen transitions shortened by the battle speed and skipped while '
    'the effects are hidden; the route line left over from a save cleared). ' + NO_RESTORE + ' Payload: NightRemaster.ain only. '
    'KR_BP* functions appended; no original function relocated; no new global / struct member; 22 same-length CALLFUNC operand '
    'swaps. Story scripts, menus, the dungeon and event-battle entries keep calling Ａ＿全表示 with their original times. '
    'The auto-nav pins stay (index, address and every code byte): ' + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE +
    ' Every earlier contract stays in force.')''' + src[b:]

src = func(src, 'stage', '''
def stage():
    man = read(O / 'manifest.json')
    want = man['files']['NightRemaster.ain']['sha256']
    assert L.sha(O / 'NightRemaster.ain') == want, 'candidate AIN differs from its manifest: rebuild'
    assert man['pact_changed'] is False and set(man['files']) == set(FILES), man['files'].keys()
    return {n: man['files'][n]['sha256'] for n in FILES}
''')
src = func(src, 'probe_mods_ok', '''
def probe_pace_ok(p):
    return bool(p and p.get('passed') and p.get('user_save_folder_unchanged_all') and not p.get('problems'))
''')
src = func(src, 'draft_contract', '''
def draft_contract():
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    pm = read(L.EVID / 'probe_pace.json')
    assert pm.get('candidate_ain') == after['NightRemaster.ain'], 'rerun the probe summary for this candidate'
    scan_ = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    rc = read(L.WORK / 'resume_offset_check.json')
    assert rc['candidate_ain'] == after['NightRemaster.ain'] and not rc['problems'], 'rerun work/resume_offset_check.py'
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, code=man['pinned_functions'].get(name))
    still = {}
    for name in PINNED_NEW:
        fid = L.fid_of(nm, name)
        still[name] = dict(index=fid, address=nm['functions'][fid]['address'], code=man['pinned_functions'].get(name))
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    return dict(
        status='BATTLE_PACE_20261016_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files=after, candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False,
        ex_changed=False, fnl_changed=False, chart_changed=False, hook_changed=False,
        no_restore_rule=NO_RESTORE, added_functions=len(ids), added_function_names=sorted(ids),
        same_length_sites=man['same_length_sites'], message_box_sites=[], relocated_original_functions=[],
        zen_calls_left_alone=man['zen_calls_left_alone_total'],
        pinned_addresses=pinned, pinned_from_now_on=still,
        saved_stacks=dict(resume_saves=rc['stats']['resume_saves'], frames=rc['stats']['frames'],
                          frames_in_changed_functions=rc['stats'].get('frames_in_changed_functions', 0), problems=len(rc['problems']),
                          changed_functions_on_stacks=sorted({h['fn'] for h in rc['frames_in_changed_functions']}),
                          check=str(L.WORK / 'resume_offset_check.json'), check_sha256=L.sha(L.WORK / 'resume_offset_check.json'),
                          note='read-only check of the user\\'s saves: every saved frame keeps its crc (the AIN function table is '
                               'unchanged), no original function moved, no frame resumes at or inside a swapped instruction'),
        verification=dict(probe=pm, defender=scan_.get('status'), transaction_fixture=fx['status'] if fx else 'NOT_RUN'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='battle_pace_20261016_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)
''')
src = once(src, "self.note_title = note_title or '모드 탭 정리 · 메시지 상자 한국어 (Claude Opus 5.5; 오토 내비게이션 설치본 위)'",
           "self.note_title = note_title or '전투 화면 전환 템포 · 경로 표시 잔상 (Claude Opus 5.5; 모드 탭 설치본 위)'")
src = once(src, '''        for f in (L.EVID / 'probe').glob('*.png'):
            shutil.copy2(f, ev / 'source' / 'probe' / f.name)
        for n in ['probe_mods.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)''', '''        for f in (L.EVID / '그림').glob('*.png'):
            shutil.copy2(f, ev / 'source' / 'probe' / f.name)
        for n in ['probe_pace.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)''')
src = once(src, '''        for f in ctx.sources.glob('pact_18*.pactex'):
            shutil.copy2(f, ev / 'source' / f.name)
''', '')
src = once(src, '''        nm['next'] = ('User screen check: 옵션 → 모드 탭(구역 · 슬라이더 바 · 위쪽 버튼 줄)과 자동 회복 설정 쪽의 새 배치; 홈에서 옵션을 '
                      '열면 왼쪽 달성률 패널이 사라졌다가 닫으면 돌아오는지; 게임 종료 · 타이틀로 확인 창이 한국어인지.')''',
           '''        nm['next'] = ('User screen check: 전투 속도 3~5배에서 전투 화면 전환이 짧아졌는지, 「전투 이펙트 보지 않기」 전투가 빨리 끝나는지; '
                      '경로 표시를 끈 채 예전 던전 세이브를 불러오면 미니맵 점선이 없는지; 이야기 장면 전환은 그대로인지.')''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 전투 화면 전환(사용자 요청 10-16 「전투 중 화면 전환 대기는 전투 속도만큼 줄이고 이펙트 보지 않기에서는 건너뛰게」): "
                "전투 장면 · 조우 전환의 Ａ＿全表示 호출 20곳 → KR_BPZen. 이펙트 보지 않기로 도는 전투(KR_QuickActive)는 대기 0, 그 밖에는 "
                "전환 시간 ÷ 전투 속도(KR_Speed, 기본 = 원래 시간). 이야기 · 메뉴 · 던전 · 이벤트 전투 진입의 전환 120곳은 그대로.\\n"
                "- 경로 표시 잔상(「경로 표시 잔상도 없애 줘」): 불러오기 뒤(ExecAfterLoad 의 마지막 호출)와 층 진입(SetMapId 의 "
                "N_Map::FadeDefault)마다 경로 선을 다시 그리게 표시(85/86 = -1, 89 = 1) → 꺼져 있으면 저장 당시 선을 한 번 지움.\\n"
                "- AIN 만, 원본 함수 이전 0, 같은 길이 CALLFUNC 피연산자 22곳, 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 " + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_pace.py --restore.\\n")
''' + src[b:]
src = once(src, "full['battle_pace_20261016_overlay'] = dict(evidence=str(ev), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)",
           "full['battle_pace_20261016_overlay'] = dict(evidence=str(ev), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)")
# fixture: one payload file
src = once(src, '''    os.unlink(l / FILES[1])
    shared = f / 'shared_copy.afa'
    shutil.copy2(b / FILES[1], shared)
    os.link(shared, l / FILES[1])
    pair_apply(s, b, l, before, after)
    assert L.sha(shared) == before[FILES[1]], 'the swap wrote through a hard link\'''', '''    os.unlink(l / FILES[-1])
    shared = f / 'shared_copy.ain'
    shutil.copy2(b / FILES[-1], shared)
    os.link(shared, l / FILES[-1])
    pair_apply(s, b, l, before, after)
    assert L.sha(shared) == before[FILES[-1]], 'the swap wrote through a hard link\'''')
src = once(src, '''    ctx, rt, rec = fake_project(f, 'proj_pact_missing_in_recovery', FILES, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == ['NightRemasterPact.afa'] and rep['recovery_hashed'] == ['NightRemaster.ain']''',
           '''    ctx, rt, rec = fake_project(f, 'proj_ain_only', FILES, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == [] and rep['recovery_hashed'] == ['NightRemaster.ain']''')
# readiness: no PACT in the payload; the probe summary instead of probe_mods.json
src = once(src, '''    man = read(O / 'manifest.json')
    if 'NightRemasterPact.afa' not in man['files']:
        return False, dict(status='NOT_READY', issues=['the PACT is not staged into candidate/ (run --stage)'])
    after = {n: man['files'][n]['sha256'] for n in FILES}''', '''    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}''')
src = once(src, '''    if L.sha(PACT_SRC) != after['NightRemasterPact.afa']:
        issues.append('NightRemasterPact.afa differs from the staged PACT: rerun --stage')
''', '')
src = once(src, '''    pm = read(L.EVID / 'probe_mods.json') if (L.EVID / 'probe_mods.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or pm.get('candidate_pact') != after['NightRemasterPact.afa'] or not probe_mods_ok(pm):
        issues.append('native probe (probe_mods.py) missing, failing or for another candidate')''', '''    pm = read(L.EVID / 'probe_pace.json') if (L.EVID / 'probe_pace.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or not probe_pace_ok(pm):
        issues.append('native probe summary (증거/probe_pace.json) missing, failing or for another candidate')''')
src = once(src, "str(HERE.parent / 'autonav_20261015' / 'scan_autonav.ps1')", "str(HERE / 'scan_pace.ps1')")
assert 'probe_mods' not in src and 'PACT_SRC' not in src and 'mdlib' not in src, 'leftover Mods-layer checks'
(HERE / 'publish_pace.py').write_text(src, 'utf8')
print('ok', len(src.splitlines()), 'lines')
