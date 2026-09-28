"""Ek-1e Mekânsal Planlar Detay Katalogları on top of the Ministry SLD styles.

The catalog annexed to the regulation is the authority. Where the Ministry's GeoServer
SLDs disagree with it or reference assets that were never published, this module
corrects the QGIS symbols after the SLD has been loaded:

* symbols: an unpublished TaramaSembol SVG or a glyph of the unshipped Intelli Eplan
  font is replaced by the symbol cut from the catalog page (``resources/katalog_sembol``);
  rules the catalog gives a symbol and the SLD does not receive it;
* vectors: symbols the catalog defines by measurement (ÇDP idari merkezler, ÇDP yolları,
  bisiklet yolu) are drawn from those measurements;
* fills and hatches: colours taken from the catalog swatches, hatches the SLD lacks.

Every decision and its catalog page lives in ``styles/mpyy_detail_catalog/decisions.json``.
"""

import base64
import json
from functools import lru_cache
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsCentroidFillSymbolLayer,
    QgsFillSymbol,
    QgsGeometryGeneratorSymbolLayer,
    QgsHashedLineSymbolLayer,
    QgsLinePatternFillSymbolLayer,
    QgsLineSymbol,
    QgsMarkerLineSymbolLayer,
    QgsMarkerSymbol,
    QgsPointPatternFillSymbolLayer,
    QgsRasterMarkerSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = PLUGIN_ROOT / "styles" / "mpyy_detail_catalog"
CURRENT_OF = {"MUIP": "UIP", "MNIP": "NIP", "MCDP25": "CDP", "MCDP100": "CDP"}
MAP_METERS = Qgis.RenderUnit.MetersInMapUnits
LEVEL_SCALES = {
    "UIP": 1000,
    "NIP": 5000,
    "CDP": 25000,
    "MUIP": 1000,
    "MNIP": 5000,
    "MCDP25": 25000,
    "MCDP100": 100000,
}


def _level_scale(level):
    """Nominal plan denominator used to turn catalog paper mm into ground m."""
    configured = catalog()["decisions"].get("levels_scale", {})
    return float(configured.get(level, LEVEL_SCALES.get(level, 1000)))


def _ground_spec(spec, level):
    """Copy a catalog decision with every paper-mm measurement in ground metres.

    Ek-1e measurements describe the printed plan.  QGIS therefore needs
    ``millimetres * nominal scale / 1000`` in map metres.  Converting the
    decision once keeps widths, marker sizes, offsets, intervals, hatch spacing
    and dash arrays in the same unit instead of letting individual symbol
    builders drift apart.
    """
    factor = _level_scale(level) / 1000.0

    def convert(value, key=""):
        if isinstance(value, dict):
            return {child: convert(item, child) for child, item in value.items()}
        if isinstance(value, list):
            if key == "pattern" and all(
                isinstance(item, (int, float)) and not isinstance(item, bool)
                for item in value
            ):
                return [item * factor for item in value]
            return [convert(item) for item in value]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if key.endswith("_mm2"):
                return value * factor * factor
            if key.endswith("_mm"):
                return value * factor
        return value

    scaled = convert(spec)
    if isinstance(scaled, dict):
        scaled["_mm_factor"] = factor
    return scaled


def _set_dash(layer, values):
    """Apply a ground-metre dash vector, including its otherwise implicit unit."""
    layer.setCustomDashVector(values)
    layer.setCustomDashPatternUnit(MAP_METERS)
    layer.setUseCustomDashPattern(True)


@lru_cache(maxsize=1)
def catalog():
    decisions = json.loads((CATALOG_DIR / "decisions.json").read_text(encoding="utf-8"))
    extracted = json.loads((CATALOG_DIR / "symbols.json").read_text(encoding="utf-8"))["symbols"]
    by_svg, by_glyph = {}, {}
    for key, entry in decisions["symbols"].items():
        for name in entry.get("svg", []):
            by_svg[name] = key
        for glyph in entry.get("glyphs", []):
            by_glyph[glyph] = key
    return {"decisions": decisions, "symbols": extracted, "svg": by_svg, "glyph": by_glyph}


@lru_cache(maxsize=None)
def _image(key):
    entry = catalog()["symbols"][key]
    data = (PLUGIN_ROOT / entry["file"]).read_bytes()
    width, height = entry["pixels"]
    return "base64:" + base64.b64encode(data).decode("ascii"), height / width


def raster_marker(key, height, unit, angle=0.0):
    """The catalog symbol ``key`` as a marker ``height`` tall (width follows the image)."""
    path, aspect = _image(key)
    marker = QgsRasterMarkerSymbolLayer(path, height / aspect, angle)
    marker.setFixedAspectRatio(aspect)
    marker.setSizeUnit(unit)
    return marker


def symbol_for_svg(name):
    return catalog()["svg"].get(name)


def symbol_for_glyph(family, character):
    return catalog()["glyph"].get(f"{family}#{character}")


def catalog_labels(level, type_name):
    """Label specs of the current level for this type (``labels`` in decisions.json)."""
    if level in CURRENT_OF:
        return []
    table = catalog()["decisions"].get("labels", {})
    return [spec for key, spec in table.items() if key == f"{level}/{type_name}/*"]


def _color(rgb):
    return QColor(*[int(v) for v in rgb.split("/")])


def _specs(section, level, type_name, label, include_borrowed):
    """Specs of ``section`` that apply to this rule, most specific key first."""
    table = catalog()["decisions"].get(section, {})
    levels = [level]
    if include_borrowed and level in CURRENT_OF:
        levels.append(CURRENT_OF[level])
    for candidate in levels:
        for key in (f"{candidate}/{type_name}/{label}", f"{candidate}/{type_name}/*"):
            if key in table:
                yield key, table[key]
                break
        else:
            continue
        break


def _rules(renderer):
    """(label, getter, setter) for every rule of a rule-based or single-symbol renderer."""
    if renderer is None:
        return []
    if renderer.type() == "RuleRenderer":
        return [(rule.label(), rule.symbol, rule.setSymbol) for rule in renderer.rootRule().children() if rule.symbol()]
    if hasattr(renderer, "symbol") and renderer.symbol() is not None:
        return [("*", renderer.symbol, renderer.setSymbol)]
    return []


def _merkez(spec):
    outer = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["outer_m"])
    outer.setSizeUnit(MAP_METERS)
    outer.setColor(_color(spec["ring"]))
    outer.setStrokeColor(_color(spec["color"]))
    outer.setStrokeWidth(spec["stroke_mm"])
    outer.setStrokeWidthUnit(MAP_METERS)
    inner = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["inner_m"])
    inner.setSizeUnit(MAP_METERS)
    inner.setColor(_color(spec["color"]))
    inner.setStrokeStyle(Qt.PenStyle.NoPen)
    return QgsMarkerSymbol([outer, inner])


