# -*- coding: utf-8 -*-
"""Plan-drawing helpers shared by the importers.

Plan styling itself is MPYY Studio's MPYY UİP / NİP / ÇDP style set, carried
under ``zero2cadgis/mpyy``. What is left here is what every plan and CAD layer
needs regardless of that style: which plan level a file is, which field holds
a drawing's text, the drawing's own text height, and the plan scale a sheet is
drawn at.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from contextlib import suppress
import re
from typing import Any, Optional

_PLAN_TYPE_WORDS = {
    "UIP": "UIP", "UYGULAMA": "UIP", "MUIP": "UIP",
    "NIP": "NIP", "NAZIM": "NIP", "MNIP": "NIP",
    "CDP": "CDP", "CEVRE": "CDP", "MCDP": "CDP",
}


_PLAN_TYPE_SCALES = {
    "500": "UIP", "1000": "UIP", "2000": "UIP",
    "5000": "NIP", "10000": "NIP",
    "25000": "CDP", "50000": "CDP", "100000": "CDP", "200000": "CDP",
}


def detect_plan_type(name: Optional[str]) -> Optional[str]:
    """Infer the plan type (UIP/NIP/CDP) from a file or layer name.

    Recognizes explicit markers (UIP/NAZIM/ÇEVRE...) and leading scale numbers
    such as ``1000_BAHCESARAY_IMAR`` or ``1/5000 NAZIM PLAN``.
    """
    if not name:
        return None
    upper = str(name).upper()
    tr_map = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})
    upper = upper.translate(tr_map)
    tokens = [t for t in re.split(r"[^A-Z0-9]+", upper) if t]
    for token in tokens:
        if token in _PLAN_TYPE_WORDS:
            return _PLAN_TYPE_WORDS[token]
    for token in tokens:
        if token in _PLAN_TYPE_SCALES:
            return _PLAN_TYPE_SCALES[token]
    return None


LABEL_FIELD_CANDIDATES = (
    "label", "label_text", "text", "text_string", "string",
    "yazi", "yazi_metni", "metin", "baslik", "name",
    "kat_adedi", "emsal", "lejant", "fonksiyon", "val", "value",
)


def pick_label_field(qgis_layer: Any) -> Optional[str]:
    """The field that actually carries the drawing's text, or None.

    A field existing is not the same as a field holding anything. A CAD point
    layer declares ``name`` on every feature but only fills ``label`` on the
    text entities, so picking by name alone binds the labels to a column that
    is empty everywhere and nothing is drawn. A candidate is therefore only
    accepted once a non-empty value has actually been seen in it.
    """
    if not hasattr(qgis_layer, "fields") or not hasattr(qgis_layer, "uniqueValues"):
        return None
    try:
        by_lower = {f.name().lower(): f.name() for f in qgis_layer.fields()}
    except Exception:
        return None

    for candidate in LABEL_FIELD_CANDIDATES:
        field = by_lower.get(candidate)
        if field is None:
            continue
        with suppress(Exception):
            index = qgis_layer.fields().indexOf(field)
            vals = qgis_layer.uniqueValues(index, 25)
            for value in vals:
                if value is not None and str(value).strip():
                    return field
            if not vals and hasattr(qgis_layer, "getFeatures"):
                for idx, feat in enumerate(qgis_layer.getFeatures()):
                    if idx >= 25:
                        break
                    val = feat[field]
                    if val is not None and str(val).strip():
                        return field
    return None


PLAN_REFERENCE_SCALES = {"UIP": 1000, "NIP": 5000, "CDP": 25000}


DEFAULT_TEXT_HEIGHT_M = 2.5


def use_drawing_text_height(settings: Any, text_format: Any, field_names: Any) -> bool:
    """Size CAD text by the drawing's own text height, in metres on the ground.

    Netcad and DXF texts carry their height in drawing units (``text_h``, metres):
    a PARK label drawn 5 m high. Rendered at a fixed point size instead, the same
    label covers the sheet when zoomed out and is a speck when zoomed in. In map
    units it stays exactly as drawn at every scale. Returns False (nothing changed)
    when the layer has no ``text_h``.
    """
    if "text_h" not in set(field_names or ()):
        return False
    from qgis.core import QgsProperty, QgsUnitTypes  # type: ignore

    meters = QgsUnitTypes.RenderUnit.RenderMetersInMapUnits
    text_format.setSizeUnit(meters)
    text_format.setSize(DEFAULT_TEXT_HEIGHT_M)
    buffer = text_format.buffer()
    buffer.setSizeUnit(meters)
    buffer.setSize(0.15 * DEFAULT_TEXT_HEIGHT_M)
    text_format.setBuffer(buffer)
    size_key = getattr(getattr(type(settings), "Property", type(settings)), "Size")
    settings.dataDefinedProperties().setProperty(
        size_key, QgsProperty.fromExpression(
            f'if("text_h" > 0, "text_h", {DEFAULT_TEXT_HEIGHT_M})'))
    settings.setFormat(text_format)
    return True
