# -*- coding: utf-8 -*-
"""Netcad 8 Smart Object property bag.

A Netcad 8 Smart Object (geometry type 15) - the building-rights notation of an
imar plan (nizam / kat / setbacks, TAKS / KAKS / emsal / Hmax) and the road width
mark - carries its values after the geometry, in a list the block header does
not count (``blocks.scan_blocks`` absorbs it to keep the stream aligned).

Format, as read from real municipal files (TIRE_MERKEZ UIP, Netcad 8)::

    entry := <u8 len> key            ASCII identifier, e.g. "kat", "txtOn"
             <u8 type>               0x12 text, 0x0F / 0x09 number as text,
                                     0x03 boolean as text ("True"/"False")
             <u8 len> value          UTF-8 text, may be empty
             <u8 len> display name   UTF-8, e.g. "Kat", "Ön"
             <7 bytes>               01 00 00 00 00 00 xx

Each value entry is paired with a ``chk<Name>IsNull`` flag entry that has the
*same display name*; the key names do not line up ("txtOn" / "chkOnIsNull",
"yEncok" / "chkYEnCokIsNull"), the display names do. A value whose flag is
"True" is unset in Netcad and is not returned.
"""
from __future__ import annotations

VALUE_TYPES = frozenset((0x03, 0x09, 0x0F, 0x12))
# Offset where the property list can start: after the fixed geometry fields.
PROPERTY_SEARCH_START = 140


def _entries(raw: bytes):
    """(key, value, display) for every well-formed entry in *raw*."""
    i, n = 0, len(raw)
    while i < n - 4:
        klen = raw[i]
        j = i + 1 + klen
        key = raw[i + 1:j]
        if (1 <= klen <= 40 and j + 2 < n and key.isascii() and key[:1].isalpha()
                and key.replace(b"_", b"").isalnum() and raw[j] in VALUE_TYPES):
            vlen = raw[j + 1]
            k = j + 2 + vlen
            if k < n and k + 1 + raw[k] <= n:
                value = raw[j + 2:k].decode("utf-8", "replace")
                display = raw[k + 1:k + 1 + raw[k]].decode("utf-8", "replace")
                yield key.decode("ascii"), value, display
                i = k + 1 + raw[k]
                continue
        i += 1


def parse_property_bag(raw: bytes) -> dict:
    """Set (non-null, non-empty) Smart Object properties, keyed by their Netcad key."""
    entries = list(_entries(raw))
    unset = {display for key, value, display in entries
             if key.startswith("chk") and key.endswith("IsNull") and value == "True"}
    return {key: value.strip() for key, value, display in entries
            if not (key.startswith("chk") and key.endswith("IsNull"))
            and display not in unset and value.strip() != ""}
