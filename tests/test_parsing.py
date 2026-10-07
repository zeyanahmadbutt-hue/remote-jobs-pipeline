from hn_parse import looks_like_job, pick_title
from normalize import hn_remote_status, strip_html
from skills import extract_skills
def test_pick_title_skips_work_mode_labels():
    assert pick_title(["Shepherd", "ONSITE", "San Francisco, CA"]) is None
def test_pick_title_finds_role():
    parts = ["Sidekick Labs", "Senior SWE, R&D Engineer", "REMOTE", "Full-time"]
    assert "Engineer" in pick_title(parts)
def test_pipe_header_is_a_job():
    assert looks_like_job("Acme | Remote | Engineer\nWe build things.", [])
def test_reply_with_question_is_not_a_job():
    text = "So people are basically only interested in hiring seniors ? Jesus."
    assert not looks_like_job(text, [])
def test_remote_status_remote():
    assert hn_remote_status("Sidekick | REMOTE (US) | Full-time") == "remote"
def test_remote_status_hybrid_when_both_mentioned():
    assert hn_remote_status("OpenRent | London | ONSITE+PART REMOTE") == "hybrid"
def test_remote_status_not_remote():
    assert hn_remote_status("Brain Corp | Engineering | San Diego CA | Onsite") == "not_remote"
def test_remote_status_unknown():
    assert hn_remote_status("ko-br | Engineering, sales | San Francisco, CA") == "unknown"
def test_strip_html():
    assert strip_html("<p>Hello&amp; <b>world</b></p>") == "Hello& world"
def test_skills_found():
    found = extract_skills("We use Python, PostgreSQL and Apache Spark on AWS")
    assert found == ["aws", "postgres", "python", "spark"]
def test_skills_ignore_ambiguous_words():
    assert extract_skills("We go fast and react quickly") == []
