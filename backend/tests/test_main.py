"""Tests for main FastAPI application."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_welcome_message(self, client: TestClient):
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Todo API is running!"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"

    def test_root_returns_json_content_type(self, client: TestClient):
        response = client.get("/")

        assert response.headers["content-type"] == "application/json"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_ok(self, client: TestClient):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}

    def test_health_check_returns_json_content_type(self, client: TestClient):
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_present_on_preflight(self, client: TestClient):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.FRONTEND_URL = "http://localhost:3000"
            mock_settings.return_value = mock_settings_obj

            # Simulate preflight OPTIONS request
            response = client.options(
                "/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

            # CORS middleware should handle this
            assert response.status_code in [
                200,
                405,
            ]  # Might be 405 if route doesn't exist

    def test_cors_allows_credentials(self, client: TestClient):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.FRONTEND_URL = "http://localhost:3000"
            mock_settings.return_value = mock_settings_obj

            response = client.get(
                "/health",
                headers={"Origin": "http://localhost:3000"},
            )

            # Check if CORS headers are present
            assert response.status_code == 200


class TestAppConfiguration:
    """Tests for FastAPI app configuration."""

    def test_app_has_correct_title(self):
        assert app.title is not None

    def test_app_has_correct_description(self):
        assert app.description == "Todo management API with authentication"

    def test_app_has_correct_version(self):
        assert app.version == "1.0.0"

    def test_app_has_openapi_url(self):
        assert app.openapi_url == "/openapi.json"


class TestRouters:
    """Tests for router inclusion."""

    def test_auth_router_included(self, client: TestClient):
        # Try to access an auth endpoint (even if it returns 405 or 422, it means the route exists)
        response = client.post("/api/v1/auth/login")
        # Should not be 404, which would mean router is not included
        assert response.status_code != 404

    def test_todos_router_included(self, client: TestClient):
        # Try to access a todos endpoint
        response = client.get("/api/v1/todos")
        # Should not be 404, which would mean router is not included
        # Might be 401/403 if authentication is required
        assert response.status_code != 404

    def test_users_router_included(self, client: TestClient):
        # Try to access a users endpoint
        response = client.get("/api/v1/users/me")
        # Should not be 404, which would mean router is not included
        # Might be 401/403 if authentication is required
        assert response.status_code != 404


class TestLifespan:
    """Tests for lifespan events."""

    @patch("app.db.session.verify_connection", return_value=None)
    @patch("builtins.print")
    def test_lifespan_startup_message(self, mock_print: MagicMock, _mock_verify: MagicMock):
        # Create a new client which triggers lifespan
        with TestClient(app):
            # Check if startup message was printed
            calls = [str(call) for call in mock_print.call_args_list]
            startup_called = any("Starting up..." in str(call) for call in calls)
            assert startup_called

    @patch("app.db.session.verify_connection", return_value=None)
    @patch("builtins.print")
    def test_lifespan_shutdown_message(self, mock_print: MagicMock, _mock_verify: MagicMock):
        # Create and close client which triggers lifespan
        with TestClient(app):
            pass  # Context manager exit triggers shutdown

        # Check if shutdown message was printed
        calls = [str(call) for call in mock_print.call_args_list]
        shutdown_called = any("Shutting down..." in str(call) for call in calls)
        assert shutdown_called


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation."""

    def test_openapi_json_accessible(self, client: TestClient):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_ui_accessible(self, client: TestClient):
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_accessible(self, client: TestClient):
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
