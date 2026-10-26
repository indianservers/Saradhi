from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Literal, TypeVar
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

Amount = Annotated[Decimal, Field(max_digits=20, decimal_places=4, allow_inf_nan=False)]
Quantity = Annotated[Decimal, Field(gt=0, max_digits=20, decimal_places=4, allow_inf_nan=False)]
Name = Annotated[str, Field(min_length=1, max_length=200)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IdOut(Output):
    id: UUID


class NamedOut(IdOut):
    name: str


class StateOut(IdOut):
    status: str


class VersionOut(StateOut):
    version: int


T = TypeVar("T")


class Page[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None


class RegisterIn(Input):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: SecretStr = Field(min_length=12, max_length=128)


class LoginIn(Input):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)


class RefreshIn(Input):
    refresh_token: SecretStr = Field(min_length=40, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_in: int


class NameIn(Input):
    name: Name


class CountryIn(NameIn):
    code: str = Field(pattern=r"^[A-Z]{2}$")


class CountryOut(NamedOut):
    code: str


class CityIn(NameIn):
    country_id: UUID
    timezone: str

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("Use a valid IANA time zone") from exc
        return value


class CityOut(NamedOut):
    country_id: UUID
    timezone: str
    active: bool


class ZoneIn(NameIn):
    city_id: UUID


class AddressIn(Input):
    city_id: UUID
    label: Name
    address_text: str = Field(min_length=5, max_length=1000)
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=10, decimal_places=7)


class AddressOut(IdOut):
    city_id: UUID
    label: str
    address_text: str
    latitude: Decimal
    longitude: Decimal


class BrandIn(NameIn):
    organization_id: UUID
    merchant_type: Literal["food", "grocery", "retail", "pharmacy", "parcel"]


class BranchIn(NameIn):
    brand_id: UUID
    city_id: UUID
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=10, decimal_places=7)


class BranchOut(VersionOut):
    name: str
    organization_id: UUID
    brand_id: UUID
    city_id: UUID
    accepting_orders: bool


class BranchReviewIn(Input):
    decision: Literal["approved", "rejected"]
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=500)


class HoursIn(Input):
    weekday: int = Field(ge=0, le=6)
    opens_at: time
    closes_at: time


class CapabilityIn(Input):
    method: Literal["pickup", "courier", "merchant_delivery"]
    active: bool = True


class CategoryIn(NameIn):
    regulated: bool = False


class ProductIn(NameIn):
    organization_id: UUID
    category_id: UUID
    unit: Literal["each", "kg", "litre"] = "each"
    variable_weight: bool = False


class VariantIn(NameIn):
    sku: str = Field(min_length=1, max_length=100)


class ProductOut(NamedOut):
    organization_id: UUID
    category_id: UUID
    unit: str
    variable_weight: bool
    active: bool


class VariantOut(NamedOut):
    product_id: UUID
    sku: str


class PriceIn(Input):
    variant_id: UUID
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: Amount = Field(ge=0)
    starts_at: datetime
    ends_at: datetime | None = None
    price_book_id: UUID | None = None

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Timestamp requires a UTC offset")
        return value


class PriceOut(IdOut):
    branch_id: UUID
    variant_id: UUID
    currency: str
    amount: Decimal
    starts_at: datetime
    ends_at: datetime | None


class WindowIn(Input):
    starts_at: datetime
    ends_at: datetime
    capacity: int = Field(ge=1, le=10000)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("Timestamp requires an explicit offset")
        return value


class WindowOut(IdOut):
    branch_id: UUID
    starts_at: datetime
    ends_at: datetime
    capacity: int
    reserved: int


class StockAdjustmentIn(Input):
    variant_id: UUID
    batch_id: UUID | None = None
    delta: Amount
    idempotency_key: str = Field(min_length=8, max_length=128)


class BatchIn(Input):
    variant_id: UUID
    lot_code: str = Field(min_length=1, max_length=100)
    quantity: Quantity
    expires_on: date | None = None
    idempotency_key: str = Field(min_length=8, max_length=128)


class StockOut(IdOut):
    branch_id: UUID
    variant_id: UUID
    on_hand: Decimal
    reserved: Decimal
    version: int


