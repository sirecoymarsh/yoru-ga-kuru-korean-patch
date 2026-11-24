from __future__ import annotations

import argparse
import pathlib

from wansung_common import (
    EXPECTED_EXTENSION_COUNT,
    WANSUNG_COUNT,
    assert_expected_counts,
    canonical_json_sha256,
    expected_extension_rows,
    load_json,
    sha256_bytes,
    validate_mapping_rows,
    wansung_syllables,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the pre-build Wansung fixture.")
    parser.add_argument("--current-map", required=True, type=pathlib.Path)
    parser.add_argument("--proxy-capacity", required=True, type=pathlib.Path)
    parser.add_argument("--translation", required=True, type=pathlib.Path)
    parser.add_argument("--expected-extension", required=True, type=pathlib.Path)
    args = parser.parse_args()

    current_rows = load_json(args.current_map).get("mapping", [])
    capacity = load_json(args.proxy_capacity)
    translation = load_json(args.translation)
    expected_document = load_json(args.expected_extension)
    expected_rows = expected_document.get("mapping", [])
    validate_mapping_rows(current_rows, "current map")
    validate_mapping_rows(expected_rows, "expected extension")

    wansung = wansung_syllables()
    entries = translation.get("entries", [])
    if len(entries) != 1:
        raise ValueError("Synthetic translation must contain exactly one entry")
    entry = entries[0]
    if entry.get("review_status") != "reviewed" or not entry.get("translation_required"):
        raise ValueError("Synthetic translation entry is not reviewed and required")
    target = entry.get("target")
    if target != "".join(wansung):
        raise ValueError("Synthetic target is not the exact CP949 B0A1-C8FE sequence")
    if len(target) != WANSUNG_COUNT or len(set(target)) != WANSUNG_COUNT:
        raise ValueError("Synthetic target does not contain 2,350 unique syllables")

    wansung_set = set(wansung)
    current_wansung = {
        row["unicode_character"]
        for row in current_rows
        if row["unicode_character"] in wansung_set
    }
    missing, candidates, recomputed_rows = expected_extension_rows(
        current_rows, capacity, wansung
    )
    assert_expected_counts(current_rows, current_wansung, missing, candidates)
    if expected_rows != recomputed_rows:
        raise ValueError(
            "Expected extension rows differ from the compatible builder's deterministic selection"
        )
    if len(expected_rows) != EXPECTED_EXTENSION_COUNT:
        raise ValueError("Expected extension row count mismatch")
    if {row["unicode_character"] for row in expected_rows} != set(missing):
        raise ValueError("Expected extension targets are not exactly the missing Wansung set")

    print(
        "PASS: fixture covers 2,350 Wansung syllables; "
        f"current={len(current_rows)}, retained_wansung={len(current_wansung)}, "
        f"new={len(expected_rows)}, candidate_capacity={len(candidates)}, "
        f"extension_sha256={canonical_json_sha256(expected_rows)}, "
        f"wansung_sha256={sha256_bytes(target.encode('utf-8'))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
