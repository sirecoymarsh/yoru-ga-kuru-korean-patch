"""Claude Opus 5.5 (2026-09-24) r6: the r3 and r5 VM checks against the r6 candidate, then the sweep carry-limit list:
- KR_T8SweepChest records only while a sweep runs; a consumable followed by 「하지만 더는 소지할 수 없다」 is lost,
  an element stone counts as an attempt; KR_SweepPay resets the records;
- the fixed KR_SweepItems line becomes the lost list (stones: attempts minus the report's gains) or 「…빠진 보상 없음」,
  coloured; the records are cleared after the report;
- relocated L_TreasureBox::ShowGetDialog / KR_SweepPay = original + exactly the prepended call.
"""
from pathlib import Path
import collections,json,re,sys
import build_claude_term_rate_20260924_r6 as e
import verify_claude_term_rate_20260924_r5 as V5
V5.e=e;V5.O=e.O;V5.v3.e=e;V5.v3.O=e.O
b=e.b;a=e.a;O=e.O
proxy=V5.proxy;ko=V5.ko;T=V5.T
ORANGE=V5.ORANGE;GRAY=V5.GRAY;CYAN=V5.CYAN;GOLD=V5.GOLD
STONES=['적색','청색','백색','흑색']

class VM6(V5.VM5):
    def __init__(self):
        super().__init__();self.sweep=False
    def native(self,name,aa):
        if name=='KR_SweepActive':return int(self.sweep)
        if name=='KR_SweepItemName':
            domain,index=aa;assert domain==2 and 0<=index<40,aa
            return proxy(f'{STONES[index//10]} 요소석({index%10+1}등급)')
        return super().native(name,aa)

