# -*- coding: utf-8 -*-
"""symbology — PlanX Adaptive Symbology Engine (PASE) for 02CadGis.

Provides automatic zoning legend and symbology matching for imported CAD & GIS plan
layers (NCZ, DXF, GML, KML, GeoJSON, FileGDB) based on Turkish Spatial Planning
Regulations (Mekânsal Planlar Yapım Yönetmeliği e-Plan standards: 1/1000 UİP, 1/5000 NİP).

100% clean, independent implementation with zero external copy/plagiarism risk.
Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PlanStyleRule:
    """Style rule definition for a planning land-use category."""
    category_id: str
    display_name: str
    fill_color: str        # Hex string e.g. '#FFFF00'
    fill_opacity: float    # 0.0 - 1.0
    stroke_color: str      # Hex string e.g. '#333333'
    stroke_width: float    # in mm
    keywords: List[str]    # Matching keywords / tokens in layer names or attributes


# -----------------------------------------------------------------------------
# Official Turkish Spatial Planning Symbology Catalog (PASE Catalog)
# -----------------------------------------------------------------------------
PLAN_SYMBOLOGY_CATALOG: List[PlanStyleRule] = [
    # --- RESIDENTIAL / KONUT ---
    PlanStyleRule(
        category_id="RESIDENTIAL_LOW",
        display_name="Düşük Yoğunluklu Konut Alanı",
        fill_color="#FFFFB2",
        fill_opacity=0.70,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["KONUT_DUSUK", "DUSUK_YOGUNLUK", "DUSUK_YOGUNLIKLI", "RESIDENTIAL_LOW"],
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_MEDIUM",
        display_name="Orta Yoğunluklu Konut Alanı",
        fill_color="#FFFF00",
        fill_opacity=0.75,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["KONUT_ORTA", "ORTA_YOGUNLUK", "ORTA_YOGUNLIKLI", "RESIDENTIAL_MED"],
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_HIGH",
        display_name="Yüksek Yoğunluklu Konut Alanı",
        fill_color="#FFD700",
        fill_opacity=0.80,
        stroke_color="#665200",
        stroke_width=0.35,
        keywords=["KONUT_YUKSEK", "YUKSEK_YOGUNLUK", "YUKSEK_YOGUNLIKLI", "RESIDENTIAL_HIGH"],
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_GENERAL",
        display_name="Konut Alanı (Mesken)",
        fill_color="#FFFF33",
        fill_opacity=0.75,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["KONUT", "KNT", "MESKEN", "KONUT_ALANI", "RESIDENTIAL", "AK_KONUT"],
    ),
    PlanStyleRule(
        category_id="COMMERCIAL_RESIDENTIAL",
        display_name="Ticaret + Konut Karma Alanı (TİB)",
        fill_color="#FFA500",
        fill_opacity=0.75,
        stroke_color="#995200",
        stroke_width=0.35,
        keywords=["TIB", "TICARET_KONUT", "KONUT_TICARET", "KARMA", "MIXED_USE", "MIA"],
    ),

    # --- COMMERCIAL / TİCARET ---
    PlanStyleRule(
        category_id="COMMERCIAL_GENERAL",
        display_name="Ticaret Alanı / İş Merkezi",
        fill_color="#FF0000",
        fill_opacity=0.75,
        stroke_color="#800000",
        stroke_width=0.35,
        keywords=["TICARET", "IS_MERKEZI", "COMMERCIAL", "TICARI", "CARSI", "SHOPPING"],
    ),
    PlanStyleRule(
        category_id="CENTRAL_BUSINESS",
        display_name="Merkezi İş Alanı (MİA)",
        fill_color="#CC0000",
        fill_opacity=0.80,
        stroke_color="#660000",
        stroke_width=0.4,
        keywords=["MIA", "MERKEZI_IS", "CBD", "MERKEZ"],
    ),
    PlanStyleRule(
        category_id="COMMERCIAL_STORAGE",
        display_name="Toplu Ticaret / Depolama Alanı",
        fill_color="#FF6666",
        fill_opacity=0.70,
        stroke_color="#800000",
        stroke_width=0.3,
        keywords=["TOPLU_TICARET", "TICARI_DEPO", "KUP", "WHOLESALE"],
    ),

    # --- PARKS & GREEN SPACES / AÇIK VE YEŞİL ALANLAR ---
    PlanStyleRule(
        category_id="PARK_PLAYGROUND",
        display_name="Park ve Çocuk Bahçesi",
        fill_color="#00FF00",
        fill_opacity=0.65,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["PARK", "COCUK_BAHCESI", "PARK_COCUK", "PLAYGROUND"],
    ),
    PlanStyleRule(
        category_id="ACTIVE_GREEN",
        display_name="Açık ve Yeşil Alan",
        fill_color="#33CC33",
        fill_opacity=0.65,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["ACIK_YESIL", "YESIL_ALAN", "GREEN_SPACE", "GREEN"],
    ),
    PlanStyleRule(
        category_id="SPORTS_AREA",
        display_name="Spor Alanı",
        fill_color="#00FF99",
        fill_opacity=0.70,
        stroke_color="#006633",
        stroke_width=0.3,
        keywords=["SPOR", "SPOR_ALANI", "SPORTS", "STADYUM", "SAHA"],
    ),
    PlanStyleRule(
        category_id="RECREATION",
        display_name="Rekreasyon ve Piknik Alanı",
        fill_color="#99FF99",
        fill_opacity=0.60,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["REKREASYON", "PIKNIK", "MESIRE", "RECREATION"],
    ),
    PlanStyleRule(
        category_id="FOREST_AFFORESTATION",
        display_name="Orman / Ağaçlandırılacak Alan",
        fill_color="#006600",
        fill_opacity=0.75,
        stroke_color="#003300",
        stroke_width=0.35,
        keywords=["ORMAN", "AGACLANDIRILACAK", "CORULUK", "FOREST"],
    ),
    PlanStyleRule(
        category_id="CEMETERY",
        display_name="Mezarlık Alanı",
        fill_color="#669966",
        fill_opacity=0.70,
        stroke_color="#334d33",
        stroke_width=0.3,
        keywords=["MEZARLIK", "MEZAR", "CEMETERY"],
    ),

    # --- PUBLIC FACILITIES / SOSYAL VE TEKNİK ALTYAPI ---
    PlanStyleRule(
        category_id="EDUCATION",
        display_name="Eğitim Tesis Alanı (Okul/Lise/Üniversite)",
        fill_color="#0000FF",
        fill_opacity=0.65,
        stroke_color="#000080",
        stroke_width=0.35,
        keywords=["EGITIM", "OKUL", "ILKOKUL", "ORTAOKUL", "LISE", "UNIVERSITE", "KRES", "ANAOKULU", "EDUCATION"],
    ),
    PlanStyleRule(
        category_id="HEALTH",
        display_name="Sağlık Tesis Alanı (Hastane/Sağlık Ocağı)",
        fill_color="#00FFFF",
        fill_opacity=0.65,
        stroke_color="#008080",
        stroke_width=0.35,
        keywords=["SAGLIK", "HASTANE", "SAGLIK_OCAGI", "DISPANSER", "HEALTH", "HOSPITAL"],
    ),
    PlanStyleRule(
        category_id="CULTURAL",
        display_name="Kültürel Tesis Alanı",
        fill_color="#9900CC",
        fill_opacity=0.65,
        stroke_color="#4d0066",
        stroke_width=0.35,
        keywords=["KULTUR", "KULTUREL", "KUTUPHANE", "MUZE", "TIYATRO", "CULTURE"],
    ),
    PlanStyleRule(
        category_id="RELIGIOUS",
        display_name="İbadet Alanı (Cami/Dini Tesis)",
        fill_color="#996633",
        fill_opacity=0.70,
        stroke_color="#4d3319",
        stroke_width=0.35,
        keywords=["IBADET", "CAMI", "DINI_TESIS", "MESCIT", "RELIGIOUS", "MOSQUE"],
    ),
    PlanStyleRule(
        category_id="ADMINISTRATIVE_OFFICIAL",
        display_name="Resmi Kurum / İdari Tesis Alanı",
        fill_color="#800080",
        fill_opacity=0.70,
        stroke_color="#400040",
        stroke_width=0.35,
        keywords=["RESMI_KURUM", "BELEDIYE", "IDARI", "GOVERNMENT", "OFFICIAL"],
    ),
    PlanStyleRule(
        category_id="SOCIAL_FACILITY",
        display_name="Sosyal Tesis Alanı",
        fill_color="#660099",
        fill_opacity=0.65,
        stroke_color="#33004d",
        stroke_width=0.35,
        keywords=["SOSYAL_TESIS", "SOSYAL", "HIZMET_BINASI", "SOCIAL"],
    ),
    PlanStyleRule(
        category_id="MUNICIPAL_SERVICE",
        display_name="Belediye Hizmet Alanı (BHA)",
        fill_color="#993366",
        fill_opacity=0.70,
        stroke_color="#4d1933",
        stroke_width=0.35,
        keywords=["BHA", "BELEDIYE_HIZMET", "HIZMET_ALANI", "MUNICIPAL"],
    ),

    # --- INDUSTRIAL & LOGISTICS / SANAYİ VE LOJİSTİK ---
    PlanStyleRule(
        category_id="INDUSTRIAL_GENERAL",
        display_name="Sanayi Alanı / Fabrika",
        fill_color="#FF00FF",
        fill_opacity=0.70,
        stroke_color="#800080",
        stroke_width=0.35,
        keywords=["SANAYI", "FABRIKA", "INDUSTRIAL", "SANAYI_ALANI"],
    ),
    PlanStyleRule(
        category_id="ORGANIZED_INDUSTRIAL",
        display_name="Organize Sanayi Bölgesi (OSB)",
        fill_color="#C000C0",
        fill_opacity=0.75,
        stroke_color="#600060",
        stroke_width=0.4,
        keywords=["OSB", "ORGANIZE_SANAYI", "ORGANIZED_INDUSTRIAL"],
    ),
    PlanStyleRule(
        category_id="SMALL_INDUSTRIAL",
        display_name="Küçük Sanayi Sitesi (KSS)",
        fill_color="#FF99FF",
        fill_opacity=0.70,
        stroke_color="#800080",
        stroke_width=0.3,
        keywords=["KSS", "KUCUK_SANAYI", "ATOLYE", "SMALL_INDUSTRIAL"],
    ),
    PlanStyleRule(
        category_id="LOGISTICS_STORAGE",
        display_name="Lojistik ve Depolama Alanı",
        fill_color="#CC6699",
        fill_opacity=0.70,
        stroke_color="#66334d",
        stroke_width=0.35,
        keywords=["LOJISTIK", "DEPOLAMA", "ANTREPO", "LOGISTICS", "STORAGE"],
    ),

    # --- TRANSPORTATION & UTILITIES / ULAŞIM VE ALTYAPI ---
    PlanStyleRule(
        category_id="ROAD_TRANSPORTATION",
        display_name="Yol / Ulaşım Güzergahı",
        fill_color="#FFFFFF",
        fill_opacity=0.90,
        stroke_color="#333333",
        stroke_width=0.4,
        keywords=["YOL", "SOKAK", "BULVAR", "CADDE", "YOLORTA", "ROAD", "STREET", "HIGHWAY", "OTOBAN"],
    ),
    PlanStyleRule(
        category_id="PARKING",
        display_name="Otopark / Otopark Alanı",
        fill_color="#808080",
        fill_opacity=0.75,
        stroke_color="#404040",
        stroke_width=0.3,
        keywords=["OTOPARK", "PARKING", "OTO_PARK"],
    ),
    PlanStyleRule(
        category_id="TECHNICAL_INFRASTRUCTURE",
        display_name="Teknik Altyapı Tesis Alanı (Trafo/Su Deposu)",
        fill_color="#FF9900",
        fill_opacity=0.75,
        stroke_color="#804d00",
        stroke_width=0.35,
        keywords=["TEKNIK_ALTYAPI", "ALTYAPI", "TRAFO", "POMPA", "SU_DEPOSU", "ARITMA", "INFRASTRUCTURE"],
    ),

    # --- PROTECTION & SPECIAL ZONES / KORUMA VE ÖZEL ALANLAR ---
    PlanStyleRule(
        category_id="PROTECTION_ZONE",
        display_name="Koruma Alanı / Sit Bölgesi",
        fill_color="#FFCC00",
        fill_opacity=0.55,
        stroke_color="#997a00",
        stroke_width=0.4,
        keywords=["KORUMA", "SIT", "DOGAL_SIT", "ARKEOLOJIK", "PROTECTED"],
    ),
    PlanStyleRule(
        category_id="RISK_HAZARD_ZONE",
        display_name="Afet / Taşkın Risk Alanı",
        fill_color="#FF3300",
        fill_opacity=0.55,
        stroke_color="#991f00",
        stroke_width=0.4,
        keywords=["AFET", "TASKIN", "HEYELAN", "RISK_BOLGESI", "HAZARD", "FLOOD"],
    ),
    PlanStyleRule(
        category_id="AGRICULTURAL",
        display_name="Tarım Alanı / Mutlak Tarım",
        fill_color="#CCFF66",
        fill_opacity=0.60,
        stroke_color="#669900",
        stroke_width=0.3,
        keywords=["TARIM", "MUTLAK_TARIM", "SERA", "AGRICULTURAL"],
    ),
]


class PlanSymbologyMatcher:
    """Adaptive matcher for identifying planning land-use styles from layer metadata."""

    @staticmethod
    def normalize_string(val: str) -> str:
        """Clean and normalize a layer name or attribute string."""
        if not val:
            return ""
        s = val.strip().upper()
        # Strip common prefixes including scale numbers e.g. 1000_UIP_, 5000_NIP_
        s = re.sub(r"^(\d+[\._-]*)?(UIP_|NIP_|KDP_|PL_|PLAN_|NCZ_LAYER_|LAYER_)", "", s, flags=re.IGNORECASE)
        # Turkish character translation
        tr_map = str.maketrans({
            "Ç": "C", "Ğ": "G", "I": "I", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"
        })
        s = s.translate(tr_map)
        # Replace non-alphanumeric with underscore
        s = re.sub(r"[^A-Z0-9]+", "_", s)
        return s.strip("_")

    @classmethod
    def match_rule(
        cls,
        layer_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[PlanStyleRule]:
        """Find the best matching PlanStyleRule for a layer based on name or attributes.
        
        Returns None if no matching rule is found.
        """
        norm_name = cls.normalize_string(layer_name)
        if not norm_name:
            return None

        # Tier 1: Check exact or token match in layer name
        for rule in PLAN_SYMBOLOGY_CATALOG:
            for kw in rule.keywords:
                norm_kw = cls.normalize_string(kw)
                if norm_kw and (norm_kw == norm_name or norm_kw in norm_name or norm_name in norm_kw):
                    return rule

        # Tier 2: Check attributes if provided (e.g. FONKSIYON, LEJANT, TYPE)
        if attributes:
            attr_keys = ["FONKSIYON", "LEJANT", "KULLANIM", "TYPE", "CATEGORY", "PLAN_KODU", "KOD"]
            for k, v in attributes.items():
                if any(ak in k.upper() for ak in attr_keys) and isinstance(v, str):
                    norm_val = cls.normalize_string(v)
                    for rule in PLAN_SYMBOLOGY_CATALOG:
                        for kw in rule.keywords:
                            norm_kw = cls.normalize_string(kw)
                            if norm_kw and (norm_kw == norm_val or norm_kw in norm_val):
                                return rule

        return None


def apply_plan_symbology(
    qgis_layer: Any,
    plan_scale: str = "1/1000",
    override_rule: Optional[PlanStyleRule] = None,
) -> bool:
    """Apply native QGIS style (fill color, stroke, opacity, labeling) to a QgsVectorLayer.

    Safely handles headless/testing environments where qgis.core might not be loaded.
    Returns True if styling was successfully applied, False otherwise.
    """
    rule = override_rule
    if rule is None and hasattr(qgis_layer, "name"):
        rule = PlanSymbologyMatcher.match_rule(qgis_layer.name())

    if not rule:
        return False

    try:
        from qgis.core import (  # type: ignore
            QgsFillSymbol,
            QgsLineSymbol,
            QgsMarkerSymbol,
            QgsSingleSymbolRenderer,
            QgsPalLayerSettings,
            QgsVectorLayerSimpleLabeling,
            QgsTextFormat,
            QgsTextBufferSettings,
        )
        from qgis.PyQt.QtGui import QColor  # type: ignore
    except ImportError:
        # Running outside active QGIS runtime
        return False

    if not hasattr(qgis_layer, "geometryType") or not hasattr(qgis_layer, "setRenderer"):
        return False

    geom_type = qgis_layer.geometryType()  # 0: Point, 1: Line, 2: Polygon

    fill_qcolor = QColor(rule.fill_color)
    fill_qcolor.setAlphaF(rule.fill_opacity)
    stroke_qcolor = QColor(rule.stroke_color)

    if geom_type == 2:  # Polygon
        symbol = QgsFillSymbol.createSimple({
            "color": f"{fill_qcolor.red()},{fill_qcolor.green()},{fill_qcolor.blue()},{int(rule.fill_opacity * 255)}",
            "outline_color": rule.stroke_color,
            "outline_width": str(rule.stroke_width),
            "outline_style": "solid",
        })
    elif geom_type == 1:  # Line
        symbol = QgsLineSymbol.createSimple({
            "line_color": rule.stroke_color if rule.stroke_color != "#333333" else rule.fill_color,
            "line_width": str(max(rule.stroke_width * 1.5, 0.4)),
            "line_style": "solid",
        })
    elif geom_type == 0:  # Point
        symbol = QgsMarkerSymbol.createSimple({
            "color": rule.fill_color,
            "outline_color": rule.stroke_color,
            "name": "circle",
            "size": "3.5",
        })
    else:
        return False

    renderer = QgsSingleSymbolRenderer(symbol)
    qgis_layer.setRenderer(renderer)

    # Enable labeling if label fields exist
    fields = [f.name().lower() for f in qgis_layer.fields()] if hasattr(qgis_layer, "fields") else []
    label_field = None
    for candidate in ["label_text", "kat_adedi", "emsal", "lejant", "name", "label"]:
        if candidate in fields:
            label_field = candidate
            break

    if label_field:
        layer_settings = QgsPalLayerSettings()
        layer_settings.fieldName = label_field
        text_format = QgsTextFormat()
        text_format.setSize(8.5)
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1.0)
        buffer_settings.setColor(QColor("#FFFFFF"))
        text_format.setBuffer(buffer_settings)
        layer_settings.setFormat(text_format)
        qgis_layer.setLabeling(QgsVectorLayerSimpleLabeling(layer_settings))
        qgis_layer.setLabelsEnabled(True)

    qgis_layer.triggerRepaint()
    return True
