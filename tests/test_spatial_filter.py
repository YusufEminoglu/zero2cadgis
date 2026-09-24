# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""test_spatial_filter — Unit tests for the CAD/GIS spatial extent filter."""
from __future__ import annotations

import os
import tempfile
import unittest

from zero2cadgis.core.spatial_filter import (
    ExtentBox,
    ExtentInspectionResult,
    discover_files,
    evaluate_extent_intersection,
    inspect_ncz_extent,
    scan_and_filter_files,
)
from zero2cadgis.tests.ncz_fixtures import (
    BASE_X,
    BASE_Y,
    block,
    point_block,
    polyline_block,
    version_block,
)


class TestExtentBox(unittest.TestCase):

    def test_extent_box_properties(self):
        b = ExtentBox(min_x=10.0, min_y=20.0, max_x=50.0, max_y=80.0)
        self.assertTrue(b.is_valid)
        self.assertEqual(b.width, 40.0)
        self.assertEqual(b.height, 60.0)
        self.assertEqual(b.center, (30.0, 50.0))

    def test_extent_box_invalid(self):
        # min > max
        b1 = ExtentBox(min_x=50.0, min_y=20.0, max_x=10.0, max_y=80.0)
        self.assertFalse(b1.is_valid)

        # All zero
        b2 = ExtentBox(min_x=0.0, min_y=0.0, max_x=0.0, max_y=0.0)
        self.assertFalse(b2.is_valid)

    def test_extent_box_intersection(self):
        target = ExtentBox(100.0, 100.0, 200.0, 200.0)

        # Overlapping
        cand1 = ExtentBox(150.0, 150.0, 250.0, 250.0)
        self.assertTrue(target.intersects(cand1))
        self.assertTrue(cand1.intersects(target))

        # Disjoint
        cand2 = ExtentBox(300.0, 300.0, 400.0, 400.0)
        self.assertFalse(target.intersects(cand2))
        self.assertFalse(cand2.intersects(target))

        # Touching boundary
        cand3 = ExtentBox(200.0, 100.0, 250.0, 200.0)
        self.assertTrue(target.intersects(cand3))

    def test_extent_box_contains(self):
        outer = ExtentBox(0.0, 0.0, 1000.0, 1000.0)
        inner = ExtentBox(100.0, 100.0, 200.0, 200.0)
        partial = ExtentBox(500.0, 500.0, 1500.0, 1500.0)

        self.assertTrue(outer.contains(inner))
        self.assertFalse(inner.contains(outer))
        self.assertFalse(outer.contains(partial))


class TestEvaluateExtentIntersection(unittest.TestCase):

    def test_predicate_intersects(self):
        target = ExtentBox(100.0, 100.0, 200.0, 200.0)
        overlapping = ExtentBox(150.0, 150.0, 250.0, 250.0)
        disjoint = ExtentBox(500.0, 500.0, 600.0, 600.0)

        matches, reason = evaluate_extent_intersection(
            overlapping, "EPSG:5258", target, "EPSG:5258", predicate="intersects"
        )
        self.assertTrue(matches)
        self.assertIn("Intersects", reason)

        matches_no, reason_no = evaluate_extent_intersection(
            disjoint, "EPSG:5258", target, "EPSG:5258", predicate="intersects"
        )
        self.assertFalse(matches_no)
        self.assertIn("Does not intersect", reason_no)

    def test_predicate_within(self):
        target = ExtentBox(0.0, 0.0, 500.0, 500.0)
        inside = ExtentBox(100.0, 100.0, 200.0, 200.0)
        straddling = ExtentBox(400.0, 400.0, 600.0, 600.0)

        matches, _ = evaluate_extent_intersection(
            inside, "EPSG:5258", target, "EPSG:5258", predicate="within"
        )
        self.assertTrue(matches)

        matches_straddle, _ = evaluate_extent_intersection(
            straddling, "EPSG:5258", target, "EPSG:5258", predicate="within"
        )
        self.assertFalse(matches_straddle)

    def test_buffer_distance(self):
        target = ExtentBox(100.0, 100.0, 200.0, 200.0)
        # Disjoint by 20 units
        near = ExtentBox(220.0, 100.0, 300.0, 200.0)

        # Without buffer -> False
        m1, _ = evaluate_extent_intersection(
            near, "EPSG:5258", target, "EPSG:5258", buffer_distance=0.0
        )
        self.assertFalse(m1)

        # With buffer of 30 units -> True
        m2, _ = evaluate_extent_intersection(
            near, "EPSG:5258", target, "EPSG:5258", buffer_distance=30.0
        )
        self.assertTrue(m2)


