"""Audit active AIN instruction sites against this game's actual x86 dispatch table."""
from pathlib import Path
import re,struct,hashlib
import pefile
from integrate_ui_opening_20260913 import read_meta
from repair_ui_runtime_weapon_text_20260913 import unpack

def native_lower(jam):
    jam=re.sub(r'(?m)^\tF_PUSH ([-+0-9.eE]+)$',lambda m:'\tPUSH '+str(struct.unpack('<i',struct.pack('<f',float(m[1])))[0]),jam)
    # The native .LOCALCREATE macro already deletes the existing local before NEW.
    jam=re.sub(r'(?m)^\tSH_LOCALDELETE (\w+)\n\tSH_LOCALCREATE \1 ([^\n]+)$',lambda m:'\t.LOCALCREATE '+m[1]+' '+m[2],jam)
    assert not re.search(r'(?m)^\t(?:F_PUSH|SH_LOCALCREATE|SH_LOCALDELETE)\b',jam)
    return jam

def audit(ain,meta,raw_jam,exe,ids=None):
    pe=pefile.PE(exe);base=pe.OPTIONAL_HEADER.ImageBase
    # Hard bind the dispatch code layout instead of trusting remembered opcodes.
    assert base==0x400000
    assert pe.get_data(0x667f40-base,6)==bytes.fromhex('81 f9 10 01 00 00')
    assert pe.get_data(0x667f4c-base,7)==bytes.fromhex('0f b6 81 dc 8a 66 00')
    assert pe.get_data(0x667f53-base,7)==bytes.fromhex('ff 24 85 20 89 66 00')
    table=pe.get_data(0x668adc-base,0x111);targets=pe.get_data(0x668920-base,444)
    def target(op):return struct.unpack_from('<I',targets,table[op]*4)[0] if op<=0x110 else 0x66888d
    assert target(0)==0x667f69 and all(target(op)==0x66888d for op in [64,129,130])
    m=read_meta(meta);raw=unpack(Path(ain).read_bytes());code=raw[16:16+struct.unpack_from('<I',raw,12)[0]]
    last=None;fid=None;active=False;unsupported=[];seen=set();count=0;opnames={}
    for line in Path(raw_jam).read_text(encoding='utf8').splitlines():
        if line.startswith('FUNC '):
            fid=int(line.split()[1]);active=(ids is None or fid in ids) and last+6==m['functions'][fid]['address']
            if active:seen.add(fid)
            continue
        z=re.match(r'^0x([0-9A-Fa-f]+):\s*(\w+)?',line)
        if not z:continue
        addr=int(z[1],16);last=addr
        if not active or z[2] in [None,'FUNC','EOF','ENDFUNC']:continue
        op=struct.unpack_from('<H',code,addr)[0];count+=1;opnames[str(op)]=z[2]
        if target(op)==0x66888d:unsupported.append(dict(fid=fid,address=addr,opcode=op,name=z[2]))
    if ids is not None:assert seen==set(ids),(set(ids)-seen)
    else:
        concrete={f['index'] for f in m['functions'] if f['address']!=0xffffffff}
        assert seen==concrete,('Uncovered executable metadata entries',sorted(concrete-seen))
    return dict(engine_sha256=hashlib.sha256(Path(exe).read_bytes()).hexdigest(),ain_sha256=hashlib.sha256(Path(ain).read_bytes()).hexdigest(),native_dispatch='0x667ef0/map0x668adc/table0x668920/default0x66888d',active_functions=len(seen),instruction_sites=count,opcodes=opnames,unsupported=unsupported,all_active_opcodes_supported=not unsupported)
