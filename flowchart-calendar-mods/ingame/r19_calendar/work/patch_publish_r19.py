"""one-off: turn the copy of publish_calendar_r18.py into publish_calendar_r19.py.
r19 payload = NightRemaster.ain + Manual/chart/yoru_flowchart_v2.html (the chart-menu contract: "when the chart is rebuilt
(chart/build_chart_v2.py) copy the new HTML to the same path and update its manifest row")."""
from pathlib import Path

P = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r19_calendar\publish_calendar_r19.py')
s = P.read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:100], s.count(old))
    s = s.replace(old, new)


rep(s[:s.index('from pathlib import Path')], '''"""Claude Opus 5.5 (2026-09-27) r19: install / restore of the calendar r19 candidate (copy of publish_calendar_r18.py).
r19 = the r18 install + names instead of the internal event numbers on every calendar page + the affinity conditions
(rule 11); the regenerated PC chart v2 (same names) goes to the help-menu chart path as the chart-menu contract asks.

  python publish_calendar_r19.py --contract   write the Codex contract draft r19_calendar/required_calendar_r19.json
  python publish_calendar_r19.py --fixture    transaction fixture on disposable files under r19_calendar/work (no runtime)
  python publish_calendar_r19.py --verify     read-only readiness check (hashes, VM, self-test, probe, native compare, scan,
                                              fixture, contract list, pointer)
  python publish_calendar_r19.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_calendar_r19.py --restore    undo an install exactly (journal-driven, resumable, idempotent): the runtime
                                              goes back to the pre-install files (= the r18 install)

Payload: NightRemaster.ain + Manual/chart/yoru_flowchart_v2.html (PACT/EX untouched). One journaled transaction, as in r4~r18:
  PREPARED (evidence/calendar_r19: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement of the two
  files -> runtime manifest + current.json + every required_*.json present at install time (calendar_r19_preserved_by; their
  required_files rows for the two files follow) + new required_calendar_r19.json + latest_worked_translation.json + progress.md
  note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore
  returns the exact pre-install state.
Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""
''')
rep('import r18lib as L\n', 'import r19lib as L\n')
rep('''E = R / 'evidence' / 'calendar_r18'                   # created only by --install''', '''E = R / 'evidence' / 'calendar_r19'                   # created only by --install''')
rep('''FILES = ['NightRemaster.ain']
NEW = 'required_calendar_r18.json'
DRAFT = HERE / NEW
STATUS = 'CALENDAR_R18_INSTALLED_NATIVE_PASS'
READY = 'CALENDAR_R18_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
DEFECTS = 27''', '''CHART = 'Manual/chart/yoru_flowchart_v2.html'
FILES = ['NightRemaster.ain', CHART]
NEW = 'required_calendar_r19.json'
DRAFT = HERE / NEW
STATUS = 'CALENDAR_R19_INSTALLED_NATIVE_PASS'
READY = 'CALENDAR_R19_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
DEFECTS = 31''')
rep('''                       'RunEvent > event. Keep index, address and code bytes in every later build. r18 changed exactly one thing in '
                       'it: the 4-byte operand of that call (LSys3xScript::RunEvent -> KR_T18RunSandboxed, same signature, same '
                       'length); every other byte equals the r15 candidate.',''',
    '''                       'RunEvent > event. Keep index, address and code bytes in every later build. r18 changed exactly one thing in '
                       'it: the 4-byte operand of that call (LSys3xScript::RunEvent -> KR_T18RunSandboxed, same signature, same '
                       'length); every other byte equals the r15 candidate. r19: byte-identical to r18.',''')
rep('''                       'keep it in place as a precaution (r15 contract; r18 byte-identical).',''',
    '''                       'keep it in place as a precaution (r15 contract; r18 and r19 byte-identical).',''')
rep('''    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17 and r18 (now called from KR_T18RunSandboxed).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17 and r18.',
    'KR_T18RunSandboxed': 'NEW in r18 and pinned from now on: on saved stacks when the player saves during a sandboxed replay \'''',
    '''    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17, r18 and r19 (called from KR_T18RunSandboxed).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17, r18 and r19.',
    'KR_T18RunSandboxed': 'r18, pinned (r19 byte-identical): on saved stacks when the player saves during a sandboxed replay \'''')
