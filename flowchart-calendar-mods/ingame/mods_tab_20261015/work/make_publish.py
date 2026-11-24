# -*- coding: utf-8 -*-
"""Make publish_mods.py from autonav_20261015/publish_autonav.py: the same journaled install / restore transaction, fixture and
readiness, with the Mods-layer payload, evidence checks, contract and notes."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'autonav_20261015' / 'publish_autonav.py').read_text('utf8')


def func(text, name, new):
    """Replace a top-level def (up to the next top-level def / class / section comment)."""
    m = re.search(r'\ndef %s\(.*?(?=\n\n\n(?:def |class |# -))' % re.escape(name), text, re.S)
    assert m, name
    return text[:m.start()] + '\n' + new.strip('\n') + text[m.end():]


def once(text, a, b):
    assert text.count(a) == 1, a[:80]
    return text.replace(a, b)


DOC = '''"""Claude Opus 5.5 (2026-10-15): install / restore of the Mods page layer (user: 「모드 옵션을 좀 보기좋게 다시 만들 수 있을까 …
모든 기능이 제대로 동작하나 체크좀」, 「지금 경고문 번역 안됐네? … 어쨌든 번역은 해줘」), made from publish_autonav.py (same
journaled transaction, same KRMenu scratch rule).

  python publish_mods.py --stage      put the PACT candidate (NightRemasterPact.afa: entries 185 Mods + 187 AutoItems) into
                                      candidate/ and record it in candidate/manifest.json (rerun after every build)
  python publish_mods.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_mods.py --contract   write the Codex contract draft required_mods_tab_20261015.json
  python publish_mods.py --fixture    transaction fixture on disposable files under mods_tab_20261015/work (no runtime)
  python publish_mods.py --verify     read-only readiness check (hashes, native probe, scan, fixture, saved stacks, contracts)
  python publish_mods.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_mods.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_MD* layer + 42 message-box texts as CP949) + NightRemasterPact.afa (entries 185 Asra/Mods and 187
Asra/AutoItems laid out again). EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction as publish_autonav.py:
PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present at install time
(mods_tab_20261015_preserved_by) + new required_mods_tab_20261015.json + latest_worked_translation.json + progress.md note ->
exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back; --restore returns the exact pre-install state.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import anlib as L', 'import mdlib as L')
for a, b in [('autonav_20261015', 'mods_tab_20261015'), ('AUTONAV_20261015', 'MODS_TAB_20261015'), ('.autonav-', '.mods-'),
             ('autonav-copy.tmp', 'mods-copy.tmp'), ('publish_autonav', 'publish_mods')]:
    src = src.replace(a, b)
