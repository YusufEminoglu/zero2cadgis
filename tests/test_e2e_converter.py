# -*- coding: utf-8 -*-
"""Unit and E2E validation tests with QGIS/GDAL mocking."""
import sys
import unittest
from unittest.mock import MagicMock, patch

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

from zero2cadgis.core.cad_engine import CadCleanupEngine  # noqa: E402
from zero2cadgis.core.gis_engine import parse_kml_html_table  # noqa: E402
from zero2cadgis.core.netcad_parser import NetcadCoordinate  # noqa: E402
from zero2cadgis.core.path_utils import ensure_extension, has_extension  # noqa: E402
from zero2cadgis.core.qgis_compat import memory_geometry_type_name  # noqa: E402


class TestZero2CadGis(unittest.TestCase):

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

    def test_qgis4_geometry_enum_detects_line_layers(self):
        class EnumLike:
            name = "Line"

            def __str__(self):
                return "GeometryType.Line"

        class FakeLayer:
            def wkbType(self):
                return object()

            def geometryType(self):
                return EnumLike()

        with patch(
            "zero2cadgis.core.qgis_compat.QgsWkbTypes.displayString",
            side_effect=Exception("no display string"),
        ):
            self.assertEqual(memory_geometry_type_name(FakeLayer()), "LineString")

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

    def test_get_geom_type_str_with_mocks(self):
        from zero2cadgis.core.gis_engine import _get_geom_type_str

        # Mock geometry with no object
        self.assertEqual(_get_geom_type_str(None), "NoGeometry")

        # Mock empty geometry
        mock_empty_geom = MagicMock()
        mock_empty_geom.isEmpty.return_value = True
        self.assertEqual(_get_geom_type_str(mock_empty_geom), "NoGeometry")

        # Mock Point geometry (type 0)
        mock_point_geom = MagicMock()
        mock_point_geom.isEmpty.return_value = False
        mock_point_geom.type.return_value = 0
        mock_point_geom.wkbType.return_value = 1  # Point
        with patch("zero2cadgis.core.gis_engine.QgsWkbTypes.isMultiType", return_value=False):
            self.assertEqual(_get_geom_type_str(mock_point_geom), "Point")

        # Mock MultiPoint geometry (type 0, multi type wkb)
        with patch("zero2cadgis.core.gis_engine.QgsWkbTypes.isMultiType", return_value=True):
            self.assertEqual(_get_geom_type_str(mock_point_geom), "MultiPoint")


