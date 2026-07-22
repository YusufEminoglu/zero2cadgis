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


class TestNczEngineV2RealFileParity(unittest.TestCase):
    """Opt-in v1<->v2 parity on a real drawing named by an env var.

    No third-party drawing is committed. Point ``ZERO2CADGIS_NCZ_FIXTURE``
    at a real ``.ncz``/``.nca`` file to run this bit-exact parity check.
    """

    def test_real_file_bit_exact_parity(self):
        path = os.environ.get("ZERO2CADGIS_NCZ_FIXTURE")
        if not path or not os.path.isfile(path):
            self.skipTest("set ZERO2CADGIS_NCZ_FIXTURE to a real .ncz file")

        with open(path, "rb") as handle:
            data = handle.read()
        v1 = sorted(_digest_entity(e)
                    for e in parse_netcad_binary_stream(path)["entities"])
        v2 = sorted(_digest_entity(e) for e in parse_bytes(data)["entities"])
        self.assertEqual(v1, v2)


def _digest_entity(entity: dict) -> tuple:
    """Full-precision (.17g) comparison key for bit-exact parity."""
    coords = tuple(
        (format(c["x"], ".17g"), format(c["y"], ".17g"),
         format(c["z"], ".17g"))
        for c in entity["coordinates"])
    scalar = tuple(
        format(entity[name], ".17g") for name in (
            "text_height", "rotation_degrees", "box_width", "box_height",
            "scale", "radius", "start_angle", "end_angle"))
    return (
        entity["geometry_kind"], entity["layer_code"], entity["layer_name"],
        entity["color_argb"], entity["name"], entity["label_text"],
        scalar, entity["is_closed"], coords)


class TestNetcadLazyReader(unittest.TestCase):
    """The dock-facing lazy reader indexes cheaply and decodes per layer."""

    def _write(self, data: bytes) -> str:
        fd, path = tempfile.mkstemp(suffix=".ncz",
                                    dir=Path(__file__).resolve().parent)
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def test_index_exposes_metadata_and_summaries(self):
        from zero2cadgis.core.netcad_parser import (
            NetcadLazyReader, PARSER_BACKEND_V2)

        path = self._write(fx.full_drawing())
        reader = NetcadLazyReader(path).index()
        self.assertEqual(reader.backend, PARSER_BACKEND_V2)
        self.assertEqual(reader.version_name, "NCZ-TEST-1.0")
        self.assertEqual(reader.epsg, "EPSG:5254")
        summaries = reader.layer_summaries()
        self.assertTrue(summaries)
        self.assertTrue(all(s.record_count > 0 for s in summaries))

    def test_decode_layers_returns_netcad_entities_for_subset(self):
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        path = self._write(fx.full_drawing())
        reader = NetcadLazyReader(path).index()
        codes = {s.layer_code for s in reader.layer_summaries()}
        self.assertIn(1, codes)

        subset = reader.decode_layers([1])
        self.assertTrue(subset)
        # entities are NetcadEntity dataclasses, not dicts
        self.assertTrue(all(e.layer_code == 1 for e in subset))
        self.assertTrue(hasattr(subset[0], "coordinates"))

        everything = reader.decode_layers(codes)
        self.assertLess(len(subset), len(everything))

    def test_decode_matches_full_parse_for_selected_layer(self):
        from zero2cadgis.core.netcad_parser import (
            NetcadBinaryReader, NetcadLazyReader)

        path = self._write(fx.full_drawing())
        full = NetcadBinaryReader(path).parse()
        expected = sorted(
            _digest_entity(_entity_to_dict(e))
            for e in full.entities if e.layer_code == 1)

        reader = NetcadLazyReader(path).index()
        got = sorted(
            _digest_entity(_entity_to_dict(e))
            for e in reader.decode_layers([1]))
        self.assertEqual(expected, got)

    def test_attribute_tables_available_from_index(self):
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        data = fx.full_drawing() + fx.attribute_table_block(b"@TAB2", b"X")
        path = self._write(data)
        reader = NetcadLazyReader(path).index()
        tables = reader.attribute_tables()
        self.assertTrue(tables)
        self.assertTrue(all(hasattr(t, "table_ref") for t in tables))


def _entity_to_dict(entity) -> dict:
    return {
        "geometry_kind": entity.geometry_kind,
        "layer_code": entity.layer_code,
        "layer_name": entity.layer_name,
        "color_argb": entity.color_argb,
        "name": entity.name,
        "label_text": entity.label_text,
        "text_height": entity.text_height,
        "rotation_degrees": entity.rotation_degrees,
        "box_width": entity.box_width,
        "box_height": entity.box_height,
        "scale": entity.scale,
        "radius": entity.radius,
        "start_angle": entity.start_angle,
        "end_angle": entity.end_angle,
        "is_closed": entity.is_closed,
        "coordinates": [
            {"x": c.x, "y": c.y, "z": c.z} for c in entity.coordinates],
    }


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
