import sys
from datetime import datetime, timezone
from db import get_conn, init_schema
EXPECTED_KEYS = {
    "arbeitnow": {"slug", "company_name", "title", "description", "remote",
                  "url", "tags", "job_types", "location", "created_at"},
    "remotive": {"id", "url", "title", "company_name", "company_logo",
                 "category", "tags", "job_type", "publication_date",
                 "candidate_required_location", "salary", "description",
                 "company_logo_url"},
    "hn_whoishiring": {"id", "text", "created_at", "created_at_i",
                       "thread_id", "thread_title"},
}
NULL_COLUMNS = ["title", "company", "posted_at", "url", "description"]
def grade(value, warn, fail):
    if value >= fail:
        return "FAIL"
    if value >= warn:
        return "WARN"
    return "PASS"
def run_checks(conn):
    results = []
    def add(check, source, value, status, detail=""):
        results.append((check, source, float(value), status, detail))
    raw = dict(conn.execute(
        "SELECT source, count(*) FROM raw_jobs GROUP BY 1").fetchall())
    norm = dict(conn.execute(
        "SELECT source, count(*) FROM jobs GROUP BY 1").fetchall())
    for s in sorted(raw):
        n = norm.get(s, 0)
        add("completeness_raw_vs_clean", s, n,
            "PASS" if n == raw[s] else "FAIL", f"raw={raw[s]} clean={n}")
    for col in NULL_COLUMNS:
        rows = conn.execute(
            f"SELECT source, avg((({col} IS NULL) OR ({col}::text = ''))::int) "
            f"FROM jobs WHERE is_job_posting GROUP BY 1").fetchall()
        for s, v in rows:
            add(f"null_rate_{col}", s, v, grade(float(v), 0.20, 0.60))
    for s, hrs in conn.execute(
        "SELECT source, extract(epoch FROM now() - max(last_seen_at)) / 3600 "
        "FROM raw_jobs GROUP BY 1"
    ).fetchall():
        add("hours_since_last_fetch", s, hrs, grade(float(hrs), 48, 168))
    for s, dups, total in conn.execute(
        "SELECT source, count(*) - count(DISTINCT (lower(company), lower(title), lower(location))), count(*) "
        "FROM jobs WHERE is_job_posting AND company IS NOT NULL AND title IS NOT NULL "
        "GROUP BY 1"
    ).fetchall():
        rate = dups / total if total else 0
        add("duplicate_rate_within_source", s, rate, grade(rate, 0.05, 0.20),
            f"{dups} of {total}")
    cross = conn.execute(
        "SELECT count(*) FROM (SELECT 1 FROM jobs "
        "WHERE company IS NOT NULL AND title IS NOT NULL "
        "GROUP BY lower(company), lower(title) "
        "HAVING count(DISTINCT source) > 1) t").fetchone()[0]
    add("cross_source_duplicates", "all", cross, "INFO",
        "company+title pairs seen in 2+ sources")
    for s, v in conn.execute(
        "SELECT source, avg((remote_status = 'unknown')::int) "
        "FROM jobs WHERE is_job_posting GROUP BY 1"
    ).fetchall():
        add("unknown_remote_status_rate", s, v, grade(float(v), 0.15, 0.40))
    for s, v in conn.execute(
        "SELECT source, avg((salary_raw IS NOT NULL)::int) "
        "FROM jobs WHERE is_job_posting GROUP BY 1"
    ).fetchall():
        add("salary_present_rate", s, v, "INFO")
    for s, v in conn.execute(
        "SELECT source, avg((NOT is_job_posting)::int) FROM jobs GROUP BY 1"
    ).fetchall():
        add("non_job_rate", s, v, "INFO")
    for s, expected in EXPECTED_KEYS.items():
        keys = {r[0] for r in conn.execute(
            "SELECT DISTINCT k FROM raw_jobs, jsonb_object_keys(payload) k "
            "WHERE source = %s", (s,)).fetchall()}
        new = sorted(keys - expected)
        add("schema_drift_new_keys", s, len(new),
            "WARN" if new else "PASS", ",".join(new))
    return results
def main():
    run_at = datetime.now(timezone.utc)
    with get_conn() as conn:
        init_schema(conn)
        results = run_checks(conn)
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO quality_checks "
                "(run_at, check_name, source, value, status, detail) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [(run_at, *r) for r in results])
        conn.commit()
    for check, source, value, status, detail in sorted(results, key=lambda r: (r[0], r[1])):
        print(f"{status:<5} {check:<30} {source:<15} {value:>9.3f}  {detail}")
    counts = {s: sum(1 for r in results if r[3] == s)
              for s in ("PASS", "WARN", "FAIL", "INFO")}
    print("summary:", counts)
    return 1 if counts["FAIL"] else 0
if __name__ == "__main__":
    sys.exit(main())