def _line(color, width):
    layer = QgsSimpleLineSymbolLayer(_color(color), width)
    layer.setWidthUnit(MAP_METERS)
    return layer


def _line_solid(spec):
    return QgsLineSymbol([_line(spec["color"], spec["width_mm"])])


def _line_dashed(spec):
    layer = _line(spec["color"], spec["width_mm"])
    _set_dash(layer, spec.get("pattern") or [spec["dash_mm"], spec["gap_mm"]])
    return QgsLineSymbol([layer])


def _line_ties(spec):
    """A rail line with perpendicular 'sleeper' ties every interval (Demiryolu: s.157, '2mm x 5mm
    ölçülerinde içi dolu dikdörtgen, 2mm düz çizgi' -- a filled rectangle drawn as a thick
    perpendicular bar, ``tie_mm`` long and ``thickness_mm`` wide along the line). ``fills``
    (default all filled) alternates hollow/filled ties for e.g. Hızlı Tren Hattı's 'bir dolu bir
    boş dikdörtgen'. ``side_rail_offset_mm`` adds two parallel side rails next to the ties
    (Raylı Toplu Taşıma Hattı: 'dikdörtgenlerin uzun kenarına ... paralel düz çizgiler')."""
    tie_mm, thickness_mm, gap_mm = spec["tie_mm"], spec["thickness_mm"], spec["gap_mm"]
    fills = spec.get("fills", [True])
    n = len(fills)
    cycle_mm = n * (thickness_mm + gap_mm)

    layers = [_line(spec["color"], spec["width_mm"])]
    offsets = spec.get("side_rail_offsets_mm")
    if offsets is None and spec.get("side_rail_offset_mm"):
        offsets = [spec["side_rail_offset_mm"]]
    for offset in offsets or []:
        for side in (-offset, offset):
            rail = _line(spec["color"], spec["width_mm"])
            rail.setOffset(side)
            rail.setOffsetUnit(MAP_METERS)
            layers.append(rail)

    hairline_mm = min(0.3 * spec["_mm_factor"], thickness_mm / 4)
    for i, filled in enumerate(fills):
        base_offset = i * (thickness_mm + gap_mm)
        if filled:
            tie = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Line, tie_mm)
            tie.setSizeUnit(MAP_METERS)
            tie.setColor(_color(spec["color"]))
            tie.setStrokeColor(_color(spec["color"]))
            tie.setStrokeWidth(thickness_mm)
            tie.setStrokeWidthUnit(MAP_METERS)
            marks = _marker_at(QgsMarkerSymbol([tie]), cycle_mm, base_offset)
            layers.append(marks)
        else:
            # An unfilled 'boş dikdörtgen' is just its two long edges: two hairline
            # perpendicular marks, one at each side of the thickness_mm span.
            for edge_offset in (0.0, thickness_mm - hairline_mm):
                edge = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Line, tie_mm)
                edge.setSizeUnit(MAP_METERS)
                edge.setColor(_color(spec["color"]))
                edge.setStrokeColor(_color(spec["color"]))
                edge.setStrokeWidth(hairline_mm)
                edge.setStrokeWidthUnit(MAP_METERS)
                marks = _marker_at(QgsMarkerSymbol([edge]), cycle_mm, base_offset + edge_offset)
                layers.append(marks)
    return QgsLineSymbol(layers)


def _line_overlay(spec):
    """A thin line drawn centred on top of a wider one (3. Derece Yol: s.150, '1mm siyah çizgi
    üzerine, 0.4mm sarı çizgi')."""
    return QgsLineSymbol([
        _line(spec["color"], spec["width_mm"]),
        _line(spec["overlay_color"], spec["overlay_width_mm"]),
    ])


_LINE_MARK_SHAPES = {
    "triangle": Qgis.MarkerShape.EquilateralTriangle,
    "arrow": Qgis.MarkerShape.ArrowHeadFilled,
}


def _line_marked(spec):
    """A line (solid, or dashed when ``dash_mm``/``gap_mm`` given) with a repeating marker every
    ``interval_mm`` (Boru Hattı, Doğalgaz/Akaryakıt Boru Hattı: s.180-181, 'düz/kesikli çizgi
    üzerinde N mm aralıklı kenar uzunluğu M mm eşkenar üçgenler' -- flow-direction chevrons).
    ``shape`` picks üçgen/ok (default üçgen); ``filled`` False hollow-outlines the marker (Atık
    Su Derin Deniz Deşarj Hattı: s.186, 'içi boş')."""
    rail = _line(spec["color"], spec["width_mm"])
    if spec.get("dash_mm"):
        _set_dash(rail, [spec["dash_mm"], spec["gap_mm"]])
    mark = QgsSimpleMarkerSymbolLayer(_LINE_MARK_SHAPES[spec.get("shape", "triangle")], spec["mark_mm"])
    mark.setSizeUnit(MAP_METERS)
    if spec.get("filled", True):
        mark.setColor(_color(spec["color"]))
        mark.setStrokeStyle(Qt.PenStyle.NoPen)
    else:
        mark.setColor(QColor(0, 0, 0, 0))
        mark.setStrokeColor(_color(spec["color"]))
        mark.setStrokeWidth(spec["width_mm"])
        mark.setStrokeWidthUnit(MAP_METERS)
    marks = QgsMarkerLineSymbolLayer(True)  # rotateSymbol: the marker points along the line
    marks.setInterval(spec["interval_mm"])
    marks.setIntervalUnit(MAP_METERS)
    marks.setSubSymbol(QgsMarkerSymbol([mark]))
    return QgsLineSymbol([rail, marks])


def _line_circles(spec):
    """A base line with a chain of hollow circles tangent to it (İçme Suyu Ana İletim Hattı:
    s.184, '10mm aralıklı 2.5mm çaplı içi boş daireler, bu dairelere teğet düz çizgi' -- the
    circles sit beside the line, not centred on it, so each is offset outward by its own radius)."""
    from qgis.PyQt.QtCore import QPointF

    circle = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["dot_mm"])
    circle.setSizeUnit(MAP_METERS)
    circle.setColor(QColor(0, 0, 0, 0))
    circle.setStrokeColor(_color(spec["color"]))
    circle.setStrokeWidth(spec["dot_width_mm"])
    circle.setStrokeWidthUnit(MAP_METERS)
    circle.setOffset(QPointF(0, spec["dot_mm"] / 2))
    circle.setOffsetUnit(MAP_METERS)
    marks = _marker_at(QgsMarkerSymbol([circle]), spec["interval_mm"], 0.0)
    return QgsLineSymbol([_line(spec["color"], spec["width_mm"]), marks])


