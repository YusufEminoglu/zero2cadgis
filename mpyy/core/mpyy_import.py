"""CAD tabakası → MPYY çalışma alanı aktarımı ve MPYY uygunluk denetimi.

The tabaka lookup is MPYY Studio's own ``styles/mpyy_tabaka_crosswalk.json``
(built and validated by ``tools/build_mpyy_tabaka_crosswalk.py``). Nothing is
guessed at runtime: a tabaka that is not in the table, or whose geometry does
not fit the MPYY type, is reported and left out.
"""

import contextlib
import csv
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)

from .form_rules import cross_field_findings, rule_for, value_in_rule
from .tabaka_matching import load_user_mappings, normalize_tabaka as _normalize_tabaka, resolve
from .mpyy_workspace import all_levels, level_schema

CROSSWALK_PATH = Path(__file__).resolve().parents[1] / "styles" / "mpyy_tabaka_crosswalk.json"
FAMILY = {
    "MultiPolygon": Qgis.GeometryType.Polygon,
    "Polygon": Qgis.GeometryType.Polygon,
    "LineString": Qgis.GeometryType.Line,
    "MultiLineString": Qgis.GeometryType.Line,
    "Point": Qgis.GeometryType.Point,
    "MultiPoint": Qgis.GeometryType.Point,
}
FAMILY_NAME = {Qgis.GeometryType.Polygon: "alan", Qgis.GeometryType.Line: "çizgi", Qgis.GeometryType.Point: "nokta"}
SYSTEM_TABLES = {"mpyy_sema", "layer_styles", "mpyy_metadata"}


# One spelling rule for every caller: the matcher owns it.
normalize_tabaka = _normalize_tabaka


def crosswalk(level):
    return json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))["levels"][level]


def workspace_level(path):
    with closing(sqlite3.connect(f"file:{Path(path).resolve().as_posix()}?mode=ro", uri=True)) as con:
        try:
            return con.execute("SELECT plan_kademesi FROM mpyy_sema").fetchone()[0]
        except sqlite3.Error:
            return None


def _fit_geometry(geometry, target):
    """Geometries for a MPYY type, or [] when the family does not fit.

    Closed CAD polylines become polygons for area types; multi parts are split for
    single-part types (LineString, Point, Polygon)."""
    if geometry is None or geometry.isEmpty():
        return []
    family = FAMILY[target]
    if geometry.type() == Qgis.GeometryType.Line and family == Qgis.GeometryType.Polygon:
        parts = geometry.asGeometryCollection() if geometry.isMultipart() else [geometry]
        rings = []
        for part in parts:
            line = part.asPolyline()
            if len(line) >= 4 and line[0] == line[-1]:
                rings.append(QgsGeometry.fromPolygonXY([line]))
        if not rings:
            return []
        geometry = QgsGeometry.collectGeometry(rings)
    if geometry.type() != family:
        return []
    if target.startswith("Multi"):
        geometry = QgsGeometry(geometry)
        geometry.convertToMultiType()
        return [geometry]
    return [part for part in geometry.asGeometryCollection()] if geometry.isMultipart() else [geometry]


def _fold(text) -> str:
    return normalize_tabaka(text).replace("_", "")


def carry_value(value, field, codelists):
    """(value to write, reason when skipped) for one plan value from the source.

    NULL is simply absent (reason None). A code-list value is written as the
    list's own code when it folds onto exactly one (``AYRIK`` -> ``Ayrik``);
    a number only when the form's bounds accept it, so a TAKS read as ``35``
    never lands in the workspace as a plan decision.
    """
    if value is None or str(value) in ("", "NULL"):
        return None, None
    kind = field["type"]
    if kind == "enum":
        codes = [c for c in codelists.get(field["codelist"], []) if _fold(c) == _fold(value)]
        return (codes[0], None) if len(codes) == 1 else (None, "kod listesinde karşılığı yok")
    if kind in ("double", "int", "long"):
        try:
            number = float(str(value).replace(",", "."))
        except ValueError:
            return None, "sayı değil"
        rule = rule_for(field)
        if rule is not None and not value_in_rule(number, rule):
            return None, rule.reason
        if kind in ("int", "long"):
            if number != int(number):
                return None, "tam sayı değil"
            return int(number), None
        return number, None
    if kind == "string":
        return str(value), None
    return None, None


