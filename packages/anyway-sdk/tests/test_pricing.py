import json
import pytest
from anyway.sdk.pricing import PricingCalculator, load_pricing


class TestPricingLoader:
    def test_load_default_pricing(self):
        """Test loading bundled default pricing data."""
        pricing = load_pricing()
        assert "chat" in pricing
        assert "embeddings" in pricing
        # Check some known models exist
        assert "gpt-4o" in pricing["chat"]

    def test_load_custom_pricing(self, tmp_path):
        """Test loading custom pricing from a file path."""
        custom_pricing = {
            "chat": {
                "test-model": {
                    "promptPrice": 1.0,
                    "completionPrice": 2.0,
                }
            },
            "embeddings": {},
        }
        pricing_file = tmp_path / "pricing.json"
        pricing_file.write_text(json.dumps(custom_pricing))

        pricing = load_pricing(str(pricing_file))
        assert "test-model" in pricing["chat"]
        assert pricing["chat"]["test-model"]["promptPrice"] == 1.0

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_pricing("/nonexistent/path/pricing.json")


class TestPricingCalculator:
    @pytest.fixture
    def calculator(self):
        """Create a calculator with default pricing."""
        pricing = load_pricing()
        return PricingCalculator(pricing)

    @pytest.fixture
    def custom_calculator(self):
        """Create a calculator with custom pricing for testing."""
        # Prices are per 1K tokens
        pricing = {
            "chat": {
                "gpt-4o": {
                    "promptPrice": 2.5,      # $2.50 per 1K tokens = $0.0025 per token
                    "completionPrice": 10.0,  # $10 per 1K tokens = $0.01 per token
                },
                "gpt-4o-mini": {
                    "promptPrice": 0.15,
                    "completionPrice": 0.6,
                },
                "claude-3-5-sonnet": {
                    "promptPrice": 3.0,
                    "completionPrice": 15.0,
                },
            },
            "embeddings": {},
        }
        return PricingCalculator(pricing)

    def test_exact_match(self, custom_calculator):
        """Test exact model name matching."""
        pricing = custom_calculator.find_pricing("gpt-4o")
        assert pricing is not None
        # 2.5 per 1K tokens = 0.0025 per token
        assert pricing["input_cost_per_token"] == 0.0025

    def test_date_suffix_stripping(self, custom_calculator):
        """Test matching by stripping date suffix."""
        # gpt-4o-2024-08-06 should match gpt-4o after stripping
        pricing = custom_calculator.find_pricing("gpt-4o-2024-08-06")
        assert pricing is not None
        assert pricing["input_cost_per_token"] == 0.0025

    def test_compact_date_suffix_stripping(self, custom_calculator):
        """Test matching by stripping compact date suffix (YYYYMMDD)."""
        pricing = custom_calculator.find_pricing("claude-3-5-sonnet-20241022")
        assert pricing is not None
        assert pricing["input_cost_per_token"] == 0.003

    def test_prefix_match(self, custom_calculator):
        """Test prefix matching (longest wins)."""
        # gpt-4o-mini-some-variant should match gpt-4o-mini, not gpt-4o
        pricing = custom_calculator.find_pricing("gpt-4o-mini-some-variant")
        assert pricing is not None
        assert pricing["input_cost_per_token"] == 0.00015

    def test_unknown_model_returns_none(self, custom_calculator):
        """Test that unknown models return None."""
        pricing = custom_calculator.find_pricing("unknown-model")
        assert pricing is None

    def test_none_input_returns_none(self, custom_calculator):
        """Test that None input returns None."""
        assert custom_calculator.find_pricing(None) is None

    def test_cost_calculation(self, custom_calculator):
        """Test cost attribute calculation on a mock span."""

        class MockSpan:
            _attributes = {
                "gen_ai.response.model": "gpt-4o",
                "gen_ai.usage.input_tokens": 1000,
                "gen_ai.usage.output_tokens": 500,
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert span._attributes["gen_ai.usage.input_cost"] == 2.5    # 1000 * 0.0025
        assert span._attributes["gen_ai.usage.output_cost"] == 5.0   # 500 * 0.01
        assert span._attributes["gen_ai.usage.cost"] == 7.5

    def test_cost_calculation_with_request_model_fallback(self, custom_calculator):
        """Test that request model is used when response model is missing."""

        class MockSpan:
            _attributes = {
                "gen_ai.request.model": "gpt-4o",
                "gen_ai.usage.input_tokens": 100,
                "gen_ai.usage.output_tokens": 50,
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert "gen_ai.usage.cost" in span._attributes
        # (100 * 0.0025) + (50 * 0.01) = 0.25 + 0.5 = 0.75
        assert span._attributes["gen_ai.usage.cost"] == 0.75

    def test_cost_calculation_skipped_without_model(self, custom_calculator):
        """Test that cost calculation is skipped when model is missing."""

        class MockSpan:
            _attributes = {
                "gen_ai.usage.input_tokens": 1000,
                "gen_ai.usage.output_tokens": 500,
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert "gen_ai.usage.cost" not in span._attributes

    def test_cost_calculation_skipped_without_tokens(self, custom_calculator):
        """Test that cost calculation is skipped when no tokens are present."""

        class MockSpan:
            _attributes = {
                "gen_ai.response.model": "gpt-4o",
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert "gen_ai.usage.cost" not in span._attributes

    def test_cost_calculation_skipped_for_unknown_model(self, custom_calculator):
        """Test that cost calculation is skipped for unknown models."""

        class MockSpan:
            _attributes = {
                "gen_ai.response.model": "unknown-model",
                "gen_ai.usage.input_tokens": 1000,
                "gen_ai.usage.output_tokens": 500,
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert "gen_ai.usage.cost" not in span._attributes

    def test_cost_calculation_with_only_input_tokens(self, custom_calculator):
        """Test cost calculation when only input tokens are present."""

        class MockSpan:
            _attributes = {
                "gen_ai.response.model": "gpt-4o",
                "gen_ai.usage.input_tokens": 1000,
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert span._attributes["gen_ai.usage.input_cost"] == 2.5
        assert span._attributes["gen_ai.usage.output_cost"] == 0.0
        assert span._attributes["gen_ai.usage.cost"] == 2.5

    def test_cost_calculation_with_only_output_tokens(self, custom_calculator):
        """Test cost calculation when only output tokens are present."""

        class MockSpan:
            _attributes = {
                "gen_ai.response.model": "gpt-4o",
                "gen_ai.usage.output_tokens": 500,
            }

        span = MockSpan()
        custom_calculator.add_cost_attributes(span)

        assert span._attributes["gen_ai.usage.input_cost"] == 0.0
        assert span._attributes["gen_ai.usage.output_cost"] == 5.0
        assert span._attributes["gen_ai.usage.cost"] == 5.0

    def test_span_without_attributes_is_skipped(self, custom_calculator):
        """Test that spans without _attributes are handled gracefully."""

        class MockSpan:
            pass

        span = MockSpan()
        # Should not raise
        custom_calculator.add_cost_attributes(span)

    def test_span_with_none_attributes_is_skipped(self, custom_calculator):
        """Test that spans with None _attributes are handled gracefully."""

        class MockSpan:
            _attributes = None

        span = MockSpan()
        # Should not raise
        custom_calculator.add_cost_attributes(span)


class TestDefaultPricingData:
    """Test the bundled default pricing data."""

    @pytest.fixture
    def default_pricing(self):
        return load_pricing()

    def test_has_chat_section(self, default_pricing):
        """Test that pricing has chat section."""
        assert "chat" in default_pricing

    def test_has_embeddings_section(self, default_pricing):
        """Test that pricing has embeddings section."""
        assert "embeddings" in default_pricing

    def test_has_openai_models(self, default_pricing):
        """Test that OpenAI models are present."""
        chat = default_pricing["chat"]
        assert "gpt-4o" in chat
        assert "gpt-4o-mini" in chat or "gpt-4o-mini-2024-07-18" in chat

    def test_has_anthropic_models(self, default_pricing):
        """Test that Anthropic models are present."""
        chat = default_pricing["chat"]
        # Check for claude models (may have various naming)
        claude_models = [k for k in chat.keys() if "claude" in k.lower()]
        assert len(claude_models) > 0, "No Claude models found"

    def test_pricing_format_is_correct(self, default_pricing):
        """Test that pricing entries have correct format."""
        for model_name, pricing in default_pricing["chat"].items():
            assert "promptPrice" in pricing, f"{model_name} missing promptPrice"
            assert "completionPrice" in pricing, f"{model_name} missing completionPrice"
            assert pricing["promptPrice"] >= 0, f"{model_name} has negative promptPrice"
            assert pricing["completionPrice"] >= 0, f"{model_name} has negative completionPrice"

    def test_calculator_works_with_default_pricing(self):
        """Test that calculator works with bundled pricing."""
        pricing = load_pricing()
        calculator = PricingCalculator(pricing)

        # Test with a known model
        result = calculator.find_pricing("gpt-4o")
        assert result is not None
        assert "input_cost_per_token" in result
        assert "output_cost_per_token" in result
