"""Typed core ORM. Supplemental relational models are registered in foundations.py.

UUIDv4 is deliberate on Python 3.12; no unreliable emulated UUIDv7 generator.
"""

from datetime import datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database import Base


def fk(target: str, **kw):
    return mapped_column(ForeignKey(target, ondelete="RESTRICT"), **kw)


class Record:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Record, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}
    status: Mapped[str] = mapped_column(Text, default="active", server_default="active")


class Email(Record, Base):
    __tablename__ = "user_email_addresses"
    __table_args__ = (
        CheckConstraint("address = lower(address)", name="normalized_email"),
        {"schema": "identity"},
    )
    user_id: Mapped[UUID] = fk("identity.users.id", unique=True, index=True)
    address: Mapped[str] = mapped_column(Text, unique=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Credential(Record, Base):
    __tablename__ = "user_credentials"
    __table_args__ = {"schema": "identity"}
    user_id: Mapped[UUID] = fk("identity.users.id", unique=True)
    password_hash: Mapped[str] = mapped_column(Text)


class Session(Record, Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "identity"}
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(Record, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "identity"}
    session_id: Mapped[UUID] = fk("identity.sessions.id", index=True)
    digest: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Organization(Record, Base):
    __tablename__ = "organizations"
    __table_args__ = {"schema": "identity"}
    name: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[UUID] = fk("identity.users.id", index=True)


class Membership(Record, Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"), {"schema": "identity"})
    organization_id: Mapped[UUID] = fk("identity.organizations.id", index=True)
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    status: Mapped[str] = mapped_column(Text, default="active")


class Role(Record, Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "identity"}
    name: Mapped[str] = mapped_column(Text, unique=True)


class Permission(Record, Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "identity"}
    code: Mapped[str] = mapped_column(Text, unique=True)


class RolePermission(Record, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"), {"schema": "identity"})
    role_id: Mapped[UUID] = fk("identity.roles.id", index=True)
    permission_id: Mapped[UUID] = fk("identity.permissions.id")


class RoleAssignment(Record, Base):
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "organization_id",
            "city_id",
            "branch_id",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(
            "(city_id IS NULL AND branch_id IS NULL) OR organization_id IS NOT NULL",
            name="scoped_assignment",
        ),
        {"schema": "identity"},
    )
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    role_id: Mapped[UUID] = fk("identity.roles.id")
    organization_id: Mapped[UUID | None] = fk("identity.organizations.id", index=True)
    city_id: Mapped[UUID | None] = fk("geo.cities.id")
    branch_id: Mapped[UUID | None] = fk("merchant.merchant_branches.id")


class Challenge(Record, Base):
    __tablename__ = "verification_challenges"
    __table_args__ = (
        CheckConstraint("attempts BETWEEN 0 AND 5", name="attempt_bound"),
        {"schema": "identity"},
    )
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    purpose: Mapped[str] = mapped_column(Text)
    digest: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    destination_reference: Mapped[str] = mapped_column(Text)


class Country(Record, Base):
    __tablename__ = "countries"
    __table_args__ = {"schema": "geo"}
    code: Mapped[str] = mapped_column(String(2), unique=True)
    name: Mapped[str] = mapped_column(Text)


class City(Record, Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("country_id", "name"), {"schema": "geo"})
    country_id: Mapped[UUID] = fk("geo.countries.id")
    name: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Zone(Record, Base):
    __tablename__ = "service_zones"
    __table_args__ = (UniqueConstraint("city_id", "name"), {"schema": "geo"})
    city_id: Mapped[UUID] = fk("geo.cities.id", index=True)
    name: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ServiceArea(Record, Base):
    __tablename__ = "delivery_service_areas"
    __table_args__ = (UniqueConstraint("id", "zone_id"), {"schema": "geo"})
    zone_id: Mapped[UUID] = fk("geo.service_zones.id", index=True)
    name: Mapped[str] = mapped_column(Text)
    # Spatial boundary is added ONLY by the explicit optional PostGIS migration.
    spatial_ready: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )


class Address(Record, Base):
    __tablename__ = "addresses"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", name="coordinates"
        ),
        {"schema": "geo"},
    )
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    city_id: Mapped[UUID] = fk("geo.cities.id")
    label: Mapped[str] = mapped_column(Text)
    address_text: Mapped[str] = mapped_column(Text)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))


