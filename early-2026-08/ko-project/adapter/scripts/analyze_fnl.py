from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
from collections import Counter
from dataclasses import dataclass


@dataclass
class Reader:
    data: bytes
    offset: int = 0

    def take(self, fmt: str) -> tuple[int, ...]:
        size = struct.calcsize(fmt)
        if self.offset + size > len(self.data):
            raise ValueError(f"FNL index truncated at offset {self.offset}")
        values = struct.unpack_from(fmt, self.data, self.offset)
        self.offset += size
        return values


def fnl_index_to_sjis(index: int) -> bytes:
    if index < 95:
        return bytes([index + 0x20])
    if index < 158:
        return bytes([(index - 95) + 0xA1])
    value = index - 158
    first_index = value // 188
    if first_index < 31:
        first = 0x81 + first_index
    else:
        first = 0xE0 + (first_index - 31)
    second = 0x40 + value % 188
    if second >= 0x7F:
        second += 1
    return bytes([first, second])


def decode_proxy(index: int) -> str | None:
    encoded = fnl_index_to_sjis(index)
    try:
        decoded = encoded.decode("cp932")
    except UnicodeDecodeError:
        return None
    if len(decoded) != 1:
        return None
    return decoded


def analyze(path: pathlib.Path) -> dict:
    raw = path.read_bytes()
    if len(raw) < 16:
        raise ValueError("FNL file is too small")
    magic, unknown, declared_filesize, index_size = struct.unpack_from("<4sIII", raw, 0)
    if magic != b"FNA\x00":
        raise ValueError(f"Unexpected FNL magic: {magic!r}")
    index_start = 16
    index_end = index_start + index_size
    if index_end > len(raw):
        raise ValueError("FNL index extends beyond end of file")
    reader = Reader(raw[index_start:index_end])
    (font_count,) = reader.take("<I")
    fonts = []
    all_glyph_counts: Counter[int] = Counter()
    all_nonempty_counts: Counter[int] = Counter()

    for font_index in range(font_count):
        (face_count,) = reader.take("<I")
        faces = []
        for face_index in range(face_count):
            height, face_unknown, glyph_count = reader.take("<III")
            nonempty = 0
            compressed_bytes = 0
            invalid_ranges = 0
            for glyph_index in range(glyph_count):
                width, data_pos, data_compsize = reader.take("<HII")
                all_glyph_counts[glyph_index] += 1
                if data_pos:
                    nonempty += 1
                    all_nonempty_counts[glyph_index] += 1
                    compressed_bytes += data_compsize
                    if data_pos + data_compsize > len(raw):
                        invalid_ranges += 1
                elif data_compsize:
                    invalid_ranges += 1
                if width > 0xFFFF:
                    invalid_ranges += 1
            faces.append(
                {
                    "face_index": face_index,
                    "height": height,
                    "unknown": face_unknown,
                    "glyph_count": glyph_count,
                    "nonempty_glyph_count": nonempty,
                    "empty_glyph_count": glyph_count - nonempty,
                    "compressed_glyph_bytes": compressed_bytes,
                    "invalid_data_range_count": invalid_ranges,
                }
            )
        fonts.append(
            {
                "font_index": font_index,
                "face_count": face_count,
                "faces": faces,
            }
        )

    max_glyph_count = max(all_glyph_counts, default=-1) + 1
    proxy_rows = []
    cp932_decodable = 0
    cp932_undecodable = 0
    private_use_count = 0
    for index in range(max_glyph_count):
        char = decode_proxy(index)
        if char is None:
            cp932_undecodable += 1
        else:
            cp932_decodable += 1
            if "\ue000" <= char <= "\uf8ff":
                private_use_count += 1
        proxy_rows.append(
            {
                "index": index,
                "sjis_hex": fnl_index_to_sjis(index).hex().upper(),
                "cp932_character": char,
                "present_in_face_count": all_nonempty_counts[index],
                "total_face_count": all_glyph_counts[index],
            }
        )

    return {
        "schema": "yorugakuru.fnl-audit.v1",
        "source": str(path),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "actual_filesize": len(raw),
        "declared_filesize": declared_filesize,
        "declared_filesize_matches": declared_filesize == len(raw),
        "unknown": unknown,
        "index_size": index_size,
        "parsed_index_bytes": reader.offset,
        "index_fully_consumed": reader.offset == index_size,
        "font_count": font_count,
        "fonts": fonts,
        "maximum_glyph_count": max_glyph_count,
        "cp932_decodable_proxy_count": cp932_decodable,
        "cp932_undecodable_proxy_count": cp932_undecodable,
        "cp932_private_use_proxy_count": private_use_count,
        "hangul_directly_encodable_in_cp932": False,
        "hangul_strategy_candidate": (
            "Map Korean glyphs to unused two-byte Shift-JIS proxy indices, append "
            "new zlib-compressed bitmaps for every FNL face, and encode only "
            "allowlisted display strings with the frozen proxy map."
        ),
        "proxy_index_map": proxy_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    result = analyze(args.input.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp.replace(args.output)
    compact = {key: value for key, value in result.items() if key != "proxy_index_map"}
    print(json.dumps(compact, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
