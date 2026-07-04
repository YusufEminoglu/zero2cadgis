# -*- coding: utf-8 -*-
"""Unit and E2E validation tests with QGIS/GDAL mocking."""
import sys
import unittest
from unittest.mock import MagicMock

# Set up mock objects for QGIS and GDAL/OGR dependencies to allow test
# execution without QGIS installation.
sys.modules["qgis"] = MagicMock()
sys.modules["qgis.core"] = MagicMock()
sys.modules["qgis.gui"] = MagicMock()
sys.modules["qgis.PyQt"] = MagicMock()
sys.modules["qgis.PyQt.QtCore"] = MagicMock()
sys.modules["qgis.PyQt.QtGui"] = MagicMock()
sys.modules["qgis.PyQt.QtXml"] = MagicMock()
sys.modules["osgeo"] = MagicMock()
sys.modules["osgeo.ogr"] = MagicMock()
sys.modules["osgeo.osr"] = MagicMock()
sys.modules["osgeo.gdal"] = MagicMock()

import qgis.core  # noqa: E402
qgis.core.QgsField = MagicMock
qgis.core.QgsFields = MagicMock

from zero2gpkg_converter.core.cad_engine import CadCleanupEngine  # noqa: E402
from zero2gpkg_converter.core.gis_engine import parse_kml_html_table  # noqa: E402
from zero2gpkg_converter.core.netcad_parser import NetcadCoordinate  # noqa: E402
from zero2gpkg_converter.core.path_utils import ensure_extension, has_extension  # noqa: E402


class TestZero2GpkgConverter(unittest.TestCase):

    def test_path_extension_helpers_are_case_insensitive(self):
        self.assertTrue(has_extension(r"C:\data\PARCELS.GPKG", ".gpkg"))
        self.assertTrue(has_extension(r"C:\data\source.GDB", ".gdb"))
        self.assertEqual(
            ensure_extension(r"C:\data\out.GPKG", ".gpkg"),
            r"C:\data\out.GPKG",
        )
        self.assertEqual(
            ensure_extension(r"C:\data\out", ".gpkg"),
            r"C:\data\out.gpkg",
        )

    def test_kml_html_balloon_parsing(self):
        html_input = """
        <table>
            <tr><td>Object ID</td><td>1042</td></tr>
            <tr><td>District</td><td>Cankaya</td></tr>
            <tr><td>Area sqm</td><td>540.25</td></tr>
        </table>
        """
        attributes = parse_kml_html_table(html_input)
        self.assertEqual(attributes.get("object_id"), "1042")
        self.assertEqual(attributes.get("district"), "Cankaya")
        self.assertEqual(attributes.get("area_sqm"), "540.25")

    def test_kml_html_balloon_list_parsing(self):
        html_input = """
        <ul>
            <li><b>Parcel No</b>: 125/4</li>
            <li><strong>Owner</strong>: PlanX Studio</li>
        </ul>
        """
        attributes = parse_kml_html_table(html_input)
        self.assertEqual(attributes.get("parcel_no"), "125/4")
        self.assertEqual(attributes.get("owner"), "PlanX Studio")

    def test_cad_collinear_node_simplification(self):
        coords = [
            NetcadCoordinate(0.0, 0.0),
            NetcadCoordinate(1.0, 0.0),
            NetcadCoordinate(2.0, 0.0),
            NetcadCoordinate(3.0, 0.0),
            NetcadCoordinate(3.0, 4.0),
        ]
        simplified = CadCleanupEngine.simplify_collinear(coords)
        self.assertLess(len(simplified), 5)
        self.assertEqual(simplified[0].x, 0.0)
        self.assertEqual(simplified[-1].y, 4.0)

    def test_cad_duplicate_points_cleanup(self):
        coords = [
            NetcadCoordinate(10.0, 20.0),
            NetcadCoordinate(10.0, 20.0),
            NetcadCoordinate(15.0, 25.0),
            NetcadCoordinate(15.0, 25.0),
        ]
        cleaned = CadCleanupEngine.clean_duplicates(coords)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(cleaned[0].x, 10.0)
        self.assertEqual(cleaned[1].x, 15.0)

    def test_cad_polyline_closure(self):
        class MockPointXY:
            def __init__(self, x, y):
                self._x = x
                self._y = y

            def x(self):
                return self._x

            def y(self):
                return self._y

        coords = [
            MockPointXY(0.0, 0.0),
            MockPointXY(0.0, 10.0),
            MockPointXY(10.0, 10.0),
            MockPointXY(0.05, 0.0),
        ]
        closed = CadCleanupEngine.close_polyline(coords, 0.1)
        self.assertEqual(len(closed), 5)
        self.assertEqual(closed[-1].x(), 0.0)
        self.assertEqual(closed[-1].y(), 0.0)

        far_open = [
            MockPointXY(0.0, 0.0),
            MockPointXY(0.0, 10.0),
            MockPointXY(10.0, 10.0),
            MockPointXY(20.0, 20.0),
        ]
        unchanged = CadCleanupEngine.close_polyline(far_open, 0.1)
        self.assertEqual(len(unchanged), 4)

        forced = CadCleanupEngine.close_polyline(far_open, 0.1, force=True)
        self.assertEqual(len(forced), 5)
        self.assertEqual(forced[-1].x(), 0.0)
        self.assertEqual(forced[-1].y(), 0.0)


if __name__ == "__main__":
    unittest.main()