src = once(src, "PACT_SRC = HERE / 'pact' / 'NightRemasterPact.afa'", "PACT_SRC = HERE / 'NightRemasterPact.afa'")
src = once(src, "READY = 'MODS_TAB_20261015_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'", "READY = 'MODS_TAB_20261015_STATIC_NATIVE_PASS_NOT_INSTALLED'")
src = once(src, "str(HERE / 'scan_autonav.ps1')", "str(HERE.parent / 'autonav_20261015' / 'scan_autonav.ps1')")
src = once(src, '''# new in this layer: functions that sit on saved stacks when the player saves while a choice / the partner confirm / the
# new-game question is open (system menu): later builds keep their index, address and every code byte''',
           '''# auto-nav pins (10-15, still in force): on saved stacks when the player saves while a choice / the partner confirm / the
# new-game question is open; this layer keeps them byte-identical (build_mods_ain.py invariance) and so must every later build''')
a = src.index('NO_RESTORE = (')
b = src.index('\n\n\ndef js(')
src = src[:a] + '''MSG_TITLE_KO = '타이틀 화면으로 돌아가시겠습니까?\\n\\n※저장하지 않은 데이터는 사라집니다'
NO_RESTORE = ('Codex must never run publish_mods*.py --restore or otherwise remove the Mods page layer: KR_MD* functions; '
              'C_ConfigView@EventConfAsraDataForParts / EventConfPartsDataForAsra call KR_MDSeenToParts / KR_MDSeenToAsra where they '
              'called KR_ANCfgSeenToParts / KR_ANCfgSeenToAsra (the auto-nav functions are called first, their result returned); the '
              'S_PUSH operands of 42 system.MsgBox* / system.Error texts point to CP949 strings (Windows shows MessageBoxA text in the '
              'system code page, so the Japanese CP932 and the FNL-proxy Korean showed as garbage); PACT 185 Asra/Mods and 187 '
              'Asra/AutoItems laid out again with the KR_MD_* parts (slider tracks, headings, tags, ticks). It is user-requested: when a '
              'rebuild needs a clean base, rebase on the runtime that current.json points to and carry it forward; restore is reserved '
              'for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_mods*.py --restore 를 실행하거나 모드 탭 층(KR_MD* 함수; 옵션 동기화 두 함수의 KR_ANCfgSeenToParts / '
                 'KR_ANCfgSeenToAsra 호출 → KR_MDSeenToParts / KR_MDSeenToAsra(오토 내비 함수를 먼저 부르고 그 결과를 돌려줌); '
                 'system.MsgBox* · system.Error 문구 42곳의 S_PUSH 피연산자 → CP949 문자열; PACT 185 · 187 새 배치와 KR_MD_* 부품)을 '
                 '지우지 않는다. 사용자가 요청한 것이다: 깨끗한 기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 이어 '
                 '싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude Mods page layer (2026-10-15, user requests: a tidier Mods options page with every option checked, and the untranslated '
    'Windows message boxes). ' + NO_RESTORE + ' Payload: NightRemaster.ain + NightRemasterPact.afa (entries 185 and 187 only). '
    'KR_MD* functions appended; no original function relocated; no new global / struct member. PACT 185 / 187 are laid out by '
    'mods_tab_20261015/build_pact_mods.py: every part name code or the EX table Ｅ＿コンフィグファイル名 looks up is kept; later '
    'edits of these entries start from the installed entries, not from an older build. Message-box texts (system.MsgBox* / '
    'system.Error) stay CP949 bytes; never write them with FNL proxy characters. While the options are open the home 달성률 panel '
    '(KR_HomeRate) is hidden by KR_MDHomeRate (KR_RateRender\\'s own ■コンフィグ実行中確認 = Ｓ＿コンフィグ on the stack misses the '
    'home path ▲コンフィグ実行 -> Ｓ＿コンフィグ／標準 / ／開始ページ); the home loop shows it again. The auto-nav pins stay '
    '(index, address and every code byte): ' + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')''' + src[b:]

