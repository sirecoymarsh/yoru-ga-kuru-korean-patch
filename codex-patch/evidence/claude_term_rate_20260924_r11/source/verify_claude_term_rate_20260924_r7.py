"""Claude Opus 5.5 (2026-09-24) r7: the r3/r5/r6 VM checks against the r7 candidate, then
- Codex review CT-RATE-003: the home-rate toggle commits only after a verified write; a failed write keeps the
  previous state, is not retried every update, and is retried after the player changes the checkbox;
- the eight monster renames in the staged EX (only those name leaves changed, glyphs present).
"""
from pathlib import Path
import collections,json,re,sys
import build_claude_term_rate_20260924_r7 as e
import verify_claude_term_rate_20260924_r6 as V6
V5=V6.V5
for mod in (V6,V5):mod.e=e;mod.O=e.O
V5.v3.e=e;V5.v3.O=e.O
b=e.b;a=e.a;O=e.O
proxy=V5.proxy;ko=V5.ko

class VM7(V6.VM6):
    def __init__(self):
        super().__init__();self.corrupt=False;self.writes=0
    def hll(self,lib,method,st,ops,pc,loc,li):
        if lib=='TextFile' and method=='WriteAll':
            self.writes+=1
            if self.corrupt:
                text=st.pop();path=st.pop();self.files[path]='garbage';st.append(1);return
        return super().hll(lib,method,st,ops,pc,loc,li)

def main():
    V6.main()
    ev=a.readj(O/'build_evidence.json');counts=collections.Counter();v=VM7()
    dat='SaveData_Test\\YoruKR_HomeRate.dat';OFF='YoruKR.HomeRate.1\r\n0\r\n';ON='YoruKR.HomeRate.1\r\n1\r\n'
    on=lambda:v.run('KR_T8HomeRateGet')
    # 1. the review's reproduction: file off, the write fails -> state stays off, file stays off
    v.files={dat:OFF};v.cache={};v.fail={('write',dat)};v.writes=0
    v.run('KR_T8HomeRateSet',[1]);assert on()==0 and v.files[dat]==OFF and v.writes==1 and v.cache['YoruKR.HomeRate.Failed']=='1',v.cache
    for _ in range(5):v.run('KR_T8HomeRateSet',[1])
    assert v.writes==1,v.writes;counts['failed_write_keeps_state_no_retry_storm']+=1
    v.cache.pop('YoruKR.HomeRate');assert on()==0;counts['failed_write_off_after_cache_reset']+=1
    # 2. the checkbox goes back (getter sync) -> latch cleared; the next change is tried again and succeeds
    v.fail=set();v.run('KR_T8HomeRateSet',[0]);assert v.cache['YoruKR.HomeRate.Failed']=='' and v.writes==1
    v.run('KR_T8HomeRateSet',[1]);assert on()==1 and v.files[dat]==ON and v.writes==2;counts['retry_after_change_succeeds']+=1
    # 3. a write that reads back different content is a failure too
    v.corrupt=True;v.run('KR_T8HomeRateSet',[0]);assert on()==1 and v.cache['YoruKR.HomeRate.Failed']=='0';v.corrupt=False;counts['readback_mismatch_is_failure']+=1
    # 4. unchanged value: no write at all
    v.files={dat:ON};v.cache={};v.writes=0
    for _ in range(3):v.run('KR_T8HomeRateSet',[1])
    assert v.writes==0 and on()==1;counts['same_value_no_write']+=1
    v.files={};v.cache={};v.run('KR_T8HomeRateSet',[1]);assert on()==1 and v.files[dat]==ON;counts['plain_success']+=1
    # 5. monster renames: exactly the eight name leaves differ from the runtime EX
    rt=Path(ev['source_pointer']['runtime']);old=b.ex.decode_ex(rt/'NightRemasterEX.ex');new=b.ex.decode_ex(O/'NightRemasterEX.ex')
    diff={p:(b.decode(old.strings[p].value),b.decode(new.strings[p].value)) for p in old.strings if old.strings[p].value!=new.strings[p].value}
    want={tuple(x['path']):(x['before'],x['target']) for x in ev['monster_names']['edits']}
    assert diff==want and len(diff)==8,(diff,want);assert {p:n.raw for p,n in old.scalars.items()}=={p:n.raw for p,n in new.scalars.items()}
    counts['ex_only_eight_names_changed']+=1
    names={int(t.name.value.decode('cp932')):b.decode(new.strings[t.leaf_value.payload.items[2].value.payload.path].value) for t in new.blocks[7].payload.children}
    for mid,(jp,before,target,why) in e.MONSTER_RENAMES.items():assert names[mid]==target,(mid,names[mid])
    counts['renamed_monsters']=len(e.MONSTER_RENAMES)
    alphabet={x['unicode_character'] for x in a.readj(a.PROXY)['mapping']}
    assert all(c in alphabet or c==' ' for x in e.MONSTER_RENAMES.values() for c in x[2]);counts['monster_glyphs_in_proxy_map']+=1
    res=a.readj(O/'vm_verification.json');res['r7']=dict(counts=dict(counts),monster_names={str(k):v[2] for k,v in e.MONSTER_RENAMES.items()})
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r7=counts),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
