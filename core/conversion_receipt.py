# -*- coding: utf-8 -*-
"""Human-readable, dependency-free conversion receipts."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ConvertedLayer:
    name: str
    geometry: str
    feature_count: int
    crs: str


def build_conversion_receipt(
        source: str,
        mode: str,
        destination: str,
        target_crs: str,
        layers: Iterable[ConvertedLayer],
        warnings: Sequence[str] = (),
        completed_at: datetime | None = None) -> str:
    """Return a copy-ready audit record for a completed import."""
    rows = list(layers)
    moment = completed_at or datetime.now().astimezone()
    if moment.tzinfo is None:
        moment = moment.astimezone()
    stamp = moment.isoformat(timespec="seconds")
    known_counts = [row.feature_count for row in rows if row.feature_count >= 0]
    total = sum(known_counts)
    count_note = str(total) if len(known_counts) == len(rows) else f"{total}+"
    lines = [
        "02CadGis conversion receipt",
        f"Completed: {stamp}",
        f"Source: {os.path.abspath(source)}",
        f"Mode: {mode}",
        f"Destination: {destination}",
        f"Target CRS: {target_crs or 'source CRS / on-the-fly'}",
        f"Result: {len(rows)} layer(s), {count_note} feature(s)",
        "",
        "Layers:",
    ]
    if rows:
        for row in rows:
            count = "unknown" if row.feature_count < 0 else f"{row.feature_count:,}"
            lines.append(
                f"- {row.name} | {row.geometry} | {count} features | {row.crs or 'unknown CRS'}")
    else:
        lines.append("- No vector layers returned")
    if warnings:
        lines.extend(("", "Warnings:"))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)