rep('''FORWARDED = {
    'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage',
    'KR_T9LaneTitle': 'KR_T18LaneTitle', 'KR_T9CardRow': 'KR_T18CardRow',
    'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
    'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage',
}''', '''FORWARDED = {           # r19's five one-call forwarders (r18's eight KR_T9 -> KR_T18 forwarders stay as they are)
    'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
    'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage',
}
R18_FORWARDED = ['KR_T9MonthPage', 'KR_T9MemPage', 'KR_T9LaneTitle', 'KR_T9CardRow', 'KR_T9ChipRow', 'KR_T9MonthChips',
                 'KR_T9CardPage', 'KR_T9EventPage']''')
rep('''NO_RESTORE = ('Codex must never run publish_calendar_*.py --restore or otherwise remove the calendar overlay (KR_T9*/KR_T17*/KR_T18* '
              'functions, the nine r15 same-length operands, the RunEvent operand swap in KR_T9HomeCasual). The calendar is a permanent '
              'user-requested feature: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'the calendar functions forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_calendar_*.py --restore 를 실행하거나 달력 오버레이(KR_T9*/KR_T17*/KR_T18* 함수, r15 의 같은 길이 '
                 '피연산자 9곳, KR_T9HomeCasual 의 RunEvent 피연산자 교체)를 지우지 않는다. 달력은 사용자가 요청한 영구 기능이다: 깨끗한 '
                 '기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 달력 함수를 이어 싣는다. 되돌리기는 사용자가 명시적으로 '
                 '요청할 때만 한다.')''',
    '''NO_RESTORE = ('Codex must never run publish_calendar_*.py --restore or otherwise remove the calendar overlay (KR_T9*/KR_T17*/KR_T18*/KR_T19* '
              'functions, the nine r15 same-length operands, the RunEvent operand swap in KR_T9HomeCasual). The calendar is a permanent '
              'user-requested feature: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'the calendar functions forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_calendar_*.py --restore 를 실행하거나 달력 오버레이(KR_T9*/KR_T17*/KR_T18*/KR_T19* 함수, r15 의 같은 길이 '
                 '피연산자 9곳, KR_T9HomeCasual 의 RunEvent 피연산자 교체)를 지우지 않는다. 달력은 사용자가 요청한 영구 기능이다: 깨끗한 '
                 '기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 달력 함수를 이어 싣는다. 되돌리기는 사용자가 명시적으로 '
                 '요청할 때만 한다.')''')
i0 = s.index('INSTRUCTION = (')
i1 = s.index('\n\n\ndef js(data):')
rep(s[i0:i1], '''INSTRUCTION = (
    'Claude r19 (2026-09-27): in-game event calendar = the r18 install + human-readable names instead of the internal event '
    'numbers (E#####) on every calendar page + affinity conditions on the 「언제」 lines (design ingame/설계_v3_글메뉴판.md, 「r19 요구」 '
    'rules 1-11). ' + NO_RESTORE + ' Payload: NightRemaster.ain and Manual/chart/yoru_flowchart_v2.html (the PC chart v2 rebuilt by '
    'chart/build_chart_v2.py with the same names in a side-panel field; required_chart_menu_20260927.json asks exactly this when the chart '
    'is rebuilt); PACT/EX untouched. KR_T19* functions appended (tables: card names / tails / lane-row conditions, scene names / list '
    'lines, the 「언제」 lines that differ from r15\\'s table, the drawer display order, list columns); no original function relocated. '
    'Five existing functions keep index and arguments but their body is a one-call forwarder at a new address: KR_T18CardRow -> '
    'KR_T19CardRow (name tails on the lane rows whose card names collide, e.g. 「10/22 밤 ● 이즈미와 1」), KR_T18CardTitle -> '
    'KR_T19CardTitle and KR_T18EventTitle -> KR_T19EventTitle (first line 「<언제> · <유형> · <이름>」, 「언제」 with names and affinity), '
    'KR_T9StagePage -> KR_T19StagePage (「2. 갈래 1 쿄카와 ○」) and KR_T9ChipPage -> KR_T19ChipPage (「마코토와 3번째 ●」). These page '
    'functions are never on a saved stack. r18\\'s eight KR_T9 -> KR_T18 forwarders stay. No same-length operand changes: r15\\'s nine and '
    'r18\\'s KR_T9HomeCasual RunEvent -> KR_T18RunSandboxed operand stay applied. Pinned (index, address and every code byte identical): '
    'KR_T9HomeCasual, KR_T9HomeConfig, C_SceneHomebase@CheckGameSysButtons, C_SceneHomebase@Run, LSys3xScript::RunEvent, '
    'KR_T18RunSandboxed. The names are computed by chart/build_chart_v2.py (event_names) from graph/schedule.json / labels.json / '
    'groups.json; graph/schedule.json triggers gained `feeling_gate` (scratch/extract.py: ConditionalCall nFeeling, '
    'GetAfterTrainingEvent GetFeeling() >= n, L_EventCall::E30152 GetFeeling() < 50 branches, L_EventCall::E10501 highest affinity '
    'when no route is set). Rebuild the calendar when the chart data changes. State: SystemService variables YoruKR.T9.* / YoruKR.T18.* '
    'only; no globals, structs or save schema change. Every earlier contract stays in force.')''')
