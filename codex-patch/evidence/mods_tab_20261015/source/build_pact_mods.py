"""Mods page redesign (PACT 185, Asra/Mods.pactex). Stage only.

Claude Opus 5.5, 2026-10-15, user request: 「모드 옵션을 좀 보기좋게 다시 만들 수 있을까? 지금은 다소 번잡하군」.
Reads the installed runtime NightRemasterPact.afa (read-only) and writes, in this folder only:
  original_pact_185.pactex      entry 185 exactly as installed (auto-nav build)
  pact_185_mods.pactex          the redesigned page
  NightRemasterPact.afa         candidate archive (only entry 185 differs)
  build_evidence.json           hashes, coordinates and every check below

What changes (no part that code or the EX page table looks up is renamed or removed):
  - the page follows the native config pages: section headings 24px white with the cyan edge and the heading sparkle
    (背景_星 construction steps, as on the sound / message pages); labels and checkbox texts 20px; notes 14-15px in
    a quiet colour instead of the cyan-edged hint style
  - sections: 보상 배율 (2x2 sliders) / 오토 내비게이션 / 전투 (left) / 던전 + 편의 (right); the four dialog buttons in
    one toolbar row at the top
  - every slider gets the native track: a dimmed 'シス／コンフィグ／バー' gauge under a bright one (横ゲージ parts copied from
    the message-speed page); the bright one is filled to the slider by the AIN layer (KR_MDGauges), like the native
    pages' UpdateEventForConnectStatus does
  - battle speed gets five tick labels under its stops instead of the 「기본 / 2배 / ...」 line
  - KR_ModTitle (「모드 설정」) is hidden (native pages have no page title; the tab shows the page); the other old hint
    parts are reused as tags and notes
Checks (asserted): runtime archive hash; decode->encode->decode round trip; only entry 185 differs; every part name
code or EX uses still exists with the same type; every Korean character is an FNL proxy and has a glyph; alice-tools
parses the entry; no clickable box overlaps another; everything stays inside the panel (x 330-1105, y 18-650).
"""
from pathlib import Path
import copy, hashlib, json, os, struct, subprocess, sys

HERE = Path(__file__).resolve().parent
AN = HERE.parent / 'autonav_20261015'
sys.path.insert(0, str(AN / 'pact' / 'lib')); sys.path.insert(0, str(AN / 'pact'))
from codex_pact_helpers import (ex, ENC, encode, decode, read_afa3, rebuild, child, maybe, val, allparts,  # noqa: E402
                                setlist, ss, si, rename, txt_info, name, coords, scalar, add, cp)
import render_layout_proof as proof  # noqa: E402
import build_pact_autonav as anb  # noqa: E402  (char_report, glyph_check, alice)

POINTER = Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/current.json')
EXPECTED_PACT_SHA = '9f8c63b9276b00b71904ecd34b7062a9f1fec091ebe5cfaa0bc7ada1c16072ce'   # auto-nav install (10-15 22:31)
ENTRY = 185
GAUGE_PAGE = 'Asra/コンフィグ／０１／メッセージ速度ページ.pactex'
GAUGE_TEMPLATE = '横ゲージ_メッセージ速度スライダ'
TMP = HERE / 'tmp'

# names code (C_ConfigView events, ClickEvent, KR_AN*) or the EX table Ｅ＿コンフィグファイル名 looks up: never renamed/removed
USED_BY_CODE = ['KR_HomeRateToggle', 'KR_SmartAutoToggle', 'KR_AutoEquipToggle', 'KR_CheatSweep', 'KR_CheatLoot', 'KR_CheatQuick',
                'KR_CheatTrap', 'KR_CheatRoute', 'KR_CheatSpeed', 'KR_CheatSpeedValue', 'KR_Multiplier_EX', 'KR_Multiplier_Training',
                'KR_Multiplier_Money', 'KR_Multiplier_PairTraining', 'KR_Multiplier_Value_EX', 'KR_Multiplier_Value_Training',
                'KR_Multiplier_Value_Money', 'KR_Multiplier_Value_PairTraining', 'KR_SaveStyleButton', 'KR_PlayerInfoButton',
                'KR_TermConfigButton', 'KR_ItemConfigButton', 'KR_ModTab', 'KR_NavOff', 'KR_NavIzumi', 'KR_NavKyouka',
                'KR_NavManami', 'KR_NavMakoto', 'SYS_ゲームを終了する', 'SYS_タイトル画面に戻る', 'SYS_ゲームに戻る']

