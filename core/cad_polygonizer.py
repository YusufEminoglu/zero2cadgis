# -*- coding: utf-8 -*-
"""cad_polygonizer — Automated polygonization of CAD boundary line segments.

In Turkish urban planning drawings, spatial zoning blocks (imar adaları ve
parseller) are frequently drawn as individual line boundaries (LineString)
instead of closed polygon entities.

This module takes the *open* line work of plan-area tabaka, nodes it (lines in a
drawing cross mid-segment far more often than they meet at a shared vertex, and
polygonize only closes faces at nodes), and returns one polygon entity per
enclosed face, holes included, inheriting the tabaka of the lines that bound it.

Closed polylines are already polygons and are left out on purpose: feeding them
in again would put a second, identical polygon on top of every one the drawing
already has.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from contextlib import suppress
import re
from typing import Dict, List, Optional, Sequence

from .netcad_parser import NetcadCoordinate, NetcadEntity


# Whole tokens that name a land-use area. Matched as tokens, not substrings:
# as substrings "KOP" is inside "KOPRU" (a bridge) and "ADA" inside "KADASTRO".
PLAN_AREA_TABAKA_KEYWORDS = frozenset((
    "KONUT", "TICARET", "PARK", "OTOPARK", "SANAYI", "EGITIM",
    "SAGLIK", "IBADET", "BHA", "SOSYAL", "KULTUREL", "YESIL",
    "GELISME", "TURIZM", "REKREASYON", "ORMAN", "MERA", "TARIM",
    "MEZARLIK", "OTOGAR", "TERMINAL", "DEPOLAMA", "KSA",
))
BLOCK_TOKENS = frozenset(("ADA", "ADAKENARI"))

_TR_MAP = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
                         "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U"})

# Faces smaller than this (map units², i.e. m² in a projected plan CRS) are
# slivers from lines that overshoot each other, not plan areas.
MIN_FACE_AREA = 1.0


def _tokens(name: str) -> List[str]:
    text = str(name).strip().translate(_TR_MAP).upper()
    return [t for t in re.split(r"[^A-Z0-9]+", text) if t]


def is_plan_area_tabaka(tabaka_name: Optional[str]) -> bool:
    """True if the tabaka names a land-use area or a block (ada) boundary."""
    if not tabaka_name:
        return False
    with suppress(Exception):
        from .plangml_schema import lookup_tabaka
        identity = lookup_tabaka(tabaka_name)
        if identity is not None:
            return identity.geometri == "POLYGON" or identity.tabaka == "ADAKENARI"
    tokens = _tokens(tabaka_name)
    if tokens and tokens[0] == "PL":
        return True
    return any(t in PLAN_AREA_TABAKA_KEYWORDS or t in BLOCK_TOKENS for t in tokens)


def is_open_line_work(entity: NetcadEntity) -> bool:
    """Line work that polygonization can use: open lines, polylines and arcs."""
    if entity.geometry_kind not in ("Line", "Polyline", "Arc"):
        return False
    return not entity.is_closed


def polygonize_cad_entities(
    line_entities: Sequence[NetcadEntity],
) -> List[NetcadEntity]:
    """Polygonize the open line work of plan-area tabaka, one tabaka at a time.

    Entities that are not open line work, or whose tabaka is not a plan area,
    are ignored, so a caller may pass a drawing's entities unfiltered.

    Returns:
        New :class:`NetcadEntity` objects with ``geometry_kind="Polygon"``,
        ``name="POLYGONIZED"`` (so they can be told apart from drawn polygons)
        and any holes in ``interior_rings``.
    """
    if not line_entities:
        return []

    # Requires QGIS runtime for robust topological polygonization
    try:
        from qgis.core import QgsGeometry, QgsPointXY  # type: ignore
    except ImportError:
        return []

    by_layer: Dict[str, List[NetcadEntity]] = {}
    for ent in line_entities:
        if not is_open_line_work(ent):
            continue
        key = ent.layer_name or f"LAYER_{ent.layer_code}"
        if not is_plan_area_tabaka(key):
            continue
        by_layer.setdefault(key, []).append(ent)

    result_polygons: List[NetcadEntity] = []

    for layer_name, entities in by_layer.items():
        qgis_lines = []
        for ent in entities:
            if not ent.coordinates or len(ent.coordinates) < 2:
                continue
            with suppress(Exception):
                line_geom = QgsGeometry.fromPolylineXY(
                    [QgsPointXY(c.x, c.y) for c in ent.coordinates])
                if line_geom and not line_geom.isEmpty():
                    qgis_lines.append(line_geom)

        if not qgis_lines:
            continue

        with suppress(Exception):
            # Node first: a union splits every line at every crossing.
            noded = QgsGeometry.unaryUnion(qgis_lines)
            if not noded or noded.isEmpty():
                continue
            poly_collection = QgsGeometry.polygonize([noded])
            if not poly_collection or poly_collection.isEmpty():
                continue

            faces = (poly_collection.asGeometryCollection()
                     if poly_collection.isMultipart() else [poly_collection])
            sample = entities[0]
            for face in faces:
                if not face or face.isEmpty() or face.area() < MIN_FACE_AREA:
                    continue
                rings = face.asPolygon()
                if not rings or len(rings[0]) < 4:
                    continue
                outer, holes = rings[0], rings[1:]
                result_polygons.append(NetcadEntity(
                    geometry_kind="Polygon",
                    layer_code=sample.layer_code,
                    layer_name=layer_name,
                    name="POLYGONIZED",
                    color_argb=sample.color_argb,
                    is_closed=True,
                    coordinates=[NetcadCoordinate(x=p.x(), y=p.y()) for p in outer],
                    interior_rings=[
                        [NetcadCoordinate(x=p.x(), y=p.y()) for p in hole]
                        for hole in holes if len(hole) >= 4
                    ],
                ))

    return result_polygons
