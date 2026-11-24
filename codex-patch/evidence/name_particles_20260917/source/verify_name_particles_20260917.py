"""Execute final helper JAM; verify independently specified linguistic cases."""
import collections,json,re,sys
from pathlib import Path
from audit_name_particles_20260917 import O,read_meta,t,decode
from audit_dynamic_ui_20260915 import encode,ex
from build_name_particles_20260917 import FORMATS,HOOKS,MARKER
from verify_saved_name_refresh_20260915 import tables
sys.stdout.reconfigure(encoding='utf-8')
def proxy(s):return encode(s).decode('cp932')
def korean(s):return decode(s.encode('cp932'))
class VM:
    def __init__(self):
        self.meta=read_meta(O/'candidate_meta.json');self.fs={f['name']:f for f in self.meta['functions'] if f['name'].startswith('KR_')};self.code={};self.calls=0;self.steps=0
    def run(self,name,args=()):
        self.calls+=1;f=self.fs[name];fid=f['index'];vs=f['arguments']+f['variables'];li={x['name']:i for i,x in enumerate(vs)};loc={i:'' if v['type'][0]==12 else 0 for i,v in enumerate(vs)};loc.update(enumerate(args));st=[]
        if fid not in self.code:
            ops=[];labels={}
            for line in (O/f'built_{fid}.jam').read_text(encoding='utf-8').splitlines():
                l=line.strip()
                if not l or l.startswith((';','FUNC ','ENDFUNC ','EOF ')):continue
                if l.endswith(':'):labels[l[:-1]]=len(ops)
                else:ops.append(l.split(maxsplit=1))
            self.code[fid]=ops,labels
        ops,labels=self.code[fid];pc=0;steps=0
        while pc<len(ops):
            steps+=1;self.steps+=1;assert steps<100000,(name,pc)
            op,*rest=ops[pc];arg=rest[0] if rest else '';pc+=1
            if op=='PUSH':st.append(int(arg,0))
            elif op=='S_PUSH':st.append(json.loads(arg))
            elif op=='.S_LOCALASSIGN':var,v=arg.split(' ',1);loc[li[var]]=json.loads(v)
            elif op=='.LOCALASSIGN':var,v=arg.rsplit(' ',1);loc[li[var]]=int(v,0)
            elif op=='.LOCALREF':st.append(loc[li[arg]])
            elif op=='.LOCALDEC2':loc[li[arg]]-=1
            elif op=='PUSHLOCALPAGE':st.append(loc)
            elif op=='A_REF':assert isinstance(st[-1],str)
            elif op in ['S_ASSIGN','X_ASSIGN']:
                if op=='X_ASSIGN':assert arg=='1'
                v=st.pop();i=st.pop();p=st.pop();p[i]=v;st.append(v)
            elif op in ['DELETE','POP']:st.pop()
            elif op in ['ADD','SUB','S_ADD','LT','LTE','GT','GTE','EQUALE','NOTE','S_EQUALE','S_NOTE']:
                b=st.pop();a=st.pop()
                if op in ['ADD','S_ADD']:v=a+b
                elif op=='SUB':v=a-b
                elif op=='LT':v=int(a<b)
                elif op=='LTE':v=int(a<=b)
                elif op=='GT':v=int(a>b)
                elif op=='GTE':v=int(a>=b)
                elif op in ['EQUALE','S_EQUALE']:v=int(a==b)
                else:v=int(a!=b)
                st.append(v)
            elif op in ['IFZ','IFNZ']:
                if bool(st.pop())==(op=='IFNZ'):pc=labels[arg]
            elif op=='JUMP':pc=labels[arg]
            elif op=='CALLFUNC':
                ff=self.fs[arg];n=len(ff['arguments']);aa=st[-n:];del st[-n:];st.append(self.run(arg,aa))
            elif op=='CALLHLL':
                lib,method,argc=arg.split();assert lib=='String' and argc=='0'
                if method=='Length':st.append(len(st.pop()))
                elif method=='Find':key=st.pop();text=st.pop();st.append(text.find(key))
                elif method=='StartsWith':key=st.pop();text=st.pop();st.append(int(text.startswith(key)))
                elif method=='GetPart':index=st.pop();text=st.pop();assert index>=0;st.append(text[index:])
                elif method=='GetPart#1':count=st.pop();index=st.pop();text=st.pop();assert count>=0 and index>=0;st.append(text[index:index+count])
                elif method=='Replace':new=st.pop();old=st.pop();text=st.pop();st.append(text.replace(old,new))
                else:raise AssertionError((name,method))
            elif op=='RETURN':assert len(st)==1,(name,st);return st.pop()
            else:raise AssertionError((name,op,arg))
        raise AssertionError('No return')
