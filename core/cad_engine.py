# -*- coding: utf-8 -*-
"""cad_engine — CAD feature cleanup, augmentation, and styling services.
Provides vertex thinning, polyline closure tolerance, attribute augmentation, and dxf export.
"""
from __future__ import annotations

import math
from contextlib import suppress
from functools import lru_cache

with suppress(ImportError):
    from qgis.core import (
        QgsProject,
        QgsVectorLayer,
        QgsFeature,
        QgsField,
        QgsMarkerSymbol,
        QgsLineSymbol,
        QgsFillSymbol,
        QgsSingleSymbolRenderer,
        QgsPalLayerSettings,
        QgsVectorLayerSimpleLabeling,
        QgsTextFormat,
        QgsTextBufferSettings,
        QgsVectorFileWriter,
        QgsFields,
        QgsCoordinateTransform,
    )
    from qgis.PyQt.QtCore import QMetaType
    from qgis.PyQt.QtGui import QColor, QFont

from .qgis_compat import add_features_or_raise, memory_geometry_type_name
from .export_utils import (
    atomic_output,
    exported_feature_count,
    verified_export_result,
)

# Standard CAD drafting helper tokens that clutter spatial plans
NOISE_LAYER_KEYWORDS = (
    "CIZPEN", "CIZ_PEN", "PEN", "KALEM", "CIZGI_PEN", "PLOT_PEN", "COLOR_PEN",
    "GRID", "KAREYAJ", "PAFTA", "PAFTA_GRID", "PAFTA_SINIRI", "PAFTA_INDEKS",
    "PAFTA_INDEX", "PAFTA_KENAR", "PAFTA_YAZI", "PINDEX", "P_INDEX", "GRID_PINDEX",
    "PINDEX_GRID", "GRIDPINDEX", "INDEX", "KOORDINAT", "KOORD",
    "TAMPON", "TEMP", "DRAFT", "YARDIMCI", "CALISMA", "ESKI", "DENEME", "YEDEK",
    "TARAMA_CIZGI", "TARAMA", "HATCH", "HATCHES",
    "KOT", "ROPER", "POLIGON_NOKTA", "NIRENGI", "MIHENK",
    "ROL_CEPHE", "Z_ADAPARSEL_PL", "SNR_GIS", "SM_AGAC",
    "ANTET", "LEJANT", "LEGEND", "CERCEVE", "BORDER", "FRAME",
    "MUELLIF", "ONAMA", "ONAY",
)


def is_helper_or_noise_layer(layer_name: str) -> bool:
    """True if the layer represents CAD draft, pen, grid or helper entities that should be hidden by default.

    A tabaka the official MPYY catalog recognizes is never noise, whatever its
    tokens: ``SNR_PLAN_ONAMA`` contains ONAMA and ``KST_SULAK_TAMPON`` contains
    TAMPON, and hiding either would hide a legally binding plan boundary.
    """
    if not layer_name:
        return False
    return _is_noise_name(str(layer_name))


@lru_cache(maxsize=4096)
def _is_noise_name(layer_name: str) -> bool:
    from .plangml_schema import lookup_tabaka
    if lookup_tabaka(layer_name) is not None:
        return False
    upper = layer_name.strip().upper()
    tr_map = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})
    upper = upper.translate(tr_map)
    clean = upper.replace("-", "_").replace(".", "_")
    tokens = [t for t in clean.split("_") if t]

    # Prominent substring check for notorious CAD drafting noise layers
    prominent_substrings = (
        "PINDEX", "CIZPEN", "CIZ_PEN", "KAREYAJ", "PAFTA_GRID", "GRID_PINDEX",
        "PINDEX_GRID", "PAFTA_INDEX", "PAFTA_INDEKS", "CAD_DRAFT",
    )
    for sub in prominent_substrings:
        if sub in upper or sub in clean:
            return True

    for kw in NOISE_LAYER_KEYWORDS:
        if kw in tokens or kw == upper:
            return True
        if clean.startswith(f"{kw}_") or clean.endswith(f"_{kw}"):
            return True
    return False


