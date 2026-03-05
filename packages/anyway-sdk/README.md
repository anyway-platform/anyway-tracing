# anyway-sdk

Anyway's Python SDK allows you to easily start monitoring and debugging your LLM execution. Tracing is done in a non-intrusive way, built on top of OpenTelemetry. You can choose to export the traces to your existing observability stack.

## Installation

```bash
pip install anyway-sdk
```

## Quick Start

```python
from anyway.sdk import Traceloop
from anyway.sdk.decorators import workflow, task

Traceloop.init(app_name="joke_generation_service")

@workflow(name="joke_creation")
def create_joke():
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Tell me a joke about opentelemetry"}],
    )
    return completion.choices[0].message.content
```

## Configuration

The SDK is built on top of OpenTelemetry and supports exporting traces to any OTEL-compatible collector.

Protocol selection is determined by `api_endpoint`:
- `http://` or `https://` -> OTLP HTTP exporter (`/v1/traces` path is appended when needed)
- `grpc://` -> OTLP gRPC exporter (`insecure=True`)
- `grpcs://` -> OTLP gRPC exporter (`insecure=False`, TLS)
- no scheme (for example `collector.example.com:4317`) -> OTLP gRPC exporter with secure default (`insecure=False`)

### Environment Variables

`TRACELOOP_*` is canonical. `ANYWAY_*` aliases are also supported for compatibility.

- `TRACELOOP_BASE_URL` (alias: `ANYWAY_BASE_URL`)
- `TRACELOOP_API_KEY` (alias: `ANYWAY_API_KEY`)
- `TRACELOOP_HEADERS` (alias: `ANYWAY_HEADERS`)
- `TRACELOOP_GRPC_INSECURE` (alias: `ANYWAY_GRPC_INSECURE`) for explicit local/dev opt-out of secure no-scheme gRPC defaults

### Anyway Cloud Example

```bash
export TRACELOOP_BASE_URL=https://api.traceloop.com
export TRACELOOP_API_KEY=sk_live_xxx
```

```python
from anyway.sdk import Traceloop

Traceloop.init(app_name="my_app")
```

### Custom OTLP Collector Example

Secure gRPC collector:

```bash
export TRACELOOP_BASE_URL=grpcs://otel-collector.example.com:4317
export TRACELOOP_HEADERS="Authorization=Bearer%20<token>"
```

Local/dev collector without TLS (no scheme endpoint + explicit opt-out):

```bash
export TRACELOOP_BASE_URL=localhost:4317
export TRACELOOP_GRPC_INSECURE=true
```

```python
from anyway.sdk import Traceloop

Traceloop.init(app_name="my_app")
```

### Migration Notes

- Endpoints without a scheme now default to secure gRPC (`insecure=False`).
- If you rely on insecure local gRPC with a no-scheme endpoint (for example `localhost:4317`), set `TRACELOOP_GRPC_INSECURE=true` (or `ANYWAY_GRPC_INSECURE=true`).
- Existing `http://`/`https://` and `grpc://`/`grpcs://` behavior remains unchanged.

## Decorators

The SDK provides `@workflow` and `@task` decorators to organize and trace your LLM operations.

### Import

```python
from anyway.sdk.decorators import workflow, task
```

### Parameters

Both decorators accept the same parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `Optional[str]` | Custom name for the span. If not provided, defaults to the function name. |



### @workflow

Use `@workflow` to define high-level operations that orchestrate multiple tasks.

```python
@workflow(name="document_processor")
def process_document(text: str):
    summary = summarize_text(text)
    keywords = extract_keywords(text)
    return {"summary": summary, "keywords": keywords}
```

### @task

Use `@task` to define individual units of work within a workflow.

```python
@task(name="text_summarizer")
def summarize_text(text: str):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Summarize: {text}"}],
    )
    return completion.choices[0].message.content

@task(name="keyword_extractor")
def extract_keywords(text: str):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Extract keywords from: {text}"}],
    )
    return completion.choices[0].message.content
```

### Nested Workflows and Tasks

Workflows can call tasks, and tasks can call other tasks to create a trace hierarchy:

```python
from anyway.sdk import Traceloop
from anyway.sdk.decorators import workflow, task

Traceloop.init(app_name="content_pipeline")

@task(name="generate_content")
def generate_content(topic: str):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Write about: {topic}"}],
    )
    return completion.choices[0].message.content

@task(name="review_content")
def review_content(content: str):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Review this content: {content}"}],
    )
    return completion.choices[0].message.content

@workflow(name="content_pipeline")
def create_content(topic: str):
    content = generate_content(topic)
    reviewed = review_content(content)
    return reviewed
```

## Async Support

Both decorators work seamlessly with async functions:

```python
@task(name="async_summarizer")
async def summarize_text(text: str):
    completion = await async_openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Summarize: {text}"}],
    )
    return completion.choices[0].message.content

@workflow(name="async_pipeline")
async def process_async(text: str):
    return await summarize_text(text)
```
