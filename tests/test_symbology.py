# -*- coding: utf-8 -*-
"""test_symbology — Unit tests for PlanX Adaptive Symbology Engine (PASE)."""
from __future__ import annotations

import unittest

from zero2cadgis.core.symbology import (
    PLAN_SYMBOLOGY_CATALOG,
    PlanStyleRule,
    PlanSymbologyMatcher,
    apply_plan_symbology,
)


class TestPlanSymbologyMatcher(unittest.TestCase):

    def test_normalize_string(self):
        self.assertEqual(PlanSymbologyMatcher.normalize_string("UIP_ACIK_YESIL_ALAN"), "ACIK_YESIL_ALAN")
        self.assertEqual(PlanSymbologyMatcher.normalize_string("NIP_KONUT_ALANI"), "KONUT_ALANI")
        self.assertEqual(PlanSymbologyMatcher.normalize_string("PL_ÖZEL_EĞİTİM"), "OZEL_EGITIM")

    def test_match_rule_residential(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_KONUT_ALANI")
        self.assertIsNotNone(rule)
        self.assertIn(rule.category_id, ["RESIDENTIAL_GENERAL", "RESIDENTIAL_MEDIUM"])
        self.assertEqual(rule.fill_color.upper(), "#FFFF00")

    def test_match_rule_park(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_ACIK_YESIL_ALAN")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.category_id, "ACTIVE_GREEN")

    def test_match_rule_school(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_ILKOKUL_ALANI")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.category_id, "EDUCATION")

    def test_match_rule_commercial(self):
        rule = PlanSymbologyMatcher.match_rule("NIP_TICARET_ALANI")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.category_id, "COMMERCIAL_GENERAL")

    def test_match_rule_road(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_YOLORTA")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.category_id, "ROAD_TRANSPORTATION")

    def test_match_rule_by_attribute(self):
        rule = PlanSymbologyMatcher.match_rule("CAD_LAYER_01", attributes={"FONKSIYON": "PARK_COCUK"})
        self.assertIsNotNone(rule)
        self.assertEqual(rule.category_id, "PARK_PLAYGROUND")

    def test_unmatched_layer(self):
        rule = PlanSymbologyMatcher.match_rule("UNKNOWN_RANDOM_LAYER_12345")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.category_id, "DEFAULT_PLAN")

    def test_apply_symbology_headless_graceful(self):
        # Outside QGIS runtime, should return False cleanly without crashing
        res = apply_plan_symbology(None)
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
