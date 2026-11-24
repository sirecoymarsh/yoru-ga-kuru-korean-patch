#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기준 실행본 스냅숏 — ingame/base/ 로 복사하고 해시를 적는다.

Codex 가 실행본을 계속 고치므로, 빌드는 **이 사본에서만** 한다.
실행본 폴더에는 아무것도 쓰지 않는다(읽기만).
새 base 로 다시 돌리려면 이 스크립트를 다시 실행하면 된다.
"""
import os, io, json, shutil, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "base")
PTR = os.path.join(r"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908",
                   "ui_cumulative", "current.json")
FILES = ["NightRemaster.ain", "NightRemasterPact.afa", "NightRemasterEX.ex"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fp:
        for b in iter(lambda: fp.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ptr = json.load(io.open(PTR, encoding="utf-8"))
    rt = ptr["runtime"]
    os.makedirs(BASE, exist_ok=True)
    man = {"schema": "yoru-ingame-base.v1",
           "taken": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "source_runtime": rt,
           "source_pointer": ptr,
           "files": {}}
    for f in FILES:
        src = os.path.join(rt, f)
        dst = os.path.join(BASE, f)
        shutil.copy2(src, dst)
        man["files"][f] = {"sha256": sha256(dst), "size": os.path.getsize(dst)}
        print(f, man["files"][f]["sha256"][:16], man["files"][f]["size"])
    with io.open(os.path.join(BASE, "manifest.json"), "w", encoding="utf-8") as fp:
        json.dump(man, fp, ensure_ascii=False, indent=1)
    print("status:", ptr.get("status"))


if __name__ == "__main__":
    main()
