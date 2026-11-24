"""Scope a navy, padded confirmation to sweep only. Never writes the live game."""
from pathlib import Path
import copy,json,re,struct
from build_remaster_multiplier_20260915 import cmd,read_meta,encode
from build_instant_loot_20260915 import clean
from build_dungeon_sweep_20260916 import S,push,cf,lr,cm,assign,field
from repair_ui_runtime_weapon_text_20260913 import unpack,strings
from audit_sys43_native_opcodes_20260915 import audit
from cheat_support_20260915 import R,sha,savej

O=R/'staging/sweep_ui_20260916'
TYPE=2026091602
STATUS='SWEEP_UI_STATIC_PASS_NATIVE_PENDING'
TITLE='자동 소탕 · 남은 탐색 시간 %d\n　현재 층 기준: 전투 %d회 / 보물상자 %d개\n　보상 배율 적용 · 전투/함정 피해 없음\n　남은 시간을 모두 쓰고 다음 날로 진행할까요?'
PALETTE={(255,255,255,255):(139,180,244,255),(0,50,16,255):(8,16,42,255),(0,177,57,255):(18,32,64,255),(31,80,70,192):(12,24,52,238)}

def pick(old,new,label):
    return ('\tPUSHSTRUCTPAGE\n\tPUSH 27908\n\tCALLMETHOD 0\n'+push(TYPE)+
            '\tEQUALE\n\tIFZ '+label+'_old\n'+new+'\tJUMP '+label+'_end\n'+
            label+'_old:\n'+old+label+'_end:\n')

def main():
    O.mkdir(parents=True,exist_ok=True)
    ptr=json.loads((R/'ui_cumulative/current.json').read_text()); rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert sha(src)=='5429a0f4c2e50342e852e0c2e0279d8a5c6471571110b899ba7984e49eddb822'
    assert sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    cmd('ain','dump','-j','-o',O/'source_meta.json',src);m=read_meta(O/'source_meta.json')
    names={31892:'KR_SweepConfirm',27936:'C_SelectDialog@CreateParts'}
    for i,n in names.items():cmd('ain','dump','--function',n,'-o',O/f'original_{i}.jam',src)
    flags='\t.GLOBALREF Flags\n';g='\t.GLOBALREF g_MainSelect\n'
    title=S(TITLE)+lr('remaining')+'\tS_MOD 2\n'+lr('remaining')+push(40)+'\tDIV\n\tS_MOD 2\n'+lr('remaining')+push(200)+'\tDIV\n\tS_MOD 2\n'
    body=assign(1,cm(flags,26512))+cm(flags,26514,push(1),1)+title+cf('■選択ダイアログ／タイトル設定')
    body+=push(TYPE)+cf('■選択ダイアログ／タイプ設定')
    # Per-instance typography; no global font, serialized structure, or other dialogs changed.
    for fld in [6,7]:
        body+=field(g,fld)+push(1)+push(24)+'\tX_ASSIGN 1\n\tPOP\n'
        body+=field(g,fld)+push(4)+push(1065353216)+'\tX_ASSIGN 1\n\tPOP\n' # EdgeWeight=1.0
    body+=field(g,8)+push(1)+push(1090519040)+'\tX_ASSIGN 1\n\tPOP\n' # MarginTitle.height=8.0
    body+=push(2)+cf('■選択ダイアログ／横項目数')
    for code,label in [(12,'취소'),(11,'소탕 실행')]:body+=push(code)+S(label)+S('')+push(0)+cf('■選択ダイアログ／選択肢追加')
    body+=cf('■選択ダイアログ／クリック制限／全体')+assign(2,push(1)+push(0)+cf('■選択ダイアログ／実行'))
    body+=cm(flags,26514,lr('previousLock'),1)+lr('result')+push(11)+'\tEQUALE\n\tRETURN\n'
    confirm='FUNC 31892\n'+body+'ENDFUNC KR_SweepConfirm\n'
    original=clean((O/'original_27936.jam').read_text(encoding='utf8'),names[27936]);draw=original;count=0;reverts=[]
    # Existing geometry, events and cleanup retained. Only tagged sweep instance is styled.
    pattern=r'(\tPUSH (\d+)\n\tPUSH (\d+)\n\tPUSH (\d+)\n\tPUSH (\d+)\n)(?=\tCALLFUNC CASConstructionProcess::Fill#3)'
    def color(z):
        nonlocal count
        old=tuple(map(int,z.groups()[1:]));assert old in PALETTE,old
        count+=1;replacement=pick(z[1],''.join(push(v) for v in PALETTE[old]),f'sweep_color_{count}');reverts.append((replacement,z[1]));return replacement
    draw=re.sub(pattern,color,draw);assert count==9,count
    needle='\t.LOCALREF titleHeight\n\tPUSH 24\n\tADD\n'
    assert draw.count(needle)==1
    extra='\t.LOCALREF titleHeight\n'+pick(push(24),push(48),'sweep_padding')+'\tADD\n'
    draw=draw.replace(needle,extra);reverts.append((extra,needle))
    restored=draw
    for new,old in reversed(reverts):assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==original
    (O/'patch.jam').write_text(confirm+'\n'+draw,encoding='utf8');out=O/'NightRemaster.ain'
    cmd('ain','edit','--jam',O/'patch.jam','-o',out,src);cmd('ain','dump','-j','-o',O/'candidate_meta.json',out)
    nm=read_meta(O/'candidate_meta.json');expected=copy.deepcopy(m)
    for i in names:expected['functions'][i]['address']=nm['functions'][i]['address']
    assert expected==nm
    old=unpack(src.read_bytes());new=unpack(out.read_bytes());os=struct.unpack_from('<I',old,12)[0]
    assert old[16:16+os]==new[16:16+os]
    assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
    assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
    for i,n in names.items():cmd('ain','dump','--function',n,'-o',O/f'built_{i}.jam',out)
    cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe',ids=list(names));savej(O/'native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
    ev=dict(status=STATUS,source_pointer=ptr,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},
        unchanged_files={n:sha(rt/n) for n in ['NightRemasterPact.afa','NightRemasterEX.ex','NightRemaster.exe','NightRemasterFont.fnl']},
        AIN=dict(patched_existing=sorted(names),new_functions=0,old_CODE_STR0_MSG1_exact=True,metadata_only_two_addresses=True,save_schema_unchanged=True),
        translator_model='Codex internal',native_gameplay_verified=False,scope='Confirmation only; all reward, trap, multiplier, scope and day-transition functions unchanged.',
        title=TITLE,style_tag=TYPE,font_size=24,outline_pixels=1,line_spacing=8,title_padding=48,color_sites=count,non_sweep_render_logic_unchanged=True)
    savej(O/'build_evidence.json',ev);savej(O/'style_branch_evidence.json',dict(colors=[dict(old=list(k),new=list(v)) for k,v in PALETTE.items()],reversible_source_edits=len(reverts),non_sweep_exact=True))
    print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
