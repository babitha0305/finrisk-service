from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["tickers"] == 8


def test_search_returns_ranked_results_with_themes():
    r = client.get("/search", params={"q": "ransomware outage", "k": 3})
    body = r.json()
    assert r.status_code == 200 and len(body["results"]) == 3
    assert body["results"][0]["id"] == "VNTG-2"
    assert body["results"][0]["score"] >= body["results"][1]["score"]


def test_search_validates_input():
    assert client.get("/search", params={"q": "x"}).status_code == 422
    assert client.get("/search", params={"q": "valid query", "k": 99}).status_code == 422


def test_risk_endpoint_and_404():
    ok = client.get("/risk/hlxb").json()
    assert ok["ticker"] == "HLXB" and ok["ann_volatility"] > 0
    assert client.get("/risk/NOPE").status_code == 404


def test_screen_joins_themes_to_volatility_sorted_desc():
    rows = client.get("/screen", params={"theme": "cyber"}).json()["results"]
    assert {r["ticker"] for r in rows} == {"NWFR", "LMNR", "VNTG"}
    vols = [r["ann_volatility"] for r in rows]
    assert vols == sorted(vols, reverse=True)


def test_request_id_header_and_metrics_exposed():
    r = client.get("/health", headers={"x-request-id": "abc123"})
    assert r.headers["x-request-id"] == "abc123"
    client.get("/search", params={"q": "zzzz qqqq xxxx"})  # no-match query -> low confidence
    text = client.get("/metrics").text
    assert 'http_requests_total{method="GET",path="/health",status="200"}' in text
    assert "http_request_duration_seconds_bucket" in text
    assert "retrieval_low_confidence_total" in text
