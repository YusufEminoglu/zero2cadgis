# -*- coding: utf-8 -*-
"""test_zoning_text_extractor — Unit tests for Turkish zoning parameter parser.

Tests regex parsing of building parameters (nizam, kat adedi, emsal, TAKS, Yençok,
çekme mesafeleri) from CAD plan drawings.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import unittest

from zero2cadgis.core.zoning_text_extractor import (
    ZoningParameters,
    parse_zoning_parameters,
    assign_zoning_parameters_to_polygons,
)


class TestZoningTextExtractor(unittest.TestCase):
    """Unit tests for regex parsing of Turkish zoning parameters."""

    def test_parse_nizam_and_kat(self):
        cases = [
            (["A-3"], "AYRIK", 3),
            (["B-4"], "BITISIK", 4),
            (["BLOK-5"], "BLOK", 5),
            (["BL-6"], "BLOK", 6),
            (["İ-3"], "IKIZ", 3),
            (["IKIZ-2"], "IKIZ", 2),
            (["A/4"], "AYRIK", 4),
            (["AYRIK-5"], "AYRIK", 5),
            (["BİTİŞİK-3"], "BITISIK", 3),
            (["S-4"], "SERBEST", 4),
            (["SERBEST"], "SERBEST", None),
        ]
        for texts, expected_nizam, expected_kat in cases:
            with self.subTest(texts=texts):
                p = parse_zoning_parameters(texts)
                self.assertEqual(p.yapi_duzeni, expected_nizam)
                self.assertEqual(p.kat_adedi, expected_kat)

    def test_parse_emsal_and_kaks(self):
        cases = [
            (["E=1.50"], 1.50),
            (["E: 1.25"], 1.25),
            (["E=0,75"], 0.75),
            (["KAKS=2.07"], 2.07),
            (["EMSAL: 1.75"], 1.75),
            (["EMSAL=0.8"], 0.8),
        ]
        for texts, expected_emsal in cases:
            with self.subTest(texts=texts):
                p = parse_zoning_parameters(texts)
                self.assertIsNotNone(p.emsal_kaks)
                self.assertAlmostEqual(p.emsal_kaks, expected_emsal, places=2)

    def test_parse_taks(self):
        cases = [
            (["TAKS:0.35"], 0.35),
            (["TAKS = 0.40"], 0.40),
            (["TAKS: 0,25"], 0.25),
            (["TAKS=0.50"], 0.50),
        ]
        for texts, expected_taks in cases:
            with self.subTest(texts=texts):
                p = parse_zoning_parameters(texts)
                self.assertIsNotNone(p.taks)
                self.assertAlmostEqual(p.taks, expected_taks, places=2)

    def test_parse_yencok_and_hmax(self):
        cases = [
            (["Yençok=15.50m"], 15.50, "15.5m"),
            (["YENÇOK: 12.50"], 12.50, "12.5m"),
            (["YENCOK=21.50"], 21.50, "21.5m"),
            (["Hmax: 12.50"], 12.50, "12.5m"),
            (["H_MAX = 18.50M"], 18.50, "18.5m"),
            (["H=9.50"], 9.50, "9.5m"),
        ]
        for texts, expected_h, expected_yencok in cases:
            with self.subTest(texts=texts):
                p = parse_zoning_parameters(texts)
                self.assertAlmostEqual(p.yapi_yuksekligi, expected_h, places=2)
                self.assertEqual(p.yencok, expected_yencok)

    def test_parse_setbacks(self):
        p1 = parse_zoning_parameters(["Ön: 5.00m", "Yan: 3.00", "Arka: 3.00m"])
        self.assertEqual(p1.on_bahce, 5.0)
        self.assertEqual(p1.yan_bahce, 3.0)
        self.assertEqual(p1.arka_bahce, 3.0)

        # Setback triplet
        p2 = parse_zoning_parameters(["5/3/3"])
        self.assertEqual(p2.on_bahce, 5.0)
        self.assertEqual(p2.yan_bahce, 3.0)
        self.assertEqual(p2.arka_bahce, 3.0)

    def test_combined_realistic_block_annotation(self):
        annotations = [
            "A-4",
            "E=1.60",
            "TAKS:0.40",
            "Yençok=12.50m",
            "5/3/3",
        ]
        p = parse_zoning_parameters(annotations)
        self.assertTrue(p.has_any)
        self.assertEqual(p.yapi_duzeni, "AYRIK")
        self.assertEqual(p.kat_adedi, 4)
        self.assertAlmostEqual(p.emsal_kaks, 1.60)
        self.assertAlmostEqual(p.taks, 0.40)
        self.assertAlmostEqual(p.yapi_yuksekligi, 12.50)
        self.assertEqual(p.on_bahce, 5.0)
        self.assertEqual(p.yan_bahce, 3.0)
        self.assertEqual(p.arka_bahce, 3.0)

        d = p.as_attribute_dict()
        self.assertEqual(d["YapiDuzeni"], "AYRIK")
        self.assertEqual(d["KatAdedi"], 4)
        self.assertEqual(d["EmsalKaks"], 1.60)
        self.assertEqual(d["Taks"], 0.40)
        self.assertEqual(d["YapiYuksekligi"], 12.50)
        self.assertIn("A-4", d["PlanNotu"])

    def test_empty_and_noise_handling(self):
        p = parse_zoning_parameters(["", "   ", "NOT: BILGI", "DETAY TABLO"])
        self.assertFalse(p.has_any)
        self.assertEqual(len(p.raw_texts), 2)

    def test_parse_cadastral_ada_parsel(self):
        from zero2cadgis.core.zoning_text_extractor import parse_cadastral_numbers

        # Slash format
        ada, parsel = parse_cadastral_numbers("101/5")
        self.assertEqual(ada, "101")
        self.assertEqual(parsel, "5")

        # Explicit keywords
        ada2, parsel2 = parse_cadastral_numbers("Ada: 2045, Parsel: 12")
        self.assertEqual(ada2, "2045")
        self.assertEqual(parsel2, "12")

        # In zoning parameter parsing
        p = parse_zoning_parameters(["A-3", "E=1.20", "154/8"])
        self.assertEqual(p.ada_no, "154")
        self.assertEqual(p.parsel_no, "8")
        self.assertEqual(p.yapi_duzeni, "AYRIK")

    def test_parse_road_widths(self):
        from zero2cadgis.core.zoning_text_extractor import parse_road_width

        self.assertEqual(parse_road_width("10.00"), 10.0)
        self.assertEqual(parse_road_width("12.00m"), 12.0)
        self.assertEqual(parse_road_width("15 m"), 15.0)
        self.assertEqual(parse_road_width("7.00 m."), 7.0)
        # Bare integers are not widths: on FOÇA.NCZ they were pole numbers
        # ("3") and contour/spot-height labels ("20", "25") next to road lines.
        self.assertIsNone(parse_road_width("20"))
        self.assertIsNone(parse_road_width("3"))
        self.assertIsNone(parse_road_width("125.43"))
        self.assertEqual(parse_road_width("YOL: 12m"), 12.0)
        self.assertEqual(parse_road_width("EN KESİT 15"), 15.0)
        self.assertIsNone(parse_road_width("0.50"))
        self.assertIsNone(parse_road_width("A-3"))
        self.assertIsNone(parse_road_width("E=1.50"))

    def test_assign_zoning_empty_layer_safe(self):
        # Should exit gracefully with 0 when layer or points are empty
        self.assertEqual(assign_zoning_parameters_to_polygons(None, []), 0)
        self.assertEqual(assign_zoning_parameters_to_polygons(object(), []), 0)

    def test_assign_road_widths_safety(self):
        from zero2cadgis.core.zoning_text_extractor import assign_road_widths_to_lines
        self.assertEqual(assign_road_widths_to_lines(None, []), 0)
        self.assertEqual(assign_road_widths_to_lines(object(), []), 0)

    def test_noise_layer_detection(self):
        from zero2cadgis.core.cad_engine import is_helper_or_noise_layer
        noise_names = [
            "CIZPEN", "CIZ_PEN", "PINDEX", "P_INDEX", "GRID_PINDEX", "PINDEX_GRID",
            "GRIDPINDEX", "PAFTA_GRID", "PAFTA_INDEX", "PAFTA_INDEKS", "KAREYAJ",
            "plan_PINDEX_Point", "proje_CIZPEN_Line", "pafta_grid_Line", "CAD_DRAFT",
            "KOORDINAT", "ANTET", "LEJANT", "LEGEND",
        ]
        for name in noise_names:
            with self.subTest(name=name):
                self.assertTrue(is_helper_or_noise_layer(name), f"Expected {name} to be identified as noise")

        clean_names = [
            "PL_KONUT", "PL_PARK", "PL_TICARET", "PL_EGITIM", "YOL", "TASIT_YOLU",
            "ADA_KENARI", "SNR_PLANONAMA", "112000_KONUT_Polygon",
        ]
        for name in clean_names:
            with self.subTest(name=name):
                self.assertFalse(is_helper_or_noise_layer(name), f"Expected {name} to NOT be noise")


    def test_disagreeing_texts_leave_the_value_empty(self):
        # A zone holding two parcels holds two ada/parsel numbers; a zone with
        # two blocks may say A-3 and A-5. First-come would invent a value.
        p = parse_zoning_parameters(["A-3", "A-5", "163/8", "164/2", "E=1.50"])
        self.assertEqual(p.yapi_duzeni, "AYRIK")
        self.assertIsNone(p.kat_adedi)
        self.assertIsNone(p.ada_no)
        self.assertIsNone(p.parsel_no)
        self.assertAlmostEqual(p.emsal_kaks, 1.50)
        agreed = parse_zoning_parameters(["A-3", "A-3", "163/8"])
        self.assertEqual((agreed.kat_adedi, agreed.ada_no, agreed.parsel_no), (3, "163", "8"))

    def test_plan_notu_is_bounded_and_deduplicated(self):
        p = parse_zoning_parameters(["NOT"] * 50 + [f"T{i}" for i in range(500)])
        self.assertEqual(p.raw_texts.count("NOT"), 1)
        self.assertLessEqual(len(p.as_attribute_dict()["PlanNotu"]), 1000)

    def test_boundary_tabaka_are_not_zoning_targets(self):
        from zero2cadgis.core.zoning_text_extractor import is_boundary_tabaka
        for name in ("SNR_PLANONAMA", "SNR_PLAN_ONAMA", "SNR_BELEDIYE", "PLAN_ONAMA_SINIRI"):
            with self.subTest(name=name):
                self.assertTrue(is_boundary_tabaka(name))
        for name in ("PL_KONUT", "ADAKENARI", None, "", "CIZPEN"):
            with self.subTest(name=name):
                self.assertFalse(is_boundary_tabaka(name))

    def test_official_tabaka_are_never_noise(self):
        from zero2cadgis.core.cad_engine import is_helper_or_noise_layer
        from zero2cadgis.core.mpyy_catalog import MPYY_ALIASES, MPYY_TABAKA
        # SNR_PLAN_ONAMA contains ONAMA, KST_SULAK_TAMPON contains TAMPON:
        # hiding either hides a legally binding boundary.
        for name in list(MPYY_TABAKA) + list(MPYY_ALIASES):
            with self.subTest(name=name):
                self.assertFalse(is_helper_or_noise_layer(name))
        self.assertTrue(is_helper_or_noise_layer("CIZPEN"))
        self.assertTrue(is_helper_or_noise_layer("PAFTA_GRID"))
        # the cephe setback notation of a UIP is plan content, not a helper layer
        self.assertFalse(is_helper_or_noise_layer("ROL_CEPHE"))


    def test_netcad_smart_object_values_become_the_same_notation(self):
        from zero2cadgis.core.zoning_text_extractor import notation_texts
        self.assertEqual(notation_texts({"nizam": "BİTİŞİK", "kat": "4"}), ["B-4"])
        self.assertEqual(notation_texts({"nizam": "AYRIK", "kat": "5", "txtOn": "7", "txtYan": "5"}),
                         ["A-5", "ÖN=7", "YAN=5"])
        # choiceType 1 = TAKS/KAKS, 0 = Emsal: only the chosen pair is stated
        self.assertEqual(notation_texts({"choiceType": "1", "taks": "0.3", "kaks": "1.2", "emsal": "9"}),
                         ["TAKS=0.3", "KAKS=1.2"])
        self.assertEqual(notation_texts({"choiceType": "0", "emsal": "1.6", "taks": "9"}), ["EMSAL=1.6"])
        self.assertEqual(notation_texts({"hmax": "4", "HmaxType": "Kat"}), ["KAT=4"])
        self.assertEqual(notation_texts({"genislik": "12"}), ["YOL=12"])
        p = parse_zoning_parameters(notation_texts({"choiceType": "1", "taks": "0.3", "kaks": "1.2", "hmax": "9.5"}))
        d = p.as_attribute_dict()
        self.assertEqual((d["Taks"], d["EmsalKaks"], d["YapiYuksekligi"]), (0.3, 1.2, 9.5))
        # a stated value is an MPYY "Deger"; an unstated one is left to the planner
        self.assertEqual((d["TaksTip"], d["EmsalKaksTip"], d["YapiYuksekligiTip"]), ("Deger", "Deger", "Deger"))
        self.assertEqual(parse_zoning_parameters(["A-3"]).as_attribute_dict()["TaksTip"], "")

    def test_each_smart_object_becomes_one_notation_point_where_it_was_drawn(self):
        from types import SimpleNamespace
        from zero2cadgis.core.plan_notation import notation_points

        def smart(properties, xy, tabaka="SM_YAPILASMA"):
            corners = [SimpleNamespace(x=xy[0] + dx, y=xy[1] + dy) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            return SimpleNamespace(properties=properties, coordinates=corners, layer_name=tabaka)

        points = notation_points([
            smart({"nizam": "AYRIK", "kat": "4", "txtOn": "5", "txtYan": "3"}, (100, 200)),
            smart({"choiceType": "1", "taks": "0.30", "kaks": "1.20"}, (130, 200)),
            smart({"genislik": "15"}, (300, 400), "SM_YOL"),
            smart({"unrelated": "x"}, (0, 0)),                              # nothing to show
            SimpleNamespace(properties={}, coordinates=[SimpleNamespace(x=1, y=1)], layer_name="X"),
        ])
        self.assertEqual(len(points), 3)
        nizam, taks, road = points
        self.assertEqual((nizam.x, nizam.y), (100, 200))                       # the object's own place
        self.assertEqual(nizam.values, {"YapiDuzeni": "Ayrik", "KatAdedi": 4,
                                        "OnBahceMesafesi": 5.0, "YanBahceMesafesi": 3.0})
        self.assertEqual(taks.values, {"Taks": 0.30, "TaksTip": "Deger", "EmsalKaks": 1.20, "EmsalKaksTip": "Deger"})
        self.assertEqual((road.road_width, road.values, road.tabaka), (15.0, {}, "SM_YOL"))


if __name__ == "__main__":
    unittest.main()
