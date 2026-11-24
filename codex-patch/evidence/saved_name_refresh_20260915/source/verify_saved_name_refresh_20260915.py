"""Execute compiled getter disassembly against native EX table shapes and stale fields."""
from pathlib import Path
import copy,json,re,struct
from audit_dynamic_ui_20260915 import ex,decode,encode
from build_saved_name_refresh_20260915 import O,R,ROWS,read,sha,write
from audit_item_skill_names_20260915 import tree_values,val

def tables(doc):
    out={}
    for b in doc.blocks:
        name=b.name.value.decode('cp932');t=b.payload
        if isinstance(t,ex.TableNode):
            fields=[f.name.value.decode('cp932') for f in t.fields]
            rows=[{k:val(v) for k,v in zip(fields,r)} for r in t.rows]
            if rows and 'id' in rows[0]:out[name]={r['id']:r for r in rows}
    mons={t.name.value.decode('cp932'):tree_values(t) for t in doc.blocks[7].payload.children}
    return out,{'モンスターデータ.'+k:v for k,v in mons.items()}

class VM:
    def __init__(self,tab,lists):self.tab=tab;self.lists=lists;self.calls=[]
    def run(self,fid,fields):
        ops=[];labels={}
        for s in (O/f'built_{fid}.jam').read_text('utf8').splitlines():
            s=s.strip()
            if not s or s.startswith((';','FUNC ','ENDFUNC ')):continue
            if s.endswith(':'):labels[s[:-1]]=len(ops)
            else:ops.append(s.split(maxsplit=1))
        stack=[];pc=0;steps=0;seen=copy.deepcopy(fields)
        while pc<len(ops):
            steps+=1;assert steps<100;op,*rest=ops[pc];arg=rest[0] if rest else None;pc+=1
            if op=='.STRUCTREF':stack.append(fields[arg.split(maxsplit=1)[1]])
            elif op=='S_PUSH':stack.append(json.loads(arg))
            elif op=='PUSH':stack.append(int(arg,0))
            elif op=='A_REF':assert isinstance(stack[-1],str)
            elif op=='LT':b=stack.pop();a=stack.pop();stack.append(int(a<b))
            elif op in ['IFZ','IFNZ']:
                v=stack.pop()
                if bool(v)==(op=='IFNZ'):pc=labels[arg]
            elif op=='S_MOD':
                assert arg=='2';i=stack.pop();fmt=stack.pop();stack.append(fmt%i)
            elif op=='CALLFUNC':
                self.calls.append(arg)
                if arg=='EX_IsExistA':
                    handle=stack.pop();idx=stack.pop();name=stack.pop();assert handle==0
                    arr=self.lists.get(name,[]);stack.append(int(0<=idx<len(arr)))
                elif arg=='EX_AString':
                    handle=stack.pop();default=stack.pop();idx=stack.pop();name=stack.pop();assert handle==0
                    arr=self.lists.get(name,[]);stack.append(arr[idx] if 0<=idx<len(arr) else default)
                elif arg=='EX_IsExistIA2':
                    handle=stack.pop();field=stack.pop();idx=stack.pop();name=stack.pop();assert handle==0
                    stack.append(int(field in self.tab.get(name,{}).get(idx,{})))
                elif arg=='EX_IA2String':
                    handle=stack.pop();default=stack.pop();field=stack.pop();idx=stack.pop();name=stack.pop();assert handle==0
                    stack.append(self.tab.get(name,{}).get(idx,{}).get(field,default))
                else:raise AssertionError(arg)
            elif op=='RETURN':
                assert len(stack)==1 and isinstance(stack[0],str),(fid,stack)
                assert fields==seen,'getter changed persisted state'
                return stack[0]
            else:raise AssertionError((fid,op,arg))
        raise AssertionError('no return')

