"""Cross-check written scene summaries against their frozen sources (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

  python check_summary_consistency.py <month folder> [<month folder> ...] [--out-dir <folder>]

A month folder holds design/summaries.json, source/scenarios.json and design/events.json (the WI-010 layout); a folder that holds
month subfolders (calendar_jul_aug_… -> july, august) is expanded. Folders are only read. Result: <out-dir>/consistency_<time>.json
(default: checks/ next to this script); the console shows counts only (the summaries themselves stay in the file: the user is
playing the game).

Findings (severity error = must be fixed or waived by the reviewer; warning = look at it):
  (a) name_not_in_scene            a character name in the summary is not in the scene's installed Korean lines / speaker hints
      (nor, for a roster member, its Japanese name in the Japanese lines); name_only_in_metadata (warning) when the name is only in
      the event's metadata (who / head / cell / card). The name list: cast_evidence roster + cells.json names + every non-generic
      speaker hint; 「주인공」 is always allowed
  (b) number_not_in_source         a number in the summary is in neither the Japanese (digits, full-width, kanji numerals) nor the
      Korean lines of the scene; number_only_in_metadata (warning) when it is only in the event's date / condition metadata
  (c) ryo_standalone / ryo_name_particle (the protagonist's default name 료 alone or with a particle; 동료·치료·재료 are not hits),
      pronoun_geu / pronoun_geunyeo, stage_word (단계), e_number (E0…), kana, kanji, line_break, too_long (> 100), empty_summary,
      too_many_sentences (>= 3), bad_ending (a sentence not ending in 「다.」), unread_word (미열람), quote_mark (warning)
  (d) duplicate_summary (same text elsewhere, in the month or another loaded month or the approved April set) and
      duplicate_sentence (warning: one sentence repeated elsewhere)
  (e) source_sha_mismatch / message_ids_mismatch / event_not_in_scenarios (source_event_sha256 recomputed from scenarios.json)
  (f) name_from_neighbor_scene (warning) a name absent from this scene but present in another scene of the same group card
  copy_of rows (status copy_of, copy_of: <original>) skip the sentence checks; only the original is checked: copy_self,
  copy_chain, copy_target_excluded, copy_target_missing (error) / copy_target_not_loaded (warning, its month is not loaded)
  Also: duplicate_id (the same ID in two loaded folders, e.g. A/B halves), unknown_status, excluded_without_note (warning).
"""
from pathlib import Path
import argparse, collections, datetime, json, re, sys, unicodedata
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import sltools as T

CAST = T.STAGING / 'calendar_april_adaptive_minis_20260929/design/cast_evidence.json'
CELLS = T.STAGING / 'calendar_april_adaptive_minis_20260929/design/cells.json'
APRIL_SCEN = T.APRIL / 'source/scenarios.json'
KNOWN_STATUS = T.BAKE_STATUS | T.SKIP_STATUS | {T.COPY_STATUS, T.DRAFT_STATUS}
PROTAGONIST = '주인공'
DEFAULT_NAME = '료'
# speaker hints that describe a role, not a person (never used as names)
GENERIC = {'목소리', '소녀', '소년', '남자', '여자', '여자아이', '남학생', '여학생', '점원', '안내방송', '금발', '누나', '괴물', '새끼 고양이',
           '교사', '할머니', '전원', '신문배달원', '배달원', '관객', '객석', '아이들', '아이', '인영', '뱀', '행인', '전투원', '블루 이하 전원'}
PARTICLES = ['에게서', '한테서', '이지만', '에게는', '에게도', '와의', '과의', '에게', '한테', '께서', '에서', '으로', '까지', '부터', '처럼',
             '보다', '조차', '마저', '이랑', '이며', '이나', '이다', '이고', '이자', '이야', '이여', '선배', '선생', '하고', '같이',
             '이', '가', '은', '는', '을', '를', '와', '과', '의', '께', '도', '만', '랑', '로', '에', '뿐', '야', '아', '나', '며', '여',
             '씨', '님', '군', '양', '쨩', '짱', '네', '들']
PART_RE = '|'.join(sorted(PARTICLES, key=len, reverse=True))
HANGUL = '가-힣'
KANJI_DIGIT = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '两': 2}
KANJI_UNIT = {'十': 10, '百': 100, '千': 1000, '万': 10000}


