"""
E2E tests: send real traces to collector.anyway.sh via SDK.
Requires ANYWAY_API_KEY environment variable — skipped if not set.
"""
import os
import time
import pytest
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

BASE_URL = "https://collector.anyway.sh"

requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANYWAY_API_KEY"),
    reason="ANYWAY_API_KEY not set",
)


@requires_api_key
class TestCollectorE2E:

    def test_otlp_export(self):
        """Send an OTLP trace directly and verify no export errors."""
        api_key = os.environ["ANYWAY_API_KEY"]

        exporter = OTLPSpanExporter(
            endpoint=f"{BASE_URL}/v1/traces",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer("e2e-test-python")

        with tracer.start_as_current_span("e2e-otlp-python") as span:
            span.set_attribute("test.type", "e2e")
            with tracer.start_as_current_span("child-span"):
                time.sleep(0.01)

        provider.force_flush()
        provider.shutdown()

    def test_sdk_init(self):
        """Initialize via SDK and send a trace to the default endpoint."""
        import anyway.sdk
        # Reset singleton so init() runs fresh
        anyway.sdk.Traceloop._Traceloop__tracer_wrapper = None

        from anyway.sdk import Traceloop

        client = Traceloop.init(
            app_name="e2e-test-python",
            api_key=os.environ["ANYWAY_API_KEY"],
            disable_batch=True,
        )

        if client:
            assert client.api_endpoint == BASE_URL

        from opentelemetry import trace
        tracer = trace.get_tracer("e2e-sdk-python")
        with tracer.start_as_current_span("e2e-sdk-python") as span:
            span.set_attribute("test.via", "sdk-init")
            time.sleep(0.01)

        time.sleep(1)  # allow export
