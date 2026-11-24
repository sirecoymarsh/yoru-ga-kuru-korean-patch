from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import Counter


def fnl_char_to_index(encoded: bytes) -> int | None:
    if len(encoded) == 1:
        code = encoded[0]
        if code < 0x20:
            return 0
        if code < 0x7F:
            return code - 0x20
        if code < 0xA1:
            return None
        if code < 0xE0:
            return code - 0x42
        return None
    if len(encoded) != 2:
        return None
    first, second = encoded
    if second < 0x40 or second == 0x7F or second > 0xFC:
        return None
    second_index = second - (0x40 + (1 if second > 0x7F else 0))
    if 0x81 <= first < 0xA0:
        first_index = first - 0x81
    elif 0xE0 <= first < 0xFD:
        first_index = (first - 0xE0) + 31
    else:
        return None
    return 158 + first_index * 188 + second_index


def scan_project_text(project: pathlib.Path) -> tuple[set[str], dict[str, int]]:
    files = [
        project / "extracted" / "ain" / "NightRemaster_text.txt",
        project / "extracted" / "ain" / "NightRemaster_filenames.txt",
        project / "extracted" / "ex" / "NightRemasterEX.x",
        project / "extracted" / "timemap_sound" / "timemap_sound.ex.x",
        project / "extracted" / "timemap_voice" / "timemap_voice.ex.x",
    ]
    files.extend(sorted((project / "extracted" / "pact").rglob("*.x")))
    characters: set[str] = set()
    file_sizes: dict[str, int] = {}
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        characters.update(text)
        file_sizes[str(path.relative_to(project))] = len(text)
    return characters, file_sizes


def canonical_cp932_proxies(max_glyph_count: int) -> list[dict]:
    rows = []
    duplicate_unicode = Counter()
    for first in list(range(0x81, 0xA0)) + list(range(0xE0, 0xFD)):
        for second in range(0x40, 0xFD):
            if second == 0x7F:
                continue
            encoded = bytes([first, second])
            index = fnl_char_to_index(encoded)
            if index is None or index >= max_glyph_count:
                continue
            try:
                char = encoded.decode("cp932")
            except UnicodeDecodeError:
                continue
            if len(char) != 1:
                continue
            duplicate_unicode[char] += 1
            try:
                roundtrip = char.encode("cp932")
            except UnicodeEncodeError:
                continue
            rows.append(
                {
                    "index": index,
                    "sjis_hex": encoded.hex().upper(),
                    "proxy_character": char,
                    "roundtrip_hex": roundtrip.hex().upper(),
                    "canonical_roundtrip": roundtrip == encoded,
                }
            )
    for row in rows:
        row["unicode_mapping_multiplicity"] = duplicate_unicode[row["proxy_character"]]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--max-glyph-count", type=int, default=8994)
    args = parser.parse_args()
    project = args.project_dir.resolve()

    used_characters, scanned_files = scan_project_text(project)
    used_indices: set[int] = set()
    cp932_used_characters = 0
    for char in used_characters:
        try:
            encoded = char.encode("cp932")
        except UnicodeEncodeError:
            continue
        index = fnl_char_to_index(encoded)
        if index is not None and index < args.max_glyph_count:
            cp932_used_characters += 1
            used_indices.add(index)

    proxy_rows = canonical_cp932_proxies(args.max_glyph_count)
    candidates = [
        row
        for row in proxy_rows
        if row["canonical_roundtrip"] and row["index"] not in used_indices
    ]
    candidates.sort(
        key=lambda row: (
            row["unicode_mapping_multiplicity"] != 1,
            row["index"],
        )
    )
    result = {
        "schema": "yorugakuru.proxy-capacity.v1",
        "project_dir": str(project),
        "scanned_files": scanned_files,
        "scanned_file_count": len(scanned_files),
        "unique_source_character_count": len(used_characters),
        "cp932_used_character_count": cp932_used_characters,
        "used_fnl_index_count": len(used_indices),
        "maximum_glyph_count": args.max_glyph_count,
        "decoded_two_byte_proxy_count": len(proxy_rows),
        "canonical_roundtrip_proxy_count": sum(
            row["canonical_roundtrip"] for row in proxy_rows
        ),
        "unused_canonical_proxy_count": len(candidates),
        "capacity_verdict": (
            "candidate"
            if len(candidates) >= 2500
            else "needs_display-only_reservation_audit"
        ),
        "input_fingerprint": hashlib.sha256(
            "\n".join(
                f"{name}:{size}" for name, size in sorted(scanned_files.items())
            ).encode("utf-8")
        ).hexdigest(),
        "candidates": candidates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp.replace(args.output)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "candidates"},
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
