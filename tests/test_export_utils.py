# -*- coding: utf-8 -*-
"""Pure-Python regression tests for safe export publishing."""
from __future__ import annotations

import os
import tempfile
import unittest

from zero2cadgis.core.export_utils import (
    atomic_output,
    verified_export_result,
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


if __name__ == "__main__":
    unittest.main()