class Brand(Record, Base):
    __tablename__ = "merchant_brands"
    __table_args__ = (UniqueConstraint("id", "organization_id"), {"schema": "merchant"})
    organization_id: Mapped[UUID] = fk("identity.organizations.id", index=True)
    name: Mapped[str] = mapped_column(Text)
    merchant_type: Mapped[str] = mapped_column(Text)


class Branch(Record, Base):
    __tablename__ = "merchant_branches"
    __table_args__ = (
        ForeignKeyConstraint(
            ["brand_id", "organization_id"],
            ["merchant.merchant_brands.id", "merchant.merchant_brands.organization_id"],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "organization_id"),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", name="coordinates"
        ),
        CheckConstraint(
            "status IN ('pending','approved','rejected','suspended')", name="branch_status"
        ),
        {"schema": "merchant"},
    )
    brand_id: Mapped[UUID] = mapped_column()
    organization_id: Mapped[UUID] = fk("identity.organizations.id", index=True)
    city_id: Mapped[UUID] = fk("geo.cities.id", index=True)
    name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending")
    accepting_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    version: Mapped[int] = mapped_column(Integer, default=1)


class OperatingHour(Record, Base):
    __tablename__ = "merchant_operating_hours"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6 AND opens_at < closes_at", name="valid_hours"),
        UniqueConstraint("branch_id", "weekday", "opens_at"),
        {"schema": "merchant"},
    )
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id", index=True)
    weekday: Mapped[int] = mapped_column(Integer)
    opens_at: Mapped[time] = mapped_column(Time)
    closes_at: Mapped[time] = mapped_column(Time)


class BranchArea(Record, Base):
    __tablename__ = "merchant_service_areas"
    __table_args__ = (
        UniqueConstraint("branch_id", "area_id", "category_id", "delivery_method"),
        {"schema": "merchant"},
    )
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id", index=True)
    area_id: Mapped[UUID] = fk("geo.delivery_service_areas.id")
    category_id: Mapped[UUID] = fk("catalog.product_categories.id")
    delivery_method: Mapped[str] = mapped_column(Text)


class Category(Record, Base):
    __tablename__ = "product_categories"
    __table_args__ = {"schema": "catalog"}
    name: Mapped[str] = mapped_column(Text, unique=True)
    regulated: Mapped[bool] = mapped_column(Boolean, default=False)


class ZoneCategory(Record, Base):
    __tablename__ = "zone_service_categories"
    __table_args__ = (UniqueConstraint("zone_id", "category_id"), {"schema": "geo"})
    zone_id: Mapped[UUID] = fk("geo.service_zones.id", index=True)
    category_id: Mapped[UUID] = fk("catalog.product_categories.id")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Record, Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("id", "organization_id"), {"schema": "catalog"})
    organization_id: Mapped[UUID] = fk("identity.organizations.id", index=True)
    category_id: Mapped[UUID] = fk("catalog.product_categories.id")
    name: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text, default="each")
    variable_weight: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Variant(Record, Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "sku"), {"schema": "catalog"})
    product_id: Mapped[UUID] = fk("catalog.products.id", index=True)
    sku: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)


class Currency(Record, Base):
    __tablename__ = "currencies"
    __table_args__ = (
        CheckConstraint("scale BETWEEN 0 AND 4", name="currency_scale"),
        {"schema": "finance"},
    )
    code: Mapped[str] = mapped_column(String(3), unique=True)
    scale: Mapped[int] = mapped_column(Integer)


class Price(Record, Base):
    __tablename__ = "product_prices"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="nonnegative_price"),
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="valid_price_period"),
        Index("ix_price_lookup", "branch_id", "variant_id", "starts_at"),
        {"schema": "catalog"},
    )
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id")
    variant_id: Mapped[UUID] = fk("catalog.product_variants.id")
    currency: Mapped[str] = fk("finance.currencies.code")
    price_book_id: Mapped[UUID | None] = fk("catalog.price_books.id")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Stock(Record, Base):
    __tablename__ = "stock_balances"
    __table_args__ = (
        UniqueConstraint("branch_id", "variant_id"),
        CheckConstraint(
            "on_hand >= 0 AND reserved >= 0 AND reserved <= on_hand", name="sellable_stock"
        ),
        {"schema": "inventory"},
    )
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id", index=True)
    variant_id: Mapped[UUID] = fk("catalog.product_variants.id")
    on_hand: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    reserved: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Cart(Record, Base):
    __tablename__ = "carts"
    __table_args__ = {"schema": "commerce"}
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    status: Mapped[str] = mapped_column(Text, default="open")
    version: Mapped[int] = mapped_column(Integer, default=1)


