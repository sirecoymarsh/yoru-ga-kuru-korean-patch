"""Reuse existing, approved rest-button clean plates unchanged; no pixel editing."""
from pathlib import Path
import copy,json,shutil
import numpy as np
from PIL import Image,ImageDraw
from cheat_support_20260915 import R,sha,savej,cmd
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,txt_info
from build_mod_tab_20260915 import scalar
from verify_mod_menu_style_20260917 import Font

O=R/'staging/native_mod_button_20260917';FILES=['NightRemasterPact.afa','NightRemasterCG.afa'];BASE='39d0915ee3475441f6526a023b4a64989a4388190f07e2e62d5cbf8e8cbc5bc8'
PREFIX='シス／探索／ボタン／休憩／休憩'
def main():
    O.mkdir(exist_ok=True);ptr=json.loads((R/'ui_cumulative/current.json').read_text(encoding='utf8'));rt=Path(ptr['runtime'])
    assert sha(rt/FILES[0])==BASE and sha(Path(ptr['manifest']))==ptr['manifest_sha256'];savej(O/'source_pointer.json',ptr)
    records=json.loads((R/'ui_adjacent_repair/manifest.json').read_text(encoding='utf8'))['records'];f=Font(rt/'NightRemasterFont.fnl');assets=[];append=[]
    states=[('通常',1671),('オン',1668),('ダウン',1669),('無効',1670)]
    # Convert the persisted text-free native rest states byte-for-pixel; do not redraw.
    for state,idx in states:
        r=next(r for r in records if r['id']==idx);src=Path(r['source_png']);clean=Path(r['clean_plate']);mask=Path(r['source_mask'])
        assert sha(src)==r['source_sha256'] and r['protected_pixel_changes']==0
        original=np.array(Image.open(src).convert('RGBA'));plate=np.array(Image.open(clean).convert('RGBA'));owned=np.array(Image.open(mask).convert('L'))>0
        assert original.shape==plate.shape==(55,116,4) and not np.any(np.any(original!=plate,axis=2)&~owned)
        frozen=O/f'clean_{idx}.png';shutil.copy2(clean,frozen);out=O/f'blank_{idx}.qnt';cmd('cg','convert',frozen,out)
        reopened=O/f'reopened_{idx}.png';cmd('cg','convert',out,reopened);assert np.array_equal(plate,np.array(Image.open(reopened).convert('RGBA')))
        name=PREFIX+'／'+state+'.qnt';append.append((name,out));assets.append(dict(id=idx,state=state,name=name,source_sha256=sha(src),clean_sha256=sha(clean),payload_sha256=sha(out),canvas=[116,55],protected_diff=0,unchanged_clean_plate=True,source=str(src),clean_plate=str(clean)))
    cg=rebuild(rt/'NightRemasterCG.afa',O/'NightRemasterCG.afa',{},append)
    arc=read_afa3(rt/'NightRemasterPact.afa');repl={};buttons=[]
    for idx,rn,bn in [(153,'KR_AutoEquipRoot','KR_AutoEquipButton'),(154,'KR_AutoStoneRoot','KR_AutoStoneButton'),(161,'KR_SweepRoot','KR_SweepButton')]:
        e=arc.entries[idx];p=O/f'original_{idx}.pactex'
        with (rt/'NightRemasterPact.afa').open('rb') as stream:stream.seek(e.absolute_offset);p.write_bytes(stream.read(e.size))
        d=ex.decode_ex(p);g=part(d,rn);b=part(d,bn);lab=part(d,bn+'Label');r=txt_info(g);width=scalar(val(r,'右上').items[0].value.payload)
        if idx==161:
            # Native rest271 -> item326 -> sweep381: identical116x55 canvas, pitch55.
            width=116;setlist(g,'座標',[1142,381,40])
        height=55 if idx==161 else 42
        setlist(r,'右上',[width,0]);setlist(r,'左下',[0,height]);setlist(r,'右下',[width,height]);setlist(b,'拡大縮小',[width/116,height/55])
        info=child(b,'種類別情報')
        for native,state in [('通常状態','通常'),('オンカーソル状態','オン'),('キーダウン状態','ダウン')]:ss(child(info,native),'ＣＧ名',PREFIX+'／'+state)
        label=val(txt_info(lab),'テキスト').value
        from audit_dynamic_ui_20260915 import decode
        t=decode(label);size=scalar(val(child(txt_info(lab),'テキスト装飾'),'フォントサイズ'));w,h=f.metrics(t,size)
        setlist(lab,'座標',[(width-w)/2,(height-h)/2,2]);assert w<=width-24
        buttons.append(dict(entry=idx,root=rn,button=bn,text=t,canvas=[width,height],scale=[width/116,height/55],text_xy=[(width-w)/2,(height-h)/2],font_size=size,click_id_unchanged=True))
        out=O/f'pact_{idx}.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(out).serialize_payload()==d.serialize_payload();repl[idx]=out
    pact=rebuild(rt/'NightRemasterPact.afa',O/'NightRemasterPact.afa',repl)
    ev=dict(status='NATIVE_MOD_BUTTON_STAGED',source_pointer=ptr,source_files={n:sha(rt/n) for n in FILES},files={n:sha(O/n) for n in FILES},patched_existing=[],added_functions={},PACT=dict(archive=pact,buttons=buttons),CG=cg,assets=assets,ain_unchanged_sha256=sha(rt/'NightRemaster.ain'),save_schema_changes=0,old_CODE_STR0_MSG1_exact=True,native_verified=False,translator_model='Codex internal')
    savej(O/'build_evidence.json',ev)
    # A code-native UI reconstruction only; final QNT payloads stay exactly the clean plate.
    sheet=Image.new('RGBA',(540,185),(7,12,24,255));draw=ImageDraw.Draw(sheet)
    for j,(state,idx) in enumerate(states[:3]):
        x=15+j*178;draw.text((x,5),{'通常':'NORMAL','オン':'HOVER','ダウン':'PRESSED'}[state],fill='white')
        source=next(r for r in records if r['id']==idx);rest=Image.open(source['final_png']).convert('RGBA');sheet.alpha_composite(rest,(x,25))
        clean=Image.open(O/f'reopened_{idx}.png').convert('RGBA');sheet.alpha_composite(clean,(x,95));b=buttons[-1];f.text(sheet,b['text'],x+b['text_xy'][0],95+b['text_xy'][1],b['font_size'],(255,224,96,255))
    sheet.save(O/'rest_sweep_comparison.png')
    savej(O/'verification.json',dict(status='NATIVE_MOD_BUTTON_COMPILED_PASS',files=ev['files'],original_CG_entries_unchanged=True,new_CG_states=4,clean_to_payload_pixel_diff=0,original_protected_pixel_diff=0,original_rest_canvas_preserved=True,button_keys_callbacks_unchanged=True,ain_unchanged=True,all_three_PACT_entries_reparsed=True,native_verified=False))
    print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
