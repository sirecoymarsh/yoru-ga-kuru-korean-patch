# -*- coding: utf-8 -*-
"""Force speaker labels in Gemini results to one canonical Korean spelling.

화자명은 번역이 아니라 조회표다. 원문 34,091건이 서로 다른 표기 79종으로 환원되므로,
제미나이가 패킷마다 다르게 옮길 여지를 없애고 표 하나로 강제 일치시킨다.

report 모드(기본)는 아무것도 바꾸지 않고 다음을 알려준다.
  - 표로 확정되는 라벨과, 제미나이 출력이 표와 다른 건수
  - 아직 pending인 라벨에 대해 제미나이가 실제로 쓴 표기와 그 흔들림

apply 모드는 결과를 --out 디렉터리에 새로 쓴다. 입력은 절대 덮어쓰지 않는다.

  python apply_speaker_labels.py --kit <킷폴더> --results <결과폴더>
  python apply_speaker_labels.py --kit <킷폴더> --results <결과폴더> --apply --out <출력폴더>
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path

IDEO = "　"  # U+3000 ideographic space


def load_label_map(kit: Path) -> dict[str, str]:
    """stable_id -> 원문 화자명 라벨 (줄 전체가 【...】인 엔트리만)."""
    out: dict[str, str] = {}
    master = kit / "scenario_jp" / "scenario_jp_master.jsonl"
    with master.open(encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            s = d["source"]
            if s.startswith("【") and s.endswith("】") and "【" not in s[1:-1]:
                out[d["stable_id"]] = s
    return out


def render(row: dict, policy: str) -> str | None:
    core = row.get("korean_core")
    if not core:
        return None
    pad = row.get("pad_ideographic_spaces", 0) if policy == "preserve" else 0
    return "【" + core + IDEO * pad + "】"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--table", type=Path, default=Path(__file__).with_name("speaker_labels.json"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--policy", choices=["preserve", "strip"], default=None)
    a = ap.parse_args()

    if a.apply and not a.out:
        print("ERROR: --apply 에는 --out 이 필요하다 (입력을 덮어쓰지 않는다)")
        return 2

    table = json.loads(a.table.read_text(encoding="utf-8"))
    policy = a.policy or table.get("padding_policy", "preserve")
    rows = {r["source_label"]: r for r in table["labels"]}
    label_of = load_label_map(a.kit)
    print(f"화자명 엔트리 {len(label_of):,}건 / 표기 {len(rows)}종 / 패딩정책 {policy}")

    files = sorted(a.results.glob("*.json"))
    if not files:
        print(f"ERROR: 결과 파일이 없다: {a.results}")
        return 2

    total = matched = rewritten = agreed = 0
    pending_seen: dict[str, Counter] = defaultdict(Counter)
    disagree: dict[str, Counter] = defaultdict(Counter)
    missing_ids = 0

    for f in files:
        try:
            res = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  SKIP {f.name}: JSON 파싱 실패 ({e})")
            continue
        changed = False
        for e in res.get("entries", []):
            total += 1
            sid = e.get("stable_id")
            src = label_of.get(sid)
            if src is None:
                continue
            matched += 1
            row = rows.get(src)
            if row is None:
                missing_ids += 1
                continue
            got = str(e.get("target", "") or "")
            want = render(row, policy)
            if want is None:
                pending_seen[src][got] += 1
                continue
            if got == want:
                agreed += 1
            else:
                disagree[src][got] += 1
                if a.apply:
                    e["target"] = want
                    changed = True
                rewritten += 1
        if a.apply:
            a.out.mkdir(parents=True, exist_ok=True)
            dst = a.out / f.name
            dst.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            if changed:
                pass

    print(f"\n결과 엔트리 {total:,}건 중 화자명 {matched:,}건")
    print(f"  표와 일치       {agreed:,}")
    print(f"  표와 불일치     {rewritten:,}  ({'덮어씀' if a.apply else 'report 모드라 그대로 둠'})")
    if missing_ids:
        print(f"  표에 없는 라벨  {missing_ids:,}  <- 표를 다시 생성할 것")

    if disagree:
        print(f"\n=== 표와 달랐던 라벨 {len(disagree)}종 ===")
        for src, c in sorted(disagree.items(), key=lambda kv: -sum(kv[1].values()))[:25]:
            want = render(rows[src], policy)
            print(f"  {src!r} -> 정본 {want!r}")
            for got, n in c.most_common(5):
                print(f"      {n:6d}회  {got!r}")

    if pending_seen:
        print(f"\n=== 아직 표에 없는 라벨 {len(pending_seen)}종 — 제미나이가 쓴 표기 ===")
        print("    (아래에서 하나 골라 speaker_labels.json 의 korean_core 에 넣으면 확정된다)")
        for src, c in sorted(pending_seen.items(), key=lambda kv: -sum(kv[1].values())):
            n_tot = sum(c.values())
            flag = "  ⚠ 흔들림" if len(c) > 1 else ""
            print(f"  {src!r}  {n_tot}회  표기 {len(c)}종{flag}")
            for got, n in c.most_common(6):
                print(f"      {n:6d}회  {got!r}")

    if a.apply:
        print(f"\n{len(files)}개 파일을 {a.out} 에 기록했다. 원본은 건드리지 않았다.")
    else:
        print("\nreport 모드였다. 실제로 바꾸려면 --apply --out <폴더> 를 붙일 것.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