def _line_ticks(spec):
    """A plain line with a short perpendicular tick every interval, no rectangle (Bisiklet Yolu:
    s.153, '3mm aralıklı paralel düz çizgiler ile yola dik olacak şekilde tarama')."""
    tick = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Line, spec["tick_mm"])
    tick.setSizeUnit(MAP_METERS)
    tick.setColor(_color(spec["color"]))
    tick.setStrokeColor(_color(spec["color"]))
    tick.setStrokeWidth(spec["width_mm"])
    tick.setStrokeWidthUnit(MAP_METERS)
    return QgsLineSymbol([
        _line(spec["color"], spec["width_mm"]),
        _marker_at(QgsMarkerSymbol([tick]), spec["interval_mm"], 0.0),
    ])


def _line_tick_tie(spec):
    """A plain line with a short perpendicular tick every interval, a rectangle centred on each
    tick (Havai Hat / Havaray: s.170-171, 'çizgiye dik ... çizgiler, bu çizgilere ... bağlanmış
    ... dikdörtgenler'); ``filled`` picks a hollow rectangle (Havaray) or solid (Havai Hat)."""
    tick = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Line, spec["tick_mm"])
    tick.setSizeUnit(MAP_METERS)
    tick.setColor(_color(spec["color"]))
    tick.setStrokeColor(_color(spec["color"]))
    tick.setStrokeWidth(spec["width_mm"])
    tick.setStrokeWidthUnit(MAP_METERS)

    box = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Line, spec["box_mm"])
    box.setSizeUnit(MAP_METERS)
    box.setStrokeColor(_color(spec["color"]))
    box.setStrokeWidth(spec["box_thickness_mm"])
    box.setStrokeWidthUnit(MAP_METERS)
    box.setAngle(90)  # along the line, crossing the tick at its middle
    if spec.get("filled", True):
        box.setColor(_color(spec["color"]))
    else:
        box.setColor(QColor(0, 0, 0, 0))

    mark = QgsMarkerSymbol([tick, box])
    return QgsLineSymbol([
        _line(spec["color"], spec["width_mm"]),
        _marker_at(mark, spec["interval_mm"], 0.0),
    ])


def _road(spec):
    # cephe çizgileri outside the road body, kaldırım between them, yol platformu in the middle
    return QgsLineSymbol([
        _line(spec["color"], spec["total_mm"] + 2 * spec["cephe_mm"]),
        _line(spec["kaldirim"], spec["total_mm"]),
        _line(spec["color"], spec["platform_mm"]),
    ])


def _ladder(spec):
    layers = []
    for offset in (-spec["rung_mm"] / 2, spec["rung_mm"] / 2):
        rail = _line(spec["color"], spec["width_mm"])
        rail.setOffset(offset)
        rail.setOffsetUnit(MAP_METERS)
        layers.append(rail)
    rung = QgsHashedLineSymbolLayer()
    rung.setInterval(spec["interval_mm"])
    rung.setIntervalUnit(MAP_METERS)
    rung.setHashLength(spec["rung_mm"])
    rung.setHashLengthUnit(MAP_METERS)
    rung.setSubSymbol(QgsLineSymbol([_line(spec["color"], spec["width_mm"])]))
    layers.append(rung)
    badge = QgsMarkerLineSymbolLayer()
    badge.setPlacements(Qgis.MarkerLinePlacement.CentralPoint)
    badge.setSubSymbol(QgsMarkerSymbol([raster_marker(spec["symbol"], spec["symbol_mm"], MAP_METERS)]))
    layers.append(badge)
    return QgsLineSymbol(layers)


def _vertex_chain(spec):
    """Sahil Şeridi / Kıyı Kenar Çizgisi: a plain line through the surveyed coordinate points,
    with a (hollow or filled) circle stamped on each of those vertices."""
    dot = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["dot_mm"])
    dot.setSizeUnit(MAP_METERS)
    if spec.get("filled", True):
        dot.setColor(_color(spec["color"]))
        dot.setStrokeStyle(Qt.PenStyle.NoPen)
    else:
        dot.setColor(QColor(0, 0, 0, 0))
        dot.setStrokeColor(_color(spec["color"]))
        dot.setStrokeWidth(spec["width_mm"])
        dot.setStrokeWidthUnit(MAP_METERS)
    vertices = QgsMarkerLineSymbolLayer()
    vertices.setPlacements(Qgis.MarkerLinePlacement.Vertex)
    vertices.setSubSymbol(QgsMarkerSymbol([dot]))
    return QgsLineSymbol([_line(spec["color"], spec["width_mm"]), vertices])


def _pattern(marker, spacing_mm):
    fill = QgsPointPatternFillSymbolLayer()
    fill.setDistanceX(spacing_mm)
    fill.setDistanceY(spacing_mm)
    fill.setDistanceXUnit(MAP_METERS)
    fill.setDistanceYUnit(MAP_METERS)
    fill.setSubSymbol(QgsMarkerSymbol([marker]))
    return fill


def _dot(spec):
    dot = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["dot_mm"])
    dot.setSizeUnit(MAP_METERS)
    dot.setColor(_color(spec["color"]))
    dot.setStrokeStyle(Qt.PenStyle.NoPen)
    return dot


def _hatch(symbol, spec, level, type_name, geometry_type):
    kind = spec["kind"]
    if kind == "motif":
        if "keep_fills" in spec:
            fills = [i for i in range(symbol.symbolLayerCount()) if symbol.symbolLayer(i).layerType() == "SimpleFill"]
            for index in reversed(fills[spec["keep_fills"]:]):  # grey stand-ins for the dropped SVG hatch
                symbol.deleteSymbolLayer(index)
        symbol.appendSymbolLayer(_pattern(raster_marker(spec["motif"], spec["size_mm"], MAP_METERS), spec["spacing_mm"]))
    elif kind == "dots":
        symbol.appendSymbolLayer(_pattern(_dot(spec), spec["spacing_mm"]))
    elif kind == "random_dots":
        from qgis.core import QgsRandomMarkerFillSymbolLayer

        for index in range(symbol.symbolLayerCount()):
            if symbol.symbolLayer(index).layerType() == "SimpleFill":
                symbol.symbolLayer(index).setColor(_color(spec["fill"]))
                break
        random_fill = QgsRandomMarkerFillSymbolLayer(1, Qgis.PointCountMethod.DensityBasedCount, spec["area_per_dot_mm2"], 1)
        random_fill.setDensityAreaUnit(MAP_METERS)
        random_fill.setSubSymbol(QgsMarkerSymbol([_dot(spec)]))
        symbol.appendSymbolLayer(random_fill)
    elif kind == "tile":
        from qgis.core import QgsRasterFillSymbolLayer

        path, _ = _image(spec["tile"])
        tile = QgsRasterFillSymbolLayer(path)
        tile.setWidth(
            catalog()["symbols"][spec["tile"]]["width_mm"] * spec["_mm_factor"]
        )
        tile.setSizeUnit(MAP_METERS)
        symbol.appendSymbolLayer(tile)
    elif kind == "double_lines":
        # Kentsel arkeolojik sit (s.83): 1 mm aralıklı çift yatay çizgi,
        # çiftler arasında 3 mm. The official SLD omits this fill entirely.
        for index in reversed(range(symbol.symbolLayerCount())):
            if symbol.symbolLayer(index).layerType() in ("PointPatternFill", "RasterFill", "LinePatternFill"):
                symbol.deleteSymbolLayer(index)
        for offset in (0.0, spec["pair_gap_mm"]):
            pattern = QgsLinePatternFillSymbolLayer()
            pattern.setLineAngle(spec.get("angle_deg", 0.0))
            pattern.setDistance(spec["spacing_mm"])
            pattern.setDistanceUnit(MAP_METERS)
            pattern.setOffset(offset)
            pattern.setOffsetUnit(MAP_METERS)
            pattern.setSubSymbol(QgsLineSymbol([_line(spec["color"], spec["width_mm"])]))
            symbol.appendSymbolLayer(pattern)
    elif kind == "copy":
        source = _copied_symbol(spec["from"], geometry_type)
        if source is not None:
            return source
    return symbol


