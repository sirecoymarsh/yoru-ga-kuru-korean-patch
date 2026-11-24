"""r19: the handoff's name sample table (rules 1-8, 11): the in-game strings (baked tables) next to the raw data they come from
(graph/schedule.json triggers / labels.json speakers / groups.json rows). No dialogue, no choice text. Writes 증거/name_samples.md."""
import sys, json
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r19lib as L

t = L.readj(L.WORK / 'build' / 'tables.json')
sch = {e['id']: e for e in L.readj(L.FLOW / 'graph' / 'schedule.json')['events']}
lab = L.readj(L.FLOW / 'graph' / 'labels.json')
r15 = L.readj(L.R15 / 'work' / 'build' / 'tables.json')
cards = r15['cards']
card_of = {s: c for c in cards for s in c['stages']}
chip_of = {s: ch for ch in r15['chips'] for s in ch['scenes']}


def trig(no):
    out = []
    for x in sch[no]['triggers']:
        d = x['kind']
        if x.get('source'):
            d += ' ' + x['source'].split('::')[-1]
        if x.get('date'):
            d += ' %s/%s' % tuple(x['date'])
        if x.get('time_id'):
            d += ' t%d' % x['time_id']
        if x.get('page'):
            d += ' p%d s%d' % (x['page'], x['slot'])
        if x.get('from'):
            d += ' from E%05d' % x['from'] + (' via %s' % x['via_choice'] if x.get('via_choice') else '')
        if x.get('feeling_gate'):
            d += ' feeling_gate %s' % json.dumps(x['feeling_gate'], ensure_ascii=False)
        out.append(d)
    return '; '.join(out[:3]) + (' …' if len(out) > 3 else '')


def sp(no):
    return '/'.join(lab['cards'][str(no)].get('speakers') or [])[:40]


def row(rule, no, what):
    c = card_of.get(no)
    head = t['heads'][str(c['k'])] if c and c['entry'] == no else None
    name = t['ev_head'][str(no)]
    short = t['ev_short'][str(no)]
    where = ('카드 %s %d/%d단계' % (c['key'], c['stages'].index(no) + 1, c['size'])) if c else ('서랍 %s' % chip_of[no]['id'])
    extra = ''
    if rule == '11':
        extra = ' · 언제: ' + t['whens'][str(no)].replace('\n†　　　', ' ⏎ ')
    return '| %s | E%05d | %s | %s | %s | %s · 화자 %s · %s%s |' % (
        rule, no, (head or name).replace('|', '/'), short, what, where, sp(no), trig(no), extra)


PICK = [('1', 258, '날짜 박힌 본편 묶음'), ('1', 121, '날짜 박힌 본편'), ('1', 401, '날짜 박힌 본편(친밀도 조건)'),
        ('2', 273, '갈래 1 · 함께한 인물'), ('2', 110, '갈래 2'), ('2', 59, '사슬 단계 · 함께한 인물'), ('2', 832, '던전 묶음 단계 · 자기 조각'),
        ('3', 5024, '겹치는 카드 · 같은 인물 1'), ('3', 5025, '겹치는 카드 · 같은 인물 2'), ('3', 10181, '주인공만 말함'), ('3', 1, '동료 화자 없음'),
        ('4', 41, 'B1 → 사건 1'), ('4', 522, 'Entrance → 입구'), ('4', 24, 'Exit → 출구'), ('4', 76, 'R1 → 보스'), ('4', 50001, '최종장'),
        ('5', 2221, '마나미 레인 · 마코토와'), ('5', 2001, '이즈미 레인 · 쿄카와'), ('5', 5001, '짝 없음 → 단둘이'), ('5', 5000, '주인공 혼자'),
        ('6', 1101, '특훈 뒤 대화'), ('6', 30024, '우선 대화(차례 ≠ 사슬 순)'), ('6', 1001, '초대(특훈 권유)'), ('6', 1181, '반한 뒤 대화'),
        ('7', 60015, '회상 칸 + 원본 날짜'), ('7', 60201, '사슬 재생본 · 답 1'), ('7', 60205, '사슬 재생본 · 이어서'), ('7', 50101, '원본이 서랍 장면'),
        ('8', 6001, '시스템'), ('8', 55, '미사용 1'), ('8', 122, '미사용 3'),
        ('11', 20061, '조건부 호출 feeling(3)>=30'), ('11', 30157, 'E30152 갈래 < 50'), ('11', 30158, 'E30152 갈래 >= 50'),
        ('11', 10501, 'E10501 최고 친밀도'), ('11', 10021, '우선 대화 GetFeeling>=15')]
lines = ['| 규칙 | E번호 | 게임 안 이름(카드 · 장면 쪽 첫 줄) | 목록 줄 | 무엇 | 근거(자리 · 화자 · 트리거) |', '|---|---|---|---|---|---|']
for rule, no, what in PICK:
    lines.append(row(rule, no, what))
(L.EVID / 'name_samples.md').write_text('\n'.join(lines) + '\n', 'utf8')
print('\n'.join(lines))
