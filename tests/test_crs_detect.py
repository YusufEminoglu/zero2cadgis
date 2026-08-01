# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""test_crs_detect — naming the CRS of a Netcad drawing.

Every EPSG code asserted here was read out of the PROJ database, and each maps
to exactly one (datum, central meridian, false easting) triple. Getting one
wrong silently places the data hundreds of metres — or a whole zone — away, so
the refusals matter as much as the matches.
"""
from __future__ import annotations

import unittest

from zero2cadgis.core.crs_detect import (
    ED50_GK,
    ED50_TM,
    LABELS,
    TUREF_GK,
    TUREF_TM,
    TURKISH_CENTRAL_MERIDIANS,
    detect_crs,
)

# Bahçesaray (Van), a real 1/1000 drawing: 6-digit easting, no zone prefix.
BAHCESARAY = [(558866.402, 4205522.694), (583661.982, 4233664.606),
              (570000.0, 4220000.0)]
# İzmir sits on central meridian 27 / UTM zone 35.
IZMIR = [(490000.0, 4250000.0), (512000.0, 4238000.0)]


class TestRealDrawing(unittest.TestCase):

    def test_bahcesaray_is_turef_tm42(self):
        result = detect_crs("ITRF / 3 / Zone 42", BAHCESARAY)
        self.assertEqual(result.epsg, 5258)
        self.assertEqual(result.label, "TUREF / TM42")
        self.assertEqual(result.confidence, "high")
        self.assertTrue(result)

    def test_netcad_srs_id_is_never_used_as_an_epsg_code(self):
        # 'SRS=7936' is Netcad's own id; EPSG:7936 is something else entirely.
        result = detect_crs("ITRF / 3 / Zone 42", BAHCESARAY)
        self.assertNotEqual(result.epsg, 7936)


class TestDatumSeparation(unittest.TestCase):
    """Same ground, same coordinates — only the drawing's datum tells them apart."""

    def test_izmir_across_datums_and_projections(self):
        cases = [
            ("ITRF / 3 / Zone 27", 5253, "TUREF / TM27"),
            ("ED50 / 3 / Zone 27", 2319, "ED50 / TM27"),
            ("WGS84 / UTM / Zone 35", 32635, "WGS 84 / UTM zone 35N"),
            ("ED50 / UTM / Zone 35", 23035, "ED50 / UTM zone 35N"),
        ]
        for text, epsg, label in cases:
            with self.subTest(projection=text):
                result = detect_crs(text, IZMIR)
                self.assertEqual(result.epsg, epsg)
                self.assertEqual(result.label, label)

    def test_datum_missing_is_refused_rather_than_guessed(self):
        result = detect_crs("3 / Zone 42", BAHCESARAY)
        self.assertIsNone(result.epsg)
        self.assertEqual(result.confidence, "none")
        self.assertIn("datum", result.reason.lower())


class TestZoneForms(unittest.TestCase):

    def test_zone_index_and_central_meridian_both_read(self):
        by_cm = detect_crs("ITRF / 3 / Zone 42", BAHCESARAY)
        by_index = detect_crs("ITRF / 3 / Zone 14", BAHCESARAY)
        self.assertEqual(by_cm.epsg, 5258)
        self.assertEqual(by_index.epsg, 5258)

    def test_zone_prefixed_easting_selects_the_gauss_kruger_code(self):
        result = detect_crs("ITRF / 3 / Zone 14", [(14558866.0, 4205522.0)])
        self.assertEqual(result.epsg, 5274)
        self.assertIn("Gauss-Kruger zone 14", result.label)

    def test_plain_easting_selects_the_tm_code(self):
        result = detect_crs("ITRF / 3 / Zone 14", [(558866.0, 4205522.0)])
        self.assertEqual(result.epsg, 5258)
        self.assertIn("TM42", result.label)

    def test_coordinates_win_when_they_contradict_the_text(self):
        result = detect_crs("ITRF / 3 / Zone 14", [(11558866.0, 4205522.0)])
        self.assertEqual(result.epsg, 5271)          # zone 11, not 14
        self.assertIn("easting encodes zone 11", result.reason)


class TestRefusals(unittest.TestCase):
    """An unsure guess puts the data in the wrong place; refusing does not."""

    def test_no_hints_at_all(self):
        result = detect_crs(None, [(558866.0, 4205522.0)])
        self.assertIsNone(result.epsg)
        self.assertFalse(result)

    def test_zone_outside_the_turkish_set(self):
        result = detect_crs("ITRF / 3 / Zone 99", BAHCESARAY)
        self.assertIsNone(result.epsg)

    def test_utm_zone_outside_turkey(self):
        result = detect_crs("WGS84 / UTM / Zone 12", IZMIR)
        self.assertIsNone(result.epsg)

    def test_no_coordinates_and_no_text(self):
        self.assertIsNone(detect_crs(None, []).epsg)
        self.assertIsNone(detect_crs("", None).epsg)


class TestSofterSignals(unittest.TestCase):

    def test_datum_assumed_only_when_the_zone_is_certain(self):
        # The easting states the zone outright, so only the datum is a guess.
        result = detect_crs(None, [(14558866.0, 4205522.0)])
        self.assertEqual(result.epsg, 5274)
        self.assertEqual(result.confidence, "medium")
        self.assertIn("TUREF", result.reason)

    def test_geographic_coordinates_recognized(self):
        result = detect_crs("ITRF / 3 / Zone 42", [(29.0, 41.0), (30.1, 40.2)])
        self.assertEqual(result.epsg, 4326)

    def test_northing_outside_turkey_downgrades_confidence(self):
        result = detect_crs("ITRF / 3 / Zone 42", [(558866.0, 1200000.0)])
        self.assertEqual(result.epsg, 5258)
        self.assertEqual(result.confidence, "medium")
        self.assertIn("outside Turkey", result.reason)

    def test_junk_coordinates_are_skipped(self):
        result = detect_crs("ITRF / 3 / Zone 42",
                            [(0.0, 0.0), (0.0, 0.0)] + BAHCESARAY)
        self.assertEqual(result.epsg, 5258)


class TestTableIntegrity(unittest.TestCase):

    def test_every_turkish_zone_is_mapped_in_every_family(self):
        for table in (TUREF_TM, ED50_TM, TUREF_GK, ED50_GK):
            for cm in TURKISH_CENTRAL_MERIDIANS:
                with self.subTest(table=id(table), cm=cm):
                    self.assertIn(cm, table)

    def test_codes_are_unique_and_labelled(self):
        codes = (list(TUREF_TM.values()) + list(ED50_TM.values())
                 + list(TUREF_GK.values()) + list(ED50_GK.values()))
        self.assertEqual(len(codes), len(set(codes)))
        for code in codes:
            self.assertIn(code, LABELS)


if __name__ == "__main__":
    unittest.main()
