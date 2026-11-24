from __future__ import annotations

import argparse
import hashlib
import pathlib

from wansung_common import (
    EXPECTED_CAPACITY_HEADROOM,
    EXPECTED_EXTENSION_COUNT,
    EXPECTED_UNION_COUNT,
    WANSUNG_COUNT,
    assert_expected_counts,
    canonical_json_sha256,
    expected_extension_rows,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_mapping_rows,
    wansung_syllables,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a synthetic reviewed translation fixture that makes the "
            "compatible FNL builder require every KS X 1001/Wansung syllable."
        )
    )
    parser.add_argument("--current-map", required=True, type=pathlib.Path)
    parser.add_argument("--proxy-capacity", required=True, type=pathlib.Path)
    parser.add_argument("--translation-output", required=True, type=pathlib.Path)
    parser.add_argument("--expected-extension-output", required=True, type=pathlib.Path)
    parser.add_argument("--plan-output", required=True, type=pathlib.Path)
    args = parser.parse_args()

    current_document = load_json(args.current_map)
    capacity_document = load_json(args.proxy_capacity)
    current_rows = current_document.get("mapping", [])
    validate_mapping_rows(current_rows, "current map")

    wansung = wansung_syllables()
    wansung_set = set(wansung)
    current_wansung = {
        row["unicode_character"]
        for row in current_rows
        if row["unicode_character"] in wansung_set
    }
    missing, candidates, extension_rows = expected_extension_rows(
        current_rows, capacity_document, wansung
    )
    assert_expected_counts(current_rows, current_wansung, missing, candidates)

    source = "Synthetic KS X 1001/Wansung proxy-capacity coverage fixture"
    translation_document = {
        "schema": "contextual-game-localization.synthetic-reviewed-translation-map.v1",
        "purpose": (
            "FNL capacity input only; the target enumerates CP949 B0A1-C8FE and "
            "is not a user-visible translation."
        ),
        "translator_model": "Codex internal",
        "provenance": {
            "agent": "final_map_invariant_audit/hangul_ime_wansung_agent",
            "generation": "deterministic CP949 byte-range enumeration",
        },
        "entries": [
            {
                "stable_id": "synthetic::ks-x-1001-wansung-cp949-b0a1-c8fe",
                "source": source,
                "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                "target": "".join(wansung),
                "translation_required": True,
                "review_status": "reviewed",
                "notes": "Exactly 2,350 unique Wansung syllables in CP949 byte order.",
            }
        ],
    }
    write_json(args.translation_output, translation_document)

    expected_extension_document = {
        "schema": "contextual-game-localization.wansung-expected-extension.v1",
        "selection_algorithm": (
            "Missing targets sorted by Unicode code point, paired with eligible "
            "capacity candidates sorted by descending FNL index."
        ),
        "extension_mapping_count": len(extension_rows),
        "mapping": extension_rows,
    }
    write_json(args.expected_extension_output, expected_extension_document)

    current_assignment_bytes = b"".join(
        row["unicode_character"].encode("utf-8")
        + b"\0"
        + bytes.fromhex(row["proxy_sjis_hex"])
        + int(row["proxy_index"]).to_bytes(4, "little")
        for row in current_rows
    )
    plan_document = {
        "schema": "contextual-game-localization.wansung-extension-plan.v1",
        "inputs": {
            "current_map": {
                "path": str(args.current_map),
                "sha256": sha256_file(args.current_map),
                "mapping_count": len(current_rows),
                "mapping_canonical_sha256": canonical_json_sha256(current_rows),
                "assignment_bytes_sha256": sha256_bytes(current_assignment_bytes),
            },
            "proxy_capacity": {
                "path": str(args.proxy_capacity),
                "sha256": sha256_file(args.proxy_capacity),
            },
        },
        "wansung": {
            "cp949_byte_range": "B0A1-C8FE (lead B0-C8, trail A1-FE)",
            "count": WANSUNG_COUNT,
            "utf8_sequence_sha256": sha256_bytes("".join(wansung).encode("utf-8")),
            "first": {"character": wansung[0], "codepoint": f"U+{ord(wansung[0]):04X}"},
            "last": {"character": wansung[-1], "codepoint": f"U+{ord(wansung[-1]):04X}"},
            "already_mapped_count": len(current_wansung),
            "missing_count": len(missing),
            "missing_utf8_sequence_sha256": sha256_bytes("".join(missing).encode("utf-8")),
        },
        "capacity": {
            "eligible_unused_candidate_count": len(candidates),
            "consumed_candidate_count": len(extension_rows),
            "remaining_headroom": len(candidates) - len(extension_rows),
        },
        "expected_build": {
            "retained_base_mapping_count": len(current_rows),
            "extension_mapping_count": EXPECTED_EXTENSION_COUNT,
            "union_mapping_count": EXPECTED_UNION_COUNT,
            "forced_proxy_target_count": 0,
            "capacity_headroom": EXPECTED_CAPACITY_HEADROOM,
        },
        "generated": {
            "translation": {
                "path": str(args.translation_output),
                "sha256": sha256_file(args.translation_output),
            },
            "expected_extension": {
                "path": str(args.expected_extension_output),
                "sha256": sha256_file(args.expected_extension_output),
                "mapping_canonical_sha256": canonical_json_sha256(extension_rows),
            },
        },
        "verdict": "pass",
    }
    write_json(args.plan_output, plan_document)

    print(
        f"PASS: current={len(current_rows)}, current_wansung={len(current_wansung)}, "
        f"extension={len(extension_rows)}, union={len(current_rows) + len(extension_rows)}, "
        f"capacity={len(candidates)}, headroom={len(candidates) - len(extension_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
