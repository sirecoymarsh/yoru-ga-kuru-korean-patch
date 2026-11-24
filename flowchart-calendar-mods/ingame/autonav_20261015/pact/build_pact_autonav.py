"""Auto-navigation row for the Mods page (PACT 185, Asra/Mods.pactex). Stage only.

Claude Opus 5.5, 2026-10-15. Reads the installed runtime NightRemasterPact.afa
(read-only), adds seven parts to entry 185 and writes, in this folder only:
  original_pact_185.pactex   entry 185 exactly as installed
  pact_185_autonav.pactex    entry 185 with the new parts
  NightRemasterPact.afa      candidate archive (only entry 185 differs)
  layout_proof.png           static FNL/CG layout proof (not a game capture)
  build_evidence.json        hashes, coordinates and every check below

Parts are made the way Codex made KR_CheatLoot (build_instant_loot_20260915.build_pact):
deep copy of a page node, rename (name + コメント), 座標, text through ss(..., True)
(FNL proxy encoding), add to the parent's 子パーツ and 子パーツリスト. All seven go
under ルートパーツ like the later KR_HomeRateToggle / KR_AutoEquipToggle.

Checks (all asserted): runtime archive hash; decode->encode->decode round trip of
the new entry; removing the seven parts gives the installed payload byte for byte;
only entry 185 differs between source and candidate archive; every new character
is an FNL proxy (Korean) or plain CP932 that is not a proxy slot; each used glyph
exists in the shipped font and matches the glyph of the proxy map's own font build;
alice-tools parses the new entry; new boxes overlap nothing, stay inside the panel.
Nothing in the runtime folder, the Codex project, the AIN, EX or fonts is written.
"""
from pathlib import Path
import copy, hashlib, json, os, struct, subprocess, sys, zlib

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'lib')); sys.path.insert(0, str(HERE))
from codex_pact_helpers import (ex, ENC, encode, decode, read_afa3, rebuild, part, child, maybe, val,  # noqa: E402
                                allparts, setlist, ss, si, rename, txt_info, name, coords, scalar, add, remove)
import render_layout_proof as proof  # noqa: E402

POINTER = Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/current.json')
EXPECTED_PACT_SHA = 'd4de68c5d44ff5c80b9c41be21f86059d0ebca2717284f4ed8a7d43f6f029403'
ALICE = Path('P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830/tools/alice-tools-0.13.0/alice.exe')
MAP_FONT = Path('P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830_hangul_name_v4/wansung_build/build_output/NightRemasterFont_wansung2350.fnl')
TMP = HERE.parent / 'tmp'
ENTRY = 185

# ---------------------------------------------------------------------------
# Layout (absolute screen coordinates; the page is 1280x720, panel body x 160-1119).
# The Mods page has no free 100px-tall band any more (largest free rectangles with a 6px margin:
# 191x157 under the tab column, 570x46 right of the rewards title, 307x82 under the 달성률 toggle,
# 433x57 left of the footer buttons, 143x130 between speed and dungeon blocks). The only full-width gap
# is y 357-396 between KR_ModRewardHint (glyph box ends y 357) and the battle/dungeon blocks
# (KR_CheatTrap box starts y 396, KR_ModSpeedTitle y 400): the title and the five checkboxes
# go there as one 32px row. The note cannot sit beside or under that row; it goes to the
# largest free block that holds three 14px lines, the bottom-left footer (x 166-599,
# y 658-715, left of the 게임 종료 button), as a footnote that starts with 「※ 오토 내비게이션:」.
ROW_Y = 361                    # boxes y 361-393: 4px under the hint text, 3px over the KR_CheatTrap box
TITLE = ('KR_NavTitle', '오토 내비게이션', 363, 367, 270)   # name, text, x, y, z
TITLE_SIZE = 20                # KR_ModSpeedTitle is 23; 20 keeps the box-label/item spacing readable
LABEL_SIZE = 20                # KR_CheatTrap label is 24; at 24 the five do not fit in the gap
LABEL_PAD = '  '               # two ASCII spaces = 10px box-label gap at 20px (KR_CheatTrap uses U+3000,
                               # Codex's later toggles use ASCII spaces); item gaps are 21.5-22.5px
