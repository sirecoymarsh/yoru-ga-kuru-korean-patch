"""Native saved-scene click callback inspection; no installation or source-save writes."""
from pathlib import Path
import struct,json,zlib,sys
import build_auto_explore_20260923 as e
from build_dungeon_sweep_20260916 import push,cf,lr,cm,assign,field

D=e.R/'staging/auto_explore_fix_20260923/real_scene_probe'
def main():
    src=e.O/'NightRemaster.ain';m=e.b.read_meta(e.O/'candidate_meta.json')
    if len(sys.argv)>1: src=Path(sys.argv[1]);m=e.b.read_meta(src.parent/'candidate_meta.json')
    saved=e.q.records(e.p.SAVE/'NightR36.asd')
    raw=zlib.decompress((e.p.SAVE/'NightR36.asd').read_bytes()[8:]);rd=e.q.Reader(raw);rd.string();rd.integer();key=rd.string()
    visible='KR_ExploreVisibleBound' if any(f['name']=='KR_ExploreVisibleBound' for f in m['functions']) else 'KR_ExploreVisible'
    jaf=(e.HERE/'walk_click_probe_20260923.jaf').read_text('utf-8').replace('@@KEY@@',key).replace('@@VISIBLE@@',visible)
    (D/'click_probe.jaf').write_text(jaf,'utf-8');decl=D/'click_declared.ain';e.b.cmd('ain','edit','--jaf',D/'click_probe.jaf','-o',decl,src)
    e.b.cmd('ain','dump','-j','-o',D/'click_declared_meta.json',decl);dm=e.b.read_meta(D/'click_declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
    def bind(fn,name,expr):
        f=dm['functions'][ids[fn]];return assign(next(i for i,v in enumerate(f['arguments']+f['variables']) if v['name']==name),expr)
    p=D/'visible_template.jam';e.b.cmd('ain','dump','--function','KR_ExploreRawVisible','-o',p,src)
    t=e.b.clean(p.read_text('utf-8'),'KR_ExploreRawVisible').split('FUNC 32183\n',1)[1].split('ENDFUNC ',1)[0]
    t=t.replace('S_PUSH "KR_WalkRoot"', 'LOCALREF key')
    t=t.replace('LOCALREF key','.LOCALREF key')
    t=t.replace('\tPUSH 60\n','\tPUSH 31\n').replace('\t.LOCALREF show\n\tCALLMETHOD 1\n','\tCALLMETHOD 0\n\tPUSHLOCALPAGE\n\tPUSH 2\n\tX_MOV 3 2\n\tX_ASSIGN 1\n\tPOP\n')
    t=t.replace('\tRETURN\n',lr('number')+'\tRETURN\n')
    s=lr('number')+'\tCALLHLL PartsEngine GetDelegateIndex 0\n'+push(-1)+'\tEQUALE\n\tIFNZ empty_handlers\n'
    s+=bind('KR_ClickHandlers','set',cm('\t.GLOBALREF parts::detail::g_PartsMessageManager\n',8734,lr('number'),1))
    s+=field(lr('set'),13)+push(0)+'\tNOTE\n\tIFNZ empty_handlers\n'
    s+=bind('KR_ClickHandlers','count',field(lr('set'),12)+'\tCALLHLL Delegate Numof 0\n')
    s+=lr('dispatch')+'\tIFZ no_dispatch\n'+cm(lr('set'),8697,push(0)+push(0)+push(1),3)
    s+='no_dispatch:\n\t.LOCALDELETE set\n'+lr('count')+'\tRETURN\nempty_handlers:\n\t.LOCALDELETE set\n'+push(0)+'\tRETURN\n'
    bridges={'KR_ClickPart':t,'KR_ClickHandlers':s,'KR_ClickResult':'\tPUSHGLOBALPAGE\n\tPUSH 3\n\tX_REF 1\n\tRETURN\n'};patch=[]
    for f in added:
        n=f['name'];fid=f['index'];path=D/f'click_{fid}.jam';e.b.cmd('ain','dump','--function',n,'-o',path,decl)
        body=e.b.clean(e.b.native_lower(path.read_text('utf-8')),n)
        if n in bridges: body=f'FUNC {fid}\n'+bridges[n]+f'ENDFUNC {n}\n'
        patch.append(body)
    patch.append('FUNC 32030\n'+lr('scene')+lr('show')+cf('KR_ClickVisible')+'\tRETURN\nENDFUNC KR_WalkVisible\n')
    patch.append('FUNC 32051\n'+lr('scene')+cf('KR_ClickGuard')+'\tRETURN\nENDFUNC KR_WalkGuard\n')
    mode=1 if '--on' in sys.argv else 0
    patch.append('FUNC 31847\n'+push(mode)+'\tRETURN\nENDFUNC KR_GetRoute\n')
    (D/'click_probe.jam').write_text('\n'.join(patch),'utf-8');out=D/'NightRemaster.ain';e.b.cmd('ain','edit','--jam',D/'click_probe.jam','-o',out,decl)
    raw=bytearray(e.b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);struct.pack_into('<I',raw,raw.index(b'MAIN')+4,ids['KR_ClickProbeMain']);out.write_bytes(e.b.pack(raw,src.read_bytes()[:8]))
    (D/'click_probe_manifest.json').write_text(json.dumps(dict(source=str(src),source_sha256=e.b.a.sha(src),probe_sha256=e.b.a.sha(out),guide_mode=mode,save_slot='NightR36.asd',initialization='PassRegister handles 0, 1, 2 only; native saved scene',input='native CallFunctionMouseClick dispatch; not OS mouse hit testing'),indent=2),encoding='utf-8')
    print('READY',e.b.a.sha(out),ids)

if __name__=='__main__': main()
