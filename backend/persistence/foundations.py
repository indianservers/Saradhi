"""Supplemental relational foundations. No generic EAV or unvalidated CRUD endpoints.

Each declaration specifies actual typed business columns and explicit FK targets. These
tables share the same SQLAlchemy registry as typed core models and are mapped for repositories.
The migration is a frozen DDL snapshot, never dynamic create_all at runtime.
"""

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Table,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from backend.persistence.models import Base

FOUNDATION_MODELS = {}


def define(schema, name, fields, *, unique=(), checks=(), immutable=False):
    columns = [
        Column("id", Uuid, primary_key=True, default=uuid4),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    ]
    if not immutable:
        columns.append(
            Column(
                "updated_at",
                DateTime(timezone=True),
                nullable=False,
                server_default=func.now(),
                onupdate=func.now(),
            )
        )
    for field, kind in fields.items():
        nullable = kind.endswith("?")
        kind = kind.rstrip("?")
        if "." in kind:
            target = kind if kind.count(".") == 2 else kind + ".id"
            column = Column(field, Uuid, ForeignKey(target, ondelete="RESTRICT"), nullable=nullable)
        else:
            types = {
                "text": Text,
                "uuid": Uuid,
                "int": Integer,
                "bool": Boolean,
                "amount": Numeric(20, 4),
                "quantity": Numeric(20, 4),
                "coordinate": Numeric(10, 7),
                "json": JSONB,
                "date": Date,
                "time": Time,
                "timestamp": DateTime(timezone=True),
            }
            column = Column(field, types[kind], nullable=nullable)
        columns.append(column)
    constraints = [UniqueConstraint(*group) for group in unique]
    constraints += [CheckConstraint(sql, name=f"rule_{i}") for i, sql in enumerate(checks)]
    table = Table(
        name,
        Base.metadata,
        *columns,
        *constraints,
        schema=schema,
        info={"immutable": immutable, "foundation": True},
    )
    for column in table.columns:
        if column.foreign_keys:
            Index(f"ix_{name}_{column.name}", column)
    model = type("".join(part.title() for part in (schema + "_" + name).split("_")), (), {})
    Base.registry.map_imperatively(model, table)
    FOUNDATION_MODELS[f"{schema}.{name}"] = model
    return table


