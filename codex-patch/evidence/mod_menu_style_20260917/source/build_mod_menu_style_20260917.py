"""Restyle only tagged mod dialogs using native, text-free CG strips. No live writes."""
from pathlib import Path
import copy, json, re, struct
from cheat_support_20260915 import R, sha, savej, read_meta, cmd
from build_instant_loot_20260915 import clean
from build_dungeon_sweep_20260916 import push, lr, cf, cm, assign
from repair_ui_runtime_weapon_text_20260913 import unpack, strings
from audit_sys43_native_opcodes_20260915 import audit
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,txt_info,val,setlist

O = R / 'staging/mod_menu_style_20260917'
TYPE = 2026091602
BASE = '16025aab9b654a3a1470fa58cd0459165b26d64cdabd7f76c2d9a69c26a12f07'
PANEL = 'シス／戦闘／説明枠'
BUTTON = 'シス／コンフィグ／ボタン／ゲームに戻る／通常'
CF = 'Ｐ＿構築手順＿ＣＧ部分拡大縮小コピー'
BLEND = 'Ｐ＿構築手順＿ＣＧ部分拡大縮小アルファブレンド'
YELLOW = (255,224,96,255)
HOVER = (255,250,180,255)

def literal(s):
    return '\tS_PUSH ' + json.dumps(s, ensure_ascii=False) + '\n'

def tag():
    return cm('\tPUSHSTRUCTPAGE\n', 27908) + push(TYPE) + '\tEQUALE\n'

def guarded(old, new, label):
    return tag() + f'\tIFZ {label}_old\n' + new + f'\tJUMP {label}_end\n{label}_old:\n' + old + f'{label}_end:\n'

def arithmetic(a, b, op):
    return a + (push(b) if isinstance(b, int) else b) + '\t' + op + '\n'

def inf(ref):
    return '\t.STRUCTREF C_SelectDialog m_SelectInfos\n' + ref + '\tX_REF 1\n'

def col():
    return cm('\tPUSHSTRUCTPAGE\n', 27905)

def count():
    return '\t.STRUCTREF C_SelectDialog m_SelectInfos\n\tCALLHLL Array Numof 65538\n'

def gap():
    return cm('\t.STRUCTREF C_SelectDialog m_MarginSelect\n', 20933) + '\tFTOI\n'

def write_field(obj, index, value):
    return obj+push(index)+value+'\tX_ASSIGN 1\n\tPOP\n'

def color_field(obj, index):
    return obj+push(index)+'\tX_REF 1\n'

# Reuse the native renderer's temporary Core wrapper and its exact release idiom.
CORE = '"<dummy : IConstructionParts@Core::getの戻り値>"'
def part_id():
    return ('\tPUSHSTRUCTPAGE\n\tPUSH 2\n\tX_REF 2\n'
            '\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n\tPUSH 0\n\tX_REF 1\n'
            '\tX_MOV 2 1\n\tPUSH 13\n\tADD\n\tX_REF 1\n\tCALLMETHOD 0\n'
            f'\t.LOCALREF {CORE}\n\tDELETE\n\tPUSHLOCALPAGE\n\tPUSH 38\n\tX_MOV 4 2\n\tX_ASSIGN 2\n'
            '\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n\tPUSH 0\n\tX_REF 1\n'
            '\tX_MOV 2 1\n\tPUSH 31\n\tADD\n\tX_REF 1\n\tCALLMETHOD 0\n'
            f'\t.LOCALDELETE {CORE}\n')

def cg(name, x, y, w, h, sx, sy, sw, sh):
    # Native copy transfers RGB and alpha into an initially transparent construction.
    args = [x,y,w,h,sx,sy,sw,sh,0,1]
    return part_id() + literal(name) + ''.join(push(a) if isinstance(a,int) else a for a in args) + cf(BLEND if name==BUTTON else CF)

def panel():
    out = ''
    w,h=lr('fullWidth'),lr('fullHeight')
    # Native24px margins/corners remain unscaled. Only the text-free central area stretches.
    for dy,dh,sy,sh in [(push(0),24,0,24),(push(24),arithmetic(h,48,'SUB'),24,62),(arithmetic(h,24,'SUB'),24,86,24)]:
        for dx,dw,sx,sw in [(push(0),24,0,24),(push(24),arithmetic(w,48,'SUB'),24,592),(arithmetic(w,24,'SUB'),24,616,24)]:
            out += cg(PANEL,dx,dy,dw,dh,sx,sy,sw,sh)
    return out

