"""Execute final chest JAM with explicit scene/PartsEngine boundaries."""
from pathlib import Path
import collections,copy,json,re,struct
from cheat_support_20260915 import R,sha,savej,read_meta
from build_route_perf_20260915 import symbol
from build_chest_flow_20260917 import O
from build_remaster_multiplier_20260915 import ex,read_afa3,part,child,val,allparts,txt_info,decode,encode
from build_mod_tab_20260915 import remove,name,coords,scalar
from build_instant_loot_20260915 import clean
from verify_mod_menu_style_20260917 import Font
from verify_name_particles_20260917 import VM as JosaVM
from PIL import Image,ImageDraw

M=read_meta(O/'candidate_meta.json');FS={};seen={}
for f in M['functions']:
    n=symbol(M,f['index']);i=seen.get(n,0);seen[n]=i+1;FS[n+(f'#{i}' if i else '')]=f
def i32(n):return (n+2**31)%2**32-2**31
class Node(dict):
    def __eq__(self,o):return self is o
    def __ne__(self,o):return self is not o
class VM:
    def __init__(self):
        self.code={};self.refs=collections.Counter();self.clock=10000;self.handlers=set();self.writes=0;self.sweep=False;self.debug=False
        self.keys=['KR_ChestNotice','KR_ChestLife','KR_ChestLine1','KR_ChestLine2','KR_ChestLine3']
        self.parts={n:Node({0:[('part',i) for i in range(32)],'id':i+100,'text':'-1' if n.endswith('Life') else '', 'show':False,'alpha':255}) for i,n in enumerate(self.keys)}
        self.byid={n['id']:n for n in self.parts.values()}
        self.act=Node({0:[('act',i) for i in range(8)]});self.view=Node({0:self.act,1:0})
        self.scene=Node({0:[28634,0,0,0],2:self.view});self.outer=Node({0:[28170,0,0],3:self.scene,4:0})
        self.delegate=object();self.delegate_count=1;self.josa=JosaVM();self.calls=0
    def retain(self,p):
        if isinstance(p,Node):self.refs[id(p)]+=1
    def delete(self,p):
        if isinstance(p,Node):self.refs[id(p)]-=1;assert self.refs[id(p)]>=0
    def run(self,n,args=()):
        self.calls+=1
        if n=='KR_Time':return self.clock
        if n=='KR_SweepActive':return int(self.sweep)
        if n=='KR_ResolveJosa':return self.josa.run(n,args)
        if n=='KR_NoticeParse':return int(args[0])
        if n=='AFL_Parts_AddBeginUpdateEvent':assert args[0] not in self.handlers;self.handlers.add(args[0]);return
        if n=='AFL_Parts_EraseBeginUpdateEvent':self.handlers.discard(args[0]);return
        f=FS[n];vs=f['arguments']+f['variables'];li={v['name']:i for i,v in enumerate(vs)};loc={i:0 for i in range(len(vs))};loc.update(enumerate(args));st=[]
        if n not in self.code:
            ops=[];labs={}
            for line in (O/f'built_{f["index"]}.jam').read_text(encoding='utf8').splitlines():
                l=line.strip()
                if not l or l.startswith((';','FUNC ','ENDFUNC ','EOF ')):continue
                if l.endswith(':'):labs[l[:-1]]=len(ops)
                else:ops.append(l.split(maxsplit=1))
            self.code[n]=ops,labs
        ops,labs=self.code[n];pc=0;steps=0
        while pc<len(ops):
            steps+=1;assert steps<10000
            op,*aa=ops[pc];a=aa[0] if aa else '';pc+=1
            if op=='PUSH':st.append(int(a,0))
            elif op=='S_PUSH':st.append(json.loads(a))
            elif op=='.LOCALREF':st.append(loc[li[a]])
            elif op=='.LOCALASSIGN':key,x=a.rsplit(' ',1);loc[li[key]]=int(x)
            elif op=='.LOCALDELETE':self.delete(loc[li[a]]);loc[li[a]]=-1
            elif op=='PUSHLOCALPAGE':st.append(loc)
            elif op=='.GLOBALREF':st.append(self.delegate if a=='GetActiveScene' else int(self.debug) if a=='L_TreasureBox::IsDebugIgnoreDialog' else None);assert st[-1] is not None
            elif op=='X_DUP':st.extend(st[-int(a):])
            elif op=='X_MOV':x,y=map(int,a.split());st[-x:]=st[-x:][-y:]+st[-x:][:-y]
            elif op=='X_REF':k=st.pop();p=st.pop();st.extend(p[k+i] for i in range(int(a)))
            elif op in ['X_ASSIGN','S_ASSIGN']:
                assert op!='X_ASSIGN' or a=='1';v=st.pop();k=st.pop();p=st.pop();p[k]=v;st.append(v)
            elif op in ['POP','DELETE','SP_INC']:
                x=st.pop()
                if op=='DELETE':self.delete(x)
                elif op=='SP_INC':self.retain(x)
            elif op=='A_REF':assert isinstance(st[-1],str)
            elif op=='DG_CALLBEGIN':assert st.pop() is self.delegate;done=False
            elif op=='DG_CALL':
                _,lab=a.rsplit(' ',1)
                if done:pc=labs[lab]
                else:self.retain(self.outer);st.extend([self.outer,0]);done=True
            elif op=='DG_NEW_FROM_METHOD':fid=st.pop();owner=st.pop();st.append((owner,fid))
            elif op=='NOT':st.append(int(not st.pop()))
            elif op=='S_MOD':value=st.pop();fmt=st.pop();assert a=='2';st.append(fmt%value)
            elif op in ['ADD','SUB','MUL','DIV','LT','GTE','NOTE','EQUALE']:
                y=st.pop();x=st.pop();st.append({'ADD':lambda:i32(x+y),'SUB':lambda:i32(x-y),'MUL':lambda:i32(x*y),'DIV':lambda:int(x/y),'LT':lambda:int(x<y),'GTE':lambda:int(x>=y),'NOTE':lambda:int(x!=y),'EQUALE':lambda:int(x==y)}[op]())
            elif op in ['IFZ','IFNZ']:
                if bool(st.pop())==(op=='IFNZ'):pc=labs[a]
            elif op=='JUMP':pc=labs[a]
            elif op=='CALLFUNC':
                ff=FS[a];k=len(ff['arguments']);args=st[-k:] if k else [];del st[len(st)-k:];ret=self.run(a,args)
                if ff['return-type'][0]:st.append(ret)
            elif op=='CALLMETHOD':
                k=int(a);args=st[-k:] if k else [];del st[len(st)-k:];mid=st.pop();p=st.pop()
                if mid==('act',7):q=self.parts.get(args[0],-1);self.retain(q);st.extend([q,0])
                elif mid==('part',31):st.append(p['id'])
                else:raise AssertionError(mid)
            elif op=='CALLHLL':
                lib,method,_=a.split()
                if (lib,method)==('Delegate','Numof'):assert st.pop() is self.delegate;st.append(self.delegate_count)
                elif (lib,method)==('Array','Numof'):st.append(len(st.pop()))
                elif (lib,method)==('system','IsDebugMode'):st.append(int(self.debug))
                elif lib=='PartsEngine':
                    if method=='GetTextPartsText':assert st.pop()==1;st.append(self.byid[st.pop()]['text'])
                    elif method=='Parts_SetText':assert st.pop()==1;txt=st.pop();pid=st.pop();self.byid[pid]['text']=txt;self.writes+=1;st.append(1)
                    elif method in ['SetComponentShow','SetComponentAlpha']:value=st.pop();pid=st.pop();self.byid[pid]['show' if method.endswith('Show') else 'alpha']=value
                    else:raise AssertionError(a)
                else:raise AssertionError(a)
            elif op=='RETURN':
                assert len(st)==int(f['return-type'][0]!=0),(n,st)
                return st.pop() if st else None
            else:raise AssertionError((n,op,a))
        raise AssertionError(n)
    def check(self):assert not any(self.refs.values()),self.refs
    def lines(self):return [self.parts[f'KR_ChestLine{i}']['text'] for i in [1,2,3]]

