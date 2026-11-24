"""One-off: r22 draft_contract / readiness / probe checks in publish_chart_r22.py."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'publish_chart_r22.py'
s = p.read_text('utf8')
a = s.index('# ------------------------------------------------------------------ the contract draft')
b = s.index('# ------------------------------------------------------------------ the transaction (real paths or a disposable project)')
NEW = r'''# ------------------------------------------------------------------ the contract draft
def draft_contract():
    man = read(O / 'manifest.json')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    probe = read(L.EVID / 'probe_result.json')
    p22 = read(L.EVID / 'probe_r22.json')
    kinds = read(L.EVID / 'replay_kinds.json')
    native = read(L.WORK / 'build' / 'native_compare.json')
    scan = read(L.WORK / 'scan_report.json')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    cg = read(L.FLOW / 'graph' / 'event_cg.json')
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, code=man['pinned_functions'][name])
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    r22n = native.get('r22') or {}
    return dict(
        status='CHART_R22_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files={n: man['files'][n]['sha256'] for n in FILES},
        candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False,
        hook_changed=False, no_restore_rule=NO_RESTORE, based_on_r21_install=True,
        added_functions=len(ids), added_function_names=sorted(ids), jam_bodies=man['jam_bodies'],
        forwarded_functions=man['forwarded_functions'], r19_forwarders_kept=R19_FORWARDED, r18_forwarders_kept=R18_FORWARDED,
        same_length_sites=man['same_length_sites'], earlier_same_length_sites_kept=man['earlier_same_length_sites_kept'],
        relocated_original_functions=[], pinned_addresses=pinned,
        never_on_saved_stack=['every KR_C function except, by construction, inside the game\'s own memory-mode resume image '
                              '(NightRMemoryMode.asd, the recollection mode\'s temporary file: made by AFL_MemoryModeEvent_Begin inside '
                              'KR_CReplayRun and deleted by _Cleanup right after it is loaded back) and an engine-made SystemSuspend / '
                              'Reload image taken while the chart or a replay runs (like RunHome, KR_T9HomeMenuRun and KR_MHomeRun, not '
                              'pinned); no slot save is possible in the chart (no save UI) and the recollection mode refuses save / load '
                              'while _g_回想中 (C_SysButton@IsAbleSave / IsAbleLoad). None of the user saves has a KR_C frame or a frame in '
                              'the six forwarded functions or the two title sites (S4).'],
        chart=dict(cells=man['data']['cells'], per_tab=man['data']['per_tab'], thumbnail_cells=man['data']['thumbnail_cells'],
                   small_cells=man['data']['small_cells'], order=man['data']['cell_order'], parts=man['parts'], root_z=man['root_z'],
                   event_cg=dict(sha256=L.sha(L.FLOW / 'graph' / 'event_cg.json'), gates={k: v['ok'] for k, v in cg['gates'].items()}),
                   unlock='first-message MsgSkip read mark or N_ModeScene::CheckEnabelScenario (the game\'s recollection unlock), or 「전체 '
                          '개방」 (YoruKR_Chart.dat 1, read once when the chart opens); never IsRegisteredEvent while the chart is open',
                   replay='KR_CReplayRun = C_SceneModeScene@ExecScene from AFL_MemoryModeEvent_Begin on (S8 compares the ops)',
                   replay_kinds=kinds['verdicts'], not_playable_events=man['data']['not_playable_events']),
        protocol=dict(title_poll='C_SceneTitle@Update: KR_CTitleTick in place of C_UserInputManager::IsClickConfig (two FileOperation.ExistFile '
                                 'a title frame; a waiting request / result ends the title wait with KR_CCode 2026092802 and answers false)',
                      title_serve='C_SceneTitle@Run: KR_CTitleServe in place of ■方向キー処理／削除 (the original call, then the result and the request)',
                      home='r21 unchanged (KR_MHomeRun / KR_MTick); KR_MDo forwarded to KR_CDoHome',
                      runtime_scratch_folder=RUNTIME_SCRATCH),
        runtime_exchange_folder=dict(path='<runtime>/KRMenu', files=KRMENU_FILES, rule=KRMENU_RULE, rule_ko=KRMENU_RULE_KO,
                                     in_manifest=False, tree_checks='ignore', delete=False),
        session_variables_new=man['session_variables_new'], new_globals=0, new_struct_members=0, serialized_schema_changes=0,
        verification=dict(vm=vm['counts'], vm_steps=vm['vm_steps'], planted_defects_caught=sum(p['caught'] for p in st['planted_defects']),
                          planted_defects=len(st['planted_defects']), saves_checked=vm['saves_checked'], frames_checked=vm['frames_checked'],
                          calendar_tour_on_r22=dict(passed=probe_ok(probe), seconds=probe.get('seconds'), save=probe.get('save'),
                                                    screenshots=[Path(x).name for x in probe['screenshots']],
                                                    home_before_after_differing_pixels=probe.get('home_before_after', {}).get('differing_pixels')),
                          chart_tours=dict(passed=probe22_ok(p22), title=dict(seconds=p22['title'].get('seconds'), shots=p22['title'].get('shots')),
                                           home=dict(seconds=(p22.get('home') or {}).get('seconds'), shots=(p22.get('home') or {}).get('shots')),
                                           native_compare=r22n),
                          replay_kinds=kinds['verdicts'],
                          native_blocks_equal_vm=native['counts'].get('N_blocks_identical'), native_r20_blocks_equal_vm=native['counts'].get('N_r20_blocks_identical'),
                          native_chart_pages_equal_vm=native['counts'].get('R22N_pages_equal_vm'),
                          defender=scan['status'], transaction_fixture=fx['status'] if fx else 'NOT_RUN',
                          fixture_recovery_runtime_lacking_a_payload_file=(fx or {}).get('install_with_recovery_lacking_payload_file')),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='chart_r22_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)


def probe_ok(probe):
    """The r20 calendar tour run on the r22 candidate (probe_calendar_tour_r22.py full): r19's conditions (sandbox, home pixels) +
    r20's (the member screen returns to a pixel-identical home, the partner run ended cleanly, our parts are gone after every exit)."""
    sb = probe.get('sandbox') or {}
    user_ok = probe['user_save_folder_unchanged'] or bool((probe.get('user_game_running') or {}).get('before') or (probe.get('user_game_running') or {}).get('after'))
    r20 = probe.get('r20') or {}
    st = r20.get('status') or {}
    pt = r20.get('partner') or {}
    pr = probe.get('partner_run') or {}
    return bool(probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and user_ok and probe.get('probe_save_folder_inside_run')
                and not probe.get('vm_error') and not probe.get('message') and not probe.get('events')
                and probe.get('home_before_after', {}).get('differing_pixels') == 0
                and probe.get('home_before_after_member', {}).get('differing_pixels') == 0
                and probe.get('month_before_after_summary', {}).get('differing_pixels') == 0
                and set(sb.get('states', [])) >= {'HOME', 'PREPLAY', 'MIDREPLAY', 'AFTER', 'MIDLOAD'}
                and sb.get('home_vs_after') == {} and sb.get('home_vs_preplay') == {}
                and sb.get('after_temp_files') == ['0', '0'] and sb.get('midreplay_temp_files') == ['1', '1']
                and sb.get('midload_temp_files') == ['0', '0'] and not sb.get('temp_file_on_disk_at_end')
                and st.get('after_exit1', {}).get('ours') == 0 and st.get('after_exit2', {}).get('ours') == 0
                and st.get('page4', {}).get('ours') == 2 and st.get('second_entry_page4', {}).get('ours') == 2
                and pt.get('first', {}).get('ours') == pt.get('again', {}).get('ours') and pt.get('after_screen', {}).get('ours') == 0
                and pr.get('exit_code') == 0 and pr.get('log') and pr['log'][-1] == 'END' and not pr.get('vm_error') and not pr.get('message')
                and not pr.get('events'))


