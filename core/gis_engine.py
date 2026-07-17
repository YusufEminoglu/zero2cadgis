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

from osgeo import ogr, osr, gdal
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsFeature,
    QgsField,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsVectorFileWriter,
    QgsFields,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtXml import QDomDocument

from .qgis_compat import add_features_or_raise, memory_geometry_type_name


MAX_KML_XML_BYTES = 64 * 1024 * 1024


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
            label_match = re.match(
                r"<(b|strong)>(.*?)</\1>\s*:?\s*(.*)", li, re.IGNORECASE)
            if label_match:
                key = re.sub('<[^<]+?>', '', label_match.group(2)).strip()
                val = re.sub('<[^<]+?>', '', label_match.group(3)).strip()
                clean_key = re.sub(r'\W+', '_', key).lower().strip("_")
                if clean_key and len(clean_key) < 64:
                    attributes[clean_key] = val

    return attributes


def _get_geom_type_str(geom) -> str:
    """Helper to detect memory layer compatible geometry type string from QgsGeometry."""
    if not geom or geom.isEmpty():
        return "NoGeometry"

    t = geom.type()
    try:
        t_val = int(t)
    except (TypeError, ValueError):
        t_val = getattr(t, "value", None)
        if t_val is None:
            t_str = str(t).lower()
            if "point" in t_str:
                t_val = 0
            elif "line" in t_str:
                t_val = 1
            elif "polygon" in t_str:
                t_val = 2
            else:
                t_val = 3

    wkb = geom.wkbType()
    is_multi = False
    try:
        is_multi = QgsWkbTypes.isMultiType(wkb)
    except Exception:
        is_multi = False

    if t_val == 0:
        return "MultiPoint" if is_multi else "Point"
    elif t_val == 1:
        return "MultiLineString" if is_multi else "LineString"
    elif t_val == 2:
        return "MultiPolygon" if is_multi else "Polygon"

    return "NoGeometry"


