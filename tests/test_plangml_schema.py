# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""test_plangml_schema — official identity of a UİP tabaka.

These columns are supposed to hold the Ministry's codes, so a wrong value here
survives export and looks authoritative. The refusals are as much the point as
the matches.
"""
from __future__ import annotations

import unittest

from zero2cadgis.core.mpyy_catalog import MPYY_ALIASES, MPYY_TABAKA
from zero2cadgis.core.plangml_schema import TabakaIdentity, lookup_tabaka


class TestExactMatches(unittest.TestCase):

    def test_konut_carries_the_official_codes(self):
        identity = lookup_tabaka("PL_KONUT")
        self.assertIsNotNone(identity)
        self.assertEqual(identity.ust_grup_id, "112000")
        self.assertEqual(identity.ust_grup_adi, "KONUT ALANLARI / YERLEŞİM ALANLARI")
        self.assertEqual(identity.fonksiyon_kodu, "112002")
        self.assertEqual(identity.fonksiyon_adi, "YERLEŞİK KONUT ALANI")
        self.assertEqual(identity.matched_as, "exact")

    def test_gelisme_konut_is_a_different_function_in_the_same_group(self):
        yerlesik = lookup_tabaka("PL_KONUT")
        gelisme = lookup_tabaka("PL_GELISME_KONUT")
        self.assertEqual(yerlesik.ust_grup_id, gelisme.ust_grup_id)
        self.assertNotEqual(yerlesik.fonksiyon_kodu, gelisme.fonksiyon_kodu)
        self.assertEqual(gelisme.fonksiyon_kodu, "112001")

    def test_a_spread_of_tabaka_from_a_real_drawing(self):
        expected = {
            "PL_PARK": ("101000", "101013"),
            "PL_AGACLANDIRILACAK": ("101000", "101001"),
            "PL_ILKOKUL_ALANI": ("105000", "105003"),
            "PL_CAMI": ("108000", "108001"),
            "PL_TICARET": ("110000", "110018"),
            "PL_KUCUK_SANAYI": ("110000", "110010"),
            "PL_HASTANE": ("115000", "115002"),
            "SNR_PLANONAMA": ("122000", "122109"),
            "SNR_YAPIYAK": ("122000", "122110"),
            "ADAKENARI": ("130000", "130100"),
            "KALDIRIM": ("130000", "130103"),
            "HAT_KADEME": ("132000", "132101"),
        }
        for tabaka, (grup, fonksiyon) in expected.items():
            with self.subTest(tabaka=tabaka):
                identity = lookup_tabaka(tabaka)
                self.assertIsNotNone(identity, f"{tabaka} not found")
                self.assertEqual(identity.ust_grup_id, grup)
                self.assertEqual(identity.fonksiyon_kodu, fonksiyon)

    def test_name_folding(self):
        # Turkish letters, case and separators must not defeat a lookup.
        for spelling in ("pl_konut", "PL_KONUT ", "Pl_Konut"):
            with self.subTest(spelling=spelling):
                self.assertEqual(lookup_tabaka(spelling).fonksiyon_kodu, "112002")


class TestAliases(unittest.TestCase):
    """Local spellings for a function the catalog already defines."""

    def test_known_local_spellings(self):
        expected = {
            "PL_BELEDIYE": ("PL_BHA", "110004"),
            "PL_OYUN_ALANI": ("PL_COCUK_BAHCESI", "101003"),
            "PL_SAGLIK_OCAGI": ("PL_AILE_SAGL_MER", "115001"),
            "PL_SOSYOKULTUREL": ("PL_SOSYAL_TESIS", "116014"),
            "PL_SPOR_TESISLERI": ("PL_ACIK_SPOR_TES", "116001"),
            "PL_DERE": ("PL_SU_YUZEYI", "117005"),
        }
        for local, (official, code) in expected.items():
            with self.subTest(local=local):
                identity = lookup_tabaka(local)
                self.assertIsNotNone(identity)
                self.assertEqual(identity.tabaka, official)
                self.assertEqual(identity.fonksiyon_kodu, code)
                self.assertEqual(identity.matched_as, "alias")

    def test_every_alias_points_at_a_real_tabaka(self):
        for local, official in MPYY_ALIASES.items():
            with self.subTest(local=local):
                self.assertIn(official, MPYY_TABAKA)

    def test_no_alias_shadows_an_official_tabaka(self):
        for local in MPYY_ALIASES:
            with self.subTest(local=local):
                self.assertNotIn(local, MPYY_TABAKA)


class TestRefusals(unittest.TestCase):
    """No codes are invented for something the catalog does not define."""

    def test_cad_helper_layers_have_no_official_identity(self):
        for name in ("SM_AGAC", "YAZI_PLAN", "YAZI_FONKSIYON", "ROL_CEPHE",
                     "Z_ADAPARSEL_PL", "SM_HMAKS", "SNR_GIS"):
            with self.subTest(tabaka=name):
                self.assertIsNone(lookup_tabaka(name))

    def test_ambiguous_local_names_are_left_alone(self):
        # Deliberately not aliased: no unambiguous official counterpart.
        for name in ("PL_KDKCA", "PL_REFUJ", "REFÜJ", "SNR_FONKSIYON"):
            with self.subTest(tabaka=name):
                self.assertIsNone(lookup_tabaka(name))

    def test_empty_input(self):
        self.assertIsNone(lookup_tabaka(None))
        self.assertIsNone(lookup_tabaka(""))
        self.assertIsNone(lookup_tabaka("   "))


class TestCatalogIntegrity(unittest.TestCase):

    def test_catalog_is_populated(self):
        self.assertGreater(len(MPYY_TABAKA), 200)

    def test_every_record_is_complete(self):
        for tabaka, record in MPYY_TABAKA.items():
            with self.subTest(tabaka=tabaka):
                for key in ("ust_grup_id", "ust_grup_adi",
                            "fonksiyon_kodu", "fonksiyon_adi", "geometri"):
                    self.assertTrue(record.get(key), f"{tabaka}.{key} empty")
                self.assertTrue(record["ust_grup_id"].isdigit())
                self.assertTrue(record["fonksiyon_kodu"].isdigit())
                self.assertIn(record["geometri"], ("POLYGON", "LINE"))

    def test_function_codes_sit_inside_their_group(self):
        # 112002 belongs to group 112000: the first three digits agree.
        for tabaka, record in MPYY_TABAKA.items():
            with self.subTest(tabaka=tabaka):
                self.assertEqual(record["fonksiyon_kodu"][:3],
                                 record["ust_grup_id"][:3])

    def test_lookup_returns_the_documented_shape(self):
        self.assertIsInstance(lookup_tabaka("PL_PARK"), TabakaIdentity)


if __name__ == "__main__":
    unittest.main()