def main():
    V5.main()
    ev=a.readj(O/'build_evidence.json');counts=collections.Counter();v=VM6()
    call=lambda n,*args:v.run(n,[proxy(x) if isinstance(x,str) else x for x in args])
    by={f['name']:f['index'] for f in b.read_meta(O/'candidate_meta.json')['functions']}
    for fid,code in [(27194,'\t.LOCALREF txt\n\tA_REF\n\tCALLFUNC KR_T8SweepChest\n'),(by['KR_SweepPay'],'\tCALLFUNC KR_T8SweepLostReset\n')]:
        orig=V5.norm((O/f'original_{fid}.jam').read_text('utf8'));built=V5.norm((O/f'built_{fid}.jam').read_text('utf8'));ins=V5.norm(code)
        assert built[0]==orig[0] and built[1:1+len(ins)]==ins and built[1+len(ins):]==orig[1:],(fid,built[:6])
        counts['relocated_body_is_original_plus_prefix']+=1
    get=lambda k:ko(v.cache.get(k,''))
    item='회복 아이템「회복약」{YORU_KR_JOSA:O} 손에 넣었다';full='하지만 더는 소지할 수 없다'
    # 1. nothing is recorded outside a sweep
    v.cache={};v.sweep=False
    for t in [item,full,'요소석「빨강」(레벨 3)을 손에 넣었다']:call('KR_T8SweepChest',t)
    assert get('YoruKR.T8.SweepLost')=='' and get('YoruKR.T8.SweepStone')=='';counts['no_record_outside_sweep']+=1
    # 2. a sweep: two capped consumables, one kept, stones as attempts
    v.sweep=True;v.run('KR_T8SweepLostReset')
    for t in [item,full,item,full,'회복 아이템「해독제」{YORU_KR_JOSA:O} 손에 넣었다','꽝','요소석「빨강」(레벨 3)을 손에 넣었다','요소석「빨강」(레벨 3)을 손에 넣었다',
              '요소석「빨강」(레벨 3)을 손에 넣었다','요소석「어둠」(레벨 10)을 손에 넣었다','달조각을 12개 손에 넣었다','요소석「파랑」(레벨 1)을 손에 넣었다']:
        call('KR_T8SweepChest',t)
    assert get('YoruKR.T8.SweepLost')=='회복약\n회복약\n',get('YoruKR.T8.SweepLost')
    assert get('YoruKR.T8.SweepStone')=='적색 요소석(3등급)\n'*3+'흑색 요소석(10등급)\n청색 요소석(1등급)\n',get('YoruKR.T8.SweepStone');counts['sweep_records']+=1
    report=('이즈미  Lv 12 → 13  경험치 +1234 / 훈련치 +56\n\n달조각 +12\n해독제 +1\n적색 요소석(3등급) +1\n청색 요소석(1등급) +1\n'
            '소지 한도를 넘은 보상은 제외됩니다.\n잠시 후 다음 날로 진행합니다.')
    out=ko(v.run('KR_T8SweepColor',[proxy(report)]))
    red='r=255 g=120 b=120';blue='r=120 g=176 b=255'
    want=('이즈미  Lv '+T('12',CYAN)+' → '+T('13',CYAN)+'  경험치 '+T('+1234',CYAN)+' / 훈련치 '+T('+56',CYAN)+'\n\n'
          +T('달조각',GOLD)+' '+T('+12',CYAN)+'\n'+T('해독제',GOLD)+' '+T('+1',CYAN)+'\n'+T('적색 요소석(3등급)',red)+' '+T('+1',CYAN)+'\n'
          +T('청색 요소석(1등급)',blue)+' '+T('+1',CYAN)+'\n'+T('소지 한도로 받지 못한 보상',ORANGE)+'\n'+T('· 회복약 ×2',ORANGE)+'\n'
          +T('· 적색 요소석(3등급) ×2',ORANGE)+'\n'+T('· 흑색 요소석(10등급) ×1',ORANGE)+'\n'+T('잠시 후 다음 날로 진행합니다.',GRAY))
    assert out==want,(out,want);counts['lost_list_in_report']+=1
    assert get('YoruKR.T8.SweepLost')=='' and get('YoruKR.T8.SweepStone')=='' and get('YoruKR.T8.SweepChest')=='';counts['records_cleared_after_report']+=1
    # 3. nothing lost -> the gray line; a cancel report (no fixed line) is only coloured
    out=ko(v.run('KR_T8SweepColor',[proxy('달조각 +3\n소지 한도를 넘은 보상은 제외됩니다.\n잠시 후 다음 날로 진행합니다.')]))
    assert out==T('달조각',GOLD)+' '+T('+3',CYAN)+'\n'+T('소지 한도로 빠진 보상 없음',GRAY)+'\n'+T('잠시 후 다음 날로 진행합니다.',GRAY),out;counts['nothing_lost_line']+=1
    v.cache['YoruKR.T8.SweepLost']=proxy('회복약\n')
    out=ko(v.run('KR_T8SweepColor',[proxy('소탕을 중단했습니다.\n보상과 탐색 시간은 변경되지 않았습니다.')]))
    assert out==T('소탕을 중단했습니다.',ORANGE)+'\n'+T('보상과 탐색 시간은 변경되지 않았습니다.',GRAY) and get('YoruKR.T8.SweepLost')=='회복약\n',out;counts['cancel_report_untouched']+=1
    v.run('KR_T8SweepLostReset');assert get('YoruKR.T8.SweepLost')=='';counts['reset']+=1
    # 4. the stone gain is read only from a line start (a longer rank must not match a shorter one)
    assert v.run('KR_T8Gained',[proxy('적색 요소석(10등급) +4\n적색 요소석(1등급) +2\n'),proxy('적색 요소석(1등급)')])==2
    assert v.run('KR_T8Gained',[proxy('x적색 요소석(1등급) +9\n'),proxy('적색 요소석(1등급)')])==0;counts['gain_parse']+=1
    # 5. glyphs of the new lines
    from audit_message_pixel_widths import parse_fnl_font,sjis_bytes_to_fnl_index
    alphabet={x['unicode_character'] for x in a.readj(a.PROXY)['mapping']};carriers={x['proxy_character'] for x in a.readj(a.PROXY)['mapping']}
    visible=re.sub(r'\$\{[^}]*\}','',want+'소지 한도로 빠진 보상 없음')
    other=sorted({c for c in visible if c not in alphabet and c not in ' \n'})
    for c in other:assert c not in carriers,c
    for font in range(4):
        _,fl=parse_fnl_font(Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl',font)
        for c in other:
            idx=sjis_bytes_to_fnl_index(c.encode('cp932'));assert all(idx<len(f.widths) and f.widths[idx]>0 for f in fl),(font,c)
    counts['r6_non_proxy_glyphs']=len(other)
    res=a.readj(O/'vm_verification.json');res['r6']=dict(counts=dict(counts),report_example=want)
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r6=counts),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