rep('''    'KR_T18RunSandboxed': 'r18, pinned (r19 byte-identical): on saved stacks when the player saves during a sandboxed replay \'''',
    '''    'KR_T18RunSandboxed': 'r18, pinned (r19 byte-identical): on saved stacks when the player saves during a sandboxed replay \'''')

# ---- files with a sub-folder (the chart) in copies / fixture / install
rep('''def replace_checked(src, dest, expected):
    assert L.sha(src) == expected, ('source mismatch', str(src))''', '''def replace_checked(src, dest, expected):
    assert L.sha(src) == expected, ('source mismatch', str(src))
    assert dest.parent.is_dir(), ('target folder missing', str(dest.parent))''')
rep('''    for n in FILES:
        (b / n).write_bytes(('old ' + n).encode())
        shutil.copy2(O / n, s / n)
        shutil.copy2(b / n, l / n)''', '''    for n in FILES:
        for d in (b, s, l):
            (d / n).parent.mkdir(parents=True, exist_ok=True)
        (b / n).write_bytes(('old ' + n).encode())
        shutil.copy2(O / n, s / n)
        shutil.copy2(b / n, l / n)''')
rep('''        (l / (FILES[0] + '.calendar-copy.tmp')).write_bytes(b'partial interrupted copy')
        pair_restore(b, l, before, after)
        assert all(L.sha(l / n) == before[n] for n in FILES) and not list(l.glob('*.tmp'))''',
    '''        for n in FILES:
            (l / (n + '.calendar-copy.tmp')).write_bytes(b'partial interrupted copy')
        pair_restore(b, l, before, after)
        assert all(L.sha(l / n) == before[n] for n in FILES) and not list(l.rglob('*.tmp'))''')
rep('''                  interrupted_metadata_restoration_resumable=True, no_incoming_residue=not list(l.glob('*.tmp')))''',
    '''                  interrupted_metadata_restoration_resumable=True, no_incoming_residue=not list(l.rglob('*.tmp')), files=FILES)''')
rep('''        for n in FILES:
            shutil.copy2(b / n, E / 'before' / n)
        pair_apply(s, b, l, before, after)''', '''        for n in FILES:
            (E / 'before' / n).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(b / n, E / 'before' / n)
        pair_apply(s, b, l, before, after)''')

# ---- draft contract
rep('''                            code=man['pinned_functions'].get(name, dict(new_in_r18=True)))''', '''                            code=man['pinned_functions'][name])''')
rep('''        status='CALENDAR_R18_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),''',
    '''        status='CALENDAR_R19_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),''')
