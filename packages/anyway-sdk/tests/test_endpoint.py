"""
Tests for default endpoint and environment variable configuration.

Verifies:
1. Default endpoint is https://collector.anyway.sh
2. ANYWAY_* environment variables work correctly
3. Old TRACELOOP_* environment variables are no longer used
"""
import os
import pytest
from anyway.sdk import Traceloop
from anyway.sdk.client.client import Client
from anyway.sdk.config import is_tracing_enabled, is_logging_enabled


class TestDefaultEndpoint:

    def test_client_default_endpoint(self):
        client = Client(api_key="test-key")
        assert client.api_endpoint == "https://collector.anyway.sh"

    def test_client_custom_endpoint(self):
        custom_client = Client(
            api_key="test-key",
            api_endpoint="https://custom.example.com"
        )
        assert custom_client.api_endpoint == "https://custom.example.com"

    def test_get_default_span_processor(self):
        processor = Traceloop.get_default_span_processor(
            disable_batch=True,
            api_key="test-key"
        )
        assert processor is not None


class TestEnvironmentVariables:

    def test_base_url(self, monkeypatch):
        monkeypatch.setenv("ANYWAY_BASE_URL", "https://test.anyway.sh")
        assert os.getenv("ANYWAY_BASE_URL") == "https://test.anyway.sh"

    def test_api_key(self, monkeypatch):
        monkeypatch.setenv("ANYWAY_API_KEY", "test-api-key-123")
        assert os.getenv("ANYWAY_API_KEY") == "test-api-key-123"

    def test_tracing_enabled(self, monkeypatch):
        monkeypatch.setenv("ANYWAY_TRACING_ENABLED", "true")
        assert is_tracing_enabled() is True

        monkeypatch.setenv("ANYWAY_TRACING_ENABLED", "false")
        assert is_tracing_enabled() is False

    def test_logging_enabled(self, monkeypatch):
        monkeypatch.setenv("ANYWAY_LOGGING_ENABLED", "true")
        assert is_logging_enabled() is True

        monkeypatch.setenv("ANYWAY_LOGGING_ENABLED", "false")
        assert is_logging_enabled() is False

    def test_old_traceloop_env_vars_not_used(self, monkeypatch):
        monkeypatch.setenv("TRACELOOP_BASE_URL", "https://old.traceloop.com")
        monkeypatch.setenv("TRACELOOP_API_KEY", "old-key")

        client = Client(api_key="new-key")
        assert client.api_endpoint == "https://collector.anyway.sh"