def _copied_symbol(address, geometry_type):
    from qgis.core import QgsVectorLayer

    from .mpyy_workspace import apply_eplan_symbology

    level, type_name, label = address.split("/", 2)
    kinds = {Qgis.GeometryType.Polygon: "MultiPolygon", Qgis.GeometryType.Line: "MultiLineString", Qgis.GeometryType.Point: "Point"}
    probe = QgsVectorLayer(f"{kinds[geometry_type]}?crs=EPSG:5254", "katalog", "memory")
    if not apply_eplan_symbology(probe, level, type_name, centre_sizes=False):  # sized once, by the copying type
        return None
    for rule_label, getter, _ in _rules(probe.renderer()):
        if rule_label == label:
            return getter().clone()
    return None


def _added_symbol(symbol, key, level, geometry_type):
    entry = catalog()["symbols"][key]
    scale = _level_scale(level)
    marker = raster_marker(key, entry["height_mm"] * scale / 1000, MAP_METERS)
    if geometry_type == Qgis.GeometryType.Polygon:
        centroid = QgsCentroidFillSymbolLayer()
        centroid.setPointOnSurface(True)
        centroid.setSubSymbol(QgsMarkerSymbol([marker]))
        symbol.appendSymbolLayer(centroid)
    elif geometry_type == Qgis.GeometryType.Line:
        middle = QgsMarkerLineSymbolLayer()
        middle.setPlacements(Qgis.MarkerLinePlacement.CentralPoint)
        middle.setSubSymbol(QgsMarkerSymbol([marker]))
        symbol.appendSymbolLayer(middle)


def _clear_border(symbol):
    for index in reversed(range(symbol.symbolLayerCount())):
        if symbol.symbolLayer(index).layerType() in ("MarkerLine", "SimpleLine"):
            symbol.deleteSymbolLayer(index)  # the SLD's own attempt at this boundary


def _as_boundary(symbol, layers):
    """Redraw the polygon's outline (``boundary($geometry)``) with each of ``layers`` stacked on it."""
    _clear_border(symbol)
    for layer in layers:
        generator = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": "boundary($geometry)", "SymbolType": "Line"})
        generator.setSubSymbol(QgsLineSymbol([layer]))
        symbol.appendSymbolLayer(generator)


def _marker_at(marker_symbol, interval_mm, offset_mm):
    """One mark of ``marker_symbol`` repeated every ``interval_mm``, the first at ``offset_mm``."""
    marks = QgsMarkerLineSymbolLayer(True)
    marks.setInterval(interval_mm)
    marks.setIntervalUnit(MAP_METERS)
    marks.setOffsetAlongLine(offset_mm)
    marks.setOffsetAlongLineUnit(MAP_METERS)
    marks.setSubSymbol(marker_symbol)
    return marks


def _dot_cluster(color, dot_mm, count, spacing_mm, shape="circle", fills=None, width_mm=None, inner_dot_mm=None):
    """``count`` marks (``shape``: circle/square/cross...) ``dot_mm`` wide, ``spacing_mm`` apart
    centre-to-centre-minus-width, laid out along the line (offset X, after
    ``QgsMarkerLineSymbolLayer`` rotates the marker to it) and centred on the marker's own
    origin. ``fills`` (one bool per mark, default all filled) picks hollow marks for e.g.
    ÖÇK Bölgesi Hassas Alan's 'biri dolu' cluster (hollow-filled-hollow). ``inner_dot_mm`` adds a
    small filled dot inside each mark (İçme ve Kullanma Suyu Koruma Alanı: 'içi noktalı daire')."""
    from qgis.PyQt.QtCore import QPointF

    fills = fills if fills is not None else [True] * count
    cluster = QgsMarkerSymbol()
    while cluster.symbolLayerCount():
        cluster.takeSymbolLayer(0)
    step = dot_mm + spacing_mm
    for i in range(count):
        dot = QgsSimpleMarkerSymbolLayer(_MARKER_SHAPES.get(shape, Qgis.MarkerShape.Circle), dot_mm)
        dot.setSizeUnit(MAP_METERS)
        if fills[i]:
            dot.setColor(_color(color))
            dot.setStrokeStyle(Qt.PenStyle.NoPen)
        else:
            dot.setColor(QColor(0, 0, 0, 0))
            dot.setStrokeColor(_color(color))
            dot.setStrokeWidth(width_mm or 0.3)
            dot.setStrokeWidthUnit(MAP_METERS)
        offset_x = (i - (count - 1) / 2.0) * step
        dot.setOffset(QPointF(offset_x, 0))
        dot.setOffsetUnit(MAP_METERS)
        cluster.appendSymbolLayer(dot)
        if inner_dot_mm:
            inner = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, inner_dot_mm)
            inner.setSizeUnit(MAP_METERS)
            inner.setColor(_color(color))
            inner.setStrokeStyle(Qt.PenStyle.NoPen)
            inner.setOffset(QPointF(offset_x, 0))
            inner.setOffsetUnit(MAP_METERS)
            cluster.appendSymbolLayer(inner)
    return cluster


def _border_solid(symbol, spec):
    """A plain solid line, no dash, no marks (Tescilli Anıt Yapı/Bina/Parsel/Tabiat Varlığı: s.77-79,
    'sınırı tanımlayan düz çizgi')."""
    _as_boundary(symbol, [_line(spec["color"], spec["width_mm"])])


