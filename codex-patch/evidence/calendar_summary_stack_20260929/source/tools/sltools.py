"""Shared helpers of the monthly summary-layer tools (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

A summary layer puts the approved scene summaries of one month (or any batch of stable event IDs) on top of the current story
getter of the event-calendar detail board (after WI-009: `string KR_W29Story(int no)`), append-only:

    KR_ST<tag>StoryBase(no)  = byte-for-byte clone of the getter's current body (same arguments, locals, return type)
    KR_ST<tag>Story(no)      = sorted binary if-tree of the layer's summaries; a copy_of scene calls KR_ST<tag>Story(<original>);
                               every miss falls through to KR_ST<tag>StoryBase(no)
    <getter>(no)             = one-line forwarder to KR_ST<tag>Story(no) (index, arguments, locals, return type kept)

Layers stack: the next layer clones the forwarder of the previous one as its Base, so the lookup walks down the chain.
The r24 library (read-only reference) supplies the AIN / alice / proxy-encoding helpers: L.read_meta, L.raw_symbol, L.jaf_literal_encode.
Nothing here writes outside the folder a caller passes in.
"""
from pathlib import Path
import hashlib, json, re, sys
sys.dont_write_bytecode = True
F = Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')     # read-only reference library
if str(F) not in sys.path:
    sys.path.insert(0, str(F))
import r24lib as L

TOOLS = Path(__file__).resolve().parent
R = L.CODEX
STAGING = R / 'staging'
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
TOOL_NAME = 'calendar_summary_layer_tools_20260929'
PY = 'P:/AI/forge/venv/Scripts/python.exe'
SUPPORT = R / 'docs/agentic-workflow/handoffs/calendar_remaining_20260929_support'
SCOPE = SUPPORT / 'remaining_scope.json'
APRIL = STAGING / 'calendar_april_summary_20260929'
APRIL_SUMMARIES = APRIL / 'design/summaries.json'
R15 = APRIL / 'design/r15_tables.json'
TAG_RE = re.compile(r'[0-9A-Za-z]{2}')
MAX_LEN = 100
BAKE_STATUS = {'source_qa_pass', 'independent_qa_pass'}   # what a real layer bakes (independent_qa_pass: months after an
                                                          # independent read-only review)
SKIP_STATUS = {'excluded'}                        # never baked
COPY_STATUS = 'copy_of'                           # a scene that shows the summary of another scene (e.g. recollection replays)
DRAFT_STATUS = 'draft'                            # baked only by a --dry-run build with --allow-draft
JAF_TYPES = {10: 'int', 11: 'float', 12: 'string', 47: 'bool'}
JAF_DEFAULT = {'int': '0', 'float': '0.0', 'string': '""', 'bool': 'false'}


