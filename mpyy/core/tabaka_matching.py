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
4. ``oneri``  -- everything else is only *proposed*, and never applied until a
   person confirms it. Proposals are ranked word by word against every name a
   function has: the Ministry tabaka keys, the Ek-1e catalogue name ("ATIKSU
   TESİSLERİ ALANI (ARITMA-TERFİ MERKEZİ)") and the MPYY code (AritmaTesisi).
   A drawing word counts when it is the same word, an abbreviation of it
   (KULTR, VRLIGI, REGULATR), its plural (TESISLERI) or a listed same-concept
   word (DISPANSER -> SAGLIK); run-together names are split on the vocabulary
   (TESCILCEPHEKORUMA). Rare words weigh more than common ones, and a layer's
   geometry limits the functions to those drawn that way. Whole-name string
   similarity, used before, proposed SNR_SIT_3_ARKEOLOJIK -> Jeolojik etüt and
   found nothing at all for PL_ARITMA or PL_ORTAOGRETIM.

A name carrying IPTAL / ITIRAZ is never resolved and never proposed: a
cancelled or contested area is not that function.

Pure Python: no QGIS import at module level, so it is unit-tested without QGIS.
"""

from __future__ import annotations

import math
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STYLES = Path(__file__).resolve().parents[1] / "styles"
CROSSWALK_PATH = STYLES / "mpyy_tabaka_crosswalk.json"
SCHEMA_PATH = STYLES / "mpyy_schema.json"

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
    "OYUN": ("COCUK",),
    "SPOR": ("SPOR",),
    "ILKOGRETIM": ("ILKOKUL", "ORTAOKUL"),
    "ILKOGRTM": ("ILKOKUL", "ORTAOKUL"),
    "SAGLIK": ("SAGLIK", "HASTANE", "AILE"),
    "DISPANSER": ("SAGLIK",),
    "BELEDIYE": ("BHA",),
    "BHA": ("BELEDIYE", "BHA"),
    "DERE": ("DERE",),
    "REFUJ": ("REFUJ",),
    "PAZAR": ("PAZAR",),
    "DEPOLAM": ("DEPOLAMA",),
    "KULTUR": ("KULTUREL",),
    "ORTAOGRETIM": ("LISE",),        # ortaöğretim = lise kademesi
    "HAZIRE": ("MEZARLIK",),         # hazire: türbe/cami yanındaki mezarlık
    "KABRISTAN": ("MEZARLIK",),
    "GAR": ("ISTASYON",),
    "DEPO": ("DEPOLAMA",),
}

# Words that name no function by themselves, and the CAD layer prefixes.
STOP_WORDS = frozenset(("ALAN", "ALANI", "ALANLARI", "ALANLAR", "TESIS", "TESISI", "TESISLERI", "TESISLER",
                        "SAHA", "SAHASI", "VE", "ILE", "VEYA", "TIP", "TUR", "MERKEZI", "DIGER"))
LAYER_PREFIXES = frozenset(("PL", "HAT", "SNR", "KA", "KST", "TR", "SM", "UIP", "NIP", "CDP"))
PLURALS = ("LERI", "LARI", "LER", "LAR")
AMBIGUOUS_SINGLE_WORD = 8     # a one-word name fitting more functions than this gets no proposal
# After a vowel: DEPO+SU, BAHCE+SI. Not YI/YU: that would make SANAYI "SANA".
POSSESSIVES = ("SI", "SU")
# Layers that are never a plan function, so nothing is proposed for them: Netcad
# notation (SM_YAPILASMA, SM_KAKS), texts and inserts (YAZI_*, EKLE_*), sheet
# indexes (PINDEX_1000), the cadastre (PARSEL, ADA_NO, ADA_AYRIM), survey points
# and pen layers; and a note (BELEDIYE_NOT) is not the thing it is a note about.
# On the Tire UİP these drew "Tescilli parsel" for 20 700 cadastral parcels.
NEVER_PROPOSE_PREFIXES = frozenset(("SM", "YAZI", "EKLE", "PINDEX", "PARSEL", "ADA", "NOKTA", "CIZPEN"))
NEVER_PROPOSE_WORDS = frozenset(("NOT",))
GEOMETRY_KINDS = {"MultiPolygon": "polygon", "Polygon": "polygon", "LineString": "line",
                  "MultiLineString": "line", "Point": "point", "MultiPoint": "point"}


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
    label: str = ""


@dataclass
class Target:
    """One MPYY function (a type and its code values) and every name it goes by."""
    key: str                  # a crosswalk key, or "fn:<Ek-1e record id>" when it has none
    entry: dict               # {"feature": ..., "attrs": {...}}
    geometry: str             # polygon | line | point | ""
    label: str                # the Ek-1e name when there is one
    names: list = field(default_factory=list)
    prefixes: set = field(default_factory=set)


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
    if key not in level_table(level).entries and key not in targets(level):
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
    # PL_ only says "plan layer": PL_ADAKENARI is ADAKENARI, PL_KALDIRIM is KALDIRIM.
    if name.startswith("PL_") and len(name) > 3:
        bases.setdefault(name[3:], "PL_ öneki")
    for base, why in list(bases.items()):
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
    if confirmed and confirmed in targets(level):
        return Match(str(tabaka), confirmed, targets(level)[confirmed].entry, "onayli")
    if name in table.skipped:
        return Match(str(tabaka), None, None, "yok", table.skipped[name])
    candidates = _rule_candidates(name, table)
    if len(candidates) == 1:
        key, rule = next(iter(candidates.items()))
        return Match(str(tabaka), key, table.entries[key], "kural", rule)
    return Match(str(tabaka), None, None, "yok",
                 "birden çok kural farklı satıra gidiyor" if candidates else "")


# --- proposals -------------------------------------------------------------------

def _split_code(code) -> str:
    """AritmaTesisi -> Aritma Tesisi; 3DereceArkeolojikSit -> 3 Derece Arkeolojik Sit."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])", " ", str(code))


