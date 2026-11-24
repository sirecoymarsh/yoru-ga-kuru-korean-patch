"""r19 (Claude Opus 5.5, 2026-09-27): PC chart v2 regenerated with the name field - prove that nothing else changed.

  python chart_dom_diff_r19.py            compare chart/yoru_flowchart_v2_r18.html (the r18-era file, kept) with the new
                                          chart/yoru_flowchart_v2.html; writes 증거/chart_dom_diff.json, exit 1 on a difference

1. data: the embedded JSON of both files. Allowed differences only: `generated`; new keys ev[*].nm/ns/nr/nk and
   cards[*].nm/tail/ref (the name field); ev[*].when of the events whose schedule.json trigger gained `feeling_gate`
   (rule 11, the same wording in the PC chart and in-game). The dialogue block must be identical.
2. DOM: the page's own self test (#selftest=review and #selftest=play: every page x view x fold state, every side panel,
   the first render, the review->play switch), dumped by headless Chrome from file:// (profile + temp on P:).
   New DOM - (elements with data-nm) - (rule-11 「언제」 strings mapped back to the old strings) - (the generated time)
   must equal the old DOM byte for byte.
"""
import sys, os, re, json, html, subprocess, time, collections
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent               # ...\r19_calendar\work
R19 = HERE.parent
FLOW = R19.parent.parent
OLD = FLOW / 'chart' / 'yoru_flowchart_v2_r18.html'
NEW = FLOW / 'chart' / 'yoru_flowchart_v2.html'
PROFILE = R19 / 'tmp' / 'chrome-prof-dom'
TMP = R19 / 'tmp'
OUT = R19 / '증거' / 'chart_dom_diff.json'
CHROMES = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']
BLOCK = r'<script type="application/json" id="%s">(.*?)</script>'
NAME_KEYS_EV = {'nm', 'ns', 'nr', 'nk'}
NAME_KEYS_CARD = {'nm', 'tail', 'ref'}


def blocks(text):
    a = re.search(BLOCK % 'yoru-data', text, re.S)
    b = re.search(BLOCK % 'yoru-dialogue', text, re.S)
    return json.loads(a.group(1)), b.group(1), text[:a.start(1)] + '@DATA@' + text[a.end(1):b.start(1)] + '@DLG@' + text[b.end(1):]


def chrome():
    for p in CHROMES:
        if os.path.exists(p):
            return p
    raise SystemExit('no Chrome/Edge')


def dump(path, h):
    PROFILE.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(TMP), TMP=str(TMP))
    url = 'file:///' + str(path).replace('\\', '/') + h
    args = [chrome(), '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-extensions',
            '--disable-sync', '--disable-background-networking', '--disable-component-update', '--user-data-dir=' + str(PROFILE),
            '--window-size=1600,1000', '--virtual-time-budget=30000', '--dump-dom', url]
    t = time.time()
    p = subprocess.run(args, capture_output=True, env=env, timeout=900)
    out = p.stdout.decode('utf-8', 'replace')
    m = re.search(r'<pre id="selftest-out">(.*?)</pre>', out, re.S)
    err = re.search(r'<pre id="errors">(.*?)</pre>', out, re.S)
    assert m and m.group(1).strip(), ('self test produced nothing', path.name, h, (err.group(1) if err else '')[:300])
    print('  chrome', path.name, h, '%.1fs' % (time.time() - t), '%.1f MB' % (len(out) / 1e6), flush=True)
    return json.loads(html.unescape(m.group(1)))


def esc(s):
    return ''.join({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}.get(c, c) for c in str(s))


NM_RE = [re.compile(r'<div class="k" data-nm="k">게임 안 이름</div><div class="v" data-nm="v">[^<]*</div>'),
         re.compile(r'<span class="note" data-nm="s">[^<]*</span> ')]


def normalise(s, when_map, gen_old, gen_new, counts):
    for rx in NM_RE:
        s, n = rx.subn('', s)
        counts['name_elements_removed'] += n
    for new, old in when_map:
        n = s.count(esc(new))
        if n:
            counts['when_strings_mapped_back'] += n
            s = s.replace(esc(new), esc(old))
    if gen_new != gen_old:
        n = s.count(gen_new)
        counts['generated_time_mapped_back'] += n
        s = s.replace(gen_new, gen_old)
    return s


