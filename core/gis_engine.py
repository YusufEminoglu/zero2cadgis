# -*- coding: utf-8 -*-
"""gis_engine — Advanced GIS converter engine.
Handles KML, KMZ, DGN, and GDB database conversions to GPKG.
Includes HTML balloon description parsing inspired by kmltools.
"""
from __future__ import annotations

import os
import re
import zipfile
import tempfile
import shutil
from typing import Generator

from osgeo import ogr, osr
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsVectorFileWriter,
    QgsFields
)
from qgis.PyQt.QtCore import QVariant


def parse_kml_html_table(html_content: str) -> dict[str, str]:
    """Parses KML balloon descriptions (HTML tables) into structured attributes.
    Feyz taken from kmltools to dominate competitors.
    """
    attributes = {}
    if not html_content:
        return attributes

    # Clean line breaks
    html = html_content.replace("\r", "").replace("\n", " ")
    
    # 1. Look for standard table rows <tr><td>Name</td><td>Value</td></tr>
    tr_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.IGNORECASE)
    for tr in tr_matches:
        td_matches = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.IGNORECASE)
        if len(td_matches) >= 2:
            key = re.sub('<[^<]+?>', '', td_matches[0]).strip()
            val = re.sub('<[^<]+?>', '', td_matches[1]).strip()
            # Clean keys to be valid database column names
            clean_key = re.sub(r'\W+', '_', key).lower().strip("_")
            if clean_key and len(clean_key) < 64:
                attributes[clean_key] = val

    # 2. If no table rows, check for bullet points or lists <li><b>Name:</b> Value</li>
    if not attributes:
        li_matches = re.findall(r"<li[^>]*>(.*?)</li>", html, re.IGNORECASE)
        for li in li_matches:
            # Check bold label pattern: <b>Name</b>: Value
            label_match = re.match(r"<(b|strong)>(.*?)</\1>\s*:?\s*(.*)", li, re.IGNORECASE)
            if label_match:
                key = re.sub('<[^<]+?>', '', label_match.group(2)).strip()
                val = re.sub('<[^<]+?>', '', label_match.group(3)).strip()
                clean_key = re.sub(r'\W+', '_', key).lower().strip("_")
                if clean_key and len(clean_key) < 64:
                    attributes[clean_key] = val

    return attributes


class GisConverterEngine:
    """Core GIS conversion service handles direct OGR layers copying to target GPKG."""
    
    def __init__(self, source_path: str, target_gpkg: str, target_crs: QgsCoordinateReferenceSystem):
        self.source_path = source_path
        self.target_gpkg = target_gpkg
        self.target_crs = target_crs
        self.temp_dirs = []

    def cleanup(self):
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def extract_kmz(self) -> str:
        """Extracts KMZ zip archive and returns the path to doc.kml."""
        temp_dir = tempfile.mkdtemp(prefix="gis_kmz_")
        self.temp_dirs.append(temp_dir)
        
        with zipfile.ZipFile(self.source_path, 'r') as zip_ref:
            kml_files = [n for n in zip_ref.namelist() if n.lower().endswith(".kml")]
            if not kml_files:
                raise ValueError("KML file not found in the KMZ package.")
            zip_ref.extractall(temp_dir)
            return os.path.join(temp_dir, kml_files[0])

    def convert(self, is_kmz: bool = False, html_expansion: bool = True) -> list[QgsVectorLayer]:
        """Converts GIS layers to GPKG and returns list of loaded layers."""
        src = self.source_path
        if is_kmz:
            src = self.extract_kmz()

        # Open source OGR dataset
        from osgeo import ogr
        ogr_ds = ogr.Open(src)
        if ogr_ds is None:
            raise ValueError(f"Unable to open source dataset with GDAL/OGR provider: {src}")

        layer_names = []
        for i in range(ogr_ds.GetLayerCount()):
            layer_names.append(ogr_ds.GetLayerByIndex(i).GetName())
        ogr_ds = None

        if not layer_names:
            raise ValueError("No layers discovered inside the source GIS dataset.")

        # Re-create target GPKG
        if os.path.exists(self.target_gpkg):
            try:
                os.remove(self.target_gpkg)
            except OSError:
                pass

        loaded_layers = []
        transform_context = QgsProject.instance().transformContext()

        for layer_name in layer_names:
            # Build QGIS Vector Layer
            uri = f"{src}|layername={layer_name}"
            vlayer = QgsVectorLayer(uri, layer_name, "ogr")
            if not vlayer.isValid():
                continue

            # Process Layer: HTML Balloon Expansion
            processed_layer = vlayer
            if html_expansion and "description" in [f.name() for f in vlayer.fields()]:
                processed_layer = self._expand_html_descriptions(vlayer)

            # Define writer options
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = self._sanitize_column_name(layer_name)
            options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
            options.overrideGeometryType = processed_layer.geometryType()
            
            # Apply CRS transform
            if processed_layer.crs() != self.target_crs:
                options.ct = QgsCoordinateTransform(processed_layer.crs(), self.target_crs, QgsProject.instance())

            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                processed_layer,
                self.target_gpkg,
                transform_context,
                options
            )
            if err != QgsVectorFileWriter.WriterError.NoError:
                raise ValueError(f"Failed writing layer '{layer_name}' to GPKG: {err_msg}")

            # Loaded URI
            gpkg_uri = f"{self.target_gpkg}|layername={options.layerName}"
            gpkg_layer = QgsVectorLayer(gpkg_uri, layer_name, "ogr")
            if gpkg_layer.isValid():
                loaded_layers.append(gpkg_layer)

        return loaded_layers

    def _expand_html_descriptions(self, layer: QgsVectorLayer) -> QgsVectorLayer:
        """Parses description column and expands into distinct feature attributes.
        Feyz taken from kmltools.
        """
        # Discover all dynamic columns by checking first 100 features
        new_field_definitions = {}
        for feat in layer.getFeatures():
            desc = feat["description"]
            if desc:
                attrs = parse_kml_html_table(str(desc))
                for k in attrs.keys():
                    new_field_definitions[k] = QVariant.String

        # Construct new fields structure
        fields = QgsFields()
        for field in layer.fields():
            fields.append(field)
        for k, vtype in sorted(new_field_definitions.items()):
            if k not in [f.name() for f in layer.fields()]:
                fields.append(QgsField(k, vtype))

        # Create temporary memory layer to populate expanded features
        uri = f"{layer.geometryType().name()}?crs={layer.crs().authid()}"
        expanded_layer = QgsVectorLayer(uri, layer.name(), "memory")
        prov = expanded_layer.dataProvider()
        prov.addAttributes(fields)
        expanded_layer.updateFields()

        features = []
        for feat in layer.getFeatures():
            new_feat = QgsFeature(expanded_layer.fields())
            new_feat.setGeometry(feat.geometry())
            
            # Transfer old attributes
            for field in layer.fields():
                new_feat[field.name()] = feat[field.name()]
                
            # Expand html table attributes
            desc = feat["description"]
            if desc:
                attrs = parse_kml_html_table(str(desc))
                for k, v in attrs.items():
                    new_feat[k] = v
            features.append(new_feat)

        prov.addFeatures(features)
        expanded_layer.updateExtents()
        return expanded_layer

    def _sanitize_column_name(self, value: str) -> str:
        text = re.sub(r"\W+", "_", str(value).strip(), flags=re.UNICODE)
        return text.strip("_").upper() or "LAYER"
