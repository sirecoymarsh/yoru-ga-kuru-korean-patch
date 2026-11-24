"""Claude Opus 5.5 (2026-09-24) r5: the r3 native probes (input/term/legacy-migration checks) run unchanged
against the r7 candidate (with the staged EX). Same probe AIN construction, own folder, own SaveFolder, muted; user saves only read.
  python probe_claude_term_rate_20260924_r7.py            -> r7 staging/native_probe_result.json
  python probe_claude_term_rate_20260924_r7.py --legacy   -> r7 staging/native_probe_legacy_result.json
"""
import build_claude_term_rate_20260924_r7 as e
import probe_claude_term_rate_20260924 as c
c.e=e;c.O=e.O;c.ROOT=e.O/'native_probe'
import shutil
_setup=c.setup_folder
def setup_with_staged_ex():
    _setup()
    for n in ['NightRemasterEX.ex']:shutil.copy2(e.O/n,c.ROOT/n);shutil.copy2(e.O/n,c.ROOT/n.replace('NightRemaster',c.BOOT,1))
c.setup_folder=setup_with_staged_ex
if __name__=='__main__':c.main()