def _words(text) -> list[str]:
    name = normalize_tabaka(_split_code(text) if re.search(r"[a-z][A-Z]", str(text)) else text)
    name = re.sub(r"(?<=[A-Z])(?=[0-9])|(?<=[0-9])(?=[A-Z])", "_", name)
    return [w for w in name.split("_") if w]


def _singular(word: str) -> str:
    """Plural and possessive endings off: TESISLERI -> TESIS, DEPOSU -> DEPO, SUYU -> SU."""
    for ending in PLURALS:
        if word.endswith(ending) and len(word) - len(ending) >= 4:
            word = word[: -len(ending)]
            break
    if word == "SUYU":
        return "SU"
    for ending in POSSESSIVES:
        if word.endswith(ending) and len(word) - len(ending) >= 3 and word[-3] in "AEIOU":
            return word[: -len(ending)]
    return word


_TARGET_CACHE: dict = {}


def targets(level: str) -> dict:
    """key -> Target for every MPYY function of ``level``: crosswalk rows and Ek-1e records."""
    cached = _TARGET_CACHE.get(level)
    if cached is not None:
        return cached
    geometry = {}
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["levels"].get(level, {})
        geometry = {t["name"]: GEOMETRY_KINDS.get(t.get("geometry") or "", "")
                    for t in schema.get("feature_types", [])}
    except (OSError, ValueError, KeyError):
        pass
    by_function: dict = {}

    def target_for(feature, attrs):
        # Only a real MPYY table can receive features: six Ek-1e road records name
        # "Yolorta + AdaKenari + DigerYolNesneleri", drawn by three tables at once.
        if geometry and feature not in geometry:
            return None
        ident = (feature, tuple(sorted(attrs.items())))
        if ident not in by_function:
            names = [_split_code(v) for v in attrs.values()] or [_split_code(feature)]
            by_function[ident] = Target("", {"feature": feature, "attrs": dict(attrs)},
                                        geometry.get(feature, ""), "", names)
        return by_function[ident]

    try:
        table = level_table(level)
    except (OSError, ValueError, KeyError):
        table = _Level({}, {})
    for key in sorted(table.entries, key=lambda k: (len(k), k)):
        entry = table.entries[key]
        target = target_for(entry["feature"], entry.get("attrs", {}))
        if target is None:
            continue
        target.key = target.key or key
        target.names.append(key)
        target.prefixes.add(key.split("_")[0])
    try:
        from .function_picker import plan_functions

        functions = plan_functions(level)
    except (OSError, ValueError, KeyError, ImportError):
        functions = []
    for function in functions:
        target = target_for(function.feature_type, dict(function.attrs))
        if target is None:
            continue
        target.key = target.key or "fn:" + function.record_id
        target.label = target.label or function.name
        target.names.append(function.name)
    result = {}
    for target in by_function.values():
        codes = ", ".join(_split_code(v) for v in target.entry["attrs"].values())
        target.label = target.label or _split_code(target.entry["feature"]) + (f" — {codes}" if codes else "")
        result[target.key] = target
    _TARGET_CACHE[level] = result
    return result


