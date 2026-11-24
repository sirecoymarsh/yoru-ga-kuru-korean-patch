from pathlib import Path
import json,copy,random,struct,zlib
from loot_notice_vm_20260915 import VM as BaseVM
from build_remaster_multiplier_20260915 import read_meta,encode,decode,ex,part,child,val,allparts,txt_info,read_afa3
from build_mod_tab_20260915 import name,coords,scalar
from verify_instant_loot_20260915 import normalize
from cheat_support_20260915 import sha,savej
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from audit_dynamic_ui_20260915 import ENC
from PIL import Image,ImageDraw,ImageFont
import numpy as np
O=Path('loot_notice_20260915')
class VM(BaseVM):
 def __init__(self):
  super().__init__();self.enabled=True;self.eligible=True;self.success=True;self.load_ok=True;self.missing=None;self.clock=10000;self.handlers=set();self.widgets={};self.alpha=255;self.payouts=0;self.write_count=0
  self.party=[dict(level=10,exp=10,training=200,money=300,name=encode(n).decode('cp932')) for n in ['이즈미','쿄카','마나미']];self.rewards=[(800,50,100),(4000,80,150),(0,0,0)]
 def run(self,n,args=()):
  if n=='KR_GetLoot':return int(self.enabled)
  if n=='KR_LootEligible':return int(self.enabled and self.eligible and args[0] is not None and not args[0].get('removed'))
  if n=='KR_Time':return self.clock
  if n=='KR_TryInstantLoot':
   if not self.success:return 0
   assert self.run('KR_LootEligible',[args[0]]);self.payouts+=1;args[0]['removed']=True
   # External fixture implements native payout contract; unchanged engine code
   # is separately proven byte-identical. This is not an in-game execution.
   for p,(exp,tr,money) in zip(self.party,self.rewards):
    if p is None:continue
    if p['level']<99:
     p['exp']+=exp
     while p['level']<99 and p['exp']>=5*(p['level']+1)*(p['level']+2):
      p['exp']-=5*(p['level']+1)*(p['level']+2);p['level']+=1
    p['training']=min(99999,p['training']+tr);p['money']=min(999999,p['money']+money)
   return 1
  if n=='activity::detail::ReadFile':
   assert args==['KR_LootNotice','Asra\\LootNotice.pact',0],args
   if not self.load_ok:return 0
   self.widgets={k:'' for k in ['ルートパーツ','KR_ReceiptBody','KR_ReceiptLife'] if k!=self.missing};return 1
  if n=='AFL_Parts_AddBeginUpdateEvent':assert args[0] not in self.handlers;self.handlers.add(args[0]);return
  if n=='AFL_Parts_EraseBeginUpdateEvent':self.handlers.discard(args[0]);return
  if n=='AFL_Activity_Release':assert 'ルートパーツ' in self.widgets;self.widgets={};return 1
  if n=='Ｐ＿テキスト設定':assert args[0] in self.widgets and args[2]==1;self.widgets[args[0]]=args[1];self.write_count+=1;return
  if n=='Ｐ＿テキスト取得':assert args[0] in self.widgets and args[1]==1;return self.widgets[args[0]]
  if n=='Ｐ＿アルファ値設定':assert args[0]=='ルートパーツ' and args[0] in self.widgets and 0<=args[1]<=255;self.alpha=args[1];return
  return super().run(n,args)
 def method(self,mid,obj,args):
  k={27335:'level',27333:'exp',27339:'training',27340:'money',27300:'name'}
  if mid in k:assert not args;return obj[k[mid]]
  return super().method(mid,obj,args)

