# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""NCZ Engine v2: decode expectations, selective decode, and safety tests."""
from __future__ import annotations

import math
import os
import tempfile
import unittest
from pathlib import Path

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


class TestNczEngineV2Decode(unittest.TestCase):
    """The engine decodes the synthetic corpus into the values its builders
    wrote, at the offsets documented in ``docs/NCZ_FORMAT.md``.

    Every expectation below is derived from the fixture bytes rather than
    recorded from this engine's own output, so a decoder regression fails
    these tests instead of being frozen in as the new truth.
    """

    #: builder -> (geometry kind, layer code, vertex count)
    GEOMETRY_CASES = (
        ("point", fx.point_block, "Point", 0, 1),
        ("line", fx.line_block, "Line", 1, 2),
        ("text", fx.text_block, "Text", 2, 1),
        ("polyline", lambda: fx.polyline_block(closed=False),
         "Polyline", 1, 3),
        ("closed polyline", lambda: fx.polyline_block(closed=True),
         "Polygon", 1, 5),
        ("circle", fx.circle_block, "Circle", 3, 1),
        ("arc", fx.arc_block, "Arc", 3, 1),
        ("triangle", fx.triangle_block, "Triangle", 4, 3),
        ("symbol", fx.symbol_block, "Symbol", 4, 1),
        ("box", fx.box_block, "Polygon", 1, 5),
        ("map sheet", fx.map_sheet_block, "MapSheet", 4, 5),
        ("block reference", fx.block_reference_block, "Block", 4, 1),
        ("compressed curve", fx.compressed_curve_block, "Polyline", 1, 5),
        ("gis point", fx.gis_point_block, "Point", 0, 1),
        ("embedded container", fx.embedded_container_block, "Point", 2, 1),
        ("smart object", fx.smart_object_block, "SmartObject", 1, 5),
    )

    _LAYERS = [b"L0", b"L1", b"L2", b"L3", b"L4"]

    def _entities(self, data: bytes) -> list[dict]:
        return parse_bytes(data)["entities"]

    def _single(self, builder) -> dict:
        entities = self._entities(
            fx.layer_table_block(self._LAYERS) + builder())
        self.assertEqual(len(entities), 1)
        return entities[0]

    def test_full_drawing_decodes_its_metadata(self):
        payload = parse_bytes(fx.full_drawing())

        self.assertEqual(payload["parser_backend"], "pure-python-v2")
        self.assertEqual(payload["version_name"], "NCZ-TEST-1.0")
        self.assertEqual(payload["epsg"], "EPSG:5254")
        self.assertEqual(
            payload["layer_names"],
            ["ROADS", "PARCELS", "TEXT", "TRIANGLES", "MISC"])
        # The LEX.ST2 rows the fixture wrote, resolved to opaque ARGB.
        self.assertEqual(
            payload["layer_colors"],
            [0xFFFF0000, 0xFF008000, 0xFF0000FF, 0xFFC8C800, 0xFF0A0A0A])

    def test_full_drawing_carries_its_attribute_table(self):
        payload = parse_bytes(fx.full_drawing())

        self.assertEqual(len(payload["attribute_tables"]), 1)
        table = payload["attribute_tables"][0]
        self.assertEqual(table["table_ref"], "@TAB1")
        self.assertEqual(len(table["rows"]), 1)
        self.assertEqual(table["rows"][0]["columns"]["label"], "PARCEL-42")

    def test_point_lands_in_map_order(self):
        """The stored pair is northing-first; the decoded x is the easting."""
        entity = self._single(fx.point_block)

        self.assertEqual(entity["geometry_kind"], "Point")
        self.assertEqual(entity["name"], "PT1")
        self.assertEqual(
            entity["coordinates"],
            [{"x": fx.BASE_X, "y": fx.BASE_Y, "z": 0.0}])

    def test_line_spans_the_two_written_endpoints(self):
        entity = self._single(fx.line_block)

        coordinates = entity["coordinates"]
        self.assertEqual(len(coordinates), 2)
        self.assertEqual(
            (coordinates[0]["x"], coordinates[0]["y"]),
            (fx.BASE_X, fx.BASE_Y))
        self.assertEqual(
            (coordinates[1]["x"], coordinates[1]["y"]),
            (fx.BASE_X + 100.0, fx.BASE_Y + 100.0))

    def test_text_carries_its_label_and_height(self):
        entity = self._single(lambda: fx.text_block(
            layer=2, text=b"LABEL", height=2.5))

        self.assertEqual(entity["geometry_kind"], "Text")
        self.assertEqual(entity["label_text"], "LABEL")
        self.assertAlmostEqual(entity["text_height"], 2.5, places=6)

    def test_polyline_vertices_follow_the_written_ring(self):
        entity = self._single(lambda: fx.polyline_block(closed=False))

        self.assertFalse(entity["is_closed"])
        # polyline_block writes BASE_X into the first stored slot and BASE_Y
        # into the second; the first slot is the northing, so the decoded
        # pair is (x = BASE_Y + dy, y = BASE_X + dx).
        self.assertEqual(
            [(c["x"], c["y"]) for c in entity["coordinates"]],
            [(fx.BASE_Y, fx.BASE_X),
             (fx.BASE_Y + 10.0, fx.BASE_X + 25.0),
             (fx.BASE_Y + 40.0, fx.BASE_X + 50.0)])

    def test_closed_polyline_is_reported_closed(self):
        entity = self._single(lambda: fx.polyline_block(closed=True))

        self.assertTrue(entity["is_closed"])
        coordinates = entity["coordinates"]
        self.assertEqual(len(coordinates), 5)
        self.assertEqual(
            (coordinates[0]["x"], coordinates[0]["y"]),
            (coordinates[-1]["x"], coordinates[-1]["y"]))

    def test_circle_radius_comes_from_the_diameter_endpoints(self):
        entity = self._single(fx.circle_block)

        self.assertEqual(entity["geometry_kind"], "Circle")
        self.assertAlmostEqual(entity["radius"], 5.0, places=6)

    def test_arc_carries_its_radius_and_sweep(self):
        entity = self._single(fx.arc_block)

        self.assertEqual(entity["geometry_kind"], "Arc")
        self.assertAlmostEqual(entity["radius"], 12.0, places=6)
        self.assertAlmostEqual(entity["start_angle"], 0.0, places=6)
        self.assertAlmostEqual(entity["end_angle"], 1.5, places=6)

    def test_box_dimensions_follow_the_stored_axes(self):
        """A box reports its extent per stored axis: ``box_width`` spans the
        northing axis and ``box_height`` the easting axis, which is the
        convention the written corner ring and the plan notation share."""
        entity = self._single(fx.box_block)

        self.assertAlmostEqual(entity["box_width"], 40.0, places=6)
        self.assertAlmostEqual(entity["box_height"], 60.0, places=6)
        # The fixture's rotation, in gradians-to-degrees terms: 0.5 rad.
        self.assertAlmostEqual(
            entity["rotation_degrees"], 0.5 * 180.0 / 3.141592653589793,
            places=6)

    def test_symbol_carries_its_code(self):
        entity = self._single(lambda: fx.symbol_block(layer=4, code=7))

        self.assertEqual(entity["geometry_kind"], "Symbol")
        self.assertEqual(entity["label_text"], "S7")

    def test_map_sheet_carries_its_name_and_extent(self):
        entity = self._single(fx.map_sheet_block)

        self.assertEqual(entity["geometry_kind"], "MapSheet")
        self.assertEqual(entity["label_text"], "SHEET-A4")
        self.assertAlmostEqual(entity["box_width"], 100.0, places=6)
        self.assertAlmostEqual(entity["box_height"], 100.0, places=6)

    def test_block_reference_carries_its_name(self):
        entity = self._single(fx.block_reference_block)

        self.assertEqual(entity["geometry_kind"], "Block")
        self.assertEqual(entity["label_text"], "BLOCKREF")

    def test_compressed_curve_expands_its_deltas(self):
        entity = self._single(fx.compressed_curve_block)

        # Origin plus one vertex per stored delta pair.
        self.assertEqual(len(entity["coordinates"]), 5)

    def test_gis_layout_record_is_read_at_its_shifted_offsets(self):
        """A kind-22 record keeps its fields 28 bytes further in."""
        entity = self._single(lambda: fx.gis_point_block(name=b"GISPT"))

        self.assertEqual(entity["geometry_kind"], "Point")
        self.assertEqual(entity["name"], "GISPT")
        self.assertEqual(
            (entity["coordinates"][0]["x"], entity["coordinates"][0]["y"]),
            (fx.BASE_X, fx.BASE_Y))

    def test_embedded_record_inside_a_container_is_decoded(self):
        entity = self._single(fx.embedded_container_block)

        self.assertEqual(entity["geometry_kind"], "Point")
        self.assertEqual(entity["layer_code"], 2)
        self.assertEqual(entity["name"], "NESTED")

    def test_each_geometry_builder_decodes_to_its_expected_shape(self):
        for label, builder, kind, layer, vertex_count in self.GEOMETRY_CASES:
            with self.subTest(geometry=label):
                entity = self._single(builder)
                self.assertEqual(entity["geometry_kind"], kind)
                self.assertEqual(entity["layer_code"], layer)
                self.assertEqual(len(entity["coordinates"]), vertex_count)

    def test_short_and_odd_blocks_decode_without_raising(self):
        for data in (b"", b"\x00" * 8, fx.block(21, bytes(6)),
                     fx.block(22, bytes(40)), fx.point_block()[:20]):
            with self.subTest(length=len(data)):
                self.assertEqual(self._entities(data), [])

    def test_a_truncated_record_yields_no_geometry(self):
        payload = parse_bytes(fx.version_block() + fx.point_block()[:20])
        self.assertEqual(payload["version_name"], "NCZ-TEST-1.0")
        self.assertEqual(payload["entities"], [])


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


