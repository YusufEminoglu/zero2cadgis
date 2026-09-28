# -*- coding: utf-8 -*-
"""test_cad_polygonizer — Unit tests for CAD boundary line-to-polygon engine.

Tests area tabaka detection and boundary polygonization.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import unittest

from zero2cadgis.core.cad_polygonizer import (
    is_plan_area_tabaka,
    polygonize_cad_entities,
)
from zero2cadgis.core.netcad_parser import NetcadCoordinate, NetcadEntity


class TestCadPolygonizer(unittest.TestCase):
    """Unit tests for CAD boundary polygonizer."""

    def test_is_plan_area_tabaka(self):
        # Zoning area tabakas
        self.assertTrue(is_plan_area_tabaka("PL_KONUT"))
        self.assertTrue(is_plan_area_tabaka("PLAN_TICARET"))
        self.assertTrue(is_plan_area_tabaka("KONUT_ALANI"))
        self.assertTrue(is_plan_area_tabaka("PARK"))
        self.assertTrue(is_plan_area_tabaka("SANAYI_ALANI"))
        self.assertTrue(is_plan_area_tabaka("EGITIM_TESISI"))
        self.assertTrue(is_plan_area_tabaka("SAGLIK"))
        self.assertTrue(is_plan_area_tabaka("YESIL_ALAN"))
        self.assertTrue(is_plan_area_tabaka("GELISME_KONUT"))

        # Non-area tabakas
        self.assertFalse(is_plan_area_tabaka(None))
        self.assertFalse(is_plan_area_tabaka(""))
        self.assertFalse(is_plan_area_tabaka("CIZPEN"))
        self.assertFalse(is_plan_area_tabaka("GRID_100"))
        self.assertFalse(is_plan_area_tabaka("PAFTA_GRID"))
        self.assertFalse(is_plan_area_tabaka("KAREYAJ"))
        self.assertFalse(is_plan_area_tabaka("YOL_ORTA_HAT"))

    def test_polygonize_empty_or_headless(self):
        # Empty inputs should return empty list
        self.assertEqual(polygonize_cad_entities([]), [])

        # Non-area tabakas should be skipped
        lines = [
            NetcadEntity(
                layer_code=1,
                layer_name="BORDER_LINE",
                geometry_kind="Line",
                coordinates=[NetcadCoordinate(0, 0), NetcadCoordinate(10, 0)],
            )
        ]
        self.assertEqual(polygonize_cad_entities(lines), [])

    def test_polygonize_closed_square_in_qgis_runtime(self):
        try:
            from qgis.core import QgsGeometry
        except ImportError:
            # Running in pure Python environment; polygonize gracefully returns []
            return

        # 4 lines forming a closed 10x10 square
        lines = [
            NetcadEntity(
                layer_code=10,
                layer_name="KONUT_SINIR",
                geometry_kind="Line",
                coordinates=[NetcadCoordinate(0, 0), NetcadCoordinate(10, 0)],
            ),
            NetcadEntity(
                layer_code=10,
                layer_name="KONUT_SINIR",
                geometry_kind="Line",
                coordinates=[NetcadCoordinate(10, 0), NetcadCoordinate(10, 10)],
            ),
            NetcadEntity(
                layer_code=10,
                layer_name="KONUT_SINIR",
                geometry_kind="Line",
                coordinates=[NetcadCoordinate(10, 10), NetcadCoordinate(0, 10)],
            ),
            NetcadEntity(
                layer_code=10,
                layer_name="KONUT_SINIR",
                geometry_kind="Line",
                coordinates=[NetcadCoordinate(0, 10), NetcadCoordinate(0, 0)],
            ),
        ]

        polygons = polygonize_cad_entities(lines)
        self.assertGreaterEqual(len(polygons), 1)
        poly = polygons[0]
        self.assertEqual(poly.geometry_kind, "Polygon")
        self.assertTrue(poly.is_closed)
        self.assertEqual(poly.layer_name, "KONUT_SINIR")
        self.assertGreaterEqual(len(poly.coordinates), 4)


    def test_keywords_match_whole_tokens_only(self):
        # As substrings, KOP is inside KOPRU (a bridge) and ADA inside KADASTRO.
        self.assertFalse(is_plan_area_tabaka("KOPRU"))
        self.assertFalse(is_plan_area_tabaka("KADASTRO"))
        self.assertTrue(is_plan_area_tabaka("ADA"))
        self.assertTrue(is_plan_area_tabaka("ADAKENARI"))

    def test_only_open_line_work_is_polygonized(self):
        from zero2cadgis.core.cad_polygonizer import is_open_line_work
        square = [NetcadCoordinate(0, 0), NetcadCoordinate(10, 0),
                  NetcadCoordinate(10, 10), NetcadCoordinate(0, 10), NetcadCoordinate(0, 0)]
        closed = NetcadEntity(layer_code=1, layer_name="PL_KONUT",
                              geometry_kind="Polyline", is_closed=True, coordinates=square)
        opened = NetcadEntity(layer_code=1, layer_name="PL_KONUT",
                              geometry_kind="Polyline", is_closed=False, coordinates=square)
        text = NetcadEntity(layer_code=1, layer_name="PL_KONUT", geometry_kind="Text",
                            coordinates=square[:1])
        # A closed polyline is already a polygon; feeding it in again would
        # stack a duplicate on top of it.
        self.assertFalse(is_open_line_work(closed))
        self.assertTrue(is_open_line_work(opened))
        self.assertFalse(is_open_line_work(text))


if __name__ == "__main__":
    unittest.main()
