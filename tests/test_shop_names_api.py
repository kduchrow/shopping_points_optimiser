"""
Test for the /shop_names API endpoint.
"""


def test_shop_names_api(client, app, shop_test_data):
    """Test the /shop_names API endpoint returns filtered shop names as JSON."""
    # Test with no query (should return all or limited shops)
    resp = client.get("/shop_names")
    assert resp.status_code == 200
    data = resp.get_json()
    if isinstance(data, dict) and "shops" in data:
        shops = data["shops"]
    else:
        shops = data if isinstance(data, list) else []
    assert isinstance(shops, list)
    assert any("Amazon" in shop["name"] for shop in shops)

    # Test with query string
    resp = client.get("/shop_names?q=Ama")
    assert resp.status_code == 200
    data = resp.get_json()
    if isinstance(data, dict) and "shops" in data:
        shops = data["shops"]
    else:
        shops = data if isinstance(data, list) else []
    assert any("Amazon" in shop["name"] for shop in shops)
    assert all("Ama" in shop["name"] or "ama" in shop["name"].lower() for shop in shops)

    # Test with query that yields no results
    resp = client.get("/shop_names?q=UnbekannterShop")
    assert resp.status_code == 200
    data = resp.get_json()
    if isinstance(data, dict) and "shops" in data:
        shops = data["shops"]
    else:
        shops = data if isinstance(data, list) else []
    assert shops == []
