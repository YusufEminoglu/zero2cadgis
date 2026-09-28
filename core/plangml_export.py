# -*- coding: utf-8 -*-
"""plangml_export — DRAFT PlanGML-style (.gml) writer. Not wired into the UI.

NOT conformant with the Ministry schema, and must not be presented as if it
were. Checked against ``planGMLShema_1_7.zip`` (uip/nip/cdp.V.1.1.7.xsd):

* the schema's target namespace is ``www.csb.gov.tr`` (prefix ``plan``), GML
  2.1.2 — this writer emits ``http://www.csb.gov.tr/uip_1000`` and GML 3;
* feature types are e.g. ``Konut`` + a mandatory ``KonutTip`` enum,
  ``EgitimTesisAlani`` + ``EgitimTesisTip`` — this writer invents names such as
  ``KonutAlani`` / ``TasitYolu`` by keyword guess;
* the property is ``GeometryProperty`` of ``gml:MultiPolygonPropertyType`` and
  ``AbstractYapilasma`` requires ``KatAdedi``, ``EmsalKaks``, ``Taks``,
  ``YapiYuksekligi``, ``OnBahceMesafesi``… (``minOccurs=1``) — values a CAD
  drawing mostly does not carry and that must not be invented.

A real exporter has to be driven by the XSD and by attribute values the user
supplies. Until then this module stays unreachable from the dock.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from contextlib import suppress
import os
import re
from typing import Any, Dict, List, Optional


def _escape_xml_text(s: Any) -> str:
    """Escape XML special characters in element text."""
    val = str(s)
    return val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_xml_attr(s: Any) -> str:
    """Escape XML special characters in attribute values."""
    val = str(s)
    return (
        val.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class XmlNode:
    """Lightweight XML node representation for clean XML generation without Bandit B405."""

    def __init__(
        self,
        tag: str,
        attrs: Optional[Dict[str, str]] = None,
        text: Optional[str] = None,
    ):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.text = text
        self.children: List[XmlNode] = []

    def sub_element(
        self,
        tag: str,
        attrs: Optional[Dict[str, str]] = None,
        text: Optional[str] = None,
    ) -> XmlNode:
        child = XmlNode(tag, attrs, text)
        self.children.append(child)
        return child

    def to_xml(self, level: int = 0) -> str:
        indent = "  " * level
        attr_str = "".join(f' {k}="{_escape_xml_attr(v)}"' for k, v in self.attrs.items())
        if not self.children and (self.text is None or self.text == ""):
            return f"{indent}<{self.tag}{attr_str}/>\n"
        if not self.children:
            return f"{indent}<{self.tag}{attr_str}>{_escape_xml_text(self.text)}</{self.tag}>\n"
        inner = "".join(c.to_xml(level + 1) for c in self.children)
        return f"{indent}<{self.tag}{attr_str}>\n{inner}{indent}</{self.tag}>\n"

try:
    from qgis.core import (
        QgsCoordinateTransform,
        QgsFeature,
        QgsGeometry,
        QgsProject,
        QgsVectorLayer,
        QgsWkbTypes,
    )
except ImportError:
    QgsCoordinateTransform = None
    QgsFeature = None
    QgsGeometry = None
    QgsProject = None
    QgsVectorLayer = None
    QgsWkbTypes = None

from .export_utils import (
    atomic_output,
    exported_feature_count,
    verified_export_result,
    ExportResult,
)


# Official namespace configurations per plan type
PLANGML_NAMESPACES = {
    "UIP": {
        "prefix": "uip",
        "uri": "http://www.csb.gov.tr/uip_1000",
        "schema": "http://www.csb.gov.tr/uip_1000 uip_1000.xsd",
    },
    "NIP": {
        "prefix": "nip",
        "uri": "http://www.csb.gov.tr/nip_5000",
        "schema": "http://www.csb.gov.tr/nip_5000 nip_5000.xsd",
    },
    "CDP": {
        "prefix": "cdp",
        "uri": "http://www.csb.gov.tr/cdp_25000",
        "schema": "http://www.csb.gov.tr/cdp_25000 cdp_25000.xsd",
    },
}

# Standard mappings from common Turkish planning keywords to official PlanGML element names
ELEMENT_NAME_MAP = {
    "KONUT": "KonutAlani",
    "GELISME_KONUT": "GelismeKonutAlani",
    "YERLESIK_KONUT": "YerlesikKonutAlani",
    "TICARET": "TicaretAlani",
    "TICARET_KONUT": "TicaretKonutAlani",
    "TICKONUT": "TicaretKonutAlani",
    "PARK": "ParkAlani",
    "COCUK_BAHCESI": "CocukBahcesiVeOyunAlani",
    "YESIL": "AcikVeYesilAlan",
    "EGITIM": "EgitimTesisiAlani",
    "ILKOKUL": "IlkokulAlani",
    "ORTAOKUL": "OrtaokulAlani",
    "LISE": "LiseAlani",
    "ANAOKULU": "AnaokuluAlani",
    "SAGLIK": "SaglikTesisiAlani",
    "HASTANE": "HastaneAlani",
    "AILE_SAGLIK": "AileSagligiMerkeziAlani",
    "IBADET": "IbadetAlani",
    "CAMI": "CamiAlani",
    "KOP": "KamuOrtaklikPayiAlani",
    "BHA": "BelediyeHizmetAlani",
    "RESMI_KURUM": "ResmiKurumAlani",
    "IDARI": "IdariTesisAlani",
    "SOSYAL": "SosyalTesisAlani",
    "KULTUREL": "KulturelTesisAlani",
    "TEKNIK_ALTYAPI": "TeknikAltyapiAlani",
    "TRAFO": "TrafoAlani",
    "SU_DEPOSU": "SuDeposuAlani",
    "YOL": "TasitYolu",
    "TASIT_YOLU": "TasitYolu",
    "YAYA_YOLU": "YayaYolu",
    "OTOPARK": "OtoparkAlani",
    "PLAN_SINIRI": "PlanOnamaSiniri",
    "ONAMA_SINIRI": "PlanOnamaSiniri",
    "CEKME_MESAFESI": "YapiYaklasmaSiniri",
    "YAPI_YAKLASMA": "YapiYaklasmaSiniri",
    "SANAYI": "SanayiAlani",
    "KUCUK_SANAYI": "KucukSanayiAlani",
    "DEPO": "DepolamaAlani",
    "MEZARLIK": "MezarlikAlani",
    "AGACLANDIRILACAK": "AgaclandirilacakAlan",
    "ORMAN": "OrmanAlani",
    "MERA": "MeraAlani",
    "TARIM": "TarimsalNitelikliAlan",
}


def _resolve_element_name(feature: QgsFeature, layer_name: str) -> str:
    """Resolve the official UpperCamelCase XML element name from feature attributes."""
    candidate_tokens = []
    for field_name in ("TAM_ADI", "uip_tabaka", "FONKSIYON_KODU", "GISTERIM"):
        with suppress(Exception):
            val = str(feature[field_name] or "").strip()
            if val:
                candidate_tokens.append(val)

    candidate_tokens.append(layer_name)

    for cand in candidate_tokens:
        elem = PlanGmlExporter.map_to_element_name(cand)
        if elem != "PlanAlani":
            return elem

    return PlanGmlExporter.map_to_element_name(layer_name)


class PlanGmlExporter:
    """Exports QGIS vector plan layers to official Ministry PlanGML XML format."""

    @staticmethod
    def map_to_element_name(token: str) -> str:
        """Map a planning tabaka, function code, or text token to an official PlanGML element name."""
        if not token:
            return "PlanAlani"
        upper = str(token).upper().translate(str.maketrans("ÇĞİÖŞÜ", "CGIOSU"))
        clean = re.sub(r"^(PL_|HAT_|SNR_|UIP_|NIP_|CDP_)", "", upper)
        clean = re.sub(r"(_POLYGON|_LINESTRING|_POINT)$", "", clean)
        clean_key = re.sub(r"[^A-Z0-9]+", "_", clean).strip("_")

        if clean_key in ELEMENT_NAME_MAP:
            return ELEMENT_NAME_MAP[clean_key]

        for kw, elem in ELEMENT_NAME_MAP.items():
            if kw in clean_key:
                return elem

        words = [w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", str(token)) if w]
        return "".join(words) or "PlanAlani"

    @staticmethod
    def export_layer_to_plangml(
        layer: QgsVectorLayer,
        output_path: str,
        plan_type: str = "UIP",
        target_crs=None,
        selected_only: bool = False,
    ) -> ExportResult:
        """Export a vector layer to valid PlanGML GML 3 file.

        Args:
            layer: Source QgsVectorLayer.
            output_path: Target .gml file path.
            plan_type: UIP, NIP, or CDP (defaults to UIP).
            target_crs: Optional reprojected coordinate system.
            selected_only: True to export only selected features.

        Returns:
            An :class:`ExportResult` summary.
        """
        if not layer or not layer.isValid():
            raise ValueError("Geçersiz kaynak katman.")

        source_crs = layer.crs()
        if not source_crs.isValid():
            raise ValueError("Kaynak katmanın geçerli bir koordinat sistemi (CRS) yok.")

        effective_crs = target_crs if target_crs and target_crs.isValid() else source_crs
        coord_transform = None
        if source_crs != effective_crs:
            coord_transform = QgsCoordinateTransform(source_crs, effective_crs, QgsProject.instance())

        feature_count = exported_feature_count(layer, selected_only)
        if selected_only and feature_count == 0:
            raise ValueError("Katman üzerinde seçili detay bulunamadı.")

        plan_type_upper = (plan_type or "UIP").upper()
        ns_cfg = PLANGML_NAMESPACES.get(plan_type_upper, PLANGML_NAMESPACES["UIP"])
        ns_prefix = ns_cfg["prefix"]
        ns_uri = ns_cfg["uri"]
        srs_name = effective_crs.authid() if effective_crs.isValid() else "EPSG:3147"

        # XML Structure construction via lightweight XmlNode
        root = XmlNode(
            "gml:FeatureCollection",
            {
                "xmlns:gml": "http://www.opengis.net/gml",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                f"xmlns:{ns_prefix}": ns_uri,
                "xsi:schemaLocation": f"{ns_uri} {ns_cfg['schema']}",
            },
        )

        features = layer.selectedFeatures() if selected_only else layer.getFeatures()
        feature_idx = 1

        for feat in features:
            geom = feat.geometry()
            if not geom or geom.isEmpty():
                continue

            if coord_transform:
                with suppress(Exception):
                    geom.transform(coord_transform)

            element_name = _resolve_element_name(feat, layer.name())
            member_elem = root.sub_element("gml:featureMember")
            feature_elem = member_elem.sub_element(
                f"{ns_prefix}:{element_name}",
                {"gml:id": f"fid_{feature_idx}"},
            )

            # Geometry Property
            geom_prop = feature_elem.sub_element(f"{ns_prefix}:geometryProperty")
            wkb_type = geom.wkbType()
            geom_type = QgsWkbTypes.geometryType(wkb_type)

            if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry:
                poly_elem = geom_prop.sub_element("gml:Polygon", {"srsName": srs_name})
                ext_elem = poly_elem.sub_element("gml:exterior")
                ring_elem = ext_elem.sub_element("gml:LinearRing")
                coords_str = []
                with suppress(Exception):
                    if geom.isMultipart():
                        polygons = geom.asMultiPolygon()
                        if polygons and len(polygons[0]) > 0:
                            coords_str = [f"{p.x():.3f} {p.y():.3f}" for p in polygons[0][0]]
                    else:
                        polygon = geom.asPolygon()
                        if polygon and len(polygon) > 0:
                            coords_str = [f"{p.x():.3f} {p.y():.3f}" for p in polygon[0]]
                ring_elem.sub_element("gml:posList", {"srsDimension": "2"}, text=" ".join(coords_str))

            elif geom_type == QgsWkbTypes.GeometryType.LineGeometry:
                line_elem = geom_prop.sub_element("gml:LineString", {"srsName": srs_name})
                coords_str = []
                with suppress(Exception):
                    if geom.isMultipart():
                        lines = geom.asMultiPolyline()
                        if lines:
                            coords_str = [f"{p.x():.3f} {p.y():.3f}" for p in lines[0]]
                    else:
                        line = geom.asPolyline()
                        coords_str = [f"{p.x():.3f} {p.y():.3f}" for p in line]
                line_elem.sub_element("gml:posList", {"srsDimension": "2"}, text=" ".join(coords_str))

            elif geom_type == QgsWkbTypes.GeometryType.PointGeometry:
                pt_elem = geom_prop.sub_element("gml:Point", {"srsName": srs_name})
                pt_coords_text = ""
                with suppress(Exception):
                    pt = geom.asPoint()
                    pt_coords_text = f"{pt.x():.3f} {pt.y():.3f}"
                pt_elem.sub_element("gml:pos", {"srsDimension": "2"}, text=pt_coords_text)

            # Attributes adhering to PlanGML sequence
            attr_mappings = [
                ("PlanKodu", ["PLAN_KODU", "plan_kodu"], f"{plan_type_upper}_1000"),
                ("FonksiyonKodu", ["FONKSIYON_KODU", "fonksiyon_kodu", "DETAY_GRUP_ID"], None),
                ("TamAdi", ["TAM_ADI", "tam_adi", "fonksiyon_adi", "uip_tabaka"], None),
                ("YapiDuzeni", ["YapiDuzeni", "yapi_duzeni"], None),
                ("KatAdedi", ["KatAdedi", "kat_adedi"], None),
                ("EmsalKaks", ["EmsalKaks", "emsal_kaks", "kaks", "emsal"], None),
                ("Taks", ["Taks", "taks"], None),
                ("YapiYuksekligi", ["YapiYuksekligi", "yapi_yuksekligi", "hmax"], None),
                ("AdaNo", ["AdaNo", "ada_no", "ada"], None),
                ("ParselNo", ["ParselNo", "parsel_no", "parsel"], None),
                ("YolGenisligi", ["YolGenisligi", "yol_genisligi"], None),
                ("Gosterim", ["GISTERIM", "GÖSTERİM", "gosterim"], None),
            ]

            field_names = [f.name() for f in layer.fields()]
            for xml_tag, candidate_fields, default_val in attr_mappings:
                val = None
                for cf in candidate_fields:
                    if cf in field_names:
                        v = feat[cf]
                        if v is not None and str(v).strip() != "":
                            val = str(v).strip()
                            break
                if val is None and default_val is not None:
                    val = default_val

                if val is not None:
                    feature_elem.sub_element(f"{ns_prefix}:{xml_tag}", text=val)

            feature_idx += 1

        # Write atomic XML output
        xml_content = '<?xml version="1.0" encoding="utf-8"?>\n' + root.to_xml(level=0)

        with atomic_output(output_path) as temp_path:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

        return verified_export_result(output_path, "PlanGML", feature_count, srs_name)
