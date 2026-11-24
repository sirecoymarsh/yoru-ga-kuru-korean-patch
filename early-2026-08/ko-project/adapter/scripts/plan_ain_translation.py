from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import defaultdict


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: pathlib.Path):
    with path.open("r", encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL line {line_number}: {error}") from error


def chunks(values, size):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--message-plan", required=True, type=pathlib.Path)
    parser.add_argument("--string-plan", required=True, type=pathlib.Path)
    parser.add_argument("--max-message-entries", default=180, type=int)
    parser.add_argument("--max-string-entries", default=150, type=int)
    args = parser.parse_args()

    messages_by_function = defaultdict(list)
    strings_by_function = defaultdict(list)
    source_rows = 0
    for row in read_jsonl(args.input):
        source_rows += 1
        if not row.get("contains_japanese"):
            continue
        contexts = row.get("contexts") or ["<no-context>"]
        primary_context = contexts[0]
        row_summary = {
            "stable_id": row["stable_id"],
            "numeric_id": row["id"],
            "source_sha256": row["source_sha256"],
            "source_character_count": len(row["source"]),
            "primary_context": primary_context,
            "all_contexts": contexts,
            "first_occurrence_line": min(row.get("occurrence_lines") or [0]),
            "protected_tokens": row.get("protected_tokens", []),
        }
        if row["kind"] == "message":
            messages_by_function[primary_context].append(row_summary)
        elif row["kind"] == "string":
            strings_by_function[primary_context].append(row_summary)

    def make_plan(groups, max_entries, lane, translation_ready):
        packets = []
        ordered_groups = sorted(
            groups.items(),
            key=lambda item: min(row["first_occurrence_line"] for row in item[1]),
        )
        pending_entries = []
        pending_functions = []
        pending_chunk_notes = []

        def emit(packet_entries, functions, chunk_notes):
            if not packet_entries:
                return
            packet_entries.sort(
                key=lambda row: (row["first_occurrence_line"], row["numeric_id"])
            )
            first = packet_entries[0]
            last = packet_entries[-1]
            pilot_overlap = [
                entry
                for entry in packet_entries
                if entry["stable_id"].startswith("NightRemaster.ain::m[")
                and 2211 <= entry["numeric_id"] <= 2400
                and "ＥＶ／元／E00001" in entry["all_contexts"]
            ]
            status = (
                "partially_frozen_pilot"
                if pilot_overlap
                else ("planned" if translation_ready else "pending_visibility_triage")
            )
            packets.append(
                {
                    "packet_id": f"{lane}_{len(packets) + 1:04d}",
                    "lane": lane,
                    "status": status,
                    "functions": functions,
                    "function_count": len(functions),
                    "split_function_chunks": chunk_notes,
                    "entry_count": len(packet_entries),
                    "source_character_count": sum(
                        entry["source_character_count"] for entry in packet_entries
                    ),
                    "first_numeric_id": min(
                        entry["numeric_id"] for entry in packet_entries
                    ),
                    "last_numeric_id": max(
                        entry["numeric_id"] for entry in packet_entries
                    ),
                    "first_occurrence_line": first["first_occurrence_line"],
                    "last_occurrence_line": last["first_occurrence_line"],
                    "cross_context_entry_count": sum(
                        1 for entry in packet_entries if len(entry["all_contexts"]) > 1
                    ),
                    "pilot_frozen_stable_id_count": len(pilot_overlap),
                    "stable_ids": [entry["stable_id"] for entry in packet_entries],
                }
            )

        for function, entries in ordered_groups:
            entries.sort(key=lambda row: (row["first_occurrence_line"], row["numeric_id"]))
            if len(entries) > max_entries:
                emit(pending_entries, pending_functions, pending_chunk_notes)
                pending_entries, pending_functions, pending_chunk_notes = [], [], []
                function_chunks = list(chunks(entries, max_entries))
                for chunk_index, packet_entries in enumerate(function_chunks, 1):
                    emit(
                        packet_entries,
                        [function],
                        [
                            {
                                "function": function,
                                "chunk_index": chunk_index,
                                "chunk_count": len(function_chunks),
                            }
                        ],
                    )
                continue
            if pending_entries and len(pending_entries) + len(entries) > max_entries:
                emit(pending_entries, pending_functions, pending_chunk_notes)
                pending_entries, pending_functions, pending_chunk_notes = [], [], []
            pending_entries.extend(entries)
            pending_functions.append(function)
        emit(pending_entries, pending_functions, pending_chunk_notes)
        return packets

    message_packets = make_plan(
        messages_by_function,
        args.max_message_entries,
        "ain_message",
        translation_ready=True,
    )
    string_packets = make_plan(
        strings_by_function,
        args.max_string_entries,
        "ain_string",
        translation_ready=False,
    )

    def plan_document(packets, lane, workflow):
        return {
            "schema": "contextual-game-localization.packet-plan.v1",
            "lane": lane,
            "source_catalog": {
                "path": str(args.input),
                "sha256": sha256_file(args.input),
                "row_count": source_rows,
            },
            "semantic_source_language": "ja-JP",
            "target_language": "ko-KR",
            "provider": "Codex internal model",
            "intermediate_language": None,
            "workflow": workflow,
            "packet_count": len(packets),
            "entry_count": sum(packet["entry_count"] for packet in packets),
            "source_character_count": sum(
                packet["source_character_count"] for packet in packets
            ),
            "packets": packets,
        }

    message_document = plan_document(
        message_packets,
        "ain_message",
        [
            "Freeze glossary/style-guide hash.",
            "Materialize one packet with neighboring boundary context.",
            "Draft from Japanese directly with Codex internal model.",
            "Run independent Codex cross-review.",
            "Validate identity, source hash, tokens, encoding, and Japanese residue.",
            "Merge centrally with exactly one owner per stable_id.",
        ],
    )
    string_document = plan_document(
        string_packets,
        "ain_string",
        [
            "Trace each string consumer and classify display leaf versus lookup key.",
            "Translate only proven display strings.",
            "Keep filenames, voice IDs, asset keys, format strings, and exact-match tokens unchanged.",
            "Cross-review and validate before merging.",
        ],
    )
    for path, document in (
        (args.message_plan, message_document),
        (args.string_plan, string_document),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(
        json.dumps(
            {
                "message_plan": {
                    "path": str(args.message_plan),
                    "packet_count": message_document["packet_count"],
                    "entry_count": message_document["entry_count"],
                    "source_character_count": message_document[
                        "source_character_count"
                    ],
                },
                "string_plan": {
                    "path": str(args.string_plan),
                    "packet_count": string_document["packet_count"],
                    "entry_count": string_document["entry_count"],
                    "source_character_count": string_document[
                        "source_character_count"
                    ],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