class TestDiscoverFiles(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_discover_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_files_filtering(self):
        # Create dummy files
        f_ncz = os.path.join(self.temp_dir, "sheet1.ncz")
        f_dxf = os.path.join(self.temp_dir, "sheet2.dxf")
        f_txt = os.path.join(self.temp_dir, "notes.txt")  # Not in default CAD/GIS list
        f_kml = os.path.join(self.temp_dir, "boundary.kml")

        for f in (f_ncz, f_dxf, f_txt, f_kml):
            with open(f, "w", encoding="utf-8") as h:
                h.write("dummy")

        # Subdirectory
        sub = os.path.join(self.temp_dir, "sub")
        os.makedirs(sub, exist_ok=True)
        f_sub_ncz = os.path.join(sub, "sheet3.ncz")
        with open(f_sub_ncz, "w", encoding="utf-8") as h:
            h.write("dummy")

        # Recursive
        found = discover_files(self.temp_dir, recursive=True)
        basenames = [os.path.basename(p) for p in found]
        self.assertIn("sheet1.ncz", basenames)
        self.assertIn("sheet2.dxf", basenames)
        self.assertIn("boundary.kml", basenames)
        self.assertIn("sheet3.ncz", basenames)
        self.assertNotIn("notes.txt", basenames)

        # Flat (non-recursive)
        found_flat = discover_files(self.temp_dir, recursive=False)
        flat_basenames = [os.path.basename(p) for p in found_flat]
        self.assertIn("sheet1.ncz", flat_basenames)
        self.assertNotIn("sheet3.ncz", flat_basenames)


class TestNczExtentInspection(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_ncz_ext_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_inspect_ncz_extent_from_fixture(self):
        # Build synthetic NCZ with known coordinates:
        # Point 1 at (500000.0, 4200000.0)
        # Point 2 at (500500.0, 4200800.0)
        data = (
            version_block()
            + point_block(layer=0, x=500000.0, y=4200000.0)
            + point_block(layer=1, x=500500.0, y=4200800.0)
        )

        ncz_path = os.path.join(self.temp_dir, "test_sheet.ncz")
        with open(ncz_path, "wb") as h:
            h.write(data)

        res = inspect_ncz_extent(ncz_path, fallback_crs="EPSG:5258")
        self.assertEqual(res.error, "")
        self.assertTrue(res.box.is_valid)
        self.assertAlmostEqual(res.box.min_x, 500000.0)
        self.assertAlmostEqual(res.box.max_x, 500500.0)
        self.assertAlmostEqual(res.box.min_y, 4200000.0)
        self.assertAlmostEqual(res.box.max_y, 4200800.0)


class TestBatchScanAndFilter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_batch_filter_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_scan_matches_only_intersecting_files(self):
        # Create 3 synthetic NCZ files:
        # File 1: inside target area (500000 to 501000, 4200000 to 4201000)
        # File 2: outside target area (600000 to 601000, 4500000 to 4501000)
        # File 3: overlapping edge of target area (502000 to 503000, 4202000 to 4203000)

        f1 = os.path.join(self.temp_dir, "sheet_inside.ncz")
        f2 = os.path.join(self.temp_dir, "sheet_outside.ncz")
        f3 = os.path.join(self.temp_dir, "sheet_edge.ncz")

        with open(f1, "wb") as h:
            h.write(
                version_block()
                + point_block(layer=0, x=500000.0, y=4200000.0)
                + point_block(layer=0, x=501000.0, y=4201000.0)
            )
        with open(f2, "wb") as h:
            h.write(
                version_block()
                + point_block(layer=0, x=600000.0, y=4500000.0)
                + point_block(layer=0, x=601000.0, y=4501000.0)
            )
        with open(f3, "wb") as h:
            h.write(
                version_block()
                + point_block(layer=0, x=502000.0, y=4202000.0)
                + point_block(layer=0, x=503000.0, y=4203000.0)
            )

        # Target box: 499000 to 502500, 4199000 to 4202500
        target = ExtentBox(499000.0, 4199000.0, 502500.0, 4202500.0)

        progress_calls = []

        def on_progress(done, total, filename):
            progress_calls.append((done, total, filename))

        results = scan_and_filter_files(
            [f1, f2, f3],
            target_box=target,
            predicate="intersects",
            fallback_crs="EPSG:5258",
            progress_callback=on_progress,
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(len(progress_calls), 3)

        by_name = {os.path.basename(r.file_path): r for r in results}
        self.assertTrue(by_name["sheet_inside.ncz"].matches)
        self.assertTrue(by_name["sheet_edge.ncz"].matches)
        self.assertFalse(by_name["sheet_outside.ncz"].matches)


if __name__ == "__main__":
    unittest.main()
