from jose import jwt

from app.config import settings
from tests.conftest import auth_header


def _token_for(user_id: int) -> str:
    return jwt.encode(
        {"sub": str(user_id), "exp": 9999999999},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_viewer_can_dashboard_cannot_records(client):
    viewer_token = _token_for(2)
    h = auth_header(viewer_token)
    r = client.get("/api/dashboard/summary", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "totals" in body
    r2 = client.get("/api/records", headers=h)
    assert r2.status_code == 403


def test_analyst_can_list_records(client):
    token = _token_for(3)
    r = client.get("/api/records", headers=auth_header(token))
    assert r.status_code == 200
    assert r.headers.get("X-Total-Count") == "0"


def test_admin_can_create_record(client):
    token = _token_for(1)
    h = auth_header(token)
    payload = {
        "amount": "100.50",
        "entry_type": "income",
        "category": "sales",
        "entry_date": "2026-03-15",
        "notes": "test",
    }
    r = client.post("/api/records", json=payload, headers=h)
    assert r.status_code == 201
    rid = r.json()["id"]
    r2 = client.get(f"/api/records/{rid}", headers=h)
    assert r2.status_code == 200
    r3 = client.get("/api/records", headers=auth_header(_token_for(3)))
    assert r3.status_code == 200
    assert len(r3.json()) == 1


def test_validation_error(client):
    token = _token_for(1)
    r = client.post(
        "/api/records",
        json={"amount": "-1", "entry_type": "income", "category": "x", "entry_date": "2026-01-01"},
        headers=auth_header(token),
    )
    assert r.status_code == 422


def test_viewer_can_meta_roles_cannot_analytics(client):
    v = auth_header(_token_for(2))
    assert client.get("/api/meta/roles", headers=v).status_code == 200
    assert client.get("/api/analytics/insights", headers=v).status_code == 403


def test_analyst_analytics_and_dashboard_totals(client):
    h = auth_header(_token_for(3))
    assert client.get("/api/dashboard/totals", headers=h).status_code == 200
    assert client.get("/api/analytics/insights", headers=h).status_code == 200


def test_record_stats_requires_analyst(client):
    assert (
        client.get("/api/records/stats/summary", headers=auth_header(_token_for(2))).status_code
        == 403
    )
