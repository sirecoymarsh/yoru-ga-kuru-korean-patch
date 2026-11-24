from pathlib import Path
import json,struct,zlib,shutil,os
import build_mod_native_style_20260923 as e
from audit_dynamic_ui_20260915 import encode
D=e.R/'staging/auto_explore_fix_20260923/real_scene_probe'
def main():
    src=e.O/'NightRemaster.ain';m=e.b.read_meta(e.O/'candidate_meta.json')
    raw=zlib.decompress((e.p.SAVE/'NightR36.asd').read_bytes()[8:]);r=e.q.Reader(raw);r.string();r.integer();key=r.string()
    jaf=(e.HERE/'mod_style_probe_20260923.jaf').read_text('utf8').replace('@@KEY@@',key).replace('@@CONFIRM@@',encode('요소석 추천 확인').decode('cp932')).replace('@@ACCEPT@@',encode('원작 확인창으로').decode('cp932'))
    (D/'style_probe.jaf').write_text(jaf,'utf8');decl=D/'style_declared.ain';e.b.cmd('ain','edit','--jaf',D/'style_probe.jaf','-o',decl,src)
    e.b.cmd('ain','dump','-j','-o',D/'style_declared_meta.json',decl);dm=e.b.read_meta(D/'style_declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[]
    for f in added:
        p=D/f"style_{f['index']}.jam";e.b.cmd('ain','dump','--function',f['name'],'-o',p,decl);patch.append(e.b.clean(e.b.native_lower(p.read_text('utf8')),f['name']))
    patch.append('FUNC 32051\n\t.LOCALREF scene\n\tCALLFUNC KR_StyleGuard\n\tRETURN\nENDFUNC KR_WalkGuard\n')
    wait=next(f for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick')
    (D/'style_probe.jam').write_text('\n'.join(patch),'utf8');out=D/'NightRemaster.ain';e.b.cmd('ain','edit','--jam',D/'style_probe.jam','-o',out,decl)
    raw=bytearray(e.b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);struct.pack_into('<I',raw,raw.index(b'MAIN')+4,ids['KR_StyleMain'])
    focus=next(x for x in e.b.a.readj(e.O/'build_evidence.json')['AIN']['in_place_instructions'] if x['fid']==27928)
    off=16+focus['address'];assert raw[off:off+6].hex()==focus['after'];struct.pack_into('<Hi',raw,off,0x30,ids['KR_StyleDefault'])
    start=m['functions'][27928]['address'];end=min(f['address'] for f in m['functions'] if f['address']>start)
    pattern=struct.pack('<Hi',0x30,wait['index']);body=raw[16+start:16+end];assert body.count(pattern)==1
    struct.pack_into('<Hi',raw,16+start+body.index(pattern),0x30,ids['KR_StyleWait'])
    out.write_bytes(e.b.pack(raw,src.read_bytes()[:8]))
    # Replace links atomically: never mutate shared diagnostic/source archive in-place.
    for n in ['NightRemasterPact.afa','NightRemasterCG.afa']:
        tmp=D/(n+'.style_copy');shutil.copy2(e.O/n,tmp);os.replace(tmp,D/n)
    e.save('native_probe_manifest.json',dict(source_sha256=e.h(src),probe_sha256=e.h(out),candidate_files={n:e.h(e.O/n) for n in e.FILES},runtime=str(D),scope='Copied dungeon save; actual native PACT/CG loader, display, choice construction. WaitForClick returns diagnostic test IDs; no user input injection; no reward or synthesis execution.'))
    print('READY',D)
if __name__=='__main__':main()
