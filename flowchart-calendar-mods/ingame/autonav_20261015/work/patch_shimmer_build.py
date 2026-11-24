# -*- coding: utf-8 -*-
"""10-15: build + verifier for the shimmer (no star)."""
from pathlib import Path

LAYER = Path(__file__).resolve().parent.parent


def sub(path, pairs):
    s = path.read_text('utf8')
    for old, new in pairs:
        assert s.count(old) == 1, (path.name, old[:60], s.count(old))
        s = s.replace(old, new)
    path.write_text(s, 'utf8')


sub(LAYER / 'build_autonav.py', [
    ("STAR = dict(STAR_Z=500, BLINK_MS=900, HUE_MS=1800, STAR_X='-8.0', STAR_SIZE=40,\n            TR_STAR_X='44.0', TR_STAR_Y='-46.0', TR_STAR_SIZE=36)",
     "STAR = dict(BLINK_MS=1000, GOLD_G=55, GOLD_B=195, GLOW_W=720, GLOW_PAD=10, GLOW_X='-10.0', GLOW_A0=0, GLOW_A1=110,\n"
     "            BOX_R=150, BOX_G=110, BOX_B=20, ROW_H=40)"),
    ("ROW_H, STAR_DY = 40, -2", "ROW_H, STAR_DY = 40, 0"),
    ("    for part in (2026101501, 2026101502):", "    for part in (2026101503,):"),
    ("    b['KR_ANInfoCreate'] = (f\"\\tPUSHSTRUCTPAGE\\n\\tPUSH {info_create}\\n\\t.LOCALREF parentId\\n\\tCALLMETHOD 1\\n\"",
     "    b['KR_ANInfoCreate'] = (f\"\\t.LOCALREF parentId\\n\\tCALLFUNC KR_ANRowBegin\\n\\tPUSHSTRUCTPAGE\\n\\tPUSH {info_create}\\n\\t.LOCALREF parentId\\n\\tCALLMETHOD 1\\n\""),
    ("        parts=dict(choice_star=2026101501, training_star=2026101502),",
     "        parts=dict(choice_glow_band=2026101503, choice_row='the answer row parts found as new children of 矩形_項目位置 (tinted)',\n"
     "                   training='the target portrait (parent of the r20 box, tinted) and the r20 box (add colour)'),"),
])

