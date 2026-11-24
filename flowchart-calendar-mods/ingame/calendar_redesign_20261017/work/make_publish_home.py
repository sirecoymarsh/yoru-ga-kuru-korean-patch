# -*- coding: utf-8 -*-
"""Make publish_home.py from mods_tab_20261015/publish_mods.py (read only): the same journaled install / restore transaction,
fixture and readiness for two payload files, with the home-panel payload (AIN + PACT entry 177), evidence checks, contract and
notes. Stage 1 of the calendar / completion-rate redesign (2026-10-17)."""
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


DOC = '''"""Claude Opus 5.5 (2026-10-17): install / restore of the home 달성률 panel redesign, stage 1 (user, 10-17: 달성률 「텍스트만
있어서 정보 파악이 느려」 · 숫자 기준이 섞임 · 이름 누르는 창; mockup approved 「왜 이리 멋져? 좋아 가자」), made from
publish_mods.py (same journaled transaction, same KRMenu scratch rule).

  python publish_home.py --stage      check candidate/manifest.json against the built AIN and PACT (both built into candidate/)
  python publish_home.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_home.py --contract   write the Codex contract draft required_home_panel_20261017.json
  python publish_home.py --fixture    transaction fixture on disposable files under calendar_redesign_20261017/work (no runtime)
  python publish_home.py --verify     read-only readiness check (hashes, native probe, scan, fixture, saved stacks, contracts)
  python publish_home.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_home.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_HV* layer) + NightRemasterPact.afa (entry 177 Game/Scenes/Common/AddArea.pactex: the KR_HomeRate
group gets the KR_HR_* parts). EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction as publish_mods.py:
PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present at install time
(home_panel_20261017_preserved_by) + new required_home_panel_20261017.json + latest_worked_translation.json + progress.md note ->
exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back; --restore returns the exact pre-install state.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import mdlib as L', 'import hvlib as L')
for a, b in [('mods_tab_20261015', 'home_panel_20261017'), ('MODS_TAB_20261015', 'HOME_PANEL_20261017'), ('.mods-', '.home-'),
             ('mods-copy.tmp', 'home-copy.tmp'), ('publish_mods', 'publish_home')]:
    src = src.replace(a, b)
src = once(src, "PACT_SRC = HERE / 'NightRemasterPact.afa'\n", "PACT_SRC = HERE / 'candidate' / 'NightRemasterPact.afa'\nPACT_EVID = HERE / 'work' / 'pact' / 'build_evidence.json'\n")
a = src.index("MSG_TITLE_KO = ")
b = src.index('\n\n\ndef js(')
src = src[:a] + '''NO_RESTORE = ('Codex must never run publish_home*.py --restore or otherwise remove the home-panel layer: KR_HV* functions; '
              'KR_RateRender calls KR_HVText where it called KR_RateText and KR_HVSetText where it called Ｐ＿テキスト設定 (the body '
              'text part KR_HomeRateBody is hidden and keeps a change key; the panel is drawn on the KR_HR_* parts); '
              'KR_T8HomeMenuOpen / KR_T8HomeMenuClose call KR_HVClickable where they called KR_T8HomeClickable; KR_T8HomeClick calls '
              'KR_HVRow where it called KR_T8HomeRow; KR_T8HomeMenuClose calls KR_HVPick where it called KR_T8CharMissingPage (the '
              'calendar button opens the event calendar through KR_CDoHome). PACT 177 Game/Scenes/Common/AddArea.pactex: the '
              'KR_HomeRate group keeps KR_HomeRate / KR_HomeRateTitle / KR_HomeRateBody and gains the KR_HR_* parts. It is '
              'user-requested: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry it '
              'forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_home*.py --restore 를 실행하거나 본거지 달성률 패널 층(KR_HV* 함수; KR_RateRender 의 KR_RateText · '
                 'Ｐ＿テキスト設定 호출 → KR_HVText · KR_HVSetText(본문 글 부품은 숨기고 변경 표식만 둔다, 패널은 KR_HR_* 부품에 그린다); '
                 'KR_T8HomeMenuOpen · Close 의 KR_T8HomeClickable → KR_HVClickable; KR_T8HomeClick 의 KR_T8HomeRow → KR_HVRow; '
                 'KR_T8HomeMenuClose 의 KR_T8CharMissingPage → KR_HVPick(캘린더 단추는 KR_CDoHome 으로 이벤트 캘린더를 연다); '
                 'PACT 177 AddArea 의 KR_HR_* 부품)을 지우지 않는다. 사용자가 요청한 것이다: 깨끗한 기준이 필요하면 current.json 이 '
                 '가리키는 실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude home 달성률 panel layer (2026-10-17, user request: the text-only panel was slow to read, its numbers mixed this save '
    'and all saves, the character names did not look clickable). ' + NO_RESTORE + ' Payload: NightRemaster.ain + '
    'NightRemasterPact.afa (entry 177 only). KR_HV* functions appended; no original function relocated; no new global / struct '
    'member; 6 same-length CALLFUNC operand swaps. Numbers keep the old panel\\'s sources and totals (this save: KR_PlayerEventCount '
    '/ 1,043, KR_T8CharEvents / KR_T8CharTotal; all saves: read 74,966 · CG 60 · 회상 66 · endings 5). The rate overlay '
    '(KR_RateRender / KR_RateTick) still decides when the panel shows; the calendar button shows only while the home top menu '
    'waits. Later edits of entry 177 start from the installed entry. The auto-nav pins stay (index, address and every code '
    'byte): ' + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')''' + src[b:]

src = func(src, 'stage', '''
def stage():
    man = read(O / 'manifest.json')
    pe = read(PACT_EVID)
    arc = pe['archive']
    for n in FILES:
        assert L.sha(O / n) == man['files'][n]['sha256'], ('candidate file differs from its manifest: rebuild', n)
    assert arc['source_sha256'] == man['base']['pact_sha256'], 'the panel was built on another PACT than the AIN base'
    assert arc['candidate_sha256'] == man['files']['NightRemasterPact.afa']['sha256'] == pe['outputs']['NightRemasterPact.afa']
    assert pe['changed_entries'] == [177] and arc['replaced_ids'] == [177] and not arc['appended'], 'other entries changed'
    assert pe['round_trip_exact'] and pe['alice_ex_dump_parsed'] and man['pact_changed'] is True
    return {n: man['files'][n]['sha256'] for n in FILES}
''')
src = func(src, 'probe_mods_ok', '''
def probe_home_ok(p):
    lg = p.get('log') or []
    return bool(lg and 'END' in lg and 'FAILS 0' in lg and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('events') and not p.get('timeout') and not p.get('fails') and p.get('oks', 0) >= 11)
''')
src = func(src, 'draft_contract', '''
def draft_contract():
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    pm = read(L.EVID / 'probe_home.json')
    assert pm.get('candidate_ain') == after['NightRemaster.ain'] and pm.get('candidate_pact') == after['NightRemasterPact.afa'], 'rerun probe_home.py'
    scan_ = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    rc = read(L.WORK / 'resume_offset_check.json')
    assert rc['candidate_ain'] == after['NightRemaster.ain'] and not rc['problems'], 'rerun work/resume_offset_check.py'
    pe = read(PACT_EVID)
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
        status='HOME_PANEL_20261017_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files=after, candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=True,
        pact_changed_entries=[177], ex_changed=False, fnl_changed=False, chart_changed=False, hook_changed=False,
        no_restore_rule=NO_RESTORE, added_functions=len(ids), added_function_names=sorted(ids),
        same_length_sites=man['same_length_sites'], message_box_sites=[], relocated_original_functions=[],
        pinned_addresses=pinned, pinned_from_now_on=still,
        panel=dict(new_parts=pe['made'], hidden_at_start=pe['hidden_at_start'], body_hidden=True, layout=pe['layout'],
                   names_kept=['KR_HomeRate', 'KR_HomeRateTitle', 'KR_HomeRateBody']),
        saved_stacks=dict(resume_saves=rc['stats']['resume_saves'], frames=rc['stats']['frames'],
                          frames_in_changed_functions=rc['stats'].get('frames_in_changed_functions', 0), problems=len(rc['problems']),
                          changed_functions_on_stacks=sorted({h['fn'] for h in rc['frames_in_changed_functions']}),
                          check=str(L.WORK / 'resume_offset_check.json'), check_sha256=L.sha(L.WORK / 'resume_offset_check.json'),
                          note='read-only check of the user\\'s saves: every saved frame keeps its crc (the AIN function table is '
                               'unchanged), no original function moved, no frame resumes at or inside a swapped instruction'),
        verification=dict(probe=dict(passed=probe_home_ok(pm), oks=pm.get('oks'), fails=pm.get('fails'), seconds=pm.get('seconds'),
                                     save=pm.get('save'), shots=[Path(x).name for x in pm.get('shots', [])]),
                          defender=scan_.get('status'), transaction_fixture=fx['status'] if fx else 'NOT_RUN',
                          not_played_natively='real mouse hit-testing and the cursor-over (state 2) look of the buttons: the probe '
                                              'cuts input off and calls the click handler with each button\\'s coordinates'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='home_panel_20261017_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)
''')
src = once(src, "self.note_title = note_title or '모드 탭 정리 · 메시지 상자 한국어 (Claude Opus 5.5; 오토 내비게이션 설치본 위)'",
           "self.note_title = note_title or '본거지 달성률 패널 새 모양 (Claude Opus 5.5; 전투 템포 설치본 위)'")
src = once(src, '''        for n in ['probe_mods.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)''', '''        for n in ['probe_home.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for f in (L.WORK / 'pact').glob('*.pactex'):
            shutil.copy2(f, ev / 'source' / f.name)
        shutil.copy2(PACT_EVID, ev / 'source' / 'pact_build_evidence.json')''')
src = once(src, '''        for f in ctx.sources.glob('pact_18*.pactex'):
            shutil.copy2(f, ev / 'source' / f.name)
''', '')
src = once(src, '''        nm['next'] = ('User screen check: 옵션 → 모드 탭(구역 · 슬라이더 바 · 위쪽 버튼 줄)과 자동 회복 설정 쪽의 새 배치; 홈에서 옵션을 '
                      '열면 왼쪽 달성률 패널이 사라졌다가 닫으면 돌아오는지; 게임 종료 · 타이틀로 확인 창이 한국어인지.')''',
           '''        nm['next'] = ('User screen check: 본거지 왼쪽 달성률 패널(얼굴 · 막대, 「이 세이브」 · 「모든 세이브 합산」 구역); 인물 단추에 마우스를 '
                      '올리면 금색 테두리가 되는지; 인물 단추를 누르면 그 인물의 남은 이벤트 창, 「이벤트 캘린더」 단추를 누르면 캘린더가 '
                      '열리는지; 던전 등 본거지 밖(달성률 항상 표시)에서는 캘린더 단추 없이 숫자만 보이는지.')''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 본거지 달성률 패널(사용자 10-17 「텍스트만 있어서 정보 파악이 느려」 · 숫자 기준이 섞임 · 이름 누르는 창; 시안 승인 「좋아 "
                "가자」): 글자 대신 얼굴 · 막대로. 「이 세이브」(이벤트 · 본편 진행 · 인물 7명)와 「모든 세이브 합산」(대사 · CG · 회상 · 엔딩)을 "
                "나눴다. 인물 줄은 단추(누르면 예전처럼 그 인물의 남은 이벤트 창), 맨 아래 「이벤트 캘린더」 단추는 본거지 첫 메뉴가 떠 "
                "있을 때만 보이고 KR_CDoHome 으로 캘린더를 연다. 숫자의 출처와 분모는 예전 패널과 같다.\\n"
                "- PACT 177 AddArea 의 KR_HomeRate 묶음에 KR_HR_* 부품(글 · 단추 · 막대 · 얼굴 자리), 본문 KR_HomeRateBody 는 숨김(변경 표식). "
                "AIN 은 KR_HV* 함수, 원본 함수 이전 0, 같은 길이 CALLFUNC 피연산자 6곳(KR_RateRender 2 · KR_T8HomeMenuOpen 1 · "
                "KR_T8HomeMenuClose 2 · KR_T8HomeClick 1), 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 " + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) "
                "publish_home.py --restore.\\n")
''' + src[b:]
# readiness: the probe json of this layer
src = once(src, '''    pm = read(L.EVID / 'probe_mods.json') if (L.EVID / 'probe_mods.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or pm.get('candidate_pact') != after['NightRemasterPact.afa'] or not probe_mods_ok(pm):
        issues.append('native probe (probe_mods.py) missing, failing or for another candidate')''', '''    pm = read(L.EVID / 'probe_home.json') if (L.EVID / 'probe_home.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or pm.get('candidate_pact') != after['NightRemasterPact.afa'] or not probe_home_ok(pm):
        issues.append('native probe (probe_home.py) missing, failing or for another candidate')''')
assert 'probe_mods' not in src and 'mdlib' not in src and 'consumer_chain.json\')' not in src.split('def draft_contract')[1].split('def ')[0], 'leftover Mods-layer checks'
(HERE / 'publish_home.py').write_text(src, 'utf8')
print('ok', len(src.splitlines()), 'lines')
