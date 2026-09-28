"""Atomic, isolated GeoPackage generators for MPYY and Arazi Kullanımı."""

import json
import os
from pathlib import Path
import sqlite3
import uuid
import contextlib
from contextlib import closing
from osgeo import gdal, ogr, osr
from qgis.core import QgsCoordinateReferenceSystem

gdal.UseExceptions()

from .schema import (
    LAND_TABLES,
    LAND_USE_CLASSES,
    SAHA_CATI_KODLARI,
    SAHA_HASAR_KODLARI,
    SAHA_ISITMA_KODLARI,
    SAHA_NIZAM_KODLARI,
    SAHA_PARSEL_DURUM_KODLARI,
    SAHA_YAPI_CINS_KODLARI,
    SCHEMA_VERSION,
)


def _crs(value):
    crs = value if isinstance(value, QgsCoordinateReferenceSystem) else QgsCoordinateReferenceSystem(str(value))
    if not crs.isValid():
        raise ValueError('Geçerli bir KRS gereklidir')
    srs = osr.SpatialReference()
    if srs.SetFromUserInput(crs.authid() or crs.toWkt()) != 0:
        raise ValueError("GDAL seçilen KRS'yi okuyamıyor")
    return srs


def _quote(name: str) -> str:
    cleaned = name.replace('"', '').replace("'", "")
    return f'"{cleaned}"'







def _read_qml(rel_path: str) -> str:
    path = Path(__file__).resolve().parents[1] / rel_path
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


_SQL_AUDIT_INSERT = """
CREATE TRIGGER "__TRG__" AFTER INSERT ON "__TBL__"
WHEN NEW.olusturma_tarihi = '' OR NEW.olusturma_tarihi IS NULL
BEGIN
    UPDATE "__TBL__"
    SET olusturma_tarihi = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
        guncelleme_tarihi = strftime('%Y-%m-%dT%H:%M:%fZ','now')
    WHERE fid = NEW.fid;
END;
"""

_SQL_AUDIT_UPDATE = """
CREATE TRIGGER "__TRG__" AFTER UPDATE OF geom ON "__TBL__"
WHEN NEW.guncelleme_tarihi = OLD.guncelleme_tarihi OR NEW.guncelleme_tarihi IS NULL
BEGIN
    UPDATE "__TBL__"
    SET guncelleme_tarihi = strftime('%Y-%m-%dT%H:%M:%fZ','now')
    WHERE fid = NEW.fid;
END;
"""


def _create_audit_triggers(con: sqlite3.Connection, table: str, fields: dict) -> None:
    if "olusturma_tarihi" in fields:
        trg_name = f"audit_insert_{table}"
        sql_ins = _SQL_AUDIT_INSERT.replace("__TRG__", trg_name).replace("__TBL__", table)
        con.execute(sql_ins)
    if "guncelleme_tarihi" in fields:
        trg_name = f"audit_update_{table}"
        sql_upd = _SQL_AUDIT_UPDATE.replace("__TRG__", trg_name).replace("__TBL__", table)
        con.execute(sql_upd)


_SQL_SURVEY_INSERT = """
CREATE TRIGGER "__TRG__" AFTER INSERT ON "__TBL__"
BEGIN
    UPDATE "__TBL__"
    SET global_id = CASE WHEN NEW.global_id = '' OR NEW.global_id IS NULL
            THEN lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)), 2) || '-a' || substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)))
            ELSE NEW.global_id END,
        tarih = CASE WHEN NEW.tarih = '' OR NEW.tarih IS NULL
            THEN strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
            ELSE NEW.tarih END
    WHERE fid = NEW.fid;
END;
"""

_SQL_SURVEY_UPDATE = """
CREATE TRIGGER "__TRG__" AFTER UPDATE OF geom ON "__TBL__"
WHEN NEW.tarih = OLD.tarih OR NEW.tarih IS NULL
BEGIN
    UPDATE "__TBL__"
    SET tarih = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
    WHERE fid = NEW.fid;
END;
"""


