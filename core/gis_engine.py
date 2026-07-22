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
from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtXml import QDomDocument

from .qgis_compat import add_features_or_raise, memory_geometry_type_name
from .csv_sniffer import (
    CsvGeometryProfile,
    build_delimitedtext_uri,
    is_delimited_dataset,
    sniff_delimited_dataset,
)
from . import ogr_catalog_cache

# CAD source families whose OGR "entities"/"elements" layer carries an
# embedded per-CAD-layer field (DXF ``Layer`` name, DGN ``Level`` number).
CAD_LAYER_FIELDS = ("Layer", "Level")


MAX_KML_XML_BYTES = 64 * 1024 * 1024


class SourceLayerInfo:
    """Lightweight description of one discoverable source layer.

    ``name`` is the display label; ``key`` is the value used to select the
    layer for conversion (the OGR layer name, or a CAD-layer value when a DXF
    or DGN source is split by its ``Layer`` / ``Level`` field). They are equal
    except for the CAD split, where the display may differ (e.g. "(no layer)"
    for an empty CAD-layer value whose key is the empty string).
    """

    __slots__ = ("name", "geometry", "feature_count", "key")

    def __init__(self, name: str, geometry: str, feature_count: int,
                 key: str | None = None):
        self.name = name
        self.geometry = geometry
        self.feature_count = feature_count
        self.key = name if key is None else key


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
                 target_crs: QgsCoordinateReferenceSystem,
                 csv_profile: CsvGeometryProfile | None = None,
                 csv_source_crs: str = ""):
        self.source_path = source_path
        self.target_gpkg = target_gpkg
        self.target_crs = target_crs
        self.temp_dirs = []
        self.last_warnings: list[str] = []
        self.csv_profile = csv_profile
        self.csv_source_crs = csv_source_crs
        self._resolved_src: str | None = None
        self.catalog_from_cache = False
        # When set (to "Layer"/"Level"), the single CAD entities layer is
        # split into one output layer per distinct CAD-layer value.
        self.cad_split_field: str = ""

    # ── source resolution & discovery ────────────────────────────────

    @property
    def is_delimited(self) -> bool:
        return is_delimited_dataset(self.source_path)

    def _resolve_source(self, is_kmz: bool) -> str:
        """Return the readable source path, extracting KMZ only once."""
        if self._resolved_src is None:
            self._resolved_src = (
                self.extract_kmz() if is_kmz else self.source_path)
        return self._resolved_src

    def _ensure_csv_profile(self) -> CsvGeometryProfile:
        if self.csv_profile is None:
            self.csv_profile = sniff_delimited_dataset(self.source_path)
        return self.csv_profile

    def discover_layers(self, is_kmz: bool = False,
                         use_cache: bool = True) -> list[SourceLayerInfo]:
        """List source layers with geometry type and feature counts.

        Multi-layer OGR sources are cached by a content fingerprint (see
        :mod:`ogr_catalog_cache`), so reopening an unchanged Geodatabase or
        database returns its catalog without reopening the driver.
        """
        if self.is_delimited:
            profile = self._ensure_csv_profile()
            stem = os.path.splitext(os.path.basename(self.source_path))[0]
            geometry = ("Point" if profile.has_point_geometry
                        else "WKT" if profile.has_wkt_geometry
                        else "Table")
            return [SourceLayerInfo(stem, geometry, profile.row_count)]

        if use_cache:
            cached = ogr_catalog_cache.load(self.source_path)
            if cached is not None:
                self.catalog_from_cache = True
                return [SourceLayerInfo(
                    row.get("name", ""), row.get("geometry", "Unknown"),
                    int(row.get("feature_count", -1))) for row in cached]

        infos = []
        for prefix, src in self._ogr_sources(is_kmz):
            ogr_ds = ogr.Open(src)
            if ogr_ds is None:
                raise ValueError(self._open_error_message(src))
            for i in range(ogr_ds.GetLayerCount()):
                ogr_layer = ogr_ds.GetLayerByIndex(i)
                try:
                    geometry = ogr.GeometryTypeToName(ogr_layer.GetGeomType())
                except Exception:
                    geometry = "Unknown"
                try:
                    count = ogr_layer.GetFeatureCount()
                except Exception:
                    count = -1
                infos.append(SourceLayerInfo(
                    f"{prefix}{ogr_layer.GetName()}", geometry, count))
            ogr_ds = None

        if use_cache:
            ogr_catalog_cache.save(self.source_path, [
                {"name": i.name, "geometry": i.geometry,
                 "feature_count": i.feature_count} for i in infos])
        return infos

    @staticmethod
    def _ogr_geom_family(geom_name: str) -> str:
        name = (geom_name or "").upper()
        if "POINT" in name:
            return "Point"
        if "POLYGON" in name:
            return "Polygon"
        if "LINE" in name or "CURVE" in name:
            return "LineString"
        return "Other"

    def discover_cad_layers(
            self, is_kmz: bool = False) -> tuple[list[SourceLayerInfo], str]:
        """Group a CAD entities layer by its embedded CAD-layer field.

        DXF and DGN files expose a single OGR layer whose features each carry
        a CAD-layer name (DXF ``Layer``) or level number (DGN ``Level``). This
        returns one :class:`SourceLayerInfo` per distinct CAD-layer value,
        with its geometry families and feature count, plus the field name that
        was used (empty string if the source has no such field). The field is
        remembered so a later :meth:`convert` splits by it.
        """
        src = self._resolve_source(is_kmz)
        ogr_ds = ogr.Open(src)
        if ogr_ds is None:
            raise ValueError(self._open_error_message(src))
        if ogr_ds.GetLayerCount() == 0:
            ogr_ds = None
            return [], ""

        layer = ogr_ds.GetLayerByIndex(0)
        defn = layer.GetLayerDefn()
        field_names = [defn.GetFieldDefn(i).GetName()
                       for i in range(defn.GetFieldCount())]
        field = next((f for f in CAD_LAYER_FIELDS if f in field_names), "")
        if not field:
            ogr_ds = None
            return [], ""

        groups: dict[str, dict] = {}
        layer.ResetReading()
        for feat in layer:
            value = feat.GetField(field)
            key = "" if value is None else str(value)
            geom = feat.GetGeometryRef()
            gname = geom.GetGeometryName() if geom else "NONE"
            rec = groups.setdefault(key, {"count": 0, "families": set()})
            rec["count"] += 1
            rec["families"].add(self._ogr_geom_family(gname))
        ogr_ds = None

        self.cad_split_field = field
        infos = []
        for key in sorted(groups):
            rec = groups[key]
            infos.append(SourceLayerInfo(
                key or "(no layer)",
                "/".join(sorted(rec["families"])),
                rec["count"],
                key=key))
        return infos, field

    def _iter_cad_layers(self, src: str,
                         selected_values: list[str] | None):
        """Yield ``(cad_layer_value, QgsVectorLayer)`` per CAD-layer subset."""
        field = self.cad_split_field
        ogr_ds = ogr.Open(src)
        if ogr_ds is None or ogr_ds.GetLayerCount() == 0:
            raise ValueError(self._open_error_message(src))
        base_layer = ogr_ds.GetLayerByIndex(0)
        entities_name = base_layer.GetName()
        defn = base_layer.GetLayerDefn()
        is_numeric = False
        for i in range(defn.GetFieldCount()):
            fd = defn.GetFieldDefn(i)
            if fd.GetName() == field:
                is_numeric = fd.GetType() in (
                    ogr.OFTInteger, ogr.OFTInteger64, ogr.OFTReal)
                break
        ogr_ds = None

        values = selected_values if selected_values is not None else [None]
        for value in values:
            uri = f"{src}|layername={entities_name}"
            display = str(value) if value not in (None, "") else "NO_LAYER"
            vlayer = QgsVectorLayer(uri, display, "ogr")
            if not vlayer.isValid():
                self.last_warnings.append(
                    f"CAD layer '{display}' could not be read and was skipped.")
                continue
            if value is None:
                pass
            elif value == "":
                vlayer.setSubsetString(
                    f'"{field}" IS NULL')
            elif is_numeric:
                vlayer.setSubsetString(f'"{field}" = {value}')
            else:
                escaped = str(value).replace("'", "''")
                vlayer.setSubsetString(f"\"{field}\" = '{escaped}'")
            yield display, vlayer

    def _open_error_message(self, src: str) -> str:
        if src.lower().endswith(".mdb"):
            return (
                f"Unable to open source dataset with GDAL/OGR provider: {src}\n\n"
                "Note: Reading ArcGIS Personal Geodatabases (.mdb) requires the 64-bit "
                "Microsoft Access Database Engine (ODBC driver) to be installed on Windows. "
                "Make sure it matches your QGIS bitness (usually 64-bit)."
            )
        return f"Unable to open source dataset with GDAL/OGR provider: {src}"

    def _iter_source_layers(self, is_kmz: bool,
                            selected_layers: list[str] | None):
        """Yield ``(layer_name, QgsVectorLayer)`` for each requested layer."""
        if self.is_delimited:
            profile = self._ensure_csv_profile()
            stem = os.path.splitext(os.path.basename(self.source_path))[0]
            if selected_layers is not None and stem not in selected_layers:
                return
            uri = build_delimitedtext_uri(
                self.source_path, profile, self.csv_source_crs)
            vlayer = QgsVectorLayer(uri, stem, "delimitedtext")
            if not vlayer.isValid():
                raise ValueError(
                    "Could not read the delimited text dataset. Check the "
                    "detected delimiter and geometry columns.")
            yield stem, vlayer
            return

        if self.cad_split_field:
            yield from self._iter_cad_layers(
                self._resolve_source(is_kmz), selected_layers)
            return

        found_any = False
        for prefix, src in self._ogr_sources(is_kmz):
            ogr_ds = ogr.Open(src)
            if ogr_ds is None:
                raise ValueError(self._open_error_message(src))
            layer_names = [ogr_ds.GetLayerByIndex(i).GetName()
                           for i in range(ogr_ds.GetLayerCount())]
            ogr_ds = None

            for layer_name in layer_names:
                found_any = True
                display = f"{prefix}{layer_name}"
                if selected_layers is not None \
                        and display not in selected_layers:
                    continue
                uri = f"{src}|layername={layer_name}"
                vlayer = QgsVectorLayer(uri, display, "ogr")
                if not vlayer.isValid():
                    self.last_warnings.append(
                        f"Layer '{display}' could not be read and was skipped.")
                    continue
                yield display, vlayer

        if not found_any:
            raise ValueError(
                "No layers discovered inside the source GIS dataset.")

    def cleanup(self):
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def extract_kmz(self) -> str:
        """Extract a KMZ archive and return the primary KML path.

        ``doc.kml`` is the KMZ convention for the main document, so it is
        preferred; otherwise the first KML in sorted order is used. All KML
        documents are extracted, so :meth:`_kml_docs` can enumerate the rest.
        """
        temp_dir = tempfile.mkdtemp(prefix="gis_kmz_")
        self.temp_dirs.append(temp_dir)

        with zipfile.ZipFile(self.source_path, 'r') as zip_ref:
            kml_files = [
                n for n in zip_ref.namelist() if n.lower().endswith(".kml")]
            if not kml_files:
                raise ValueError("KML file not found in the KMZ package.")
            zip_ref.extractall(temp_dir)

        doc = next((n for n in kml_files
                    if os.path.basename(n).lower() == "doc.kml"), None)
        primary = doc if doc is not None else sorted(kml_files)[0]
        return os.path.join(temp_dir, primary)

    def _kml_docs(self, is_kmz: bool) -> list[str]:
        """Return every KML document to read for the current source.

        For a plain KML this is just the file; for a KMZ it is every extracted
        ``.kml`` with the primary document first, so additional KML documents
        inside a multi-document KMZ are not silently dropped.
        """
        primary = self._resolve_source(is_kmz)
        if not is_kmz:
            return [primary]
        folder = os.path.dirname(primary)
        docs = []
        for root, _dirs, files in os.walk(folder):
            for name in sorted(files):
                if name.lower().endswith(".kml"):
                    docs.append(os.path.join(root, name))
        ordered = [primary] + [d for d in docs if d != primary]
        return ordered or [primary]

    def _ogr_sources(self, is_kmz: bool) -> list[tuple[str, str]]:
        """Yield ``(name_prefix, dataset_path)`` for each OGR source to open.

        A single dataset yields one entry with an empty prefix. A
        multi-document KMZ yields one entry per KML document, each prefixed
        with its document stem so layers from different documents stay
        distinct.
        """
        if is_kmz:
            docs = self._kml_docs(is_kmz)
            multi = len(docs) > 1
            sources = []
            for path in docs:
                stem = os.path.splitext(os.path.basename(path))[0]
                prefix = f"{stem}_" if multi else ""
                sources.append((prefix, path))
            return sources
        return [("", self._resolve_source(is_kmz))]

    def convert(
            self,
            is_kmz: bool = False,
            html_expansion: bool = True,
            selected_layers: list[str] | None = None,
            progress_cb=None) -> list[QgsVectorLayer]:
        """Converts GIS layers to GPKG and returns list of loaded vector layers."""
        # Re-create target GPKG
        if os.path.exists(self.target_gpkg):
            try:
                os.remove(self.target_gpkg)
            except OSError:
                pass

        loaded_layers = []
        transform_context = QgsProject.instance().transformContext()
        wrote_any = False

        for layer_name, vlayer in self._iter_source_layers(
                is_kmz, selected_layers):
            if progress_cb:
                progress_cb(layer_name)

            processed_layer = vlayer
            if html_expansion and "description" in [
                    f.name() for f in vlayer.fields()]:
                processed_layer = self._expand_html_descriptions(vlayer)

            # CAD layer subsets can mix geometry types; a GeoPackage layer
            # holds one geometry type, so split them before writing.
            if self.cad_split_field:
                wrote_any = self._write_cad_layer_gpkg(
                    processed_layer, layer_name, wrote_any,
                    transform_context, loaded_layers)
                continue

            # Define writer options
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = self._sanitize_column_name(layer_name)

            # GML/GeoJSON sources may carry a non-integer "fid" attribute;
            # GPKG reserves fid for its integer primary key, so move the
            # primary key to another column in that case.
            fid_index = processed_layer.fields().lookupField("fid")
            if fid_index >= 0:
                fid_type = processed_layer.fields()[fid_index] \
                    .typeName().lower()
                if fid_type not in (
                        "integer", "integer64", "int", "int2", "int4",
                        "int8", "int16", "int32", "int64", "long",
                        "longlong"):
                    options.layerOptions = ["FID=cadgis_fid"]
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

        if not wrote_any:
            raise ValueError(
                "No readable layers were selected for conversion.")
        return loaded_layers

    def _write_cad_layer_gpkg(self, processed_layer, layer_name, wrote_any,
                              transform_context, loaded_layers) -> bool:
        """Write one CAD-layer subset to GPKG, split by geometry type."""
        transform = None
        src_crs = processed_layer.crs()
        if src_crs.isValid() and src_crs != self.target_crs:
            transform = QgsCoordinateTransform(
                src_crs, self.target_crs, QgsProject.instance())

        groups: dict[str, list] = {}
        for feat in processed_layer.getFeatures():
            geom = feat.geometry()
            if geom and not geom.isEmpty() and transform:
                geom.transform(transform)
            geom_type_str = _get_geom_type_str(geom)
            if geom_type_str == "NoGeometry":
                continue
            groups.setdefault(geom_type_str, []).append((geom, feat))

        for geom_type_str, type_data in sorted(groups.items()):
            mem_uri = f"{geom_type_str}?crs={self.target_crs.authid()}"
            mem_layer = QgsVectorLayer(mem_uri, layer_name, "memory")
            prov = mem_layer.dataProvider()
            prov.addAttributes(processed_layer.fields())
            mem_layer.updateFields()

            features = []
            for geom, original_feat in type_data:
                new_feat = QgsFeature(mem_layer.fields())
                new_feat.setGeometry(geom)
                new_feat.setAttributes(original_feat.attributes())
                features.append(new_feat)
            add_features_or_raise(mem_layer, features, "CAD layer split")

            base = self._sanitize_column_name(layer_name)
            gpkg_layer_name = (
                base if len(groups) == 1
                else f"{base}_{geom_type_str.upper()}")

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = gpkg_layer_name
            options.actionOnExistingFile = (
                QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                if wrote_any
                else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile
            )
            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                mem_layer, self.target_gpkg, transform_context, options)
            if err != QgsVectorFileWriter.WriterError.NoError:
                raise ValueError(
                    f"Failed writing CAD layer '{layer_name}' to GPKG: "
                    f"{err_msg}")
            wrote_any = True

            gpkg_uri = f"{self.target_gpkg}|layername={gpkg_layer_name}"
            gpkg_layer = QgsVectorLayer(gpkg_uri, gpkg_layer_name, "ogr")
            if gpkg_layer.isValid():
                loaded_layers.append(gpkg_layer)
        return wrote_any

    def load_layers_live(
            self,
            is_kmz: bool = False,
            selected_layers: list[str] | None = None,
            progress_cb=None) -> list[QgsVectorLayer]:
        """Return the selected source layers as live, zero-copy references.

        Unlike :meth:`convert` (which writes a GeoPackage) and
        :meth:`convert_to_memory` (which copies every feature into RAM), this
        hands back the source-referencing ``QgsVectorLayer`` objects directly.
        No geometry is read, copied, or reprojected, so even a multi-million
        feature Geodatabase layer becomes usable in milliseconds; QGIS reads
        features lazily from the source and reprojects on the fly using each
        layer's own CRS.
        """
        loaded_layers = []
        for layer_name, vlayer in self._iter_source_layers(
                is_kmz, selected_layers):
            if progress_cb:
                progress_cb(layer_name)
            loaded_layers.append(vlayer)

        if not loaded_layers:
            raise ValueError(
                "No readable layers were selected for live loading.")
        return loaded_layers

    def extract_ground_overlays(
            self, is_kmz: bool = False) -> list[QgsRasterLayer]:
        """Discovers GroundOverlay elements from KML/KMZ, georeferences images as GeoTiff layers.
        Feyz taken from kmltools.
        """
        loaded_rasters = []
        try:
            docs = self._kml_docs(is_kmz)
        except ValueError as exc:
            self.last_warnings.append(str(exc))
            return loaded_rasters

        for src in docs:
            if os.path.exists(src):
                self._scan_ground_overlays(src, loaded_rasters)
        return loaded_rasters

    def _scan_ground_overlays(self, src: str,
                              loaded_rasters: list) -> None:
        """Georeference every GroundOverlay in one KML document."""
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
                    new_field_definitions[k] = QMetaType.Type.QString

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
            html_expansion: bool = True,
            selected_layers: list[str] | None = None,
            progress_cb=None) -> list[QgsVectorLayer]:
        """Converts GIS layers directly to memory layers without writing a GPKG file."""
        loaded_layers = []
        for layer_name, vlayer in self._iter_source_layers(
                is_kmz, selected_layers):
            if progress_cb:
                progress_cb(layer_name)

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

        if not loaded_layers:
            raise ValueError(
                "No readable layers were selected for conversion.")
        return loaded_layers
