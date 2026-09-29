# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Fingerprinted on-disk cache for the NCZ v2 layer catalog.

The cache stores a drawing's decoded metadata, its lightweight per-layer
catalog, and its attribute tables so that reopening the same unchanged file
shows its layer tree instantly, without reading the file bytes or scanning
its blocks. Geometry is still decoded from the file on import.

The cache is a best-effort optimization: any read/write/validation error is
swallowed and the caller simply rebuilds the index. Content is stored as
JSON (never pickle) under a per-user cache directory. Invalidation is by a
``(size, mtime_ns)`` fingerprint, :data:`CACHE_VERSION`, and a hash of the
decoder sources themselves (:func:`engine_signature`).

The decoder hash is what keeps the cache honest: the Netcad 8 Smart Object
realignment (3.2.0) changed which layers a drawing has, but the version number
was not bumped, so drawings opened before it kept showing their old, shorter
layer list — K34C10B4C.NCZ offered 12 of its 28 layers, without SM_YAPILASMA
(emsal / yençok), SM_YOL, SNR_YAPIYAK or KALDIRIM. Any change to a decoder file
now makes every stored catalog a miss.
"""
from __future__ import annotations

import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path

from .blocks import DrawingMetadata

# Bump when the cached layout changes. Decoder changes are caught by
# engine_signature() without a bump.
CACHE_VERSION = 3

# The files whose code decides what a catalog contains.
_ENGINE_FILES = ("blocks.py", "parser.py", "geometry.py", "properties.py", "cache.py")
_ENGINE_SIGNATURE = None


def engine_signature() -> str:
    """Hash of the v2 decoder sources: a stored catalog is valid for this code only."""
    global _ENGINE_SIGNATURE
    if _ENGINE_SIGNATURE is None:
        digest = hashlib.sha256()
        here = Path(__file__).resolve().parent
        for name in _ENGINE_FILES:
            with suppress(OSError):
                digest.update(name.encode("ascii"))
                digest.update((here / name).read_bytes().replace(b"\r\n", b"\n"))
        _ENGINE_SIGNATURE = digest.hexdigest()[:16]
    return _ENGINE_SIGNATURE

_DISABLE_ENV = "ZERO2CADGIS_NCZ_CACHE_DISABLE"


def _cache_root() -> Path:
    base = (os.environ.get("LOCALAPPDATA")
            or os.environ.get("XDG_CACHE_HOME")
            or os.path.join(os.path.expanduser("~"), ".cache"))
    return Path(base) / "zero2cadgis" / "ncz_index"


def _is_disabled() -> bool:
    return os.environ.get(_DISABLE_ENV, "").strip().lower() in (
        "1", "true", "yes")


def _cache_file(file_path: str) -> Path:
    digest = hashlib.sha256(
        os.path.abspath(file_path).encode("utf-8", "surrogatepass")
    ).hexdigest()[:20]
    return _cache_root() / f"{digest}.json"


def fingerprint(file_path: str) -> dict:
    stat = os.stat(file_path)
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def load(file_path: str) -> dict | None:
    """Return the cached catalog for *file_path*, or None on any miss.

    On success the dict has keys ``metadata`` (DrawingMetadata),
    ``summaries`` (list[dict]) and ``attribute_tables`` (list[dict]).
    """
    if _is_disabled():
        return None
    try:
        current = fingerprint(file_path)
    except OSError:
        return None

    cache_file = _cache_file(file_path)
    try:
        with open(cache_file, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
    except (OSError, ValueError):
        return None

    if stored.get("cache_version") != CACHE_VERSION:
        return None
    if stored.get("engine") != engine_signature():
        return None
    if stored.get("fingerprint") != current:
        return None

    try:
        metadata = DrawingMetadata.from_dict(stored["metadata"])
        summaries = list(stored["summaries"])
        attribute_tables = stored.get("attribute_tables", [])
    except (KeyError, TypeError):
        return None

    return {
        "metadata": metadata,
        "summaries": summaries,
        "attribute_tables": attribute_tables,
    }


def save(file_path: str, metadata: DrawingMetadata,
         summaries: list[dict], attribute_tables: list[dict]) -> None:
    """Persist a catalog for *file_path*. Silent on any failure."""
    if _is_disabled():
        return
    try:
        current = fingerprint(file_path)
    except OSError:
        return

    payload = {
        "cache_version": CACHE_VERSION,
        "engine": engine_signature(),
        "fingerprint": current,
        "source": os.path.basename(file_path),
        "metadata": metadata.to_dict(),
        "summaries": summaries,
        "attribute_tables": attribute_tables,
    }

    cache_file = _cache_file(file_path)
    with suppress(OSError, TypeError, ValueError):
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
        os.replace(tmp, cache_file)


def clear() -> int:
    """Delete all cached indexes. Returns the number of files removed."""
    removed = 0
    root = _cache_root()
    if not root.is_dir():
        return 0
    for entry in root.glob("*.json"):
        with suppress(OSError):
            entry.unlink()
            removed += 1
    return removed
