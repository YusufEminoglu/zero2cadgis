# -*- coding: utf-8 -*-
"""Real-QGIS conversion and hostile-input regression tests."""
from __future__ import annotations

import json
import gc
import os
import tempfile
import unittest
import zipfile
from contextlib import suppress
from unittest.mock import MagicMock

from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsProject,
)
from qgis.PyQt.QtWidgets import QMainWindow


_APP = QgsApplication.instance()
if _APP is None:
    _APP = QgsApplication([], False)
    _APP.initQgis()

from zero2cadgis.core.gis_engine import GisConverterEngine  # noqa: E402


class TestLiveConversion(unittest.TestCase):

    def setUp(self):
        self.converted_layers = []
        self.engines = []
        self.work = tempfile.mkdtemp(prefix="zero2cadgis-live-qgis-")
        self.source = os.path.join(self.work, "izmir_points.geojson")
        self.target = os.path.join(self.work, "delivery.gpkg")
        payload = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"name": "Konak"},
                 "geometry": {"type": "Point", "coordinates": [27.1287, 38.4189]}},
                {"type": "Feature", "properties": {"name": "Bornova"},
                 "geometry": {"type": "Point", "coordinates": [27.2195, 38.4622]}},
            ],
        }
        with open(self.source, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def tearDown(self):
        QgsProject.instance().removeAllMapLayers()
        self.converted_layers.clear()
        self.engines.clear()
        gc.collect()
        with suppress(OSError):
            import shutil
            shutil.rmtree(self.work)

    def _engine(self):
        engine = GisConverterEngine(
            self.source,
            self.target,
            QgsCoordinateReferenceSystem("EPSG:3857"),
        )
        self.engines.append(engine)
        return engine

    def test_geojson_is_atomically_reprojected_and_reopened(self):
        engine = self._engine()
        catalog = engine.discover_layers(use_cache=False)
        self.assertEqual(len(catalog), 1)
        layers = engine.convert()
        self.converted_layers.extend(layers)
        self.assertTrue(os.path.isfile(self.target))
        self.assertGreater(os.path.getsize(self.target), 0)
        self.assertEqual(len(layers), 1)
        self.assertTrue(layers[0].isValid())
        self.assertEqual(layers[0].featureCount(), 2)
        self.assertEqual(layers[0].crs().authid(), "EPSG:3857")
        extent = layers[0].extent()
        self.assertGreater(extent.xMinimum(), 3_000_000)
        self.assertGreater(extent.yMinimum(), 4_000_000)

    def test_failed_selection_preserves_existing_delivery(self):
        known_good = b"known-good-delivery"
        with open(self.target, "wb") as handle:
            handle.write(known_good)
        with self.assertRaises(ValueError):
            self._engine().convert(selected_layers=["missing-layer"])
        with open(self.target, "rb") as handle:
            self.assertEqual(handle.read(), known_good)

    def test_kmz_path_traversal_is_rejected(self):
        kmz = os.path.join(self.work, "hostile.kmz")
        with zipfile.ZipFile(kmz, "w") as archive:
            archive.writestr("doc.kml", "<kml/>")
            archive.writestr("../outside.txt", "must not escape")
        engine = GisConverterEngine(
            kmz, self.target, QgsCoordinateReferenceSystem("EPSG:3857"))
        with self.assertRaisesRegex(ValueError, "Unsafe path"):
            engine.extract_kmz()
        self.assertFalse(os.path.exists(os.path.join(self.work, "outside.txt")))

    def test_full_dock_builds_with_conversion_receipt(self):
        from zero2cadgis.dialogs.dock import Zero2CadGisDockWidget

        window = QMainWindow()
        iface = MagicMock()
        iface.mainWindow.return_value = window
        icon_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "icons"))
        dock = Zero2CadGisDockWidget(iface, icon_dir, window)
        self.assertEqual(dock.main_tab.count(), 3)
        self.assertEqual(
            dock.conversion_receipt_group.title(), "Last Conversion Receipt")
        self.assertEqual(dock.btn_copy_receipt.text(), "Copy Receipt")
        dock.close()
        dock.setParent(None)


if __name__ == "__main__":
    unittest.main()
