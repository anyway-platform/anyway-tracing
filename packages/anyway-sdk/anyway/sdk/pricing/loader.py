import json
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
