"""Build from the latest josa/polish runtime; only chest blocking and display change."""
from pathlib import Path
import copy,json,re,struct,shutil
from cheat_support_20260915 import R,sha,savej,cmd,read_meta
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,allparts,rename,setlist,ss,si,txt_info,fn
import build_mod_tab_20260915 as mt
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from build_dungeon_sweep_20260916 import lr,push,cf,assign
from build_route_puzzle_20260916 import borrowed,fld
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=R/'staging/chest_flow_20260917'
EXPECTED='93b052dbd64037588a8c68220d6c3602c948897404c7f84328bee300d2bb92da'
FILES=['NightRemaster.ain','NightRemasterPact.afa']
HERE=Path(__file__).resolve().parent

def text(s):return '\tS_PUSH '+json.dumps(s,ensure_ascii=False)+'\n'
def virtual(pair,slot,args='',argc=0):
    return pair+'\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n'+push(0)+'\tX_REF 1\n\tX_MOV 2 1\n'+push(slot)+'\tADD\n\tX_REF 1\n'+args+f'\tCALLMETHOD {argc}\n'

def part_body():
    # Same validated owned GetActiveScene reference and borrowed descendants as puzzle guide.
    fail='chest_part_done'
    b=''.join(f'\t.LOCALASSIGN {n} -1\n' for n in ['outer','scene','view','result'])
    b+='\t.GLOBALREF GetActiveScene\n\tCALLHLL Delegate Numof 0\n'+push(1)+f'\tNOTE\n\tIFNZ {fail}\n'
    dg='\t.GLOBALREF GetActiveScene\n\tDG_CALLBEGIN "DG_Func<ref I_Scene>"\nchest_delegate_loop:\n\tDG_CALL "DG_Func<ref I_Scene>" chest_delegate_done\n\tJUMP chest_delegate_loop\nchest_delegate_done:\n\tPOP\n'
    b+=assign(1,dg)
    def nn(o):return o+push(-1)+f'\tEQUALE\n\tIFNZ {fail}\n'
    def check(o,minimum,first):
        a=fld(o,0)
        return nn(o)+nn(a)+a+'\tCALLHLL Array Numof 1\n'+push(minimum)+f'\tLT\n\tIFNZ {fail}\n'+fld(a,0)+push(first)+f'\tNOTE\n\tIFNZ {fail}\n'
    b+=check(lr('outer'),3,28170)
    b+=borrowed(2,lr('outer')+push(3)+'\tX_REF 2\n\tPOP\n')+check(lr('scene'),4,28634)
    b+=borrowed(3,fld(lr('scene'),2))+nn(lr('view'))
    pair=lr('view')+push(0)+'\tX_REF 2\n'
    b+=nn(fld(lr('view'),0))
    b+=virtual(pair,7,lr('key')+'\tA_REF\n',1)
    b+='\tX_DUP 2\n\tPOP\n'+push(-1)+'\tEQUALE\n\tIFNZ chest_part_null\n'
    b+=virtual('\tX_DUP 2\n',31)
    # Retain numeric ID while releasing the exact owned IParts pair.
    b+='\tX_MOV 3 1\n\tPOP\n\tDELETE\n\tPUSHLOCALPAGE\n'+push(4)+'\tX_MOV 3 2\n\tX_ASSIGN 1\n\tPOP\n\tJUMP chest_part_done\n'
    b+='chest_part_null:\n\tPOP\n\tDELETE\nchest_part_done:\n'
    b+=''.join(f'\t.LOCALDELETE {n}\n' for n in ['view','scene','outer'])+lr('result')+'\tRETURN\n'
    return b