class CartItem(Record, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        {"schema": "commerce"},
    )
    cart_id: Mapped[UUID] = fk("commerce.carts.id", index=True)
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id")
    variant_id: Mapped[UUID] = fk("catalog.product_variants.id")
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    address_id: Mapped[UUID | None] = fk("geo.addresses.id")
    window_id: Mapped[UUID] = fk("fulfillment.delivery_windows.id")
    delivery_method: Mapped[str] = mapped_column(Text, default="pickup")


class Window(Record, Base):
    __tablename__ = "delivery_windows"
    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at AND capacity >= 0 AND reserved BETWEEN 0 AND capacity",
            name="window_capacity",
        ),
        {"schema": "fulfillment"},
    )
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id", index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    reserved: Mapped[int] = mapped_column(Integer, default=0)


class Quote(Record, Base):
    __tablename__ = "checkout_quotes"
    __table_args__ = {"schema": "commerce"}
    cart_id: Mapped[UUID] = fk("commerce.carts.id", index=True)
    user_id: Mapped[UUID] = fk("identity.users.id")
    cart_version: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = fk("finance.currencies.code")
    total: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    snapshot: Mapped[dict] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Order(Record, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total >= 0", name="nonnegative_total"),
        {"schema": "commerce"},
    )
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    quote_id: Mapped[UUID] = fk("commerce.checkout_quotes.id", unique=True)
    status: Mapped[str] = mapped_column(Text, default="confirmed")
    currency: Mapped[str] = fk("finance.currencies.code")
    total: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    version: Mapped[int] = mapped_column(Integer, default=1)


class MerchantOrder(Record, Base):
    __tablename__ = "merchant_orders"
    __table_args__ = (
        CheckConstraint("total >= 0", name="nonnegative_total"),
        UniqueConstraint("id", "branch_id"),
        {"schema": "commerce"},
    )
    order_id: Mapped[UUID] = fk("commerce.orders.id", index=True)
    branch_id: Mapped[UUID] = fk("merchant.merchant_branches.id", index=True)
    status: Mapped[str] = mapped_column(Text, default="pending")
    currency: Mapped[str] = fk("finance.currencies.code")
    total: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    version: Mapped[int] = mapped_column(Integer, default=1)


class OrderItem(Record, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0 AND unit_price >= 0 AND total >= 0", name="order_item_amounts"
        ),
        {"schema": "commerce"},
    )
    merchant_order_id: Mapped[UUID] = fk("commerce.merchant_orders.id", index=True)
    fulfillment_unit_id: Mapped[UUID] = fk("fulfillment.fulfillment_units.id", index=True)
    variant_id: Mapped[UUID] = fk("catalog.product_variants.id")
    product_name: Mapped[str] = mapped_column(Text)
    variant_name: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    total: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    snapshot: Mapped[dict] = mapped_column(JSONB)


class Reservation(Record, Base):
    __tablename__ = "stock_reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_reservation"),
        {"schema": "inventory"},
    )
    stock_id: Mapped[UUID] = fk("inventory.stock_balances.id", index=True)
    order_item_id: Mapped[UUID] = fk("commerce.order_items.id", unique=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(Text, default="reserved")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class StockMovement(Record, Base):
    __tablename__ = "stock_movements"
    __table_args__ = {"schema": "inventory"}
    stock_id: Mapped[UUID] = fk("inventory.stock_balances.id", index=True)
    batch_id: Mapped[UUID | None] = fk("inventory.stock_batches.id")
    reservation_id: Mapped[UUID | None] = fk("inventory.stock_reservations.id")
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    kind: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True)
    actor_id: Mapped[UUID | None] = fk("identity.users.id")


class FulfillmentUnit(Record, Base):
    __tablename__ = "fulfillment_units"
    __table_args__ = {"schema": "fulfillment"}
    merchant_order_id: Mapped[UUID] = fk("commerce.merchant_orders.id", index=True)
    window_id: Mapped[UUID] = fk("fulfillment.delivery_windows.id")
    delivery_method: Mapped[str] = mapped_column(Text)
    address_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, default="pending")


