"""MPYY çalışma alanı: Bakanlığın MPYY 1.1.7 XSD şemasından birebir GeoPackage.

One table per member of the schema's ``plan:features`` collection, named exactly
like the GML element. Fields keep the XSD element names, order and types; code
lists become dropdowns that store the schema's own enumeration value;
``minOccurs="1"`` becomes a not-null constraint. The structure comes only from
``styles/mpyy_schema.json`` (compiled by ``tools/compile_mpyy_schema.py``).

Not-null constraints are *soft*: QGIS warns but lets a draft be saved, because
a plan is drawn before every attribute is known. Conformance of a finished plan
is reported by :func:`audit_required_fields`.

Symbology is the Ministry's own e-Plan GeoServer SLD for the same feature type,
compiled by ``tools/compile_mpyy_eplan_styles.py`` with its filters rewritten
to this schema. QGIS' SLD reader turns ``ttf://`` marks into plain circles, so
those markers are restored from the SLD; tarama images are embedded in the
style so a GeoPackage stays portable. Types without an official SLD stay neutral.
"""

import base64
import contextlib
import json
import tempfile
import os
import re
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from osgeo import gdal, ogr
from qgis.core import (
    Qgis,
    QgsEditorWidgetSetup,
    QgsFieldConstraints,
    QgsFontMarkerSymbolLayer,
    QgsProject,
    QgsRuleBasedRenderer,
    QgsSymbol,
    QgsSymbolLayer,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor, QFont

from .schema import SCHEMA_VERSION
from .legend_scope import limit_to_present, watch as watch_legend

gdal.UseExceptions()

KIND = "MPYY_XSD"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PLUGIN_ROOT / "styles" / "mpyy_schema.json"
SLD_DIR = PLUGIN_ROOT / "styles" / "mpyy_sld"
TARAMA_PLACEHOLDER = "mpyy-tarama:"
MISSING_SYMBOL_PLACEHOLDER = "mpyy-eksik-sembol:"
LEVEL_TITLES = {
    "UIP": "Uygulama imar planı (UİP)",
    "NIP": "Nazım imar planı (NİP)",
    "CDP": "Çevre düzeni planı (ÇDP)",
    "MUIP": "M serisi uygulama imar planı (MUİP)",
    "MNIP": "M serisi nazım imar planı (MNİP)",
    "MCDP25": "M serisi çevre düzeni planı 1/25.000 (MÇDP25)",
    "MCDP100": "M serisi çevre düzeni planı 1/100.000 (MÇDP100)",
}
M_CATALOG_PATH = PLUGIN_ROOT / "styles" / "mpyy_m_schema.json"
QGIS_NULL = "{2839923C-8B7D-419E-B84B-CA2FE9B80EC7}"
DETAIL_HIERARCHY_TABLE = "mpyy_detay_katalogu"
DETAIL_HIERARCHY_LAYER_NAME = "Detay kataloğu hiyerarşisi"
# The companion table's column contract, in the order the rows are inserted.  The
# acceptance suite reads the table back through this list, so a column added here but
# not written, or written in another order, fails there rather than silently shifting
# every field one place to the right.
DETAIL_HIERARCHY_COLUMNS = (
    "sembol_adi", "detay_sinifi", "detay_alt_sinifi", "plan_kademesi", "geometri",
    "plan_gml_tipi", "sld_kurali", "kaynak_sayfa",
)

_OGR_GEOMETRY = {
    "MultiPolygon": ogr.wkbMultiPolygon,
    "Polygon": ogr.wkbPolygon,
    "LineString": ogr.wkbLineString,
    "MultiLineString": ogr.wkbMultiLineString,
    "Point": ogr.wkbPoint,
    "MultiPoint": ogr.wkbMultiPoint,
    None: ogr.wkbNone,
}
_OGR_FIELD = {
    "string": ogr.OFTString,
    "enum": ogr.OFTString,
    "double": ogr.OFTReal,
    "int": ogr.OFTInteger,
    "long": ogr.OFTInteger64,
    "dateTime": ogr.OFTDateTime,
}
_GROUPS = (
    ("Alanlar", ("MultiPolygon", "Polygon")),
    ("Çizgiler", ("LineString", "MultiLineString")),
    ("Noktalar", ("Point", "MultiPoint")),
    ("Tablolar", (None,)),
)


def catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def all_levels():
    """Current MPYY levels plus the M series (read-only import of legacy-legend plans)."""
    levels = dict(catalog()["levels"])
    levels.update(json.loads(M_CATALOG_PATH.read_text(encoding="utf-8"))["levels"])
    return levels


def level_schema(level):
    levels = all_levels()
    if level not in levels:
        raise ValueError('MPYY şemasında olmayan plan kademesi: ' + str(level))
    return levels[level]


def caption(code):
    """Readable caption for a schema identifier without changing its spelling."""
    text = re.sub(r"(?<=[a-zçğıöşü0-9])(?=[A-ZÇĞİÖŞÜ])", " ", str(code))
    return re.sub(r"(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])", " ", text)


def _ordered_fields(feature_type):
    # symbolizer is an optional rendering hint inherited by every type; keep it last in forms.
    fields = [f for f in feature_type["fields"] if f["name"] != "symbolizer"]
    return fields + [f for f in feature_type["fields"] if f["name"] == "symbolizer"]


def create_mpyy_workspace(output_path, crs, level):
    """Create an empty GeoPackage whose tables are the MPYY feature types of ``level``."""
    output = Path(output_path).resolve()
    if output.exists():
        raise FileExistsError(str(output))
    if output.suffix.lower() != ".gpkg":
        raise ValueError('Çıktı .gpkg uzantısını kullanmalıdır')
    schema = level_schema(level)
    source = catalog()["source"]
    from .db_factory import _crs

    srs = _crs(crs)
    staging = output.parent / (".mpyy-" + uuid.uuid4().hex)
    staging.mkdir(parents=True, exist_ok=True)
    staged = staging / "dataset.gpkg"
    try:
        ds = ogr.GetDriverByName("GPKG").CreateDataSource(str(staged))
        if ds is None:
            raise RuntimeError('GeoPackage oluşturulamadı')
        for feature_type in schema["feature_types"]:
            geometry = feature_type["geometry"]
            options = ["FID=fid"] + (["GEOMETRY_NAME=geom", "SPATIAL_INDEX=YES"] if geometry else [])
            layer = ds.CreateLayer(
                feature_type["name"], srs if geometry else None, _OGR_GEOMETRY[geometry], options=options
            )
            if layer is None:
                raise RuntimeError('Katman oluşturulamadı: ' + feature_type["name"])
            for field in _ordered_fields(feature_type):
                if layer.CreateField(ogr.FieldDefn(field["name"], _OGR_FIELD[field["type"]])) != 0:
                    raise RuntimeError(f'Alan oluşturulamadı: {feature_type["name"]}.{field["name"]}')
        ds = None

        with closing(sqlite3.connect(staged)) as con, con:
            con.execute(
                "CREATE TABLE mpyy_metadata (dataset_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL, "
                "workspace_kind TEXT NOT NULL, plan_levels TEXT NOT NULL)"
            )
            con.execute("INSERT INTO mpyy_metadata VALUES (?,?,?,?)", (str(uuid.uuid4()), SCHEMA_VERSION, KIND, level))
            con.execute(
                "CREATE TABLE mpyy_sema (plan_kademesi TEXT PRIMARY KEY, xsd_dosyasi TEXT NOT NULL, "
                "xsd_sha256 TEXT NOT NULL, hedef_ad_alani TEXT NOT NULL, kaynak_url TEXT NOT NULL, "
                "arsiv_sha256 TEXT NOT NULL)"
            )
            con.execute(
                "INSERT INTO gpkg_contents(table_name, data_type, identifier) "
                "VALUES ('mpyy_sema', 'attributes', 'MPYY şema kaynağı')"
            )
            con.execute(
                "INSERT INTO mpyy_sema VALUES (?,?,?,?,?,?)",
                (
                    level,
                    schema["xsd"]["file"],
                    schema["xsd"]["sha256"],
                    schema["target_namespace"],
                    source["url"],
                    source["sha256"],
                ),
            )
            _store_detail_hierarchy(con, level)
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError('Veritabanı bütünlüğü doğrulanamadı: ' + str(integrity))
        os.replace(staged, output)
    finally:
        for item in staging.glob("*"):
            with contextlib.suppress(OSError):
                item.unlink()
        with contextlib.suppress(OSError):
            staging.rmdir()

    _store_default_forms(output, schema)
    return str(output)


def _store_detail_hierarchy(connection, level):
    """Store the Ek-1e polygon/line classification next to, not inside, the XSD schema."""
    from .mpyy_detail_hierarchy import records_for_level

    connection.execute(
        f"CREATE TABLE {DETAIL_HIERARCHY_TABLE} ("
        "id INTEGER PRIMARY KEY, sembol_adi TEXT NOT NULL, detay_sinifi TEXT NOT NULL, "
        "detay_alt_sinifi TEXT NOT NULL, plan_kademesi TEXT NOT NULL, geometri TEXT NOT NULL, "
        "plan_gml_tipi TEXT NOT NULL, sld_kurali TEXT NOT NULL, kaynak_sayfa INTEGER NOT NULL)"
    )
    connection.execute(
        "INSERT INTO gpkg_contents(table_name, data_type, identifier) VALUES (?,?,?)",
        (DETAIL_HIERARCHY_TABLE, "attributes", "Ek-1e detay kataloğu hiyerarşisi"),
    )
    # One literal statement, table name included, rather than an f-string.  The Hub's
    # Bandit gate reads any f-string whose text reads "INSERT INTO ... VALUES" as a SQL
    # injection vector and blocks the upload (B608); a plain literal is not a
    # string-building operation, so nothing needs suppressing.  The literal column list
    # and DETAIL_HIERARCHY_COLUMNS must stay in step -- tests/test_mpyy_workspace_qgis.py
    # reads every column back in that order and compares row by row, so a swap fails
    # there instead of silently writing each field into its neighbour's column.
    connection.executemany(
        "INSERT INTO mpyy_detay_katalogu "
        "(sembol_adi, detay_sinifi, detay_alt_sinifi, plan_kademesi, geometri, "
        "plan_gml_tipi, sld_kurali, kaynak_sayfa) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            tuple(record[column] for column in DETAIL_HIERARCHY_COLUMNS)
            for record in records_for_level(level)
        ],
    )


