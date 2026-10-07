import logging
import sys
import time
import requests
from psycopg.types.json import Jsonb
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from db import get_conn, init_schema
from sources_hn import fetch_hn
log = logging.getLogger("ingest")
HEADERS = {"User-Agent": "remote-jobs-pipeline (learning project)"}
MIN_HOURS = {"arbeitnow": 1, "remotive": 6, "hn_whoishiring": 6}
UPSERT_SQL = """
INSERT INTO raw_jobs (source, source_job_id, payload)
VALUES (%s, %s, %s)
ON CONFLICT (source, source_job_id) DO UPDATE SET
    payload = EXCLUDED.payload,
    last_seen_at = now()
"""
def make_session():
    retry = Retry(total=3, backoff_factor=2,
                  status_forcelist=[500, 502, 503, 504])
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session
def fetch_arbeitnow(session, max_pages=3):
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    for _ in range(max_pages):
        r = session.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        jobs.extend((j["slug"], j) for j in data.get("data", []))
        url = (data.get("links") or {}).get("next")
        if not url:
            break
        time.sleep(1)
    return jobs
def fetch_remotive(session):
    r = session.get("https://remotive.com/api/remote-jobs", timeout=30)
    r.raise_for_status()
    return [(str(j["id"]), j) for j in r.json().get("jobs", [])]
FETCHERS = {"arbeitnow": fetch_arbeitnow, "remotive": fetch_remotive, "hn_whoishiring": fetch_hn}
def recently_fetched(conn, source, hours):
    row = conn.execute(
        "SELECT max(last_seen_at) > now() - make_interval(hours => %s) "
        "FROM raw_jobs WHERE source = %s",
        (hours, source),
    ).fetchone()
    return bool(row[0])
def store(conn, source, jobs):
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL,
                        [(source, jid, Jsonb(p)) for jid, p in jobs])
    conn.commit()
    return len(jobs)
def main(force=False):
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    session = make_session()
    failed = 0
    with get_conn() as conn:
        init_schema(conn)
        for source, fetch in FETCHERS.items():
            if not force and recently_fetched(conn, source, MIN_HOURS[source]):
                log.info("skipping %s: fetched recently", source)
                continue
            try:
                jobs = fetch(session)
            except (requests.RequestException, ValueError):
                log.exception("fetch failed for %s", source)
                failed += 1
                continue
            log.info("stored %d raw jobs from %s", store(conn, source, jobs), source)
    return 2 if failed else 0
if __name__ == "__main__":
    sys.exit(main(force="--force" in sys.argv))