def _jp_alias():
    """Korean display name -> Japanese name from the cast roster's portrait names (いずみ／楽眼鏡 -> いずみ); descriptive ones
    (鏡花の姉) are skipped."""
    out = {}
    for tag, display, _id, portrait in T.readj(CAST)['roster']:
        jp = str(portrait).split('／')[0]
        if display not in (PROTAGONIST, DEFAULT_NAME) and jp and 'の' not in jp:
            out[display] = jp
    return out


JP_ALIAS = _jp_alias()


def expand(folders):
    out = []
    for f in folders:
        f = Path(f).resolve()
        if (f / 'design/summaries.json').exists() or (f / 'source/scenarios.json').exists():
            out.append(f)
            continue
        subs = sorted(d for d in f.iterdir() if d.is_dir() and ((d / 'design/summaries.json').exists() or (d / 'source/scenarios.json').exists()))
        assert subs, ('no month folder in', str(f))
        out += subs
    return out


def split_hint(h):
    return [x.strip() for x in re.split(r'[·＆&　]+|\s{2,}', h) if x.strip()]


def is_generic(h):
    base = re.sub(r'\s+([A-Z]|\d+)$', '', h)
    return base in GENERIC or '복면' in base or base.endswith('남학생') or base.endswith('여학생')


def name_list(hint_counter):
    names = collections.defaultdict(set)
    cast = T.readj(CAST)
    for tag, display, *_ in cast['roster']:
        for n in (tag, display):
            if n not in (PROTAGONIST, DEFAULT_NAME):
                names[n].add('cast_evidence.roster')
    roster = set(names)
    for c in T.readj(CELLS):
        for tok in re.split(r'[\s·,()/\n]+', c['name']):
            tok = re.sub(r'(와|과)$', '', tok)
            if tok in roster:
                names[tok].add('cells.json')
    skipped = set()
    for h in hint_counter:
        for part in split_hint(h):
            if part in (PROTAGONIST, DEFAULT_NAME):
                continue
            if is_generic(part):
                skipped.add(part)
                continue
            names[part].add('speaker_hint')
            words = part.split()
            if len(words) > 1:
                for w in words:
                    if len(w) >= 3 and not is_generic(w):
                        names[w].add('speaker_hint part')
    return {k: sorted(v) for k, v in sorted(names.items())}, sorted(skipped)


def name_regex(names):
    alts = '|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf'(?<![{HANGUL}])({alts})(?=$|[^{HANGUL}]|(?:{PART_RE}))')


def kanji_numbers(s):
    out = set()
    for run in re.findall(r'[〇零一二三四五六七八九十百千万两]+', s):
        total, section, digit = 0, 0, None
        for ch in run:
            if ch in KANJI_DIGIT:
                if digit is not None:              # 二〇二六-style positional run
                    digit = digit * 10 + KANJI_DIGIT[ch]
                else:
                    digit = KANJI_DIGIT[ch]
            elif ch in KANJI_UNIT:
                unit = KANJI_UNIT[ch]
                if unit == 10000:
                    total += (section + (digit or 0)) * unit
                    section = 0
                else:
                    section += (digit if digit is not None else 1) * unit
                digit = None
        total += section + (digit or 0)
        out.add(total)
    return out


def numbers_in(s):
    s = unicodedata.normalize('NFKC', s or '')
    return {int(x) for x in re.findall(r'\d+', s)} | kanji_numbers(s)


def sentences(t):
    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', t.strip()) if p.strip()]
    return parts


def norm(s):
    return re.sub(r'\s+', '', s)


def load_folder(f):
    d = dict(folder=str(f), name=f.name if f.name not in ('july', 'august', 'september', 'other') else f.parent.name + '/' + f.name)
    sp, sc, ev = f / 'design/summaries.json', f / 'source/scenarios.json', f / 'design/events.json'
    d['summaries_path'] = str(sp) if sp.exists() else None
    d['summaries'] = T.readj(sp) if sp.exists() else None
    d['scenarios'] = {int(e['no']): e for e in T.readj(sc)['events']} if sc.exists() else {}
    d['scenarios_sha256'] = T.L.sha(sc) if sc.exists() else None
    d['summaries_sha256'] = T.L.sha(sp) if sp.exists() else None
    evs = T.readj(ev) if ev.exists() else {}
    d['events'] = {int(k): v for k, v in evs.items()} if isinstance(evs, dict) else {int(e['no']): e for e in evs}
    return d