rep('''        replaces=man['replaces'], no_restore_rule=NO_RESTORE,
        added_functions=len(ids), added_function_names=sorted(ids), forwarded_functions=forwarded, same_length_sites=man['same_length_sites'],
        sandbox=dict(man['sandbox'], verified_natively=dict(probe['sandbox'], files_at_end=None) if probe.get('sandbox') else None,
                     session_variables_restored_by_resumeload=(probe.get('sandbox') or {}).get('session_variables_restored_by_resumeload')),
        replay_lock=dict(rule='「이 장면 재생」 only when the scene is registered in this save (IsRegisteredEvent, ○); ● / △ -> one lock line',
                         pages=['KR_T9CardPage -> KR_T18CardPage', 'KR_T9EventPage -> KR_T18EventPage'],
                         second_check='KR_T18Request (state 2 + context) and KR_T18RunSandboxed (IsRegisteredEvent of the prepared name)'),
        r15_same_length_sites_kept=man['r15_same_length_sites_kept'], relocated_original_functions=[], pinned_addresses=pinned,''',
    '''        no_restore_rule=NO_RESTORE, based_on_r18_install=True,
        added_functions=len(ids), added_function_names=sorted(ids), forwarded_functions=forwarded, r18_forwarders_kept=R18_FORWARDED,
        same_length_sites=[], same_length_sites_kept=man['same_length_sites_kept'],
        names=dict(man['names'], computed_by='chart/build_chart_v2.py event_names (the PC chart v2 shows the same names)',
                   chart_file=CHART, chart_sha256=man['files'][CHART]['sha256'], chart_builder_sha256=man['chart']['builder_sha256'],
                   schedule_sha256=man['chart']['schedule_sha256']),
        sandbox_replay_unchanged_since_r18=dict(verified_natively=dict(probe['sandbox'], files_at_end=None) if probe.get('sandbox') else None,
                                                session_variables_restored_by_resumeload=(probe.get('sandbox') or {}).get('session_variables_restored_by_resumeload')),
        relocated_original_functions=[], pinned_addresses=pinned,''')
rep('''        summary_dialog_top=186,
        session_variables=man['session_variables'], serialized_schema_changes=0,''', '''        session_variables=man['session_variables'], serialized_schema_changes=0,''')
rep('''                          panel=vm['panel'] and {k: v for k, v in vm['panel'].items() if k != 'states'},''',
    '''                          panel=vm['panel'] and {k: v for k, v in vm['panel'].items() if k != 'states'},
                          chart_dom=read(L.EVID / 'chart_dom_diff.json')['dom'] if (L.EVID / 'chart_dom_diff.json').exists() else None,''')
rep('''        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_r18_preserved_by',''',
    '''        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_r19_preserved_by',''')

# ---- readiness
rep('''    if L.sha(O / 'NightRemaster.ain') != after['NightRemaster.ain']:
        issues.append('candidate AIN differs from its manifest')''', '''    if any(L.sha(O / n) != after[n] for n in FILES):
        issues.append('candidate files differ from their manifest')''')
rep('''        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r18 on the new runtime')''',
    '''        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r19 on the new runtime')''')
rep('''    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')''', '''    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')
    if L.sha(rt / CHART) != man['chart_runtime_before_sha256']:
        issues.append('the runtime help-menu chart moved since the build (another chart installed?)')''')
rep('''        issues.append('native titles / rows / panel / sandbox not compared with the VM (verify_calendar_r18.py --native)')''',
    '''        issues.append('native titles / rows / lists / panel / sandbox not compared with the VM (verify_calendar_r19.py --native)')
    dom = read(L.EVID / 'chart_dom_diff.json') if (L.EVID / 'chart_dom_diff.json').exists() else {}
    if not dom.get('dom_identical_except_name_field_and_rule11') or L.sha(Path(dom.get('new', ''))) != after[CHART] if dom.get('new') else True:
        issues.append('PC chart DOM identity (work/chart_dom_diff_r19.py) missing, failing or for another chart')''')
rep('''    if E.exists():
        issues.append('evidence/calendar_r18 already exists: inspect the earlier transaction')
    if (R / 'evidence' / 'calendar_r16').exists() or (R / 'required_calendar_r16.json').exists():
        issues.append('r16 appears installed after all (evidence/calendar_r16 or required_calendar_r16.json) - inspect first')
    j17 = read(L.R17_JOURNAL) if L.R17_JOURNAL.exists() else {}
    if j17.get('status') != 'RESTORED' or (R / 'required_calendar_r17.json').exists():
        issues.append('r17 is installed again (evidence/calendar_r17 journal not RESTORED or required_calendar_r17.json present): r18 was built on the base without r17 - rebuild')''',
    '''    if E.exists():
        issues.append('evidence/calendar_r19 already exists: inspect the earlier transaction')
    j18 = read(R / 'evidence' / 'calendar_r18' / 'journal.json') if (R / 'evidence' / 'calendar_r18' / 'journal.json').exists() else {}
    if j18.get('status') != 'COMMITTED' or not (R / 'required_calendar_r18.json').exists():
        issues.append('r18 is not installed as the base expects (evidence/calendar_r18 journal not COMMITTED or required_calendar_r18.json missing): rebuild')''')

