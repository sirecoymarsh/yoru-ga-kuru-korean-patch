from pathlib import Path
import struct,json,zlib,sys,shutil,os
import build_mod_native_style_20260923 as e
import diagnostic_audio_20260923 as audio
from build_dungeon_sweep_20260916 import push,cf,lr,field
D=e.R/'staging/auto_explore_fix_20260923/real_scene_probe'
def main():
    src=Path(sys.argv[1]) if len(sys.argv)>1 else e.O/'NightRemaster.ain';m=e.b.read_meta(src.parent/'candidate_meta.json')
    raw=zlib.decompress((e.p.SAVE/'NightR36.asd').read_bytes()[8:]);r=e.q.Reader(raw);r.string();r.integer();key=r.string()
    jaf=(e.HERE/'weapon_cancel_probe_20260923.jaf').read_text('utf8').replace('@@KEY@@',key)
    jaf=audio.JAF+'\n'+jaf.replace('int KR_WeaponProbeMain() {','int KR_WeaponProbeMain() {\n    KR_DiagnosticMute();')
    if '--control' in sys.argv:jaf=jaf.replace('if(count==0) return 701;','if(count==0) return 102;')
    if '--prefs' in sys.argv:jaf=jaf.replace('C_SceneHomebaseView home;','KR_WeaponPrefsProbe();\n    C_SceneHomebaseView home;')
    if '--prefs-reload' in sys.argv:jaf=jaf.replace('C_SceneHomebaseView home;','KR_WeaponPrefsReload();\n    C_SceneHomebaseView home;')
    if '--result' in sys.argv:jaf=jaf.replace('C_SceneHomebaseView home;','KR_WeaponResultProbe(scene);\n    C_SceneHomebaseView home;')
    input_pairs={}
    if '--input-domain' in sys.argv:
        from audit_dynamic_ui_20260915 import ENC
        checks=[]
        cases=[c for c in ENC if len(c)==1 and '\uac00'<=c<='\ud7a3']+['료료료료료','료 A12','료료료료료료',' Ryo','Ryo ','Ryo12','?','']
        for i,c in enumerate(cases):
            r=f'RAW_INPUT_{i:05d}';p=f'PROXY_INPUT_{i:05d}';input_pairs[r.encode()]=c.encode('cp949');input_pairs[p.encode()]=e.encode(c)
            checks.append(f'if(KR_KoreanInputEncode("{r}")!="{p}") {{ KR_WeaponProbeLog("FAIL input {i}");system.Exit(30); }}')
        checks.append(f'KR_WeaponProbeLog("PASS native input conversion {len(cases)} cases");')
        jaf=jaf.replace('/*INPUT_DOMAIN_CHECK*/','\n'.join(checks))
    if any(f['name']=='KR_KoreanInputEncode' for f in m['functions']):
        jaf=jaf.replace('/*INPUT_FIXED_CHECK*/','string converted=KR_KoreanInputEncode(raw); if(converted!=proxy || !KR_PlayerNameValid(converted)) { KR_WeaponProbeLog("FAIL raw input conversion");system.Exit(21); } KR_WeaponProbeLog("PASS raw input converted to valid Ryo");')
    (D/'weapon_probe.jaf').write_text(jaf,'utf8');decl=D/'weapon_declared.ain'
    e.b.cmd('ain','edit','--jaf',D/'weapon_probe.jaf','-o',decl,src)
    e.b.cmd('ain','dump','-j','-o',D/'weapon_declared_meta.json',decl);dm=e.b.read_meta(D/'weapon_declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    for f in added:
        p=D/f"weapon_{f['index']}.jam";e.b.cmd('ain','dump','--function',f['name'],'-o',p,decl);body=e.b.clean(e.b.native_lower(p.read_text('utf8')),f['name'])
        if f['name']=='KR_WeaponProbeState':body=f"FUNC {f['index']}\n"+field(lr('scene'),2)+lr('label')+cf('KR_WeaponProbeView')+'\tRETURN\nENDFUNC KR_WeaponProbeState\n'
        if f['name']=='KR_WeaponByte':body=f"FUNC {f['index']}\n"+lr('text')+lr('index')+'\tC_REF\n\tRETURN\nENDFUNC KR_WeaponByte\n'
        if f['name']=='KR_WeaponHideDungeon':
            s=next(s for s in m['structures'] if s['name']=='C_SceneDungeon');ix=next(i for i,v in enumerate(s['members']) if v['name']=='m_DungeonView')
            body=f"FUNC {f['index']}\n"+field(lr('scene'),ix)+push(28739)+'\tCALLMETHOD 0\n\tRETURN\nENDFUNC KR_WeaponHideDungeon\n'
        if f['name']=='KR_WeaponProbeGuard':
            ix=next(i for i,v in enumerate(f['arguments']+f['variables']) if v['name']=='sub')
            body=body.replace(cf('KR_WeaponProbeBind'),'\tNEW C_SceneSubWeapon 28579\n\tPUSHLOCALPAGE\n'+push(ix)+'\tX_MOV 3 2\n\tX_ASSIGN 1\n\tPOP\n')
        patch.append(body)
    patch.append('FUNC 32051\n'+lr('scene')+cf('KR_WeaponProbeGuard')+'\tRETURN\nENDFUNC KR_WalkGuard\n')
    for fid,mark in [(28583,'mode_loop'),(28509,'begin_memory'),(28576,'end_weapon'),(28499,'destroy_weapon_view'),(28469,'destroy_memory_view')]:
        p=D/f'weapon_original_{fid}.jam';e.b.cmd('ain','dump','--function',e.b.symbol(m,fid),'-o',p,src);body=e.b.clean(p.read_text('utf8'),e.b.symbol(m,fid))
        call='\tS_PUSH "'+mark+'"\n'+cf('KR_WeaponProbeLog')
        patch.append(body.replace(f'FUNC {fid}\n',f'FUNC {fid}\n'+call))
    if '--no-mod-ui' in sys.argv:patch.append('FUNC 31919\n\tRETURN\nENDFUNC KR_AutoStoneVisible\n')
    if '--old-mod-ui' in sys.argv:
        p=D/'visibility_before_graphics.jam';e.b.cmd('ain','dump','--function','KR_AutoStoneVisible','-o',p,src)
        body=e.b.clean(p.read_text('utf8'),'KR_AutoStoneVisible')
        needle=lr('view')+lr('show')+cf('KR_ModStoneGraphics');assert body.count(needle)==1
        patch.append(body.replace(needle,''))
    if '--fix-key' in sys.argv:
        p=D/'stonepart_before_keyfix.jam';e.b.cmd('ain','dump','--function','KR_ModStonePart','-o',p,src)
        body=e.b.clean(p.read_text('utf8'),'KR_ModStonePart');needle=lr('key')+'\tCALLMETHOD 1\n';assert body.count(needle)==1
        patch.append(body.replace(needle,lr('key')+'\tA_REF\n\tCALLMETHOD 1\n'))
    (D/'weapon_probe.jam').write_text('\n'.join(patch),'utf8');out=D/'NightRemaster.ain';e.b.cmd('ain','edit','--jam',D/'weapon_probe.jam','-o',out,decl)
    raw=bytearray(e.b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);struct.pack_into('<I',raw,raw.index(b'MAIN')+4,ids['KR_WeaponProbeMain'])
    wait=next(f for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick')['index']
    for fid,helper in [(28585,'Custom'),(28590,'Memory'),(27928,'Dialog')]:
        start=m['functions'][fid]['address'];end=min(f['address'] for f in m['functions'] if f['address']>start)
        # Inline lambdas lie inside the caller: use the next known top-level end instead.
        if fid==28585:end=m['functions'][28586]['address'] if m['functions'][28586]['address']>start else start+4000
        if fid==28590:end=m['functions'][28591]['address']
        pat=struct.pack('<Hi',0x30,wait);body=raw[16+start:16+end];assert body.count(pat)==1,(fid,body.count(pat))
        struct.pack_into('<Hi',raw,16+start+body.index(pat),0x30,ids['KR_WeaponProbe'+helper])
    a,z,strings=e.b.strings(raw)
    for i,s in enumerate(strings):
        if bytes(s) in input_pairs:strings[i]=input_pairs[bytes(s)]
        if s==b'RAW_CP949_RYO':strings[i]='료'.encode('cp949')
        if s==b'PROXY_RYO':strings[i]=e.encode('료')
    raw[a:z]=b'STR0'+struct.pack('<I',len(strings))+b''.join(s+b'\0' for s in strings)
    for f in added:
        for v in f['arguments']+f['variables']:
            if v['name']=='incomes':
                sid=next(i for i,s in enumerate(m['structures']) if s['name']=='S_IncomeCalc')
                start=raw.index(f['name'].encode()+b'\0');off=raw.index(b'incomes\0\0',start)+9
                t=struct.unpack_from('<7i',raw,off)
                if t[0] in (79,80) and t[1]==13:struct.pack_into('<7i',raw,off,t[0],sid,t[2],t[3],t[4],t[5],t[6])
    out.write_bytes(e.b.pack(raw,src.read_bytes()[:8]))
    for n in ['NightRemasterPact.afa','NightRemasterCG.afa']:
        s=src.parent/n
        if not s.exists():s=e.O/n
        t=D/(n+'.weapon_copy');shutil.copy2(s,t);os.replace(t,D/n)
        alias=D/n.replace('NightRemaster','NightRemasterProbe',1)
        if alias.exists():alias.unlink()
        os.link(D/n,alias)
    (D/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(src),source_sha256=e.h(src),probe_sha256=e.h(out),audio=audio.POLICY,input='Only targeted WaitForClick return values are scripted; native recommendation, confirm, tab navigation and cancellation controllers run. Source save copied; no source writes.'),indent=2),'utf8')
    print('READY',e.h(out))
if __name__=='__main__':
    try:main()
    except AssertionError as x:print(str(x)[-2500:]);raise SystemExit(1)