CHECKS = [                     # name, label, box x (row y = ROW_Y). 쿄카's box ends at x 778, clear
    ('KR_NavOff', '쓰지 않음', 498),     # of the KR_CheatTrap box under the row (x 783-815)
    ('KR_NavIzumi', '이즈미', 633),
    ('KR_NavKyouka', '쿄카', 746),
    ('KR_NavManami', '마나미', 843),
    ('KR_NavMakoto', '마코토', 957),
]
CHECK_Z0 = 271
NOTE = ('KR_NavNote', '\n'.join([
    '※ 오토 내비게이션: 고른 인물 쪽 답이 반짝이고 20초 뒤 자동으로 골라집니다.',
    '이야기가 있는 토요일엔 특훈 상대도 안내합니다. 세이브마다 따로 기억합니다.',
    '모자란 친밀도는 채워 줍니다(원래 규칙 밖 보정). 게임 중에만 바꿀 수 있습니다.',
]), 176, 660, 276)
NOTE_SIZE, NOTE_LINE_GAP = 14, 3     # 14px like KR_ModQuickHint; line pitch 17px
NEW = [TITLE[0]] + [c[0] for c in CHECKS] + [NOTE[0]]
PAGE_BOUNDS = (166, 6, 1105, 714)     # inside the opaque panel with a 6px margin
GAP = 2                               # minimum clearance to any existing box


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p, d): Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def alice(*args):
    env = dict(os.environ); env.update(TEMP=str(TMP), TMP=str(TMP))
    q = subprocess.run([str(ALICE), *map(str, args)], capture_output=True, timeout=120, env=env)
    assert q.returncode == 0, (args, q.stdout[-600:], q.stderr[-600:])
    return q


# ---- character and glyph checks ---------------------------------------------
PROXY_SLOTS = {bytes.fromhex(r['proxy_sjis_hex']) for r in __import__('codex_pact_helpers').MAPPING}


def char_report(texts):
    rows = []
    for ch in sorted(set(''.join(texts)) - {'\n'}):
        if ch in ENC:
            rows.append(dict(char=ch, kind='proxy', bytes=ENC[ch].hex()))
        else:
            b = ch.encode('cp932')            # raises if not CP932
            assert b not in PROXY_SLOTS, ('CP932 symbol collides with a Hangul proxy slot', ch, b.hex())
            assert b.decode('cp932') == ch, ('CP932 round trip', ch)
            rows.append(dict(char=ch, kind='cp932', bytes=b.hex()))
    return rows


def fnl_index(path, font_no=3):
    """Glyph table of one FNL font without loading the 300MB payload."""
    with open(path, 'rb') as f:
        magic, _u, _size, index_size = struct.unpack('<4sIII', f.read(16)); idx = f.read(index_size)
    q = 4; faces = []
    for fno in range(struct.unpack_from('<I', idx, 0)[0]):
        nf = struct.unpack_from('<I', idx, q)[0]; q += 4
        for _fi in range(nf):
            hh, _uu, n = struct.unpack_from('<III', idx, q); q += 12
            if fno == font_no: faces.append((hh, [struct.unpack_from('<HII', idx, q + 10 * j) for j in range(n)]))
            q += 10 * n
    return faces


def glyph_bytes(path, entry):
    w, pos, n = entry
    if not n: return (w, b'')
    with open(path, 'rb') as f: f.seek(pos); return (w, zlib.decompress(f.read(n)))


