# -*- coding: utf-8 -*-
"""test_plangml_export — Unit tests for Ministry PlanGML export engine.

Tests XML schema generation, element mapping, and GML 3 geometry serialization.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from zero2cadgis.core.plangml_export import (
    ELEMENT_NAME_MAP,
    PLANGML_NAMESPACES,
    PlanGmlExporter,
)


class TestPlanGmlExport(unittest.TestCase):
    """Unit tests for PlanGML exporter."""

    def test_namespace_definitions(self):
        self.assertIn("UIP", PLANGML_NAMESPACES)
        self.assertIn("NIP", PLANGML_NAMESPACES)
        self.assertIn("CDP", PLANGML_NAMESPACES)

        uip = PLANGML_NAMESPACES["UIP"]
        self.assertEqual(uip["prefix"], "uip")
        self.assertIn("uip_1000", uip["uri"])

    def test_element_name_mapping(self):
        self.assertEqual(
            PlanGmlExporter.map_to_element_name("PL_KONUT_ALANI"),
            "KonutAlani"
        )
        self.assertEqual(
            PlanGmlExporter.map_to_element_name("TICARET"),
            "TicaretAlani"
        )
        self.assertEqual(
            PlanGmlExporter.map_to_element_name("PARK_VE_YESIL_ALAN"),
            "ParkAlani"
        )
        self.assertEqual(
            PlanGmlExporter.map_to_element_name("TASIT_YOLU_10M"),
            "TasitYolu"
        )
        # Unknown falls back to sanitized UpperCamelCase
        self.assertEqual(
            PlanGmlExporter.map_to_element_name("OZEL_PROJE_ALANI"),
            "OzelProjeAlani"
        )

    def test_export_layer_to_plangml_qgis(self):
        try:
            from qgis.core import (
                QgsCoordinateReferenceSystem,
                QgsFeature,
                QgsField,
                QgsGeometry,
                QgsPointXY,
                QgsVectorLayer,
            )
            from qgis.PyQt.QtCore import QMetaType
        except ImportError:
            # Skip full QGIS geometry export when running outside QGIS runtime
            return

        # Create a polygon memory layer with zoning fields
        crs = QgsCoordinateReferenceSystem("EPSG:5254")
        layer = QgsVectorLayer(f"Polygon?crs={crs.toWkt()}", "PL_KONUT", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("YapiDuzeni", QMetaType.Type.QString),
            QgsField("KatAdedi", QMetaType.Type.Int),
            QgsField("EmsalKaks", QMetaType.Type.Double),
            QgsField("AdaNo", QMetaType.Type.QString),
            QgsField("ParselNo", QMetaType.Type.QString),
        ])
        layer.updateFields()

        # Add a polygon feature
        feat = QgsFeature(layer.fields())
        feat.setAttribute("YapiDuzeni", "AYRIK")
        feat.setAttribute("KatAdedi", 4)
        feat.setAttribute("EmsalKaks", 1.50)
        feat.setAttribute("AdaNo", "101")
        feat.setAttribute("ParselNo", "5")

        pts = [
            QgsPointXY(500000, 4500000),
            QgsPointXY(500100, 4500000),
            QgsPointXY(500100, 4500100),
            QgsPointXY(500000, 4500100),
            QgsPointXY(500000, 4500000),
        ]
        feat.setGeometry(QgsGeometry.fromPolygonXY([pts]))
        pr.addFeature(feat)
        layer.updateExtents()

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_gml = os.path.join(tmp_dir, "test_plan.gml")
            result = PlanGmlExporter.export_layer_to_plangml(
                layer=layer,
                output_path=out_gml,
                plan_type="UIP",
                target_crs=crs,
            )

            self.assertTrue(os.path.exists(out_gml))
            self.assertEqual(result.feature_count, 1)
            self.assertEqual(result.driver, "PlanGML")

            # Parse and verify XML structure
            tree = ET.parse(out_gml)
            root = tree.getroot()
            self.assertIn("FeatureCollection", root.tag)

            # Check that feature member exists
            features = list(root)
            self.assertGreaterEqual(len(features), 1)

            # Check tags within exported feature
            xml_text = ET.tostring(root, encoding="utf-8").decode("utf-8")
            self.assertIn("KonutAlani", xml_text)
            self.assertIn("<uip:YapiDuzeni>AYRIK</uip:YapiDuzeni>", xml_text)
            self.assertIn("<uip:KatAdedi>4</uip:KatAdedi>", xml_text)
            self.assertIn("<uip:EmsalKaks>1.5</uip:EmsalKaks>", xml_text)
            self.assertIn("<uip:AdaNo>101</uip:AdaNo>", xml_text)
            self.assertIn("<uip:ParselNo>5</uip:ParselNo>", xml_text)
            self.assertIn("gml:LinearRing", xml_text)
            self.assertIn("500000.000 4500000.000", xml_text)


if __name__ == "__main__":
    unittest.main()
