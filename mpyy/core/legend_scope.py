"""Legend limited to the values a plan actually contains.

An MPYY type carries the Ministry's full symbol set -- every KonutTip, every
AcikYesilTip, the whole Ek-1e hierarchy -- while one plan uses a handful of
them. Drawn as shipped, a plan's legend lists dozens of symbols that appear
nowhere on the map.

``limit_to_present`` keeps only the rules / categories at least one feature of
the layer is drawn with, and drops the hierarchy groups left empty. Which
rules are "used" is decided by QGIS itself (``legendKeysForFeature``), so ELSE
rules, nested filters and the hierarchy need no second interpretation here.

The full set is never lost. It is kept on the layer (compressed renderer XML in
a custom property, saved with the project), and ``watch`` puts it back while
the layer is being edited -- a feature drawn with a value the plan did not have
yet must get its real symbol, not the grey fallback -- and trims again after
the edits are saved.
"""

from __future__ import annotations

import base64
import zlib

from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsFeatureRenderer,
    QgsFeatureRequest,
    QgsReadWriteContext,
    QgsRenderContext,
    QgsRuleBasedRenderer,
)
from qgis.PyQt.QtXml import QDomDocument

FULL_PROPERTY = "mpyy/legend_full_renderer"
MODE_PROPERTY = "mpyy/legend"            # "mevcut" when trimmed, "tam" when full

_WATCHED: set[str] = set()


def _encode(renderer) -> str:
    doc = QDomDocument()
    doc.appendChild(renderer.save(doc, QgsReadWriteContext()))
    return base64.b64encode(zlib.compress(doc.toString().encode("utf-8"), 9)).decode("ascii")


def _decode(text: str):
    doc = QDomDocument()
    doc.setContent(zlib.decompress(base64.b64decode(text)).decode("utf-8"))
    return QgsFeatureRenderer.load(doc.documentElement(), QgsReadWriteContext())


def _used_keys(layer, renderer) -> set[str]:
    context = QgsRenderContext()
    context.setExpressionContext(layer.createExpressionContext())
    renderer = renderer.clone()
    renderer.startRender(context, layer.fields())
    used: set[str] = set()
    try:
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.Flag.NoGeometry)
        request.setSubsetOfAttributes(renderer.usedAttributes(context), layer.fields())
        for feature in layer.getFeatures(request):
            context.expressionContext().setFeature(feature)
            used |= set(renderer.legendKeysForFeature(feature, context))
    finally:
        renderer.stopRender(context)
    return used


def _used_values(layer, attribute: str) -> set[str]:
    """String forms of the classification values the layer's features have."""
    from qgis.core import QgsExpression

    expression = QgsExpression(attribute if not layer.fields().indexFromName(attribute) >= 0
                               else QgsExpression.quotedColumnRef(attribute))
    context = layer.createExpressionContext()
    expression.prepare(context)
    values = set()
    for feature in layer.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.Flag.NoGeometry)):
        context.setFeature(feature)
        value = expression.evaluate(context)
        values.add("" if value is None or str(value) == "NULL" else str(value))
    return values


def _prune_rule(rule, used) -> bool:
    """Drop unused descendants; True when this rule (or a descendant) is used."""
    for child in list(rule.children()):
        if not _prune_rule(child, used):
            rule.removeChild(child)
    return rule.ruleKey() in used or bool(rule.children())


def full_renderer(layer):
    """The layer's complete renderer: the stored one, or the current one if none is stored."""
    stored = layer.customProperty(FULL_PROPERTY)
    if stored:
        renderer = _decode(stored)
        if renderer is not None:
            return renderer
    return layer.renderer().clone() if layer.renderer() else None


def limit_to_present(layer) -> tuple[int, int]:
    """Keep only the symbols the layer's features use. Returns (kept, dropped).

    Renderers other than rule-based and categorized are left untouched.
    """
    if layer.isEditable():
        return 0, 0                        # full symbols while editing; trimmed on save
    renderer = full_renderer(layer)
    if renderer is None:
        return 0, 0
    if not layer.customProperty(FULL_PROPERTY):
        layer.setCustomProperty(FULL_PROPERTY, _encode(renderer))
    used = _used_keys(layer, renderer) if isinstance(renderer, QgsRuleBasedRenderer) else set()
    trimmed = renderer.clone()
    if isinstance(trimmed, QgsRuleBasedRenderer):
        root = trimmed.rootRule()
        total = len(root.descendants())
        for child in list(root.children()):
            if not _prune_rule(child, used):
                root.removeChild(child)
        kept = len(root.descendants())
    elif isinstance(trimmed, QgsCategorizedSymbolRenderer):
        total = len(trimmed.categories())
        values = _used_values(layer, trimmed.classAttribute())
        known = {str(c.value()) for c in trimmed.categories() if str(c.value()) not in ("", "NULL")}
        unmatched = any(v not in known for v in values)
        for index in reversed(range(total)):
            value = str(trimmed.categories()[index].value())
            if value in ("", "NULL"):
                keep = unmatched          # the "all other values" category
            else:
                keep = value in values
            if not keep:
                trimmed.deleteCategory(index)
        kept = len(trimmed.categories())
    else:
        return 0, 0
    layer.setRenderer(trimmed)
    layer.setCustomProperty(MODE_PROPERTY, "mevcut")
    layer.triggerRepaint()
    return kept, total - kept


def show_full(layer) -> bool:
    """Put the complete symbol set back. Returns False when none was stored."""
    stored = layer.customProperty(FULL_PROPERTY)
    if not stored:
        return False
    renderer = _decode(stored)
    if renderer is None:
        return False
    layer.setRenderer(renderer)
    layer.setCustomProperty(MODE_PROPERTY, "tam")
    layer.triggerRepaint()
    return True


def watch(layer) -> None:
    """Full symbols while editing, trimmed legend once the edits are saved or dropped."""
    layer_id = layer.id()
    if layer_id in _WATCHED:
        return
    _WATCHED.add(layer_id)
    layer.editingStarted.connect(lambda: show_full(layer))
    layer.editingStopped.connect(lambda: limit_to_present(layer))
    # The id is captured now: a layer being deleted must not be called back into.
    layer.willBeDeleted.connect(lambda: _WATCHED.discard(layer_id))