def main():
    ev=read(O/'build_evidence.json');assert sha(O/'NightRemaster.ain')==ev['files']['NightRemaster.ain']
    assert sha(O/'source.ex')==ev['source_files']['NightRemasterEX.ex'];doc=ex.decode_ex(O/'source.ex');tab,lists=tables(doc)
    vm=VM(tab,lists);m=read(Path(ev['source_pointer']['manifest']));tm=read(Path(m['item_skill_name_revision']['translation_map']))
    catalog=tm['rows']+tm['enemy_rows'];byblock={b:[r for r in catalog if r['block']==b] for b in [6,7,39,48]}
    tested=0;names=0;descs=0;fallback=0
    for fid,cls,member,node,block,field in ROWS:
        for row in byblock[block]:
            expected=decode(doc.strings[tuple(row['string_paths'][field])].value)
            stale=row['current']['name'] if field=='name' else 'stale description from saved game'
            state={'<nID>':row['id'],member:stale,'<nLevel>':17,'<nHitPoint>':43,'<nNumber>':29,'<bFound>':False,'custom_modifiers':[4,9]}
            got=vm.run(fid,state);assert got==expected,(fid,row['id'],expected,got)
            if field=='name':assert expected==row['target_name'];names+=1
            else:descs+=1
            tested+=1
        for idx in [-2147483648,-1,2147483647,999999]:
            state={'<nID>':idx,member:'original fallback'};before=len(vm.calls)
            assert vm.run(fid,state)=='original fallback';fallback+=1
            if idx<0:assert len(vm.calls)==before,'negative ID reached native indexing'
        if node!='monster':
            row=byblock[block][0];table_row=vm.tab[node][row['id']];saved=table_row.pop(field)
            assert vm.run(fid,{'<nID>':row['id'],member:'missing-field fallback'})=='missing-field fallback';fallback+=1
            table_row[field]=saved
    # User screenshot and actual copied resume save: the old cached string exists
    # even though the freshly loaded authoritative EX has the new display value.
    raw=(O/'NightR07.snapshot.raw').read_bytes();old=encode('아카나메');new=encode('때핥이')
    assert raw.count(old)==1 and raw.count(new)==0
    state={'<nID>':4,'<sName>':'아카나메','<nHitPoint>':17}
    got=vm.run(26155,state);assert got=='때핥이';assert state['<sName>']=='아카나메' and state['<nHitPoint>']==17
    # Original battle consumers call getter26155, including incoming attacks;
    # inventory, skill, weapon and equipment name members have no bypass reads.
    code=(O/'current_code.jam').read_text('utf8');blocks=re.split(r'(?m)(?=^FUNC \d+)',code)
    owners={}
    for fid,cls,member,_,__,___ in ROWS:
        needle=f'.STRUCTREF {cls} {member}'
        seen=[int(b.splitlines()[0].split()[1]) for b in blocks if b.startswith('FUNC ') and needle in b]
        expected=sorted([r[0] for r in ROWS if r[1:3]==(cls,member)])
        assert sorted(seen)==expected,(needle,seen,expected);owners[needle]=seen
    enemy_attack=next(b for b in blocks if b.startswith('FUNC 29257\n'));assert 'PUSH 26155\n\tCALLMETHOD 0' in enemy_attack
    load=(O/'built_29556.jam').read_text('utf8');calls=re.findall(r'CALLFUNC (.+)',load)
    assert calls==['MemModeInfo::Load','SystemFlagManager::Load','L_Weapon::LoadComment'];assert 'CALLFUNC L_Weapon::LoadComment\n\tPOP\n\tRETURN' in load
    comment_loader=next(b for b in blocks if b.startswith('FUNC 26914\n'));assert set(re.findall(r'\.GLOBALREF (.+)',comment_loader))=={'L_Weapon::m_comment'}
    comments={int(t.name.value.decode('cp932')[3:]):tree_values(t) for t in doc.blocks[40].payload.children}
    assert all(0<=i<1000 for i in comments);assert all(isinstance(s,str) for arr in comments.values() for s in arr)
    report=dict(status='COMPILED_GETTER_VM_PASS_NATIVE_PENDING',files=ev['files'],
        EX_name_rows=512,compiled_name_getter_cases=names,compiled_skill_description_cases=descs,total_compiled_table_cases=tested,
        negative_missing_id_and_missing_field_fallback_cases=fallback,no_persisted_structure_fields_changed=True,
        saved_old_enemy_name_count=raw.count(old),saved_new_enemy_name_count=raw.count(new),screenshot_regression={'id':4,'saved':'아카나메','getter_result':got},
        weapon_comment_rows=len(comments),weapon_comment_id_range_within_original1000_slots=True,
        after_load_new_call_only_reloads_weapon_description_strings=True,direct_member_bypass_reads=0,
        native_verified=False,save_file_reloaded_in_native_engine=False,
        limitation='Compiled getters executed in bounded VM with current parsed EX tables. Actual native save reload/visual result remains pending; user save was only copied/read.',
        translator_model='Codex internal')
    write(O/'verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