def readj(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def writej(p, value):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def event_sha(row):
    """April build / authoring brief: sha256 of the scenarios.json row, keys sorted, UTF-8."""
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def prefix(tag):
    assert TAG_RE.fullmatch(tag), ('tag must be two ASCII letters or digits', tag)
    return 'KR_ST' + tag


def names(tag):
    p = prefix(tag)
    return p + 'Story', p + 'StoryBase'


def key(tag):
    return f'calendar_{tag}_summaries_20260929'


# ---------------------------------------------------------------- event universe / protected summaries
def scope():
    return readj(SCOPE)


def all_event_ids():
    return {int(n) for n in readj(R15)['events']}


def tab_of():
    out = {}
    for t in scope()['tabs']:
        for n in t['event_ids']:
            out[int(n)] = t['tab']
    return out


def tab_names():
    return {t['tab']: t['name'] for t in scope()['tabs']}


def cards():
    return readj(R15)['cards']


def authored_before():
    """IDs that had a summary before the monthly layers: April 146 (KR_AS29Story) + E00011 (KR_P29Story)."""
    return sorted({int(n) for t in scope()['tabs'] for n in t['authored_summary_ids']})


def april_texts():
    return {int(e['no']): e['summary'] for e in readj(APRIL_SUMMARIES)['events']}


# ---------------------------------------------------------------- summary text gate
def text_problems(t):
    """Why a summary text cannot be baked as a JAF string literal shown on the board (empty list = ok)."""
    bad = []
    if not isinstance(t, str) or not t.strip():
        return ['empty']
    if t != t.strip():
        bad.append('leading/trailing space')
    if any(c in t for c in '\n\r'):
        bad.append('line break')
    if any(ord(c) < 0x20 or ord(c) == 0x7f for c in t):
        bad.append('control character')
    if len(t) > MAX_LEN:
        bad.append(f'longer than {MAX_LEN} ({len(t)})')
    if '"' in t or '\\' in t:
        bad.append('double quote or backslash (JAF literal)')
    alphabet = L.proxy_alphabet()
    for c in sorted(set(t)):
        if c in alphabet:
            continue
        try:
            c.encode('cp932')
        except UnicodeEncodeError:
            bad.append(f'U+{ord(c):04X} has no proxy glyph and no cp932 code')
    return bad


# ---------------------------------------------------------------- summaries loading (build / probe / verify share this)
def default_scenarios(summaries_path):
    return Path(summaries_path).resolve().parent.parent / 'source' / 'scenarios.json'


def load_layer(summary_paths, scenario_paths=None, allow_draft=False, require_source=True):
    """Merge one or more summaries.json files (4월 form: events[{no, summary, source_message_ids, source_event_sha256, status}]).
    Returns dict(texts={no: text}, copies={no: original}, excluded=[...], files=[per-file record]).
    Gates: known status only; excluded never baked; a draft only with allow_draft; unique IDs across all files (A/B halves merged in
    ID order); text gate; source_message_ids / source_event_sha256 re-derived from the frozen scenarios.json when present."""
    scenario_paths = list(scenario_paths or [])
    assert not scenario_paths or len(scenario_paths) == len(summary_paths), '--scenarios must be aligned with --summaries'
    texts, copies, excluded, files, seen, origin = {}, {}, [], [], {}, {}
    problems = []
    for i, sp in enumerate(summary_paths):
        sp = Path(sp).resolve()
        doc = readj(sp)
        scp = Path(scenario_paths[i]).resolve() if scenario_paths else default_scenarios(sp)
        rows = None
        if scp.exists():
            rows = {int(e['no']): e for e in readj(scp)['events']}
        elif require_source:
            raise AssertionError(('frozen scenarios.json not found next to the summaries', str(sp), str(scp)))
        rec = dict(path=str(sp), sha256=L.sha(sp), scenarios=str(scp) if rows is not None else None,
                   scenarios_sha256=L.sha(scp) if rows is not None else None,
                   translator_model=doc.get('translator_model'), author=doc.get('author'), events=len(doc.get('events', [])),
                   baked=0, copies=0, excluded=0, drafts=0)
        for e in doc.get('events', []):
            n = int(e['no'])
            where = f'{sp.name}#{n}'
            if n in seen:
                problems.append(f'duplicate ID {n} in {seen[n]} and {sp}')
                continue
            seen[n] = str(sp)
            st = e.get('status')
            if rows is not None:
                if n not in rows:
                    problems.append(f'{where}: not in the frozen scenarios')
                else:
                    if e.get('source_message_ids') != [r['m'] for r in rows[n]['lines']]:
                        problems.append(f'{where}: source_message_ids differ from the frozen scenarios')
                    if e.get('source_event_sha256') != event_sha(rows[n]):
                        problems.append(f'{where}: source_event_sha256 differs from the frozen scenarios')
            if st in SKIP_STATUS:
                excluded.append(n)
                rec['excluded'] += 1
                continue
            if st == COPY_STATUS:
                o = e.get('copy_of')
                if not isinstance(o, int) or isinstance(o, bool):
                    problems.append(f'{where}: copy_of must be an event number')
                    continue
                copies[n] = o
                rec['copies'] += 1
                continue
            if st == DRAFT_STATUS:
                if not allow_draft:
                    problems.append(f'{where}: status draft (only a --dry-run build may bake drafts)')
                    continue
                rec['drafts'] += 1
            elif st not in BAKE_STATUS:
                problems.append(f'{where}: unknown status {st!r}')
                continue
            bad = text_problems(e.get('summary'))
            if bad:
                problems.append(f'{where}: ' + '; '.join(bad))
                continue
            texts[n] = e['summary']
            origin[n] = str(sp)
            rec['baked'] += 1
        files.append(rec)
    # copy_of: no self reference, no chain, no excluded target (the target text itself is resolved by the caller: this layer, the
    # April set or a lower layer)
    for n, o in sorted(copies.items()):
        if o == n:
            problems.append(f'copy_of self reference {n}')
        elif o in copies:
            problems.append(f'copy_of chain {n} -> {o} -> {copies[o]} (point at the original scene)')
        elif o in excluded:
            problems.append(f'copy_of {n} -> excluded {o}')
    assert not problems, problems
    return dict(texts=dict(sorted(texts.items())), copies=dict(sorted(copies.items())), excluded=sorted(excluded), files=files,
                origin=origin)


# ---------------------------------------------------------------- term-alignment patch (coordinator 09-29)
CONF_RANK = {'low': 0, 'medium': 1, 'high': 2}
JOSA_PAIRS = [('이랑', '랑'), ('이나', '나'), ('이며', '며'), ('으로', '로'), ('이', '가'), ('은', '는'), ('을', '를'), ('과', '와')]
JOSA_TAILS = ('의', '는', '도', '만', '부터', '서', '써')


def _jong(ch):
    code = ord(ch) - 0xAC00
    return code % 28 if 0 <= code < 11172 else None


def josa_problems(text, words):
    """Particles right after `words` that do not agree with the word's last syllable (받침): 이/가, 은/는, 을/를, 과/와, 으로/로
    (ㄹ받침 + 로), 이랑/랑, 이나/나, 이며/며. A particle counts only when a non-Hangul character or a short tail (의 는 도 만 …)
    follows it, so 「히카리다」 or 「참된 달빛」 are not particles."""
    out = []
    for w in sorted(set(x for x in words if x), key=len, reverse=True):
        for z in re.finditer(re.escape(w), text):
            jong = _jong(text[z.end() - 1])
            if jong is None:
                continue
            rest = text[z.end():]
            for a, b in JOSA_PAIRS:
                hit = None
                for form, after_consonant in ((a, True), (b, False)):
                    if rest.startswith(form):
                        tail = rest[len(form):]
                        if not tail or not ('가' <= tail[0] <= '힣') or tail.startswith(JOSA_TAILS):
                            hit = (form, after_consonant)
                            break
                if hit:
                    form, after_consonant = hit
                    ok = (jong != 0) == after_consonant
                    if (a, b) == ('으로', '로') and jong == 8:
                        ok = form == '로'
                    if not ok:
                        out.append(f'{w}+{form}')
                    break
    return out


def load_terms(path):
    """term_alignment.json -> {resolved summaries path: {no: event entry}}, the default terms, the document."""
    doc = readj(path)
    by_file = {}
    for name, f in doc['folders'].items():
        p = (R / f['summaries_path']).resolve()
        by_file[str(p)] = dict(folder=name, author=f.get('author'), file_sha_at_audit=f.get('summaries_file_sha256_at_build'),
                               events={int(e['no']): e for e in f.get('events', [])})
    words = [t['default'] for t in doc.get('terms', [])]
    return by_file, words, doc


def apply_terms(layer, term_path, threshold='high', strict=False):
    """Apply the term-alignment proposals of `threshold` or higher to layer['texts'] (a copy). Per summary: the current text's
    sha256 must equal the audited summary_sha256 (else skipped with a warning); each `before` must occur exactly once (else that
    proposal is skipped); the patched text must pass text_problems() and the particle check (else that summary keeps its approved
    text and is listed in gate_skipped; strict=True stops instead). The summaries files are never modified. Returns (texts, record)."""
    assert threshold in CONF_RANK, threshold
    by_file, words, doc = load_terms(term_path)
    texts = dict(layer['texts'])
    rec = dict(term_file=str(Path(term_path).resolve()), term_file_sha256=L.sha(term_path), generated_by=doc.get('generated_by'),
               threshold=threshold, strict=strict, files=[], events=[], applied=0, skipped_proposals=0, skipped_summaries=0,
               below_threshold=0, changed_ids=[], gate_skipped=[])
    failures = []
    for f in layer['files']:
        entry = by_file.get(str(Path(f['path']).resolve()))
        rec['files'].append(dict(path=f['path'], term_folder=entry['folder'] if entry else None,
                                 file_sha_now=f['sha256'], file_sha_at_audit=entry['file_sha_at_audit'] if entry else None))
        if not entry:
            continue
        for n, e in sorted(entry['events'].items()):
            props = e.get('proposal') or []
            if not props or n not in texts or layer['origin'].get(n) != f['path']:
                continue
            use = [p for p in props if CONF_RANK.get(p.get('confidence'), -1) >= CONF_RANK[threshold]]
            rec['below_threshold'] += len(props) - len(use)
            if not use:
                continue
            before_text = texts[n]
            row = dict(no=n, folder=entry['folder'], proposals=len(props), eligible=len(use), applied=[], skipped=[])
            if hashlib.sha256(before_text.encode()).hexdigest() != e.get('summary_sha256'):
                row['skipped_summary'] = 'summary changed since the audit (sha256 differs): all proposals of this summary skipped'
                rec['skipped_summaries'] += 1
                rec['events'].append(row)
                continue
            t = before_text
            for p in use:
                c = t.count(p['before'])
                if c != 1:
                    row['skipped'].append(dict(before=p['before'], after=p['after'], confidence=p['confidence'], reason=f'before occurs {c} times'))
                    rec['skipped_proposals'] += 1
                    continue
                t = t.replace(p['before'], p['after'])
                row['applied'].append(dict(before=p['before'], after=p['after'], type=p.get('type'), confidence=p['confidence']))
                rec['applied'] += 1
            if t != before_text:
                bad = text_problems(t)
                last_words = [re.findall(r'[가-힣]+', p['after'])[-1] for p in row['applied'] if re.findall(r'[가-힣]+', p['after'])]
                bad += ['particle ' + x for x in josa_problems(t, words + last_words)]
                row.update(sha256_before=hashlib.sha256(before_text.encode()).hexdigest(), sha256_after=hashlib.sha256(t.encode()).hexdigest(),
                           summary_after=t, gate_problems=bad)
                if bad:
                    # the patched text fails the gate: the summary keeps its approved text (strict: stop the build)
                    failures.append((n, bad))
                    row['skipped_summary'] = 'patched text fails the gate (' + '; '.join(bad) + '): the approved text is baked unchanged'
                    rec['gate_skipped'].append(dict(no=n, problems=bad, proposals=len(row['applied'])))
                    rec['applied'] -= len(row['applied'])
                    rec['skipped_proposals'] += len(row['applied'])
                    row['applied_then_reverted'] = row.pop('applied')
                    row['applied'] = []
                else:
                    texts[n] = t
                    rec['changed_ids'].append(n)
            rec['events'].append(row)
    assert not (strict and failures), ('term patch breaks the text gate', failures)
    return texts, rec


def month_summary_files():
    """Every monthly summaries.json of the WI-010 batches (read only) + the approved April file."""
    out = [APRIL_SUMMARIES]
    for p in sorted(STAGING.glob('calendar_*_summaries_20260929/**/design/summaries.json')):
        out.append(p)
    return out


def copy_resolution(copies, texts):
    """Where the text of every copy_of target lives: this layer, April (KR_AS29Story), E00011 (KR_P29Story) or another month's
    summaries.json (that layer must be stacked below this one), else missing."""
    index = {}
    for p in month_summary_files():
        for e in readj(p).get('events', []):
            if e.get('status') in BAKE_STATUS and (e.get('summary') or '').strip():
                index.setdefault(int(e['no']), []).append(str(p.parent.parent.relative_to(STAGING)))
    april = set(april_texts())
    out = {}
    for n, o in sorted(copies.items()):
        if o in texts:
            where = 'this layer'
        elif o in april:
            where = 'April KR_AS29Story (or the April term-patch layer)'
        elif o == 11:
            where = 'E00011 KR_P29Story'
        elif o in index:
            where = 'layer of ' + ', '.join(index[o]) + ' (must be stacked below)'
        else:
            where = 'missing'
        out[str(n)] = dict(copy_of=o, text_in=where, tab=tab_of().get(o))
    return out


def prepare_layer(summary_paths, scenario_paths=None, allow_draft=False, term_path=None, threshold='high', only_patched=False,
                  strict=False):
    """The base-independent part of a layer: merge + gates (load_layer), term patch (apply_terms), --only-patched selection,
    copy_of resolution. Returns dict(layer, texts, copies, term_record, copy_resolution)."""
    layer = load_layer(summary_paths, scenario_paths, allow_draft=allow_draft)
    texts = dict(layer['texts'])
    term = None
    if term_path:
        texts, term = apply_terms(layer, term_path, threshold, strict)
    copies = dict(layer['copies'])
    if only_patched:
        assert term, '--only-patched needs --term-patch'
        texts = {n: t for n, t in texts.items() if n in set(term['changed_ids'])}
        copies = {}
    return dict(layer=layer, texts=dict(sorted(texts.items())), copies=copies, term_record=term,
                copy_resolution=copy_resolution(copies, texts))


# ---------------------------------------------------------------- JAF generation
def tree(items, story, base, indent='    '):
    """Sorted binary if-tree (the April build's tree(), leaf = the Base call). items: [(no, ('text', s) | ('copy', o))]."""
    if not items:
        return indent + f'return {base}(no);\n'
    mid = len(items) // 2
    n, (kind, v) = items[mid]
    val = json.dumps(v, ensure_ascii=False) if kind == 'text' else f'{story}({int(v)})'
    out = indent + f'if(no=={n})return {val};\n'
    if items[:mid]:
        out += indent + f'if(no<{n}) {{\n' + tree(items[:mid], story, base, indent + '    ') + indent + '}\n'
    return out + tree(items[mid + 1:], story, base, indent)


def jaf_type(t):
    assert t[0] in JAF_TYPES and t[1] == -1 and t[2] == 0, ('unsupported type for a cloned local', t)
    return JAF_TYPES[t[0]]


def stub(name, f):
    """A JAF declaration with the same arguments, locals (in order) and return type as metadata entry f; the body is replaced by
    the clone later, the stub only has to compile to the same metadata."""
    args = ', '.join(f'{jaf_type(a["type"])} {a["name"]}' for a in f['arguments'])
    ret = jaf_type(f['return-type'])
    lines = [f'{ret} {name}({args}) {{']
    for v in f['variables']:
        t = jaf_type(v['type'])
        lines.append(f'    {t} {v["name"]}={JAF_DEFAULT[t]};')
    lines.append(f'    return {JAF_DEFAULT[ret]};')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def signature(f):
    return dict(arguments=f['arguments'], variables=f['variables'], ret=f['return-type'])


# ---------------------------------------------------------------- jam readers (static twins of the compiled layer)
def jam_ops(text):
    """Instruction lines of an `ain dump --function` file: (label or None, op, operand-text)."""
    out = []
    for line in text.splitlines():
        if not line or line.startswith(';') or line.startswith('FUNC ') or line.startswith('ENDFUNC ') or line.startswith('EOF'):
            continue
        z = re.match(r'^(0x[0-9A-Fa-f]+):$', line)
        if z:
            out.append((z[1].lower(), None, None))
            continue
        s = line.strip()
        op, _, rest = s.partition(' ')
        out.append((None, op, rest))
    return out


def normalized_body(text):
    """Op sequence with jump labels renamed by first appearance (so a clone at another address compares equal)."""
    labels = {}

    def lab(x):
        x = x.lower()
        if x not in labels:
            labels[x] = f'L{len(labels)}'
        return labels[x]
    out = []
    for label, op, rest in jam_ops(text):
        if label:
            out.append(lab(label) + ':')
        else:
            out.append(op + ' ' + re.sub(r'0x[0-9A-Fa-f]+', lambda z: lab(z[0]), rest))
    return out


def simulate(text, no, story, base, depth=0):
    """Evaluate the compiled KR_ST<tag>Story tree for one argument (ops the JAF compiler emits for it). Returns ('text', s) for a
    string literal, ('base', n) for the fall-through, following the layer's own self-calls (copy_of)."""
    assert depth < 8, 'copy_of recursion too deep'
    ops = jam_ops(text)
    at = {label: i for i, (label, op, _) in enumerate(ops) if label}
    stack = []
    i = 0
    steps = 0
    while True:
        steps += 1
        assert steps < 100000, 'no return'
        label, op, rest = ops[i]
        i += 1
        if label:
            continue
        if op == '.LOCALREF':
            assert rest == 'no', rest
            stack.append(no)
        elif op == 'PUSH':
            stack.append(int(rest))
        elif op in ('EQUALE', 'LT', 'GT', 'LTE', 'GTE', 'NOTE'):
            b, a = stack.pop(), stack.pop()
            stack.append(int({'EQUALE': a == b, 'LT': a < b, 'GT': a > b, 'LTE': a <= b, 'GTE': a >= b, 'NOTE': a != b}[op]))
        elif op == 'IFNZ':
            if stack.pop():
                i = at[rest.lower()]
        elif op == 'IFZ':
            if not stack.pop():
                i = at[rest.lower()]
        elif op == 'JUMP':
            i = at[rest.lower()]
        elif op == 'S_PUSH':
            lit = json.loads(rest)
            stack.append(('text', L.decode(lit.encode('cp932'))))
        elif op == 'CALLFUNC':
            arg = stack.pop()
            if rest == base:
                stack.append(('base', arg))
            elif rest == story:
                stack.append(simulate(text, arg, story, base, depth + 1))
            else:
                raise AssertionError(('unexpected call in the layer tree', rest))
        elif op == 'RETURN':
            v = stack.pop()
            assert isinstance(v, tuple), v
            return v
        else:
            raise AssertionError(('op outside the tree twin', op, rest))


# ---------------------------------------------------------------- path guards
OTHER_AGENT_FOLDERS = ['calendar_all_tabs_20260929', 'calendar_may_summaries_20260929', 'calendar_june_summaries_20260929',
                       'calendar_jul_aug_summaries_20260929', 'calendar_sep_other_summaries_20260929',
                       'calendar_october_summaries_20260929', 'calendar_november_a_summaries_20260929',
                       'calendar_november_b_summaries_20260929', 'calendar_memory_a_summaries_20260929',
                       'calendar_memory_b_summaries_20260929']


def assert_writable(out, extra_forbidden=()):
    """Outputs only under staging/, never inside the runtime, another agent's folder, the base or a summaries folder."""
    out = Path(out).resolve()
    assert out.is_relative_to(STAGING.resolve()), ('output must be under staging/', str(out))
    cur = readj(L.CURRENT)
    rt = Path(cur['runtime']).resolve()
    assert not out.is_relative_to(rt) and not out.is_relative_to(rt.parent), ('output inside the runtime', str(out))
    for name in OTHER_AGENT_FOLDERS:
        assert not out.is_relative_to((STAGING / name).resolve()), ('output inside another agent folder', str(out))
    for p in extra_forbidden:
        p = Path(p).resolve()
        assert not out.is_relative_to(p) and not p.is_relative_to(out), ('output overlaps a read-only input', str(out), str(p))
    return out


def chain(top):
    """The layers below (and including) `top`, top first: every folder whose candidate/manifest.json was written by this tool
    (summary / board / adopted external layers), following manifest['base'] down to the first foreign base (WI-009)."""
    out = []
    folder = Path(top).resolve()
    while True:
        mp = folder / 'candidate/manifest.json'
        man = readj(mp)
        if man.get('tool') != TOOL_NAME:
            out.append(dict(folder=str(folder), manifest=man, foreign=True))
            return out
        out.append(dict(folder=str(folder), manifest=man, foreign=False))
        folder = Path(man['base']).resolve()