def configure_mpyy_layer(layer, feature_type, codelists):
    """Dropdowns, captions and required-field checks straight from the schema."""
    fields = layer.fields()
    fid = fields.indexFromName("fid")
    if fid >= 0:
        layer.setEditorWidgetSetup(fid, QgsEditorWidgetSetup("Hidden", {}))
    missing = []
    for field in feature_type["fields"]:
        index = fields.indexFromName(field["name"])
        if index < 0:
            # A workspace created with an older MPYY version; the audit reports it.
            missing.append(field["name"])
            continue
        layer.setFieldAlias(index, caption(field["name"]))
        if field["type"] == "enum":
            entries = [] if field["required"] else [{"(boş)": QGIS_NULL}]
            entries += [{caption(code): code} for code in codelists[field["codelist"]]]
            layer.setEditorWidgetSetup(index, QgsEditorWidgetSetup("ValueMap", {"map": entries}))
        elif field["type"] == "dateTime":
            layer.setEditorWidgetSetup(
                index,
                QgsEditorWidgetSetup(
                    "DateTime",
                    {"allow_null": not field["required"], "calendar_popup": True,
                     "display_format": "dd.MM.yyyy HH:mm", "field_format": "yyyy-MM-ddTHH:mm:ss",
                     "field_iso_format": True},
                ),
            )
        if field["required"]:
            layer.setFieldConstraint(
                index, QgsFieldConstraints.Constraint.ConstraintNotNull,
                QgsFieldConstraints.ConstraintStrength.ConstraintStrengthSoft,
            )
            if field["type"] == "enum":
                allowed = ", ".join("'" + code.replace("'", "''") + "'" for code in codelists[field["codelist"]])
                layer.setConstraintExpression(
                    index, f'"{field["name"]}" IS NULL OR "{field["name"]}" IN ({allowed})',
                    f'{caption(field["name"])}: MPYY kod listesinde olmayan değer.',
                )
    from .form_rules import apply_numeric_rules

    # Range widgets and bounds for the numeric fields the XSD leaves untyped beyond
    # double/int (TAKS 0-1, non-negative distances, >= 1 storey ...).
    apply_numeric_rules(layer, feature_type)
    layer.setCustomProperty("mpyy/schema_missing_fields", ", ".join(missing))
    layer.setCustomProperty("mpyy/form", "MPYY şeması: " + feature_type["name"])
    layer.setCustomProperty("mpyy/template", "mpyy:" + feature_type["name"])
    layer.setCustomProperty("mpyy/workspace_kind", KIND)


def _store_default_forms(path, schema):
    """Save each layer's form as the GeoPackage default style so plain QGIS gets the dropdowns too."""
    for feature_type in schema["feature_types"]:
        layer = QgsVectorLayer(f"{path}|layername={feature_type['name']}", feature_type["name"], "ogr")
        if not layer.isValid():
            raise RuntimeError('Katman açılamadı: ' + feature_type["name"])
        configure_mpyy_layer(layer, feature_type, schema["codelists"])
        apply_eplan_symbology(layer, schema_level(schema), feature_type["name"])
        if not apply_line_labels(layer, schema_level(schema), feature_type["name"]) and not layer.labelsEnabled():
            apply_building_notation(layer)
        # layer_styles.styleName is TEXT(30); the table name already identifies the row.
        message = layer.saveStyleToDatabase("MPYY " + schema["xsd"]["file"].split(".V.")[1][:-4], "MPYY şeması formu", True, "")
        if message:
            raise RuntimeError(f'{feature_type["name"]}: stil kaydedilemedi: {message}')
        del layer


