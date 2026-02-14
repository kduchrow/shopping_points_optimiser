import io
import json
import uuid

import pytest

from spo.extensions import db
from spo.models import BonusProgram, Shop, ShopMain


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def setex(self, key, ttl, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        self.store.pop(key, None)


def _create_shop(name: str) -> Shop:
    shop_main = ShopMain(
        canonical_name=name,
        canonical_name_lower=name.lower(),
        status="active",
    )
    shop_main.id = str(uuid.uuid4())
    db.session.add(shop_main)
    db.session.commit()

    shop = Shop(name=name, shop_main_id=shop_main.id)
    db.session.add(shop)
    db.session.commit()
    return shop


def _upload_payload(client, payload):
    return client.post(
        "/admin/import_coupons/preview",
        data={"file": (io.BytesIO(json.dumps(payload).encode("utf-8")), "coupons.json")},
        content_type="multipart/form-data",
    )


@pytest.mark.usefixtures("logged_in_admin")
def test_coupon_import_preview_returns_rows_with_suggestions(monkeypatch, client):
    fake_redis = _FakeRedis()
    from spo.routes.admin import jobs as jobs_module

    monkeypatch.setattr(jobs_module, "get_redis_connection", lambda: fake_redis)

    program = BonusProgram(name="Corporate Benefits", point_value_eur=0.01)
    db.session.add(program)
    db.session.commit()

    shop = _create_shop("RTL+")

    payload = {
        "program": "Corporate Benefits",
        "coupons": [{"merchant": "RTL+", "discount_text": "< 33% Rabatt", "value": 33}],
    }

    resp = _upload_payload(client, payload)
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["coupon_count"] == 1
    assert "rows" in data
    row = data["rows"][0]
    assert row["merchant"] == "RTL+"
    assert row["matched_shop_id"] == shop.id
    assert any(s["id"] == shop.id for s in row["suggestions"])


@pytest.mark.usefixtures("logged_in_admin")
def test_coupon_import_confirm_uses_selected_rows(monkeypatch, client):
    fake_redis = _FakeRedis()
    from spo.routes.admin import jobs as jobs_module

    monkeypatch.setattr(jobs_module, "get_redis_connection", lambda: fake_redis)

    captured = {}

    def _fake_enqueue(payload, requested_by):
        captured["payload"] = payload
        captured["requested_by"] = requested_by
        return "job-123"

    monkeypatch.setattr(jobs_module, "enqueue_coupon_import_job", _fake_enqueue)

    program = BonusProgram(name="Corporate Benefits", point_value_eur=0.01)
    db.session.add(program)
    db.session.commit()

    shop = _create_shop("RTL+")

    payload = {
        "program": "Corporate Benefits",
        "coupons": [
            {"merchant": "RTL+", "discount_text": "< 33% Rabatt", "value": 33},
            {"merchant": "Unknown Shop", "discount_text": "10%", "value": 10},
        ],
    }

    preview = _upload_payload(client, payload).get_json()
    token = preview["token"]

    confirm_resp = client.post(
        "/admin/import_coupons/confirm",
        json={
            "token": token,
            "selections": [{"index": 0, "shop_id": shop.id, "merchant": "RTL+"}],
        },
    )
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.get_json()
    assert confirm_data["job_id"] == "job-123"

    assert captured["payload"]["program"] == "Corporate Benefits"
    coupons = captured["payload"]["coupons"]
    assert len(coupons) == 1
    assert coupons[0]["shop_id"] == shop.id
    assert coupons[0]["merchant"] == "RTL+"
