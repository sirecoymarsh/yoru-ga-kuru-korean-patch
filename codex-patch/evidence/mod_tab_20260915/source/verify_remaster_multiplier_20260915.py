"""Execute persisted disassembly in a bounded arithmetic VM; verify native UI geometry."""
from pathlib import Path
import copy,json,math,re,struct,zlib
from audit_dynamic_ui_20260915 import R,ex,encode,ENC,decode
from publish_training_fix_20260915 import read,write,sha
from integrate_ui_opening_20260913 import read_meta
from build_remaster_multiplier_20260915 import O,ROWS,OLD_PARTS,part,child,val,allparts
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index

def i32(x):return (int(x)+2**31)%2**32-2**31
def bits(x):return struct.unpack('<i',struct.pack('<f',x))[0]
def flt(x):return struct.unpack('<f',struct.pack('<i',i32(x)))[0]
def trunc(a,b):return (abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)

class VM:
    def __init__(self,meta):
        self.meta=meta;self.g={201:100,202:100,203:100,204:100}
        self.names={r['name']:i for i,r in enumerate(meta['globals'])};self.functions={f['name']:f for f in meta['functions']};self.cache={};self.calls=0
    def run(self,name,args):
        f=self.functions[name];fid=f['index']
        if fid not in self.cache:
            ops=[];labels={}
            for line in (O/f'built_{fid}.jam').read_text(encoding='utf8').splitlines():
                s=line.strip()
                if not s or s.startswith((';','FUNC','ENDFUNC','EOF')):continue
                if s.endswith(':'):labels[s[:-1]]=len(ops);continue
                ops.append(s.split(maxsplit=1))
            self.cache[fid]=(ops,labels)
        ops,labels=self.cache[fid];loc={d['name']:a for d,a in zip(f['arguments'],args)};stack=[];pc=0;steps=0;self.calls+=1
        while pc<len(ops):
            steps+=1;assert steps<300
            op,*rest=ops[pc];arg=rest[0] if rest else None;pc+=1
            if op=='PUSH':stack.append(i32(int(arg,0)))
            elif op=='PUSHGLOBALPAGE':stack.append('GLOBALS')
            elif op=='.GLOBALREF':stack.append(self.g[self.names[arg]])
            elif op=='.GLOBALASSIGN':
                global_name,number=arg.rsplit(' ',1);self.g[self.names[global_name]]=i32(int(number,0))
            elif op=='.LOCALREF':stack.append(loc[arg])
            elif op=='POP':stack.pop()
            elif op=='X_ASSIGN':
                assert arg=='1';v=stack.pop();idx=stack.pop();assert stack.pop()=='GLOBALS';self.g[idx]=v;stack.append(v)
            elif op=='ITOF':stack.append(bits(stack.pop()))
            elif op=='FTOI':stack.append(i32(math.trunc(flt(stack.pop()))))
            elif op in ['IFNZ','IFZ']:
                v=stack.pop()
                if bool(v)==(op=='IFNZ'):pc=labels[arg]
            elif op=='JUMP':pc=labels[arg]
            elif op=='RETURN':
                if f['return-type'][0]==0:assert not stack;return None
                assert len(stack)==1,(name,stack);return stack.pop()
            elif op=='CALLFUNC':
                ff=self.functions[arg];n=len(ff['arguments']);aa=stack[-n:] if n else []
                if n:del stack[-n:]
                v=self.run(arg,aa)
                if ff['return-type'][0]!=0:stack.append(v)
            else:
                b=stack.pop();a=stack.pop()
                if op.startswith('F_'):
                    a,b=flt(a),flt(b);k=op[2:]
                    if k=='ADD':v=bits(a+b)
                    elif k=='SUB':v=bits(a-b)
                    elif k=='MUL':v=bits(a*b)
                    elif k=='DIV':v=bits(a/b)
                    elif k=='GTE':v=int(a>=b)
                    elif k=='LTE':v=int(a<=b)
                    elif k=='LT':v=int(a<b)
                    elif k=='GT':v=int(a>b)
                    else:raise AssertionError(op)
                elif op=='ADD':v=i32(a+b)
                elif op=='SUB':v=i32(a-b)
                elif op=='MUL':v=i32(a*b)
                elif op=='DIV':v=i32(trunc(a,b))
                elif op=='MOD':v=i32(a-trunc(a,b)*b)
                elif op=='GTE':v=int(a>=b)
                elif op=='LTE':v=int(a<=b)
                elif op=='LT':v=int(a<b)
                elif op=='GT':v=int(a>b)
                elif op=='NOTE':v=int(a!=b)
                elif op=='EQUALE':v=int(a==b)
                else:raise AssertionError(op)
                stack.append(v)
        raise AssertionError(('No return',name))

