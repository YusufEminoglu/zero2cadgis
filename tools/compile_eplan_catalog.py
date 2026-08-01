# -*- coding: utf-8 -*-
"""Offline compiler: official e-Plan GeoServer SLD set -> embedded plugin catalog.

Reads the Ministry of Environment, Urbanisation and Climate Change e-Plan
GeoServer data directory archive ("E-Plan SLD.zip", the public plan gösterimleri
style set) and emits:

  * ``core/eplan_catalog.py``  — resolved official style data (fill colors,
    tarama pattern references, stroke colors/widths/dash arrays) for every CAD
    tabaka token the plugin knows how to map, per plan type (UIP / NIP / CDP).
  * ``resources/eplan_tarama/<uuid>.png`` — only the tarama (hatch pattern)
    tiles actually referenced by the mapped rules.

This tool is development-only: it is excluded from the released zip via
``.zipignore`` and is re-run manually whenever the Ministry publishes a new
style set.

Usage:
    py -3 tools/compile_eplan_catalog.py "C:/path/to/E-Plan SLD.zip"

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import io
import os
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
OUT_CATALOG = os.path.join(PLUGIN_ROOT, "core", "eplan_catalog.py")
OUT_TARAMA_DIR = os.path.join(PLUGIN_ROOT, "resources", "eplan_tarama")

NS = {
    "sld": "http://www.opengis.net/sld",
    "ogc": "http://www.opengis.net/ogc",
}
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"

# ---------------------------------------------------------------------------
# CAD tabaka token -> official e-Plan (style, rule title) mapping.
#
# Key: normalized token sequence (see PlanSymbologyMatcher.normalize_string);
# matching is longest-key-first on contiguous token subsequences, so
# "KONUT_TICARET" wins over "KONUT" for layer PL_KONUT_TICARET.
#
# Value: (turkish_label, {plan_type: (style_name, rule_title_or_None)}).
# rule_title None selects the style's first rule. A missing plan type falls
# back at runtime (requested -> UIP -> NIP). Styles from the mekansal set
# (MUIP/MNIP) are borrowed where the classic set lacks an equivalent rule —
# they are equally official.
# ---------------------------------------------------------------------------
U, N, C = "UIP", "NIP", "CDP"

MAPPING = {
    # --- Konut / karma kullanim ---
    "KONUT_TICARET": ("Ticaret + Konut Alanı (TİCK)", {
        U: ("UIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI")}),
    "TICARET_KONUT": ("Ticaret + Konut Alanı (TİCK)", {
        U: ("UIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI")}),
    "TICARET_TURIZM": ("Ticaret + Turizm Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "TICARET_TURIZM_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_TURIZM_ALANI")}),
    "TIB": ("Ticaret + Konut Alanı (TİCK)", {
        U: ("UIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI")}),
    "TICK": ("Ticaret + Konut Alanı (TİCK)", {
        U: ("UIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_KONUT_ALANI")}),
    "YERLESIK_KONUT": ("Yerleşik Konut Alanı", {
        U: ("UIP_KONUT", "YERLESIK_KONUT"),
        N: ("NIP_MEVCUT_KONUT", "ORTA_151_300HA"),
        C: ("CDP_KENTSEL_YERLESIK", None)}),
    "KONUT_YERLESIK": ("Yerleşik Konut Alanı", {
        U: ("UIP_KONUT", "YERLESIK_KONUT"),
        N: ("NIP_MEVCUT_KONUT", "ORTA_151_300HA"),
        C: ("CDP_KENTSEL_YERLESIK", None)}),
    "MESKUN": ("Yerleşik (Meskun) Konut Alanı", {
        U: ("UIP_KONUT", "YERLESIK_KONUT"),
        N: ("NIP_MEVCUT_KONUT", "ORTA_151_300HA"),
        C: ("CDP_KENTSEL_YERLESIK", None)}),
    "GELISME_KONUT": ("Gelişme Konut Alanı", {
        U: ("UIP_KONUT", "GELISME_KONUT"),
        N: ("NIP_GELISME_KONUT", "ORTA_121_250HA"),
        C: ("CDP_KENTSEL_GELISME_KONUT", None)}),
    "KONUT_GELISME": ("Gelişme Konut Alanı", {
        U: ("UIP_KONUT", "GELISME_KONUT"),
        N: ("NIP_GELISME_KONUT", "ORTA_121_250HA"),
        C: ("CDP_KENTSEL_GELISME_KONUT", None)}),
    "KONUT": ("Konut Alanı", {
        U: ("UIP_KONUT", "GELISME_KONUT"),
        N: ("NIP_MEVCUT_KONUT", "ORTA_151_300HA"),
        C: ("CDP_KENTSEL_YERLESIK", None)}),
    "MESKEN": ("Konut Alanı", {
        U: ("UIP_KONUT", "GELISME_KONUT"),
        N: ("NIP_MEVCUT_KONUT", "ORTA_151_300HA"),
        C: ("CDP_KENTSEL_YERLESIK", None)}),
    "TOPLU_KONUT": ("Toplu Konut Alanı", {
        U: ("UIP_DONUSUM_KONUT_ALANLARI", "TOPLU_KONUT_ALANLARI"),
        N: ("NIP_DONUSUM_KONUT_ALANLARI", "TOPLU_KONUT_ALANLARI")}),
    "GECEKONDU": ("Gecekondu Önleme Bölgesi", {
        U: ("UIP_DONUSUM_KONUT_ALANLARI", "GECEKONDU_ONLEME_BOLGESI"),
        N: ("NIP_DONUSUM_KONUT_ALANLARI", "GECEKONDU_ONLEME_BOLGESI")}),
    "KDKCA": ("Konut Dışı Kentsel Çalışma Alanı", {
        U: ("MUIP_KENTSEL_CALISMA", "KONUT_DISI_KENTSEL"),
        N: ("NIP_KENTSEL_CALISMA", "KONUT_DISI_KENTSEL_CALISMA_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "KENTSEL_SERVIS_ALANI")}),
    "KONUT_DISI": ("Konut Dışı Kentsel Çalışma Alanı", {
        U: ("MUIP_KENTSEL_CALISMA", "KONUT_DISI_KENTSEL"),
        N: ("NIP_KENTSEL_CALISMA", "KONUT_DISI_KENTSEL_CALISMA_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "KENTSEL_SERVIS_ALANI")}),

    # --- Ticaret ve calisma ---
    "MIA": ("Merkezi İş Alanı (MİA)", {
        U: ("NIP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI")}),
    "MERKEZI_IS": ("Merkezi İş Alanı (MİA)", {
        U: ("NIP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI")}),
    "TICARET": ("Ticaret Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "TICARET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI")}),
    "KUCUK_SANAYI": ("Küçük Sanayi Alanı (KSS)", {
        U: ("UIP_KENTSEL_CALISMA", "KUCUK_SANAYI_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "KUCUK_SANAYI_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "SANAYI_VE_DEPOLAMA_BOLGESI")}),
    "KSS": ("Küçük Sanayi Alanı (KSS)", {
        U: ("UIP_KENTSEL_CALISMA", "KUCUK_SANAYI_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "KUCUK_SANAYI_ALANI")}),
    "OSB": ("Organize Sanayi Bölgesi (OSB)", {
        U: ("UIP_ILAN_EDILEN_CLSMA_ALAN", "OSB"),
        N: ("NIP_ILAN_EDILEN_CLSMA_ALAN", "OSB"),
        C: ("CDP_KENTSEL_CALISMA", "OSB")}),
    "ORGANIZE_SANAYI": ("Organize Sanayi Bölgesi (OSB)", {
        U: ("UIP_ILAN_EDILEN_CLSMA_ALAN", "OSB"),
        N: ("NIP_ILAN_EDILEN_CLSMA_ALAN", "OSB"),
        C: ("CDP_KENTSEL_CALISMA", "OSB")}),
    "SANAYI": ("Sanayi Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "SANAYI_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "SANAYI_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "SANAYI_VE_DEPOLAMA_BOLGESI")}),
    "PAZAR": ("Pazar Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "PAZAR_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "PAZAR_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "KENTSEL_SERVIS_ALANI")}),
    "HAL": ("Toptan Ticaret Alanı (Hal)", {
        U: ("UIP_KENTSEL_CALISMA", "TOPTAN_TICARET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "MERKEZI_IS_ALANI")}),
    "TOPTAN_TICARET": ("Toptan Ticaret Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "TOPTAN_TICARET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_ALANI")}),
    "TOPTANCI": ("Toptan Ticaret Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "TOPTAN_TICARET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "TICARET_ALANI")}),
    "SU_DEPOSU": ("Su Deposu (İçmesuyu Tesisi)", {
        U: ("UIP_ICMESU_TESIS", "DEPOLAMA"),
        N: ("NIP_ICMESU_TESIS", "DEPOLAMA")}),
    "DEPOLAMA": ("Depolama Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "DEPOLAMA_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "DEPOLAMA_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "SANAYI_VE_DEPOLAMA_BOLGESI")}),
    "DEPO": ("Depolama Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "DEPOLAMA_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "DEPOLAMA_ALANI")}),
    "LOJISTIK": ("Lojistik Tesis Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "LOJISTIK_TESIS_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "LOJISTIK_TESIS_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "LOJISTIK_BOLGE")}),
    "AKARYAKIT": ("Akaryakıt ve Servis İstasyonu", {
        U: ("UIP_KENTSEL_CALISMA", "AKARYAKIT_SERVIS_ISTASYONU"),
        N: ("NIP_KENTSEL_CALISMA", "AKARYAKIT_SERVIS_ISTASYONU_ALANI")}),
    "ASKERI": ("Askeri Alan", {
        U: ("UIP_KENTSEL_CALISMA", "ASKERI_ALAN"),
        N: ("NIP_KENTSEL_CALISMA", "ASKERI_ALAN"),
        C: ("CDP_ASKERI_YSK_GUVENLIK_BLG", None)}),
    "RESMI_KURUM": ("Resmi Kurum Alanı", {
        U: ("UIP_FONKSIYONLU_CALISMA", "RESMI_KURUM_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "KAMU_HIZMET_ALANI"),
        C: ("CDP_KENTSEL_CALISMA", "KENTSEL_SERVIS_ALANI")}),
    "KAMU_HIZMET": ("Kamu Hizmet Alanı", {
        U: ("MUIP_KENTSEL_CALISMA", "KAMU_HIZMET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "KAMU_HIZMET_ALANI")}),
    "BELEDIYE_SINIRI": ("Belediye Sınırı", {
        U: ("UIP_BELEDIYE_SINIRI", None),
        N: ("NIP_BELEDIYE_SINIRI", None),
        C: ("CDP_BELEDIYE_SINIRI", None)}),
    "BHA": ("Belediye Hizmet Alanı (BHA)", {
        U: ("UIP_FONKSIYONLU_CALISMA", "BELEDIYE_HIZMET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "BELEDIYE_HIZMET_ALANI")}),
    "BELEDIYE_HIZMET": ("Belediye Hizmet Alanı (BHA)", {
        U: ("UIP_FONKSIYONLU_CALISMA", "BELEDIYE_HIZMET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "BELEDIYE_HIZMET_ALANI")}),
    "BELEDIYE": ("Belediye Hizmet Alanı (BHA)", {
        U: ("UIP_FONKSIYONLU_CALISMA", "BELEDIYE_HIZMET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "BELEDIYE_HIZMET_ALANI")}),
    "IDARI": ("İdari Hizmet Alanı", {
        U: ("UIP_KENTSEL_CALISMA", "IDARI_HIZMET_ALANI"),
        N: ("NIP_KENTSEL_CALISMA", "KAMU_HIZMET_ALANI")}),
    "TOPLU_ISYERI": ("Toplu İşyerleri", {
        U: ("UIP_FONKSIYONLU_CALISMA", "TOPLU_ISYERI"),
        N: ("NIP_KENTSEL_CALISMA", "TOPLU_ISYERLERI")}),

    # --- Sosyal / kulturel ---
    "SOSYOKULTUREL": ("Sosyal ve Kültürel Tesis Alanı", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "SOSYAL_TESIS_ALANI"),
        N: ("NIP_SOSYAL_KULTUREL_ALAN", "SOSYAL_TESIS_ALANI"),
        C: ("CDP_SOSYAL_KULTUREL_ALAN", "KENTSEL_BOLGESEL_SOSYAL_ALTYAPI_ALANI")}),
    "SOSYAL_KULTUREL": ("Sosyal ve Kültürel Tesis Alanı", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "SOSYAL_TESIS_ALANI"),
        N: ("NIP_SOSYAL_KULTUREL_ALAN", "SOSYAL_TESIS_ALANI"),
        C: ("CDP_SOSYAL_KULTUREL_ALAN", "KENTSEL_BOLGESEL_SOSYAL_ALTYAPI_ALANI")}),
    "SOSYAL_TESIS": ("Sosyal Tesis Alanı", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "SOSYAL_TESIS_ALANI"),
        N: ("NIP_SOSYAL_KULTUREL_ALAN", "SOSYAL_TESIS_ALANI")}),
    "KULTUR": ("Kültürel Tesis Alanı", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "KULTUREL_TESIS_ALANI"),
        N: ("NIP_SOSYAL_KULTUREL_ALAN", "KULTUREL_TESIS_ALANI")}),
    "KRES": ("Kreş / Gündüz Bakımevi", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "KRES_GUNDUZ_BAKIMEVI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "YURT": ("Yurt Alanı", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "YURT_ALANI"),
        N: ("MNIP_SOSYAL_KULTUREL_ALAN", "YURT_ALANI")}),
    "SPOR": ("Spor Tesisleri Alanı", {
        U: ("UIP_SOSYAL_KULTUREL_ALAN", "ACIK_SPOR_TESISI_ALANI"),
        N: ("NIP_SOSYAL_KULTUREL_ALAN", "SPOR_ALANI"),
        C: ("CDP_ACIK_YESIL_ALAN", "KENTSEL_BOLGESEL_YESIL_SPOR_ALANI")}),

    # --- Acik ve yesil alanlar ---
    "PARK": ("Park", {
        U: ("UIP_ACIK_YESIL_ALAN", "PARK"),
        N: ("NIP_ACIK_YESIL_ALAN", "PARK_VE_YESIL_ALAN"),
        C: ("CDP_ACIK_YESIL_ALAN", "KENTSEL_BOLGESEL_YESIL_SPOR_ALANI")}),
    "COCUK_BAHCESI": ("Çocuk Bahçesi / Oyun Alanı", {
        U: ("UIP_ACIK_YESIL_ALAN", "COCUK_BAHCESI_OYUN_ALANI"),
        N: ("NIP_ACIK_YESIL_ALAN", "PARK_VE_YESIL_ALAN")}),
    "OYUN": ("Çocuk Bahçesi / Oyun Alanı", {
        U: ("UIP_ACIK_YESIL_ALAN", "COCUK_BAHCESI_OYUN_ALANI"),
        N: ("NIP_ACIK_YESIL_ALAN", "PARK_VE_YESIL_ALAN")}),
    "YESIL": ("Yeşil Alan", {
        U: ("UIP_ACIK_YESIL_ALAN", "PARK"),
        N: ("NIP_ACIK_YESIL_ALAN", "PARK_VE_YESIL_ALAN"),
        C: ("CDP_ACIK_YESIL_ALAN", "KENTSEL_BOLGESEL_YESIL_SPOR_ALANI")}),
    "REKREASYON": ("Rekreasyon Alanı", {
        U: ("UIP_ACIK_YESIL_ALAN", "REKREASYON_ALANI"),
        N: ("NIP_ACIK_YESIL_ALAN", "REKREASYON_ALANI")}),
    "MESIRE": ("Mesire Yeri", {
        U: ("UIP_ACIK_YESIL_ALAN", "MESIRE_YERI"),
        N: ("NIP_ACIK_YESIL_ALAN", "MESIRE_YERI")}),
    "MEZARLIK": ("Mezarlık Alanı", {
        U: ("UIP_ACIK_YESIL_ALAN", "MEZARLIK_ALANI"),
        N: ("NIP_ACIK_YESIL_ALAN", "MEZARLIK_ALANI")}),
    "AGACLANDIRILACAK": ("Ağaçlandırılacak Alan", {
        U: ("UIP_ACIK_YESIL_ALAN", "AGACLANDIRILACAK_ALAN"),
        N: ("NIP_ACIK_YESIL_ALAN", "AGACLANDIRILACAK_ALAN")}),
    "KENT_ORMANI": ("Kent Ormanı", {
        U: ("UIP_ACIK_YESIL_ALAN", "KENT_ORMANI"),
        N: ("NIP_ACIK_YESIL_ALAN", "KENT_ORMANI")}),
    "ORMAN": ("Orman Alanı", {
        U: ("UIP_ORMAN", None),
        N: ("NIP_ORMAN", None),
        C: ("CDP_ORMAN", None)}),
    "MEYDAN": ("Meydan", {
        U: ("UIP_ACIK_YESIL_ALAN", "MEYDAN")}),

    # --- Egitim ---
    "ANAOKUL": ("Anaokulu Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "ANAOKULU_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "ILKOKUL": ("İlkokul Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "ILKOKUL_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "ORTAOKUL": ("Ortaokul Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "ORTAOKUL_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "YATILI": ("Yatılı Bölge Okulu", {
        U: ("UIP_EGITIM_TESIS_ALANI", "ORTAOKUL_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "LISE": ("Lise Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "LISE_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "TEKNIK_OGRETIM": ("Mesleki ve Teknik Öğretim Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "MESLEKI_TEKNIK_OGRETIM_TESIS_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "MESLEK": ("Mesleki ve Teknik Öğretim Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "MESLEKI_TEKNIK_OGRETIM_TESIS_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "UNIVERSITE": ("Yükseköğretim Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "YUKSEK_OGRETIM_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "YUKSEK_OGRETIM_ALANI"),
        C: ("CDP_EGITIM_TESIS_ALANI", "YUKSEK_OGRETIM_ALANI")}),
    "YUKSEK_OGRETIM": ("Yükseköğretim Alanı", {
        U: ("UIP_EGITIM_TESIS_ALANI", "YUKSEK_OGRETIM_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "YUKSEK_OGRETIM_ALANI"),
        C: ("CDP_EGITIM_TESIS_ALANI", "YUKSEK_OGRETIM_ALANI")}),
    "OKUL": ("Eğitim Alanı", {
        U: ("MUIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),
    "EGITIM": ("Eğitim Alanı", {
        U: ("MUIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI"),
        N: ("NIP_EGITIM_TESIS_ALANI", "EGITIM_ALANI")}),

    # --- Ibadet / saglik ---
    "CAMI": ("Cami", {
        U: ("UIP_IBADET_ALANI", "CAMI"),
        N: ("NIP_IBADET_ALANI", "CAMI")}),
    "MESCIT": ("Mescit", {
        U: ("UIP_IBADET_ALANI", "MESCIT"),
        N: ("NIP_IBADET_ALANI", "MESCIT")}),
    "IBADET": ("İbadet Alanı", {
        U: ("UIP_IBADET_ALANI", "CAMI"),
        N: ("NIP_IBADET_ALANI", "CAMI")}),
    "DINI": ("İbadet Alanı", {
        U: ("UIP_IBADET_ALANI", "CAMI"),
        N: ("NIP_IBADET_ALANI", "CAMI")}),
    "HASTANE": ("Hastane", {
        U: ("UIP_SAGLIK_TESIS_ALANI", "HASTANE"),
        N: ("NIP_SAGLIK_TESIS_ALANI", "SAGLIK_TESIS_ALANI")}),
    "SAGLIK_OCAGI": ("Aile Sağlığı Merkezi", {
        U: ("UIP_SAGLIK_TESIS_ALANI", "AILE_SAGLIK_MERKEZI"),
        N: ("NIP_SAGLIK_TESIS_ALANI", "SAGLIK_TESIS_ALANI")}),
    "ASM": ("Aile Sağlığı Merkezi", {
        U: ("UIP_SAGLIK_TESIS_ALANI", "AILE_SAGLIK_MERKEZI"),
        N: ("NIP_SAGLIK_TESIS_ALANI", "SAGLIK_TESIS_ALANI")}),
    "SAGLIK": ("Sağlık Tesisleri Alanı", {
        U: ("UIP_SAGLIK_TESIS_ALANI", "SAGLIK_TESIS_ALANI"),
        N: ("NIP_SAGLIK_TESIS_ALANI", "SAGLIK_TESIS_ALANI")}),

    # --- Su / tarim / doga ---
    "DERE": ("Dere (Akarsu)", {
        U: ("UIP_SU_YUZEYI", "NEHIR_DERE"),
        N: ("NIP_SU_YUZEYI", "NEHIR_DERE"),
        C: ("CDP_SU_YUZEYI_CIZGI", "AKARSU_NEHIR_DERE")}),
    "AKARSU": ("Akarsu", {
        U: ("UIP_SU_YUZEYI", "NEHIR_DERE"),
        N: ("NIP_SU_YUZEYI", "NEHIR_DERE"),
        C: ("CDP_SU_YUZEYI_CIZGI", "AKARSU_NEHIR_DERE")}),
    "NEHIR": ("Nehir", {
        U: ("UIP_SU_YUZEYI", "NEHIR_DERE"),
        N: ("NIP_SU_YUZEYI", "NEHIR_DERE"),
        C: ("CDP_SU_YUZEYI_CIZGI", "AKARSU_NEHIR_DERE")}),
    "GOL": ("Göl", {
        U: ("UIP_SU_YUZEYI", "GOL"),
        N: ("NIP_SU_YUZEYI", "GOL"),
        C: ("CDP_SU_YUZEYI", "GOL")}),
    "BARAJ": ("Baraj", {
        U: ("UIP_SU_YUZEYI", "BARAJ"),
        N: ("NIP_SU_YUZEYI", "BARAJ"),
        C: ("CDP_SU_YUZEYI", "BARAJ")}),
    "DENIZ": ("Deniz", {
        U: ("UIP_SU_YUZEYI", "DENIZ"),
        N: ("NIP_SU_YUZEYI", "DENIZ"),
        C: ("CDP_SU_YUZEYI", "DENIZ")}),
    "SU_YUZEYI": ("Su Yüzeyi", {
        U: ("UIP_SU_YUZEYI", "GOL"),
        N: ("NIP_SU_YUZEYI", "GOL"),
        C: ("CDP_SU_YUZEYI", "GOL")}),
    "MUTLAK_TARIM": ("Mutlak Tarım Arazisi", {
        U: ("MUIP_TARIM", "MUTLAK_TARIM"),
        N: ("NIP_TARIM", "TARIM_ALANI")}),
    "ZEYTINLIK": ("Zeytinlik", {
        U: ("UIP_TARIM", "ZEYTINLIK"),
        N: ("NIP_TARIM", "ZEYTINLIK"),
        C: ("CDP_TARIM", "ZEYTINLIK")}),
    "TARIM": ("Tarım Alanı", {
        U: ("UIP_TARIM", "TARIMSAL_NITELIKLI_ALAN"),
        N: ("NIP_TARIM", "TARIM_ALANI"),
        C: ("CDP_TARIM", "TARIM_ALANI")}),
    "SERA": ("Örtü Altı Tarım Alanı", {
        U: ("UIP_TARIM", "ORTU_ALTI_TARIM"),
        N: ("NIP_TARIM", "TARIM_ALANI")}),
    "MERA": ("Mera", {
        U: ("UIP_MERA", None),
        N: ("NIP_MERA", "MERA"),
        C: ("CDP_MERA", None)}),

    # --- Turizm ---
    "TURIZM": ("Turizm Tesis Alanı", {
        U: ("MUIP_TURIZM_ALANI", "TURIZM_TESIS_ALANI"),
        N: ("NIP_TURIZM_ALANI", "TURIZM_ALANI"),
        C: ("CDP_TURIZM_ALANI", "TURIZM_BOLGESI")}),
    "OTEL": ("Otel Alanı", {
        U: ("UIP_TURIZM_ALANI", "OTEL_ALANI"),
        N: ("NIP_TURIZM_ALANI", "TURIZM_ALANI")}),
    "PANSIYON": ("Pansiyon Alanı", {
        U: ("UIP_TURIZM_ALANI", "PANSIYON_ALANI"),
        N: ("NIP_TURIZM_ALANI", "TURIZM_ALANI")}),
    "KAMPING": ("Kamping Alanı", {
        U: ("UIP_TURIZM_ALANI", "KAMPING_ALANI"),
        N: ("NIP_TURIZM_ALANI", "TURIZM_ALANI")}),
    "TATIL_KOYU": ("Tatil Köyü Alanı", {
        U: ("UIP_TURIZM_ALANI", "TATIL_KOYU_ALANI"),
        N: ("NIP_TURIZM_ALANI", "TURIZM_ALANI")}),
    "TERMAL": ("Termal Turizm Alanı", {
        U: ("UIP_TURIZM_ALANI", "TERMAL_TURIZM_ALANI"),
        N: ("NIP_TURIZM_ALANI", "TURIZM_ALANI")}),
    "GUNUBIRLIK": ("Günübirlik Tesis Alanı", {
        U: ("UIP_TURIZM_ALANI", "GUNUBIRLIK_TESIS_ALANI"),
        N: ("NIP_TURIZM_ALANI", "GUNUBIRLIK_TESIS_ALANI")}),

    # --- Teknik altyapi / ulasim tesisleri ---
    "TRAFO": ("Trafo Alanı", {
        U: ("UIP_ENERJI_DAGITIM_DEPOLAMA", "TRAFO_ALANI"),
        N: ("NIP_TEKNIK_ALTYAPI", "ENERJI")}),
    "ARITMA": ("Arıtma Tesisi", {
        U: ("UIP_ATIKSU_TESIS", "ARITMA"),
        N: ("NIP_ATIKSU_TESIS", "ARITMA")}),
    "TEKNIK_ALTYAPI": ("Teknik Altyapı Alanı", {
        U: ("UIP_TEKNIK_ALTYAPI", None),
        N: ("NIP_TEKNIK_ALTYAPI", None),
        C: ("CDP_TEKNIK_ALTYAPI", None)}),
    "ALTYAPI": ("Teknik Altyapı Alanı", {
        U: ("UIP_TEKNIK_ALTYAPI", None),
        N: ("NIP_TEKNIK_ALTYAPI", None)}),
    "OTOPARK": ("Genel Otopark", {
        U: ("UIP_KARAYOLU_TESISLERI", "GENEL_OTOPARK"),
        N: ("NIP_KARAYOLU_TESISLERI", "GENEL_OTOPARK")}),
    "ENERJI_NAKIL": ("Enerji Nakil Hattı", {
        U: ("UIP_ENERJI_NAKIL_HATTI", None),
        N: ("NIP_ENERJI_NAKIL_HATTI", None),
        C: ("CDP_ENERJI_NAKIL_HATTI", None)}),
    "DEMIRYOLU": ("Demiryolu", {
        U: ("UIP_DEMIRYOLU", "DEMIRYOLU"),
        N: ("NIP_DEMIRYOLU", "DEMIRYOLU"),
        C: ("CDP_DEMIRYOLU", "DEMIRYOLU")}),

    # --- Koruma / risk ---
    "ARKEOLOJIK": ("Arkeolojik Sit Alanı", {
        U: ("UIP_SIT_ALANLARI", "1_DERECE_ARKEOLOJIK_SIT"),
        N: ("NIP_SIT_ALANLARI", "1_DERECE_ARKEOLOJIK_SIT")}),
    "DOGAL_SIT": ("Doğal Sit Alanı", {
        U: ("UIP_SIT_ALANLARI", "1_DERECE_DOGAL_SIT"),
        N: ("NIP_SIT_ALANLARI", "1_DERECE_DOGAL_SIT")}),
    "KENTSEL_SIT": ("Kentsel Sit Alanı", {
        U: ("UIP_SIT_ALANLARI", "KENTSEL_SIT"),
        N: ("NIP_SIT_ALANLARI", "KENTSEL_SIT")}),
    "TARIHI_SIT": ("Tarihi Sit Alanı", {
        U: ("UIP_SIT_ALANLARI", "TARIHI_SIT"),
        N: ("NIP_SIT_ALANLARI", "TARIHI_SIT")}),
    "SIT": ("Sit Alanı", {
        U: ("UIP_SIT_ALANLARI", None),
        N: ("NIP_SIT_ALANLARI", None),
        C: ("CDP_SIT_ALANLARI", None)}),
    "TASKIN": ("Taşkına Maruz Alan", {
        U: ("UIP_AFET_TEHLIKELI_ALANLAR", "TASKINA_MARUZ_ALAN"),
        N: ("NIP_AFET_TEHLIKELI_ALANLAR", "TASKINA_MARUZ_ALAN")}),
    "HEYELAN": ("Heyelan Alanı", {
        U: ("UIP_AFET_TEHLIKELI_ALANLAR", "HEYELAN_ALANI"),
        N: ("NIP_AFET_TEHLIKELI_ALANLAR", "KUTLE_HAREKETI_RISKLI_ALAN")}),
    "AFET": ("Afet Tehlikeli Alan", {
        U: ("UIP_AFET_TEHLIKELI_ALANLAR", "YAPI_YASAKLI_ALAN"),
        N: ("NIP_AFET_TEHLIKELI_ALANLAR", "YAPI_YASAKLI_ALAN")}),

    # --- Sinirlar ve cizgiler ---
    "ADAKENARI": ("Ada Kenarı (Önerilen)", {
        U: ("UIP_ADA_KENARI", "ONERILEN"),
        N: ("NIP_ADA_KENARI", None)}),
    "ADA_KENARI": ("Ada Kenarı (Önerilen)", {
        U: ("UIP_ADA_KENARI", "ONERILEN"),
        N: ("NIP_ADA_KENARI", None)}),
    "KADEME": ("Kademe Hattı", {
        U: ("UIP_ADA_KENARI", "KADEME_HATTI")}),
    "IFRAZ": ("İfraz Hattı", {
        U: ("UIP_ADA_KENARI", "IFRAZ_HATTI")}),
    "PLANONAMA": ("Plan (Onama) Sınırı", {
        U: ("UIP_PLAN_SINIRI", "PLAN"),
        N: ("NIP_PLAN_SINIRI", "PLAN"),
        C: ("CDP_PLAN_SINIRI", "PLAN")}),
    "ONAMA": ("Plan (Onama) Sınırı", {
        U: ("UIP_PLAN_SINIRI", "PLAN"),
        N: ("NIP_PLAN_SINIRI", "PLAN"),
        C: ("CDP_PLAN_SINIRI", "PLAN")}),
    "PLAN_SINIRI": ("Plan Sınırı", {
        U: ("UIP_PLAN_SINIRI", "PLAN"),
        N: ("NIP_PLAN_SINIRI", "PLAN"),
        C: ("CDP_PLAN_SINIRI", "PLAN")}),
    "PLAN_DEGISIKLIK": ("Plan Değişikliği Sınırı", {
        U: ("UIP_PLAN_DEGISIKLIK_SINIRI", None),
        N: ("NIP_PLAN_DEGISIKLIK_SINIRI", None),
        C: ("CDP_PLAN_DEGISIKLIK_SINIRI", None)}),
    "YAPIYAK": ("Yapı Yaklaşma Sınırı", {
        U: ("UIP_YAPI_YAKLASMA_SINIRI", None),
        N: ("MNIP_YAPI_YAKLASMA_SINIRI", None)}),
    "YAPI_YAKLASMA": ("Yapı Yaklaşma Sınırı", {
        U: ("UIP_YAPI_YAKLASMA_SINIRI", None),
        N: ("MNIP_YAPI_YAKLASMA_SINIRI", None)}),
    "KALDIRIM": ("Kaldırım", {
        U: ("UIP_DIGER_YOL_NESNELERI", "KALDIRIM"),
        N: ("MUIP_DIGER_YOL_NESNELERI", "KALDIRIM")}),
    "YAYA": ("Yaya Yolu", {
        U: ("UIP_YAYA_YOLU", None),
        N: ("MNIP_YAYA_YOLU", None)}),
    "REFUJ": ("Refüj", {
        U: ("UIP_DIGER_YOL_NESNELERI", "REFUJ"),
        N: ("MUIP_DIGER_YOL_NESNELERI", "REFUJ")}),
    "BISIKLET": ("Bisiklet Yolu", {
        U: ("UIP_BISIKLET_YOLU", None)}),
    "YOLORTA": ("Taşıt Yolu", {
        U: ("UIP_YOLORTA", None),
        N: ("NIP_YOLORTA", None)}),
    "YOL": ("Taşıt Yolu", {
        U: ("UIP_YOLORTA", None),
        N: ("NIP_YOLORTA", None)}),
    "ILCE_SINIRI": ("İlçe Sınırı", {
        U: ("UIP_ILCE_SINIRI", None),
        N: ("NIP_ILCE_SINIRI", None),
        C: ("CDP_ILCE_SINIRI", None)}),
    "ILCE": ("İlçe Sınırı", {
        U: ("UIP_ILCE_SINIRI", None),
        N: ("NIP_ILCE_SINIRI", None),
        C: ("CDP_ILCE_SINIRI", None)}),
    "IL_SINIRI": ("İl Sınırı", {
        U: ("UIP_IL_SINIRI", None),
        N: ("NIP_IL_SINIRI", None),
        C: ("CDP_IL_SINIRI", None)}),
    "MAHALLE": ("Mahalle Sınırı", {
        U: ("UIP_MAHALLE_SINIRI", None)}),
    "KOY_SINIRI": ("Köy Sınırı", {
        U: ("UIP_KOY_SINIRI", None),
        N: ("NIP_KOY_SINIRI", None)}),
    "MUCAVIR": ("Mücavir Alan Sınırı", {
        U: ("UIP_MUCAVIR_ALAN_SINIRI", None),
        N: ("NIP_MUCAVIR_ALAN_SINIRI", None),
        C: ("CDP_MUCAVIR_ALAN_SINIRI", None)}),
    "KIYI_KENAR": ("Kıyı Kenar Çizgisi", {
        U: ("UIP_KIYI_KENAR_CIZGISI", None),
        N: ("NIP_KIYI_KENAR_CIZGISI", None)}),
}

# Style-name family -> PlanGML upper group label used for layer grouping.
UST_GRUP_BY_FAMILY = {
    "KONUT": "KONUT ALANLARI",
    "MEVCUT_KONUT": "KONUT ALANLARI",
    "GELISME_KONUT": "KONUT ALANLARI",
    "DONUSUM_KONUT_ALANLARI": "KONUT ALANLARI",
    "KENTSEL_YERLESIK": "KONUT ALANLARI",
    "KENTSEL_GELISME_KONUT": "KONUT ALANLARI",
    "KIRSAL_YERLESIK_KONUT": "KONUT ALANLARI",
    "KENTSEL_CALISMA": "TİCARET VE ÇALIŞMA ALANLARI",
    "FONKSIYONLU_CALISMA": "TİCARET VE ÇALIŞMA ALANLARI",
    "ILAN_EDILEN_CLSMA_ALAN": "TİCARET VE ÇALIŞMA ALANLARI",
    "TURIZM_ALANI": "TİCARET VE ÇALIŞMA ALANLARI",
    "ACIK_YESIL_ALAN": "AÇIK VE YEŞİL ALANLAR",
    "ORMAN": "AÇIK VE YEŞİL ALANLAR",
    "MERA": "AÇIK VE YEŞİL ALANLAR",
    "SU_YUZEYI": "AÇIK VE YEŞİL ALANLAR",
    "SU_YUZEYI_CIZGI": "AÇIK VE YEŞİL ALANLAR",
    "EGITIM_TESIS_ALANI": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "SAGLIK_TESIS_ALANI": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "SOSYAL_KULTUREL_ALAN": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "IBADET_ALANI": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "TEKNIK_ALTYAPI": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "ENERJI_DAGITIM_DEPOLAMA": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "ATIKSU_TESIS": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "ICMESU_TESIS": "SOSYAL VE TEKNİK ALTYAPI ALANLARI",
    "KARAYOLU_TESISLERI": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "YOLORTA": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "YAYA_YOLU": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "DIGER_YOL_NESNELERI": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "BISIKLET_YOLU": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "DEMIRYOLU": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "ENERJI_NAKIL_HATTI": "ULAŞIM VE ALTYAPI GÜZERGAHLARI",
    "TARIM": "KORUMA VE ÖZEL ALANLAR",
    "SIT_ALANLARI": "KORUMA VE ÖZEL ALANLAR",
    "AFET_TEHLIKELI_ALANLAR": "KORUMA VE ÖZEL ALANLAR",
    "ASKERI_YSK_GUVENLIK_BLG": "KORUMA VE ÖZEL ALANLAR",
}
DEFAULT_UST_GRUP = "PLAN SINIRLARI VE KADASTRAL HATLAR"


def _text(el):
    return el.text.strip() if el is not None and el.text else None


def _css(parent, name):
    if parent is None:
        return None
    for p in parent.findall("sld:CssParameter", NS):
        if p.get("name") == name:
            return _text(p)
    return None


def _parse_float(val, default=None):
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _parse_dash(val):
    if not val:
        return None
    parts = [_parse_float(p) for p in val.replace(",", " ").split()]
    parts = [p for p in parts if p is not None and p >= 0]
    return parts or None


class SldCatalog:
    """All rules of every SLD in the archive, indexed by style name."""

    def __init__(self, zip_path: str):
        self.zip = zipfile.ZipFile(zip_path)
        self.styles = {}
        self.tarama_index = {}
        for name in self.zip.namelist():
            if name.startswith("__MACOSX"):
                continue
            base = os.path.basename(name)
            if "TaramaResim" in name and base.lower().endswith(".png"):
                self.tarama_index[base] = name
            if name.startswith("gs-data") and base.lower().endswith(".sld"):
                self._load_sld(base[:-4], name)

    def _load_sld(self, style_name: str, member: str):
        data = self.zip.read(member).decode("utf-8", errors="replace")
        root = ET.fromstring(data)
        rules = []
        for rule in root.findall(".//sld:Rule", NS):
            rules.append(self._parse_rule(rule))
        self.styles[style_name] = rules

    def _parse_rule(self, rule):
        out = {
            "title": _text(rule.find("sld:Title", NS)) or _text(rule.find("sld:Name", NS)),
        }
        ps = rule.find("sld:PolygonSymbolizer", NS)
        if ps is not None:
            fill = ps.find("sld:Fill", NS)
            poly = {}
            if fill is not None:
                poly["fill"] = _css(fill, "fill")
                poly["fill_opacity"] = _parse_float(_css(fill, "fill-opacity"), 1.0)
                gf = fill.find("sld:GraphicFill/sld:Graphic/sld:ExternalGraphic/sld:OnlineResource", NS)
                if gf is not None:
                    poly["tarama"] = gf.get(XLINK_HREF, "").rsplit("/", 1)[-1]
            stroke = ps.find("sld:Stroke", NS)
            if stroke is not None:
                poly["stroke"] = _css(stroke, "stroke")
                poly["stroke_width"] = _parse_float(_css(stroke, "stroke-width"))
            out["polygon"] = poly
        ls = rule.find("sld:LineSymbolizer", NS)
        if ls is not None:
            stroke = ls.find("sld:Stroke", NS)
            line = {}
            if stroke is not None:
                line["stroke"] = _css(stroke, "stroke")
                line["stroke_width"] = _parse_float(_css(stroke, "stroke-width"))
                line["dash"] = _parse_dash(_css(stroke, "stroke-dasharray"))
            out["line"] = line
        return out

    def find_rule(self, style_name: str, rule_title):
        rules = self.styles.get(style_name)
        if not rules:
            raise KeyError(f"style not found: {style_name}")
        if rule_title is None:
            return rules[0]
        for r in rules:
            if r["title"] == rule_title:
                return r
        raise KeyError(f"rule not found: {style_name} / {rule_title}")

    def resolve_tarama_name(self, png_name: str) -> str:
        if png_name in self.tarama_index:
            return png_name
        # The Ministry SLD set contains a bulk-edit typo: "40" -> "40m" inside
        # some uuid hrefs; the archive holds the untainted names.
        fixed = png_name.replace("40m", "40")
        if fixed in self.tarama_index:
            return fixed
        raise KeyError(f"tarama png not found in archive: {png_name}")

    def read_tarama(self, png_name: str) -> bytes:
        return self.zip.read(self.tarama_index[self.resolve_tarama_name(png_name)])


def image_dimensions(data: bytes):
    """PNG or BMP pixel size. The Ministry archive ships BMP bytes under a
    ``.png`` extension; Qt image readers detect the format from content, so the
    bytes are shipped untouched — only the size is needed for the raster fill."""
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    if len(data) >= 26 and data[:2] == b"BM":
        width, height = struct.unpack("<ii", data[18:26])
        return abs(int(width)), abs(int(height))
    return None


def resolve_entry(cat: SldCatalog, label, style_name, rule_title, shipped_pngs):
    rule = cat.find_rule(style_name, rule_title)
    entry = {"label": label, "style": style_name, "rule": rule["title"]}

    poly = rule.get("polygon")
    if poly:
        if poly.get("fill"):
            entry["fill"] = poly["fill"]
            entry["fill_opacity"] = poly.get("fill_opacity", 1.0)
        tarama = poly.get("tarama")
        if tarama:
            tarama = cat.resolve_tarama_name(tarama)
            data = cat.read_tarama(tarama)
            dims = image_dimensions(data)
            if dims:
                shipped_pngs[tarama] = data
                entry["tarama"] = tarama
                entry["tarama_size"] = list(dims)
        if poly.get("stroke"):
            entry["stroke"] = poly["stroke"]
            if poly.get("stroke_width") is not None:
                entry["stroke_width"] = poly["stroke_width"]

    line = rule.get("line")
    if line is not None:
        entry["line_color"] = line.get("stroke") or "#000000"
        width = line.get("stroke_width")
        entry["line_width"] = max(0.2, min(2.0, width)) if width else 0.4
        if line.get("dash"):
            entry["dash"] = line["dash"]

    family = style_name.split("_", 1)[1] if "_" in style_name else style_name
    entry["ust_grup"] = UST_GRUP_BY_FAMILY.get(family, DEFAULT_UST_GRUP)

    # The YOLORTA styles carry only width-driven cased-road symbolizers that do
    # not survive extraction; the official plan appearance of a road is a plain
    # white body with a dark casing.
    if "fill" not in entry and "tarama" not in entry and "line_color" not in entry:
        entry["fill"] = "#FFFFFF"
        entry["fill_opacity"] = 1.0
        entry["stroke"] = "#000000"
        entry["stroke_width"] = 0.25
        entry["line_color"] = "#000000"
        entry["line_width"] = 0.4
    return entry


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    zip_path = sys.argv[1]
    cat = SldCatalog(zip_path)
    print(f"Loaded {len(cat.styles)} SLD styles, "
          f"{len(cat.tarama_index)} tarama tiles from {zip_path}")

    shipped_pngs = {}
    catalog = {U: {}, N: {}, C: {}}
    for token, (label, plans) in MAPPING.items():
        for plan_type, (style_name, rule_title) in plans.items():
            entry = resolve_entry(cat, label, style_name, rule_title, shipped_pngs)
            catalog[plan_type][token] = entry

    os.makedirs(OUT_TARAMA_DIR, exist_ok=True)
    for name, data in sorted(shipped_pngs.items()):
        with open(os.path.join(OUT_TARAMA_DIR, name), "wb") as fh:
            fh.write(data)
    total_kb = sum(len(d) for d in shipped_pngs.values()) / 1024.0
    print(f"Wrote {len(shipped_pngs)} tarama tiles ({total_kb:.0f} KiB) "
          f"to {OUT_TARAMA_DIR}")

    buf = io.StringIO()
    buf.write('# -*- coding: utf-8 -*-\n')
    buf.write('"""Official Turkish e-Plan symbology catalog (generated file).\n\n')
    buf.write('Compiled from the public Ministry e-Plan plan gösterimleri SLD style set by\n')
    buf.write('``tools/compile_eplan_catalog.py`` — do not edit by hand; re-run the compiler.\n\n')
    buf.write('Maps normalized CAD tabaka tokens to resolved official style data per plan\n')
    buf.write('type: UIP (uygulama imar planı 1/1000), NIP (nazım imar planı 1/5000),\n')
    buf.write('CDP (çevre düzeni planı 1/25.000+). Tarama tiles referenced here are shipped\n')
    buf.write('under ``resources/eplan_tarama/``.\n\n')
    buf.write('Copyright (C) 2026 Yusuf Eminoğlu\n')
    buf.write('SPDX-License-Identifier: GPL-2.0-or-later\n')
    buf.write('"""\n\n')
    buf.write("EPLAN_PLAN_TYPES = (\"UIP\", \"NIP\", \"CDP\")\n\n")
    buf.write("EPLAN_CATALOG = ")
    import pprint
    buf.write(pprint.pformat(catalog, width=100, sort_dicts=True))
    buf.write("\n")
    with open(OUT_CATALOG, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(buf.getvalue())
    n_entries = sum(len(v) for v in catalog.values())
    print(f"Wrote {n_entries} catalog entries to {OUT_CATALOG}")


if __name__ == "__main__":
    main()
