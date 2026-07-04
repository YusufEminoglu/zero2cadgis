# -*- coding: utf-8 -*-
"""gis_engine — Advanced GIS converter and exporter engine.
Handles KML, KMZ, DGN, and GDB database conversions to GPKG.
Includes HTML balloon description parsing and KML GroundOverlay Georeferencing.
"""
from __future__ import annotations

import os
import re
import zipfile
import tempfile
import shutil
import xml.etree.ElementTree as ET
from typing import Generator

from osgeo import ogr, osr, gdal
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
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
    """Parses KML balloon descriptions (HTML tables) into structured attributes."""
    attributes = {}
    if not html_content:
        return attributes

    html = html_content.replace("\r", "").replace("\n", " ")
    
    # tr td lookup
    tr_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.IGNORECASE)
    for tr in tr_matches:
        td_matches = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.IGNORECASE)
        if len(td_matches) >= 2:
            key = re.sub('<[^<]+?>', '', td_matches[0]).strip()
            val = re.sub('<[^<]+?>', '', td_matches[1]).strip()
            clean_key = re.sub(r'\W+', '_', key).lower().strip("_")
            if clean_key and len(clean_key) < 64:
                attributes[clean_key] = val

    if not attributes:
        li_matches = re.findall(r"<li[^>]*>(.*?)</li>", html, re.IGNORECASE)
        for li in li_matches:
            label_match = re.match(r"<(b|strong)>(.*?)</\1>\s*:?\s*(.*)", li, re.IGNORECASE)
            if label_match:
                key = re.sub('<[^<]+?>', '', label_match.group(2)).strip()
                val = re.sub('<[^<]+?>', '', label_match.group(3)).strip()
                clean_key = re.sub(r'\W+', '_', key).lower().strip("_")
                if clean_key and len(clean_key) < 64:
                    attributes[clean_key] = val

    return attributes