def pact(rt):
    src=rt/'NightRemasterPact.afa';a=read_afa3(src)
    for i in [160,161]:
        e=a.entries[i]
        with src.open('rb') as f:f.seek(e.absolute_offset);(O/f'original_pact_{i}.pactex').write_bytes(f.read(e.size))
    doc=ex.decode_ex(O/'original_pact_161.pactex');donor=ex.decode_ex(O/'original_pact_160.pactex')
    parent=part(doc,'矩形_000');mt.ORDER=copy.deepcopy(val(parent,'子パーツリスト').items[0])
    root=mt.clean_group(part(doc,'KR_SweepRoot'),'KR_ChestNotice',20,18)
    setlist(root,'座標',[20,18,300]);si(root,'表示',0)
    rect=child(child(root,'種類別情報'),'通常状態')
    for key,point in [('左上',[0,0]),('右上',[620,0]),('左下',[0,120]),('右下',[620,120])]:setlist(rect,key,point)
    panel=copy.deepcopy(part(donor,'構築_マップ名土台'));rename(panel,'KR_ChestPanel');setlist(panel,'座標',[0,0,1])
    child(panel,'子パーツ').children=[];val(panel,'子パーツリスト').items=[]
    steps=child(txt_info(panel),'手順リスト').children
    old_rects=[]
    for s in steps:
        vs=[mt.scalar(i.value.payload) for i in val(s,'先矩形').items];old_rects.append(vs.copy())
        if vs[4]>0:vs[4]+=320;vs[5]+=84;setlist(s,'先矩形',vs)
    mt.add(root,panel)
    donor_text=part(donor,'テキスト_マップ名')
    for name,txt,y,size in [('KR_ChestTitle','보물상자',10,18),('KR_ChestLine1','',36,20),('KR_ChestLine2','',61,20),('KR_ChestLine3','',86,20),('KR_ChestLife','-1',0,12)]:
        p=copy.deepcopy(donor_text);rename(p,name);setlist(p,'座標',[14,y,3]);si(p,'原点座標モード',1)
        ti=txt_info(p);ss(ti,'テキスト',txt,True);si(ti,'タグ処理有効',0);si(ti,'一文字辺りの表示時間',0)
        d=child(ti,'テキスト装飾');si(d,'フォントタイプ',259);si(d,'フォントサイズ',size);si(d,'字間隔',0);si(d,'行間隔',0)
        setlist(d,'フォント色',[255,224,96]);si(d,'フォント太さ',0);si(d,'フォント縁取り',1)
        si(p,'表示',int(name!='KR_ChestLife'));mt.add(root,p)
    for p in allparts(root):
        si(p,'クリック許可',0);si(p,'オンカーソル透過',1);si(p,'メッセージウィンドウ表示連動',0)
    mt.add(parent,root)
    out=O/'pact_161_chest.pactex';out.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()))
    assert ex.decode_ex(out).serialize_payload()==doc.serialize_payload()
    mt.remove(parent,'KR_ChestNotice');assert doc.serialize_payload()==ex.decode_ex(O/'original_pact_161.pactex').serialize_payload()
    return dict(archive=rebuild(src,O/'NightRemasterPact.afa',{161:out}),source_rectangles=old_rects,own_subtree='KR_ChestNotice',clickthrough=True,hidden_by_default=True)

