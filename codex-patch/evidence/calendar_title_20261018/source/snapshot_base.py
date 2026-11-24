# -*- coding: utf-8 -*-
"""Copy the runtime AIN that current.json points at into work/base and dump its metadata (-j) and raw code (--raw-code).
Reads the runtime only; refuses when the runtime is not the base this layer was designed on."""
import shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ltlib as L


def main():
    ptr, rt = L.runtime()
    src = rt / 'NightRemaster.ain'
    got = L.sha(src)
    assert got == L.BASE_AIN_SHA, ('runtime AIN is not the base', got, ptr.get('status'))
    assert ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA, ('manifest moved', ptr['manifest_sha256'])
    own = L.WORK / 'base'
    own.mkdir(parents=True, exist_ok=True)
    dst = own / 'NightRemaster.ain'
    shutil.copy2(src, dst)
    assert L.sha(dst) == L.BASE_AIN_SHA
    L.cmd('ain', 'dump', '-j', '-o', own / 'meta.json', dst, timeout=900)
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', own / 'raw_code.jam', dst, timeout=900)
    L.writej(own / 'SOURCE.json', dict(runtime=str(rt), ain_sha256=got, status=ptr['status'], manifest_sha256=ptr['manifest_sha256']))
    print('base snapshot ok', got[:16], ptr['status'])


if __name__ == '__main__':
    main()
