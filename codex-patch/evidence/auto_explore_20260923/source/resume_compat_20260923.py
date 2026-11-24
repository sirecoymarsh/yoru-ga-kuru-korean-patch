"""Read-only RSM14 return-record audit and exact-version compatibility inputs.
Header layout checked against actual RSM14 saves; never rewrites saves.
Reference: nunuhara/libsys4/src/savefile.c (RSM9 prefix, no uk1 field in RSM14).
"""
from pathlib import Path
import collections,difflib,hashlib,json,re,struct,zlib
import build_term_switch_20260923 as b
from publish_cheat_menu_20260915 import SAVE
R=b.R;O=R/'staging/load_error_20260923';BASE=R/'staging/player_tools_20260923'
EXPECTED='769d461aa51037eae34d48f7b15125ba6e8a4ae83126b17fb7b848ab41f9184c'
def save(name,data):(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
class Reader:
 def __init__(self,data):self.data=data;self.p=0
 def integer(self):
  v=struct.unpack_from('<i',self.data,self.p)[0];self.p+=4;return v
 def string(self):
  end=self.data.index(b'\0',self.p);v=self.data[self.p:end].decode('cp932');self.p=end+1;return v
 def array(self):
  n=self.integer();assert 0<=n<5000;return [self.integer() for _ in range(n)]
 def record(self):
  address=self.integer()
  if address==-1:return dict(address=address)
  return dict(address=address,name=self.string(),offset=self.integer(),crc=self.integer()&0xffffffff)
def records(path):
 raw=path.read_bytes();assert raw[:4]==b'GD\x01\x01'
 data=zlib.decompress(raw[8:]);assert len(data)==struct.unpack_from('<I',raw,4)[0]
 if not data.startswith(b'RSM\0'):return None
 q=Reader(data);assert q.string()=='RSM' and q.integer()==14
 key=q.string();comments=[q.string() for _ in range(q.integer())];ip=q.record()
 stack=q.array();locals_=q.array();types=q.array();structs=q.array();assert len(locals_)==len(types)
 n=q.integer();assert n in (len(locals_),len(locals_)-1) and 0<n<200
 rr=[q.record() for _ in range(n)];assert rr[0]['address']==-1
 return dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),ip=ip,returns=rr,header_end=q.p,types=types,locals=locals_,structs=structs)
def versions(path):
 out=collections.defaultdict(list);last=0;active=None
 for line in path.read_text('utf8').splitlines():
  if line.startswith('FUNC '):
   fid=int(line.split()[1]);active=dict(start=last+6,ops=[]);out[fid].append(active);continue
  z=re.match(r'0x([0-9A-Fa-f]+):\s*(.*)',line)
  if z:
   last=int(z[1],16)
   if z[2] and active is not None:active['ops'].append((last,z[2]))
 return out
def norm(op):return re.sub(r'^(JUMP|IFZ|IFNZ) .+',r'\1 TARGET',op)
def main():
 O.mkdir(parents=True,exist_ok=True);ptr=b.a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime'])
 assert b.a.sha(rt/'NightRemaster.ain')==EXPECTED
 m=b.read_meta(BASE/'candidate_meta.json');vs=versions(BASE/'native_raw_code.jam')
 saves=[records(p) for p in SAVE.glob('NightR*.asd') if re.fullmatch(r'NightR\d+\.asd',p.name)];assert len(saves)==37
 mapping={};sites=[];aliases=collections.defaultdict(dict);currents={}
 for row in saves:
  for rr in [row['ip']]+row['returns']:
   if rr['address']==-1:continue
   source_start=rr['address']-rr['offset']
   choices=[(f['index'],v) for f in m['functions'] if rr['name'].startswith(b.raw_symbol(m,f['index'])+'(') for v in vs[f['index']] if v['start']==source_start]
   assert len(choices)==1,(row['file'],rr,choices)
   fid,old=choices[0];f=m['functions'][fid];assert (f['crc']&0xffffffff)==rr['crc']
   current=next(v for v in vs[fid] if v['start']==f['address']);currents[fid]=current
   cachekey=(fid,source_start)
   if cachekey not in mapping:
    blocks=difflib.SequenceMatcher(None,[norm(op) for _,op in old['ops']],[norm(op) for _,op in current['ops']],autojunk=False).get_matching_blocks()
    mapping[cachekey]={i:(j+i-start,size) for start,j,size in blocks for i in range(start,start+size)}
   idx=next(i for i,(ad,op) in enumerate(old['ops']) if ad==rr['address']);j,block=mapping[cachekey][idx]
   assert block>=8 or old['ops']==current['ops'],(fid,rr,block)
   target=current['ops'][j][0];target_offset=target-current['start']
   # Require an unchanged immediate return boundary, not merely the same opcode.
   assert [norm(x[1]) for x in old['ops'][max(0,idx-1):idx+3]]==[norm(x[1]) for x in current['ops'][max(0,j-1):j+3]],(fid,rr)
   site=dict(save=row['file'],fid=fid,name=rr['name'],source_start=source_start,saved_address=rr['address'],saved_offset=rr['offset'],current_start=current['start'],target=target,target_offset=target_offset,matching_block_instructions=block,opcode=current['ops'][j][1])
   sites.append(site)
   if rr['offset']!=target_offset:
    prior=aliases[fid].get(rr['offset']);assert prior is None or prior==target_offset
    aliases[fid][rr['offset']]=target_offset
 # For every changed function, also preserve all return sites actually stored by
 # current saves even if they happened not to move before this compatibility shim.
 for site in sites:
  fid=site['fid']
  if fid in aliases:
   prior=aliases[fid].get(site['saved_offset']);assert prior is None or prior==site['target_offset']
   aliases[fid][site['saved_offset']]=site['target_offset']
 for fid,entries in aliases.items():
  offsets=sorted(entries);assert min(offsets)>=6 and all((a%2)==0 for a in offsets)
  assert all(z-a>=6 for a,z in zip(offsets,offsets[1:]))
 save('source_pointer.json',ptr);save('save_inventory.json',saves);save('resume_sites.json',sites)
 save('resume_aliases.json',{str(fid):{str(k):v for k,v in entries.items()} for fid,entries in aliases.items()})
 print('functions',[(i,b.raw_symbol(m,i),{hex(k):hex(v) for k,v in a.items()}) for i,a in aliases.items()]);print('saves',len(saves),'frames',len(sites))
if __name__=='__main__':main()
