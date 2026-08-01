# -*- coding: utf-8 -*-
"""test_symbology — Unit tests for the plan symbology engines.

Covers the official e-Plan catalog (Ministry plan gösterimleri, per plan type)
and the legacy PASE keyword catalog that backs it up.
"""
from __future__ import annotations

import os
import pathlib
import re
import unittest

from zero2cadgis.core.eplan_catalog import EPLAN_CATALOG, EPLAN_PLAN_TYPES
from zero2cadgis.core.symbology import (
    PLAN_SYMBOLOGY_CATALOG,
    PlanStyleRule,
    PlanSymbologyMatcher,
    apply_plan_symbology,
    detect_plan_type,
    match_official_rule,
)

TARAMA_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "resources", "eplan_tarama"))


class TestPlanTypeDetection(unittest.TestCase):

    def test_scale_prefix(self):
        self.assertEqual(detect_plan_type("1000_BAHÇESARAY İMAR 2026"), "UIP")
        self.assertEqual(detect_plan_type("5000_ILCE_PLANI"), "NIP")
        self.assertEqual(detect_plan_type("100000_BOLGE"), "CDP")

    def test_explicit_words_win_over_scale(self):
        self.assertEqual(detect_plan_type("1000_NAZIM_IMAR"), "NIP")
        self.assertEqual(detect_plan_type("CEVRE DUZENI 5000"), "CDP")
        self.assertEqual(detect_plan_type("UIP_KONUT"), "UIP")

    def test_unknown_returns_none(self):
        self.assertIsNone(detect_plan_type("drawing_final_v2"))
        self.assertIsNone(detect_plan_type(""))
        self.assertIsNone(detect_plan_type(None))


class TestOfficialCatalog(unittest.TestCase):

    def test_every_entry_carries_visual_data(self):
        for plan_type in EPLAN_PLAN_TYPES:
            for token, entry in EPLAN_CATALOG[plan_type].items():
                with self.subTest(plan_type=plan_type, token=token):
                    self.assertTrue(
                        entry.get("fill") or entry.get("tarama")
                        or entry.get("line_color"),
                        "entry has no fill, tarama or line color")
                    self.assertTrue(entry.get("label"))
                    self.assertTrue(entry.get("style"))
                    self.assertTrue(entry.get("ust_grup"))

    def test_referenced_tarama_tiles_are_shipped(self):
        for plan_type in EPLAN_PLAN_TYPES:
            for token, entry in EPLAN_CATALOG[plan_type].items():
                tarama = entry.get("tarama")
                if not tarama:
                    continue
                with self.subTest(plan_type=plan_type, token=token):
                    self.assertTrue(
                        os.path.exists(os.path.join(TARAMA_DIR, tarama)),
                        f"missing tarama tile {tarama}")
                    size = entry.get("tarama_size")
                    self.assertEqual(len(size), 2)
                    self.assertTrue(all(int(v) > 0 for v in size))

    def test_style_names_match_plan_type_family(self):
        # Classic (UIP/NIP/CDP) and mekansal (MUIP/MNIP) style sets are both
        # official; a UIP entry must never borrow a CDP-only style.
        allowed = {
            "UIP": ("UIP_", "MUIP_", "NIP_", "MNIP_"),
            "NIP": ("NIP_", "MNIP_", "UIP_", "MUIP_"),
            "CDP": ("CDP_", "MCDP_"),
        }
        for plan_type in EPLAN_PLAN_TYPES:
            for token, entry in EPLAN_CATALOG[plan_type].items():
                with self.subTest(plan_type=plan_type, token=token):
                    self.assertTrue(
                        entry["style"].startswith(allowed[plan_type]),
                        f"{entry['style']} not valid for {plan_type}")