sub(LAYER / 'verify_autonav.py', [
    ("STAR, TR_STAR = 2026101501, 2026101502\n", "GLOW = 2026101503\nGOLD = (255, 200, 60)\n"),
    # parts model: children, z, widths
    ("        self.cfg = {}\n        self.boxes = {}",
     "        self.cfg = {}\n        self.boxes = {}\n        self.kids = collections.defaultdict(list)\n        self.next_part = 1000500000"),
    ("        if lib == 'PartsEngine' and method == 'SetComponentMulColor':\n            b, g, r, n = st.pop(), st.pop(), st.pop(), st.pop()\n            self.colors[n].add((r, g, b))\n            self.part(n)['mul'] = (r, g, b)\n            return\n",
     "        if lib == 'PartsEngine' and method == 'SetComponentMulColor':\n            b, g, r, n = st.pop(), st.pop(), st.pop(), st.pop()\n            self.colors[n].add((r, g, b))\n            self.part(n)['mul'] = (r, g, b)\n            return\n"
     "        if lib == 'PartsEngine' and method == 'SetComponentAddColor':\n            b, g, r, n = st.pop(), st.pop(), st.pop(), st.pop()\n            self.part(n)['add'] = (r, g, b)\n            self.colors[('add', n)].add((r, g, b))\n            return\n"
     "        if lib == 'PartsEngine' and method == 'NumofChild':\n            st.append(len(self.kids[st.pop()]))\n            return\n"
     "        if lib == 'PartsEngine' and method == 'GetChild':\n            i = st.pop()\n            n = st.pop()\n            st.append(self.kids[n][i])\n            return\n"
     "        if lib == 'PartsEngine' and method == 'GetComponentPosZ':\n            st.append(self.parts.get(st.pop(), {}).get('z', 0))\n            return\n"
     "        if lib == 'PartsEngine' and method == 'Parts_GetPartsWidth':\n            st.pop()\n            n = st.pop()\n            st.append(self.parts.get(n, {}).get('w', 0))\n            return\n"
     "        if lib == 'PartsEngine' and method == 'Parts_GetParentPartsNumber':\n            st.append(self.parts.get(st.pop(), {}).get('parent', 0))\n            return\n"),
    # CreateParts of a row adds a box (child of the frame) and its text (child of the box)
    ("        if name == 'C_SelectMessInfo@CreateParts':\n            obj['made'] = aa[0]\n            return 1",
     "        if name == 'C_SelectMessInfo@CreateParts':\n            obj['made'] = aa[0]\n"
     "            box, txt = self.next_part, self.next_part + 1\n            self.next_part += 2\n"
     "            self.parts[box] = dict(kind='row box', show=1, z=20, parent=aa[0], mul=(255, 255, 255), row=obj['id'])\n"
     "            self.parts[txt] = dict(kind='row text', show=1, z=21, parent=box, mul=(255, 255, 255), row=obj['id'])\n"
     "            self.kids[aa[0]].append(box)\n            self.kids[box].append(txt)\n            obj['parts'] = (box, txt)\n            return 1"),
    ("        info_create = self.fs['KR_ANInfoCreate']['index']\n        for i in range(sim['n']):\n            info = {'kind': 'C_SelectMessInfo', 'id': i + 1}\n            r = self.method(info_create, info, [PARENT])\n            assert r == 1 and info['made'] == PARENT, ('row creation lost', info)\n        rec['stars'] = [dict(self.parts[STAR])] if STAR in self.parts else []",
     "        info_create = self.fs['KR_ANInfoCreate']['index']\n        self.parts[PARENT] = dict(kind='frame', show=1, z=5, w=600)\n        self.kids[PARENT] = []\n        rows = []\n"
     "        for i in range(sim['n']):\n            info = {'kind': 'C_SelectMessInfo', 'id': i + 1}\n            r = self.method(info_create, info, [PARENT])\n            assert r == 1 and info['made'] == PARENT, ('row creation lost', info)\n            rows.append(info['parts'])\n"
     "        rec['rows'] = rows\n        rec['glow'] = dict(self.parts[GLOW]) if GLOW in self.parts else None\n        rec['tints'] = collections.defaultdict(set)"),
    ("            self.run('KR_ANSelFrame')\n            if self.ended is not None:",
     "            self.run('KR_ANSelFrame')\n            for i, (bx, tx) in enumerate(rows):\n                rec['tints'][i + 1].add(self.parts[bx]['mul'])\n                rec['tints'][i + 1].add(self.parts[tx]['mul'])\n            if self.ended is not None:"),
    # A1: the shimmer instead of the star
    ("            st = rec['stars']\n            assert len(st) == 1 and st[0]['parent'] == PARENT and st[0]['text'] == '★' and st[0]['show'] == 1, ('A1 star', st)\n            x, y = st[0]['pos']\n            row_h, dy = vm.man['data']['row_h'], vm.man['data']['star_dy']\n            assert x < 0 and abs(y - ((want - 1) * row_h + dy)) < 0.01, ('A1 star row', e, t, st[0]['pos'])\n            al = vm.alpha.get(STAR, [])\n            assert al and min(al) >= 150 and max(al) <= 255 and max(al) - min(al) >= 90, ('A1 blink', min(al or [0]), max(al or [0]))\n            assert len(vm.colors[STAR]) >= 20, ('A1 colour cycle', len(vm.colors[STAR]))\n            assert STAR not in vm.parts, 'A1 star left after the choice'",
     "            g = rec['glow']\n            row_h, dy = vm.man['data']['row_h'], vm.man['data']['star_dy']\n"
     "            assert g and g['parent'] == PARENT and abs(g['pos'][1] - ((want - 1) * row_h + dy)) < 0.01 and g['z'] == 19, ('A1 glow band', e, t, g)\n"
     "            al = vm.alpha.get(GLOW, [])\n            assert al and min(al) <= 5 and max(al) >= 100 and max(al) <= 110, ('A1 glow blink', min(al or [0]), max(al or [0]))\n"
     "            for row in range(1, n + 1):\n                ts = rec['tints'][row]\n                if row == want:\n                    assert (255, 255, 255) in ts or any(c[1] > 250 for c in ts), ('A1 white phase', e, t, ts)\n                    assert any(c[1] <= 205 and c[2] <= 65 for c in ts), ('A1 gold phase', e, t, sorted(ts)[:3])\n                else:\n                    assert ts == {(255, 255, 255)}, ('A1 another row tinted', e, t, row, ts)\n"
     "            assert GLOW not in vm.parts, 'A1 glow band left after the choice'\n"
     "            assert all(vm.parts[p]['mul'] == (255, 255, 255) for bt in rec['rows'] for p in bt), 'A1 row left tinted'"),
    ("            assert r == -77 and rec['ended'] == 'player' and not rec['stars'], ('A4 untouched', label, e, rec)",
     "            assert r == -77 and rec['ended'] == 'player' and rec['glow'] is None and all(ts == {(255, 255, 255)} for ts in rec['tints'].values()), ('A4 untouched', label, e)"),
    ("        assert STAR not in vm.parts\n        counts['A3'] += 1", "        assert GLOW not in vm.parts\n        counts['A3'] += 1"),
    ("            vm.parts.pop(STAR, None)\n            vm.alpha.clear()", "            vm.parts.pop(GLOW, None)\n            vm.alpha.clear()"),
    ("            vm.parts.pop(STAR, None)\n            vm.sel = dict(n=4 if e in (322, 611, 30152) else 2, frames=frames_for(WAIT_MS) + 200, default=-77)",
     "            vm.parts.pop(GLOW, None)\n            vm.sel = dict(n=4 if e in (322, 611, 30152) else 2, frames=frames_for(WAIT_MS) + 200, default=-77)"),
    # A7: the portrait shimmer
    ("            vm.parts[box(t)] = dict(kind='box', show=1)\n            vm.parts.pop(TR_STAR, None)\n            vm.ended = None",
     "            cg = 1000600000 + t\n            vm.parts[cg] = dict(kind='portrait', show=1, mul=(255, 255, 255))\n            vm.parts[box(t)] = dict(kind='box', show=1, parent=cg, add=(0, 0, 0))\n            vm.colors.clear()\n            vm.ended = None"),
    ("                assert TR_STAR in vm.parts and vm.parts[TR_STAR]['parent'] == box(t), ('A7 star', vm.parts.get(TR_STAR))\n                vm.script = []                       # no dialog may run\n                r = vm.run('KR_ANTrainConfirm', [1, 200])\n                assert r == 1 and TR_STAR not in vm.parts, ('A7 auto confirm', r)",
     "                cs = vm.colors[cg]\n                assert any(c[1] <= 205 and c[2] <= 65 for c in cs) and len(cs) >= 10, ('A7 portrait shimmer', t, sorted(cs)[:3])\n"
     "                assert any(c[0] >= 140 for c in vm.colors[('add', box(t))]), ('A7 box glow', t)\n"
     "                vm.script = []                       # no dialog may run\n                r = vm.run('KR_ANTrainConfirm', [1, 200])\n"
     "                assert r == 1 and vm.parts[cg]['mul'] == (255, 255, 255) and vm.parts[box(t)]['add'] == (0, 0, 0), ('A7 auto confirm restores', r, vm.parts[cg], vm.parts[box(t)])"),
    ("                assert fired is None and TR_STAR not in vm.parts, ('A7 not a story Saturday', t)",
     "                assert fired is None and not vm.colors[cg], ('A7 not a story Saturday', t)"),
    # selftest
    ("        ('star never released', body_patch('KR_ANStarClear', ['CALLHLL', 'PartsEngine Release 0'], ['VM_POP_PUSH1'])),",
     "        ('glow band never released', body_patch('KR_ANDrop', ['CALLHLL', 'PartsEngine Release 0'], ['VM_POP_PUSH1'])),\n"
     "        ('row left gold', body_patch('KR_ANUntint', ['PUSH', '255'], ['PUSH', '254'])),"),
    ("        ('training star on the text part', body_patch('KR_ANTrainTick', ['CALLFUNC', 'KR_T20TrBox'], ['CALLFUNC', 'KR_T20TrPart'])),",
     "        ('training shimmer on the text part', body_patch('KR_ANTrainAnim', ['CALLFUNC', 'KR_T20TrBox'], ['CALLFUNC', 'KR_T20TrPart'])),"),
])
print('ok')
