"""Claude Opus 5.5 (2026-09-24) r4: the r3 native probes (input/term/legacy-migration checks) run unchanged
against the r4 candidate. Same probe AIN construction, own folder, own SaveFolder, muted; user saves only read.
  python probe_claude_term_rate_20260924_r4.py            -> r4 staging/native_probe_result.json
  python probe_claude_term_rate_20260924_r4.py --legacy   -> r4 staging/native_probe_legacy_result.json
"""
import build_claude_term_rate_20260924_r4 as e
import probe_claude_term_rate_20260924 as c
c.e=e;c.O=e.O;c.ROOT=e.O/'native_probe'
if __name__=='__main__':c.main()