def load_mpyy_layers(path, project=None, dataset_id=None, level=None):
    project = project or QgsProject.instance()
    if level is None:
        with closing(sqlite3.connect(f"file:{Path(path).resolve().as_posix()}?mode=ro", uri=True)) as con:
            level = con.execute("SELECT plan_kademesi FROM mpyy_sema").fetchone()[0]
    schema = level_schema(level)
    gpkg = str(Path(path).resolve())
    root = project.layerTreeRoot()
    title = f'MPYY {LEVEL_TITLES.get(level, level)}'
    base = root.findGroup(title) or root.insertGroup(0, title)
    loaded = []
    for group_name, geometries in _GROUPS:
        members = sorted(
            (t for t in schema["feature_types"] if t["geometry"] in geometries), key=lambda t: t["name"]
        )
        if not members:
            continue
        group = base.findGroup(group_name) or base.addGroup(group_name)
        group.setExpanded(False)
        for feature_type in members:
            layer = QgsVectorLayer(f"{gpkg}|layername={feature_type['name']}", feature_type["name"], "ogr")
            if not layer.isValid():
                raise RuntimeError('Katman açılamadı: ' + feature_type["name"])
            configure_mpyy_layer(layer, feature_type, schema["codelists"])
            if not str(layer.customProperty("mpyy/symbology") or "").startswith(("e-Plan SLD", "Detay kataloğu")):
                apply_eplan_symbology(layer, level, feature_type["name"])  # default style missing or replaced
            if not layer.labelsEnabled() and not apply_line_labels(layer, level, feature_type["name"]):
                apply_building_notation(layer)
            # Workspaces saved before the reference scale existed carry a style without it.
            apply_plan_reference_scale(layer, level)
            # Legend lists only the symbols this plan uses; the full set returns
            # while the layer is edited (see core/legend_scope.py).
            limit_to_present(layer)
            watch_legend(layer)
            if dataset_id:
                layer.setCustomProperty("mpyy/dataset_id", dataset_id)
            project.addMapLayer(layer, False)
            group.addLayer(layer)
            loaded.append(layer)
    with closing(sqlite3.connect(f"file:{Path(path).resolve().as_posix()}?mode=ro", uri=True)) as con:
        has_catalog = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (DETAIL_HIERARCHY_TABLE,)
        ).fetchone() is not None
    if has_catalog:
        catalog_layer = QgsVectorLayer(
            f"{gpkg}|layername={DETAIL_HIERARCHY_TABLE}", DETAIL_HIERARCHY_LAYER_NAME, "ogr"
        )
        if catalog_layer.isValid():
            group = base.findGroup("Katalog") or base.addGroup("Katalog")
            group.setExpanded(False)
            project.addMapLayer(catalog_layer, False)
            group.addLayer(catalog_layer)
            loaded.append(catalog_layer)
    return loaded


def audit_required_fields(layers):
    """Count features whose schema-required attributes are empty, per layer."""
    report = {}
    for layer in layers:
        name = str(layer.customProperty("mpyy/template") or "")
        if not name.startswith("mpyy:"):
            continue
        required = [
            layer.fields().at(i).name()
            for i in range(layer.fields().count())
            if layer.fields().at(i).constraints().constraints() & QgsFieldConstraints.Constraint.ConstraintNotNull
        ]
        missing = {}
        for feature in layer.getFeatures():
            for field in required:
                value = feature[field]
                if value is None or value == "" or (hasattr(value, "isNull") and value.isNull()):
                    missing[field] = missing.get(field, 0) + 1
        if missing:
            report[layer.name()] = missing
    return report


def schema_level(schema):
    return next(level for level, compiled in all_levels().items() if compiled["xsd"] == schema["xsd"])


METRE_UOM = "http://www.opengeospatial.org/se/units/metre"


def _sld_graphics(sld_text, line_layer=False):
    """Per rule, one entry per SLD graphic QGIS turns into a marker symbol layer, in document order.

    Each entry is a dict: ``font`` (family, character) for a ttf mark, ``size`` and ``metre`` from the
    graphic and its symbolizer, and for a GraphicStroke ``interval``/``offset`` from the stroke dash
    pattern (GeoServer repeats the graphic once per dash; with no dasharray it repeats contiguously,
    so the interval is the graphic's own size). ``None`` where QGIS makes no marker: a fill tile, or a
    PointSymbolizer on a line layer.

    QGIS reads none of this when it imports the SLD (every marker line comes in with interval 0 and
    graphics inside a stroke or fill lose the symbolizer's metre unit), so it is applied afterwards."""
    from qgis.PyQt.QtXml import QDomDocument

    doc = QDomDocument()
    doc.setContent(sld_text, True)  # namespace aware
    sld = "http://www.opengis.net/sld"
    rules = []
    rule_nodes = doc.elementsByTagNameNS(sld, "Rule")
    for i in range(rule_nodes.count()):
        marks = []
        graphic_nodes = rule_nodes.at(i).toElement().elementsByTagNameNS(sld, "Graphic")
        for j in range(graphic_nodes.count()):
            graphic = graphic_nodes.at(j).toElement()
            mark = graphic.firstChildElement("Mark")
            external = graphic.firstChildElement("ExternalGraphic")
            parent = graphic.parentNode().toElement()
            holder = parent.localName()
            if (holder == "GraphicFill" and not external.isNull()) or (line_layer and holder == "PointSymbolizer"):
                continue
            name = mark.firstChildElement("WellKnownName").text() if not mark.isNull() else ""
            found = re.match(r"ttf://(?P<family>[^#]+)#0x(?P<code>[0-9A-Fa-f]+)", name)
            entry = {"font": (found.group("family"), chr(int(found.group("code"), 16))) if found else None}
            entry["size"] = _number(graphic.firstChildElement("Size").text())
            node, entry["metre"] = graphic, False
            while not node.isNull():
                element = node.toElement()
                if element.localName().endswith("Symbolizer"):
                    entry["metre"] = element.attribute("uom") == METRE_UOM
                    break
                node = node.parentNode()
            if holder == "GraphicStroke":
                stroke = parent.parentNode().toElement()
                dashes = [_number(v) for v in _css(stroke, "stroke-dasharray").split()]
                dashes = [d for d in dashes if d is not None]
                entry["interval"] = sum(dashes) if dashes else entry["size"]
                entry["offset"] = _number(_css(stroke, "stroke-dashoffset"))
            marks.append(entry)
        rules.append(marks)
    return rules


def _css(element, name):
    """Value of the ``<CssParameter name=...>`` directly under ``element``."""
    child = element.firstChildElement("CssParameter")
    while not child.isNull():
        if child.attribute("name") == name:
            return child.text().strip()
        child = child.nextSiblingElement("CssParameter")
    return ""


def _number(text):
    try:
        return float(str(text).strip())
    except (TypeError, ValueError):
        return None


def _marker_paths(symbol, prefix=()):
    """Index path of every marker symbol layer, depth first, in drawing order.

    A path such as ``(1, 0)`` means ``symbol.symbolLayer(1).subSymbol().symbolLayer(0)``. Paths are
    used instead of symbol layer references because a layer fetched from a sub-symbol does not stay
    valid while the tree is walked and edited."""
    paths = []
    for index in range(symbol.symbolLayerCount()):
        layer = symbol.symbolLayer(index)
        # MarkerLine/CentroidFill containers report a marker symbol type too,
        # but they have no size() and must not be paired with an SLD Graphic.
        if layer.type() == Qgis.SymbolType.Marker and hasattr(layer, "size"):
            paths.append(prefix + (index,))
        if layer.subSymbol() is not None:
            paths.extend(_marker_paths(layer.subSymbol(), prefix + (index,)))
    return paths


def _owner_of(symbol, path):
    """The symbol holding the layer at ``path`` (resolved from the root every time)."""
    current = symbol
    for index in path[:-1]:
        current = current.symbolLayer(index).subSymbol()
    return current


_COMBINED_CATALOG_RULES = {
    "IcmesuTesis": {
        "values": ("Depolama", "Aritma", "TerfiMerkezi"),
        "label": "İÇME SUYU TESİSLERİ ALANI (DEPOLAMA-ARITMA-TERFİ MERKEZİ)",
    },
    "KatiAtikTesis": {
        "values": ("Bosaltma", "Bertaraf", "Isleme", "Transfer", "Depolama"),
        "label": "KATI ATIK TESİSLERİ ALANI (BOŞALTMA, BERTARAF, İŞLEME, TRANSFER VE DEPOLAMA)",
    },
}