def glyph_check(runtime_font, texts):
    """Every glyph used exists in the shipped font; Hangul proxies equal the map's own font build."""
    from audit_message_pixel_widths import sjis_bytes_to_fnl_index
    rt = fnl_index(runtime_font); mp = fnl_index(MAP_FONT) if MAP_FONT.exists() else None
    out = dict(faces=len(rt), chars=0, nonblank=0, equal_to_map_font=0, compared=bool(mp))
    for ch in sorted(set(''.join(texts)) - {'\n'}):
        b = ENC[ch] if ch in ENC else ch.encode('cp932'); gi = sjis_bytes_to_fnl_index(b); out['chars'] += 1
        for fi, (hh, table) in enumerate(rt):
            g = glyph_bytes(runtime_font, table[gi])
            if not ch.isspace(): assert g[0] > 0 and g[1] and any(g[1]), ('empty glyph', ch, fi)
            if mp is not None and ch in ENC:
                assert len(mp) == len(rt) and mp[fi][0] == hh
                assert glyph_bytes(MAP_FONT, mp[fi][1][gi]) == g, ('glyph differs from the proxy map font', ch, fi)
        out['nonblank'] += not ch.isspace(); out['equal_to_map_font'] += int(mp is not None and ch in ENC)
    return out


# ---- the edit -----------------------------------------------------------------
def make_parts(d):
    """Deep-copied nodes, exactly Codex's KR_CheatLoot pattern."""
    root = d.blocks[2].payload.children[0]
    made = []
    # Title: copy of the section title 「전투 속도」 (KR_ModSpeedTitle: font 259, cyan edge), 20px.
    nm, text, x, y, z = TITLE
    t = copy.deepcopy(part(d, 'KR_ModSpeedTitle')); rename(t, nm); setlist(t, '座標', [x, y, z])
    ti = txt_info(t); ss(ti, 'テキスト', text, True); si(child(ti, 'テキスト装飾'), 'フォントサイズ', TITLE_SIZE)
    made.append(t)
    # Checkboxes: copies of KR_CheatTrap (same CG, font 259, edge, enabled), relabelled, 20px.
    # Codex kept KR_CheatTrap's U+3000 padding for KR_CheatLoot; here LABEL_PAD (see the layout notes).
    tpl = part(d, 'KR_CheatTrap')
    for k, (nm, label, x) in enumerate(CHECKS):
        c = copy.deepcopy(tpl); rename(c, nm); setlist(c, '座標', [x, ROW_Y, CHECK_Z0 + k])
        ci = child(c, '種類別情報'); old = decode(val(ci, 'テキスト').value); pad = old[:len(old) - len(old.lstrip())]
        assert pad == '\u3000', repr(pad)
        assert scalar(val(ci, 'フォントサイズ')) == 24
        ss(ci, 'テキスト', LABEL_PAD + label, True); si(ci, 'フォントサイズ', LABEL_SIZE); si(ci, 'チェック状態', 0)
        assert scalar(val(ci, '有効状態')) == 1
        made.append(c)
    # Note: copy of the 14px hint KR_ModQuickHint, three lines.
    nm, text, x, y, z = NOTE
    n = copy.deepcopy(part(d, 'KR_ModQuickHint')); rename(n, nm); setlist(n, '座標', [x, y, z])
    ni = txt_info(n); ss(ni, 'テキスト', text, True); dec = child(ni, 'テキスト装飾')
    si(dec, 'フォントサイズ', NOTE_SIZE); si(dec, '行間隔', NOTE_LINE_GAP); made.append(n)
    for p in made: add(root, p)
    return root, made


