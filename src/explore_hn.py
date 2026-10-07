import json
import pathlib
import re
import sys
import requests
sys.stdout.reconfigure(encoding="utf-8")
OUT = pathlib.Path("data/samples")
OUT.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "remote-jobs-pipeline (learning project)"}
def fetch(url, name):
    f = OUT / name
    if not f.exists():
        r = requests.get(url, timeout=60, headers=HEADERS)
        r.raise_for_status()
        f.write_text(r.text, encoding="utf-8")
    return json.loads(f.read_text(encoding="utf-8"))
search = fetch(
    "https://hn.algolia.com/api/v1/search_by_date"
    "?tags=story,author_whoishiring&hitsPerPage=10",
    "hn_search.json",
)
hits = [h for h in search["hits"] if "who is hiring" in h["title"].lower()]
latest = hits[0]
print("thread:", latest["title"], "| id:", latest["objectID"])
thread = fetch(
    f"https://hn.algolia.com/api/v1/items/{latest['objectID']}",
    f"hn_{latest['objectID']}.json",
)
kids = [c for c in thread.get("children", []) if c.get("text")]
remote = sum("remote" in c["text"].lower() for c in kids)
print("top-level postings:", len(kids), "| mention 'remote':", remote)
print("keys of one posting:", list(kids[0].keys()))
for c in kids[:3]:
    text = re.sub(r"<[^>]+>", " ", c["text"]).replace("\n", " ")
    print("---")
    print(text[:250])