def tests():
    count=0;v=VM();root=v.parts['KR_ChestNotice'];history=[]
    for i in range(60):
        text=encode(f'달조각 {i+1}개 획득').decode('cp932');v.run('L_TreasureBox::ShowGetDialog',[text]);history.append(text)
        assert v.lines()==(['']*max(0,3-len(history))+history[-3:]) and root['show'] and root['alpha']==255 and len(v.handlers)==1
        v.check();count+=1
    # Same-frame cap warning survives; no delayed API is available to the fixture.
    v.run('KR_ChestShow',[encode('소지 한도를 넘었습니다.').decode('cp932')]);assert '넘었습니다' in decode(v.lines()[-1].encode('cp932'));v.check();count+=1
    writes=v.writes
    for t in [0,1,1000,3999,4000,4250,4499]:
        v.clock=10000+t;v.run('KR_ChestTick',[16,80]);v.check();assert v.writes==writes and root['show'];count+=1
    v.clock=14500;v.run('KR_ChestTick',[16,16]);v.check();assert not root['show'] and v.lines()==['']*3 and not v.handlers;count+=1
    v.run('KR_ChestShow',[encode('장비 아이템「망치」{YORU_KR_JOSA:O} 손에 넣었다').decode('cp932')]);assert decode(v.lines()[-1].encode('cp932'))=='장비 아이템「망치」를 손에 넣었다';count+=1
    for phase in ['fade','clear','backwards','wrap','expired_show','transition']:
        v=VM();v.run('KR_ChestShow',['A']);v.clock=14250;v.run('KR_ChestTick',[16,16])
        if phase=='fade':assert 0<v.parts['KR_ChestNotice']['alpha']<255;v.run('KR_ChestShow',['B']);assert v.parts['KR_ChestNotice']['alpha']==255
        elif phase=='clear':v.run('KR_ChestClear');assert v.lines()==['']*3 and not v.handlers
        elif phase in ['backwards','wrap']:v.clock=0 if phase=='backwards' else -2147483640;v.run('KR_ChestTick',[16,16]);assert not v.handlers
        elif phase=='expired_show':v.clock=16000;v.run('KR_ChestShow',['B']);assert v.lines()==['','','B']
        else:v.outer=-1;v.run('KR_ChestTick',[16,16]);assert not v.handlers
        v.check();count+=1
    for issue in ['no_delegate','many_delegates','no_outer','wrong_outer','short_outer','no_scene','wrong_scene','short_scene','no_view','no_act',*VM().keys]:
        v=VM()
        if issue=='no_delegate':v.delegate_count=0
        elif issue=='many_delegates':v.delegate_count=2
        elif issue=='no_outer':v.outer=-1
        elif issue=='wrong_outer':v.outer[0][0]=0
        elif issue=='short_outer':v.outer[0]=[]
        elif issue=='no_scene':v.outer[3]=-1
        elif issue=='wrong_scene':v.scene[0][0]=0
        elif issue=='short_scene':v.scene[0]=[]
        elif issue=='no_view':v.scene[2]=-1
        elif issue=='no_act':v.view[0]=-1
        else:del v.parts[issue]
        v.run('KR_ChestShow',['x']);v.check();assert not v.handlers and v.writes==0;count+=1
    for attr in ['sweep','debug']:
        v=VM();setattr(v,attr,True);v.run('L_TreasureBox::ShowGetDialog',['A']);assert v.writes==0 and not v.handlers;v.check();count+=1
    return count