class TestNczEngineV2RealFile(unittest.TestCase):
    """Opt-in decode of a real drawing named by an environment variable.

    No real drawing is committed. Point ``ZERO2CADGIS_NCZ_FIXTURE`` at a
    real ``.ncz``/``.nca`` file to run the engine over genuine data rather
    than the synthetic corpus, which is where format assumptions that the
    fixtures share would otherwise go unnoticed.
    """

    def test_real_file_decodes(self):
        path = os.environ.get("ZERO2CADGIS_NCZ_FIXTURE")
        if not path or not os.path.isfile(path):
            self.skipTest("set ZERO2CADGIS_NCZ_FIXTURE to a real .ncz file")

        with open(path, "rb") as handle:
            data = handle.read()
        payload = parse_bytes(data)

        self.assertEqual(payload["parser_backend"], "pure-python-v2")
        self.assertTrue(payload["entities"])
        self.assertTrue(payload["layer_names"])
        for entity in payload["entities"]:
            for coordinate in entity["coordinates"]:
                self.assertTrue(
                    math.isfinite(coordinate["x"])
                    and math.isfinite(coordinate["y"]))


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


class TestNczIndexCache(unittest.TestCase):
    """The fingerprinted index cache serves reopens without re-scanning."""

    def setUp(self):
        import tempfile as _tempfile
        from unittest import mock
        from zero2cadgis.core.ncz_engine.v2 import cache as ncz_cache

        self.ncz_cache = ncz_cache
        self._cache_dir = Path(_tempfile.mkdtemp(prefix="ncz_cache_test_"))
        patcher = mock.patch.object(
            ncz_cache, "_cache_root", return_value=self._cache_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

        import shutil
        self.addCleanup(
            lambda: shutil.rmtree(self._cache_dir, ignore_errors=True))

    def _write(self, data: bytes) -> str:
        fd, path = tempfile.mkstemp(suffix=".ncz")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "wb") as handle:
            handle.write(data)
        return path

    def test_second_open_is_served_from_cache(self):
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        path = self._write(fx.full_drawing())
        first = NetcadLazyReader(path).index()
        self.assertFalse(first.from_cache)

        second = NetcadLazyReader(path).index()
        self.assertTrue(second.from_cache)

        # identical catalog and decode results from the cached index
        self.assertEqual(
            [(s.layer_code, s.layer_name, s.record_count)
             for s in first.layer_summaries()],
            [(s.layer_code, s.layer_name, s.record_count)
             for s in second.layer_summaries()])
        codes = [s.layer_code for s in second.layer_summaries()]
        d1 = sorted(_digest_entity(_entity_to_dict(e))
                    for e in first.decode_layers(codes))
        d2 = sorted(_digest_entity(_entity_to_dict(e))
                    for e in second.decode_layers(codes))
        self.assertEqual(d1, d2)

    def test_cache_invalidated_when_content_changes(self):
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        path = self._write(fx.full_drawing())
        NetcadLazyReader(path).index()  # writes cache

        # rewrite with different content and a moved mtime
        with open(path, "wb") as handle:
            handle.write(fx.full_drawing() + fx.point_block(layer=4))
        os.utime(path, ns=(0, 0))

        reopened = NetcadLazyReader(path).index()
        self.assertFalse(reopened.from_cache)

    def test_layer_pen_widths_reach_the_entities_and_survive_the_cache(self):
        # LEX.ST2 carries each layer's pen width (Tire: SNR_YAPI_YAKLASMA 1.0,
        # PARSEL 0.3 mm); a layer without the flag draws with the default pen.
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        drawing = b"".join([
            fx.version_block(),
            fx.layer_table_block([b"PARSEL", b"SNR_YAPIYAK", b"H_H"]),
            fx.color_table_block([(0, 0, 0), (255, 0, 0), (128, 128, 128)], widths=[0.3, 1.0, None]),
            fx.line_block(layer=0), fx.line_block(layer=1), fx.line_block(layer=2),
        ])
        path = self._write(drawing)
        for reader in (NetcadLazyReader(path).index(), NetcadLazyReader(path).index()):   # fresh, then cached
            entities = reader.decode_layers([s.layer_code for s in reader.layer_summaries()])
            widths = {e.layer_name: e.line_width for e in entities}
            self.assertEqual(widths, {"PARSEL": 0.3, "SNR_YAPIYAK": 1.0, "H_H": None})

    def test_cache_is_a_miss_after_any_decoder_change(self):
        # A catalog cached by an older decoder hid 16 of K34C10B4C.NCZ's 28
        # layers (SM_YAPILASMA with emsal / yençok among them) because the
        # decoder changed and the version number did not.
        from unittest import mock
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        path = self._write(fx.full_drawing())
        NetcadLazyReader(path).index()                       # cached by this decoder
        self.assertTrue(NetcadLazyReader(path).index().from_cache)
        with mock.patch.object(self.ncz_cache, "engine_signature", return_value="an-older-decoder"):
            self.assertFalse(NetcadLazyReader(path).index().from_cache)
        signature = self.ncz_cache.engine_signature()
        self.assertEqual(len(signature), 16)
        self.assertEqual(signature, self.ncz_cache.engine_signature())   # stable within a build

    def test_cache_can_be_disabled_by_env(self):
        from unittest import mock
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        path = self._write(fx.full_drawing())
        with mock.patch.dict(
                os.environ,
                {"ZERO2CADGIS_NCZ_CACHE_DISABLE": "1"}):
            NetcadLazyReader(path).index()
            again = NetcadLazyReader(path).index()
            self.assertFalse(again.from_cache)

    def test_clear_removes_cache_entries(self):
        from zero2cadgis.core.netcad_parser import NetcadLazyReader

        path = self._write(fx.full_drawing())
        NetcadLazyReader(path).index()
        self.assertGreaterEqual(self.ncz_cache.clear(), 1)
        reopened = NetcadLazyReader(path).index()
        self.assertFalse(reopened.from_cache)


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

    def test_smart_object_uncounted_trailer_alignment(self):
        # Netcad 8 appends 81+ bytes of uncounted properties after smart objects.
        # Ensure the stream recovers alignment and decodes subsequent entities.
        trailer = b"\x14drawBorderInGridMode\x03\x04True" + b"\x00" * 53
        data = (fx.layer_table_block([b"0", b"PLAN"])
                + fx.smart_object_block(layer=1)
                + trailer
                + fx.line_block(layer=1))
        payload = parse_bytes(data)
        entities = payload["entities"]
        self.assertEqual(len(entities), 2)
        kinds = {e["geometry_kind"] for e in entities}
        self.assertIn("SmartObject", kinds)
        self.assertIn("Line", kinds)


    def test_smart_object_corner_fallback_passes_through_both_corners(self):
        # When the stored width/height are unusable, the size comes from the two
        # stored corners. "first" is y and "second" is x (the ring runs width
        # along x), so width = |dx| and height = |dy|. The two are easy to
        # transpose here, which draws any non-square object off its own second
        # corner instead of around it.
        body = bytearray(fx.smart_object_block(layer=1)[5:])
        fx._put_f64(body, 169, 0.0)
        fx._put_f64(body, 177, 0.0)
        fx._put_f64(body, 66, fx.BASE_Y + 20.0)   # corner B, first (y)
        fx._put_f64(body, 74, fx.BASE_X + 30.0)   # corner B, second (x)
        data = fx.layer_table_block([b"0", b"PLAN"]) + fx.block(21, body)
        entity = parse_bytes(data)["entities"][0]
        self.assertEqual((entity["box_width"], entity["box_height"]), (30.0, 20.0))
        ring = {(round(c["x"], 6), round(c["y"], 6)) for c in entity["coordinates"]}
        self.assertIn((fx.BASE_X, fx.BASE_Y), ring)
        self.assertIn((fx.BASE_X + 30.0, fx.BASE_Y + 20.0), ring)


