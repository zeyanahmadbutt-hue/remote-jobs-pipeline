import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv
load_dotenv()
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
def get_conn():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
def init_schema(conn):
    conn.execute(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    conn.commit()
