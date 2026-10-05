# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""NCZ Engine v2 — independent block-oriented Netcad drawing decoder.

New implementation written for 02CadGis against the format notes in
``docs/NCZ_FORMAT.md``: bounds-checked cursor reads, a declarative block
scanner, a geometry-decoder registry, and a two-phase lazy catalog that
can decode a selected subset of records.
"""
from .geometry import (  # noqa: F401
    KIND_ARC,
    KIND_BLOCK,
    KIND_CIRCLE,
    KIND_FAMILY,
    KIND_LINE,
    KIND_MAP_SHEET,
    KIND_POINT,
    KIND_POLYGON,
    KIND_POLYLINE,
    KIND_SMART_OBJECT,
    KIND_SYMBOL,
    KIND_TEXT,
    KIND_TRIANGLE,
)
from .parser import PARSER_BACKEND_V2, NczCatalog, parse_file  # noqa: F401
