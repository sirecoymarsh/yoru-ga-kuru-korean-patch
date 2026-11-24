from __future__ import annotations

import argparse
import pathlib
import struct
import zlib

from PIL import Image, ImageDraw


def sjis_to_index(encoded: bytes) -> int:
    if len(encoded) == 1:
        value = encoded[0]
        if 0x20 <= value < 0x7F:
            return value - 0x20
        if 0xA1 <= value < 0xE0:
            return value - 0x42
        raise ValueError(f"Unsupported single-byte Shift-JIS code: {encoded.hex()}")
    if len(encoded) != 2:
        raise ValueError(f"Unsupported Shift-JIS code: {encoded.hex()}")
    first, second = encoded
    if 0x81 <= first < 0xA0:
        first_index = first - 0x81
    elif 0xE0 <= first < 0xFD:
        first_index = first - 0xE0 + 31
    else:
        raise ValueError(f"Invalid Shift-JIS lead byte: {first:#x}")
    if not (0x40 <= second <= 0xFC) or second == 0x7F:
        raise ValueError(f"Invalid Shift-JIS trail byte: {second:#x}")
    second_index = second - 0x40 - (1 if second > 0x7F else 0)
    return 158 + first_index * 188 + second_index


def parse_faces(data: bytes):
    magic, unknown, declared_size, index_size = struct.unpack_from("<4sIII", data, 0)
    if magic != b"FNA\x00":
        raise ValueError("Not an FNL file")
    offset = 16
    font_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    fonts = []
    for font_index in range(font_count):
        face_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        faces = []
        for face_index in range(face_count):
            height, face_unknown, glyph_count = struct.unpack_from("<III", data, offset)
            offset += 12
            glyphs = []
            for glyph_index in range(glyph_count):
                width, data_pos, compressed_size = struct.unpack_from("<HII", data, offset)
                offset += 10
                glyphs.append((width, data_pos, compressed_size))
            faces.append(
                {
                    "font_index": font_index,
                    "face_index": face_index,
                    "height": height,
                    "unknown": face_unknown,
                    "glyphs": glyphs,
                }
            )
        fonts.append(faces)
    if offset != 16 + index_size:
        raise ValueError(f"Index parse mismatch: {offset} != {16 + index_size}")
    return fonts


def glyph_image(data: bytes, face, glyph_index: int) -> Image.Image:
    width, data_pos, compressed_size = face["glyphs"][glyph_index]
    stride = (width + 31) // 32 * 4
    height = face["height"]
    raw = zlib.decompress(data[data_pos : data_pos + compressed_size])
    expected = stride * height
    if len(raw) > expected:
        raise ValueError("Decompressed glyph data is larger than its canvas")
    raw += b"\x00" * (expected - len(raw))
    image = Image.new("1", (stride * 8, height), 0)
    pixels = image.load()
    for stored_row in range(height):
        display_y = height - 1 - stored_row
        row_offset = stored_row * stride
        for x in range(width):
            byte = raw[row_offset + x // 8]
            pixels[x, display_y] = 255 if byte & (1 << (7 - x % 8)) else 0
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--characters", default="Aaあ国月")
    parser.add_argument("--face-index", default=0, type=int)
    args = parser.parse_args()

    data = args.input.read_bytes()
    fonts = parse_faces(data)
    indices = [(char, sjis_to_index(char.encode("cp932"))) for char in args.characters]

    rendered = []
    max_width = 0
    max_height = 0
    for font_index, faces in enumerate(fonts):
        if args.face_index >= len(faces):
            continue
        face = faces[args.face_index]
        for char, glyph_index in indices:
            image = glyph_image(data, face, glyph_index)
            rendered.append((font_index, face, char, glyph_index, image))
            max_width = max(max_width, image.width)
            max_height = max(max_height, image.height)

    label_height = 30
    cell_width = max_width + 24
    cell_height = max_height + label_height + 24
    sheet = Image.new("RGB", (cell_width * len(indices), cell_height * len(fonts)), "white")
    draw = ImageDraw.Draw(sheet)
    for font_index, face, char, glyph_index, image in rendered:
        col = [value[0] for value in indices].index(char)
        x = col * cell_width + 12
        y = font_index * cell_height + label_height + 12
        sheet.paste(image.convert("RGB"), (x, y))
        width = face["glyphs"][glyph_index][0]
        draw.text(
            (col * cell_width + 4, font_index * cell_height + 4),
            f"font{font_index} h{face['height']} {char} i{glyph_index} w{width}",
            fill="black",
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
