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
