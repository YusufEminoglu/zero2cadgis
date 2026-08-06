# -*- coding: utf-8 -*-
"""Unit tests for MsAccessDbReader (.accdb and .mdb support)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from qgis.core import QgsGeometry, QgsPointXY, QgsWkbTypes

from zero2cadgis.core.msaccess_reader import (
    MsAccessDbReader,
    _clean_attribute_value,
    _coerce_geometry,
    _geom_from_geojson_dict,
    find_best_geometry_column,
    get_msaccess_odbc_driver,
    is_msaccess_available,
    parse_geometry_value,
)


def test_clean_attribute_value():
    assert _clean_attribute_value(None) is None
    assert _clean_attribute_value(123) == 123
    assert _clean_attribute_value(45.67) == 45.67
    assert _clean_attribute_value("hello") == "hello"
    assert _clean_attribute_value(b"binary_data") == "<binary>"


def test_geom_from_geojson_dict():
    # Point
    p_dict = {"type": "Point", "coordinates": [500000.0, 4200000.0]}
    g_p = _geom_from_geojson_dict(p_dict)
    assert not g_p.isEmpty()
    assert g_p.type() == QgsWkbTypes.GeometryType.PointGeometry

    # LineString
    l_dict = {"type": "LineString", "coordinates": [[10, 20], [30, 40]]}
    g_l = _geom_from_geojson_dict(l_dict)
    assert not g_l.isEmpty()
    assert g_l.type() == QgsWkbTypes.GeometryType.LineGeometry

    # Polygon
    poly_dict = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
    }
    g_poly = _geom_from_geojson_dict(poly_dict)
    assert not g_poly.isEmpty()
    assert g_poly.type() == QgsWkbTypes.GeometryType.PolygonGeometry


def test_parse_geometry_value():
    # GeoJSON string
    geojson_str = json.dumps({"type": "Point", "coordinates": [500000.0, 4200000.0]})
    g1 = parse_geometry_value(geojson_str)
    assert g1 is not None and not g1.isEmpty()

    # WKT string
    wkt_str = "POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0))"
    g2 = parse_geometry_value(wkt_str)
    assert g2 is not None and not g2.isEmpty()

    # X, Y numeric coordinates
    g3 = parse_geometry_value(None, x_val=500100.0, y_val=4200100.0)
    assert g3 is not None and not g3.isEmpty()
    assert g3.asPoint() == QgsPointXY(500100.0, 4200100.0)

    # Empty / Invalid
    assert parse_geometry_value(None) is None
    assert parse_geometry_value("") is None
    assert parse_geometry_value("invalid string") is None


def test_find_best_geometry_column():
    cols = ["OBJECTID", "Layer", "geom", "POLY"]
    rows = [
        [1, "PL_REFUJ", '{"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]}', b"123"],
    ]
    g_col, x_col, y_col, geom_family = find_best_geometry_column(cols, rows)
    assert g_col == "geom"
    assert x_col is None
    assert y_col is None
    assert geom_family == "MultiPolygon"


def test_coerce_geometry():
    poly = QgsGeometry.fromPolygonXY([
        [QgsPointXY(0, 0), QgsPointXY(1, 0), QgsPointXY(1, 1), QgsPointXY(0, 0)],
    ])
    c_poly = _coerce_geometry(poly, "MultiPolygon")
    assert c_poly is not None
    assert QgsWkbTypes.isMultiType(c_poly.wkbType())

    line = QgsGeometry.fromPolylineXY([
        QgsPointXY(0, 0), QgsPointXY(10, 0), QgsPointXY(10, 10), QgsPointXY(0, 0),
    ])
    c_poly_from_line = _coerce_geometry(line, "MultiPolygon")
    assert c_poly_from_line is not None
    assert c_poly_from_line.type() == QgsWkbTypes.GeometryType.PolygonGeometry


def test_msaccess_available_flag():
    # Smoke test for function existence and boolean return
    res = is_msaccess_available()
    assert isinstance(res, bool)
    drv = get_msaccess_odbc_driver()
    assert drv is None or isinstance(drv, str)