def _combine_catalog_rules(layer, type_name):
    """Keep XSD values separate while presenting a single Ek-1e catalog display rule."""
    specification = _COMBINED_CATALOG_RULES.get(type_name)
    renderer = layer.renderer()
    if specification is None or not isinstance(renderer, QgsRuleBasedRenderer):
        return
    root = renderer.rootRule()
    selected = [
        rule for rule in root.children()
        if rule.symbol() is not None and any(f"'{value}'" in rule.filterExpression() for value in specification["values"])
    ]
    if len(selected) != len(specification["values"]):
        return
    keeper = selected[0]
    keeper.setFilterExpression("(" + ") OR (".join(rule.filterExpression() for rule in selected) + ")")
    keeper.setLabel(specification["label"])
    keeper.setDescription(specification["label"])
    for rule in selected[1:]:
        root.removeChild(rule)


def _restore_source_ground_units(symbol):
    """A small set of official SLD boundary marks really are specified in ground metres."""
    for index in range(symbol.symbolLayerCount()):
        layer = symbol.symbolLayer(index)
        if hasattr(layer, "setSizeUnit"):
            layer.setSizeUnit(Qgis.RenderUnit.MetersInMapUnits)
        if hasattr(layer, "setIntervalUnit"):
            layer.setIntervalUnit(Qgis.RenderUnit.MetersInMapUnits)
        if hasattr(layer, "setOffsetAlongLineUnit"):
            layer.setOffsetAlongLineUnit(Qgis.RenderUnit.MetersInMapUnits)
        if layer.subSymbol() is not None:
            _restore_source_ground_units(layer.subSymbol())


def apply_plan_reference_scale(layer, level):
    """Draw every paper-unit size (mm, pt, px) and label as paper at the plan's scale.

    The Ministry SLDs size marks, hatch tiles, line widths and texts in paper units,
    while the catalogue redraws and boundary bands are in ground metres. Mixed, a
    PARK glyph stays the same size on screen when zooming out and covers the sheet,
    while an askeri alan band shrinks with the map. A symbology reference scale
    makes the paper units behave like the printed sheet: exact at 1:1000 for a UİP,
    and smaller together with the ground-unit parts at every other scale.
    """
    from .mpyy_detail_catalog import _level_scale

    renderer = layer.renderer()
    if renderer is None:
        return False
    renderer.setReferenceScale(_level_scale(level))
    return True


def apply_eplan_symbology(layer, level, type_name, centre_sizes=True):
    """Apply the official SLD of this MPYY type; returns False when the Ministry set has none.

    ``centre_sizes=False`` keeps the centre pictograms at the size the SLD gives
    them; only ``tools/measure_centre_symbols.py`` needs that, to measure them."""
    from .centre_symbols import apply_centre_symbol_sizes

    source = SLD_DIR / level / f"{type_name}.sld"
    if not source.exists():
        applied = _apply_catalog_symbol(layer, level, type_name)
        if applied and centre_sizes:
            apply_centre_symbol_sizes(layer, level, type_name)
        return applied
    from .fonts import register_mpyy_fonts

    register_mpyy_fonts()
    text = source.read_text(encoding="utf-8").replace(TARAMA_PLACEHOLDER, (PLUGIN_ROOT / "resources").as_uri() + "/")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"{type_name}.sld"
        path.write_text(text, encoding="utf-8")
        message, ok = layer.loadSldStyle(str(path))
    if not ok:
        # UIP/NIP YOLORTA only carries text symbolizers (the road width in a circle).
        if _apply_road_width_labels(layer, text):
            layer.setCustomProperty("mpyy/symbology", "e-Plan SLD (yol genişliği yazısı): " + level + "/" + type_name)
            return True
        layer.setCustomProperty("mpyy/symbology", "e-Plan SLD QGIS'e aktarılamadı: " + level + "/" + type_name)
        return False

    marks = _sld_graphics(text, layer.geometryType() == Qgis.GeometryType.Line)
    renderer = layer.renderer()
    if isinstance(renderer, QgsRuleBasedRenderer):
        root = renderer.rootRule()
        symbols = [rule.symbol() for rule in root.children()]
        labels = [rule.label() for rule in root.children()]
        setters = [rule.setSymbol for rule in root.children()]
    else:
        # A single rule without a filter (ManiaSiniri, CDP StratejikKarar ...) comes in as a single symbol.
        root, symbols = None, [renderer.symbol()] if hasattr(renderer, "symbol") else []
        labels = ["*"] * len(symbols)
        setters = [renderer.setSymbol] * len(symbols)
    for symbol in symbols:
        if symbol is not None:
            _fix_metre_uom_units(symbol)
    from .mpyy_detail_catalog import apply_catalog_overrides, raster_marker, symbol_for_glyph

    families = installed_font_families()
    missing = {}  # rule label -> gaps left in that rule
    for symbol, rule_marks, label, setter in zip(symbols, marks, labels, setters):
        if symbol is None:
            continue
        if _mark_missing_svg_symbols(symbol):
            missing.setdefault(label, set()).add("TaramaSembol SVG")
        paths = _marker_paths(symbol)
        if len(paths) == len(rule_marks):
            for path, mark in zip(paths, rule_marks):
                if mark["font"] is None:
                    continue
                index = path[-1]
                old = _owner_of(symbol, path).symbolLayer(index)
                family, character, color = mark["font"][0], mark["font"][1], old.color()
                # The Ek-1e catalog is the authority, so its symbol of the same item replaces the
                # SLD's own glyph wherever one is registered. That is the only repair for a family
                # the Ministry never shipped (Intelli Eplan) and for their 0x003f "we never mapped
                # this" marker (Kumsal-Plaj s.97, Kongre ve Sergi Merkezi s.128). 0x003f is *not*
                # a placeholder in the rest of the pictogram fonts though -- there it is an
                # ordinary slot holding a designed symbol, checked by rendering the face against
                # the catalog: MUIP_10_1 draws s.12's İL SINIRI dash-dot there, UIP_10_1 s.142's
                # arboretum trees, uygulama_imar_07_2 a "KSM" box, UIP_10_2 a beach parasol. With
                # no catalog symbol registered the glyph is drawn as it stands, never greyed out.
                if (family not in families or character == "?") and symbol_for_glyph(family, character):
                    replacement = raster_marker(symbol_for_glyph(family, character), old.size(), old.sizeUnit(), old.angle())
                    _owner_of(symbol, path).changeSymbolLayer(index, replacement)
                    continue
                if family not in families:
                    if family in UNICODE_TEXT_FONTS:
                        family = "DejaVu Sans"  # same Unicode character, e.g. Tahoma U+02C4
                    else:
                        # A private symbol font the Ministry set does not ship (Intelli Eplan):
                        # another font would draw a wrong symbol, so mark the gap instead.
                        missing.setdefault(label, set()).add(family)
                        family, character, color = "DejaVu Sans", "?", QColor("#8a8f96")
                font = QgsFontMarkerSymbolLayer(family, character, old.size(), color, old.angle())
                font.setSizeUnit(old.sizeUnit())
                font.setStrokeWidth(0)
                font.setStrokeColor(QColor(0, 0, 0, 0))
                _owner_of(symbol, path).changeSymbolLayer(index, font)
        sized = _sized_symbol(symbol, rule_marks)
        if sized is not None:
            setter(sized)
            symbol = sized
        _embed_images(symbol)

    applied, redrawn, border_text, line_text = apply_catalog_overrides(layer, level, type_name)
    from .mpyy_detail_catalog import catalog_labels

    for spec in catalog_labels(level, type_name):
        if spec["kind"] == "road_width" and _apply_road_width_labels(layer, None, spec["field"], keep_renderer=True):
            applied.append(f"genişlik yazısı: s.{spec['page']}")
    if border_text and layer.geometryType() == Qgis.GeometryType.Polygon:
        _apply_border_text_labels(layer, border_text, level)
        applied.append("sınır yazısı: " + ", ".join(sorted({text for text, _ in border_text.values()})))
    if line_text and layer.geometryType() == Qgis.GeometryType.Line:
        _apply_line_text_labels(layer, line_text, level)
        applied.append("çizgi yazısı: " + ", ".join(sorted({text for text, _ in line_text.values()})))
    missing = set().union(*[gaps for label, gaps in missing.items() if label not in redrawn])
    if applied:
        layer.setCustomProperty("mpyy/katalog", "; ".join(applied))
    else:
        layer.removeCustomProperty("mpyy/katalog")
    renderer = layer.renderer()
    root = renderer.rootRule() if isinstance(renderer, QgsRuleBasedRenderer) else None
    if root is not None:
        fallback = QgsSymbol.defaultSymbol(layer.geometryType())
        fallback.setColor(QColor("#9aa3ab"))
        else_rule = QgsRuleBasedRenderer.Rule(fallback, 0, 0, "ELSE", "Kodu girilmemiş / resmî gösterimi yok")
        root.appendChild(else_rule)
    if level == "UIP" and type_name == "BuyuksehirSiniri" and root is not None:
        for rule in root.children():
            if rule.label() == "UIP_BUYUKSEHIR_SINIRI" and rule.symbol() is not None:
                _restore_source_ground_units(rule.symbol())
    _combine_catalog_rules(layer, type_name)
    from .mpyy_detail_hierarchy import apply_renderer_hierarchy

    apply_renderer_hierarchy(layer, level, type_name)
    if centre_sizes:
        apply_centre_symbol_sizes(layer, level, type_name)
    apply_plan_reference_scale(layer, level)
    layer.setCustomProperty("mpyy/symbology", "e-Plan SLD: " + level + "/" + type_name)
    if missing:
        layer.setCustomProperty("mpyy/missing_symbols", ", ".join(sorted(missing)))
    else:
        layer.removeCustomProperty("mpyy/missing_symbols")
    layer.triggerRepaint()
    return True


