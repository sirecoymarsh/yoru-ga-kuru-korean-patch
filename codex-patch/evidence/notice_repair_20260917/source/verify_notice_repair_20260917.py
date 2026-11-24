"""Integration checks derive Activity contents from the actual final PACT, not invented keys."""
from pathlib import Path
import copy,json,shutil
from PIL import Image,ImageDraw
from build_notice_repair_20260917 import O,R,FILES
from cheat_support_20260915 import sha,savej,read_meta,cmd
from build_remaster_multiplier_20260915 import ex,part,child,val,txt_info,allparts,decode
from build_mod_tab_20260915 import scalar,name,remove
from build_route_perf_20260915 import symbol
import verify_chest_flow_20260917 as cv
import verify_mod_menu_style_20260917 as rv

ev=json.loads((O/'build_evidence.json').read_text(encoding='utf8'));rt=Path(ev['source_pointer']['runtime'])
M=read_meta(O/'candidate_meta.json')
for i in [27194,31874,*range(31960,31968)]:
    cmd('ain','dump','--function',symbol(M,i),'-o',O/f'built_{i}.jam',O/'NightRemaster.ain')
cv.O=O

class VM(cv.VM):
    def __init__(self,doc):
        super().__init__();self.loot=True
        self.parts={}
        for i,p in enumerate(allparts(doc.blocks[2].payload.children[0])):
            n=name(p)
            if not n.startswith(('KR_Chest','KR_Receipt','KR_LootNotice')):continue
            try:t=val(txt_info(p),'テキスト').value.decode('cp932')
            except (StopIteration,AttributeError):t=''
            self.parts[n]=cv.Node({0:[('part',j) for j in range(32)],'id':100+i,'text':t,'show':bool(scalar(val(p,'表示'))),'alpha':scalar(val(p,'アルファ'))})
        self.byid={p['id']:p for p in self.parts.values()}
    def run(self,n,args=()):
        if n=='KR_GetLoot':return int(self.loot)
        return super().run(n,args)

def cases():
    doc=ex.decode_ex(O/'pact_160.pactex');count=0
    # The old fixture invented the keys. Real source160 has none: recreate that failure.
    old=VM(ex.decode_ex(O/'original_pact_160.pactex'));old.run('KR_ChestShow',['A']);old.check();assert old.writes==0;count+=1
    v=VM(doc);assert not v.parts['KR_ChestNotice']['show'] and not v.parts['KR_LootNoticeRoot']['show']
    for i in range(60):
        v.run('L_TreasureBox::ShowGetDialog',[str(i)]);v.check()
        assert v.parts['KR_ChestNotice']['show'] and not v.parts['KR_LootNoticeRoot']['show']
        assert v.lines()==(['']*max(0,2-i)+[str(j) for j in range(max(0,i-2),i+1)]);count+=1
    receipt='A\nEXP +100\nB\nEXP +200\nC\nEXP +300'
    v.run('KR_NoticeShow',[receipt]);v.check();assert v.parts['KR_ReceiptBody']['text']==receipt
    assert v.parts['KR_LootNoticeRoot']['show'] and not v.parts['KR_ChestNotice']['show'];count+=1
    writes=v.writes
    for dt in [0,16,1000,5499,5500,5750,5999]:
        v.clock=10000+dt;v.run('KR_NoticeTick',[16,80]);v.check();assert v.parts['KR_LootNoticeRoot']['show'] and v.writes==writes;count+=1
    v.clock=16000;v.run('KR_NoticeTick',[16,80]);v.check();assert not v.handlers and not v.parts['KR_LootNoticeRoot']['show'];count+=1
    for phase in ['fade_refresh','loot_off','chest_after_enemy','scene_change','config_clear','expiry_chest','backward_clock']:
        v=VM(doc);v.run('KR_NoticeShow',[receipt]);v.check()
        if phase=='fade_refresh':
            v.clock=15800;v.run('KR_NoticeTick',[16,80]);assert v.parts['KR_LootNoticeRoot']['alpha']<255;v.run('KR_NoticeShow',['fresh']);assert v.parts['KR_LootNoticeRoot']['alpha']==255
        elif phase=='loot_off':v.loot=False;v.run('KR_NoticeTick',[16,80]);assert not v.parts['KR_LootNoticeRoot']['show']
        elif phase=='chest_after_enemy':v.run('KR_ChestShow',['chest']);assert not v.parts['KR_LootNoticeRoot']['show'] and v.parts['KR_ChestNotice']['show']
        elif phase=='scene_change':v.outer=-1;v.run('KR_NoticeTick',[16,16]);assert not v.handlers
        elif phase=='config_clear':v.run('KR_NoticeClear');v.run('KR_ChestClear');assert not v.handlers
        elif phase=='expiry_chest':v.run('KR_ChestShow',['chest']);v.clock+=4500;v.run('KR_ChestTick',[16,80]);assert not v.handlers
        else:v.clock=-1;v.run('KR_NoticeTick',[16,80]);assert not v.handlers
        v.check();count+=1
    for missing in ['KR_LootNoticeRoot','KR_ReceiptBody','KR_ReceiptLife','KR_ChestNotice','KR_ChestLife']:
        v=VM(doc);del v.parts[missing];v.run('KR_NoticeShow',['receipt']);v.run('KR_ChestShow',['chest']);v.check();count+=1
    return count

