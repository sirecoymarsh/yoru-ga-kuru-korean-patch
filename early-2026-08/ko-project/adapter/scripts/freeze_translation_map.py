from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from collections import Counter


JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def token_counter(text: str, tokens: list[str]) -> Counter:
    return Counter({token: text.count(token) for token in tokens})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", action="append", required=True, type=pathlib.Path)
    parser.add_argument("--review", action="append", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--qa-output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if len(args.packet) != len(args.review):
        raise ValueError("--packet and --review counts must match")

    frozen_entries = []
    seen_ids = set()
    packet_reports = []
    failures = []

    identity_keys = [
        "stable_id",
        "kind",
        "numeric_id",
        "source_sha256",
        "source",
        "function",
        "role",
        "speaker",
        "previous_source",
        "next_source",
        "protected_tokens",
        "translation_required",
    ]

    for packet_path, review_path in zip(args.packet, args.review, strict=True):
        packet = load_json(packet_path)
        review = load_json(review_path)
        packet_id = packet["packet_id"]
        if review.get("packet_id") != packet_id:
            failures.append(f"{packet_id}: reviewed packet_id mismatch")
        source_entries = packet.get("entries", [])
        reviewed_entries = review.get("entries", [])
        if len(source_entries) != len(reviewed_entries):
            failures.append(f"{packet_id}: entry count mismatch")
            continue

        reviewed_count = 0
        translatable_count = 0
        for source_entry, reviewed_entry in zip(
            source_entries, reviewed_entries, strict=True
        ):
            stable_id = source_entry["stable_id"]
            for key in identity_keys:
                if source_entry.get(key) != reviewed_entry.get(key):
                    failures.append(f"{stable_id}: identity field changed: {key}")
            calculated_source_hash = sha256_bytes(source_entry["source"].encode("utf-8"))
            if calculated_source_hash != source_entry["source_sha256"]:
                failures.append(f"{stable_id}: source SHA-256 mismatch")
            if stable_id in seen_ids:
                failures.append(f"{stable_id}: duplicate ownership")
            seen_ids.add(stable_id)

            if not source_entry["translation_required"]:
                if reviewed_entry.get("target") != source_entry["source"]:
                    failures.append(f"{stable_id}: non-translatable target changed")
                continue

            translatable_count += 1
            target = reviewed_entry.get("target", "")
            if not target:
                failures.append(f"{stable_id}: empty reviewed target")
            if reviewed_entry.get("review_status") != "reviewed":
                failures.append(f"{stable_id}: review_status is not reviewed")
            else:
                reviewed_count += 1
            protected_tokens = source_entry.get("protected_tokens", [])
            if token_counter(source_entry["source"], protected_tokens) != token_counter(
                target, protected_tokens
            ):
                failures.append(f"{stable_id}: protected-token count mismatch")
            if JAPANESE_RE.search(target):
                failures.append(f"{stable_id}: strong Japanese residue in target")

            frozen_entries.append(
                {
                    "key": stable_id,
                    "file": "NightRemaster.ain",
                    "uid": f"{source_entry['kind'][0]}[{source_entry['numeric_id']}]",
                    "stable_id": stable_id,
                    "kind": source_entry["kind"],
                    "numeric_id": source_entry["numeric_id"],
                    "source": source_entry["source"],
                    "source_sha256": source_entry["source_sha256"],
                    "translation": target,
                    "target": target,
                    "allow_unchanged": target == source_entry["source"],
                    "allow_non_korean": not bool(
                        re.search(r"[\uac00-\ud7a3]", target)
                    ),
                    "function": source_entry["function"],
                    "role": source_entry["role"],
                    "speaker": source_entry["speaker"],
                    "protected_tokens": protected_tokens,
                    "provenance": {
                        "packet_id": packet_id,
                        "draft_provider": "Codex internal model",
                        "review_provider": "independent Codex pass",
                        "review_status": reviewed_entry.get("review_status"),
                        "review_notes": reviewed_entry.get("translator_notes", ""),
                    },
                }
            )

        packet_reports.append(
            {
                "packet_id": packet_id,
                "source_path": str(packet_path),
                "source_sha256": sha256_file(packet_path),
                "review_path": str(review_path),
                "review_sha256": sha256_file(review_path),
                "entry_count": len(source_entries),
                "translatable_count": translatable_count,
                "reviewed_count": reviewed_count,
                "review_summary": review.get("review_summary"),
            }
        )

    if failures:
        raise ValueError("Translation freeze validation failed:\n" + "\n".join(failures[:100]))

    frozen_entries.sort(key=lambda entry: (entry["kind"], entry["numeric_id"]))
    translation_map = {
        "schema": "contextual-game-localization.translation-map.v1",
        "status": "pilot_frozen_after_independent_review",
        "semantic_source_language": "ja-JP",
        "target_language": "ko-KR",
        "translation_provider": "Codex internal model",
        "intermediate_language": None,
        "source_asset": "NightRemaster.ain",
        "entry_count": len(frozen_entries),
        "packets": packet_reports,
        "entries": frozen_entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(translation_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    map_sha256 = sha256_file(args.output)
    target_characters = sorted(
        {character for entry in frozen_entries for character in entry["target"]},
        key=ord,
    )
    message_ids = [
        entry["numeric_id"] for entry in frozen_entries if entry["kind"] == "message"
    ]
    functions = {entry["function"] for entry in frozen_entries}
    if message_ids and len(functions) == 1:
        function_name = next(iter(functions))
        function_match = re.search(r"[Ee]\d+$", function_name)
        function_slug = (
            function_match.group(0).lower()
            if function_match
            else re.sub(r"\W+", "_", function_name.lower()).strip("_")
        )
        qa_scope = (
            f"pilot_{function_slug}_m{min(message_ids)}_m{max(message_ids)}"
        )
    else:
        qa_scope = "pilot_multi_packet"
    hangul_syllables = [
        character for character in target_characters if "\uac00" <= character <= "\ud7a3"
    ]
    non_cp932 = []
    for character in target_characters:
        try:
            if character.encode("cp932").decode("cp932") != character:
                non_cp932.append(character)
        except UnicodeError:
            non_cp932.append(character)

    qa = {
        "schema": "contextual-game-localization.language-qa.v1",
        "scope": qa_scope,
        "translation_map": {
            "path": str(args.output),
            "sha256": map_sha256,
            "entry_count": len(frozen_entries),
        },
        "packet_count": len(packet_reports),
        "source_entry_count": sum(report["entry_count"] for report in packet_reports),
        "reviewed_translation_count": len(frozen_entries),
        "identity_error_count": 0,
        "protected_token_error_count": 0,
        "strong_japanese_residue_count": 0,
        "unique_target_character_count": len(target_characters),
        "unique_hangul_syllable_count": len(hangul_syllables),
        "unique_non_cp932_character_count": len(non_cp932),
        "non_cp932_characters": non_cp932,
        "verdict": "pass",
        "limitations": [
            "This QA covers only the frozen pilot range, not the full game.",
            "Runtime rendering, layout, AIN proxy encoding, and FNL patching are separate pending gates.",
        ],
    }
    args.qa_output.parent.mkdir(parents=True, exist_ok=True)
    args.qa_output.write_text(
        json.dumps(qa, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "translation_map": str(args.output),
                "translation_map_sha256": map_sha256,
                "entry_count": len(frozen_entries),
                "unique_non_cp932_character_count": len(non_cp932),
                "qa": str(args.qa_output),
                "verdict": "pass",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
