from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re


ENTRY_RE = re.compile(r'^(?P<prefix>;(?P<kind>[ms])\[(?P<id>\d+)\]\s*=\s*)(?P<literal>".*")$')


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply a reviewed Korean translation map to an alice-tools AIN text dump using an FNL proxy map."
    )
    parser.add_argument("--input-text", required=True, type=pathlib.Path)
    parser.add_argument("--translation-map", required=True, type=pathlib.Path)
    parser.add_argument("--proxy-map", required=True, type=pathlib.Path)
    parser.add_argument("--output-text", required=True, type=pathlib.Path)
    parser.add_argument("--manifest-output", required=True, type=pathlib.Path)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate source identities and proxy coverage without writing output files.",
    )
    args = parser.parse_args()

    translation_document = load_json(args.translation_map)
    proxy_document = load_json(args.proxy_map)
    proxy_by_character = {
        row["unicode_character"]: row["proxy_character"]
        for row in proxy_document.get("mapping", [])
    }
    proxy_index_by_character = {
        row["unicode_character"]: row["proxy_index"]
        for row in proxy_document.get("mapping", [])
    }

    translations = {}
    for entry in translation_document.get("entries", []):
        stable_id = entry["stable_id"]
        match = re.fullmatch(r"NightRemaster\.ain::([ms])\[(\d+)\]", stable_id)
        if not match:
            raise ValueError(f"Unsupported stable_id: {stable_id}")
        key = (match.group(1), int(match.group(2)))
        if key in translations:
            raise ValueError(f"Duplicate translation ID: {stable_id}")
        calculated_hash = hashlib.sha256(entry["source"].encode("utf-8")).hexdigest()
        if calculated_hash != entry["source_sha256"]:
            raise ValueError(f"Source hash mismatch in translation map: {stable_id}")
        translations[key] = entry

    def proxy_encode(target: str, stable_id: str) -> str:
        output = []
        for character in target:
            try:
                roundtrip_ok = character.encode("cp932").decode("cp932") == character
            except UnicodeError:
                roundtrip_ok = False
            if roundtrip_ok:
                output.append(character)
                continue
            if character not in proxy_by_character:
                raise ValueError(
                    f"Missing proxy for {character!r} (U+{ord(character):04X}) in {stable_id}"
                )
            output.append(proxy_by_character[character])
        encoded = "".join(output)
        encoded.encode("cp932")
        return encoded

    original_bytes = args.input_text.read_bytes()
    original_text = original_bytes.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in original_text else "\n"
    had_final_newline = original_text.endswith(("\n", "\r"))
    lines = original_text.splitlines()
    seen = {key: 0 for key in translations}
    changed_occurrences = []

    for line_index, line in enumerate(lines):
        match = ENTRY_RE.match(line)
        if not match:
            continue
        key = (match.group("kind"), int(match.group("id")))
        if key not in translations:
            continue
        entry = translations[key]
        try:
            source_in_dump = json.loads(match.group("literal"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid quoted AIN text literal on line {line_index + 1}: {error}"
            ) from error
        if source_in_dump != entry["source"]:
            raise ValueError(
                f"Source mismatch for {entry['stable_id']} on line {line_index + 1}: "
                f"{source_in_dump!r} != {entry['source']!r}"
            )
        proxied = proxy_encode(entry["target"], entry["stable_id"])
        literal = json.dumps(proxied, ensure_ascii=False)
        lines[line_index] = f"{match.group('prefix')}{literal}"
        seen[key] += 1
        changed_occurrences.append(
            {
                "stable_id": entry["stable_id"],
                "line_number": line_index + 1,
                "target_sha256": hashlib.sha256(entry["target"].encode("utf-8")).hexdigest(),
                "proxy_text_sha256": hashlib.sha256(proxied.encode("utf-8")).hexdigest(),
                "proxy_indices": sorted(
                    {
                        proxy_index_by_character[character]
                        for character in entry["target"]
                        if character in proxy_index_by_character
                    }
                ),
            }
        )

    missing = [
        translations[key]["stable_id"] for key, occurrence_count in seen.items() if occurrence_count == 0
    ]
    if missing:
        raise ValueError(f"Translation IDs not found in AIN dump: {missing[:20]}")

    output_text = newline.join(lines) + (newline if had_final_newline else "")
    output_bytes = output_text.encode("utf-8")
    if args.validate_only:
        print(
            json.dumps(
                {
                    "mode": "validate_only",
                    "translated_stable_id_count": len(translations),
                    "changed_occurrence_count": len(changed_occurrences),
                    "prospective_output_size": len(output_bytes),
                    "prospective_output_sha256": hashlib.sha256(output_bytes).hexdigest(),
                    "verdict": "pass",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    args.output_text.parent.mkdir(parents=True, exist_ok=True)
    args.output_text.write_bytes(output_bytes)
    manifest = {
        "schema": "contextual-game-localization.ain-proxy-text-manifest.v1",
        "input_text": {
            "path": str(args.input_text),
            "size": len(original_bytes),
            "sha256": hashlib.sha256(original_bytes).hexdigest(),
        },
        "translation_map": {
            "path": str(args.translation_map),
            "sha256": sha256_file(args.translation_map),
            "entry_count": len(translations),
        },
        "proxy_map": {
            "path": str(args.proxy_map),
            "sha256": sha256_file(args.proxy_map),
            "mapping_count": len(proxy_by_character),
        },
        "output_text": {
            "path": str(args.output_text),
            "size": len(output_bytes),
            "sha256": hashlib.sha256(output_bytes).hexdigest(),
            "encoding": "utf-8",
        },
        "translated_stable_id_count": len(translations),
        "changed_occurrence_count": len(changed_occurrences),
        "occurrences": changed_occurrences,
        "verdict": "pass",
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output_text": str(args.output_text),
                "output_sha256": manifest["output_text"]["sha256"],
                "translated_stable_id_count": len(translations),
                "changed_occurrence_count": len(changed_occurrences),
                "verdict": "pass",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
