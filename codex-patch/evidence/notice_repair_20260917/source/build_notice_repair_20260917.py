"""Repair reported native UI failures against the current chest-flow build only."""
from pathlib import Path
import copy,json,re,struct
from cheat_support_20260915 import R,sha,savej,read_meta,cmd
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,rename,txt_info,fn
import build_mod_tab_20260915 as mt
from build_dungeon_sweep_20260916 import push,lr,cf,assign
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from repair_ui_runtime_weapon_text_20260913 import unpack,strings
from audit_sys43_native_opcodes_20260915 import audit

O=R/'staging/notice_repair_20260917'
BASE='9d8fee1e3e4914ed0ba0f2898b0c30ab55e4cdda5ddc1f9bf8f4d09bf8e165e3'
FILES=['NightRemaster.ain','NightRemasterPact.afa']
def text(t):return '\tS_PUSH '+json.dumps(t,ensure_ascii=False)+'\n'
def pid(t):return text(t)+cf('KR_ChestPart')
def numeric(t):return t+text('%d')+'\tX_MOV 2 1\n\tS_MOD 2\n'

def pact(rt):
    src=rt/'NightRemasterPact.afa';a=read_afa3(src);ds={}
    for i in [153,154,160,161,186]:
        e=a.entries[i]
        with src.open('rb') as f:f.seek(e.absolute_offset);(O/f'original_pact_{i}.pactex').write_bytes(f.read(e.size))
        ds[i]=ex.decode_ex(O/f'original_pact_{i}.pactex')
    parent=part(ds[160],'矩形_000');mt.ORDER=copy.deepcopy(val(parent,'子パーツリスト').items[0])
    chest=copy.deepcopy(part(ds[161],'KR_ChestNotice'))
    mt.remove(part(ds[161],'矩形_000'),'KR_ChestNotice');mt.add(parent,chest)
    # Actual lookup owner is SceneDungeon160, NOT the independently loaded161.
    receipt=mt.clean_group(chest,'KR_LootNoticeRoot',20,18);setlist(receipt,'座標',[20,18,301]);si(receipt,'表示',0)
    rect=txt_info(receipt)
    for k,v in [('右上',[570,0]),('左下',[0,188]),('右下',[570,188])]:setlist(rect,k,v)
    for n in ['KR_ReceiptPanel','KR_ReceiptTitle','KR_ReceiptBody','KR_ReceiptLife']:
        p=copy.deepcopy(part(ds[186],n));mt.add(receipt,p)
        if n.endswith(('Title','Body')):
            deco=child(txt_info(p),'テキスト装飾');setlist(deco,'フォント色',[255,224,96]);setlist(deco,'フォント縁取り色',[0,0,32]);si(deco,'フォント縁取り',1)
    mt.add(parent,receipt)
    # Both notices reside above the map and survive subbutton show/hide updates.
    for root in [chest,receipt]:
        for p in mt.allparts(root):
            si(p,'クリック許可',0);si(p,'オンカーソル透過',1);si(p,'メッセージウィンドウ表示連動',0)
    buttons=[]
    for i,rootname,bn,ln in [(153,'KR_AutoEquipRoot','KR_AutoEquipButton','KR_AutoEquipButtonLabel'),(154,'KR_AutoStoneRoot','KR_AutoStoneButton','KR_AutoStoneButtonLabel'),(161,'KR_SweepRoot','KR_SweepButton','KR_SweepButtonLabel')]:
        d=ds[i];g=part(d,rootname);old=part(d,bn);label=part(d,ln)
        r=txt_info(g);width=mt.scalar(val(r,'右上').items[0].value.payload)
        if i==161:
            # Same horizontal centre as the114px native rest/item buttons.
            width=114;setlist(g,'座標',[1142,386,40])
            setlist(r,'右上',[width,0]);setlist(r,'右下',[width,42])
        # Native full CG sprite transformation: never copy/read outside source pixels.
        button=mt.clean_group(chest,bn,0,0);si(button,'表示',1);si(button,'クリック許可',1);si(button,'オンカーソル透過',0)
        setlist(button,'座標',[0,0,1]);setlist(button,'拡大縮小',[width/640,42/110])
        info=child(button,'種類別情報');cg=copy.deepcopy(child(info,'オンカーソル状態'))
        cg.name.replacement='通常状態'.encode('cp932')
        ix=info.children.index(child(info,'通常状態'));info.children[ix]=cg
        ss(cg,'ＣＧ名','シス／戦闘／説明枠')
        for state in ['オンカーソル状態','キーダウン状態']:
            target=next(c for c in info.children if c is not cg and c.name.value.decode('cp932')==state)
            ss(target,'ＣＧ名','シス／戦闘／説明枠')
        kids=child(g,'子パーツ').children;kids[kids.index(old)]=button
        deco=child(txt_info(label),'テキスト装飾');setlist(deco,'フォント色',[255,224,96]);setlist(deco,'フォント縁取り色',[0,0,32]);si(deco,'フォント縁取り',1)
        # The label is a sibling, not a scaled child of the background sprite.
        if i==161:
            from verify_mod_menu_style_20260917 import Font
            f=Font(rt/'NightRemasterFont.fnl');w,h=f.metrics('자동 소탕',24);setlist(label,'座標',[(width-w)/2,(42-h)/2,2])
        buttons.append(dict(entry=i,root=rootname,button=bn,width=width,height=42,whole_native_cg='シス／戦闘／説明枠',partial_copy=False,outline=[0,0,32]))
    repl={}
    for i in [153,154,160,161]:
        p=O/f'pact_{i}.pactex';d=ds[i];p.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(p).serialize_payload()==d.serialize_payload();repl[i]=p
    return dict(archive=rebuild(src,O/'NightRemasterPact.afa',repl),changed_entries=list(repl),chest_moved_from=161,notices_loaded_by=160,buttons=buttons)

