# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""NCZ Engine v2 — independent block-oriented Netcad drawing decoder.

New implementation written for 02CadGis against the format notes in
``docs/NCZ_FORMAT.md``: bounds-checked cursor reads, a declarative block
scanner, a geometry-decoder registry, and a two-phase lazy catalog that
can decode a selected subset of records.
"""
from .parser import PARSER_BACKEND_V2, NczCatalog, parse_file  # noqa: F401