def run(folders, include_april=True):
    folders = expand(folders)
    docs = [load_folder(f) for f in folders]
    hints = collections.Counter()
    for d in docs:
        for row in d['scenarios'].values():
            for l in row['lines']:
                if l.get('speaker_hint'):
                    hints[l['speaker_hint']] += 1
    april_rows = {int(e['no']): e for e in T.readj(APRIL_SCEN)['events']}
    for row in april_rows.values():
        for l in row['lines']:
            if l.get('speaker_hint'):
                hints[l['speaker_hint']] += 1
    names, skipped = name_list(hints)
    nre = name_regex(names)
    scen_all = {}
    for d in docs:
        scen_all.update(d['scenarios'])
    events_all = {}
    for d in docs:
        events_all.update(d['events'])
    april = T.april_texts() if include_april else {}
    findings = []
    stats = []
    seen_ids = {}
    texts_at = collections.defaultdict(list)       # normalized summary -> [(where)]
    sentence_at = collections.defaultdict(list)    # normalized sentence -> [(where)]
    rows_all = {}                                  # no -> (doc, event, index)
    for n, t in april.items():
        texts_at[norm(t)].append(dict(folder='calendar_april_summary_20260929 (approved)', no=n))
        for i, s in enumerate(sentences(t)):
            sentence_at[norm(s)].append(dict(folder='calendar_april_summary_20260929 (approved)', no=n, sentence=i))

    def add(d, idx, no, typ, sev, token=None, summary=None, **ev):
        findings.append(dict(folder=d['name'], file=d['summaries_path'], index=idx, no=no, type=typ, severity=sev, token=token,
                             summary=summary, evidence=ev or None))

    for d in docs:
        st = dict(folder=d['name'], path=d['folder'], summaries=d['summaries_path'], summaries_sha256=d['summaries_sha256'],
                  scenarios_sha256=d['scenarios_sha256'], scenario_events=len(d['scenarios']), rows=0,
                  status=collections.Counter(), checked=0)
        stats.append(st)
        if not d['summaries']:
            continue
        for idx, e in enumerate(d['summaries'].get('events', [])):
            no = int(e['no'])
            st['rows'] += 1
            status = e.get('status')
            st['status'][status] += 1
            s = e.get('summary') or ''
            if no in seen_ids:
                add(d, idx, no, 'duplicate_id', 'error', other=seen_ids[no])
            seen_ids[no] = f"{d['name']}#{idx}"
            rows_all[no] = (d, e, idx)
            if status not in KNOWN_STATUS:
                add(d, idx, no, 'unknown_status', 'error', token=str(status))
            # (e) source binding
            row = d['scenarios'].get(no)
            if row is None:
                add(d, idx, no, 'event_not_in_scenarios', 'error')
            else:
                if e.get('source_message_ids') != [l['m'] for l in row['lines']]:
                    add(d, idx, no, 'message_ids_mismatch', 'error')
                if e.get('source_event_sha256') != T.event_sha(row):
                    add(d, idx, no, 'source_sha_mismatch', 'error', recomputed=T.event_sha(row), recorded=e.get('source_event_sha256'))
            if status in T.SKIP_STATUS:
                if not (e.get('note') or '').strip():
                    add(d, idx, no, 'excluded_without_note', 'warning')
                continue
            if status == T.COPY_STATUS:
                continue                            # resolved after every folder is loaded
            st['checked'] += 1
            # (c) form
            if not s.strip():
                add(d, idx, no, 'empty_summary', 'error')
                continue
            if any(c in s for c in '\n\r'):
                add(d, idx, no, 'line_break', 'error', summary=s)
            if len(s) > T.MAX_LEN:
                add(d, idx, no, 'too_long', 'error', token=str(len(s)), summary=s)
            for z in re.finditer(rf'(?<![{HANGUL}])료(?![{HANGUL}])', s):
                add(d, idx, no, 'ryo_standalone', 'error', token='료', summary=s, at=z.start())
            for z in re.finditer(rf'(?<![{HANGUL}])료(?=(?:{PART_RE})(?![{HANGUL}]))', s):
                add(d, idx, no, 'ryo_name_particle', 'error', token=s[z.start():z.start() + 4].split(' ')[0], summary=s, at=z.start())
            for z in re.finditer(rf'(?<![{HANGUL}])그(가|는|를|의|와|에게|에게서|한테|한테서|도|와의|에게는|에게도)(?![{HANGUL}])', s):
                add(d, idx, no, 'pronoun_geu', 'error', token=z[0], summary=s, at=z.start())
            for z in re.finditer(rf'(?<![{HANGUL}])그녀', s):
                add(d, idx, no, 'pronoun_geunyeo', 'error', token='그녀', summary=s, at=z.start())
            if '단계' in s:
                add(d, idx, no, 'stage_word', 'error', token='단계', summary=s)
            if re.search(r'E0|E\d{3,}', s):
                add(d, idx, no, 'e_number', 'error', token=re.search(r'E0\d*|E\d{3,}', s)[0], summary=s)
            if re.search(r'[぀-ヿㇰ-ㇿｦ-ﾟ]', s):
                add(d, idx, no, 'kana', 'error', token=re.search(r'[぀-ヿㇰ-ㇿｦ-ﾟ]+', s)[0], summary=s)
            if re.search(r'[㐀-䶿一-鿿豈-﫿]', s):
                add(d, idx, no, 'kanji', 'error', token=re.search(r'[㐀-䶿一-鿿豈-﫿]+', s)[0], summary=s)
            if '미열람' in s:
                add(d, idx, no, 'unread_word', 'error', token='미열람', summary=s)
            if re.search(r'[「」『』“”"‘’\']', s):
                add(d, idx, no, 'quote_mark', 'warning', token=re.search(r'[「」『』“”"‘’\']', s)[0], summary=s)
            sents = sentences(s)
            if len(sents) >= 3:
                add(d, idx, no, 'too_many_sentences', 'error', token=str(len(sents)), summary=s)
            for i, x in enumerate(sents):
                if not x.endswith('다.'):
                    add(d, idx, no, 'bad_ending', 'error', token=x[-3:], summary=s, sentence=i)
            # (a) + (f) names
            scene_text = ''
            scene_hints = set()
            if row is not None:
                scene_text = '\n'.join(l.get('kr') or '' for l in row['lines'])
                for l in row['lines']:
                    if l.get('speaker_hint'):
                        scene_hints.update(split_hint(l['speaker_hint']))
            found = []
            for z in nre.finditer(s):
                if z[1] not in found and row is not None:      # no frozen scene: already event_not_in_scenarios
                    found.append(z[1])
            card = (d['events'].get(no) or {}).get('card') or {}
            neighbors = [x for x in (card.get('stages') or []) if x != no]
            meta = d['events'].get(no) or {}
            meta_text = ' '.join(str(meta.get(k) or '') for k in ('when', 'who', 'head', 'short')) + ' ' + \
                json.dumps(meta.get('cell') or {}, ensure_ascii=False) + ' ' + json.dumps(meta.get('card') or {}, ensure_ascii=False)
            jp_text = '\n'.join(l.get('jp') or '' for l in row['lines']) if row is not None else ''
            for nm in found:
                if nm in scene_text or nm in scene_hints:
                    continue
                alias = JP_ALIAS.get(nm)
                if alias and alias in jp_text:
                    continue                        # the Japanese line names the person; the Korean line says it otherwise
                if nm in meta_text:
                    add(d, idx, no, 'name_only_in_metadata', 'warning', token=nm, summary=s,
                        scene_messages=len(row['lines']) if row else 0)
                    continue
                add(d, idx, no, 'name_not_in_scene', 'error', token=nm, summary=s,
                    scene_messages=len(row['lines']) if row else 0)
                hits = []
                for nb in neighbors:
                    r2 = scen_all.get(nb)
                    if not r2:
                        continue
                    m = next((l['m'] for l in r2['lines'] if nm in (l.get('kr') or '') or nm in split_hint(l.get('speaker_hint') or '')), None)
                    if m is not None:
                        hits.append(dict(no=nb, message_id=m))
                if hits:
                    add(d, idx, no, 'name_from_neighbor_scene', 'warning', token=nm, summary=s, neighbors=hits, card=card.get('k'))
            # (b) numbers
            nums = {int(x) for x in re.findall(r'\d+', unicodedata.normalize('NFKC', s))}
            if nums and row is not None:
                src_nums = set()
                if row is not None:
                    for l in row['lines']:
                        src_nums |= numbers_in(l.get('jp')) | numbers_in(l.get('kr'))
                meta = d['events'].get(no) or {}
                meta_text = ' '.join(str(meta.get(k) or '') for k in ('when', 'head', 'short')) + ' ' + json.dumps(meta.get('cell') or {}, ensure_ascii=False) \
                    + ' ' + json.dumps(meta.get('card') or {}, ensure_ascii=False)
                meta_nums = numbers_in(meta_text)
                for x in sorted(nums):
                    if x in src_nums:
                        continue
                    if x in meta_nums:
                        add(d, idx, no, 'number_only_in_metadata', 'warning', token=str(x), summary=s)
                    else:
                        add(d, idx, no, 'number_not_in_source', 'error', token=str(x), summary=s,
                            scene_messages=len(row['lines']) if row else 0)
            # (d) duplicates (collected; reported below)
            where = dict(folder=d['name'], no=no)
            texts_at[norm(s)].append(where)
            for i, x in enumerate(sents):
                sentence_at[norm(x)].append(dict(where, sentence=i))
        st['status'] = dict(st['status'])
    # copy_of rows
    have_text = {n for n, (d, e, i) in rows_all.items() if e.get('status') not in T.SKIP_STATUS and e.get('status') != T.COPY_STATUS
                 and (e.get('summary') or '').strip()} | set(april) | {11}
    for n, (d, e, idx) in rows_all.items():
        if e.get('status') != T.COPY_STATUS:
            continue
        o = e.get('copy_of')
        if not isinstance(o, int) or isinstance(o, bool):
            add(d, idx, n, 'copy_bad_target', 'error', token=str(o))
        elif o == n:
            add(d, idx, n, 'copy_self', 'error', token=str(o))
        elif o in rows_all and rows_all[o][1].get('status') == T.COPY_STATUS:
            add(d, idx, n, 'copy_chain', 'error', token=str(o), next=rows_all[o][1].get('copy_of'))
        elif o in rows_all and rows_all[o][1].get('status') in T.SKIP_STATUS:
            add(d, idx, n, 'copy_target_excluded', 'error', token=str(o))
        elif o in have_text:
            pass
        elif o in scen_all or o in rows_all:
            add(d, idx, n, 'copy_target_missing', 'error', token=str(o))
        else:
            add(d, idx, n, 'copy_target_not_loaded', 'warning', token=str(o), tab=T.tab_of().get(o))
    # (d) duplicates
    for key_, places in texts_at.items():
        mine = [p for p in places if 'approved' not in p['folder']]
        if len(places) > 1 and mine:
            for p in mine:
                d, e, idx = rows_all[p['no']]
                add(d, idx, p['no'], 'duplicate_summary', 'error', summary=e.get('summary'),
                    others=[q for q in places if q is not p])
    dup_whole = {norm(e.get('summary') or '') for n, (d, e, i) in rows_all.items()} & {k for k, v in texts_at.items() if len(v) > 1}
    for key_, places in sentence_at.items():
        mine = [p for p in places if 'approved' not in p['folder']]
        if len(places) > 1 and mine:
            for p in mine:
                d, e, idx = rows_all[p['no']]
                if norm(e.get('summary') or '') in dup_whole:
                    continue
                add(d, idx, p['no'], 'duplicate_sentence', 'warning', summary=e.get('summary'), sentence=p['sentence'],
                    others=[q for q in places if q is not p])
    by_type = collections.Counter(f['type'] for f in findings)
    by_sev = collections.Counter(f['severity'] for f in findings)
    by_folder = collections.defaultdict(collections.Counter)
    for f in findings:
        by_folder[f['folder']][f['severity']] += 1
    return dict(tool='check_summary_consistency.py', author=T.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
                folders=stats, april_reference=include_april, name_list=names, generic_hints_skipped=skipped,
                counts=dict(by_severity=dict(by_sev), by_type=dict(sorted(by_type.items())),
                            by_folder={k: dict(v) for k, v in by_folder.items()}),
                findings=findings)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('folders', nargs='+')
    ap.add_argument('--out-dir', default=str(H / 'checks'))
    ap.add_argument('--no-april', action='store_true', help='do not compare against the approved April summaries')
    a = ap.parse_args(argv)
    res = run([Path(f) for f in a.folders], include_april=not a.no_april)
    out = Path(a.out_dir).resolve()
    T.assert_writable(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ('consistency_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
    T.writej(path, res)
    for st in res['folders']:
        c = res['counts']['by_folder'].get(st['folder'], {})
        print(f"{st['folder']}: rows={st['rows']} checked={st['checked']} status={st['status']} errors={c.get('error', 0)} warnings={c.get('warning', 0)}")
    print('by_type', res['counts']['by_type'])
    print('result', path)
    return res


if __name__ == '__main__':
    main()