def main():
    ev=t.readj(O/'build_evidence.json');assert t.sha((O/'output/NightRemaster.ain').read_bytes())==ev['ain_sha256'];v=VM();count=collections.Counter();examples=[]
    def call(name,*args):return v.run(name,[proxy(x) if isinstance(x,str) else x for x in args])
    def resolve(s):return korean(call('KR_ResolveJosa',s))
    def replace(s,n,key='료　　　　'):return korean(call('KR_ReplacePlayerJosa',s,key,n))
    for row in t.readj(t.INPUT/'proxy.json')['mapping']:
        c=row['unicode_character']
        if not '\uac00'<=c<='\ud7a3':continue
        final=(ord(c)-0xac00)%28;want=0 if final==0 else 2 if final==8 else 1
        assert call('KR_JosaClass',c)==want,c;count['all_shipped_hangul_classes']+=1
        for kind,pair in [('n',('는','은')),('g',('가','이')),('o',('를','을')),('w',('와','과')),('r',('로','으로'))]:
            expected=pair[int(want!=0 and (kind!='r' or want!=2))]
            assert korean(call('KR_JosaSelect',c,kind,'?'))==expected,(c,kind);count['all_hangul_five_particle_pairs']+=1
    golden=[('민수{KJ:n} 빛구슬{KJ:q} 검{KJ:r} 공격','민수는 빛구슬을 검으로 공격'),('민준{KJ:g} 아카나메{KJ:q} 구슬{KJ:r} 공격','민준이 아카나메를 구슬로 공격'),('하늘{KJ:w} 민수{KJ:g} 도망쳤다','하늘과 민수가 도망쳤다'),('회복 아이템「약」{KJ:O} 손에 넣었다','회복 아이템「약」을 손에 넣었다'),('장비 아이템「망치」{KJ:O} 손에 넣었다','장비 아이템「망치」를 손에 넣었다'),('Alex{KJ:n} 회피했다','Alex는 회피했다'),('8{KJ:r} 이동','8로 이동'),('6{KJ:r} 이동','6으로 이동'),('abc{KJ:x}!', 'abc{KJ:x}!'),('abc{KJ:', 'abc{KJ:'),('', ''),('일반 문장: 이름과 무관하다.','일반 문장: 이름과 무관하다.')]
    golden=[(s.replace('{KJ:',MARKER),w.replace('{KJ:',MARKER)) for s,w in golden]
    golden+=[('{KJ:n}', '{KJ:n}'),('{KJ:n}'+MARKER+'g}', '{KJ:n}가')]
    for src,want in golden:
        actual=resolve(src);assert actual==want,(src,actual,want);assert resolve(actual)==actual;count['golden_and_idempotence']+=1;examples.append(dict(input=src,output=actual))
    player=[('료　　　　는 친구다.','민수','민수는 친구다.'),('료　　　　는 친구다.','민준','민준은 친구다.'),('료　　　　와 함께.','하늘','하늘과 함께.'),('료　　　　로 불러.','민준','민준으로 불러.'),('료　　　　로 불러.','하늘','하늘로 불러.'),('료　　　　다.','민준','민준이다.'),('료　　　　라고 했다.','민준','민준이라고 했다.'),('료　　　　잖아!','민준','민준이잖아!'),('료　　　　냐……','민준','민준이냐……'),('【료　　　　】','민준','【민준】'),('료　　　　군은 여기에.','민수','민수군은 여기에.'),('료　　　　선배는 여기에.','민준','민준선배는 여기에.'),('료　　　　는 료　　　　와 다르다.','민준','민준은 민준과 다르다.'),('료　　　　라고 했다.','료　　　　','료　　　　이라고 했다.'),('료　　　　는 친구다.','Alex','Alex는 친구다.'),('무료 자료','민준','무료 자료'),('료　　　　다음에','민준','민준다음에'),('료　　　　야!','민준','민준야!')]
    # A custom name equal to the sentinel is emitted once, never recursively replaced.
    player=[(s,n,'료　　　　라고 했다.' if n=='료　　　　' else want) for s,n,want in player]
    # Both live name+야 sites were checked against JP だよ: these are copulas.
    player=[(s,n,'민준이야!' if s=='료　　　　야!' else want) for s,n,want in player]
    for src,name,want in player:
        actual=replace(src,name);assert actual==want,(src,name,actual,want);count['player_sentinel_and_suffix_cases']+=1
    assert replace('키는 이름이다.','값','키')=='값는 이름이다.';count['non_player_replacement_unchanged']+=1
    tab,mon=tables(ex.decode_ex(O/'source.ex'));monster_names=[decode(vals[2]) if isinstance(vals[2],bytes) else vals[2] for vals in mon.values() if len(vals)>2]
    for name in monster_names:
        cls=call('KR_JosaClass',name)
        for kind in ['n','g','q','w','r']:
            result=resolve(name+MARKER+kind+'}')
            assert MARKER not in result and result.startswith(name),(name,result)
            count['actual_monster_name_pairs']+=1
    # Frozen production formats retain placeholder count/order; realistic all three actor roles.
    for sid,fmt in FORMATS.items():
        n=fmt.count('%s')
        for name in ['민수','민준','하늘','빛구슬','아카나메']:
            formatted=fmt%tuple([name]*n);actual=resolve(formatted);assert MARKER not in actual;count['production_format_examples']+=1
    # Every current player-name occurrence can pass through without changing its field identity.
    raw=t.raw_messages((O/'source.ain').read_bytes())[3]
    for b in raw:
        s=decode(b)
        if '료　　　　' not in s:continue
        for name in ['료','민준','하늘']:
            actual=replace(s,name);assert '료　　　　' not in actual and MARKER not in actual;count['current_MSG_name_substitutions']+=1
    # Reconstruct each old hook from exact stored edits; no silent body changes.
    edits=t.readj(O/'reversible_hook_edits.json');assert {x['fid'] for x in edits}==set(HOOKS)
    for x in edits:
        if x['fid']==7184:
            restored=x['after'].replace('\tCALLFUNC KR_ReplacePlayerJosa\n','\tCALLHLL String Replace 0\n').replace('\t.LOCALREF baseText\n\tA_REF\n\tPUSHLOCALPAGE\n','\t.LOCALREF baseText\n\tPUSHLOCALPAGE\n')
        else:
            prefix='\tPUSHLOCALPAGE\n\tPUSH 0\n\t.LOCALREF txt\n\tA_REF\n\tCALLFUNC KR_ResolveJosa\n\tS_ASSIGN\n\tDELETE\n';assert x['after'].count(prefix)==1;restored=x['after'].replace(prefix,'',1)
        assert restored==x['before'];count['exact_hook_inverse']+=1
    report={'status':'COMPILED_JAM_AND_CORPUS_PASS','ain_sha256':ev['ain_sha256'],'counts':dict(count),'compiled_helper_calls':v.calls,'executed_JAM_steps':v.steps,'examples':examples,'native_verified':False,'original_save_file_modified':False,'limits':'String HLL behavior modeled in bounded VM; actual native rendering/load not yet observed. Unknown non-Hangul endings retain existing forms. Both current name+야 sites verified as copulas against Japanese.'}
    t.writej(O/'verification.json',report);print(json.dumps({k:z for k,z in report.items() if k!='examples'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