# ---------------------------------------------------------------------------------------------------------------------
# Layout (absolute screen coordinates; panel body x 160-1119, tab column to x 302, footer buttons from y 656)
HX, RX = 377, 745                   # left / right column (377 = the native pages' heading x)
ICON_DX, ICON_DY = -44, -7          # heading sparkle relative to its heading text (native: icon 333/38, text 377/45)
HEAD = dict(size=24, color=(255, 255, 255), edge=1.0, edge_color=(0, 198, 255), spacing=-2)   # native heading style
LABEL = dict(size=20, color=(255, 255, 255), edge=1.0, edge_color=(0, 0, 0), spacing=-2)
NOTE = dict(size=15, color=(214, 224, 246), edge=1.0, edge_color=(6, 12, 44), spacing=-3)   # native capture: -1 read wide
TAG = dict(size=15, color=(196, 214, 248), edge=1.0, edge_color=(6, 12, 44), spacing=-3)
TICK = dict(size=14, color=(196, 214, 248), edge=1.0, edge_color=(6, 12, 44), spacing=-2)
CHECK_SIZE, CHECK_PAD = 20, '  '
ROW = 36                            # checkbox pitch
SLIDER_L, LABEL_W, VALUE_GAP = 196, 104, 8
GAUGE_W = 300                       # 'シス／コンフィグ／バー' is 300x12
TRACK_MUL = (70, 82, 120)           # dim copy under the fill

TOOLBAR_Y, BTN_W, BTN_H, BTN_STEP = 24, 150, 30, 180
BUTTONS = [('KR_SaveStyleButton', 'KR_SaveStyleLabel'), ('KR_ItemConfigButton', 'KR_ItemConfigLabel'),
           ('KR_TermConfigButton', 'KR_TermConfigLabel'), ('KR_PlayerInfoButton', 'KR_PlayerInfoLabel')]

A_Y = 72                            # 보상 배율
A_ROWS = (108, 152)
CELLS = [('EX', HX, A_ROWS[0]), ('Training', RX, A_ROWS[0]), ('Money', HX, A_ROWS[1]), ('PairTraining', RX, A_ROWS[1])]
B_Y = 212                           # 오토 내비게이션
B_RADIO_Y, B_NOTE_Y = 246, 286
NAV = [('KR_NavOff', '쓰지 않음'), ('KR_NavIzumi', '이즈미'), ('KR_NavKyouka', '쿄카'), ('KR_NavManami', '마나미'), ('KR_NavMakoto', '마코토')]
NAV_GAP = 26
C_Y = 336                           # 전투 (left) / 던전 (right)
SPEED_Y = 372
LEFT_CHECKS_Y = 460
LEFT_CHECKS = [('KR_CheatQuick', '전투 이펙트 보지 않기'), ('KR_CheatLoot', '일반 적 즉시 처치'), ('KR_SmartAutoToggle', '강화 자동 전투')]
RIGHT_CHECKS_Y = 370
RIGHT_CHECKS = [('KR_CheatTrap', '함정 즉시 해체'), ('KR_CheatRoute', '다음 층 경로 표시'), ('KR_CheatSweep', '소탕 버튼 표시')]
E_Y = 528                           # 편의 (right column)
E_CHECKS = [('KR_AutoEquipToggle', '자동 장착·요소석 추천'), ('KR_HomeRateToggle', '달성률 항상 표시')]

TEXTS = {   # existing text parts reused: name -> (text, style)
    'KR_ModRewardsTitle': ('보상 배율', HEAD),
    'KR_ModScope': ('세이브마다 · 리마스터 탭의 2배 체크를 바꾸면 1배나 2배로 바뀝니다', TAG),
    'KR_NavTitle': ('오토 내비게이션', HEAD),
    'KR_NavNote': ('고른 인물 쪽 답이 반짝이고 20초 뒤 자동으로 골라집니다. 이야기가 있는 토요일엔 특훈 상대도 안내합니다.\n'
                   '모자란 친밀도는 채워 줍니다(원래 규칙 밖 보정).', NOTE),
    'KR_ModSpeedTitle': ('전투 속도', LABEL),
    'KR_ModSpeedDefaultHint': ('기본: 게임 설정의 전투 가속을 따릅니다.', NOTE),
    'KR_ModQuickHint': ('일반 던전에 소탕 버튼을 띄웁니다.', NOTE),
    'KR_ModQuickCancel': ('소탕하면 남은 시간을 정산하고 다음 날로', NOTE),
}
HIDE = ['KR_ModTitle', 'KR_ModRewardHint', 'KR_ModSpeedHint']
NEW_TEXTS = {   # new text parts: name -> (text, style)
    'KR_MD_TagNav': ('세이브마다 · 게임 중에만 바꿀 수 있음', TAG),
    'KR_MD_HeadBattle': ('전투', HEAD), 'KR_MD_TagBattle': ('모든 세이브 공통', TAG),
    'KR_MD_HeadDungeon': ('던전', HEAD), 'KR_MD_TagDungeon': ('모든 세이브 공통', TAG),
    'KR_MD_HeadEtc': ('편의', HEAD), 'KR_MD_TagEtc': ('모든 세이브 공통', TAG),
}
TICKS = ['기본', '2배', '3배', '4배', '5배']
SLIDERS = {'EX': 'KR_Multiplier_EX', 'Training': 'KR_Multiplier_Training', 'Money': 'KR_Multiplier_Money',
           'PairTraining': 'KR_Multiplier_PairTraining', 'Speed': 'KR_CheatSpeed'}
