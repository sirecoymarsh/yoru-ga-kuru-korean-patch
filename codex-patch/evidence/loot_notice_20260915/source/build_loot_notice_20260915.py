from pathlib import Path
import copy,json,re,struct
from build_remaster_multiplier_20260915 import cmd,read_meta,fn,ex,read_afa3,rebuild,part,child,maybe,val,allparts,rename,setlist,ss,si,txt_info,encode
import build_mod_tab_20260915 as mt
from build_route_perf_20260915 import symbol
from cheat_support_20260915 import R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit
from build_instant_loot_20260915 import clean,begin

O=Path('loot_notice_20260915');FILES=['NightRemaster.ain','NightRemasterPact.afa']
def build_pact(rt):
 d=ex.decode_ex(O/'original_pact_160.pactex');template=copy.deepcopy(part(d,'構築_マップ名土台'));tx=copy.deepcopy(part(d,'テキスト_マップ名'))
 root=d.blocks[2].payload.children[0];mt.ORDER=copy.deepcopy(val(root,'子パーツリスト').items[0]);child(root,'子パーツ').children=[];val(root,'子パーツリスト').items=[]
 setlist(root,'座標',[220,24,300]);ss(root,'コメント','KR_LootNotice');si(root,'表示',1)
 rename(template,'KR_ReceiptPanel');setlist(template,'座標',[0,0,1]);child(template,'子パーツ').children=[];val(template,'子パーツリスト').items=[]
 # Resize native construction, retaining the original frame colors and recipe.
 steps=child(txt_info(template),'手順リスト').children
 dims=[]
 for s in steps:
  r=val(s,'先矩形');vs=[mt.scalar(i.value.payload) for i in r.items];dims.append(vs.copy())
  # Native [x,y,xMode,yMode,width,height]; full-area fill needs no extent.
  assert len(vs)==6,vs
  if vs[4]>0:vs[4]+=270;vs[5]+=152;setlist(s,'先矩形',vs)
 mt.add(root,template)
 for n,text,x,y,size in [('KR_ReceiptTitle','즉시 처치 · 획득 보상',14,10,20),('KR_ReceiptBody','',14,40,18),('KR_ReceiptLife','0',0,0,18)]:
  t=copy.deepcopy(tx);rename(t,n);setlist(t,'座標',[x,y,3]);si(t,'原点座標モード',1)
  ti=txt_info(t);ss(ti,'テキスト',text,True);si(ti,'タグ処理有効',0);si(ti,'一文字辺りの表示時間',0)
  decor=child(ti,'テキスト装飾');si(decor,'フォントタイプ',259);si(decor,'フォントサイズ',size);si(decor,'行間隔',4);si(decor,'字間隔',0)
  setlist(decor,'フォント色',[140,225,255] if n.endswith('Title') else [255,255,255]);si(decor,'フォント太さ',0);si(decor,'フォント縁取り',0)
  if n.endswith('Life'):si(t,'表示',0)
  mt.add(root,t)
 # Plain, click-through native display parts only; no input hooks.
 for t in allparts(root):
  si(t,'クリック許可',0);si(t,'オンカーソル透過',1);si(t,'メッセージウィンドウ表示連動',0)
 p=O/'pact_186_notice.pactex';p.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(p).serialize_payload()==d.serialize_payload()
 report=rebuild(rt/'NightRemasterPact.afa',O/'NightRemasterPact.afa',{},[('Asra/LootNotice.pactex',p)])
 return dict(archive=report,appended_entry=186,source_recipe_rectangles=dims,notice_bounds=[220,24,570,188],font=259,seconds=6,old_entries_unchanged=True)

