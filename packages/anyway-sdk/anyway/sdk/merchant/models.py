"""Merchant API models.

Core models are auto-generated from the OpenAPI spec via:
    cd anyway-backend-go && make generate-merchant-sdk

Hand-written additions:
    - PaginatedResponse[T]: generic pagination wrapper (Go generics not in OpenAPI)
    - ApiResponse[T]: response envelope
    - model_config on generated models for populate_by_name support
"""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Re-export generated models with populate_by_name enabled
from .gen.models import (  # noqa: F401
    CustomerResponse as _CustomerResponse,
    EntitledProduct as _EntitledProduct,
    EntitlementCheckResponse as _EntitlementCheckResponse,
    MeResponse as _MeResponse,
    OrderDetailResponse as _OrderDetailResponse,
    OrderResponse as _OrderResponse,
    ProductResponse as _ProductResponse,
    SubscriptionResponse as _SubscriptionResponse,
)

_BY_NAME = ConfigDict(populate_by_name=True)


class MeResponse(_MeResponse):
    model_config = _BY_NAME


class OrderResponse(_OrderResponse):
    model_config = _BY_NAME


class OrderDetailResponse(_OrderDetailResponse):
    model_config = _BY_NAME


class SubscriptionResponse(_SubscriptionResponse):
    model_config = _BY_NAME


class ProductResponse(_ProductResponse):
    model_config = _BY_NAME


class CustomerResponse(_CustomerResponse):
    model_config = _BY_NAME


class EntitledProduct(_EntitledProduct):
    model_config = _BY_NAME


class EntitlementCheckResponse(_EntitlementCheckResponse):
    model_config = _BY_NAME
    products: List[EntitledProduct] = Field(default_factory=list)


# ── Hand-written (not in OpenAPI spec) ──────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


class PaginatedResponse(BaseModel, Generic[T]):
    records: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0
