"""Area centre symbols drawn at the regulated sheet size of their plan level.

Ek-1e: "Sembol büyüklükleri: Çevre Düzeni Planı için 5 mm, Nazım İmar Planı için
7 mm, Uygulama İmar Planı için 10 mm'dir." The Ministry SLDs do not follow it: the
same pictogram is 15 mm at every level (3x the ÇDP size), a few are 30 mm, and
the ticaret family's boxes are 4 mm. The size an SLD asks for is not even the size
drawn, since a font glyph fills only part of its em box.

So the drawn ink of every centre marker (the sub-symbol of a CentroidFill) was
measured once, by rendering it at the level's scale
(``tools/measure_centre_symbols.py`` -> ``styles/mpyy_centre_symbols.json``), and
here each marker is scaled so the short side of its ink -- the frame of a framed
pictogram, not the caption under it -- is the regulated size. Pixel sizes are
turned into millimetres first: a pixel is a screen unit, 38 px is 10 mm on a
96 dpi screen but 3 mm on a 300 dpi print.

Only pictograms are scaled: a marker whose ink is more than twice as long as it
is high (the word "PARK") or whose short side is under 2.5 mm (a dot, a small
square) is a different kind of mark, and is left as the SLD draws it.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from qgis.core import Qgis

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = PLUGIN_ROOT / "styles" / "mpyy_centre_symbols.json"

SYMBOL_MM = {"UIP": 10.0, "NIP": 7.0, "CDP": 5.0,
             "MUIP": 10.0, "MNIP": 7.0, "MCDP25": 5.0, "MCDP100": 5.0}
MAX_ASPECT = 2.0
MIN_SIDE_MM = 2.5
MM_PER_PIXEL = 25.4 / 96.0
MEASURE_DPI = 384.0  # 0.07 mm a pixel: a 4 mm glyph scaled 2.4x stays within 0.2 mm


def centre_markers(renderer):
    """(rule label, CentroidFill symbol layer) for every centre marker, in rule order."""
    from qgis.core import QgsRuleBasedRenderer

    if isinstance(renderer, QgsRuleBasedRenderer):
        symbols = [(rule.label(), rule.symbol()) for rule in renderer.rootRule().children()]
    else:
        symbols = [("*", renderer.symbol())] if hasattr(renderer, "symbol") else []
    found = []
    for label, symbol in symbols:
        if symbol is not None:
            _collect(label, symbol, found)
    return found


def _collect(label, symbol, found):
    for index in range(symbol.symbolLayerCount()):
        layer = symbol.symbolLayer(index)
        sub = layer.subSymbol()
        if sub is None:
            continue
        if layer.layerType() == "CentroidFill":
            found.append((label, layer))
        else:
            _collect(label, sub, found)


def scale_factor(ink_mm, level):
    """Factor bringing a marker of ``ink_mm`` (width, height) to the level's size; None to leave it."""
    target = SYMBOL_MM.get(level)
    if target is None or not ink_mm:
        return None
    short, long = sorted(ink_mm)
    if short < MIN_SIDE_MM or long > MAX_ASPECT * short:
        return None
    return target / short


@lru_cache(maxsize=None)
def _table():
    if not TABLE_PATH.exists():
        return {}
    return json.loads(TABLE_PATH.read_text(encoding="utf-8"))["levels"]


def in_millimetres(marker):
    """Copy of ``marker`` with its pixel sizes and offsets as millimetres (same size at 96 dpi)."""
    marker = marker.clone()
    pixels = Qgis.RenderUnit.Pixels
    for index in range(marker.symbolLayerCount()):
        layer = marker.symbolLayer(index)
        if layer.sizeUnit() == pixels:
            layer.setSize(layer.size() * MM_PER_PIXEL)
            layer.setSizeUnit(Qgis.RenderUnit.Millimeters)
        if layer.offsetUnit() == pixels:
            offset = layer.offset()
            offset.setX(offset.x() * MM_PER_PIXEL)
            offset.setY(offset.y() * MM_PER_PIXEL)
            layer.setOffset(offset)
            layer.setOffsetUnit(Qgis.RenderUnit.Millimeters)
        if hasattr(layer, "strokeWidthUnit") and layer.strokeWidthUnit() == pixels:
            layer.setStrokeWidth(layer.strokeWidth() * MM_PER_PIXEL)
            layer.setStrokeWidthUnit(Qgis.RenderUnit.Millimeters)
    return marker


