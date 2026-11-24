# -*- coding: utf-8 -*-
"""Read only (10-15): for every Mods setting, which live functions read it (callers of the getter / readers of the global),
outside the options page itself. Base = the installed AIN (auto-nav install)."""
import sys, re, json, collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mdlib as L

bp = L.base_paths()
m = L.read_meta(bp['meta'])
vers = L.versions(bp['raw'])
names = {f['index']: L.raw_symbol(m, f['index']) for f in m['functions']}
gname = {i: g.get('name') for i, g in enumerate(m['globals'])}
live = {}
for fid, vs in vers.items():
    for v in vs:
        if v['start'] == m['functions'][fid]['address']:
            live[fid] = v['ops']
SETTINGS = {
    '함정 즉시 해체': ['KR_GetTrap'], '전투 이펙트 보지 않기': ['KR_GetQuick'], '다음 층 경로 표시': ['KR_GetRoute'],
    '일반 적 즉시 처치': ['KR_GetLoot'], '소탕 버튼 표시': ['KR_GetSweep'], '자동 장착·요소석 추천': ['KR_GetAutoEquip'],
    '강화 자동 전투': ['KR_GetSmartAuto'], '전투 속도': ['KR_Speed'], '달성률 항상 표시': ['KR_T8HomeRateOn'],
    '자동 회복(아이템)': ['KR_ItemsEnabled', 'KR_ItemsGetThreshold', 'KR_ItemsAllowed', 'KR_ItemsReserve'],
    '보상 배율 계산': ['KR_MultiplierCalc'],
}
GLOBALS = {'경험치 배율': 'L_CasualMode::RateEX', '월편 배율': 'L_CasualMode::RateMoney', '훈련치 배율': 'L_CasualMode::RateTrainging',
           '동료 특훈치 배율': 'L_CasualMode::RatePairTraining'}
fid_by = collections.defaultdict(list)
for i, n in names.items():
    fid_by[n].append(i)
SKIP = re.compile(r'^(C_ConfigView@|KR_Multiplier(Get|Set)|KR_Get|KR_Set|KR_Items(Get|Set)|KR_T8HomeRate(Get|Set)|KR_SetBattleMode)')
out = {}
for label, getters in SETTINGS.items():
    ids = {i: g for g in getters for i in fid_by.get(g, [])}
    callers = collections.Counter()
    for fid, ops in live.items():
        for ad, op in ops:
            z = re.match(r'CALLFUNC 0x([0-9a-f]+)$', op)
            if z and int(z[1], 16) in ids and not SKIP.match(names[fid]):
                callers[names[fid]] += 1
    out[label] = dict(getters=getters, callers=dict(callers))
gidx = {v: k for k, v in gname.items()}
for label, g in GLOBALS.items():
    gi = gidx[g]
    readers = collections.Counter()
    for fid, ops in live.items():
        for k, (ad, op) in enumerate(ops):
            if op == 'PUSHGLOBALPAGE' and k + 1 < len(ops) and ops[k + 1][1] == 'PUSH 0x%x' % gi:
                if not SKIP.match(names[fid]):
                    readers[names[fid]] += 1
    out[label] = dict(global_=g, readers=dict(readers))
(Path(__file__).resolve().parent / 'consumer_audit.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf8')
for k, v in out.items():
    who = v.get('callers', v.get('readers'))
    print(k, '|', len(who), '|', ', '.join(sorted(who))[:600])
