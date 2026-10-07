import re
from db import get_conn, init_schema
SKILL_PATTERNS = {
    "python": r"\bpython\b",
    "sql": r"\bsql\b",
    "postgres": r"\bpostgres(ql)?\b",
    "mysql": r"\bmysql\b",
    "mongodb": r"\bmongo(db)?\b",
    "redis": r"\bredis\b",
    "spark": r"\b(apache spark|pyspark)\b",
    "airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "kafka": r"\bkafka\b",
    "snowflake": r"\bsnowflake\b",
    "bigquery": r"\bbig ?query\b",
    "etl/elt": r"\b(etl|elt)\b",
    "aws": r"\baws\b",
    "gcp": r"\b(gcp|google cloud)\b",
    "azure": r"\bazure\b",
    "docker": r"\bdocker\b",
    "kubernetes": r"\b(kubernetes|k8s)\b",
    "terraform": r"\bterraform\b",
    "pytorch": r"\bpytorch\b",
    "tensorflow": r"\btensorflow\b",
    "machine learning": r"\bmachine learning\b",
    "llm": r"\b(llms?|large language models?)\b",
    "rag": r"\brag\b",
    "nlp": r"\bnlp\b",
    "langchain": r"\blang ?chain\b",
    "mlops": r"\bmlops\b",
    "pandas": r"\bpandas\b",
    "numpy": r"\bnumpy\b",
    "scikit-learn": r"\b(scikit-learn|sklearn)\b",
    "fastapi": r"\bfastapi\b",
    "django": r"\bdjango\b",
    "flask": r"\bflask\b",
    "git": r"\bgit\b",
    "linux": r"\blinux\b",
    "java": r"\bjava\b",
    "scala": r"\bscala\b",
    "rust": r"\brust\b",
    "golang": r"\bgolang\b",
}
COMPILED = {k: re.compile(v, re.I) for k, v in SKILL_PATTERNS.items()}
def extract_skills(text):
    return sorted(k for k, rx in COMPILED.items() if rx.search(text or ""))
def main():
    with get_conn() as conn:
        init_schema(conn)
        jobs = conn.execute(
            "SELECT source, source_job_id, coalesce(title,'') || E'\n' || coalesce(description,'') "
            "FROM jobs WHERE is_job_posting"
        ).fetchall()
        rows = [(s, jid, skill) for s, jid, text in jobs for skill in extract_skills(text)]
        with conn.cursor() as cur:
            cur.execute("DELETE FROM job_skills")
            cur.executemany(
                "INSERT INTO job_skills (source, source_job_id, skill) VALUES (%s, %s, %s)",
                rows,
            )
        conn.commit()
    print(f"jobs scanned: {len(jobs)} | skill tags stored: {len(rows)}")
if __name__ == "__main__":
    main()