src = func(src, 'stage', '''
def stage():
    man = read(O / 'manifest.json')
    want = L.sha(PACT_SRC)
    pe = read(HERE / 'build_evidence.json')
    arc = pe['archive']
    assert arc['source_sha256'] == man['base']['pact_sha256'], 'the pages were built on another PACT than the AIN base'
    assert arc['candidate_sha256'] == want == pe['outputs']['NightRemasterPact.afa'], 'NightRemasterPact.afa is not the one the evidence describes'
    assert pe['changed_entries'] == [185, 187] and arc['replaced_ids'] == [185, 187] and not arc['appended'], 'other entries changed'
    assert pe['round_trip_exact'] and pe['alice_ex_dump_parsed']
    dest = O / 'NightRemasterPact.afa'
    if not dest.exists() or L.sha(dest) != want:
        shutil.copy2(PACT_SRC, dest)
    assert L.sha(dest) == want
    man['files']['NightRemasterPact.afa'] = dict(sha256=want, size=dest.stat().st_size, built_by='build_pact_mods.py',
                                                 source_sha256=arc['source_sha256'], changed_entries=[185, 187],
                                                 evidence_sha256=L.sha(HERE / 'build_evidence.json'),
                                                 note='185 Asra/Mods and 187 Asra/AutoItems laid out again (KR_MD_* parts)')
    man['pact_changed'] = True
    put(O / 'manifest.json', js(man))
    return {n: man['files'][n]['sha256'] for n in FILES}
''')
src = func(src, 'probe_train_ok', '')
src = func(src, 'probe_home_ok', '''
def probe_mods_ok(p):
    lg = p.get('log') or []
    return bool(lg and 'END' in lg and 'FAILS 0' in lg and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('events') and not p.get('timeout') and not p.get('fails') and p.get('oks', 0) >= 37
                and p.get('msgbox_title_korean') and (p.get('message') or {}).get('cp949') == MSG_TITLE_KO)
''')
src = func(src, 'draft_contract', '''
def draft_contract():
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    pm = read(L.EVID / 'probe_mods.json')
    scan_ = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    rc = read(L.WORK / 'resume_offset_check.json')
    assert rc['candidate_ain'] == after['NightRemaster.ain'] and not rc['problems'], 'rerun work/resume_offset_check.py'
    ca = read(L.WORK / 'consumer_chain.json')
    pe = read(HERE / 'build_evidence.json')
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
        status='MODS_TAB_20261015_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files=after, candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=True,
        pact_changed_entries=[185, 187], ex_changed=False, fnl_changed=False, chart_changed=False, hook_changed=False,
        no_restore_rule=NO_RESTORE, added_functions=len(ids), added_function_names=sorted(ids),
        same_length_sites=man['same_length_sites'], message_box_sites=man['message_box_sites'], relocated_original_functions=[],
        pinned_addresses=pinned, pinned_from_now_on=still,
        pages=dict(mods_new_parts=pe['made'], mods_hidden=pe['hidden'], mods_names_kept=pe['used_by_code_kept'],
                   items_new_parts=pe['items_page']['made'], items_names_kept=pe['items_page']['used_by_code_kept']),
        saved_stacks=dict(resume_saves=rc['stats']['resume_saves'], frames=rc['stats']['frames'],
                          frames_in_changed_functions=rc['stats']['frames_in_changed_functions'], problems=len(rc['problems']),
                          changed_functions_on_stacks=sorted({h['fn'] for h in rc['frames_in_changed_functions']}),
                          check=str(L.WORK / 'resume_offset_check.json'), check_sha256=L.sha(L.WORK / 'resume_offset_check.json'),
                          note='read-only check of the user\\'s saves: every saved frame keeps its crc (the AIN function table is '
                               'unchanged), no original function moved, no frame resumes at or inside a swapped instruction'),
        verification=dict(probe=dict(passed=probe_mods_ok(pm), oks=pm.get('oks'), fails=pm.get('fails'), seconds=pm.get('seconds'),
                                     save=pm.get('save'), shots=[Path(x).name for x in pm.get('shots', [])], message_box=pm.get('message')),
                          setting_readers=ca, defender=scan_.get('status'), transaction_fixture=fx['status'] if fx else 'NOT_RUN',
                          not_played_natively='battle / dungeon effects of the options (static reader chain only; Codex contracts '
                                              'for those features say native gameplay pending)'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='mods_tab_20261015_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)
''')
src = once(src, "self.note_title = note_title or '오토 내비게이션 설치 (Claude Opus 5.5; claude_text_20261001 설치본 위)'",
           "self.note_title = note_title or '모드 탭 정리 · 메시지 상자 한국어 (Claude Opus 5.5; 오토 내비게이션 설치본 위)'")
src = once(src, '''        for n in ['verify.json', 'probe_home.json', 'probe_train.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for n in ['scan_report.json', 'transaction_verification.json', 'resume_offset_check.json', 'build/native_opcode_audit.json']:
            if (L.WORK / n).exists():
                shutil.copy2(L.WORK / n, ev / 'source' / Path(n).name)
        (ev / 'source' / 'pact').mkdir()
        for f in (ctx.sources / 'pact').iterdir():
            if f.is_file() and f.suffix in ('.py', '.json', '.png'):
                shutil.copy2(f, ev / 'source' / 'pact' / f.name)''',
           '''        for n in ['probe_mods.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for n in ['scan_report.json', 'transaction_verification.json', 'resume_offset_check.json', 'consumer_audit.json',
                  'consumer_chain.json', 'build/native_opcode_audit.json']:
            if (L.WORK / n).exists():
                shutil.copy2(L.WORK / n, ev / 'source' / Path(n).name)
        for f in ctx.sources.glob('pact_18*.pactex'):
            shutil.copy2(f, ev / 'source' / f.name)''')