class TestSmartObjectPropertyBag(unittest.TestCase):
    """Netcad 8 building-rights values stored after a Smart Object."""

    @staticmethod
    def _entry(key, kind, value, display):
        k, v, d = key.encode(), value.encode("utf-8"), display.encode("utf-8")
        return bytes([len(k)]) + k + bytes([kind, len(v)]) + v + bytes([len(d)]) + d + bytes([1, 0, 0, 0, 0, 0, 1])

    def test_values_are_read_and_unset_ones_dropped_by_display_name(self):
        from zero2cadgis.core.ncz_engine.v2.properties import parse_property_bag
        raw = bytes(7) + b"".join([
            self._entry("nizam", 0x12, "BİTİŞİK", "Nizam"),
            self._entry("kat", 0x09, "4", "Kat"),
            self._entry("chkKatIsNull", 0x03, "False", "Kat"),
            # key "txtOn" and flag "chkOnIsNull" only share the display name "Ön"
            self._entry("txtOn", 0x0F, "0", "Ön"),
            self._entry("chkOnIsNull", 0x03, "True", "Ön"),
            self._entry("txtArka", 0x12, "", "Arka"),
        ])
        self.assertEqual(parse_property_bag(raw), {"nizam": "BİTİŞİK", "kat": "4"})

    def test_a_smart_object_record_carries_its_properties(self):
        body = bytearray(fx.smart_object_block(layer=1)[5:])
        trailer = b"".join([self._entry("taks", 0x0F, "0.3", "Taks"),
                            self._entry("chkTaksIsNull", 0x03, "False", "Taks")])
        data = fx.layer_table_block([b"0", b"SM_YAPILASMA"]) + fx.block(21, bytes(body) + trailer)
        entity = parse_bytes(data)["entities"][0]
        self.assertEqual(entity["properties"].get("taks"), "0.3")


if __name__ == "__main__":
    unittest.main()
