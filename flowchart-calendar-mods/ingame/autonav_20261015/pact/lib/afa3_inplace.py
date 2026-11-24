#!/usr/bin/env python3
"""Read and safely patch AliceSoft AFA v3 archives without rebuilding the index.

The AFA3 index stores each entry's fixed data offset and capacity.  This tool
only permits a replacement that fits inside the original entry.  The remaining
bytes are zero-filled, so every index byte, file offset, and archive size stays
unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path


MASK32 = 0xFFFFFFFF


class Afa3Error(RuntimeError):
    pass


class Rnd521:
    def __init__(self, seed: int):
        self.state = [0] * 521
        val = 0
        seed &= MASK32
        for i in range(17):
            for _ in range(32):
                seed = (1566083941 * seed + 1) & MASK32
                val = ((seed & 0x80000000) | (val >> 1)) & MASK32
            self.state[i] = val
        self.state[16] = (
            self.state[15]
            ^ (self.state[0] >> 9)
            ^ ((self.state[16] << 23) & MASK32)
        ) & MASK32
        for i in range(17, 521):
            self.state[i] = (
                self.state[i - 1]
                ^ (self.state[i - 16] >> 9)
                ^ ((self.state[i - 17] << 23) & MASK32)
            ) & MASK32
        for _ in range(4):
            self.shuffle()
        self.current = -1

    def shuffle(self) -> None:
        for i in range(0, 32, 4):
            self.state[i] ^= self.state[i + 489]
            self.state[i + 1] ^= self.state[i + 490]
            self.state[i + 2] ^= self.state[i + 491]
            self.state[i + 3] ^= self.state[i + 492]
        for i in range(32, 521, 3):
            self.state[i] ^= self.state[i - 32]
            self.state[i + 1] ^= self.state[i - 31]
            self.state[i + 2] ^= self.state[i - 30]
        self.state = [x & MASK32 for x in self.state]

    def next(self) -> int:
        self.current += 1
        if self.current >= 521:
            self.shuffle()
            self.current = 0
        return self.state[self.current]


class BitStream:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.nr_cached = 0
        self.cache = 0

    def read_bits(self, count: int) -> int:
        if count < 0 or count > 32:
            raise Afa3Error(f"invalid bit count: {count}")
        while self.nr_cached < count:
            if self.pos >= len(self.data):
                raise Afa3Error("unexpected end of bitstream")
            self.cache = ((self.cache << 8) | self.data[self.pos]) & 0xFFFFFFFFFFFFFFFF
            self.pos += 1
            self.nr_cached += 8
        self.nr_cached -= count
        value = (self.cache >> self.nr_cached) & ((1 << count) - 1 if count else 0)
        # The C reader effectively discards consumed high bits.  Trimming here
        # also prevents unbounded Python integers while preserving cached bits.
        self.cache &= (1 << self.nr_cached) - 1 if self.nr_cached else 0
        return value

    def read_u32le(self) -> int:
        b0 = self.read_bits(8)
        b1 = self.read_bits(8)
        b2 = self.read_bits(8)
        b3 = self.read_bits(8)
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def tell_bits(self) -> int:
        return self.pos * 8 - self.nr_cached


class BitWriter:
    def __init__(self):
        self.data = bytearray()
        self.bit_count = 0

    def write_bit(self, value: int) -> None:
        if self.bit_count % 8 == 0:
            self.data.append(0)
        if value & 1:
            self.data[-1] |= 1 << (7 - (self.bit_count % 8))
        self.bit_count += 1

    def write_bits(self, value: int, count: int) -> None:
        for shift in range(count - 1, -1, -1):
            self.write_bit((value >> shift) & 1)

    def copy_bits(self, source: bytes, start: int, count: int) -> None:
        for pos in range(start, start + count):
            self.write_bit((source[pos // 8] >> (7 - (pos % 8))) & 1)

    def write_u32le(self, value: int) -> None:
        for b in struct.pack("<I", value):
            self.write_bits(b, 8)

    def write_bytes(self, value: bytes) -> None:
        for b in value:
            self.write_bits(b, 8)

    def finish(self) -> bytes:
        return bytes(self.data)


@dataclass(frozen=True)
class Afa3Entry:
    no: int
    name: str
    name_raw_hex: str
    unknown0: int
    unknown1: int
    offset: int
    size: int
    absolute_offset: int


@dataclass(frozen=True)
class Afa3Archive:
    path: str
    file_size: int
    index_size: int
    data_start: int
    packed_size: int
    unpacked_size: int
    entries: tuple[Afa3Entry, ...]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_dict(bs: BitStream) -> bytes:
    size = bs.read_u32le()
    if size > 1_000_000:
        raise Afa3Error(f"implausible dictionary size: {size}")
    rnd = Rnd521(size)
    out = bytearray(size)
    for dst in range(size):
        count = rnd.next() & 3
        bs.read_bits(count + 1)
        rnd.next()
        out[dst] = bs.read_bits(8)
    return bytes(out)


def _read_encrypted_chars(bs: BitStream) -> list[int]:
    size = bs.read_u32le()
    if size > 1_000_000:
        raise Afa3Error(f"implausible encrypted string size: {size}")
    rnd = Rnd521(size)
    out: list[int] = []
    for _ in range(size):
        count = rnd.next() & 3
        bs.read_bits(count + 1)
        rnd.next()
        lo = bs.read_bits(8)
        hi = bs.read_bits(8)
        out.append(lo | (hi << 8))
    return out


def _decrypt_name(chars: list[int], dictionary: bytes) -> tuple[str, bytes]:
    try:
        raw = bytes(dictionary[ch] ^ 0xA4 for ch in chars)
    except IndexError as exc:
        raise Afa3Error("encrypted filename references outside dictionary") from exc
    try:
        return raw.decode("cp932"), raw
    except UnicodeDecodeError:
        return raw.decode("cp932", errors="replace"), raw


def read_afa3(path: Path) -> Afa3Archive:
    data = path.read_bytes()
    if len(data) < 12 or data[:4] != b"AFAH":
        raise Afa3Error("not an AFA archive")
    index_size, version = struct.unpack_from("<II", data, 4)
    if version != 3:
        raise Afa3Error(f"expected AFA v3, got v{version}")
    data_start = index_size + 8
    if data_start > len(data):
        raise Afa3Error("data start is outside archive")

    bs = BitStream(data[12:data_start])
    bs.read_bits(1)
    dictionary = _read_dict(bs)
    packed_size = bs.read_u32le()
    unpacked_size = bs.read_u32le()
    packed = bytes(bs.read_bits(8) for _ in range(packed_size))
    try:
        unpacked = zlib.decompress(packed)
    except zlib.error as exc:
        raise Afa3Error(f"metadata zlib error: {exc}") from exc
    if len(unpacked) != unpacked_size:
        raise Afa3Error(
            f"metadata size mismatch: expected {unpacked_size}, got {len(unpacked)}"
        )

    ibs = BitStream(unpacked)
    ibs.read_bits(1)
    count = ibs.read_u32le()
    if count > 1_000_000:
        raise Afa3Error(f"implausible entry count: {count}")
    entries: list[Afa3Entry] = []
    for no in range(count):
        ibs.read_bits(2)
        chars = _read_encrypted_chars(ibs)
        name, raw = _decrypt_name(chars, dictionary)
        unknown0 = ibs.read_u32le()
        unknown1 = ibs.read_u32le()
        offset = ibs.read_u32le()
        size = ibs.read_u32le()
        absolute = data_start + offset
        if absolute < data_start or absolute + size > len(data):
            raise Afa3Error(
                f"entry {no} ({name!r}) is outside archive: {absolute}+{size}"
            )
        entries.append(
            Afa3Entry(
                no=no,
                name=name,
                name_raw_hex=raw.hex(),
                unknown0=unknown0,
                unknown1=unknown1,
                offset=offset,
                size=size,
                absolute_offset=absolute,
            )
        )
    return Afa3Archive(
        path=str(path),
        file_size=len(data),
        index_size=index_size,
        data_start=data_start,
        packed_size=packed_size,
        unpacked_size=unpacked_size,
        entries=tuple(entries),
    )


def select_entry(ar: Afa3Archive, selector: str) -> Afa3Entry:
    if selector.isdecimal():
        no = int(selector)
        if 0 <= no < len(ar.entries):
            return ar.entries[no]
    exact = [e for e in ar.entries if e.name == selector]
    if len(exact) == 1:
        return exact[0]
    folded = [e for e in ar.entries if e.name.casefold() == selector.casefold()]
    if len(folded) == 1:
        return folded[0]
    raise Afa3Error(f"entry selector did not match exactly once: {selector!r}")


def cmd_list(args: argparse.Namespace) -> None:
    path = Path(args.archive)
    ar = read_afa3(path)
    result = {
        "schema": "yorugakuru.afa3-index.v1",
        "status": "pass",
        "archive": str(path),
        "archive_sha256": sha256_file(path),
        "file_size": ar.file_size,
        "index_size": ar.index_size,
        "data_start": ar.data_start,
        "packed_size": ar.packed_size,
        "unpacked_size": ar.unpacked_size,
        "entry_count": len(ar.entries),
        "entries": [asdict(e) for e in ar.entries],
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(json.dumps(result, ensure_ascii=True, indent=2))


def cmd_extract(args: argparse.Namespace) -> None:
    path = Path(args.archive)
    ar = read_afa3(path)
    entry = select_entry(ar, args.entry)
    with path.open("rb") as f:
        f.seek(entry.absolute_offset)
        payload = f.read(entry.size)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    print(json.dumps({"entry": asdict(entry), "sha256": sha256_bytes(payload), "output": str(out)}, ensure_ascii=True, indent=2))


def cmd_patch(args: argparse.Namespace) -> None:
    src = Path(args.archive)
    out = Path(args.output)
    if src.resolve() == out.resolve():
        raise Afa3Error("refusing to patch the source archive in place")
    ar = read_afa3(src)
    replacements: list[tuple[Afa3Entry, Path, bytes]] = []
    seen: set[int] = set()
    for spec in args.replace:
        if "=" not in spec:
            raise Afa3Error("replacement must be ENTRY=FILE")
        selector, filename = spec.split("=", 1)
        entry = select_entry(ar, selector)
        if entry.no in seen:
            raise Afa3Error(f"duplicate replacement for entry {entry.no}")
        seen.add(entry.no)
        repl_path = Path(filename)
        payload = repl_path.read_bytes()
        if len(payload) > entry.size:
            raise Afa3Error(
                f"replacement too large for {entry.name!r}: {len(payload)} > {entry.size}"
            )
        replacements.append((entry, repl_path, payload))

    original = src.read_bytes()
    patched = bytearray(original)
    records = []
    allowed_ranges: list[tuple[int, int]] = []
    for entry, repl_path, payload in replacements:
        start = entry.absolute_offset
        end = start + entry.size
        before = original[start:end]
        padded = payload + bytes(entry.size - len(payload))
        patched[start:end] = padded
        allowed_ranges.append((start, end))
        records.append(
            {
                "entry": asdict(entry),
                "replacement": str(repl_path),
                "replacement_size": len(payload),
                "capacity": entry.size,
                "padding_size": entry.size - len(payload),
                "original_payload_sha256": sha256_bytes(before),
                "replacement_sha256": sha256_bytes(payload),
                "stored_region_sha256": sha256_bytes(padded),
            }
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(patched)

    # Strong invariant: every changed byte is inside a selected entry region.
    unexpected = []
    changed = 0
    for i, (a, b) in enumerate(zip(original, patched)):
        if a == b:
            continue
        changed += 1
        if not any(lo <= i < hi for lo, hi in allowed_ranges):
            unexpected.append(i)
            if len(unexpected) >= 20:
                break
    reread = read_afa3(out)
    index_equal = original[: ar.data_start] == patched[: ar.data_start]
    meta_equal = ar.entries == reread.entries
    size_equal = len(original) == len(patched)
    status = "pass" if index_equal and meta_equal and size_equal and not unexpected else "fail"
    manifest = {
        "schema": "yorugakuru.afa3-inplace-patch.v1",
        "status": status,
        "source": str(src),
        "source_sha256": sha256_bytes(original),
        "output": str(out),
        "output_sha256": sha256_bytes(patched),
        "file_size": len(patched),
        "data_start": ar.data_start,
        "entry_count": len(ar.entries),
        "replacement_count": len(records),
        "changed_byte_count": changed,
        "index_byte_identical": index_equal,
        "metadata_identical": meta_equal,
        "file_size_identical": size_equal,
        "unexpected_changed_offsets": unexpected,
        "replacements": records,
    }
    manifest_path = Path(args.manifest) if args.manifest else out.with_suffix(out.suffix + ".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=True, indent=2))
    if status != "pass":
        raise Afa3Error("post-patch invariants failed")


def _set_bit(buf: bytearray, pos: int, value: int) -> None:
    mask = 1 << (7 - (pos % 8))
    if value:
        buf[pos // 8] |= mask
    else:
        buf[pos // 8] &= ~mask


def _patch_u32le_bits(buf: bytearray, pos: int, value: int) -> None:
    raw = struct.pack("<I", value)
    for i, b in enumerate(raw):
        for j in range(8):
            _set_bit(buf, pos + i * 8 + j, (b >> (7 - j)) & 1)


def _read_layout(path: Path):
    """Return parsed archive plus raw metadata and patchable bit positions."""
    data = path.read_bytes()
    ar = read_afa3(path)
    body = data[12 : ar.data_start]
    outer = BitStream(body)
    outer.read_bits(1)
    dictionary = _read_dict(outer)
    prefix_bits = outer.tell_bits()
    packed_size = outer.read_u32le()
    unpacked_size = outer.read_u32le()
    packed = bytes(outer.read_bits(8) for _ in range(packed_size))
    unpacked = zlib.decompress(packed)
    if len(unpacked) != unpacked_size:
        raise Afa3Error("unpacked metadata length mismatch")

    inner = BitStream(unpacked)
    inner.read_bits(1)
    count = inner.read_u32le()
    if count != len(ar.entries):
        raise Afa3Error("layout entry count mismatch")
    positions = []
    for no in range(count):
        inner.read_bits(2)
        chars = _read_encrypted_chars(inner)
        _decrypt_name(chars, dictionary)
        inner.read_u32le()  # unknown0
        inner.read_u32le()  # unknown1
        offset_pos = inner.tell_bits()
        old_offset = inner.read_u32le()
        size_pos = inner.tell_bits()
        old_size = inner.read_u32le()
        entry = ar.entries[no]
        if old_offset != entry.offset or old_size != entry.size:
            raise Afa3Error(f"layout position mismatch at entry {no}")
        positions.append((offset_pos, size_pos))
    return data, ar, body, prefix_bits, bytearray(unpacked), positions


def _load_manifest_replacements(path: Path) -> dict[int, Path]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    records = doc.get("records")
    if not isinstance(records, list):
        raise Afa3Error("replacement manifest has no records array")
    out: dict[int, Path] = {}
    for rec in records:
        if "entry_no" not in rec or "payload" not in rec:
            continue
        no = int(rec["entry_no"])
        payload = Path(rec["payload"])
        if not payload.is_absolute():
            # Builder manifests use paths relative to the current worktree.
            payload = Path.cwd() / payload
        if no in out:
            raise Afa3Error(f"duplicate replacement entry: {no}")
        if not payload.exists():
            raise Afa3Error(f"replacement payload missing: {payload}")
        out[no] = payload
    if not out:
        raise Afa3Error("replacement manifest selected zero payloads")
    return out


def cmd_rebuild(args: argparse.Namespace) -> None:
    src = Path(args.archive)
    out = Path(args.output)
    if src.resolve() == out.resolve():
        raise Afa3Error("refusing to overwrite the source archive")
    replacements = _load_manifest_replacements(Path(args.replacements_manifest))
    source, ar, body, prefix_bits, metadata, positions = _read_layout(src)
    if any(no < 0 or no >= len(ar.entries) for no in replacements):
        raise Afa3Error("replacement entry number outside archive")

    new_sizes = []
    payload_hashes: dict[int, str] = {}
    replacement_records = []
    for entry in ar.entries:
        if entry.no in replacements:
            payload = replacements[entry.no].read_bytes()
            new_sizes.append(len(payload))
            payload_hashes[entry.no] = sha256_bytes(payload)
            replacement_records.append({
                "entry_no": entry.no,
                "archive_name": entry.name,
                "source_size": entry.size,
                "replacement_size": len(payload),
                "replacement": str(replacements[entry.no]),
                "replacement_sha256": payload_hashes[entry.no],
            })
        else:
            new_sizes.append(entry.size)

    new_offsets = []
    cursor = 0
    for size in new_sizes:
        new_offsets.append(cursor)
        cursor += size
    for no, (offset_pos, size_pos) in enumerate(positions):
        _patch_u32le_bits(metadata, offset_pos, new_offsets[no])
        _patch_u32le_bits(metadata, size_pos, new_sizes[no])

    packed = zlib.compress(bytes(metadata), level=9)
    writer = BitWriter()
    writer.copy_bits(body, 0, prefix_bits)
    writer.write_u32le(len(packed))
    writer.write_u32le(len(metadata))
    writer.write_bytes(packed)
    new_body = writer.finish()
    new_index_size = 4 + len(new_body)
    new_data_start = new_index_size + 8
    header = b"AFAH" + struct.pack("<II", new_index_size, 3) + new_body
    if len(header) != new_data_start:
        raise Afa3Error("rebuilt index length invariant failed")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as dst, src.open("rb") as sf:
        dst.write(header)
        for entry in ar.entries:
            if entry.no in replacements:
                with replacements[entry.no].open("rb") as rf:
                    shutil_copyfileobj(rf, dst)
            else:
                sf.seek(entry.absolute_offset)
                remaining = entry.size
                while remaining:
                    chunk = sf.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise Afa3Error(f"unexpected EOF while copying entry {entry.no}")
                    dst.write(chunk)
                    remaining -= len(chunk)

    reread = read_afa3(out)
    structural_mismatches = []
    for old, new in zip(ar.entries, reread.entries):
        if (
            old.no != new.no
            or old.name != new.name
            or old.name_raw_hex != new.name_raw_hex
            or old.unknown0 != new.unknown0
            or old.unknown1 != new.unknown1
            or new.offset != new_offsets[old.no]
            or new.size != new_sizes[old.no]
        ):
            structural_mismatches.append(old.no)
            if len(structural_mismatches) >= 20:
                break

    # Verify every payload.  For untouched entries, the strong criterion is an
    # exact byte hash match; for replacements, it must equal the supplied file.
    payload_mismatches = []
    untouched_verified = 0
    replaced_verified = 0
    with src.open("rb") as sf, out.open("rb") as of:
        for old, new in zip(ar.entries, reread.entries):
            of.seek(new.absolute_offset)
            new_payload = of.read(new.size)
            if old.no in replacements:
                expected_hash = payload_hashes[old.no]
                replaced_verified += 1
            else:
                sf.seek(old.absolute_offset)
                expected_hash = sha256_bytes(sf.read(old.size))
                untouched_verified += 1
            if sha256_bytes(new_payload) != expected_hash:
                payload_mismatches.append(old.no)
                if len(payload_mismatches) >= 20:
                    break

    expected_size = new_data_start + sum(new_sizes)
    actual_size = out.stat().st_size
    status = "pass" if (
        len(reread.entries) == len(ar.entries)
        and not structural_mismatches
        and not payload_mismatches
        and actual_size == expected_size
        and replaced_verified == len(replacements)
        and untouched_verified == len(ar.entries) - len(replacements)
    ) else "fail"
    manifest = {
        "schema": "yorugakuru.afa3-rebuild.v1",
        "status": status,
        "source": str(src),
        "source_sha256": sha256_file(src),
        "source_size": len(source),
        "source_data_start": ar.data_start,
        "output": str(out),
        "output_sha256": sha256_file(out),
        "output_size": actual_size,
        "expected_output_size": expected_size,
        "output_data_start": reread.data_start,
        "entry_count": len(ar.entries),
        "replacement_count": len(replacements),
        "untouched_payloads_verified": untouched_verified,
        "replacement_payloads_verified": replaced_verified,
        "structural_mismatches": structural_mismatches,
        "payload_mismatches": payload_mismatches,
        "replacement_records": replacement_records,
    }
    manifest_path = Path(args.manifest) if args.manifest else out.with_suffix(out.suffix + ".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("status", "output_sha256", "output_size", "output_data_start", "entry_count", "replacement_count", "untouched_payloads_verified", "replacement_payloads_verified", "structural_mismatches", "payload_mismatches")}, ensure_ascii=True, indent=2))
    if status != "pass":
        raise Afa3Error("rebuilt archive validation failed")


def shutil_copyfileobj(src, dst, length: int = 1024 * 1024) -> None:
    while True:
        buf = src.read(length)
        if not buf:
            return
        dst.write(buf)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("archive")
    lp.add_argument("--output")
    lp.set_defaults(func=cmd_list)
    ep = sub.add_parser("extract")
    ep.add_argument("archive")
    ep.add_argument("entry")
    ep.add_argument("output")
    ep.set_defaults(func=cmd_extract)
    pp = sub.add_parser("patch")
    pp.add_argument("archive")
    pp.add_argument("output")
    pp.add_argument("--replace", action="append", required=True, metavar="ENTRY=FILE")
    pp.add_argument("--manifest")
    pp.set_defaults(func=cmd_patch)
    rp = sub.add_parser("rebuild")
    rp.add_argument("archive")
    rp.add_argument("output")
    rp.add_argument("--replacements-manifest", required=True)
    rp.add_argument("--manifest")
    rp.set_defaults(func=cmd_rebuild)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
