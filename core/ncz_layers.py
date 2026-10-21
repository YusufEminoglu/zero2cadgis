# -*- coding: utf-8 -*-
"""ncz_layers — decoded Netcad entities to QGIS memory layers.

The dock's Netcad importer and the Processing algorithms build layers through
these functions, so a drawing comes out the same whichever way it is
imported: one feature per entity, the CAD columns below, arcs and circles
approximated the same way, closed rings closed with the same tolerance.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import math
from contextlib import suppress
from typing import Optional

from qgis.core import QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.PyQt.QtCore import QMetaType

from .cad_engine import CadCleanupEngine
from .ncz_engine.v2.geometry import KIND_FAMILY, KIND_POLYLINE
from .qgis_compat import add_features_or_raise

# Name and type of every CAD column, in feature attribute order.
CAD_FIELD_SPECS = (
    ("source_file", QMetaType.Type.QString),
    ("layer_code", QMetaType.Type.Int),
    ("layer_name", QMetaType.Type.QString),
    ("entity_type", QMetaType.Type.QString),
    ("name", QMetaType.Type.QString),
    ("label", QMetaType.Type.QString),
    ("color_argb", QMetaType.Type.QString),
    ("radius", QMetaType.Type.Double),
    ("start_ang", QMetaType.Type.Double),
    ("end_ang", QMetaType.Type.Double),
    ("text_h", QMetaType.Type.Double),
    ("rotation", QMetaType.Type.Double),
    ("box_width", QMetaType.Type.Double),
    ("box_height", QMetaType.Type.Double),
    ("scale", QMetaType.Type.Double),
    ("grid_x", QMetaType.Type.Double),
    ("grid_y", QMetaType.Type.Double),
    # The drawing layer's pen width in mm (Netcad LEX.ST2), empty when the
    # layer draws with the default pen. The style draws it at that width.
    ("line_width_mm", QMetaType.Type.Double),
)

# Geometry family -> (QGIS geometry type, layer-name suffix).
FAMILY_LAYERS = {
    "POINT": ("Point", "POINT/TEXT"),
    "LINE": ("LineString", "LINE"),
    "POLYGON": ("Polygon", "POLYGON"),
}
# A closed polyline is an area; a hairline of gap between its first and
# last vertex still counts, because CAD drawings routinely leave one.
RING_CLOSE_TOLERANCE = 1e-4
# The dock's default for closing a ring left open by less than this (map units).
DEFAULT_CLOSE_TOLERANCE = 0.10


def cad_fields() -> list:
    return [QgsField(name, kind) for name, kind in CAD_FIELD_SPECS]


def rings_shut(coords, is_closed: bool) -> bool:
    """Whether a polyline's vertex list describes an area."""
    if not coords:
        return False
    if is_closed and len(coords) >= 3:
        return True
    if len(coords) < 4:
        return False
    first, last = coords[0], coords[-1]
    return (abs(first.x - last.x) < RING_CLOSE_TOLERANCE
            and abs(first.y - last.y) < RING_CLOSE_TOLERANCE)


def geometry_family(geometry_kind: str, is_closed: bool = False,
                    coords: list | None = None) -> tuple:
    """The layer family of one decoded feature: (group suffix, QGIS type).

    The kind's family is the engine's (``KIND_FAMILY``), so a kind the decoder
    grows later is routed without a change here. The one thing the kind
    alone cannot say is whether a polyline encloses an area, which depends on
    the vertices.
    """
    family = KIND_FAMILY.get(geometry_kind)
    if family is None:
        return None, None
    if geometry_kind == KIND_POLYLINE and rings_shut(coords, is_closed):
        family = "POLYGON"
    geometry_type, suffix = FAMILY_LAYERS[family]
    return suffix, geometry_type


def angle_to_radians(angle: float) -> float:
    if abs(angle) <= (2.0 * math.pi) + 1e-6:
        return float(angle)
    return math.radians(angle)


def approximate_circle(center, radius, segments=72) -> list:
    if radius <= 0:
        return []
    points = [
        QgsPointXY(center.x + math.cos(2.0 * math.pi * i / segments) * radius,
                   center.y + math.sin(2.0 * math.pi * i / segments) * radius)
        for i in range(segments)
    ]
    points.append(QgsPointXY(points[0]))
    return points


def approximate_arc(center, radius, start_angle, end_angle) -> list:
    if radius <= 0:
        return []
    start = angle_to_radians(start_angle)
    end = angle_to_radians(end_angle)
    if abs(end - start) <= 1e-9:
        end = start + (2.0 * math.pi)
    while end < start:
        end += 2.0 * math.pi
    span = end - start
    segments = max(8, min(96, int(abs(span) / (math.pi / 24.0)) + 1))
    return [
        QgsPointXY(center.x + math.cos(start + (span * i / segments)) * radius,
                   center.y + math.sin(start + (span * i / segments)) * radius)
        for i in range(segments + 1)
    ]