M_BASE = {"MUIP": "UIP", "MNIP": "NIP", "MCDP25": "CDP", "MCDP100": "CDP"}
UNICODE_TEXT_FONTS = {"Tahoma", "Arial", "Calibri", "Microsoft Sans Serif"}
ROAD_WIDTH_GLYPH_RATIO = 0.70  # "(" in ESRI Default Marker: circle diameter / font size (measured)


def _apply_road_width_labels(layer, sld_text, field="YolGenisligi", keep_renderer=False):
    """UIP/NIP YOLORTA: road width written in a circle at the middle of the axis, up to 1:2000.

    ``sld_text`` None skips the SLD check; ``keep_renderer`` adds the circle as an extra rule of the
    existing rule-based renderer (Ek-1e s.155 yaya yolu: same width notation on its own line style).

    The Ministry style draws no axis line. It places the ESRI Default Marker "(" glyph (a circle)
    at font size YolGenisligi * 2.5 map units and writes the width inside it: the whole metres,
    then the decimals underlined. The circle is the same glyph here; the text size is chosen to
    fit inside it because the SLD sizes the text from a server-side view column."""
    if (sld_text is not None and "yol_genisligi1" not in sld_text) or layer.fields().indexOf(field) < 0:
        return False
    from qgis.core import (
        QgsMarkerLineSymbolLayer,
        QgsMarkerSymbol,
        QgsPalLayerSettings,
        QgsProperty,
        QgsPropertyCollection,
        QgsLineSymbol,
        QgsTextFormat,
        QgsVectorLayerSimpleLabeling,
    )
    from .fonts import register_mpyy_fonts

    register_mpyy_fonts()
    map_units = Qgis.RenderUnit.MapUnits
    middle = 'line_interpolate_point($geometry, length($geometry) / 2)'
    circle = QgsFontMarkerSymbolLayer("ESRI Default Marker", "(", 10, QColor("black"))
    circle.setSizeUnit(map_units)
    circle.setDataDefinedProperty(QgsSymbolLayer.Property.Size, QgsProperty.fromExpression(f'"{field}" * 2.5'))
    carrier = QgsMarkerLineSymbolLayer()
    carrier.setPlacements(Qgis.MarkerLinePlacement.CentralPoint)
    carrier.setSubSymbol(QgsMarkerSymbol([circle]))
    width_rule = QgsRuleBasedRenderer.Rule(QgsLineSymbol([carrier]), 0, 2000, f'"{field}" > 0', "Yol genişliği")
    if keep_renderer and isinstance(layer.renderer(), QgsRuleBasedRenderer):
        layer.renderer().rootRule().appendChild(width_rule)
    else:
        root = QgsRuleBasedRenderer.Rule(None)
        root.appendChild(width_rule)
        layer.setRenderer(QgsRuleBasedRenderer(root))

    settings = QgsPalLayerSettings()
    settings.isExpression = True
    settings.fieldName = (
        f'CASE WHEN "{field}" IS NULL THEN NULL '
        f'WHEN round("{field}" * 100) % 100 = 0 THEN to_string(floor("{field}")) '
        f"""ELSE to_string(floor("{field}")) || '<u>' || """
        f"""lpad(to_string(round("{field}" * 100) % 100), 2, '0') || '</u>' END"""
    )
    settings.geometryGenerator = middle
    settings.geometryGeneratorEnabled = True
    settings.geometryGeneratorType = Qgis.GeometryType.Point
    settings.placement = Qgis.LabelPlacement.OverPoint
    settings.scaleVisibility = True
    settings.minimumScale = 2000  # most zoomed-out scale shown, as the SLD MaxScaleDenominator
    settings.maximumScale = 0
    text_format = QgsTextFormat()
    text_format.setFont(QFont("DejaVu Sans"))
    text_format.setSizeUnit(map_units)
    text_format.setSize(4)
    text_format.setColor(QColor("black"))
    text_format.setAllowHtmlFormatting(True)
    settings.setFormat(text_format)
    properties = QgsPropertyCollection()
    properties.setProperty(
        QgsPalLayerSettings.Property.Size,
        QgsProperty.fromExpression(f'"{field}" * 2.5 * {ROAD_WIDTH_GLYPH_RATIO} * 0.26'),
    )
    settings.setDataDefinedProperties(properties)
    placement = settings.placementSettings()
    placement.setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)
    settings.setPlacementSettings(placement)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)
    return True


BORDER_TEXT_REPEAT_MM = 40  # katalog "uygun aralıklarla ... yazılacak" der, aralığı ölçmez
LINE_TEXT_REPEAT_MM = 15  # s.183: üçgenlerle aynı 15mm aralık


