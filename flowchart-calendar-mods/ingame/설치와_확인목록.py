#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingame/설치와_확인목록.md 를 쓴다(해시를 그때그때 박아 넣는다)."""
import io, os, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


base = json.load(io.open(os.path.join(HERE, "base", "manifest.json"), encoding="utf-8"))
cands = {}
for d in ("candidate", "candidate_test"):
    p = os.path.join(HERE, d)
    if os.path.isdir(p):
        cands[d] = json.load(io.open(os.path.join(p, "manifest.json"), encoding="utf-8"))

B = base["files"]
rt = base["source_runtime"]

TEXT = """# 설치와 확인 목록 — 게임 안 「검수」 장면 재생 (1·2단계)

**아직 설치하지 않았습니다. 아래는 사용자가 직접 하는 절차입니다.**
저는 게임을 돌리지 않았고 실행본·세이브 폴더에 아무것도 쓰지 않았습니다.

---

## 0. 이 후보가 무엇인가

- 회상(메모리얼) 화면에 들어가면 **「검수」 메뉴**가 뜹니다. 거기서
  - 번호로 장면 재생 (예: 10001)
  - 달·갈래로 찾기 → 장면 고르기 → 재생
  - 최근 재생 목록
  을 할 수 있습니다. 끝나면 회상 화면으로 돌아옵니다.
- 장면 실행은 원작 개발자 실행기가 하는 두 줄과 **글자 그대로 같습니다**
  (`LSys3xScript::PrepareSys(이름)` → `RunEvent()`).
- **바꾸는 파일은 `NightRemaster.ain` 하나뿐**입니다. PACT·EX 는 건드리지 않았습니다.

## 1. 바꾸기 전에 — 기준이 맞는지

이 후보는 아래 실행본에서 뜬 사본으로 만들었습니다.

```
runtime : {rt}
NightRemaster.ain      {ain}
NightRemasterPact.afa  {pact}
NightRemasterEX.ex     {ex}
```

**지금 실행본의 세 파일 해시가 위와 같은지 먼저 보세요.** 다르면 Codex 가 그새 실행본을 고친 것이니,
이 후보를 넣지 말고 저에게 다시 빌드를 시키세요(`ingame/snapshot_base.py` → `ingame/build_ingame.py`).

PowerShell 로 해시 보기:

```
Get-FileHash -Algorithm SHA256 "<runtime>\\NightRemaster.ain","<runtime>\\NightRemasterPact.afa","<runtime>\\NightRemasterEX.ex"
```

## 2. 어느 판을 넣을까

| 판 | 폴더 | 언제 |
|---|---|---|
| 배포용 | `ingame/candidate/` | 공통 설정 **슬롯 80** 이 켜져야 검수 메뉴가 뜬다. 지금 실행본에서는 슬롯 80 을 켜는 장치가 아직 없다(아래 5절) |
| **시험용** | `ingame/candidate_test/` | **늘 켜져 있다.** 지금 눈으로 확인하려면 이것을 넣으세요 |

```
{cand_table}
```

## 3. 설치 (사용자)

1. **게임을 완전히 끕니다.** (돌아가는 중에 바꾸면 안 됩니다)
2. 실행본 폴더에서 원본을 백업합니다 — 이름에 해시 앞 8자리를 붙입니다:
   ```
   NightRemaster.ain  →  NightRemaster.ain.{ain8}.bak
   ```
3. 후보의 `NightRemaster.ain` 을 실행본 폴더에 덮어씁니다.
4. 덮어쓴 파일의 해시가 위 표의 값과 같은지 봅니다.
5. 되돌리려면 `.bak` 을 다시 덮어쓰면 됩니다(해시가 1번의 값으로 돌아오는지 확인).

## 4. 실기에서 볼 것 (사용자)

- [ ] **게임이 평소처럼 켜지고 타이틀·이어하기가 된다** (가장 먼저)
- [ ] 회상(메모리얼) 화면에 들어가면 **「검수 — 장면 재생」** 창이 뜬다
- [ ] 「회상 화면으로」를 고르면 **원래 회상 화면이 그대로** 뜬다
- [ ] 기존 **7쪽 76칸이 그대로**이고, 열리던 칸이 그대로 열린다
- [ ] 「번호로 장면 재생」 → 10001 입력 → 확인창에 `ＥＶ／元／E10001` 과 읽음 표시가 보인다
- [ ] 「재생」을 누르면 그 장면이 뜨고, **끝나면 회상 화면으로 돌아온다**
- [ ] 없는 번호(예: 99998)를 넣으면 「그 번호의 장면이 없습니다.」 가 뜬다
- [ ] 「달·갈래로 찾기」 → 달 → 갈래 → 목록에 번호와 읽음 표시가 보이고, 골라서 재생된다
- [ ] 목록의 「이전/다음」이 동작한다
- [ ] **글자가 깨지지 않는다**(네모·물음표·이상한 한자가 없다)
- [ ] 「최근 재생 목록」에 방금 본 장면이 남는다
- [ ] 배포용 판을 넣었다면: 검수 메뉴가 **뜨지 않는다**(기본 꺼짐이 맞는지)

### 미리 알아 둘 것

- 재생한 장면은 **읽음으로 기록되고 회상도 열립니다**(원작 실행기와 같은 경로라 그렇습니다).
  친밀도를 올리는 장면 25개는 **친밀도도 오릅니다**. → **검수용 세이브 슬롯을 따로 쓰세요.**
- 한 장면을 부르면 **이어지는 장면까지 잇달아 돕니다**(원작이 그렇게 만들어져 있고, 릴리스에서는 끌 수 없습니다).
- 날짜·파티·친밀도를 맞춰 주지 않습니다(원작 개발자 실행기도 안 합니다). 배경이 어색할 수 있습니다.

## 5. 배포판에서 숨기기 — 남은 한 가지

- 검수 메뉴는 `KR_Flag(80) != 0` 일 때만 뜨도록 되어 있습니다(슬롯 80 은 Codex 가 쓰는 72~79 와 겹치지 않음을 실행본 코드에서 확인했습니다).
- 그런데 **기준 실행본의 `KR_Flag`·`KR_Poke` 는 아직 속이 빈 함수**입니다
  (`current.json` 의 상태가 `…NATIVE_PENDING` — Codex 의 네이티브 단계가 아직 안 들어간 스냅숏).
  그래서 지금은 슬롯 80 을 켤 방법이 없고, 시험용 판으로만 확인할 수 있습니다.
- Codex 의 네이티브 단계가 들어오면 모드 탭에 토글 한 줄만 붙이면 됩니다:
  켤 때 `KR_ChartSetEnabled(true)`, 끌 때 `KR_ChartSetEnabled(false)`.
  계약은 `ingame/required_flowchart.json` 에 적어 두었습니다.

## 6. 무엇이 바뀌었나 (정적 검사로 확인한 것)

- 고친 원작 함수: **`C_SceneModeScene@Run` 하나**, 맨 앞에 `CALLFUNC KR_ChartEntry` 한 줄.
- 더한 함수 **{nfunc}개** (전부 `KR_Chart…`), 더한 전역 **6개**.
- **대사(MSG1)는 한 바이트도 안 바뀌었습니다.** 문자열 표는 기존 항목이 그대로고 화면 문구만 뒤에 붙었습니다.
- 구조체·기존 전역·기존 함수 이름 그대로. PACT·EX 는 손대지 않았습니다.
- 검사 한 명령: `python checks/stage_ingame.py` (결함 심기 증명은 `--selftest`).
"""

rows = []
for d, m in cands.items():
    for f, info in m["files"].items():
        rows.append("%-16s %s  %s" % (d, f, info["sha256"]))

out = TEXT.format(
    rt=rt,
    ain=B["NightRemaster.ain"]["sha256"],
    pact=B["NightRemasterPact.afa"]["sha256"],
    ex=B["NightRemasterEX.ex"]["sha256"],
    ain8=B["NightRemaster.ain"]["sha256"][:8],
    cand_table="\n".join(rows),
    nfunc=len(list(cands.values())[0]["added_functions"]),
)
p = os.path.join(HERE, "설치와_확인목록.md")
io.open(p, "w", encoding="utf-8", newline="\n").write(out)
print("wrote", p, len(out))