PANEL = (330, 18, 1105, 650)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p, d): Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def index(root):
    out = {}

    def walk(t, ox, oy, parent):
        c = coords(t) if maybe(t, '座標') is not None else [0.0, 0.0, 0]
        ax, ay = ox + c[0], oy + c[1]
        out[name(t)] = dict(node=t, parent=parent, pabs=(ox, oy), abs=(ax, ay))
        kids = maybe(t, '子パーツ')
        if kids:
            for k in kids.children:
                walk(k, ax, ay, t)
    walk(root, 0.0, 0.0, None)
    return out


class Page:
    def __init__(self, doc):
        self.doc = doc
        self.root = doc.blocks[2].payload.children[0]
        self.refresh()

    def refresh(self):
        self.idx = index(self.root)

    def node(self, n): return self.idx[n]['node']

    def place(self, n, x, y, z=None):
        e = self.idx[n]; c = coords(e['node'])
        setlist(e['node'], '座標', [float(x - e['pabs'][0]), float(y - e['pabs'][1]), int(c[2] if z is None else z)])
        self.refresh()

    def scalar_set(self, node, key, v):
        si(node, key, v)


def style_text(t, text=None, size=None, color=None, edge=None, edge_color=None, spacing=None, line_gap=None, **_):
    ti = txt_info(t); dec = child(ti, 'テキスト装飾')
    if text is not None: ss(ti, 'テキスト', text, True)
    if size is not None: si(dec, 'フォントサイズ', size)
    if color is not None: setlist(dec, 'フォント色', list(color))
    if edge is not None: si(dec, 'フォント縁取り', edge)
    if edge_color is not None: setlist(dec, 'フォント縁取り色', list(edge_color))
    if spacing is not None: si(dec, '字間隔', spacing)
    if line_gap is not None: si(dec, '行間隔', line_gap)


def style_check(t, label):
    info = child(t, '種類別情報')
    ss(info, 'テキスト', CHECK_PAD + label, True); si(info, 'フォントサイズ', CHECK_SIZE)


class Measure:
    def __init__(self, runtime):
        self.fnl = proof.Fnl(Path(runtime) / 'NightRemasterFont.fnl')

    def w(self, text, st):
        return max(self.fnl.width(s, st['size'], st.get('spacing', 0), st.get('edge', 0.0), 0.0) for s in text.split('\n'))

    def h(self, text, st):
        return (len(text.split('\n')) - 1) * (st['size'] + st.get('line_gap', 0)) + self.fnl.line_height(st['size'])


def gauge_template(runtime):
    arc = read_afa3(runtime / 'NightRemasterPact.afa')
    e = next(x for x in arc.entries if x.name == GAUGE_PAGE)
    with (runtime / 'NightRemasterPact.afa').open('rb') as f:
        f.seek(e.absolute_offset); raw = f.read(e.size)
    TMP.mkdir(exist_ok=True)
    p = TMP / 'gauge_page.pactex'; p.write_bytes(raw)
    d = ex.decode_ex(p)
    t = next(x for x in allparts(d.blocks[2].payload.children[0]) if name(x) == GAUGE_TEMPLATE)
    st = child(child(t, '種類別情報'), '通常状態')
    assert val(st, 'パーツタイプ').value.decode('cp932') == '横ゲージパーツ'
    assert val(st, 'ＣＧ名').value.decode('cp932') == 'シス／コンフィグ／バー'
    return t


