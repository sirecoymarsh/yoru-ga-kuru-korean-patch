"""Preserve AFA3 and all original logical IDs; append uniquely named caption assets.

Existing encrypted names/dictionary and unknown fields are retained bit-for-bit.
Only count, data offsets/sizes and the appended records are rewritten.
"""
from pathlib import Path
import json,hashlib,struct,zlib,sys
from ui_container_tools_20260912 import R,O
sys.path.insert(0,str(O/'work'))
from afa3_inplace import BitStream,BitWriter,Rnd521,read_afa3,_read_layout,_read_dict,_patch_u32le_bits

def h(b):return hashlib.sha256(b).hexdigest()

def rebuild(source,output,replacements=None,append=None):
 replacements=replacements or {};append=append or []
 assert source.resolve()!=output.resolve()
 data,ar,body,prefix_bits,metadata,positions=_read_layout(source)
 outer=BitStream(body);outer.read_bits(1);dictionary=_read_dict(outer)
 lookup={v^0xa4:i for i,v in reversed(list(enumerate(dictionary)))}
 assert max(lookup.values())<65536
 names={e.name for e in ar.entries};assert set(replacements)<=set(range(len(ar.entries)))
 for name,payload in append:
  assert name not in names;names.add(name);assert all(c in lookup for c in name.encode('cp932'))
 payloads=[Path(replacements[e.no]).read_bytes() if e.no in replacements else data[e.absolute_offset:e.absolute_offset+e.size] for e in ar.entries]
 cursor=0
 for e,(offpos,sizepos),payload in zip(ar.entries,positions,payloads):
  _patch_u32le_bits(metadata,offpos,cursor);_patch_u32le_bits(metadata,sizepos,len(payload));cursor+=len(payload)
 _patch_u32le_bits(metadata,1,len(ar.entries)+len(append))
 inner=BitWriter();inner.copy_bits(metadata,0,positions[-1][1]+32)
 for name,path in append:
  raw=name.encode('cp932');inner.write_bits(0,2);inner.write_u32le(len(raw));rnd=Rnd521(len(raw))
  for byte in raw:
   padding=(rnd.next()&3)+1;inner.write_bits(0,padding);rnd.next();index=lookup[byte]
   inner.write_bits(index&255,8);inner.write_bits(index>>8,8)
  payload=Path(path).read_bytes()
  for value in [0,0,cursor,len(payload)]:inner.write_u32le(value)
  cursor+=len(payload);payloads.append(payload)
 rawmeta=inner.finish();packed=zlib.compress(rawmeta,9);writer=BitWriter();writer.copy_bits(body,0,prefix_bits)
 writer.write_u32le(len(packed));writer.write_u32le(len(rawmeta));writer.write_bytes(packed);outbody=writer.finish()
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('wb') as f:
  f.write(b'AFAH'+struct.pack('<II',len(outbody)+4,3)+outbody)
  for payload in payloads:f.write(payload)
 reopened=read_afa3(output);newdata=output.read_bytes();assert len(reopened.entries)==len(payloads)
 for e,new in zip(ar.entries,reopened.entries):
  for key in ['no','name','name_raw_hex','unknown0','unknown1']:assert getattr(e,key)==getattr(new,key),(e.no,key)
 for i,(e,payload) in enumerate(zip(reopened.entries,payloads)):
  assert newdata[e.absolute_offset:e.absolute_offset+e.size]==payload,(i,'payload mismatch')
 for i,(name,path) in enumerate(append,len(ar.entries)):assert reopened.entries[i].name==name
 return dict(source_sha256=h(data),candidate_sha256=h(newdata),original_entries_preserved=len(ar.entries),replaced_ids=sorted(replacements),appended=[dict(id=len(ar.entries)+i,name=name,sha256=h(Path(path).read_bytes())) for i,(name,path) in enumerate(append)],wrapper='AFA3',metadata_identity='PASS (names/order/unknown fields)',payload_identity='PASS (all untouched entries and exact replacement bytes)',new_archive=str(output))

def main():
 b=Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_layout_v3_final\runtime_layout_v3\NightRemasterCG.afa')
 out=R/'cg_cumulative';out.mkdir(exist_ok=True)
 # Mandatory no-change roundtrip before appending anything.
 roundtrip=rebuild(b,out/'roundtrip.afa');assert not roundtrip['replaced_ids'] and not roundtrip['appended']
 caption=json.loads((R/'opening_raster/manifest.json').read_text(encoding='utf-8'))
 appended=[(x['cg_name'],Path(x['payload'])) for x in caption['records']]
 result=rebuild(b,out/'NightRemasterCG_captions.afa',append=appended)
 (out/'caption_merge_validation.json').write_text(json.dumps(dict(no_change_roundtrip=roundtrip,cumulative=result),ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
