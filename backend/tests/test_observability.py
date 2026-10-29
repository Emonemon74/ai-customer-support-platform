def test_response_carries_request_id(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_incoming_request_id_is_echoed(client):
    response = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_metrics_endpoint_reports_request_counts(client):
    client.get("/health")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
    assert 'method="GET"' in body
