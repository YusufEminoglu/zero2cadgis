# -*- coding: utf-8 -*-
"""test_e2e_converter — Unit and E2E validation test suite with QGIS/GDAL mocking.
100% English.
"""
import sys
import unittest
from unittest.mock import MagicMock

# Set up mock objects for QGIS and GDAL/OGR dependencies to allow test execution without QGIS installation
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()
sys.modules['qgis.gui'] = MagicMock()
sys.modules['qgis.PyQt'] = MagicMock()
sys.modules['qgis.PyQt.QtCore'] = MagicMock()
sys.modules['qgis.PyQt.QtGui'] = MagicMock()
sys.modules['osgeo'] = MagicMock()
sys.modules['osgeo.ogr'] = MagicMock()
sys.modules['osgeo.osr'] = MagicMock()
sys.modules['osgeo.gdal'] = MagicMock()

# Inject dummy classes/attributes that modules import at runtime
import qgis.core
qgis.core.QgsField = MagicMock
qgis.core.QgsFields = MagicMock

# Now import test target core modules
from zero2gpkg_converter.core.gis_engine import parse_kml_html_table
from zero2gpkg_converter.core.cad_engine import CadCleanupEngine
from zero2gpkg_converter.core.netcad_parser import NetcadCoordinate, NetcadEntity


class TestZero2GpkgConverter(unittest.TestCase):
    
    def test_kml_html_balloon_parsing(self):
        """Tests that HTML balloon description tables are successfully expanded to fields."""
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
        """Tests fallback to <li> balloon styling tags parsing."""
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
        """Verifies collinear nodes thinning algorithm."""
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
        """Verifies adjacent duplicate points are successfully stripped."""
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
        """Verifies polyline endpoint automatic closure gap tolerance."""
        coords = [
            NetcadCoordinate(0.0, 0.0),
            NetcadCoordinate(0.0, 10.0),
            NetcadCoordinate(10.0, 10.0),
            NetcadCoordinate(10.0, 0.05),
        ]
        closed = CadCleanupEngine.close_polyline(coords, 0.1)
        self.assertEqual(len(closed), 5)
        self.assertEqual(closed[-1].x, 0.0)
        self.assertEqual(closed[-1].y, 0.0)


if __name__ == "__main__":
    unittest.main()