def value(p):
    if isinstance(p,ex.ScalarNode):return struct.unpack('<f' if p.type_id==2 else '<i',p.raw)[0]
    if isinstance(p,ex.StringNode):return decode(p.value)
    if isinstance(p,ex.ListNode):return [value(x.value.payload) for x in p.items]
    raise TypeError(type(p))

def main():
    ev=read(O/'build_evidence.json');p=read(R/'ui_cumulative/current.json');assert p==ev['source_pointer'];rt=Path(p['runtime'])
    for n,h in ev['files'].items():assert sha(O/n)==h
    meta=read_meta(O/'candidate_meta.json');vm=VM(meta);checks=[]
    for key,_,gi,__,calc,ratekey in ROWS:
        for mult in range(1,21):
            prior=copy.deepcopy(vm.g);vm.run('KR_MultiplierSet'+key,[bits((mult-1)/19)]);assert vm.g[gi]==mult*100
            assert all(vm.g[g]==v for g,v in prior.items() if g!=gi)
            for _ in range(100):
                encoded=vm.run('KR_MultiplierGet'+key,[]);vm.run('KR_MultiplierSet'+key,[encoded]);assert vm.g[gi]==mult*100
            checks.append(dict(key=key,multiplier=mult,stored_percent=vm.g[gi],stable_roundtrips=100))
            for src in [0,1,7,100,100000,1073741,1073742,2147483647,-1,-7,-2147483648]:
                got=vm.run(meta['functions'][calc]['name'],[src]);expected=max(-2147483648,min(2147483647,src*mult));assert got==expected,(key,mult,src,got,expected)
        for input_,expected in [(-1.,100),(float('-inf'),100),(float('nan'),100),(2.,2000),(float('inf'),2000)]:
            vm.run('KR_MultiplierSet'+key,[bits(input_)]);assert vm.g[gi]==expected
    for (key,_,gi,*_),mult in zip(ROWS,[1,2,5,20]):vm.run('KR_MultiplierSet'+key,[bits((mult-1)/19)])
    assert vm.g=={201:100,203:200,202:500,204:2000}
    # Original gameplay uses1x/2x. Noninteger debug percentages keep original formula.
    for percent in [0,50,125,150,250,2500]:
        for src in [0,1,7,12345,-7]:assert vm.run('KR_MultiplierCalc',[src,percent])==trunc(i32(src*percent),100)
    # The two pre-existing config event methods must bind all4 float callbacks,
    # and cannot invoke the old bool sync for those controls.
    for fid,method,mode in [(29817,29825,'Get'),(29818,29826,'Set')]:
        s=(O/f'built_{fid}.jam').read_text(encoding='utf8')
        for key,_,__,oldset,___,____ in ROWS:
            newname='KR_Multiplier'+mode+key;newid=ev['AIN']['added_function_ids'][newname]
            assert f'PUSH {method}\n\tS_PUSH "KR_Multiplier_{key}"\n\tPUSH -1\n\tPUSH {newid}' in s
            assert f'S_PUSH "KR_Multiplier_Value_{key}"' in s
            assert f'PUSH {oldset if mode=="Set" else oldset+1}\n\tDG_NEW_FROM_METHOD' not in s
    doc=ex.decode_ex(O/'pact_125_sliders.pactex');cas=part(doc,'レイアウト_カジュアル');kids=child(cas,'子パーツ')
    names=[t.name.value.decode('cp932') for t in kids.children]
    order=[x.value.payload.value.decode('cp932') for x in val(cas,'子パーツリスト').items]
    assert names==order and len(names)==len(set(names))
    assert not any(n in names for n in OLD_PARTS)
    bounds=[]
    for i,(key,*_) in enumerate(ROWS):
        t=part(doc,'KR_Multiplier_'+key);x,y,z=value(val(t,'座標'));info=child(t,'種類別情報')
        assert value(val(info,'全体スクロール量'))-value(val(info,'表示量'))==19
        assert value(val(t,'原点座標モード'))==1
        w,h=value(val(info,'長さ')),value(val(info,'幅'));bounds.append([x,y,x+w,y+h])
    for i,a in enumerate(bounds):
        for b in bounds[i+1:]:assert a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1]
    assert max(b[3] for b in bounds)==192 and min(value(val(child(kids,n),'座標'))[1] for n in ['SYS_敵強制表示','SYS_罠強制表示','SYS_宝箱強制表示'])==230
    assert value(val(part(doc,'レイアウト_壁紙'),'座標'))[1]==466
    assert 147+value(val(child(kids,'SYS_アイテム所持数増加'),'座標'))[1]+32<466
    # Inspect actual FNL face3 (GUI font259) bitmaps and text advance, not an OS font.
    font=rt/'NightRemasterFont.fnl';raw=font.read_bytes();_,faces=parse_fnl_font(font,3);table={};q=20
    for fontno in range(struct.unpack_from('<I',raw,16)[0]):
        nf=struct.unpack_from('<I',raw,q)[0];q+=4
        for index in range(nf):
            h,u,ng=struct.unpack_from('<III',raw,q);q+=12
            if fontno==3:table[index]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(ng)])
            q+=10*ng
    proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};glyphs=set();textrows=[]
    for t in kids.children:
        name=t.name.value.decode('cp932')
        if not (name.startswith('KR_Multiplier_') or name=='テキストパーツ_000:0'):continue
        info=child(t,'種類別情報');normal=next((c for c in info.children if c.name.value.decode('cp932')=='通常状態'),None)
        if normal is None:continue
        txt=value(val(normal,'テキスト'));decor=child(normal,'テキスト装飾');size=value(val(decor,'フォントサイズ'))
        assert value(val(decor,'フォントタイプ'))==259
        texts=[str(n)+'배' for n in range(1,21)] if '_Value_' in name else [txt]
        face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,value(val(decor,'字間隔')),0,0)
        budget=56 if '_Value_' in name else 268 if '_Label_' in name else 700
        for text in texts:
            width=measure.measure(text,True)['lines'][0]['width_px'];assert width<=budget,(name,text,width,budget)
            for ch in text:
                if ch.isspace():continue
                index=measure.glyph_index(ch,True);w,pos,n=table[face.face_index][1][index];assert w>0 and n>0 and pos>0 and any(zlib.decompress(raw[pos:pos+n])),ch
                glyphs.add((size,ch))
            textrows.append(dict(name=name,text=text,size=size,width=width,budget=budget))
    report=dict(status='STATIC_VM_LAYOUT_PASS_NATIVE_PENDING',translator_model='Codex internal',files=ev['files'],
        compiled_disassembly_vm_calls=vm.calls,independent_category_steps=80,repeat_roundtrips=8000,
        separate_rates_proven=[1,2,5,20],integer_saturation_and_legacy_percent_checks=True,
        float_callback_bindings_verified=8,actual_FNL_face=3,nonempty_glyph_checks=len(glyphs),text_width_overflows=0,
        no_slider_or_preserved_lower_section_overlap=True,slider_bounds=bounds,text_rows=textrows,
        all_existing_global_struct_and_function_signatures_preserved=True,
        native_verified=False,save_file_roundtrip_verified=False,
        limitation='Persisted code arithmetic and native control schema/layout checks, not a live engine UI or disk save/reload test.')
    write(O/'verification.json',report);print(json.dumps({k:v for k,v in report.items() if k!='text_rows'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
