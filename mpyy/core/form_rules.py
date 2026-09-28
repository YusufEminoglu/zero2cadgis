"""Entry widgets and value checks for the numeric fields of the MPYY forms.

The MPYY 1.1.7 XSD gives each numeric field a type (``double``, ``int``, ``long``)
and nothing else: no range, no unit. Left at that, a form accepts ``Taks = 35``
for 0.35, ``KatAdedi = -3`` or a negative setback, and the value is stored and
exported as if it were a plan decision.

The bounds below come from what each quantity *is*, never from a regulation's
permitted values, which vary by plan and are the planner's decision:

* TAKS is a footprint / parcel ratio, so 0 < TAKS <= 1;
* distances, widths, heights and areas cannot be negative;
* a building has at least one storey; a Turkish province (plate) code is 1-81;
* codes and identifiers are whole numbers >= 0.

A value outside those bounds cannot be right, so it is a *hard* check: the form
refuses to save it. A value that is merely implausible together with another
one (KAKS below TAKS) is not a form check: it is reported by the workspace
audit as a warning, because a draft is entered one field at a time and QGIS
holds only one constraint expression, of one strength, per field. NULL always
passes -- a plan is drawn before every value is known.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from qgis.core import QgsEditorWidgetSetup, QgsFieldConstraints


@dataclass(frozen=True)
class NumericRule:
    minimum: float
    maximum: float
    step: float
    precision: int
    suffix: str = ""
    style: str = "SpinBox"                 # QGIS Range widget: SpinBox | Slider
    lower_open: bool = False               # True: the minimum itself is not allowed
    reason: str = ""


# Field name -> rule. The names are the XSD's own; one rule serves every level
# and feature type that carries the field.
NUMERIC_RULES = {
    "Taks": NumericRule(0.0, 1.0, 0.01, 2, style="Slider", lower_open=True,
                        reason="TAKS bir oran: 0'dan büyük, en çok 1 olmalı (0,35 gibi)."),
    "EmsalKaks": NumericRule(0.0, 100.0, 0.05, 2, lower_open=True,
                             reason="Emsal (KAKS) 0'dan büyük olmalı."),
    "Emsal": NumericRule(0.0, 100.0, 0.05, 2, lower_open=True,
                         reason="Emsal 0'dan büyük olmalı."),
    "KatAdedi": NumericRule(1, 300, 1, 0, " kat", reason="Kat adedi en az 1 olmalı."),
    "YapiYuksekligi": NumericRule(0.0, 1000.0, 0.5, 2, " m", lower_open=True,
                                  reason="Yapı yüksekliği 0'dan büyük olmalı (metre)."),
    "Yukseklik": NumericRule(0.0, 10000.0, 0.5, 2, " m",
                             reason="Yükseklik negatif olamaz (metre)."),
    "OnBahceMesafesi": NumericRule(0.0, 1000.0, 0.5, 2, " m",
                                   reason="Ön bahçe mesafesi negatif olamaz (metre)."),
    "YanBahceMesafesi": NumericRule(0.0, 1000.0, 0.5, 2, " m",
                                    reason="Yan bahçe mesafesi negatif olamaz (metre)."),
    "YapiYaklasmaMesafesi": NumericRule(0.0, 1000.0, 0.5, 2, " m",
                                        reason="Yapı yaklaşma mesafesi negatif olamaz (metre)."),
    "Mesafe": NumericRule(0.0, 10000.0, 0.5, 2, " m", reason="Mesafe negatif olamaz (metre)."),
    "YolGenisligi": NumericRule(0.0, 500.0, 0.5, 2, " m", lower_open=True,
                                reason="Yol genişliği 0'dan büyük olmalı (metre)."),
    "Genislik": NumericRule(0.0, 500.0, 0.5, 2, " m", lower_open=True,
                            reason="Genişlik 0'dan büyük olmalı (metre)."),
    "YogunlukDeger": NumericRule(0.0, 10000.0, 5.0, 0, " kişi/ha",
                                 reason="Yoğunluk negatif olamaz (kişi/ha)."),
    "MinimumIfraz": NumericRule(0.0, 100000000.0, 10.0, 0, " m²", lower_open=True,
                                reason="Minimum ifraz alanı 0'dan büyük olmalı (m²)."),
    "KuruluGuc": NumericRule(0.0, 1000000.0, 0.1, 2, reason="Kurulu güç negatif olamaz."),
    "CizgiKalinligi": NumericRule(0.0, 100.0, 0.05, 2, lower_open=True,
                                  reason="Çizgi kalınlığı 0'dan büyük olmalı."),
    "IlKod": NumericRule(1, 81, 1, 0, reason="İl kodu 1 ile 81 arasında olmalı."),
    "Ilkod": NumericRule(1, 81, 1, 0, reason="İl kodu 1 ile 81 arasında olmalı."),
    "IlceKod": NumericRule(1, 99999, 1, 0, reason="İlçe kodu pozitif bir tam sayı olmalı."),
    "UlkeKod": NumericRule(0, 999, 1, 0, reason="Ülke kodu negatif olamaz."),
    "NutKodD1": NumericRule(0, 999999, 1, 0, reason="NUTS kodu negatif olamaz."),
    "NutKodD2": NumericRule(0, 999999, 1, 0, reason="NUTS kodu negatif olamaz."),
    "NutKodD3": NumericRule(0, 999999, 1, 0, reason="NUTS kodu negatif olamaz."),
    "Pin": NumericRule(0, 2147483647, 1, 0, reason="Pin negatif olamaz."),
    "EnvanterNo": NumericRule(0, 2147483647, 1, 0, reason="Envanter numarası negatif olamaz."),
}

NUMERIC_TYPES = {"double", "int", "long"}

# Checks across two fields of one feature. They are *not* form constraints: a
# field holds one constraint expression and one strength, and the range check
# above must stay hard. They are reported by the workspace audit instead, as
# warnings, because each names a combination that is implausible, not impossible.
CROSS_FIELD_RULES = (
    ("EmsalKaks", ("EmsalKaks", "Taks"),
     lambda f: f["EmsalKaks"] < f["Taks"],
     "Emsal (KAKS) TAKS'tan küçük: en az bir tam kat, taban alanı kadar inşaat alanı demektir."),
)


def rule_for(field: dict) -> Optional[NumericRule]:
    """The rule for one schema field, or None when it is not a numeric field we bound."""
    if field.get("type") not in NUMERIC_TYPES:
        return None
    return NUMERIC_RULES.get(field["name"])


def value_in_rule(value, rule: NumericRule) -> bool:
    """True when a stored value satisfies the rule (NULL passes, like the form)."""
    if value is None or str(value) == "NULL":
        return True
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    low_ok = number > rule.minimum if rule.lower_open else number >= rule.minimum
    return low_ok and number <= rule.maximum


def range_expression(name: str, rule: NumericRule) -> str:
    low = ">" if rule.lower_open else ">="
    quoted = '"' + name.replace('"', '""') + '"'
    return f"{quoted} IS NULL OR ({quoted} {low} {rule.minimum:g} AND {quoted} <= {rule.maximum:g})"


def apply_numeric_rules(layer, feature_type: dict) -> list[str]:
    """Range widgets and value checks for the numeric fields of one MPYY layer.

    Returns the names of the fields that received a rule. A field that already
    carries a constraint expression (the code-list check of a required enum)
    is never a numeric field, so nothing here overwrites one.
    """
    fields = layer.fields()
    applied = []
    for field in feature_type["fields"]:
        rule = rule_for(field)
        index = fields.indexFromName(field["name"])
        if rule is None or index < 0:
            continue
        integer = field["type"] in ("int", "long")
        config = {
            "Min": int(rule.minimum) if integer else rule.minimum,
            "Max": int(rule.maximum) if integer else rule.maximum,
            "Step": int(rule.step) if integer else rule.step,
            "Precision": 0 if integer else rule.precision,
            "AllowNull": True,
            "Style": rule.style,
            "Suffix": rule.suffix,
        }
        layer.setEditorWidgetSetup(index, QgsEditorWidgetSetup("Range", config))
        layer.setConstraintExpression(index, range_expression(field["name"], rule), rule.reason)
        layer.setFieldConstraint(
            index, QgsFieldConstraints.Constraint.ConstraintExpression,
            QgsFieldConstraints.ConstraintStrength.ConstraintStrengthHard,
        )
        applied.append(field["name"])

    return applied


def cross_field_findings(feature, field_names) -> list[str]:
    """Warnings for implausible value combinations on one feature (NULLs skipped)."""
    found = []
    for _target, needed, broken, message in CROSS_FIELD_RULES:
        if not set(needed) <= set(field_names):
            continue
        values = {name: feature[name] for name in needed}
        if any(v is None or str(v) == "NULL" for v in values.values()):
            continue
        try:
            if broken(values):
                found.append(message)
        except TypeError:
            continue
    return found
