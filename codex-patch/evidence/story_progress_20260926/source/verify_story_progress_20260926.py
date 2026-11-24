"""Reuse complete save-frame/row gates, adding story/data/display invariants."""
from pathlib import Path
import json,re
import build_story_progress_20260926 as e
def main():
    # Unchanged assets and the current pair of independently resumed scene types.
    code=(e.HERE/'verify_save_slots_20260925.py').read_text('utf8')
    code=code.replace('import build_save_slots_20260925 as e','import build_story_progress_20260926 as e')
    code=code.replace('assert changed==[168]','assert changed==[]')
    code=code.replace("{'NightR36.asd','NightR49.asd'}","{'NightR36.asd','NightR38.asd'}")
    code=code.replace("if __name__=='__main__':main()",'')
    scope={'__name__':'story_save_base_checks'};exec(compile(code,'verified_save_checks','exec'),scope);scope['main']()
    report=e.a.readj(e.O/'verification.json')
    for save,path in report['native_probes'].items():
        r=e.a.readj(Path(path));log=r['A']['log']
        assert 'PASS story checkpoint aliases, side-event separation, home click rows' in log
        snapshot=next(t.split('SNAPSHOT=',1)[1] for t in log if 'SNAPSHOT=' in t).split(',')
        assert len(snapshot)==30 and snapshot[21]=='KR_SAVE2' and snapshot[28]=='KR_MAIN1' and 0<=int(snapshot[29])<=13
        stage=next(t for t in log if t.startswith('STORY='));assert stage.startswith('STORY='+snapshot[29]+' ')
        if save=='NightR36.asd':
            assert int(snapshot[29])==7 and snapshot[26:28]==['147','1043']
            for name in ['story_info.png','story_detail.png']:assert (Path(path).parent/name).is_file()
        if save=='NightR38.asd':assert (Path(path).parent/'story_home.png').is_file()
    helpers=(e.O/'helpers_readable.jaf').read_text('utf8')
    stage=helpers.split('string KR_StoryLabel',1)[0]
    assert 'Calendar' not in stage and 'KR_PlayerEventCount' not in stage and 'LEventFlag::GetTotal' not in stage
    assert 'RegisterEvent' not in stage and 'Set(' not in stage
    assert 'fields[29]' in helpers and 'fields.Numof()>=30' in helpers and 'fields[28]=="KR_MAIN1"' in helpers
    assert 'fields[26].ToInt()' in helpers and '미기록 (재저장 필요)' in helpers
    # Geometry proof for the saved metadata, longest labels, and expanded header.
    from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
    from audit_dynamic_ui_20260915 import ENC
    rt=Path(e.a.readj(e.S/'current.json')['runtime']);_,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',3)
    measures=[]
    tests=[(16,220,['본편: '+v for v in e.LABELS.values()]+['본편: 미기록 (재저장 필요)']),
           (14,220,['전체 달성률 100.0% (이벤트)','전체 달성률 -- / 재저장 필요']),
           (20,696,['12월 31일 · 호무라 라이코 동굴 최심층⑩ · 남은 시간 9999'])]
    for size,limit,texts in tests:
        face,den,_=select_fnl_face(faces,size);w=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()},0,0,0)
        for text in texts:
            width=w.measure(text,True)['lines'][0]['width_px'];assert width<=limit,(text,width,limit)
            measures.append(dict(size=size,width=width,limit=limit,text=text))
    report.update(status='STORY_PROGRESS_STATIC_NATIVE_PASS',checkpoint_aliases=sum(len(x[2]) for x in e.STAGES),story_source='Current-save event registry; highest checkpoint, no estimated percentage',separate_event_collection='Current-save entered events / 1043 across all branches',geometry=measures,legacy_metadata='Missing main checkpoint is explicit; new save captures it',changed_PACT=[])
    e.save('verification.json',report);print('STORY PROGRESS PASS',flush=True)
if __name__=='__main__':main()