def build_ain(rt):
 src=rt/'NightRemaster.ain';m=read_meta(Path('instant_loot_20260915/candidate_meta.json'));seen={};names={}
 for f in m['functions']:
  n=symbol(m,f['index']);c=seen.get(n,0);seen[n]=c+1;names[f['index']]=n+(f'#{c}' if c else '')
 def get(i):
  p=O/f'original_{i}.jam';cmd('ain','dump','--function',names[i],'-o',p,src);return clean(p.read_text(encoding='utf8'),names[i])
 jaf=(O/'helpers_source.jaf').read_text(encoding='utf8')
 # Only Korean display literals use the shipped CP932 proxy font encoding.
 jaf=re.sub(r'"([^"\n]*)"',lambda x:'"'+(encode(x[1]).decode('cp932') if any('\uac00'<=c<='\ud7a3' for c in x[1]) else x[1])+'"',jaf)
 (O/'helpers.jaf').write_text(jaf,encoding='utf8');stage=O/'helpers_declared.ain';cmd('ain','edit','--jaf',O/'helpers.jaf','-o',stage,src)
 cmd('ain','dump','-j','-o',O/'declared_meta.json',stage);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
 old=unpack(src.read_bytes());raw=bytearray(unpack(stage.read_bytes()));size=struct.unpack_from('<I',old,12)[0];nsize=struct.unpack_from('<I',raw,12)[0]
 assert raw[16:16+size]==old[16:16+size] and raw[16+nsize:20+nsize]==b'FUNC'
 struct.pack_into('<I',raw,24+nsize,m['functions'][0]['address']);stage.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 bridge={}
 bridge['KR_NoticeParse']='\t.LOCALREF value\n\tCALLHLL String ToInt 0\n\tRETURN\n'
 bridge['KR_NoticeRegister']=f'\tPUSH -1\n\tPUSH {ids["KR_NoticeTick"]}\n\tDG_NEW_FROM_METHOD\n\t.LOCALREF enable\n\tIFZ notice_unregister\n\tCALLFUNC AFL_Parts_AddBeginUpdateEvent\n\tRETURN\nnotice_unregister:\n\tCALLFUNC AFL_Parts_EraseBeginUpdateEvent\n\tRETURN\n'
 bridge['KR_NoticeLoad']='\tS_PUSH "KR_LootNotice"\n\tS_PUSH "Asra\\\\LootNotice.pact"\n\tPUSH 0\n\tCALLFUNC activity::detail::ReadFile\n\tRETURN\n'
 # One owned reference is balanced on every branch. Getter calls borrow it.
 pro='\t.LOCALREF index\n\tCALLFUNC L_Party::AbilityAt\n\tX_DUP 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ notice_null\n'
 body=pro
 for k,mid in enumerate([27335,27333,27339,27340]):
  body+=f'\t.LOCALREF kind\n\tPUSH {k}\n\tNOTE\n\tIFNZ notice_kind_{k}\n\tX_DUP 1\n\tPUSH {mid}\n\tCALLMETHOD 0\n\tX_MOV 2 1\n\tDELETE\n\tRETURN\nnotice_kind_{k}:\n'
 bridge['KR_NoticeStat']=body+'notice_null:\n\tDELETE\n\tPUSH 0\n\tRETURN\n'
 bridge['KR_NoticeName']=pro+'\tX_DUP 1\n\tPUSH 27300\n\tCALLMETHOD 0\n\tX_MOV 2 1\n\tDELETE\n\tRETURN\nnotice_null:\n\tDELETE\n\tS_PUSH ""\n\tRETURN\n'
 patches={}
 for n,i in ids.items():
  p=O/f'jaf_{i}.jam';cmd('ain','dump','--function',n,'-o',p,stage);s=clean(native_lower(p.read_text(encoding='utf8')),n)
  s=s.replace('\tI_STRING\n','\tS_PUSH "%d"\n\tX_MOV 2 1\n\tS_MOD 2\n').replace('\tSTOI\n','\tCALLFUNC KR_NoticeParse\n')
  patches[i]=fn(i,n,bridge[n].replace('notice_null','notice_null_'+n)) if n in bridge else s
 s=get(28664);assert s.count('CALLFUNC KR_TryInstantLoot')==1;patches[28664]=s.replace('CALLFUNC KR_TryInstantLoot','CALLFUNC KR_NoticeInstant')
 for i in [28736,28739,28751,29813]:patches[i]=begin(get(i),'\tCALLFUNC KR_NoticeClear\n')
 jam=O/'notice_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,stage)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y,a['index']
  if aa!=bb:changed.append(a['index'])
 assert changed==[28664,28736,28739,28751,29813],changed
 for k in m:
  if k not in ['functions','switches']:assert m[k]==nm[k],k
 sw=[i for i,(a,b) in enumerate(zip(m['switches'],nm['switches'])) if a!=b];assert sw==[450,451],sw
 new=unpack(out.read_bytes());assert old[16:16+size]==new[16:16+size];assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
 for i in patches:cmd('ain','dump','--function',names.get(i) or next(n for n,ix in ids.items() if ix==i),'-o',O/f'built_{i}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);nat=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert nat['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',nat)
 return dict(patched_existing=changed,added_functions=ids,relocated_switches=sw,save_schema_unchanged=True,native_payout_unchanged=True)
def main():
 p=json.loads((O/'source_pointer.json').read_text());assert p==json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);assert sha(rt/'NightRemaster.ain')=='e12a6cc123471e3dd445839f7559ebbc6e5ea889bdae4e0cfc2db15c69ec52a6'
 ui=build_pact(rt);ain=build_ain(rt);ev=dict(status='LOOT_NOTICE_STAGED',source_pointer=p,source_files={n:sha(rt/n) for n in FILES},files={n:sha(O/n) for n in FILES},AIN=ain,PACT=ui,EX_unchanged_sha256=sha(rt/'NightRemasterEX.ex'),translator_model='Codex internal',native_gameplay_verified=False)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