def probe22_ok(p22):
    """The chart tours (probe_chart_r22.py --title / --home): ended with END, exit 0, no engine error / message box, the replay ran in
    memory mode with the chart closed and came back."""
    ok = True
    for mode in ('title', 'home'):
        r = p22.get(mode)
        if not r:
            return False
        lg = r.get('log') or []
        ok = ok and r.get('exit_code') == 0 and not r.get('vm_error') and not r.get('message') and not r.get('timeout') and lg and lg[-1] == 'END' \
            and any(x.startswith('REPLAY first message memory=1') and 'ours=0' in x for x in lg) and any(x.startswith('RETURNED') and 'ours=0' in x for x in lg)
    return bool(ok)


'''
s = s[:a] + NEW + s[b:]
# readiness
a = s.index('def readiness():')
b = s.index('def install():')
READY_FN = r'''def readiness():
    """Everything the install needs, read only. Returns (ready, report)."""
    issues = []
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    if any(L.sha(O / n) != after[n] for n in FILES):
        issues.append('candidate files differ from their manifest')
    base = man['base']
    if L.sha(rt / 'NightRemaster.ain') != base['ain_sha256']:
        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r22 on the new runtime')
    if L.sha(rt / 'NightRemasterPact.afa') != base['pact_sha256'] or L.sha(rt / 'NightRemasterEX.ex') != base['ex_sha256']:
        issues.append('runtime PACT/EX moved since the build')
    if cur['manifest_sha256'] != base['manifest_sha256'] or L.sha(Path(cur['manifest'])) != cur['manifest_sha256']:
        issues.append('current.json / runtime manifest moved since the build')
    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')
    if L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') != base['chart_sha256']:
        issues.append('the runtime Manual chart moved since the build')
    if L.sha(rt / 'winmm.dll') != base['winmm_sha256']:
        issues.append('the runtime winmm.dll (mod-menu hook) moved since the build: re-check the hook contract, rebuild if needed')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    c = vm.get('counts', {})
    if vm['candidate_sha256'] != after['NightRemaster.ain']:
        issues.append('VM verification is for another candidate')
    elif c.get('V14_saves', 0) < 1 or c.get('V14_native_panel_equal') != c.get('V14_saves'):
        issues.append('real-save summary = panel check missing')
    elif not c.get('V27_real_saves') or not c.get('V30_status_page_steps') or not c.get('V31_parts_per_entry'):
        issues.append('r20 VM checks (V27 real saves, V30, V31) missing')
    elif c.get('V34_commands', 0) < 10 or not c.get('V35_flag_saved_and_reloaded') or not c.get('V36_yes_schedules_and_exits') \
            or not c.get('V37_exit_path_equals_game_exit_tail') or not c.get('V38_results_shown') \
            or not c.get('V39_dialogs_outside_home_not_polled') or not c.get('V40_r21_windows_checked'):
        issues.append('r21 VM checks (V34-V40) missing')
    elif not c.get('V41_cells') or not c.get('V42_pages') or c.get('V43_states', 0) < 4 or not c.get('V43_registration_ignored') \
            or not c.get('V44_replays_ctx1') or not c.get('V44_replays_ctx2') or not c.get('V44_card_stage_paths') \
            or not c.get('V45_calendar_equal_r21') or not c.get('V45_calendar_equal_r21_stale_flag') or not c.get('V46_ways_out') \
            or c.get('V47_title_commands', 0) < 5 or not c.get('V48_page_and_request') or not c.get('S8_replay_ops_equal_ExecScene'):
        issues.append('r22 VM checks (V41-V48, S8 replay) missing')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    if st['candidate_sha256'] != after['NightRemaster.ain'] or len(st['planted_defects']) != DEFECTS or not all(p['caught'] for p in st['planted_defects']):
        issues.append('planted-defect self-test missing or failing (%d defects expected)' % DEFECTS)
    probe = read(L.EVID / 'probe_result.json') if (L.EVID / 'probe_result.json').exists() else {}
    if probe.get('candidate_sha256') != after['NightRemaster.ain'] or not probe_ok(probe):
        issues.append('native calendar tour on the r22 candidate (probe_calendar_tour_r22.py) missing or failing')
    regs = read(L.EVID / 'probe_regs.json') if (L.EVID / 'probe_regs.json').exists() else {}
    if not regs.get('saves') or any(s_.get('candidate_sha256') != after['NightRemaster.ain'] for s_ in regs['saves']):
        issues.append('real save states (probe_calendar_tour_r22.py --regs) missing or from another candidate')
    p22 = read(L.EVID / 'probe_r22.json') if (L.EVID / 'probe_r22.json').exists() else {}
    if any((p22.get(k) or {}).get('candidate_sha256') != after['NightRemaster.ain'] for k in ('title', 'home')) or not probe22_ok(p22):
        issues.append('native chart tours (probe_chart_r22.py --title / --home) missing, failing or for another candidate')
    kinds = read(L.EVID / 'replay_kinds.json') if (L.EVID / 'replay_kinds.json').exists() else {}
    if kinds.get('candidate_sha256') != after['NightRemaster.ain'] or any(e.get('candidate_sha256') != after['NightRemaster.ain'] for e in kinds.get('events', {}).values()) \
            or not kinds.get('events'):
        issues.append('per-kind replay probes (probe_chart_r22.py --kinds) missing or for another candidate')
    native = read(L.WORK / 'build' / 'native_compare.json') if (L.WORK / 'build' / 'native_compare.json').exists() else {}
    nc = native.get('counts', {})
    if native.get('candidate_sha256') != after['NightRemaster.ain'] or not nc.get('N_blocks_identical') or 'panel_same_save' not in native.get('blocks', {}) \
            or not nc.get('N_sandbox_state_equal') or not nc.get('N_r20_blocks_identical') or not nc.get('R22N_pages_equal_vm') \
            or not nc.get('R22N_title_tour') or not nc.get('R22N_home_tour') or not nc.get('R22N_kinds'):
        issues.append('native calendar / chart pages not compared with the VM (verify_chart_r22.py --native)')
    scan = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    if scan.get('status') != 'SCANNED_NO_TARGET_DETECTIONS' or scan.get('files') != after:
        issues.append('Defender scan missing or not for this candidate')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else {}
    if fx.get('status') != 'TRANSACTION_FIXTURE_PASS' or fx.get('payload') != after or not (fx.get('install_with_recovery_lacking_payload_file') or {}).get('committed'):
        issues.append('transaction fixture missing (run --fixture)')
    if not DRAFT.exists():
        issues.append('contract draft missing (run --contract)')
    else:
        d = read(DRAFT)
        if sorted(d['preserves_contracts']) != contracts_now():
            issues.append('required_*.json list changed since the contract draft: rerun --contract')
        if d['required_files'] != after:
            issues.append('contract draft is for another candidate')
    latest = read(R / 'latest_worked_translation.json')
    if latest.get('manifest_sha256') != cur['manifest_sha256'] or latest.get('ain_sha256') != base['ain_sha256'] \
            or L.sha(Path(latest['translation_map'])) != latest.get('translation_map_sha256'):
        issues.append('latest_worked_translation.json does not match the runtime')
    keep = read(R / 'required_build_retention.json')
    if L.sha(Path(keep['recovery_manifest'])) != keep['recovery_manifest_sha256']:
        issues.append('recovery runtime manifest moved')
    try:
        exact_tree(rt, read(Path(cur['manifest']))['files'])
    except AssertionError as ex:
        issues.append('runtime tree differs from its manifest: ' + str(ex)[:200])
    if E.exists():
        issues.append('evidence/chart_r22 already exists: inspect the earlier transaction')
    j21 = read(L.R21_JOURNAL) if L.R21_JOURNAL.exists() else {}
    if j21.get('status') != 'COMMITTED' or j21.get('after', {}).get('NightRemaster.ain') != L.BASE_AIN_SHA or not (R / 'required_modmenu_r21.json').exists():
        issues.append('r21 is not installed as the base expects (evidence/modmenu_r21 journal not COMMITTED or required_modmenu_r21.json missing): rebuild')
    jh = read(L.HOOK_JOURNAL) if L.HOOK_JOURNAL.exists() else {}
    if jh.get('status') != 'COMMITTED' or jh.get('after', {}).get('winmm.dll') != L.BASE_WINMM_SHA:
        issues.append('the mod-menu hook is not installed as the base expects (evidence/mod_menu_20260928 journal)')
    running = active_target(processes(), rt)
    rec = Path(keep['recovery_runtime'])
    report = dict(status=READY if not issues else 'NOT_READY', candidate=after, runtime=str(rt), base=base, issues=issues,
                  game_running=bool(running), contracts_now=len(contracts_now()),
                  recovery_runtime=str(rec), recovery_has=sorted(recovery_hashes(rec, FILES)),
                  install_command=f'python "{Path(__file__)}" --install',
                  restore_command=f'python "{Path(__file__)}" --restore', checked=datetime.datetime.now().astimezone().isoformat())
    return not issues, report


'''
s = s[:a] + READY_FN + s[b:]
# the r21 integrated / r21 tour helpers are gone from r22 (the calendar and chart tours replace them)
s = s.replace("        if (L.EVID / 'integrated').exists():\n            shutil.copytree(L.EVID / 'integrated', ev / 'source' / 'integrated')\n", '')
p.write_text(s, 'utf8')
print('publish: contract / readiness done')
