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

Traceloop.init()
```

For local development, disable batch sending to see traces immediately:

```python
Traceloop.init(disable_batch=True)
```

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