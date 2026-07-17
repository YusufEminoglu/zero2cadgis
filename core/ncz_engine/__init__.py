# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Public model contract for the modular 02CadGis NCZ engine."""

from .model import (
    NetcadAttributeRow,
    NetcadAttributeTable,
    NetcadCoordinate,
    NetcadEntity,
    NetcadParseResult,
)

__all__ = (
    "NetcadAttributeRow",
    "NetcadAttributeTable",
    "NetcadCoordinate",
    "NetcadEntity",
    "NetcadParseResult",
)
