from pathlib import Path
import copy,json,re,struct,zlib
from cheat_support_20260915 import R,sha,read_meta,savej,cmd
from build_remaster_multiplier_20260915 import ex,part,child,maybe,val,allparts,read_afa3,decode
from build_mod_tab_20260915 import remove,name,coords,scalar
from build_route_perf_20260915 import symbol
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from audit_dynamic_ui_20260915 import ENC
O=R/'staging/autoequip_20260917';ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime']);m=read_meta(O/'candidate_meta.json');ids=ev['AIN']['added_functions']
assert all(sha(O/n)==h for n,h in ev['files'].items())
docs={i:ex.decode_ex(O/f'pact_{i}_autoequip.pactex') for i in [153,154,185]}
for i,parent,root in [(153,'矩形_アイテム','KR_AutoEquipRoot'),(154,'矩形_追加より上','KR_AutoStoneRoot'),(185,None,'KR_AutoEquipToggle')]:
 d=copy.deepcopy(docs[i]);remove(part(d,parent) if parent else d.blocks[2].payload.children[0],root)
 assert d.serialize_payload()==ex.decode_ex(O/f'original_pact_{i}.pactex').serialize_payload(),('original UI changed',i)
 for t in allparts(docs[i].blocks[2].payload.children[0]):
  if maybe(t,'子パーツ') is None:continue
  ns=[name(k) for k in child(t,'子パーツ').children];order=[(x.value.payload.replacement or x.value.payload.value).decode('cp932') for x in val(t,'子パーツリスト').items]
  assert ns==order and len(ns)==len(set(ns))
ar=(rt/'NightRemasterPact.afa').read_bytes();br=(O/'NightRemasterPact.afa').read_bytes();a=read_afa3(rt/'NightRemasterPact.afa');b=read_afa3(O/'NightRemasterPact.afa');changed=[]
for i,(x,y) in enumerate(zip(a.entries,b.entries)):
 assert x.name==y.name
 if ar[x.absolute_offset:x.absolute_offset+x.size]!=br[y.absolute_offset:y.absolute_offset+y.size]:changed.append(i)
assert changed==[153,154,185] and len(a.entries)==len(b.entries)==187
# Every original nested callback retained, modulo branch relocation.
def normalize(s):
 labs={x[:-1]:f'L{i}' for i,x in enumerate(z.strip() for z in s.splitlines() if re.fullmatch('0x[0-9a-f]+:',z.strip()))}
 return re.sub(r'0x[0-9a-f]+',lambda x:labs[x[0]],'\n'.join(z for z in s.splitlines() if z.strip() and not z.startswith(';')))
seen={};names={}
for f in m['functions']:
 n=symbol(m,f['index']);j=seen.get(n,0);seen[n]=j+1;names[f['index']]=n+(f'#{j}' if j else '')
lambdas=[i for i in ev['AIN']['patched_existing'] if 31000<i<31814]
for fid in lambdas:
 for suffix,ain in [('old',rt/'NightRemaster.ain'),('new',O/'NightRemaster.ain')]:cmd('ain','dump','--function',names[fid],'-o',O/f'lambda_{suffix}_{fid}.jam',ain)
 assert normalize((O/f'lambda_old_{fid}.jam').read_text(encoding='utf8'))==normalize((O/f'lambda_new_{fid}.jam').read_text(encoding='utf8'))
