from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import pathlib
import re
from typing import Any


ENTRY_RE = re.compile(r'^;?([sm])\[(\d+)\]\s*=\s*"(.*)"$')
ARCHIVE_ENTRY_RE = re.compile(r"^(\d+):\s*(.*)$")
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')
JP_RE = re.compile(
    "["
    "\u3040-\u30ff"
    "\u3400-\u4dbf"
    "\u4e00-\u9fff"
    "\uf900-\ufaff"
    "]"
)
HANGUL_RE = re.compile("[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
FORMAT_TOKEN_RE = re.compile(
    r"%(?:\d+\$)?[-+#0 ']*(?:\d+|\*)?(?:\.(?:\d+|\*))?"
    r"(?:hh|h|ll|l|j|z|t|L)?[diuoxXfFeEgGaAcspn%]"
    r"|\{[^{}\r\n]+\}"
    r"|\\[nrt]"
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def decode_c_string(raw: str) -> tuple[str, bool]:
    try:
        value = ast.literal_eval(f'"{raw}"')
        if isinstance(value, str):
            return value, True
    except (SyntaxError, ValueError):
        pass
    return raw, False


def atomic_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp.replace(path)


def atomic_jsonl(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp.replace(path)


def parse_ain_text(path: pathlib.Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    current_function: str | None = None
    occurrences: list[dict[str, Any]] = []
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    function_counts: collections.Counter[str] = collections.Counter()
    parse_failures = 0

    for line_number, line in enumerate(lines, start=1):
        if line.startswith("; ") and not line.startswith("; s[") and not line.startswith("; m["):
            current_function = line[2:]
            continue
        match = ENTRY_RE.match(line)
        if not match:
            continue
        kind, ident_text, raw = match.groups()
        ident = int(ident_text)
        decoded, decoded_ok = decode_c_string(raw)
        parse_failures += int(not decoded_ok)
        context = current_function or "<unknown>"
        function_counts[context] += 1
        occurrence = {
            "kind": "message" if kind == "m" else "string",
            "id": ident,
            "source_raw": raw,
            "source": decoded,
            "decode_ok": decoded_ok,
            "function": context,
            "line": line_number,
        }
        occurrences.append(occurrence)
        key = (kind, ident)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = {
                "stable_id": f"NightRemaster.ain::{kind}[{ident}]",
                "kind": "message" if kind == "m" else "string",
                "id": ident,
                "source_raw": raw,
                "source": decoded,
                "source_sha256": sha256_text(decoded),
                "contexts": [context],
                "occurrence_lines": [line_number],
                "decode_ok": decoded_ok,
            }
        else:
            if context not in existing["contexts"]:
                existing["contexts"].append(context)
            existing["occurrence_lines"].append(line_number)
            if existing["source_raw"] != raw:
                existing.setdefault("conflicting_sources", []).append(
                    {
                        "source_raw": raw,
                        "source": decoded,
                        "function": context,
                        "line": line_number,
                    }
                )

    catalog: list[dict[str, Any]] = []
    for (kind, _ident), entry in sorted(by_key.items(), key=lambda item: (item[0][0], item[0][1])):
        source = entry["source"]
        entry["contains_japanese"] = bool(JP_RE.search(source))
        entry["contains_hangul"] = bool(HANGUL_RE.search(source))
        entry["protected_tokens"] = FORMAT_TOKEN_RE.findall(entry["source_raw"])
        entry["visibility"] = "display" if kind == "m" else "pending"
        entry["translation_status"] = "pending" if entry["contains_japanese"] else "not_applicable"
        catalog.append(entry)

    messages = [row for row in catalog if row["kind"] == "message"]
    strings = [row for row in catalog if row["kind"] == "string"]
    summary = {
        "schema": "yorugakuru.ain-text-summary.v1",
        "source": str(path),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "line_count": len(lines),
        "occurrence_count": len(occurrences),
        "unique_entry_count": len(catalog),
        "unique_message_count": len(messages),
        "unique_string_count": len(strings),
        "japanese_message_count": sum(row["contains_japanese"] for row in messages),
        "japanese_string_count": sum(row["contains_japanese"] for row in strings),
        "hangul_entry_count": sum(row["contains_hangul"] for row in catalog),
        "decode_failure_count": parse_failures,
        "conflicting_id_count": sum(bool(row.get("conflicting_sources")) for row in catalog),
        "function_count": len(function_counts),
        "top_functions_by_occurrences": [
            {"function": name, "occurrences": count}
            for name, count in function_counts.most_common(50)
        ],
    }
    return summary, catalog


def parse_archive_lists(directory: pathlib.Path) -> dict[str, Any]:
    archives: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.list.txt")):
        entries: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = ARCHIVE_ENTRY_RE.match(line)
            if not match:
                continue
            index, name = match.groups()
            suffix = pathlib.PurePosixPath(name.replace("\\", "/")).suffix.lower()
            entries.append({"index": int(index), "name": name, "extension": suffix})
        extension_counts = collections.Counter(row["extension"] or "<none>" for row in entries)
        archives.append(
            {
                "list_file": str(path),
                "list_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "archive": path.name.removesuffix(".list.txt"),
                "entry_count": len(entries),
                "extension_counts": dict(sorted(extension_counts.items())),
                "first_entry": entries[0]["name"] if entries else None,
                "last_entry": entries[-1]["name"] if entries else None,
            }
        )
    return {"schema": "yorugakuru.archive-list-summary.v1", "archives": archives}


def parse_ex_strings(path: pathlib.Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for ordinal, match in enumerate(QUOTED_RE.finditer(line)):
            raw = match.group(1)
            decoded, decoded_ok = decode_c_string(raw)
            rows.append(
                {
                    "stable_id": f"NightRemasterEX.ex::line[{line_number}]::string[{ordinal}]",
                    "line": line_number,
                    "ordinal": ordinal,
                    "source_raw": raw,
                    "source": decoded,
                    "source_sha256": sha256_text(decoded),
                    "contains_japanese": bool(JP_RE.search(decoded)),
                    "contains_hangul": bool(HANGUL_RE.search(decoded)),
                    "protected_tokens": FORMAT_TOKEN_RE.findall(raw),
                    "decode_ok": decoded_ok,
                    "visibility": "pending",
                    "translation_status": "pending" if JP_RE.search(decoded) else "not_applicable",
                }
            )
    summary = {
        "schema": "yorugakuru.ex-string-summary.v1",
        "source": str(path),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "quoted_string_occurrence_count": len(rows),
        "unique_string_count": len({row["source"] for row in rows}),
        "japanese_occurrence_count": sum(row["contains_japanese"] for row in rows),
        "hangul_occurrence_count": sum(row["contains_hangul"] for row in rows),
        "decode_failure_count": sum(not row["decode_ok"] for row in rows),
    }
    return summary, rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True, type=pathlib.Path)
    args = parser.parse_args()
    project = args.project_dir.resolve()

    ain_summary, ain_catalog = parse_ain_text(
        project / "extracted" / "ain" / "NightRemaster_text.txt"
    )
    ex_summary, ex_catalog = parse_ex_strings(
        project / "extracted" / "ex" / "NightRemasterEX.x"
    )
    archive_summary = parse_archive_lists(project / "audit" / "archive_lists")

    atomic_json(project / "audit" / "ain_text_summary.json", ain_summary)
    atomic_jsonl(project / "catalog" / "ain_entries_raw.jsonl", ain_catalog)
    atomic_json(project / "audit" / "ex_string_summary.json", ex_summary)
    atomic_jsonl(project / "catalog" / "ex_strings_raw.jsonl", ex_catalog)
    atomic_json(project / "audit" / "archive_list_summary.json", archive_summary)

    result = {
        "ain": ain_summary,
        "ex": ex_summary,
        "archives": archive_summary,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
