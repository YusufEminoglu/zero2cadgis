# -*- coding: utf-8 -*-
"""Renderer-default colours per MPYY upper group — NOT the regulation's.

Used only when a tabaka has an official identity (``plangml_schema``) but the
Ministry's e-Plan style set gives it no style of its own. The Mekânsal Planlar
Yapım Yönetmeliği defines the groups and codes; it does not define these
swatches — they are authored (Material Design tones chosen to keep groups
apart), so rules built from them carry ``official=False``. Where the e-Plan
catalog styles a function, that style always wins.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

# Authored defaults per upper group: 23 polygon groups, 10 line groups
MPYY_GROUP_PALETTES: Dict[Tuple[int, str], Dict[str, Any]] = {
    # POLYGON GROUPS
    (101000, "POLYGON"): {"fill": "#81C784", "stroke": "#2E7D32", "stroke_width": 0.35},  # Açık ve Yeşil Alanlar
    (102000, "POLYGON"): {"fill": "#FF8A80", "stroke": "#C62828", "stroke_width": 0.4},   # Afet Tehlikeli Alanlar
    (103000, "POLYGON"): {"fill": "#A5D6A7", "stroke": "#388E3C", "stroke_width": 0.35},  # Bugünkü Arazi Kullanımı Korunacak
    (104000, "POLYGON"): {"fill": "#BCAAA4", "stroke": "#4E342E", "stroke_width": 0.4},   # Demiryolları
    (105000, "POLYGON"): {"fill": "#90CAF9", "stroke": "#1565C0", "stroke_width": 0.35},  # Eğitim Tesisleri
    (106000, "POLYGON"): {"fill": "#FFAB91", "stroke": "#D84315", "stroke_width": 0.35},  # Enerji Üretim Dağıtım
    (107000, "POLYGON"): {"fill": "#CFD8DC", "stroke": "#37474F", "stroke_width": 0.4},   # Havayolları
    (108000, "POLYGON"): {"fill": "#C5CAE9", "stroke": "#283593", "stroke_width": 0.35},  # İbadet Alanları
    (109000, "POLYGON"): {"fill": "#FFE0B2", "stroke": "#EF6C00", "stroke_width": 0.35},  # Karayolları
    (110000, "POLYGON"): {"fill": "#CE93D8", "stroke": "#6A1B9A", "stroke_width": 0.35},  # Kentsel Çalışma Alanları
    (111000, "POLYGON"): {"fill": "#B0BEC5", "stroke": "#37474F", "stroke_width": 0.35},  # Kentsel Toplu Taşıma
    (112000, "POLYGON"): {"fill": "#FFE082", "stroke": "#F57F17", "stroke_width": 0.35},  # Konut / Yerleşim
    (113000, "POLYGON"): {"fill": "#80CBC4", "stroke": "#004D40", "stroke_width": 0.35},  # Korunacak Alanlar
    (114000, "POLYGON"): {"fill": "#FFCC80", "stroke": "#E65100", "stroke_width": 0.35},  # Özel Kanunlarla Belirlenen Alanlar
    (115000, "POLYGON"): {"fill": "#80CBC4", "stroke": "#00695C", "stroke_width": 0.35},  # Sağlık Tesisleri
    (116000, "POLYGON"): {"fill": "#F48FB1", "stroke": "#AD1457", "stroke_width": 0.35},  # Sosyal ve Kültürel Tesisler
    (117000, "POLYGON"): {"fill": "#81D4FA", "stroke": "#0277BD", "stroke_width": 0.35},  # Su - Atıksu Sistemleri
    (118000, "POLYGON"): {"fill": "#80DEEA", "stroke": "#00838F", "stroke_width": 0.35},  # Turizm Alanları
    (119000, "POLYGON"): {"fill": "#FFCCBC", "stroke": "#BF360C", "stroke_width": 0.35},  # Yapı Sınırlaması Korumaları
    (120000, "POLYGON"): {"fill": "#80DEEA", "stroke": "#006064", "stroke_width": 0.35},  # Denizyolları
    (121000, "POLYGON"): {"fill": "#ECEFF1", "stroke": "#263238", "stroke_width": 0.5},   # İdari Sınırlar
    (122000, "POLYGON"): {"fill": "#ECEFF1", "stroke": "#263238", "stroke_width": 0.5},   # Planlama Sınırları
    (123000, "POLYGON"): {"fill": "#C8E6C9", "stroke": "#2E7D32", "stroke_width": 0.35},  # Sosyal Altyapı Alanları

    # LINE GROUPS
    (104000, "LINE"): {"line_color": "#4E342E", "line_width": 0.6, "dash": [6.0, 2.0, 2.0, 2.0]},  # Demiryolları
    (106000, "LINE"): {"line_color": "#D84315", "line_width": 0.5, "dash": [5.0, 2.0]},            # Enerji / Boru Hatları
    (111000, "LINE"): {"line_color": "#00838F", "line_width": 0.6, "dash": [4.0, 2.0]},            # Toplu Taşıma / Havaray
    (114000, "LINE"): {"line_color": "#E65100", "line_width": 0.5, "dash": [6.0, 3.0]},            # Özel Kanun Sınırları / Sahil
    (117000, "LINE"): {"line_color": "#0277BD", "line_width": 0.5, "dash": [4.0, 2.0]},            # Su - Atıksu Hatları
    (119000, "LINE"): {"line_color": "#C62828", "line_width": 0.5, "dash": [3.0, 2.0]},            # Yapı Sınırlaması / Mania
    (120000, "LINE"): {"line_color": "#006064", "line_width": 0.6},                                 # Denizyolu
    (130000, "LINE"): {"line_color": "#000000", "line_width": 0.5},                                 # Ada Kenarı
    (132000, "LINE"): {"line_color": "#D32F2F", "line_width": 0.6, "dash": [4.0, 2.0]},            # Cephe Çizgileri
    (133000, "LINE"): {"line_color": "#37474F", "line_width": 0.5},                                 # Karayolları
}

# Function-specific overrides for distinct legislative appearance
MPYY_FUNCTION_PALETTES: Dict[str, Dict[str, Any]] = {
    # Yeşil & Spor
    "ARBORETUM_BOTANIK_PARKI": {"fill": "#43A047", "stroke": "#1B5E20"},
    "FUAR_PANAYIR_VE_FESTIVAL_ALANI": {"fill": "#66BB6A", "stroke": "#1B5E20"},
    "HAYVANAT_BAHCESI": {"fill": "#4CAF50", "stroke": "#2E7D32"},
    "HIPODROM": {"fill": "#81C784", "stroke": "#2E7D32"},
    "COCUK_BAHCESI_VE_OYUN_ALANI": {"fill": "#A5D6A7", "stroke": "#2E7D32"},
    "BOTANIK_BAHCESI": {"fill": "#43A047", "stroke": "#1B5E20"},
    # Afet
    "ONLEMLI_ALAN": {"fill": "#FFE082", "stroke": "#FF8F00", "stroke_width": 0.45},
    "YAPI_YASAKLI_ALAN": {"fill": "#FF8A80", "stroke": "#D50000", "stroke_width": 0.5},
    # Eğitim & Sağlık
    "ANAOKULU_ALANI": {"fill": "#90CAF9", "stroke": "#1565C0"},
    "OZEL_ANAOKULU_ALANI": {"fill": "#BBDEFB", "stroke": "#0D47A1"},
    "AILE_SAGLIGI_MERKEZI": {"fill": "#80CBC4", "stroke": "#00695C"},
    # Ulaşım
    "TERMINAL_OTOGAR": {"fill": "#FFCC80", "stroke": "#E65100"},
    "TIR_KAMYON_MAKINE_PARKI_VE_GARAJ_ALANI": {"fill": "#FFE0B2", "stroke": "#EF6C00"},
    "ELEKTRIKLI_ARAC_SARJ_ISTASYONU": {"fill": "#B2DFDB", "stroke": "#00695C"},
    "HAVAALANI_HAVALIMANI": {"fill": "#CFD8DC", "stroke": "#37474F"},
    "HELIKOPTER_INIS_ALANI": {"fill": "#ECEFF1", "stroke": "#455A64"},
    "BALIKCI_BARINAGI": {"fill": "#80DEEA", "stroke": "#006064"},
    "ISKELE": {"fill": "#4DD0E1", "stroke": "#00838F"},
    "TERSANE_ALANI": {"fill": "#B0BEC5", "stroke": "#37474F"},
    "YAT_LIMANI": {"fill": "#26C6DA", "stroke": "#006064"},
    "LIMAN": {"fill": "#00ACC1", "stroke": "#006064"},
    # Turizm
    "GOLF_ALANI": {"fill": "#C8E6C9", "stroke": "#2E7D32"},
    "GOLF_TURIZMI": {"fill": "#C8E6C9", "stroke": "#2E7D32"},
    "EKOTURIZM_KIRSAL_TURIZM": {"fill": "#DCEDC8", "stroke": "#558B2F"},
    "HOSTEL_ALANI": {"fill": "#80DEEA", "stroke": "#00838F"},
    "MOTEL_ALANI": {"fill": "#80DEEA", "stroke": "#00838F"},
    "KIS_SPORLARI_VE_KAYAK_TESISI_ALANI": {"fill": "#B3E5FC", "stroke": "#0277BD"},
    # Sosyal Tesisler
    "KONGRE_VE_SERGI_MERKEZI_ALANI": {"fill": "#F48FB1", "stroke": "#AD1457"},
    "KULTUREL_TESIS_ALANI": {"fill": "#F06292", "stroke": "#C2185B"},
    "OZEL_KULTUREL_TESIS_ALANI": {"fill": "#F8BBD0", "stroke": "#880E4F"},
    "SEFKAT_EVLERI_ALANI": {"fill": "#CE93D8", "stroke": "#7B1FA2"},
    "YASLI_BAKIMEVI_ALANI": {"fill": "#D1C4E9", "stroke": "#512DA8"},
    "SOKAK_HAYVANLARI_BARINAGI_ALANI": {"fill": "#C8E6C9", "stroke": "#2E7D32"},
    # İbadet
    "KILISE": {"fill": "#C5CAE9", "stroke": "#283593"},
    "SAPEL": {"fill": "#D1C4E9", "stroke": "#311B92"},
    "SINAGOG_HAVRA": {"fill": "#9FA8DA", "stroke": "#1A237E"},
    # Lines
    "HAT_HIZLI_TREN": {"line_color": "#B71C1C", "line_width": 0.8, "dash": [8.0, 2.0, 2.0, 2.0]},
    "HIZLI_TREN_HATTI": {"line_color": "#B71C1C", "line_width": 0.8, "dash": [8.0, 2.0, 2.0, 2.0]},
    "HAT_TRIYAJ": {"line_color": "#4E342E", "line_width": 0.6, "dash": [4.0, 2.0]},
    "HAT_BORU_HATTI": {"line_color": "#E65100", "line_width": 0.5, "dash": [6.0, 2.0]},
    "BORU_HATTI": {"line_color": "#E65100", "line_width": 0.5, "dash": [6.0, 2.0]},
    "HAT_CEBRI_BORU": {"line_color": "#BF360C", "line_width": 0.6, "dash": [5.0, 2.0]},
    "CEBRI_BORU_HATTI": {"line_color": "#BF360C", "line_width": 0.6, "dash": [5.0, 2.0]},
    "HAT_DOGALGAZ": {"line_color": "#F57C00", "line_width": 0.5, "dash": [6.0, 2.0, 2.0, 2.0]},
    "DOGALGAZ_BORU_HATTI": {"line_color": "#F57C00", "line_width": 0.5, "dash": [6.0, 2.0, 2.0, 2.0]},
    "HAT_HAVAI": {"line_color": "#00838F", "line_width": 0.6, "dash": [6.0, 3.0]},
    "HAVAI_HAT": {"line_color": "#00838F", "line_width": 0.6, "dash": [6.0, 3.0]},
    "HAT_HAVARAY": {"line_color": "#0097A7", "line_width": 0.7, "dash": [5.0, 2.0]},
    "HAVARAY": {"line_color": "#0097A7", "line_width": 0.7, "dash": [5.0, 2.0]},
    "HAT_RAYLI_TOPLU_TAS": {"line_color": "#D32F2F", "line_width": 0.7, "dash": [6.0, 2.0]},
    "RAYLI_TOPLU_TASIMA_HATTI": {"line_color": "#D32F2F", "line_width": 0.7, "dash": [6.0, 2.0]},
    "SNR_SAHIL_SERIDI": {"line_color": "#00838F", "line_width": 0.6, "dash": [6.0, 3.0]},
    "SAHIL_SERIDI": {"line_color": "#00838F", "line_width": 0.6, "dash": [6.0, 3.0]},
    "HAT_ANA_ICME_SUYU": {"line_color": "#0288D1", "line_width": 0.6, "dash": [6.0, 2.0]},
    "ICME_SUYU_ANA_HATTI": {"line_color": "#0288D1", "line_width": 0.6, "dash": [6.0, 2.0]},
    "HAT_ATIKSU_KOLLEKTOR": {"line_color": "#5D4037", "line_width": 0.6, "dash": [6.0, 2.0]},
    "ATIK_SU_ANA_KOLLEKTORU": {"line_color": "#5D4037", "line_width": 0.6, "dash": [6.0, 2.0]},
    "HAT_SOGUTMA_SUYU": {"line_color": "#0097A7", "line_width": 0.5, "dash": [4.0, 2.0]},
    "SOGUTMA_SUYU_ALMA_HATTI": {"line_color": "#0097A7", "line_width": 0.5, "dash": [4.0, 2.0]},
    "SNR_MANIA_PLAN": {"line_color": "#E53935", "line_width": 0.6, "dash": [6.0, 2.0, 2.0, 2.0]},
    "MANIA_PLANI": {"line_color": "#E53935", "line_width": 0.6, "dash": [6.0, 2.0, 2.0, 2.0]},
    "KST_HAVA_KORIDORU": {"line_color": "#D32F2F", "line_width": 0.6, "dash": [6.0, 3.0]},
    "HAVAALANI_HAVA_KORIDORU": {"line_color": "#D32F2F", "line_width": 0.6, "dash": [6.0, 3.0]},
    "HAT_OTOYOL": {"line_color": "#D84315", "line_width": 0.8},
    "ERISME_KONTROLLU_KARAYOLU_OTOYOL": {"line_color": "#D84315", "line_width": 0.8},
    "BOLUNMUS_TASIT_YOLU": {"line_color": "#37474F", "line_width": 0.7, "dash": [6.0, 2.0]},
    "TASIT_YOLU": {"line_color": "#455A64", "line_width": 0.5},
    "KORUNAN_CEPHE_CIZGISI": {"line_color": "#1976D2", "line_width": 0.6, "dash": [4.0, 2.0]},
    "DUZELTILEN_CEPHE_CIZGISI": {"line_color": "#FB8C00", "line_width": 0.6, "dash": [4.0, 2.0]},
    "ONERILEN_CEPHE_CIZGISI": {"line_color": "#E53935", "line_width": 0.6, "dash": [4.0, 2.0]},
}
