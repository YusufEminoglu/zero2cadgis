import re

def fix_mojibake(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    # 1. Unescape DXF \U+XXXX / \u+XXXX unicode escapes
    if "\\U+" in text or "\\u+" in text or r"\U+" in text or r"\u+" in text:
        text = re.sub(r"\\?[Uu]\+([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), text)

    # 2. Fix UTF-8 / CP1254 Mojibake sequences
    if any(c in text for c in ("Ã", "Â", "Å", "Ä", "Ã°", "Ã½")):
        for src_enc in ("latin1", "cp1252"):
            for dst_enc in ("utf-8", "cp1254", "iso-8859-9"):
                try:
                    fixed = text.encode(src_enc).decode(dst_enc)
                    if not any(c in fixed for c in ("Ã", "Â", "Å", "Ä")):
                        return fixed
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
    return text

print("Test 1:", fix_mojibake(r"YAPI \U+015EENL\U+00D6Z"))
print("Test 2:", fix_mojibake("YAPI Ã§ENLÃ–Z"))