@dataclass
class _Vocabulary:
    words: set
    weight: dict           # word -> rarity weight (idf)
    target_words: dict     # target key -> [set of core words, one per name]


_VOCAB_CACHE: dict = {}


def _vocabulary(level: str) -> _Vocabulary:
    cached = _VOCAB_CACHE.get(level)
    if cached is not None:
        return cached
    per_target, counts = {}, {}
    for key, target in targets(level).items():
        names = []
        for name in target.names:
            core = {_singular(w) for w in _words(name)} - STOP_WORDS - LAYER_PREFIXES
            if core:
                names.append(core)
        per_target[key] = names
        for word in set().union(*names) if names else ():
            counts[word] = counts.get(word, 0) + 1
    total = max(len(per_target), 1)
    weight = {word: math.log(1 + total / n) for word, n in counts.items()}
    vocabulary = _Vocabulary(set(counts), weight, per_target)
    _VOCAB_CACHE[level] = vocabulary
    return vocabulary


def _segment(word: str, words: set) -> list[str]:
    """TESCILCEPHEKORUMA -> [TESCIL, CEPHE, KORUMA]: split on known words.

    Letters no known word covers stay together as one piece (CEPHE above); the
    split is kept only when known words cover at least two pieces and two
    thirds of the letters. A word with a listed meaning is never split
    (ORTAOGRETIM stays one word, it means lise)."""
    if len(word) < 8 or word in words or word in SYNONYMS:
        return [word]
    # best[i] = (unknown letters, pieces, list) for word[:i]
    best = {0: (0, 0, [])}
    for end in range(1, len(word) + 1):
        options = []
        if end - 1 in best:
            unknown, count, pieces = best[end - 1]
            if pieces and pieces[-1][1] is False:
                merged = pieces[:-1] + [(pieces[-1][0] + word[end - 1], False)]
                options.append((unknown + 1, count, merged))
            else:
                options.append((unknown + 1, count + 1, pieces + [(word[end - 1], False)]))
        for start in range(max(0, end - 20), end - 2):
            piece = word[start:end]
            if start in best and (piece in words or _singular(piece) in words):
                unknown, count, pieces = best[start]
                options.append((unknown, count + 1, pieces + [(piece, True)]))
        best[end] = min(options, key=lambda option: (option[0], option[1]))
    unknown, _count, pieces = best[len(word)]
    if sum(1 for _piece, known in pieces if known) < 2 or unknown > len(word) / 3:
        return [word]
    return [piece for piece, _known in pieces]


def _is_abbreviation(short: str, long: str) -> bool:
    """KULTR / KULTUR, VRLIGI / VARLIGI, REGULATR / REGULATOR, PLN / PLAN."""
    if len(short) < 3 or len(short) >= len(long) or short[0] != long[0] or len(short) < 0.55 * len(long):
        return False
    position = 0
    for letter in short:
        position = long.find(letter, position) + 1
        if position == 0:
            return False
    return True