stock=(O/f'built_{ids["KR_AutoStoneRun"]}.jam').read_text(encoding='utf8');assert re.search(r'PUSH 28586\n(?:(?!CALLMETHOD).)*CALLMETHOD 4',stock,re.S)
make=(O/f'built_{ids["KR_AutoMakeWeapon"]}.jam').read_text(encoding='utf8');assert 'CALLFUNC L_Weapon::CreateNewWeapon' in make and 'PUSH 26895' in make
assert 'PUSH 99' in stock and 'PUSH 99999' not in stock
assert 'CALLFUNC KR_AutoBindAbilityMarker' not in (O/f'built_{ids["KR_AutoGearRun"]}.jam').read_text(encoding='utf8')
control=(O/'built_28585.jam').read_text(encoding='utf8');assert 'autostone_regular' not in control # reassembled numeric labels
assert control.count('CALLFUNC KR_AutoStoneVisible')==2 and 'CALLFUNC KR_AutoStoneRun' in control
# Flag83 is absent from the original enum and all previously added literal flag calls.
enum=Path('autoequip_probe_20260917/31349.jam').read_text();assert '\tPUSH 83\n' not in enum
prior=(R/'staging/route_puzzle_20260916/native_raw_code.jam').read_text();assert not re.search(r'PUSH 0x53\n[^\n]*CALLFUNC 0x7c5c',prior)
# Actual shipped font coverage and measured button centering. No game capture claim.
fp=rt/'NightRemasterFont.fnl';raw=fp.read_bytes();_,faces=parse_fnl_font(fp,3);table={};q=20
for fontno in range(struct.unpack_from('<I',raw,16)[0]):
 nf=struct.unpack_from('<I',raw,q)[0];q+=4
 for fi in range(nf):
  h,u,n=struct.unpack_from('<III',raw,q);q+=12
  if fontno==3:table[fi]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(n)])
  q+=10*n
proxy={c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()};checked=set();widths=[]
def width(text,size):
 face,den,_=select_fnl_face(faces,size);wm=WidthMeasurer(face,den,proxy,0,0,0)
 for ch in text:
  if ch.isspace():continue
  ix=wm.glyph_index(ch,True);h,entries=table[face.face_index];w,pos,n=entries[ix]
  assert w>0 and pos>0 and n>0 and any(zlib.decompress(raw[pos:pos+n])),(ch,size)
  checked.add((ch,size))
 return max(row['width_px'] for row in wm.measure(text,True)['lines'])
for ix,root,label,budget in [(153,'KR_AutoEquipRoot','KR_AutoEquipButtonLabel',192),(154,'KR_AutoStoneRoot','KR_AutoStoneButtonLabel',138)]:
 p=part(docs[ix],label);info=child(p,'種類別情報');txt=next(c for c in info.children if c.name.value.decode('cp932')=='テキスト情報') if False else None
 from build_remaster_multiplier_20260915 import txt_info
 t=decode(val(txt_info(p),'テキスト').value);w=width(t,21);x,y,z=coords(p);assert abs(x+w/2-budget/2)<=0.01 and w<=budget-12
 rr=part(docs[ix],root);rx,ry,rz=coords(rr);assert 160+rx+budget<=1280 and ry+42<=720
 widths.append(dict(name=label,text=t,width=w,container=budget,center_error=abs(x+w/2-budget/2)))
jaf=(O/'helpers.jaf').read_text(encoding='utf8');text_literals=[json.loads(z) for z in re.findall(r'"(?:[^"\\]|\\.)*"',jaf) if any('\uac00'<=c<='\ud7a3' for c in z)]
for s in text_literals:
 s=s.replace('%d','99999').replace('%s','장비');assert width(s,20)<=1050,(s,width(s,20))
items=ex.decode_ex(rt/'NightRemasterEX.ex').blocks[48].payload.rows;names_ko=[decode(r[2].payload.value) for r in items]
longest=max(names_ko,key=lambda x:width(x,20));worst=f'4번: {longest} → {longest}';assert width(worst,20)<=1050
v=json.loads((O/'verification.json').read_text());assert v['status']=='COMPILED_FIXTURES_PASS' and v['files']==ev['files']
report=dict(status='RELEASE_STATIC_PASS',files=ev['files'],original_pact_subtrees_exact=True,changed_archive_entries=changed,unchanged_callbacks=len(lambdas),original_enum83_absent=True,native_font_glyph_states=len(checked),button_widths=widths,max_preview_width=width(worst,20),native_gameplay_verified=False)
savej(O/'release_checks.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