class CartItemIn(Input):
    branch_id: UUID
    variant_id: UUID
    quantity: Quantity
    address_id: UUID | None = None
    window_id: UUID
    delivery_method: Literal["pickup", "courier", "merchant_delivery"] = "pickup"


class CartItemOut(IdOut):
    cart_id: UUID
    branch_id: UUID
    variant_id: UUID
    quantity: Decimal
    address_id: UUID | None
    window_id: UUID
    delivery_method: str


class QuoteOut(IdOut):
    cart_id: UUID
    currency: str
    total: Decimal
    expires_at: datetime


class ConfirmIn(Input):
    quote_id: UUID


class OrderOut(VersionOut):
    currency: str
    total: Decimal


class ChildOut(OrderOut):
    order_id: UUID
    branch_id: UUID


class TransitionIn(Input):
    target: Literal["accepted", "rejected", "preparing", "ready", "cancelled"]
    expected_version: int = Field(ge=1)


class VersionIn(Input):
    expected_version: int = Field(ge=1)


class OfferIn(Input):
    pilot_id: UUID | None = None


class AssignmentOut(StateOut):
    task_id: UUID
    pilot_id: UUID
    expires_at: datetime


class PilotIn(Input):
    city_id: UUID


class AvailableIn(Input):
    available: bool


class LocationIn(Input):
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=10, decimal_places=7)
    observed_at: datetime


class CurrencyIn(Input):
    code: str = Field(pattern=r"^[A-Z]{3}$")
    scale: int = Field(ge=0, le=4)


class AccountIn(Input):
    organization_id: UUID
    book_id: UUID
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    code: Name
    kind: Literal["asset", "liability", "equity", "revenue", "expense"]


class LegalEntityIn(Input):
    country_id: UUID
    registered_name: Name
    registration_reference: Name


class BookIn(Input):
    organization_id: UUID
    legal_entity_id: UUID
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class JournalLineIn(Input):
    account_id: UUID
    amount: Amount


class JournalIn(Input):
    organization_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=128)
    description: str = Field(min_length=1, max_length=500)
    lines: list[JournalLineIn] = Field(min_length=2, max_length=100)


class PaymentIn(Input):
    order_id: UUID


class PaymentOut(StateOut):
    order_id: UUID
    provider: str
    currency: str
    amount: Decimal
    refunded: Decimal


class RefundIn(Input):
    organization_id: UUID
    approval_id: UUID
    amount: Amount = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=128)


class RefundApprovalIn(Input):
    organization_id: UUID
    order_id: UUID
    amount: Amount = Field(gt=0)


class ApprovalDecisionIn(Input):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=5, max_length=500)


class QuantityIn(Input):
    quantity: Quantity
    expected_version: int = Field(ge=1)


class HistoryOut(IdOut):
    order_id: UUID
    merchant_order_id: UUID | None
    previous: str | None
    current: str
    created_at: datetime


class MovementOut(IdOut):
    stock_id: UUID
    quantity: Decimal
    kind: str
    created_at: datetime


class TaskOut(VersionOut):
    fulfillment_unit_id: UUID


class ServiceabilityIn(Input):
    branch_id: UUID
    window_id: UUID
    category_id: UUID
    address_id: UUID | None = None
    delivery_method: Literal["pickup", "courier", "merchant_delivery"]


class ServiceabilityOut(BaseModel):
    serviceable: bool


class TicketIn(Input):
    subject: str = Field(min_length=3, max_length=200)
    order_id: UUID | None = None


class MessageIn(Input):
    body: str = Field(min_length=1, max_length=5000)


class MessageOut(IdOut):
    ticket_id: UUID
    author_id: UUID
    body: str


class MemberIn(Input):
    user_id: UUID
    role: Literal["branch_manager", "kitchen_operator"]
    branch_id: UUID


class OtpIn(Input):
    purpose: Literal["verify_email"] = "verify_email"


class OtpConsumeIn(Input):
    code: SecretStr = Field(min_length=6, max_length=6)


class AuditOut(IdOut):
    actor_id: UUID | None
    action: str
    resource_id: UUID
    created_at: datetime
    correlation_id: str