def coords_to_geometry(geometry_kind: str, geometry_type: str, coords: list,
                       radius: float, start_angle: float, end_angle: float,
                       is_closed: bool,
                       close_tolerance: float = DEFAULT_CLOSE_TOLERANCE) -> Optional[QgsGeometry]:
    if geometry_type == "Point":
        if not coords:
            return None
        return QgsGeometry.fromPointXY(QgsPointXY(coords[0].x, coords[0].y))

    if geometry_type == "LineString":
        if geometry_kind == "Arc":
            if not coords:
                return None
            arc_points = approximate_arc(coords[0], radius, start_angle, end_angle)
            if len(arc_points) < 2:
                return None
            return QgsGeometry.fromPolylineXY(arc_points)
        if len(coords) < 2:
            return None
        return QgsGeometry.fromPolylineXY([QgsPointXY(c.x, c.y) for c in coords])

    if geometry_type == "Polygon":
        if geometry_kind == "Circle":
            if not coords:
                return None
            return QgsGeometry.fromPolygonXY([approximate_circle(coords[0], radius)])
        ring = [QgsPointXY(c.x, c.y) for c in coords]
        if len(ring) < 3:
            return None
        force_close = is_closed or geometry_kind in {
            "Box", "Triangle", "MapSheet", "SmartObject", "Polyline"}
        ring = CadCleanupEngine.close_polyline(ring, close_tolerance, force=force_close)
        if len(ring) < 4:
            return None
        return QgsGeometry.fromPolygonXY([ring])
    return None


def entity_attributes(entity, source_value: str) -> list:
    """The CAD column values of one entity, in ``CAD_FIELD_SPECS`` order."""
    return [
        source_value,
        entity.layer_code,
        entity.layer_name or f"LAYER_{entity.layer_code}",
        entity.geometry_kind,
        entity.name,
        entity.label_text,
        "" if entity.color_argb is None else str(entity.color_argb),
        entity.radius,
        entity.start_angle,
        entity.end_angle,
        entity.text_height,
        entity.rotation_degrees,
        entity.box_width,
        entity.box_height,
        entity.scale,
        entity.grid_x,
        entity.grid_y,
        getattr(entity, "line_width", None),
    ]


def build_entity_layer(layer_name: str, geometry_type: str, entities, crs,
                       source_file_name: str,
                       entity_source_files: dict | None = None,
                       clip_boundary: QgsGeometry | None = None,
                       clip_mode: str = "none",
                       clean: bool = False,
                       simplify: bool = False,
                       close_tolerance: float = DEFAULT_CLOSE_TOLERANCE) -> Optional[QgsVectorLayer]:
    """One memory layer of *geometry_type* holding *entities*.

    *clean* drops consecutive duplicate vertices and *simplify* collinear
    ones; with a *clip_boundary*, each geometry is filtered or cropped by it
    (``spatial_filter.clip_or_filter_geometry``).
    """
    layer = QgsVectorLayer(f"{geometry_type}?crs={crs.authid()}", layer_name, "memory")
    if not layer.isValid():
        return None
    layer.dataProvider().addAttributes(cad_fields())
    layer.updateFields()

    clip = clip_boundary is not None and clip_mode and clip_mode != "none"
    if clip:
        from .spatial_filter import clip_or_filter_geometry

    features = []
    for entity in entities:
        coords = entity.coordinates
        if clean:
            coords = CadCleanupEngine.clean_duplicates(coords)
        if simplify and len(coords) > 3:
            coords = CadCleanupEngine.simplify_collinear(coords)
        geom = coords_to_geometry(
            entity.geometry_kind, geometry_type, coords, entity.radius,
            entity.start_angle, entity.end_angle, entity.is_closed, close_tolerance)
        if geom and geometry_type == "Polygon" and entity.interior_rings:
            with suppress(Exception):
                geom = QgsGeometry.fromPolygonXY([
                    [QgsPointXY(c.x, c.y) for c in ring]
                    for ring in [coords, *entity.interior_rings]])
        if not geom or geom.isEmpty():
            continue
        if clip:
            geom = clip_or_filter_geometry(geom, clip_boundary, clip_mode)
            if not geom or geom.isEmpty():
                continue
        source_value = source_file_name
        if entity_source_files:
            source_value = entity_source_files.get(id(entity), source_file_name)
        feature = QgsFeature(layer.fields())
        feature.setGeometry(geom)
        feature.setAttributes(entity_attributes(entity, source_value))
        features.append(feature)

    add_features_or_raise(layer, features, f"NCZ geometry layer {layer_name}")
    return layer