def _border_dashed(symbol, spec):
    """A plain dash-gap line, no marks (Mevcut Plandaki Durumu Korunacak / Yeniden Düzenlenecek /
    Sağlıklaştırma Alanı Sınırı: s.17-18, 'X mm çizgi, Y mm ara, X mm çizgi' is just a dash)."""
    outline = _line(spec["color"], spec["width_mm"])
    _set_dash(outline, [spec["dash_mm"], spec["gap_mm"]])
    _as_boundary(symbol, [outline])


_MARKER_SHAPES = {
    "cross2": Qgis.MarkerShape.Cross2,  # çarpı / X (Askeri Yasak ve Güvenlik Bölgesi)
    "cross": Qgis.MarkerShape.Cross,  # artı / + (Gecekondu Önleme, Toplu Konut Alanı Sınırı)
    "square": Qgis.MarkerShape.Square,
    "line": Qgis.MarkerShape.Line,  # dik çentik (Havaalanı Hava Koridoru)
}


def _border_cross(symbol, spec):
    """A continuous line with one mark every interval: ``shape`` picks çarpı/artı/kare (default
    çarpı, AYB); an optional ``ring_mm`` draws a hollow circle around the mark (Toplu Konut Alanı
    Sınırı: 'daire içinde artılar')."""
    outline = _line(spec["color"], spec["width_mm"])
    mark = QgsSimpleMarkerSymbolLayer(_MARKER_SHAPES[spec.get("shape", "cross2")], spec["size_mm"])
    mark.setSizeUnit(MAP_METERS)
    mark.setColor(_color(spec["color"]))
    mark.setStrokeColor(_color(spec["color"]))
    mark.setStrokeWidth(spec["width_mm"])
    mark.setStrokeWidthUnit(MAP_METERS)
    layers = [mark]
    if spec.get("ring_mm"):
        ring = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["ring_mm"])
        ring.setSizeUnit(MAP_METERS)
        ring.setColor(QColor(0, 0, 0, 0))
        ring.setStrokeColor(_color(spec["color"]))
        ring.setStrokeWidth(spec["width_mm"])
        ring.setStrokeWidthUnit(MAP_METERS)
        layers.append(ring)
    marks = QgsMarkerLineSymbolLayer()
    # The annex describes 2 mm as the *clear gap* after a 3 mm mark, not
    # its centre-to-centre interval.  The old 2 mm implementation made the
    # marks overlap, most visibly for Toplu Konut and Gecekondu Önleme.
    interval = spec.get("interval_mm", 0.0)
    if "gap_mm" in spec:
        interval = max(spec["size_mm"], spec.get("ring_mm", 0.0)) + spec["gap_mm"]
    marks.setInterval(interval)
    marks.setIntervalUnit(MAP_METERS)
    marks.setSubSymbol(QgsMarkerSymbol(layers))
    _as_boundary(symbol, [outline, marks])


def _border_cross_cluster(symbol, spec):
    """Two hollow circle-plus marks after a solid segment (TM/KTKGB, s.20)."""
    from qgis.PyQt.QtCore import QPointF

    circle_mm = spec["circle_mm"]
    cluster_gap = spec["cluster_gap_mm"]
    dash_mm = spec["dash_mm"]
    edge_gap = spec["edge_gap_mm"]
    cluster_width = circle_mm * 2 + cluster_gap
    cycle = dash_mm + edge_gap + cluster_width + edge_gap
    cluster = QgsMarkerSymbol()
    while cluster.symbolLayerCount():
        cluster.takeSymbolLayer(0)
    for offset_x in (-((circle_mm + cluster_gap) / 2.0), (circle_mm + cluster_gap) / 2.0):
        cross = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Cross, circle_mm)
        cross.setSizeUnit(MAP_METERS)
        cross.setColor(_color(spec["color"]))
        cross.setStrokeColor(_color(spec["color"]))
        cross.setStrokeWidth(spec["width_mm"])
        cross.setStrokeWidthUnit(MAP_METERS)
        cross.setOffset(QPointF(offset_x, 0))
        cross.setOffsetUnit(MAP_METERS)
        ring = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, circle_mm)
        ring.setSizeUnit(MAP_METERS)
        ring.setColor(QColor(0, 0, 0, 0))
        ring.setStrokeColor(_color(spec["color"]))
        ring.setStrokeWidth(spec["width_mm"])
        ring.setStrokeWidthUnit(MAP_METERS)
        ring.setOffset(QPointF(offset_x, 0))
        ring.setOffsetUnit(MAP_METERS)
        cluster.appendSymbolLayer(cross)
        cluster.appendSymbolLayer(ring)
    outline = _line(spec["color"], spec["width_mm"])
    _set_dash(outline, [dash_mm, cycle - dash_mm])
    _as_boundary(symbol, [outline, _marker_at(cluster, cycle, dash_mm + edge_gap + cluster_width / 2)])


def _border_dots(symbol, spec):
    """Ek-1e idari sınır deseni: çizgi - ara - N noktalık öbek - ara, tekrar (``gap_mm`` simetrik,
    veya ayrı ``gap_before_mm``/``gap_after_mm``). İsteğe bağlı ``flank_mm`` çizginin iki ucuna
    (Belediye/Mücavir Alan Sınırı) birer büyük nokta ekler, aralarında ara olmadan. İsteğe bağlı
    ``hatch`` (angle_deg/interval_mm/length_mm) sınırın tamamı boyunca eğik bir tarama ekler (Sit
    Alanları: 'çizgi eksenine 45 derece açılı ... tarama')."""
    dash_mm, dot_mm = spec["dash_mm"], spec["dot_mm"]
    count = spec["dot_count"]
    spacing_mm = spec.get("dot_spacing_mm", 0.0)
    gap_before = spec.get("gap_before_mm", spec.get("gap_mm", 0.0))
    gap_after = spec.get("gap_after_mm", gap_before)
    cluster_width = count * dot_mm + max(0, count - 1) * spacing_mm
    cycle_mm = dash_mm + gap_before + cluster_width + gap_after
    cluster_offset = dash_mm + gap_before + cluster_width / 2

    outline = _line(spec["color"], spec["width_mm"])
    _set_dash(outline, [dash_mm, cycle_mm - dash_mm])

    shape = spec.get("dot_shape", "circle")
    layers = [outline]
    flank_mm = spec.get("flank_mm")
    if flank_mm:
        layers.append(_marker_at(_dot_cluster(spec["color"], flank_mm, 1, 0.0, shape), cycle_mm, 0.0))
        layers.append(_marker_at(_dot_cluster(spec["color"], flank_mm, 1, 0.0, shape), cycle_mm, dash_mm))
    cluster = _dot_cluster(spec["color"], dot_mm, count, spacing_mm, shape, spec.get("fills"), spec["width_mm"], spec.get("inner_dot_mm"))
    layers.append(_marker_at(cluster, cycle_mm, cluster_offset))
    hatch = spec.get("hatch")
    if hatch:
        tick = QgsHashedLineSymbolLayer()
        tick.setInterval(hatch["interval_mm"])
        tick.setIntervalUnit(MAP_METERS)
        tick.setHashLength(hatch["length_mm"])
        tick.setHashLengthUnit(MAP_METERS)
        tick.setHashAngle(hatch["angle_deg"])
        tick.setSubSymbol(QgsLineSymbol([_line(spec["color"], spec["width_mm"])]))
        layers.append(tick)
    _as_boundary(symbol, layers)