def tests():
 count=0;v=VM()
 for lv in range(1,100):
  for exp in [0,1,99999]:
   assert v.run('KR_NoticeTotal',[lv,exp])==exp+sum(sum(range(1,i+2))*10 for i in range(1,lv));count+=1
 rng=random.Random(15);scenarios=0;examples=[]
 for _ in range(120):
  v=VM()
  for p in v.party:
   p.update(level=rng.choice([1,10,20,98,99]),exp=rng.randrange(20),training=rng.choice([0,99990,99999]),money=rng.choice([0,999990,999999]))
  v.rewards=[(rng.choice([0,1,500,50000,500000]),rng.choice([0,30,50000]),rng.choice([0,500,500000])) for _ in v.party]
  before=copy.deepcopy(v.party);c={};assert v.run('KR_NoticeInstant',[c,202])==1 and c['removed'] and v.payouts==1 and len(v.handlers)==1 and not any(v.refs.values())
  text=decode(v.widgets['KR_ReceiptBody'].encode('cp932'));rows=text.splitlines();assert len(rows)==6
  for i,(a,b,(exp,tr,mo)) in enumerate(zip(before,v.party,v.rewards)):
   assert rows[i*2+1]==f'경험치 +{exp if a["level"]<99 else 0} / 훈련치 +{min(tr,99999-a["training"])} / 달조각 +{min(mo,999999-a["money"])}'
   assert ('레벨업!' in rows[i*2])==(b['level']>a['level'])
   if b['level']>a['level']:assert f'{a["level"]} → {b["level"]}' in rows[i*2]
  assert not v.run('KR_NoticeInstant',[c,202]) and v.payouts==1
  examples.append(text);scenarios+=1
 for issue in ['disabled','ineligible','failed','loadfail','missingbody','missinglife','nullparty']:
  v=VM()
  if issue=='disabled':v.enabled=False
  if issue=='ineligible':v.eligible=False
  if issue=='failed':v.success=False
  if issue=='loadfail':v.load_ok=False
  if issue=='missingbody':v.missing='KR_ReceiptBody'
  if issue=='missinglife':v.missing='KR_ReceiptLife'
  if issue=='nullparty':v.party[1]=None
  want=issue not in ['disabled','ineligible','failed'];assert bool(v.run('KR_NoticeInstant',[{},202]))==want;assert v.payouts==int(want) and not any(v.refs.values())
  if issue in ['loadfail','missingbody','missinglife']:assert not v.widgets and not v.handlers
 v=VM();v.run('KR_NoticeShow',['a']);writes=v.write_count
 for elapsed in [0,1,1000,4999,5499,5500]:
  v.clock=10000+elapsed;v.run('KR_NoticeTick',[16,16000]);assert v.handlers and v.alpha==255 and v.write_count==writes
 v.clock=15750;v.run('KR_NoticeTick',[16,16000]);assert v.alpha==127
 v.run('KR_NoticeShow',['b']);assert v.alpha==255 and len(v.handlers)==1 and v.widgets['KR_ReceiptBody']=='b'
 v.clock+=6000;v.run('KR_NoticeTick',[16,0]);assert not v.widgets and not v.handlers
 for _ in range(10):v.run('KR_NoticeClear');assert not v.widgets and not v.handlers
 for mode in ['clockreset','clockwrap','disabled','missing']:
  v=VM();v.clock=2147483640 if mode=='clockwrap' else 10000;v.run('KR_NoticeShow',['a'])
  if mode=='clockreset':v.clock=0
  if mode=='clockwrap':v.clock=-2147483640
  if mode=='disabled':v.enabled=False
  if mode=='missing':v.widgets={}
  v.run('KR_NoticeTick',[0,0]);assert bool(v.handlers)==(mode=='clockwrap')
 # Stress no duplicate callback, no text allocation during steady-state frames.
 v=VM()
 for _ in range(300):v.run('KR_NoticeShow',['latest']);v.clock+=1;v.run('KR_NoticeTick',[1,5]);assert len(v.handlers)==1
 savej(O/'receipt_examples.json',examples)
 return dict(total_exp_cases=count,compiled_receipt_scenarios=scenarios,failure_cases=7,rapid_replace_cases=300,balanced_getter_references=True,no_per_frame_text_rebuild=True,native_reward_execution='external fixture; original native payout byte identity checked')

