import html
import re
from datetime import datetime, timezone
from db import get_conn, init_schema
from hn_parse import pick_title, looks_like_job
TAG_RE = re.compile(r"<[^>]+>")
SALARY_RE = re.compile(
    r"\$\s?\d[\d,\.]*\s?[kK]?"
    r"(?:\s*(?:-|to|\u2013)\s*\$?\s?\d[\d,\.]*\s?[kK]?)?"
)
NEGATIVE_RE = re.compile(
    r"\b(no remote|not remote|remote not|onsite only|on-site only|in-person only)\b"
)
UPSERT_SQL = """
INSERT INTO jobs (source, source_job_id, title, company, location,
                  remote_status, posted_at, url, description, salary_raw, category, is_job_posting)
VALUES (%(source)s, %(source_job_id)s, %(title)s, %(company)s, %(location)s,
        %(remote_status)s, %(posted_at)s, %(url)s, %(description)s,
        %(salary_raw)s, %(category)s, %(is_job_posting)s)
ON CONFLICT (source, source_job_id) DO UPDATE SET
    title = EXCLUDED.title, company = EXCLUDED.company,
    location = EXCLUDED.location, remote_status = EXCLUDED.remote_status,
    posted_at = EXCLUDED.posted_at, url = EXCLUDED.url,
    description = EXCLUDED.description, salary_raw = EXCLUDED.salary_raw,
    category = EXCLUDED.category, is_job_posting = EXCLUDED.is_job_posting, normalized_at = now()
"""
def strip_html(raw):
    if not raw:
        return ""
    raw = re.sub(r"<\s*(p|br|li|div)[^>]*>", "\n", raw, flags=re.I)
    text = html.unescape(TAG_RE.sub(" ", raw))
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)
def clean(value):
    value = (value or "").strip()
    return value or None
def normalize_arbeitnow(job_id, p):
    return {
        "source": "arbeitnow", "source_job_id": job_id,
        "title": clean(p.get("title")),
        "company": clean(p.get("company_name")),
        "location": clean(p.get("location")),
        "remote_status": "remote" if p.get("remote") else "not_remote",
        "posted_at": datetime.fromtimestamp(int(p["created_at"]), tz=timezone.utc)
        if p.get("created_at") else None,
        "url": p.get("url"),
        "description": strip_html(p.get("description")),
        "salary_raw": None,
        "category": clean((p.get("tags") or [None])[0]),
    }
def normalize_remotive(job_id, p):
    posted = None
    if p.get("publication_date"):
        posted = datetime.fromisoformat(p["publication_date"]).replace(tzinfo=timezone.utc)
    return {
        "source": "remotive", "source_job_id": job_id,
        "title": clean(p.get("title")),
        "company": clean(p.get("company_name")),
        "location": clean(p.get("candidate_required_location")),
        "remote_status": "remote",
        "posted_at": posted,
        "url": p.get("url"),
        "description": strip_html(p.get("description")),
        "salary_raw": clean(p.get("salary")),
        "category": clean(p.get("category")),
    }
def hn_remote_status(text):
    head = text[:300].lower()
    if NEGATIVE_RE.search(head):
        return "not_remote"
    if "hybrid" in head or ("remote" in head and re.search(r"on-?site|on site|in[- ]person|in[- ]office", head)):
        return "hybrid"
    if "remote" in head:
        return "remote"
    if re.search(r"on-?site|on site|in[- ]person|in[- ]office", head):
        return "not_remote"
    return "unknown"
def normalize_hn(job_id, p):
    text = strip_html(p.get("text"))
    header = text.split("\n", 1)[0] if text else ""
    if "|" in header[:200]:
        parts = [x.strip() for x in header.split("|")]
    else:
        parts = [x.strip() for x in re.split(r"\s[\u2014\u2013-]\s", header)]
    company = re.sub(r"https?://\S+", "", re.sub(r"\(.*?\)", "", parts[0])).strip() if parts else None
    if not company or len(company) > 80:
        company = None
    title = pick_title(parts)
    salary = SALARY_RE.search(text[:400])
    posted = None
    if p.get("created_at_i"):
        posted = datetime.fromtimestamp(int(p["created_at_i"]), tz=timezone.utc)
    return {
        "source": "hn_whoishiring", "source_job_id": job_id,
        "title": title, "company": company, "location": None,
        "remote_status": hn_remote_status(text),
        "posted_at": posted,
        "url": f"https://news.ycombinator.com/item?id={job_id}", "is_job_posting": looks_like_job(text, parts),
        "description": text,
        "salary_raw": salary.group(0).strip() if salary else None,
        "category": None,
    }
NORMALIZERS = {
    "arbeitnow": normalize_arbeitnow,
    "remotive": normalize_remotive,
    "hn_whoishiring": normalize_hn,
}
def main():
    with get_conn() as conn:
        init_schema(conn)
        rows = conn.execute(
            "SELECT source, source_job_id, payload FROM raw_jobs"
        ).fetchall()
        out = [{"is_job_posting": True, **NORMALIZERS[s](jid, p)} for s, jid, p in rows]
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, out)
        conn.commit()
    print("normalized rows:", len(out))
if __name__ == "__main__":
    main()




