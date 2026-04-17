import re
from typing import List, Dict, Tuple, Optional

# Gender normalization map
_GENDER_MAP = {
    'm': 'M', 'male': 'M', 'man': 'M', 'boy': 'M', 'bf': 'M', 'boyfriend': 'M', 'husband': 'M',
    'f': 'F', 'female': 'F', 'woman': 'F', 'girl': 'F', 'gf': 'F', 'girlfriend': 'F', 'wife': 'F',
}

# Common relationship/person tokens to label entities
_ENTITY_ALIASES = {
    # self
    'i': 'me', 'me': 'me', 'myself': 'me',
    # partners by pronoun
    'he': 'him', 'him': 'him', 'his': 'him',
    'she': 'her', 'her': 'her',
    # partners by role
    'bf': 'him', 'boyfriend': 'him', 'fiance': 'him', 'fiancé': 'him', 'husband': 'him', 'partner': 'him',
    'gf': 'her', 'girlfriend': 'her', 'fiancee': 'her', 'wife': 'her',
}

# Precompiled regexes for performance
# Examples captured:
#   Me (21F), me [21f], boyfriend (25m), John (30M), him (31F)
#   Also tolerate spaces inside brackets and missing gender like (21)
_BRACKETED = re.compile(
    r"\b(?P<label>[A-Z][a-z]+|i|me|myself|he|him|his|she|her|bf|gf|boyfriend|girlfriend|husband|wife|partner|fiancee|fiance|fiancé)\s*"  # entity label
    r"[\(\[]\s*(?P<age>\d{1,2})\s*(?P<gender>[MmFf]|male|female)?\s*[\)\]]",
    flags=re.IGNORECASE,
)

# Also capture reversed inside brackets like [F21] occasionally seen; optional
_REVERSED_IN_BRACKETS = re.compile(
    r"\b(?P<label>[A-Z][a-z]+|i|me|myself|he|him|his|she|her|bf|gf|boyfriend|girlfriend|husband|wife|partner|fiancee|fiance|fiancé)\s*"  # entity label
    r"[\(\[]\s*(?P<gender>[MmFf]|male|female)\s*(?P<age>\d{1,2})\s*[\)\]]",
    flags=re.IGNORECASE,
)

# Examples without brackets next to role: "my boyfriend 20M", "my gf 22f"
_ROLE_INLINE = re.compile(
    r"\bmy\s+(?P<role>boyfriend|girlfriend|husband|wife|bf|gf|partner)\b[^\d\w]{0,10}(?P<age>\d{1,2})\s*(?P<gender>[MmFf]|male|female)?",
    flags=re.IGNORECASE,
)

# Lone bracketed age/gender without preceding label in the sentence start e.g., "(21F) and my boyfriend (23M)"
# We'll label the first as 'me' heuristically if it occurs near sentence start
_LONE_BRACKETED = re.compile(r"[\(\[]\s*(?P<age>\d{1,2})\s*(?P<gender>[MmFf]|male|female)?\s*[\)\]]")


def _norm_gender(g: Optional[str]) -> Optional[str]:
    if not g:
        return None
    g = g.strip().lower()
    return _GENDER_MAP.get(g, g.upper() if g in {"m", "f"} else None)


def _norm_entity(label: str) -> str:
    l = label.strip().lower()
    return _ENTITY_ALIASES.get(l, label)


def _make_record(entity: str, age: int, gender: Optional[str], source: str, span: Tuple[int, int], text: str) -> Dict:
    entity_norm = _norm_entity(entity)
    gender_norm = _norm_gender(gender)
    return {
        'entity': entity,
        'entity_norm': entity_norm,
        'age': int(age),
        'gender': gender_norm,
        'source': source,
        'span': span,
        'match_text': text[span[0]:span[1]],
    }


def extract_ages(text: str) -> List[Dict]:
    """
    Extract age (and optional gender) mentions tied to entities from a free-text string.

    Captures patterns like:
      - "Me (21F)", "me [21f]"
      - "him (31F)", "boyfriend (25m)"
      - "John (30M)" (capitalized names)
      - "my boyfriend 20M", "my gf 22f"
      - Lone bracket like "(21F) ..." near start will be labeled as 'me' heuristically

    Returns a list of dicts with keys:
      - entity (original token), entity_norm (normalized), age (int), gender ("M"/"F" or None),
        source (pattern id), span (start, end), match_text (verbatim)
    """
    if not text:
        return []

    out: List[Dict] = []

    # 1) Label (AgeGender) e.g., Me (21F)
    for m in _BRACKETED.finditer(text):
        out.append(_make_record(m.group('label'), int(m.group('age')), m.group('gender'), 'bracketed_label_age', m.span(), text))

    # 2) Label (GenderAge) e.g., Me (F21)
    for m in _REVERSED_IN_BRACKETS.finditer(text):
        out.append(_make_record(m.group('label'), int(m.group('age')), m.group('gender'), 'bracketed_label_gender_age', m.span(), text))

    # 3) my ROLE 21F (no brackets)
    for m in _ROLE_INLINE.finditer(text):
        role = m.group('role')
        out.append(_make_record(role, int(m.group('age')), m.group('gender'), 'role_inline', m.span(), text))

    # 4) Lone bracketed ages – heuristic for leading token means 'me'
    # Only if no overlapping match already captured at that span
    # We'll take only those within first 30 chars as 'me'
    for m in _LONE_BRACKETED.finditer(text):
        s, e = m.span()
        if s > 30:
            continue
        # Avoid overlaps
        if any(not (e <= r['span'][0] or s >= r['span'][1]) for r in out):
            continue
        out.append(_make_record('me', int(m.group('age')), m.group('gender'), 'lone_bracketed_early', (s, e), text))

    # Deduplicate identical spans (favor earlier sources)
    uniq: Dict[Tuple[int, int], Dict] = {}
    for r in out:
        uniq.setdefault(tuple(r['span']), r)
    return list(uniq.values())


def extract_ages_from_post(title: str, selftext: str) -> Dict[str, List[Dict]]:
    """
    Convenience to extract ages from both post title and selftext.
    """
    return {
        'title': extract_ages(title or ''),
        'selftext': extract_ages(selftext or ''),
    }


if __name__ == '__main__':
    sample = (
        "My boyfriend (20M) asked me (19F) what I rated myself 1-10, and then proceeded to tell me I’m an 8/10..."
    )
    print(extract_ages(sample))
