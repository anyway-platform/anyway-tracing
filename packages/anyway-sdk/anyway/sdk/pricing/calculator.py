import re
from typing import Optional

from opentelemetry.sdk.trace import ReadableSpan


class PricingCalculator:
    """Calculates LLM usage costs based on token counts and model pricing.

    Expects pricing data with 'chat' and 'embeddings' sections where prices are per 1K tokens.
    """

    def __init__(self, pricing_data: dict):
        """
        Initialize calculator with pricing data.

        Args:
            pricing_data: Pricing dictionary with 'chat' and 'embeddings' keys.
        """
        self.chat_models = pricing_data.get("chat", {})
        self.embedding_models = pricing_data.get("embeddings", {})

    def find_pricing(self, model_name: str) -> Optional[dict]:
        """
        Find pricing for a model using multi-tier matching.

        Matching strategy (in order):
        1. Exact match on model name
        2. Strip date suffix (-2024-08-06 or -20240806) and retry
        3. Prefix match (longest wins)
        4. Return None (don't fail, just skip cost)

        Args:
            model_name: Model name from span attributes

        Returns:
            Normalized pricing dict with input_cost_per_token and output_cost_per_token,
            or None if not found.
        """
        if not model_name:
            return None

        models = self.chat_models

        # 1. Exact match
        if model_name in models:
            return self._normalize_pricing(models[model_name])

        # 2. Strip date suffix patterns and retry
        stripped = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model_name)
        stripped = re.sub(r"-\d{8}$", "", stripped)
        if stripped != model_name and stripped in models:
            return self._normalize_pricing(models[stripped])

        # 3. Prefix match (longest match wins)
        best_match = None
        best_len = 0
        for base_model in models.keys():
            if model_name.startswith(base_model) and len(base_model) > best_len:
                best_match = base_model
                best_len = len(base_model)

        if best_match:
            return self._normalize_pricing(models[best_match])

        return None

    def _normalize_pricing(self, pricing: dict) -> dict:
        """
        Convert per-1K-token pricing to per-token.

        Args:
            pricing: Dict with 'promptPrice' and 'completionPrice' (per 1K tokens)

        Returns:
            Dict with 'input_cost_per_token' and 'output_cost_per_token' (per token)
        """
        return {
            "input_cost_per_token": pricing.get("promptPrice", 0) / 1000,
            "output_cost_per_token": pricing.get("completionPrice", 0) / 1000,
        }

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
        pricing = self.find_pricing(model)
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