class TestOfficialMatching(unittest.TestCase):
    """Layer names taken from a real 1/1000 Netcad plan drawing."""

    def test_residential(self):
        rule = match_official_rule("PL_KONUT", "UIP")
        self.assertIsNotNone(rule)
        self.assertTrue(rule.official)
        self.assertEqual(rule.plan_type, "UIP")
        self.assertEqual(rule.fill_color.upper(), "#FFFA26")
        self.assertEqual(rule.ust_grup_adi, "KONUT ALANLARI")

    def test_yerlesik_and_gelisme_konut_are_told_apart_by_tabaka_name(self):
        # UIP_KONUT konut_tip 0 / 1 in the official set; the CAD layer carries no
        # such attribute, so the tabaka name is the only signal there is.
        for name in ("PL_YERLESIK_KONUT", "PL_KONUT_YERLESIK", "PL_YERLESIK",
                     "KENTSEL_YERLESIK", "PL_MESKUN_KONUT", "PL_MEVCUT_KONUT"):
            with self.subTest(name=name):
                rule = match_official_rule(name, "UIP")
                self.assertEqual(rule.fill_color.upper(), "#8C541A")
        for name in ("PL_GELISME_KONUT", "PL_KONUT_GELISME", "PL_GELISME",
                     "KENTSEL_GELISME"):
            with self.subTest(name=name):
                rule = match_official_rule(name, "UIP")
                self.assertEqual(rule.fill_color.upper(), "#FFFA26")

    def test_bare_konut_keeps_the_gelisme_default(self):
        rule = match_official_rule("PL_KONUT", "UIP")
        self.assertEqual(rule.fill_color.upper(), "#FFFA26")

    def test_konut_readings_stay_distinct_in_every_plan_type(self):
        def appearance(rule):
            return rule.tarama_path and os.path.basename(rule.tarama_path) \
                or rule.fill_color
        for plan_type in EPLAN_PLAN_TYPES:
            with self.subTest(plan_type=plan_type):
                yerlesik = match_official_rule("PL_YERLESIK_KONUT", plan_type)
                gelisme = match_official_rule("PL_GELISME_KONUT", plan_type)
                self.assertNotEqual(appearance(yerlesik), appearance(gelisme))

    def test_mixed_use_beats_bare_residential(self):
        rule = match_official_rule("PL_KONUT_TICARET", "UIP")
        self.assertIsNotNone(rule)
        self.assertIn("TİCK", rule.display_name)
        self.assertEqual(rule.ust_grup_adi, "TİCARET VE ÇALIŞMA ALANLARI")

    def test_school_uses_official_tarama_tile(self):
        rule = match_official_rule("PL_ILKOKUL_ALANI", "UIP")
        self.assertIsNotNone(rule)
        self.assertIsNotNone(rule.tarama_path)
        self.assertTrue(os.path.exists(rule.tarama_path))
        self.assertEqual(rule.tarama_size, (25, 25))

    def test_setback_line_carries_official_dash(self):
        rule = match_official_rule("SNR_YAPIYAK", "UIP")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.dash_pattern, [11.0, 1.0])

    def test_plan_boundary_carries_official_dash(self):
        rule = match_official_rule("SNR_PLANONAMA", "UIP")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.dash_pattern, [15.0, 2.5])
        self.assertEqual(rule.ust_grup_adi, "PLAN SINIRLARI VE KADASTRAL HATLAR")

    def test_turkish_characters_normalize(self):
        rule = match_official_rule("REFÜJ", "UIP")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.display_name, "Refüj")

    def test_water_surface(self):
        rule = match_official_rule("PL_DERE", "UIP")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.fill_color.upper(), "#73E9EB")

    def test_merged_upper_group_layer_name(self):
        rule = match_official_rule(
            "1000_BAHCESARAY_IMAR_2026_KONUT_ALANLARI_POLYGON", "UIP")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.ust_grup_adi, "KONUT ALANLARI")

    def test_plan_type_changes_the_style(self):
        uip = match_official_rule("PL_KONUT", "UIP")
        nip = match_official_rule("PL_KONUT", "NIP")
        cdp = match_official_rule("PL_KONUT", "CDP")
        self.assertEqual(uip.category_id, "EPLAN_UIP_KONUT")
        self.assertEqual(nip.category_id, "EPLAN_NIP_KONUT")
        self.assertEqual(cdp.category_id, "EPLAN_CDP_KONUT")
        self.assertNotEqual(uip.fill_color, nip.fill_color)

    def test_plan_type_falls_back_when_token_absent(self):
        # CDP has no küçük sanayi rule; the official UIP/NIP equivalent is used
        # instead of dropping to the legacy catalog.
        rule = match_official_rule("PL_KUCUK_SANAYI", "CDP")
        self.assertIsNotNone(rule)
        self.assertTrue(rule.official)

    def test_non_planning_layer_is_not_matched(self):
        self.assertIsNone(match_official_rule("SM_AGAC", "UIP"))
        self.assertIsNone(match_official_rule("ROL_CEPHE", "UIP"))
        self.assertIsNone(match_official_rule("", "UIP"))


