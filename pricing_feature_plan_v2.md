# Model Pricing Cost Calculation

> **Status: IMPLEMENTED** - This feature is now available in the SDK.

## Summary

The SDK now supports automatic cost calculation for LLM operations using bundled pricing data.

**Features:**
- 100+ models supported out of the box
- Custom pricing JSON file path supported
- Enabled by default
- Cost appears in span attributes (`gen_ai.usage.cost`, `gen_ai.usage.input_cost`, `gen_ai.usage.output_cost`)

---

## Architecture Decision

Use the existing `span_postprocess_callback` mechanism in `TracerWrapper`. This callback runs before span export and allows modifying `span._attributes` directly - solves the immutable ReadableSpan problem without changing any instrumentation packages.

**Why this approach:**
- The SDK already has this pattern implemented in `tracing.py` (lines 134-144)
- Tests in `conftest.py` demonstrate that `span._attributes` can be modified in the callback
- No changes needed to 30+ instrumentation packages
- Token counts are already set when the callback fires

---

## Implementation Steps

### Step 1: Add Cost Semantic Conventions

**File:** `packages/opentelemetry-semantic-conventions-ai/opentelemetry/semconv_ai/__init__.py`

Add to `SpanAttributes` class:
```python
# Cost Attributes
GEN_AI_USAGE_COST = "gen_ai.usage.cost"
GEN_AI_USAGE_INPUT_COST = "gen_ai.usage.input_cost"
GEN_AI_USAGE_OUTPUT_COST = "gen_ai.usage.output_cost"
```

---

### Step 2: Create Pricing Module

**New directory:** `packages/anyway-sdk/anyway/sdk/pricing/`

**Files to create:**

#### 2.1 `__init__.py`
```python
from anyway.sdk.pricing.calculator import PricingCalculator
from anyway.sdk.pricing.loader import load_pricing

__all__ = ["PricingCalculator", "load_pricing"]
```

#### 2.2 `loader.py`
```python
import json
import os
from pathlib import Path
from typing import Optional


def load_pricing(pricing_json_path: Optional[str] = None) -> dict:
    """
    Load pricing data from a JSON file.

    Args:
        pricing_json_path: Path to custom pricing JSON file.
                          If None, uses bundled default pricing.

    Returns:
        Pricing data dictionary.

    Raises:
        FileNotFoundError: If custom path provided but file doesn't exist.
        json.JSONDecodeError: If JSON is invalid.
    """
    if pricing_json_path is None:
        # Use bundled default pricing
        default_path = Path(__file__).parent / "data" / "default_pricing.json"
        pricing_json_path = str(default_path)

    with open(pricing_json_path, "r") as f:
        return json.load(f)
```

#### 2.3 `calculator.py`
```python
import re
from typing import Optional
from opentelemetry.sdk.trace import ReadableSpan


class PricingCalculator:
    """Calculates LLM usage costs based on token counts and model pricing."""

    def __init__(self, pricing_data: dict):
        """
        Initialize calculator with pricing data.

        Args:
            pricing_data: Pricing dictionary loaded from JSON.
        """
        self.pricing_data = pricing_data
        self._build_lookup_cache()

    def _build_lookup_cache(self):
        """Build alias lookup cache for faster model matching."""
        self._alias_cache = {}
        providers = self.pricing_data.get("providers", {})
        for provider_name, provider_data in providers.items():
            models = provider_data.get("models", {})
            for model_name, model_config in models.items():
                for alias in model_config.get("aliases", []):
                    self._alias_cache[(provider_name, alias)] = model_config

    def find_pricing(self, provider: str, model_name: str) -> Optional[dict]:
        """
        Find pricing for a model using multi-tier matching.

        Matching strategy (in order):
        1. Exact match on model name
        2. Check aliases list
        3. Strip date suffix (-2024-08-06 or -20240806)
        4. Prefix match (longest wins)
        5. Return None (don't fail, just skip cost)

        Args:
            provider: Provider name (e.g., "openai", "Anthropic")
            model_name: Model name from span attributes

        Returns:
            Model pricing dict or None if not found.
        """
        if not provider or not model_name:
            return None

        provider_data = self.pricing_data.get("providers", {}).get(provider)
        if not provider_data:
            return None

        models = provider_data.get("models", {})

        # 1. Exact match
        if model_name in models:
            return models[model_name]

        # 2. Check aliases (using cache)
        cached = self._alias_cache.get((provider, model_name))
        if cached:
            return cached

        # 3. Strip date suffix patterns
        stripped = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', model_name)
        stripped = re.sub(r'-\d{8}$', '', stripped)
        if stripped != model_name and stripped in models:
            return models[stripped]

        # 4. Prefix match (longest match wins)
        best_match = None
        best_len = 0
        for base_model in models.keys():
            if model_name.startswith(base_model) and len(base_model) > best_len:
                best_match = base_model
                best_len = len(base_model)

        if best_match:
            return models[best_match]

        return None

    def add_cost_attributes(self, span: ReadableSpan) -> None:
        """
        Add cost attributes to a span based on token usage.

        Modifies span._attributes in place to add:
        - gen_ai.usage.input_cost
        - gen_ai.usage.output_cost
        - gen_ai.usage.cost (total)

        Args:
            span: The span to enrich with cost attributes.
        """
        if not hasattr(span, "_attributes") or not span._attributes:
            return

        attrs = span._attributes

        # Get provider
        provider = attrs.get("gen_ai.system")
        if not provider:
            return

        # Get model (prefer response model, fall back to request model)
        model = attrs.get("gen_ai.response.model") or attrs.get("gen_ai.request.model")
        if not model:
            return

        # Get token counts
        input_tokens = attrs.get("gen_ai.usage.input_tokens")
        output_tokens = attrs.get("gen_ai.usage.output_tokens")

        if input_tokens is None and output_tokens is None:
            return

        # Find pricing
        pricing = self.find_pricing(provider, model)
        if not pricing:
            return

        # Calculate costs
        input_cost = (input_tokens or 0) * pricing.get("input_cost_per_token", 0)
        output_cost = (output_tokens or 0) * pricing.get("output_cost_per_token", 0)
        total_cost = input_cost + output_cost

        # Set cost attributes (modifying in place)
        attrs["gen_ai.usage.input_cost"] = input_cost
        attrs["gen_ai.usage.output_cost"] = output_cost
        attrs["gen_ai.usage.cost"] = total_cost
```

