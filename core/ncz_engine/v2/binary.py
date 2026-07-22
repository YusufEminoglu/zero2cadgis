# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounds-checked binary reading primitives for NCZ Engine v2.

Every read is clamped to the underlying buffer and returns a neutral
default instead of raising, so decoders never need per-field guards.
"""
from __future__ import annotations

import math
import struct

# Netcad OEM byte values for Turkish characters (see docs/NCZ_FORMAT.md).
_OEM_TURKISH = {221: "I", 222: "S", 208: "G", 240: "g", 253: "i", 254: "s"}

_F32 = struct.Struct("<f")
_F64 = struct.Struct("<d")

COORDINATE_LIMIT = 100000000.0


def decode_oem_text(raw: bytes) -> str:
    """Decode NUL-padded OEM bytes to text with Turkish substitutions."""
    return "".join(
        _OEM_TURKISH.get(value, chr(value)) for value in raw).rstrip("\0")


def finite_pair_in_range(x: float, y: float) -> bool:
    return (math.isfinite(x) and math.isfinite(y)
            and abs(x) <= COORDINATE_LIMIT and abs(y) <= COORDINATE_LIMIT)


class Cursor:
    """Random-access reader over an immutable byte buffer.

    All accessors take absolute offsets and never read past the buffer;
    out-of-range reads yield 0 / 0.0 / empty string.
    """

    __slots__ = ("data", "size")

    def __init__(self, data: bytes):
        self.data = data
        self.size = len(data)

    def u8(self, offset: int) -> int:
        if 0 <= offset < self.size:
            return self.data[offset]
        return 0

    def u16(self, offset: int) -> int:
        if 0 <= offset and offset + 2 <= self.size:
            return int.from_bytes(self.data[offset:offset + 2], "little")
        return 0

    def u32(self, offset: int) -> int:
        if 0 <= offset and offset + 4 <= self.size:
            return int.from_bytes(self.data[offset:offset + 4], "little")
        return 0

    def f32(self, offset: int) -> float:
        if 0 <= offset and offset + 4 <= self.size:
            return _F32.unpack_from(self.data, offset)[0]
        return 0.0

    def f64(self, offset: int) -> float:
        if 0 <= offset and offset + 8 <= self.size:
            return _F64.unpack_from(self.data, offset)[0]
        return 0.0

    def raw(self, offset: int, length: int) -> bytes:
        if length <= 0 or offset >= self.size or offset < 0:
            return b""
        return self.data[offset:min(offset + length, self.size)]

    def text(self, offset: int, length: int) -> str:
        return decode_oem_text(self.raw(offset, length))

    def length_prefixed_text(self, length_offset: int,
                             text_offset: int,
                             max_length: int = 240) -> str:
        """Text whose 1-byte length lives at *length_offset*."""
        if not (0 <= length_offset < self.size
                and 0 <= text_offset < self.size):
            return ""
        text_length = self.data[length_offset]
        if text_length <= 0 or text_length > max_length \
                or text_offset + text_length > self.size:
            return ""
        return self.text(text_offset, text_length).strip("\0 ")

    def positive_f32(self, offset: int,
                     upper: float = 100000.0) -> float | None:
        """A finite strictly-positive f32 within (0, upper], else None."""
        if offset < 0 or offset + 4 > self.size:
            return None
        value = self.f32(offset)
        if not math.isfinite(value) or value <= 0.0 or value > upper:
            return None
        return float(value)

    def find(self, needle: bytes, start: int = 0) -> int:
        return self.data.find(needle, start)
