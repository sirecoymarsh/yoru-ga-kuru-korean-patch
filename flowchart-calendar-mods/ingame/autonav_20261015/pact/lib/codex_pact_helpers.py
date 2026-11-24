"""Verbatim copies of Codex's PACT helper functions, gathered in one module.

Nothing here is new logic. Each block below is copied unchanged (apart from
whitespace and the import lines) from the Codex file named above it, so the
autonav build reuses exactly the tooling that made PACT 185:

  audit_dynamic_ui_20260915.py   (ui_cumulative/dynamic_ui_a5571abed07f/text_evidence)
      PROXY, MAPPING, DEC, ENC, decode, encode
  build_remaster_multiplier_20260915.py   (evidence/remaster_multiplier_20260915/source)
      cp, child, maybe, val, allparts, part, si, ss, setlist, rename, txt_info
  build_mod_tab_20260915.py   (evidence/mod_tab_20260915/source)
      name, scalar, coords, add, remove
  build_afa3_cumulative_20260912.py   (evidence/mod_tab_20260915/source)
      h, rebuild

The two binary modules are verbatim file copies in this folder:
  build_binary_preserving_ex_patch.py  (Codex game_localization/.../work, sha256 185be11e...)
  afa3_inplace.py                      (Codex game_localization/.../work, sha256 9576c69f...)
"""
from pathlib import Path
import copy, hashlib, json, struct, zlib, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_binary_preserving_ex_patch as ex  # noqa: E402
from afa3_inplace import (BitStream, BitWriter, Rnd521, read_afa3,  # noqa: E402
                          _read_layout, _read_dict, _patch_u32le_bits)

# ---- audit_dynamic_ui_20260915.py -------------------------------------------
PROXY = Path('P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830_hangul_name_v4/wansung_build/build_output/fnl_proxy_map_wansung2350.json')
MAPPING = json.loads(PROXY.read_text(encoding='utf-8'))['mapping']
DEC = {r['proxy_character']: r['unicode_character'] for r in MAPPING}
ENC = {r['unicode_character']: bytes.fromhex(r['proxy_sjis_hex']) for r in MAPPING}


def decode(b):
    return ''.join(DEC.get(c, c) for c in b.decode('cp932'))


def encode(t):
    return b''.join(ENC[c] if c in ENC else c.encode('cp932') for c in t)


# ---- build_remaster_multiplier_20260915.py ----------------------------------
def cp(s): return s.encode('cp932')
def child(t, k): return next(c for c in t.children if c.name.value.decode('cp932') == k)
def maybe(t, k): return next((c for c in t.children if c.name.value.decode('cp932') == k), None)
def val(t, k): return child(t, k).leaf_value.payload


def allparts(t):
    if maybe(t, '座標') is not None: yield t
    kids = maybe(t, '子パーツ')
    if kids:
        for c in kids.children: yield from allparts(c)


def part(doc, name): return next(t for t in allparts(doc.blocks[2].payload.children[0]) if t.name.value.decode('cp932') == name)


def si(t, k, x): n = val(t, k); assert isinstance(n, ex.ScalarNode); n.raw = struct.pack('<f' if n.type_id == 2 else '<i', x)
def ss(t, k, s, korean=False): val(t, k).replacement = encode(s) if korean else cp(s)


def setlist(t, k, vs):
    n = val(t, k); assert len(n.items) == len(vs)
    for i, v in zip(n.items, vs):
        p = i.value.payload
        if isinstance(p, ex.ScalarNode): p.raw = struct.pack('<f' if p.type_id == 2 else '<i', v)
        else: p.replacement = cp(v)


def rename(t, s): t.name.replacement = cp(s); ss(t, 'コメント', s)
def txt_info(t): return child(child(t, '種類別情報'), '通常状態')


# ---- build_mod_tab_20260915.py ----------------------------------------------
def name(t): return (t.name.replacement or t.name.value).decode('cp932')
def scalar(n): return struct.unpack('<f' if n.type_id == 2 else '<i', n.raw)[0]
def coords(t): return [scalar(i.value.payload) for i in val(t, '座標').items]


