# -*- coding: utf-8 -*-
"""Pure-Python regression tests for safe export publishing."""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone

from zero2cadgis.core.export_utils import (
    atomic_output,
    verified_export_result,
)
from zero2cadgis.core.conversion_receipt import (
    ConvertedLayer,
    build_conversion_receipt,
)


class TestAtomicExport(unittest.TestCase):

    def setUp(self):
        # Use the existing repository scratch directory. Some restricted
        # Windows runners permit files but not newly created directories.
        scratch = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "scratch"))
        fd, self.output_path = tempfile.mkstemp(
            prefix="export-test-", suffix=".kml", dir=scratch)
        os.close(fd)
        os.remove(self.output_path)
        self.addCleanup(
            lambda: os.path.exists(self.output_path)
            and os.remove(self.output_path))

    def test_success_replaces_existing_delivery(self):
        with open(self.output_path, "wb") as handle:
            handle.write(b"old")

        with atomic_output(self.output_path) as temporary_path:
            self.assertTrue(temporary_path.endswith(".kml"))
            with open(temporary_path, "wb") as handle:
                handle.write(b"new-valid-output")

        with open(self.output_path, "rb") as handle:
            self.assertEqual(handle.read(), b"new-valid-output")

    def test_failure_keeps_existing_delivery(self):
        with open(self.output_path, "wb") as handle:
            handle.write(b"known-good")

        with self.assertRaisesRegex(RuntimeError, "writer crashed"):
            with atomic_output(self.output_path) as temporary_path:
                with open(temporary_path, "wb") as handle:
                    handle.write(b"partial")
                raise RuntimeError("writer crashed")

        with open(self.output_path, "rb") as handle:
            self.assertEqual(handle.read(), b"known-good")
        leftovers = [name for name in os.listdir(os.path.dirname(self.output_path))
                     if name.startswith(".zero2cadgis-export-")]
        self.assertEqual(leftovers, [])

    def test_empty_writer_output_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty output"):
            with atomic_output(self.output_path) as temporary_path:
                open(temporary_path, "wb").close()
        self.assertFalse(os.path.exists(self.output_path))

    def test_verified_result_reports_final_size(self):
        with open(self.output_path, "wb") as handle:
            handle.write(b"123456")
        result = verified_export_result(
            self.output_path, "KML", 17, "EPSG:4326")
        self.assertEqual(result.feature_count, 17)
        self.assertEqual(result.bytes_written, 6)
        self.assertEqual(result.target_crs, "EPSG:4326")

    def test_verified_result_reports_mbtiles(self):
        with open(self.output_path, "wb") as handle:
            handle.write(b"mbtiles_binary_data")
        result = verified_export_result(
            self.output_path, "MBTiles", 128, "EPSG:3857")
        self.assertEqual(result.feature_count, 128)
        self.assertEqual(result.driver, "MBTiles")
        self.assertEqual(result.target_crs, "EPSG:3857")
        self.assertEqual(result.bytes_written, 19)

    def test_conversion_receipt_is_copy_ready_and_deterministic(self):
        receipt = build_conversion_receipt(
            source=r"C:\data\izmir.geojson",
            mode="Atomic GeoPackage",
            destination=r"C:\delivery\izmir.gpkg",
            target_crs="EPSG:32635",
            layers=[
                ConvertedLayer("parcels", "Polygon", 12, "EPSG:32635"),
                ConvertedLayer("roads", "LineString", 30, "EPSG:32635"),
            ],
            warnings=["One empty geometry was skipped."],
            completed_at=datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc),
        )
        self.assertIn("2026-09-06T12:00:00+00:00", receipt)
        self.assertIn("Result: 2 layer(s), 42 feature(s)", receipt)
        self.assertIn("parcels | Polygon | 12 features | EPSG:32635", receipt)
        self.assertIn("Warnings:\n- One empty geometry was skipped.", receipt)

    def test_estimate_mbtiles_tile_count(self):
        from zero2cadgis.core.export_utils import estimate_mbtiles_tile_count
        from zero2cadgis.core.spatial_filter import ExtentBox

        # 1000m urban block in Web Mercator
        ext = ExtentBox(3924000.0, 4679000.0, 3925000.0, 4680000.0)
        count_15_16 = estimate_mbtiles_tile_count(ext, 15, 16)
        self.assertGreater(count_15_16, 0)
        self.assertLess(count_15_16, 50)

        # Global extent triggers huge count
        global_ext = ExtentBox(-20037508.0, -20037508.0, 20037508.0, 20037508.0)
        global_count = estimate_mbtiles_tile_count(global_ext, 12, 16)
        self.assertGreater(global_count, 1000000)

        # Tuple extent support
        tup_ext = (3924000.0, 4679000.0, 3925000.0, 4680000.0)
        self.assertEqual(estimate_mbtiles_tile_count(tup_ext, 15, 16), count_15_16)


if __name__ == "__main__":
    unittest.main()