class CadCleanupEngine:
    """Removes collinear nodes and duplicate points from CAD paths."""

    @staticmethod
    def clean_duplicates(coords: list) -> list:
        if len(coords) < 2:
            return coords
        cleaned = []
        for c in coords:
            if not cleaned:
                cleaned.append(c)
                continue
            prev = cleaned[-1]
            if abs(prev.x - c.x) < 0.0001 and abs(prev.y - c.y) < 0.0001:
                continue
            cleaned.append(c)
        return cleaned

    @staticmethod
    def simplify_collinear(coords: list) -> list:
        if len(coords) <= 3:
            return coords

        simplified = list(coords)
        removed = True
        while removed and len(simplified) > 3:
            removed = False
            for idx in range(len(simplified)):
                if idx == 0 or idx == len(simplified) - 1:
                    continue

                prev_p = simplified[idx - 1]
                curr_p = simplified[idx]
                next_p = simplified[idx + 1]

                v1x, v1y = curr_p.x - prev_p.x, curr_p.y - prev_p.y
                v2x, v2y = next_p.x - curr_p.x, next_p.y - curr_p.y

                len1 = math.sqrt(v1x * v1x + v1y * v1y)
                len2 = math.sqrt(v2x * v2x + v2y * v2y)
                if len1 < 0.0001 or len2 < 0.0001:
                    simplified.pop(idx)
                    removed = True
                    break

                cross = abs(v1x * v2y - v1y * v2x) / (len1 * len2)
                if cross <= 0.02:
                    simplified.pop(idx)
                    removed = True
                    break
        return simplified

    @staticmethod
    def close_polyline(
            coords: list,
            tolerance: float,
            force: bool = False) -> list:
        if len(coords) < 3:
            return coords

        first = coords[0]
        last = coords[-1]
        dist = math.hypot(first.x() - last.x(), first.y() - last.y())

        closed_coords = list(coords)
        if dist <= 0.0001:
            return closed_coords
        if force or dist <= tolerance:
            closed_coords.append(first)

        return closed_coords


class CadFeatureAugmenter:
    """Calculates geometric properties (area, length, centroid) to enrich CAD data."""

    @staticmethod
    def augment_layer(layer: QgsVectorLayer) -> QgsVectorLayer:
        """Enriches memory layers with computed geometric metadata columns."""
        fields = QgsFields()
        for field in layer.fields():
            fields.append(field)

        # Add new geo-statistical columns
        fields.append(QgsField("geom_len", QMetaType.Type.Double))
        fields.append(QgsField("geom_area", QMetaType.Type.Double))
        fields.append(QgsField("cent_x", QMetaType.Type.Double))
        fields.append(QgsField("cent_y", QMetaType.Type.Double))

        geom_type_str = memory_geometry_type_name(layer)

        uri = f"{geom_type_str}?crs={layer.crs().authid()}"
        enriched_layer = QgsVectorLayer(uri, layer.name(), "memory")
        prov = enriched_layer.dataProvider()
        prov.addAttributes(fields)
        enriched_layer.updateFields()

        from .qgis_compat import fix_mojibake
        features = []
        for feat in layer.getFeatures():
            geom = feat.geometry()
            new_feat = QgsFeature(enriched_layer.fields())
            new_feat.setGeometry(geom)

            # Copy original values in field order (the enriched layer starts
            # with the same fields); one list, not a by-name lookup per cell.
            values = [fix_mojibake(val) if isinstance(val, str) else val
                      for val in feat.attributes()]

            # Perform calculations
            length = 0.0
            area = 0.0
            cx = 0.0
            cy = 0.0

            if geom and not geom.isEmpty():
                length = geom.length()
                area = geom.area()
                centroid = geom.centroid()
                if centroid and not centroid.isEmpty():
                    cx = centroid.asPoint().x()
                    cy = centroid.asPoint().y()

            values.extend((round(length, 3), round(area, 3), round(cx, 6), round(cy, 6)))
            new_feat.setAttributes(values)
            features.append(new_feat)

        add_features_or_raise(
            enriched_layer, features, "Geometry metadata augmentation")
        return enriched_layer


