"""Stage a separate text-only QA fixture in the existing disposable runtime."""
import re,shutil,struct,zlib
import polish_translation_20260917 as p
import publish_cheat_menu_20260915 as tx
W=p.WORK/'page_lineflow_v2'
rt=p.WORK/'runtime'
assert tx.stopped(rt)
packed=(W/'output/NightRemaster.ain').read_bytes()
plain,a,b,raw=p.raw_messages(packed)
out=list(raw)
pairs=[([2234,2235,2236],[2280,2281,2282]),([2242,2243,2244],[22178,22179,22180])]
for dest,source in pairs:
    for d,s in zip(dest,source):out[d]=raw[s]
body=b''.join(struct.pack('<I',len(x))+bytes((c+n+0x60)&255 for n,c in enumerate(x)) for x in out)
qplain=plain[:a+12]+body+plain[b:];z=zlib.compress(qplain,9)
qa=packed[:8]+struct.pack('<II',len(qplain),len(z))+z
Q=W/'qa';Q.mkdir(exist_ok=True)
(Q/'NightRemaster.ain').write_bytes(qa)
shutil.copy2(Q/'NightRemaster.ain',rt/'NightRemaster.ain')
ini=rt/'AliceStart.ini';old=ini.read_bytes()
if not (Q/'previous_test_AliceStart.ini').exists():(Q/'previous_test_AliceStart.ini').write_bytes(old)
data,n=re.subn(rb'SaveFolder\s*=\s*"[^"]+"',b'SaveFolder = "SaveData_KR_Pageflow_V2_Test_20260917"',old);assert n==1
ini.write_bytes(data)
p.writej(Q/'fixture.json',{'runtime':str(rt),'production_ain_sha256':p.sha(packed),'qa_ain_sha256':p.sha(qa),'only_test_MSG_replacements':pairs,'purpose':'Observe unchanged production example strings in early existing three-field Text pages, including empty trailing MSG and backlog. Not a native Face-window test.','save_folder':'SaveData_KR_Pageflow_V2_Test_20260917','live_save_hashes_before':tx.snapshot_saves()})
print(str(rt))