def main():
    TMP.mkdir(exist_ok=True)
    ptr = json.loads(POINTER.read_text(encoding='utf-8')); rt = Path(ptr['runtime']); src = rt / 'NightRemasterPact.afa'
    src_sha = sha(src)
    if src_sha != EXPECTED_PACT_SHA:
        raise SystemExit(f'STOP: runtime NightRemasterPact.afa is {src_sha}, expected {EXPECTED_PACT_SHA}')
    arc = read_afa3(src); e = arc.entries[ENTRY]; assert e.name == 'Asra/Mods.pactex', e.name
    with src.open('rb') as f: f.seek(e.absolute_offset); raw = f.read(e.size)
    original_path = HERE / 'original_pact_185.pactex'; original_path.write_bytes(raw)
    original = ex.decode_ex(original_path); assert original.serialize_payload() == original.raw_payload
    d = ex.decode_ex(original_path)
    names_before = [name(t) for t in allparts(d.blocks[2].payload.children[0])]
    assert not set(NEW) & set(names_before), 'a new name already exists on the page'

    root, made = make_parts(d)
    names_after = [name(t) for t in allparts(root)]
    assert len(names_after) == len(set(names_after)) and names_after[:len(names_before)] == names_before
    assert [name(t) for t in child(root, '子パーツ').children] == [i.value.payload.replacement.decode('cp932') if i.value.payload.replacement else i.value.payload.value.decode('cp932') for i in val(root, '子パーツリスト').items]
    payload = d.serialize_payload()

    out = HERE / 'pact_185_autonav.pactex'; out.write_bytes(ex.encode_ex(d.header, payload))
    reopened = ex.decode_ex(out)
    assert reopened.raw_payload == payload and reopened.serialize_payload() == payload, 'decode->encode round trip'
    assert reopened.header[:24] == original.header[:24] and reopened.header[:4] == b'HEAD'
    # independent parser: alice-tools reads the new entry
    alice('ex', 'dump', '-o', TMP / 'pact_185_autonav.x', out)
    dump = (TMP / 'pact_185_autonav.x').read_text(encoding='utf-8', errors='replace')
    assert all(n in dump for n in NEW), 'alice dump lacks a new part name'

    # inverse: drop exactly the seven new parts -> installed payload, byte for byte
    inv = ex.decode_ex(out); inv_root = inv.blocks[2].payload.children[0]
    for n in NEW: remove(inv_root, n)
    assert inv.serialize_payload() == original.raw_payload, 'removing the new parts must give the installed entry 185'

    # candidate archive: only entry 185 differs
    cand = HERE / 'NightRemasterPact.afa'; archive = rebuild(src, cand, {ENTRY: out})
    new_arc = read_afa3(cand); changed = []
    with src.open('rb') as a, cand.open('rb') as b:
        assert len(arc.entries) == len(new_arc.entries)
        for x, y in zip(arc.entries, new_arc.entries):
            assert (x.no, x.name, x.name_raw_hex, x.unknown0, x.unknown1) == (y.no, y.name, y.name_raw_hex, y.unknown0, y.unknown1)
            a.seek(x.absolute_offset); b.seek(y.absolute_offset); pa = a.read(x.size); pb = b.read(y.size)
            if pa != pb: changed.append(x.no)
            if x.no == ENTRY: assert pb == out.read_bytes()
    assert changed == [ENTRY], changed
    # independent reader: alice-tools extracts every entry of both archives; only 185 may differ
    import shutil
    trees = {}
    for tag, path in [('src', src), ('cand', cand)]:
        dst = TMP / f'alice_{tag}'
        if dst.exists(): shutil.rmtree(dst)
        for x in arc.entries: (dst / x.name).parent.mkdir(parents=True, exist_ok=True)   # alice does not mkdir
        alice('ar', 'extract', '--raw', '-f', '-o', dst, path)
        trees[tag] = {p.relative_to(dst).as_posix(): p.read_bytes() for p in dst.rglob('*') if p.is_file()}
    assert set(trees['src']) == set(trees['cand']) and len(trees['src']) == len(arc.entries)
    alice_diff = sorted(k for k in trees['src'] if trees['src'][k] != trees['cand'][k])
    assert alice_diff == [e.name] and trees['cand'][e.name] == out.read_bytes(), alice_diff
    for tag in trees: shutil.rmtree(TMP / f'alice_{tag}')
    assert sha(src) == src_sha, 'runtime archive changed during the build'

    # characters and glyphs
    texts = [TITLE[1]] + [LABEL_PAD + c[1] for c in CHECKS] + [NOTE[1]]
    chars = char_report(texts); glyphs = glyph_check(rt / 'NightRemasterFont.fnl', texts)

    # geometry: measured boxes of every visible part (same code that draws the proof)
    fnl = proof.Fnl(rt / 'NightRemasterFont.fnl'); bx = proof.boxes(proof.collect(reopened), fnl)
    new_boxes = {b['name']: b for b in bx if b['name'] in NEW}; assert set(new_boxes) == set(NEW)
    old_boxes = [b for b in bx if b['name'] not in NEW] + [dict(name='背景_星 sparkle', rect=r) for r in proof.icon_rects()]
    clear = {}
    for n, b in new_boxes.items():
        x0, y0, x1, y1 = b['rect']; L, T, R, B = PAGE_BOUNDS
        assert L <= x0 and x1 <= R and T <= y0 and y1 <= B, ('outside the panel', n, b['rect'])
        best = 1e9
        for o in old_boxes + [v for k, v in new_boxes.items() if k != n]:
            p0, q0, p1, q1 = o['rect']
            dx = max(p0 - x1, x0 - p1, 0); dy = max(q0 - y1, y0 - q1, 0)
            assert dx >= GAP or dy >= GAP, ('overlap', n, o['name'], b['rect'], o['rect'])
            best = min(best, max(dx, dy))
        clear[n] = round(best, 1)
    legend = ['분홍 모서리 = 새 부품 7개: ' + ' · '.join('%s (%d,%d)' % (n, *coords(part(reopened, n))[:2]) for n in NEW),
              f'제목 {TITLE_SIZE}px · 체크박스 글자 {LABEL_SIZE}px(칸 32px) · 안내 {NOTE_SIZE}px, 줄 간격 {NOTE_SIZE + NOTE_LINE_GAP}px. 체크 칸은 모두 꺼진 모양(통상 CG)으로 그림.',
              '탭 글자(원점 모드 2)는 가운데 맞춤 근사, 슬라이더는 판정 영역 + 커서 CG로 그림. 게임 화면 캡처가 아님.']
    parts, _ = proof.render(out, rt, HERE / 'layout_proof.png', mark=NEW, notes=legend, legend_h=100,
                            zoom=(345, 330, 1105, 432, 1.6))

    ev = dict(status='AUTONAV_PACT185_STAGED_NOT_INSTALLED', builder='Claude Opus 5.5', time=__import__('datetime').datetime.now().astimezone().isoformat(),
              source=dict(pointer=str(POINTER), runtime=str(rt), pact_sha256=src_sha, entry=ENTRY, entry_name=e.name, entry_sha256=hashlib.sha256(raw).hexdigest()),
              outputs={p.name: sha(p) for p in [original_path, out, cand]},
              archive=archive, changed_entries=changed,
              round_trip_exact=True, inverse_exact=True, alice_ex_dump_parsed=True,
              alice_ar_extract_all_entries=dict(entries=len(arc.entries), differing=alice_diff),
              parts=[dict(name=n, type=new_boxes[n]['kind'], xyz=coords(part(reopened, n)), rect=[round(v, 1) for v in new_boxes[n]['rect']],
                          text=new_boxes[n].get('text'), font_size=(new_boxes[n].get('style') or {}).get('size'), clearance_px=clear[n]) for n in NEW],
              templates=dict(KR_NavTitle='KR_ModSpeedTitle', checkboxes='KR_CheatTrap', KR_NavNote='KR_ModQuickHint'),
              parent='ルートパーツ (root, like KR_HomeRateToggle)', characters=chars, glyphs=glyphs,
              proof=dict(path=str(HERE / 'layout_proof.png'), sha256=sha(HERE / 'layout_proof.png'), native_capture=False),
              not_touched=['runtime folder', 'Codex project files', 'AIN', 'EX', 'fonts', 'other PACT entries', 'saves'])
    savej(HERE / 'build_evidence.json', ev)
    print(json.dumps({k: ev[k] for k in ['status', 'outputs', 'changed_entries']}, ensure_ascii=False, indent=2))
    for p in ev['parts']: print(p['name'], p['xyz'], p['rect'], 'clear', p['clearance_px'])


if __name__ == '__main__':
    main()