def structure(ev):
    rt=Path(ev['source_pointer']['runtime']);aa,bb=[read_afa3(p) for p in [rt/'NightRemasterPact.afa',O/'NightRemasterPact.afa']];ab=(rt/'NightRemasterPact.afa').read_bytes();bc=(O/'NightRemasterPact.afa').read_bytes();changed=[]
    for i,(a,b) in enumerate(zip(aa.entries,bb.entries)):
        assert (a.no,a.name,a.unknown0,a.unknown1)==(b.no,b.name,b.unknown0,b.unknown1)
        if ab[a.absolute_offset:a.absolute_offset+a.size]!=bc[b.absolute_offset:b.absolute_offset+b.size]:changed.append(i)
    assert len(aa.entries)==len(bb.entries)==187 and changed==[161]
    doc=ex.decode_ex(O/'pact_161_chest.pactex');root=part(doc,'KR_ChestNotice')
    assert scalar(val(root,'表示'))==0
    for p in allparts(root):assert scalar(val(p,'クリック許可'))==0 and scalar(val(p,'オンカーソル透過'))==1
    remove(part(doc,'矩形_000'),'KR_ChestNotice');assert doc.serialize_payload()==ex.decode_ex(O/'original_pact_161.pactex').serialize_payload()
    edits=json.loads((O/'reversible_edits.json').read_text(encoding='utf8'));source=(O/'patch.jam').read_text(encoding='utf8')
    for fid,rows in edits.items():
        f=FS[next(n for n,v in FS.items() if v['index']==int(fid))];n=symbol(M,int(fid));base=clean((O/f'original_{fid}.jam').read_text(encoding='utf8'),n)
        for e in reversed(rows):assert source.count(e['new'])==1;source=source.replace(e['new'],e['old'])
        assert source.count(base)==1,fid
    # No delay setter, input wait, frame pump or gameplay mutation in the helpers.
    allowed={'KR_ChestPart','KR_ChestRegister','KR_ChestRead','KR_ChestWrite','KR_ChestVisible','KR_ChestAlpha','KR_ChestClear','KR_ChestTick','KR_ChestShow','KR_Time','KR_NoticeParse','KR_ResolveJosa','AFL_Parts_AddBeginUpdateEvent','AFL_Parts_EraseBeginUpdateEvent'}
    for fid in ev['added_functions'].values():
        s=(O/f'built_{fid}.jam').read_text(encoding='utf8');assert set(re.findall(r'CALLFUNC ([^\n]+)',s))<=allowed
    return dict(unchanged_pact_entries=186,original_subtree_inverse=True,hook_inverses=len(edits),no_wait_or_frame_pump=True)

