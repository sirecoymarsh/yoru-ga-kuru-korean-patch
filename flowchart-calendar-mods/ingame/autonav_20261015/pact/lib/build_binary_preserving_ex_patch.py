from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pathlib
import struct
import tempfile
import zlib
from typing import Iterable


EX_INT = 1
EX_FLOAT = 2
EX_STRING = 3
EX_TABLE = 4
EX_LIST = 5
EX_TREE = 6


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
    ) as handle:
        temp = pathlib.Path(handle.name)
        handle.write(data)
        handle.flush()
    temp.replace(path)


def atomic_json(path: pathlib.Path, document: dict) -> None:
    atomic_write(
        path,
        (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def make_ex_tables() -> tuple[bytes, bytes]:
    decode = bytearray(256)
    for i in range(256):
        tmpfor = i
        tmp = tmpfor
        tmp = (tmp & 0x55) + ((tmp >> 1) & 0x55)
        tmp = (tmp & 0x33) + ((tmp >> 2) & 0x33)
        tmp = (tmp & 0x0F) + ((tmp >> 4) & 0x0F)
        if (tmp & 1) == 0:
            tmpfor = ((tmpfor << (8 - tmp)) | (tmpfor >> tmp)) & 0xFF
        else:
            tmpfor = ((tmpfor >> (8 - tmp)) | (tmpfor << tmp)) & 0xFF
        decode[i] = tmpfor
    encode = bytearray(256)
    for i, value in enumerate(decode):
        encode[value] = i
    return bytes(decode), bytes(encode)


EX_DECODE, EX_ENCODE = make_ex_tables()


@dataclasses.dataclass
class StringNode:
    path: tuple
    content: bytes
    replacement: bytes | None = None

    @property
    def value(self) -> bytes:
        return self.content.split(b"\0", 1)[0]

    def serialize(self) -> bytes:
        if self.replacement is None:
            return struct.pack("<I", len(self.content)) + self.content
        if b"\0" in self.replacement:
            raise ValueError(f"Embedded NUL in replacement at {self.path!r}")
        body = self.replacement
        body += b"\0" * ((-len(body)) & 3)
        return struct.pack("<I", len(body)) + body


@dataclasses.dataclass
class ScalarNode:
    type_id: int
    raw: bytes
    path: tuple

    def serialize(self) -> bytes:
        return self.raw


@dataclasses.dataclass
class FieldNode:
    type_id: int
    name: StringNode
    has_value: int
    is_index: int
    default: object | None
    subfields: list["FieldNode"]
    path: tuple

    def serialize(self) -> bytes:
        out = bytearray(struct.pack("<I", self.type_id))
        out += self.name.serialize()
        out += struct.pack("<II", self.has_value, self.is_index)
        if self.has_value:
            out += serialize_payload(self.default)
        if self.type_id == EX_TABLE:
            out += struct.pack("<I", len(self.subfields))
            for field in self.subfields:
                out += field.serialize()
        return bytes(out)


@dataclasses.dataclass
class ValueNode:
    type_id: int
    payload: object
    path: tuple

    def serialize(self) -> bytes:
        return struct.pack("<I", self.type_id) + serialize_payload(self.payload)


@dataclasses.dataclass
class TableNode:
    fields: list[FieldNode]
    rows: list[list[ValueNode]]
    dimensions: tuple[int, int]
    has_own_fields: bool
    path: tuple

    def serialize(self) -> bytes:
        out = bytearray()
        if self.has_own_fields:
            out += struct.pack("<I", len(self.fields))
            for field in self.fields:
                out += field.serialize()
        out += struct.pack("<II", *self.dimensions)
        for row in self.rows:
            for value in row:
                out += value.serialize()
        return bytes(out)


@dataclasses.dataclass
class ListItemNode:
    value: ValueNode
    original_size: int
    path: tuple

    def serialize(self) -> bytes:
        payload = serialize_payload(self.value.payload)
        return struct.pack("<II", self.value.type_id, len(payload)) + payload


@dataclasses.dataclass
class ListNode:
    items: list[ListItemNode]
    path: tuple

    def serialize(self) -> bytes:
        out = bytearray(struct.pack("<I", len(self.items)))
        for item in self.items:
            out += item.serialize()
        return bytes(out)


@dataclasses.dataclass
class TreeNode:
    name: StringNode
    is_leaf: int
    children: list["TreeNode"]
    leaf_name: StringNode | None
    leaf_value: ValueNode | None
    leaf_original_size: int | None
    trailing_zero: int | None
    path: tuple

    def serialize(self) -> bytes:
        out = bytearray(self.name.serialize())
        out += struct.pack("<I", self.is_leaf)
        if not self.is_leaf:
            out += struct.pack("<I", len(self.children))
            for child in self.children:
                out += child.serialize()
            return bytes(out)
        assert self.leaf_name is not None and self.leaf_value is not None
        leaf_payload = self.leaf_name.serialize() + serialize_payload(
            self.leaf_value.payload
        )
        out += struct.pack("<II", self.leaf_value.type_id, len(leaf_payload))
        out += leaf_payload
        out += struct.pack("<I", self.trailing_zero or 0)
        return bytes(out)


@dataclasses.dataclass
class BlockNode:
    type_id: int
    name: StringNode
    payload: object
    original_size: int
    path: tuple

    def serialize(self) -> bytes:
        body = self.name.serialize() + serialize_payload(self.payload)
        return struct.pack("<II", self.type_id, len(body)) + body


def serialize_payload(payload: object) -> bytes:
    if isinstance(payload, (StringNode, ScalarNode, TableNode, ListNode, TreeNode)):
        return payload.serialize()
    raise TypeError(f"Unsupported EX payload node: {type(payload)!r}")


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.rows_first: bool | None = None
        self.strings: dict[tuple, StringNode] = {}
        self.scalars: dict[tuple, ScalarNode] = {}

    def need(self, size: int) -> None:
        if self.pos + size > len(self.data):
            raise ValueError(
                f"EX payload truncated at 0x{self.pos:x}: need {size}, have {len(self.data)-self.pos}"
            )

    def read(self, size: int) -> bytes:
        self.need(size)
        value = self.data[self.pos : self.pos + size]
        self.pos += size
        return value

    def u32(self) -> int:
        return struct.unpack("<I", self.read(4))[0]

    def string(self, path: tuple) -> StringNode:
        size = self.u32()
        if size & 3:
            raise ValueError(f"Invalid padded string size {size} at {path!r}")
        content = self.read(size)
        node = StringNode(path=path, content=content)
        if path in self.strings:
            raise ValueError(f"Duplicate string path: {path!r}")
        self.strings[path] = node
        return node

    def scalar(self, type_id: int, path: tuple) -> ScalarNode:
        node = ScalarNode(type_id=type_id, raw=self.read(4), path=path)
        if path in self.scalars:
            raise ValueError(f"Duplicate scalar path: {path!r}")
        self.scalars[path] = node
        return node

    def field(self, path: tuple) -> FieldNode:
        type_id = self.u32()
        if type_id < EX_INT or type_id > EX_TABLE:
            raise ValueError(f"Invalid field type {type_id} at {path!r}")
        name = self.string(path + ("name",))
        has_value = self.u32()
        is_index = self.u32()
        default = None
        if has_value:
            default = self.payload(type_id, path + ("default",), None)
        subfields: list[FieldNode] = []
        if type_id == EX_TABLE:
            count = self.u32()
            subfields = [
                self.field(path + ("subfield", index)) for index in range(count)
            ]
        return FieldNode(
            type_id=type_id,
            name=name,
            has_value=has_value,
            is_index=is_index,
            default=default,
            subfields=subfields,
            path=path,
        )

    def table(
        self, path: tuple, borrowed_fields: list[FieldNode] | None
    ) -> TableNode:
        has_own_fields = borrowed_fields is None
        if has_own_fields:
            field_count = self.u32()
            fields = [
                self.field(path + ("field", index)) for index in range(field_count)
            ]
        else:
            fields = borrowed_fields
        dim1 = self.u32()
        dim2 = self.u32()
        nr_fields = len(fields)
        if self.rows_first is None:
            if dim1 == nr_fields and dim2 != nr_fields:
                self.rows_first = False
            elif dim2 == nr_fields:
                self.rows_first = True
            else:
                raise ValueError(
                    f"Cannot infer EX table layout at {path!r}: dims={dim1,dim2}, fields={nr_fields}"
                )
        nr_rows, nr_columns = (
            (dim1, dim2) if self.rows_first else (dim2, dim1)
        )
        if nr_columns != nr_fields:
            raise ValueError(
                f"EX table field/column mismatch at {path!r}: {nr_fields} != {nr_columns}"
            )
        rows: list[list[ValueNode]] = []
        for row_index in range(nr_rows):
            row = []
            for column_index, field in enumerate(fields):
                value_path = path + ("row", row_index, "column", column_index)
                row.append(self.value(value_path, field.subfields or None))
            rows.append(row)
        return TableNode(
            fields=fields,
            rows=rows,
            dimensions=(dim1, dim2),
            has_own_fields=has_own_fields,
            path=path,
        )

    def list_value(self, path: tuple) -> ListNode:
        count = self.u32()
        items = []
        for index in range(count):
            item_path = path + ("item", index)
            type_id = self.u32()
            original_size = self.u32()
            start = self.pos
            payload = self.payload(type_id, item_path + ("value",), None)
            consumed = self.pos - start
            if consumed != original_size:
                raise ValueError(
                    f"EX list item size mismatch at {item_path!r}: {original_size} != {consumed}"
                )
            items.append(
                ListItemNode(
                    value=ValueNode(type_id, payload, item_path + ("value",)),
                    original_size=original_size,
                    path=item_path,
                )
            )
        return ListNode(items=items, path=path)

    def tree(self, path: tuple) -> TreeNode:
        name = self.string(path + ("name",))
        is_leaf = self.u32()
        if is_leaf not in (0, 1):
            raise ValueError(f"Invalid EX tree leaf flag {is_leaf} at {path!r}")
        if not is_leaf:
            count = self.u32()
            children = [self.tree(path + ("child", index)) for index in range(count)]
            return TreeNode(name, is_leaf, children, None, None, None, None, path)
        type_id = self.u32()
        original_size = self.u32()
        start = self.pos
        leaf_name = self.string(path + ("leaf_name",))
        payload = self.payload(type_id, path + ("leaf_value",), None)
        consumed = self.pos - start
        if consumed != original_size:
            raise ValueError(
                f"EX tree leaf size mismatch at {path!r}: {original_size} != {consumed}"
            )
        trailing_zero = self.u32()
        if trailing_zero != 0:
            raise ValueError(f"Non-zero EX tree trailer at {path!r}: {trailing_zero}")
        return TreeNode(
            name=name,
            is_leaf=is_leaf,
            children=[],
            leaf_name=leaf_name,
            leaf_value=ValueNode(type_id, payload, path + ("leaf_value",)),
            leaf_original_size=original_size,
            trailing_zero=trailing_zero,
            path=path,
        )

    def payload(
        self, type_id: int, path: tuple, table_fields: list[FieldNode] | None
    ) -> object:
        if type_id in (EX_INT, EX_FLOAT):
            return self.scalar(type_id, path)
        if type_id == EX_STRING:
            return self.string(path)
        if type_id == EX_TABLE:
            return self.table(path, table_fields)
        if type_id == EX_LIST:
            return self.list_value(path)
        if type_id == EX_TREE:
            return self.tree(path)
        raise ValueError(f"Invalid EX value type {type_id} at {path!r}")

    def value(
        self, path: tuple, table_fields: list[FieldNode] | None
    ) -> ValueNode:
        type_id = self.u32()
        return ValueNode(type_id, self.payload(type_id, path, table_fields), path)

    def block(self, index: int) -> BlockNode:
        path = ("block", index)
        type_id = self.u32()
        if type_id < EX_INT or type_id > EX_TREE:
            raise ValueError(f"Invalid EX block type {type_id} at index {index}")
        original_size = self.u32()
        start = self.pos
        name = self.string(path + ("name",))
        payload = self.payload(type_id, path + ("value",), None)
        consumed = self.pos - start
        if consumed != original_size:
            raise ValueError(
                f"EX block size mismatch at index {index}: {original_size} != {consumed}"
            )
        return BlockNode(type_id, name, payload, original_size, path)


@dataclasses.dataclass
class ParsedEx:
    header: bytes
    raw_payload: bytes
    blocks: list[BlockNode]
    strings: dict[tuple, StringNode]
    scalars: dict[tuple, ScalarNode]
    rows_first: bool | None
    compressed_size: int
    uncompressed_size: int

    def serialize_payload(self) -> bytes:
        return b"".join(block.serialize() for block in self.blocks)


def decode_ex(path: pathlib.Path) -> ParsedEx:
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError(f"EX file is too short: {path}")
    if data[:4] != b"HEAD" or data[8:12] != b"EXTF" or data[20:24] != b"DATA":
        raise ValueError(f"Invalid EX header: {path}")
    nr_blocks = struct.unpack_from("<I", data, 16)[0]
    compressed_size, uncompressed_size = struct.unpack_from("<II", data, 24)
    if len(data) != 32 + compressed_size:
        raise ValueError(
            f"EX compressed size mismatch: {len(data)} != {32 + compressed_size}"
        )
    decoded = bytes(EX_DECODE[value] for value in data[32:])
    raw = zlib.decompress(decoded)
    if len(raw) != uncompressed_size:
        raise ValueError(
            f"EX uncompressed size mismatch: {len(raw)} != {uncompressed_size}"
        )
    reader = Reader(raw)
    blocks = [reader.block(index) for index in range(nr_blocks)]
    if reader.pos != len(raw):
        raise ValueError(f"Unread EX payload bytes: {len(raw) - reader.pos}")
    return ParsedEx(
        header=data[:32],
        raw_payload=raw,
        blocks=blocks,
        strings=reader.strings,
        scalars=reader.scalars,
        rows_first=reader.rows_first,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
    )


def encode_ex(original_header: bytes, raw_payload: bytes) -> bytes:
    compressed = zlib.compress(raw_payload, level=9)
    encoded = bytes(EX_ENCODE[value] for value in compressed)
    header = bytearray(original_header)
    struct.pack_into("<II", header, 24, len(encoded), len(raw_payload))
    return bytes(header) + encoded


def path_text(path: tuple) -> str:
    return "/".join(str(part) for part in path)


def structure_signature(parsed: ParsedEx) -> dict:
    return {
        "block_count": len(parsed.blocks),
        "string_paths": [path_text(path) for path in parsed.strings],
        "scalar_types": {
            path_text(path): node.type_id for path, node in parsed.scalars.items()
        },
        "rows_first": parsed.rows_first,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Transplant changed string values from an alice-tools candidate into the "
            "original EX AST while preserving every original non-string semantic value."
        )
    )
    parser.add_argument("--original-ex", type=pathlib.Path, required=True)
    parser.add_argument("--translated-candidate-ex", type=pathlib.Path, required=True)
    parser.add_argument("--translation-manifest", type=pathlib.Path, required=True)
    parser.add_argument("--output-ex", type=pathlib.Path, required=True)
    parser.add_argument("--manifest-output", type=pathlib.Path, required=True)
    parser.add_argument("--expected-original-sha256", required=True)
    parser.add_argument("--expected-changes", type=int)
    parser.add_argument("--change-start", type=int, default=0)
    parser.add_argument("--change-count", type=int)
    parser.add_argument("--exclude-indices-json", type=pathlib.Path)
    args = parser.parse_args()

    if sha256_file(args.original_ex).lower() != args.expected_original_sha256.lower():
        raise ValueError("Original EX hash mismatch")

    source_manifest = json.loads(
        args.translation_manifest.read_text(encoding="utf-8-sig")
    )
    expected_changes = (
        args.expected_changes
        if args.expected_changes is not None
        else int(source_manifest["changed_entry_count"])
    )

    original = decode_ex(args.original_ex)
    candidate = decode_ex(args.translated_candidate_ex)

    # The parser/serializer must reproduce the original decompressed payload byte
    # for byte before any translation is allowed.
    nochange = original.serialize_payload()
    if nochange != original.raw_payload:
        first = next(
            index
            for index, pair in enumerate(zip(nochange, original.raw_payload))
            if pair[0] != pair[1]
        )
        raise ValueError(f"Original EX AST no-change roundtrip differs at 0x{first:x}")

    original_paths = set(original.strings)
    candidate_paths = set(candidate.strings)
    if original_paths != candidate_paths:
        missing_candidate = sorted(original_paths - candidate_paths, key=repr)
        missing_original = sorted(candidate_paths - original_paths, key=repr)
        raise ValueError(
            "EX string structure differs: "
            f"missing_candidate={missing_candidate[:5]!r}, "
            f"missing_original={missing_original[:5]!r}"
        )

    if set(original.scalars) != set(candidate.scalars):
        raise ValueError("EX scalar structure differs between original and candidate")

    candidate_changed_paths = []
    for path in sorted(original_paths, key=repr):
        before = original.strings[path].value
        after = candidate.strings[path].value
        if before != after:
            candidate_changed_paths.append(path)

    if len(candidate_changed_paths) != expected_changes:
        raise ValueError(
            "Candidate changed EX string count mismatch: "
            f"{len(candidate_changed_paths)} != {expected_changes}"
        )

    if args.change_start < 0 or args.change_start > len(candidate_changed_paths):
        raise ValueError(f"Invalid --change-start: {args.change_start}")
    change_end = (
        len(candidate_changed_paths)
        if args.change_count is None
        else args.change_start + args.change_count
    )
    if change_end < args.change_start or change_end > len(candidate_changed_paths):
        raise ValueError(
            f"Invalid change range: {args.change_start}:{change_end} / {len(candidate_changed_paths)}"
        )
    excluded_indices: set[int] = set()
    if args.exclude_indices_json:
        excluded_document = json.loads(
            args.exclude_indices_json.read_text(encoding="utf-8-sig")
        )
        rows = (
            excluded_document.get("excluded_indices", [])
            if isinstance(excluded_document, dict)
            else excluded_document
        )
        excluded_indices = {int(value) for value in rows}
        invalid = sorted(
            value
            for value in excluded_indices
            if value < 0 or value >= len(candidate_changed_paths)
        )
        if invalid:
            raise ValueError(f"Invalid excluded candidate indices: {invalid[:20]!r}")

    selected_indices = [
        index
        for index in range(args.change_start, change_end)
        if index not in excluded_indices
    ]
    changed_paths = [candidate_changed_paths[index] for index in selected_indices]
    for index, path in zip(selected_indices, changed_paths):
        del index
        original.strings[path].replacement = candidate.strings[path].value

    patched_raw = original.serialize_payload()
    output_data = encode_ex(original.header, patched_raw)
    atomic_write(args.output_ex, output_data)

    verified = decode_ex(args.output_ex)
    if structure_signature(verified) != structure_signature(original):
        raise ValueError("Patched EX structure differs from original")
    if {
        path: node.raw for path, node in verified.scalars.items()
    } != {path: node.raw for path, node in original.scalars.items()}:
        raise ValueError("Patched EX non-string scalar values differ from original")

    for path in original_paths:
        expected = (
            candidate.strings[path].value
            if original.strings[path].replacement is not None
            else original.strings[path].value
        )
        if verified.strings[path].value != expected:
            raise ValueError(f"Patched EX string verification failed at {path!r}")

    change_rows = []
    for candidate_index, path in zip(selected_indices, changed_paths):
        before = original.strings[path].value
        after = candidate.strings[path].value
        change_rows.append(
            {
                "candidate_index": candidate_index,
                "path": path_text(path),
                "source_size": len(before),
                "replacement_size": len(after),
                "source_sha256": sha256_bytes(before),
                "replacement_sha256": sha256_bytes(after),
            }
        )

    manifest = {
        "schema": "contextual-game-localization.ex-binary-preserving-string-patch.v1",
        "original": {
            "path": str(args.original_ex),
            "size": args.original_ex.stat().st_size,
            "sha256": sha256_file(args.original_ex),
            "compressed_size": original.compressed_size,
            "uncompressed_size": original.uncompressed_size,
        },
        "translated_candidate": {
            "path": str(args.translated_candidate_ex),
            "size": args.translated_candidate_ex.stat().st_size,
            "sha256": sha256_file(args.translated_candidate_ex),
        },
        "translation_manifest": {
            "path": str(args.translation_manifest),
            "sha256": sha256_file(args.translation_manifest),
            "expected_changed_entry_count": expected_changes,
        },
        "output": {
            "path": str(args.output_ex),
            "size": len(output_data),
            "sha256": sha256_bytes(output_data),
            "compressed_size": len(output_data) - 32,
            "uncompressed_size": len(patched_raw),
        },
        "verification": {
            "original_ast_nochange_roundtrip_byte_identical": True,
            "block_count": len(original.blocks),
            "string_node_count": len(original.strings),
            "candidate_changed_string_count": len(candidate_changed_paths),
            "changed_string_count": len(changed_paths),
            "change_range": [args.change_start, change_end],
            "excluded_candidate_indices": sorted(excluded_indices),
            "non_string_scalar_count": len(original.scalars),
            "non_string_scalars_preserved": True,
            "structure_preserved": True,
            "all_replacements_verified": True,
            "verdict": "pass",
        },
        "changes": change_rows,
    }
    atomic_json(args.manifest_output, manifest)
    print(
        json.dumps(
            {
                "output": str(args.output_ex),
                "sha256": sha256_bytes(output_data),
                "size": len(output_data),
                "changed_string_count": len(changed_paths),
                "non_string_scalar_count": len(original.scalars),
                "verdict": "pass",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
