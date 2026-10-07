# Remote Jobs Pipeline

A data pipeline that collects job postings from three public sources, stores them untouched in a raw layer, normalizes them into one schema, extracts skills from the job text, and runs a data quality report on every run.

Question it answers: **which skills do remote tech postings ask for most?**

## Data sources

| Source | What it is | Notes |
|---|---|---|
| [Arbeitnow](https://www.arbeitnow.com) | Free public job board API | General board, mostly on-site jobs; only a small share is remote |
| [Remotive](https://remotive.com) | Public remote jobs API | Jobs are credited to Remotive and link back to the original posting. The API terms allow about 4 fetches per day, so the ingest step skips Remotive if it was fetched in the last 6 hours |
| [Hacker News "Who is hiring?"](https://news.ycombinator.com/) via the official Algolia API | Monthly thread of free-text postings | Tech-heavy and messy: every company writes its posting differently |

Raw data and logs are kept out of git (see `.gitignore`), because Remotive's terms do not allow republishing their jobs.

## Flow

```
ingest.py -> raw_jobs (JSONB, unchanged)
          -> normalize.py -> jobs (one schema)
          -> skills.py -> job_skills
          -> quality.py -> quality_checks (PASS / WARN / FAIL)
```

`pipeline.py` runs all four steps in order, logs to `logs/pipeline.log`, and returns an exit code: `0` success, `1` failure (including any failed quality check), `2` partial run (a source failed).

## Design decisions

- **Raw layer first.** Every API response is stored as JSONB exactly as received. If the cleaning logic has a bug, it can be re-run on the original data.
- **Idempotent writes.** Primary keys on `(source, source_job_id)` plus `INSERT ... ON CONFLICT DO UPDATE`, so re-runs never create duplicates, and `first_seen_at` / `last_seen_at` record how long a job stays posted.
- **Honest NULLs.** A Hacker News posting with no role in its header gets no title, not a guessed one.
- **Rule-based parsing of free text,** with every rule measured by the quality report instead of trusted blindly.
- **Non-job filtering.** Replies and comments in the Hacker News thread are flagged with `is_job_posting = false` and excluded from analysis.
- **Rate-limit guard.** Sources are skipped if fetched recently (`--force` overrides this).

## Data quality checks

Each run stores the results in `quality_checks`. Checks cover completeness (raw rows vs clean rows), null rates, freshness, duplicates within a source (a job in several cities counts as separate jobs), unknown remote-status rate, and schema drift (new fields in an API). Latest run: **29 PASS, 1 WARN, 0 FAIL.**

The one warning is real: about 28% of Hacker News postings never state a role in the header line, so their title stays empty.

## Results (one run, October 2026)

999 raw postings: 749 from Arbeitnow, 232 from Hacker News, 18 from Remotive. 220 were remote or hybrid, and 109 of those mentioned at least one skill from the dictionary.

Most mentioned skills among remote and hybrid postings: Python (55), Postgres (35), LLM (30), AWS (19), Java (18), Kubernetes (18), Rust (18), SQL (15).

**Limits:** about 70% of the remote sample comes from Hacker News, which skews toward startups and engineers, so this describes remote tech postings on Hacker News in one month, not the whole job market. Skills are matched with keyword rules, which undercount and cannot judge context. Counts below about 10 are noise.

## Setup

1. Install Python 3.11+ and PostgreSQL 16, then create a database named `remotejobs`.
2. Create `.env` in the project root:

        POSTGRES_USER=postgres
        POSTGRES_PASSWORD=your_password
        POSTGRES_DB=remotejobs
        POSTGRES_HOST=localhost
        POSTGRES_PORT=5432

3. Install and run:

        python -m venv .venv
        .venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        python src\pipeline.py
        pytest

## Scheduling

Runs daily through Windows Task Scheduler.

## Example query

    SELECT skill, count(*) AS jobs
    FROM job_skills s
    JOIN jobs j USING (source, source_job_id)
    WHERE j.remote_status IN ('remote', 'hybrid')
    GROUP BY skill
    ORDER BY jobs DESC
    LIMIT 10;
