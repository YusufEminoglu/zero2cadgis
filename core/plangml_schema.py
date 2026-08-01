# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""plangml_schema — official identity of a UİP tabaka.

The PlanGML schema columns of an imported plan are supposed to carry the
Ministry's own codes: the upper group and its code, the function and its code.
They were previously derived from the symbology engine's keyword lists, which
had no codes in them at all, so every feature came out claiming group ``100``.

``core/mpyy_catalog.py`` holds the real values, compiled offline from the
Mekânsal Planlar Yapım Yönetmeliği UİP database. This module resolves a CAD
tabaka name against it.

A lookup either finds the official record or returns ``None``. There is no
approximate answer: a plausible-looking code in a column reserved for the
Ministry's codes is worse than an empty cell, because it survives export and
looks authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from .mpyy_catalog import MPYY_ALIASES, MPYY_TABAKA

_TR_MAP = str.maketrans({
    "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
    "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U",
})


@dataclass(frozen=True)
class TabakaIdentity:
    """One tabaka as the official catalog defines it."""

    tabaka: str                 # official tabaka name
    ust_grup_id: str            # e.g. "112000"
    ust_grup_adi: str           # e.g. "KONUT ALANLARI / YERLEŞİM ALANLARI"
    fonksiyon_kodu: str         # e.g. "112002"
    fonksiyon_adi: str          # e.g. "YERLEŞİK KONUT ALANI"
    geometri: str               # "POLYGON" | "LINE"
    matched_as: str             # "exact" | "alias"


def _normalize(name: Optional[str]) -> str:
    """Fold a CAD tabaka name onto the catalog's spelling."""
    if not name:
        return ""
    text = str(name).strip().translate(_TR_MAP).upper()
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_")


def _index():
    """Normalized catalog, built once."""
    cached = getattr(_index, "_cache", None)
    if cached is None:
        cached = {_normalize(name): name for name in MPYY_TABAKA}
        _index._cache = cached
    return cached


def _alias_index():
    cached = getattr(_alias_index, "_cache", None)
    if cached is None:
        cached = {_normalize(local): official
                  for local, official in MPYY_ALIASES.items()}
        _alias_index._cache = cached
    return cached


def lookup_tabaka(name: Optional[str]) -> Optional[TabakaIdentity]:
    """Official identity of a CAD tabaka, or None if it has none.

    ``None`` is the right answer for a CAD helper layer — symbol, text anchor,
    rölöve — and for a planning tabaka whose local name has no unambiguous
    official counterpart. Neither should be handed codes it does not own.
    """
    key = _normalize(name)
    if not key:
        return None

    official = _index().get(key)
    matched_as = "exact"
    if official is None:
        official = _alias_index().get(key)
        matched_as = "alias"
    if official is None:
        return None

    record = MPYY_TABAKA[official]
    return TabakaIdentity(
        tabaka=official,
        ust_grup_id=record["ust_grup_id"],
        ust_grup_adi=record["ust_grup_adi"],
        fonksiyon_kodu=record["fonksiyon_kodu"],
        fonksiyon_adi=record["fonksiyon_adi"],
        geometri=record["geometri"],
        matched_as=matched_as,
    )
