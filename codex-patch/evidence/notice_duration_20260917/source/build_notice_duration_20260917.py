"""Patch six verified PUSH operands in existing functions, with no relocation."""
from pathlib import Path
from collections import Counter
import json,re,struct,shutil
from publish_remaster_multiplier_20260915 import read,sha,put,js
from cheat_support_20260915 import read_meta
from build_remaster_multiplier_20260915 import cmd
from repair_ui_runtime_weapon_text_20260913 import unpack,pack
from build_route_perf_20260915 import symbol

R=Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908')
O=R/'staging/notice_duration_20260917';OLD=R/'staging/notice_repair_20260917'
BASE='3b7bb70cb51caba08dc291693919554c3d35783314352eccc77f7b16ab18f8e9'
REPLACE={31880:{6000:3000},31967:{4500:2000,4000:1500},31968:{4500:2000}}
EXPECTED=Counter({(31880,6000):2,(31967,4500):2,(31967,4000):1,(31968,4500):1})

def main():
    O.mkdir(exist_ok=True);ptr=read(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert sha(src)==BASE and sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    meta=read_meta(OLD/'candidate_meta.json');source=src.read_bytes();raw=unpack(source);patched=bytearray(raw)
    code=raw[16:16+struct.unpack_from('<I',raw,12)[0]];last=None;active=False;changes=[]
    for line in (OLD/'raw.jam').open(encoding='utf8'):
        if line.startswith('FUNC '):
            fid=int(line.split()[1]);active=fid in REPLACE and last+6==meta['functions'][fid]['address'];continue
        match=re.match(r'^0x([0-9a-fA-F]+):\s*(\w+)?(?:\s+(\S+))?',line)
        if not match:continue
        last=int(match[1],16)
        if not active or match[2]!='PUSH':continue
        old=int(match[3],0)
        if old not in REPLACE[fid]:continue
        assert code[last:last+6]==struct.pack('<Hi',0,old)
        new=REPLACE[fid][old];struct.pack_into('<i',patched,16+last+2,new)
        changes.append(dict(function=fid,code_address=last,operand_offset=16+last+2,before=old,after=new))
    assert Counter((c['function'],c['before']) for c in changes)==EXPECTED
    reverted=bytearray(patched)
    for c in changes:struct.pack_into('<i',reverted,c['operand_offset'],c['before'])
    assert reverted==raw and len(patched)==len(raw)
    output=O/'NightRemaster.ain';output.write_bytes(pack(bytes(patched),source[:8]));assert unpack(output.read_bytes())==patched
    for i in REPLACE:
        name=symbol(meta,i);cmd('ain','dump','--function',name,'-o',O/f'original_{i}.jam',src)
        cmd('ain','dump','--function',name,'-o',O/f'built_{i}.jam',output)
        expected=(O/f'original_{i}.jam').read_text(encoding='utf8')
        for a,b in REPLACE[i].items():expected=expected.replace(f'\tPUSH {a}\n',f'\tPUSH {b}\n')
        assert (O/f'built_{i}.jam').read_text(encoding='utf8')==expected
    # Unchanged helper JAM is used only by the existing explicit-boundary VM.
    for f in OLD.glob('built_*.jam'):
        if not (O/f.name).exists():shutil.copy2(f,O/f.name)
    ev=dict(status='NOTICE_DURATION_STAGED',source_pointer=ptr,source_files={'NightRemaster.ain':BASE},
        files={'NightRemaster.ain':sha(output)},changes=changes,durations_ms={'chest':2000,'loot':3000,'fade':500},
        unchanged_PACT=sha(rt/'NightRemasterPact.afa'),unchanged_CG=sha(rt/'NightRemasterCG.afa'),
        six_operand_reverse_exact=True,no_relocation=True,metadata_MSG1_STR0_exact=True,semantic_text_changes=0,native_verified=False)
    put(O/'source_pointer.json',js(ptr));put(O/'build_evidence.json',js(ev));print(js(ev).decode('utf8'))

if __name__=='__main__':main()
