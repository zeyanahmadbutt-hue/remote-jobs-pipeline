import logging
import sys
from pathlib import Path
import psycopg
import ingest
import normalize
import quality
import skills
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
log = logging.getLogger("pipeline")
def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
def main():
    setup_logging()
    log.info("pipeline started")
    try:
        ingest_code = ingest.main()
        normalize.main()
        skills.main()
        quality_code = quality.main()
    except psycopg.Error:
        log.exception("database step failed")
        return 1
    except Exception:
        log.exception("pipeline failed")
        return 1
    if quality_code:
        log.error("data quality checks failed")
        return 1
    if ingest_code:
        log.warning("partial run: at least one source failed")
        return 2
    log.info("pipeline finished OK")
    return 0
if __name__ == "__main__":
    sys.exit(main())