def register():
    d = define
    d(
        "identity",
        "user_profiles",
        {"user_id": "identity.users", "display_name": "text", "locale": "text"},
        unique=[("user_id",)],
    )
    d(
        "identity",
        "user_phone_numbers",
        {"user_id": "identity.users", "e164": "text", "verified_at": "timestamp?"},
        unique=[("e164",)],
    )
    d(
        "identity",
        "external_identities",
        {"user_id": "identity.users", "issuer": "text", "subject": "text"},
        unique=[("issuer", "subject")],
    )
    d(
        "identity",
        "user_devices",
        {
            "user_id": "identity.users",
            "platform": "text",
            "device_key_hash": "text",
            "last_seen_at": "timestamp",
        },
        unique=[("user_id", "device_key_hash")],
    )
    d(
        "identity",
        "organization_settings",
        {"organization_id": "identity.organizations", "setting_key": "text", "value": "json"},
        unique=[("organization_id", "setting_key")],
    )
    d(
        "identity",
        "invitations",
        {
            "organization_id": "identity.organizations",
            "email_digest": "text",
            "token_digest": "text",
            "role_id": "identity.roles",
            "expires_at": "timestamp",
            "accepted_at": "timestamp?",
        },
        unique=[("token_digest",)],
    )
    d(
        "identity",
        "login_attempts",
        {
            "identity_digest": "text",
            "network_digest": "text",
            "succeeded": "bool",
            "occurred_at": "timestamp",
        },
        immutable=True,
    )
    d(
        "identity",
        "authentication_events",
        {
            "user_id": "identity.users?",
            "event_type": "text",
            "session_id": "identity.sessions?",
            "correlation_id": "text",
        },
        immutable=True,
    )
    d(
        "identity",
        "customer_profiles",
        {"user_id": "identity.users", "preferred_currency": "text"},
        unique=[("user_id",)],
    )
    d(
        "geo",
        "states_provinces",
        {"country_id": "geo.countries", "name": "text", "code": "text"},
        unique=[("country_id", "code")],
    )
    d("geo", "service_regions", {"country_id": "geo.countries", "name": "text", "timezone": "text"})
    d(
        "geo",
        "zone_boundaries",
        {
            "zone_id": "geo.service_zones",
            "revision": "int",
            "effective_at": "timestamp",
            "object_key": "text",
        },
        unique=[("zone_id", "revision")],
    )
    d(
        "geo",
        "postal_codes",
        {"city_id": "geo.cities", "code": "text"},
        unique=[("city_id", "code")],
    )
    d(
        "geo",
        "geo_locations",
        {
            "address_id": "geo.addresses",
            "latitude": "coordinate",
            "longitude": "coordinate",
            "source": "text",
        },
        checks=["latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180"],
    )
    d("geo", "operating_calendars", {"city_id": "geo.cities", "name": "text", "timezone": "text"})
    d(
        "geo",
        "holidays",
        {
            "calendar_id": "geo.operating_calendars",
            "local_date": "date",
            "closed": "bool",
            "name": "text",
        },
        unique=[("calendar_id", "local_date")],
    )
    d(
        "geo",
        "zone_operating_hours",
        {"zone_id": "geo.service_zones", "weekday": "int", "opens_at": "time", "closes_at": "time"},
        checks=["weekday BETWEEN 0 AND 6", "opens_at < closes_at"],
    )
    d(
        "geo",
        "zone_delivery_policies",
        {
            "zone_id": "geo.service_zones",
            "delivery_method": "text",
            "maximum_distance_m": "int",
            "active": "bool",
        },
        unique=[("zone_id", "delivery_method")],
        checks=["maximum_distance_m > 0"],
    )
    d(
        "geo",
        "zone_capacity_settings",
        {"zone_id": "geo.service_zones", "maximum_active_tasks": "int", "version": "int"},
        unique=[("zone_id",)],
        checks=["maximum_active_tasks > 0"],
    )
    d(
        "merchant",
        "merchant_organizations",
        {"organization_id": "identity.organizations", "onboarding_status": "text"},
        unique=[("organization_id",)],
    )
    d("merchant", "merchant_categories", {"name": "text"}, unique=[("name",)])
    d(
        "merchant",
        "merchant_category_assignments",
        {"brand_id": "merchant.merchant_brands", "category_id": "merchant.merchant_categories"},
        unique=[("brand_id", "category_id")],
    )
    d(
        "merchant",
        "merchant_legal_entities",
        {
            "organization_id": "identity.organizations",
            "country_id": "geo.countries",
            "registered_name": "text",
            "registration_reference": "text",
        },
        unique=[("country_id", "registration_reference")],
    )
    d(
        "merchant",
        "merchant_documents",
        {
            "organization_id": "identity.organizations",
            "document_type": "text",
            "private_object_key": "text",
            "expires_at": "timestamp?",
            "review_status": "text",
        },
    )
    d(
        "merchant",
        "merchant_contracts",
        {
            "organization_id": "identity.organizations",
            "legal_entity_id": "merchant.merchant_legal_entities",
            "private_object_key": "text",
            "starts_at": "timestamp",
            "ends_at": "timestamp?",
        },
    )
    d(
        "merchant",
        "merchant_commission_agreements",
        {
            "contract_id": "merchant.merchant_contracts",
            "rate": "amount",
            "starts_at": "timestamp",
            "ends_at": "timestamp?",
        },
        checks=["rate BETWEEN 0 AND 1"],
    )
    d(
        "merchant",
        "merchant_bank_accounts",
        {
            "legal_entity_id": "merchant.merchant_legal_entities",
            "provider_token": "text",
            "display_last_four": "text",
            "verified_at": "timestamp?",
        },
    )
    d(
        "merchant",
        "merchant_tax_registrations",
        {
            "legal_entity_id": "merchant.merchant_legal_entities",
            "country_id": "geo.countries",
            "registration_token": "text",
            "tax_type": "text",
        },
    )
    d(
        "merchant",
        "merchant_staff",
        {
            "organization_id": "identity.organizations",
            "user_id": "identity.users",
            "branch_id": "merchant.merchant_branches?",
            "active": "bool",
        },
        unique=[("organization_id", "user_id", "branch_id")],
    )
    d(
        "merchant",
        "merchant_staff_roles",
        {"staff_id": "merchant.merchant_staff", "role_id": "identity.roles"},
        unique=[("staff_id", "role_id")],
    )
    d(
        "merchant",
        "merchant_special_hours",
        {
            "branch_id": "merchant.merchant_branches",
            "local_date": "date",
            "opens_at": "time",
            "closes_at": "time",
        },
        checks=["opens_at < closes_at"],
    )
    d(
        "merchant",
        "merchant_temporary_closures",
        {
            "branch_id": "merchant.merchant_branches",
            "starts_at": "timestamp",
            "ends_at": "timestamp",
            "reason": "text",
        },
        checks=["ends_at > starts_at"],
    )
    d(
        "merchant",
        "merchant_fulfillment_capabilities",
        {"branch_id": "merchant.merchant_branches", "method": "text", "active": "bool"},
        unique=[("branch_id", "method")],
    )
    d(
        "merchant",
        "merchant_onboarding_reviews",
        {
            "branch_id": "merchant.merchant_branches",
            "reviewer_id": "identity.users",
            "decision": "text",
            "safe_reason": "text",
        },
        immutable=True,
    )
    d(
        "merchant",
        "merchant_status_history",
        {
            "branch_id": "merchant.merchant_branches",
            "actor_id": "identity.users",
            "previous": "text",
            "current": "text",
        },
        immutable=True,
    )
    d(
        "catalog",
        "category_hierarchy",
        {"parent_id": "catalog.product_categories", "child_id": "catalog.product_categories"},
        unique=[("parent_id", "child_id")],
        checks=["parent_id <> child_id"],
    )
    d(
        "catalog",
        "category_attributes",
        {
            "category_id": "catalog.product_categories",
            "name": "text",
            "value_type": "text",
            "required": "bool",
        },
        unique=[("category_id", "name")],
    )
    d(
        "catalog",
        "merchant_catalogs",
        {
            "organization_id": "identity.organizations",
            "branch_id": "merchant.merchant_branches?",
            "name": "text",
            "active": "bool",
        },
    )
    d(
        "catalog",
        "catalog_sections",
        {"catalog_id": "catalog.merchant_catalogs", "name": "text", "sort_order": "int"},
    )
    d(
        "catalog",
        "option_groups",
        {
            "organization_id": "identity.organizations",
            "name": "text",
            "minimum_selections": "int",
            "maximum_selections": "int",
        },
        checks=["minimum_selections >= 0 AND maximum_selections >= minimum_selections"],
    )
    d(
        "catalog",
        "option_values",
        {"group_id": "catalog.option_groups", "name": "text", "price_delta": "amount"},
        checks=["price_delta >= 0"],
    )
    d(
        "catalog",
        "product_options",
        {"product_id": "catalog.products", "group_id": "catalog.option_groups"},
        unique=[("product_id", "group_id")],
    )
    d(
        "catalog",
        "product_option_assignments",
        {"variant_id": "catalog.product_variants", "option_id": "catalog.option_values"},
        unique=[("variant_id", "option_id")],
    )
    d(
        "catalog",
        "product_images",
        {
            "product_id": "catalog.products",
            "object_key": "text",
            "alt_text": "text",
            "sort_order": "int",
        },
    )
    d(
        "catalog",
        "product_allergens",
        {"product_id": "catalog.products", "allergen_code": "text", "may_contain": "bool"},
        unique=[("product_id", "allergen_code")],
    )
    d(
        "catalog",
        "dietary_attributes",
        {"product_id": "catalog.products", "dietary_code": "text"},
        unique=[("product_id", "dietary_code")],
    )
    d(
        "catalog",
        "product_tags",
        {"product_id": "catalog.products", "tag": "text"},
        unique=[("product_id", "tag")],
    )
    d(
        "catalog",
        "product_branch_availability",
        {
            "branch_id": "merchant.merchant_branches",
            "variant_id": "catalog.product_variants",
            "available": "bool",
        },
        unique=[("branch_id", "variant_id")],
    )
    d(
        "catalog",
        "price_books",
        {
            "organization_id": "identity.organizations",
            "name": "text",
            "currency_id": "finance.currencies",
            "starts_at": "timestamp",
            "ends_at": "timestamp?",
        },
    )
    d(
        "catalog",
        "product_tax_categories",
        {"product_id": "catalog.products", "tax_code_id": "finance.tax_codes"},
        unique=[("product_id", "tax_code_id")],
    )
    d(
        "catalog",
        "product_availability_windows",
        {
            "product_id": "catalog.products",
            "branch_id": "merchant.merchant_branches",
            "starts_at": "timestamp",
            "ends_at": "timestamp",
        },
        checks=["ends_at > starts_at"],
    )
    d(
        "catalog",
        "product_customizations",
        {
            "product_id": "catalog.products",
            "option_group_id": "catalog.option_groups",
            "required": "bool",
        },
    )
    d(
        "catalog",
        "product_combinations",
        {
            "product_id": "catalog.products",
            "component_variant_id": "catalog.product_variants",
            "quantity": "quantity",
        },
        checks=["quantity > 0"],
    )
    d(
        "catalog",
        "product_status_history",
        {
            "product_id": "catalog.products",
            "actor_id": "identity.users",
            "previous": "text",
            "current": "text",
        },
        immutable=True,
    )
    d(
        "catalog",
        "pharmacy_restrictions",
        {
            "product_id": "catalog.products",
            "prescription_required": "bool",
            "license_category": "text",
            "country_id": "geo.countries",
        },
    )
    d(
        "inventory",
        "inventory_locations",
        {"branch_id": "merchant.merchant_branches", "name": "text"},
        unique=[("branch_id", "name")],
    )
    d(
        "inventory",
        "inventory_items",
        {"location_id": "inventory.inventory_locations", "variant_id": "catalog.product_variants"},
        unique=[("location_id", "variant_id")],
    )
    d(
        "inventory",
        "reservation_expirations",
        {
            "reservation_id": "inventory.stock_reservations",
            "due_at": "timestamp",
            "processed_at": "timestamp?",
        },
        unique=[("reservation_id",)],
    )
    d(
        "inventory",
        "stock_adjustments",
        {
            "movement_id": "inventory.stock_movements",
            "reason": "text",
            "approved_by": "identity.users",
        },
        unique=[("movement_id",)],
        immutable=True,
    )
    d(
        "inventory",
        "stock_count_sessions",
        {
            "location_id": "inventory.inventory_locations",
            "started_by": "identity.users",
            "completed_at": "timestamp?",
            "status": "text",
        },
    )
    d(
        "inventory",
        "stock_count_lines",
        {
            "session_id": "inventory.stock_count_sessions",
            "variant_id": "catalog.product_variants",
            "counted": "quantity",
        },
        unique=[("session_id", "variant_id")],
        checks=["counted >= 0"],
    )
    d(
        "inventory",
        "stock_batches",
        {
            "stock_id": "inventory.stock_balances",
            "lot_code": "text",
            "quantity": "quantity",
            "reserved": "quantity",
            "received_at": "timestamp",
        },
        unique=[("stock_id", "lot_code")],
        checks=["quantity >= 0", "reserved BETWEEN 0 AND quantity"],
    )
    d(
        "inventory",
        "batch_reservation_allocations",
        {
            "reservation_id": "inventory.stock_reservations",
            "batch_id": "inventory.stock_batches",
            "quantity": "quantity",
            "status": "text",
        },
        unique=[("reservation_id", "batch_id")],
        checks=["quantity > 0"],
    )
    d(
        "inventory",
        "expiry_dates",
        {"batch_id": "inventory.stock_batches", "expires_on": "date"},
        unique=[("batch_id",)],
    )
    d(
        "inventory",
        "inventory_alerts",
        {"stock_id": "inventory.stock_balances", "kind": "text", "resolved_at": "timestamp?"},
    )
    d(
        "inventory",
        "inventory_policy_settings",
        {
            "branch_id": "merchant.merchant_branches",
            "allow_backorders": "bool",
            "reservation_ttl_seconds": "int",
        },
        unique=[("branch_id",)],
        checks=["reservation_ttl_seconds BETWEEN 60 AND 86400"],
    )
    d(
        "commerce",
        "cart_item_options",
        {
            "cart_item_id": "commerce.cart_items",
            "option_id": "catalog.option_values",
            "quantity": "int",
        },
        unique=[("cart_item_id", "option_id")],
        checks=["quantity > 0"],
    )
    d(
        "commerce",
        "checkout_sessions",
        {
            "cart_id": "commerce.carts",
            "user_id": "identity.users",
            "expires_at": "timestamp",
            "status": "text",
        },
    )
    d(
        "commerce",
        "checkout_quote_lines",
        {
            "quote_id": "commerce.checkout_quotes",
            "cart_item_id": "commerce.cart_items",
            "amount": "amount",
            "currency_id": "finance.currencies",
            "snapshot": "json",
        },
        immutable=True,
    )
    d(
        "commerce",
        "order_item_options",
        {
            "order_item_id": "commerce.order_items",
            "name_snapshot": "text",
            "amount": "amount",
            "quantity": "int",
        },
        checks=["quantity > 0"],
        immutable=True,
    )
    d(
        "commerce",
        "order_addresses",
        {
            "order_id": "commerce.orders",
            "fulfillment_unit_id": "fulfillment.fulfillment_units",
            "kind": "text",
            "snapshot": "json",
        },
        immutable=True,
    )
    for name, extra in {
        "order_amount_breakdowns": {
            "kind": "text",
            "amount": "amount",
            "funding_organization_id": "identity.organizations?",
        },
        "order_tax_lines": {
            "tax_code_id": "finance.tax_codes",
            "rate": "amount",
            "taxable_amount": "amount",
            "amount": "amount",
        },
        "order_discounts": {
            "campaign_id": "engagement.promotional_campaigns?",
            "amount": "amount",
            "funding_organization_id": "identity.organizations",
        },
        "order_adjustments": {"amount": "amount", "reason": "text", "actor_id": "identity.users"},
    }.items():
        d(
            "commerce",
            name,
            {"order_id": "commerce.orders", "currency_id": "finance.currencies", **extra},
            immutable=True,
        )
    d(
        "commerce",
        "order_timeline_events",
        {"order_id": "commerce.orders", "event_type": "text", "safe_payload": "json"},
        immutable=True,
    )
    d(
        "commerce",
        "cancellation_reasons",
        {"code": "text", "description": "text"},
        unique=[("code",)],
    )
    d(
        "commerce",
        "order_cancellations",
        {
            "order_id": "commerce.orders",
            "merchant_order_id": "commerce.merchant_orders?",
            "reason_id": "commerce.cancellation_reasons?",
            "actor_id": "identity.users",
            "refund_required": "bool",
        },
        immutable=True,
    )
    d(
        "commerce",
        "order_substitutions",
        {
            "order_item_id": "commerce.order_items",
            "replacement_variant_id": "catalog.product_variants",
            "approved_by": "identity.users",
            "price_difference": "amount",
            "status": "text",
        },
    )
    d(
        "commerce",
        "order_refund_requests",
        {
            "order_id": "commerce.orders",
            "requested_by": "identity.users",
            "amount": "amount",
            "reason": "text",
            "status": "text",
        },
    )
    d(
        "commerce",
        "group_order_members",
        {"cart_id": "commerce.carts", "user_id": "identity.users", "invited_by": "identity.users"},
        unique=[("cart_id", "user_id")],
    )
    d(
        "commerce",
        "corporate_order_references",
        {
            "order_id": "commerce.orders",
            "organization_id": "identity.organizations",
            "purchase_order_reference": "text",
        },
        unique=[("order_id",)],
    )
    d(
        "fulfillment",
        "delivery_slot_capacity",
        {
            "window_id": "fulfillment.delivery_windows",
            "category_id": "catalog.product_categories",
            "capacity": "int",
        },
        unique=[("window_id", "category_id")],
        checks=["capacity >= 0"],
    )
    d(
        "fulfillment",
        "scheduled_orders",
        {
            "order_id": "commerce.orders",
            "window_id": "fulfillment.delivery_windows",
            "revalidate_at": "timestamp",
            "status": "text",
        },
    )
    d(
        "fulfillment",
        "recurring_order_plans",
        {
            "user_id": "identity.users",
            "cart_template": "json",
            "timezone": "text",
            "payment_agreement_reference": "text?",
            "active": "bool",
            "status": "text",
        },
        checks=["status IN ('active','paused','cancelled')"],
    )
    d(
        "fulfillment",
        "recurring_order_rules",
        {
            "plan_id": "fulfillment.recurring_order_plans",
            "frequency": "text",
            "interval": "int",
            "local_time": "time",
            "start_date": "date",
            "end_date": "date?",
        },
        checks=["interval > 0"],
    )
    d(
        "fulfillment",
        "recurrence_exceptions",
        {"plan_id": "fulfillment.recurring_order_plans", "local_date": "date", "skip": "bool"},
        unique=[("plan_id", "local_date")],
    )
    d(
        "fulfillment",
        "scheduled_order_occurrences",
        {
            "plan_id": "fulfillment.recurring_order_plans",
            "scheduled_at": "timestamp",
            "order_id": "commerce.orders?",
            "status": "text",
            "revalidation_reason": "text?",
        },
        unique=[("plan_id", "scheduled_at")],
    )
    d(
        "engagement",
        "subscription_plans",
        {
            "name": "text",
            "currency_id": "finance.currencies",
            "amount": "amount",
            "billing_interval": "text",
        },
        checks=["amount >= 0"],
    )
    d(
        "engagement",
        "customer_subscriptions",
        {
            "user_id": "identity.users",
            "plan_id": "engagement.subscription_plans",
            "payment_agreement_reference": "text?",
            "starts_at": "timestamp",
            "ends_at": "timestamp?",
            "status": "text",
        },
    )
    d(
        "engagement",
        "subscription_billing_events",
        {
            "subscription_id": "engagement.customer_subscriptions",
            "period_start": "timestamp",
            "amount": "amount",
            "provider_reference": "text?",
            "status": "text",
        },
        unique=[("subscription_id", "period_start")],
        immutable=True,
    )
    d(
        "fulfillment",
        "scheduling_job_records",
        {
            "occurrence_id": "fulfillment.scheduled_order_occurrences",
            "attempts": "int",
            "available_at": "timestamp",
            "locked_until": "timestamp?",
            "completed_at": "timestamp?",
        },
        unique=[("occurrence_id",)],
    )
    for name, fields in {
        "pilot_documents": {
            "pilot_id": "fulfillment.pilot_profiles",
            "document_type": "text",
            "private_object_key": "text",
            "expires_at": "timestamp?",
        },
        "pilot_vehicles": {
            "pilot_id": "fulfillment.pilot_profiles",
            "vehicle_type": "text",
            "registration_token": "text",
        },
        "pilot_vehicle_assignments": {
            "pilot_id": "fulfillment.pilot_profiles",
            "vehicle_id": "fulfillment.pilot_vehicles",
            "starts_at": "timestamp",
            "ends_at": "timestamp?",
        },
        "pilot_availability": {
            "pilot_id": "fulfillment.pilot_profiles",
            "available": "bool",
            "changed_at": "timestamp",
        },
        "pilot_shifts": {
            "pilot_id": "fulfillment.pilot_profiles",
            "starts_at": "timestamp",
            "ends_at": "timestamp",
        },
        "pilot_service_zones": {
            "pilot_id": "fulfillment.pilot_profiles",
            "zone_id": "geo.service_zones",
        },
        "pilot_capabilities": {
            "pilot_id": "fulfillment.pilot_profiles",
            "capability": "text",
            "expires_at": "timestamp?",
        },
        "pilot_status_history": {
            "pilot_id": "fulfillment.pilot_profiles",
            "previous": "text",
            "current": "text",
            "actor_id": "identity.users",
        },
        "pilot_location_events": {
            "pilot_id": "fulfillment.pilot_profiles",
            "latitude": "coordinate",
            "longitude": "coordinate",
            "observed_at": "timestamp",
            "accuracy_m": "amount",
            "heading_degrees": "amount?",
            "speed_mps": "amount?",
            "client_sequence": "int",
            "battery_percent": "int?",
            "app_state": "text",
            "expires_at": "timestamp",
        },
        "pilot_location_consents": {
            "pilot_id": "fulfillment.pilot_profiles",
            "policy_version": "text",
            "accepted": "bool",
        },
        "tracking_ws_tickets": {
            "user_id": "identity.users",
            "token_hash": "text",
            "expires_at": "timestamp",
            "consumed_at": "timestamp?",
        },
        "dispatch_policies": {
            "city_id": "geo.cities",
            "version": "int",
            "weights": "json",
            "active": "bool",
        },
        "eta_estimates": {
            "task_id": "fulfillment.delivery_tasks",
            "generated_at": "timestamp",
            "pickup_at": "timestamp?",
            "delivery_at": "timestamp",
            "source": "text",
            "confidence": "text",
            "rule_version": "text",
            "reason": "text",
        },
        "delivery_task_items": {
            "task_id": "fulfillment.delivery_tasks",
            "order_item_id": "commerce.order_items",
            "quantity": "quantity",
        },
        "assignment_offers": {
            "assignment_id": "fulfillment.pilot_assignments",
            "expires_at": "timestamp",
        },
        "assignment_responses": {
            "assignment_id": "fulfillment.pilot_assignments",
            "response": "text",
            "responded_at": "timestamp",
        },
        "pickup_stops": {
            "task_id": "fulfillment.delivery_tasks",
            "branch_id": "merchant.merchant_branches",
            "position": "int",
        },
        "delivery_stops": {
            "task_id": "fulfillment.delivery_tasks",
            "address_snapshot": "json",
            "position": "int",
        },
        "delivery_routes": {"pilot_id": "fulfillment.pilot_profiles", "status": "text"},
        "route_stops": {
            "route_id": "fulfillment.delivery_routes",
            "task_id": "fulfillment.delivery_tasks",
            "position": "int",
            "kind": "text",
        },
        "route_optimization_runs": {
            "route_id": "fulfillment.delivery_routes",
            "strategy": "text",
            "input_hash": "text",
            "result": "json",
        },
        "pickup_confirmations": {
            "task_id": "fulfillment.delivery_tasks",
            "pilot_id": "fulfillment.pilot_profiles",
            "confirmed_at": "timestamp",
        },
        "delivery_confirmations": {
            "task_id": "fulfillment.delivery_tasks",
            "pilot_id": "fulfillment.pilot_profiles",
            "confirmed_at": "timestamp",
            "mode": "text",
        },
        "proof_of_delivery": {
            "task_id": "fulfillment.delivery_tasks",
            "mode": "text",
            "private_object_key": "text?",
            "acknowledged_by": "identity.users?",
            "expires_at": "timestamp",
        },
        "delivery_attempts": {
            "task_id": "fulfillment.delivery_tasks",
            "pilot_id": "fulfillment.pilot_profiles",
            "outcome": "text",
            "reason_id": "fulfillment.failed_delivery_reasons?",
        },
        "failed_delivery_reasons": {"code": "text", "description": "text"},
        "dispatch_events": {
            "task_id": "fulfillment.delivery_tasks",
            "event_type": "text",
            "actor_id": "identity.users",
            "strategy": "text",
        },
        "pilot_incentives": {
            "pilot_id": "fulfillment.pilot_profiles",
            "currency_id": "finance.currencies",
            "amount": "amount",
            "policy_reference": "text",
        },
        "pilot_earnings": {
            "pilot_id": "fulfillment.pilot_profiles",
            "task_id": "fulfillment.delivery_tasks",
            "currency_id": "finance.currencies",
            "amount": "amount",
        },
        "pilot_settlement_references": {
            "pilot_id": "fulfillment.pilot_profiles",
            "settlement_line_id": "finance.settlement_lines",
        },
    }.items():
        d(
            "fulfillment",
            name,
            fields,
            unique=(
                [("token_hash",)]
                if name == "tracking_ws_tickets"
                else [("city_id", "version")]
                if name == "dispatch_policies"
                else []
            ),
            checks=["latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180"]
            if name == "pilot_location_events"
            else [],
            immutable=name
            in {
                "pilot_status_history",
                "pilot_location_consents",
                "pickup_confirmations",
                "delivery_confirmations",
                "dispatch_events",
                "pilot_earnings",
            },
        )
    for name, fields in {
        "tax_codes": {"country_id": "geo.countries", "code": "text", "description": "text"},
        "tax_rules": {
            "tax_code_id": "finance.tax_codes",
            "city_id": "geo.cities?",
            "rate": "amount",
            "starts_at": "timestamp",
            "ends_at": "timestamp?",
        },
        "payment_providers": {"code": "text", "enabled": "bool", "sandbox_only": "bool"},
        "payment_attempts": {
            "payment_id": "finance.payment_intents",
            "idempotency_key": "text",
            "status": "text",
            "provider_reference": "text?",
        },
        "payment_authorizations": {
            "payment_id": "finance.payment_intents",
            "amount": "amount",
            "provider_reference": "text",
            "expires_at": "timestamp",
        },
        "payment_captures": {
            "payment_id": "finance.payment_intents",
            "amount": "amount",
            "provider_reference": "text",
        },
        "refund_allocations": {
            "refund_id": "finance.payment_refunds",
            "merchant_order_id": "commerce.merchant_orders",
            "amount": "amount",
        },
        "payment_reconciliations": {
            "payment_id": "finance.payment_intents",
            "provider_reference": "text",
            "amount": "amount",
            "status": "text",
        },
        "merchant_payables": {
            "organization_id": "identity.organizations",
            "merchant_order_id": "commerce.merchant_orders",
            "currency_id": "finance.currencies",
            "amount": "amount",
            "status": "text",
        },
        "pilot_payables": {
            "pilot_id": "fulfillment.pilot_profiles",
            "task_id": "fulfillment.delivery_tasks",
            "currency_id": "finance.currencies",
            "amount": "amount",
            "status": "text",
        },
        "settlement_batches": {
            "organization_id": "identity.organizations",
            "currency_id": "finance.currencies",
            "period_start": "timestamp",
            "period_end": "timestamp",
            "status": "text",
        },
        "settlement_lines": {
            "batch_id": "finance.settlement_batches",
            "journal_id": "finance.journal_entries",
            "amount": "amount",
            "payee_reference": "text",
        },
        "payout_requests": {
            "batch_id": "finance.settlement_batches",
            "idempotency_key": "text",
            "amount": "amount",
            "status": "text",
        },
        "payout_attempts": {
            "request_id": "finance.payout_requests",
            "provider_reference": "text",
            "status": "text",
        },
        "payout_bank_references": {
            "request_id": "finance.payout_requests",
            "provider_bank_token": "text",
            "display_last_four": "text",
        },
        "commission_rules": {
            "organization_id": "identity.organizations",
            "category_id": "catalog.product_categories?",
            "rate": "amount",
            "starts_at": "timestamp",
        },
        "fee_rules": {
            "city_id": "geo.cities",
            "currency_id": "finance.currencies",
            "name": "text",
            "amount": "amount",
            "starts_at": "timestamp",
        },
        "billing_documents": {
            "organization_id": "identity.organizations",
            "private_object_key": "text",
            "document_type": "text",
        },
        "invoices": {
            "organization_id": "identity.organizations",
            "order_id": "commerce.orders?",
            "currency_id": "finance.currencies",
            "invoice_number": "text",
            "total": "amount",
            "issued_at": "timestamp",
        },
        "invoice_lines": {
            "invoice_id": "finance.invoices",
            "description": "text",
            "quantity": "quantity",
            "unit_price": "amount",
            "total": "amount",
        },
        "credit_notes": {
            "invoice_id": "finance.invoices",
            "refund_id": "finance.payment_refunds?",
            "amount": "amount",
            "reason": "text",
        },
        "ledger_posting_batches": {
            "organization_id": "identity.organizations",
            "idempotency_key": "text",
            "posted_at": "timestamp",
        },
        "ledger_reconciliation_results": {
            "organization_id": "identity.organizations",
            "currency_id": "finance.currencies",
            "period_end": "timestamp",
            "debit_total": "amount",
            "credit_total": "amount",
            "status": "text",
        },
    }.items():
        uniques = []
        if name == "payment_attempts":
            uniques = [("payment_id", "idempotency_key")]
        if name == "payout_requests":
            uniques = [("idempotency_key",)]
        if name == "payment_captures":
            uniques = [("provider_reference",)]
        if name == "ledger_posting_batches":
            uniques = [("organization_id", "idempotency_key")]
        d(
            "finance",
            name,
            fields,
            unique=uniques,
            immutable=name
            in {
                "payment_captures",
                "refund_allocations",
                "settlement_lines",
                "invoice_lines",
                "credit_notes",
                "ledger_posting_batches",
            },
        )
    for name, fields in {
        "promotional_campaigns": {
            "organization_id": "identity.organizations",
            "name": "text",
            "starts_at": "timestamp",
            "ends_at": "timestamp",
            "funding_party_id": "identity.organizations",
        },
        "coupons": {
            "campaign_id": "engagement.promotional_campaigns",
            "code": "text",
            "total_limit": "int",
            "per_user_limit": "int",
            "per_merchant_limit": "int",
            "redeemed": "int",
            "stackable": "bool",
        },
        "coupon_eligibility_rules": {
            "coupon_id": "engagement.coupons",
            "category_id": "catalog.product_categories?",
            "minimum_amount": "amount",
        },
        "coupon_redemptions": {
            "coupon_id": "engagement.coupons",
            "user_id": "identity.users",
            "order_id": "commerce.orders",
            "branch_id": "merchant.merchant_branches",
            "amount": "amount",
        },
        "merchant_promotions": {
            "campaign_id": "engagement.promotional_campaigns",
            "branch_id": "merchant.merchant_branches",
        },
        "loyalty_accounts": {"user_id": "identity.users", "program_code": "text", "points": "int"},
        "loyalty_transactions": {
            "account_id": "engagement.loyalty_accounts",
            "order_id": "commerce.orders?",
            "points": "int",
            "idempotency_key": "text",
        },
        "referral_programs": {"name": "text", "active": "bool", "reward_points": "int"},
        "referrals": {
            "program_id": "engagement.referral_programs",
            "referrer_id": "identity.users",
            "referred_user_id": "identity.users",
            "status": "text",
        },
        "customer_favorites": {
            "user_id": "identity.users",
            "branch_id": "merchant.merchant_branches",
            "product_id": "catalog.products?",
        },
        "customer_preferences": {
            "user_id": "identity.users",
            "preference_key": "text",
            "value": "json",
        },
        "reviews": {
            "user_id": "identity.users",
            "order_item_id": "commerce.order_items",
            "rating": "int",
            "body": "text",
            "moderation_status": "text",
        },
        "review_media": {"review_id": "engagement.reviews", "private_object_key": "text"},
        "review_moderation": {
            "review_id": "engagement.reviews",
            "reviewer_id": "identity.users",
            "decision": "text",
        },
        "notification_preferences": {
            "user_id": "identity.users",
            "channel": "text",
            "enabled": "bool",
        },
        "device_push_tokens": {
            "device_id": "identity.user_devices",
            "encrypted_token_reference": "text",
        },
        "communication_templates": {
            "template_key": "text",
            "locale": "text",
            "channel": "text",
            "body": "text",
            "version": "int",
        },
    }.items():
        uniques = {
            "coupons": [("code",)],
            "coupon_redemptions": [("coupon_id", "order_id", "branch_id")],
            "customer_preferences": [("user_id", "preference_key")],
            "loyalty_transactions": [("idempotency_key",)],
            "reviews": [("user_id", "order_item_id")],
        }.get(name, [])
        checks = {
            "reviews": ["rating BETWEEN 1 AND 5"],
            "coupons": [
                "total_limit > 0 AND per_user_limit > 0 AND per_merchant_limit > 0 "
                "AND redeemed BETWEEN 0 AND total_limit"
            ],
        }.get(name, [])
        d(
            "engagement",
            name,
            fields,
            unique=uniques,
            checks=checks,
            immutable=name in {"coupon_redemptions", "loyalty_transactions", "review_moderation"},
        )
    for name, fields in {
        "support_categories": {"name": "text", "requires_finance_approval": "bool"},
        "ticket_assignments": {
            "ticket_id": "operations.support_tickets",
            "agent_id": "identity.users",
            "assigned_at": "timestamp",
        },
        "support_escalations": {
            "ticket_id": "operations.support_tickets",
            "raised_by": "identity.users",
            "reason": "text",
            "resolved_at": "timestamp?",
        },
        "refund_approval_requests": {
            "order_id": "commerce.orders",
            "requested_by": "identity.users",
            "organization_id": "identity.organizations",
            "amount": "amount",
            "status": "text",
        },
        "refund_approval_decisions": {
            "request_id": "operations.refund_approval_requests",
            "decided_by": "identity.users",
            "decision": "text",
            "reason": "text",
        },
        "operational_incidents": {
            "city_id": "geo.cities",
            "pilot_id": "fulfillment.pilot_profiles?",
            "delivery_task_id": "fulfillment.delivery_tasks?",
            "reporter_id": "identity.users?",
            "category": "text?",
            "severity": "text",
            "summary": "text",
            "resolution_summary": "text?",
            "status": "text",
            "safety_emergency": "bool",
        },
        "notification_jobs": {
            "user_id": "identity.users",
            "template_id": "engagement.communication_templates?",
            "event_id": "integration.outbox_events?",
            "channel": "text",
            "status": "text",
            "available_at": "timestamp",
        },
        "notification_deliveries": {
            "job_id": "operations.notification_jobs",
            "provider_reference": "text",
            "delivered_at": "timestamp",
        },
        "notification_attempts": {
            "job_id": "operations.notification_jobs",
            "attempt": "int",
            "result_code": "text",
        },
        "service_health_events": {"service": "text", "status": "text", "occurred_at": "timestamp"},
    }.items():
        d(
            "operations",
            name,
            fields,
            immutable=name
            in {
                "refund_approval_decisions",
                "notification_deliveries",
                "notification_attempts",
                "service_health_events",
            },
        )
    for name in ["admin_action_logs", "access_audit_events", "security_events"]:
        d(
            "audit",
            name,
            {
                "actor_id": "identity.users?",
                "organization_id": "identity.organizations?",
                "action": "text",
                "resource_id": "uuid?",
                "correlation_id": "text",
                "redacted_details": "json",
            },
            immutable=True,
        )
    for name, fields in {
        "ai_model_registry": {"name": "text", "purpose": "text", "provider": "text"},
        "ai_model_versions": {
            "model_id": "intelligence.ai_model_registry",
            "version": "text",
            "artifact_reference": "text",
            "approved_by": "identity.users?",
            "algorithm": "text",
            "training_code_version": "text",
            "dataset_reference": "text?",
            "feature_schema_version": "text",
            "trained_at": "timestamp?",
            "metrics": "json",
            "artifact_checksum": "text?",
            "validation_passed": "bool",
            "status": "text",
        },
        "ai_inference_runs": {
            "version_id": "intelligence.ai_model_versions",
            "actor_id": "identity.users",
            "organization_id": "identity.organizations?",
            "input_digest": "text",
            "status": "text",
            "retention_until": "timestamp",
        },
        "ai_prediction_records": {
            "run_id": "intelligence.ai_inference_runs",
            "prediction_type": "text",
            "output": "json",
            "expires_at": "timestamp",
        },
        "ai_feature_definitions": {"name": "text", "value_type": "text", "privacy_class": "text"},
        "ai_feature_snapshots": {
            "feature_id": "intelligence.ai_feature_definitions",
            "subject_digest": "text",
            "value": "json",
            "observed_at": "timestamp",
            "expires_at": "timestamp",
        },
        "ai_feedback": {
            "run_id": "intelligence.ai_inference_runs",
            "user_id": "identity.users",
            "rating": "int",
            "safe_comment": "text?",
        },
        "ai_evaluation_runs": {
            "version_id": "intelligence.ai_model_versions",
            "dataset_reference": "text",
            "metrics": "json",
            "status": "text",
        },
        "ai_agent_sessions": {
            "user_id": "identity.users",
            "organization_id": "identity.organizations?",
            "purpose": "text",
            "expires_at": "timestamp",
        },
        "ai_agent_tool_calls": {
            "session_id": "intelligence.ai_agent_sessions",
            "tool_name": "text",
            "argument_digest": "text",
            "policy_decision": "text",
            "result_digest": "text?",
        },
        "ai_agent_action_approvals": {
            "tool_call_id": "intelligence.ai_agent_tool_calls",
            "approver_id": "identity.users",
            "decision": "text",
        },
        "ai_risk_signals": {
            "run_id": "intelligence.ai_inference_runs",
            "subject_digest": "text",
            "kind": "text",
            "score": "amount",
            "review_status": "text",
        },
    }.items():
        d(
            "intelligence",
            name,
            fields,
            immutable=name in {"ai_agent_tool_calls", "ai_agent_action_approvals"},
        )
    d(
        "intelligence",
        "ai_training_jobs",
        {
            "model_id": "intelligence.ai_model_registry",
            "status": "text",
            "dataset_reference": "text",
            "sample_count": "int",
            "code_version": "text",
            "feature_schema_version": "text",
            "metrics": "json",
            "started_at": "timestamp?",
            "finished_at": "timestamp?",
            "error_code": "text?",
        },
        checks=[
            "sample_count >= 0",
            "status IN ('queued','running','succeeded','failed','cancelled')",
            "(started_at IS NULL) = (status = 'queued')",
        ],
    )
    d(
        "intelligence",
        "ai_feature_pipeline_runs",
        {
            "feature_schema_version": "text",
            "source_cutoff": "timestamp",
            "row_count": "int",
            "quality": "json",
            "status": "text",
        },
        checks=["row_count >= 0", "status IN ('succeeded','failed','partial')"],
    )
    d(
        "intelligence",
        "ai_forecast_outputs",
        {
            "city_id": "geo.cities",
            "zone_id": "geo.service_zones?",
            "interval_minutes": "int",
            "forecast": "json",
            "provenance": "text",
            "feature_schema_version": "text",
            "source_cutoff": "timestamp",
            "expires_at": "timestamp",
        },
        checks=["interval_minutes > 0"],
    )
    d(
        "intelligence",
        "ai_optimization_decisions",
        {
            "city_id": "geo.cities",
            "mode": "text",
            "policy_version": "text",
            "objective_score": "amount",
            "plan": "json",
            "constraint_checks": "json",
            "runtime_ms": "int",
            "fallback_reason": "text?",
        },
        checks=["runtime_ms >= 0"],
    )
    for name, fields in {
        "integration_connections": {
            "organization_id": "identity.organizations",
            "provider": "text",
            "status": "text",
        },
        "integration_credentials_references": {
            "connection_id": "integration.integration_connections",
            "secret_manager_reference": "text",
            "rotated_at": "timestamp",
        },
        "integration_webhook_subscriptions": {
            "connection_id": "integration.integration_connections",
            "event_type": "text",
            "endpoint_reference": "text",
            "active": "bool",
        },
        "webhook_delivery_attempts": {
            "subscription_id": "integration.integration_webhook_subscriptions",
            "outbox_event_id": "integration.outbox_events",
            "attempt": "int",
            "response_code": "int?",
        },
        "integration_sync_jobs": {
            "connection_id": "integration.integration_connections",
            "status": "text",
            "available_at": "timestamp",
            "attempts": "int",
        },
        "integration_sync_checkpoints": {
            "connection_id": "integration.integration_connections",
            "stream": "text",
            "cursor": "text",
        },
        "integration_errors": {
            "connection_id": "integration.integration_connections",
            "error_code": "text",
            "safe_message": "text",
            "retry_at": "timestamp?",
        },
    }.items():
        d(
            "integration",
            name,
            fields,
            unique=[("connection_id", "stream")] if name == "integration_sync_checkpoints" else [],
        )


register()

# High-volume query/retention indexes; current-location reads use the separate unique
# pilot_latest_location row and never scan the history stream.
Index(
    "ix_pilot_history_subject_time",
    FOUNDATION_MODELS["fulfillment.pilot_location_events"].__table__.c.pilot_id,
    FOUNDATION_MODELS["fulfillment.pilot_location_events"].__table__.c.observed_at,
    FOUNDATION_MODELS["fulfillment.pilot_location_events"].__table__.c.id,
)
for table_name, index_name in [
    ("fulfillment.pilot_location_events", "ix_pilot_history_retention"),
    ("fulfillment.proof_of_delivery", "ix_delivery_proof_retention"),
]:
    table = FOUNDATION_MODELS[table_name].__table__
    Index(index_name, table.c.expires_at, table.c.id)
