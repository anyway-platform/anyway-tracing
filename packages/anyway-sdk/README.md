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

### Authentication

Choose one of the following methods to set your API key:

**Option 1: Environment Variable**

```bash
export TRACELOOP_HEADERS="Authorization=Bearer%20<your-api-key>"
```

Note: The space between `Bearer` and the key must be URL-encoded as `%20`.

Example:
```bash
export TRACELOOP_HEADERS="Authorization=Bearer%20sk_test_mncd5s5tQQJLuLNhRoXcYuNuptoOPuAY"
```

Then initialize the SDK:
```python
from anyway.sdk import Traceloop

Traceloop.init(app_name="my_app")
```

**Option 2: Pass Headers Directly**

```python
from anyway.sdk import Traceloop

Traceloop.init(
    app_name="my_app",
    headers={"Authorization": "Bearer <your-api-key>"}
)
```

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
