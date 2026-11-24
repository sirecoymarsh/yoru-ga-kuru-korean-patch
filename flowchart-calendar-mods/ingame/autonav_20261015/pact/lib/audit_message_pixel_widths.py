#!/usr/bin/env python3
"""Audit AIN message translations against the runtime FNL font metrics.

The NightRemaster message window uses xsystem4's bitmap FNL renderer, font
type 256 (FNL font 0), requested size 60, font spacing -2, edge width 2, and
bold 0.  This script reproduces xsystem4's face/denominator selection and
per-character cursor advance.  It resolves every target character exactly as
the compatible AIN builder does (explicit proxy mapping first, CP932
otherwise), looks up the resulting glyph advance in the output FNL, and
reports translated message lines that exceed soft or hard pixel budgets.

Only actual C0 line controls receive special treatment: CR/LF start a new
display line, while any other C0 control is retained in the report but has no
assumed width.  Printable punctuation, ideographic spaces, middle dots, and
other special characters are measured as real FNL glyphs rather than being
stripped or approximated by character counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import re
import struct
import tempfile
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable


FNL_MAGIC = b"FNA\x00"
FNL_GLYPH_ENTRY_SIZE = 10
MESSAGE_ID_RE = re.compile(r"^(?P<asset>.+?)::m\[(?P<id>\d+)\]$")


@dataclass(frozen=True)
class FaceMetrics:
    font_index: int
    face_index: int
    height: int
    unknown: int
    widths: tuple[int, ...]


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write_json(path: pathlib.Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def extract_translation_entries(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, list):
        entries = document
    elif isinstance(document, dict):
        entries = None
        for key in ("entries", "records", "translations"):
            candidate = document.get(key)
            if isinstance(candidate, list):
                entries = candidate
                break
        if entries is None:
            raise ValueError(
                "Translation map must contain a list under entries, records, or translations"
            )
    else:
        raise ValueError("Translation map must be a JSON object or list")

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Translation entry {index} is not an object")
    return entries


def parse_fnl_font(
    path: pathlib.Path, requested_font_index: int
) -> tuple[dict[str, Any], list[FaceMetrics]]:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError(f"FNL is too small: {path}")

    magic, unknown, declared_size, index_size = struct.unpack_from("<4sIII", data, 0)
    if magic != FNL_MAGIC:
        raise ValueError(f"Unexpected FNL magic {magic!r}: {path}")
    if declared_size != len(data):
        raise ValueError(
            f"FNL declared size mismatch: header={declared_size}, actual={len(data)}"
        )

    index_end = 16 + index_size
    if index_size < 4 or index_end > len(data):
        raise ValueError("FNL index extends beyond end of file")

    cursor = 16

    def require(size: int, label: str) -> None:
        if size < 0 or cursor + size > index_end:
            raise ValueError(f"Truncated FNL index while reading {label} at {cursor}")

    require(4, "font count")
    font_count = struct.unpack_from("<I", data, cursor)[0]
    cursor += 4
    face_counts: list[int] = []
    requested_faces: list[FaceMetrics] = []

    for font_index in range(font_count):
        require(4, f"font {font_index} face count")
        face_count = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4
        face_counts.append(face_count)

        for face_index in range(face_count):
            require(12, f"font {font_index} face {face_index} header")
            height, face_unknown, glyph_count = struct.unpack_from("<III", data, cursor)
            cursor += 12
            if height <= 0:
                raise ValueError(f"Zero-height FNL face {font_index}/{face_index}")

            require(
                glyph_count * FNL_GLYPH_ENTRY_SIZE,
                f"font {font_index} face {face_index} glyph table",
            )
            widths: list[int] | None = [] if font_index == requested_font_index else None
            for glyph_index in range(glyph_count):
                width, data_pos, compressed_size = struct.unpack_from(
                    "<HII", data, cursor
                )
                cursor += FNL_GLYPH_ENTRY_SIZE
                if (data_pos == 0) != (compressed_size == 0):
                    raise ValueError(
                        "Inconsistent empty glyph at "
                        f"{font_index}/{face_index}/{glyph_index}"
                    )
                if data_pos:
                    if width == 0:
                        raise ValueError(
                            f"Non-empty zero-width glyph at {font_index}/{face_index}/{glyph_index}"
                        )
                    if data_pos < index_end or data_pos + compressed_size > len(data):
                        raise ValueError(
                            f"Glyph payload out of range at {font_index}/{face_index}/{glyph_index}"
                        )
                if widths is not None:
                    widths.append(width)

            if widths is not None:
                requested_faces.append(
                    FaceMetrics(
                        font_index=font_index,
                        face_index=face_index,
                        height=height,
                        unknown=face_unknown,
                        widths=tuple(widths),
                    )
                )

    if cursor != index_end:
        raise ValueError(f"FNL index parse mismatch: parsed={cursor}, expected={index_end}")
    if not requested_faces:
        raise ValueError(f"Requested FNL font {requested_font_index} does not exist")

    return (
        {
            "unknown": unknown,
            "declared_size": declared_size,
            "index_size": index_size,
            "index_end": index_end,
            "font_count": font_count,
            "font_face_counts": face_counts,
        },
        requested_faces,
    )


def select_fnl_face(
    faces: list[FaceMetrics], requested_size: float
) -> tuple[FaceMetrics, int, list[dict[str, Any]]]:
    """Reproduce xsystem4 font_fnl.c face/denominator selection.

    xsystem4 enumerates each face in file order and, for that face, integer
    denominators 1 through 12.  It keeps the first candidate with the minimum
    absolute distance from the requested size; an equal-distance candidate
    therefore never replaces an earlier one.
    """

    if requested_size <= 0:
        raise ValueError("requested font size must be positive")
    if not faces:
        raise ValueError("cannot select a face from an empty font")

    selected_face: FaceMetrics | None = None
    selected_denominator: int | None = None
    selected_error: float | None = None
    candidates: list[dict[str, Any]] = []

    for face in faces:
        for denominator in range(1, 13):
            effective_size = face.height / denominator
            error = abs(effective_size - requested_size)
            candidates.append(
                {
                    "face_index": face.face_index,
                    "face_height": face.height,
                    "denominator": denominator,
                    "effective_size": effective_size,
                    "absolute_error": error,
                }
            )
            if selected_error is None or error < selected_error:
                selected_face = face
                selected_denominator = denominator
                selected_error = error

    assert selected_face is not None
    assert selected_denominator is not None
    return selected_face, selected_denominator, candidates


def sjis_bytes_to_fnl_index(encoded: bytes) -> int:
    """Convert one CP932 character to the compact AliceSoft FNL glyph index."""

    if len(encoded) == 1:
        value = encoded[0]
        if 0x20 <= value <= 0x7E:
            return value - 0x20
        if 0xA1 <= value <= 0xDF:
            return 95 + (value - 0xA1)
        raise ValueError(f"Unsupported single-byte CP932 display code: {encoded.hex().upper()}")

    if len(encoded) != 2:
        raise ValueError(f"Expected one CP932 character, got {encoded.hex().upper()}")

    lead, trail = encoded
    if 0x81 <= lead <= 0x9F:
        lead_index = lead - 0x81
    elif 0xE0 <= lead <= 0xFC:
        lead_index = 31 + (lead - 0xE0)
    else:
        raise ValueError(f"Invalid CP932 lead byte: {encoded.hex().upper()}")

    if 0x40 <= trail <= 0x7E:
        trail_index = trail - 0x40
    elif 0x80 <= trail <= 0xFC:
        trail_index = trail - 0x40 - 1
    else:
        raise ValueError(f"Invalid CP932 trail byte: {encoded.hex().upper()}")
    return 158 + lead_index * 188 + trail_index


def load_proxy_indices(
    document: Any, glyph_count: int
) -> tuple[dict[str, int], dict[str, Any]]:
    if not isinstance(document, dict) or not isinstance(document.get("mapping"), list):
        raise ValueError("Proxy map must be an object containing a mapping list")

    proxy_indices: dict[str, int] = {}
    index_owners: dict[int, str] = {}
    for row_index, row in enumerate(document["mapping"]):
        if not isinstance(row, dict):
            raise ValueError(f"Proxy mapping row {row_index} is not an object")
        character = row.get("unicode_character")
        proxy_index = row.get("proxy_index")
        if not isinstance(character, str) or len(character) != 1:
            raise ValueError(f"Invalid unicode_character in proxy row {row_index}")
        if not isinstance(proxy_index, int) or not (0 <= proxy_index < glyph_count):
            raise ValueError(f"Invalid proxy_index in proxy row {row_index}: {proxy_index!r}")
        if character in proxy_indices and proxy_indices[character] != proxy_index:
            raise ValueError(f"Conflicting proxy mappings for {character!r}")
        if proxy_index in index_owners and index_owners[proxy_index] != character:
            raise ValueError(
                f"Proxy glyph index {proxy_index} is shared by "
                f"{index_owners[proxy_index]!r} and {character!r}"
            )

        proxy_character = row.get("proxy_character")
        if isinstance(proxy_character, str) and len(proxy_character) == 1:
            encoded = proxy_character.encode("cp932")
            calculated_index = sjis_bytes_to_fnl_index(encoded)
            if calculated_index != proxy_index:
                raise ValueError(
                    f"Proxy row {row_index} index mismatch: "
                    f"declared={proxy_index}, encoded={calculated_index}"
                )

        proxy_indices[character] = proxy_index
        index_owners[proxy_index] = character

    return proxy_indices, {
        "schema": document.get("schema"),
        "mapping_count": len(document["mapping"]),
        "unique_character_count": len(proxy_indices),
        "unique_proxy_index_count": len(index_owners),
    }


class WidthMeasurer:
    def __init__(
        self,
        face: FaceMetrics,
        denominator: int,
        proxy_indices: dict[str, int],
        font_spacing: float,
        edge_width: float,
        bold: float,
    ) -> None:
        if not 1 <= denominator <= 12:
            raise ValueError("FNL denominator must be in 1..12")
        if edge_width < 0:
            raise ValueError("edge width must not be negative")
        self.face = face
        self.denominator = denominator
        self.proxy_indices = proxy_indices
        self.font_spacing = float(font_spacing)
        self.edge_width = float(edge_width)
        self.bold = float(bold)
        self.edge_spacing_per_side = self.edge_width + math.ceil(self.bold)
        self.constant_advance = self.font_spacing + 2 * self.edge_spacing_per_side

    def glyph_index(self, character: str, use_proxy_map: bool) -> int:
        if use_proxy_map and character in self.proxy_indices:
            return self.proxy_indices[character]

        try:
            encoded = character.encode("cp932")
            roundtrip = encoded.decode("cp932")
        except UnicodeError as error:
            raise ValueError(
                f"No CP932/proxy representation for {character!r} "
                f"(U+{ord(character):04X})"
            ) from error
        # Alice-tools/libiconv represents a few original CP932 aliases (most
        # notably U+301C WAVE DASH) differently from Python's decode result.
        # Accept those aliases while measuring immutable source text.  Target
        # text must still round-trip unless it has an explicit proxy row, which
        # mirrors the compatible AIN builder's stricter target handling.
        if use_proxy_map and roundtrip != character:
            raise ValueError(
                f"CP932 roundtrip mismatch for {character!r} "
                f"(U+{ord(character):04X}); an explicit proxy mapping is required"
            )
        index = sjis_bytes_to_fnl_index(encoded)
        if index >= len(self.face.widths):
            raise ValueError(
                f"FNL glyph index {index} is out of range for {character!r}"
            )
        return index

    def measure(self, text: str, use_proxy_map: bool) -> dict[str, Any]:
        # JSON has already decoded any escaped CR/LF.  Normalize CRLF without
        # touching printable backslashes or tag-like punctuation.
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        display_lines = normalized.split("\n")
        measured_lines: list[dict[str, Any]] = []
        unmeasured_controls: list[dict[str, Any]] = []

        for line_index, line in enumerate(display_lines):
            raw_width_units = 0
            glyph_count = 0
            mapped_proxy_count = 0
            glyph_rows: list[dict[str, Any]] = []
            for character_index, character in enumerate(line):
                if ord(character) < 0x20 or ord(character) == 0x7F:
                    unmeasured_controls.append(
                        {
                            "line_index": line_index,
                            "character_index": character_index,
                            "codepoint": f"U+{ord(character):04X}",
                            "repr": repr(character),
                        }
                    )
                    continue

                mapped = use_proxy_map and character in self.proxy_indices
                glyph_index = self.glyph_index(character, use_proxy_map)
                width_units = self.face.widths[glyph_index]
                raw_width_units += width_units
                glyph_count += 1
                if mapped:
                    mapped_proxy_count += 1
                glyph_rows.append(
                    {
                        "character": character,
                        "codepoint": f"U+{ord(character):04X}",
                        "glyph_index": glyph_index,
                        "fnl_width_units": width_units,
                        "glyph_advance_px": round(width_units / self.denominator, 6),
                        "render_advance_px": round(
                            width_units / self.denominator + self.constant_advance, 6
                        ),
                        "explicit_proxy": mapped,
                    }
                )

            # xsystem4 text.c advances after every rendered character by:
            #   glyph.width / denominator + font_spacing
            #   + 2 * (edge_width + ceil(bold))
            # With this game's defaults, the non-glyph term is -2 + 2*2 = +2.
            glyph_advance_px = raw_width_units / self.denominator
            edge_spacing_px = glyph_count * 2 * self.edge_spacing_per_side
            font_spacing_px = glyph_count * self.font_spacing
            width_px = glyph_advance_px + font_spacing_px + edge_spacing_px
            measured_lines.append(
                {
                    "line_index": line_index,
                    "text": line,
                    "character_count": len(line),
                    "measured_glyph_count": glyph_count,
                    "explicit_proxy_glyph_count": mapped_proxy_count,
                    "fnl_width_units": raw_width_units,
                    "glyph_advance_px": round(glyph_advance_px, 6),
                    "font_spacing_px": round(font_spacing_px, 6),
                    "edge_spacing_px": round(edge_spacing_px, 6),
                    "constant_advance_per_glyph_px": round(self.constant_advance, 6),
                    "width_px": round(width_px, 6),
                    "glyphs": glyph_rows,
                }
            )

        widths = [row["width_px"] for row in measured_lines]
        return {
            "line_count": len(measured_lines),
            "max_width_px": max(widths, default=0.0),
            "line_widths_px": widths,
            "lines": measured_lines,
            "unmeasured_controls": unmeasured_controls,
        }


def compact_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    """Remove per-glyph detail from the normal finding list."""

    return {
        "line_count": measurement["line_count"],
        "max_width_px": measurement["max_width_px"],
        "line_widths_px": measurement["line_widths_px"],
        "lines": [
            {
                key: value
                for key, value in line.items()
                if key != "glyphs"
            }
            for line in measurement["lines"]
        ],
        "unmeasured_controls": measurement["unmeasured_controls"],
    }


def entry_sort_key(entry: dict[str, Any]) -> tuple[int, str]:
    numeric_id = entry.get("numeric_id")
    if not isinstance(numeric_id, int):
        match = MESSAGE_ID_RE.match(str(entry.get("stable_id", "")))
        numeric_id = int(match.group("id")) if match else 2**31 - 1
    return numeric_id, str(entry.get("stable_id", ""))


def make_finding(
    entry: dict[str, Any],
    source_measurement: dict[str, Any],
    target_measurement: dict[str, Any],
    soft_budget: float,
    hard_budget: float,
) -> dict[str, Any]:
    target_width = float(target_measurement["max_width_px"])
    numeric_id = entry.get("numeric_id")
    stable_id = str(entry.get("stable_id", ""))
    if not isinstance(numeric_id, int):
        match = MESSAGE_ID_RE.match(stable_id)
        numeric_id = int(match.group("id")) if match else None

    if target_width > hard_budget:
        severity = "hard"
    elif target_width > soft_budget:
        severity = "soft"
    else:
        severity = "pass"

    return {
        "stable_id": stable_id,
        "numeric_id": numeric_id,
        "packet_id": entry.get("packet_id"),
        "kind": entry.get("kind"),
        "source": entry["source"],
        "source_sha256": entry.get("source_sha256"),
        "target": entry["target"],
        "review_status": entry.get("review_status"),
        "provider": entry.get("provider"),
        "model_id": entry.get("model_id"),
        "severity": severity,
        "soft_budget_px": soft_budget,
        "hard_budget_px": hard_budget,
        "overflow_soft_px": round(max(0.0, target_width - soft_budget), 6),
        "overflow_hard_px": round(max(0.0, target_width - hard_budget), 6),
        "source_measurement": compact_measurement(source_measurement),
        "target_measurement": compact_measurement(target_measurement),
    }


def unique_pair_count(findings: Iterable[dict[str, Any]]) -> int:
    return len({(row["source"], row["target"]) for row in findings})


def summarize_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "stable_id_count": len(findings),
        "unique_source_target_pair_count": unique_pair_count(findings),
        "unique_target_count": len({row["target"] for row in findings}),
        "packet_count": len(
            {row["packet_id"] for row in findings if row.get("packet_id") is not None}
        ),
        "provider_counts": dict(
            sorted(Counter(str(row.get("provider")) for row in findings).items())
        ),
    }


def summarize_threshold(
    audited: list[dict[str, Any]], threshold: float
) -> dict[str, Any]:
    target_rows = [
        row
        for row in audited
        if float(row["target_measurement"]["max_width_px"]) > threshold
    ]
    source_rows = [
        row
        for row in audited
        if float(row["source_measurement"]["max_width_px"]) > threshold
    ]
    target_ids = {row["entry"]["stable_id"] for row in target_rows}
    source_ids = {row["entry"]["stable_id"] for row in source_rows}

    def row_summary(rows: list[dict[str, Any]], side: str) -> dict[str, Any]:
        return {
            "stable_id_count": len(rows),
            "unique_source_target_pair_count": len(
                {(row["entry"]["source"], row["entry"]["target"]) for row in rows}
            ),
            "unique_text_count": len({row["entry"][side] for row in rows}),
            "packet_count": len(
                {
                    row["entry"].get("packet_id")
                    for row in rows
                    if row["entry"].get("packet_id") is not None
                }
            ),
        }

    return {
        "threshold_px": threshold,
        "comparison": "strictly greater than",
        "target": row_summary(target_rows, "target"),
        "source": row_summary(source_rows, "source"),
        "target_and_source_stable_id_count": len(target_ids & source_ids),
        "target_only_stable_id_count": len(target_ids - source_ids),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit NightRemaster AIN message translations by actual FNL glyph width."
    )
    parser.add_argument("--translation-map", required=True, type=pathlib.Path)
    parser.add_argument("--fnl", required=True, type=pathlib.Path)
    parser.add_argument("--proxy-map", required=True, type=pathlib.Path)
    parser.add_argument("--output-json", required=True, type=pathlib.Path)
    parser.add_argument("--soft-budget", type=float, default=800.0)
    parser.add_argument("--hard-budget", type=float, default=880.0)
    parser.add_argument("--font-index", type=int, default=0)
    parser.add_argument("--font-size", type=float, default=60.0)
    parser.add_argument(
        "--font-spacing",
        "--character-spacing",
        dest="font_spacing",
        type=float,
        default=-2.0,
    )
    parser.add_argument("--edge-width", type=float, default=2.0)
    parser.add_argument("--bold", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.soft_budget <= 0 or args.hard_budget <= 0:
        raise ValueError("Pixel budgets must be positive")
    if args.soft_budget > args.hard_budget:
        raise ValueError("soft budget must not exceed hard budget")
    if args.bold < 0:
        raise ValueError("bold must not be negative")

    translation_document = load_json(args.translation_map)
    proxy_document = load_json(args.proxy_map)
    entries = extract_translation_entries(translation_document)
    fnl_header, font_faces = parse_fnl_font(args.fnl, args.font_index)
    face, denominator, selection_candidates = select_fnl_face(font_faces, args.font_size)
    proxy_indices, proxy_summary = load_proxy_indices(proxy_document, len(face.widths))
    measurer = WidthMeasurer(
        face=face,
        denominator=denominator,
        proxy_indices=proxy_indices,
        font_spacing=args.font_spacing,
        edge_width=args.edge_width,
        bold=args.bold,
    )

    audited: list[dict[str, Any]] = []
    skipped_non_messages: list[str] = []
    duplicate_ids: list[str] = []
    seen_ids: set[str] = set()
    control_rows: list[dict[str, Any]] = []

    for entry in entries:
        stable_id = entry.get("stable_id") or entry.get("key")
        if not isinstance(stable_id, str):
            raise ValueError("Translation entry is missing stable_id/key")
        entry = dict(entry)
        entry["stable_id"] = stable_id

        kind = entry.get("kind")
        match = MESSAGE_ID_RE.match(stable_id)
        if kind != "message" and not match:
            skipped_non_messages.append(stable_id)
            continue
        if not match:
            raise ValueError(f"Unsupported message stable_id: {stable_id}")
        if stable_id in seen_ids:
            duplicate_ids.append(stable_id)
            continue
        seen_ids.add(stable_id)

        if not isinstance(entry.get("source"), str) or not isinstance(entry.get("target"), str):
            raise ValueError(f"Message entry lacks source/target strings: {stable_id}")
        if entry.get("source_sha256") is not None:
            calculated_source_hash = hashlib.sha256(entry["source"].encode("utf-8")).hexdigest()
            if calculated_source_hash != entry["source_sha256"]:
                raise ValueError(f"Source SHA-256 mismatch: {stable_id}")

        source_measurement = measurer.measure(entry["source"], use_proxy_map=False)
        target_measurement = measurer.measure(entry["target"], use_proxy_map=True)
        if source_measurement["unmeasured_controls"] or target_measurement["unmeasured_controls"]:
            control_rows.append(
                {
                    "stable_id": stable_id,
                    "source_controls": source_measurement["unmeasured_controls"],
                    "target_controls": target_measurement["unmeasured_controls"],
                }
            )
        audited.append(
            {
                "entry": entry,
                "source_measurement": source_measurement,
                "target_measurement": target_measurement,
            }
        )

    if duplicate_ids:
        raise ValueError(f"Duplicate message IDs: {duplicate_ids[:10]}")

    audited.sort(key=lambda row: entry_sort_key(row["entry"]))
    findings = [
        make_finding(
            row["entry"],
            row["source_measurement"],
            row["target_measurement"],
            args.soft_budget,
            args.hard_budget,
        )
        for row in audited
        if row["target_measurement"]["max_width_px"] > args.soft_budget
    ]
    above_hard = [
        row for row in findings if row["target_measurement"]["max_width_px"] > args.hard_budget
    ]

    reported_ids: dict[str, Any] = {}
    for wanted_id in (2893, 2894):
        stable_suffix = f"::m[{wanted_id}]"
        matches = [row for row in audited if row["entry"]["stable_id"].endswith(stable_suffix)]
        if len(matches) != 1:
            reported_ids[f"m[{wanted_id}]"] = {
                "status": "missing" if not matches else "ambiguous",
                "match_count": len(matches),
            }
            continue
        row = matches[0]
        reported_ids[f"m[{wanted_id}]"] = make_finding(
            row["entry"],
            row["source_measurement"],
            row["target_measurement"],
            args.soft_budget,
            args.hard_budget,
        )

    source_max = max(
        (float(row["source_measurement"]["max_width_px"]) for row in audited),
        default=0.0,
    )
    target_max = max(
        (float(row["target_measurement"]["max_width_px"]) for row in audited),
        default=0.0,
    )
    widest_target = sorted(
        audited,
        key=lambda row: (
            -float(row["target_measurement"]["max_width_px"]),
            entry_sort_key(row["entry"]),
        ),
    )[:25]

    reference_thresholds = (800.0, 860.0, 884.0, 932.0)
    face_thresholds = (648.0, 668.0, 716.0)
    threshold_cache = {
        threshold: summarize_threshold(audited, threshold)
        for threshold in sorted(
            set(
                reference_thresholds
                + face_thresholds
                + (float(args.soft_budget), float(args.hard_budget))
            )
        )
    }

    document = {
        "schema": "contextual-game-localization.message-pixel-width-audit.v2",
        "verdict": "fail" if above_hard else ("review" if findings else "pass"),
        "inputs": {
            "translation_map": {
                "path": str(args.translation_map.resolve()),
                "size": args.translation_map.stat().st_size,
                "sha256": sha256_file(args.translation_map),
            },
            "fnl": {
                "path": str(args.fnl.resolve()),
                "size": args.fnl.stat().st_size,
                "sha256": sha256_file(args.fnl),
            },
            "proxy_map": {
                "path": str(args.proxy_map.resolve()),
                "size": args.proxy_map.stat().st_size,
                "sha256": sha256_file(args.proxy_map),
                **proxy_summary,
            },
        },
        "metric": {
            "engine_model": "xsystem4 FNL renderer",
            "engine_references": [
                "xsystem4 font_fnl.c: enumerate every face x denominator 1..12 and keep first minimum absolute size error",
                "xsystem4 text.c lines 205-233 and 261-296: per-character glyph/font/edge advance",
            ],
            "font_type": 256,
            "font_type_resolution": "type 256 -> FNL font index 0",
            "font_index": face.font_index,
            "available_face_count": len(font_faces),
            "available_face_heights": [candidate.height for candidate in font_faces],
            "face_index": face.face_index,
            "face_height_units": face.height,
            "face_unknown": face.unknown,
            "face_glyph_count": len(face.widths),
            "requested_font_size_px": args.font_size,
            "selected_denominator": denominator,
            "selected_effective_size": face.height / denominator,
            "selected_size_absolute_error": abs(
                face.height / denominator - args.font_size
            ),
            "selection_order": "face file order, then denominator 1..12; ties retain first candidate",
            "selection_candidates": selection_candidates,
            "font_spacing_px_per_glyph": args.font_spacing,
            "edge_width_px_per_side": args.edge_width,
            "bold": args.bold,
            "ceil_bold": math.ceil(args.bold),
            "edge_spacing_px_per_glyph": 2 * measurer.edge_spacing_per_side,
            "constant_advance_px_per_glyph": measurer.constant_advance,
            "width_formula": (
                "sum(fnl_glyph_width / selected_denominator + font_spacing + "
                "2 * (edge_width + ceil(bold)))"
            ),
            "proxy_resolution": (
                "explicit unicode_character->proxy_index first; otherwise exact CP932 "
                "roundtrip and AliceSoft compact FNL index"
            ),
            "control_handling": (
                "CR/LF split display lines; other C0 controls are preserved in findings "
                "and assigned no guessed width; all printable special characters are measured"
            ),
            "fnl_header": fnl_header,
        },
        "budgets": {
            "soft_px": args.soft_budget,
            "hard_px": args.hard_budget,
            "comparison": "strictly greater than",
        },
        "summary": {
            "input_entry_count": len(entries),
            "audited_message_count": len(audited),
            "skipped_non_message_count": len(skipped_non_messages),
            "source_max_width_px": round(source_max, 6),
            "target_max_width_px": round(target_max, 6),
            "above_soft": summarize_findings(findings),
            "above_hard": summarize_findings(above_hard),
            "messages_with_unmeasured_controls": len(control_rows),
        },
        "threshold_aggregates": {
            "reference_800_860_884_932": {
                str(int(threshold)): threshold_cache[threshold]
                for threshold in reference_thresholds
            },
            "face_648_668_716": {
                str(int(threshold)): threshold_cache[threshold]
                for threshold in face_thresholds
            },
            "configured_budgets": {
                str(threshold): threshold_cache[threshold]
                for threshold in (float(args.soft_budget), float(args.hard_budget))
            },
        },
        "reported_ids": reported_ids,
        "widest_targets": [
            make_finding(
                row["entry"],
                row["source_measurement"],
                row["target_measurement"],
                args.soft_budget,
                args.hard_budget,
            )
            for row in widest_target
        ],
        "above_soft": findings,
        "above_hard": above_hard,
        "unmeasured_controls": control_rows,
        "skipped_non_message_ids": skipped_non_messages,
    }
    atomic_write_json(args.output_json, document)

    print(
        json.dumps(
            {
                "output": str(args.output_json.resolve()),
                "verdict": document["verdict"],
                "audited_messages": len(audited),
                "selected_face": face.face_index,
                "selected_face_height": face.height,
                "selected_denominator": denominator,
                "constant_advance_px_per_glyph": measurer.constant_advance,
                "above_soft": len(findings),
                "above_hard": len(above_hard),
                "unique_pairs_above_soft": unique_pair_count(findings),
                "unique_pairs_above_hard": unique_pair_count(above_hard),
                "m2893_width_px": reported_ids.get("m[2893]", {})
                .get("target_measurement", {})
                .get("max_width_px"),
                "m2894_width_px": reported_ids.get("m[2894]", {})
                .get("target_measurement", {})
                .get("max_width_px"),
                "threshold_target_counts": {
                    str(int(threshold)): threshold_cache[threshold]["target"][
                        "stable_id_count"
                    ]
                    for threshold in face_thresholds + reference_thresholds
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