class GisConverterEngine:
    """Core GIS conversion service with HTML parser and GroundOverlay extraction."""
    
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
        """Converts GIS layers to GPKG and returns list of loaded vector layers."""
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
            uri = f"{src}|layername={layer_name}"
            vlayer = QgsVectorLayer(uri, layer_name, "ogr")
            if not vlayer.isValid():
                continue

            processed_layer = vlayer
            if html_expansion and "description" in [f.name() for f in vlayer.fields()]:
                processed_layer = self._expand_html_descriptions(vlayer)

            # Define writer options
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = self._sanitize_column_name(layer_name)
            options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
            options.overrideGeometryType = processed_layer.geometryType()
            
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

            gpkg_uri = f"{self.target_gpkg}|layername={options.layerName}"
            gpkg_layer = QgsVectorLayer(gpkg_uri, layer_name, "ogr")
            if gpkg_layer.isValid():
                loaded_layers.append(gpkg_layer)

        return loaded_layers

    def extract_ground_overlays(self, is_kmz: bool = False) -> list[QgsRasterLayer]:
        """Discovers GroundOverlay elements from KML/KMZ, georeferences images as GeoTiff layers.
        Feyz taken from kmltools.
        """
        loaded_rasters = []
        src = self.source_path
        extracted_dir = None
        
        if is_kmz:
            extracted_dir = tempfile.mkdtemp(prefix="kmz_raster_")
            self.temp_dirs.append(extracted_dir)
            with zipfile.ZipFile(self.source_path, 'r') as zip_ref:
                kml_files = [n for n in zip_ref.namelist() if n.lower().endswith(".kml")]
                if not kml_files:
                    return loaded_rasters
                zip_ref.extractall(extracted_dir)
                src = os.path.join(extracted_dir, kml_files[0])

        if not os.path.exists(src):
            return loaded_rasters

        try:
            # Parse KML xml directly to search for GroundOverlay
            tree = ET.parse(src)
            root = tree.getroot()
            
            # KML namespace handles
            ns = {"kml": "http://www.opengis.net/kml/2.2"}
            overlays = root.findall(".//kml:GroundOverlay", ns)
            if not overlays:
                # Try parsing namespace-less elements
                overlays = root.findall(".//GroundOverlay")

            for overlay in overlays:
                name_el = overlay.find("kml:name", ns) or overlay.find("name")
                name = name_el.text if name_el is not None else "GroundOverlay"
                
                href_el = overlay.find(".//kml:href", ns) or overlay.find(".//href")
                if href_el is None:
                    continue
                image_ref = href_el.text
                
                # Locate relative image file
                base_dir = os.path.dirname(src)
                image_path = os.path.join(base_dir, image_ref)
                if not os.path.exists(image_path):
                    # Check in root if relative path contains directories
                    image_path = os.path.join(base_dir, os.path.basename(image_ref))
                    if not os.path.exists(image_path):
                        continue

                # Locate LatLonBox
                latlonbox = overlay.find("kml:LatLonBox", ns) or overlay.find("LatLonBox")
                if latlonbox is None:
                    continue

                north = float((latlonbox.find("kml:north", ns) or latlonbox.find("north")).text)
                south = float((latlonbox.find("kml:south", ns) or latlonbox.find("south")).text)
                east = float((latlonbox.find("kml:east", ns) or latlonbox.find("east")).text)
                west = float((latlonbox.find("kml:west", ns) or latlonbox.find("west")).text)

                # Use GDAL to georeference and copy image to GeoTiff
                output_tiff = os.path.splitext(image_path)[0] + "_georef.tif"
                
                src_ds = gdal.Open(image_path)
                if src_ds is None:
                    continue
                
                width = src_ds.RasterXSize
                height = src_ds.RasterYSize
                
                # Calculate pixel resolution sizes
                pixel_width = (east - west) / width
                pixel_height = (north - south) / height
                
                # Create destination georeferenced GeoTiff
                driver = gdal.GetDriverByName("GTiff")
                dst_ds = driver.CreateCopy(output_tiff, src_ds)
                
                # Apply geotransform coordinates
                # [West limits, pixel width, rotationX, North limits, rotationY, -pixel height]
                dst_ds.SetGeoTransform([west, pixel_width, 0.0, north, 0.0, -pixel_height])
                
                # Set projection reference
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(4326) # KML default
                dst_ds.SetProjection(srs.ExportToWkt())
                
                dst_ds = None
                src_ds = None

                # Load as QGIS Raster Layer
                raster_layer = QgsRasterLayer(output_tiff, name)
                if raster_layer.isValid():
                    loaded_rasters.append(raster_layer)

        except Exception:
            pass

        return loaded_rasters

    @staticmethod
    def export_layer_to_gis(layer: QgsVectorLayer, output_path: str, format_name: str) -> bool:
        """Exports any vector layer to KML or KMZ format."""
        transform_context = QgsProject.instance().transformContext()
        options = QgsVectorFileWriter.SaveVectorOptions()
        
        if format_name.upper() == "KML":
            options.driverName = "KML"
            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_path, transform_context, options
            )
            return err == QgsVectorFileWriter.WriterError.NoError
            
        elif format_name.upper() == "KMZ":
            # Write to a temporary KML first, then package as KMZ zip
            temp_dir = tempfile.mkdtemp(prefix="kmz_export_")
            temp_kml = os.path.join(temp_dir, "doc.kml")
            options.driverName = "KML"
            
            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, temp_kml, transform_context, options
            )
            
            if err == QgsVectorFileWriter.WriterError.NoError:
                # Zip to KMZ
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(temp_kml, "doc.kml")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return True
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False

        return False

    def _expand_html_descriptions(self, layer: QgsVectorLayer) -> QgsVectorLayer:
        new_field_definitions = {}
        for feat in layer.getFeatures():
            desc = feat["description"]
            if desc:
                attrs = parse_kml_html_table(str(desc))
                for k in attrs.keys():
                    new_field_definitions[k] = QVariant.String

        fields = QgsFields()
        for field in layer.fields():
            fields.append(field)
        for k, vtype in sorted(new_field_definitions.items()):
            if k not in [f.name() for f in layer.fields()]:
                fields.append(QgsField(k, vtype))

        uri = f"{layer.geometryType().name()}?crs={layer.crs().authid()}"
        expanded_layer = QgsVectorLayer(uri, layer.name(), "memory")
        prov = expanded_layer.dataProvider()
        prov.addAttributes(fields)
        expanded_layer.updateFields()

        features = []
        for feat in layer.getFeatures():
            new_feat = QgsFeature(expanded_layer.fields())
            new_feat.setGeometry(feat.geometry())
            
            for field in layer.fields():
                new_feat[field.name()] = feat[field.name()]
                
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
