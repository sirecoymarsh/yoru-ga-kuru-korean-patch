"""r20 one-off: the full probe runs twice (home save, then the partner-select save); blocks parse the r20 kinds; the result
records the r20 screens (parts counts, pixel identity of the home before/after the member screen)."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'probe_calendar_r20.py'
s = p.read_text(encoding='utf8')
assert 'partner_run' not in s, 'already patched'


def rep(a, b, count=1):
    global s
    assert s.count(a) == count, (a[:80], s.count(a))
    s = s.replace(a, b)


rep('''    elif args:
        saves = args[:1]
    elif (L.WORK / 'probe_pick.json').exists():
        saves = [L.readj(L.WORK / 'probe_pick.json')['save']]
    else:
        saves = home_saves()[-1:]''',
    '''    elif args:
        saves = args[:1]
    elif (L.WORK / 'probe_pick.json').exists():
        saves = [L.readj(L.WORK / 'probe_pick.json')['save']]
    else:
        saves = home_saves()[-1:]
    if mode == 'full':
        saves = saves + [PARTNER_SAVE]          # r20 run 2: the Saturday partner selection''')
rep("""        (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
            probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=save, mode=mode, author=L.AUTHOR,
            input='Resume of a copied home-base save; user input patched off; dialogs answered by KR_CalProbeTick.'), ensure_ascii=False, indent=1), 'utf8')""",
    """        (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
            probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=save, mode=mode, author=L.AUTHOR,
            input='Resume of a copied save; user input patched off; dialogs answered by KR_CalProbeTick; the r20 screens driven by '
                  'KR_CPTick2 (IsClickCancelOtherMouse) with EndWaitForClick codes; the partner hover and the member-view hover '
                  'simulated (GetOnmouseChara / SetInfo + Show).'), ensure_ascii=False, indent=1), 'utf8')""")
# screenshots: converted after EACH run (the next run's folder setup deletes cal_*.bmp)
rep("""        r = run_one(save, mode, info, f'{stamp0}_{i:02d}')""",
    """        r = run_one(save, mode, info, f'{stamp0}_{i:02d}')
        r['shots_taken'] = collect_shots(mode)""")
rep("""    result = dict(results[0], **common)
    shots = []
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    for b in sorted(RUN.glob('cal_*.bmp')):
        png = dest / (b.stem + ('_savefoldertest' if mode == 'savefolder' else '') + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    result['screenshots'] = shots""",
    """    result = dict(results[0], **common)
    dest = L.EVID / 'probe'
    result['screenshots'] = [s_ for r_ in results for s_ in r_.get('shots_taken', [])]""")
rep('''def run_one(save, mode, info_builder, stamp):''',
    '''def collect_shots(mode):
    """cal_*.bmp of the run that just ended -> 증거/probe/*.png (removed from run/)."""
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('cal_*.bmp')):
        png = dest / (b.stem + ('_savefoldertest' if mode == 'savefolder' else '') + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    return shots


def run_one(save, mode, info_builder, stamp):''')
rep("""    result = dict(results[0], **common)""",
    """    result = dict(results[0], **common)
    if mode == 'full':
        pr = results[1]
        result['partner_run'] = dict(save=pr['save'], exit_code=pr.get('exit_code'), seconds=pr.get('seconds'), log=pr['log'],
                                     vm_error=pr.get('vm_error'), message=pr.get('message'), events=pr.get('events'),
                                     save_folder=pr.get('save_folder'), shots=pr.get('shots_taken'))""")
rep("""        result['sandbox']['temp_file_on_disk_at_end'] = [n for n in result['sandbox']['files_at_end'] if 'KRReplay' in n]""",
    """        result['sandbox']['temp_file_on_disk_at_end'] = [n for n in result['sandbox']['files_at_end'] if 'KRReplay' in n]
        a, b = dest / 'cal_home_r20_before.png', dest / 'cal_home_r20_after.png'
        if a.exists() and b.exists():
            result['home_before_after_member'] = diff_pixels(a, b)
        a2 = dest / 'cal_home_before.png'
        if a.exists() and a2.exists():
            result['home_r20_before_vs_calendar_home_before'] = diff_pixels(a, a2)
        result['r20'] = r20_report(result['log'], result['partner_run']['log'])""")
# block parser: the r20 kinds
rep("""        z = re.match(r'(TITLE|ROWS|PANEL|STATE) (.*) <<<$', log[i])""",
    """        z = re.match(r'(TITLE|ROWS|PANEL|STATE|STTEXT|STCALC|TRCALC|TRTEXT) (.*) <<<$', log[i])""")
rep('''def parse_state(text):''',
    '''def r20_report(log, plog):
    """Parts counts after every r20 step (ours = our fixed-number parts; the three activities' own part counts), the event
    page texts, the partner labels and their brightness."""
    counts = [l for l in log + plog if l.startswith('COUNT ')]
    def ours(tag):
        hits = [l for l in counts if l.startswith('COUNT ' + tag + ' ')]
        assert hits, ('no COUNT line', tag)
        z = re.search(r' ours=(\\d+) charastatus=(\\d+) selectally=(\\d+) homemember=(\\d+)', hits[-1])
        return dict(ours=int(z.group(1)), charastatus=int(z.group(2)), selectally=int(z.group(3)), homemember=int(z.group(4)))
    b = blocks(log)
    pb = blocks(plog)
    mul = {}
    for l in plog:
        z = re.match(r'TRMUL (\\w+) (\\d) (\\d+) box=(\\d)', l)
        if z:
            mul.setdefault(z.group(1), {})[int(z.group(2))] = (int(z.group(3)), int(z.group(4)))
    rep_ = dict(counts=counts,
                status=dict(page1=ours('S1 page1'), page4=ours('S4 page4 A'), page4_next_person=ours('S4 page4 B (next person)'),
                            page3_from4=ours('S3B page3 (prev from 4)'), page4_from3=ours('S4C page4 (next from 3)'),
                            page1_from4=ours('S1B page1 (next from 4)'), page4_from1=ours('S4D page4 (prev from 1)'),
                            after_exit1=ours('AFTER EXIT 1'), second_entry_page4=ours('T4 page4 C (second entry)'),
                            after_exit2=ours('AFTER EXIT 2'), home_after=ours('HOME after the member screen'),
                            home_before=ours('HOME before')),
                status_texts={t: b.get(('STTEXT', t)) for t in ('A', 'B', 'C')},
                status_charas={l.split()[1]: int(l.split()[2]) for l in log if l.startswith('STCHARA ')},
                partner=dict(first=ours('PARTNER 1'), dialog1=ours('CONFIRM DIALOG ptdlg1'), again=ours('PARTNER 2 (entered again)'),
                             dialog2=ours('CONFIRM DIALOG ptdlg2'), after_screen=ours('FIRST MESSAGE AFTER THE PARTNER SCREEN')),
                partner_labels={tag: {k[1]: v for k, v in pb.items() if k[0] == 'TRTEXT' and k[1].startswith(tag + ' ')} for tag in ('P0', 'PA', 'PB', 'P2')},
                partner_mul=mul, partner_calc={k[1]: v for k, v in pb.items() if k[0] in ('STCALC', 'TRCALC')},
                partner_date=next((l for l in plog if l.startswith('PARTNER date=')), None),
                event_page_ms=next((l for l in log if l.startswith('EVENT PAGE shown after')), None))
    return rep_


def parse_state(text):''')
p.write_text(s, encoding='utf8')
print('patched', p)
