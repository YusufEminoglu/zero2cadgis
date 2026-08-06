import re

def fix_mojibake(text: str | None) -> str:
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ""

    # 1. Unescape DXF \U+XXXX / \u+XXXX unicode escapes
    if "\\U+" in text or "\\u+" in text or r"\U+" in text or r"\u+" in text:
        text = re.sub(r"\\?[Uu]\+([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), text)

    # 2. Fix UTF-8 / CP1254 / CP1252 Mojibake sequences
    if any(c in text for c in ("Ã", "Â", "Å", "Ä", "Ã°", "Ã½", "â", "ï")):
        for src_enc in ("latin1", "cp1252"):
            for dst_enc in ("utf-8", "cp1254", "iso-8859-9"):
                try:
                    fixed = text.encode(src_enc).decode(dst_enc)
                    if not any(c in fixed for c in ("Ã", "Â", "Å", "Ä", "â")):
                        text = fixed
                        break
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass

    # 3. Direct character replacement for remaining stubborn Turkish Mojibake double-encodings
    replacements = {
        "Ã§": "ç", "Ã‡": "Ç",
        "Ã¶": "ö", "Ã–": "Ö",
        "Ã¼": "ü", "Ãœ": "Ü",
        "ÅŸ": "ş", "ÅŞ": "Ş", "ÃŸ": "ş",
        "ÄŸ": "ğ", "ÄĞ": "Ğ", "Ã°": "ğ",
        "Ä±": "ı", "Ã½": "ı", "Ãİ": "İ",
    }
    for bad, good in replacements.items():
        if bad in text:
            text = text.replace(bad, good)

    return text

print("Test 1 (DXF):", fix_mojibake(r"B\U+00DCY\U+00DCK\U+015EEH\U+00D6R"))
print("Test 2 (UTF8):", fix_mojibake("BÃ¼yÃ¼kÅŸehir"))
print("Test 3 (CP1254):", fix_mojibake("Ã§ENLÃ–Z"))