class TestQt6EnumSafety(unittest.TestCase):
    """Qt6 dropped unscoped enum members, and QGIS 4 ships PyQt6.

    The unscoped ``SolidLine`` spelling raises AttributeError there, while the
    scoped ``Qt.PenStyle.SolidLine`` works on both PyQt5 and PyQt6 — that is the
    form to use. Symbology runs inside ``suppress(Exception)``, so a
    regression would not crash — it would silently leave every plan layer with
    QGIS random colors. This static scan is the only thing that catches it in
    the pure suite.
    """

    SCOPES = {
        "PenStyle", "BrushStyle", "ItemDataRole", "CheckState", "ItemFlag",
        "AlignmentFlag", "Orientation", "GlobalColor", "ContextMenuPolicy",
        "WidgetAttribute", "TextInteractionFlag", "ScrollBarPolicy",
        "CaseSensitivity", "KeyboardModifier", "MouseButton", "Key",
        "CursorShape", "WindowType", "FocusPolicy", "SortOrder",
        "TextElideMode", "PenCapStyle", "PenJoinStyle", "FillRule",
        "AspectRatioMode", "TransformationMode", "ConnectionType",
        "MatchFlag", "DockWidgetArea", "ToolButtonStyle",
    }

    def test_no_unscoped_qt_enum_members(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        offenders = []
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                for match in re.finditer(r"\bQt\.([A-Za-z_]\w*)", line):
                    if match.group(1) not in self.SCOPES:
                        offenders.append(
                            f"{path.relative_to(root)}:{lineno}: Qt.{match.group(1)}")
        self.assertEqual(offenders, [], "unscoped Qt enum members break QGIS 4")


class TestPlanSymbologyMatcher(unittest.TestCase):

    def test_normalize_string(self):
        self.assertEqual(PlanSymbologyMatcher.normalize_string("UIP_ACIK_YESIL_ALAN"), "ACIK_YESIL_ALAN")
        self.assertEqual(PlanSymbologyMatcher.normalize_string("NIP_KONUT_ALANI"), "KONUT_ALANI")
        self.assertEqual(PlanSymbologyMatcher.normalize_string("PL_ÖZEL_EĞİTİM"), "OZEL_EGITIM")

    def test_official_catalog_has_priority(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_KONUT_ALANI")
        self.assertTrue(rule.official)
        self.assertEqual(rule.category_id, "EPLAN_UIP_KONUT")

    def test_plan_type_inferred_from_layer_prefix(self):
        rule = PlanSymbologyMatcher.match_rule("NIP_TICARET_ALANI")
        self.assertTrue(rule.official)
        self.assertEqual(rule.plan_type, "NIP")

    def test_explicit_plan_type_overrides_name(self):
        rule = PlanSymbologyMatcher.match_rule("NIP_TICARET_ALANI", plan_type="UIP")
        self.assertEqual(rule.plan_type, "UIP")

    def test_match_rule_school(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_ILKOKUL_ALANI")
        self.assertEqual(rule.display_name, "İlkokul Alanı")

    def test_match_rule_road(self):
        rule = PlanSymbologyMatcher.match_rule("UIP_YOLORTA")
        self.assertTrue(rule.official)
        self.assertEqual(rule.ust_grup_adi, "ULAŞIM VE ALTYAPI GÜZERGAHLARI")

    def test_legacy_catalog_backs_up_attribute_matching(self):
        rule = PlanSymbologyMatcher.match_rule(
            "CAD_LAYER_01", attributes={"FONKSIYON": "PARK_COCUK"})
        self.assertFalse(rule.official)
        self.assertEqual(rule.category_id, "PARK_PLAYGROUND")

    def test_unmatched_layer(self):
        rule = PlanSymbologyMatcher.match_rule("UNKNOWN_RANDOM_LAYER_12345")
        self.assertEqual(rule.category_id, "DEFAULT_PLAN")

    def test_legacy_catalog_still_populated(self):
        self.assertTrue(PLAN_SYMBOLOGY_CATALOG)
        self.assertIsInstance(PLAN_SYMBOLOGY_CATALOG[0], PlanStyleRule)

    def test_apply_symbology_headless_graceful(self):
        # Outside QGIS runtime, should return False cleanly without crashing
        res = apply_plan_symbology(None)
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