def main():
    old_t, new_t = OLD.read_text('utf8'), NEW.read_text('utf8')
    od, odlg, oshell = blocks(old_t)
    nd, ndlg, nshell = blocks(new_t)
    res = dict(schema='yoru-calendar-r19.chart-dom-diff.v1', old=str(OLD), new=str(NEW))
    # ---- 1. data
    assert odlg == ndlg, 'dialogue block changed'
    diffs = []
    for k in od:
        if k in ('ev', 'cards', 'generated'):
            continue
        if od[k] != nd[k]:
            diffs.append(k)
    assert set(nd) == set(od), (set(nd) ^ set(od))
    when_changed = {}
    for i, e in od['ev'].items():
        f = nd['ev'][i]
        extra = set(f) - set(e)
        assert extra <= NAME_KEYS_EV and {'nm', 'ns', 'nr'} <= extra, (i, extra)
        for k in e:
            if k == 'when' and e[k] != f[k]:
                when_changed[i] = (e[k], f[k])
            elif e[k] != f[k]:
                diffs.append(('ev', i, k))
    for a, b in zip(od['cards'], nd['cards']):
        extra = set(b) - set(a)
        assert extra == NAME_KEYS_CARD, (a['key'], extra)
        for k in a:
            if a[k] != b[k]:
                diffs.append(('card', a['key'], k))
    assert len(od['cards']) == len(nd['cards'])
    sch = json.load(open(FLOW / 'graph' / 'schedule.json', encoding='utf-8'))
    gated = sorted(e['id'] for e in sch['events'] if any(t.get('feeling_gate') for t in e['triggers']))
    changed_ids = sorted(int(i) for i in when_changed)
    # every gated event whose V1 label lacked the person/condition changed; conditional ones already had it
    res['data'] = dict(other_differences=diffs, when_changed=len(when_changed), when_changed_events=['E%05d' % i for i in changed_ids],
                       feeling_gated_events=len(gated), generated=[od['generated'], nd['generated']],
                       shell_identical_except_template=(oshell == nshell))
    assert not diffs, diffs[:5]
    assert set(changed_ids) <= set(gated), sorted(set(changed_ids) - set(gated))
    when_map = []
    for i, (o, n) in when_changed.items():
        assert len(o) == len(n), i
        for x, y in zip(o, n):
            if x != y:
                when_map.append((y, x))
    when_map.sort(key=lambda p: -len(p[0]))
    # ---- 2. DOM
    counts = collections.Counter()
    same = {}
    for mode in ('review', 'play'):
        a = dump(OLD, '#selftest=' + mode)
        b = dump(NEW, '#selftest=' + mode)
        assert len(a['states']) == len(b['states']) and len(a['panels']) == len(b['panels'])
        for x, y in zip(a['states'], b['states']):
            assert (x['state'], x['page'], x['view']) == (y['state'], y['page'], y['view'])
            for k in ('html', 'band'):
                ok = x[k] == normalise(y[k], when_map, od['generated'], nd['generated'], counts)
                same.setdefault(mode + ':states', []).append(ok)
                if not ok and 'first_state_diff' not in res:
                    res['first_state_diff'] = dict(mode=mode, state=x['state'], page=x['page'], part=k)
        for j, (x, y) in enumerate(zip(a['panels'], b['panels'])):
            ok = x == normalise(y, when_map, od['generated'], nd['generated'], counts)
            same.setdefault(mode + ':panels', []).append(ok)
            if not ok and 'first_panel_diff' not in res:
                res['first_panel_diff'] = dict(mode=mode, index=j)
        for k in ('initial', 'after_switch'):
            if k in a:
                # body outerHTML carries the inline <script> (the template code, compared line by line below)
                strip = lambda t: re.sub(r'<script>.*?</script>', '<script>@CODE@</script>', t, flags=re.S)
                ok = strip(a[k]) == strip(normalise(b[k], when_map, od['generated'], nd['generated'], counts))
                same.setdefault(mode + ':' + k, []).append(ok)
        counts[mode + '_states'] = len(a['states'])
        counts[mode + '_panels'] = len(a['panels'])
    # the page shell (HTML + CSS + JS without the two data blocks): only the name-field code may differ
    import difflib
    changed = [l for l in difflib.unified_diff(oshell.splitlines(), nshell.splitlines(), lineterm='', n=0)
               if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    added = [l[1:] for l in changed if l[0] == '+']
    # an added line must carry the name field; a removed line must be one of the added lines without the stageName call
    extra = [l for l in changed if l[0] == '+' and not any(w in l for w in ('nameBlock', 'stageName', 'data-nm'))]
    extra += [l for l in changed if l[0] == '-' and l[1:] not in [a.replace("'</span> ' + stageName(x) + '<span class=\"w\">'", "'</span> <span class=\"w\">'") for a in added]]
    res['template_changed_lines'] = changed
    same.setdefault('template', []).append(not extra)
    res['dom'] = {k: dict(compared=len(v), identical=sum(v)) for k, v in same.items()}
    res['counts'] = dict(counts)
    res['dom_identical_except_name_field_and_rule11'] = all(all(v) for v in same.values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in res.items() if k != 'data'}, ensure_ascii=False, indent=1))
    print('data', json.dumps({k: v for k, v in res['data'].items() if k != 'when_changed_events'}, ensure_ascii=False))
    if not res['dom_identical_except_name_field_and_rule11']:
        raise SystemExit(1)
    print('CHART DOM = r18 DOM + name field + rule 11')


if __name__ == '__main__':
    main()
