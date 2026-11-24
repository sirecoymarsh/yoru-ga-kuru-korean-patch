from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import struct
import tempfile
import unicodedata
import zlib
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont


UINT16_MAX = (1 << 16) - 1
UINT32_MAX = (1 << 32) - 1
FNL_GLYPH_ENTRY_SIZE = 10


@dataclass
class Glyph:
    index: int
    entry_offset: int
    width: int
    data_pos: int
    compressed_size: int


@dataclass
class Face:
    font_index: int
    face_index: int
    height: int
    unknown: int
    glyphs: list[Glyph]


@dataclass(frozen=True)
class DonorContext:
    image: Image.Image
    width: int
    bitmap_sha256: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = pathlib.Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        temp_path.replace(path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def atomic_write_bytes(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = pathlib.Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        temp_path.replace(path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def atomic_save_png(path: pathlib.Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp_path = pathlib.Path(temp_name)
    try:
        image.save(temp_path, format="PNG")
        temp_path.replace(path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def offsets_to_ranges(offsets: Iterable[int]) -> list[dict]:
    ordered = sorted(set(offsets))
    if not ordered:
        return []
    ranges = []
    start = previous = ordered[0]
    for offset in ordered[1:]:
        if offset == previous + 1:
            previous = offset
            continue
        ranges.append({"start": start, "end_exclusive": previous + 1})
        start = previous = offset
    ranges.append({"start": start, "end_exclusive": previous + 1})
    return ranges


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


def parse_fnl(data: bytes) -> tuple[dict, list[Face]]:
    if len(data) < 20:
        raise ValueError("FNL file is too small")
    magic, unknown, declared_size, index_size = struct.unpack_from("<4sIII", data, 0)
    if magic != b"FNA\x00":
        raise ValueError(f"Unexpected FNL magic: {magic!r}")
    if declared_size != len(data):
        raise ValueError(f"Declared FNL size mismatch: {declared_size} != {len(data)}")
    index_end = 16 + index_size
    if index_size < 4 or index_end > len(data):
        raise ValueError("FNL index extends past EOF")
    offset = 16
    def require_index(size: int, label: str) -> None:
        if size < 0 or offset + size > index_end:
            raise ValueError(f"Truncated FNL index while reading {label} at {offset}")

    require_index(4, "font count")
    font_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    faces: list[Face] = []
    font_face_counts: list[int] = []
    for font_index in range(font_count):
        require_index(4, f"font {font_index} face count")
        face_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        font_face_counts.append(face_count)
        for face_index in range(face_count):
            require_index(12, f"font {font_index} face {face_index} header")
            height, face_unknown, glyph_count = struct.unpack_from("<III", data, offset)
            offset += 12
            if height == 0:
                raise ValueError(f"Zero-height face {font_index}/{face_index}")
            require_index(
                glyph_count * FNL_GLYPH_ENTRY_SIZE,
                f"font {font_index} face {face_index} glyph table",
            )
            glyphs = []
            for glyph_index in range(glyph_count):
                entry_offset = offset
                width, data_pos, compressed_size = struct.unpack_from("<HII", data, offset)
                offset += 10
                if (data_pos == 0) != (compressed_size == 0):
                    raise ValueError(
                        f"Inconsistent empty glyph {font_index}/{face_index}/{glyph_index}"
                    )
                if data_pos:
                    if width == 0:
                        raise ValueError(
                            f"Non-empty zero-width glyph {font_index}/{face_index}/{glyph_index}"
                        )
                    data_end = data_pos + compressed_size
                    if data_pos < index_end or data_end > len(data):
                        raise ValueError(
                            f"Glyph payload out of range {font_index}/{face_index}/{glyph_index}"
                        )
                glyphs.append(
                    Glyph(
                        index=glyph_index,
                        entry_offset=entry_offset,
                        width=width,
                        data_pos=data_pos,
                        compressed_size=compressed_size,
                    )
                )
            faces.append(
                Face(
                    font_index=font_index,
                    face_index=face_index,
                    height=height,
                    unknown=face_unknown,
                    glyphs=glyphs,
                )
            )
    if offset != index_end:
        raise ValueError(f"FNL index parse mismatch: {offset} != {index_end}")
    return (
        {
            "unknown": unknown,
            "declared_size": declared_size,
            "index_size": index_size,
            "index_end": index_end,
            "font_count": font_count,
            "font_face_counts": font_face_counts,
        },
        faces,
    )


def decompress_glyph_stream(compressed: bytes, expected: int, label: str) -> bytes:
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(compressed, expected + 1)
        if len(raw) > expected or decoder.unconsumed_tail:
            raise ValueError(f"{label} exceeds expected bitmap size {expected}")
        raw += decoder.flush()
    except zlib.error as error:
        raise ValueError(f"Invalid zlib stream for {label}: {error}") from error
    if len(raw) > expected:
        raise ValueError(f"{label} exceeds expected bitmap size {expected}")
    if not decoder.eof:
        raise ValueError(f"Truncated zlib stream for {label}")
    if decoder.unused_data:
        raise ValueError(f"Trailing bytes after zlib stream for {label}")
    if decoder.unconsumed_tail:
        raise ValueError(f"Unconsumed zlib input for {label}")
    return raw


def decode_glyph(data: bytes, face: Face, glyph: Glyph) -> Image.Image:
    stride = (glyph.width + 31) // 32 * 4
    expected = stride * face.height
    if glyph.data_pos == 0:
        return Image.new("1", (max(8, stride * 8), face.height), 0)
    compressed = data[glyph.data_pos : glyph.data_pos + glyph.compressed_size]
    raw = decompress_glyph_stream(
        compressed,
        expected,
        f"glyph {face.font_index}/{face.face_index}/{glyph.index}",
    )
    raw += b"\x00" * (expected - len(raw))
    image = Image.new("1", (stride * 8, face.height), 0)
    pixels = image.load()
    for stored_row in range(face.height):
        display_y = face.height - 1 - stored_row
        row_offset = stored_row * stride
        for x in range(glyph.width):
            value = raw[row_offset + x // 8]
            pixels[x, display_y] = 255 if value & (1 << (7 - x % 8)) else 0
    return image


def encode_glyph(image: Image.Image, width: int, height: int) -> bytes:
    if image.mode != "1":
        image = image.convert("1")
    stride = (width + 31) // 32 * 4
    raw = bytearray(stride * height)
    pixels = image.load()
    for stored_row in range(height):
        display_y = height - 1 - stored_row
        row_offset = stored_row * stride
        for x in range(width):
            if pixels[x, display_y]:
                raw[row_offset + x // 8] |= 1 << (7 - x % 8)
    return bytes(raw)


def set_font_weight(font: ImageFont.FreeTypeFont, weight: int) -> None:
    try:
        axes = font.get_variation_axes()
    except AttributeError:
        return
    except OSError as error:
        raise ValueError(f"Unable to inspect font variation axes: {error}") from error
    if not axes:
        return
    values = []
    for axis in axes:
        name = axis.get("name", b"")
        if isinstance(name, bytes):
            name = name.decode("ascii", "ignore")
        if str(name).lower() == "weight":
            values.append(max(axis["minimum"], min(axis["maximum"], weight)))
        else:
            values.append(axis["default"])
    try:
        font.set_variation_by_axes(values)
    except (AttributeError, OSError, ValueError) as error:
        raise ValueError(f"Unable to apply variable-font weight {weight}: {error}") from error


def load_font(font_path: pathlib.Path, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(font_path), size=size)
    set_font_weight(font, weight)
    return font


def fit_render(
    character: str,
    face: Face,
    donor_image: Image.Image,
    donor_width: int,
    font_path: pathlib.Path,
    weight: int,
) -> Image.Image:
    donor_bbox = donor_image.getbbox()
    if donor_bbox is None:
        target_box = (1, max(1, face.height // 4), max(2, donor_width - 1), face.height * 3 // 4)
    else:
        left, top, right, bottom = donor_bbox
        margin_x = max(1, round((right - left) * 0.02))
        margin_y = max(1, round((bottom - top) * 0.02))
        target_box = (
            max(0, left - margin_x),
            max(0, top - margin_y),
            min(donor_width, right + margin_x),
            min(face.height, bottom + margin_y),
        )
    target_width = max(1, target_box[2] - target_box[0])
    target_height = max(1, target_box[3] - target_box[1])

    low, high = 1, max(2, face.height * 2)
    best = None
    while low <= high:
        size = (low + high) // 2
        font = load_font(font_path, size, weight)
        bbox = font.getbbox(character)
        rendered_width = bbox[2] - bbox[0]
        rendered_height = bbox[3] - bbox[1]
        if (
            rendered_width > 0
            and rendered_height > 0
            and rendered_width <= target_width
            and rendered_height <= target_height
        ):
            best = (font, bbox)
            low = size + 1
        else:
            high = size - 1
    if best is None:
        raise ValueError(
            f"Glyph {character!r} cannot fit donor advance {donor_width}x{face.height}"
        )
    font, bbox = best
    rendered_width = bbox[2] - bbox[0]
    rendered_height = bbox[3] - bbox[1]
    x = target_box[0] + (target_width - rendered_width) // 2 - bbox[0]
    y = target_box[1] + (target_height - rendered_height) // 2 - bbox[1]

    antialias_scale = 4
    large_font = load_font(font_path, max(1, font.size * antialias_scale), weight)
    large_bbox = large_font.getbbox(character)
    large = Image.new("L", (donor_width * antialias_scale, face.height * antialias_scale), 0)
    draw = ImageDraw.Draw(large)
    large_x = x * antialias_scale - (large_bbox[0] - bbox[0] * antialias_scale)
    large_y = y * antialias_scale - (large_bbox[1] - bbox[1] * antialias_scale)
    draw.text((large_x, large_y), character, font=large_font, fill=255)
    gray = large.resize((donor_width, face.height), Image.Resampling.LANCZOS)
    binary = gray.point(lambda value: 255 if value >= 112 else 0, mode="1")
    if binary.getbbox() is None:
        raise ValueError(
            f"Font rendered an empty glyph for {character!r} in font {face.font_index}, face {face.face_index}"
        )
    ink_box = binary.getbbox()
    if ink_box[0] < 0 or ink_box[1] < 0 or ink_box[2] > donor_width or ink_box[3] > face.height:
        raise ValueError(f"Rendered glyph {character!r} escaped donor canvas")
    return binary


def load_translation_targets(
    paths: Iterable[pathlib.Path], allow_unreviewed: bool
) -> tuple[list[str], dict]:
    targets: list[str] = []
    seen_ids: dict[str, tuple[pathlib.Path, str | None]] = {}
    statuses: Counter[str] = Counter()
    required_entries = 0
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
        for entry in document.get("entries", []):
            stable_id = entry.get("stable_id")
            if not isinstance(stable_id, str) or not stable_id:
                raise ValueError(f"Missing stable_id in {path}")
            if stable_id in seen_ids:
                previous_path, previous_target = seen_ids[stable_id]
                conflict = previous_target != entry.get("target")
                raise ValueError(
                    f"Duplicate stable_id {stable_id!r} in {previous_path} and {path}"
                    + (" with conflicting targets" if conflict else "")
                )
            seen_ids[stable_id] = (path, entry.get("target"))
            status = str(entry.get("review_status") or "missing")
            statuses[status] += 1
            if not entry.get("translation_required"):
                continue
            required_entries += 1
            target = entry.get("target")
            if not isinstance(target, str) or not target.strip():
                raise ValueError(f"Missing target for required entry {stable_id!r}")
            if status != "reviewed" and not allow_unreviewed:
                raise ValueError(
                    f"Required entry {stable_id!r} is not reviewed (status={status!r})"
                )
            targets.append(target)
    return targets, {
        "entry_count": len(seen_ids),
        "translation_required_count": required_entries,
        "included_target_count": len(targets),
        "review_status_counts": dict(sorted(statuses.items())),
    }


def requires_proxy(character: str) -> bool:
    try:
        encoded = character.encode("cp932")
        decoded = encoded.decode("cp932")
    except UnicodeError:
        return True
    return decoded != character


def inspect_font(path: pathlib.Path, required: Iterable[str]) -> dict:
    with TTFont(path, lazy=True) as font:
        cmap = font.getBestCmap() or {}
        missing = sorted({char for char in required if ord(char) not in cmap}, key=ord)
        axes = []
        if "fvar" in font:
            for axis in font["fvar"].axes:
                axes.append(
                    {
                        "tag": axis.axisTag,
                        "minimum": float(axis.minValue),
                        "default": float(axis.defaultValue),
                        "maximum": float(axis.maxValue),
                    }
                )
    if missing:
        raise ValueError(
            f"Font {path} lacks {len(missing)} required glyphs: "
            + " ".join(f"U+{ord(char):04X}" for char in missing[:20])
        )
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "required_cmap_coverage": "pass",
        "variation_axes": axes,
    }


def choose_proxies(
    required_characters: list[str],
    proxy_capacity_path: pathlib.Path,
    literal_target_characters: set[str],
    faces: list[Face],
) -> list[dict]:
    capacity = json.loads(proxy_capacity_path.read_text(encoding="utf-8-sig"))
    candidates = []
    seen_indices: set[int] = set()
    seen_characters: set[str] = set()
    minimum_glyph_count = min(len(face.glyphs) for face in faces)
    for row in capacity.get("candidates", []):
        character = row.get("proxy_character", "")
        index = row.get("index")
        if not isinstance(index, int) or index < 5000 or index >= minimum_glyph_count:
            continue
        if not row.get("canonical_roundtrip"):
            continue
        if row.get("unicode_mapping_multiplicity") != 1:
            continue
        if not character or not unicodedata.name(character, "").startswith("CJK UNIFIED IDEOGRAPH-"):
            continue
        if character in literal_target_characters:
            continue
        if index in seen_indices or character in seen_characters:
            raise ValueError(f"Duplicate proxy candidate at index {index}: {character!r}")
        seen_indices.add(index)
        seen_characters.add(character)
        candidates.append(row)
    candidates.sort(key=lambda row: row["index"], reverse=True)
    if len(candidates) < len(required_characters):
        raise ValueError(
            f"Insufficient safe proxy capacity: need {len(required_characters)}, have {len(candidates)}"
        )
    mapping = []
    for target, proxy in zip(
        required_characters, candidates[: len(required_characters)], strict=True
    ):
        encoded = fnl_index_to_sjis(proxy["index"])
        if encoded.hex().upper() != proxy["sjis_hex"].upper():
            raise ValueError(f"Proxy index/byte mismatch at {proxy['index']}")
        if proxy["proxy_character"].encode("cp932") != encoded:
            raise ValueError(f"Proxy round-trip mismatch at {proxy['index']}")
        if encoded.decode("cp932") != proxy["proxy_character"]:
            raise ValueError(f"Proxy canonical decode mismatch at {proxy['index']}")
        mapping.append(
            {
                "unicode_character": target,
                "unicode_codepoint": f"U+{ord(target):04X}",
                "proxy_character": proxy["proxy_character"],
                "proxy_codepoint": f"U+{ord(proxy['proxy_character']):04X}",
                "proxy_index": proxy["index"],
                "proxy_sjis_hex": proxy["sjis_hex"].upper(),
            }
        )
    return mapping


def font_spec(font_index: int, args) -> tuple[pathlib.Path, int]:
    specs = {
        0: (args.serif_font, 500),
        1: (args.sans_font, 750),
        2: (args.sans_font, 350),
        3: (args.serif_font, 400),
        4: (args.sans_font, 900),
    }
    return specs.get(font_index, (args.sans_font, 500))


def build_preview(
    original: bytes,
    faces: list[Face],
    mapping: list[dict],
    donor_index: int,
    args,
) -> None:
    if not args.preview_output or not mapping:
        return
    samples = mapping[: min(12, len(mapping))]
    preview_faces = []
    for font_index in range(max(face.font_index for face in faces) + 1):
        font_faces = [face for face in faces if face.font_index == font_index]
        if font_faces:
            for index in sorted({0, len(font_faces) // 2, len(font_faces) - 1}):
                preview_faces.append(font_faces[index])
    max_height = max(face.height for face in preview_faces)
    max_advance = max(face.glyphs[donor_index].width for face in preview_faces)
    cell_width = max_advance + 24
    cell_height = max_height + 42
    sheet = Image.new(
        "RGB",
        (cell_width * len(samples), cell_height * len(preview_faces)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for row_index, face in enumerate(preview_faces):
        donor = face.glyphs[donor_index]
        donor_image = decode_glyph(original, face, donor)
        font_path, weight = font_spec(face.font_index, args)
        for column_index, mapping_row in enumerate(samples):
            rendered = fit_render(
                mapping_row["unicode_character"],
                face,
                donor_image,
                donor.width,
                font_path,
                weight,
            )
            x = column_index * cell_width + 12
            y = row_index * cell_height + 30
            sheet.paste(rendered.convert("RGB"), (x, y))
            draw.text(
                (column_index * cell_width + 3, row_index * cell_height + 3),
                f"f{face.font_index}/{face.face_index} h{face.height} U+{ord(mapping_row['unicode_character']):04X}",
                fill="black",
            )
    atomic_save_png(args.preview_output, sheet)


def patch_fnl(
    original: bytes,
    header: dict,
    faces: list[Face],
    mapping: list[dict],
    donor_index: int,
    args,
) -> tuple[bytes, dict]:
    patched = bytearray(original)
    allowed_diff_offsets = set(range(8, 12))
    appended_total = 0
    changed_entries = []
    render_cache: dict[
        tuple[int, int, int, int, str, str, int, str], tuple[int, bytes]
    ] = {}

    for mapping_row in mapping:
        proxy_index = mapping_row["proxy_index"]
        target = mapping_row["unicode_character"]
        for face in faces:
            if proxy_index >= len(face.glyphs):
                raise ValueError(
                    f"Proxy index {proxy_index} exceeds face {face.font_index}/{face.face_index}"
                )
            donor = face.glyphs[donor_index]
            donor_image = decode_glyph(original, face, donor)
            font_path, weight = font_spec(face.font_index, args)
            donor_bitmap_hash = sha256_bytes(
                encode_glyph(donor_image, donor.width, face.height)
            )
            cache_key = (
                face.font_index,
                face.face_index,
                face.height,
                donor.width,
                donor_bitmap_hash,
                str(font_path),
                weight,
                target,
            )
            if cache_key not in render_cache:
                rendered = fit_render(
                    target,
                    face,
                    donor_image,
                    donor.width,
                    font_path,
                    weight,
                )
                packed = encode_glyph(rendered, donor.width, face.height)
                render_cache[cache_key] = (donor.width, zlib.compress(packed, level=9))
            width, compressed = render_cache[cache_key]
            data_pos = len(patched)
            patched.extend(compressed)
            appended_total += len(compressed)
            glyph = face.glyphs[proxy_index]
            struct.pack_into("<HII", patched, glyph.entry_offset, width, data_pos, len(compressed))
            allowed_diff_offsets.update(range(glyph.entry_offset, glyph.entry_offset + 10))
            changed_entries.append(
                {
                    "font_index": face.font_index,
                    "face_index": face.face_index,
                    "height": face.height,
                    "proxy_index": proxy_index,
                    "target_character": target,
                    "entry_offset": glyph.entry_offset,
                    "width": width,
                    "data_pos": data_pos,
                    "compressed_size": len(compressed),
                }
            )

    struct.pack_into("<I", patched, 8, len(patched))
    unexpected_prefix_diffs = [
        offset
        for offset, (before, after) in enumerate(zip(original, patched))
        if before != after and offset not in allowed_diff_offsets
    ]
    if unexpected_prefix_diffs:
        raise ValueError(
            f"Unexpected FNL prefix changes at offsets {unexpected_prefix_diffs[:20]}"
        )
    if patched[header["index_end"] : len(original)] != original[header["index_end"] :]:
        raise ValueError("Original FNL glyph payload region changed unexpectedly")

    return bytes(patched), {
        "changed_index_entry_count": len(changed_entries),
        "appended_compressed_bytes": appended_total,
        "changed_entries": changed_entries,
        "unexpected_prefix_diff_count": 0,
        "original_payload_region_unchanged": True,
    }


def verify_patch(data: bytes, mapping: list[dict]) -> dict:
    header, faces = parse_fnl(data)
    failures = []
    for mapping_row in mapping:
        proxy_index = mapping_row["proxy_index"]
        for face in faces:
            glyph = face.glyphs[proxy_index]
            if glyph.data_pos == 0 or glyph.compressed_size == 0:
                failures.append(
                    f"missing:{face.font_index}/{face.face_index}/{proxy_index}"
                )
                continue
            stride = (glyph.width + 31) // 32 * 4
            try:
                raw = zlib.decompress(
                    data[glyph.data_pos : glyph.data_pos + glyph.compressed_size]
                )
            except zlib.error:
                failures.append(
                    f"zlib:{face.font_index}/{face.face_index}/{proxy_index}"
                )
                continue
            if len(raw) > stride * face.height or not any(raw):
                failures.append(
                    f"bitmap:{face.font_index}/{face.face_index}/{proxy_index}"
                )
    return {
        "declared_size_matches": header["declared_size"] == len(data),
        "face_count": len(faces),
        "checked_glyph_count": len(faces) * len(mapping),
        "failure_count": len(failures),
        "failures": failures[:100],
        "verdict": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Korean CP932-proxy glyph patch for AliceSoft FNL fonts."
    )
    parser.add_argument("--input-fnl", required=True, type=pathlib.Path)
    parser.add_argument("--output-fnl", type=pathlib.Path)
    parser.add_argument(
        "--translation-json", required=True, action="append", type=pathlib.Path
    )
    parser.add_argument("--proxy-capacity", required=True, type=pathlib.Path)
    parser.add_argument("--map-output", required=True, type=pathlib.Path)
    parser.add_argument("--manifest-output", type=pathlib.Path)
    parser.add_argument("--preview-output", type=pathlib.Path)
    parser.add_argument("--expected-source-sha256")
    parser.add_argument(
        "--allow-unreviewed",
        action="store_true",
        help="Permit non-reviewed translation entries in map-only exploratory runs.",
    )
    parser.add_argument(
        "--serif-font",
        type=pathlib.Path,
        default=pathlib.Path(r"C:\Windows\Fonts\NotoSerifKR-VF.ttf"),
    )
    parser.add_argument(
        "--sans-font",
        type=pathlib.Path,
        default=pathlib.Path(r"C:\Windows\Fonts\NotoSansKR-VF.ttf"),
    )
    parser.add_argument("--donor-character", default="国")
    parser.add_argument(
        "--map-only",
        action="store_true",
        help="Generate and validate only the proxy map and preview; do not patch an FNL.",
    )
    args = parser.parse_args()

    if args.allow_unreviewed and not args.map_only:
        raise ValueError("--allow-unreviewed is permitted only with --map-only")
    if args.map_only and (args.output_fnl or args.manifest_output):
        raise ValueError("--map-only does not accept patch output arguments")
    if not args.map_only:
        if not args.expected_source_sha256:
            raise ValueError("--expected-source-sha256 is required for patch mode")
        if not args.output_fnl or not args.manifest_output:
            raise ValueError("--output-fnl and --manifest-output are required without --map-only")
        if os.path.normcase(os.path.abspath(args.output_fnl)) == os.path.normcase(
            os.path.abspath(args.input_fnl)
        ):
            raise ValueError("Refusing to overwrite the input FNL")
    for font_path in (args.serif_font, args.sans_font):
        if not font_path.is_file():
            raise FileNotFoundError(font_path)
    original = args.input_fnl.read_bytes()
    source_sha256 = sha256_bytes(original)
    if not args.map_only and source_sha256.lower() != args.expected_source_sha256.lower():
        raise ValueError(
            f"Source FNL SHA-256 mismatch: {source_sha256} != {args.expected_source_sha256}"
        )
    header, faces = parse_fnl(original)
    donor_index = None
    donor_encoded = args.donor_character.encode("cp932")
    if len(donor_encoded) != 2:
        raise ValueError("Donor character must be a two-byte CP932 character")
    lead, trail = donor_encoded
    lead_index = lead - 0x81 if lead < 0xA0 else lead - 0xE0 + 31
    trail_index = trail - 0x40 - (1 if trail > 0x7F else 0)
    donor_index = 158 + lead_index * 188 + trail_index
    donor_hashes = []
    for face in faces:
        if donor_index >= len(face.glyphs):
            raise ValueError(f"Donor index missing from face {face.font_index}/{face.face_index}")
        donor = face.glyphs[donor_index]
        if donor.width == 0 or donor.data_pos == 0 or donor.compressed_size == 0:
            raise ValueError(f"Invalid donor in face {face.font_index}/{face.face_index}")
        donor_image = decode_glyph(original, face, donor)
        if donor_image.getbbox() is None:
            raise ValueError(f"Empty donor bitmap in face {face.font_index}/{face.face_index}")
        donor_hashes.append(
            sha256_bytes(encode_glyph(donor_image, donor.width, face.height))
        )

    target_strings, translation_summary = load_translation_targets(
        args.translation_json, args.allow_unreviewed
    )
    target_text = "".join(target_strings)
    required = sorted({char for char in target_text if requires_proxy(char)}, key=ord)
    font_sources = [
        inspect_font(args.serif_font, required),
        inspect_font(args.sans_font, required),
    ]
    mapping = choose_proxies(required, args.proxy_capacity, set(target_text), faces)
    mapping_document = {
        "schema": "contextual-game-localization.fnl-proxy-map.v2",
        "source_fnl_sha256": source_sha256,
        "translation_inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in args.translation_json
        ],
        "proxy_capacity_sha256": sha256_file(args.proxy_capacity),
        "translation_summary": translation_summary,
        "target_text_sha256": sha256_bytes(target_text.encode("utf-8")),
        "required_character_set_sha256": sha256_bytes("".join(required).encode("utf-8")),
        "font_sources": font_sources,
        "donor": {
            "character": args.donor_character,
            "index": donor_index,
            "validated_face_count": len(donor_hashes),
            "bitmap_set_sha256": sha256_bytes("".join(donor_hashes).encode("ascii")),
        },
        "required_proxy_character_count": len(required),
        "mapping": mapping,
    }
    atomic_write_text(
        args.map_output,
        json.dumps(mapping_document, ensure_ascii=False, indent=2) + "\n",
    )
    build_preview(original, faces, mapping, donor_index, args)

    if args.map_only:
        print(
            json.dumps(
                {
                    "mode": "map_only",
                    "required_proxy_character_count": len(required),
                    "map_output": str(args.map_output),
                    "preview_output": str(args.preview_output)
                    if args.preview_output
                    else None,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    patched, patch_details = patch_fnl(
        original, header, faces, mapping, donor_index, args
    )
    verification = verify_patch(patched, mapping)
    if verification["verdict"] != "pass":
        raise ValueError(f"FNL verification failed: {verification}")
    atomic_write_bytes(args.output_fnl, patched)
    manifest = {
        "schema": "contextual-game-localization.fnl-patch-manifest.v1",
        "source": {
            "path": str(args.input_fnl),
            "size": len(original),
            "sha256": sha256_bytes(original),
        },
        "output": {
            "path": str(args.output_fnl),
            "size": len(patched),
            "sha256": sha256_bytes(patched),
        },
        "proxy_map": {
            "path": str(args.map_output),
            "sha256": sha256_file(args.map_output),
            "character_count": len(mapping),
        },
        "font_sources": [
            {"path": str(args.serif_font), "sha256": sha256_file(args.serif_font)},
            {"path": str(args.sans_font), "sha256": sha256_file(args.sans_font)},
        ],
        "donor_character": args.donor_character,
        "donor_index": donor_index,
        "patch": patch_details,
        "verification": verification,
    }
    atomic_write_text(
        args.manifest_output,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    print(
        json.dumps(
            {
                "output": str(args.output_fnl),
                "output_sha256": manifest["output"]["sha256"],
                "character_count": len(mapping),
                "changed_index_entry_count": patch_details[
                    "changed_index_entry_count"
                ],
                "verification": verification["verdict"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