# ---- install
rep('''    rh = {n: L.sha(rec / n) for n in FILES}''', '''    rh = {n: L.sha(rec / n) for n in FILES if (rec / n).exists()}''')
rep('''    for n in FILES:
        shutil.copy2(rt / n, E / 'before' / n)
        shutil.copy2(O / n, E / 'candidate' / n)''', '''    for n in FILES:
        for d in ('before', 'candidate'):
            (E / d / n).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rt / n, E / 'before' / n)
        shutil.copy2(O / n, E / 'candidate' / n)''')
rep('''    full['calendar_r18_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)''',
    '''    full['calendar_r19_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)''')
rep('''        nm.update(status=STATUS, time=now, calendar_r18_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r18_overlay=str(E / 'source' / 'manifest.json'))''',
    '''        nm.update(status=STATUS, time=now, calendar_r19_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r19_overlay=str(E / 'source' / 'manifest.json'))''')
rep('''        nm['next'] = 'User screen check: 이벤트 달력 r17 화면(막대·▲●○·달성도 보기·서랍 줄) + r18: ● · △ 카드는 「이 장면 재생」 대신 잠금 줄, ○ 장면 재생 뒤 본거지 달성률 · 친밀도 · 날짜가 재생 전과 같음.\'''',
    '''        nm['next'] = 'User screen check: 이벤트 달력 r19 — 카드 쪽 · 장면 쪽 첫 줄과 단계 목록 · 서랍 장면 목록에 E번호 대신 이름(「특훈 뒤 대화 3번째」「마코토와 3번째」「2. 갈래 1 쿄카와」), 친밀도 조건(「쿄카 친밀도 30 이상」), 도움말 메뉴 차트의 「게임 안 이름」.\'''')
rep('''            c['calendar_r18_preserved_by'] = str(E)''', '''            c['calendar_r19_preserved_by'] = str(E)''')
rep('''        nc.update(status=STATUS, manifest_sha256=mh, calendar_r18_revision=rev)''', '''        nc.update(status=STATUS, manifest_sha256=mh, calendar_r19_revision=rev)''')
rep('''                      translation_map_sha256=L.sha(translation), calendar_r18_evidence=str(E))''', '''                      translation_map_sha256=L.sha(translation), calendar_r19_evidence=str(E))''')
n0 = s.index('''        note = (f"\\n\\n### {now} 인게임 이벤트 달력 r18 설치''')
n1 = s.index('''        write(R / 'progress.md',''')
rep(s[n0:n1], '''        note = (f"\\n\\n### {now} 인게임 이벤트 달력 r19 설치 (Claude Opus 5.5; r18 설치본 위)\\n"
                "- 달력의 모든 쪽에서 E번호 대신 이름(카드 · 장면 쪽 첫 줄 「<언제> · <유형> · <이름>」, 단계 목록 「2. 갈래 1 쿄카와」, 서랍 장면 목록 「마코토와 3번째」, 겹치는 레인 줄 꼬리 「이즈미와 1」) + 「언제」 줄의 친밀도 조건(「쿄카 친밀도 30 이상」). 이름은 chart/build_chart_v2.py 가 계산하고 PC 차트 v2(도움말 메뉴 차트)에도 같은 이름을 넣었다.\\n"
                "- AIN 과 Manual/chart/yoru_flowchart_v2.html 두 파일, 원본 함수 이전 0, 기존 함수 5개는 번호 그대로 한 줄 전달(KR_T18CardRow · KR_T18CardTitle · KR_T18EventTitle · KR_T9StagePage · KR_T9ChipPage), 같은 길이 교체 없음(r15 의 9곳 · r18 의 1곳 그대로), 주소 유지 함수 6개 바이트 동일.\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; chart {after[CHART]}; manifest {mh}; evidence {E}; 되돌리기(사용자 요청 때만) publish_calendar_r19.py --restore.\\n")
''')
assert 'r18lib' not in s and 'L.R17_JOURNAL' not in s
P.write_text(s, encoding='utf-8', newline='\n')
print('ok')