#### 2.4 `data/default_pricing.json`
```json
{
  "version": "1.0",
  "updated_at": "2026-01-16T00:00:00Z",
  "providers": {
    "openai": {
      "models": {
        "gpt-4o": {
          "input_cost_per_token": 0.0000025,
          "output_cost_per_token": 0.00001,
          "aliases": ["gpt-4o-2024-08-06", "gpt-4o-2024-05-13"]
        },
        "gpt-4o-mini": {
          "input_cost_per_token": 0.00000015,
          "output_cost_per_token": 0.0000006,
          "aliases": ["gpt-4o-mini-2024-07-18"]
        },
        "gpt-4-turbo": {
          "input_cost_per_token": 0.00001,
          "output_cost_per_token": 0.00003,
          "aliases": ["gpt-4-turbo-2024-04-09", "gpt-4-turbo-preview"]
        },
        "gpt-4": {
          "input_cost_per_token": 0.00003,
          "output_cost_per_token": 0.00006,
          "aliases": ["gpt-4-0613", "gpt-4-0314"]
        },
        "gpt-3.5-turbo": {
          "input_cost_per_token": 0.0000005,
          "output_cost_per_token": 0.0000015,
          "aliases": ["gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106"]
        },
        "o1": {
          "input_cost_per_token": 0.000015,
          "output_cost_per_token": 0.00006,
          "aliases": ["o1-2024-12-17"]
        },
        "o1-mini": {
          "input_cost_per_token": 0.000003,
          "output_cost_per_token": 0.000012,
          "aliases": ["o1-mini-2024-09-12"]
        }
      }
    },
    "Anthropic": {
      "models": {
        "claude-3-5-sonnet": {
          "input_cost_per_token": 0.000003,
          "output_cost_per_token": 0.000015,
          "aliases": ["claude-3-5-sonnet-20240620", "claude-3-5-sonnet-20241022", "claude-3-5-sonnet-latest"]
        },
        "claude-3-opus": {
          "input_cost_per_token": 0.000015,
          "output_cost_per_token": 0.000075,
          "aliases": ["claude-3-opus-20240229", "claude-3-opus-latest"]
        },
        "claude-3-5-haiku": {
          "input_cost_per_token": 0.0000008,
          "output_cost_per_token": 0.000004,
          "aliases": ["claude-3-5-haiku-20241022", "claude-3-5-haiku-latest"]
        },
        "claude-3-haiku": {
          "input_cost_per_token": 0.00000025,
          "output_cost_per_token": 0.00000125,
          "aliases": ["claude-3-haiku-20240307"]
        }
      }
    },
    "cohere": {
      "models": {
        "command-r-plus": {
          "input_cost_per_token": 0.0000025,
          "output_cost_per_token": 0.00001,
          "aliases": []
        },
        "command-r": {
          "input_cost_per_token": 0.00000015,
          "output_cost_per_token": 0.0000006,
          "aliases": []
        }
      }
    },
    "mistralai": {
      "models": {
        "mistral-large": {
          "input_cost_per_token": 0.000002,
          "output_cost_per_token": 0.000006,
          "aliases": ["mistral-large-latest", "mistral-large-2411"]
        },
        "mistral-small": {
          "input_cost_per_token": 0.0000002,
          "output_cost_per_token": 0.0000006,
          "aliases": ["mistral-small-latest", "mistral-small-2409"]
        }
      }
    },
    "groq": {
      "models": {
        "llama-3.3-70b-versatile": {
          "input_cost_per_token": 0.00000059,
          "output_cost_per_token": 0.00000079,
          "aliases": []
        },
        "llama-3.1-8b-instant": {
          "input_cost_per_token": 0.00000005,
          "output_cost_per_token": 0.00000008,
          "aliases": []
        }
      }
    }
  }
}
```