def scaled(marker, factor):
    """Copy of ``marker`` with every size, offset and stroke multiplied by ``factor``."""
    marker = marker.clone()
    for index in range(marker.symbolLayerCount()):
        layer = marker.symbolLayer(index)
        layer.setSize(layer.size() * factor)
        offset = layer.offset()
        offset.setX(offset.x() * factor)
        offset.setY(offset.y() * factor)
        layer.setOffset(offset)
        if hasattr(layer, "setStrokeWidth"):
            layer.setStrokeWidth(layer.strokeWidth() * factor)
    return marker


def apply_centre_symbol_sizes(layer, level, type_name):
    """Bring every centre pictogram of ``layer`` to the regulated size; returns how many were set.

    The measured table is keyed by rule label in rule order; a renderer that no
    longer lines up with it (a rule added or renamed since) is left untouched
    rather than scaled by another rule's measurement.
    """
    entries = _table().get(level, {}).get(type_name)
    renderer = layer.renderer()
    if not entries or renderer is None:
        return 0
    markers = centre_markers(renderer)
    if [label for label, _ in markers] != [entry["kural"] for entry in entries]:
        return 0
    count = 0
    for (label, holder), entry in zip(markers, entries):
        marker = in_millimetres(holder.subSymbol())
        factor = scale_factor(entry["murekkep_mm"], level)
        if factor is not None:
            marker = scaled(marker, factor)
            count += 1
        holder.setSubSymbol(marker)
    layer.setCustomProperty("mpyy/merkez_sembol_mm", f"{SYMBOL_MM.get(level)} mm ({count} sembol)")
    return count


def measure_ink(marker, scale, dpi=MEASURE_DPI, pixels=1400):
    """(width, height) in paper mm of what ``marker`` draws at ``scale``; None when nothing is drawn."""
    from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsMapRendererCustomPainterJob,
                           QgsMapSettings, QgsPointXY, QgsRectangle, QgsSingleSymbolRenderer, QgsVectorLayer)
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor, QImage, QPainter

    layer = QgsVectorLayer("Point?crs=EPSG:5254", "olcum", "memory")
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(500000, 4200000)))
    layer.dataProvider().addFeatures([feature])
    renderer = QgsSingleSymbolRenderer(marker.clone())
    renderer.setReferenceScale(scale)
    layer.setRenderer(renderer)
    settings = QgsMapSettings()
    settings.setLayers([layer])
    settings.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:5254"))
    settings.setOutputDpi(dpi)
    settings.setOutputSize(QSize(pixels, pixels))
    half = pixels / dpi * 0.0254 * scale / 2
    settings.setExtent(QgsRectangle(500000 - half, 4200000 - half, 500000 + half, 4200000 + half))
    settings.setBackgroundColor(QColor(0, 0, 0, 0))
    image = QImage(pixels, pixels, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    job = QgsMapRendererCustomPainterJob(settings, painter)
    job.renderSynchronously()
    painter.end()
    rows, columns = [], set()
    for y in range(pixels):
        line = bytes(image.constScanLine(y).asstring(pixels * 4))[3::4]
        hits = [x for x, alpha in enumerate(line) if alpha > 40]
        if hits:
            rows.append(y)
            columns.update((hits[0], hits[-1]))
    if not rows:
        return None
    mm = 25.4 / dpi
    return [round((max(columns) - min(columns) + 1) * mm, 2), round((rows[-1] - rows[0] + 1) * mm, 2)]
