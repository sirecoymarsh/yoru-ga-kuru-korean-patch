"""Exact compiled planners, native map fixtures, saved frames and native evidence."""
from pathlib import Path
import collections,copy,json,re,struct,sys
import build_event_navigation_20260926 as e
import verify_route_linear_20260916 as L

def static():
    m=e.b.read_meta(e.O/'candidate_meta.json');oldm=e.b.read_meta(e.S/'candidate_meta.json');ev=e.a.readj(e.O/'build_evidence.json')
    src=e.S/'NightRemaster.ain';out=e.O/'NightRemaster.ain'
    assert e.h(out)==ev['files']['NightRemaster.ain']
    old=e.b.unpack(src.read_bytes());new=e.b.unpack(out.read_bytes());size=struct.unpack_from('<I',old,12)[0]
    assert old[16:16+size]==new[16:16+size]
    for key in oldm:
        if key!='functions':assert oldm[key]==m[key],key
    for f,g in zip(oldm['functions'],m['functions']):
        cmp=dict(f)
        if f['index'] in ev['relocated']:cmp['address']=g['address']
        assert cmp==g
    assert ev['relocated']==[31908,31909,32027]
    deps=['KR_DrawRoute','KR_DrawRouteLinear','KR_WalkPlanLinear','KR_RouteCellLinear','KR_RouteAppendLinear','KR_EventRouteOrdered','KR_EventRouteTag','KR_GetRoute','KR_InitOptions','KR_Flag','KR_Poke']
    for name in deps:
        fid=next(f['index'] for f in m['functions'] if f['name']==name)
        (e.O/f'built_{fid}.jam').write_text(e.textdump(m,fid,out),'utf8')
    L.META=m;L.ns['O']=e.O;L.ns['read_meta']=lambda path:m
    root=e.n.ex.decode_ex(e.O/'NightRemasterEX.ex').blocks[2].payload;maps={}
    for t in root.children:
        mid=int(t.name.value);data={c.name.value.decode('cp932'):[struct.unpack('<i',i.value.payload.raw)[0] for i in c.leaf_value.payload.items] for c in t.children}
        maps[mid]=L.Map(mid,L.native_map(data['地面データ'],data['置物データ'],mid))
    def expected(mp,start):
        if mp.map_id not in e.MAPS:return L.expected(mp,start)
        target=(6,0)
        if mp.map_id in [101,605] and any(c==(7,0) and p not in mp.removed for p,c in mp.items()):target=(7,0)
        q=collections.deque([start]);dist={start:0}
        while q:
            x,y=q.popleft()
            for v in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if 0<=v[0]<30 and 0<=v[1]<30 and v not in dist and L.walk(mp,v):dist[v]=dist[x,y]+1;q.append(v)
        candidates=[(dist[p],p[1]*30+p[0],p) for p,c in mp.items() if c==target and p not in mp.removed and dist.get(p,0)>0]
        return min(candidates)[::2] if candidates else (0,None)
    rows=[]
    def check(mp,start,label,nonempty=False):
        vm=L.VM();vm.flags[84]=20260915;vm.flags[93]=1;view={};saved=copy.deepcopy(mp);flags=list(vm.flags)
        vm.run('KR_DrawRoute',[mp,view,*start]);path=view['drawn'];length,target=expected(mp,start)
        assert len(path)==length and (path[-1] if path else None)==target,(label,path,length,target)
        if nonempty:assert path,label
        prev=start
        for point in path:assert abs(point[0]-prev[0])+abs(point[1]-prev[1])==1 and L.walk(mp,point);prev=point
        assert mp==saved and mp.removed==saved.removed and not vm.owned
        assert all(vm.flags[i]==flags[i] for i in range(101) if i not in [85,86,89])
        reads=vm.count[27082];assert reads==900
        for _ in range(100):vm.run('KR_DrawRoute',[mp,view,*start])
        assert vm.count[27082]==reads,'stationary frames rescanned grid'
        route=[];snapshot=list(vm.flags);vm.run('KR_WalkPlanLinear',[mp,view,*start,mp.map_id,route])
        assert route==path and vm.flags==snapshot and not vm.owned
        rows.append(dict(case=label,map=mp.map_id,start=start,goal=target,length=length,path=path,grid_reads=reads,guide_equals_movement=True))
    for mid in e.MAPS:
        mp=copy.deepcopy(maps[mid]);start=next((p for p,c in mp.items() if c==(2,2)),next(p for p,c in mp.items() if c==(0,0)))
        if mid==605:start=(1,14)
        check(mp,start,f'{mid} original map first target',True)
        if mid in [101,605]:
            mp.removed.update(p for p,c in mp.items() if c==(7,0))
            check(mp,start,f'{mid} B1 completed, now R1',True)
        mp.removed.update(p for p,c in mp.items() if c==(6,0))
        check(mp,start,f'{mid} completed targets excluded')
    for mid in [201,202,203,204,301,302,501,502,601,603,801,802,901,902,903,904,905,906,907,910]:
        mp=maps[mid];start=next((p for p,c in mp.items() if c==(2,2)),next(p for p,c in mp.items() if c==(0,0)))
        check(mp,start,f'{mid} unchanged ordinary/department selector')
    for mid in [101,605]:
        mp=L.Map(mid,{(x,y):(0,0) for y in range(5) for x in range(5)});mp[1,0]=(6,0);mp[4,4]=(7,0)
        check(mp,(0,0),f'{mid} distant B1 before nearby R1',True)
        for pos in [(3,4),(4,3)]:mp[pos]=(1,0)
        check(mp,(0,0),f'{mid} unreachable prerequisite fails closed')
    mp=L.Map(1001,{(i,0):(0,0) for i in range(5)});mp[4,0]=(2,1);check(mp,(0,0),'ordinary random dungeon',True)
    mp=L.Map(999,{(i,0):(0,0) for i in range(5)});mp[4,0]=(6,0);check(mp,(0,0),'unknown event does not become an exit')
    # Body identities plus metadata preserve existing story actions, puzzles and controls.
    names=['KR_ExploreGate','KR_ExplorePlan','KR_ExploreStart','KR_WalkPathValid','KR_WalkCommit','KR_DrawPuzzleRoute','KR_WalkPlanPuzzle','KR_PuzzleReadState']
    for name in names:
        fid=next(f['index'] for f in m['functions'] if f['name']==name);assert m['functions'][fid]==oldm['functions'][fid]
    oldvs=e.q.versions(e.S/'native_raw_code.jam');sig=collections.defaultdict(list)
    for f in oldm['functions']:sig[f['crc']&0xffffffff].append(f)
    before=e.p.snapshot_saves();saves=[];frames=[]
    for path in sorted(e.p.SAVE.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
        data=e.q.records(path);saves.append(path.name)
        for rec in [data['ip']]+data['returns']:
            if rec['address']==-1:continue
            choices=[f for f in sig[rec['crc']] if rec['name'].startswith(e.b.raw_symbol(oldm,f['index'])+'(') and any(v['start']==rec['address']-rec['offset'] for v in oldvs[f['index']])]
            assert len(choices)==1,(path,rec)
            f=choices[0];assert f['index'] not in ev['relocated'];assert m['functions'][f['index']]==f
            ad=f['address']+rec['offset'];assert old[16+ad:18+ad]==new[16+ad:18+ad]
            frames.append(dict(save=path.name,fid=f['index'],offset=rec['offset']))
    assert before==e.p.snapshot_saves()
    for name in ['NightRemasterPact.afa','NightRemasterEX.ex']:assert e.h(e.S/name)==e.h(e.O/name)
    e.save('save_frames.json',dict(saves=saves,frames=frames));e.save('map_checks.json',rows)
    result=dict(status='EVENT_NAVIGATION_STATIC_PASS',files=ev['files'],existing_resume_saves=len(saves),saved_return_frames=len(frames),save_schema_equal=True,old_CODE_allowlist_exact=True,changed_PACT=[],map_cases=len(rows),real_saves_unchanged=True,OS_mouse_hit_test=False)
    e.save('verification.json',result);print('STATIC PASS',len(rows),'maps/states,',len(saves),'saves',len(frames),'frames')

def finish():
    qa=e.a.readj(e.O/'verification.json');paths={}
    for path in sorted(e.O.glob('probe_*/result.json')):
        row=e.a.readj(path);log=row.get('log',[])
        if row.get('exit_code')!=0:continue
        manifest=e.a.readj(path.parent/'weapon_probe_manifest.json')
        assert manifest['source_sha256']==qa['files']['NightRemaster.ain']
        assert manifest['probe_sha256']==row['ain_sha256']==e.h(path.parent/'NightRemaster.ain')
        assert not any(row.get(k) for k in ['timeout','message','vm_error','events']) and row['real_saves_unchanged']
        assert not any('FAIL' in x for x in log)
        if row['save']=='NightR45.asd' and 'START_GUIDED=1 queue=2' in log and 'GUIDED=2 valid=1' in log:paths['45-start']=str(path)
        if 'PASS native movement reached original story; no dialogue/party choice answered' in log:paths['45-native-story']=str(path)
        if any(x.startswith('CONTINUED ON NEW FLOOR') for x in log):paths['36-floor']=str(path)
    assert set(paths)=={'45-start','45-native-story','36-floor'},paths
    qa.update(status='EVENT_NAVIGATION_STATIC_NATIVE_PASS',native_probes=paths);e.save('verification.json',qa);print('FINAL PASS',paths)
if __name__=='__main__':finish() if '--finish' in sys.argv else static()
