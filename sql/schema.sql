CREATE TABLE IF NOT EXISTS raw_jobs (
    source         TEXT        NOT NULL,
    source_job_id  TEXT        NOT NULL,
    payload        JSONB       NOT NULL,
    first_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, source_job_id)
);
CREATE TABLE IF NOT EXISTS jobs (
    source         TEXT        NOT NULL,
    source_job_id  TEXT        NOT NULL,
    title          TEXT,
    company        TEXT,
    location       TEXT,
    remote_status  TEXT        NOT NULL,
    posted_at      TIMESTAMPTZ,
    url            TEXT,
    description    TEXT,
    salary_raw     TEXT,
    category       TEXT,
    normalized_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, source_job_id)
);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_job_posting BOOLEAN NOT NULL DEFAULT TRUE;
CREATE TABLE IF NOT EXISTS quality_checks (
    run_at      TIMESTAMPTZ NOT NULL,
    check_name  TEXT        NOT NULL,
    source      TEXT        NOT NULL,
    value       DOUBLE PRECISION,
    status      TEXT        NOT NULL,
    detail      TEXT
);
CREATE TABLE IF NOT EXISTS job_skills (
    source        TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    skill         TEXT NOT NULL,
    PRIMARY KEY (source, source_job_id, skill)
);
