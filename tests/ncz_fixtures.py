# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Synthetic NCZ block builders for engine parity and regression tests.

These helpers construct in-memory NCZ byte streams from first principles
using the layout documented in ``docs/NCZ_FORMAT.md``. They are not real
Netcad drawings; their purpose is to exercise every decoder path with
deterministic bytes so the v1 and v2 engines can be compared field by
field, and so decoders keep bounds-checking short/odd blocks.

Coordinates are stored northing-first (see the format notes): the value
at record offset 8 becomes the decoded *y*, and the value at offset 16
becomes the decoded *x*.
"""
from __future__ import annotations

import struct

# A projected coordinate that passes validity checks (|v| <= 1e8, and
# >= 1e3 for attribute segment rows).
BASE_X = 500000.0
BASE_Y = 4500000.0


def block(kind: int, body: bytes) -> bytes:
    """Wrap *body* (bytes from absolute offset 5 onward) as one block."""
    return bytes([kind]) + len(body).to_bytes(4, "little") + bytes(body)


def _body(size: int) -> bytearray:
    return bytearray(size)


def _put_f64(body: bytearray, abs_offset: int, value: float) -> None:
    struct.pack_into("<d", body, abs_offset - 5, value)


def _put_f32(body: bytearray, abs_offset: int, value: float) -> None:
    struct.pack_into("<f", body, abs_offset - 5, value)


def _put_u8(body: bytearray, abs_offset: int, value: int) -> None:
    body[abs_offset - 5] = value & 0xFF


def _put_u16(body: bytearray, abs_offset: int, value: int) -> None:
    struct.pack_into("<H", body, abs_offset - 5, value)


def _put_text(body: bytearray, length_offset: int, value: bytes) -> None:
    """Write a length-prefixed ASCII string (length at *length_offset*)."""
    body[length_offset - 5] = len(value)
    body[length_offset - 4:length_offset - 4 + len(value)] = value


# ── geometry records (block kind 21, shift 0) ───────────────────────

def point_block(layer: int = 0, x: float = BASE_X, y: float = BASE_Y,
                name: bytes = b"PT1", color: int = 0) -> bytes:
    body = _body(128)
    _put_u8(body, 6, 1)          # geometry type
    _put_u8(body, 7, layer)
    _put_f64(body, 8, y)         # stored northing -> decoded y
    _put_f64(body, 16, x)        # stored easting  -> decoded x
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    _put_text(body, 86, name)    # name length at 86, text at 87
    return block(21, body)


def line_block(layer: int = 1, color: int = 0) -> bytes:
    body = _body(64)
    _put_u8(body, 6, 2)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    size = len(body) + 4  # container size convention
    tail = size
    _put_f64(body, tail - 19, BASE_Y + 100.0)
    _put_f64(body, tail - 11, BASE_X + 100.0)
    _put_f32(body, tail - 3, 0.0)
    return block(21, body)


def text_block(layer: int = 2, text: bytes = b"LABEL",
               height: float = 2.5, color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 5)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    # text payload: length at 97, text at 98 (primary path)
    _put_text(body, 97, text)
    _put_f32(body, 86, height)   # height at offset 86
    _put_f32(body, 90, 0.0)      # rotation radians
    return block(21, body)


def polyline_block(layer: int = 1, closed: bool = False,
                   color: int = 0) -> bytes:
    if closed:
        rings = [(0.0, 0.0), (0.0, 50.0), (50.0, 50.0), (50.0, 0.0),
                 (0.0, 0.0)]
    else:
        rings = [(0.0, 0.0), (25.0, 10.0), (50.0, 40.0)]
    count = len(rings)
    # vertices start at offset 113 (shift 0), 24 bytes each
    size = 113 + count * 24
    body = _body(size - 4)  # body length so container size == size
    _put_u8(body, 6, 7)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_u8(body, 37, color)
    _put_text(body, 86, b"PL")
    for index, (dx, dy) in enumerate(rings):
        vertex = 113 + index * 24
        _put_f64(body, vertex, BASE_X + dx)      # stored[0]
        _put_f64(body, vertex + 8, BASE_Y + dy)  # stored[1]
        _put_f64(body, vertex + 16, 0.0)
    return block(21, body)


def circle_block(layer: int = 3, color: int = 0) -> bytes:
    body = _body(96)
    _put_u8(body, 6, 3)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    _put_f64(body, 50, 10.0)   # diameter endpoints -> radius (|10-0|/2 = 5)
    _put_f64(body, 66, 0.0)
    return block(21, body)


def arc_block(layer: int = 3, color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 4)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    _put_f64(body, 86, 12.0)    # radius
    _put_f64(body, 104, 0.0)    # start angle
    _put_f64(body, 112, 1.5)    # end angle
    return block(21, body)


def triangle_block(layer: int = 4, color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 12)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)          # A first
    _put_f64(body, 16, BASE_X)         # A second
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    _put_f64(body, 86, BASE_Y + 50.0)  # B
    _put_f64(body, 94, BASE_X)
    _put_f64(body, 106, BASE_Y)        # C
    _put_f64(body, 114, BASE_X + 50.0)
    return block(21, body)


def symbol_block(layer: int = 4, code: int = 7, size: float = 3.0,
                 color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 6)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    _put_f32(body, 86, size)     # size at 86
    _put_f32(body, 90, 0.0)      # rotation
    _put_u8(body, 94, code)      # symbol code at 94
    return block(21, body)


def box_block(layer: int = 1, color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 10)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)          # corner 1
    _put_f64(body, 16, BASE_X)
    _put_u8(body, 37, color)
    _put_f64(body, 104, BASE_Y + 40.0)  # corner 2 (shift 0)
    _put_f64(body, 112, BASE_X + 60.0)
    _put_f32(body, 120, 0.5)            # rotation radians
    return block(21, body)


def map_sheet_block(layer: int = 4, color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 11)
    _put_u8(body, 7, layer)
    _put_u8(body, 37, color)
    _put_f64(body, 50, BASE_Y)          # corner 1
    _put_f64(body, 58, BASE_X)
    _put_f64(body, 66, BASE_Y + 100.0)  # corner 2
    _put_f64(body, 74, BASE_X + 100.0)
    _put_text(body, 86, b"SHEET-A4")
    return block(21, body)


def block_reference_block(layer: int = 4, color: int = 0) -> bytes:
    body = _body(160)
    _put_u8(body, 6, 13)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, color)
    _put_text(body, 86, b"BLOCKREF")
    _put_f32(body, 118, 0.0)
    return block(21, body)


def smart_object_block(layer: int = 1, color: int = 0) -> bytes:
    body = _body(224)
    _put_u8(body, 6, 15)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_u8(body, 37, color)
    _put_f32(body, 82, 0.0)     # angle grads
    _put_f32(body, 86, 1.0)     # scale
    _put_f64(body, 169, 30.0)   # width
    _put_f64(body, 177, 20.0)   # height
    _put_f64(body, 185, 1.0)    # grid_x
    _put_f64(body, 193, 1.0)    # grid_y
    body[145 - 5:145 - 5 + 5] = b"BASIC"
    return block(21, body)


def compressed_curve_block(layer: int = 1, color: int = 0) -> bytes:
    deltas = [(0.0, 0.0), (5.0, 5.0), (10.0, 0.0), (15.0, 8.0)]
    size = 122 + len(deltas) * 18 + 8
    body = _body(size - 4)
    _put_u8(body, 6, 9)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)   # origin first
    _put_f64(body, 16, BASE_X)  # origin second
    _put_u8(body, 37, color)
    for index, (dx, dy) in enumerate(deltas):
        record = 122 + index * 18
        _put_f32(body, record, dx)
        _put_f32(body, record + 4, dy)
    return block(21, body)


def gis_point_block(layer: int = 0, name: bytes = b"GISPT") -> bytes:
    """A kind-22 point record: geometry fields shifted by +28 bytes."""
    body = _body(160)
    _put_u8(body, 6, 1)
    _put_u8(body, 7, layer)
    _put_f64(body, 8, BASE_Y)
    _put_f64(body, 16, BASE_X)
    _put_f32(body, 24, 0.0)
    _put_u8(body, 37, 0)
    _put_text(body, 28 + 86, name)   # name at shift(28)+86
    return block(22, body)


def embedded_container_block() -> bytes:
    """A container block (kind 0) wrapping one nested kind-21 point.

    The nested record's bytes at offset 5 and 6 are made equal to satisfy
    the length-echo heuristic both engines use to detect embedded records.
    """
    inner = bytearray(point_block(layer=2, name=b"NESTED"))
    inner[5] = inner[6]  # length-echo: record byte 5 == byte 6
    body = bytearray(5 + len(inner) + 8)
    body[5:5 + len(inner)] = inner
    return block(0, bytes(body))


# ── metadata blocks ─────────────────────────────────────────────────

def version_block(version: bytes = b"NCZ-TEST-1.0") -> bytes:
    body = _body(2 + len(version))
    _put_text(body, 5, version)   # length at 5, text at 6
    return block(25, body)


def layer_table_block(names: list[bytes]) -> bytes:
    size = 18 + len(names) * 29 + 8
    body = _body(size)
    _put_u16(body, 16, len(names))
    for index, name in enumerate(names):
        item = 18 + index * 29
        _put_text(body, item + 4, name)  # length at item+4, text at item+5
    return block(6, body)


def color_table_block(colors: list[tuple[int, int, int]]) -> bytes:
    size = 23 + len(colors) * 256 + 64
    body = _body(size)
    _put_text(body, 5, b"LEX.ST2")
    _put_u8(body, 20, len(colors))
    for index, (red, green, blue) in enumerate(colors):
        item = 23 + index * 256 + 56
        _put_u8(body, item, red)
        _put_u8(body, item + 1, green)
        _put_u8(body, item + 2, blue)
    return block(28, body)


def projection_block(projection_code: int = 2, datum_code: int = 0,
                     zone: int = 35) -> bytes:
    body = _body(32)
    _put_text(body, 5, b"MPROJ")
    _put_u8(body, 16, projection_code)
    _put_u8(body, 17, datum_code)
    _put_u8(body, 21, zone)
    return block(28, body)


def epsg_block(epsg: bytes = b"EPSG:5254") -> bytes:
    marker = b'SRS:"' + epsg + b'">'
    body = bytearray(64)
    _put_text(body, 5, b"TILED_XML")
    body[24:24 + len(marker)] = marker
    return block(28, body)


def attribute_table_block(table_ref: bytes = b"@TAB1",
                          label: bytes = b"PARCEL-42") -> bytes:
    """A label-variant attribute record with a leading length byte."""
    body = bytearray(160)
    body[0] = len(table_ref)          # length echo before marker
    body[1:1 + len(table_ref)] = table_ref
    # label length at record offset 28, text at 29
    body[28] = len(label)
    body[29:29 + len(label)] = label
    return bytes(body)


# ── composite corpus ────────────────────────────────────────────────

def full_drawing() -> bytes:
    """A single NCZ stream exercising metadata and every decoder path."""
    return b"".join([
        version_block(),
        layer_table_block([b"ROADS", b"PARCELS", b"TEXT", b"TRIANGLES",
                           b"MISC"]),
        color_table_block([(255, 0, 0), (0, 128, 0), (0, 0, 255),
                           (200, 200, 0), (10, 10, 10)]),
        projection_block(),
        epsg_block(),
        point_block(layer=0),
        line_block(layer=1),
        text_block(layer=2),
        polyline_block(layer=1, closed=False),
        polyline_block(layer=1, closed=True),
        circle_block(layer=3),
        arc_block(layer=3),
        triangle_block(layer=4),
        symbol_block(layer=4),
        box_block(layer=1),
        map_sheet_block(layer=4),
        block_reference_block(layer=4),
        compressed_curve_block(layer=1),
        gis_point_block(layer=0),
        embedded_container_block(),
        attribute_table_block(),
    ])


ALL_GEOMETRY_BUILDERS = [
    point_block, line_block, text_block, circle_block, arc_block,
    triangle_block, symbol_block, box_block, map_sheet_block,
    block_reference_block, compressed_curve_block, smart_object_block,
    gis_point_block, embedded_container_block,
    lambda: polyline_block(closed=False),
    lambda: polyline_block(closed=True),
]