class GisConverterEngine:
    """Core GIS conversion service with HTML parser and GroundOverlay extraction."""

    def __init__(self, source_path: str, target_gpkg: str,
                 target_crs: QgsCoordinateReferenceSystem):
        self.source_path = source_path
        self.target_gpkg = target_gpkg
        self.target_crs = target_crs
        self.temp_dirs = []
        self.last_warnings: list[str] = []

    def cleanup(self):
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def extract_kmz(self) -> str:
        """Extracts KMZ zip archive and returns the path to doc.kml."""
        temp_dir = tempfile.mkdtemp(prefix="gis_kmz_")
        self.temp_dirs.append(temp_dir)

        with zipfile.ZipFile(self.source_path, 'r') as zip_ref:
            kml_files = [
                n for n in zip_ref.namelist() if n.lower().endswith(".kml")]
            if not kml_files:
                raise ValueError("KML file not found in the KMZ package.")
            zip_ref.extractall(temp_dir)
            return os.path.join(temp_dir, kml_files[0])

    def convert(
            self,
            is_kmz: bool = False,
            html_expansion: bool = True) -> list[QgsVectorLayer]:
        """Converts GIS layers to GPKG and returns list of loaded vector layers."""
        src = self.source_path
        if is_kmz:
            src = self.extract_kmz()

        # Open source OGR dataset
        from osgeo import ogr
        ogr_ds = ogr.Open(src)
        if ogr_ds is None:
            if src.lower().endswith(".mdb"):
                raise ValueError(
                    f"Unable to open source dataset with GDAL/OGR provider: {src}\n\n"
                    "Note: Reading ArcGIS Personal Geodatabases (.mdb) requires the 64-bit "
                    "Microsoft Access Database Engine (ODBC driver) to be installed on Windows. "
                    "Make sure it matches your QGIS bitness (usually 64-bit)."
                )
            raise ValueError(
                f"Unable to open source dataset with GDAL/OGR provider: {src}")

        layer_names = []
        for i in range(ogr_ds.GetLayerCount()):
            layer_names.append(ogr_ds.GetLayerByIndex(i).GetName())
        ogr_ds = None

        if not layer_names:
            raise ValueError(
                "No layers discovered inside the source GIS dataset.")

        # Re-create target GPKG
        if os.path.exists(self.target_gpkg):
            try:
                os.remove(self.target_gpkg)
            except OSError:
                pass

        loaded_layers = []
        transform_context = QgsProject.instance().transformContext()
        wrote_any = False

        for layer_name in layer_names:
            uri = f"{src}|layername={layer_name}"
            vlayer = QgsVectorLayer(uri, layer_name, "ogr")
            if not vlayer.isValid():
                continue

            processed_layer = vlayer
            if html_expansion and "description" in [
                    f.name() for f in vlayer.fields()]:
                processed_layer = self._expand_html_descriptions(vlayer)

            # Define writer options
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = self._sanitize_column_name(layer_name)
            options.actionOnExistingFile = (
                QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                if wrote_any
                else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
            )

            if processed_layer.crs() != self.target_crs:
                options.ct = QgsCoordinateTransform(
                    processed_layer.crs(), self.target_crs, QgsProject.instance())

            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                processed_layer,
                self.target_gpkg,
                transform_context,
                options
            )
            if err != QgsVectorFileWriter.WriterError.NoError:
                raise ValueError(
                    f"Failed writing layer '{layer_name}' to GPKG: {err_msg}")
            wrote_any = True

            gpkg_uri = f"{self.target_gpkg}|layername={options.layerName}"
            gpkg_layer = QgsVectorLayer(gpkg_uri, layer_name, "ogr")
            if gpkg_layer.isValid():
                loaded_layers.append(gpkg_layer)

        return loaded_layers

    def extract_ground_overlays(
            self, is_kmz: bool = False) -> list[QgsRasterLayer]:
        """Discovers GroundOverlay elements from KML/KMZ, georeferences images as GeoTiff layers.
        Feyz taken from kmltools.
        """
        loaded_rasters = []
        self.last_warnings = []
        src = self.source_path
        extracted_dir = None

        if is_kmz:
            extracted_dir = tempfile.mkdtemp(prefix="kmz_raster_")
            self.temp_dirs.append(extracted_dir)
            with zipfile.ZipFile(self.source_path, 'r') as zip_ref:
                kml_files = [
                    n for n in zip_ref.namelist() if n.lower().endswith(".kml")]
                if not kml_files:
                    self.last_warnings.append(
                        "No KML document was found inside the KMZ package.")
                    return loaded_rasters
                zip_ref.extractall(extracted_dir)
                src = os.path.join(extracted_dir, kml_files[0])

        if not os.path.exists(src):
            return loaded_rasters

        try:
            root = self._read_kml_dom(src)
            overlays = self._dom_descendants(root, "GroundOverlay")

            for overlay in overlays:
                name = self._dom_child_text(overlay, "name") or "GroundOverlay"
                image_ref = self._dom_child_text(
                    overlay, "href", recursive=True)
                if not image_ref:
                    continue

                # Locate relative image file
                base_dir = os.path.dirname(src)
                image_path = os.path.join(base_dir, image_ref)
                if not os.path.exists(image_path):
                    # Check in root if relative path contains directories
                    image_path = os.path.join(
                        base_dir, os.path.basename(image_ref))
                    if not os.path.exists(image_path):
                        continue

                latlonbox = self._dom_child(
                    overlay, "LatLonBox", recursive=True)
                if latlonbox is None:
                    continue

                north = float(self._dom_child_text(latlonbox, "north"))
                south = float(self._dom_child_text(latlonbox, "south"))
                east = float(self._dom_child_text(latlonbox, "east"))
                west = float(self._dom_child_text(latlonbox, "west"))

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
                if dst_ds is None:
                    self.last_warnings.append(
                        f"Could not create georeferenced raster for {image_ref}.")
                    src_ds = None
                    continue

                # Apply geotransform coordinates
                # [West limits, pixel width, rotationX, North limits, rotationY, -pixel height]
                dst_ds.SetGeoTransform(
                    [west, pixel_width, 0.0, north, 0.0, -pixel_height])

                # Set projection reference
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(4326)  # KML default
                dst_ds.SetProjection(srs.ExportToWkt())

                dst_ds = None
                src_ds = None

                # Load as QGIS Raster Layer
                raster_layer = QgsRasterLayer(output_tiff, name)
                if raster_layer.isValid():
                    loaded_rasters.append(raster_layer)

        except Exception as exc:
            self.last_warnings.append(
                f"GroundOverlay extraction skipped: {exc}")

        return loaded_rasters

    def _read_kml_dom(self, path: str):
        with open(path, "rb") as handle:
            raw = handle.read(MAX_KML_XML_BYTES + 1)

        if len(raw) > MAX_KML_XML_BYTES:
            raise ValueError(
                "KML document is too large for GroundOverlay scan.")
        if b"<!DOCTYPE" in raw.upper():
            raise ValueError(
                "KML documents with DOCTYPE declarations are not supported.")

        document = QDomDocument()
        result = document.setContent(raw.decode("utf-8-sig", errors="replace"))
        ok = result[0] if isinstance(result, tuple) else bool(result)
        if not ok:
            raise ValueError("KML document could not be parsed.")
        return document.documentElement()

    def _dom_descendants(self, node, local_name: str):
        matches = []
        child = node.firstChild()
        while not child.isNull():
            if child.isElement():
                element = child.toElement()
                if self._dom_local_name(element) == local_name:
                    matches.append(element)
                matches.extend(self._dom_descendants(element, local_name))
            child = child.nextSibling()
        return matches

    def _dom_child(self, node, local_name: str, recursive: bool = False):
        child = node.firstChild()
        while not child.isNull():
            if child.isElement():
                element = child.toElement()
                if self._dom_local_name(element) == local_name:
                    return element
                if recursive:
                    found = self._dom_child(
                        element, local_name, recursive=True)
                    if found is not None:
                        return found
            child = child.nextSibling()
        return None

    def _dom_child_text(
            self,
            node,
            local_name: str,
            recursive: bool = False) -> str:
        child = self._dom_child(node, local_name, recursive=recursive)
        if child is None:
            return ""
        return child.text().strip()

    def _dom_local_name(self, element) -> str:
        local_name = element.localName()
        if local_name:
            return local_name
        return element.tagName().split(":")[-1]

    @staticmethod
    def export_layer_to_gis(
            layer: QgsVectorLayer,
            output_path: str,
            format_name: str) -> bool:
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

    def _expand_html_descriptions(
            self, layer: QgsVectorLayer) -> QgsVectorLayer:
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

        geom_type_str = memory_geometry_type_name(layer)

        uri = f"{geom_type_str}?crs={layer.crs().authid()}"
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

        add_features_or_raise(
            expanded_layer, features, "KML attribute expansion")
        return expanded_layer

    def _sanitize_column_name(self, value: str) -> str:
        text = re.sub(r"\W+", "_", str(value).strip(), flags=re.UNICODE)
        return text.strip("_").upper() or "LAYER"

    def convert_to_memory(
            self,
            is_kmz: bool = False,
            html_expansion: bool = True) -> list[QgsVectorLayer]:
        """Converts GIS layers directly to memory layers without writing a GPKG file."""
        src = self.source_path
        if is_kmz:
            src = self.extract_kmz()

        # Open source OGR dataset
        ogr_ds = ogr.Open(src)
        if ogr_ds is None:
            if src.lower().endswith(".mdb"):
                raise ValueError(
                    f"Unable to open source dataset with GDAL/OGR provider: {src}\n\n"
                    "Note: Reading ArcGIS Personal Geodatabases (.mdb) requires the 64-bit "
                    "Microsoft Access Database Engine (ODBC driver) to be installed on Windows. "
                    "Make sure it matches your QGIS bitness (usually 64-bit)."
                )
            raise ValueError(
                f"Unable to open source dataset with GDAL/OGR provider: {src}")

        layer_names = []
        for i in range(ogr_ds.GetLayerCount()):
            layer_names.append(ogr_ds.GetLayerByIndex(i).GetName())
        ogr_ds = None

        if not layer_names:
            raise ValueError(
                "No layers discovered inside the source GIS dataset.")

        loaded_layers = []
        for layer_name in layer_names:
            uri = f"{src}|layername={layer_name}"
            vlayer = QgsVectorLayer(uri, layer_name, "ogr")
            if not vlayer.isValid():
                continue

            processed_layer = vlayer
            if html_expansion and "description" in [
                    f.name() for f in vlayer.fields()]:
                processed_layer = self._expand_html_descriptions(vlayer)

            # Group features by geometry type to support layers with mixed geometry types (e.g. DXF layers)
            default_geom_type = memory_geometry_type_name(processed_layer)
            features_by_type = {}

            transform = None
            if processed_layer.crs() != self.target_crs:
                transform = QgsCoordinateTransform(
                    processed_layer.crs(), self.target_crs, QgsProject.instance())

            for feat in processed_layer.getFeatures():
                geom = feat.geometry()
                if geom and not geom.isEmpty() and transform:
                    geom.transform(transform)

                geom_type_str = _get_geom_type_str(geom)
                if geom_type_str == "NoGeometry":
                    geom_type_str = default_geom_type

                # Store geometry and original feature for later reconstruction
                features_by_type.setdefault(geom_type_str, []).append((geom, feat))

            if not features_by_type:
                features_by_type[default_geom_type] = []

            for geom_type_str, type_data in sorted(features_by_type.items()):
                mem_uri = f"{geom_type_str}?crs={self.target_crs.authid()}"
                mem_layer_name = (
                    layer_name
                    if len(features_by_type) == 1
                    else f"{layer_name}_{geom_type_str}"
                )
                mem_layer = QgsVectorLayer(mem_uri, mem_layer_name, "memory")
                prov = mem_layer.dataProvider()
                prov.addAttributes(processed_layer.fields())
                mem_layer.updateFields()

                # Reconstruct features with target memory layer's fields
                features = []
                for geom, original_feat in type_data:
                    new_feat = QgsFeature(mem_layer.fields())
                    new_feat.setGeometry(geom)
                    new_feat.setAttributes(original_feat.attributes())
                    features.append(new_feat)

                add_features_or_raise(
                    mem_layer, features, "GIS scratch layer clone")
                loaded_layers.append(mem_layer)

        return loaded_layers
