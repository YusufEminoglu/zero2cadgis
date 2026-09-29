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

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = PLUGIN_ROOT / "styles" / "mpyy_centre_symbols.json"

SYMBOL_MM = {"UIP": 10.0, "NIP": 7.0, "CDP": 5.0,
             "MUIP": 10.0, "MNIP": 7.0, "MCDP25": 5.0, "MCDP100": 5.0}
MAX_ASPECT = 2.0
MIN_SIDE_MM = 2.5
MM_PER_PIXEL = 25.4 / 96.0
MEASURE_DPI = 384.0  # 0.07 mm a pixel: a 4 mm glyph scaled 2.4x stays within 0.2 mm


# The work is done on each rule symbol's XML (saveSymbol / loadSymbol), never on
# the symbol-layer objects inside it. A Python wrapper of a symbol layer that
# C++ deleted stays in sip's address map; a new layer allocated at that address
# is then handed back under the old wrapper and its old class. On QGIS 4 a
# centre marker came back as a QgsSimpleLineSymbolLayer ("no attribute
# sizeUnit") in about half the runs of the level suite, and the process died at
# exit (docs/TRAPS.md 4.7). A symbol saved to XML carries no such wrapper.
SIZE_OPTIONS = (("size", "size_unit"), ("offset", "offset_unit"), ("outline_width", "outline_width_unit"))


def _rule_symbols(renderer):
    """(label, symbol, setter) for every top-level symbol of ``renderer``, in rule order."""
    from qgis.core import QgsRuleBasedRenderer

    if isinstance(renderer, QgsRuleBasedRenderer):
        return [(rule.label(), rule.symbol(), rule.setSymbol)
                for rule in renderer.rootRule().children() if rule.symbol() is not None]
    if hasattr(renderer, "symbol") and renderer.symbol() is not None:
        return [("*", renderer.symbol(), renderer.setSymbol)]
    return []


def _symbol_element(symbol):
    from qgis.core import QgsReadWriteContext, QgsSymbolLayerUtils
    from qgis.PyQt.QtXml import QDomDocument

    document = QDomDocument()
    element = QgsSymbolLayerUtils.saveSymbol("s", symbol, document, QgsReadWriteContext())
    document.appendChild(element)
    return document, element


def _load(element):
    from qgis.core import QgsReadWriteContext, QgsSymbolLayerUtils

    return QgsSymbolLayerUtils.loadSymbol(element, QgsReadWriteContext())


def _children(element, tag):
    child = element.firstChildElement(tag)
    while not child.isNull():
        yield child
        child = child.nextSiblingElement(tag)


def _centre_elements(symbol_element):
    """Marker <symbol> elements of the CentroidFill layers under ``symbol_element``, in layer order."""
    found = []
    for layer in _children(symbol_element, "layer"):
        inner = layer.firstChildElement("symbol")
        if inner.isNull():
            continue
        if layer.attribute("class") == "CentroidFill":
            found.append(inner)
        else:
            found.extend(_centre_elements(inner))
    return found


def _options(layer_element):
    """name -> <Option> element of a symbol layer's property map."""
    options = layer_element.firstChildElement("Option")
    return {option.attribute("name"): option for option in _children(options, "Option")}


def _number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _rescale(marker_element, pixel_to_mm, factor):
    """Every size, offset and outline of a marker <symbol> element: pixels to mm, then times ``factor``."""
    for layer in _children(marker_element, "layer"):
        options = _options(layer)
        for value_name, unit_name in SIZE_OPTIONS:
            value, unit = options.get(value_name), options.get(unit_name)
            if value is None:
                continue
            ratio = factor
            if pixel_to_mm and unit is not None and unit.attribute("value") == "Pixel":
                ratio *= MM_PER_PIXEL
                unit.setAttribute("value", "MM")
            if ratio == 1.0:
                continue
            parts = [_number(part) for part in value.attribute("value").split(",")]
            if parts and all(part is not None for part in parts):
                value.setAttribute("value", ",".join(repr(part * ratio) for part in parts))


def centre_markers(renderer):
    """(rule label, marker symbol) for every centre marker, pixel sizes read as mm.

    Each marker is a new symbol loaded from XML, the caller's own: for
    measuring, never for editing the renderer.
    """
    found = []
    for label, symbol, _setter in _rule_symbols(renderer):
        document, element = _symbol_element(symbol)
        for marker_element in _centre_elements(element):
            _rescale(marker_element, True, 1.0)
            found.append((label, _load(marker_element)))
    return found


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
    rules = []
    labels = []
    for label, symbol, setter in _rule_symbols(renderer):
        document, element = _symbol_element(symbol)
        markers = _centre_elements(element)
        rules.append((setter, document, element, markers))
        labels.extend([label] * len(markers))
    if labels != [entry["kural"] for entry in entries]:
        return 0
    count = 0
    remaining = iter(entries)
    for setter, _document, element, markers in rules:
        if not markers:
            continue
        for marker_element in markers:
            factor = scale_factor(next(remaining)["murekkep_mm"], level)
            _rescale(marker_element, True, factor or 1.0)
            count += factor is not None
        rebuilt = _load(element)
        if rebuilt is not None:
            setter(rebuilt)
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
