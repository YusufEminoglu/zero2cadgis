# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Contract and malformed-input tests for the built-in NCZ parser."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from zero2cadgis.core.netcad_parser import (
    NetcadAttributeRow,
    NetcadAttributeTable,
    NetcadBinaryReader,
    NetcadCoordinate,
    NetcadEntity,
    NetcadParseResult,
)


class TestNczParserContract(unittest.TestCase):
    def setUp(self) -> None:
        descriptor, path = tempfile.mkstemp(
            prefix=".ncz-test-",
            suffix=".ncz",
            dir=Path(__file__).resolve().parent,
        )
        os.close(descriptor)
        self._input_path = Path(path)
        self.addCleanup(self._input_path.unlink, missing_ok=True)

    def _parse(self, payload: bytes | bytearray) -> NetcadParseResult:
        self._input_path.write_bytes(payload)
        return NetcadBinaryReader(str(self._input_path)).parse()

    def test_public_result_model_remains_available(self) -> None:
        coordinate = NetcadCoordinate(1.0, 2.0, 3.0)
        entity = NetcadEntity(
            geometry_kind="Point",
            layer_code=4,
            coordinates=[coordinate],
        )
        row = NetcadAttributeRow(row_index=1, columns={"name": "parcel"})
        table = NetcadAttributeTable(table_ref="@TAB1", rows=[row])
        result = NetcadParseResult(entities=[entity], attribute_tables=[table])

        self.assertEqual(result.entities[0].coordinates[0].z, 3.0)
        self.assertEqual(
            result.attribute_tables[0].rows[0].columns["name"],
            "parcel",
        )

    def test_empty_and_truncated_inputs_are_safe(self) -> None:
        for payload in (b"", b"\x00", b"NCZ", b"\x00" * 16):
            with self.subTest(length=len(payload)):
                result = self._parse(payload)
                self.assertEqual(result.entities, [])
                self.assertEqual(result.attribute_tables, [])
                self.assertEqual(result.parser_backend, "pure-python")

    def test_short_known_blocks_do_not_read_past_input(self) -> None:
        short_layer_block = bytes([6, 0, 0, 0, 0, 0])

        short_projection_block = bytearray(12)
        short_projection_block[0] = 28
        short_projection_block[1:5] = (7).to_bytes(4, "little")
        short_projection_block[5] = 5
        short_projection_block[6:11] = b"MPROJ"

        short_color_block = bytearray(14)
        short_color_block[0] = 28
        short_color_block[1:5] = (9).to_bytes(4, "little")
        short_color_block[5] = 7
        short_color_block[6:13] = b"LEX.ST2"

        for payload in (
            short_layer_block,
            short_projection_block,
            short_color_block,
        ):
            with self.subTest(payload=bytes(payload)):
                result = self._parse(payload)
                self.assertEqual(result.entities, [])

    def test_declared_block_beyond_file_is_skipped(self) -> None:
        payload = bytearray(32)
        payload[0] = 21
        payload[1:5] = (2**32 - 1).to_bytes(4, "little")

        result = self._parse(payload)

        self.assertEqual(result.entities, [])
        self.assertEqual(result.unsupported_geometry_types, {})

    def test_deterministic_short_block_matrix_does_not_crash(self) -> None:
        block_types = (
            0, 5, 6, 14, 21, 22, 25, 28,
            48, 108, 111, 132, 150, 180,
        )
        for length in range(6, 49):
            for block_type in block_types:
                payload = bytearray(
                    (index * 37 + block_type) % 256
                    for index in range(length)
                )
                payload[0] = block_type
                payload[1:5] = (length - 5).to_bytes(4, "little")
                with self.subTest(length=length, block_type=block_type):
                    self._parse(payload)


if __name__ == "__main__":
    unittest.main()