def buttons():
    idx=lr('i#4')
    x=arithmetic(arithmetic(arithmetic(idx,col(),'MOD'),lr('oneSelWidth'),'MUL'),22,'ADD')
    y=arithmetic(arithmetic(lr('titleBackHeight'),arithmetic(arithmetic(idx,col(),'DIV'),arithmetic(push(48),gap(),'ADD'),'MUL'),'ADD'),4,'ADD')
    width=arithmetic(lr('oneSelWidth'),10,'SUB')
    # Do not copy the source label at all: 12px caps and one empty gradient column only.
    return (cg(BUTTON,x,y,12,40,0,0,12,40)
            +cg(BUTTON,arithmetic(x,12,'ADD'),y,arithmetic(width,24,'SUB'),40,12,0,1,40)
            +cg(BUTTON,arithmetic(x,arithmetic(width,12,'SUB'),'ADD'),y,12,40,138,0,12,40))

def pact(rt):
    src=rt/'NightRemasterPact.afa';arc=read_afa3(src);replacements={};rows=[]
    for i,n in [(153,'KR_AutoEquipButtonLabel'),(154,'KR_AutoStoneButtonLabel'),(161,'KR_SweepButtonLabel')]:
        e=arc.entries[i];path=O/f'original_pact_{i}.pactex'
        with src.open('rb') as f:f.seek(e.absolute_offset);path.write_bytes(f.read(e.size))
        doc=ex.decode_ex(path);deco=child(txt_info(part(doc,n)),'テキスト装飾')
        before=[struct.unpack('<i',v.value.payload.raw)[0] for v in val(deco,'フォント色').items]
        setlist(deco,'フォント色',YELLOW[:3]);out=O/f'pact_{i}_yellow.pactex'
        out.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()));replacements[i]=out
        setlist(deco,'フォント色',before);assert doc.serialize_payload()==ex.decode_ex(path).serialize_payload()
        rows.append(dict(entry=i,label=n,before=before,after=YELLOW[:3],only_field='テキスト装飾/フォント色'))
    return dict(changes=rows,archive=rebuild(src,O/'NightRemasterPact.afa',replacements))

