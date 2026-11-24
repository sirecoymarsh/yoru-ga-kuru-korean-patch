def run():
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    before = user_state()
    setup_folder()
    key = L.save_records(L.SAVES / HOME_SAVE)['key']
    info = build_probe(key, PROBE / 'work')
    savename = f'SaveData_HomeProbe_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    savedir.mkdir(parents=True)
    for n in COPY_GLOBAL:
        if (L.SAVES / n).exists():
            shutil.copy2(L.SAVES / n, savedir / n)
    shutil.copy2(L.SAVES / HOME_SAVE, savedir / HOME_SAVE)
    (RUN / 'claude_probe_save.txt').write_bytes(HOME_SAVE.encode('cp932'))
    (RUN / 'claude_probe_stage.txt').write_bytes(b'home0')
    t0 = time.time()
    result = launch(timeout=900)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['shots'] = collect_shots()
    result.update(save=HOME_SAVE, save_folder=str(savedir), probe=info, candidate_ain=L.sha(O / 'NightRemaster.ain'), candidate_pact=L.sha(PACT))
    result['fails'] = [x for x in result['log'] if x.startswith('FAIL ')]
    result['oks'] = len([x for x in result['log'] if x.startswith('OK ')])
    result['ended'] = 'END' in result['log']
    result['user_save_folder_unchanged'] = before == user_state()
    L.EVID.mkdir(parents=True, exist_ok=True)
    L.writej(L.EVID / f'probe_home_{stamp}.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(result['log'][-60:]))


if __name__ == '__main__':
    run()