class TestCsvSniffer(unittest.TestCase):
    """Pure-Python tests for the delimited-text geometry sniffer."""

    def _write_temp(self, content: str, suffix: str = ".csv") -> str:
        import tempfile
        import os
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_detects_lonlat_point_geometry_and_wgs84(self):
        from zero2cadgis.core.csv_sniffer import sniff_delimited_dataset

        path = self._write_temp(
            "id,name,lon,lat\n1,A,32.85,39.93\n2,B,29.02,41.01\n")
        profile = sniff_delimited_dataset(path)
        self.assertEqual(profile.delimiter, ",")
        self.assertEqual(profile.x_field, "lon")
        self.assertEqual(profile.y_field, "lat")
        self.assertEqual(profile.crs_authid, "EPSG:4326")
        self.assertTrue(profile.has_point_geometry)
        self.assertEqual(profile.row_count, 2)

    def test_detects_semicolon_delimiter_and_xy(self):
        from zero2cadgis.core.csv_sniffer import sniff_delimited_dataset

        path = self._write_temp(
            "parcel;x;y\nP1;500123.4;4432100.9\nP2;500200.0;4432155.5\n")
        profile = sniff_delimited_dataset(path)
        self.assertEqual(profile.delimiter, ";")
        self.assertEqual(profile.x_field, "x")
        self.assertEqual(profile.y_field, "y")
        self.assertEqual(profile.crs_authid, "")

    def test_wkt_column_overrides_xy(self):
        from zero2cadgis.core.csv_sniffer import sniff_delimited_dataset

        path = self._write_temp(
            "id,wkt,x,y\n1,POINT (1 2),1,2\n")
        profile = sniff_delimited_dataset(path)
        self.assertEqual(profile.wkt_field, "wkt")
        self.assertTrue(profile.has_wkt_geometry)
        self.assertEqual(profile.x_field, "")

    def test_attribute_only_table_has_no_geometry(self):
        from zero2cadgis.core.csv_sniffer import sniff_delimited_dataset

        path = self._write_temp("id,name,owner\n1,Parcel,PlanX\n")
        profile = sniff_delimited_dataset(path)
        self.assertFalse(profile.has_point_geometry)
        self.assertFalse(profile.has_wkt_geometry)
        self.assertIn("No geometry", profile.geometry_summary)

    def test_non_numeric_xy_candidates_are_rejected(self):
        from zero2cadgis.core.csv_sniffer import sniff_delimited_dataset

        path = self._write_temp("x,y,z\nleft,up,1\nright,down,2\n")
        profile = sniff_delimited_dataset(path)
        self.assertFalse(profile.has_point_geometry)

    def test_tsv_uses_tab_delimiter(self):
        from zero2cadgis.core.csv_sniffer import sniff_delimited_dataset

        path = self._write_temp(
            "id\tlongitude\tlatitude\n1\t27.14\t38.42\n", suffix=".tsv")
        profile = sniff_delimited_dataset(path)
        self.assertEqual(profile.delimiter, "\t")
        self.assertEqual(profile.x_field, "longitude")
        self.assertEqual(profile.y_field, "latitude")

    def test_delimitedtext_uri_point_fields(self):
        from zero2cadgis.core.csv_sniffer import (
            CsvGeometryProfile, build_delimitedtext_uri)

        profile = CsvGeometryProfile(
            delimiter=";", fields=["a", "x", "y"],
            x_field="x", y_field="y", crs_authid="EPSG:5254")
        uri = build_delimitedtext_uri(r"C:\data\pts.csv", profile)
        self.assertTrue(uri.startswith("file:///"))
        self.assertIn("xField=x", uri)
        self.assertIn("yField=y", uri)
        # provider does not percent-decode values: keep them raw
        self.assertIn("crs=EPSG:5254", uri)
        self.assertIn("delimiter=;", uri)

    def test_delimitedtext_uri_tab_token(self):
        from zero2cadgis.core.csv_sniffer import (
            CsvGeometryProfile, build_delimitedtext_uri)

        profile = CsvGeometryProfile(
            delimiter="\t", x_field="lon", y_field="lat")
        uri = build_delimitedtext_uri("/tmp/a.tsv", profile)
        self.assertIn("delimiter=\\t", uri)

    def test_delimitedtext_uri_wkt_and_none(self):
        from zero2cadgis.core.csv_sniffer import (
            CsvGeometryProfile, build_delimitedtext_uri)

        wkt_profile = CsvGeometryProfile(wkt_field="geom")
        uri = build_delimitedtext_uri("/tmp/a.csv", wkt_profile)
        self.assertIn("wktField=geom", uri)
        self.assertNotIn("xField", uri)

        table_profile = CsvGeometryProfile()
        uri = build_delimitedtext_uri("/tmp/b.csv", table_profile)
        self.assertIn("geomType=none", uri)

    def test_is_delimited_dataset(self):
        from zero2cadgis.core.csv_sniffer import is_delimited_dataset

        self.assertTrue(is_delimited_dataset(r"C:\d\points.CSV"))
        self.assertTrue(is_delimited_dataset("data.tsv"))
        self.assertTrue(is_delimited_dataset("data.txt"))
        self.assertFalse(is_delimited_dataset("drawing.dxf"))


if __name__ == "__main__":
    unittest.main()
