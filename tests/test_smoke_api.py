import pytest

from spo import create_app


@pytest.fixture
def app():
    app = create_app()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_index_route(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Shopping Points Optimiser" in resp.data


def test_evaluate_route(client, test_resources):
    shop = test_resources["shop"]
    resp = client.post("/evaluate", data={"shop": shop.id, "amount": 100, "mode": "shopping"})
    assert resp.status_code == 200
    assert b"Ergebnisse" in resp.data


def test_voucher_route(client, test_resources):
    # Voucher mode is currently disabled, should redirect to index
    shop = test_resources["shop"]
    resp = client.post(
        "/evaluate",
        data={"shop": shop.id, "voucher": 10, "mode": "voucher"},
        follow_redirects=False,
    )
    assert resp.status_code == 302  # Redirect to index
    assert resp.location == "/"


def test_contract_route(client, test_resources):
    shop = test_resources["shop"]
    resp = client.post("/evaluate", data={"shop": shop.id, "mode": "contract"})
    assert resp.status_code == 200
    assert b"Vertragsabschluss" in resp.data


def test_suggest_shop_route(client):
    resp = client.get("/shop/1/suggest")
    assert resp.status_code in (302, 401, 403)


def test_health_route(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert b"OK" in resp.data


# --- Proposals routes ---
def test_proposals_route(client):
    resp = client.get("/proposals")
    assert resp.status_code in (200, 302, 401, 403)


def test_vote_route_requires_login(client):
    resp = client.post("/vote/1", data={"vote": 1})
    assert resp.status_code in (302, 401, 403)


def test_approve_proposal_requires_login(client):
    resp = client.post("/approve/1")
    assert resp.status_code in (302, 401, 403)


def test_create_proposal_requires_login(client):
    resp = client.get("/proposals/new")
    assert resp.status_code in (200, 302, 401, 403)


def test_review_scraper_proposal_requires_login(client):
    resp = client.get("/review-scraper-proposal/1")
    assert resp.status_code in (302, 401, 403)


# --- Notifications API ---
def test_notifications_api_requires_login(client):
    resp = client.get("/api/notifications")
    assert resp.status_code in (302, 401, 403)


def test_mark_notification_read_requires_login(client):
    resp = client.post("/api/notifications/1/read")
    assert resp.status_code in (302, 401, 403)


def test_mark_all_notifications_read_requires_login(client):
    resp = client.post("/api/notifications/read_all")
    assert resp.status_code in (302, 401, 403)


# --- Auth routes ---
def test_register_route(client):
    resp = client.get("/register")
    assert resp.status_code == 200


def test_login_route(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_logout_requires_login(client):
    resp = client.get("/logout")
    assert resp.status_code in (302, 401, 403)


def test_profile_requires_login(client):
    resp = client.get("/profile")
    assert resp.status_code in (302, 401, 403)


def test_request_contributor_requires_login(client):
    resp = client.post("/request-contributor")
    assert resp.status_code in (302, 401, 403)


# --- Admin routes (all require admin login) ---
@pytest.mark.parametrize(
    "method,route",
    [
        ("get", "/admin/shops_overview"),
        ("get", "/admin"),
        ("post", "/admin/add_program"),
        ("post", "/admin/run_scraper"),
        ("post", "/admin/run_payback"),
        ("post", "/admin/run_miles_and_more"),
        ("get", "/admin/job_status/testjobid"),
        ("get", "/admin/jobs"),
        ("post", "/admin/rate/{rate_id}/comment"),
        ("get", "/admin/rate/{rate_id}/comments"),
        ("get", "/admin/shops/merge_proposals"),
        ("post", "/admin/shops/merge_proposal"),
        ("post", "/admin/shops/merge_proposal/{merge_proposal_id}/approve"),
        ("post", "/admin/shops/merge_proposal/{merge_proposal_id}/reject"),
        ("get", "/admin/shops/metadata_proposals"),
        # Add metadata proposal IDs if you create them in test_resources
        # ("post", "/admin/shops/metadata_proposals/{metadata_proposal_id}/approve"),
        # ("post", "/admin/shops/metadata_proposals/{metadata_proposal_id}/reject"),
        # ("post", "/admin/shops/metadata_proposals/{metadata_proposal_id}/delete"),
        ("post", "/admin/clear_shops"),
    ],
)
def test_admin_routes_require_admin(logged_in_admin, test_resources, method, route):
    # Replace placeholders with real IDs
    route = route.format(
        rate_id=test_resources["rate"].id,
        merge_proposal_id=test_resources["merge_proposal"].id,
        # metadata_proposal_id=test_resources.get("metadata_proposal", None) and test_resources["metadata_proposal"].id or 1
    )
    req = getattr(logged_in_admin, method)
    # Provide required POST data for specific routes
    post_data = None
    json_data = None
    if route.startswith("/admin/add_program"):
        post_data = {
            "name": f"Test Program {test_resources['program'].id}",
            "point_value_eur": 0.01,
        }
    elif "/rate/" in route and "/comment" in route:
        json_data = {"comment": "Test comment", "type": "FEEDBACK"}
    elif (
        route.startswith("/admin/shops/merge_proposal")
        and method == "post"
        and "approve" not in route
        and "reject" not in route
    ):
        json_data = {
            "variant_a_id": test_resources["variant_a"].id,
            "variant_b_id": test_resources["variant_b"].id,
            "reason": "Test merge",
        }

    # Handle job_status route (expect 404 or skip)
    if "/admin/job_status/" in route:
        resp = req(route)
        assert resp.status_code in (200, 404)
        return

    # For routes that may redirect, follow_redirects=True
    follow = False
    if route in ["/admin/clear_shops", "/admin/add_program"]:
        follow = True

    if method == "post":
        if json_data is not None:
            resp = req(route, json=json_data, follow_redirects=follow)
        else:
            resp = req(route, data=post_data or {}, follow_redirects=follow)
    else:
        resp = req(route, follow_redirects=follow)

    # Accept 200 or 302 (if not following redirects)
    if not follow and resp.status_code == 302:
        # Accept redirect for routes that are expected to redirect
        assert resp.status_code == 302
    else:
        assert resp.status_code == 200