def main():
    ptr=json.loads((R/'ui_cumulative/current.json').read_text(encoding='utf8'));rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert ptr==json.loads((O/'source_pointer.json').read_text()) and sha(src)==EXPECTED and sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    m=read_meta(O/'source_meta.json');seen={};names={}
    for f in m['functions']:
        n=symbol(m,f['index']);k=seen.get(n,0);seen[n]=k+1;names[f['index']]=n+(f'#{k}' if k else '')
    def get(i):
        p=O/f'original_{i}.jam';cmd('ain','dump','--function',names[i],'-o',p,src);return clean(p.read_text(encoding='utf8'),names[i])
    jaf=HERE/'chest_flow_helpers_20260917.jaf';shutil.copy2(jaf,O/jaf.name)
    decl=O/'declared.ain';cmd('ain','edit','--jaf',jaf,'-o',decl,src)
    old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));size=struct.unpack_from('<I',old,12)[0];ns=struct.unpack_from('<I',raw,12)[0]
    assert raw[16:16+size]==old[16:16+size];struct.pack_into('<I',raw,24+ns,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
    cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
    bridge={'KR_ChestPart':part_body(),'KR_ChestRegister':push(-1)+push(ids['KR_ChestTick'])+'\tDG_NEW_FROM_METHOD\n'+lr('enable')+'\tIFZ chest_unregister\n'+cf('AFL_Parts_AddBeginUpdateEvent')+'\tRETURN\nchest_unregister:\n'+cf('AFL_Parts_EraseBeginUpdateEvent')+'\tRETURN\n'}
    # Immediate text/state HLL adapters are filled from native ABI evidence.
    bridge.update(json.loads((O/'immediate_bridges.json').read_text(encoding='utf8')))
    patches={};edits={}
    for n,i in ids.items():
        p=O/f'jaf_{i}.jam';cmd('ain','dump','--function',n,'-o',p,decl)
        s=clean(native_lower(p.read_text(encoding='utf8')),n).replace('\tI_STRING\n','\tS_PUSH "%d"\n\tX_MOV 2 1\n\tS_MOD 2\n')
        patches[i]=fn(i,n,bridge[n]) if n in bridge else s
    s=get(27194);oldcall=lr('txt')+'\tA_REF\n'+push(150)+cf('■シンプルダイアログ');newcall=lr('txt')+'\tA_REF\n'+cf('KR_ChestShow')
    assert s.count(oldcall)==1;patches[27194]=s.replace(oldcall,newcall);edits[27194]=[dict(old=oldcall,new=newcall)]
    s=get(28664);start=s.index('.CASE 450:5 4\n');end=s.index('.CASE 450:6 5\n',start);region=s[start:end]
    motion='\tPUSHSTRUCTPAGE\n'+push(28652)+'\tCALLMETHOD 0\n';assert region.count(motion)==1
    updated=region.replace(motion,'');patches[28664]=s[:start]+updated+s[end:];edits[28664]=[dict(old=region,new=updated)]
    for i in [28736,28739,28751,29813]:
        s=get(i);patches[i]=begin(s,cf('KR_ChestClear'));edits[i]=[dict(old=s,new=patches[i])]
    jam=O/'patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,decl)
    cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
    for a,b in zip(m['functions'],nm['functions']):
        a=dict(a);b=dict(b);aa=a.pop('address');bb=b.pop('address');assert a==b
        if aa!=bb:changed.append(a['index'])
    assert changed==[27194,28664,28736,28739,28751,29813]
    for k in m:
        if k not in ['functions','switches']:assert m[k]==nm[k],k
    sw=[i for i,(a,b) in enumerate(zip(m['switches'],nm['switches'])) if a!=b];assert sw==[450,451]
    for i in sw:
        a,b=m['switches'][i],nm['switches'][i];assert a['case-type']==b['case-type'] and a['default-address']==b['default-address'] and [x['value'] for x in a['cases']]==[x['value'] for x in b['cases']]
    new=unpack(out.read_bytes());assert old[16:16+size]==new[16:16+size]
    assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
    assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
    for i in patches:cmd('ain','dump','--function',names.get(i,nm['functions'][i]['name']),'-o',O/f'built_{i}.jam',out)
    cmd('ain','dump','--raw-code','--no-macros','-o',O/'raw.jam',out);na=audit(out,O/'candidate_meta.json',O/'raw.jam',rt/'NightRemaster.exe',ids=list(patches));assert na['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',na)
    pe=pact(rt);savej(O/'reversible_edits.json',edits)
    ev=dict(status='CHEST_FLOW_STAGED',source_pointer=ptr,source_files={n:sha(rt/n) for n in FILES},files={n:sha(O/n) for n in FILES},patched_existing=changed,added_functions=ids,relocated_switches=sw,old_CODE_STR0_MSG1_exact=True,save_schema_changes=0,PACT=pe,translator_model='Codex internal',native_verified=False,unchanged_files={n:sha(rt/n) for n in ['NightRemasterEX.ex','NightRemasterFont.fnl','NightRemasterCG.afa','NightRemaster.exe']})
    savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
