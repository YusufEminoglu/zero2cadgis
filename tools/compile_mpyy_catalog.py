# -*- coding: utf-8 -*-
"""Offline compiler: MPYY UİP tabaka catalog -> embedded plugin table.

Reads the Mekânsal Planlar Yapım Yönetmeliği UİP database compiled and
maintained by Yusuf Eminoğlu (``MpyyUipDb_2026_02_27.gpkg``) and emits
``core/mpyy_catalog.py``: the official identity of every UİP tabaka — its upper
group and code, and its function and code — so the PlanGML schema columns of an
imported plan carry the standard values.

The source tables are ``uipPolygonTable`` and ``uipLineTable``, both with
columns ``id1, ust_konu_grup, id2, uip_fonksiyon, id3, uip_tabaka``.

Development-only: excluded from the released zip via ``.zipignore`` and re-run
by hand whenever the Ministry publishes a new database.

Usage:
    py -3 tools/compile_mpyy_catalog.py "C:/path/to/MpyyUipDb_2026_02_27.gpkg"

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import io
import os
import pprint
import sqlite3
import sys

# Everything this tool reports is Turkish; a cp1252 console would kill the run
# on the first İ rather than print the report it exists to print.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
OUT_CATALOG = os.path.join(PLUGIN_ROOT, "core", "mpyy_catalog.py")

SOURCE_TABLES = (("uipPolygonTable", "POLYGON"), ("uipLineTable", "LINE"))
NO_TABAKA = {"", "YOK", "NULL", "-"}

# ---------------------------------------------------------------------------
# Local spellings seen in real municipal drawings, mapped to the official
# tabaka they are the same function as.
#
# Deliberately short. Each entry has to be a spelling of *exactly* the same
# function, because the codes it pulls in end up in columns that are supposed
# to hold the Ministry's values — a plausible-looking guess there is worse than
# an empty cell. Tabaka with no unambiguous official counterpart (PL_KDKCA,
# PL_REFUJ, a generic PL_TURIZM, PL_YATILI_BOLGE_OKUL, SNR_FONKSIYON) are left
# out on purpose and simply resolve to nothing.
#
# Not needed here: spellings that only drop the ``PL_`` prefix or add/drop the
# ``_ALANI`` ending — ``plangml_schema.lookup_tabaka`` derives those itself, and
# a test fails if an alias here disagrees with what it derives.
#
# Also left out on purpose, each for a stated reason:
#   generic -> one specific function (invents a precision the drawing lacks):
#     EGITIM (ilkokul? lise?), IBADET (cami? kilise?), TARIM (4 official
#     kinds), PL_ENERJI, PL_KAMU*, AKARYAKIT (servis istasyonu 110002 or
#     ürün depolama 106001), SNR_PLAN (onama or değişiklik sınırı);
#   a different function: BISIKLET_YOLU is not 109001 BİSİKLET PARKI,
#     PL_KATLI_OTOPARK is not 109003 GENEL OTOPARK (109100 exists, untabaka'd);
#   ambiguous abbreviation: KOP (Kamu Ortaklık Payı as often as Küçük Sanayi);
#   roads: the Ministry defines 133002-133005 (taşıt, bisiklet, yaya yolu)
#     with NO tabaka name, so no local road layer can claim one.
# ---------------------------------------------------------------------------
ALIASES = {
    "ADA_KENARI": "ADAKENARI",                  # 130100 Adakenari
    "AGACLANDIRILACAK_ALAN": "PL_AGACLANDIRILACAK",# 101001 Ağaçlandirilacak Alan
    "AILE_SAGLIGI": "PL_AILE_SAGL_MER",         # 115001 Ai̇le Sağliği Merkezi̇
    "AKARSU": "PL_SU_YUZEYI",                   # 117005 Su Yüzeyi̇
    "AKARYAKIT_LPG": "PL_BAKIM_AKARYAKIT",      # 110002 Akaryakit Ve Servi̇s İstasyonu Alani
    "ARITMA": "PL_ATIKSU_TESISI",               # 117001 Atiksu Tesi̇sleri̇ Alani (Aritma, Terfi̇ Merkezi̇)
    "ASKERI_YASAK": "KST_ASKERI_YASAK",         # 114001 Askeri̇ Yasak Ve Güvenli̇k Bölgesi̇
    "BELEDIYE_HIZMET": "PL_BHA",                # 110004 Beledi̇ye Hi̇zmet Alani
    "BELEDIYE_HIZMET_ALANI": "PL_BHA",          # 110004 Beledi̇ye Hi̇zmet Alani
    "BELEDIYE_SINIRI": "SNR_BELEDIYE",          # 121101 Beledi̇ye Siniri
    "DENIZ": "PL_SU_YUZEYI",                    # 117005 Su Yüzeyi̇
    "DERE": "PL_SU_YUZEYI",                     # 117005 Su Yüzeyi̇
    "ETAPLAMA_SINIRI": "SNR_ETAPLAMA",          # 122103 Etaplama Siniri
    "GECEKONDU_ONLEME": "SNR_GOB",              # 114105 Gecekondu Önleme Bölgesi̇ Siniri
    "GOL": "PL_SU_YUZEYI",                      # 117005 Su Yüzeyi̇
    "HEYELAN_ALANI": "KST_HEYELAN",             # 102001 Heyelan Alani
    "IFRAZ_HATTI": "HAT_IFRAZ",                 # 132102 İfraz Hatti
    "ILCE_SINIRI": "SNR_ILCE",                  # 121103 İlçe Siniri
    "IL_SINIRI": "SNR_IL",                      # 121102 İl Siniri
    "IMAR_HAKKI_AKT_SINIRI": "SNR_IMAR_HAKKI_AKT",# 122105 İmar Hakki Aktarim Alani Siniri
    "KADEME_HATTI": "HAT_KADEME",               # 132101 Kademe Hatti
    "KATI_ATIK": "PL_KATI_ATIK_TESISI",         # 117003 Kati Atik Tesi̇sleri̇ Alani (Boşaltma, Bertaraf, İşleme, Transfer Ve Depolama)
    "KENTSEL_TASARIM_SINIRI": "SNR_KENTSEL_TASARIM",# 122106 Kentsel Tasarim Projesi̇ Siniri
    "KIYI_KENAR": "SNR_KIYI_KENAR",             # 114106 Kiyi Kenar Çi̇zgi̇si̇
    "KIYI_KENAR_CIZGISI": "SNR_KIYI_KENAR",     # 114106 Kiyi Kenar Çi̇zgi̇si̇
    "KOY_SINIRI": "SNR_KOY",                    # 121104 Köy Siniri
    "KSA": "PL_KUCUK_SANAYI",                   # 110010 Küçük Sanayi̇ Alani
    "KST_ONLEMLI": "KST_ONLEMLI_ALAN",          # 102002 Önlemli̇ Alan
    "LOJISTIK": "PL_LOJISTIK_TESIS",            # 110011 Loji̇sti̇k Tesi̇s Alani
    "MAHALLE_SINIRI": "SNR_MAHALLE",            # 121105 Mahalle Siniri
    "MESIRE": "PL_MESIRE_YERI",                 # 101009 Mesi̇re Yeri̇
    "MESKUN_KONUT": "PL_KONUT",                 # 112002 Yerleşi̇k Konut Alani
    "MUCAVIR_ALAN": "SNR_MUCAVIR",              # 121106 Mücavi̇r Alan Siniri
    "MUCAVIR_ALAN_SINIRI": "SNR_MUCAVIR",       # 121106 Mücavi̇r Alan Siniri
    "NEHIR": "PL_SU_YUZEYI",                    # 117005 Su Yüzeyi̇
    "ONLEMLI_ALAN": "KST_ONLEMLI_ALAN",         # 102002 Önlemli̇ Alan
    "ORGANIZE_SANAYI": "PL_OSB",                # 114003 Organi̇ze Sanayi̇ Bölgesi̇
    "OYUN_ALANI": "PL_COCUK_BAHCESI",           # 101003 Çocuk Bahçesi̇ Ve Oyun Alani
    "PLAN_DEGISIKLIGI": "SNR_PLAN_DEGISIKLIGI", # 122108 Plan Deği̇şi̇kli̇ği̇ Onama Siniri
    "PLAN_DEGISIKLIK": "SNR_PLAN_DEGISIKLIGI",  # 122108 Plan Deği̇şi̇kli̇ği̇ Onama Siniri
    "PLAN_ONAMA": "SNR_PLANONAMA",              # 122109 Plan Onama Siniri
    "PLAN_ONAMA_SINIRI": "SNR_PLANONAMA",       # 122109 Plan Onama Siniri
    "PL_ACIK_OTOPARK": "PL_OTOPARK",            # 109003 Genel Otopark Alani
    "PL_AGACLANDIRILACAK_ALAN": "PL_AGACLANDIRILACAK",# 101001 Ağaçlandirilacak Alan
    "PL_AILE_SAGLIGI": "PL_AILE_SAGL_MER",      # 115001 Ai̇le Sağliği Merkezi̇
    "PL_AKARSU": "PL_SU_YUZEYI",                # 117005 Su Yüzeyi̇
    "PL_AKARYAKIT_LPG": "PL_BAKIM_AKARYAKIT",   # 110002 Akaryakit Ve Servi̇s İstasyonu Alani
    "PL_ANAOKUL": "PL_ANAOKULU",                # 105001 Anaokulu Alani
    "PL_ARITMA": "PL_ATIKSU_TESISI",            # 117001 Atiksu Tesi̇sleri̇ Alani (Aritma, Terfi̇ Merkezi̇)
    "PL_ATIKSU": "PL_ATIKSU_TESISI",            # 117001 Atiksu Tesi̇sleri̇ Alani (Aritma, Terfi̇ Merkezi̇)
    "PL_BELEDIYE": "PL_BHA",                    # 110004 Beledi̇ye Hi̇zmet Alani
    "PL_BELEDIYE_HIZMET": "PL_BHA",             # 110004 Beledi̇ye Hi̇zmet Alani
    "PL_DENIZ": "PL_SU_YUZEYI",                 # 117005 Su Yüzeyi̇
    "PL_DERE": "PL_SU_YUZEYI",                  # 117005 Su Yüzeyi̇
    "PL_EGITIM_ILK": "PL_ILKOKUL_ALANI",        # 105003 İlkokul Alani
    "PL_EGITIM_ILKOKUL": "PL_ILKOKUL_ALANI",    # 105003 İlkokul Alani
    "PL_EGITIM_LISE": "PL_LISE_ALANI",          # 105004 Li̇se Alani
    "PL_EGITIM_MESLEK": "PL_TEKNIK_OGRETIM",    # 105008 Mesleki̇ Ve Tekni̇k Öğreti̇m Tesi̇si̇ Alani
    "PL_EGITIM_ORTA": "PL_ORTAOKUL_ALANI",      # 105005 Ortaokul Alani
    "PL_ENDUSTRI_MESLEK": "PL_TEKNIK_OGRETIM",  # 105008 Mesleki̇ Ve Tekni̇k Öğreti̇m Tesi̇si̇ Alani
    "PL_GECEKONDU_ONLEME": "SNR_GOB",           # 114105 Gecekondu Önleme Bölgesi̇ Siniri
    "PL_GOL": "PL_SU_YUZEYI",                   # 117005 Su Yüzeyi̇
    "PL_HAL": "PL_TOPTAN_TICARET",              # 110024 Toptan Ti̇caret Alani
    "PL_HEYELAN": "KST_HEYELAN",                # 102001 Heyelan Alani
    "PL_KATI_ATIK": "PL_KATI_ATIK_TESISI",      # 117003 Kati Atik Tesi̇sleri̇ Alani (Boşaltma, Bertaraf, İşleme, Transfer Ve Depolama)
    "PL_KONUT_GELISME": "PL_GELISME_KONUT",     # 112001 Geli̇şme Konut Alani
    "PL_KSA": "PL_KUCUK_SANAYI",                # 110010 Küçük Sanayi̇ Alani
    "PL_KULTUR": "PL_KULTUREL_TESIS",           # 116005 Kültürel Tesi̇s Alani
    "PL_KULTUREL": "PL_KULTUREL_TESIS",         # 116005 Kültürel Tesi̇s Alani
    "PL_LOJISTIK": "PL_LOJISTIK_TESIS",         # 110011 Loji̇sti̇k Tesi̇s Alani
    "PL_MESIRE": "PL_MESIRE_YERI",              # 101009 Mesi̇re Yeri̇
    "PL_MESIRE_ALANI": "PL_MESIRE_YERI",        # 101009 Mesi̇re Yeri̇
    "PL_MESKUN_KONUT": "PL_KONUT",              # 112002 Yerleşi̇k Konut Alani
    "PL_NEHIR": "PL_SU_YUZEYI",                 # 117005 Su Yüzeyi̇
    "PL_ORGANIZE_SANAYI": "PL_OSB",             # 114003 Organi̇ze Sanayi̇ Bölgesi̇
    "PL_OYUN_ALANI": "PL_COCUK_BAHCESI",        # 101003 Çocuk Bahçesi̇ Ve Oyun Alani
    "PL_SAGLIK": "PL_SAGLIK_TESISI",            # 115004 Sağlik Tesi̇si̇ Alani
    "PL_SAGLIK_OCAGI": "PL_AILE_SAGL_MER",      # 115001 Ai̇le Sağliği Merkezi̇
    "PL_SANAYI": "PL_SANAYI_TESIS",             # 110014 Sanayi̇ Tesi̇s Alani
    "PL_SANAYI_ALANI": "PL_SANAYI_TESIS",       # 110014 Sanayi̇ Tesi̇s Alani
    "PL_SOSYAL": "PL_SOSYAL_TESIS",             # 116014 Sosyal Tesi̇s Alani
    "PL_SOSYAL_TESISI": "PL_SOSYAL_TESIS",      # 116014 Sosyal Tesi̇s Alani
    "PL_SOSYOKULTUREL": "PL_SOSYAL_TESIS",      # 116014 Sosyal Tesi̇s Alani
    "PL_SPOR_TESISLERI": "PL_ACIK_SPOR_TES",    # 116001 Açik Spor Tesi̇si̇ Alani
    "PL_SUYUZEYI": "PL_SU_YUZEYI",              # 117005 Su Yüzeyi̇
    "PL_TASKIN": "KST_TASKIN",                  # 102003 Taşkina Maruz Alan
    "PL_TERMINAL": "PL_OTOGAR",                 # 109002 Termi̇nal (Otogar)
    "PL_TICARET_KONUT": "PL_KONUT_TICARET",     # 110009 Ti̇caret - Konut Alani
    "PL_TICK": "PL_KONUT_TICARET",              # 110009 Ti̇caret - Konut Alani
    "PL_TICKONUT": "PL_KONUT_TICARET",          # 110009 Ti̇caret - Konut Alani
    "PL_TOPLU_ISYERI": "PL_TOPLU_ISYERLERI",    # 110023 Toplu İşyerleri̇
    "PL_TURIZM_TICARET": "PL_TICARET_TURIZM",   # 110022 Ti̇caret - Turi̇zm Alani
    "PL_UNIVERSITE": "PL_YUKSEKOGRETIM",        # 105009 Yüksek Öğreti̇m Alani
    "PL_ZEYTINLIK": "PL_ZEYTINLIK_ALAN",        # 103011 Zeyti̇nli̇k Alan
    "SAGLIK": "PL_SAGLIK_TESISI",               # 115004 Sağlik Tesi̇si̇ Alani
    "SAGLIK_OCAGI": "PL_AILE_SAGL_MER",         # 115001 Ai̇le Sağliği Merkezi̇
    "SAGLIK_TESIS_ALANI": "PL_SAGLIK_TESISI",   # 115004 Sağlik Tesi̇si̇ Alani
    "SAHIL_SERIDI": "SNR_SAHIL_SERIDI",         # 114200 Sahi̇l Şeri̇di̇
    "SANAYI": "PL_SANAYI_TESIS",                # 110014 Sanayi̇ Tesi̇s Alani
    "SANAYI_ALANI": "PL_SANAYI_TESIS",          # 110014 Sanayi̇ Tesi̇s Alani
    "SNR_ONAMA": "SNR_PLANONAMA",               # 122109 Plan Onama Siniri
    "SNR_PLANDEGISIK": "SNR_PLAN_DEGISIKLIGI",  # 122108 Plan Deği̇şi̇kli̇ği̇ Onama Siniri
    "SNR_PLAN_DEG": "SNR_PLAN_DEGISIKLIGI",     # 122108 Plan Deği̇şi̇kli̇ği̇ Onama Siniri
    "SNR_PLAN_DEGISIK": "SNR_PLAN_DEGISIKLIGI", # 122108 Plan Deği̇şi̇kli̇ği̇ Onama Siniri
    "SNR_PLAN_ONAMA": "SNR_PLANONAMA",          # 122109 Plan Onama Siniri
    "SNR_PLAN_ONAMA_ILAVE": "SNR_PLANONAMA",    # 122109 Plan Onama Siniri
    "SNR_YAPIYAKLASMA": "SNR_YAPIYAK",          # 122110 Yapi Yaklaşma Siniri
    "SNR_YAPI_YAK": "SNR_YAPIYAK",              # 122110 Yapi Yaklaşma Siniri
    "SNR_YAPI_YAKLASMA": "SNR_YAPIYAK",         # 122110 Yapi Yaklaşma Siniri
    "SUYUZEYI": "PL_SU_YUZEYI",                 # 117005 Su Yüzeyi̇
    "TASKIN_ALANI": "KST_TASKIN",               # 102003 Taşkina Maruz Alan
    "TERMINAL": "PL_OTOGAR",                    # 109002 Termi̇nal (Otogar)
    "TICARET_KONUT": "PL_KONUT_TICARET",        # 110009 Ti̇caret - Konut Alani
    "TICK": "PL_KONUT_TICARET",                 # 110009 Ti̇caret - Konut Alani
    "TICKONUT": "PL_KONUT_TICARET",             # 110009 Ti̇caret - Konut Alani
    "TOPLU_ISYERI": "PL_TOPLU_ISYERLERI",       # 110023 Toplu İşyerleri̇
    "TURIZM_TICARET": "PL_TICARET_TURIZM",      # 110022 Ti̇caret - Turi̇zm Alani
    "ULKE_SINIRI": "SNR_ULKE",                  # 121107 Ülke Siniri
    "UNIVERSITE": "PL_YUKSEKOGRETIM",           # 105009 Yüksek Öğreti̇m Alani
    "YAPI_YAKLASMA": "SNR_YAPIYAK",             # 122110 Yapi Yaklaşma Siniri
    "YAPI_YAKLASMA_SINIRI": "SNR_YAPIYAK",      # 122110 Yapi Yaklaşma Siniri
    "YAPI_YASAKLI_ALAN": "KST_YAPI_YASAK",      # 102004 Yapi Yasakli Alan
    "YOL_KALDIRIM": "KALDIRIM",                 # 130103 Kaldirim
    "ZEYTINLIK": "PL_ZEYTINLIK_ALAN",           # 103011 Zeyti̇nli̇k Alan
}


def read_catalog(gpkg_path: str):
    connection = sqlite3.connect(gpkg_path)
    cursor = connection.cursor()
    catalog, duplicates, skipped = {}, [], 0

    for table, family in SOURCE_TABLES:
        rows = cursor.execute(
            f"SELECT id1, ust_konu_grup, id2, uip_fonksiyon, id3, uip_tabaka "
            f"FROM {table}").fetchall()
        for id1, grup, id2, fonksiyon, id3, tabaka in rows:
            name = (tabaka or "").strip().upper()
            if name in NO_TABAKA:
                skipped += 1
                continue
            record = {
                "ust_grup_id": str(id1).strip(),
                "ust_grup_adi": (grup or "").strip(),
                "fonksiyon_kodu": str(id2).strip(),
                "fonksiyon_adi": (fonksiyon or "").strip(),
                "geometri": family,
            }
            # id3 repeats id2 throughout the published database; assert it so a
            # future release that diverges is noticed instead of silently lost.
            if str(id3).strip() != record["fonksiyon_kodu"]:
                record["detay_kodu"] = str(id3).strip()
            if name in catalog:
                duplicates.append((name, catalog[name]["fonksiyon_adi"],
                                   record["fonksiyon_adi"]))
                continue                      # first definition wins
            catalog[name] = record

    connection.close()
    return catalog, duplicates, skipped


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    gpkg_path = sys.argv[1]

    catalog, duplicates, skipped = read_catalog(gpkg_path)
    print(f"Read {len(catalog)} tabaka from {os.path.basename(gpkg_path)} "
          f"({skipped} rows carry no tabaka name)")
    if duplicates:
        print(f"{len(duplicates)} tabaka defined twice; kept the first:")
        for name, kept, dropped in duplicates:
            print(f"  {name}: kept '{kept}', dropped '{dropped}'")

    unknown = sorted(t for t in ALIASES.values() if t not in catalog)
    if unknown:
        raise SystemExit(f"ALIASES point at tabaka missing from the catalog: {unknown}")
    print(f"{len(ALIASES)} local spellings aliased onto official tabaka")

    groups = {r["ust_grup_id"]: r["ust_grup_adi"] for r in catalog.values()}
    print(f"{len(groups)} upper groups")

    buf = io.StringIO()
    buf.write('# -*- coding: utf-8 -*-\n')
    buf.write('"""Official MPYY UİP tabaka catalog (generated file).\n\n')
    buf.write('Compiled by ``tools/compile_mpyy_catalog.py`` from the Mekânsal Planlar\n')
    buf.write('Yapım Yönetmeliği UİP database published by the T.C. Çevre, Şehircilik ve\n')
    buf.write('İklim Değişikliği Bakanlığı. Do not edit by hand; re-run the compiler.\n\n')
    buf.write('Gives each UİP tabaka its official identity — upper group and code, function\n')
    buf.write('and code — so the PlanGML schema columns of an imported plan carry the\n')
    buf.write('Ministry\'s own values. ``MPYY_ALIASES`` maps local spellings seen in real\n')
    buf.write('municipal drawings onto the official tabaka they are the same function as.\n\n')
    buf.write('The codes and names below are the official standard and are not claimed as\n')
    buf.write('original work; see THIRD_PARTY_NOTICES.md. The compiler, the alias list and\n')
    buf.write('this catalog\'s structure are:\n\n')
    buf.write('Copyright (C) 2026 Yusuf Eminoğlu\n')
    buf.write('SPDX-License-Identifier: GPL-2.0-or-later\n')
    buf.write('"""\n\n')
    buf.write("MPYY_TABAKA = ")
    buf.write(pprint.pformat(catalog, width=100, sort_dicts=True))
    buf.write("\n\nMPYY_ALIASES = ")
    buf.write(pprint.pformat(ALIASES, width=100, sort_dicts=True))
    buf.write("\n")

    with open(OUT_CATALOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(buf.getvalue())
    print(f"Wrote {OUT_CATALOG}")


if __name__ == "__main__":
    main()
