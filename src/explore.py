import json
import pathlib
import requests
OUT = pathlib.Path("data/samples")
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = {
    "arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "remotive": "https://remotive.com/api/remote-jobs?limit=50",
}
def get(name, url):
    f = OUT / f"{name}.json"
    if not f.exists():
        r = requests.get(url, timeout=30,
                         headers={"User-Agent": "remote-jobs-pipeline (learning project)"})
        r.raise_for_status()
        f.write_text(r.text, encoding="utf-8")
    return json.loads(f.read_text(encoding="utf-8"))
for name, url in SOURCES.items():
    data = get(name, url)
    jobs = data.get("data") or data.get("jobs") or []
    print(name, "| top keys:", list(data.keys()), "| jobs:", len(jobs))
    if jobs:
        print("  job keys:", list(jobs[0].keys()))