def _apply_repeating_text_labels(layer, texts, placement, repeat_mm, level):
    """Repeat each rule's catalog text around/along its geometry, one label rule per SLD rule so
    unrelated rules of the same type stay unlabelled."""
    from qgis.core import QgsPalLayerSettings, QgsRuleBasedLabeling, QgsTextFormat

    from .fonts import register_mpyy_fonts
    from .mpyy_detail_catalog import _level_scale

    renderer = layer.renderer()
    if not isinstance(renderer, QgsRuleBasedRenderer):
        return
    register_mpyy_fonts()
    root = QgsRuleBasedLabeling.Rule(None)
    for rule in renderer.rootRule().children():
        entry = texts.get(rule.label())
        if entry is None:
            continue
        text, color = entry
        settings = QgsPalLayerSettings()
        settings.isExpression = True
        settings.fieldName = "'" + text.replace("'", "''") + "'"
        settings.placement = placement
        factor = _level_scale(level) / 1000.0
        settings.repeatDistance = repeat_mm * factor
        settings.repeatDistanceUnit = Qgis.RenderUnit.MetersInMapUnits
        text_format = QgsTextFormat()
        text_format.setFont(QFont("DejaVu Sans"))
        text_format.setSizeUnit(Qgis.RenderUnit.MetersInMapUnits)
        text_format.setSize(3 * factor)
        text_format.setColor(QColor(*[int(v) for v in color.split("/")]))
        settings.setFormat(text_format)
        label_rule = QgsRuleBasedLabeling.Rule(settings)
        label_rule.setFilterExpression(rule.filterExpression())
        label_rule.setDescription(rule.label())
        root.appendChild(label_rule)
    if root.children():
        layer.setLabeling(QgsRuleBasedLabeling(root))
        layer.setLabelsEnabled(True)


def _apply_border_text_labels(layer, border_text, level):
    """Repeat each border's catalog text (AYB, RA, RYA, YENİLEME, TEA...) around its polygon's
    perimeter (s.24 etc.: 'uygun aralıklarla sınır üzerine ... yazılacak')."""
    _apply_repeating_text_labels(
        layer,
        border_text,
        Qgis.LabelPlacement.PerimeterCurved,
        BORDER_TEXT_REPEAT_MM,
        level,
    )


def _apply_line_text_labels(layer, line_text, level):
    """Repeat each line's catalog text (Soğutma Suyu Alma Hattı's 'S') along the line itself,
    between the chevron markers (s.183: 'ardışık iki üçgen arasında orta noktada ... S harfi')."""
    _apply_repeating_text_labels(
        layer, line_text, Qgis.LabelPlacement.Line, LINE_TEXT_REPEAT_MM, level
    )


def installed_font_families():
    from qgis.PyQt.QtCore import QT_VERSION_STR
    from qgis.PyQt.QtGui import QFontDatabase

    # Qt 6 made QFontDatabase static; Qt 5 needs an instance.
    database = QFontDatabase if int(QT_VERSION_STR.split(".")[0]) >= 6 else QFontDatabase()
    return set(database.families())


def _sized_symbol(symbol, rule_marks):
    """Copy of ``symbol`` with the size, unit and repeat interval every SLD graphic asks for.

    QGIS drops both when it reads a graphic inside a stroke or a fill: the marker keeps a pixel size
    and the marker line is left with interval 0, so the symbols pile up on the line's first vertex.
    The work is done on the symbol's XML rather than on the live symbol layers, because a symbol layer
    fetched from a sub-symbol does not stay valid while the tree is being walked."""
    from qgis.core import QgsReadWriteContext, QgsSymbolLayerUtils
    from qgis.PyQt.QtXml import QDomDocument

    document = QDomDocument()
    element = QgsSymbolLayerUtils.saveSymbol("s", symbol, document, QgsReadWriteContext())
    marks = list(rule_marks)
    if not _walk_symbol_element(element, marks) or marks:
        return None
    return QgsSymbolLayerUtils.loadSymbol(element, QgsReadWriteContext())


def _walk_symbol_element(symbol_element, marks):
    """Apply and consume ``marks`` over the <layer> elements of one <symbol>; False when they run out."""
    is_marker = symbol_element.attribute("type") == "marker"
    layer = symbol_element.firstChildElement("layer")
    while not layer.isNull():
        if is_marker:
            if not marks:
                return False
            mark = marks.pop(0)
            if mark["size"]:
                _set_option(layer, "size", mark["size"])
                _set_option(layer, "size_unit", _unit_name(mark))
        inner = layer.firstChildElement("symbol")
        if not inner.isNull():
            if layer.attribute("class") == "MarkerLine" and marks and marks[0].get("interval"):
                spacing = marks[0]
                _set_option(layer, "interval", spacing["interval"])
                _set_option(layer, "interval_unit", _unit_name(spacing))
                _set_option(layer, "placements", "Interval")
                if spacing.get("offset"):
                    _set_option(layer, "offset_along_line", spacing["offset"])
                    _set_option(layer, "offset_along_line_unit", _unit_name(spacing))
            if not _walk_symbol_element(inner, marks):
                return False
        layer = layer.nextSiblingElement("layer")
    return True


def _unit_name(mark):
    # The Ministry's SLD sometimes declares uom="...units/metre" on a symbolizer, taken here at
    # face value as "this graphic's numbers are millimetres" rather than real ground metres -- see
    # _fix_metre_uom_units for why (2.8344672 "metre" is exactly 1mm's point-equivalent).
    return "MM" if mark["metre"] else "Pixel"


def _set_option(layer_element, name, value):
    """Set one <Option name=...> of a symbol layer's property map, adding it when absent."""
    options = layer_element.firstChildElement("Option")
    if options.isNull():
        return
    option = options.firstChildElement("Option")
    while not option.isNull():
        if option.attribute("name") == name:
            option.setAttribute("value", str(value))
            return
        option = option.nextSiblingElement("Option")
    added = layer_element.ownerDocument().createElement("Option")
    added.setAttribute("type", "QString")
    added.setAttribute("name", name)
    added.setAttribute("value", str(value))
    options.appendChild(added)


def _unit_of(mark):
    return Qgis.RenderUnit.Millimeters if mark["metre"] else Qgis.RenderUnit.Pixels


def _fix_metre_uom_units(symbol, _seen=None):
    """The Ministry's SLD sometimes declares uom="...units/metre" on a Symbolizer (LineSymbolizer,
    PointSymbolizer, TextSymbolizer): QGIS's own SLD importer honours that literally, so a border or
    marker ends up sized in real ground metres -- a boundary line rendered 2.8 m thick regardless of
    zoom, or a centre icon the size of a city block. The declared unit is the mistake, not QGIS's
    reading of it: 2.8344672 "metre" is exactly 1 mm's point-equivalent (72/25.4), so every symbol
    layer QGIS imported as MetersInMapUnits is corrected here to Millimeters, same number."""
    if _seen is None:
        _seen = set()
    if id(symbol) in _seen:
        return
    _seen.add(id(symbol))
    METERS, MM = Qgis.RenderUnit.MetersInMapUnits, Qgis.RenderUnit.Millimeters
    for index in range(symbol.symbolLayerCount()):
        layer = symbol.symbolLayer(index)
        if hasattr(layer, "outputUnit") and layer.outputUnit() == METERS:
            layer.setOutputUnit(MM)
        if hasattr(layer, "strokeWidthUnit") and layer.strokeWidthUnit() == METERS:
            layer.setStrokeWidthUnit(MM)
        sub = layer.subSymbol()
        if sub is not None:
            _fix_metre_uom_units(sub, _seen)