class DeliveryTask(Record, Base):
    __tablename__ = "delivery_tasks"
    __table_args__ = {"schema": "fulfillment"}
    fulfillment_unit_id: Mapped[UUID] = fk("fulfillment.fulfillment_units.id", unique=True)
    status: Mapped[str] = mapped_column(Text, default="unassigned")
    version: Mapped[int] = mapped_column(Integer, default=1)


class Pilot(Record, Base):
    __tablename__ = "pilot_profiles"
    __table_args__ = {"schema": "fulfillment"}
    user_id: Mapped[UUID] = fk("identity.users.id", unique=True)
    city_id: Mapped[UUID] = fk("geo.cities.id", index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    available: Mapped[bool] = mapped_column(Boolean, default=False)


class Assignment(Record, Base):
    __tablename__ = "pilot_assignments"
    __table_args__ = (
        Index(
            "uq_active_task_assignment",
            "task_id",
            unique=True,
            postgresql_where=text("status IN ('offered','accepted','picked_up')"),
        ),
        {"schema": "fulfillment"},
    )
    task_id: Mapped[UUID] = fk("fulfillment.delivery_tasks.id", index=True)
    pilot_id: Mapped[UUID] = fk("fulfillment.pilot_profiles.id", index=True)
    status: Mapped[str] = mapped_column(Text, default="offered")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LatestLocation(Record, Base):
    __tablename__ = "pilot_latest_location"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="location_coordinates",
        ),
        {"schema": "fulfillment"},
    )
    pilot_id: Mapped[UUID] = fk("fulfillment.pilot_profiles.id", unique=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Idempotency(Record, Base):
    __tablename__ = "order_idempotency_records"
    __table_args__ = (UniqueConstraint("user_id", "key"), {"schema": "commerce"})
    user_id: Mapped[UUID] = fk("identity.users.id")
    key: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(Text)
    order_id: Mapped[UUID | None] = fk("commerce.orders.id")


class LedgerBook(Record, Base):
    __tablename__ = "ledger_books"
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "currency"),
        UniqueConstraint("id", "organization_id", "currency", name="uq_ledger_book_currency_scope"),
        UniqueConstraint("id", "organization_id", name="uq_ledger_book_org_scope"),
        {"schema": "finance"},
    )
    organization_id: Mapped[UUID] = fk("identity.organizations.id")
    legal_entity_id: Mapped[UUID] = fk("merchant.merchant_legal_entities.id")
    currency: Mapped[str] = fk("finance.currencies.code")


class LedgerAccount(Record, Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["book_id", "organization_id", "currency"],
            [
                "finance.ledger_books.id",
                "finance.ledger_books.organization_id",
                "finance.ledger_books.currency",
            ],
            ondelete="RESTRICT",
            name="fk_account_book_scope",
        ),
        UniqueConstraint("book_id", "code"),
        UniqueConstraint("id", "organization_id", "currency"),
        {"schema": "finance"},
    )
    organization_id: Mapped[UUID] = fk("identity.organizations.id", index=True)
    book_id: Mapped[UUID] = fk("finance.ledger_books.id")
    currency: Mapped[str] = fk("finance.currencies.code")
    code: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)


class Journal(Record, Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["book_id", "organization_id"],
            ["finance.ledger_books.id", "finance.ledger_books.organization_id"],
            ondelete="RESTRICT",
            name="fk_journal_book_scope",
        ),
        UniqueConstraint("organization_id", "idempotency_key"),
        UniqueConstraint("id", "organization_id"),
        CheckConstraint("status IN ('draft','posted')", name="journal_status"),
        {"schema": "finance"},
    )
    organization_id: Mapped[UUID] = fk("identity.organizations.id")
    book_id: Mapped[UUID] = fk("finance.ledger_books.id")
    idempotency_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="draft")
    description: Mapped[str] = mapped_column(Text)
    reversal_of: Mapped[UUID | None] = fk("finance.journal_entries.id")


class JournalLine(Record, Base):
    __tablename__ = "journal_lines"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id", "organization_id", "currency"],
            [
                "finance.ledger_accounts.id",
                "finance.ledger_accounts.organization_id",
                "finance.ledger_accounts.currency",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["journal_id", "organization_id"],
            ["finance.journal_entries.id", "finance.journal_entries.organization_id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount <> 0", name="nonzero_line"),
        {"schema": "finance"},
    )
    journal_id: Mapped[UUID] = mapped_column(index=True)
    organization_id: Mapped[UUID] = mapped_column()
    account_id: Mapped[UUID] = mapped_column()
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))  # debit positive, credit negative