class CadStylingEngine:
    """Translates CAD layout parameters to styled QGIS rendering."""

    @staticmethod
    def apply_argb_renderer(layer: QgsVectorLayer, geometry_type: str) -> None:
        color_rgb = None
        for feature in layer.getFeatures():
            color_str = feature["color_argb"]
            if color_str:
                try:
                    argb = int(color_str)
                    red = (argb >> 16) & 0xFF
                    green = (argb >> 8) & 0xFF
                    blue = argb & 0xFF
                    color_rgb = QColor(red, green, blue)
                    break
                except ValueError:
                    pass

        if not color_rgb:
            color_rgb = QColor(110, 110, 110)

        symbol = None
        if geometry_type == "Point":
            symbol = QgsMarkerSymbol.createSimple({
                "name": "circle",
                "color": color_rgb.name(),
                "size": "3.5",
                "outline_color": "#ffffff",
                "outline_width": "0.4"
            })
        elif geometry_type == "LineString":
            symbol = QgsLineSymbol.createSimple({
                "color": color_rgb.name(),
                "width": "0.7",
                "line_style": "solid"
            })
        elif geometry_type == "Polygon":
            symbol = QgsFillSymbol.createSimple({
                "color": f"{color_rgb.red()},{color_rgb.green()},{color_rgb.blue()},70",
                "outline_color": color_rgb.name(),
                "outline_width": "0.5"
            })

        if symbol:
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            layer.triggerRepaint()

    @staticmethod
    def apply_buffered_labels(layer: QgsVectorLayer) -> None:
        from .symbology import pick_label_field, use_drawing_text_height

        # Bind to the column that actually holds the drawing's text. Naming one
        # outright is how this silently produced blank labels once already.
        field = pick_label_field(layer) or "label"

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Segoe UI", 9))
        text_format.setColor(QColor(0, 0, 0))

        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(1.2)
        buffer.setColor(QColor(255, 255, 255))
        text_format.setBuffer(buffer)

        label_settings = QgsPalLayerSettings()
        label_settings.setFormat(text_format)
        label_settings.fieldName = field
        label_settings.isExpression = False
        label_settings.placement = QgsPalLayerSettings.Placement.OverPoint
        # The drawing's own text height (metres) when the layer carries it.
        use_drawing_text_height(label_settings, text_format, layer.fields().names())

        simple_labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(simple_labeling)
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()


class CadExportEngine:
    """Exports active vectors into DXF format."""

    @staticmethod
    def export_layer_to_dxf(
            layer: QgsVectorLayer,
            output_path: str,
            target_crs=None,
            selected_only: bool = False):
        transform_context = QgsProject.instance().transformContext()
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "DXF"
        options.skipAttributeCreation = True
        options.onlySelectedFeatures = selected_only

        source_crs = layer.crs()
        if not source_crs.isValid():
            raise ValueError(
                "The source layer has no valid CRS. Assign its source CRS "
                "before exporting so coordinates are not mislabelled.")
        effective_crs = (
            target_crs if target_crs and target_crs.isValid() else source_crs)
        if source_crs.isValid() and effective_crs.isValid() \
                and source_crs != effective_crs:
            options.ct = QgsCoordinateTransform(
                source_crs, effective_crs, QgsProject.instance())

        feature_count = exported_feature_count(layer, selected_only)
        if selected_only and feature_count == 0:
            raise ValueError("No features are selected in the source layer.")

        with atomic_output(output_path) as temporary_path:
            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, temporary_path, transform_context, options)
            if err != QgsVectorFileWriter.WriterError.NoError:
                raise ValueError(f"DXF writer failed: {err_msg}")

        authid = effective_crs.authid() if effective_crs.isValid() else "Unknown"
        return verified_export_result(
            output_path, "DXF", feature_count, authid)
