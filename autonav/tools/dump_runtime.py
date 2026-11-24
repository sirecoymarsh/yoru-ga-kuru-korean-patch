# -*- coding: utf-8 -*-
"""Read-only dump of the current runtime AIN (functions, globals, code) into yoru-autonav\dump."""
import os, subprocess, sys, time, json, hashlib
ALICE = r"P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe"
cur = json.load(open(r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\ui_cumulative\current.json", encoding="utf-8"))
AIN = os.path.join(cur["runtime"], "NightRemaster.ain")
OUT = r"P:\AI\yoru-autonav\dump"
h = hashlib.sha256(open(AIN, "rb").read()).hexdigest()
print("AIN", AIN, h)
for args, name in ((["-c"], "code.jam"), (["-f"], "functions.txt"), (["-g"], "globals.txt"), (["-s"], "structs.txt")):
    t0 = time.time()
    p = subprocess.run([ALICE, "ain", "dump"] + args + ["-o", os.path.join(OUT, name), AIN], capture_output=True)
    print(name, "rc", p.returncode, "%.1fs" % (time.time() - t0), os.path.getsize(os.path.join(OUT, name)) if os.path.exists(os.path.join(OUT, name)) else "n/a")
    if p.returncode:
        sys.stderr.write(p.stderr.decode("utf-8", "replace")[:2000])
open(os.path.join(OUT, "SOURCE.txt"), "w", encoding="utf-8").write(AIN + "\n" + h + "\n")
