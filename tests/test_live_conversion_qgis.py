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
        self.assertEqual(dock.main_tab.tabText(0), "CAD & GIS Converter")
        self.assertEqual(dock.main_tab.tabText(1), "Netcad NCZ/NCA Importer")
        self.assertEqual(dock.main_tab.tabText(2), "CAD & GIS Exporter")
        self.assertEqual(
            dock.conversion_receipt_group.title(), "Last Conversion Receipt")
        self.assertEqual(dock.btn_copy_receipt.text(), "Copy Receipt")
        dock.close()
        dock.setParent(None)

    def test_spatial_filter_tab_components_and_flow(self):
        from zero2cadgis.dialogs.dock import Zero2CadGisDockWidget

        window = QMainWindow()
        iface = MagicMock()
        iface.mainWindow.return_value = window
        icon_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "icons"))
        dock = Zero2CadGisDockWidget(iface, icon_dir, window)

        # Spatial filter sub-dialog and tab buttons
        self.assertIsNotNone(dock.btn_cad_filter_extent)
        self.assertIsNotNone(dock.btn_ncz_filter_extent)
        self.assertIsNotNone(dock.spatial_filter_dialog)
        self.assertIsNotNone(dock.btn_run_filter_scan)
        self.assertIsNotNone(dock.tree_filter_results)
        self.assertEqual(dock.tree_filter_results.columnCount(), 7)

        # Boundary mode switching
        dock.cmb_filter_boundary_mode.setCurrentIndex(1)  # polygon
        self.assertFalse(dock.widget_filter_poly.isHidden())
        self.assertTrue(dock.widget_filter_canvas.isHidden())

        dock.cmb_filter_boundary_mode.setCurrentIndex(3)  # manual
        self.assertFalse(dock.widget_filter_manual.isHidden())
        dock.txt_filter_minx.setText("100.0")
        dock.txt_filter_miny.setText("200.0")
        dock.txt_filter_maxx.setText("300.0")
        dock.txt_filter_maxy.setText("400.0")
        geom, crs = dock._get_current_boundary_geometry()
        self.assertIsNotNone(geom)
        self.assertFalse(geom.isEmpty())
        self.assertAlmostEqual(geom.boundingBox().xMinimum(), 100.0)

        # Source paths application
        dock._apply_filter_source_paths([self.source])
        self.assertEqual(len(dock._filter_discovered_files), 1)
        self.assertTrue(dock.btn_run_filter_scan.isEnabled())

        # Tab 2 filter extent button exists
        self.assertIsNotNone(dock.btn_ncz_filter_extent)

        # Tab 2 MBTiles export button exists
        self.assertIsNotNone(dock.btn_ncz_to_mbtiles)

        # Tab 3 MBTiles format switching and options
        dock.cmb_exp_format.setCurrentIndex(3)
        self.assertFalse(dock.widget_mbtiles_opts.isHidden())
        self.assertTrue(dock.chk_export_selected.isHidden())
        self.assertEqual(dock.export_crs.crs().authid(), "EPSG:3857")
        self.assertEqual(
            dock.cmb_exp_layer.itemText(0),
            "[All Visible Canvas Layers / Project]")

        # Test bridge from Tab 2 to MBTiles exporter
        dock.txt_ncz_path.setText(os.path.join(self.work, "sample_plan.ncz"))
        dock._send_ncz_to_mbtiles_exporter()
        self.assertEqual(dock.main_tab.currentIndex(), 2)
        self.assertEqual(dock.cmb_exp_format.currentIndex(), 3)
        self.assertTrue(dock.txt_exp_path.text().endswith("sample_plan.mbtiles"))

        dock.close()
        dock.setParent(None)

    def test_mbtiles_export_engine(self):
        engine = self._engine()
        layers = engine.convert()
        self.converted_layers.extend(layers)
        self.assertEqual(len(layers), 1)
        layer = layers[0]
        self.assertTrue(layer.isValid())

        mbtiles_target = os.path.join(self.work, "points_pyramid.mbtiles")
        result = GisConverterEngine.export_to_mbtiles(
            output_path=mbtiles_target,
            layer=layer,
            min_zoom=10,
            max_zoom=11,
            tile_format="PNG",
            metatile_size=1
        )
        self.assertEqual(result.driver, "MBTiles")
        self.assertEqual(result.target_crs, "EPSG:3857")
        self.assertTrue(os.path.isfile(mbtiles_target))
        self.assertGreater(result.bytes_written, 0)
        self.assertGreater(result.feature_count, 0)


