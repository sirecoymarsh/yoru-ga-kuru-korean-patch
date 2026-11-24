"""Isolated, character-preserving common-rule layout candidate."""
import collections,json,os,re,shutil,struct,sys,zlib
from pathlib import Path
import polish_translation_20260917 as p
sys.stdout.reconfigure(encoding='utf-8')
trial=p.WORK/'global_lineflow_trial';trial.mkdir(exist_ok=True)
source=p.WORK/'output/NightRemaster.ain';frozen=source.read_bytes()
plain,start,end,raw=p.raw_messages(frozen)
proxy=p.readj(p.INPUT/'proxy.json')
forward={x['unicode_character']:x['proxy_character'] for x in proxy['mapping']};reverse={v:k for k,v in forward.items()}
decode=lambda b:''.join(reverse.get(c,c) for c in b.decode('cp932'))
old=[decode(b) for b in raw];edits=p.readj(p.WORK/'global_lineflow_dry_run_map.json');report=p.readj(p.WORK/'global_lineflow_dry_run.json')
newraw=list(raw)
for k,t in edits.items():
 i=int(k);newraw[i]=''.join(forward.get(c,c) for c in t).encode('cp932');assert decode(newraw[i])==t
 assert re.findall(r'[\x00-\x1f\x7f]',old[i])==re.findall(r'[\x00-\x1f\x7f]',t)
 assert old[i].count('료　　　　')==t.count('료　　　　')
for r in report['records']:
 a=''.join(old[i] for i in r['ids']);b=''.join(decode(newraw[i]) for i in r['ids'])
 assert re.sub(r'\s','',a)==re.sub(r'\s','',b)
body=b''.join(struct.pack('<I',len(b))+bytes((c+n+0x60)&255 for n,c in enumerate(b)) for b in newraw)
outplain=plain[:start+12]+body+plain[end:];packed=zlib.compress(outplain,9)
packed=frozen[:8]+struct.pack('<II',len(outplain),len(packed))+packed
check,s,e,out=p.raw_messages(packed)
assert len(out)==len(raw)==100944
assert check[:s+12]==plain[:start+12] and check[e:]==plain[end:]
assert {i for i,(a,b) in enumerate(zip(raw,out)) if a!=b}==set(map(int,edits))
output=trial/'NightRemaster.ain';output.write_bytes(packed)
runtime=trial/'runtime';runtime.mkdir(exist_ok=True)
source_run=p.WORK/'runtime'
for src in source_run.rglob('*'):
 rel=src.relative_to(source_run);dest=runtime/rel
 assert not src.is_symlink()
 if src.is_dir():dest.mkdir(exist_ok=True);continue
 if dest.exists():continue
 if src.stat().st_size>20_000_000:os.link(src,dest)
 else:shutil.copy2(src,dest)
shutil.copy2(output,runtime/'NightRemaster.ain')
ini=runtime/'AliceStart.ini';text=ini.read_text(encoding='cp932')
text,n=re.subn(r'SaveFolder\s*=\s*"[^"]+"','SaveFolder = "SaveData_KR_Lineflow_Test_20260917"',text);assert n==1
ini.write_text(text,encoding='cp932',newline='')
p.writej(trial/'manifest.json',{'status':'static_pass_native_pending','source_polish_sha256':p.sha(frozen),'ain_sha256':p.sha(packed),'layout_changed_fields':len(edits),'layout_changed_pages':len(report['records']),'empty_tail_pages':report['counts']['pages_with_empty_tail'],'outside_MSG1_exact':True,'page_text_except_whitespace_exact':True,'MSG_count':len(raw),'font_sha256':p.sha((p.INPUT/'font.fnl').read_bytes()),'runtime':str(runtime),'translator_model':'Codex internal','operation':'Deterministic layout only; no semantic translation','live_install':False})
print('trial',runtime,'sha256',p.sha(packed))
