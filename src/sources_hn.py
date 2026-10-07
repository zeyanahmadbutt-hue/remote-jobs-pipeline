def fetch_hn(session):
    search = session.get(
        "https://hn.algolia.com/api/v1/search_by_date",
        params={"tags": "story,author_whoishiring", "hitsPerPage": 10},
        timeout=30,
    )
    search.raise_for_status()
    threads = [h for h in search.json()["hits"]
               if "who is hiring" in h["title"].lower()]
    if not threads:
        raise ValueError("no who-is-hiring thread found")
    thread = threads[0]
    r = session.get(
        f"https://hn.algolia.com/api/v1/items/{thread['objectID']}",
        timeout=60,
    )
    r.raise_for_status()
    jobs = []
    for c in r.json().get("children", []):
        if not c.get("text"):
            continue
        payload = {k: c.get(k) for k in ("id", "text", "created_at", "created_at_i")}
        payload["thread_id"] = thread["objectID"]
        payload["thread_title"] = thread["title"]
        jobs.append((str(c["id"]), payload))
    return jobs
