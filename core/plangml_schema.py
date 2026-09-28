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
from functools import lru_cache
import re
from typing import Optional

from .mpyy_catalog import MPYY_ALIASES, MPYY_TABAKA

_TR_MAP = str.maketrans({
    "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
    "ç": "C", "ğ": "G", "ı": "I", "ö": "O", "ş": "S", "ü": "U",
})

# Where a tabaka goes when the official catalog does not define one for it: CAD
# helper layers, and local names with no unambiguous official counterpart. It is
# deliberately the *only* group name here that is not the Ministry's own, so a
# layer tree never mixes official group names with near-identical invented ones.
UNCLASSIFIED_UPPER_GROUP = "DİĞER PLAN ALANLARI"


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


# A plan-revision drawing marks the function it proposes or adds with a suffix;
# the function itself is unchanged, so the suffix is dropped before lookup.
# `_IPTAL` (cancelled) and `_ITIRAZ` (objection) are deliberately NOT here: a
# cancelled or contested area is not that function, and handing it the live
# official code would put a cancelled KONUT into an export as a KONUT.
_REVISION_SUFFIXES = ("_ONERISI", "_ONERI", "_ILAVE", "_DEGISIKLIK")

# Official tabaka names carry one of these prefixes. A local name without one
# ("PARK", "CAMI") is tried as "PL_<name>" — only an exact official name counts.
_OFFICIAL_PREFIXES = ("PL_", "SNR_", "HAT_", "KST_", "YOL_")


def _normalize(name: Optional[str]) -> str:
    """Fold a CAD tabaka name onto the catalog's spelling."""
    if not name:
        return ""
    text = str(name).strip().translate(_TR_MAP).upper()
    key = re.sub(r"[^A-Z0-9]+", "_", text).strip("_")
    for suffix in _REVISION_SUFFIXES:
        if key.endswith(suffix) and len(key) > len(suffix):
            return key[:-len(suffix)]
    return key


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


def _resolve_variant(key: str) -> Optional[str]:
    """Official tabaka for a local spelling that is not itself official.

    Tried in order, each needing an *exact* official or alias hit:
    the alias table; the name with the ``PL_`` prefix a local drawing left off;
    and each of those with or without the ``_ALANI`` ("area") ending, which
    local drawings add and drop freely without changing the function.
    """
    stems = [key]
    if not key.startswith(_OFFICIAL_PREFIXES):
        stems.append("PL_" + key)
    candidates = []
    for stem in stems:
        candidates.append(stem)
        if stem.endswith("_ALANI"):
            candidates.append(stem[:-len("_ALANI")])
        else:
            candidates.append(stem + "_ALANI")
    for candidate in candidates:
        official = _alias_index().get(candidate) or _index().get(candidate)
        if official is not None:
            return official
    return None


@lru_cache(maxsize=4096)
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
        official = _resolve_variant(key)
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


def upper_group_of(tabaka_name: Optional[str]) -> str:
    """Official upper group a tabaka belongs to, for grouping layers.

    Always returns a name: the Ministry's when the tabaka has an official
    identity, and :data:`UNCLASSIFIED_UPPER_GROUP` when it does not.
    """
    identity = lookup_tabaka(tabaka_name)
    return identity.ust_grup_adi if identity else UNCLASSIFIED_UPPER_GROUP