def make_layout(page, m, runtime):
    root = page.root
    made, notes = [], {}
    # groups to the origin so every child is placed absolutely
    for g in ('KR_ModHeader', 'KR_ModRewards', 'KR_ModBattle', 'KR_ModDungeon'):
        page.place(g, 0, 0)
    for n in HIDE:
        si(page.node(n), '表示', 0)

    # toolbar: four dialog buttons, 150x30 (tab plate 192x42 scaled), labels centred
    for i, (b, lab) in enumerate(BUTTONS):
        x = HX + i * BTN_STEP
        page.place(b, x, TOOLBAR_Y)
        setlist(page.node(b), '拡大縮小', [BTN_W / 192.0, BTN_H / 42.0])
        lt = page.node(lab); ti = txt_info(lt); dec = child(ti, 'テキスト装飾')
        st = dict(size=scalar(val(dec, 'フォントサイズ')), spacing=scalar(val(dec, '字間隔')), edge=float(scalar(val(dec, 'フォント縁取り'))))
        txt = decode(val(ti, 'テキスト').value)
        if m.w(txt, st) > BTN_W - 12:
            st['size'] = 18; si(dec, 'フォントサイズ', 18)
        tw = m.w(txt, st)
        page.place(lab, x + (BTN_W - tw) / 2.0, TOOLBAR_Y + (BTN_H - m.fnl.line_height(st['size'])) / 2.0)

    # existing texts restyled / reused
    for n, (text, st) in TEXTS.items():
        style_text(page.node(n), text=text, **st)
        if n == 'KR_NavNote':
            si(child(txt_info(page.node(n)), 'テキスト装飾'), '行間隔', 4)

    def new_text(n, text, st, x, y, z):
        t = copy.deepcopy(page.node('KR_ModQuickHint')); rename(t, n)
        style_text(t, text=text, **st); setlist(t, '座標', [float(x), float(y), int(z)])
        add(root, t); made.append(n); page.refresh()
        return t

    heads = []

    def heading(n, x, y, tag=None, tag_text=None):
        page.place(n, x, y) if n in page.idx else None
        heads.append((x, y))
        if tag:
            tw = m.w(TEXTS[n][0] if n in TEXTS else NEW_TEXTS[n][0], HEAD)
            ty = y + (HEAD['size'] - TAG['size']) / 2.0 + 1
            if tag in page.idx:
                page.place(tag, x + tw + 16, ty)
            else:
                new_text(tag, NEW_TEXTS[tag][0], TAG, x + tw + 16, ty, 61)

    # 보상 배율
    heading('KR_ModRewardsTitle', HX, A_Y, 'KR_ModScope')
    gauges = []
    for key, x, y in CELLS:
        lab, sl, vt = f'KR_Multiplier_Label_{key}', f'KR_Multiplier_{key}', f'KR_Multiplier_Value_{key}'
        style_text(page.node(lab), **LABEL); style_text(page.node(vt), **LABEL)
        page.place(lab, x, y - 1)
        page.place(sl, x + LABEL_W, y)
        si(child(page.node(sl), '種類別情報'), '長さ', SLIDER_L)
        page.place(vt, x + LABEL_W + SLIDER_L + VALUE_GAP, y - 1)
        gauges.append((key, x + LABEL_W, y))

    # 오토 내비게이션
    heading('KR_NavTitle', HX, B_Y, 'KR_MD_TagNav')
    x = HX
    for k, (n, label) in enumerate(NAV):
        style_check(page.node(n), label); page.place(n, x, B_RADIO_Y)
        x += 32 + m.w(CHECK_PAD + label, dict(size=CHECK_SIZE, spacing=-2, edge=1.0)) + NAV_GAP
    page.place('KR_NavNote', HX, B_NOTE_Y)

    # 전투 (left)
    new_text('KR_MD_HeadBattle', '전투', HEAD, HX, C_Y, 60)
    heading('KR_MD_HeadBattle', HX, C_Y, 'KR_MD_TagBattle')
    page.place('KR_ModSpeedTitle', HX, SPEED_Y - 1)
    page.place('KR_CheatSpeed', HX + LABEL_W, SPEED_Y)
    si(child(page.node('KR_CheatSpeed'), '種類別情報'), '長さ', SLIDER_L)
    style_text(page.node('KR_CheatSpeedValue'), **LABEL)
    page.place('KR_CheatSpeedValue', HX + LABEL_W + SLIDER_L + VALUE_GAP, SPEED_Y - 1)
    gauges.append(('Speed', HX + LABEL_W, SPEED_Y))
    total = scalar(val(child(page.node('KR_CheatSpeed'), '種類別情報'), '全体スクロール量'))
    shown = scalar(val(child(page.node('KR_CheatSpeed'), '種類別情報'), '表示量'))
    steps = total - shown
    assert steps == len(TICKS) - 1, ('battle speed stops', total, shown)
    tick_y = SPEED_Y + 42 + 2
    for i, label in enumerate(TICKS):
        cx = HX + LABEL_W + 12.5 + i * (SLIDER_L - 25) / steps
        new_text(f'KR_MD_Tick{i + 1}', label, TICK, cx - m.w(label, TICK) / 2.0, tick_y, 62 + i)
    page.place('KR_ModSpeedDefaultHint', HX, tick_y + 20)
    y = LEFT_CHECKS_Y
    for n, label in LEFT_CHECKS:
        style_check(page.node(n), label); page.place(n, HX, y); y += ROW

    # 던전 + 편의 (right)
    new_text('KR_MD_HeadDungeon', '던전', HEAD, RX, C_Y, 60)
    heading('KR_MD_HeadDungeon', RX, C_Y, 'KR_MD_TagDungeon')
    y = RIGHT_CHECKS_Y
    for n, label in RIGHT_CHECKS:
        style_check(page.node(n), label); page.place(n, RX, y); y += ROW
    page.place('KR_ModQuickHint', RX + 38, y + 2)
    page.place('KR_ModQuickCancel', RX + 38, y + 20)
    new_text('KR_MD_HeadEtc', '편의', HEAD, RX, E_Y, 60)
    heading('KR_MD_HeadEtc', RX, E_Y, 'KR_MD_TagEtc')
    y = E_Y + 36
    for n, label in E_CHECKS:
        style_check(page.node(n), label); page.place(n, RX, y); y += ROW

    # slider tracks: dim full gauge + bright gauge (filled by KR_MDGauges), both under the slider group (root z 30-39)
    tpl = GAUGE_TPL
    for k, (key, sx, sy) in enumerate(gauges):
        for j, kind in enumerate(('Track', 'Fill')):
            g = copy.deepcopy(tpl); rename(g, f'KR_MD_{kind}{key}')
            setlist(g, '座標', [float(sx + 12), float(sy + 3), int(30 + 2 * k + j)])
            setlist(g, '拡大縮小', [(SLIDER_L - 24) / float(GAUGE_W), 1.0])
            if kind == 'Track':
                setlist(g, '乗算色', list(TRACK_MUL))
            add(root, g); made.append(f'KR_MD_{kind}{key}')
    page.refresh()

    # heading sparkles: 背景_星 (root z 2) draws one 'シス／コンフィグ／見出しアイコン' per heading
    star = page.node('背景_星'); sx0 = page.idx['背景_星']['abs'][0]
    lst = child(child(child(star, '種類別情報'), '通常状態'), '手順リスト')
    steps_ = lst.children
    assert len(steps_) == 4 and scalar(val(steps_[0], 'コマンド')) == 0 and scalar(val(steps_[2], 'コマンド')) == 19
    setlist(steps_[0], '先矩形', [0, 0, 0, 0, 800, 720])
    icon_tpl = copy.deepcopy(steps_[2])
    del steps_[2:]
    for i, (hx, hy) in enumerate(heads):
        s = copy.deepcopy(icon_tpl); s.name.replacement = cp(f'手順{3 + i}')
        setlist(s, '先矩形', [int(hx + ICON_DX - sx0), int(hy + ICON_DY), 0, 0, 58, 53])
        steps_.append(s)
    notes['sparkles'] = [(hx + ICON_DX, hy + ICON_DY) for hx, hy in heads]
    notes['gauges'] = [dict(slider=SLIDERS[k], track=f'KR_MD_Track{k}', fill=f'KR_MD_Fill{k}', x=sx + 12, y=sy + 3,
                            width=SLIDER_L - 24) for k, sx, sy in gauges]
    return made, notes


