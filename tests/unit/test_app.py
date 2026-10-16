from psrs import create_app


def test_home_page_returns_success():
    client = create_app().test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Predictive Supply Resilience System" in response.data


def test_health_endpoint_returns_ok():
    client = create_app().test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "project": "PSRS"}


def test_summary_reports_missing_dataset(tmp_path):
    class TestConfig:
        DATA_DIRECTORY = str(tmp_path)
        TESTING = True

    response = create_app(TestConfig).test_client().get("/api/summary")
    assert response.status_code == 200
    assert response.get_json()["dataset_available"] is False
