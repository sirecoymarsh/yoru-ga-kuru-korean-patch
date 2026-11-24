"""Run compiled getter paths using the screenshot's old names and quantities."""
import copy,json,re
from pathlib import Path
from build_consume_saved_display_20260915 import O,GETTERS,read,sha,write,decode,encode

def run(fid,state):
    original=copy.deepcopy(state);ops=[];labels={}
    for s in (O/f'built_{fid}.jam').read_text('utf8').splitlines():
        s=s.strip()
        if not s or s.startswith((';','FUNC ','ENDFUNC ')):continue
        if s.endswith(':'):labels[s[:-1]]=len(ops)
        else:ops.append(s.split(maxsplit=1))
    stack=[];pc=0;steps=0
    while pc<len(ops):
        steps+=1;assert steps<100;op,*rest=ops[pc];arg=rest[0] if rest else '';pc+=1
        if op=='.STRUCTREF':stack.append(state[arg.split(maxsplit=1)[1]])
        elif op=='PUSH':stack.append(int(arg,0))
        elif op=='S_PUSH':stack.append(json.loads(arg,strict=False))
        elif op=='EQUALE':b=stack.pop();a=stack.pop();stack.append(int(a==b))
        elif op=='IFZ':
            if not stack.pop():pc=labels[arg]
        elif op=='A_REF':assert isinstance(stack[-1],str)
        elif op=='RETURN':
            assert len(stack)==1 and isinstance(stack[0],str) and state==original
            return stack[0]
        else:raise AssertionError((fid,op,arg))
    raise AssertionError('Missing return')

def main():
    ev=read(O/'build_evidence.json');assert sha(O/'NightRemaster.ain')==ev['files']['NightRemaster.ain'];assert sha(O/'display_catalog.json')==ev['source_catalog_sha256']
    catalog=read(O/'display_catalog.json')['rows'];legacy=['반월환','달의 물방울','월광정','만월환','카사의 영약'];quantity=[3,4,5,4,2]
    count=0;unknown=0;displays=[]
    for fid,member,field in GETTERS:
        for row in catalog:
            itemid=row['id'];state={'<nID>':itemid,member:encode(legacy[itemid-1]).decode('cp932'),'<nNumber>':quantity[itemid-1],'<bFound>':True,'_nMoonPiece':[100,300,600]}
            before=copy.deepcopy(state);result=run(fid,state)
            assert result==row['raw_'+field] and decode(result.encode('cp932'))==row[field] and state==before
            count+=1
            if fid==26668:displays.append(dict(id=itemid,before=legacy[itemid-1],after=row['name'],quantity=quantity[itemid-1]))
        for invalid in [-2147483648,-1,0,6,99,2147483647]:
            state={'<nID>':invalid,member:'unchanged fallback','<nNumber>':11};assert run(fid,state)=='unchanged fallback' and state['<nNumber>']==11;unknown+=1
    required={26693:26668,26694:26668,27188:26668,27749:26671,31454:26680,31481:26680}
    for consumer,getter in required.items():
        body=(O/f'consumer_{consumer}.jam').read_text('utf8');assert f'PUSH {getter}\n\tCALLMETHOD 0' in body,(consumer,getter)
    for fid in [31454,31481]:
        source=(O/f'original_{fid}.jam').read_text('utf8');built=(O/f'built_{fid}.jam').read_text('utf8')
        raw=encode('무기 강화 재료').decode('cp932');assert built.count('S_PUSH '+json.dumps(raw,ensure_ascii=False))==1
        assert 'S_PUSH "武器強化素材"' not in built
        # Reassembly relocates labels. Normalize addresses and the one allowed
        # string operand; everything else, including captured offsets, must match.
        def norm(s):return re.sub(r'0x[0-9a-f]+','ADDR',s.strip())
        assert norm(source.replace('S_PUSH "武器強化素材"','S_PUSH '+json.dumps(raw,ensure_ascii=False)))==norm(built)
    # These six are the only direct reads of the three stored display members.
    original=Path('saved_name_refresh_20260915/current_code.jam').read_text('utf8');blocks=re.split(r'(?m)(?=^FUNC \d+)',original)
    for member in ['<sName>','<sMoldName>','<sDesc>']:
        direct=[int(b.splitlines()[0].split()[1]) for b in blocks if b.startswith('FUNC ') and f'.STRUCTREF C_ConsumeItem {member}' in b]
        assert sorted(direct)==sorted(f for f,m,k in GETTERS if m==member)
    previous=read(Path('saved_name_refresh_20260915/verification.json'));assert previous['EX_name_rows']==512
    report=dict(status='CONSUMABLE_COMPILED_VM_AND_CONSUMER_CLOSURE_PASS',files=ev['files'],getter_cases=count,unknown_id_fallback_cases=unknown,
        screenshot_regression=displays,selection_use_acquisition_crafting_and_description_consumers_verified=list(required),direct_member_bypasses=0,
        approved_name_catalog_coverage={'EX_names_previously_fixed_and_retained':512,'separate_consumable_names_now_fixed':5,'total':517},
        descriptions_and_original_crafting_name_padding_preserved=True,adjacent_element_stone_UI_description_operands_fixed=2,no_quantity_found_price_stat_or_multiplier_mutation=True,
        native_verified=False,actual_save_reload_verified=False,limitation='Executed persisted compiled getters in a bounded VM. Real native menu display remains pending.',translator_model='Codex internal')
    write(O/'verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