def structure(ev):
 old=read_meta(Path('instant_loot_20260915/candidate_meta.json'));new=read_meta(O/'candidate_meta.json')
 allowed=ev['AIN']['patched_existing'];checks={}
 for i in allowed:
  a=(O/f'original_{i}.jam').read_text(encoding='utf8');b=(O/f'built_{i}.jam').read_text(encoding='utf8')
  if i==28664:b=b.replace('CALLFUNC KR_NoticeInstant','CALLFUNC KR_TryInstantLoot')
  else:assert b.count('CALLFUNC KR_NoticeClear')==1;b=b.replace('\tCALLFUNC KR_NoticeClear\n','')
  assert normalize(a)==normalize(b),i;checks[str(i)]=len(normalize(a))
 for i in [26258,31870,29817,29818,31859,31860]:assert old['functions'][i]==new['functions'][i]
 rt=Path(ev['source_pointer']['runtime']);a=read_afa3(rt/'NightRemasterPact.afa');b=read_afa3(O/'NightRemasterPact.afa');ab=(rt/'NightRemasterPact.afa').read_bytes();bb=(O/'NightRemasterPact.afa').read_bytes();assert len(a.entries)==186 and len(b.entries)==187
 for x,y in zip(a.entries,b.entries):assert x.name==y.name and ab[x.absolute_offset:x.absolute_offset+x.size]==bb[y.absolute_offset:y.absolute_offset+y.size]
 d=ex.decode_ex(O/'pact_186_notice.pactex');root=d.blocks[2].payload.children[0];names=[]
 for t in allparts(root):
  names.append(name(t));assert scalar(val(t,'クリック許可'))==0 and scalar(val(t,'オンカーソル透過'))==1
 assert len(names)==len(set(names))==5
 assert scalar(val(part(d,'KR_ReceiptLife'),'表示'))==0
 return dict(inverse_original_instruction_counts=checks,native_payout_and_prior_mod_functions_unchanged=True,old_PACT_entries_identical=186,click_through_parts=5)

def font_proof(rt):
 fp=rt/'NightRemasterFont.fnl';raw=fp.read_bytes();_,faces=parse_fnl_font(fp,3);table={};q=20
 for fontno in range(struct.unpack_from('<I',raw,16)[0]):
  nf=struct.unpack_from('<I',raw,q)[0];q+=4
  for fi in range(nf):
   h,u,n=struct.unpack_from('<III',raw,q);q+=12
   if fontno==3:table[fi]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(n)])
   q+=10*n
 proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};samples=json.loads((O/'receipt_examples.json').read_text());samples.append('이즈미  레벨업! 10 → 15\n경험치 +50000 / 훈련치 +500 / 달조각 +999\n쿄카\n경험치 +0 / 훈련치 +0 / 달조각 +0\n마나미  레벨업! 98 → 99\n경험치 +500000 / 훈련치 +99999 / 달조각 +999999')
 im=Image.new('RGB',(620,235),(17,24,44));dr=ImageDraw.Draw(im);dr.rectangle((24,12,593,199),fill=(5,10,52),outline=(255,255,255));dr.text((18,214),'ACTUAL SHIPPED FNL / NOT A GAME CAPTURE',font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12),fill=(150,180,200))
 checked=set();widths=[]
 for text,size in [('즉시 처치 · 획득 보상',20)]+[(s,18) for s in samples]:
  face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,0,0,0)
  for line in text.splitlines():
   width=measure.measure(line,True)['lines'][0]['width_px'];assert width<=542,(line,width);widths.append(width)
   for c in line:
    if c.isspace():continue
    idx=measure.glyph_index(c,True);h,es=table[face.face_index];w,pos,n=es[idx];assert pos>0 and w>0 and n>0 and any(zlib.decompress(raw[pos:pos+n])),(c,size);checked.add((c,size))
 def draw(text,x,y,size,color):
  face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,0,0,0)
  for c in text:
   h,es=table[face.face_index];w,pos,n=es[measure.glyph_index(c,True)]
   if not c.isspace():
    rg=zlib.decompress(raw[pos:pos+n]);bits=np.unpackbits(np.frombuffer(rg,dtype=np.uint8).reshape(h,len(rg)//h),axis=1,bitorder='big')[::-1]*255;mask=Image.fromarray(bits,'L').resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS);im.paste(color,(round(x),round(y)),mask)
   x+=w/den
 draw('즉시 처치 · 획득 보상',38,22,20,(140,225,255))
 for i,line in enumerate(samples[-1].splitlines()):draw(line,38,52+22*i,18,(255,255,255))
 im.save(O/'font_layout_proof.png');return dict(font_sha256=sha(fp),actual_face=3,checked_glyph_size_pairs=len(checked),max_width=max(widths),width_budget=542,body_lines_max=6,native_gameplay_verified=False)
def main():
 ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items());t=tests();s=structure(ev);f=font_proof(Path(ev['source_pointer']['runtime']))
 r=dict(status='LOOT_NOTICE_STATIC_PASS_NATIVE_PENDING',files=ev['files'],compiled=t,structure=s,font=f,native_gameplay_verified=False,actual_save_reload_verified=False,translator_model='Codex internal');savej(O/'verification.json',r);print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