GAUGE_TPL = None

# ---------------------------------------------------------------------------------------------------------------------
# PACT 187 Asra/AutoItems.pactex (자동 회복 설정, opened by KR_ItemConfigButton through the EX page table): the same treatment
ITEMS_ENTRY = 187
ITEMS_USED = (['KR_ItemsEnabled', 'KR_ItemsThreshold', 'KR_ItemsThresholdValue', 'KR_ModTab', 'SYS_ゲームを終了する', 'SYS_タイトル画面に戻る',
               'SYS_ゲームに戻る'] + ['KR_ItemsAllow%d' % i for i in range(1, 6)] + ['KR_ItemsReserve%d' % i for i in range(1, 6)]
              + ['KR_ItemsReserveValue%d' % i for i in range(1, 6)])
SUB = dict(size=16, color=(196, 214, 248), edge=1.0, edge_color=(6, 12, 44), spacing=-2)
I_TITLE_Y, I_ENABLED_Y, I_THRESH_Y, I_HEAD_Y, I_ROW0, I_ROW_STEP, I_HINT_Y = 40, 84, 134, 186, 222, 64, 560
I_SLIDER_X, I_SLIDER_L = 700, 300
I_TEXTS = {
    'KR_ItemsTitle': ('자동 회복 설정', HEAD),
    'KR_ItemsScope': ('자동 전투 중에만 사용 · 모든 세이브 공통', TAG),
    'KR_ItemsThresholdLabel': ('영력 회복 기준', LABEL),
    'KR_ItemsAllowHeader': ('사용 허용 / 아이템 효과', SUB),
    'KR_ItemsReserveHeader': ('최소 보유 개수 (0~99개)', SUB),
    'KR_ItemsHint': ('보유량이 지정 개수보다 많을 때만 사용합니다. 모드 탭으로 돌아갈 수 있습니다.', NOTE),
}


