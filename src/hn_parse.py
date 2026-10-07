import re
ROLE_RE = re.compile(
    r"engineer|developer|scientist|analyst|manager|designer|architect|devops|"
    r"\bsre\b|researcher|\blead\b|director|head of|founding|\bintern(ship)?s?\b|"
    r"\bcto\b|product|\bdata\b|machine learning|\bml\b|\bai\b|\broles?\b|\bpositions?\b",
    re.I,
)
NON_TITLE_RE = re.compile(
    r"^(remote|onsite|on-site|hybrid|full[- ]?time|part[- ]?time|contract|visa|relocation)\b",
    re.I,
)
HIRING_RE = re.compile(
    r"(is|are|we.re|we are|now|currently) hiring|looking for|how to apply|recruit",
    re.I,
)
LABEL_RE = re.compile(r"^\s*(location|remote|company)\s*:", re.I | re.M)
CAREERS_RE = re.compile(r"/careers|/jobs|careers\.|jobs\.|greenhouse\.io|lever\.co|ashbyhq", re.I)
def pick_title(parts):
    for seg in parts[1:]:
        if not seg or len(seg) > 150:
            continue
        if NON_TITLE_RE.match(seg):
            continue
        if ROLE_RE.search(seg):
            return seg
    return None
def looks_like_job(text, parts):
    if not text:
        return False
    header = text.split("\n", 1)[0]
    if "|" in header[:200]:
        return True
    opening = text[:300]
    if "?" in opening[:200]:
        return False
    return bool(
        LABEL_RE.search(opening)
        or CAREERS_RE.search(text)
        or HIRING_RE.search(opening)
        or ROLE_RE.search(opening[:200])
    )
