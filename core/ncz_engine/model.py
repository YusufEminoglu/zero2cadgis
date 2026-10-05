# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""The data contract between the NCZ engine and everything downstream.

A decoded drawing reaches the rest of 02CadGis as these dataclasses rather
than as raw dictionaries, so the dock, the exporters and the styling
pipeline all read one spelling of every field. The engine writes them; the
converters only read them and never touch the file bytes themselves.

Two shapes matter here:

* :class:`NetcadCoordinate` and :class:`NetcadEntity` describe one drawing
  feature. Netcad stores a point's northing before its easting, but a
  coordinate here is already in map order — ``x`` is the easting.
* :class:`NetcadParseResult` is one whole drawing: its features, its
  attribute tables, and the metadata read from the header blocks.

The field names below are part of the plugin's public surface. They appear
in the converter's column mapping and in the on-disk index cache, so
renaming one is a cache-invalidating change rather than a private
refactor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

__all__ = [
    "NetcadAttributeRow",
    "NetcadAttributeTable",
    "NetcadCoordinate",
    "NetcadEntity",
    "NetcadParseResult",
]


@dataclass
class NetcadCoordinate:
    """One vertex, already in map order (``x`` = easting, ``y`` = northing)."""

    x: float
    y: float
    z: float = 0.0


@dataclass
class NetcadEntity:
    """One drawing feature, whatever its geometry type.

    Every geometry the decoder understands is flattened into this single
    record. ``geometry_kind`` says which one it was, and the fields that do
    not apply to that kind keep their neutral default. That keeps the
    converter free of per-type branching: it switches on ``geometry_kind``
    once, where it builds the QGIS geometry, and never again.
    """

    # What this feature is, and which layer of the drawing it sits on.
    geometry_kind: str
    layer_code: int
    layer_name: str = ""

    # Netcad stores colour as a pen index into the LEX.ST2 table. The
    # decoder resolves that index to an ARGB value, or leaves it None when
    # the index points at nothing.
    color_argb: Optional[int] = None

    # Text-bearing features: the label itself and how it is drawn. Block
    # and symbol records carry their name through the same fields.
    name: str = ""
    label_text: str = ""
    text_height: float = 0.0
    rotation_degrees: float = 0.0

    # Plan boxes, smart objects and map sheets report a footprint and a
    # repetition grid rather than explicit corners.
    box_width: float = 0.0
    box_height: float = 0.0
    scale: float = 0.0
    grid_x: float = 0.0
    grid_y: float = 0.0

    # Curves.
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0

    # Whether a polyline returns to the vertex it started from.
    is_closed: bool = False

    # The feature's vertices, in draw order.
    coordinates: list[NetcadCoordinate] = field(default_factory=list)

    # Filled in by the polygonizer when it turns line work into areas. The
    # NCZ decoder never sets these itself, so they stay empty on decode.
    interior_rings: list[list[NetcadCoordinate]] = field(default_factory=list)

    # Netcad 8 Smart Objects carry planning values (nizam, kat, taks, kaks,
    # hmax, genislik ...) as a name-to-value bag. Only the values the record
    # actually sets appear here; every other geometry leaves it empty.
    properties: dict[str, str] = field(default_factory=dict)

    # The layer's pen width in millimetres, read from the LEX.ST2 block
    # when that block sets one.
    line_width: float | None = None


@dataclass
class NetcadAttributeRow:
    """One row of a Netcad attribute table."""

    row_index: int
    columns: dict[str, object] = field(default_factory=dict)


@dataclass
class NetcadAttributeTable:
    """An ``@TAB`` attribute table, keyed by its reference in the drawing."""

    table_ref: str
    rows: list[NetcadAttributeRow] = field(default_factory=list)


@dataclass
class NetcadParseResult:
    """One decoded drawing."""

    entities: list[NetcadEntity] = field(default_factory=list)
    attribute_tables: list[NetcadAttributeTable] = field(default_factory=list)

    # The drawing's layer table, in the order the file declares it, with
    # each entry's colour resolved to ARGB.
    layer_names: list[str] = field(default_factory=list)
    layer_colors: list[int] = field(default_factory=list)

    # Which engine produced this result, reported to the user so a decode
    # is never silently attributed to the wrong backend.
    parser_backend: str = ""

    # Drawing-level metadata read from the header blocks.
    version_name: str = ""
    epsg: str = ""
    projection_text: str = ""

    # Geometry type codes the decoder met but does not implement, mapped to
    # how many records carried them. Surfaced so a drawing that comes back
    # thin can say why instead of merely looking empty.
    unsupported_geometry_types: dict[int, int] = field(default_factory=dict)