def make_items_layout(page, m):
    root = page.root
    made, heads, gauges = [], [], []
    for n, (text, st) in I_TEXTS.items():
        style_text(page.node(n), text=text, **st)
    page.place('KR_ItemsTitle', HX, I_TITLE_Y); heads.append((HX, I_TITLE_Y))
    page.place('KR_ItemsScope', HX + m.w(I_TEXTS['KR_ItemsTitle'][0], HEAD) + 16, I_TITLE_Y + (HEAD['size'] - TAG['size']) / 2.0 + 1)
    info = child(page.node('KR_ItemsEnabled'), '種類別情報')
    label = decode(val(info, 'テキスト').value).strip('　 ')
    style_check(page.node('KR_ItemsEnabled'), label); page.place('KR_ItemsEnabled', HX, I_ENABLED_Y)
    page.place('KR_ItemsThresholdLabel', HX, I_THRESH_Y - 1)
    page.place('KR_ItemsThreshold', I_SLIDER_X, I_THRESH_Y)
    si(child(page.node('KR_ItemsThreshold'), '種類別情報'), '長さ', I_SLIDER_L)
    style_text(page.node('KR_ItemsThresholdValue'), **LABEL)
    page.place('KR_ItemsThresholdValue', I_SLIDER_X + I_SLIDER_L + VALUE_GAP, I_THRESH_Y - 1)
    gauges.append(('Threshold', 'KR_ItemsThreshold', I_SLIDER_X, I_THRESH_Y))
    page.place('KR_ItemsAllowHeader', HX, I_HEAD_Y)
    page.place('KR_ItemsReserveHeader', I_SLIDER_X, I_HEAD_Y)
    for i in range(1, 6):
        y = I_ROW0 + (i - 1) * I_ROW_STEP
        box = page.node('KR_ItemsAllow%d' % i); bi = child(box, '種類別情報')
        style_check(box, decode(val(bi, 'テキスト').value).strip('　 ')); page.place('KR_ItemsAllow%d' % i, HX, y)
        style_text(page.node('KR_ItemsEffect%d' % i), **NOTE)
        page.place('KR_ItemsEffect%d' % i, HX + 32 + m.w(CHECK_PAD, dict(size=CHECK_SIZE, spacing=-2, edge=1.0)), y + 34)
        page.place('KR_ItemsReserve%d' % i, I_SLIDER_X, y)
        si(child(page.node('KR_ItemsReserve%d' % i), '種類別情報'), '長さ', I_SLIDER_L)
        style_text(page.node('KR_ItemsReserveValue%d' % i), **LABEL)
        page.place('KR_ItemsReserveValue%d' % i, I_SLIDER_X + I_SLIDER_L + VALUE_GAP, y - 1)
        gauges.append(('Reserve%d' % i, 'KR_ItemsReserve%d' % i, I_SLIDER_X, y))
    page.place('KR_ItemsHint', HX, I_HINT_Y)
    for k, (key, sl, sx, sy) in enumerate(gauges):
        for j, kind in enumerate(('Track', 'Fill')):
            g = copy.deepcopy(GAUGE_TPL); rename(g, f'KR_MD_{kind}{key}')
            setlist(g, '座標', [float(sx + 12), float(sy + 3), int(30 + 2 * k + j)])
            setlist(g, '拡大縮小', [(I_SLIDER_L - 24) / float(GAUGE_W), 1.0])
            if kind == 'Track':
                setlist(g, '乗算色', list(TRACK_MUL))
            add(root, g); made.append(f'KR_MD_{kind}{key}')
    page.refresh()
    star = page.node('背景_星'); sx0 = page.idx['背景_星']['abs'][0]
    lst = child(child(child(star, '種類別情報'), '通常状態'), '手順リスト')
    steps_ = lst.children
    cmds = [scalar(val(s_, 'コマンド')) for s_ in steps_]
    assert cmds[:2] == [0, 5] and all(c == 19 for c in cmds[2:]), cmds
    icon_tpl = copy.deepcopy(steps_[2])
    del steps_[2:]
    for i, (hx, hy) in enumerate(heads):
        s_ = copy.deepcopy(icon_tpl); s_.name.replacement = cp(f'手順{3 + i}')
        setlist(s_, '先矩形', [int(hx + ICON_DX - sx0), int(hy + ICON_DY), 0, 0, 58, 53])
        steps_.append(s_)
    return made, dict(gauges=[dict(slider=sl, track=f'KR_MD_Track{k}', fill=f'KR_MD_Fill{k}', x=sx + 12, y=sy + 3, width=I_SLIDER_L - 24)
                              for k, sl, sx, sy in gauges], sparkles=[(hx + ICON_DX, hy + ICON_DY) for hx, hy in heads])


