# -*- coding: utf-8 -*-
"""Unit tests for DGN v8 pure-Python reader and DGN conversion logic."""
import math
import struct
import unittest
from unittest.mock import MagicMock, patch

from zero2cadgis.core.dgn_v8_reader import DgnElement, DgnV8Reader, ElementType


class TestDgnV8Reader(unittest.TestCase):
    """Test binary decoding logic in DgnV8Reader."""

    def test_decode_points_2d(self):
        # Pack two 2D points: (10.0, 20.0), (30.0, 40.0)
        data = struct.pack("<dddd", 10.0, 20.0, 30.0, 40.0)
        pts = DgnV8Reader._decode_points(data, 0, len(data), is_3d=False)
        self.assertEqual(len(pts), 2)
        self.assertEqual(pts[0], (10.0, 20.0))
        self.assertEqual(pts[1], (30.0, 40.0))

    def test_decode_points_3d(self):
        # Pack two 3D points: (10.0, 20.0, 5.0), (30.0, 40.0, 15.0)
        data = struct.pack("<dddddd", 10.0, 20.0, 5.0, 30.0, 40.0, 15.0)
        pts = DgnV8Reader._decode_points(data, 0, len(data), is_3d=True)
        self.assertEqual(len(pts), 2)
        self.assertEqual(pts[0], (10.0, 20.0))
        self.assertEqual(pts[1], (30.0, 40.0))

    def test_decode_points_handles_nan_and_giant_values(self):
        # Pack point with nan and giant value
        data = struct.pack("<dddd", float("nan"), 20.0, 1e18, 40.0)
        pts = DgnV8Reader._decode_points(data, 0, len(data), is_3d=False)
        self.assertEqual(len(pts), 0)

    def test_read_level_decodes_various_offsets(self):
        data = bytearray(0x40)
        struct.pack_into("<I", data, 0x2C, 42)
        self.assertEqual(DgnV8Reader._read_level(bytes(data), 0), 42)

    def test_read_color_decodes_rgba_fields(self):
        data = bytearray(0x40)
        # cg = color | (weight << 8) | (style << 16)
        cg = 5 | (2 << 8) | (3 << 16)
        struct.pack_into("<I", data, 0x30, cg)
        c, w, s = DgnV8Reader._read_color(bytes(data), 0)
        self.assertEqual(c, 5)
        self.assertEqual(w, 2)
        self.assertEqual(s, 3)

    def test_parse_stream_yields_dgn_elements(self):
        # Construct a synthetic decompressed DGN v8 stream with 1 line element
        # pos 0: header padding (4 bytes)
        # pos 4: type_byte (LINE = 3)
        # pos 5: subtype_byte (0)
        # pos 6-7: padding
        # pos 8: word_count (e.g., 60 words -> 124 bytes size)
        # pos 0x2C (44): level (10)
        # pos 0x30 (48): color/weight/style
        # pos 0x64 (100): geometry points (2 points = 32 bytes)
        total_len = 140
        buf = bytearray(total_len)
        buf[4] = ElementType.LINE
        buf[5] = 0
        struct.pack_into("<I", buf, 8, 68)  # word count
        struct.pack_into("<I", buf, 0x2C, 10)  # level 10
        struct.pack_into("<I", buf, 0x30, 3 | (1 << 8))  # color 3, weight 1

        # Pack 2D points at offset 0x64
        pts_data = struct.pack("<dddd", 100.0, 200.0, 300.0, 400.0)
        buf[0x64:0x64 + len(pts_data)] = pts_data

        reader = DgnV8Reader.__new__(DgnV8Reader)
        elems = list(reader._parse_stream(bytes(buf)))
        self.assertEqual(len(elems), 1)
        elem = elems[0]
        self.assertEqual(elem.element_type, ElementType.LINE)
        self.assertEqual(elem.type_name, "Line")
        self.assertEqual(elem.level, 10)
        self.assertEqual(elem.color_index, 3)
        self.assertEqual(elem.weight, 1)
        self.assertEqual(len(elem.geometry), 2)
        self.assertEqual(elem.geometry[0], (100.0, 200.0))


if __name__ == "__main__":
    unittest.main()