class TestPlanPipelineQgis(unittest.TestCase):
    """Plan-mode pieces that only mean anything with real QGIS geometry."""

    @staticmethod
    def _line(name, *pts, closed=False, kind="Line"):
        from zero2cadgis.core.netcad_parser import NetcadCoordinate, NetcadEntity
        return NetcadEntity(
            geometry_kind=kind, layer_code=7, layer_name=name, is_closed=closed,
            coordinates=[NetcadCoordinate(x, y) for x, y in pts])

    def test_polygonizer_nodes_crossings_keeps_holes_and_skips_closed(self):
        from zero2cadgis.core.cad_polygonizer import polygonize_cad_entities
        L = self._line
        # Two long lines crossing mid-segment plus two closing lines: without
        # noding there is no shared vertex at the crossings and no face at all.
        cross = [
            L("PL_KONUT", (0, 10), (100, 10)), L("PL_KONUT", (0, 90), (100, 90)),
            L("PL_KONUT", (10, 0), (10, 100)), L("PL_KONUT", (90, 0), (90, 100)),
        ]
        faces = polygonize_cad_entities(cross)
        self.assertEqual(len(faces), 1)
        self.assertEqual(faces[0].name, "POLYGONIZED")
        # A square inside it: the outer face keeps it as a hole.
        inner = [
            L("PL_KONUT", (40, 40), (60, 40)), L("PL_KONUT", (60, 40), (60, 60)),
            L("PL_KONUT", (60, 60), (40, 60)), L("PL_KONUT", (40, 60), (40, 40)),
        ]
        faces = polygonize_cad_entities(cross + inner)
        self.assertEqual(len(faces), 2)
        outer = max(faces, key=lambda f: len(f.interior_rings))
        self.assertEqual(len(outer.interior_rings), 1)
        # A closed polyline is already a polygon and must not come back twice.
        drawn = L("PL_KONUT", (200, 0), (220, 0), (220, 20), (200, 20), (200, 0),
                  closed=True, kind="Polyline")
        self.assertEqual(len(polygonize_cad_entities([drawn])), 0)
        # Not a plan area: KOPRU is a bridge, not KOP.
        bridge = [L("KOPRU", *seg) for seg in (((0, 0), (5, 0)), ((5, 0), (5, 5)),
                                               ((5, 5), (0, 5)), ((0, 5), (0, 0)))]
        self.assertEqual(polygonize_cad_entities(bridge), [])

    def test_cad_text_is_drawn_at_its_own_height_in_metres(self):
        from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsUnitTypes, QgsVectorLayer
        from qgis.PyQt.QtCore import QMetaType
        from zero2cadgis.core.cad_engine import CadStylingEngine

        layer = QgsVectorLayer("Point?crs=EPSG:5253", "YAZI_FONKSIYON_POINT", "memory")
        layer.dataProvider().addAttributes([
            QgsField("layer_name", QMetaType.Type.QString),
            QgsField("label", QMetaType.Type.QString),
            QgsField("text_h", QMetaType.Type.Double),
        ])
        layer.updateFields()
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromWkt("POINT(500000 4250000)"))
        f.setAttributes(["YAZI_FONKSIYON", "PARK", 4.9])
        layer.dataProvider().addFeatures([f])
        CadStylingEngine.apply_buffered_labels(layer)
        settings = layer.labeling().settings()
        self.assertEqual(settings.format().sizeUnit(), QgsUnitTypes.RenderUnit.RenderMetersInMapUnits)
        size_key = getattr(getattr(type(settings), "Property", type(settings)), "Size")
        self.assertTrue(settings.dataDefinedProperties().isActive(size_key))
        self.assertIn("text_h", settings.dataDefinedProperties().property(size_key).expressionString())


