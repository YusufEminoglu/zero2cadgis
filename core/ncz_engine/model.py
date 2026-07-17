# -*- coding: utf-8 -*-
# NCZ result model adapted from Jeomatik NCZ Reader ncz_binary.py.
# Copyright (C) 2026 Erdinç Örsan ÜNAL
# Original source: https://github.com/erdincunal/Jeomatik-NCZ-Reader
#
# Modified and separated for 02CadGis on 2026-07-16.
# Modifications Copyright (C) 2026 Yusuf Eminoğlu
# See THIRD_PARTY_NOTICES.md and LICENSE for details.
# SPDX-License-Identifier: GPL-2.0-or-later
"""Stable data contract shared by the NCZ engine and QGIS integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NetcadCoordinate:
    x: float
    y: float
    z: float = 0.0


@dataclass
class NetcadEntity:
    geometry_kind: str
    layer_code: int
    layer_name: str = ""
    color_argb: Optional[int] = None
    name: str = ""
    label_text: str = ""
    text_height: float = 0.0
    rotation_degrees: float = 0.0
    box_width: float = 0.0
    box_height: float = 0.0
    scale: float = 0.0
    grid_x: float = 0.0
    grid_y: float = 0.0
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0
    is_closed: bool = False
    coordinates: list[NetcadCoordinate] = field(default_factory=list)


@dataclass
class NetcadAttributeRow:
    row_index: int
    columns: dict[str, object] = field(default_factory=dict)


@dataclass
class NetcadAttributeTable:
    table_ref: str
    rows: list[NetcadAttributeRow] = field(default_factory=list)


@dataclass
class NetcadParseResult:
    entities: list[NetcadEntity] = field(default_factory=list)
    attribute_tables: list[NetcadAttributeTable] = field(default_factory=list)
    layer_names: list[str] = field(default_factory=list)
    layer_colors: list[int] = field(default_factory=list)
    parser_backend: str = ""
    version_name: str = ""
    epsg: str = ""
    projection_text: str = ""
    unsupported_geometry_types: dict[int, int] = field(default_factory=dict)