def main():
    O.mkdir(exist_ok=True)
    ptr=json.loads((R/'ui_cumulative/current.json').read_text(encoding='utf8'))
    rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert sha(src)==BASE and sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    m=read_meta(R/'staging/autoequip_20260917/candidate_meta.json')
    name='C_SelectDialog@CreateParts'
    cmd('ain','dump','--function',name,'-o',O/'original_27936.jam',src)
    original=clean((O/'original_27936.jam').read_text(encoding='utf8'),name)
    s=original;edits=[]
    def change(old,new):
        nonlocal s
        assert s.count(old)==1,old[:120]
        s=s.replace(old,new);edits.append(dict(old=old,new=new))
    # COLORS is instance-owned by each newly-created C_SelectInfo. Keep the third
    # disabled state and all its input callbacks unchanged.
    palette='\t.LOCALASSIGN i#4 0\nmod_colors_loop:\n'+lr('i#4')+count()+'\tGTE\n\tIFNZ mod_colors_done\n'
    for state, rgba in enumerate([YELLOW,HOVER]):
        color=inf(lr('i#4'))+push(0)+'\tX_REF 1\n'+push(state)+'\tX_REF 1\n'
        for component,value in enumerate(rgba):palette+=write_field(color,component,push(value))
    palette+='\t.LOCALINC2 i#4\n\tJUMP mod_colors_loop\nmod_colors_done:\n'
    change('\t.LOCALASSIGN selWidth 0\n',guarded('',palette,'mod_colors')+'\t.LOCALASSIGN selWidth 0\n')
    # After native measurement, assign every root the same48px hitbox and compute
    # total height with the exact row pitch used by native positioning below.
    layout='\t.LOCALASSIGN i#4 0\nmod_height_loop:\n'+lr('i#4')+count()+'\tGTE\n\tIFNZ mod_height_done\n'
    layout+=cm(inf(lr('i#4')),27900,push(48),1)+'\t.LOCALINC2 i#4\n\tJUMP mod_height_loop\nmod_height_done:\n'
    rows=arithmetic(arithmetic(count(),arithmetic(col(),1,'SUB'),'ADD'),col(),'DIV')
    layout+=assign(1,arithmetic(arithmetic(rows,arithmetic(push(48),gap(),'ADD'),'MUL'),gap(),'SUB'))
    needle='\tPUSHLOCALPAGE\n\tPUSH 8\n\t.LOCALREF selHeight\n'
    change(needle,guarded('',layout,'mod_rows')+needle)
    # The title gets equal side padding inside the original glowing frame.
    needle='\tPUSHLOCALPAGE\n\tPUSH 15\n\t.LOCALREF lineCount\n'
    change(needle,guarded('',assign(14,arithmetic(lr('titleWidth'),48,'ADD')),'mod_title_width')+needle)
    # Skip all old table/title rectangles for the style tag; preserve the exact
    # legacy block on its original branch, including all prior colors and logic.
    start=s.index('0x9667fa:\n')+len('0x9667fa:\n')
    end=s.index('\tPUSHLOCALPAGE\n\tPUSH 33\n',start)
    change(s[start:end],guarded(s[start:end],panel(),'mod_panel'))
    # Table divider loop stays intact for every nonmod dialog; mod cells have gaps.
    start=s.index('\t.LOCALASSIGN i#3 1\n')
    end=s.index('\t.LOCALASSIGN i#4 0\n',start)
    change(s[start:end],guarded(s[start:end],'','mod_dividers'))
    # At this point final per-column width is known. Draw below the unchanged text
    # sprites, then let native anchors, hover, click codes, sound and disposal run.
    needle='\t.LOCALINC3 i#4\n\tJUMP 0x967444\n'
    change(needle,guarded('',buttons(),'mod_cell')+needle)
    needle='\tPUSH 8\n\tPUSH 8\n\t.STRUCTREF C_SelectDialog m_Title\n'
    change(needle,guarded(push(8)+push(8),push(28)+push(28),'mod_title_pos')+'\t.STRUCTREF C_SelectDialog m_Title\n')
    # The native low-level text command reads the font immediately. Temporarily
    # tint its four scalar components, then restore them so later native dialogs
    # cannot inherit yellow through the reused font reference.
    titlecolor='\t.STRUCTREF C_SelectDialog m_FontTitle\n'+push(2)+'\tX_REF 1\n'
    save='';restore=''
    for component,(local,index,value) in enumerate(zip(['columnW','columnH','count','maxLineCnt'],[3,4,9,12],YELLOW)):
        save+=assign(index,color_field(titlecolor,component))+write_field(titlecolor,component,push(value))
        restore+=write_field(titlecolor,component,lr(local))
    needle=guarded(push(8)+push(8),push(28)+push(28),'mod_title_pos')+'\t.STRUCTREF C_SelectDialog m_Title\n'
    change(needle,guarded('',save,'mod_title_tint')+needle)
    needle='\tCALLFUNC Ｐ＿構築手順＿テキストアルファブレンド\n'
    change(needle,needle+guarded('',restore,'mod_title_restore'))
    restored=s
    for item in reversed(edits):
        assert restored.count(item['new'])==1
        restored=restored.replace(item['new'],item['old'])
    assert restored==original
    (O/'patch.jam').write_text(s,encoding='utf8')
    out=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'patch.jam','-o',out,src)
    cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json')
    expected=copy.deepcopy(m);expected['functions'][27936]['address']=nm['functions'][27936]['address'];assert expected==nm
    old,new=unpack(src.read_bytes()),unpack(out.read_bytes());size=struct.unpack_from('<I',old,12)[0]
    assert old[16:16+size]==new[16:16+size]
    assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
    assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
    cmd('ain','dump','--function',name,'-o',O/'built_27936.jam',out)
    cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe',ids=[27936])
    savej(O/'native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
    pe=pact(rt)
    ev=dict(status='MOD_MENU_STYLE_STAGED',source_pointer=ptr,source_files={n:sha(rt/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},
            files={n:sha(O/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},unchanged_files={n:sha(rt/n) for n in ['NightRemasterCG.afa','NightRemasterEX.ex','NightRemaster.exe','NightRemasterFont.fnl']},
            PACT=pe,
            changed_function_ids=[27936],added_functions=0,old_CODE_STR0_MSG1_exact=True,metadata_only_one_address=True,
            reward_inventory_equip_and_input_functions_exact=True,style_tag=TYPE,renderer_edits=len(edits),
            native_gameplay_verified=False,translator_model='Codex internal',text_changes=0,
            palette=dict(normal=YELLOW,hover=HOVER,disabled='native unchanged',title='temporary then restored'),
            sources=[dict(id=i,path=str(O/f'cg_{i}.qnt'),sha256=sha(O/f'cg_{i}.qnt')) for i in [1500,1840]])
    savej(O/'reversible_edits.json',edits);savej(O/'build_evidence.json',ev)
    print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