src = once(src, '''        nm['next'] = ('User screen check: 오토 내비게이션 — 새 게임 시작 때 대상 고르기 창; 옵션 → 모드 탭의 「오토 내비게이션」 다섯 칸(게임 중에만); '
                      '선택지가 뜨면 고른 인물 쪽 답이 금빛으로 반짝이고 20초 뒤 자동으로 골라짐(직접 골라도 됨); 이야기가 있는 토요일엔 특훈 상대 '
                      '화면에서 대상 초상이 반짝이고 20초 뒤 자동 선택 · 확인.')''',
           '''        nm['next'] = ('User screen check: 옵션 → 모드 탭(구역 · 슬라이더 바 · 위쪽 버튼 줄)과 자동 회복 설정 쪽의 새 배치; 홈에서 옵션을 '
                      '열면 왼쪽 달성률 패널이 사라졌다가 닫으면 돌아오는지; 게임 종료 · 타이틀로 확인 창이 한국어인지.')''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 모드 탭 정리(사용자 요청 10-15 「모드 옵션을 좀 보기좋게」): PACT 185 를 구역(보상 배율 · 오토 내비게이션 · 전투 · 던전 · 편의)과 "
                "위쪽 버튼 줄로 다시 배치하고 187(자동 회복 설정)도 같은 모양으로. 슬라이더마다 네이티브식 바(KR_MD_Track*/Fill*, 채움은 "
                "KR_MDGauges), 작은 설명은 차분한 색. 코드 · EX 표가 이름으로 찾는 부품은 이름 · 종류 그대로.\\n"
                "- 홈에서 옵션을 열면 홈 달성률 패널이 옵션 탭 위를 가리던 문제: 옵션이 열린 동안 KR_MDHomeRate 가 숨기고, 홈으로 돌아오면 "
                "KR_T8HomeEnter 가 다시 보인다.\\n"
                "- 윈도 메시지 상자 42곳(게임 종료 · 타이틀로 확인, 세이브 · 불러오기 오류 등)을 CP949 한국어 문자열로: MessageBoxA 는 시스템 "
                "코드 페이지로 읽으므로 일본어 · FNL 대체 글자 모두 깨져 보였다(사용자 10-15 「경고문 번역 안됐네」).\\n"
                "- AIN + PACT(185 · 187 만), 원본 함수 이전 0, 같은 길이 피연산자 44곳(옵션 동기화 2 + 메시지 42), 새 전역 · 구조체 필드 0. "
                "오토 내비게이션 고정 함수(" + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) "
                "publish_mods.py --restore.\\n")
''' + src[b:]
src = once(src, '''    vf = read(L.EVID / 'verify.json') if (L.EVID / 'verify.json').exists() else {}
    c = vf.get('counts', {})
    if vf.get('candidate') != after['NightRemaster.ain']:
        issues.append('VM verification (verify_autonav.py --selftest) is for another candidate')
    elif c.get('A1') != 76 or c.get('A4') != 76 or c.get('A8', 0) < 7000 or c.get('A9', 0) < 27 or c.get('S1') != 27 or c.get('A7', 0) < 8:
        issues.append('VM checks incomplete')
    elif (vf.get('selftest') or {}).get('planted') != DEFECTS or (vf.get('selftest') or {}).get('caught') != DEFECTS:
        issues.append('planted-defect self-test missing or failing (%d expected)' % DEFECTS)
    home = read(L.EVID / 'probe_home.json') if (L.EVID / 'probe_home.json').exists() else {}
    train = read(L.EVID / 'probe_train.json') if (L.EVID / 'probe_train.json').exists() else {}
    for label, p, ok in (('home', home, probe_home_ok), ('train', train, probe_train_ok)):
        if p.get('candidate_ain') != after['NightRemaster.ain'] or p.get('candidate_pact') != after['NightRemasterPact.afa'] or not ok(p):
            issues.append('native probe %s missing, failing or for another candidate' % label)''',
           '''    pm = read(L.EVID / 'probe_mods.json') if (L.EVID / 'probe_mods.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or pm.get('candidate_pact') != after['NightRemasterPact.afa'] or not probe_mods_ok(pm):
        issues.append('native probe (probe_mods.py) missing, failing or for another candidate')''')
src = once(src, "issues.append('pact/NightRemasterPact.afa differs from the staged PACT: rerun --stage')",
           "issues.append('NightRemasterPact.afa differs from the staged PACT: rerun --stage')")
assert 'probe_home_ok' not in src and 'probe_train_ok' not in src and 'verify.json' not in src, 'leftover autonav checks'
assert 'anlib' not in src
(HERE / 'publish_mods.py').write_text(src, 'utf8')
print('ok', len(src.splitlines()), 'lines')
