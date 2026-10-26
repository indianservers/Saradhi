from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Any, Literal, TypeVar
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

Amount = Annotated[Decimal, Field(max_digits=20, decimal_places=4, allow_inf_nan=False)]
Quantity = Annotated[Decimal, Field(gt=0, max_digits=20, decimal_places=4, allow_inf_nan=False)]
Name = Annotated[str, Field(min_length=1, max_length=200)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BulkMappingIn(Input):
    mapping: dict[str, str] = Field(min_length=1, max_length=20)


class BulkExportIn(Input):
    entity: Literal["branches"]
    city_id: UUID
    limit: int = Field(default=500, ge=1, le=500)


class CustomerConsentIn(Input):
    purpose: Literal["marketing"] = "marketing"
    channel: Literal["push", "email", "sms", "whatsapp"]
    enabled: bool
    policy_version: str = Field(min_length=1, max_length=80)


class CustomerSegmentConditionIn(Input):
    field: Literal[
        "status", "order_count", "gross_purchase_value", "last_order_days", "marketing_consent"
    ]
    op: Literal["eq", "gte", "lte"]
    value: str | int | float | bool
    channel: Literal["push", "email", "sms", "whatsapp"] | None = None


class CustomerSegmentPreviewIn(Input):
    city_id: UUID
    logic: Literal["and", "or"] = "and"
    conditions: list[CustomerSegmentConditionIn] = Field(min_length=1, max_length=10)


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
    state_province_id: UUID | None = None
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


class ZoneCategoryIn(Input):
    category_id: UUID
    enabled: bool


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


class MerchantOnboardingIn(Input):
    organization_id: UUID | None = None
    organization_name: Name | None = None
    brand_name: Name
    merchant_type: Literal["food", "grocery", "retail", "pharmacy", "parcel"]
    branch_name: Name
    city_id: UUID
    latitude: Decimal = Field(ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal = Field(ge=-180, le=180, max_digits=10, decimal_places=7)


class BranchOut(VersionOut):
    name: str
    organization_id: UUID
    brand_id: UUID
    city_id: UUID
    accepting_orders: bool
    merchant_type: Literal["food", "grocery", "retail", "pharmacy", "parcel"] | None = None


class BranchReviewIn(Input):
    decision: Literal["approved", "rejected"]
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=500)


class BranchAvailabilityIn(Input):
    accepting_orders: bool
    expected_version: int = Field(ge=1)


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


class CatalogProductOut(IdOut):
    product_id: UUID
    variant_id: UUID
    branch_id: UUID
    branch_name: str
    merchant_type: Literal["food", "grocery", "retail", "pharmacy", "parcel"]
    category_id: UUID
    category_name: str
    name: str
    variant_name: str
    unit: str
    variable_weight: bool
    currency: str
    unit_price: Decimal
    available_quantity: Decimal
    serviceable: bool | None = None


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


class StockBatchOut(IdOut):
    branch_id: UUID
    variant_id: UUID
    lot_code: str
    quantity: Decimal
    reserved: Decimal
    expires_on: date | None
    received_at: datetime


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
    product_name: str | None = None
    variant_name: str | None = None
    branch_name: str | None = None
    window_starts_at: datetime | None = None
    window_ends_at: datetime | None = None


class QuoteLineOut(BaseModel):
    product_name: str
    variant_name: str
    branch_id: UUID
    quantity: Decimal
    unit: str
    unit_price: Decimal
    currency: str
    total: Decimal
    window_id: UUID
    delivery_method: str
    branch_name: str | None = None
    window_starts_at: datetime | None = None
    window_ends_at: datetime | None = None
    delivery_address: str | None = None


class QuoteOut(IdOut):
    cart_id: UUID
    currency: str
    total: Decimal
    expires_at: datetime
    lines: list[QuoteLineOut] = Field(default_factory=list)


class ConfirmIn(Input):
    quote_id: UUID


class OrderOut(VersionOut):
    currency: str
    total: Decimal


class ChildOut(OrderOut):
    order_id: UUID
    branch_id: UUID


class MerchantQueueItem(BaseModel):
    product_name: str
    variant_name: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    total: Decimal


class MerchantQueueOut(ChildOut):
    created_at: datetime
    items: list[MerchantQueueItem] = Field(default_factory=list)


class MerchantQueuePage(BaseModel):
    items: list[MerchantQueueOut]
    next_cursor: str | None = None


class KitchenStationIn(Input):
    name: str = Field(min_length=2, max_length=100)
    is_packaging: bool = False
    max_concurrent: int = Field(default=5, ge=1, le=100)


class KitchenStationOut(Output):
    id: UUID
    version: int
    branch_id: UUID
    name: str
    is_packaging: bool
    max_concurrent: int
    active: bool


class KitchenTaskOut(VersionOut):
    merchant_order_id: UUID
    order_item_id: UUID | None
    branch_id: UUID
    station_id: UUID
    station_name: str
    task_key: str
    task_type: Literal["prep", "packing"]
    label: str
    quantity: Decimal
    target_completed_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    estimate_provenance: str
    estimate_model_version: str
    blocked_by: list[UUID] = Field(default_factory=list)


class KitchenTaskPage(BaseModel):
    items: list[KitchenTaskOut]
    next_cursor: str | None = None


class KitchenTaskTransitionIn(Input):
    target: Literal["in_progress", "paused", "completed"]
    expected_version: int = Field(ge=1)


class KitchenTaskStationIn(Input):
    station_id: UUID
    expected_version: int = Field(ge=1)


class MerchantCatalogOut(BaseModel):
    product_id: UUID
    variant_id: UUID
    name: str
    variant_name: str
    sku: str
    unit: str
    active: bool
    currency: str | None = None
    unit_price: Decimal | None = None
    on_hand: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")


class ReorderLineOut(BaseModel):
    branch_id: UUID
    branch_name: str
    variant_id: UUID
    product_name: str
    variant_name: str
    quantity: Decimal
    delivery_method: str
    address_id: UUID | None = None


class TransitionIn(Input):
    target: Literal["accepted", "rejected", "preparing", "ready", "cancelled"]
    expected_version: int = Field(ge=1)


class VersionIn(Input):
    expected_version: int = Field(ge=1)


class OfferIn(Input):
    pilot_id: UUID | None = None


class ReassignmentIn(Input):
    pilot_id: UUID
    reason: str = Field(min_length=5, max_length=500)


class DispatchPolicyIn(Input):
    weights: dict[str, Decimal] = Field(min_length=2, max_length=2)

    @field_validator("weights")
    @classmethod
    def valid_weights(cls, value):
        if set(value) != {"pickup_distance", "workload"}:
            raise ValueError("Only pickup_distance and workload scoring weights are supported")
        if any(not weight.is_finite() or weight < 0 or weight > 100 for weight in value.values()):
            raise ValueError("Dispatch weights must be finite values between zero and 100")
        return value


class PreparationPredictIn(Input):
    branch_id: UUID
    item_count: int = Field(ge=1, le=100)


class EtaPredictIn(Input):
    task_id: UUID


class DispatchOptimizeIn(Input):
    city_id: UUID
    task_ids: list[UUID] = Field(min_length=1, max_length=50)


class RecommendationQueryIn(Input):
    city_id: UUID
    category_id: UUID | None = None
    limit: int = Field(default=10, ge=1, le=30)


class CopilotQueryIn(Input):
    question: str = Field(min_length=1, max_length=2000)


class AiAgentQueryIn(Input):
    question: str = Field(min_length=1, max_length=1200)
    city_id: UUID | None = None
    branch_id: UUID | None = None
    organization_id: UUID | None = None
    ticket_id: UUID | None = None


class AiAgentQueryOut(Output):
    agent: str
    answer: str
    evidence: dict[str, Any]
    provider: str
    model: str
    fallback: bool
    latency_ms: int


class AiEvaluateIn(Input):
    city_id: UUID


class RecurringPlanCreateIn(Input):
    cart_id: UUID
    timezone: str
    frequency: Literal["daily", "weekly", "monthly"]
    interval: int = Field(default=1, ge=1, le=30)
    local_time: time
    start_date: date
    end_date: date | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("Use a valid IANA time zone") from exc
        return value

    @field_validator("end_date")
    @classmethod
    def valid_plan_dates(cls, value, info):
        start_date = info.data.get("start_date")
        if value and start_date and value < start_date:
            raise ValueError("End date must be on or after the start date")
        return value


class RecurringPlanStatusIn(Input):
    status: Literal["active", "paused", "cancelled"]


class RecurringPlanSkipIn(Input):
    local_date: date


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
    accuracy_m: Decimal = Field(ge=0, le=1000, max_digits=8, decimal_places=2)
    heading_degrees: Decimal | None = Field(
        default=None, ge=0, le=360, max_digits=6, decimal_places=2
    )
    speed_mps: Decimal | None = Field(default=None, ge=0, le=100, max_digits=7, decimal_places=2)
    client_sequence: int = Field(ge=0)
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    app_state: Literal["foreground", "background"] = "foreground"


class PilotAvailabilityIn(Input):
    state: Literal["online_available", "on_break", "unavailable", "offline"]


class PilotIncidentIn(Input):
    category: Literal[
        "vehicle_breakdown",
        "road_blockage",
        "accident",
        "unsafe_pickup_area",
        "unsafe_delivery_area",
        "customer_unavailable",
        "merchant_closed",
        "package_damaged",
        "wrong_package",
        "medical_emergency",
        "severe_weather",
        "navigation_failure",
        "low_battery",
        "other",
    ]
    summary: str = Field(min_length=10, max_length=1000)
    delivery_task_id: UUID | None = None
    safety_emergency: bool = False


class PilotIncidentResolveIn(Input):
    resolution_summary: str = Field(min_length=10, max_length=1000)


class LocationConsentIn(Input):
    accepted: bool
    policy_version: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9._-]+$")


class TrackingTicketOut(Output):
    ticket: str
    expires_at: datetime


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


class RazorpayVerifyIn(Input):
    order_id: str = Field(min_length=8, max_length=64, pattern=r"^order_[A-Za-z0-9]+$")
    payment_id: str = Field(min_length=8, max_length=64, pattern=r"^pay_[A-Za-z0-9]+$")
    signature: str = Field(min_length=64, max_length=64, pattern=r"^[A-Fa-f0-9]{64}$")


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