class PaymentIntent(Record, Base):
    __tablename__ = "payment_intents"
    __table_args__ = (
        UniqueConstraint("order_id", "provider"),
        CheckConstraint("amount > 0 AND refunded BETWEEN 0 AND amount", name="payment_amounts"),
        {"schema": "finance"},
    )
    order_id: Mapped[UUID] = fk("commerce.orders.id")
    provider: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending")
    currency: Mapped[str] = fk("finance.currencies.code")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    refunded: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    provider_reference: Mapped[str | None] = mapped_column(Text, unique=True)


class Webhook(Record, Base):
    __tablename__ = "payment_webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_id"), {"schema": "finance"})
    provider: Mapped[str] = mapped_column(Text)
    event_id: Mapped[str] = mapped_column(Text)
    payment_id: Mapped[UUID] = fk("finance.payment_intents.id")
    payload_hash: Mapped[str] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Refund(Record, Base):
    __tablename__ = "payment_refunds"
    __table_args__ = (
        UniqueConstraint("payment_id", "idempotency_key"),
        CheckConstraint("amount > 0", name="positive_refund"),
        {"schema": "finance"},
    )
    payment_id: Mapped[UUID] = fk("finance.payment_intents.id")
    approval_id: Mapped[UUID | None] = fk("operations.refund_approval_requests.id", unique=True)
    idempotency_key: Mapped[str] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    status: Mapped[str] = mapped_column(Text)
    provider_reference: Mapped[str] = mapped_column(Text, unique=True)


class Outbox(Record, Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index(
            "ix_outbox_pending",
            "available_at",
            postgresql_where=text("delivered_at IS NULL AND dead_lettered_at IS NULL"),
        ),
        {"schema": "integration"},
    )
    event_type: Mapped[str] = mapped_column(Text)
    payload_version: Mapped[int] = mapped_column(Integer, default=1)
    aggregate_id: Mapped[UUID] = mapped_column()
    payload: Mapped[dict] = mapped_column(JSONB)
    correlation_id: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Inbox(Record, Base):
    __tablename__ = "inbox_processed_messages"
    __table_args__ = (UniqueConstraint("consumer", "event_id"), {"schema": "integration"})
    consumer: Mapped[str] = mapped_column(Text)
    event_id: Mapped[UUID] = mapped_column()


class AuditEvent(Record, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_scope_time", "organization_id", "created_at", "id"),
        {"schema": "audit"},
    )
    organization_id: Mapped[UUID | None] = fk("identity.organizations.id")
    actor_id: Mapped[UUID | None] = fk("identity.users.id")
    action: Mapped[str] = mapped_column(Text)
    resource_id: Mapped[UUID] = mapped_column()
    correlation_id: Mapped[str] = mapped_column(Text)
    safe_changes: Mapped[dict] = mapped_column(JSONB, default=dict)


class OrderHistory(Record, Base):
    __tablename__ = "order_status_history"
    __table_args__ = {"schema": "commerce"}
    order_id: Mapped[UUID] = fk("commerce.orders.id", index=True)
    merchant_order_id: Mapped[UUID | None] = fk("commerce.merchant_orders.id")
    previous: Mapped[str | None] = mapped_column(Text)
    current: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[UUID] = fk("identity.users.id")


class Ticket(Record, Base):
    __tablename__ = "support_tickets"
    __table_args__ = {"schema": "operations"}
    user_id: Mapped[UUID] = fk("identity.users.id", index=True)
    order_id: Mapped[UUID | None] = fk("commerce.orders.id")
    organization_id: Mapped[UUID | None] = fk("identity.organizations.id")
    subject: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="open")


class TicketMessage(Record, Base):
    __tablename__ = "support_ticket_messages"
    __table_args__ = {"schema": "operations"}
    ticket_id: Mapped[UUID] = fk("operations.support_tickets.id", index=True)
    author_id: Mapped[UUID] = fk("identity.users.id")
    body: Mapped[str] = mapped_column(Text)


class RateBucket(Record, Base):
    __tablename__ = "auth_rate_buckets"
    __table_args__ = (UniqueConstraint("bucket_key", "window_start"), {"schema": "identity"})
    bucket_key: Mapped[str] = mapped_column(Text)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    attempts: Mapped[int] = mapped_column(Integer)