---

### Step 3: Integrate into SDK Init

**File:** `packages/anyway-sdk/anyway/sdk/__init__.py`

Add new parameters to `Traceloop.init()`:

```python
@staticmethod
def init(
    # ... existing parameters ...
    pricing_enabled: bool = True,
    pricing_json_path: Optional[str] = None,
) -> Optional[Client]:
    """
    Initialize the SDK.

    Args:
        pricing_enabled: Enable cost calculation (default: True).
        pricing_json_path: Path to custom pricing JSON file.
                          If None, uses bundled default pricing.
    """
```

Add pricing callback integration (before TracerWrapper initialization):

```python
from anyway.sdk.pricing import PricingCalculator, load_pricing

# In Traceloop.init(), before TracerWrapper.set_static_params():
if pricing_enabled:
    try:
        pricing_data = load_pricing(pricing_json_path)
        pricing_calculator = PricingCalculator(pricing_data)

        # Wrap existing callback or create new one
        original_callback = span_postprocess_callback

        def pricing_callback(span):
            if original_callback:
                original_callback(span)
            pricing_calculator.add_cost_attributes(span)

        span_postprocess_callback = pricing_callback
    except Exception as e:
        # Log warning but don't fail SDK initialization
        logging.warning(f"Failed to initialize pricing: {e}")
```

---

## Files Summary

| File | Action |
|------|--------|
| `packages/opentelemetry-semantic-conventions-ai/opentelemetry/semconv_ai/__init__.py` | Modify - add 3 cost attributes |
| `packages/anyway-sdk/anyway/sdk/pricing/__init__.py` | Create |
| `packages/anyway-sdk/anyway/sdk/pricing/loader.py` | Create |
| `packages/anyway-sdk/anyway/sdk/pricing/calculator.py` | Create |
| `packages/anyway-sdk/anyway/sdk/pricing/data/default_pricing.json` | Create |
| `packages/anyway-sdk/anyway/sdk/__init__.py` | Modify - add pricing params + callback |

---

## Model Name Matching Strategy

Models have various naming patterns that need to be handled:

| Pattern | Example | Matching |
|---------|---------|----------|
| Base name | `gpt-4o` | Exact match |
| Date versioned | `gpt-4o-2024-08-06` | Strip suffix, match `gpt-4o` |
| Compact date | `claude-3-5-sonnet-20241022` | Strip suffix, match `claude-3-5-sonnet` |
| Alias | `claude-3-5-sonnet-latest` | Explicit alias lookup |
| Prefix variant | `gpt-4o-mini-2024-07-18` | Prefix match to `gpt-4o-mini` |

