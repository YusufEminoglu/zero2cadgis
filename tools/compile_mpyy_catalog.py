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
# ---------------------------------------------------------------------------
ALIASES = {
    "PL_BELEDIYE": "PL_BHA",                 # 110004 Belediye Hizmet Alanı
    "PL_OYUN_ALANI": "PL_COCUK_BAHCESI",     # 101003 Çocuk Bahçesi VE Oyun Alanı
    "PL_SAGLIK_OCAGI": "PL_AILE_SAGL_MER",   # 115001 Aile Sağlığı Merkezi
    "PL_SOSYOKULTUREL": "PL_SOSYAL_TESIS",   # 116014 Sosyal Tesis Alanı
    "PL_SPOR_TESISLERI": "PL_ACIK_SPOR_TES",  # 116001 Açık Spor Tesisi Alanı
    "PL_DERE": "PL_SU_YUZEYI",               # 117005 Su Yüzeyi
    "PL_HAL": "PL_TOPTAN_TICARET",           # 110024 Toptan Ticaret Alanı
    "PL_MEZARLIK_ALANI": "PL_MEZARLIK",      # 101011 Mezarlık Alanı
    "PL_ORMAN": "PL_ORMAN_ALANI",            # 103008 Orman Alanı
    "PL_MERA": "PL_MERA_ALANI",              # 103006 Mera Alanı
    "PL_ZEYTINLIK": "PL_ZEYTINLIK_ALAN",     # 103011 Zeytinlik Alan
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
