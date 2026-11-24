"""Read-only live audit; write a separate, hash-bound review candidate, never install."""
from pathlib import Path
import collections
import datetime
import hashlib
import html
import json
import re

from polish_translation_20260917 import raw_messages
from audit_message_pixel_widths import parse_fnl_font, select_fnl_face, load_proxy_indices, WidthMeasurer

HERE = Path(__file__).resolve().parent
R = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')
Q = R / 'claude_qa_20260923'
OUT = R / 'handoff_review_20260923'
MAP = R / 'evidence/auto_walk_20260922/source/installed_translation_map.json'
PROXY = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4\wansung_build\build_output\fnl_proxy_map_wansung2350.json')

def readj(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def writej(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def writejl(name, rows):
    (OUT / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


# Primary-model decisions. Replacement applies ONLY to these reviewed display IDs.
# Named real-world antecedents are inferred from source spellings AND surrounding scenes.
GROUPS = [
    ('네이키', '나이키', [94853], 'ネイキ', []),
    ('아베다스', '아디다스', [94859], 'アベダス', []),
    ('우니클로', '유니클로', [99650], 'ウニクロ', []),
    ('왁도날드', '맥도날드', [93280], 'ワクドナルド', []),
    ('써니', '소니', [94827], 'サニー; 휴대전화 디자인 비교 장면', []),
    ('KOKO 3번', '코코이찌방야', [94804], 'ＫＯＫＯ三番; 카레와 토핑 주문', ['https://www.cocoichibanya.co.kr/main.jsp']),
    ('제미', '제니', [94095, 97826], 'ジェミー; 인형/크리스마스 한정판', ['https://www.takaratomy.co.jp/product_release/pdf/p230531.pdf']),
    ('E-SHOCK', 'G-SHOCK', [94096], 'E-SHOCK; 한정판 시계', ['https://www.casio.com/jp/watches/gshock/']),
    ('산요도', '카이요도', [98047], '山洋堂; 북두의 권 피규어 제작사', ['https://kaiyodo.co.jp/items/tag/%E5%8C%97%E6%96%97%E3%81%AE%E6%8B%B3/']),
    ('데카피타', '데카비타', [46136, 46142], 'デカピタ; 음료', ['https://www.suntory.co.jp/softdrink/dekavita/products/']),
    ('드림캐스', '드림캐스트', [31882, 93997, 94005, 95018], '夢キャス; 게임기', ['https://www.sega.jp/history/hard/dreamcast/']),
    ('프소', 'PSO', [93993, 93995, 95016, 95018], 'ぷそ; 드림캐스트 온라인 게임', ['https://www.sega.jp/game/detail/pso2/']),
    ('마른 판다', '타레판다', [92811, 92976, 94309, 94324, 95474, 95482], '枯れぱんだ; 캐릭터/열쇠고리/뽑기', ['https://www.san-x.co.jp/ja/characters/tarepanda/']),
    ('존프', '점프', [94929, 94931, 99389], 'ジョンプ; 월요일 발매 소년만화 잡지', []),
    ('번터×번터', '헌터×헌터', [94942], 'バンター×バンター; 소년 점프 연재작', []),
    ('칸담', '건담', [24932, 83234, 97668], 'カンダム; LSI 게임/프라모델', []),
    ('칸프라', '건프라', [97672], 'カンプラ', []),
    ('후르츠 보스켓', '후르츠 바스켓', [97791], 'フルーツボスケット', []),
    ('브리트라맨', '울트라맨', [98029], 'ヴリトラマン', []),
    ('누폰', '스폰', [98032, 98035], 'ヌポーン; 해외 피규어', []),
    ('복두의 권', '북두의 권', [98047, 98050], '僕との拳', ['https://kaiyodo.co.jp/items/tag/%E5%8C%97%E6%96%97%E3%81%AE%E6%8B%B3/']),
    ('호게몬', '포켓몬', [100268], 'ホゲモン', ['https://www.pokemonkorea.co.kr/pokedex/view/37']),
    ('비카츄', '피카츄', [100268, 99797], 'ビガチュウ/ポケットビガジュウ', ['https://www.pokemonkorea.co.kr/pokedex/view/37', 'https://www.nintendo.com/jp/hardware/index.html']),
    ('워닝 무스메', '모닝구무스메', [3368], 'ワーニング娘; 여성 보컬 그룹 패러디', ['https://helloproject.com/morningmusume/']),
    ('워무스', '모무스', [3364, 3368, 3377, 96375, 99373], 'ワー娘; 모닝구무스메 약칭 モー娘', ['https://helloproject.com/morningmusume/']),
]
CRIES = {
    100261: '「피카-♪」',
    100265: '「피카-, 피카피카, 피-카.',
    100266: '　피피피피카카」',
    100271: '「피카피카♪」',
    100275: '「피-카, 피카, 피피카 핏핏핏, 츄-!」',
    100280: '「피카? 미와사카한테는 반응이',
    100281: '　좋았는데…… 피카…… 피카피……',
    100282: '　피카피카아」',
}
CONTEXT_EDITS = {
    3367: ('「워~ 무~ 스으으~~？」', '「모~ 무~ 스으으~~？」', '바로 다음 줄의 모무스 약칭을 늘여 말하는 대사 일치'),
    95477: ('「응, 바짝 마른 모습이 귀엽잖아」', '「응, 축 처진 모습이 귀엽잖아」',
            '사용자 실명 전환에 따른 각색: 枯れぱんだ의 마른 외형 말장난을 실제 타레판다의 늘어진 외형에 맞춤; 원문의 직역이 아님'),
}


def main():
    pointer = readj(R / 'ui_cumulative/current.json')
    rt = Path(pointer['runtime'])
    manifest = readj(pointer['manifest'])
    assert sha(pointer['manifest']) == pointer['manifest_sha256'], 'Manifest changed'
    assert sha(MAP) == '7c111362d5065cb7d8e130c67828cba65f05418b56c787ed5d0a43039830a76d'
    source = Q / 'pending_merge/final_map_20260923.jsonl'
    assert sha(source) == '797672210f698ef6f938d44d1cd769891eeb53c76959b0c47731d2d1e14f1c24'
    frozen_inputs = [Path(__file__), source, Q / 'pending_merge/final_map_20260923.summary.json',
                     Q / 'pending_merge/user_overlay.json', Q / 'pending_merge/manual_allow.jsonl',
                     Q / 'pending_merge/merge_final.py', Q / 'review_base/inputs.json',
                     Q / 'corrections/opus_B_decisions.jsonl', MAP, PROXY,
                     HERE / 'message_window_classification.json', HERE / 'message_page_groups.json',
                     Path(pointer['manifest']), R / 'ui_cumulative/current.json']
    inputs = {str(p): sha(p) for p in frozen_inputs}
    live_checks = []
    for row in manifest['files']:
        actual = sha(rt / row['path'])
        live_checks.append(dict(path=row['path'], expected=row['sha256'], actual=actual, match=actual == row['sha256']))
    assert all(x['match'] for x in live_checks), 'Live files differ; reject fixed-ID merge'
    proxy = readj(PROXY)
    enc = {x['unicode_character']: bytes.fromhex(x['proxy_sjis_hex']) for x in proxy['mapping']}
    dec = {x['proxy_character']: x['unicode_character'] for x in proxy['mapping']}
    decode = lambda b: ''.join(dec.get(c, c) for c in b.decode('cp932'))
    encode = lambda s: b''.join(enc[c] if c in enc else c.encode('cp932') for c in s)
    raw = raw_messages((rt / 'NightRemaster.ain').read_bytes())[3]
    current = [decode(b) for b in raw]
    t = {x['numeric_id']: x for x in readj(MAP)['entries']}
    assert all(x['target'] == current[i] for i, x in t.items()), 'Installed map not exact'
    proposal_rows = [json.loads(s) for s in source.read_text('utf-8').splitlines() if s]
    f = {x['m_id']: x for x in proposal_rows}
    assert len(f) == len(proposal_rows) == 1774
    assert all(x['current'] == current[i] and x['proposed'] and x['proposed'] != current[i] for i, x in f.items())
    candidate = {i: x['proposed'] for i, x in f.items()}
    decisions = []
    for old, new, ids, rationale, links in GROUPS:
        for i in ids:
            before = candidate.get(i, current[i])
            assert old in before, (i, old, before)
            after = before.replace(old, new)
            candidate[i] = after
            decisions.append(dict(m_id=i, old_name=old, real_name=new, before=before, after=after,
                                  rationale=rationale, identification='Codex contextual inference; real-name spelling checked',
                                  reference_links=links, translator_model='Codex internal'))
    for i, after in CRIES.items():
        before = candidate.get(i, current[i])
        assert '비' in before
        candidate[i] = after
        decisions.append(dict(m_id=i, old_name='피카츄 흉내의 비카 계열', real_name='피카 계열',
                              before=before, after=after, rationale='같은 장면의 이름/흉내 일치; 끊어 말하기와 반복 유지',
                              identification='Scoped to the verified imitation scene 100261..100282',
                              reference_links=[], translator_model='Codex internal'))
    for i, (expected, after, rationale) in CONTEXT_EDITS.items():
        before = candidate.get(i, current[i])
        assert before == expected
        candidate[i] = after
        decisions.append(dict(m_id=i, old_name='명칭 연동 대사', real_name='실명 표기와 일치', before=before,
                              after=after, rationale=rationale, identification='Context reviewed by primary Codex',
                              reference_links=[], translator_model='Codex internal'))
    brand_ids = {d['m_id'] for d in decisions}
    noop_ids = sorted(i for i, text in candidate.items() if text == current[i])
    candidate = {i: text for i, text in candidate.items() if text != current[i]}
    classes = {x['message_id']: x for x in readj(HERE / 'message_window_classification.json')['rows']}
    _, faces = parse_fnl_font(rt / 'NightRemasterFont.fnl', 0)
    face, den, _ = select_fnl_face(faces, 60)
    indices, _ = load_proxy_indices(proxy, len(face.widths))
    measure = WidthMeasurer(face, den, indices, -2., 2., 0.)
    checks = []
    width_issues = []
    errors = []
    tokens = re.compile(r'%[-+0-9.*]*[sdifuxX]|\{\d+\}|[\x00-\x1f\x7f]')
    for i, proposed in sorted(candidate.items()):
        c = classes.get(i, {})
        supported = (not c.get('ambiguous', True) and c.get('font_commands') == [0]
                     and c.get('window_types') in [['Face'], ['Text'], ['All']]
                     and c.get('message_roles') == ['Body'])
        budget = (668 if c.get('window_types') == ['Face'] else 884) if supported else None
        old_width = measure.measure(current[i], True)
        new_width = measure.measure(proposed, True)
        item = dict(m_id=i, window_types=c.get('window_types'), supported_body_width=supported,
                    budget_px=budget, before_px=old_width['max_width_px'], after_px=new_width['max_width_px'])
        if budget is not None and new_width['max_width_px'] > budget:
            width_issues.append(item | dict(new_overflow=old_width['max_width_px'] <= budget,
                                           current=current[i], proposed=proposed))
        try:
            if decode(encode(proposed)) != proposed:
                errors.append(dict(m_id=i, error='encoding roundtrip'))
        except UnicodeError as e:
            errors.append(dict(m_id=i, error=str(e)))
        if tokens.findall(current[i]) != tokens.findall(proposed):
            errors.append(dict(m_id=i, error='protected control/placeholder mismatch'))
        checks.append(item)
    records = []
    for i, proposed in sorted(candidate.items()):
        records.append(dict(stable_id=f'NightRemaster.ain::m[{i}]', m_id=i, current=current[i], proposed=proposed,
                            source_neighborhood=[dict(m_id=j, source=t.get(j, {}).get('source'))
                                                 for j in range(max(0, i-1), min(len(current), i+2))],
                            external_sources=f.get(i, {}).get('sources', []),
                            translator_model='mixed: externally supplied Claude proposals; Codex internal name override' if i in f and i in brand_ids
                                else ('Codex internal' if i in brand_ids else 'external Claude proposal; exact model ID unrecorded'),
                            codex_name_policy_override=i in brand_ids,
                            semantic_review_status='name override reviewed; other external prose pending' if i in brand_ids and i in f
                                else ('name override reviewed' if i in brand_ids else 'external proposal pending Codex semantic review')))
    preserved = dict(title='まるちっぽ☆ウニーク', korean='마루칫포☆우니크', character='우니크',
                     reason='확인 가능한 실존 대응 작품을 찾지 못함. 임의로 다른 작품/캐릭터로 치환하지 않음.',
                     other_unconfirmed=['TV 오츠나', '밋치·고유키(96372): 가수 별칭의 정확한 실존 대응 인물은 미확정'])
    old_names = [old for old, _, _, _, _ in GROUPS if old not in ('제미', '써니', '드림캐스')]
    residual = [dict(m_id=i, text=candidate.get(i, e['target'])) for i, e in t.items()
                if any(old in candidate.get(i, e['target']) for old in old_names)
                or re.search(r'드림캐스(?!트)|푸소|시든 팬더|워~ 무~', candidate.get(i, e['target']))]
    assert not residual, ('Known parody target residue', residual)
    summary = dict(status='HANDOFF_AUDITED_NAME_POLICY_REBASED_NOT_INSTALLED',
                   checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   runtime=str(rt), runtime_manifest=pointer['manifest'], inputs_sha256=inputs,
                   runtime_files_exact=len(live_checks), actual_msg1_count=len(current), map_entries_exact=len(t),
                   external_proposals_exact_current=len(f), external_review_scope_packets=202, external_review_scope_lines=28805,
                   external_review_scope_is_whole_game=False,
                   name_replacement_occurrences=len(decisions), name_policy_ids=len(brand_ids),
                   net_name_changes_vs_live=sum(candidate.get(i, current[i]) != current[i] for i in brand_ids),
                   external_policy_reversions_to_current=noop_ids, combined_candidate_rows=len(records),
                   unsupported_width_ids=[x['m_id'] for x in checks if not x['supported_body_width']],
                   width_overflow_rows=len(width_issues), new_width_overflow_rows=sum(x['new_overflow'] for x in width_issues),
                   encoding_or_token_errors=errors, preserved_unidentified_parody=preserved,
                   known_name_residuals=residual,
                   independent_review=dict(reviewer='baseline_evidence_review', read_only=True,
                       findings_addressed=['Morning Musume parody six display IDs included',
                                           'Tarepanda appearance joke adapted with explicit provenance'],
                       scope='stable-ID names, reflow context, provenance and reporting; not entire external semantic review'),
                   external_merge_tool_findings=[
                       'merge_final.py fixed 09-22 map/read_base check does not validate actual live AIN; independent exact baseline gate passed here.',
                       'merge_final.py follow-up check errors may still exit 0; not used as a release gate.'],
                   installed=False, whole_semantic_review=False, native_tested=False,
                   remaining=['외부 교정문 의미/호칭 검토', '폭 초과 페이지 단위 줄바꿈', '검증된 후보 빌드/설치 및 실제 화면 확인'])
    # No live mutation anywhere in this script. Recheck input hashes before publishing review files.
    assert all(sha(p) == v for p, v in inputs.items()), 'Inputs changed during review'
    OUT.mkdir(parents=True, exist_ok=True)
    writejl('brand_name_overrides.jsonl', decisions)
    writejl('combined_candidate.jsonl', records)
    writej('width_issues.json', width_issues)
    writej('width_checks.json', checks)
    writej('live_hash_checks.json', live_checks)
    writej('review_summary.json', summary)
    group_rows = ''.join('<tr><td>'+html.escape(old)+'</td><td>'+html.escape(new)+'</td><td>'+
                         ', '.join(map(str, ids))+'</td></tr>' for old, new, ids, _, _ in GROUPS)
    page = '''<!doctype html><html lang="ko"><meta charset="utf-8"><title>실명 표기 및 인계 검토</title>
<style>body{font:16px/1.65 "Malgun Gothic",sans-serif;background:#111a2c;color:#e8ecf4;max-width:1100px;margin:40px auto;padding:0 24px}h1{color:#83ceff}table{border-collapse:collapse;width:100%;background:#18243b}td,th{border:1px solid #3b4d69;padding:10px;text-align:left}.status{padding:18px;background:#263d54}code{color:#ffda89}</style>
<h1>패러디 실명 표기 · 클로드 교정 인계</h1><p class="status">검토용 후보입니다. 게임에는 아직 설치하지 않았습니다.</p>'''
    page += f'<p>회사·상품·작품·캐릭터까지 실명 표기로 통일. {len(brand_ids)}개 ID 검토, 현재 게임과 달라지는 이름 행 {summary["net_name_changes_vs_live"]}개. 피카츄 흉내 8행도 맞췄습니다.</p>'
    page += '<table><tr><th>패러디 표기</th><th>실명 표기</th><th>MSG1 ID</th></tr>'+group_rows+'</table>'
    page += '<p>마루칫포☆우니크/우니크는 실존 대응 대상을 확인하지 못해 유지합니다. 패러디의 대응 관계는 원문·장면에 근거한 추정이며, 공식 출처 링크는 이름 확인용입니다.</p>'
    page += '<p>TV 오츠나·밋치·고유키도 정확한 대응 대상을 확인하지 못해 유지합니다. 모무스 이름 늘여 말하기와 타레판다 외형 대사는 새 명칭에 맞췄습니다. 타레판다의 “바짝 마른”→“축 처진”은 실명 전환에 따른 각색으로 별도 기록했습니다. 그룹의 권법 등 작품 속 허구적 설정은 바꾸지 않았습니다.</p>'
    page += f'<h2>기술 검토</h2><ul><li>실행본 {len(live_checks)}개 파일과 설치 지도 {len(t):,}행 일치.</li><li>외부 교정 1,774행 모두 최신 MSG1 기준과 일치.</li><li>정책 재조정 후 {len(records):,}행 후보.</li><li>새 폭 초과 {summary["new_width_overflow_rows"]}행 / 전체 폭 초과 {len(width_issues)}행.</li><li>인코딩·제어 토큰 오류 {len(errors)}건.</li></ul>'
    page += '<p>외부 검수 범위는 202패킷·28,805행입니다. 전체 게임 의미 검수가 끝났다는 뜻은 아닙니다. 외부 교정문 의미 검토, 넘치는 페이지 재배치, 빌드·설치·실기 확인은 남아 있습니다.</p></html>'
    (OUT/'index.html').write_text(page, encoding='utf-8')
    report = f'''# 클로드 교정 인계 및 실명 표기 검토 — 2026-09-23

## 결과
- 현재 실행본 {len(live_checks)}개 파일이 최신 자동 이동 설치 manifest와 정확히 일치합니다. 기존 모드/번역 실행본을 변경하지 않았습니다.
- 설치 번역 지도 {len(t):,}행과 실제 AIN MSG1을 대조했습니다. 외부 교정 1,774행의 current도 전부 일치합니다.
- 사용자 확답에 따라 회사·상품·작품·캐릭터 및 식별 가능한 그룹 패러디를 실제 이름으로 바꾸는 정책을 반영했습니다.
- 이름 및 연동 대사 {len(brand_ids)}개 ID, {len(decisions)}개 수정 기록. 현재 실행본과 다른 행 {summary['net_name_changes_vs_live']}개. 외부 교정이 실제 이름을 패러디로 되돌리던 {len(noop_ids)}행은 현행 유지로 되돌렸습니다.
- 합친 후보는 {len(records):,}행입니다. `combined_candidate.jsonl`은 검토용이며 **설치본/최종 승인본이 아닙니다**.

## 검증과 남은 작업
- 실제 설치 FNL, 크기60·간격-2·테두리2 기준 계산: Face 668px / Text·All 884px. 모든 후보가 이 검사의 지원 범위에 들어옵니다.
- 새 폭 초과 {len(width_issues)}행. 상세 ID/폭은 `width_issues.json`; 이름 변경 행과의 교집합은 {len([x for x in width_issues if x['m_id'] in brand_ids])}행입니다.
- 인코딩 왕복 및 검사 대상 제어/포맷 토큰 오류 {len(errors)}건. 알려진 패러디 한국어 표기의 잔여 검색 0건입니다.
- 외부 검수는 202패킷·28,805행 범위입니다. 게임 전체 의미 검수도, 본 후보의 Codex 전체 의미 승인도 아닙니다.
- 다음 단계: 외부 교정 의미/호칭 검토 → 91개 넘치는 행을 원래 페이지 필드 수 내에서 재배치 → 별도 후보 빌드/정적 차이 검사 → 설치와 실제 화면 확인.

## 예외와 출처
- 마루칫포☆우니크/우니크, TV 오츠나, 밋치·고유키는 정확한 실존 대응이 확인되지 않아 임의로 변경하지 않았습니다.
- 타레판다 외형 대사 95477은 실명 전환에 따른 각색임을 기록했습니다. 허구적인 그룹 설정 자체는 보존합니다.
- 외부 교정은 사용자 제공 Claude/Fable·Opus 계열 자료이며 정확한 모델 ID가 없어 추정하지 않았습니다. Codex 내부 모델이 작성한 명칭 및 연동 대사만 `translator_model: Codex internal`로 구분했습니다.
- 실존 대응은 원문/인접 장면에 근거한 추정입니다. `brand_name_overrides.jsonl`의 공식 링크는 실명 철자·해당 상품/작품의 존재를 확인하는 근거이지 게임 제작사가 패러디를 공인한 근거는 아닙니다.
- 독립 읽기 전용 검토의 누락 지적(모닝구무스메)과 연동 대사 지적(타레판다)을 반영했습니다.

## 기존 병합 도구의 검증 허점
1. `merge_final.py`는 고정된 09-22 지도와 review_base만 비교하여 실제 최신 AIN 변경을 검출하지 못합니다. 이번에는 실제 런타임 해시와 MSG1 전체를 별도로 대조했습니다.
2. 후속 점검 실패 후에도 종료 코드0일 수 있으므로 성공 종료만을 배포 허가로 삼지 않았습니다.

원본 외부 교정 파일, 실행본, 세이브, 복구 빌드는 수정하지 않았습니다. 입력 해시는 `review_summary.json`, 실행본 대조는 `live_hash_checks.json`에 있습니다.
'''
    (OUT/'README.md').write_text(report, encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs_sha256','external_merge_tool_findings')}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