def _word_match(word: str, other: str) -> tuple:
    """(strength, why) with which drawing ``word`` stands for vocabulary ``other``."""
    if word == other:
        return 1.0, ""
    if word.isdigit() or other.isdigit():
        return 0.0, ""
    if other in {_singular(w) for w in SYNONYMS.get(word, ())}:
        return 0.75, "eş anlam"
    short, long = sorted((word, other), key=len)
    if len(short) >= 4 and long.startswith(short) and len(short) >= 0.6 * len(long):
        return 0.85, "ek/kısaltma"
    if _is_abbreviation(word, other):
        return 0.8, "kısaltma"
    return 0.0, ""


def suggest(level: str, tabaka, limit: int = 5, minimum: float = 0.45,
            geometry: Optional[str] = None) -> list[Suggestion]:
    """Ranked proposals for a tabaka that did not resolve. Never applied by itself.

    ``geometry`` (polygon / line / point) keeps only the functions drawn that way.
    """
    name = normalize_tabaka(tabaka)
    raw = _words(name)
    if (not name or set(raw) & (NEVER_MATCH_TOKENS | NEVER_PROPOSE_WORDS)
            or (raw and raw[0] in NEVER_PROPOSE_PREFIXES)):
        return []
    vocabulary = _vocabulary(level)
    prefix = raw[0] if raw and raw[0] in LAYER_PREFIXES else ""
    words = []
    for word in raw:
        if word in LAYER_PREFIXES or word in STOP_WORDS or (len(word) == 1 and not word.isdigit()):
            continue
        base = word if word in SYNONYMS else _singular(word)
        for piece in _segment(base, vocabulary.words):
            piece = piece if piece in SYNONYMS else _singular(piece)
            if piece not in STOP_WORDS:
                words.append(piece)
    if not words:
        return []

    def weight(word):
        known = vocabulary.weight.get(word)
        if known is not None:
            return known
        related = [vocabulary.weight[w] for w in vocabulary.words if _word_match(word, w)[0]]
        if related:
            return max(related)
        # A word no function uses (PAZARLAMA, KDKCA): it still counts against every
        # proposal, half as much as a typical word, so a half-explained name ranks lower.
        ordered = sorted(vocabulary.weight.values())
        return 0.5 * ordered[len(ordered) // 2] if ordered else 1.0

    weights = {word: weight(word) for word in words}
    total = sum(weights.values()) or 1.0
    scored = []
    for key, target in targets(level).items():
        if geometry and target.geometry and target.geometry != geometry:
            continue
        best = (0.0, "")
        for core in vocabulary.target_words.get(key, []):
            found, reasons = 0.0, set()
            for word in words:
                value, why = max((_word_match(word, other) for other in core), default=(0.0, ""))
                found += value * weights[word]
                if value and why:
                    reasons.add(why)
            explained = sum(1 for other in core if any(_word_match(w, other)[0] for w in words)) / len(core)
            score = 0.8 * found / total + 0.2 * explained
            if score > best[0]:
                best = (score, ", ".join(sorted(reasons)) or "aynı kelimeler")
        score = best[0] + (0.05 if prefix and prefix in target.prefixes else 0.0)
        if score >= minimum:
            scored.append((score, key, target, best[1]))
    scored.sort(key=lambda row: (-row[0], row[1]))
    # One word that fits many functions says nothing about which: A_SINIR
    # ("boundary") drew "Önlemli alan" 0.93 on a municipal plan. Such a name is
    # left for a hand pick instead of an arbitrary top proposal.
    if len(set(words)) == 1 and len(scored) > AMBIGUOUS_SINGLE_WORD:
        return []
    return [Suggestion(key, target.entry, round(score, 2), reason, target.label)
            for score, key, target, reason in scored[:limit]]