def page_checks(doc, m, label):
    parts = proof.collect(doc); bx = proof.boxes(parts, m.fnl)
    clickable = [b for b in bx if b['kind'] in ('checkbox', 'button', 'slider') and b['group'] != 'タブ／ボタン類']
    overlaps = []
    for i, a in enumerate(clickable):
        for b in clickable[i + 1:]:
            ax0, ay0, ax1, ay1 = a['rect']; bx0, by0, bx1, by1 = b['rect']
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                overlaps.append((a['name'], b['name']))
    assert not overlaps, (label, overlaps)
    outside = [b['name'] for b in bx if b['group'] not in ('タブ／ボタン類', 'レイアウト_タブテキスト') and b['name'] not in ('背景', '背景_星')
               and not (PANEL[0] <= b['rect'][0] and b['rect'][2] <= PANEL[2] and PANEL[1] <= b['rect'][1] and b['rect'][3] <= PANEL[3])]
    assert not outside, (label, outside)
    return [dict(name=b['name'], kind=b['kind'], rect=[round(v, 1) for v in b['rect']]) for b in bx]


def build_items(src, rt, m):
    arc = read_afa3(src); e = arc.entries[ITEMS_ENTRY]; assert e.name == 'Asra/AutoItems.pactex', e.name
    with src.open('rb') as f:
        f.seek(e.absolute_offset); raw = f.read(e.size)
    original_path = HERE / 'original_pact_187.pactex'; original_path.write_bytes(raw)
    original = ex.decode_ex(original_path); assert original.serialize_payload() == original.raw_payload
    page = Page(ex.decode_ex(original_path))
    before = {n: val(child(page.node(n), '種類別情報'), 'パーツタイプ').value.decode('cp932') for n in page.idx if maybe(page.node(n), '種類別情報') is not None}
    made, notes = make_items_layout(page, m)
    after = {n: val(child(page.node(n), '種類別情報'), 'パーツタイプ').value.decode('cp932') for n in page.idx if maybe(page.node(n), '種類別情報') is not None}
    for n in ITEMS_USED:
        assert n in after and after[n] == before[n], ('a part code or EX uses changed', n)
    assert set(before) <= set(after)
    payload = page.doc.serialize_payload()
    out = HERE / 'pact_187_items.pactex'; out.write_bytes(ex.encode_ex(page.doc.header, payload))
    reopened = ex.decode_ex(out)
    assert reopened.raw_payload == payload and reopened.serialize_payload() == payload, 'decode->encode round trip (187)'
    assert reopened.header[:24] == original.header[:24]
    anb.alice('ex', 'dump', '-o', TMP / 'pact_187_items.x', out)
    dump = (TMP / 'pact_187_items.x').read_text(encoding='utf-8', errors='replace')
    assert all(n in dump for n in made), 'alice dump lacks a new part name (187)'
    boxes = page_checks(reopened, m, '187')
    texts = [t for t, _ in I_TEXTS.values()]
    return out, dict(original=sha(original_path), output=sha(out), made=made, notes=notes, boxes=boxes, texts=texts)