def _border_tick_circle(symbol, spec):
    """Ek-1e ülke sınırı deseni: çizgi - dik çentik - (içi boş) daire - dik çentik, tekrar."""
    dash_mm, circle_mm, tick_mm = spec["dash_mm"], spec["circle_mm"], spec["tick_mm"]
    cycle_mm = dash_mm + circle_mm

    outline = _line(spec["color"], spec["width_mm"])
    _set_dash(outline, [dash_mm, circle_mm])

    def _tick():
        tick = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Line, tick_mm)
        tick.setSizeUnit(MAP_METERS)
        tick.setColor(_color(spec["color"]))
        tick.setStrokeColor(_color(spec["color"]))
        tick.setStrokeWidth(spec["width_mm"])
        tick.setStrokeWidthUnit(MAP_METERS)
        return QgsMarkerSymbol([tick])

    circle = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, circle_mm)
    circle.setSizeUnit(MAP_METERS)
    if spec.get("filled", True):
        circle.setColor(_color(spec["color"]))
        circle.setStrokeStyle(Qt.PenStyle.NoPen)
    else:
        circle.setColor(QColor(0, 0, 0, 0))
        circle.setStrokeColor(_color(spec["color"]))
        circle.setStrokeWidth(spec["width_mm"])
        circle.setStrokeWidthUnit(MAP_METERS)

    _as_boundary(symbol, [
        outline,
        _marker_at(_tick(), cycle_mm, 0.0),
        _marker_at(_tick(), cycle_mm, dash_mm),
        _marker_at(QgsMarkerSymbol([circle]), cycle_mm, dash_mm + circle_mm / 2),
    ])


def _border_circles(symbol, spec):
    """Ek-1e 'Planlama Sınırları' dizisi: eşit aralıklı daireler (hepsi dolu ya da hepsi boş,
    ya da 1 dolu 1 boş sırayla), isteğe bağlı ``dash_mm`` aradaki boşluğu bir çizgiyle doldurur
    (Özel Proje Alanı Sınırı); yoksa daireler arası boş kalır (Plan Onama, Etaplama Sınırı).
    ``continuous: true`` kesintisiz ince bir temel çizgi ekler (Yöresel Mimari Özellikleri
    Korunacak Alan: 'N mm aralıkla' -- kesik çizgi değil, düz çizgi üzerinde tekrarlayan daire)."""
    circle_mm = spec["circle_mm"]
    dash_mm = spec.get("dash_mm")
    gap_mm = spec.get("gap_mm", 0.0)
    cycle_mm = circle_mm + (dash_mm if dash_mm else gap_mm)

    layers = []
    if dash_mm:
        outline = _line(spec["color"], spec["width_mm"])
        _set_dash(outline, [dash_mm, cycle_mm - dash_mm])
        layers.append(outline)
    elif spec.get("continuous"):
        layers.append(_line(spec["color"], spec["width_mm"]))

    def _hollow(size_mm):
        mark = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, size_mm)
        mark.setSizeUnit(MAP_METERS)
        mark.setColor(QColor(0, 0, 0, 0))
        mark.setStrokeColor(_color(spec["color"]))
        mark.setStrokeWidth(spec["width_mm"])
        mark.setStrokeWidthUnit(MAP_METERS)
        return mark

    def _filled(size_mm):
        mark = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, size_mm)
        mark.setSizeUnit(MAP_METERS)
        mark.setColor(_color(spec["color"]))
        mark.setStrokeStyle(Qt.PenStyle.NoPen)
        return mark

    def _circle(filled):
        if spec.get("inner_mm"):  # concentric rings: hollow outer, inner hollow or filled
            # (İmar Hakkı Aktarım Alanı Sınırı: both hollow; Sit Etkileşim Geçiş: inner dolu)
            inner = _filled(spec["inner_mm"]) if spec.get("inner_filled") else _hollow(spec["inner_mm"])
            return QgsMarkerSymbol([_hollow(circle_mm), inner])
        if filled:
            mark = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, circle_mm)
            mark.setSizeUnit(MAP_METERS)
            mark.setColor(_color(spec["color"]))
            mark.setStrokeStyle(Qt.PenStyle.NoPen)
            return QgsMarkerSymbol([mark])
        return QgsMarkerSymbol([_hollow(circle_mm)])

    # The dash vector's own "on" segment always starts at boundary position 0, so when there is a
    # connecting dash it must come first in the cycle or it draws under the circle.
    circle_offset = (dash_mm or 0) + circle_mm / 2
    if spec.get("alternate"):
        layers.append(_marker_at(_circle(True), 2 * cycle_mm, circle_offset))
        layers.append(_marker_at(_circle(False), 2 * cycle_mm, circle_offset + cycle_mm))
    else:
        layers.append(_marker_at(_circle(spec.get("filled", True)), cycle_mm, circle_offset))
    _as_boundary(symbol, layers)


@lru_cache(maxsize=None)
def _gear_image(name):
    data = (CATALOG_DIR.parents[1] / "resources" / "katalog_sembol" / name).read_bytes()
    return "base64:" + base64.b64encode(data).decode("ascii")


def _gear_cluster(names, size_mm, count, spacing_mm):
    """``count`` gear images (``names``: one filename reused, or a list, one per gear), laid out
    along the line ``spacing_mm`` apart and centred on the marker's own origin."""
    from qgis.PyQt.QtCore import QPointF

    cluster = QgsMarkerSymbol()
    while cluster.symbolLayerCount():
        cluster.takeSymbolLayer(0)
    step = size_mm + spacing_mm
    for i in range(count):
        name = names if isinstance(names, str) else names[i]
        layer = QgsRasterMarkerSymbolLayer(_gear_image(name), size_mm)
        layer.setSizeUnit(MAP_METERS)
        layer.setOffset(QPointF((i - (count - 1) / 2.0) * step, 0))
        layer.setOffsetUnit(MAP_METERS)
        cluster.appendSymbolLayer(layer)
    return cluster