def main():
    O.mkdir(exist_ok=True)
    ptr=json.loads((R/'ui_cumulative/current.json').read_text(encoding='utf8'));rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert sha(src)==BASE and sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    savej(O/'source_pointer.json',ptr);cmd('ain','dump','-j','-o',O/'source_meta.json',src);m=read_meta(O/'source_meta.json');names={};seen={}
    for f in m['functions']:
        n=symbol(m,f['index']);k=seen.get(n,0);seen[n]=k+1;names[f['index']]=n+(f'#{k}' if k else '')
    def get(i):
        p=O/f'original_{i}.jam';cmd('ain','dump','--function',names[i],'-o',p,src);return clean(p.read_text(encoding='utf8'),names[i])
    patches={}
    # Revert only unsafe new raster-copy composition, not the cumulative build.
    style=R/'staging/mod_menu_style_20260917';s=(style/'patch.jam').read_text(encoding='utf8');removed=[]
    for e in reversed(json.loads((style/'reversible_edits.json').read_text(encoding='utf8'))):
        if any(tag in e['new'] for tag in ['mod_panel_old:','mod_cell_old:','mod_dividers_old:']):
            assert s.count(e['new'])==1;s=s.replace(e['new'],e['old']);removed.append(e)
    assert len(removed)==3 and 'ＣＧ部分拡大縮小' not in s
    patches[27936]=s;get(27936)
    # Existing getter now resolves both panels in the correct original scene Activity.
    bodies={}
    bodies[31876]=lr('key')+'\tA_REF\n'+cf('KR_ChestPart')+'\tRETURN\n'
    bodies[31877]=pid('KR_LootNoticeRoot')+push(0)+'\tGTE\n\tRETURN\n'
    bodies[31878]=''
    for n in ['KR_LootNoticeRoot','KR_ReceiptBody','KR_ReceiptLife']:
        bodies[31878]+=pid(n)+push(0)+'\tLT\n\tIFNZ receipt_missing\n'
    bodies[31878]+=push(1)+'\tRETURN\nreceipt_missing:\n'+push(0)+'\tRETURN\n'
    bodies[31875]=cf('KR_NoticeReady')+'\tRETURN\n'
    bodies[31879]=push(0)+cf('KR_NoticeRegister')+cf('KR_NoticeReady')+'\tIFZ receipt_clear_done\n'
    bodies[31879]+=pid('KR_LootNoticeRoot')+push(0)+cf('KR_ChestVisible')+pid('KR_LootNoticeRoot')+push(255)+cf('KR_ChestAlpha')
    bodies[31879]+=pid('KR_ReceiptBody')+text('')+cf('KR_ChestWrite')+pid('KR_ReceiptLife')+text('-1')+cf('KR_ChestWrite')+'receipt_clear_done:\n\tRETURN\n'
    s=get(31880).replace(text('ルートパーツ'),text('KR_LootNoticeRoot'))
    s=s.replace(push(1)+cf('Ｐ＿テキスト取得'),cf('KR_ChestRead')).replace(cf('Ｐ＿アルファ値設定'),cf('KR_ChestAlpha'))
    patches[31880]=s
    s=cf('KR_NoticeReady')+'\tIFZ receipt_show_done\n'+cf('KR_ChestClear')+push(0)+cf('KR_NoticeRegister')
    s+=pid('KR_ReceiptBody')+lr('text')+'\tA_REF\n'+cf('KR_ResolveJosa')+cf('KR_ChestWrite')
    s+=pid('KR_ReceiptLife')+numeric(cf('KR_Time'))+cf('KR_ChestWrite')
    s+=pid('KR_LootNoticeRoot')+push(255)+cf('KR_ChestAlpha')+pid('KR_LootNoticeRoot')+push(1)+cf('KR_ChestVisible')+push(1)+cf('KR_NoticeRegister')+'receipt_show_done:\n\tRETURN\n'
    bodies[31881]=s
    for i,b in bodies.items():get(i);patches[i]=fn(i,names[i],b)
    patches[31968]=begin(get(31968),cf('KR_NoticeClear'))
    jam=O/'patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,src)
    cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
    for a,b in zip(m['functions'],nm['functions']):
        a=dict(a);b=dict(b);aa=a.pop('address');bb=b.pop('address');assert a==b
        if aa!=bb:changed.append(a['index'])
    assert changed==sorted(patches)
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    old=unpack(src.read_bytes());new=unpack(out.read_bytes());size=struct.unpack_from('<I',old,12)[0]
    assert old[16:16+size]==new[16:16+size];assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
    assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
    for i in patches:cmd('ain','dump','--function',names[i],'-o',O/f'built_{i}.jam',out)
    cmd('ain','dump','--raw-code','--no-macros','-o',O/'raw.jam',out);na=audit(out,O/'candidate_meta.json',O/'raw.jam',rt/'NightRemaster.exe',ids=list(patches));assert na['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',na)
    pe=pact(rt)
    ev=dict(status='NOTICE_REPAIR_STAGED',source_pointer=ptr,source_files={n:sha(rt/n) for n in FILES},files={n:sha(O/n) for n in FILES},patched_existing=changed,added_functions={},PACT=pe,old_CODE_STR0_MSG1_exact=True,save_schema_changes=0,translator_model='Codex internal',native_verified=False,removed_rendering_blocks=3,rewards_and_progress_functions_unchanged=True)
    savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