def import_cad_layer(source, tabaka_field, workspace, feedback=None, project=None):
    """Write ``source`` features into the MPYY workspace by their tabaka name.

    Returns one report row per tabaka: count, MPYY type, written, and why the rest was not."""
    level = workspace_level(workspace)
    if level is None:
        raise ValueError('Hedef dosya MPYY 1.1.7 çalışma alanı değil (mpyy_sema tablosu yok).')
    if source.fields().indexFromName(tabaka_field) < 0:
        raise ValueError(f'Kaynakta tabaka alanı yok: {tabaka_field}')
    table = crosswalk(level)
    user_mappings = load_user_mappings()
    schema = level_schema(level)
    types = {t["name"]: t for t in schema["feature_types"]}
    source_names = set(source.fields().names())
    groups = {}
    for feature in source.getFeatures(QgsFeatureRequest()):
        groups.setdefault(str(feature[tabaka_field] or ""), []).append(feature)

    targets, report = {}, []
    project = project or QgsProject.instance()
    total = max(len(groups), 1)
    for step, (tabaka, features) in enumerate(sorted(groups.items())):
        if feedback is not None:
            if feedback.isCanceled():
                break
            feedback.setProgress(100 * step / total)
        key = normalize_tabaka(tabaka)
        # Exact, then a confirmed mapping, then a meaning-preserving spelling rule;
        # a mere suggestion is never applied here (core/tabaka_matching.py).
        match = resolve(level, tabaka, user=user_mappings)
        entry = match.entry
        row = {"tabaka": tabaka, "adet": len(features), "mpyy_tipi": "", "oznitelik": "", "aktarilan": 0,
               "geometri_uyusmayan": 0, "durum": "", "eslesme": match.method,
               "eslesme_kurali": match.rule}
        if entry is None:
            row["durum"] = table["skipped"].get(key) or match.rule or "eşleşme tablosunda yok"
            report.append(row)
            continue
        type_name = entry["feature"]
        if type_name not in types:
            # A stored mapping to something that is not one MPYY table (an older
            # confirmation of a composite road record): reported, never opened.
            row["durum"] = f"MPYY şemasında tek bir tablo değil: {type_name}"
            report.append(row)
            continue
        row["mpyy_tipi"] = type_name
        row["oznitelik"] = ", ".join(f"{k}={v}" for k, v in entry["attrs"].items())
        target = targets.get(type_name)
        if target is None:
            target = QgsVectorLayer(f"{Path(workspace).resolve()}|layername={type_name}", type_name, "ogr")
            if not target.isValid():
                raise RuntimeError('Hedef tablo açılamadı: ' + type_name)
            targets[type_name] = target
        transform = QgsCoordinateTransform(source.crs(), target.crs(), project)
        # Plan values the source already carries under the schema's own field
        # names (KatAdedi, Taks, YapiDuzeni ... read from the drawing's texts):
        # carried over, but only as the form would accept them.
        carried = [f for f in types[type_name]["fields"]
                   if f["name"] in source_names and f["name"] not in entry["attrs"]]
        row["tasinan_deger"] = 0
        row["atlanan_deger"] = []
        new_features = []
        for feature in features:
            geometry = QgsGeometry(feature.geometry())
            if geometry.isNull():
                row["geometri_uyusmayan"] += 1
                continue
            if source.crs() != target.crs():
                geometry.transform(transform)
            parts = _fit_geometry(geometry, types[type_name]["geometry"])
            if not parts:
                row["geometri_uyusmayan"] += 1
                continue
            for part in parts:
                out = QgsFeature(target.fields())
                out.setGeometry(part)
                for field, value in entry["attrs"].items():
                    out[field] = value
                for field in carried:
                    value, why = carry_value(feature[field["name"]], field, schema["codelists"])
                    if value is not None:
                        out[field["name"]] = value
                        row["tasinan_deger"] += 1
                    elif why and len(row["atlanan_deger"]) < 10:
                        row["atlanan_deger"].append(f'{field["name"]}={feature[field["name"]]}: {why}')
                new_features.append(out)
        if new_features:
            ok, _ = target.dataProvider().addFeatures(new_features)
            if not ok:
                raise RuntimeError(f'{type_name}: nesneler yazılamadı: ' + "; ".join(target.dataProvider().errors()[-3:]))
        row["aktarilan"] = len(new_features)
        if row["geometri_uyusmayan"]:
            source_family = FAMILY_NAME.get(features[0].geometry().type(), "?")
            row["durum"] = f'Geometri uyuşmuyor (şema: {FAMILY_NAME[FAMILY[types[type_name]["geometry"]]]}, veri: {source_family})'
        else:
            row["durum"] = "aktarıldı"
        report.append(row)
    for layer in targets.values():
        layer.reload()
    return report