def main():
    global GAUGE_TPL
    TMP.mkdir(exist_ok=True)
    ptr = json.loads(POINTER.read_text(encoding='utf-8-sig')); rt = Path(ptr['runtime']); src = rt / 'NightRemasterPact.afa'
    src_sha = sha(src)
    if src_sha != EXPECTED_PACT_SHA:
        raise SystemExit(f'STOP: runtime NightRemasterPact.afa is {src_sha}, expected {EXPECTED_PACT_SHA}')
    arc = read_afa3(src); e = arc.entries[ENTRY]; assert e.name == 'Asra/Mods.pactex', e.name
    with src.open('rb') as f:
        f.seek(e.absolute_offset); raw = f.read(e.size)
    original_path = HERE / 'original_pact_185.pactex'; original_path.write_bytes(raw)
    original = ex.decode_ex(original_path); assert original.serialize_payload() == original.raw_payload
    GAUGE_TPL = gauge_template(rt)
    page = Page(ex.decode_ex(original_path))
    before = {n: dict(type=page.idx[n]['node'] and val(child(page.node(n), '種類別情報'), 'パーツタイプ').value.decode('cp932'))
              for n in page.idx if maybe(page.node(n), '種類別情報') is not None}
    m = Measure(rt)
    made, notes = make_layout(page, m, rt)
    after = {n: val(child(page.node(n), '種類別情報'), 'パーツタイプ').value.decode('cp932') for n in page.idx if maybe(page.node(n), '種類別情報') is not None}
    for n in USED_BY_CODE:
        assert n in after and after[n] == before[n]['type'], ('a part code or EX uses changed', n)
    assert set(before) <= set(after)
    payload = page.doc.serialize_payload()
    out = HERE / 'pact_185_mods.pactex'; out.write_bytes(ex.encode_ex(page.doc.header, payload))
    reopened = ex.decode_ex(out)
    assert reopened.raw_payload == payload and reopened.serialize_payload() == payload, 'decode->encode round trip'
    assert reopened.header[:24] == original.header[:24]
    anb.alice('ex', 'dump', '-o', TMP / 'pact_185_mods.x', out)
    dump = (TMP / 'pact_185_mods.x').read_text(encoding='utf-8', errors='replace')
    assert all(n in dump for n in made), 'alice dump lacks a new part name'
    items_out, items = build_items(src, rt, m)
    cand = HERE / 'NightRemasterPact.afa'
    arcrep = rebuild(src, cand, {ENTRY: out, ITEMS_ENTRY: items_out})
    texts = [t for t, _ in TEXTS.values()] + [t for t, _ in NEW_TEXTS.values()] + TICKS + [lab for _, lab in NAV + LEFT_CHECKS + RIGHT_CHECKS + E_CHECKS] + items['texts']
    chars = anb.char_report(texts + [CHECK_PAD])
    glyphs = anb.glyph_check(rt / 'NightRemasterFont.fnl', texts)
    # geometry: clickable boxes must not overlap; everything inside the panel
    parts = proof.collect(reopened); bx = proof.boxes(parts, m.fnl)
    clickable = [b for b in bx if b['kind'] in ('checkbox', 'button', 'slider') and b['group'] != 'タブ／ボタン類']
    overlaps = []
    for i, a in enumerate(clickable):
        for b in clickable[i + 1:]:
            ax0, ay0, ax1, ay1 = a['rect']; bx0, by0, bx1, by1 = b['rect']
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                overlaps.append((a['name'], b['name']))
    assert not overlaps, overlaps
    outside = [b['name'] for b in bx if b['group'] not in ('タブ／ボタン類', 'レイアウト_タブテキスト') and b['name'] not in ('背景', '背景_星')
               and not (PANEL[0] <= b['rect'][0] and b['rect'][2] <= PANEL[2] and PANEL[1] <= b['rect'][1] and b['rect'][3] <= PANEL[3])]
    assert not outside, outside
    ev = dict(status='MODS_PACT185_187_STAGED_NOT_INSTALLED', builder='Claude Opus 5.5', source=dict(pointer=str(POINTER), runtime=str(rt), pact_sha256=src_sha),
              outputs={'original_pact_185.pactex': sha(original_path), 'pact_185_mods.pactex': sha(out), 'original_pact_187.pactex': items['original'],
                       'pact_187_items.pactex': items['output'], 'NightRemasterPact.afa': sha(cand)},
              archive=arcrep, changed_entries=[ENTRY, ITEMS_ENTRY], round_trip_exact=True, alice_ex_dump_parsed=True, made=made, hidden=HIDE,
              items_page=dict(made=items['made'], notes=items['notes'], used_by_code_kept=ITEMS_USED, boxes=items['boxes']),
              used_by_code_kept=USED_BY_CODE, characters=chars, glyphs=glyphs, notes=notes,
              boxes=[dict(name=b['name'], kind=b['kind'], rect=[round(v, 1) for v in b['rect']]) for b in bx])
    savej(HERE / 'build_evidence.json', ev)
    print('OK', sha(cand), len(made), 'new parts on 185,', len(items['made']), 'on 187')


if __name__ == '__main__':
    main()
