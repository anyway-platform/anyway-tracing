from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .models import (
    ApiResponse,
    CustomerResponse,
    EntitlementCheckResponse,
    MeResponse,
    OrderDetailResponse,
    OrderResponse,
    PaginatedResponse,
    ProductResponse,
    SubscriptionResponse,
)

_DEFAULT_BASE_URL = "https://merchant-api.anyway.sh"
_STAGING_BASE_URL = "https://merchant-api-stg.anyway.sh"


class MerchantAPIError(Exception):
    """Raised when the Merchant API returns an error response."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        super().__init__(f"[{status_code}] {code}: {message}")


class MerchantClient:
    """Python client for the Anyway Merchant API.

    Usage::

        from anyway.sdk.merchant import MerchantClient

        client = MerchantClient(api_key="ak_...")

        # Get current key info
        me = client.me()

        # List products
        products = client.list_products()

        # Check entitlement
        result = client.check_entitlement(email="user@example.com", product_id="PRD_xxx")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": self._api_key})

    @classmethod
    def staging(cls, api_key: str, **kwargs: Any) -> "MerchantClient":
        """Create a client pointing at the staging environment."""
        return cls(api_key=api_key, base_url=_STAGING_BASE_URL, **kwargs)

    # ── Internal ────────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = self._session.get(
            f"{self._base_url}/v1/{path.lstrip('/')}",
            params=params,
            timeout=self._timeout,
        )
        data = resp.json()
        if not data.get("success", False):
            err = data.get("error", {})
            raise MerchantAPIError(
                status_code=resp.status_code,
                code=err.get("code", "UNKNOWN"),
                message=err.get("message", data.get("message", "Unknown error")),
            )
        return data

    # ── /me ─────────────────────────────────────────────────────────────

    def me(self) -> MeResponse:
        """Get info about the current API key."""
        data = self._get("me")
        return MeResponse.model_validate(data["data"])

    # ── /orders ─────────────────────────────────────────────────────────

    def list_orders(
        self,
        *,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        product_id: Optional[str] = None,
        provider: Optional[str] = None,
        from_address: Optional[str] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> PaginatedResponse[OrderResponse]:
        """List orders with optional filters.

        Args:
            status: Filter by display status (Paid, Pending, Refunded).
            product_id: Filter by product ID.
            provider: Filter by payment provider (STRIPE or CRYPTO).
            from_address: Filter by buyer wallet address (crypto orders).
            date_from: Filter orders created after this unix timestamp.
            date_to: Filter orders created before this unix timestamp.
        """
        params: Dict[str, Any] = {"page": page, "size": size}
        if status is not None:
            params["status"] = status
        if product_id is not None:
            params["product_id"] = product_id
        if provider is not None:
            params["provider"] = provider
        if from_address is not None:
            params["from_address"] = from_address
        if date_from is not None:
            params["date_from"] = date_from
        if date_to is not None:
            params["date_to"] = date_to

        data = self._get("orders", params)
        page_data = data["data"]
        return PaginatedResponse[OrderResponse](
            records=[OrderResponse.model_validate(r) for r in page_data["records"]],
            total=page_data["total"],
            page=page_data["page"],
            size=page_data["size"],
            pages=page_data["pages"],
        )

    def get_order(self, order_id: str) -> OrderDetailResponse:
        """Get a single order by ID, including provider details."""
        data = self._get(f"orders/{order_id}")
        return OrderDetailResponse.model_validate(data["data"])

    # ── /subscriptions ──────────────────────────────────────────────────

    def list_subscriptions(
        self,
        *,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> PaginatedResponse[SubscriptionResponse]:
        """List subscriptions with optional filters.

        Args:
            status: Filter by status (ACTIVE, CANCELED, PAUSED, EXPIRED, ENDED).
            customer_id: Filter by customer ID.
        """
        params: Dict[str, Any] = {"page": page, "size": size}
        if status is not None:
            params["status"] = status
        if customer_id is not None:
            params["customer_id"] = customer_id

        data = self._get("subscriptions", params)
        page_data = data["data"]
        return PaginatedResponse[SubscriptionResponse](
            records=[SubscriptionResponse.model_validate(r) for r in page_data["records"]],
            total=page_data["total"],
            page=page_data["page"],
            size=page_data["size"],
            pages=page_data["pages"],
        )

    def get_subscription(self, subscription_id: str) -> SubscriptionResponse:
        """Get a single subscription by ID."""
        data = self._get(f"subscriptions/{subscription_id}")
        return SubscriptionResponse.model_validate(data["data"])

    # ── /products ───────────────────────────────────────────────────────

    def list_products(
        self,
        *,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        status: str = "PUBLISHED",
    ) -> PaginatedResponse[ProductResponse]:
        """List products with optional filters.

        Args:
            search: Search by product name.
            status: Filter by status (default: PUBLISHED).
        """
        params: Dict[str, Any] = {"page": page, "size": size, "status": status}
        if search is not None:
            params["search"] = search

        data = self._get("products", params)
        page_data = data["data"]
        return PaginatedResponse[ProductResponse](
            records=[ProductResponse.model_validate(r) for r in page_data["records"]],
            total=page_data["total"],
            page=page_data["page"],
            size=page_data["size"],
            pages=page_data["pages"],
        )

    def get_product(self, product_id: str) -> ProductResponse:
        """Get a single product by ID."""
        data = self._get(f"products/{product_id}")
        return ProductResponse.model_validate(data["data"])

    # ── /customers ──────────────────────────────────────────────────────

    def list_customers(
        self,
        *,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[CustomerResponse]:
        """List customers (derived from orders)."""
        params: Dict[str, Any] = {"page": page, "size": size}
        data = self._get("customers", params)
        page_data = data["data"]
        return PaginatedResponse[CustomerResponse](
            records=[CustomerResponse.model_validate(r) for r in page_data["records"]],
            total=page_data["total"],
            page=page_data["page"],
            size=page_data["size"],
            pages=page_data["pages"],
        )

    def get_customer(self, customer_id: str) -> CustomerResponse:
        """Get a single customer by ID."""
        data = self._get(f"customers/{customer_id}")
        return CustomerResponse.model_validate(data["data"])

    # ── /entitlements ───────────────────────────────────────────────────

    def check_entitlement(
        self,
        *,
        email: Optional[str] = None,
        wallet: Optional[str] = None,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        refresh: bool = False,
    ) -> EntitlementCheckResponse:
        """Check if a customer is entitled to a product.

        At least one identifier (email, wallet, or customer_id) is required.
        If product_id is provided, checks that specific product.
        If omitted, returns all entitled products.

        Args:
            email: Customer email (Stripe).
            wallet: Buyer wallet address (crypto).
            customer_id: Customer ID (CUS_xxx).
            product_id: Product ID to check (optional).
            refresh: Force refresh from Stripe API (only with email).
        """
        if not any([email, wallet, customer_id]):
            raise ValueError("At least one identifier is required: email, wallet, or customer_id")

        params: Dict[str, Any] = {}
        if email is not None:
            params["email"] = email
        if wallet is not None:
            params["wallet"] = wallet
        if customer_id is not None:
            params["customer_id"] = customer_id
        if product_id is not None:
            params["product_id"] = product_id
        if refresh:
            params["refresh"] = "true"

        data = self._get("entitlements/check", params)
        return EntitlementCheckResponse.model_validate(data["data"])