def _border_gears(symbol, spec):
    """Ek-1e 'dişli' sınır ailesi: bir dişli öbeği - ara - çizgi, tekrar (Teknoloji Geliştirme
    Bölgesi, Organize Sanayi Bölgesi, Endüstri Bölgesi); ``alternate_file`` verilince öbek yerine
    boş ve dolu dişli sırayla gelir (Serbest Bölge). Diş sayısı ve diş derinliği kataloğun
    ölçmediği bir çizim ayrıntısıdır; kataloğun küçük dişli simgesinden okunmuştur."""
    gear_mm = spec["gear_mm"]
    count = spec.get("gear_count", 1)
    cluster_spacing = spec.get("gear_spacing_mm", spec["_mm_factor"])
    cluster_width = count * gear_mm + max(0, count - 1) * cluster_spacing
    gap_mm = spec["gap_mm"]
    dash_mm = spec["dash_mm"]
    cycle_mm = dash_mm + gap_mm + cluster_width + gap_mm
    cluster_offset = dash_mm + gap_mm + cluster_width / 2

    # The dash vector's own "on" segment always starts at boundary position 0, so the dash must
    # be the first thing in the cycle -- otherwise it draws underneath the gear cluster instead
    # of in the gap next to it.
    outline = _line(spec["color"], spec["width_mm"])
    _set_dash(outline, [dash_mm, cycle_mm - dash_mm])
    layers = [outline]

    cluster = _gear_cluster(spec["gear_file"], gear_mm, count, cluster_spacing)
    if spec.get("alternate_file"):
        layers.append(_marker_at(cluster, 2 * cycle_mm, cluster_offset))
        alternate = _gear_cluster(spec["alternate_file"], gear_mm, 1, 0)
        layers.append(_marker_at(alternate, 2 * cycle_mm, cluster_offset + cycle_mm))
    else:
        layers.append(_marker_at(cluster, cycle_mm, cluster_offset))
    _as_boundary(symbol, layers)


def _border_triangle_cluster(symbol, spec):
    """Diğer Özel Kanunlarla Belirlenen Alan Sınırları: çizgi - ara - N eşkenar üçgenlik öbek
    (``fills``: her üçgenin dolu/boş sırası, varsayılan 2 dolu 1 boş) - ara, tekrar. İsteğe bağlı
    ``dot_mm`` her üçgenin içine küçük bir dolu nokta ekler (Korunması Gerekli Flora ve Fauna
    Alanı, Ekolojik Niteliği Korunacak Alan: 'üçgenlerin içerisinde N mm çapında nokta').
    ``dash_mm`` 0/verilmemişse (Afet Tehlikeli Alanlar ailesi: 'üçgenlerin köşesinden geçen
    tabanlarına paralel düz çizgi') taban çizgisi kesintisiz sürer, sadece üçgen öbekleri
    aralıklıdır -- tek üçgenlik öbek (``fills`` tek elemanlı) 'tabanı eksik üçgen' sırasını
    yaklaştırır: kapalı üçgenin tabanı zaten bu kesintisiz çizgiyle çakıştığından görünmez."""
    from qgis.PyQt.QtCore import QPointF

    tri_mm = spec["triangle_mm"]
    spacing_mm = spec.get("triangle_spacing_mm", 0.0)
    fills = spec.get("fills", [True, True, False])
    count = len(fills)
    cluster_width = count * tri_mm + max(0, count - 1) * spacing_mm
    gap_mm, dash_mm = spec["gap_mm"], spec.get("dash_mm", 0.0)
    cycle_mm = dash_mm + gap_mm + cluster_width + gap_mm
    cluster_offset = dash_mm + gap_mm + cluster_width / 2

    outline = _line(spec["color"], spec["width_mm"])
    if dash_mm:
        _set_dash(outline, [dash_mm, cycle_mm - dash_mm])

    step = tri_mm + spacing_mm
    cluster = QgsMarkerSymbol()
    while cluster.symbolLayerCount():
        cluster.takeSymbolLayer(0)
    for i, filled in enumerate(fills):
        tri = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.EquilateralTriangle, tri_mm)
        tri.setSizeUnit(MAP_METERS)
        if filled:
            tri.setColor(_color(spec["color"]))
            tri.setStrokeStyle(Qt.PenStyle.NoPen)
        else:
            tri.setColor(QColor(0, 0, 0, 0))
            tri.setStrokeColor(_color(spec["color"]))
            tri.setStrokeWidth(spec["width_mm"])
            tri.setStrokeWidthUnit(MAP_METERS)
        tri.setOffset(QPointF((i - (count - 1) / 2.0) * step, 0))
        tri.setOffsetUnit(MAP_METERS)
        cluster.appendSymbolLayer(tri)
        if spec.get("dot_mm"):
            dot = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, spec["dot_mm"])
            dot.setSizeUnit(MAP_METERS)
            dot.setColor(_color(spec["color"]))
            dot.setStrokeStyle(Qt.PenStyle.NoPen)
            dot.setOffset(QPointF((i - (count - 1) / 2.0) * step, 0))
            dot.setOffsetUnit(MAP_METERS)
            cluster.appendSymbolLayer(dot)

    _as_boundary(symbol, [outline, _marker_at(cluster, cycle_mm, cluster_offset)])


def _border_circle_triangle(symbol, spec):
    """Statüsü Özel Kanunlarla Belirlenen Alan Sınırı: çizgi - ara - (içinde boş üçgen olan boş
    daire) - ara, tekrar."""
    circle_mm, tri_mm = spec["circle_mm"], spec["triangle_mm"]
    gap_mm, dash_mm = spec["gap_mm"], spec["dash_mm"]
    cycle_mm = dash_mm + gap_mm + circle_mm + gap_mm
    offset = dash_mm + gap_mm + circle_mm / 2

    outline = _line(spec["color"], spec["width_mm"])
    _set_dash(outline, [dash_mm, cycle_mm - dash_mm])

    def _hollow_shape(shape, size_mm):
        mark = QgsSimpleMarkerSymbolLayer(shape, size_mm)
        mark.setSizeUnit(MAP_METERS)
        mark.setColor(QColor(0, 0, 0, 0))
        mark.setStrokeColor(_color(spec["color"]))
        mark.setStrokeWidth(spec["width_mm"])
        mark.setStrokeWidthUnit(MAP_METERS)
        return mark

    mark = QgsMarkerSymbol([
        _hollow_shape(Qgis.MarkerShape.Circle, circle_mm),
        _hollow_shape(Qgis.MarkerShape.EquilateralTriangle, tri_mm),
    ])
    _as_boundary(symbol, [outline, _marker_at(mark, cycle_mm, offset)])


