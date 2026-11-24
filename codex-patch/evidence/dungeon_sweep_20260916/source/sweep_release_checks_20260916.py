from pathlib import Path
import json,copy,re,struct,zlib,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_remaster_multiplier_20260915 import ex,part,child,val,read_afa3,read_meta,encode,decode
from build_mod_tab_20260915 import scalar,coords,name
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from audit_dynamic_ui_20260915 import ENC
from cheat_support_20260915 import sha,savej
from verify_dungeon_sweep_20260916 import VM
O=Path('dungeon_skip_20260916');ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime'])
assert all(sha(O/n)==h for n,h in ev['files'].items())
old=read_meta(Path('loot_notice_20260915/candidate_meta.json'));new=read_meta(O/'candidate_meta.json')
assert old['switches']==new['switches'] and old['structures']==new['structures'] and old['globals']==new['globals']
# Originals still exist verbatim in CODE; nested lambdas must also retain their semantics.
def normalize(s):
 labels={};out=[]
 for l in s.splitlines():
  if l.startswith(';') or not l.strip():continue
  if l.endswith(':') and re.fullmatch(r'0x[0-9a-f]+:',l):labels[l[:-1]]=len(labels)
  out.append(l)
 return re.sub(r'0x[0-9a-f]+',lambda m:'label'+str(labels[m[0]]),'\n'.join(out))
from build_remaster_multiplier_20260915 import cmd
from build_dungeon_sweep_20260916 import NAMES
for i in [31473]+list(range(31639,31652)):
 for prefix,ain in [('before',rt/'NightRemaster.ain'),('after',O/'NightRemaster.ain')]:
  cmd('ain','dump','--function',NAMES[i],'-o',O/f'lambda_{prefix}_{i}.jam',ain)
 assert normalize((O/f'lambda_before_{i}.jam').read_text(encoding='utf8'))==normalize((O/f'lambda_after_{i}.jam').read_text(encoding='utf8'))
a=read_afa3(rt/'NightRemasterPact.afa');b=read_afa3(O/'NightRemasterPact.afa');assert len(a.entries)==len(b.entries)==187
ar=(rt/'NightRemasterPact.afa').read_bytes();br=(O/'NightRemasterPact.afa').read_bytes();changed=[]
for i,(x,y) in enumerate(zip(a.entries,b.entries)):
 if ar[x.absolute_offset:x.absolute_offset+x.size]!=br[y.absolute_offset:y.absolute_offset+y.size]:changed.append(i)
assert changed==[161,185]
d=ex.decode_ex(O/'pact_161_sweep.pactex');root=part(d,'KR_SweepRoot');button=part(d,'KR_SweepButton');label=part(d,'KR_SweepButtonLabel')
assert coords(root)[:2]==[1130,386] and scalar(val(root,'表示'))==0
scale=[scalar(i.value.payload) for i in val(button,'拡大縮小').items];assert scale==[.71875,1]
assert [scalar(i.value.payload) for i in val(label,'拡大縮小').items]==[1,1]
assert coords(root)[0]+192*scale[0]==1268
fp=rt/'NightRemasterFont.fnl';raw=fp.read_bytes();_,faces=parse_fnl_font(fp,3);table={};q=20
for fontno in range(struct.unpack_from('<I',raw,16)[0]):
 nf=struct.unpack_from('<I',raw,q)[0];q+=4
 for fi in range(nf):
  h,u,n=struct.unpack_from('<III',raw,q);q+=12
  if fontno==3:table[fi]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(n)])
  q+=10*n
proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};checked=set();widths=[]
v=VM();assert v.run('KR_SweepExecute',[v.scene]);receipt=decode(v.report[0].encode('cp932'))
samples=[('자동 소탕',24),('소탕',24),('일반 던전에 자동 소탕 버튼을 표시합니다.',14),('소탕: 남은 시간 정산 후 다음 날로 진행',14),(receipt,24)]
im=Image.new('RGB',(1000,620),(13,20,43));dr=ImageDraw.Draw(im)
def draw(text,x,y,size):
 face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,0,0,0)
 for line in text.splitlines():
  width=measure.measure(line,True)['lines'][0]['width_px'];assert width<950,(line,width);widths.append(width);xx=x
  for c in line:
   h,es=table[face.face_index];w,pos,n=es[measure.glyph_index(c,True)]
   if not c.isspace():
    assert pos and n and w,(c,size);rg=zlib.decompress(raw[pos:pos+n]);assert any(rg)
    bits=np.unpackbits(np.frombuffer(rg,dtype=np.uint8).reshape(h,len(rg)//h),axis=1,bitorder='big')[::-1]*255
    mask=Image.fromarray(bits,'L').resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS);im.paste((240,245,255),(round(xx),round(y)),mask);checked.add((c,size))
   xx+=w/den
  y+=size+5
 return y
face,den,_=select_fnl_face(faces,24);measure=WidthMeasurer(face,den,proxy,0,0,0);bw=measure.measure('자동 소탕',True)['lines'][0]['width_px'];assert abs(coords(label)[0]+bw/2-69)<=2,(bw,coords(label))
dr.rectangle((20,20,158,62),outline=(65,190,255),width=2);draw('자동 소탕',20+coords(label)[0],29,24)
draw(receipt,20,85,24)
for s,size in samples:draw(s,20,85 if s==receipt else 550 if size==14 else 29,size) if False else None
for s,size in samples:
 face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,0,0,0)
 for c in s:
  if c.isspace():continue
  h,es=table[face.face_index];w,pos,n=es[measure.glyph_index(c,True)];assert pos and n and w,(c,size)
dr.text((20,594),'SHIPPED FNL / COMPILED LOGIC FIXTURE / NOT A GAME CAPTURE',font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14),fill=(140,180,210));im.save(O/'font_layout_proof.png')
# Native equipment table preflight assumptions, not fixture-only existence claims.
ed=ex.decode_ex(rt/'NightRemasterEX.ex');t=next(b.payload for b in ed.blocks if b.name.value.decode('cp932')=='装備アイテムデータ')
ranks=collections.Counter(scalar(row[1].payload) for row in t.rows)
assert all(ranks[x]>0 for x in range(1,8)),ranks
savej(O/'release_checks.json',dict(status='RELEASE_STATIC_PASS',files=ev['files'],nested_lambda_semantics_unchanged=14,switches_metadata_unchanged=True,unchanged_PACT_entries=185,changed_PACT_entries=changed,button_bounds=[1130,386,1268,428],button_text_width=bw,unscaled_Hangul=True,font_glyph_size_pairs=len(checked),font_sha256=sha(fp),native_equipment_rank_counts=dict(ranks),native_gameplay_verified=False))
savej(O/'reward-policy.json',dict(translator_model='Codex internal',status='FROZEN_IMPLEMENTED',time_unit='native L_Calendar raw exploration units, not wall-clock minutes',day_budget=1000,assumptions=dict(shared_budget_block=200,battles_per_block=5,chests_per_block=1,effective_battle_interval=40,explanation='Gameplay-balancing assumption, not measured encounter duration. Current floor only. floor(R/40) native encounters, one native ordinary chest after each fifth encounter. The block budget includes movement/encounter/chest time; no double-use of remaining time.'),rounding='floor; R<40 gives no payout, no minimum grant',maximum=dict(battles=25,chests=5),payout='Native placement26995, KR_LootMonsterById, silent Settle26258 and chest27183. Existing per-item rates apply once in native routines. Native ceilings preserved. No guaranteed equal rewards to exploring an infinite dungeon.',rollback='Copy of all native reward scalar targets before payout; controlled false return restores, clears temporary incomes and resets private RNG. Fatal VM/process errors are not catchable; no disk saves during transaction.',transition='AdvanceRemainTime28650 to zero, original28637 exit block, fixed income once, normal Sunday/day-end to NextDate27741; no direct date increment',story='Strict hash-bound whitelist80 regular floors. All ID<1000,1201,2601 and unknown rejected.'))
print('RELEASE STATIC CHECKS PASS',ranks,'buttontext',bw)
