"""WI-009 shared helpers (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): paths, the frozen baseline, and Python twins of the
KR_W29 display rules (the build uses them for static gates, the probe for its expected values)."""
from pathlib import Path
import json, re, sys
sys.dont_write_bytecode = True
F = Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
if str(F) not in sys.path:
    sys.path.insert(0, str(F))
import r24lib as L

R = L.CODEX
O = R / 'staging' / 'calendar_all_tabs_20260929'
PRE = R / 'staging' / 'calendar_label_particles_20260929_r2'          # the installed build; its candidate = the live AIN
KEY = 'calendar_all_tabs_20260929'
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
DESIGNER = 'Claude Fable 5.1 (claude-fable-5-1)'
BASE_AIN = 'b74ebc26c77656bd927b9540769fa0b70bff1210b052167cdf22856781c256b8'
BASE_DLL = '0df1aa37edae29a9eb878e8043779b620ba0a3de5ee450cd872a5eac9c1e495e'
BASE_MANIFEST = '54fd6042482905d777efa8ec1a9f7ead4714ee7ab5f52b6ab5d986477f7ca61f'
ROUTES = {'KR_CDraw': ('KR_AM29Draw', 'KR_W29Minis'),
          'KR_P29Board': ('KR_AS29Router', 'KR_W29Board'),
          'KR_T9StagePage': ('KR_U29Stages', 'KR_W29Stages')}
ADDED = {'KR_W29Plain', 'KR_W29Trim', 'KR_W29Story', 'KR_W29Date', 'KR_W29Clean', 'KR_W29Join', 'KR_W29GroupOf', 'KR_W29Title', 'KR_W29Info', 'KR_W29HeadWrap', 'KR_W29Board',
         'KR_W29Cond', 'KR_W29StateCG', 'KR_W29Cell', 'KR_W29Draw', 'KR_W29Minis', 'KR_W29StageItem', 'KR_W29Stages'}
TITLE_LIMIT = 38          # one select-dialog title line, colour mark included (r19 LIMIT)
ITEM_CAP = 38             # one-column item width in full-width units (r17: 「1열 한도 38칸」)
DIALOG_MAX = 704          # 64 + 34 x title lines + 48 x items


def readj(p):
    return json.loads(Path(p).read_text('utf-8-sig'))


def tables():
    """Design tables copied next to the build (cells = the KR_P29Cell* tables, r15 / r19 = the base label tables)."""
    D = O / 'design'
    return dict(cells=readj(D / 'cells.json'), t15=readj(D / 'r15_tables.json'), t19=readj(D / 'r19_tables.json'),
                choices=readj(D / 'choices_label_patch.json'), context=readj(D / 'choice_context_label_patch.json'),
                particles=readj(D / 'label_particles_patch.json'))


def effective(T, key, n, read):
    """The runtime value of an r19 label getter for id n: r19 table -> KR_R29 (choices) -> KR_S29 (choice context) -> KR_N29."""
    v = T['t19'][key].get(str(n), '')
    for layer in (T['choices'], T['context']):
        src = layer['patch'] if read else layer['unread']
        if key in src and str(n) in src[key]:
            v = src[key][str(n)]
    patch = T['particles']['patch']
    if key in patch and str(n) in patch[key] and v == patch[key][str(n)]['before']:
        v = patch[key][str(n)]['after']
    return v


def when(T, n, read):
    w = effective(T, 'when_fix', n, read)
    return w if w else T['t19']['whens'].get(str(n), '')


DG = '0123456789'


def plain(s, group):
    """KR_W29Plain: 「N단계」 -> 「장면 N」 (group: 「장면 N개」)."""
    out, digits, i, n = '', '', 0, len(s)
    while i < n:
        c = s[i]
        if c in DG:
            digits += c
            i += 1
            continue
        if c == '단' and digits and i + 1 < n and s[i + 1] == '계':
            out += '장면 ' + digits + ('개' if group else '')
            digits = ''
            i += 2
            continue
        out += digits + c
        digits = ''
        i += 1
    return out + digits


def clean(s):
    """KR_W29Clean: the r19 title continuation 「\n† + full-width indent」 -> 「 · 」."""
    return re.sub('\n[†‡¶〓]\u3000*', ' · ', s)


def trim(name):
    """KR_W29Trim: the stage-count tail of a group name."""
    n = len(name)
    if n < 4 or name[n - 2:] != '단계':
        return name
    i = n - 3
    while i >= 0 and name[i] in DG:
        i -= 1
    if i == n - 3 or i < 0:
        return name
    if name[i] == '\n':
        return name[:i]
    if i >= 2 and name[i - 2:i + 1] == ' · ':
        return name[:i - 2]
    if name[i] == ' ':
        return name[:i]
    return name