def _mark_missing_svg_symbols(symbol):
    """Markers pointing at the Ministry's unpublished TaramaSembol SVGs: the Ek-1e catalog symbol of
    the same item when there is one, otherwise a grey "?". True when a "?" was left."""
    from .mpyy_detail_catalog import raster_marker, symbol_for_svg

    found = False
    for index in range(symbol.symbolLayerCount()):
        layer = symbol.symbolLayer(index)
        path = str(layer.path() if hasattr(layer, "path") else "")
        name = path.split(MISSING_SYMBOL_PLACEHOLDER, 1)[-1].rsplit("/", 1)[-1]
        if (MISSING_SYMBOL_PLACEHOLDER in path or "TaramaSembol" in path) and symbol_for_svg(name):
            symbol.changeSymbolLayer(index, raster_marker(symbol_for_svg(name), layer.size(), layer.sizeUnit(), layer.angle()))
            continue
        if MISSING_SYMBOL_PLACEHOLDER in path or "TaramaSembol" in path:
            gap = QgsFontMarkerSymbolLayer("DejaVu Sans", "?", layer.size(), QColor("#8a8f96"), layer.angle())
            gap.setSizeUnit(layer.sizeUnit())
            symbol.changeSymbolLayer(index, gap)  # deletes ``layer``; do not touch it afterwards
            found = True
            continue
        sub = layer.subSymbol()
        if sub is not None and _mark_missing_svg_symbols(sub):
            found = True
    return found


def _embed_images(symbol):
    for index in range(symbol.symbolLayerCount()):
        layer = symbol.symbolLayer(index)
        if layer.layerType() == "RasterFill" and hasattr(layer, "imageFilePath"):
            path = layer.imageFilePath()
            if path.startswith("file:"):
                from qgis.PyQt.QtCore import QUrl

                path = QUrl(path).toLocalFile()
            if path and not path.startswith("base64:") and Path(path).is_file():
                layer.setImageFilePath("base64:" + base64.b64encode(_png_bytes(Path(path))).decode("ascii"))
        sub = layer.subSymbol()
        if sub is not None:
            _embed_images(sub)


def _png_bytes(path):
    """Most Ministry tiles are uncompressed BMP despite the .png name; re-encode losslessly as PNG."""
    from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice
    from qgis.PyQt.QtGui import QImage

    image = QImage(str(path))
    if image.isNull():
        return path.read_bytes()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    encoded = bytes(data)
    return encoded if encoded and len(encoded) < path.stat().st_size else path.read_bytes()


def _apply_catalog_symbol(layer, level, type_name):
    """Types absent from the Ministry SLD set, drawn from the detail catalog's line definition."""
    decisions = json.loads((SLD_DIR / "decisions.json").read_text(encoding="utf-8"))
    symbols = decisions.get("catalog_symbols", {})
    spec = symbols.get(level, {}).get(type_name) or symbols.get(M_BASE.get(level), {}).get(type_name)
    if not spec:
        return False
    from .mpyy_detail_catalog import _ground_spec

    spec = _ground_spec(spec, level)
    from qgis.core import (
        QgsFillSymbol,
        QgsLineSymbol,
        QgsMarkerLineSymbolLayer,
        QgsMarkerSymbol,
        QgsSimpleLineSymbolLayer,
        QgsSimpleMarkerSymbolLayer,
        QgsSingleSymbolRenderer,
    )

    color = QColor(*[int(v) for v in spec["rgb"].split("/")])
    map_meters = Qgis.RenderUnit.MetersInMapUnits
    carrier = QgsSimpleLineSymbolLayer(color, spec["line_width_mm"])
    carrier.setWidthUnit(map_meters)
    layers = [carrier]
    cursor, markers = 0.0, []
    for part in spec["pattern"]:
        if part["kind"] == "circle":
            markers.append((cursor + part["diameter_mm"] / 2, part))
            cursor += part["diameter_mm"]
        else:
            cursor += part["length_mm"]
    for center, part in markers:
        circle = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, part["diameter_mm"])
        circle.setSizeUnit(map_meters)
        circle.setColor(color if part["filled"] else QColor("white"))
        circle.setStrokeColor(color)
        circle.setStrokeWidth(spec["line_width_mm"])
        circle.setStrokeWidthUnit(map_meters)
        line = QgsMarkerLineSymbolLayer(False, cursor)
        line.setIntervalUnit(map_meters)
        line.setOffsetAlongLine(center)
        line.setOffsetAlongLineUnit(map_meters)
        line.setSubSymbol(QgsMarkerSymbol([circle]))
        layers.append(line)
    if layer.geometryType() == Qgis.GeometryType.Polygon:
        from qgis.core import QgsGeometryGeneratorSymbolLayer

        symbol = QgsFillSymbol()
        symbol.deleteSymbolLayer(0)
        outline = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": "boundary($geometry)", "SymbolType": "Line"})
        outline.setSubSymbol(QgsLineSymbol(layers))
        symbol.appendSymbolLayer(outline)
    else:
        symbol = QgsLineSymbol(layers)
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.setCustomProperty("mpyy/symbology", "Detay kataloğu: " + level + "/" + type_name)
    layer.triggerRepaint()
    return True


BUILDING_FIELDS = (
    "Taks", "TaksTip", "EmsalKaks", "EmsalKaksTip", "KatAdedi", "YapiDuzeni",
    "YapiYuksekligi", "YapiYuksekligiTip", "OnBahceMesafesi", "YanBahceMesafesi",
)
NOTATION_CIRCLE_M = 18.0  # Ek-1e: 18 mm circle, 5 mm text, drawn at 1/1000 so 1 mm = 1 m
NOTATION_TEXT_M = 5.0