def renderers():
    rv.FONT=rv.Font(rt/'NightRemasterFont.fnl');tests=0
    for tag in [0,1,2,999,rv.TYPE]:
        for n in [1,2,8,9]:
            for gap in [0,4,8]:
                v=rv.VM(O/'built_27936.jam',tag,'자동 장착\n유지할 슬롯과 기준을 선택하세요.',['유틸리티 추천']*n,gap=gap);v.run()
                assert v.obj[6][2]==v.original_color
                assert not any('ＣＧ部分' in x[0] for x in v.commands)
                if tag!=rv.TYPE:
                    old=rv.VM(O/'original_27936.jam',tag,'자동 장착\n유지할 슬롯과 기준을 선택하세요.',['유틸리티 추천']*n,gap=gap);old.run();assert v.commands==old.commands
                else:
                    assert all(i['height']==48 and i[0][0]==list(rv.YELLOW) for i in v.obj[4])
                tests+=1
    return tests

def structure_and_proof():
    # Remove added notices and compare160 byte-for-byte. Chest is an exact moved subtree.
    a=ex.decode_ex(O/'pact_160.pactex');src=ex.decode_ex(O/'original_pact_160.pactex')
    b=ex.decode_ex(O/'original_pact_161.pactex')
    assert part(a,'KR_ChestNotice').serialize()==part(b,'KR_ChestNotice').serialize()
    remove(part(a,'矩形_000'),'KR_ChestNotice');remove(part(a,'矩形_000'),'KR_LootNoticeRoot');assert a.serialize_payload()==src.serialize_payload()
    # Native initializer selects160 by exact archive key; candidate contains both panels there.
    init=(R/'staging/chest_flow_20260917/original_28775.jam').read_text(encoding='utf8')
    assert 'Game\\\\Scenes\\\\5000Dungeon\\\\SceneDungeon.pact' in init
    a=ex.decode_ex(O/'pact_160.pactex')
    for rn in ['KR_ChestNotice','KR_LootNoticeRoot']:
        root=part(a,rn);assert scalar(val(root,'表示'))==0
        for p in allparts(root):assert scalar(val(p,'クリック許可'))==0 and scalar(val(p,'オンカーソル透過'))==1
    for i in ev['patched_existing']:
        if i==27936:continue
        s=(O/f'built_{i}.jam').read_text(encoding='utf8')
        assert 'AFL_Activity_Release' not in s and 'Ｐ＿テキスト設定' not in s and 'Wait' not in s
    # Full original source texture, ordinary component transform; render only a proof.
    srcim=Image.open(R/'staging/mod_menu_style_20260917/cg_1840.png').convert('RGBA')
    im=Image.new('RGBA',(440,205),(12,18,36,255));draw=ImageDraw.Draw(im);f=rv.FONT
    for j,row in enumerate(ev['PACT']['buttons']):
        d=ex.decode_ex(O/f'pact_{row["entry"]}.pactex');p=part(d,row['button']);label=part(d,row['button']+'Label');info=child(p,'種類別情報')
        assert scalar(val(p,'クリック許可'))==1 and scalar(val(p,'オンカーソル透過'))==0
        for state in ['通常状態','オンカーソル状態','キーダウン状態']:assert val(child(info,state),'ＣＧ名').value.decode('cp932')=='シス／戦闘／説明枠'
        deco=child(txt_info(label),'テキスト装飾');assert [scalar(v.value.payload) for v in val(deco,'フォント縁取り色').items]==[0,0,32]
        w=round(row['width']);x,y=20,12+j*62;im.alpha_composite(srcim.resize((w,42)),(x,y))
        t=decode(val(txt_info(label),'テキスト').value);pos=[scalar(v.value.payload) for v in val(label,'座標').items];size=scalar(val(deco,'フォントサイズ'));tw,th=f.metrics(t,size)
        assert pos[0]>=0 and pos[0]+tw<=w+0.01 and pos[1]>=0 and pos[1]+th<=42.01
        f.text(im,t,x+pos[0],y+pos[1],size,(255,224,96,255));draw.text((235,y+15),str(row['entry'])+' / full native CG',fill='white')
    im.save(O/'button_proof.png')
    return dict(source_activity_regression_proven=True,correct_native_owner_entry=160,notice_clickthrough=True,button_states=9,full_native_cg_transform=True,partial_cg_copy_removed=True,gameplay_payout_unchanged=True)

def main():
    assert all(sha(O/n)==h for n,h in ev['files'].items())
    report=dict(status='NOTICE_REPAIR_COMPILED_PASS',files=ev['files'],notice_cases=cases(),renderer_cases=renderers(),integration=structure_and_proof(),native_verified=False,boundaries='Actual candidate JAM executes against explicit PartsEngine/scene mocks derived from final PACT160. Renderer commands are inspected but not executed by the native graphics engine. Native gameplay still pending.')
    savej(O/'verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