_NATURAL_CHARACTER_FALLBACKS = {
    # The seven distinct official resource UUIDs in UIP_DOGAL_KARAKTER are
    # byte-identical in the supplied archive.  These clear, portable vector
    # fallbacks keep the code-list values legible without pretending that the
    # archive's duplicated bitmap is authoritative for every land cover.
    "AGACLIK": {"fill": "220/239/211", "kind": "dots", "color": "45/112/48", "dot_mm": 1.8, "spacing_mm": 6},
    "KAYALIK_TASLIK": {"fill": "225/222/211", "kind": "triangles", "color": "112/106/92", "dot_mm": 2.2, "spacing_mm": 7},
    "CALILIK": {"fill": "207/230/190", "kind": "dots", "color": "75/128/61", "dot_mm": 1.2, "spacing_mm": 4},
    "KUMUL": {"fill": "246/232/181", "kind": "lines", "color": "183/149/67", "width_mm": 0.25, "spacing_mm": 4, "angle_deg": 35},
    "MAKILIK_FUNDALIK": {"fill": "210/224/170", "kind": "lines", "color": "86/111/55", "width_mm": 0.3, "spacing_mm": 5, "angle_deg": 0},
    "DIGER": {"fill": "209/255/155", "kind": "crosses", "color": "63/113/54", "dot_mm": 1.8, "spacing_mm": 10},
}


def _natural_character_symbol(label, level):
    spec = _NATURAL_CHARACTER_FALLBACKS.get(label)
    if spec is None:
        return None
    spec = _ground_spec(spec, level)
    symbol = QgsFillSymbol.createSimple({"color": _color(spec["fill"]).name(), "outline_style": "no"})
    if spec["kind"] == "lines":
        pattern = QgsLinePatternFillSymbolLayer()
        pattern.setLineAngle(spec["angle_deg"])
        pattern.setDistance(spec["spacing_mm"])
        pattern.setDistanceUnit(MAP_METERS)
        pattern.setSubSymbol(QgsLineSymbol([_line(spec["color"], spec["width_mm"])]))
        symbol.appendSymbolLayer(pattern)
        return symbol
    shape = {
        "dots": Qgis.MarkerShape.Circle,
        "triangles": Qgis.MarkerShape.EquilateralTriangle,
        "crosses": Qgis.MarkerShape.Cross,
    }[spec["kind"]]
    marker = QgsSimpleMarkerSymbolLayer(shape, spec["dot_mm"])
    marker.setSizeUnit(MAP_METERS)
    marker.setColor(_color(spec["color"]))
    marker.setStrokeColor(_color(spec["color"]))
    marker.setStrokeWidth(0.2 * spec["_mm_factor"])
    marker.setStrokeWidthUnit(MAP_METERS)
    symbol.appendSymbolLayer(_pattern(marker, spec["spacing_mm"]))
    return symbol


_BORDER_KINDS = {
    "cross": _border_cross,
    "cross_cluster": _border_cross_cluster,
    "solid": _border_solid,
    "dashed": _border_dashed,
    "dots": _border_dots,
    "tick_circle": _border_tick_circle,
    "circles": _border_circles,
    "gears": _border_gears,
    "triangle_cluster": _border_triangle_cluster,
    "circle_triangle": _border_circle_triangle,
}


def apply_catalog_overrides(layer, level, type_name):
    """Correct the SLD-derived renderer of ``layer`` to the catalog.

    Returns (notes of what was applied, labels of rules redrawn entirely from catalog
    measurements, {rule label: border text} for borders the catalog repeats along the line,
    e.g. AYB/RA/RYA/YENİLEME, {rule label: line text} for LINE features that repeat a letter
    along themselves, e.g. Soğutma Suyu Alma Hattı's 'S')."""
    applied, redrawn, border_text, line_text = [], set(), {}, {}
    geometry_type = layer.geometryType()
    current = level not in CURRENT_OF
    for label, getter, setter in _rules(layer.renderer()):
        symbol = getter().clone()
        natural = _natural_character_symbol(label, level) if level == "UIP" and type_name == "DogalKarakter" else None
        if natural is not None:
            symbol = natural
            applied.append(f"{label}: kaynak arşivdeki yinelenen tarama yerine ayrıştırılmış vektör tarama")
        for key, spec in _specs("vectors", level, type_name, label, include_borrowed=True):
            spec = _ground_spec(spec, level)
            if spec["kind"] == "merkez" and geometry_type == Qgis.GeometryType.Point:
                symbol = _merkez(spec)
            elif spec["kind"] == "road" and geometry_type == Qgis.GeometryType.Line:
                symbol = _road(spec)
            elif spec["kind"] == "ladder" and geometry_type == Qgis.GeometryType.Line:
                symbol = _ladder(spec)
            elif spec["kind"] == "vertex_chain" and geometry_type == Qgis.GeometryType.Line:
                symbol = _vertex_chain(spec)
            elif spec["kind"] == "line_solid" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_solid(spec)
            elif spec["kind"] == "line_dashed" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_dashed(spec)
            elif spec["kind"] == "line_ties" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_ties(spec)
            elif spec["kind"] == "line_overlay" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_overlay(spec)
            elif spec["kind"] == "line_tick_tie" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_tick_tie(spec)
            elif spec["kind"] == "line_marked" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_marked(spec)
            elif spec["kind"] == "line_circles" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_circles(spec)
            elif spec["kind"] == "line_ticks" and geometry_type == Qgis.GeometryType.Line:
                symbol = _line_ticks(spec)
            else:
                continue
            applied.append(f"{label}: s.{spec['page']} ölçüleri")
            redrawn.add(label)
            if spec.get("text"):
                line_text[label] = (spec["text"], spec["color"])
        if current:
            for key, spec in _specs("borders", level, type_name, label, include_borrowed=False):
                spec = _ground_spec(spec, level)
                border = _BORDER_KINDS.get(spec["kind"])
                if border is not None and geometry_type == Qgis.GeometryType.Polygon:
                    border(symbol, spec)
                    applied.append(f"{label}: s.{spec['page']} sınır çizgisi")
                    if spec.get("text"):
                        border_text[label] = (spec["text"], spec["color"])
            for key, spec in _specs("fills", level, type_name, label, include_borrowed=False):
                for index in range(symbol.symbolLayerCount()):
                    if symbol.symbolLayer(index).layerType() == "SimpleFill":
                        symbol.symbolLayer(index).setColor(_color(spec["rgb"]))
                        applied.append(f"{label}: s.{spec['page']} renk {spec['rgb']}")
                        break
            for key, spec in _specs("hatches", level, type_name, label, include_borrowed=False):
                if isinstance(symbol, QgsFillSymbol):
                    symbol = _hatch(
                        symbol,
                        _ground_spec(spec, level),
                        level,
                        type_name,
                        geometry_type,
                    )
                    applied.append(f"{label}: s.{spec['page']} tarama")
        for key, entry in catalog()["decisions"]["symbols"].items():
            for target in entry.get("rules", []):
                if level in target["levels"] and target["type"] == type_name and target["rule"] in ("*", label):
                    _added_symbol(symbol, key, level, geometry_type)
                    applied.append(f"{label}: s.{entry['page']} sembol")
        setter(symbol)
    return applied, redrawn, border_text, line_text
