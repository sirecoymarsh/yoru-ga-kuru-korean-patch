from pathlib import Path
import re,json,subprocess,hashlib
from integrate_ui_opening_20260913 import read_meta
from build_remaster_multiplier_20260915 import cmd,fn,f32
from audit_dynamic_ui_20260915 import R,encode,decode

O=Path('cheat_menu_20260915'); O.mkdir(exist_ok=True)
SRC=Path('consume_saved_display_20260915/NightRemaster.ain')
M=read_meta(Path('consume_saved_display_20260915/candidate_meta.json'))
names={}; counts={}
for f in M['functions']:
 n=f['name'];n=n.encode('utf8','surrogateescape').decode('cp932') if any(0xdc80<=ord(c)<=0xdcff for c in n) else n
 ix=counts.get(n,0);counts[n]=ix+1;names[f['index']]=n+(f'#{ix}' if ix else '')
def dump(fid):
 p=O/f'original_{fid}.jam'
 if not p.exists():cmd('ain','dump','--function',names[fid],'-o',p,SRC)
 s=p.read_text(encoding='utf8');assert s.strip(),fid
 return s
def refs(fid):
 s=dump(fid)
 def rep(mt):
  i=int(mt[1]);return mt[0]+(' ; '+names[i] if i in names and i>25000 else '')
 return re.sub(r'PUSH (\d+)',rep,s)
def savej(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
 import sys
 for fid in map(int,sys.argv[1:]):print(refs(fid))