def add(parent, t):
    # Codex falls back to a module-level ORDER template only when the group is
    # empty; every group touched here already has children, so it is not needed.
    order = val(parent, '子パーツリスト'); assert order.items, 'empty group needs ORDER template'
    oi = copy.deepcopy(order.items[0])
    oi.value.payload.replacement = (t.name.replacement or t.name.value)
    child(parent, '子パーツ').children.append(t); order.items.append(oi)


def remove(parent, n):
    kids = child(parent, '子パーツ'); kids.children[:] = [t for t in kids.children if name(t) != n]
    order = val(parent, '子パーツリスト'); order.items[:] = [i for i in order.items if (i.value.payload.replacement or i.value.payload.value).decode('cp932') != n]


# ---- build_afa3_cumulative_20260912.py --------------------------------------
def h(b): return hashlib.sha256(b).hexdigest()


def rebuild(source, output, replacements=None, append=None):
    replacements = replacements or {}; append = append or []
    assert source.resolve() != output.resolve()
    data, ar, body, prefix_bits, metadata, positions = _read_layout(source)
    outer = BitStream(body); outer.read_bits(1); dictionary = _read_dict(outer)
    lookup = {v ^ 0xa4: i for i, v in reversed(list(enumerate(dictionary)))}
    assert max(lookup.values()) < 65536
    names = {e.name for e in ar.entries}; assert set(replacements) <= set(range(len(ar.entries)))
    for nm, payload in append:
        assert nm not in names; names.add(nm); assert all(c in lookup for c in nm.encode('cp932'))
    payloads = [Path(replacements[e.no]).read_bytes() if e.no in replacements else data[e.absolute_offset:e.absolute_offset + e.size] for e in ar.entries]
    cursor = 0
    for e, (offpos, sizepos), payload in zip(ar.entries, positions, payloads):
        _patch_u32le_bits(metadata, offpos, cursor); _patch_u32le_bits(metadata, sizepos, len(payload)); cursor += len(payload)
    _patch_u32le_bits(metadata, 1, len(ar.entries) + len(append))
    inner = BitWriter(); inner.copy_bits(metadata, 0, positions[-1][1] + 32)
    for nm, path in append:
        raw = nm.encode('cp932'); inner.write_bits(0, 2); inner.write_u32le(len(raw)); rnd = Rnd521(len(raw))
        for byte in raw:
            padding = (rnd.next() & 3) + 1; inner.write_bits(0, padding); rnd.next(); index = lookup[byte]
            inner.write_bits(index & 255, 8); inner.write_bits(index >> 8, 8)
        payload = Path(path).read_bytes()
        for value in [0, 0, cursor, len(payload)]: inner.write_u32le(value)
        cursor += len(payload); payloads.append(payload)
    rawmeta = inner.finish(); packed = zlib.compress(rawmeta, 9); writer = BitWriter(); writer.copy_bits(body, 0, prefix_bits)
    writer.write_u32le(len(packed)); writer.write_u32le(len(rawmeta)); writer.write_bytes(packed); outbody = writer.finish()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('wb') as f:
        f.write(b'AFAH' + struct.pack('<II', len(outbody) + 4, 3) + outbody)
        for payload in payloads: f.write(payload)
    reopened = read_afa3(output); newdata = output.read_bytes(); assert len(reopened.entries) == len(payloads)
    for e, new in zip(ar.entries, reopened.entries):
        for key in ['no', 'name', 'name_raw_hex', 'unknown0', 'unknown1']: assert getattr(e, key) == getattr(new, key), (e.no, key)
    for i, (e, payload) in enumerate(zip(reopened.entries, payloads)):
        assert newdata[e.absolute_offset:e.absolute_offset + e.size] == payload, (i, 'payload mismatch')
    for i, (nm, path) in enumerate(append, len(ar.entries)): assert reopened.entries[i].name == nm
    return dict(source_sha256=h(data), candidate_sha256=h(newdata), original_entries_preserved=len(ar.entries), replaced_ids=sorted(replacements), appended=[dict(id=len(ar.entries) + i, name=nm, sha256=h(Path(path).read_bytes())) for i, (nm, path) in enumerate(append)], wrapper='AFA3', metadata_identity='PASS (names/order/unknown fields)', payload_identity='PASS (all untouched entries and exact replacement bytes)', new_archive=str(output))
