"""CAD tabaka -> MPYY type: exact, confirmed, safe rules, and suggestions.

A drawing's tabaka names are rarely the table's own spellings: ``PL_ILKOKUL``
for ``PL_ILKOKUL_ALANI``, ``PL_DERE_2``, ``ADAKENARI_NETCAD``,
``PL_BAKIMAKARYAKIT``. On a real UİP (TIRE_MERKEZ, 155 tabaka) the exact table
matched only 31. Resolution therefore runs in tiers, and only the first three
ever write an MPYY code without a person deciding:

1. ``tam``    -- the name is a key of the crosswalk table.
2. ``onayli`` -- a planner confirmed this name before (stored per user, reused).
3. ``kural``  -- one of a few spelling rules that cannot change the meaning:
   a trailing sheet/copy number, a Netcad export suffix, the ``_ALANI`` /
   ``_TES`` area ending, the underscores. Accepted only when every rule that
   fires points at the *same single* key.
4. ``oneri``  -- everything else is only *proposed*: a synonym table (DINI ->
   IBADET / CAMI ...) and string similarity. Measured on TIRE, similarity alone
   proposed PL_DINI_TESIS -> Sanayi Tesis and HAT_DERE -> Kademe hattı, so a
   proposal is never applied until a person confirms it.

A name carrying IPTAL / ITIRAZ is never resolved and never proposed: a
cancelled or contested area is not that function.

Pure Python: no QGIS import at module level, so it is unit-tested without QGIS.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CROSSWALK_PATH = Path(__file__).resolve().parents[1] / "styles" / "mpyy_tabaka_crosswalk.json"

NEVER_MATCH_TOKENS = frozenset(("IPTAL", "ITIRAZ"))
NETCAD_SUFFIXES = ("_NETCAD", "_NETC", "_NTC", "_NET")
AREA_SUFFIXES = ("_ALANI", "_ALAN", "_TESISI", "_TESIS", "_TES")

# Token -> tokens it may stand for. Used only to *propose*; each entry is a
# same-concept spelling seen in municipal drawings, never a looser category.
SYNONYMS = {
    "DINI": ("IBADET", "CAMI", "MESCIT"),
    "IBADET": ("CAMI", "MESCIT", "KILISE"),
    "TICK": ("TICARET", "KONUT"),
    "TIC": ("TICARET",),
    "TICART": ("TICARET",),
    "TRIZM": ("TURIZM",),
    "YESIL": ("PARK", "YESIL", "REKREASYON"),
    "OYUN": ("COCUK", "BAHCESI"),
    "SPOR": ("SPOR",),
    "ILKOGRETIM": ("ILKOKUL", "ORTAOKUL"),
    "ILKOGRTM": ("ILKOKUL", "ORTAOKUL"),
    "SAGLIK": ("SAGLIK", "HASTANE", "AILE"),
    "DISPANSER": ("SAGLIK",),
    "BELEDIYE": ("BHA",),
    "BHA": ("BELEDIYE", "BHA"),
    "DERE": ("DERE", "SU", "YUZEYI"),
    "REFUJ": ("REFUJ",),
    "PAZAR": ("PAZAR",),
    "DEPOLAM": ("DEPOLAMA",),
    "KULTUR": ("KULTUREL",),
}


def normalize_tabaka(name) -> str:
    text = str(name or "").replace("ı", "i").replace("İ", "I")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")


@dataclass(frozen=True)
class Match:
    tabaka: str
    key: Optional[str]
    entry: Optional[dict]
    method: str            # "tam" | "onayli" | "kural" | "yok"
    rule: str = ""

    @property
    def resolved(self) -> bool:
        return self.entry is not None


@dataclass(frozen=True)
class Suggestion:
    key: str
    entry: dict
    score: float
    reason: str


@dataclass
class _Level:
    entries: dict
    skipped: dict
    compact: dict = field(default_factory=dict)   # key without underscores -> keys


_TABLE_CACHE: dict = {}


def level_table(level: str, path: Path = CROSSWALK_PATH) -> _Level:
    cache_key = (str(path), level)
    table = _TABLE_CACHE.get(cache_key)
    if table is None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))["levels"][level]
        table = _Level(entries=data["entries"], skipped=data.get("skipped", {}))
        for key in table.entries:
            table.compact.setdefault(key.replace("_", ""), set()).add(key)
        _TABLE_CACHE[cache_key] = table
    return table


# --- confirmed mappings ------------------------------------------------------

def user_mappings_path() -> Path:
    """Per-user file shared by every plugin that carries this module."""
    override = os.environ.get("MPYY_TABAKA_ESLESME")
    if override:
        return Path(override)
    try:
        from qgis.core import QgsApplication

        base = Path(QgsApplication.qgisSettingsDirPath())
    except Exception:  # noqa: BLE001 - no QGIS: tests, tools
        base = Path.home() / ".mpyy"
    return base / "mpyy" / "tabaka_eslesmeleri.json"


def load_user_mappings(path: Optional[Path] = None) -> dict:
    path = Path(path or user_mappings_path())
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data.get("levels", {}) if isinstance(data, dict) else {}


def confirm(level: str, tabaka: str, key: str, path: Optional[Path] = None) -> None:
    """Remember that ``tabaka`` means the crosswalk row ``key`` at ``level``."""
    table = level_table(level)
    if key not in table.entries:
        raise KeyError(f"{level}: '{key}' eşleşme tablosunda yok")
    path = Path(path or user_mappings_path())
    levels = load_user_mappings(path)
    levels.setdefault(level, {})[normalize_tabaka(tabaka)] = key
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=str(path.parent), suffix=".json")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        json.dump({"version": 1, "levels": levels}, stream, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(temp, path)


# --- resolution -----------------------------------------------------------------

def _tokens(normalized: str) -> list[str]:
    return [t for t in normalized.split("_") if t]


def _rule_candidates(name: str, table: _Level) -> dict[str, str]:
    """key -> rule name, for every rule that turns ``name`` into a table key."""
    found: dict[str, str] = {}

    def hit(candidate: str, rule: str):
        if candidate and candidate != name and candidate in table.entries:
            found.setdefault(candidate, rule)

    bases = {name: ""}
    stripped = re.sub(r"_?\d+$", "", name)
    if stripped != name and stripped:
        bases[stripped] = "sıra/kopya numarası"
    for suffix in NETCAD_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            bases[name[: -len(suffix)]] = "Netcad dışa aktarım eki"
            break
    for base, why in bases.items():
        hit(base, why)
        for suffix in AREA_SUFFIXES:
            if base.endswith(suffix):
                hit(base[: -len(suffix)], (why + " + " if why else "") + f"'{suffix}' eki")
            else:
                hit(base + suffix, (why + " + " if why else "") + f"'{suffix}' eki")
        compact = table.compact.get(base.replace("_", ""), set())
        if len(compact) == 1:
            hit(next(iter(compact)), (why + " + " if why else "") + "bitişik/ayrık yazım")
    return found


def resolve(level: str, tabaka, user: Optional[dict] = None) -> Match:
    """The MPYY row a tabaka resolves to without a person deciding, if any."""
    name = normalize_tabaka(tabaka)
    table = level_table(level)
    if not name:
        return Match(str(tabaka or ""), None, None, "yok")
    if set(_tokens(name)) & NEVER_MATCH_TOKENS:
        return Match(str(tabaka), None, None, "yok", "iptal/itiraz tabakası")
    if name in table.entries:
        return Match(str(tabaka), name, table.entries[name], "tam")
    confirmed = (user if user is not None else load_user_mappings()).get(level, {}).get(name)
    if confirmed in table.entries:
        return Match(str(tabaka), confirmed, table.entries[confirmed], "onayli")
    if name in table.skipped:
        return Match(str(tabaka), None, None, "yok", table.skipped[name])
    candidates = _rule_candidates(name, table)
    if len(candidates) == 1:
        key, rule = next(iter(candidates.items()))
        return Match(str(tabaka), key, table.entries[key], "kural", rule)
    return Match(str(tabaka), None, None, "yok",
                 "birden çok kural farklı satıra gidiyor" if candidates else "")


def suggest(level: str, tabaka, limit: int = 3, minimum: float = 0.45) -> list[Suggestion]:
    """Ranked proposals for a tabaka that did not resolve. Never applied by itself."""
    name = normalize_tabaka(tabaka)
    tokens = set(_tokens(name))
    if not name or tokens & NEVER_MATCH_TOKENS:
        return []
    table = level_table(level)
    prefix = name.split("_")[0]
    expanded = set(tokens)
    for token in tokens:
        expanded.update(SYNONYMS.get(token, ()))
    ignore = {"PL", "ALANI", "ALAN", "TES", "TESIS", "TESISI"}
    core_tokens = expanded - ignore
    scored = []
    for key, entry in table.entries.items():
        key_tokens = set(_tokens(key)) - ignore
        if not key_tokens:
            continue
        overlap = len(core_tokens & key_tokens) / max(len(key_tokens), 1)
        char = difflib.SequenceMatcher(None, name, key).ratio()
        same_prefix = key.split("_")[0] == prefix
        score = 0.55 * overlap + 0.45 * char + (0.05 if same_prefix else -0.15)
        via = [t for t in tokens if SYNONYMS.get(t) and set(SYNONYMS[t]) & key_tokens]
        reason = ("eş anlam: " + ", ".join(sorted(via))) if via else "yazım benzerliği"
        scored.append((score, key, entry, reason))
    scored.sort(key=lambda row: -row[0])
    return [Suggestion(key, entry, round(score, 2), reason)
            for score, key, entry, reason in scored[:limit] if score >= minimum]