def _create_survey_audit_triggers(con: sqlite3.Connection, table: str, fields: dict) -> None:
    if "global_id" in fields and "tarih" in fields:
        trg_ins = f"survey_insert_{table}"
        sql_ins = _SQL_SURVEY_INSERT.replace("__TRG__", trg_ins).replace("__TBL__", table)
        con.execute(sql_ins)
    if "tarih" in fields:
        trg_upd = f"survey_update_{table}"
        sql_upd = _SQL_SURVEY_UPDATE.replace("__TRG__", trg_upd).replace("__TBL__", table)
        con.execute(sql_upd)


def _create(output_path, crs, tables, kind, levels=()):
    output = Path(output_path).resolve()
    if output.exists():
        raise FileExistsError(str(output))
    if output.suffix.lower() != ".gpkg":
        raise ValueError('Çıktı .gpkg uzantısını kullanmalıdır')

    geometry_types = {
        "MultiPolygon": ogr.wkbMultiPolygon,
        "MultiLineString": ogr.wkbMultiLineString,
        "Point": ogr.wkbPoint,
    }

    staging = output.parent / (".mpyy-" + uuid.uuid4().hex)
    staging.mkdir(parents=True, exist_ok=True)
    staged = staging / "dataset.gpkg"

    try:
        ds = ogr.GetDriverByName("GPKG").CreateDataSource(str(staged))
        if ds is None:
            raise RuntimeError('GeoPackage oluşturulamadı')

        srs = _crs(crs)
        for table, (geom_type, _) in tables.items():
            layer = ds.CreateLayer(
                table,
                srs,
                geometry_types[geom_type],
                options=["GEOMETRY_NAME=geom", "SPATIAL_INDEX=YES"],
            )
            if layer is None:
                raise RuntimeError('Katman oluşturulamadı: ' + table)
        ds = None

        with closing(sqlite3.connect(staged)) as con, con:
            con.execute("PRAGMA foreign_keys=ON")

            # 1. Metadata table
            con.execute(
                "CREATE TABLE mpyy_metadata (dataset_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL, workspace_kind TEXT NOT NULL, plan_levels TEXT NOT NULL)"
            )
            con.execute(
                "INSERT INTO mpyy_metadata VALUES (?,?,?,?)",
                (str(uuid.uuid4()), SCHEMA_VERSION, kind, ",".join(levels)),
            )

            # 2. Layer styles table (OGC GPKG standard style table)
            con.execute(
                """CREATE TABLE IF NOT EXISTS layer_styles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    f_table_catalog TEXT,
                    f_table_schema TEXT,
                    f_table_name TEXT NOT NULL,
                    f_geometry_column TEXT,
                    styleName TEXT NOT NULL,
                    styleQML TEXT,
                    styleSLD TEXT,
                    useAsDefault BOOLEAN,
                    description TEXT,
                    owner TEXT,
                    ui TEXT,
                    update_time DATETIME DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                )"""
            )
            con.execute(
                "INSERT OR IGNORE INTO gpkg_contents(table_name,data_type,identifier) VALUES ('layer_styles','attributes','QGIS katman stilleri')"
            )

            # 3. If Planning workspace, add catalogs & lookups
            if kind == "ARAZI_KULLANIMI":
                # 1. Non-TUCBS Urban Land Use Code Dictionary (Mevcut Arazi Kullanımı Sözlüğü)
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_kullanim_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL,
                        ana_grup TEXT NOT NULL,
                        renk_hex TEXT NOT NULL,
                        aciklama TEXT
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_kullanim_kodlari','attributes','Land use / field survey use code dictionary')"
                )
                from .schema import LAND_USE_CLASSES
                con.executemany(
                    "INSERT INTO saha_kullanim_kodlari (kod, ad, ana_grup, renk_hex, aciklama) VALUES (?,?,?,?,?)",
                    LAND_USE_CLASSES,
                )

                # 2. Building physical condition lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_yapi_durum_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_yapi_durum_kodlari','attributes','Building physical condition codes')"
                )
                con.executemany(
                    "INSERT INTO saha_yapi_durum_kodlari (kod, ad) VALUES (?,?)",
                    [
                        ("İYİ", 'İyi durumda / bakımlı'),
                        ("ORTA", 'Orta durumda / basit onarım gerektirir'),
                        ("KÖTÜ", 'Kötü durumda / esaslı onarım gerektirir'),
                        ("METRUK", 'Metruk / terk edilmiş bina'),
                        ("HARABE", 'Yıkık / harabe yapı'),
                        ("İNŞAAT", 'İnşaat Halindeki Yapı'),
                    ],
                )

                # 3. Building structural system lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_yapi_cins_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_yapi_cins_kodlari','attributes','Building structural system codes')"
                )
                con.executemany(
                    "INSERT INTO saha_yapi_cins_kodlari (kod, ad) VALUES (?,?)",
                    SAHA_YAPI_CINS_KODLARI,
                )

                # 3b. Building layout / zoning order lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_nizam_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_nizam_kodlari','attributes','Building arrangement codes')"
                )
                con.executemany(
                    "INSERT INTO saha_nizam_kodlari (kod, ad) VALUES (?,?)",
                    SAHA_NIZAM_KODLARI,
                )

                # 3c. Parcel development state lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_parsel_durum_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_parsel_durum_kodlari','attributes','Parcel occupation status codes')"
                )
                con.executemany(
                    "INSERT INTO saha_parsel_durum_kodlari (kod, ad) VALUES (?,?)",
                    SAHA_PARSEL_DURUM_KODLARI,
                )


                # 4. Road hierarchy classification lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_yol_tip_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL,
                        oneri_genislik_m REAL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_yol_tip_kodlari','attributes','Road hierarchy type codes')"
                )
                con.executemany(
                    "INSERT INTO saha_yol_tip_kodlari (kod, ad, oneri_genislik_m) VALUES (?,?,?)",
                    [
                        ("ANA_ARTER", "Ana Arter / Bulvar (1. Derece)", 30.0),
                        ("TOPLAYICI_YOL", 'Toplayıcı Yol (2. Derece)', 15.0),
                        ("SERVIS_YOLU", 'Servis / İmar Yolu (3. Derece)', 10.0),
                        ("YAYA_YOLU", 'Yaya Yolu / Yayalaştırılmış Bölge', 8.0),
                        ("CIKMAZ_SOKAK", 'Çıkmaz Sokak', 6.0),
                        ("KIRSAL_YOL", 'Kırsal / Tarla Yolu', 5.0),
                    ],
                )

                # 5. Land ownership classification lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_mulkiyet_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_mulkiyet_kodlari','attributes','Ownership type codes')"
                )
                con.executemany(
                    "INSERT INTO saha_mulkiyet_kodlari (kod, ad) VALUES (?,?)",
                    [
                        ("ÖZEL", 'Özel Mülkiyet (Şahıs / Şirket)'),
                        ("BELEDİYE", 'Belediye Mülkiyeti'),
                        ("HAZİNE", 'Maliye Hazinesi'),
                        ("VAKIF", 'Vakıflar Genel Müdürlüğü'),
                        ("KAMU_DİĞER", 'Diğer Kamu Kurumları (TCDD, DSİ vb.)'),
                        ("TESCİL_HARİCİ", "Tescil Harici / Yol / Terkin"),
                    ],
                )

                # 6. Building quality lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_yapi_kalite_kodlari (
                        kod INTEGER PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_yapi_kalite_kodlari','attributes','Building quality classes')"
                )
                con.executemany(
                    "INSERT INTO saha_yapi_kalite_kodlari (kod, ad) VALUES (?,?)",
                    [
                        (1, '1 - Çok Kötü / Yıkılacak'),
                        (2, '2 - Kötü / Esaslı Onarım'),
                        (3, '3 - Orta / Bakımlı'),
                        (4, '4 - İyi / Yeni'),
                        (5, '5 - Çok İyi / Lüks'),
                    ],
                )

                # 7. Road paving surface lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_yol_kaplama_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_yol_kaplama_kodlari','attributes','Road surface material codes')"
                )
                con.executemany(
                    "INSERT INTO saha_yol_kaplama_kodlari (kod, ad) VALUES (?,?)",
                    [
                        ("ASFALT_BSK", 'Asfalt (Sıcak/BSK)'),
                        ("ASFALT_SATHI", "Asfalt (Sathi)"),
                        ("KILIT_PARKE", 'Kilit Parke Taşı'),
                        ("BETON", "Beton"),
                        ("GRANIT_KUP", 'Granit Küptaş'),
                        ("ARNAVUT", 'Arnavut Kaldırımı'),
                        ("STABILIZE", 'Stabilize (Çakıl)'),
                        ("TOPRAK", "Toprak (Tesviye)"),
                        ("HAM_YOL", 'Ham Yol (İz)'),
                    ],
                )

                # 8. Protection status lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_koruma_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_koruma_kodlari','attributes','Protection and heritage designation codes')"
                )
                con.executemany(
                    "INSERT INTO saha_koruma_kodlari (kod, ad) VALUES (?,?)",
                    [
                        ("YOK", 'Herhangi Bir Sit / Koruma Statüsü Yok'),
                        ("KENTSEL_SİT", 'Kentsel Sit Alanı İçi'),
                        ("DOĞAL_SİT", 'Doğal Sit Alanı İçi'),
                        ("ARKEOLOJİK_SİT", 'Arkeolojik Sit Alanı İçi'),
                        ("TESCİLLİ_YAPI", 'Tescilli Kültür Varlığı / Yapı'),
                    ],
                )

                # 9. Roof types lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_cati_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_cati_kodlari','attributes','Building roof type codes')"
                )
                con.executemany(
                    "INSERT INTO saha_cati_kodlari (kod, ad) VALUES (?,?)",
                    SAHA_CATI_KODLARI,
                )

                # 10. Heating types lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_isitma_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_isitma_kodlari','attributes','Building heating type codes')"
                )
                con.executemany(
                    "INSERT INTO saha_isitma_kodlari (kod, ad) VALUES (?,?)",
                    SAHA_ISITMA_KODLARI,
                )

                # 11. Damage status lookup table
                con.execute(
                    """CREATE TABLE IF NOT EXISTS saha_hasar_kodlari (
                        kod TEXT PRIMARY KEY,
                        ad TEXT NOT NULL
                    )"""
                )
                con.execute(
                    "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES ('saha_hasar_kodlari','attributes','Building damage condition codes')"
                )
                con.executemany(
                    "INSERT INTO saha_hasar_kodlari (kod, ad) VALUES (?,?)",
                    SAHA_HASAR_KODLARI,
                )

                # 12. Embed official QML styles for Arazi Kullanımı layers
                arazi_styles = [
                    ("parsel_saha", "forms/arazi/01_parsel_saha.qml"),
                    ("Tucbs_1000_alan", "forms/arazi/02_Tucbs_1000_alan.qml"),
                    ("Tucbs_1000_Cizgi", "forms/arazi/03_Tucbs_1000_Cizgi.qml"),
                    ("yapi_saha", "forms/arazi/04_yapi_saha.qml"),
                    ("yol_saha", "forms/arazi/05_yol_saha.qml"),
                ]
                for target_layer, qml_file in arazi_styles:
                    qml_text = _read_qml(qml_file)
                    if qml_text:
                        con.execute(
                            """INSERT INTO layer_styles(f_table_name, styleName, styleQML, useAsDefault, description)
                               VALUES (?, ?, ?, 1, ?)""",
                            (target_layer, target_layer, qml_text, f"{target_layer} saha anket stili"),
                        )

            # 4. Add columns, indexes and triggers to spatial tables
            for table, (geometry, fields) in tables.items():
                for field, definition in fields.items():
                    con.execute(f"ALTER TABLE {_quote(table)} ADD COLUMN {_quote(field)} {definition}")

                # Unique index on global_id
                if "global_id" in fields:
                    con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {_quote('idx_' + table + '_gid')} ON {_quote(table)}({_quote('global_id')})")

                if "catalog_id" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_cat')} ON {_quote(table)}({_quote('catalog_id')})")

                if "fonksiyon_kodu" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_fonk')} ON {_quote(table)}({_quote('fonksiyon_kodu')})")

                if "ADA" in fields and "PARSEL" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_ada_parsel')} ON {_quote(table)}({_quote('ADA')}, {_quote('PARSEL')})")

                if "P_FONK" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_p_fonk')} ON {_quote(table)}({_quote('P_FONK')})")

                if "B_FONK" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_b_fonk')} ON {_quote(table)}({_quote('B_FONK')})")

                if "Y_TIP" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_y_tip')} ON {_quote(table)}({_quote('Y_TIP')})")

                if "MAHALLE" in fields:
                    con.execute(f"CREATE INDEX IF NOT EXISTS {_quote('idx_' + table + '_mahalle')} ON {_quote(table)}({_quote('MAHALLE')})")

                if table.startswith("mpyy_"):
                    _create_audit_triggers(con, table, fields)
                elif table in ("parsel_saha", "yapi_saha", "yol_saha"):
                    _create_survey_audit_triggers(con, table, fields)

            # 5. Summary and reporting SQL views (registered in gpkg_contents as attribute layers)
            if kind == "ARAZI_KULLANIMI":
                views_arazi = [
                    (
                        "v_saha_parsel_kullanim_ozet",
                        """CREATE VIEW IF NOT EXISTS v_saha_parsel_kullanim_ozet AS
                        SELECT 
                            COALESCE(P_FONK, 'BELİRTİLMEMİŞ') AS kullanim_fonksiyonu,
                            COUNT(*) AS parsel_sayisi,
                            ROUND(SUM(COALESCE(alan_m2, 0)), 2) AS toplam_alan_m2,
                            ROUND(AVG(COALESCE(alan_m2, 0)), 2) AS ortalama_alan_m2,
                            SUM(COALESCE(P_NUFUS, 0)) AS tahmini_nufus,
                            SUM(COALESCE(P_BAGIMSIZ_BOLUM, 0)) AS toplam_bagimsiz_bolum,
                            SUM(COALESCE(P_YAPI_ADET, 0)) AS toplam_bina_sayisi
                        FROM parsel_saha
                        GROUP BY P_FONK
                        ORDER BY toplam_alan_m2 DESC""",
                        'Saha Parsel Kullanım Fonksiyonu Dağılım Özeti',
                    ),
                    (
                        "v_saha_yapi_kat_ve_durum_ozet",
                        """CREATE VIEW IF NOT EXISTS v_saha_yapi_kat_ve_durum_ozet AS
                        SELECT 
                            COALESCE(B_FONK, 'BELİRTİLMEMİŞ') AS yapi_fonksiyonu,
                            COALESCE(B_KAT, 0) AS kat_adedi,
                            COALESCE(B_DURUM, 'BELİRSİZ') AS yapi_durumu,
                            COALESCE(B_YAPI_CINSI, 'BELİRSİZ') AS yapi_cinsi,
                            COUNT(*) AS bina_adedi,
                            ROUND(SUM(COALESCE(alan_m2, 0)), 2) AS toplam_taban_alani_m2,
                            ROUND(AVG(COALESCE(B_YAS, 0)), 1) AS ortalama_bina_yasi
                        FROM yapi_saha
                        GROUP BY B_FONK, B_KAT, B_DURUM, B_YAPI_CINSI""",
                        'Saha Yapı Kat, Durum ve Taşıyıcı Cins Dağılım Özeti',
                    ),
                    (
                        "v_saha_mahalle_bilancosu",
                        """CREATE VIEW IF NOT EXISTS v_saha_mahalle_bilancosu AS
                        SELECT 
                            COALESCE(MAHALLE, 'BELİRSİZ') AS mahalle_adi,
                            COUNT(DISTINCT ADA || '-' || PARSEL) AS parsel_adedi,
                            ROUND(SUM(COALESCE(alan_m2, 0)), 2) AS toplam_parsel_alani_m2,
                            SUM(COALESCE(P_NUFUS, 0)) AS toplam_nufus,
                            SUM(COALESCE(P_BAGIMSIZ_BOLUM, 0)) AS toplam_bagimsiz_bolum
                        FROM parsel_saha
                        GROUP BY MAHALLE
                        ORDER BY mahalle_adi""",
                        'Mahalle Bazlı Parsel ve Nüfus Bilançosu',
                    ),
                    (
                        "v_saha_yol_envanteri",
                        """CREATE VIEW IF NOT EXISTS v_saha_yol_envanteri AS
                        SELECT 
                            COALESCE(Y_TIP, 'DİĞER') AS yol_kademesi,
                            COALESCE(Y_KAPLAMA, 'BELİRSİZ') AS kaplama_turu,
                            COUNT(*) AS segment_sayisi,
                            ROUND(SUM(COALESCE(uzunluk_m, 0)), 2) AS toplam_uzunluk_m,
                            ROUND(SUM(COALESCE(uzunluk_m, 0)) / 1000.0, 3) AS toplam_uzunluk_km,
                            ROUND(AVG(COALESCE(Y_GENISLIK, 0)), 2) AS ortalama_genislik_m
                        FROM yol_saha
                        GROUP BY Y_TIP, Y_KAPLAMA
                        ORDER BY toplam_uzunluk_m DESC""",
                        'Yol Ağı Hiyerarşi ve Kaplama Envanteri',
                    ),
                ]
                for view_name, view_sql, view_ident in views_arazi:
                    con.execute(view_sql)
                    con.execute(
                        "INSERT INTO gpkg_contents(table_name,data_type,identifier) VALUES (?, 'attributes', ?)",
                        (view_name, view_ident),
                    )

            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError('Veritabanı bütünlüğü doğrulanamadı: ' + str(integrity))

        # Rename atomic staging file to target
        if os.name == "nt":
            os.replace(staged, output)
        else:
            os.rename(staged, output)

    finally:
        for item in staging.glob("*"):
            with contextlib.suppress(Exception):
                item.unlink(missing_ok=True)
        with contextlib.suppress(Exception):
            staging.rmdir()

    return str(output)


def create_land_use_workspace(output_path, crs):
    """Create an independent Arazi Kullanımı GeoPackage containing TUCBS and field survey tables."""
    return _create(output_path, crs, LAND_TABLES, "ARAZI_KULLANIMI", ())


def read_dataset_info(path):
    """Read metadata from a PlanX MPYY GeoPackage."""
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as con:
        row = con.execute(
            "SELECT dataset_id, schema_version, workspace_kind, plan_levels FROM mpyy_metadata"
        ).fetchone()
    if not row or row[1] != SCHEMA_VERSION:
        raise ValueError('Desteklenmeyen veya geçersiz MPYY şema sürümü')
    uuid.UUID(row[0])
    return {
        "dataset_id": row[0],
        "schema_version": row[1],
        "workspace_kind": row[2],
        "plan_levels": tuple(filter(None, row[3].split(","))),
    }


def read_dataset_id(path):
    return read_dataset_info(path)["dataset_id"]
