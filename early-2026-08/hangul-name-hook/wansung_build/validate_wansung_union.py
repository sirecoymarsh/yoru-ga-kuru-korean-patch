from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys

from wansung_common import (
    EXPECTED_CURRENT_MAPPING_COUNT,
    EXPECTED_EXTENSION_COUNT,
    EXPECTED_UNION_COUNT,
    canonical_json_sha256,
    load_json,
    validate_mapping_rows,
    wansung_syllables,
)


def load_builder(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("wansung_fnl_builder", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Unable to load builder module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_fnl_preservation(
    builder_script: pathlib.Path,
    base_fnl_path: pathlib.Path,
    output_fnl_path: pathlib.Path,
    current_rows: list[dict],
    extension_rows: list[dict],
) -> None:
    module = load_builder(builder_script)
    base = base_fnl_path.read_bytes()
    output = output_fnl_path.read_bytes()
    _, base_faces = module.parse_fnl(base)
    _, output_faces = module.parse_fnl(output)
    if len(base_faces) != len(output_faces):
        raise ValueError("FNL face count changed")

    extension_indices = {row["proxy_index"] for row in extension_rows}
    retained_indices = {row["proxy_index"] for row in current_rows}
    if extension_indices & retained_indices:
        raise ValueError("New FNL indices overlap retained indices")

    for base_face, output_face in zip(base_faces, output_faces, strict=True):
        if (
            base_face.font_index,
            base_face.face_index,
            base_face.height,
            len(base_face.glyphs),
        ) != (
            output_face.font_index,
            output_face.face_index,
            output_face.height,
            len(output_face.glyphs),
        ):
            raise ValueError("FNL face geometry changed")
        for index in retained_indices:
            before = base_face.glyphs[index]
            after = output_face.glyphs[index]
            metadata_before = (
                before.entry_offset,
                before.width,
                before.data_pos,
                before.compressed_size,
            )
            metadata_after = (
                after.entry_offset,
                after.width,
                after.data_pos,
                after.compressed_size,
            )
            if metadata_before != metadata_after:
                raise ValueError(
                    f"Retained glyph metadata changed at "
                    f"{base_face.font_index}/{base_face.face_index}/{index}"
                )
            if before.compressed_size:
                before_data = base[
                    before.data_pos : before.data_pos + before.compressed_size
                ]
                after_data = output[
                    after.data_pos : after.data_pos + after.compressed_size
                ]
                if before_data != after_data:
                    raise ValueError(
                        f"Retained glyph payload changed at "
                        f"{base_face.font_index}/{base_face.face_index}/{index}"
                    )
        for index in extension_indices:
            before = base_face.glyphs[index]
            after = output_face.glyphs[index]
            before_blob = (
                base[before.data_pos : before.data_pos + before.compressed_size]
                if before.compressed_size
                else b""
            )
            after_blob = (
                output[after.data_pos : after.data_pos + after.compressed_size]
                if after.compressed_size
                else b""
            )
            if (
                before.width,
                before.data_pos,
                before.compressed_size,
                before_blob,
            ) == (
                after.width,
                after.data_pos,
                after.compressed_size,
                after_blob,
            ):
                raise ValueError(
                    f"Extension glyph was not replaced at "
                    f"{base_face.font_index}/{base_face.face_index}/{index}"
                )

    verification = module.verify_patch(output, current_rows + extension_rows)
    if verification.get("verdict") != "pass":
        raise ValueError(f"Built union FNL failed glyph verification: {verification}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a built Wansung union map/FNL.")
    parser.add_argument("--current-map", required=True, type=pathlib.Path)
    parser.add_argument("--union-map", required=True, type=pathlib.Path)
    parser.add_argument("--expected-extension", required=True, type=pathlib.Path)
    parser.add_argument("--builder-script", type=pathlib.Path)
    parser.add_argument("--base-fnl", type=pathlib.Path)
    parser.add_argument("--output-fnl", type=pathlib.Path)
    args = parser.parse_args()

    optional_fnl = (args.builder_script, args.base_fnl, args.output_fnl)
    if any(optional_fnl) and not all(optional_fnl):
        raise ValueError(
            "--builder-script, --base-fnl and --output-fnl must be supplied together"
        )

    current_rows = load_json(args.current_map).get("mapping", [])
    union_document = load_json(args.union_map)
    union_rows = union_document.get("mapping", [])
    expected_rows = load_json(args.expected_extension).get("mapping", [])
    validate_mapping_rows(current_rows, "current map")
    validate_mapping_rows(union_rows, "union map")

    if len(current_rows) != EXPECTED_CURRENT_MAPPING_COUNT:
        raise ValueError("Current map count changed")
    if len(union_rows) != EXPECTED_UNION_COUNT:
        raise ValueError("Union map count is not 2,368")
    if len(expected_rows) != EXPECTED_EXTENSION_COUNT:
        raise ValueError("Expected extension count is not 844")

    # The compatible builder copies base rows with dict(row), so exact list and
    # field equality is the strongest assignment ABI check.
    if union_rows[: len(current_rows)] != current_rows:
        raise ValueError("One or more of the retained 1,524 mapping rows changed")
    extension_rows = union_rows[len(current_rows) :]
    if extension_rows != expected_rows:
        raise ValueError("Built extension rows differ from the pinned deterministic selection")

    wansung = set(wansung_syllables())
    covered = {row["unicode_character"] for row in union_rows} & wansung
    if covered != wansung:
        missing = sorted(wansung - covered, key=ord)
        raise ValueError(
            f"Union map misses {len(missing)} Wansung syllables: "
            + " ".join(f"U+{ord(character):04X}" for character in missing[:20])
        )
    current_targets = {row["unicode_character"] for row in current_rows}
    if {row["unicode_character"] for row in extension_rows} != wansung - current_targets:
        raise ValueError("New targets are not exactly the formerly missing Wansung syllables")

    metadata_expected = {
        "retained_base_mapping_count": EXPECTED_CURRENT_MAPPING_COUNT,
        "extension_mapping_count": EXPECTED_EXTENSION_COUNT,
        "union_mapping_count": EXPECTED_UNION_COUNT,
    }
    metadata_actual = {
        key: union_document.get(key) for key in metadata_expected
    }
    if metadata_actual != metadata_expected:
        raise ValueError(
            f"Union count metadata mismatch: {metadata_actual} != {metadata_expected}"
        )

    if all(optional_fnl):
        validate_fnl_preservation(
            args.builder_script,
            args.base_fnl,
            args.output_fnl,
            current_rows,
            extension_rows,
        )

    print(
        "PASS: retained 1,524 assignments are field/byte-identical; "
        "844 deterministic rows were appended; all 2,350 Wansung syllables are covered; "
        f"union_sha256={canonical_json_sha256(union_rows)}; "
        f"fnl_checked={all(optional_fnl)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
