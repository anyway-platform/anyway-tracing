# Anyway SDK

> Anyway's Python SDK allows you to easily start monitoring and debugging your LLM execution.

## Overview

Tracing is done in a non-intrusive way, built on top of OpenTelemetry. You can choose to export the traces to your existing observability stack.

## Getting Started

Install the SDK:

```bash
pip install anyway-sdk
```

Initialize in your code:

```python
from anyway.sdk import Traceloop

Traceloop.init(app_name="my_app")
```

For local development, disable batch sending to see traces immediately:

```python
Traceloop.init(app_name="my_app", disable_batch=True)
```

## Configuration

The SDK is built on top of OpenTelemetry and supports exporting traces to any OTEL-compatible collector.

The protocol is determined by the URL format:
- Without `http://` or `https://` prefix → gRPC (e.g., `localhost:4317`)
- With `http://` or `https://` prefix → HTTP (e.g., `http://localhost:4318`)

### Connecting to Anyway Collector

Configure the SDK endpoint and authentication using one of the following methods.

**Option 1: Environment Variables**

```bash
export TRACELOOP_BASE_URL=localhost:4317
export TRACELOOP_HEADERS="Authorization=Bearer%20<your-api-key>"
```

Note: The space between `Bearer` and the key must be URL-encoded as `%20`.

**Option 2: Pass Directly to Init**

```python
from anyway.sdk import Traceloop

Traceloop.init(
    app_name="my_app",
    api_endpoint="localhost:4317",
    headers={"Authorization": "Bearer <your-api-key>"}
)
```

### OpenTelemetry Collector

The SDK can export traces to any OpenTelemetry Collector.

**Using Environment Variables**

```bash
export TRACELOOP_BASE_URL=<your-collector-endpoint>
```

**Using a Custom Exporter**

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from anyway.sdk import Traceloop

exporter = OTLPSpanExporter(endpoint="localhost:4317")

Traceloop.init(
    app_name="my_app",
    exporter=exporter
)
```

## Decorators

Use `@workflow` and `@task` decorators to organize and trace your LLM operations.

```python
from anyway.sdk import Traceloop
from anyway.sdk.decorators import workflow, task

Traceloop.init(app_name="my_app")

@task(name="generate_content")
def generate_content(topic: str):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Write about: {topic}"}],
    )
    return completion.choices[0].message.content

@workflow(name="content_pipeline")
def create_content(topic: str):
    return generate_content(topic)
```

The `name` parameter is optional - if not provided, it defaults to the function name.

## Supported Destinations

- Anyway Platform

## Supported Providers

### LLM Providers

- Anthropic
- OpenAI / Azure OpenAI
- AWS Bedrock
- Google Generative AI (Gemini)
- Cohere
- Mistral AI
- And more...

### Vector DBs

- Chroma
- Pinecone
- Qdrant
- Weaviate
- And more...

### Frameworks

- LangChain
- LlamaIndex
- CrewAI
- And more...

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

*This project is forked from [Traceloop's OpenLLMetry](https://github.com/traceloop/openllmetry).*