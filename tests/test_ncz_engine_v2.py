# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""NCZ Engine v2: parity with v1, selective decode, and safety tests."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from zero2cadgis.core.netcad_parser import parse_netcad_binary_stream
from zero2cadgis.core.ncz_engine.v2 import NczCatalog, parse_file
from zero2cadgis.core.ncz_engine.v2.parser import parse_bytes
from zero2cadgis.tests import ncz_fixtures as fx


def _normalize_entity(entity: dict) -> tuple:
    """Order-independent, backend-independent comparison key."""
    coords = tuple(
        (round(c["x"], 6), round(c["y"], 6), round(c["z"], 6))
        for c in entity["coordinates"]
    )
    return (
        entity["geometry_kind"],
        entity["layer_code"],
        entity["layer_name"],
        entity["color_argb"],
        entity["name"],
        entity["label_text"],
        round(entity["text_height"], 6),
        round(entity["rotation_degrees"], 6),
        round(entity["box_width"], 6),
        round(entity["box_height"], 6),
        round(entity["scale"], 6),
        round(entity["radius"], 6),
        round(entity["start_angle"], 6),
        round(entity["end_angle"], 6),
        entity["is_closed"],
        coords,
    )


def _normalize_payload(payload: dict) -> dict:
    return {
        "entities": sorted(
            _normalize_entity(e) for e in payload["entities"]),
        "layer_names": list(payload["layer_names"]),
        "layer_colors": list(payload["layer_colors"]),
        "version_name": payload["version_name"],
        "epsg": payload["epsg"],
        "projection_text": payload["projection_text"],
        "unsupported": dict(payload["unsupported_geometry_types"]),
        "tables": [
            (t["table_ref"], [
                (r["row_index"], tuple(sorted(r["columns"].items())))
                for r in t["rows"]])
            for t in payload["attribute_tables"]
        ],
    }


class TestNczEngineV2Parity(unittest.TestCase):
    """v2 must decode identical output to the v1 reference engine."""

    def _write(self, data: bytes) -> str:
        fd, path = tempfile.mkstemp(suffix=".ncz",
                                    dir=Path(__file__).resolve().parent)
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def _assert_parity(self, data: bytes) -> dict:
        path = self._write(data)
        v1 = _normalize_payload(parse_netcad_binary_stream(path))
        v2 = _normalize_payload(parse_bytes(data))
        self.assertEqual(v1, v2)
        return v2

    def test_full_drawing_parity(self):
        payload = self._assert_parity(fx.full_drawing())
        # sanity: the fixture actually produced geometry
        self.assertGreaterEqual(len(payload["entities"]), 8)
        self.assertEqual(payload["version_name"], "NCZ-TEST-1.0")
        self.assertEqual(payload["epsg"], "EPSG:5254")
        self.assertIn("ROADS", payload["layer_names"])

    def test_each_geometry_builder_parity(self):
        for builder in fx.ALL_GEOMETRY_BUILDERS:
            with self.subTest(builder=getattr(builder, "__name__", "lambda")):
                data = (fx.layer_table_block([b"L0", b"L1", b"L2", b"L3",
                                              b"L4"]) + builder())
                self._assert_parity(data)

    def test_parity_on_short_and_odd_blocks(self):
        payloads = (
            b"",
            b"\x00" * 8,
            fx.block(21, bytes(6)),
            fx.block(22, bytes(40)),
            fx.point_block()[:20],
            fx.version_block() + fx.point_block(),
        )
        for data in payloads:
            with self.subTest(length=len(data)):
                self._assert_parity(data)


class TestNczCatalogSelectiveDecode(unittest.TestCase):
    """The lazy catalog indexes cheaply and decodes chosen layers only."""

    def setUp(self):
        self.data = fx.full_drawing()

    def test_layer_catalog_lists_layers_without_decoding(self):
        catalog = NczCatalog(self.data).index()
        summaries = catalog.layer_catalog()
        codes = {summary.layer_code for summary in summaries}
        self.assertIn(1, codes)
        for summary in summaries:
            self.assertGreater(summary.record_count, 0)
            self.assertTrue(summary.families)

    def test_decode_layers_is_a_subset_of_decode_all(self):
        catalog = NczCatalog(self.data).index()
        every = catalog.decode_all()
        only_layer_1 = catalog.decode_layers([1])
        self.assertTrue(only_layer_1)
        self.assertLess(len(only_layer_1), len(every))
        for entity in only_layer_1:
            self.assertEqual(entity["layer_code"], 1)

    def test_decode_layers_matches_full_decode_for_that_layer(self):
        catalog = NczCatalog(self.data).index()
        full_layer_1 = sorted(
            _normalize_entity(e) for e in catalog.decode_all()
            if e["layer_code"] == 1)
        selective = sorted(
            _normalize_entity(e) for e in catalog.decode_layers([1]))
        self.assertEqual(full_layer_1, selective)

    def test_empty_selection_decodes_nothing(self):
        catalog = NczCatalog(self.data).index()
        self.assertEqual(catalog.decode_layers([]), [])


class TestNczEngineV2Safety(unittest.TestCase):
    """Malformed input must never raise or read past the buffer."""

    def test_parse_bytes_on_garbage_is_safe(self):
        for data in (b"", b"\x15", b"@TAB", bytes(range(256))):
            with self.subTest(length=len(data)):
                payload = parse_bytes(data)
                self.assertEqual(payload["parser_backend"],
                                 "pure-python-v2")

    def test_declared_block_beyond_file_is_skipped(self):
        payload = bytearray(32)
        payload[0] = 21
        payload[1:5] = (2 ** 32 - 1).to_bytes(4, "little")
        result = parse_bytes(bytes(payload))
        self.assertEqual(result["entities"], [])

    def test_parse_file_round_trip(self):
        fd, path = tempfile.mkstemp(suffix=".ncz")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "wb") as handle:
            handle.write(fx.full_drawing())
        payload = parse_file(path)
        self.assertGreaterEqual(len(payload["entities"]), 8)


if __name__ == "__main__":
    unittest.main()