def apply_building_notation(layer):
    """Yapılaşma notasyonu as drawn in Ek-1e Mekânsal Planlar Detay Katalogları (pages 39-43).

    * Yapı düzeni circle (18 mm): nizam letter on the left (A-, B-, BL-), kat adedi on the right,
      ön bahçe mesafesi on top and yan bahçe mesafesi at the bottom.
    * TAKS / KAKS circle (18 mm): TAKS above the dividing line, KAKS below it; the same layout as
      the Ministry's YAPILASMA_SEMBOL style.
    * "E = ..." when only the emsal is given, and "Yençok = ... m".
    Text is 5 mm; sizes are in map units for a 1/1000 plan and the notation shows up to 1:2000.
    The symbols sit around SembolPoz when it holds two coordinates, otherwise inside the polygon.
    Returns the number of label rules; 0 when the layer has no building fields."""
    names = set(layer.fields().names())
    if not set(BUILDING_FIELDS) <= names:
        return 0
    from qgis.core import QgsPalLayerSettings, QgsRuleBasedLabeling, QgsTextFormat
    from .fonts import register_mpyy_fonts

    register_mpyy_fonts()
    notation = json.loads((SLD_DIR / "decisions.json").read_text(encoding="utf-8"))["building_notation"]
    anchor = (
        """CASE WHEN regexp_match("SembolPoz", '^ *-?[0-9.]+ *[ ,;] *-?[0-9.]+ *$') """
        """THEN make_point(to_real(regexp_substr("SembolPoz", '^ *(-?[0-9.]+)')), """
        """to_real(regexp_substr("SembolPoz", '(-?[0-9.]+) *$'))) """
        """ELSE pole_of_inaccessibility($geometry, 0.5) END"""
    )
    radius = NOTATION_CIRCLE_M / 2
    gap = radius + 1.0  # the two circles sit side by side around the anchor
    taks = """"TaksTip" = 'Deger' AND "Taks" IS NOT NULL"""
    kaks = """"EmsalKaksTip" = 'Deger' AND "EmsalKaks" IS NOT NULL"""
    order = """("YapiDuzeni" IS NOT NULL OR "KatAdedi" > 0 OR "OnBahceMesafesi" > 0 OR "YanBahceMesafesi" > 0)"""
    letters = "map(" + ", ".join(f"'{code}', '{letter}'" for code, letter in notation["nizam_letters"].items()) + ")"

    def number(field):
        return f"""CASE WHEN "{field}" IS NULL THEN NULL WHEN "{field}" = floor("{field}") THEN to_string(floor("{field}")) ELSE format_number("{field}", 2, 'en') END"""

    texts = (
        "array_to_string(array_filter(array("
        f"""CASE WHEN {kaks} AND NOT ({taks}) THEN 'E = ' || format_number("EmsalKaks", 2, 'en') END, """
        """CASE WHEN "YapiYuksekligiTip" = 'Deger' AND "YapiYuksekligi" > 0 THEN 'Y<sub>ençok</sub> = ' || format_number("YapiYuksekligi", 2, 'en') || ' m' END"""
        "), @element IS NOT NULL), '<br>')"
    )
    glyph_drop = 0.13 * NOTATION_CIRCLE_M / ROAD_WIDTH_GLYPH_RATIO  # circle sits 0.13 em above the text box centre

    def rule(expression, filter_expression, description, size=NOTATION_TEXT_M, font="DejaVu Sans",
             dx=0.0, dy=0.0, underline=False, below=False, html=False):
        settings = QgsPalLayerSettings()
        settings.isExpression = True
        settings.fieldName = expression
        settings.geometryGenerator = anchor
        settings.geometryGeneratorEnabled = True
        settings.geometryGeneratorType = Qgis.GeometryType.Point
        settings.placement = Qgis.LabelPlacement.OverPoint
        settings.xOffset, settings.yOffset = dx, dy  # map units, y grows downwards
        if below:
            settings.quadOffset = Qgis.LabelQuadrantPosition.Below
        settings.offsetUnits = Qgis.RenderUnit.MapUnits
        settings.multilineAlign = Qgis.LabelMultiLineAlignment.Center
        placement = settings.placementSettings()
        placement.setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)
        settings.setPlacementSettings(placement)
        text_format = QgsTextFormat()
        qfont = QFont(font)
        qfont.setUnderline(underline)
        text_format.setFont(qfont)
        text_format.setSize(size)
        text_format.setSizeUnit(Qgis.RenderUnit.MapUnits)
        text_format.setColor(QColor("black"))
        text_format.setAllowHtmlFormatting(html)
        settings.setFormat(text_format)
        return QgsRuleBasedLabeling.Rule(settings, 0, 2000, filter_expression, description)

    circle_size = NOTATION_CIRCLE_M / ROAD_WIDTH_GLYPH_RATIO
    inner = radius * 0.52
    root = QgsRuleBasedLabeling.Rule(None)
    root.appendChild(rule("'('", order, "Yapı düzeni dairesi", circle_size, "ESRI Default Marker", -gap, glyph_drop))
    root.appendChild(rule(f"""map_get({letters}, "YapiDuzeni") || '-'""", """"YapiDuzeni" IS NOT NULL""", "Yapı düzeni (A-, B-, BL-)", dx=-gap - inner))
    root.appendChild(rule(number("KatAdedi"), """"KatAdedi" > 0""", "Kat adedi", dx=-gap + inner))
    root.appendChild(rule(number("OnBahceMesafesi"), """"OnBahceMesafesi" > 0""", "Ön bahçe mesafesi", dx=-gap, dy=-inner))
    root.appendChild(rule(number("YanBahceMesafesi"), """"YanBahceMesafesi" > 0""", "Yan bahçe mesafesi", dx=-gap, dy=inner))
    root.appendChild(rule("'('", taks, "TAKS/KAKS dairesi", circle_size, "ESRI Default Marker", gap, glyph_drop))
    root.appendChild(rule("""format_number("Taks", 2, 'en')""", taks, "TAKS", dx=gap, dy=-2.6, underline=True))
    root.appendChild(rule("""format_number("EmsalKaks", 2, 'en')""", f"({taks}) AND ({kaks})", "KAKS", dx=gap, dy=3.4))
    root.appendChild(rule(texts, "", "Emsal ve yençok", dy=radius + 1.5, below=True, html=True))
    layer.setLabeling(QgsRuleBasedLabeling(root))
    layer.setLabelsEnabled(True)
    layer.setCustomProperty("mpyy/building_notation", "Ek-1e detay kataloğu yapılaşma notasyonu")
    layer.triggerRepaint()
    return len(root.children())


def apply_line_labels(layer, level, type_name):
    """Boundary abbreviations (A1, KS, YKK ...) written along the line, as the detail catalog requires.

    Returns the number of label rules; 0 when this type carries no catalog abbreviation."""
    from qgis.core import (
        QgsPalLayerSettings,
        QgsRuleBasedLabeling,
        QgsTextBufferSettings,
        QgsTextFormat,
    )
    from .mpyy_detail_catalog import _level_scale

    table = json.loads((PLUGIN_ROOT / "styles" / "mpyy_line_labels.json").read_text(encoding="utf-8"))
    rules = [r for r in table["levels"].get(level, {}).values() if r["feature"] == type_name]
    if not rules:
        return 0
    root = QgsRuleBasedLabeling.Rule(None)
    polygon = layer.geometryType() == Qgis.GeometryType.Polygon
    factor = _level_scale(level) / 1000.0
    for rule in rules:
        settings = QgsPalLayerSettings()
        settings.fieldName = "'" + rule["text"].replace("'", "''") + "'"
        settings.isExpression = True
        settings.placement = Qgis.LabelPlacement.PerimeterCurved if polygon else Qgis.LabelPlacement.Curved
        settings.repeatDistance = 60 * factor
        settings.repeatDistanceUnit = Qgis.RenderUnit.MetersInMapUnits
        line_settings = settings.lineSettings()
        line_settings.setPlacementFlags(Qgis.LabelLinePlacementFlag.OnLine)
        settings.setLineSettings(line_settings)
        text_format = QgsTextFormat()
        text_format.setSize(2.5 * factor)
        text_format.setSizeUnit(Qgis.RenderUnit.MetersInMapUnits)
        text_format.setColor(QColor(rule["color"]))
        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(0.6 * factor)
        buffer.setSizeUnit(Qgis.RenderUnit.MetersInMapUnits)
        buffer.setColor(QColor("white"))
        text_format.setBuffer(buffer)
        settings.setFormat(text_format)
        child = QgsRuleBasedLabeling.Rule(settings)
        child.setDescription(rule["text"] + " — " + rule["kaynak"])
        if rule["field"]:
            child.setFilterExpression('"{}" = \'{}\''.format(rule["field"], rule["code"].replace("'", "''")))
        root.appendChild(child)
    layer.setLabeling(QgsRuleBasedLabeling(root))
    layer.setLabelsEnabled(True)
    layer.setCustomProperty("mpyy/line_labels", ", ".join(r["text"] for r in rules))
    layer.triggerRepaint()
    return len(rules)