def audit_mpyy_workspace(path, level=None):
    """Schema conformance findings for a MPYY 1.1.7 GeoPackage (read only)."""
    level = level or workspace_level(path)
    if level not in all_levels():
        raise ValueError('Plan kademesi belirlenemedi; kademeyi seçin.')
    schema = level_schema(level)
    types = {t["name"]: t for t in schema["feature_types"]}
    findings = []
    with closing(sqlite3.connect(f"file:{Path(path).resolve().as_posix()}?mode=ro", uri=True)) as con:
        tables = dict(con.execute("SELECT table_name, data_type FROM gpkg_contents"))
        with contextlib.suppress(sqlite3.Error):
            stored = con.execute("SELECT xsd_dosyasi FROM mpyy_sema").fetchone()[0]
            if stored != schema["xsd"]["file"]:
                findings.append({"katman": "mpyy_sema", "fid": "", "sorun": "Şema sürümü farklı",
                                 "ayrinti": f"Çalışma alanı {stored} ile oluşturulmuş; eklentinin şeması {schema['xsd']['file']}. "
                                            "Yeni tipler ve alanlar bu dosyada yok."})
        columns = {name: {row[1] for row in con.execute(f'PRAGMA table_info("{name}")')} for name in tables if name in types}
    for name, kind in sorted(tables.items()):
        if name in SYSTEM_TABLES or name in types or kind not in ("features", "attributes"):
            continue
        findings.append({"katman": name, "fid": "", "sorun": "Şemada olmayan katman",
                         "ayrinti": f"{level} MPYY 1.1.7 şemasında '{name}' tipi yok; GML'e aktarılmaz."})
    for type_name, feature_type in types.items():
        if type_name not in tables:
            findings.append({"katman": type_name, "fid": "", "sorun": "Şemadaki katman dosyada yok",
                             "ayrinti": f"{schema['xsd']['file']} bu tipi içeriyor; çalışma alanı eski bir şemayla oluşturulmuş olabilir."})
            continue
        for field in feature_type["fields"]:
            if field["name"] not in columns[type_name]:
                findings.append({"katman": type_name, "fid": "", "sorun": "Şemadaki alan tabloda yok", "ayrinti": field["name"]})
        layer = QgsVectorLayer(f"{Path(path).resolve()}|layername={type_name}", type_name, "ogr")
        if not layer.isValid():
            findings.append({"katman": type_name, "fid": "", "sorun": "Katman açılamadı", "ayrinti": ""})
            continue
        family = FAMILY.get(feature_type["geometry"])
        fields = feature_type["fields"]
        for feature in layer.getFeatures():
            fid = feature.id()
            geometry = feature.geometry()
            if family is not None:
                if geometry.isNull() or geometry.isEmpty():
                    findings.append({"katman": type_name, "fid": fid, "sorun": "Geometri yok", "ayrinti": ""})
                elif geometry.type() != family:
                    findings.append({"katman": type_name, "fid": fid, "sorun": "Geometri uyuşmuyor",
                                     "ayrinti": f"şema: {FAMILY_NAME[family]}, veri: {FAMILY_NAME.get(geometry.type(), '?')}"})
                elif not geometry.isGeosValid():
                    findings.append({"katman": type_name, "fid": fid, "sorun": "Geçersiz geometri",
                                     "ayrinti": geometry.lastError() or "GEOS geçerlilik denetimi"})
            for field in fields:
                if field["name"] not in columns[type_name]:
                    continue
                value = feature[field["name"]]
                empty = value is None or value == "" or (hasattr(value, "isNull") and value.isNull())
                if empty:
                    if field["required"]:
                        findings.append({"katman": type_name, "fid": fid, "sorun": "Zorunlu alan boş", "ayrinti": field["name"]})
                elif field["type"] == "enum" and str(value) not in schema["codelists"][field["codelist"]]:
                    findings.append({"katman": type_name, "fid": fid, "sorun": "Kod listesinde olmayan değer",
                                     "ayrinti": f'{field["name"]}={value}'})
                else:
                    rule = rule_for(field)
                    if rule is not None and not value_in_rule(value, rule):
                        # Data that came in past the form (GML, CAD transfer, SQL).
                        findings.append({"katman": type_name, "fid": fid, "sorun": "Değer aralık dışında",
                                         "ayrinti": f'{field["name"]}={value}: {rule.reason}'})
            names = [f["name"] for f in fields if f["name"] in columns[type_name]]
            for message in cross_field_findings(feature, names):
                findings.append({"katman": type_name, "fid": fid, "sorun": "Tutarsız değer (uyarı)",
                                 "ayrinti": message})
    return findings


def write_csv(rows, path, columns):
    with open(path, "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return str(path)