def title_fit(head):
    """KR_W29Title (r2): the trailing 「 · 장면 N개」 always goes, then a line over 37 characters breaks at " · "."""
    n = len(head)
    cut = -1
    for i in range(n - 3, 0, -1):
        if head[i:i + 3] == ' · ':
            cut = i
            break
    if cut > 0:
        last = head[cut + 3:]
        if len(last) >= 4 and last[:3] == '장면 ' and last[-1] == '개':
            head = head[:cut]
            n = len(head)
    if n <= 37:
        return head
    out = ''
    while n > 37:
        at = -1
        for j in range(37, 0, -1):
            if j + 3 <= n and head[j:j + 3] == ' · ':
                at = j
                break
        if at <= 0:
            break
        out += head[:at] + '\n〓'
        head = head[at + 3:]
        n = len(head)
    return out + head


def head_wrap(title):
    """KR_W29HeadWrap (None where the JAF would fall back to KR_B29Wrap: <= 34 characters, or no " · " break that fits)."""
    n = len(title)
    if n <= 34:
        return None
    out, rest = '', title
    while n > 34:
        at = -1
        for j in range(33, 0, -1):
            if j + 3 <= n and rest[j:j + 3] == ' · ':
                at = j
                break
        if at <= 0:
            return None
        out += rest[:at] + '\n'
        rest = rest[at + 3:]
        n = len(rest)
    return out + rest


def units(t):
    """Glyph width in full-width units (ASCII draws half width) - r19 build_calendar_r19.units."""
    return sum(0.5 if ord(c) < 0x80 else 1.0 for c in t)


def page_tag(page, pages):
    return '' if pages <= 1 else f'　〓{page + 1}/{pages}쪽'


def picker_layout(n):
    per = 10 if n <= 10 else 8
    pages = max(1, (n + per - 1) // per)
    return per, pages


def norm(s):
    """Review gate: both spellings of a stage number reduced to the bare number (「N단계」, 「장면 N」, 「장면 N개」 -> 「N」). Two strings
    with the same norm differ only by the stage wording rule."""
    return re.sub(r'장면 (\d+)개?', lambda z: z[1], re.sub(r'(\d+)단계', lambda z: z[1], s))


def wording_map(T):
    """Every on-screen string this batch changes, before -> after (read state; the unread masks of KR_R29 / KR_S29 are
    untouched and never contain 단계). Used as the batch's display 'translation map' and for the wording review."""
    cells, t15 = T['cells'], T['t15']
    cards = {c['k']: c for c in t15['cards']}
    out = dict(list_names={}, list_conditions={}, card_heads={}, scene_heads={}, when={}, card_conditions={}, picker_titles={})
    for c in cells:
        a = plain(trim(c['name']), False)
        if a != c['name']:
            out['list_names'][str(c['no'])] = dict(before=c['name'], after=a, cell_tab=c['tab'])
        b = plain(c['cond'], False)
        if b != c['cond']:
            out['list_conditions'][str(c['no'])] = dict(before=c['cond'], after=b, cell_tab=c['tab'])
    for k, c in sorted(cards.items()):
        h = effective(T, 'heads', k, True)
        if plain(h, c['size'] > 1) != h:
            out['card_heads'][str(k)] = dict(before=h, after=plain(h, c['size'] > 1), size=c['size'])
        if c['size'] > 1 and k != 6:
            t = title_fit(plain(h, True))
            if t != plain(h, True):
                out['picker_titles'][str(k)] = dict(before=plain(h, True), after=t, rule='r2 (review F-04): the trailing 「 · 장면 N개」 '
                                                    'goes on every generic picker (the count stands on the second title line)')
        v = effective(T, 'conds', k, True)
        if plain(v, False) != v:
            out['card_conditions'][str(k)] = dict(before=v, after=plain(v, False))
    for n in sorted(int(x) for x in t15['events']):
        h = effective(T, 'ev_head', n, True)
        if plain(h, False) != h:
            out['scene_heads'][str(n)] = dict(before=h, after=plain(h, False))
        for read in (True, False):
            w = when(T, n, read)
            if plain(clean(w), False) != w:
                out['when'][str(n) + ('' if read else ' unread')] = dict(before=w, after=plain(clean(w), False))
    out['counts'] = {k: len(v) for k, v in out.items() if isinstance(v, dict)}
    return out