def proof(ev):
    rt=Path(ev['source_pointer']['runtime']);font=Font(rt/'NightRemasterFont.fnl');j=JosaVM();samples=[]
    d=ex.decode_ex(rt/'NightRemasterEX.ex');items=[decode(r[2].payload.value) for r in d.blocks[48].payload.rows];longest=max(items,key=lambda x:font.metrics(x,20)[0])
    for fid in [27186,27187,27188,27189,27190,27191,27192,27193]:
        s=(O/f'original_{fid}.jam').read_text(encoding='utf8')
        for raw in re.findall(r'S_PUSH ("(?:[^"\\]|\\.)*")',s):
            z=json.loads(raw)
            if '\\n' in z or '\n' in z or 'DUNG.' in z or '【' in z:continue
            z=z.replace('%s',encode(longest).decode('cp932')).replace('%d','999999')
            z=j.run('KR_ResolveJosa',[z]);ko=decode(z.encode('cp932'))
            if ko:samples.append(ko)
    samples+=['보물상자']
    widths=[font.metrics(x,20)[0] for x in samples];assert max(widths)<=592,(samples[widths.index(max(widths))],max(widths))
    doc=ex.decode_ex(O/'pact_161_chest.pactex');steps=child(txt_info(part(doc,'KR_ChestPanel')),'手順リスト').children
    im=Image.new('RGBA',(620,120));draw=ImageDraw.Draw(im)
    # Render the actual native construction fill recipe, not an invented mockup.
    recipes=[]
    for step in steps:
        rec={k:([scalar(x.value.payload) for x in val(step,k).items] if hasattr(val(step,k),'items') else scalar(val(step,k))) for k in ['コマンド','先矩形','色１','全体']};recipes.append(rec)
        if rec['コマンド']==0:continue
        assert rec['コマンド']==6
        x,y,_,__,w,h=rec['先矩形']
        if rec['全体']:x,y,w,h=0,0,620,120
        draw.rectangle((x,y,x+w-1,y+h-1),fill=tuple(rec['色１']))
    savej(O/'panel_recipe.json',recipes)
    for s in samples:font.text(Image.new('RGBA',(620,32)),s,0,0,20,(255,224,96,255))
    font.text(im,'보물상자',14,10,18,(255,224,96,255))
    chosen=['달조각 150개를 손에 넣었다',decode(j.run('KR_ResolveJosa',[encode(f'장비 아이템「{longest}」').decode('cp932')+'{YORU_KR_JOSA:O}'+encode(' 손에 넣었다').decode('cp932')]).encode('cp932')),'소지 한도를 넘었습니다.']
    for y,s in zip([36,61,86],chosen):font.text(im,s,14,y,20,(255,224,96,255))
    im.save(O/'chest_text_layout_proof.png')
    return dict(font_sha256=sha(rt/'NightRemasterFont.fnl'),max_message_width=max(widths),width_budget=592,messages=len(samples),glyph_states=len(font.checked),proof_kind='native construction colors and FNL layout reconstruction; not game capture')

def main():
    ev=json.loads((O/'build_evidence.json').read_text(encoding='utf8'));assert all(sha(O/n)==h for n,h in ev['files'].items())
    report=dict(status='CHEST_FLOW_COMPILED_PASS',files=ev['files'],compiled_cases=tests(),structure=structure(ev),font=proof(ev),native_verified=False,boundaries='Scene delegate and PartsEngine are explicit fixture boundaries; final compiled helpers and real josa code execute. Not a game run.')
    savej(O/'verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
