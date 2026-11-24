from __future__ import annotations

import hashlib
import json
import pathlib
import unicodedata
from typing import Iterable


WANSUNG_LEAD_RANGE = range(0xB0, 0xC9)
WANSUNG_TRAIL_RANGE = range(0xA1, 0xFF)
WANSUNG_COUNT = 2350
EXPECTED_CURRENT_MAPPING_COUNT = 1524
EXPECTED_CURRENT_WANSUNG_COUNT = 1506
EXPECTED_EXTENSION_COUNT = 844
EXPECTED_UNION_COUNT = 2368
EXPECTED_AVAILABLE_EXTENSION_CAPACITY = 1357
EXPECTED_CAPACITY_HEADROOM = 513


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: pathlib.Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: object) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(raw)


def wansung_syllables() -> list[str]:
    syllables: list[str] = []
    for lead in WANSUNG_LEAD_RANGE:
        for trail in WANSUNG_TRAIL_RANGE:
            raw = bytes((lead, trail))
            character = raw.decode("cp949")
            if not (0xAC00 <= ord(character) <= 0xD7A3):
                raise ValueError(
                    f"CP949 {raw.hex().upper()} did not decode to a Hangul syllable"
                )
            if character.encode("cp949") != raw:
                raise ValueError(f"CP949 round trip failed for {raw.hex().upper()}")
            syllables.append(character)
    if len(syllables) != WANSUNG_COUNT or len(set(syllables)) != WANSUNG_COUNT:
        raise ValueError("KS X 1001/Wansung enumeration is not exactly 2,350 unique syllables")
    return syllables


def fnl_index_to_sjis(index: int) -> bytes:
    if index < 95:
        return bytes([index + 0x20])
    if index < 158:
        return bytes([(index - 95) + 0xA1])
    value = index - 158
    lead_index = value // 188
    lead = 0x81 + lead_index if lead_index < 31 else 0xE0 + (lead_index - 31)
    trail = 0x40 + value % 188
    if trail >= 0x7F:
        trail += 1
    return bytes([lead, trail])


def validate_mapping_rows(rows: list[dict], label: str) -> None:
    if not rows:
        raise ValueError(f"{label} has no mapping rows")
    targets: set[str] = set()
    proxies: set[str] = set()
    indices: set[int] = set()
    for position, row in enumerate(rows, 1):
        target = row.get("unicode_character")
        proxy = row.get("proxy_character")
        index = row.get("proxy_index")
        proxy_hex = str(row.get("proxy_sjis_hex", "")).upper()
        if not isinstance(target, str) or len(target) != 1:
            raise ValueError(f"{label} row {position} has an invalid target")
        if not isinstance(proxy, str) or len(proxy) != 1:
            raise ValueError(f"{label} row {position} has an invalid proxy")
        if not isinstance(index, int) or index < 0:
            raise ValueError(f"{label} row {position} has an invalid index")
        expected_hex = fnl_index_to_sjis(index).hex().upper()
        if proxy_hex != expected_hex:
            raise ValueError(
                f"{label} row {position} byte/index mismatch: {proxy_hex} != {expected_hex}"
            )
        if target in targets or proxy in proxies or index in indices:
            raise ValueError(f"{label} row {position} duplicates a target/proxy/index")
        targets.add(target)
        proxies.add(proxy)
        indices.add(index)


def eligible_extension_candidates(
    capacity_document: dict,
    used_indices: set[int],
    used_proxy_characters: set[str],
    literal_target_characters: set[str],
) -> list[dict]:
    # This mirrors choose_extension_rows() in
    # build_compatible_fnl_proxy_patch.py. The capacity document was generated
    # against the same FNL and marks candidates outside its glyph count.
    glyph_count = int(capacity_document.get("maximum_glyph_count", 0))
    candidates: list[dict] = []
    seen_indices: set[int] = set()
    seen_characters: set[str] = set()
    for row in capacity_document.get("candidates", []):
        character = row.get("proxy_character", "")
        index = row.get("index")
        if not isinstance(index, int) or index < 5000 or index >= glyph_count:
            continue
        if index in used_indices or character in used_proxy_characters:
            continue
        if not row.get("canonical_roundtrip"):
            continue
        if row.get("unicode_mapping_multiplicity") != 1:
            continue
        if row.get("alice_roundtrip") is False:
            continue
        if row.get("within_fnl_glyph_count") is False:
            continue
        if row.get("alice_index_multiplicity", 1) != 1:
            continue
        if not character or not unicodedata.name(character, "").startswith(
            "CJK UNIFIED IDEOGRAPH-"
        ):
            continue
        if character in literal_target_characters:
            continue
        if index in seen_indices or character in seen_characters:
            raise ValueError(f"Duplicate eligible candidate at index {index}")
        seen_indices.add(index)
        seen_characters.add(character)
        candidates.append(row)
    candidates.sort(key=lambda row: row["index"], reverse=True)
    return candidates


def expected_extension_rows(
    current_rows: list[dict], capacity_document: dict, targets: Iterable[str]
) -> tuple[list[str], list[dict], list[dict]]:
    target_characters = set(targets)
    current_targets = {row["unicode_character"] for row in current_rows}
    missing = sorted(target_characters - current_targets, key=ord)
    candidates = eligible_extension_candidates(
        capacity_document,
        {row["proxy_index"] for row in current_rows},
        {row["proxy_character"] for row in current_rows},
        target_characters,
    )
    if len(candidates) < len(missing):
        raise ValueError(
            f"Insufficient extension capacity: need {len(missing)}, have {len(candidates)}"
        )
    rows: list[dict] = []
    for target, candidate in zip(missing, candidates, strict=False):
        index = candidate["index"]
        expected_hex = fnl_index_to_sjis(index).hex().upper()
        candidate_hex = str(
            candidate.get("alice_sjis_hex", candidate.get("sjis_hex", ""))
        ).upper()
        if candidate_hex != expected_hex:
            raise ValueError(f"Candidate {index} byte/index mismatch")
        rows.append(
            {
                "unicode_character": target,
                "unicode_codepoint": f"U+{ord(target):04X}",
                "proxy_character": candidate["proxy_character"],
                "proxy_codepoint": f"U+{ord(candidate['proxy_character']):04X}",
                "proxy_index": index,
                "proxy_sjis_hex": expected_hex,
                "proxy_encoder": (
                    "alice-tools-libiconv"
                    if "alice_sjis_hex" in candidate
                    else "python-cp932"
                ),
            }
        )
    return missing, candidates, rows


def assert_expected_counts(
    current_rows: list[dict], current_wansung: set[str], missing: list[str], candidates: list[dict]
) -> None:
    actual = {
        "current_mapping_count": len(current_rows),
        "current_wansung_count": len(current_wansung),
        "extension_count": len(missing),
        "union_count": len(current_rows) + len(missing),
        "available_extension_capacity": len(candidates),
        "capacity_headroom": len(candidates) - len(missing),
    }
    expected = {
        "current_mapping_count": EXPECTED_CURRENT_MAPPING_COUNT,
        "current_wansung_count": EXPECTED_CURRENT_WANSUNG_COUNT,
        "extension_count": EXPECTED_EXTENSION_COUNT,
        "union_count": EXPECTED_UNION_COUNT,
        "available_extension_capacity": EXPECTED_AVAILABLE_EXTENSION_CAPACITY,
        "capacity_headroom": EXPECTED_CAPACITY_HEADROOM,
    }
    if actual != expected:
        raise ValueError(f"Pinned count mismatch: actual={actual}, expected={expected}")
