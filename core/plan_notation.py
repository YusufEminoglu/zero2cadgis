# -*- coding: utf-8 -*-
"""plan_notation — the plan's own notation, drawn where the planner put it.

A Netcad 8 imar plan stores its building rights (nizam, kat, TAKS / KAKS or
emsal, Hmax, setbacks) and its road widths as Smart Objects placed on the
sheet. The MPYY transfer carries those values into the plan areas, but an area
covering several blocks with different notation cannot hold one value, and a
road width has no MPYY axis to sit on when the drawing's road layers are not
Yolorta. So every Smart Object also becomes a point, where it was drawn:

* ``Building notation`` — MPYY field names (YapiDuzeni, KatAdedi, Taks, ...),
  drawn by MPYY Studio's Ek-1e notation (nizam / kat circle, TAKS / KAKS circle,
  E = / Yençok);
* ``Road widths`` — YolGenisligi, drawn as MPYY's road-width circle.

Values come from the object's own form through the same parser as the drawing
texts (``notation_texts`` / ``parse_zoning_parameters``); nothing is guessed.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Parser nizam words -> MPYY 1.1.7 YapiDuzenTip codes.
NIZAM_CODES = {"AYRIK": "Ayrik", "BITISIK": "Bitisik", "BLOK": "Blok", "IKIZ": "Ikiz", "SERBEST": "Serbest"}

BUILDING_LAYER = "Building notation"
ROAD_LAYER = "Road widths"


@dataclass
class NotationPoint:
    x: float
    y: float
    values: Dict[str, Any] = field(default_factory=dict)   # MPYY field -> value
    road_width: Optional[float] = None
    tabaka: str = ""                                        # the Smart Object's CAD layer


def notation_points(entities) -> List[NotationPoint]:
    """One point per Smart Object that states building rights or a road width."""
    from .zoning_text_extractor import notation_texts, parse_zoning_parameters

    points = []
    for entity in entities:
        properties = getattr(entity, "properties", None)
        if not properties or not entity.coordinates:
            continue
        params = parse_zoning_parameters(notation_texts(properties))
        if not params.has_any:
            continue
        x = sum(c.x for c in entity.coordinates) / len(entity.coordinates)
        y = sum(c.y for c in entity.coordinates) / len(entity.coordinates)
        values = {}
        if params.yapi_duzeni in NIZAM_CODES:
            values["YapiDuzeni"] = NIZAM_CODES[params.yapi_duzeni]
        if params.kat_adedi is not None:
            values["KatAdedi"] = params.kat_adedi
        if params.taks is not None:
            values["Taks"], values["TaksTip"] = params.taks, "Deger"
        if params.emsal_kaks is not None:
            values["EmsalKaks"], values["EmsalKaksTip"] = params.emsal_kaks, "Deger"
        if params.yapi_yuksekligi is not None:
            values["YapiYuksekligi"], values["YapiYuksekligiTip"] = params.yapi_yuksekligi, "Deger"
        if params.on_bahce is not None:
            values["OnBahceMesafesi"] = params.on_bahce
        if params.yan_bahce is not None:
            values["YanBahceMesafesi"] = params.yan_bahce
        if values or params.yol_genisligi is not None:
            points.append(NotationPoint(x, y, values, params.yol_genisligi,
                                        str(getattr(entity, "layer_name", "") or "")))
    return points


def build_notation_layers(points: List[NotationPoint], crs) -> List[Any]:
    """The two point layers, styled with MPYY Studio's notation; empty ones are left out."""
    from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsVectorLayer
    from qgis.PyQt.QtCore import QMetaType

    from ..mpyy.core import mpyy_workspace

    string, double, integer = QMetaType.Type.QString, QMetaType.Type.Double, QMetaType.Type.Int
    building_fields = [
        ("YapiDuzeni", string), ("KatAdedi", integer), ("Taks", double), ("TaksTip", string),
        ("EmsalKaks", double), ("EmsalKaksTip", string), ("YapiYuksekligi", double),
        ("YapiYuksekligiTip", string), ("OnBahceMesafesi", double), ("YanBahceMesafesi", double),
        ("SembolPoz", string),
    ]
    layers = []

    def point_layer(name, fields):
        layer = QgsVectorLayer(f"Point?crs={crs.authid()}", name, "memory")
        layer.dataProvider().addAttributes([QgsField(n, t) for n, t in fields])
        layer.updateFields()
        return layer

    buildings = [p for p in points if p.values]
    if buildings:
        layer = point_layer(BUILDING_LAYER, building_fields)
        features = []
        for point in buildings:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point.x, point.y)))
            for name, value in point.values.items():
                feature[name] = value
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        _invisible_points(layer)
        mpyy_workspace.apply_building_notation(layer)
        layers.append(layer)

    roads = [p for p in points if p.road_width is not None]
    if roads:
        layer = point_layer(ROAD_LAYER, [("YolGenisligi", double)])
        features = []
        for point in roads:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point.x, point.y)))
            feature["YolGenisligi"] = point.road_width
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        mpyy_workspace.apply_road_width_notation(layer)
        layers.append(layer)
    return layers


def _invisible_points(layer) -> None:
    """The notation is all labels: the anchor point itself is not drawn."""
    from qgis.core import QgsMarkerSymbol, QgsSingleSymbolRenderer

    symbol = QgsMarkerSymbol.createSimple({"name": "circle", "size": "0", "color": "0,0,0,0",
                                           "outline_style": "no"})
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))


def hide_drawn_notation_objects(layers, points: List[NotationPoint]) -> int:
    """Hide the Smart Object shapes whose notation is now drawn by the notation layers.

    Their frames (a box behind a road width, a circle outline) would otherwise
    be drawn a second time in the drawing's colours. Only Smart Objects of the
    CAD layers that produced notation are filtered; the features stay in the
    layer. Returns how many layers were filtered.
    """
    tabakas = sorted({p.tabaka for p in points if p.tabaka})
    if not tabakas:
        return 0
    quoted = ", ".join("'" + t.replace("'", "''") + "'" for t in tabakas)
    expression = f"""NOT ("entity_type" = 'SmartObject' AND "layer_name" IN ({quoted}))"""
    filtered = 0
    for layer in layers:
        names = layer.fields().names()
        if "entity_type" in names and "layer_name" in names and layer.setSubsetString(expression):
            filtered += 1
    return filtered
