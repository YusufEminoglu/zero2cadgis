# -*- coding: utf-8 -*-
"""symbology — PlanX Adaptive Symbology Engine (PASE) for 02CadGis.

Provides automatic zoning legend and symbology matching for imported CAD & GIS plan
layers (NCZ, DXF, GML, KML, GeoJSON, FileGDB) based on Turkish Spatial Planning
Regulations (Mekânsal Planlar Yapım Yönetmeliği e-Plan standards: 1/1000 UİP, 1/5000 NİP).

Supports native vector hatch fills (tarama desenleri), custom stroke widths and line styles
(solid, dash, dash-dot), point symbols, text annotations, and rule-based/categorized layer styling.

100% clean, independent implementation authored by Yusuf Eminoğlu with zero external plagiarism.
Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PlanStyleRule:
    """Style rule definition for a planning land-use category."""
    category_id: str
    display_name: str
    fill_color: str                         # Hex string e.g. '#FFFF00'
    fill_opacity: float                     # 0.0 - 1.0
    stroke_color: str                       # Hex string e.g. '#333333'
    stroke_width: float                     # in mm
    keywords: List[str]                     # Matching keywords / tokens in layer names or attributes
    stroke_style: str = "solid"             # solid, dash, dot, dashdot
    hatch_pattern: Optional[str] = None     # None, diagonal, cross, horizontal, vertical
    hatch_color: Optional[str] = None       # Hex string for hatch lines
    hatch_distance: float = 3.0             # Line pattern spacing in mm
    hatch_angle: float = 45.0               # Line pattern angle in degrees
    marker_shape: str = "circle"            # circle, square, triangle, cross


# -----------------------------------------------------------------------------
# Official Turkish Spatial Planning Symbology Catalog (PASE Catalog)
# -----------------------------------------------------------------------------
PLAN_SYMBOLOGY_CATALOG: List[PlanStyleRule] = [
    # --- PLAN BOUNDARIES & CADASTRAL LINES ---
    PlanStyleRule(
        category_id="PLAN_BOUNDARY",
        display_name="Plan Sınırı / Ada Kenarı",
        fill_color="#000000",
        fill_opacity=0.0,
        stroke_color="#000000",
        stroke_width=0.8,
        stroke_style="solid",
        keywords=["ADA_KENARI", "PLAN_SINIRI", "SINIR", "KENAR", "PARSEL_KENARI", "CADASTRE", "BOUNDARY"],
    ),
    PlanStyleRule(
        category_id="SIDEWALK",
        display_name="Kaldırım / Yaya Yolu",
        fill_color="#FF0000",
        fill_opacity=0.0,
        stroke_color="#FF0000",
        stroke_width=0.4,
        stroke_style="solid",
        keywords=["KALDIRIM", "YAYA_YOLU", "YAYA", "SIDEWALK", "PAVEMENT"],
    ),
    PlanStyleRule(
        category_id="REFUGE",
        display_name="Refüj / Orta Refüj",
        fill_color="#008000",
        fill_opacity=0.0,
        stroke_color="#008000",
        stroke_width=0.4,
        stroke_style="solid",
        keywords=["REFUJ", "ORTA_REFUJ", "MEDIAN"],
    ),

    # --- RESIDENTIAL / KONUT ---
    PlanStyleRule(
        category_id="RESIDENTIAL_LOW",
        display_name="Düşük Yoğunluklu Konut Alanı",
        fill_color="#FFFFB2",
        fill_opacity=1.0,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["KONUT_DUSUK", "DUSUK_YOGUNLUK", "DUSUK_YOGUNLIKLI", "RESIDENTIAL_LOW"],
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_MEDIUM",
        display_name="Orta Yoğunluklu Konut Alanı",
        fill_color="#FFFF00",
        fill_opacity=1.0,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["KONUT_ORTA", "ORTA_YOGUNLUK", "ORTA_YOGUNLIKLI", "RESIDENTIAL_MED"],
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_HIGH",
        display_name="Yüksek Yoğunluklu Konut Alanı",
        fill_color="#FFD700",
        fill_opacity=1.0,
        stroke_color="#665200",
        stroke_width=0.35,
        keywords=["KONUT_YUKSEK", "YUKSEK_YOGUNLUK", "YUKSEK_YOGUNLIKLI", "RESIDENTIAL_HIGH"],
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_GENERAL",
        display_name="Konut Alanı (Mesken)",
        fill_color="#FFFF00",
        fill_opacity=1.0,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["KONUT", "KNT", "MESKEN", "KONUT_ALANI", "RESIDENTIAL", "AK_KONUT"],
    ),
    PlanStyleRule(
        category_id="COMMERCIAL_RESIDENTIAL",
        display_name="Ticaret + Konut Karma Alanı (TİB)",
        fill_color="#FFA500",
        fill_opacity=1.0,
        stroke_color="#995200",
        stroke_width=0.35,
        keywords=["TIB", "TICARET_KONUT", "KONUT_TICARET", "KARMA", "MIXED_USE"],
    ),

    # --- COMMERCIAL / TİCARET ---
    PlanStyleRule(
        category_id="COMMERCIAL_GENERAL",
        display_name="Ticaret Alanı / İş Merkezi",
        fill_color="#FF0000",
        fill_opacity=1.0,
        stroke_color="#800000",
        stroke_width=0.35,
        keywords=["TICARET", "TCR", "IS_MERKEZI", "COMMERCIAL", "TICARI", "CARSI", "SHOPPING"],
    ),
    PlanStyleRule(
        category_id="CENTRAL_BUSINESS",
        display_name="Merkezi İş Alanı (MİA)",
        fill_color="#CC0000",
        fill_opacity=1.0,
        stroke_color="#660000",
        stroke_width=0.4,
        keywords=["MIA", "MERKEZI_IS", "CBD", "MERKEZ"],
    ),
    PlanStyleRule(
        category_id="COMMERCIAL_STORAGE",
        display_name="Toplu Ticaret / Depolama Alanı",
        fill_color="#FF6666",
        fill_opacity=1.0,
        stroke_color="#800000",
        stroke_width=0.3,
        keywords=["TOPLU_TICARET", "TICARI_DEPO", "KUP", "WHOLESALE"],
    ),

    # --- PARKS & GREEN SPACES / AÇIK VE YEŞİL ALANLAR ---
    PlanStyleRule(
        category_id="PARK_PLAYGROUND",
        display_name="Park ve Çocuk Bahçesi",
        fill_color="#00FF00",
        fill_opacity=1.0,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["PARK", "COCUK_BAHCESI", "PARK_COCUK", "PLAYGROUND"],
    ),
    PlanStyleRule(
        category_id="ACTIVE_GREEN",
        display_name="Açık ve Yeşil Alan",
        fill_color="#33CC33",
        fill_opacity=1.0,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["ACIK_YESIL", "YESIL_ALAN", "YESIL", "GREEN_SPACE", "GREEN"],
    ),
    PlanStyleRule(
        category_id="SPORTS_AREA",
        display_name="Spor Alanı",
        fill_color="#00FF99",
        fill_opacity=1.0,
        stroke_color="#006633",
        stroke_width=0.3,
        marker_shape="square",
        keywords=["SPOR", "SPOR_ALANI", "SPORTS", "STADYUM", "SAHA"],
    ),
    PlanStyleRule(
        category_id="RECREATION",
        display_name="Rekreasyon ve Piknik Alanı",
        fill_color="#99FF99",
        fill_opacity=1.0,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["REKREASYON", "PIKNIK", "MESIRE", "RECREATION"],
    ),
    PlanStyleRule(
        category_id="FOREST_AFFORESTATION",
        display_name="Orman / Ağaçlandırılacak Alan",
        fill_color="#006600",
        fill_opacity=1.0,
        stroke_color="#003300",
        stroke_width=0.35,
        hatch_pattern="diagonal",
        hatch_color="#003300",
        hatch_distance=3.5,
        hatch_angle=45.0,
        keywords=["ORMAN", "AGACLANDIRILACAK", "CORULUK", "FOREST"],
    ),
    PlanStyleRule(
        category_id="CEMETERY",
        display_name="Mezarlık Alanı",
        fill_color="#669966",
        fill_opacity=1.0,
        stroke_color="#334d33",
        stroke_width=0.3,
        hatch_pattern="cross",
        hatch_color="#334d33",
        hatch_distance=4.0,
        keywords=["MEZARLIK", "MEZAR", "CEMETERY"],
    ),

    # --- PUBLIC FACILITIES / SOSYAL VE TEKNİK ALTYAPI ---
    PlanStyleRule(
        category_id="EDUCATION",
        display_name="Eğitim Tesis Alanı (Okul/Lise/Üniversite)",
        fill_color="#0000FF",
        fill_opacity=1.0,
        stroke_color="#000080",
        stroke_width=0.35,
        marker_shape="square",
        keywords=["EGITIM", "EGTM", "OKUL", "OKL", "ILKOKUL", "ORTAOKUL", "LISE", "UNIVERSITE", "KRES", "ANAOKULU", "EDUCATION"],
    ),
    PlanStyleRule(
        category_id="HEALTH",
        display_name="Sağlık Tesis Alanı (Hastane/Sağlık Ocağı)",
        fill_color="#00FFFF",
        fill_opacity=1.0,
        stroke_color="#008080",
        stroke_width=0.35,
        marker_shape="cross",
        keywords=["SAGLIK", "SGL", "HASTANE", "SAGLIK_OCAGI", "DISPANSER", "HEALTH", "HOSPITAL"],
    ),
    PlanStyleRule(
        category_id="CULTURAL",
        display_name="Kültürel Tesis Alanı",
        fill_color="#9900CC",
        fill_opacity=1.0,
        stroke_color="#4d0066",
        stroke_width=0.35,
        keywords=["KULTUR", "KULTUREL", "KUTUPHANE", "MUZE", "TIYATRO", "CULTURE"],
    ),
    PlanStyleRule(
        category_id="RELIGIOUS",
        display_name="İbadet Alanı (Cami/Dini Tesis)",
        fill_color="#996633",
        fill_opacity=1.0,
        stroke_color="#4d3319",
        stroke_width=0.35,
        marker_shape="triangle",
        keywords=["IBADET", "CAMI", "DINI_TESIS", "MESCIT", "RELIGIOUS", "MOSQUE"],
    ),
    PlanStyleRule(
        category_id="ADMINISTRATIVE_OFFICIAL",
        display_name="Resmi Kurum / İdari Tesis Alanı",
        fill_color="#800080",
        fill_opacity=1.0,
        stroke_color="#400040",
        stroke_width=0.35,
        keywords=["RESMI_KURUM", "BELEDIYE", "IDARI", "GOVERNMENT", "OFFICIAL"],
    ),
    PlanStyleRule(
        category_id="SOCIAL_FACILITY",
        display_name="Sosyal Tesis Alanı",
        fill_color="#660099",
        fill_opacity=1.0,
        stroke_color="#33004d",
        stroke_width=0.35,
        keywords=["SOSYAL_TESIS", "SOSYAL", "HIZMET_BINASI", "SOCIAL"],
    ),
    PlanStyleRule(
        category_id="MUNICIPAL_SERVICE",
        display_name="Belediye Hizmet Alanı (BHA)",
        fill_color="#993366",
        fill_opacity=1.0,
        stroke_color="#4d1933",
        stroke_width=0.35,
        keywords=["BHA", "BELEDIYE_HIZMET", "HIZMET_ALANI", "MUNICIPAL"],
    ),

    # --- INDUSTRIAL & LOGISTICS / SANAYİ VE LOJİSTİK ---
    PlanStyleRule(
        category_id="INDUSTRIAL_GENERAL",
        display_name="Sanayi Alanı / Fabrika",
        fill_color="#FF00FF",
        fill_opacity=1.0,
        stroke_color="#800080",
        stroke_width=0.35,
        keywords=["SANAYI", "SAN", "FABRIKA", "INDUSTRIAL", "SANAYI_ALANI"],
    ),
    PlanStyleRule(
        category_id="ORGANIZED_INDUSTRIAL",
        display_name="Organize Sanayi Bölgesi (OSB)",
        fill_color="#C000C0",
        fill_opacity=1.0,
        stroke_color="#600060",
        stroke_width=0.4,
        keywords=["OSB", "ORGANIZE_SANAYI", "ORGANIZED_INDUSTRIAL"],
    ),
    PlanStyleRule(
        category_id="SMALL_INDUSTRIAL",
        display_name="Küçük Sanayi Sitesi (KSS)",
        fill_color="#FF99FF",
        fill_opacity=1.0,
        stroke_color="#800080",
        stroke_width=0.3,
        keywords=["KSS", "KUCUK_SANAYI", "ATOLYE", "SMALL_INDUSTRIAL"],
    ),
    PlanStyleRule(
        category_id="LOGISTICS_STORAGE",
        display_name="Lojistik ve Depolama Alanı",
        fill_color="#CC6699",
        fill_opacity=1.0,
        stroke_color="#66334d",
        stroke_width=0.35,
        keywords=["LOJISTIK", "DEPOLAMA", "ANTREPO", "LOGISTICS", "STORAGE"],
    ),

    # --- TRANSPORTATION & UTILITIES / ULAŞIM VE ALTYAPI ---
    PlanStyleRule(
        category_id="ROAD_TRANSPORTATION",
        display_name="Yol / Ulaşım Güzergahı",
        fill_color="#FFFFFF",
        fill_opacity=1.0,
        stroke_color="#333333",
        stroke_width=0.5,
        keywords=["YOL", "SOKAK", "BULVAR", "CADDE", "YOLORTA", "ROAD", "STREET", "HIGHWAY", "OTOBAN"],
    ),
    PlanStyleRule(
        category_id="PARKING",
        display_name="Otopark / Otopark Alanı",
        fill_color="#808080",
        fill_opacity=1.0,
        stroke_color="#404040",
        stroke_width=0.3,
        keywords=["OTOPARK", "OPK", "PARKING", "OTO_PARK"],
    ),
    PlanStyleRule(
        category_id="TECHNICAL_INFRASTRUCTURE",
        display_name="Teknik Altyapı Tesis Alanı (Trafo/Su Deposu)",
        fill_color="#FF9900",
        fill_opacity=1.0,
        stroke_color="#804d00",
        stroke_width=0.35,
        hatch_pattern="cross",
        hatch_color="#804d00",
        hatch_distance=3.0,
        hatch_angle=45.0,
        keywords=["TEKNIK_ALTYAPI", "ALTYAPI", "TRAFO", "POMPA", "SU_DEPOSU", "ARITMA", "INFRASTRUCTURE"],
    ),

    # --- PROTECTION & SPECIAL ZONES / KORUMA VE ÖZEL ALANLAR ---
    PlanStyleRule(
        category_id="PROTECTION_ZONE",
        display_name="Koruma Alanı / Sit Bölgesi",
        fill_color="#FFCC00",
        fill_opacity=0.60,
        stroke_color="#997a00",
        stroke_width=0.45,
        stroke_style="dashdot",
        hatch_pattern="diagonal",
        hatch_color="#997a00",
        hatch_distance=3.0,
        hatch_angle=135.0,
        keywords=["KORUMA", "SIT", "DOGAL_SIT", "ARKEOLOJIK", "PROTECTED"],
    ),
    PlanStyleRule(
        category_id="RISK_HAZARD_ZONE",
        display_name="Afet / Taşkın Risk Alanı",
        fill_color="#FF3300",
        fill_opacity=0.60,
        stroke_color="#991f00",
        stroke_width=0.5,
        stroke_style="dash",
        hatch_pattern="diagonal",
        hatch_color="#FF3300",
        hatch_distance=2.5,
        hatch_angle=45.0,
        keywords=["AFET", "TASKIN", "HEYELAN", "RISK_BOLGESI", "HAZARD", "FLOOD"],
    ),
    PlanStyleRule(
        category_id="AGRICULTURAL",
        display_name="Tarım Alanı / Mutlak Tarım",
        fill_color="#CCFF66",
        fill_opacity=1.0,
        stroke_color="#669900",
        stroke_width=0.3,
        hatch_pattern="horizontal",
        hatch_color="#669900",
        hatch_distance=3.5,
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
        # Strip common scale numbers and prefixes e.g. 1000_UIP_, 5000_NIP_
        s = re.sub(r"^(\d+[\._-]*)?(UIP_|NIP_|CDP_|MUIP_|MNIP_|KDP_|PL_|PLAN_|NCZ_LAYER_|LAYER_)", "", s, flags=re.IGNORECASE)
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
        scale: str = "1000",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> PlanStyleRule:
        """Find the best matching PlanStyleRule using the PASE catalog."""
        norm_name = cls.normalize_string(layer_name)

        if norm_name:
            for rule in PLAN_SYMBOLOGY_CATALOG:
                for kw in rule.keywords:
                    norm_kw = cls.normalize_string(kw)
                    if norm_kw and (norm_kw == norm_name or norm_kw in norm_name or norm_name in norm_kw):
                        return rule

        if attributes:
            attr_keys = ["FONKSIYON", "LEJANT", "KULLANIM", "TYPE", "CATEGORY", "PLAN_KODU", "KOD", "DETAY", "LAYER"]
            for k, v in attributes.items():
                if any(ak in k.upper() for ak in attr_keys) and isinstance(v, str):
                    norm_val = cls.normalize_string(v)
                    if not norm_val:
                        continue
                    for rule in PLAN_SYMBOLOGY_CATALOG:
                        for kw in rule.keywords:
                            norm_kw = cls.normalize_string(kw)
                            if norm_kw and (norm_kw == norm_val or norm_kw in norm_val):
                                return rule

        # Fallback default rule if no match
        return PlanStyleRule(
            category_id="DEFAULT_PLAN",
            display_name=layer_name or "Plan Katmanı",
            fill_color="#E0E0E0" if "YOL" not in norm_name else "#FFFFFF",
            fill_opacity=0.5,
            stroke_color="#333333",
            stroke_width=0.35,
            keywords=[],
        )


def create_qgis_fill_symbol(rule: PlanStyleRule) -> Any:
    """Build a rich multi-layer QgsFillSymbol with vector hatch patterns and outlines."""
    from qgis.core import (  # type: ignore
        QgsFillSymbol,
        QgsSimpleFillSymbolLayer,
        QgsLinePatternFillSymbolLayer,
    )
    from qgis.PyQt.QtCore import Qt  # type: ignore
    from qgis.PyQt.QtGui import QColor  # type: ignore

    symbol = QgsFillSymbol()
    while symbol.symbolLayerCount() > 0:
        symbol.takeSymbolLayer(0)

    fill_qcolor = QColor(rule.fill_color)
    fill_qcolor.setAlphaF(rule.fill_opacity)
    stroke_qcolor = QColor(rule.stroke_color)

    # 1. Base background fill layer
    if rule.fill_opacity > 0:
        bg_layer = QgsSimpleFillSymbolLayer()
        bg_layer.setColor(fill_qcolor)
        bg_layer.setStrokeStyle(Qt.NoPen if rule.hatch_pattern else Qt.SolidLine)
        bg_layer.setStrokeColor(stroke_qcolor)
        bg_layer.setStrokeWidth(rule.stroke_width)
        symbol.appendSymbolLayer(bg_layer)

    # 2. Vector Hatch / Tarama pattern layer if specified
    if rule.hatch_pattern:
        hatch_color = QColor(rule.hatch_color or rule.stroke_color)
        hatch_layer = QgsLinePatternFillSymbolLayer()
        hatch_layer.setColor(hatch_color)
        hatch_layer.setLineAngle(rule.hatch_angle)
        hatch_layer.setDistance(rule.hatch_distance)
        hatch_layer.setLineWidth(max(rule.stroke_width, 0.3))

        symbol.appendSymbolLayer(hatch_layer)

        if rule.hatch_pattern == "cross":
            hatch_layer2 = QgsLinePatternFillSymbolLayer()
            hatch_layer2.setColor(hatch_color)
            hatch_layer2.setLineAngle((rule.hatch_angle + 90.0) % 360.0)
            hatch_layer2.setDistance(rule.hatch_distance)
            hatch_layer2.setLineWidth(max(rule.stroke_width, 0.3))
            symbol.appendSymbolLayer(hatch_layer2)

    # 3. Clean boundary outline layer
    if rule.stroke_width > 0:
        outline_layer = QgsSimpleFillSymbolLayer()
        outline_layer.setBrushStyle(Qt.NoBrush)
        outline_layer.setStrokeColor(stroke_qcolor)
        outline_layer.setStrokeWidth(rule.stroke_width)

        if rule.stroke_style == "dash":
            outline_layer.setStrokeStyle(Qt.DashLine)
        elif rule.stroke_style == "dashdot":
            outline_layer.setStrokeStyle(Qt.DashDotLine)
        elif rule.stroke_style == "dot":
            outline_layer.setStrokeStyle(Qt.DotLine)
        else:
            outline_layer.setStrokeStyle(Qt.SolidLine)

        symbol.appendSymbolLayer(outline_layer)

    return symbol


def create_qgis_line_symbol(rule: PlanStyleRule) -> Any:
    """Build a QgsLineSymbol with line width and stroke style."""
    from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer  # type: ignore
    from qgis.PyQt.QtCore import Qt  # type: ignore
    from qgis.PyQt.QtGui import QColor  # type: ignore

    symbol = QgsLineSymbol()
    while symbol.symbolLayerCount() > 0:
        symbol.takeSymbolLayer(0)

    line_layer = QgsSimpleLineSymbolLayer()
    line_color = rule.stroke_color if rule.stroke_color != "#333333" else rule.fill_color
    if line_color == "#E0E0E0":
        line_color = "#222222"
    line_layer.setColor(QColor(line_color))
    line_layer.setWidth(max(rule.stroke_width * 1.5, 0.5))

    if rule.stroke_style == "dash":
        line_layer.setPenStyle(Qt.DashLine)
    elif rule.stroke_style == "dashdot":
        line_layer.setPenStyle(Qt.DashDotLine)
    elif rule.stroke_style == "dot":
        line_layer.setPenStyle(Qt.DotLine)
    else:
        line_layer.setPenStyle(Qt.SolidLine)

    symbol.appendSymbolLayer(line_layer)
    return symbol


def create_qgis_marker_symbol(rule: PlanStyleRule) -> Any:
    """Build a QgsMarkerSymbol for point features."""
    from qgis.core import QgsMarkerSymbol, QgsSimpleMarkerSymbolLayer  # type: ignore
    from qgis.PyQt.QtGui import QColor  # type: ignore

    symbol = QgsMarkerSymbol()
    while symbol.symbolLayerCount() > 0:
        symbol.takeSymbolLayer(0)

    marker_layer = QgsSimpleMarkerSymbolLayer()
    marker_layer.setColor(QColor(rule.fill_color if rule.fill_color != "#E0E0E0" else "#333333"))
    marker_layer.setStrokeColor(QColor(rule.stroke_color))
    marker_layer.setStrokeWidth(0.3)
    marker_layer.setSize(3.0)

    if rule.marker_shape == "square":
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Square)
    elif rule.marker_shape == "triangle":
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
    elif rule.marker_shape == "cross":
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Cross)
    else:
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)

    symbol.appendSymbolLayer(marker_layer)
    return symbol


def apply_plan_symbology(
    qgis_layer: Any,
    plan_scale: str = "1/1000",
    override_rule: Optional[PlanStyleRule] = None,
) -> bool:
    """Apply native QGIS style (fill color, hatch pattern, stroke width, labeling) to a QgsVectorLayer.

    Safely handles headless/testing environments where qgis.core might not be loaded.
    Returns True if styling was successfully applied, False otherwise.
    """
    rule = override_rule
    if rule is None and hasattr(qgis_layer, "name"):
        rule = PlanSymbologyMatcher.match_rule(qgis_layer.name(), scale=plan_scale)

    try:
        from qgis.core import (  # type: ignore
            QgsSingleSymbolRenderer,
            QgsCategorizedSymbolRenderer,
            QgsRendererCategory,
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

    # Helper builder for a rule & geom type
    def build_symbol(r: PlanStyleRule):
        if geom_type == 2:
            return create_qgis_fill_symbol(r)
        elif geom_type == 1:
            return create_qgis_line_symbol(r)
        elif geom_type == 0:
            return create_qgis_marker_symbol(r)
        return None

    # Check if layer has a land-use attribute field to categorize multiple functions inside 1 layer
    category_field = None
    if hasattr(qgis_layer, "fields"):
        fields = [f.name() for f in qgis_layer.fields()]
        for candidate in ["FONKSIYON", "LEJANT", "KULLANIM", "TYPE", "DETAY", "LAYER", "PLAN_KODU"]:
            if candidate in fields or candidate.lower() in [f.lower() for f in fields]:
                # Found a potential category field! Check if layer has unique values
                for f in qgis_layer.fields():
                    if f.name().upper() == candidate.upper():
                        category_field = f.name()
                        break
                break

    if category_field and hasattr(qgis_layer, "uniqueValues"):
        unique_vals = qgis_layer.uniqueValues(qgis_layer.fields().indexOf(category_field))
        if len(unique_vals) > 1 and len(unique_vals) <= 100:
            categories = []
            for val in unique_vals:
                val_str = str(val) if val is not None else ""
                matched_rule = PlanSymbologyMatcher.match_rule(qgis_layer.name(), scale=plan_scale, attributes={category_field: val_str}) or rule
                sym = build_symbol(matched_rule)
                if sym:
                    categories.append(QgsRendererCategory(val, sym, matched_rule.display_name))
            if categories:
                renderer = QgsCategorizedSymbolRenderer(category_field, categories)
                qgis_layer.setRenderer(renderer)
            else:
                sym = build_symbol(rule)
                if sym:
                    qgis_layer.setRenderer(QgsSingleSymbolRenderer(sym))
        else:
            sym = build_symbol(rule)
            if sym:
                qgis_layer.setRenderer(QgsSingleSymbolRenderer(sym))
    else:
        sym = build_symbol(rule)
        if sym:
            qgis_layer.setRenderer(QgsSingleSymbolRenderer(sym))

    # Comprehensive candidate search for Text Annotations / Labeling
    field_names = [f.name() for f in qgis_layer.fields()] if hasattr(qgis_layer, "fields") else []
    field_names_lower = [f.lower() for f in field_names]

    label_candidates = [
        "label_text", "text", "string", "name", "yazi", "metin", "label", "text_string",
        "kat_adedi", "emsal", "lejant", "fonksiyon", "val", "value", "yazi_metni", "baslik"
    ]
    label_field = None
    for candidate in label_candidates:
        if candidate in field_names_lower:
            idx = field_names_lower.index(candidate)
            label_field = field_names[idx]
            break

    if label_field:
        layer_settings = QgsPalLayerSettings()
        layer_settings.fieldName = label_field
        text_format = QgsTextFormat()
        text_format.setSize(9.0)
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1.2)
        buffer_settings.setColor(QColor("#FFFFFF"))
        text_format.setBuffer(buffer_settings)
        layer_settings.setFormat(text_format)
        qgis_layer.setLabeling(QgsVectorLayerSimpleLabeling(layer_settings))
        qgis_layer.setLabelsEnabled(True)

    qgis_layer.triggerRepaint()
    return True
