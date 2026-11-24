"""Run actual candidate JAM expiry/fade/refresh against real PACT keys."""
from build_notice_duration_20260917 import R,O,OLD
from publish_remaster_multiplier_20260915 import read,sha,put,js
from build_remaster_multiplier_20260915 import ex,allparts,val,txt_info
from build_mod_tab_20260915 import name,scalar
import verify_chest_flow_20260917 as cv

class VM(cv.VM):
    def __init__(self):
        super().__init__();self.loot=True;self.parts={}
        doc=ex.decode_ex(R/'staging/notice_depth_20260917/pact_160.pactex')
        for i,p in enumerate(allparts(doc.blocks[2].payload.children[0])):
            n=name(p)
            if not n.startswith(('KR_Chest','KR_Receipt','KR_LootNotice')):continue
            try:t=val(txt_info(p),'テキスト').value.decode('cp932')
            except (StopIteration,AttributeError):t=''
            self.parts[n]=cv.Node({0:[('part',j) for j in range(32)],'id':100+i,'text':t,'show':bool(scalar(val(p,'表示'))),'alpha':scalar(val(p,'アルファ'))})
        self.byid={p['id']:p for p in self.parts.values()}
    def run(self,n,args=()):
        if n=='KR_GetLoot':return int(self.loot)
        return super().run(n,args)

def main():
    cv.O=O;count=0
    for prefix,root,duration in [('Chest','KR_ChestNotice',2000),('Notice','KR_LootNoticeRoot',3000)]:
        for elapsed in [0,1,duration-501,duration-500,duration-250,duration-1,duration,duration+1]:
            v=VM();v.run(f'KR_{prefix}Show',['A']);v.clock+=elapsed;v.run(f'KR_{prefix}Tick',[16,80]);v.check()
            assert bool(v.parts[root]['show'])==(elapsed<duration)
            if elapsed<duration:
                alpha=255 if elapsed<=duration-500 else (duration-elapsed)*255//500
                assert v.parts[root]['alpha']==alpha
            else:assert not v.handlers
            count+=1
        v=VM();v.run(f'KR_{prefix}Show',['A']);v.clock+=duration-100;v.run(f'KR_{prefix}Tick',[16,80])
        v.run(f'KR_{prefix}Show',['B']);assert v.parts[root]['alpha']==255
        v.clock+=duration-1;v.run(f'KR_{prefix}Tick',[16,80]);assert v.parts[root]['show']
        v.clock+=1;v.run(f'KR_{prefix}Tick',[16,80]);assert not v.parts[root]['show'];v.check();count+=1
        for invalid in [-1,-2147483640]:
            v=VM();v.run(f'KR_{prefix}Show',['A']);v.clock=invalid;v.run(f'KR_{prefix}Tick',[16,80]);assert not v.handlers;v.check();count+=1
    # Back-to-back chest records roll off according to the NEW, not old lifetime.
    for gap,lines in [(1999,['','A','B']),(2000,['','','B']),(2499,['','','B'])]:
        v=VM();v.run('KR_ChestShow',['A']);v.clock+=gap;v.run('KR_ChestShow',['B']);assert v.lines()==lines;v.check();count+=1
    for a,b in [('Chest','Notice'),('Notice','Chest')]:
        v=VM();v.run(f'KR_{a}Show',['A']);v.run(f'KR_{b}Show',['B']);v.check();assert len(v.handlers)==1;count+=1
    ev=read(O/'build_evidence.json');assert all(sha(O/n)==h for n,h in ev['files'].items())
    r=dict(status='NOTICE_DURATION_STATIC_PASS',files=ev['files'],compiled_cases=count,durations_ms=ev['durations_ms'],
        six_operand_reverse_exact=True,refresh_and_fade_verified=True,no_save_schema_or_payout_changes=True,native_verified=False)
    put(O/'verification.json',js(r));print(js(r).decode('utf8'))

if __name__=='__main__':main()
