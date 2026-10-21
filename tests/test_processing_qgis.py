# -*- coding: utf-8 -*-
"""Real-QGIS tests of the 02CadGis Processing provider.

Each algorithm is run through ``QgsProcessingAlgorithm.run`` on data the test
writes itself, and its outputs are opened and counted — the provider loading
is not taken as evidence that an algorithm works.
"""
from __future__ import annotations

import gc
import json
import os
import shutil
import tempfile
import unittest
from contextlib import suppress

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QMetaType

_APP = QgsApplication.instance()
if _APP is None:
    _APP = QgsApplication([], False)
    _APP.initQgis()

from zero2cadgis.processing.algorithms import (  # noqa: E402
    CheckPlanConsistencyAlgorithm,
    ConvertDatasetAlgorithm,
    ImportNetcadAlgorithm,
)
from zero2cadgis.processing.provider import Zero2CadGisProvider  # noqa: E402
from zero2cadgis.tests import ncz_fixtures as fx  # noqa: E402


class _Feedback(QgsProcessingFeedback):
    """Keeps the errors an algorithm reports, so a failing run says why."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def reportError(self, error, fatalError=False):
        self.errors.append(error)


class _ProcessingCase(unittest.TestCase):
    CRS = "EPSG:5258"

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="zero2cadgis-processing-")
        self.project = QgsProject.instance()

    def tearDown(self):
        self.project.removeAllMapLayers()
        gc.collect()
        with suppress(OSError):
            shutil.rmtree(self.work)

    def _run(self, algorithm_class, parameters):
        algorithm = algorithm_class().create()
        context = QgsProcessingContext()
        context.setProject(self.project)
        feedback = _Feedback()
        results, ok = algorithm.run(parameters, context, feedback)
        return results, ok, context, feedback

    def _polygon_layer(self, wkts, fields=(), rows=None):
        layer = QgsVectorLayer(f"Polygon?crs={self.CRS}", "areas", "memory")
        layer.dataProvider().addAttributes(
            [QgsField(name, getattr(QMetaType.Type, kind)) for name, kind in fields])
        layer.updateFields()
        features = []
        for index, wkt in enumerate(wkts):
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromWkt(wkt))
            if rows:
                feature.setAttributes(list(rows[index]))
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        self.project.addMapLayer(layer)
        return layer

    @staticmethod
    def _gpkg_layers(path):
        from osgeo import ogr
        ds = ogr.Open(path)
        try:
            return {ds.GetLayer(i).GetName(): ds.GetLayer(i).GetFeatureCount()
                    for i in range(ds.GetLayerCount())}
        finally:
            ds = None


class TestProviderQgis(_ProcessingCase):

    def test_the_provider_registers_its_three_algorithms(self):
        provider = Zero2CadGisProvider()
        registry = QgsApplication.processingRegistry()
        self.assertTrue(registry.addProvider(provider))
        try:
            ids = sorted(a.id() for a in provider.algorithms())
            self.assertEqual(ids, ["zero2cadgis:checkplan", "zero2cadgis:convertdataset",
                                   "zero2cadgis:importnetcad"])
            for algorithm in provider.algorithms():
                self.assertTrue(algorithm.shortHelpString(), algorithm.id())
        finally:
            registry.removeProvider(provider)


class TestImportNetcadQgis(_ProcessingCase):

    FAMILY_GEOMETRY = {"POINT": QgsWkbTypes.GeometryType.PointGeometry,
                       "LINE": QgsWkbTypes.GeometryType.LineGeometry,
                       "POLYGON": QgsWkbTypes.GeometryType.PolygonGeometry}

    def setUp(self):
        super().setUp()
        self.drawing = os.path.join(self.work, "plan.ncz")
        with open(self.drawing, "wb") as handle:
            handle.write(fx.full_drawing())

    def _import(self, boundary=None, mode=1, name="out.gpkg"):
        parameters = {"INPUT": self.drawing, "SOURCE_CRS": self.CRS,
                      "CLOSE_TOLERANCE": 0.1, "CLIP_MODE": mode,
                      "OUTPUT": os.path.join(self.work, name)}
        if boundary is not None:
            parameters["BOUNDARY"] = boundary.id()
        return self._run(ImportNetcadAlgorithm, parameters)

    def test_each_tabaka_and_geometry_becomes_its_own_gpkg_layer(self):
        results, ok, context, feedback = self._import()
        self.assertTrue(ok, feedback.errors)
        written = self._gpkg_layers(results["OUTPUT"])
        self.assertEqual(results["LAYER_COUNT"], len(written))
        self.assertGreaterEqual(len(written), 3)
        self.assertEqual(results["FEATURE_COUNT"], sum(written.values()))
        tabaka = {"ROADS", "PARCELS", "TEXT", "TRIANGLES", "MISC"}
        for name, count in written.items():
            stem, family = name.rsplit("_", 1)
            self.assertIn(stem, tabaka, name)
            self.assertGreater(count, 0, name)
            layer = QgsVectorLayer(f"{results['OUTPUT']}|layername={name}", name, "ogr")
            self.assertTrue(layer.isValid(), name)
            self.assertEqual(layer.geometryType(), self.FAMILY_GEOMETRY[family], name)
            self.assertEqual(layer.crs().authid(), self.CRS, name)
            for column in ("source_file", "layer_name", "entity_type", "color_argb",
                           "line_width_mm"):
                self.assertIn(column, layer.fields().names(), name)
            self.assertEqual({f["layer_name"] for f in layer.getFeatures()}, {stem}, name)
            self.assertEqual({f["source_file"] for f in layer.getFeatures()}, {"plan"}, name)
        self.assertEqual(len(context.layersToLoadOnCompletion()), len(written))

    def test_a_boundary_around_the_drawing_keeps_every_feature(self):
        everything, ok, _context, feedback = self._import()
        self.assertTrue(ok, feedback.errors)
        # The boundary is the drawing's own extent, measured from the output:
        # the fixture's polylines decode far from BASE_X/BASE_Y (their stored
        # order is swapped, see test_ncz_engine_v2), so a box around the base
        # point would legitimately leave them out.
        extent = None
        for name in self._gpkg_layers(everything["OUTPUT"]):
            layer = QgsVectorLayer(f"{everything['OUTPUT']}|layername={name}", name, "ogr")
            if extent is None:
                extent = layer.extent()
            else:
                extent.combineExtentWith(layer.extent())
        around = self._polygon_layer([QgsGeometry.fromRect(extent).buffer(10, 4).asWkt()])
        kept, ok, _context, feedback = self._import(around, name="kept.gpkg")
        self.assertTrue(ok, feedback.errors)
        self.assertEqual(kept["FEATURE_COUNT"], everything["FEATURE_COUNT"])
        # Cropping at the same boundary keeps every feature too.
        cropped, ok, _context, feedback = self._import(around, mode=2, name="cropped.gpkg")
        self.assertTrue(ok, feedback.errors)
        self.assertEqual(cropped["FEATURE_COUNT"], everything["FEATURE_COUNT"])

    def test_a_boundary_away_from_the_drawing_is_refused_and_writes_nothing(self):
        away = self._polygon_layer(["POLYGON((0 0,10 0,10 10,0 10,0 0))"])
        results, ok, _context, feedback = self._import(away, name="away.gpkg")
        self.assertFalse(ok)
        self.assertTrue(any("spatial boundary" in e for e in feedback.errors), feedback.errors)
        self.assertFalse(os.path.exists(os.path.join(self.work, "away.gpkg")))


class TestCheckPlanQgis(_ProcessingCase):

    FIELDS = (("layer_name", "QString"), ("Taks", "Double"), ("EmsalKaks", "Double"),
              ("KatAdedi", "Int"))

    def test_findings_go_to_a_point_sink_and_overlaps_to_a_polygon_sink(self):
        areas = self._polygon_layer(
            ["POLYGON((0 0,100 0,100 100,0 100,0 0))",
             "POLYGON((50 0,150 0,150 100,50 100,50 0))"],
            self.FIELDS,
            [("PL_KONUT", 0.40, 2.00, 4),          # KAKS 2.00 > 0.40 x 4: unreachable
             ("PL_PARK", None, None, None)])       # overlaps the konut by 50 x 100
        results, ok, context, feedback = self._run(CheckPlanConsistencyAlgorithm, {
            "AREAS": [areas.id()], "OVERLAP_MIN_AREA": 1.0,
            "OUTPUT": "memory:", "OVERLAPS": "memory:"})
        self.assertTrue(ok, feedback.errors)
        self.assertEqual((results["FINDING_COUNT"], results["ERROR_COUNT"],
                          results["WARNING_COUNT"]), (2, 0, 2))
        points = context.getMapLayer(results["OUTPUT"])
        overlaps = context.getMapLayer(results["OVERLAPS"])
        self.assertEqual(sorted(f["check"] for f in points.getFeatures()),
                         ["overlapping_areas", "unreachable_kaks"])
        self.assertEqual(overlaps.featureCount(), 1)
        overlap = next(overlaps.getFeatures())
        self.assertAlmostEqual(overlap.geometry().area(), 5000.0, places=3)
        self.assertAlmostEqual(overlap["overlap_m2"], 5000.0, places=3)

    def test_a_geographic_crs_is_refused(self):
        areas = QgsVectorLayer("Polygon?crs=EPSG:4326", "areas", "memory")
        self.project.addMapLayer(areas)
        _results, ok, _context, feedback = self._run(CheckPlanConsistencyAlgorithm, {
            "AREAS": [areas.id()], "OUTPUT": "memory:"})
        self.assertFalse(ok)
        self.assertTrue(any("projected CRS" in e for e in feedback.errors), feedback.errors)


class TestConvertDatasetQgis(_ProcessingCase):

    def test_a_geojson_is_converted_and_reprojected(self):
        source = os.path.join(self.work, "points.geojson")
        with open(source, "w", encoding="utf-8") as handle:
            json.dump({"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"name": "Konak"},
                 "geometry": {"type": "Point", "coordinates": [27.1287, 38.4189]}},
                {"type": "Feature", "properties": {"name": "Bornova"},
                 "geometry": {"type": "Point", "coordinates": [27.2195, 38.4622]}},
            ]}, handle)
        output = os.path.join(self.work, "delivery.gpkg")
        results, ok, context, feedback = self._run(ConvertDatasetAlgorithm, {
            "INPUT": source, "SPLIT_CAD_LAYERS": True, "TARGET_CRS": "EPSG:3857",
            "OUTPUT": output})
        self.assertTrue(ok, feedback.errors)
        self.assertEqual((results["LAYER_COUNT"], results["FEATURE_COUNT"]), (1, 2))
        self.assertEqual(sum(self._gpkg_layers(output).values()), 2)
        (name,) = self._gpkg_layers(output)
        layer = QgsVectorLayer(f"{output}|layername={name}", name, "ogr")
        self.assertEqual(layer.crs().authid(), "EPSG:3857")
        self.assertGreater(layer.extent().xMinimum(), 3.0e6)     # metres, not degrees
        self.assertEqual(len(context.layersToLoadOnCompletion()), 1)


if __name__ == "__main__":
    unittest.main()
