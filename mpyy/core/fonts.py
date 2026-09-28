"""E-Plan TTF font registry and font marker symbol factory."""

import os
from pathlib import Path
from qgis.core import QgsFontMarkerSymbolLayer, QgsMarkerSymbol
from qgis.PyQt.QtGui import QColor, QFontDatabase

_LOADED_FONTS = {}
_FONT_FAMILIES = {}


def register_mpyy_fonts() -> int:
    """Register all E-Plan TTF fonts located in resources/fonts into QGIS."""
    fonts_dir = Path(__file__).resolve().parents[1] / "resources" / "fonts"
    if not fonts_dir.exists():
        return 0

    from qgis.PyQt.QtWidgets import QApplication
    from qgis.PyQt.QtGui import QFont

    # 1. Register DejaVu text fonts FIRST so Qt default font is never hijacked by CAD symbol fonts
    text_font_paths = sorted(fonts_dir.glob("DejaVu*.[tT][tT][fF]"))
    loaded_count = 0
    for font_path in text_font_paths:
        stem = font_path.stem
        if stem not in _LOADED_FONTS:
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(font_id)
                _LOADED_FONTS[stem] = font_id
                _FONT_FAMILIES[stem] = families[0] if families else stem
                loaded_count += 1

    # Preserve readable application default font
    app = QApplication.instance()
    if app:
        cur_fam = app.font().family()
        if not cur_fam or any(s in cur_fam for s in ("CDP", "NIP", "UIP", "MNIP", "MCDP", "MUIP", "OG_V", "esri", "mulga")):
            app.setFont(QFont("DejaVu Sans", 9))

    # 2. Register all other symbol/notation TTF fonts
    for font_path in sorted(fonts_dir.glob("*.[tT][tT][fF]")):
        stem = font_path.stem
        if stem not in _LOADED_FONTS:
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(font_id)
                _LOADED_FONTS[stem] = font_id
                _FONT_FAMILIES[stem] = families[0] if families else stem
                loaded_count += 1

    # Re-verify app font did not get overridden
    if app:
        cur_fam = app.font().family()
        if not cur_fam or any(s in cur_fam for s in ("CDP", "NIP", "UIP", "MNIP", "MCDP", "MUIP", "OG_V", "esri", "mulga")):
            app.setFont(QFont("DejaVu Sans", 9))

    return loaded_count



def create_font_marker_symbol(
    font_name: str,
    glyph_hex_or_char: str | int,
    size: float = 14.0,
    color: QColor = None,
) -> QgsMarkerSymbol:
    """Create a QgsMarkerSymbol using a registered E-Plan TTF font glyph."""
    register_mpyy_fonts()

    # Determine character
    if isinstance(glyph_hex_or_char, int):
        char = chr(glyph_hex_or_char)
    elif isinstance(glyph_hex_or_char, str):
        if glyph_hex_or_char.startswith("0x") or glyph_hex_or_char.startswith("0X"):
            char = chr(int(glyph_hex_or_char, 16))
        elif len(glyph_hex_or_char) == 1:
            char = glyph_hex_or_char
        else:
            try:
                char = chr(int(glyph_hex_or_char, 16))
            except ValueError:
                char = glyph_hex_or_char[0]
    else:
        char = "•"

    clean_font_name = Path(font_name).stem
    family = _FONT_FAMILIES.get(clean_font_name, clean_font_name)

    layer = QgsFontMarkerSymbolLayer()
    layer.setFontFamily(family)
    layer.setCharacter(char)
    layer.setColor(color or QColor(0, 0, 0))
    layer.setSize(float(size))

    symbol = QgsMarkerSymbol()
    symbol.changeSymbolLayer(0, layer)
    return symbol