class TestMpyyStructureImportQgis(unittest.TestCase):
    """NCZ -> 02CadGis -> MPYY 1.1.7 workspace with the MPYY UİP styles."""

    def setUp(self):
        from qgis.PyQt.QtWidgets import QMessageBox
        self.errors = []
        self._critical, self._warning = QMessageBox.critical, QMessageBox.warning
        QMessageBox.critical = staticmethod(lambda *a, **k: self.errors.append(a[2:]))
        QMessageBox.warning = staticmethod(lambda *a, **k: self.errors.append(a[2:]))
        self.work = tempfile.mkdtemp(prefix="zero2cadgis-mpyy-")
        # Confirmed mappings go to a scratch file, never the planner's own.
        self._mapping_env = os.environ.get("MPYY_TABAKA_ESLESME")
        os.environ["MPYY_TABAKA_ESLESME"] = os.path.join(self.work, "eslesme.json")

    def tearDown(self):
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.critical, QMessageBox.warning = self._critical, self._warning
        if self._mapping_env is None:
            os.environ.pop("MPYY_TABAKA_ESLESME", None)
        else:
            os.environ["MPYY_TABAKA_ESLESME"] = self._mapping_env
        QgsProject.instance().removeAllMapLayers()
        QgsProject.instance().layerTreeRoot().removeAllChildren()
        gc.collect()

    TABAKA = [b"PL_KONUT", b"PL_GELISME_KONUT", b"ADAKENARI", b"CIZPEN", b"PL_ILKOKUL", b"PL_DINI_TESIS"]

    def _import(self):
        from qgis.PyQt.QtCore import Qt
        from zero2cadgis.dialogs.dock import Zero2CadGisDockWidget
        from zero2cadgis.tests import ncz_fixtures as fx

        path = os.path.join(self.work, "1000_TEST_UIP.ncz")
        with open(path, "wb") as handle:
            handle.write(b"".join([
                fx.version_block(),
                fx.layer_table_block(self.TABAKA),
                fx.polyline_block(layer=0, closed=True),
                fx.polyline_block(layer=1, closed=True),
                fx.line_block(layer=2),
                fx.polyline_block(layer=3, closed=True),
                fx.polyline_block(layer=4, closed=True),     # PL_ILKOKUL: spelling rule
                fx.polyline_block(layer=5, closed=True),     # PL_DINI_TESIS: proposal only
            ]))
        window = QMainWindow()
        iface = MagicMock()
        iface.mainWindow.return_value = window
        icon_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icons"))
        dock = Zero2CadGisDockWidget(iface, icon_dir, window)
        self.addCleanup(lambda: (dock.close(), dock.setParent(None)))
        dock._load_ncz_paths([path])
        tree = dock.ncz_layer_tree
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            for j in range(top.childCount()):
                for k in range(top.child(j).childCount()):
                    top.child(j).child(k).setCheckState(0, Qt.CheckState.Checked)
        dock.ncz_crs_selector.setCrs(QgsCoordinateReferenceSystem("EPSG:5253"))
        dock.chk_ncz_temporary.setChecked(True)
        dock.chk_ncz_plan_symbology.setChecked(True)     # plan mode = MPYY
        return dock

    def test_a_confirmed_proposal_is_transferred_and_remembered(self):
        from zero2cadgis.dialogs import tabaka_confirm_dialog as tcd
        from zero2cadgis.mpyy.core import tabaka_matching

        asked = []

        def fake_exec(dialog):
            asked.extend(tabaka for tabaka, _n, _s in dialog.rows)
            dialog.checks[[r[0] for r in dialog.rows].index("PL_DINI_TESIS")].setChecked(True)
            combo = dialog.combos[[r[0] for r in dialog.rows].index("PL_DINI_TESIS")]
            combo.setCurrentIndex(combo.findData("PL_CAMI"))
            return tcd.QDialog.DialogCode.Accepted

        original = tcd.TabakaConfirmDialog.exec
        tcd.TabakaConfirmDialog.exec = fake_exec
        try:
            dock = self._import()
            dock._import_netcad_dataset()
        finally:
            tcd.TabakaConfirmDialog.exec = original
        self.assertEqual(self.errors, [])
        self.assertIn("PL_DINI_TESIS", asked)          # proposals are asked about ...
        self.assertNotIn("PL_ILKOKUL", asked)          # ... safe rules are not
        result = dock.last_mpyy_result
        ibadet = {l.name(): l for l in result.layers}["IbadetAlani"]
        self.assertEqual([f["IbadetTip"] for f in ibadet.getFeatures()], ["Cami"])
        self.assertEqual(tabaka_matching.load_user_mappings()["UIP"]["PL_DINI_TESIS"], "PL_CAMI")
        self.assertIn("onaylı", result.summary())

    def test_any_function_can_be_picked_by_hand_in_the_confirmation_table(self):
        from zero2cadgis.dialogs.tabaka_confirm_dialog import TabakaConfirmDialog
        from zero2cadgis.mpyy.core import tabaka_matching as matching

        functions = matching.targets("UIP")
        rows = [("PL_ARITMA", 3, matching.suggest("UIP", "PL_ARITMA", geometry="polygon")),
                ("PL_KDKCA", 2, matching.suggest("UIP", "PL_KDKCA", geometry="polygon"))]
        self.assertTrue(rows[0][2])
        self.assertEqual(rows[1][2], [])                    # nothing to propose ...
        dialog = TabakaConfirmDialog("UIP", rows, None, functions=functions,
                                     geometries={"PL_ARITMA": "polygon", "PL_KDKCA": "polygon"})
        self.addCleanup(dialog.deleteLater)
        self.assertTrue(dialog.table.isRowHidden(1))        # ... listed, hidden until asked for
        dialog.chk_show_all.setChecked(True)
        self.assertFalse(dialog.table.isRowHidden(1))
        self.assertFalse(any(box.isChecked() for box in dialog.checks))   # proposals start unticked
        self.assertEqual(dialog.selections(), [])
        combo = dialog.combos[1]
        offered = {combo.itemData(i) for i in range(combo.count())}
        self.assertTrue(all(functions[k].geometry in ("polygon", "") for k in offered if k))
        lise = next(k for k, t in functions.items() if t.entry["attrs"].get("EgitimTesisTip") == "LiseAlani")
        combo.setCurrentIndex(combo.findData(lise))
        self.assertTrue(dialog.checks[1].isChecked())        # a hand pick is the planner's decision
        self.assertEqual(dialog.selections(), [("PL_KDKCA", lise)])

    def test_dxf_layers_go_to_mpyy_through_the_converter_path(self):
        from osgeo import ogr
        from qgis.core import QgsVectorLayer
        from zero2cadgis.dialogs.dock import Zero2CadGisDockWidget

        dxf = os.path.join(self.work, "1000_TEST_UIP.dxf")
        ds = ogr.GetDriverByName("DXF").CreateDataSource(dxf)
        entities = ds.CreateLayer("entities")
        for tabaka, x in (("PL_KONUT", 0), ("PL_ILKOKUL", 200), ("CIZPEN", 400)):
            feature = ogr.Feature(entities.GetLayerDefn())
            feature.SetField("Layer", tabaka)
            x0, y0 = 500000 + x, 4250000
            feature.SetGeometry(ogr.CreateGeometryFromWkt(
                f"LINESTRING({x0} {y0},{x0 + 100} {y0},{x0 + 100} {y0 + 100},{x0} {y0 + 100},{x0} {y0})"))
            entities.CreateFeature(feature)
        ds = None
        layer = QgsVectorLayer(dxf, "entities", "ogr")
        self.assertTrue(layer.isValid())
        layer.setCrs(QgsCoordinateReferenceSystem("EPSG:5253"))

        window = QMainWindow()
        iface = MagicMock()
        iface.mainWindow.return_value = window
        icon_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icons"))
        dock = Zero2CadGisDockWidget(iface, icon_dir, window)
        self.addCleanup(lambda: (dock.close(), dock.setParent(None)))
        dock.ask_tabaka_confirmation = False
        result = dock._transfer_converted_to_mpyy([layer], dxf, True, "")
        self.assertIsNotNone(result)
        self.assertEqual(result.level, "UIP")
        self.assertEqual({l.name() for l in result.layers}, {"Konut", "EgitimTesisAlani"})
        self.assertEqual([r["tabaka"] for r in result.unmatched], ["CIZPEN"])
        self.assertEqual(sum(l.featureCount() for l in result.leftovers), 1)
        for leftover in result.leftovers:
            self.assertEqual(leftover.renderer().referenceScale(), 1000)

    def test_ncz_import_in_mpyy_structure(self):
        dock = self._import()
        dock.ask_tabaka_confirmation = False
        try:
            dock._import_netcad_dataset()
            self.assertEqual(self.errors, [])

            result = dock.last_mpyy_result
            self.assertEqual(result.level, "UIP")
            by_name = {layer.name(): layer for layer in result.layers}
            # PL_ILKOKUL reaches its type by a spelling rule, without being asked.
            self.assertEqual(set(by_name), {"Konut", "AdaKenari", "EgitimTesisAlani"})
            self.assertEqual([f["EgitimTesisTip"] for f in by_name["EgitimTesisAlani"].getFeatures()],
                             ["IlkokulAlani"])
            self.assertIn("yazım kuralıyla", result.summary())
            konut_tip = sorted(f["KonutTip"] for f in by_name["Konut"].getFeatures())
            self.assertEqual(konut_tip, ["GelismeKonut", "YerlesikKonut"])
            for layer in result.layers:
                self.assertTrue(str(layer.customProperty("mpyy/symbology")).startswith("e-Plan SLD: UIP/"),
                                layer.name())
                self.assertIsNone(layer.customProperty("mpyy/missing_symbols"), layer.name())
            # The legend lists only what this plan uses: both konut types, and no
            # "no official symbol" fallback because every feature has its code.
            konut_rules = " ".join(r.filterExpression() + "|" + r.label()
                                   for r in by_name["Konut"].renderer().rootRule().descendants())
            self.assertIn("YerlesikKonut", konut_rules)
            self.assertIn("GelismeKonut", konut_rules)
            self.assertNotIn("Kodu girilmemiş", konut_rules)
            self.assertEqual(by_name["Konut"].customProperty("mpyy/legend"), "mevcut")
            # A numeric field gets a bounded widget (TAKS 0-1) from the MPYY forms.
            taks = by_name["Konut"].fields().indexFromName("Taks")
            self.assertEqual(by_name["Konut"].editorWidgetSetup(taks).type(), "Range")
            # Everything zooms together like the printed sheet: MPYY layers and the
            # 02CadGis layers of unmatched tabaka carry the UİP reference scale.
            for layer in result.layers + result.leftovers:
                self.assertEqual(layer.renderer().referenceScale(), 1000, layer.name())
            # Not in the crosswalk: reported and kept, never guessed.
            # Not confirmed, so a proposal is not applied: PL_DINI_TESIS stays unmatched.
            self.assertEqual(sorted(r["tabaka"] for r in result.unmatched), ["CIZPEN", "PL_DINI_TESIS"])
            self.assertEqual(sum(l.featureCount() for l in result.leftovers), 2)
            root = QgsProject.instance().layerTreeRoot()
            self.assertIsNotNone(root.findGroup("1000_TEST_UIP_MPYY_UIP"))
            self.assertIsNotNone(root.findGroup("1000_TEST_UIP_ESLESMEYEN_TABAKALAR"))
            # The MPYY styles come from inside 02CadGis, not from MPYY Studio.
            import sys
            self.assertFalse(any(m.startswith("planx_mpyy_studio") for m in sys.modules))
        finally:
            dock.close()
            dock.setParent(None)


if __name__ == "__main__":
    unittest.main()

