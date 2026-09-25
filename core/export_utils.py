# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Small, QGIS-independent helpers for reliable dataset exports."""
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager, suppress
from dataclasses import dataclass


@dataclass(frozen=True)
class ExportResult:
    """Verified details of a completed export."""

    path: str
    driver: str
    feature_count: int
    target_crs: str
    bytes_written: int


@contextmanager
def atomic_output(output_path: str):
    """Publish a sibling temporary file only after a successful write."""
    final_path = os.path.abspath(output_path)
    folder = os.path.dirname(final_path)
    if not os.path.isdir(folder):
        raise ValueError(f"Output folder does not exist: {folder}")

    extension = os.path.splitext(final_path)[1]
    fd, temporary_path = tempfile.mkstemp(
        prefix=".zero2cadgis-export-", suffix=extension, dir=folder)
    os.close(fd)
    with suppress(OSError):
        os.remove(temporary_path)

    try:
        yield temporary_path
        if not os.path.isfile(temporary_path):
            raise ValueError("The export writer did not create an output file.")
        if os.path.getsize(temporary_path) <= 0:
            raise ValueError("The export writer created an empty output file.")
        os.replace(temporary_path, final_path)
    finally:
        with suppress(OSError):
            os.remove(temporary_path)


def exported_feature_count(layer, selected_only: bool) -> int:
    """Return the intended export count using QGIS' inexpensive counters."""
    if selected_only:
        return int(layer.selectedFeatureCount())
    return int(layer.featureCount())


def verified_export_result(
        output_path: str,
        driver: str,
        feature_count: int,
        target_crs: str) -> ExportResult:
    """Build a result only after the final file is present and non-empty."""
    final_path = os.path.abspath(output_path)
    size = os.path.getsize(final_path)
    if size <= 0:
        raise ValueError("Exported file is empty.")
    return ExportResult(
        path=final_path,
        driver=driver,
        feature_count=feature_count,
        target_crs=target_crs,
        bytes_written=size,
    )


def estimate_mbtiles_tile_count(extent, min_zoom: int, max_zoom: int) -> int:
    """Estimate total number of Web Mercator raster tiles for a bounding box.

    Supports QgsRectangle, ExtentBox, tuple/list (min_x, min_y, max_x, max_y),
    or any object exposing min_x/max_x or xMinimum()/xMaximum().
    """
    if extent is None:
        return 0
    if hasattr(extent, "isEmpty") and extent.isEmpty():
        return 0
    if hasattr(extent, "xMinimum"):
        min_x = extent.xMinimum()
        max_x = extent.xMaximum()
        min_y = extent.yMinimum()
        max_y = extent.yMaximum()
    elif hasattr(extent, "min_x"):
        min_x = extent.min_x
        max_x = extent.max_x
        min_y = extent.min_y
        max_y = extent.max_y
    elif isinstance(extent, (tuple, list)) and len(extent) >= 4:
        min_x, min_y, max_x, max_y = extent[:4]
    else:
        return 0

    x_min_world = -20037508.342789244
    world_size = 40075016.68557849
    total = 0
    min_x = max(float(min_x), -20037508.34)
    max_x = min(float(max_x), 20037508.34)
    min_y = max(float(min_y), -20037508.34)
    max_y = min(float(max_y), 20037508.34)
    if min_x >= max_x or min_y >= max_y:
        return 0
    for z in range(int(min_zoom), int(max_zoom) + 1):
        num_tiles = 1 << z
        tile_size = world_size / num_tiles
        c_min = max(0, min(num_tiles - 1, int((min_x - x_min_world) / tile_size)))
        c_max = max(0, min(num_tiles - 1, int((max_x - x_min_world) / tile_size)))
        r_min = max(0, min(num_tiles - 1, int((min_y - x_min_world) / tile_size)))
        r_max = max(0, min(num_tiles - 1, int((max_y - x_min_world) / tile_size)))
        total += (c_max - c_min + 1) * (r_max - r_min + 1)
    return total
