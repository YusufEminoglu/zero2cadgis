# -*- coding: utf-8 -*-
"""symbology — PlanX Adaptive Symbology Engine (PASE) for 02CadGis.

Provides automatic zoning legend and symbology matching for imported CAD & GIS plan
layers (NCZ, DXF, GML, KML, GeoJSON, FileGDB) based on Turkish Spatial Planning
Regulations (Mekânsal Planlar Yapım Yönetmeliği e-Plan standards: 1/1000 UİP, 1/5000 NİP).

Supports PlanGML official attribute schema and code hierarchy:
  - UST_GRUP_ID, UST_GRUP_ADI
  - ALT_GRUP_ID, ALT_GRUP_ADI
  - DETAY_GRUP_ID, PLAN_KODU, FONKSIYON_KODU, LEJANT_KODU, KOD
  - TAM_ADI, GISTERIM, GUSTERIM_ADI, LEJANT, FONKSIYON, KULLANIM
  - Native CAD layer_name & uip_tabaka attributes

100% clean, independent implementation authored by Yusuf Eminoğlu with zero external plagiarism.
Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import os
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
    keywords: List[str]                     # Matching keywords, codes or tokens in layer names or attributes
    ust_grup_adi: str = "AÇIK VE YEŞİL ALANLAR"   # PlanGML Upper Group Name
    alt_grup_adi: str = "Park ve Çocuk Bahçesi"   # PlanGML Sub Group Name
    stroke_style: str = "solid"             # solid, dash, dot, dashdot
    hatch_pattern: Optional[str] = None     # None, diagonal, cross, horizontal, vertical
    hatch_color: Optional[str] = None       # Hex string for hatch lines
    hatch_distance: float = 3.0             # Line pattern spacing in mm
    hatch_angle: float = 45.0               # Line pattern angle in degrees
    marker_shape: str = "circle"            # circle, square, triangle, cross
    dash_pattern: Optional[List[float]] = None   # Custom dash vector (mm) from official SLD
    tarama_path: Optional[str] = None       # Official tarama (hatch tile) image path
    tarama_size: Optional[Tuple[int, int]] = None  # Tile pixel size (w, h)
    official: bool = False                  # True when sourced from the e-Plan SLD catalog
    plan_type: str = ""                     # UIP / NIP / CDP when official


# -----------------------------------------------------------------------------
# Official Turkish Spatial Planning Symbology Catalog (PASE Catalog)
# Incorporates Official PlanGML Upper/Sub-Group Hierarchy Codes (100 - 700)
# -----------------------------------------------------------------------------
PLAN_SYMBOLOGY_CATALOG: List[PlanStyleRule] = [
    # --- 700: PLAN BOUNDARIES & CADASTRAL LINES ---
    PlanStyleRule(
        category_id="PLAN_BOUNDARY",
        display_name="Plan Sınırı / Ada Kenarı / Onama Sınırı",
        fill_color="#000000",
        fill_opacity=0.0,
        stroke_color="#000000",
        stroke_width=0.8,
        stroke_style="dashdot",
        keywords=["700", "701", "ADA_KENARI", "ADAKENARI", "PLAN_SINIRI", "SNR_PLANONAMA", "PLANONAMA", "ONAMA_SINIRI", "SINIR", "KENAR", "PARSEL_KENARI", "CADASTRE", "BOUNDARY"],
        ust_grup_adi="PLAN SINIRLARI VE KADASTRAL HATLAR",
        alt_grup_adi="Plan Sınırı ve Ada Kenarı",
    ),
    PlanStyleRule(
        category_id="SETBACK_LINE",
        display_name="Yapı Yaklaşma Sınırı / Çekme Mesafesi",
        fill_color="#FF0000",
        fill_opacity=0.0,
        stroke_color="#FF0000",
        stroke_width=0.5,
        stroke_style="dash",
        keywords=["SNR_YAPIYAK", "YAPIYAK", "YAPI_YAKLASMA", "CEKME_MESAFESI", "SETBACK"],
        ust_grup_adi="PLAN SINIRLARI VE KADASTRAL HATLAR",
        alt_grup_adi="Yapı Yaklaşma Sınırı",
    ),
    PlanStyleRule(
        category_id="FUNCTION_BOUNDARY",
        display_name="Fonksiyon Ayrım Çizgisi",
        fill_color="#333333",
        fill_opacity=0.0,
        stroke_color="#333333",
        stroke_width=0.4,
        stroke_style="dot",
        keywords=["SNR_FONKSIYON", "FONKSIYON_SINIRI"],
        ust_grup_adi="PLAN SINIRLARI VE KADASTRAL HATLAR",
        alt_grup_adi="Fonksiyon Ayrım Çizgisi",
    ),
    PlanStyleRule(
        category_id="SIDEWALK",
        display_name="Kaldırım / Yaya Yolu",
        fill_color="#FF0000",
        fill_opacity=0.0,
        stroke_color="#FF0000",
        stroke_width=0.4,
        stroke_style="solid",
        keywords=["503", "KALDIRIM", "YAYA_YOLU", "YAYA", "SIDEWALK", "PAVEMENT"],
        ust_grup_adi="ULAŞIM VE ALTYAPI GÜZERGAHLARI",
        alt_grup_adi="Kaldırım ve Yaya Yolu",
    ),
    PlanStyleRule(
        category_id="REFUGE",
        display_name="Refüj / Orta Refüj",
        fill_color="#008000",
        fill_opacity=0.0,
        stroke_color="#008000",
        stroke_width=0.4,
        stroke_style="solid",
        keywords=["504", "REFUJ", "REFÜJ", "ORTA_REFUJ", "MEDIAN"],
        ust_grup_adi="ULAŞIM VE ALTYAPI GÜZERGAHLARI",
        alt_grup_adi="Refüj ve Orta Refüj",
    ),

    # --- 100: RESIDENTIAL / KONUT ALANLARI ---
    PlanStyleRule(
        category_id="RESIDENTIAL_GENERAL",
        display_name="Konut Alanı (Mesken)",
        fill_color="#FFFF00",
        fill_opacity=1.0,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["100", "PL_KONUT", "KONUT", "KNT", "MESKEN", "KONUT_ALANI", "KDKCA", "PL_KDKCA", "RESIDENTIAL", "AK_KONUT"],
        ust_grup_adi="KONUT ALANLARI",
        alt_grup_adi="Konut Alanı (Mesken)",
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_LOW",
        display_name="Düşük Yoğunluklu Konut Alanı",
        fill_color="#FFFFB2",
        fill_opacity=1.0,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["101", "KONUT_DUSUK", "DUSUK_YOGUNLUK", "DUSUK_YOGUNLIKLI", "RESIDENTIAL_LOW"],
        ust_grup_adi="KONUT ALANLARI",
        alt_grup_adi="Düşük Yoğunluklu Konut Alanı",
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_MEDIUM",
        display_name="Orta Yoğunluklu Konut Alanı",
        fill_color="#FFFF00",
        fill_opacity=1.0,
        stroke_color="#666600",
        stroke_width=0.3,
        keywords=["102", "KONUT_ORTA", "ORTA_YOGUNLUK", "ORTA_YOGUNLIKLI", "RESIDENTIAL_MED"],
        ust_grup_adi="KONUT ALANLARI",
        alt_grup_adi="Orta Yoğunluklu Konut Alanı",
    ),
    PlanStyleRule(
        category_id="RESIDENTIAL_HIGH",
        display_name="Yüksek Yoğunluklu Konut Alanı",
        fill_color="#FFD700",
        fill_opacity=1.0,
        stroke_color="#665200",
        stroke_width=0.35,
        keywords=["103", "KONUT_YUKSEK", "YUKSEK_YOGUNLUK", "YUKSEK_YOGUNLIKLI", "RESIDENTIAL_HIGH"],
        ust_grup_adi="KONUT ALANLARI",
        alt_grup_adi="Yüksek Yoğunluklu Konut Alanı",
    ),
    PlanStyleRule(
        category_id="COMMERCIAL_RESIDENTIAL",
        display_name="Ticaret + Konut Karma Alanı (TİB)",
        fill_color="#FFA500",
        fill_opacity=1.0,
        stroke_color="#995200",
        stroke_width=0.35,
        keywords=["105", "PL_KONUT_TICARET", "TIB", "TICARET_KONUT", "KONUT_TICARET", "KARMA", "MIXED_USE"],
        ust_grup_adi="KONUT ALANLARI",
        alt_grup_adi="Ticaret + Konut Karma Alanı (TİB)",
    ),

    # --- 200: COMMERCIAL / TİCARET VE ÇALIŞMA ALANLARI ---
    PlanStyleRule(
        category_id="COMMERCIAL_GENERAL",
        display_name="Ticaret Alanı / İş Merkezi",
        fill_color="#FF0000",
        fill_opacity=1.0,
        stroke_color="#800000",
        stroke_width=0.35,
        keywords=["200", "201", "PL_TICARET", "TICARET", "TCR", "IS_MERKEZI", "COMMERCIAL", "TICARI", "CARSI", "SHOPPING"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Ticaret Alanı / İş Merkezi",
    ),
    PlanStyleRule(
        category_id="MARKET_AREA",
        display_name="Pazar Alanı / Pazar Yeri",
        fill_color="#FF9966",
        fill_opacity=1.0,
        stroke_color="#804d00",
        stroke_width=0.35,
        keywords=["PAZAR", "PAZAR_ALANI", "PL_PAZAR_ALANI", "MARKET"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Pazar Alanı",
    ),
    PlanStyleRule(
        category_id="WHOLESALE_HAL",
        display_name="Toptancı Hal Alanı",
        fill_color="#FF6666",
        fill_opacity=1.0,
        stroke_color="#800000",
        stroke_width=0.35,
        keywords=["PL_HAL", "HAL", "TOPTANCI_HAL"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Toptancı Hal Alanı",
    ),
    PlanStyleRule(
        category_id="TOURISM",
        display_name="Turizm Tesis Alanı / Otel",
        fill_color="#CC9900",
        fill_opacity=1.0,
        stroke_color="#664d00",
        stroke_width=0.35,
        keywords=["TURIZM", "PL_TURIZM", "OTEL", "TOURISM"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Turizm Tesis Alanı",
    ),
    PlanStyleRule(
        category_id="CENTRAL_BUSINESS",
        display_name="Merkezi İş Alanı (MİA)",
        fill_color="#CC0000",
        fill_opacity=1.0,
        stroke_color="#660000",
        stroke_width=0.4,
        keywords=["202", "MIA", "MERKEZI_IS", "CBD", "MERKEZ"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Merkezi İş Alanı (MİA)",
    ),
    PlanStyleRule(
        category_id="COMMERCIAL_STORAGE",
        display_name="Toplu Ticaret / Depolama Alanı",
        fill_color="#FF6666",
        fill_opacity=1.0,
        stroke_color="#800000",
        stroke_width=0.3,
        keywords=["203", "TOPLU_TICARET", "TICARI_DEPO", "KUP", "WHOLESALE"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Toplu Ticaret ve Depolama Alanı",
    ),
    PlanStyleRule(
        category_id="INDUSTRIAL_GENERAL",
        display_name="Sanayi Alanı / Fabrika / KSS",
        fill_color="#FF00FF",
        fill_opacity=1.0,
        stroke_color="#800080",
        stroke_width=0.35,
        keywords=["204", "206", "PL_KUCUK_SANAYI", "KUCUK_SANAYI", "KSS", "SANAYI", "SAN", "FABRIKA", "INDUSTRIAL", "SANAYI_ALANI"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Sanayi ve Küçük Sanayi Sitesi (KSS)",
    ),
    PlanStyleRule(
        category_id="ORGANIZED_INDUSTRIAL",
        display_name="Organize Sanayi Bölgesi (OSB)",
        fill_color="#C000C0",
        fill_opacity=1.0,
        stroke_color="#600060",
        stroke_width=0.4,
        keywords=["205", "OSB", "ORGANIZE_SANAYI", "ORGANIZED_INDUSTRIAL"],
        ust_grup_adi="TİCARET VE ÇALIŞMA ALANLARI",
        alt_grup_adi="Organize Sanayi Bölgesi (OSB)",
    ),

    # --- 300: PARKS & GREEN SPACES / AÇIK VE YEŞİL ALANLAR ---
    PlanStyleRule(
        category_id="PARK_PLAYGROUND",
        display_name="Park ve Çocuk Bahçesi",
        fill_color="#00FF00",
        fill_opacity=1.0,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["300", "301", "PL_PARK", "PARK", "PL_COCUK_BAHCESI", "COCUK_BAHCESI", "PL_OYUN_ALANI", "OYUN_ALANI", "PLAYGROUND"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Park ve Çocuk Bahçesi",
    ),
    PlanStyleRule(
        category_id="ACTIVE_GREEN",
        display_name="Açık ve Yeşil Alan",
        fill_color="#33CC33",
        fill_opacity=1.0,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["302", "ACIK_YESIL", "YESIL_ALAN", "YESIL", "GREEN_SPACE", "GREEN"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Açık ve Yeşil Alan",
    ),
    PlanStyleRule(
        category_id="SPORTS_AREA",
        display_name="Spor Alanı / Spor Tesisleri",
        fill_color="#00FF99",
        fill_opacity=1.0,
        stroke_color="#006633",
        stroke_width=0.3,
        marker_shape="square",
        keywords=["303", "SPOR", "PL_SPOR_TESISLERI", "SPOR_TESISLERI", "SPOR_ALANI", "SPORTS", "STADYUM", "SAHA"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Spor ve Oyun Alanı",
    ),
    PlanStyleRule(
        category_id="RECREATION",
        display_name="Rekreasyon ve Piknik Alanı",
        fill_color="#99FF99",
        fill_opacity=1.0,
        stroke_color="#006600",
        stroke_width=0.3,
        keywords=["304", "REKREASYON", "PIKNIK", "MESIRE", "RECREATION"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Rekreasyon ve Piknik Alanı",
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
        keywords=["305", "ORMAN", "PL_AGACLANDIRILACAK", "AGACLANDIRILACAK", "CORULUK", "FOREST"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Orman ve Ağaçlandırılacak Alan",
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
        keywords=["306", "MEZARLIK", "MEZAR", "CEMETERY"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Mezarlık Alanı",
    ),
    PlanStyleRule(
        category_id="WATERBODY_STREAM",
        display_name="Dere / Su Yüzeyi / Akarsu",
        fill_color="#99CCFF",
        fill_opacity=1.0,
        stroke_color="#3399FF",
        stroke_width=0.35,
        keywords=["PL_DERE", "DERE", "SU_YUZEYI", "AKARSU", "GOL", "WATER"],
        ust_grup_adi="AÇIK VE YEŞİL ALANLAR",
        alt_grup_adi="Dere ve Su Yüzeyi",
    ),

    # --- 400: PUBLIC FACILITIES & UTILITIES / SOSYAL VE TEKNİK ALTYAPI ---
    PlanStyleRule(
        category_id="EDUCATION",
        display_name="Eğitim Tesis Alanı (Okul/Lise/Üniversite)",
        fill_color="#0000FF",
        fill_opacity=1.0,
        stroke_color="#000080",
        stroke_width=0.35,
        marker_shape="square",
        keywords=["400", "401", "PL_ILKOKUL_ALANI", "PL_ORTAOKUL_ALANI", "PL_LISE_ALANI", "PL_YATILI_BOLGE_OKUL", "PL_SOSYOKULTUREL", "PL_TEKNIK_OGRETIM", "EGITIM", "EGTM", "OKUL", "OKL", "ILKOKUL", "ORTAOKUL", "LISE", "UNIVERSITE", "KRES", "ANAOKULU", "EDUCATION"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Eğitim Tesis Alanı",
    ),
    PlanStyleRule(
        category_id="HEALTH",
        display_name="Sağlık Tesis Alanı (Hastane/Sağlık Ocağı)",
        fill_color="#00FFFF",
        fill_opacity=1.0,
        stroke_color="#008080",
        stroke_width=0.35,
        marker_shape="cross",
        keywords=["402", "PL_HASTANE", "PL_SAGLIK_OCAGI", "SAGLIK", "SGL", "HASTANE", "SAGLIK_OCAGI", "DISPANSER", "HEALTH", "HOSPITAL"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Sağlık Tesis Alanı",
    ),
    PlanStyleRule(
        category_id="CULTURAL",
        display_name="Kültürel Tesis Alanı",
        fill_color="#9900CC",
        fill_opacity=1.0,
        stroke_color="#4d0066",
        stroke_width=0.35,
        keywords=["403", "KULTUR", "KULTUREL", "SOSYOKULTUREL", "KUTUPHANE", "MUZE", "TIYATRO", "CULTURE"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Kültürel Tesis Alanı",
    ),
    PlanStyleRule(
        category_id="RELIGIOUS",
        display_name="İbadet Alanı (Cami/Dini Tesis)",
        fill_color="#996633",
        fill_opacity=1.0,
        stroke_color="#4d3319",
        stroke_width=0.35,
        marker_shape="triangle",
        keywords=["404", "PL_CAMI", "IBADET", "CAMI", "DINI_TESIS", "MESCIT", "RELIGIOUS", "MOSQUE"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="İbadet Alanı",
    ),
    PlanStyleRule(
        category_id="ADMINISTRATIVE_OFFICIAL",
        display_name="Resmi Kurum / İdari Tesis Alanı",
        fill_color="#800080",
        fill_opacity=1.0,
        stroke_color="#400040",
        stroke_width=0.35,
        keywords=["405", "PL_RESMI_KURUM", "PL_BELEDIYE", "RESMI_KURUM", "BELEDIYE", "IDARI", "GOVERNMENT", "OFFICIAL"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Resmi Kurum / İdari Tesis Alanı",
    ),
    PlanStyleRule(
        category_id="SOCIAL_FACILITY",
        display_name="Sosyal Tesis Alanı",
        fill_color="#660099",
        fill_opacity=1.0,
        stroke_color="#33004d",
        stroke_width=0.35,
        keywords=["406", "SOSYAL_TESIS", "SOSYAL", "HIZMET_BINASI", "SOCIAL"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Sosyal Tesis Alanı",
    ),
    PlanStyleRule(
        category_id="MUNICIPAL_SERVICE",
        display_name="Belediye Hizmet Alanı (BHA)",
        fill_color="#993366",
        fill_opacity=1.0,
        stroke_color="#4d1933",
        stroke_width=0.35,
        keywords=["407", "PL_BHA", "BHA", "BELEDIYE_HIZMET", "HIZMET_ALANI", "MUNICIPAL"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Belediye Hizmet Alanı (BHA)",
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
        keywords=["408", "TEKNIK_ALTYAPI", "ALTYAPI", "TRAFO", "POMPA", "SU_DEPOSU", "ARITMA", "INFRASTRUCTURE"],
        ust_grup_adi="SOSYAL VE TEKNİK ALTYAPI ALANLARI",
        alt_grup_adi="Teknik Altyapı Tesis Alanı",
    ),

    # --- 500: TRANSPORTATION & UTILITIES / ULAŞIM VE ALTYAPI ---
    PlanStyleRule(
        category_id="ROAD_TRANSPORTATION",
        display_name="Yol / Ulaşım Güzergahı",
        fill_color="#FFFFFF",
        fill_opacity=1.0,
        stroke_color="#333333",
        stroke_width=0.5,
        keywords=["500", "501", "YOL", "SOKAK", "BULVAR", "CADDE", "YOLORTA", "ROAD", "STREET", "HIGHWAY", "OTOBAN"],
        ust_grup_adi="ULAŞIM VE ALTYAPI GÜZERGAHLARI",
        alt_grup_adi="Yol ve Ulaşım Güzergahı",
    ),
    PlanStyleRule(
        category_id="PARKING",
        display_name="Otopark / Otopark Alanı",
        fill_color="#808080",
        fill_opacity=1.0,
        stroke_color="#404040",
        stroke_width=0.3,
        keywords=["502", "OTOPARK", "OPK", "PARKING", "OTO_PARK"],
        ust_grup_adi="ULAŞIM VE ALTYAPI GÜZERGAHLARI",
        alt_grup_adi="Otopark Alanı",
    ),

    # --- 600: PROTECTION & SPECIAL ZONES / KORUMA VE ÖZEL ALANLAR ---
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
        keywords=["600", "601", "KORUMA", "SIT", "DOGAL_SIT", "ARKEOLOJIK", "PROTECTED"],
        ust_grup_adi="KORUMA VE ÖZEL ALANLAR",
        alt_grup_adi="Sit ve Koruma Bölgesi",
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
        keywords=["602", "AFET", "TASKIN", "HEYELAN", "RISK_BOLGESI", "HAZARD", "FLOOD"],
        ust_grup_adi="KORUMA VE ÖZEL ALANLAR",
        alt_grup_adi="Afet ve Risk Bölgesi",
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
        keywords=["603", "TARIM", "MUTLAK_TARIM", "SERA", "AGRICULTURAL"],
        ust_grup_adi="KORUMA VE ÖZEL ALANLAR",
        alt_grup_adi="Tarım Alanı",
    ),
]


# -----------------------------------------------------------------------------
# Official e-Plan symbology engine
#
# ``eplan_catalog.py`` is generated offline from the public Ministry e-Plan
# GeoServer SLD style set (tools/compile_eplan_catalog.py). It resolves CAD
# tabaka tokens to the official plan gösterimleri appearance per plan type:
# UIP (uygulama imar planı 1/1000), NIP (nazım imar planı 1/5000) and
# CDP (çevre düzeni planı 1/25.000+). Tarama pattern tiles are shipped under
# resources/eplan_tarama/.
# -----------------------------------------------------------------------------
from .eplan_catalog import EPLAN_CATALOG, EPLAN_PLAN_TYPES  # noqa: E402

_TARAMA_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "resources", "eplan_tarama"))

# Plan type fallback chain: a token missing for the requested plan type reuses
# the closest official equivalent instead of dropping to the legacy catalog.
_PLAN_TYPE_FALLBACK = {
    "UIP": ("UIP", "NIP", "CDP"),
    "NIP": ("NIP", "UIP", "CDP"),
    "CDP": ("CDP", "NIP", "UIP"),
}

_PLAN_TYPE_WORDS = {
    "UIP": "UIP", "UYGULAMA": "UIP", "MUIP": "UIP",
    "NIP": "NIP", "NAZIM": "NIP", "MNIP": "NIP",
    "CDP": "CDP", "CEVRE": "CDP", "MCDP": "CDP",
}
_PLAN_TYPE_SCALES = {
    "500": "UIP", "1000": "UIP", "2000": "UIP",
    "5000": "NIP", "10000": "NIP",
    "25000": "CDP", "50000": "CDP", "100000": "CDP", "200000": "CDP",
}


def detect_plan_type(name: Optional[str]) -> Optional[str]:
    """Infer the plan type (UIP/NIP/CDP) from a file or layer name.

    Recognizes explicit markers (UIP/NAZIM/ÇEVRE...) and leading scale numbers
    such as ``1000_BAHCESARAY_IMAR`` or ``1/5000 NAZIM PLAN``.
    """
    if not name:
        return None
    upper = str(name).upper()
    tr_map = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})
    upper = upper.translate(tr_map)
    tokens = [t for t in re.split(r"[^A-Z0-9]+", upper) if t]
    for token in tokens:
        if token in _PLAN_TYPE_WORDS:
            return _PLAN_TYPE_WORDS[token]
    for token in tokens:
        if token in _PLAN_TYPE_SCALES:
            return _PLAN_TYPE_SCALES[token]
    return None


def _eplan_match_keys():
    """All catalog tokens sorted for longest-first matching (cached)."""
    cached = getattr(_eplan_match_keys, "_cache", None)
    if cached is None:
        keys = set()
        for entries in EPLAN_CATALOG.values():
            keys.update(entries)
        cached = sorted(
            ((tuple(k.split("_")), k) for k in keys),
            key=lambda item: (-len(item[0]), -len(item[1])))
        _eplan_match_keys._cache = cached
    return cached


def _contains_subsequence(tokens: List[str], key_tokens: Tuple[str, ...]) -> bool:
    n, m = len(tokens), len(key_tokens)
    if m > n:
        return False
    for i in range(n - m + 1):
        if tuple(tokens[i:i + m]) == key_tokens:
            return True
    return False


def _eplan_entry_for(token_key: str, plan_type: str) -> Optional[Dict[str, Any]]:
    for pt in _PLAN_TYPE_FALLBACK.get(plan_type, ("UIP", "NIP", "CDP")):
        entry = EPLAN_CATALOG.get(pt, {}).get(token_key)
        if entry:
            return entry
    return None


def match_official_rule(layer_name: str, plan_type: str = "UIP") -> Optional[PlanStyleRule]:
    """Match a CAD tabaka / layer name against the official e-Plan catalog.

    Returns a fully populated :class:`PlanStyleRule` carrying the official fill
    color or tarama tile, stroke and dash data, or ``None`` when the name maps
    to nothing official (caller falls back to the legacy PASE catalog).
    """
    if not layer_name:
        return None
    if plan_type not in EPLAN_PLAN_TYPES:
        plan_type = detect_plan_type(layer_name) or "UIP"

    norm = PlanSymbologyMatcher.normalize_string(layer_name)
    if not norm:
        return None
    tokens = [t for t in norm.split("_") if t]

    for key_tokens, key in _eplan_match_keys():
        if not _contains_subsequence(tokens, key_tokens):
            continue
        entry = _eplan_entry_for(key, plan_type)
        if entry is None:
            continue
        return _rule_from_entry(key, entry, plan_type)
    return None


def _rule_from_entry(token_key: str, entry: Dict[str, Any], plan_type: str) -> PlanStyleRule:
    tarama_path = None
    tarama_size = None
    if entry.get("tarama"):
        candidate = os.path.join(_TARAMA_DIR, entry["tarama"])
        if os.path.exists(candidate):
            tarama_path = candidate
            size = entry.get("tarama_size")
            tarama_size = (int(size[0]), int(size[1])) if size else None

    fill = entry.get("fill")
    line_color = entry.get("line_color")
    has_area = bool(fill or tarama_path)
    stroke = entry.get("stroke") or line_color or "#000000"
    if has_area:
        stroke_width = float(entry.get("stroke_width", 0.15) or 0.15)
    else:
        stroke_width = float(entry.get("line_width", 0.4) or 0.4)

    dash = entry.get("dash")
    return PlanStyleRule(
        category_id=f"EPLAN_{plan_type}_{token_key}",
        display_name=entry.get("label", token_key),
        fill_color=fill or "#FFFFFF",
        fill_opacity=float(entry.get("fill_opacity", 1.0)) if fill else 0.0,
        stroke_color=stroke,
        stroke_width=stroke_width,
        keywords=[],
        ust_grup_adi=entry.get("ust_grup", "DİĞER PLAN ALANLARI"),
        alt_grup_adi=entry.get("label", token_key),
        stroke_style="solid",
        dash_pattern=[float(d) for d in dash] if dash else None,
        tarama_path=tarama_path,
        tarama_size=tarama_size,
        official=True,
        plan_type=plan_type,
    )


class PlanSymbologyMatcher:
    """Adaptive matcher for identifying planning land-use styles from layer metadata."""

    @staticmethod
    def normalize_string(val: str) -> str:
        """Clean and normalize a layer name or attribute string."""
        if not val:
            return ""
        s = str(val).strip().upper()
        s = re.sub(r"^(\d+[\._-]*)?(UIP_|NIP_|CDP_|MUIP_|MNIP_|KDP_|PL_|PLAN_|NCZ_LAYER_|LAYER_)", "", s, flags=re.IGNORECASE)
        s = re.sub(r"(_POLYGON|_LINESTRING|_LINE|_POINT|_TEXT|_TABLE)$", "", s, flags=re.IGNORECASE)
        tr_map = str.maketrans({
            "Ç": "C", "Ğ": "G", "I": "I", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"
        })
        s = s.translate(tr_map)
        s = re.sub(r"[^A-Z0-9]+", "_", s)
        return s.strip("_")

    @classmethod
    def match_rule(
        cls,
        layer_name: str,
        scale: str = "1000",
        attributes: Optional[Dict[str, Any]] = None,
        plan_type: Optional[str] = None,
    ) -> PlanStyleRule:
        """Find the best matching PlanStyleRule using official PlanGML codes & keywords.

        The official e-Plan SLD catalog (per plan type UIP/NIP/CDP) has priority;
        the legacy PASE keyword catalog is the fallback for names the Ministry
        style set does not cover.
        """
        official = match_official_rule(
            layer_name, plan_type or detect_plan_type(layer_name) or "UIP")
        if official is not None:
            return official

        if attributes:
            code_fields = ["UST_GRUP_ID", "ALT_GRUP_ID", "DETAY_GRUP_ID", "PLAN_KODU", "FONKSIYON_KODU", "LEJANT_KODU", "KOD"]
            for k, v in attributes.items():
                if any(cf == k.upper() for cf in code_fields) and v is not None:
                    code_str = str(v).strip()
                    if code_str:
                        for rule in PLAN_SYMBOLOGY_CATALOG:
                            if code_str in rule.keywords:
                                return rule

            title_fields = ["TAM_ADI", "GISTERIM", "GUSTERIM_ADI", "LEJANT", "FONKSIYON", "KULLANIM", "layer_name", "layer", "uip_tabaka", "tabaka"]
            for k, v in attributes.items():
                if any(tf == k.upper() for tf in title_fields) and isinstance(v, str):
                    norm_val = cls.normalize_string(v)
                    if norm_val:
                        val_tokens = [t for t in norm_val.split("_") if t]
                        for rule in PLAN_SYMBOLOGY_CATALOG:
                            for kw in rule.keywords:
                                norm_kw = cls.normalize_string(kw)
                                if norm_kw and (norm_kw in val_tokens or norm_kw == norm_val):
                                    return rule

        # 1. Exact Tabaka Name Match First!
        clean_layer = layer_name.strip().upper()
        tr_map = str.maketrans({"Ç": "C", "Ğ": "G", "I": "I", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})
        clean_layer_tr = clean_layer.translate(tr_map)
        for rule in PLAN_SYMBOLOGY_CATALOG:
            for kw in rule.keywords:
                kw_tr = kw.strip().upper().translate(tr_map)
                if kw_tr == clean_layer_tr or kw_tr == f"PL_{clean_layer_tr}" or f"PL_{kw_tr}" == clean_layer_tr:
                    return rule

        norm_name = cls.normalize_string(layer_name)
        if norm_name:
            tokens = [t for t in norm_name.split("_") if t]
            for rule in PLAN_SYMBOLOGY_CATALOG:
                for kw in rule.keywords:
                    norm_kw = cls.normalize_string(kw)
                    if norm_kw:
                        if norm_kw in tokens or norm_kw == norm_name:
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
            ust_grup_adi="DİĞER PLAN ALANLARI",
            alt_grup_adi=layer_name or "Plan Katmanı",
        )


def create_qgis_fill_symbol(rule: PlanStyleRule) -> Any:
    """Build a rich multi-layer QgsFillSymbol with vector hatch patterns and outlines.

    Official e-Plan rules with a tarama tile render the Ministry pattern image
    via a raster fill at its native pixel size; the rest use flat fills plus
    optional vector hatches.
    """
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

    if rule.tarama_path and os.path.exists(rule.tarama_path):
        with suppress(Exception):
            from qgis.core import QgsRasterFillSymbolLayer  # type: ignore
            raster_layer = QgsRasterFillSymbolLayer(rule.tarama_path)
            with suppress(Exception):
                from qgis.core import QgsUnitTypes  # type: ignore
                if rule.tarama_size:
                    raster_layer.setWidth(float(rule.tarama_size[0]))
                    raster_layer.setWidthUnit(QgsUnitTypes.RenderUnit.RenderPixels)
            symbol.appendSymbolLayer(raster_layer)

            outline_layer = QgsSimpleFillSymbolLayer()
            outline_layer.setBrushStyle(Qt.BrushStyle.NoBrush)
            outline_layer.setFillColor(QColor(0, 0, 0, 0))
            outline_layer.setStrokeStyle(Qt.PenStyle.SolidLine)
            outline_layer.setStrokeColor(QColor(rule.stroke_color))
            outline_layer.setStrokeWidth(max(rule.stroke_width, 0.1))
            symbol.appendSymbolLayer(outline_layer)
            return symbol

    fill_qcolor = QColor(rule.fill_color)
    fill_qcolor.setAlphaF(rule.fill_opacity)
    stroke_qcolor = QColor(rule.stroke_color)

    # 1. Base background fill layer with explicit SolidPattern brush & setFillColor
    if rule.fill_opacity > 0:
        bg_layer = QgsSimpleFillSymbolLayer()
        bg_layer.setColor(fill_qcolor)
        bg_layer.setFillColor(fill_qcolor)
        bg_layer.setBrushStyle(Qt.BrushStyle.SolidPattern)
        bg_layer.setStrokeStyle(
            Qt.PenStyle.NoPen if rule.hatch_pattern else Qt.PenStyle.SolidLine)
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
        hatch_layer.setLineWidth(max(rule.stroke_width, 0.35))
        symbol.appendSymbolLayer(hatch_layer)

        if rule.hatch_pattern == "cross":
            hatch_layer2 = QgsLinePatternFillSymbolLayer()
            hatch_layer2.setColor(hatch_color)
            hatch_layer2.setLineAngle((rule.hatch_angle + 90.0) % 360.0)
            hatch_layer2.setDistance(rule.hatch_distance)
            hatch_layer2.setLineWidth(max(rule.stroke_width, 0.35))
            symbol.appendSymbolLayer(hatch_layer2)

    # 3. Clean boundary outline layer
    if rule.stroke_width > 0:
        outline_layer = QgsSimpleFillSymbolLayer()
        outline_layer.setBrushStyle(Qt.BrushStyle.NoBrush)
        outline_layer.setFillColor(QColor(0, 0, 0, 0))
        outline_layer.setStrokeColor(stroke_qcolor)
        outline_layer.setStrokeWidth(rule.stroke_width)

        if rule.stroke_style == "dash":
            outline_layer.setStrokeStyle(Qt.PenStyle.DashLine)
        elif rule.stroke_style == "dashdot":
            outline_layer.setStrokeStyle(Qt.PenStyle.DashDotLine)
        elif rule.stroke_style == "dot":
            outline_layer.setStrokeStyle(Qt.PenStyle.DotLine)
        else:
            outline_layer.setStrokeStyle(Qt.PenStyle.SolidLine)

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
    if rule.official:
        line_layer.setColor(QColor(rule.stroke_color))
        line_layer.setWidth(max(rule.stroke_width, 0.3))
    else:
        line_layer.setWidth(max(rule.stroke_width * 1.5, 0.5))

    if rule.dash_pattern:
        with suppress(Exception):
            line_layer.setCustomDashVector(rule.dash_pattern)
            line_layer.setUseCustomDashPattern(True)
            symbol.appendSymbolLayer(line_layer)
            return symbol

    if rule.stroke_style == "dash":
        line_layer.setPenStyle(Qt.PenStyle.DashLine)
    elif rule.stroke_style == "dashdot":
        line_layer.setPenStyle(Qt.PenStyle.DashDotLine)
    elif rule.stroke_style == "dot":
        line_layer.setPenStyle(Qt.PenStyle.DotLine)
    else:
        line_layer.setPenStyle(Qt.PenStyle.SolidLine)

    symbol.appendSymbolLayer(line_layer)
    return symbol


LABEL_FIELD_CANDIDATES = (
    "label", "label_text", "text", "text_string", "string",
    "yazi", "yazi_metni", "metin", "baslik", "name",
    "kat_adedi", "emsal", "lejant", "fonksiyon", "val", "value",
)


def pick_label_field(qgis_layer: Any) -> Optional[str]:
    """The field that actually carries the drawing's text, or None.

    A field existing is not the same as a field holding anything. A CAD point
    layer declares ``name`` on every feature but only fills ``label`` on the
    text entities, so picking by name alone binds the labels to a column that
    is empty everywhere and nothing is drawn. A candidate is therefore only
    accepted once a non-empty value has actually been seen in it.
    """
    if not hasattr(qgis_layer, "fields") or not hasattr(qgis_layer, "uniqueValues"):
        return None
    try:
        by_lower = {f.name().lower(): f.name() for f in qgis_layer.fields()}
    except Exception:
        return None

    for candidate in LABEL_FIELD_CANDIDATES:
        field = by_lower.get(candidate)
        if field is None:
            continue
        with suppress(Exception):
            index = qgis_layer.fields().indexOf(field)
            for value in qgis_layer.uniqueValues(index, 25):
                if value is not None and str(value).strip():
                    return field
    return None


def create_qgis_marker_symbol(rule: PlanStyleRule, text_anchor: bool = False) -> Any:
    """Build a QgsMarkerSymbol for point features.

    ``text_anchor`` marks a point whose real content is the label drawn at it —
    a CAD text insertion point. There the marker is only an anchor and must not
    compete with the text it carries.
    """
    from qgis.core import QgsMarkerSymbol, QgsSimpleMarkerSymbolLayer  # type: ignore
    from qgis.PyQt.QtGui import QColor  # type: ignore

    symbol = QgsMarkerSymbol()
    while symbol.symbolLayerCount() > 0:
        symbol.takeSymbolLayer(0)

    marker_layer = QgsSimpleMarkerSymbolLayer()
    marker_layer.setColor(QColor(rule.fill_color if rule.fill_color != "#E0E0E0" else "#333333"))
    marker_layer.setStrokeColor(QColor(rule.stroke_color))
    if text_anchor:
        marker_layer.setStrokeWidth(0.0)
        marker_layer.setSize(0.6)
    else:
        marker_layer.setStrokeWidth(0.4)
        # CAD symbol layers carry no official point gösterim; a chunky marker
        # would bury the plan under dots, so they stay discreet.
        marker_layer.setSize(2.6 if rule.category_id != "DEFAULT_PLAN" else 1.2)

    if rule.marker_shape == "square":
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Shape.Square)
    elif rule.marker_shape == "triangle":
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Shape.Triangle)
    elif rule.marker_shape == "cross":
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Shape.Cross)
    else:
        marker_layer.setShape(QgsSimpleMarkerSymbolLayer.Shape.Circle)

    symbol.appendSymbolLayer(marker_layer)
    return symbol


def apply_plan_symbology(
    qgis_layer: Any,
    plan_scale: str = "1/1000",
    override_rule: Optional[PlanStyleRule] = None,
    plan_type: str = "AUTO",
    source_name: Optional[str] = None,
) -> bool:
    """Apply native QGIS style (fill color, hatch pattern, stroke width, labeling) to a QgsVectorLayer.

    2-Stage Hybrid Rendering Pipeline (official e-Plan catalog first, legacy
    PASE keyword catalog as fallback):
      1. If attribute table contains land-use fields with multiple unique values, applies QgsCategorizedSymbolRenderer.
      2. If single-use layer or no multi-value field, matches layer name against PlanGML rules and applies QgsSingleSymbolRenderer.

    ``plan_type`` selects the official style set: "UIP", "NIP", "CDP" or
    "AUTO" to infer it from ``source_name`` / the layer name (scale prefixes
    like 1000/5000/25000 and words like NAZIM or ÇEVRE are recognized).

    Safely handles headless/testing environments where qgis.core might not be loaded.
    Returns True if styling was successfully applied, False otherwise.
    """
    layer_name = qgis_layer.name() if hasattr(qgis_layer, "name") else ""
    if plan_type not in EPLAN_PLAN_TYPES:
        plan_type = (detect_plan_type(source_name)
                     or detect_plan_type(layer_name)
                     or "UIP")

    rule = override_rule
    if rule is None and layer_name:
        rule = PlanSymbologyMatcher.match_rule(
            layer_name, scale=plan_scale, plan_type=plan_type)

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

    # Decided before the symbols are built: on a point layer that carries text,
    # the label is the content and the marker shrinks to an anchor.
    label_field = pick_label_field(qgis_layer)
    text_anchor = geom_type == 0 and label_field is not None

    # Helper builder for a rule & geom type
    def build_symbol(r: PlanStyleRule):
        if geom_type == 2:
            return create_qgis_fill_symbol(r)
        elif geom_type == 1:
            return create_qgis_line_symbol(r)
        elif geom_type == 0:
            return create_qgis_marker_symbol(r, text_anchor=text_anchor)
        return None

    # Stage 1: Categorized Renderer Check on Attribute Fields
    category_field = None
    if hasattr(qgis_layer, "fields") and hasattr(qgis_layer, "uniqueValues"):
        fields = [f.name() for f in qgis_layer.fields()]
        plangml_candidates = [
            "uip_tabaka", "ALT_GRUP_ADI", "TAM_ADI", "GISTERIM", "layer_name", "tabaka", "layer",
            "ALT_GRUP_ID", "FONKSIYON_KODU", "LEJANT_KODU", "KOD", "FONKSIYON", "LEJANT", "KULLANIM",
            "UST_GRUP_ADI", "UST_GRUP_ID", "TYPE", "DETAY"
        ]
        # Prefer candidate field that actually has MULTIPLE unique values in this layer
        for candidate in plangml_candidates:
            for f in qgis_layer.fields():
                if f.name().upper() == candidate.upper():
                    idx = qgis_layer.fields().indexOf(f.name())
                    u_vals = qgis_layer.uniqueValues(idx)
                    if len(u_vals) > 1:
                        category_field = f.name()
                        break
            if category_field:
                break

        # Fallback: if no multi-value field found, pick first candidate field that exists
        if not category_field:
            for candidate in plangml_candidates:
                for f in qgis_layer.fields():
                    if f.name().upper() == candidate.upper():
                        category_field = f.name()
                        break
                if category_field:
                    break

    applied_categorized = False
    if category_field and hasattr(qgis_layer, "uniqueValues"):
        idx = qgis_layer.fields().indexOf(category_field)
        unique_vals = qgis_layer.uniqueValues(idx)
        if len(unique_vals) > 1 and len(unique_vals) <= 300:
            categories = []
            for val in unique_vals:
                val_str = str(val) if val is not None else ""
                matched_rule = PlanSymbologyMatcher.match_rule(
                    val_str,
                    scale=plan_scale,
                    attributes={category_field: val},
                    plan_type=plan_type,
                ) or rule
                sym = build_symbol(matched_rule)
                if sym:
                    cat_label = matched_rule.display_name if matched_rule else val_str
                    categories.append(QgsRendererCategory(val, sym, cat_label))
            if categories:
                renderer = QgsCategorizedSymbolRenderer(category_field, categories)
                qgis_layer.setRenderer(renderer)
                applied_categorized = True

    # Stage 2: Single Symbol Renderer (for single-use CAD tabaka layers or fallback)
    if not applied_categorized:
        sym = build_symbol(rule or PLAN_SYMBOLOGY_CATALOG[0])
        if sym:
            qgis_layer.setRenderer(QgsSingleSymbolRenderer(sym))

    # Text annotations: the drawing's own text, drawn where the CAD put it.
    if label_field:
        layer_settings = QgsPalLayerSettings()
        layer_settings.fieldName = label_field
        layer_settings.isExpression = False
        with suppress(Exception):
            layer_settings.placement = QgsPalLayerSettings.Placement.OverPoint
        text_format = QgsTextFormat()
        text_format.setSize(9.5)
        text_format.setColor(QColor("#1A1A1A"))
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
