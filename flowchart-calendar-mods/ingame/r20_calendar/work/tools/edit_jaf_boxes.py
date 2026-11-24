"""r20 one-off: backing boxes behind the partner-select labels (readability over the room background and the stand picture)."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'claude_calendar_r20.jaf'
s = p.read_text(encoding='utf8')
rep = [
    ('int KR_T20TrPart(int p) { return 2026092010 + p; }',
     'int KR_T20TrPart(int p) { return 2026092010 + p; }\nint KR_T20TrBox(int p) { return 2026092020 + p; }'),
    ('''        if (active <= 0 || p == active) PartsEngine.SetComponentMulColor(n, 255, 255, 255);
        else PartsEngine.SetComponentMulColor(n, 110, 110, 110);''',
     '''        if (active <= 0 || p == active) PartsEngine.SetComponentMulColor(n, 255, 255, 255);
        else PartsEngine.SetComponentMulColor(n, 128, 128, 128);'''),
    ('''void KR_T20TrClear() {
    for (int p = 2; p <= 8; p++) {
        int n = KR_T20TrPart(p);
        if (PartsEngine.IsExist(n)) PartsEngine.Release(n);
    }
}''',
     '''void KR_T20TrClear() {
    for (int p = 2; p <= 8; p++) {
        int n = KR_T20TrPart(p);
        if (PartsEngine.IsExist(n)) PartsEngine.Release(n);
        int b = KR_T20TrBox(p);
        if (PartsEngine.IsExist(b)) PartsEngine.Release(b);
    }
}'''),
    ('''    for (int q = 2; q <= 8; q++) {
        if (PartsEngine.IsExist(KR_T20TrPart(q))) return;
    }''',
     '''    for (int q = 2; q <= 8; q++) {
        if (PartsEngine.IsExist(KR_T20TrPart(q))) return;
        if (PartsEngine.IsExist(KR_T20TrBox(q))) return;
    }'''),
    ('''        int n = KR_T20TrPart(p);
        PartsEngine.Parts_SetText(n, "", 1);''',
     '''        int b = KR_T20TrBox(p);
        Ｐ＿構築手順＿作成(b, 124, 52, 1);
        Ｐ＿構築手順＿色塗り全(b, 0, 0, 0, 150, 1);
        Ｐ＿構築ビルド(b, 1);
        PartsEngine.Parts_SetParentPartsNumber(b, cg);
        PartsEngine.SetComponentPos(b, 4.0, -56.0);
        PartsEngine.SetComponentPosZ(b, @@TR_BOX_Z@@);
        PartsEngine.SetComponentShow(b, true);
        int n = KR_T20TrPart(p);
        PartsEngine.Parts_SetText(n, "", 1);'''),
    ('        PartsEngine.SetComponentPos(n, 6.0, -48.0);', '        PartsEngine.SetComponentPos(n, 10.0, -52.0);'),
]
for a, b in rep:
    assert s.count(a) == 1, (a[:60], s.count(a))
    s = s.replace(a, b)
s = s.replace('//   · 특훈 상대 고르기(C_SceneTraining@RunSelectPartner): 보이는 초상마다 고정 번호 글 파츠 하나(두 줄, 초상 위).',
              '//   · 특훈 상대 고르기(C_SceneTraining@RunSelectPartner): 보이는 초상마다 고정 번호 판 · 글 파츠 둘(두 줄, 초상 위).')
p.write_text(s, encoding='utf8')
b = Path(__file__).resolve().parents[2] / 'build_calendar_r20.py'
t = b.read_text(encoding='utf8')
rep = [
    ("ST_PANEL, ST_TEXT, TR_BASE = 2026092001, 2026092002, 2026092010",
     "ST_PANEL, ST_TEXT, TR_BASE, TR_BOX = 2026092001, 2026092002, 2026092010, 2026092020"),
    ("ST_PANEL_Z, ST_TEXT_Z, TR_Z = 40, 41, 20          # relative to the parent part (status root z 204 -> 244/245; portrait ~253 -> ~273)",
     "ST_PANEL_Z, ST_TEXT_Z, TR_BOX_Z, TR_Z = 40, 41, 20, 21   # relative to the parent part (status root z 204 -> 244/245; portrait 253.. -> 273..)"),
    ("    for k, v in dict(ST_PANEL_Z=ST_PANEL_Z, ST_TEXT_Z=ST_TEXT_Z, TR_Z=TR_Z).items():",
     "    for k, v in dict(ST_PANEL_Z=ST_PANEL_Z, ST_TEXT_Z=ST_TEXT_Z, TR_BOX_Z=TR_BOX_Z, TR_Z=TR_Z).items():"),
    ("    assert ('return %d + p;' % TR_BASE) in jaf",
     "    assert ('return %d + p;' % TR_BASE) in jaf and ('return %d + p;' % TR_BOX) in jaf"),
    ("        parts=dict(status_panel=ST_PANEL, status_text=ST_TEXT, training_labels=[TR_BASE + p for p in range(2, 9)],\n"
     "                   z_relative=dict(status_panel=ST_PANEL_Z, status_text=ST_TEXT_Z, training_label=TR_Z)),",
     "        parts=dict(status_panel=ST_PANEL, status_text=ST_TEXT, training_labels=[TR_BASE + p for p in range(2, 9)],\n"
     "                   training_boxes=[TR_BOX + p for p in range(2, 9)],\n"
     "                   z_relative=dict(status_panel=ST_PANEL_Z, status_text=ST_TEXT_Z, training_box=TR_BOX_Z, training_label=TR_Z)),"),
]
for a, c in rep:
    assert t.count(a) == 1, (a[:60], t.count(a))
    t = t.replace(a, c)
b.write_text(t, encoding='utf8')
print('ok')
