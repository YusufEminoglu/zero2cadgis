# -*- coding: utf-8 -*-
"""test_symbology — the plan-drawing helpers that remain after the MPYY switch.

Plan styling is MPYY Studio's style set (zero2cadgis/mpyy); what is tested here
is which field carries a drawing's text and which plan level a file is.
"""
from __future__ import annotations

import os
import unittest

from zero2cadgis.core.symbology import (
    LABEL_FIELD_CANDIDATES,
    detect_plan_type,
    pick_label_field,
)


class _FakeField:
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class _FakeFields:
    """Just enough of QgsFields for the label-field choice to be testable."""

    def __init__(self, names):
        self._names = list(names)

    def __iter__(self):
        return iter(_FakeField(n) for n in self._names)

    def indexOf(self, name):
        return self._names.index(name)


class _FakeLayer:
    def __init__(self, values_by_field):
        self._values = values_by_field
        self._fields = _FakeFields(values_by_field)

    def fields(self):
        return self._fields

    def uniqueValues(self, index, limit=-1):
        name = self._fields._names[index]
        values = self._values[name]
        return set(values if limit < 0 else values[:limit])


class TestLabelFieldChoice(unittest.TestCase):
    """A field existing is not the same as a field holding anything."""

    def test_empty_field_is_skipped_for_the_one_with_text(self):
        # Exactly the real CAD point layer: `name` is declared but empty on
        # every feature, while `label` holds the drawing's text.
        layer = _FakeLayer({
            "name": [None, "", None],
            "label": ["Hmaks: 12.50", "TAKS 0.40", None],
        })
        self.assertEqual(pick_label_field(layer), "label")

    def test_no_text_anywhere_means_no_labels(self):
        layer = _FakeLayer({"name": [None, ""], "label": [None, "   "]})
        self.assertIsNone(pick_label_field(layer))

    def test_layer_without_candidate_fields(self):
        layer = _FakeLayer({"source_file": ["a.ncz"], "layer_code": [5]})
        self.assertIsNone(pick_label_field(layer))

    def test_numeric_text_counts_as_text(self):
        layer = _FakeLayer({"label": [None], "kat_adedi": [4, 5]})
        self.assertEqual(pick_label_field(layer), "kat_adedi")

    def test_label_outranks_name_in_the_candidate_order(self):
        self.assertLess(LABEL_FIELD_CANDIDATES.index("label"),
                        LABEL_FIELD_CANDIDATES.index("name"))

    def test_non_layer_input_is_handled(self):
        self.assertIsNone(pick_label_field(None))
        self.assertIsNone(pick_label_field(object()))

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





if __name__ == "__main__":
    unittest.main()

