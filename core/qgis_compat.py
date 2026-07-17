# -*- coding: utf-8 -*-
"""Small QGIS 3/4 compatibility helpers used by conversion engines."""
from __future__ import annotations

from qgis.core import QgsWkbTypes


def _value_text(value) -> str:
    parts = [str(value).lower()]
    name = getattr(value, "name", "")
    if name:
        parts.append(str(name).lower())
    return " ".join(parts)


def _value_number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        enum_value = getattr(value, "value", None)
        if enum_value is not None:
            try:
                return int(enum_value)
            except (TypeError, ValueError):
                return None
    return None


def _geometry_name_from_text(text: str) -> str | None:
    text = (text or "").lower()
    if "multipoint" in text:
        return "MultiPoint"
    if "multiline" in text or ("multi" in text and "line" in text):
        return "MultiLineString"
    if "multipolygon" in text or ("multi" in text and "polygon" in text):
        return "MultiPolygon"
    if "point" in text:
        return "Point"
    if "line" in text or "curve" in text:
        return "LineString"
    if "polygon" in text or "surface" in text:
        return "Polygon"
    return None


def memory_geometry_type_name(layer) -> str:
    """Return a memory-provider geometry token for a QGIS 3 or QGIS 4 layer."""
    try:
        wkb_name = QgsWkbTypes.displayString(layer.wkbType())
        geometry_name = _geometry_name_from_text(wkb_name)
        if geometry_name:
            return geometry_name
    except Exception:
        geometry_name = None

    try:
        geometry_type = layer.geometryType()
    except Exception:
        geometry_type = None

    geometry_name = _geometry_name_from_text(_value_text(geometry_type))
    if geometry_name:
        return geometry_name

    geometry_number = _value_number(geometry_type)
    if geometry_number == 0:
        return "Point"
    if geometry_number == 1:
        return "LineString"
    if geometry_number == 2:
        return "Polygon"

    return "Point"


def _feature_count(layer) -> int | None:
    try:
        count = layer.featureCount()
    except Exception:
        return None
    return count if isinstance(count, int) else None


def add_features_or_raise(layer, features: list, context: str) -> None:
    """Add features and fail loudly if QGIS rejects any feature silently."""
    if not features:
        layer.updateExtents()
        return

    before = _feature_count(layer)
    provider = layer.dataProvider()
    result = provider.addFeatures(features)

    ok = True
    if isinstance(result, tuple):
        ok = bool(result[0])
    elif result is not None:
        ok = bool(result)

    layer.updateExtents()
    after = _feature_count(layer)
    if before is not None and after is not None:
        added = after - before
    else:
        added = len(features) if ok else 0

    if not ok or added < len(features):
        added = max(0, added)
        raise ValueError(
            f"{context}: only {added} of {len(features)} features were "
            f"accepted by layer '{layer.name()}'."
        )