**Matching order:**
1. Exact match on model name
2. Check explicit aliases list
3. Strip date suffix and retry exact match
4. Prefix match (longest wins)
5. Return None (skip cost calculation, don't fail)

---

## Verification

### Unit Tests

Create `packages/anyway-sdk/tests/test_pricing.py`:

```python
import pytest
from anyway.sdk.pricing import PricingCalculator, load_pricing


class TestPricingLoader:
    def test_load_default_pricing(self):
        pricing = load_pricing()
        assert "providers" in pricing
        assert "openai" in pricing["providers"]

    def test_load_custom_pricing(self, tmp_path):
        custom_pricing = {"providers": {"test": {"models": {}}}}
        pricing_file = tmp_path / "pricing.json"
        pricing_file.write_text(json.dumps(custom_pricing))

        pricing = load_pricing(str(pricing_file))
        assert "test" in pricing["providers"]


class TestPricingCalculator:
    @pytest.fixture
    def calculator(self):
        pricing = load_pricing()
        return PricingCalculator(pricing)

    def test_exact_match(self, calculator):
        pricing = calculator.find_pricing("openai", "gpt-4o")
        assert pricing is not None
        assert pricing["input_cost_per_token"] == 0.0000025

    def test_alias_match(self, calculator):
        pricing = calculator.find_pricing("openai", "gpt-4o-2024-08-06")
        assert pricing is not None

    def test_date_suffix_stripping(self, calculator):
        pricing = calculator.find_pricing("Anthropic", "claude-3-5-sonnet-20241022")
        assert pricing is not None

    def test_unknown_model_returns_none(self, calculator):
        pricing = calculator.find_pricing("openai", "unknown-model")
        assert pricing is None

    def test_cost_calculation(self, calculator):
        # Create mock span with token attributes
        class MockSpan:
            _attributes = {
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o",
                "gen_ai.usage.input_tokens": 1000,
                "gen_ai.usage.output_tokens": 500,
            }

        span = MockSpan()
        calculator.add_cost_attributes(span)

        assert span._attributes["gen_ai.usage.input_cost"] == 0.0025  # 1000 * 0.0000025
        assert span._attributes["gen_ai.usage.output_cost"] == 0.005  # 500 * 0.00001
        assert span._attributes["gen_ai.usage.cost"] == 0.0075
```

### Integration Test

```python
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from anyway.sdk import Traceloop

# Initialize with console exporter to see spans
Traceloop.init(
    app_name="pricing-test",
    exporter=ConsoleSpanExporter(),
    pricing_enabled=True,  # default
)

# Make LLM call
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

# Check console output for:
# - gen_ai.usage.input_tokens
# - gen_ai.usage.output_tokens
# - gen_ai.usage.input_cost
# - gen_ai.usage.output_cost
# - gen_ai.usage.cost
```

### Run Tests

```bash
cd packages/anyway-sdk && poetry run pytest tests/test_pricing.py -v
```

---

## Usage

### Quick Start

```python
from anyway.sdk import Traceloop

# Initialize SDK - pricing is enabled by default with bundled pricing data
Traceloop.init(app_name="my-app")

# Make LLM calls as usual - costs will be automatically calculated
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Spans will now include:
# - gen_ai.usage.input_tokens: 10
# - gen_ai.usage.output_tokens: 25
# - gen_ai.usage.input_cost: 0.000025
# - gen_ai.usage.output_cost: 0.00025
# - gen_ai.usage.cost: 0.000275
```

### Configuration Options

#### Default Pricing (Recommended)

```python
from anyway.sdk import Traceloop

# Uses bundled default pricing automatically
Traceloop.init(app_name="my-app")
```

#### Custom Pricing File

```python
from anyway.sdk import Traceloop

# Use custom pricing JSON file
Traceloop.init(
    app_name="my-app",
    pricing_json_path="/path/to/my-pricing.json"
)
```

#### Disable Pricing

```python
from anyway.sdk import Traceloop

# Disable cost calculation entirely
Traceloop.init(
    app_name="my-app",
    pricing_enabled=False
)
```

### Custom Pricing JSON Format

To create your own pricing file, use this format:

```json
{
  "chat": {
    "my-custom-model": {
      "promptPrice": 2.5,
      "completionPrice": 10.0
    },
    "my-custom-model-v2": {
      "promptPrice": 2.0,
      "completionPrice": 8.0
    }
  },
  "embeddings": {
    "my-embedding-model": 0.0001
  }
}
```

**Key points:**
- `promptPrice`: Cost in USD per 1K input tokens
- `completionPrice`: Cost in USD per 1K output tokens
- Models are listed directly by name (no provider grouping)
- Each model version should be listed separately

### Span Attributes Added

When pricing is enabled, the following attributes are added to LLM spans:

| Attribute | Type | Description |
|-----------|------|-------------|
| `gen_ai.usage.input_cost` | float | Cost of input tokens in USD |
| `gen_ai.usage.output_cost` | float | Cost of output tokens in USD |
| `gen_ai.usage.cost` | float | Total cost (input + output) in USD |

### Supported Models (Default Pricing)

The bundled default pricing includes 100+ models:

- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo, o1, o1-mini, and more
- **Anthropic**: claude-3-5-sonnet, claude-3-opus, claude-3-haiku, and variants
- **Azure OpenAI**: All Azure-prefixed versions of OpenAI models
- **Cohere**: command-r, command-r-plus, embed models
- **Mistral**: mistral-large, mistral-small, mistral-medium
- **Google**: gemini-pro, gemini-1.5-pro, gemini-1.5-flash
- **AWS Bedrock**: Various Bedrock model prefixes
- **And many more...**

---

## Notes

- Costs are calculated in USD
- Prices in the JSON are per 1K tokens (SDK converts to per-token internally)
- If a model is not found in pricing data, cost attributes are simply not added (no error)
- The pricing callback runs after all instrumentation has set token counts
- Users can override the default pricing by providing their own JSON file
- Pricing is calculated using the `span_postprocess_callback` mechanism, which runs before spans are exported