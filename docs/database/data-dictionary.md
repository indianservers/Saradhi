# Data dictionary

Generated from SQLAlchemy metadata. Frozen migration is independently versioned.
All FK delete actions are RESTRICT; no accounting cascades. UUIDv4 IDs, UTC timestamps.

## catalog.product_categories

- `name`: TEXT; required.
- `regulated`: BOOLEAN; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_product_categories", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_categories_name", "type": "UniqueConstraint", "sql": null, "columns": ["name"]}].
Indexes: [].

## commerce.cancellation_reasons

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `code`: TEXT; required.
- `description`: TEXT; required.

Constraints: [{"name": "pk_cancellation_reasons", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_cancellation_reasons_code", "type": "UniqueConstraint", "sql": null, "columns": ["code"]}].
Indexes: [].

## engagement.communication_templates

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `template_key`: TEXT; required.
- `locale`: TEXT; required.
- `channel`: TEXT; required.
- `body`: TEXT; required.
- `version`: INTEGER; required.

Constraints: [{"name": "pk_communication_templates", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## engagement.referral_programs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `name`: TEXT; required.
- `active`: BOOLEAN; required.
- `reward_points`: INTEGER; required.

Constraints: [{"name": "pk_referral_programs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## finance.currencies

- `code`: VARCHAR(3); required.
- `scale`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_currencies_currency_scale", "type": "CheckConstraint", "sql": "scale BETWEEN 0 AND 4", "columns": []}, {"name": "pk_currencies", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_currencies_code", "type": "UniqueConstraint", "sql": null, "columns": ["code"]}].
Indexes: [].

## finance.payment_providers

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `code`: TEXT; required.
- `enabled`: BOOLEAN; required.
- `sandbox_only`: BOOLEAN; required.

Constraints: [{"name": "pk_payment_providers", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## fulfillment.failed_delivery_reasons

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `code`: TEXT; required.
- `description`: TEXT; required.

Constraints: [{"name": "pk_failed_delivery_reasons", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## geo.countries

- `code`: VARCHAR(2); required.
- `name`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_countries", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_countries_code", "type": "UniqueConstraint", "sql": null, "columns": ["code"]}].
Indexes: [].

## identity.auth_rate_buckets

- `bucket_key`: TEXT; required.
- `window_start`: TIMESTAMP WITH TIME ZONE; required.
- `attempts`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_auth_rate_buckets", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_auth_rate_buckets_bucket_key", "type": "UniqueConstraint", "sql": null, "columns": ["bucket_key", "window_start"]}].
Indexes: [{"name": "ix_auth_rate_buckets_window_start", "columns": ["window_start"], "unique": false, "predicate": "None"}].

## identity.login_attempts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `identity_digest`: TEXT; required.
- `network_digest`: TEXT; required.
- `succeeded`: BOOLEAN; required.
- `occurred_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "pk_login_attempts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## identity.permissions

- `code`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_permissions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_permissions_code", "type": "UniqueConstraint", "sql": null, "columns": ["code"]}].
Indexes: [].

## identity.roles

- `name`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_roles", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_roles_name", "type": "UniqueConstraint", "sql": null, "columns": ["name"]}].
Indexes: [].

## identity.users

- `status`: TEXT; required; default active.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_users", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## integration.inbox_processed_messages

- `consumer`: TEXT; required.
- `event_id`: UUID; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_inbox_processed_messages", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_inbox_processed_messages_consumer", "type": "UniqueConstraint", "sql": null, "columns": ["consumer", "event_id"]}].
Indexes: [].

## integration.outbox_events

- `event_type`: TEXT; required.
- `payload_version`: INTEGER; required.
- `aggregate_id`: UUID; required.
- `payload`: JSONB; required.
- `correlation_id`: TEXT; required.
- `attempts`: INTEGER; required.
- `available_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `delivered_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `dead_lettered_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "pk_outbox_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_outbox_pending", "columns": ["available_at"], "unique": false, "predicate": "delivered_at IS NULL AND dead_lettered_at IS NULL"}].

## intelligence.ai_feature_definitions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `name`: TEXT; required.
- `value_type`: TEXT; required.
- `privacy_class`: TEXT; required.

Constraints: [{"name": "pk_ai_feature_definitions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## intelligence.ai_model_registry

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `name`: TEXT; required.
- `purpose`: TEXT; required.
- `provider`: TEXT; required.

Constraints: [{"name": "pk_ai_model_registry", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## merchant.merchant_categories

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `name`: TEXT; required.

Constraints: [{"name": "pk_merchant_categories", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_categories_name", "type": "UniqueConstraint", "sql": null, "columns": ["name"]}].
Indexes: [].

## operations.service_health_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `service`: TEXT; required.
- `status`: TEXT; required.
- `occurred_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "pk_service_health_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## operations.support_categories

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `name`: TEXT; required.
- `requires_finance_approval`: BOOLEAN; required.

Constraints: [{"name": "pk_support_categories", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [].

## catalog.category_attributes

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `category_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).
- `name`: TEXT; required.
- `value_type`: TEXT; required.
- `required`: BOOLEAN; required.

Constraints: [{"name": "fk_category_attributes_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "pk_category_attributes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_category_attributes_category_id", "type": "UniqueConstraint", "sql": null, "columns": ["category_id", "name"]}].
Indexes: [{"name": "ix_category_attributes_category_id", "columns": ["category_id"], "unique": false, "predicate": "None"}].

## catalog.category_hierarchy

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `parent_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).
- `child_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).

Constraints: [{"name": "ck_category_hierarchy_rule_0", "type": "CheckConstraint", "sql": "parent_id <> child_id", "columns": []}, {"name": "fk_category_hierarchy_child_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["child_id"]}, {"name": "fk_category_hierarchy_parent_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["parent_id"]}, {"name": "pk_category_hierarchy", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_category_hierarchy_parent_id", "type": "UniqueConstraint", "sql": null, "columns": ["parent_id", "child_id"]}].
Indexes: [{"name": "ix_category_hierarchy_child_id", "columns": ["child_id"], "unique": false, "predicate": "None"}, {"name": "ix_category_hierarchy_parent_id", "columns": ["parent_id"], "unique": false, "predicate": "None"}].

## commerce.carts

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `status`: TEXT; required.
- `version`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_carts_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_carts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_carts_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.customer_preferences

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `preference_key`: TEXT; required.
- `value`: JSONB; required.

Constraints: [{"name": "fk_customer_preferences_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_customer_preferences", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_customer_preferences_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id", "preference_key"]}].
Indexes: [{"name": "ix_customer_preferences_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.loyalty_accounts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `program_code`: TEXT; required.
- `points`: INTEGER; required.

Constraints: [{"name": "fk_loyalty_accounts_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_loyalty_accounts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_loyalty_accounts_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.notification_preferences

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `channel`: TEXT; required.
- `enabled`: BOOLEAN; required.

Constraints: [{"name": "fk_notification_preferences_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_notification_preferences", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_notification_preferences_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.referrals

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `program_id`: UUID; required; FK → engagement.referral_programs.id (RESTRICT).
- `referrer_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `referred_user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `status`: TEXT; required.

Constraints: [{"name": "fk_referrals_program_id_referral_programs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["program_id"]}, {"name": "fk_referrals_referred_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["referred_user_id"]}, {"name": "fk_referrals_referrer_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["referrer_id"]}, {"name": "pk_referrals", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_referrals_program_id", "columns": ["program_id"], "unique": false, "predicate": "None"}, {"name": "ix_referrals_referred_user_id", "columns": ["referred_user_id"], "unique": false, "predicate": "None"}, {"name": "ix_referrals_referrer_id", "columns": ["referrer_id"], "unique": false, "predicate": "None"}].

## engagement.subscription_plans

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `name`: TEXT; required.
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `billing_interval`: TEXT; required.

Constraints: [{"name": "ck_subscription_plans_rule_0", "type": "CheckConstraint", "sql": "amount >= 0", "columns": []}, {"name": "fk_subscription_plans_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "pk_subscription_plans", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_subscription_plans_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}].

## finance.tax_codes

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).
- `code`: TEXT; required.
- `description`: TEXT; required.

Constraints: [{"name": "fk_tax_codes_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "pk_tax_codes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_tax_codes_country_id", "columns": ["country_id"], "unique": false, "predicate": "None"}].

## fulfillment.recurring_order_plans

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `cart_template`: JSONB; required.
- `timezone`: TEXT; required.
- `payment_agreement_reference`: TEXT; nullable.
- `active`: BOOLEAN; required.

Constraints: [{"name": "fk_recurring_order_plans_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_recurring_order_plans", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_recurring_order_plans_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## geo.cities

- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).
- `name`: TEXT; required.
- `timezone`: TEXT; required.
- `active`: BOOLEAN; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_cities_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "pk_cities", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_cities_country_id", "type": "UniqueConstraint", "sql": null, "columns": ["country_id", "name"]}].
Indexes: [].

## geo.service_regions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).
- `name`: TEXT; required.
- `timezone`: TEXT; required.

Constraints: [{"name": "fk_service_regions_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "pk_service_regions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_service_regions_country_id", "columns": ["country_id"], "unique": false, "predicate": "None"}].

## geo.states_provinces

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).
- `name`: TEXT; required.
- `code`: TEXT; required.

Constraints: [{"name": "fk_states_provinces_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "pk_states_provinces", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_states_provinces_country_id", "type": "UniqueConstraint", "sql": null, "columns": ["country_id", "code"]}].
Indexes: [{"name": "ix_states_provinces_country_id", "columns": ["country_id"], "unique": false, "predicate": "None"}].

## identity.customer_profiles

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `preferred_currency`: TEXT; required.

Constraints: [{"name": "fk_customer_profiles_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_customer_profiles", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_customer_profiles_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id"]}].
Indexes: [{"name": "ix_customer_profiles_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.external_identities

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `issuer`: TEXT; required.
- `subject`: TEXT; required.

Constraints: [{"name": "fk_external_identities_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_external_identities", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_external_identities_issuer", "type": "UniqueConstraint", "sql": null, "columns": ["issuer", "subject"]}].
Indexes: [{"name": "ix_external_identities_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.organizations

- `name`: TEXT; required.
- `owner_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_organizations_owner_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["owner_id"]}, {"name": "pk_organizations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_organizations_owner_id", "columns": ["owner_id"], "unique": false, "predicate": "None"}].

## identity.role_permissions

- `role_id`: UUID; required; FK → identity.roles.id (RESTRICT).
- `permission_id`: UUID; required; FK → identity.permissions.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_role_permissions_permission_id_permissions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["permission_id"]}, {"name": "fk_role_permissions_role_id_roles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["role_id"]}, {"name": "pk_role_permissions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_role_permissions_role_id", "type": "UniqueConstraint", "sql": null, "columns": ["role_id", "permission_id"]}].
Indexes: [{"name": "ix_role_permissions_role_id", "columns": ["role_id"], "unique": false, "predicate": "None"}].

## identity.sessions

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `revoked_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_sessions_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_sessions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_sessions_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.user_credentials

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `password_hash`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_user_credentials_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_user_credentials", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_user_credentials_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id"]}].
Indexes: [].

## identity.user_devices

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `platform`: TEXT; required.
- `device_key_hash`: TEXT; required.
- `last_seen_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_user_devices_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_user_devices", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_user_devices_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id", "device_key_hash"]}].
Indexes: [{"name": "ix_user_devices_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.user_email_addresses

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `address`: TEXT; required.
- `verified_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_user_email_addresses_normalized_email", "type": "CheckConstraint", "sql": "address = lower(address)", "columns": []}, {"name": "fk_user_email_addresses_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_user_email_addresses", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_user_email_addresses_address", "type": "UniqueConstraint", "sql": null, "columns": ["address"]}].
Indexes: [{"name": "ix_user_email_addresses_user_id", "columns": ["user_id"], "unique": true, "predicate": "None"}].

## identity.user_phone_numbers

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `e164`: TEXT; required.
- `verified_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_user_phone_numbers_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_user_phone_numbers", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_user_phone_numbers_e164", "type": "UniqueConstraint", "sql": null, "columns": ["e164"]}].
Indexes: [{"name": "ix_user_phone_numbers_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.user_profiles

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `display_name`: TEXT; required.
- `locale`: TEXT; required.

Constraints: [{"name": "fk_user_profiles_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_user_profiles", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_user_profiles_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id"]}].
Indexes: [{"name": "ix_user_profiles_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.verification_challenges

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `purpose`: TEXT; required.
- `digest`: TEXT; required.
- `attempts`: INTEGER; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `consumed_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `destination_reference`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_verification_challenges_attempt_bound", "type": "CheckConstraint", "sql": "attempts BETWEEN 0 AND 5", "columns": []}, {"name": "fk_verification_challenges_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_verification_challenges", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_verification_challenges_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_feature_snapshots

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `feature_id`: UUID; required; FK → intelligence.ai_feature_definitions.id (RESTRICT).
- `subject_digest`: TEXT; required.
- `value`: JSONB; required.
- `observed_at`: TIMESTAMP WITH TIME ZONE; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_ai_feature_snapshots_feature_id_ai_feature_definitions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["feature_id"]}, {"name": "pk_ai_feature_snapshots", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_feature_snapshots_feature_id", "columns": ["feature_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_model_versions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `model_id`: UUID; required; FK → intelligence.ai_model_registry.id (RESTRICT).
- `version`: TEXT; required.
- `artifact_reference`: TEXT; required.
- `approved_by`: UUID; nullable; FK → identity.users.id (RESTRICT).

Constraints: [{"name": "fk_ai_model_versions_approved_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["approved_by"]}, {"name": "fk_ai_model_versions_model_id_ai_model_registry", "type": "ForeignKeyConstraint", "sql": null, "columns": ["model_id"]}, {"name": "pk_ai_model_versions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_model_versions_approved_by", "columns": ["approved_by"], "unique": false, "predicate": "None"}, {"name": "ix_ai_model_versions_model_id", "columns": ["model_id"], "unique": false, "predicate": "None"}].

## operations.notification_jobs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `template_id`: UUID; nullable; FK → engagement.communication_templates.id (RESTRICT).
- `event_id`: UUID; nullable; FK → integration.outbox_events.id (RESTRICT).
- `channel`: TEXT; required.
- `status`: TEXT; required.
- `available_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_notification_jobs_event_id_outbox_events", "type": "ForeignKeyConstraint", "sql": null, "columns": ["event_id"]}, {"name": "fk_notification_jobs_template_id_communication_templates", "type": "ForeignKeyConstraint", "sql": null, "columns": ["template_id"]}, {"name": "fk_notification_jobs_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_notification_jobs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_notification_jobs_event_id", "columns": ["event_id"], "unique": false, "predicate": "None"}, {"name": "ix_notification_jobs_template_id", "columns": ["template_id"], "unique": false, "predicate": "None"}, {"name": "ix_notification_jobs_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## audit.access_audit_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `actor_id`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `action`: TEXT; required.
- `resource_id`: UUID; nullable.
- `correlation_id`: TEXT; required.
- `redacted_details`: JSONB; required.

Constraints: [{"name": "fk_access_audit_events_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_access_audit_events_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_access_audit_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_access_audit_events_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_access_audit_events_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## audit.admin_action_logs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `actor_id`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `action`: TEXT; required.
- `resource_id`: UUID; nullable.
- `correlation_id`: TEXT; required.
- `redacted_details`: JSONB; required.

Constraints: [{"name": "fk_admin_action_logs_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_admin_action_logs_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_admin_action_logs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_admin_action_logs_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_admin_action_logs_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## audit.audit_events

- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `actor_id`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `action`: TEXT; required.
- `resource_id`: UUID; required.
- `correlation_id`: TEXT; required.
- `safe_changes`: JSONB; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_audit_events_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_audit_events_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_audit_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_audit_scope_time", "columns": ["organization_id", "created_at", "id"], "unique": false, "predicate": "None"}].

## audit.security_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `actor_id`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `action`: TEXT; required.
- `resource_id`: UUID; nullable.
- `correlation_id`: TEXT; required.
- `redacted_details`: JSONB; required.

Constraints: [{"name": "fk_security_events_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_security_events_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_security_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_security_events_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_security_events_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## catalog.option_groups

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `name`: TEXT; required.
- `minimum_selections`: INTEGER; required.
- `maximum_selections`: INTEGER; required.

Constraints: [{"name": "ck_option_groups_rule_0", "type": "CheckConstraint", "sql": "minimum_selections >= 0 AND maximum_selections >= minimum_selections", "columns": []}, {"name": "fk_option_groups_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_option_groups", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_option_groups_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## catalog.price_books

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `name`: TEXT; required.
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_price_books_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_price_books_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_price_books", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_price_books_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_price_books_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## catalog.products

- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `category_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).
- `name`: TEXT; required.
- `unit`: TEXT; required.
- `variable_weight`: BOOLEAN; required.
- `active`: BOOLEAN; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_products_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "fk_products_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_products", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_products_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id"]}].
Indexes: [{"name": "ix_products_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## commerce.checkout_quotes

- `cart_id`: UUID; required; FK → commerce.carts.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `cart_version`: INTEGER; required.
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT).
- `total`: NUMERIC(20, 4); required.
- `snapshot`: JSONB; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `consumed_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_checkout_quotes_cart_id_carts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["cart_id"]}, {"name": "fk_checkout_quotes_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_checkout_quotes_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_checkout_quotes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_checkout_quotes_cart_id", "columns": ["cart_id"], "unique": false, "predicate": "None"}].

## commerce.checkout_sessions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `cart_id`: UUID; required; FK → commerce.carts.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_checkout_sessions_cart_id_carts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["cart_id"]}, {"name": "fk_checkout_sessions_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_checkout_sessions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_checkout_sessions_cart_id", "columns": ["cart_id"], "unique": false, "predicate": "None"}, {"name": "ix_checkout_sessions_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## commerce.group_order_members

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `cart_id`: UUID; required; FK → commerce.carts.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `invited_by`: UUID; required; FK → identity.users.id (RESTRICT).

Constraints: [{"name": "fk_group_order_members_cart_id_carts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["cart_id"]}, {"name": "fk_group_order_members_invited_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["invited_by"]}, {"name": "fk_group_order_members_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_group_order_members", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_group_order_members_cart_id", "type": "UniqueConstraint", "sql": null, "columns": ["cart_id", "user_id"]}].
Indexes: [{"name": "ix_group_order_members_cart_id", "columns": ["cart_id"], "unique": false, "predicate": "None"}, {"name": "ix_group_order_members_invited_by", "columns": ["invited_by"], "unique": false, "predicate": "None"}, {"name": "ix_group_order_members_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.customer_subscriptions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `plan_id`: UUID; required; FK → engagement.subscription_plans.id (RESTRICT).
- `payment_agreement_reference`: TEXT; nullable.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `status`: TEXT; required.

Constraints: [{"name": "fk_customer_subscriptions_plan_id_subscription_plans", "type": "ForeignKeyConstraint", "sql": null, "columns": ["plan_id"]}, {"name": "fk_customer_subscriptions_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_customer_subscriptions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_customer_subscriptions_plan_id", "columns": ["plan_id"], "unique": false, "predicate": "None"}, {"name": "ix_customer_subscriptions_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.device_push_tokens

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `device_id`: UUID; required; FK → identity.user_devices.id (RESTRICT).
- `encrypted_token_reference`: TEXT; required.

Constraints: [{"name": "fk_device_push_tokens_device_id_user_devices", "type": "ForeignKeyConstraint", "sql": null, "columns": ["device_id"]}, {"name": "pk_device_push_tokens", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_device_push_tokens_device_id", "columns": ["device_id"], "unique": false, "predicate": "None"}].

## engagement.promotional_campaigns

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `name`: TEXT; required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; required.
- `funding_party_id`: UUID; required; FK → identity.organizations.id (RESTRICT).

Constraints: [{"name": "fk_promotional_campaigns_funding_party_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["funding_party_id"]}, {"name": "fk_promotional_campaigns_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_promotional_campaigns", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_promotional_campaigns_funding_party_id", "columns": ["funding_party_id"], "unique": false, "predicate": "None"}, {"name": "ix_promotional_campaigns_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.billing_documents

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `private_object_key`: TEXT; required.
- `document_type`: TEXT; required.

Constraints: [{"name": "fk_billing_documents_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_billing_documents", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_billing_documents_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.commission_rules

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `category_id`: UUID; nullable; FK → catalog.product_categories.id (RESTRICT).
- `rate`: NUMERIC(20, 4); required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_commission_rules_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "fk_commission_rules_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_commission_rules", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_commission_rules_category_id", "columns": ["category_id"], "unique": false, "predicate": "None"}, {"name": "ix_commission_rules_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.fee_rules

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `name`: TEXT; required.
- `amount`: NUMERIC(20, 4); required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_fee_rules_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "fk_fee_rules_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "pk_fee_rules", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_fee_rules_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}, {"name": "ix_fee_rules_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}].

## finance.ledger_posting_batches

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `idempotency_key`: TEXT; required.
- `posted_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_ledger_posting_batches_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_ledger_posting_batches", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_ledger_posting_batches_organization_id", "type": "UniqueConstraint", "sql": null, "columns": ["organization_id", "idempotency_key"]}].
Indexes: [{"name": "ix_ledger_posting_batches_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.ledger_reconciliation_results

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `period_end`: TIMESTAMP WITH TIME ZONE; required.
- `debit_total`: NUMERIC(20, 4); required.
- `credit_total`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_ledger_reconciliation_results_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_ledger_reconciliation_results_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_ledger_reconciliation_results", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ledger_reconciliation_results_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_ledger_reconciliation_results_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.settlement_batches

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `period_start`: TIMESTAMP WITH TIME ZONE; required.
- `period_end`: TIMESTAMP WITH TIME ZONE; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_settlement_batches_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_settlement_batches_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_settlement_batches", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_settlement_batches_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_settlement_batches_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.tax_rules

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `tax_code_id`: UUID; required; FK → finance.tax_codes.id (RESTRICT).
- `city_id`: UUID; nullable; FK → geo.cities.id (RESTRICT).
- `rate`: NUMERIC(20, 4); required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_tax_rules_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "fk_tax_rules_tax_code_id_tax_codes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["tax_code_id"]}, {"name": "pk_tax_rules", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_tax_rules_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}, {"name": "ix_tax_rules_tax_code_id", "columns": ["tax_code_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_profiles

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `verified`: BOOLEAN; required.
- `available`: BOOLEAN; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_pilot_profiles_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "fk_pilot_profiles_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_pilot_profiles", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_pilot_profiles_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id"]}].
Indexes: [{"name": "ix_pilot_profiles_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}].

## fulfillment.recurrence_exceptions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `plan_id`: UUID; required; FK → fulfillment.recurring_order_plans.id (RESTRICT).
- `local_date`: DATE; required.
- `skip`: BOOLEAN; required.

Constraints: [{"name": "fk_recurrence_exceptions_plan_id_recurring_order_plans", "type": "ForeignKeyConstraint", "sql": null, "columns": ["plan_id"]}, {"name": "pk_recurrence_exceptions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_recurrence_exceptions_plan_id", "type": "UniqueConstraint", "sql": null, "columns": ["plan_id", "local_date"]}].
Indexes: [{"name": "ix_recurrence_exceptions_plan_id", "columns": ["plan_id"], "unique": false, "predicate": "None"}].

## fulfillment.recurring_order_rules

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `plan_id`: UUID; required; FK → fulfillment.recurring_order_plans.id (RESTRICT).
- `frequency`: TEXT; required.
- `interval`: INTEGER; required.
- `local_time`: TIME WITHOUT TIME ZONE; required.
- `start_date`: DATE; required.
- `end_date`: DATE; nullable.

Constraints: [{"name": "ck_recurring_order_rules_rule_0", "type": "CheckConstraint", "sql": "interval > 0", "columns": []}, {"name": "fk_recurring_order_rules_plan_id_recurring_order_plans", "type": "ForeignKeyConstraint", "sql": null, "columns": ["plan_id"]}, {"name": "pk_recurring_order_rules", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_recurring_order_rules_plan_id", "columns": ["plan_id"], "unique": false, "predicate": "None"}].

## geo.addresses

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `label`: TEXT; required.
- `address_text`: TEXT; required.
- `latitude`: NUMERIC(10, 7); required.
- `longitude`: NUMERIC(10, 7); required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_addresses_coordinates", "type": "CheckConstraint", "sql": "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", "columns": []}, {"name": "fk_addresses_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "fk_addresses_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_addresses", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_addresses_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## geo.operating_calendars

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `name`: TEXT; required.
- `timezone`: TEXT; required.

Constraints: [{"name": "fk_operating_calendars_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "pk_operating_calendars", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_operating_calendars_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}].

## geo.postal_codes

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `code`: TEXT; required.

Constraints: [{"name": "fk_postal_codes_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "pk_postal_codes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_postal_codes_city_id", "type": "UniqueConstraint", "sql": null, "columns": ["city_id", "code"]}].
Indexes: [{"name": "ix_postal_codes_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}].

## geo.service_zones

- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `name`: TEXT; required.
- `active`: BOOLEAN; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_service_zones_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "pk_service_zones", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_service_zones_city_id", "type": "UniqueConstraint", "sql": null, "columns": ["city_id", "name"]}].
Indexes: [{"name": "ix_service_zones_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}].

## identity.authentication_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `event_type`: TEXT; required.
- `session_id`: UUID; nullable; FK → identity.sessions.id (RESTRICT).
- `correlation_id`: TEXT; required.

Constraints: [{"name": "fk_authentication_events_session_id_sessions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["session_id"]}, {"name": "fk_authentication_events_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_authentication_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_authentication_events_session_id", "columns": ["session_id"], "unique": false, "predicate": "None"}, {"name": "ix_authentication_events_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.invitations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `email_digest`: TEXT; required.
- `token_digest`: TEXT; required.
- `role_id`: UUID; required; FK → identity.roles.id (RESTRICT).
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `accepted_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_invitations_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_invitations_role_id_roles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["role_id"]}, {"name": "pk_invitations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_invitations_token_digest", "type": "UniqueConstraint", "sql": null, "columns": ["token_digest"]}].
Indexes: [{"name": "ix_invitations_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_invitations_role_id", "columns": ["role_id"], "unique": false, "predicate": "None"}].

## identity.organization_memberships

- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `status`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_organization_memberships_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_organization_memberships_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_organization_memberships", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_organization_memberships_organization_id", "type": "UniqueConstraint", "sql": null, "columns": ["organization_id", "user_id"]}].
Indexes: [{"name": "ix_organization_memberships_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_organization_memberships_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## identity.organization_settings

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `setting_key`: TEXT; required.
- `value`: JSONB; required.

Constraints: [{"name": "fk_organization_settings_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_organization_settings", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_organization_settings_organization_id", "type": "UniqueConstraint", "sql": null, "columns": ["organization_id", "setting_key"]}].
Indexes: [{"name": "ix_organization_settings_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## identity.refresh_tokens

- `session_id`: UUID; required; FK → identity.sessions.id (RESTRICT).
- `digest`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `used_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_refresh_tokens_session_id_sessions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["session_id"]}, {"name": "pk_refresh_tokens", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_refresh_tokens_digest", "type": "UniqueConstraint", "sql": null, "columns": ["digest"]}].
Indexes: [{"name": "ix_refresh_tokens_session_id", "columns": ["session_id"], "unique": false, "predicate": "None"}].

## integration.integration_connections

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `provider`: TEXT; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_integration_connections_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_integration_connections", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_integration_connections_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_agent_sessions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `purpose`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_ai_agent_sessions_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_ai_agent_sessions_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_ai_agent_sessions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_agent_sessions_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_ai_agent_sessions_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_evaluation_runs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `version_id`: UUID; required; FK → intelligence.ai_model_versions.id (RESTRICT).
- `dataset_reference`: TEXT; required.
- `metrics`: JSONB; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_ai_evaluation_runs_version_id_ai_model_versions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["version_id"]}, {"name": "pk_ai_evaluation_runs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_evaluation_runs_version_id", "columns": ["version_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_inference_runs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `version_id`: UUID; required; FK → intelligence.ai_model_versions.id (RESTRICT).
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `input_digest`: TEXT; required.
- `status`: TEXT; required.
- `retention_until`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_ai_inference_runs_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_ai_inference_runs_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_ai_inference_runs_version_id_ai_model_versions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["version_id"]}, {"name": "pk_ai_inference_runs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_inference_runs_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_ai_inference_runs_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_ai_inference_runs_version_id", "columns": ["version_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_brands

- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `name`: TEXT; required.
- `merchant_type`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_merchant_brands_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_brands", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_brands_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id"]}].
Indexes: [{"name": "ix_merchant_brands_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_documents

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `document_type`: TEXT; required.
- `private_object_key`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `review_status`: TEXT; required.

Constraints: [{"name": "fk_merchant_documents_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_documents", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_documents_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_legal_entities

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).
- `registered_name`: TEXT; required.
- `registration_reference`: TEXT; required.

Constraints: [{"name": "fk_merchant_legal_entities_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "fk_merchant_legal_entities_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_legal_entities", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_legal_entities_country_id", "type": "UniqueConstraint", "sql": null, "columns": ["country_id", "registration_reference"]}].
Indexes: [{"name": "ix_merchant_legal_entities_country_id", "columns": ["country_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_legal_entities_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_organizations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `onboarding_status`: TEXT; required.

Constraints: [{"name": "fk_merchant_organizations_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_organizations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_organizations_organization_id", "type": "UniqueConstraint", "sql": null, "columns": ["organization_id"]}].
Indexes: [{"name": "ix_merchant_organizations_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## operations.notification_attempts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `job_id`: UUID; required; FK → operations.notification_jobs.id (RESTRICT).
- `attempt`: INTEGER; required.
- `result_code`: TEXT; required.

Constraints: [{"name": "fk_notification_attempts_job_id_notification_jobs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["job_id"]}, {"name": "pk_notification_attempts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_notification_attempts_job_id", "columns": ["job_id"], "unique": false, "predicate": "None"}].

## operations.notification_deliveries

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `job_id`: UUID; required; FK → operations.notification_jobs.id (RESTRICT).
- `provider_reference`: TEXT; required.
- `delivered_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_notification_deliveries_job_id_notification_jobs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["job_id"]}, {"name": "pk_notification_deliveries", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_notification_deliveries_job_id", "columns": ["job_id"], "unique": false, "predicate": "None"}].

## operations.operational_incidents

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `severity`: TEXT; required.
- `summary`: TEXT; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_operational_incidents_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "pk_operational_incidents", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_operational_incidents_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}].

## catalog.dietary_attributes

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `dietary_code`: TEXT; required.

Constraints: [{"name": "fk_dietary_attributes_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_dietary_attributes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_dietary_attributes_product_id", "type": "UniqueConstraint", "sql": null, "columns": ["product_id", "dietary_code"]}].
Indexes: [{"name": "ix_dietary_attributes_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.option_values

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `group_id`: UUID; required; FK → catalog.option_groups.id (RESTRICT).
- `name`: TEXT; required.
- `price_delta`: NUMERIC(20, 4); required.

Constraints: [{"name": "ck_option_values_rule_0", "type": "CheckConstraint", "sql": "price_delta >= 0", "columns": []}, {"name": "fk_option_values_group_id_option_groups", "type": "ForeignKeyConstraint", "sql": null, "columns": ["group_id"]}, {"name": "pk_option_values", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_option_values_group_id", "columns": ["group_id"], "unique": false, "predicate": "None"}].

## catalog.pharmacy_restrictions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `prescription_required`: BOOLEAN; required.
- `license_category`: TEXT; required.
- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).

Constraints: [{"name": "fk_pharmacy_restrictions_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "fk_pharmacy_restrictions_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_pharmacy_restrictions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pharmacy_restrictions_country_id", "columns": ["country_id"], "unique": false, "predicate": "None"}, {"name": "ix_pharmacy_restrictions_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_allergens

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `allergen_code`: TEXT; required.
- `may_contain`: BOOLEAN; required.

Constraints: [{"name": "fk_product_allergens_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_allergens", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_allergens_product_id", "type": "UniqueConstraint", "sql": null, "columns": ["product_id", "allergen_code"]}].
Indexes: [{"name": "ix_product_allergens_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_customizations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `option_group_id`: UUID; required; FK → catalog.option_groups.id (RESTRICT).
- `required`: BOOLEAN; required.

Constraints: [{"name": "fk_product_customizations_option_group_id_option_groups", "type": "ForeignKeyConstraint", "sql": null, "columns": ["option_group_id"]}, {"name": "fk_product_customizations_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_customizations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_product_customizations_option_group_id", "columns": ["option_group_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_customizations_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_images

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `object_key`: TEXT; required.
- `alt_text`: TEXT; required.
- `sort_order`: INTEGER; required.

Constraints: [{"name": "fk_product_images_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_images", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_product_images_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_options

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `group_id`: UUID; required; FK → catalog.option_groups.id (RESTRICT).

Constraints: [{"name": "fk_product_options_group_id_option_groups", "type": "ForeignKeyConstraint", "sql": null, "columns": ["group_id"]}, {"name": "fk_product_options_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_options", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_options_product_id", "type": "UniqueConstraint", "sql": null, "columns": ["product_id", "group_id"]}].
Indexes: [{"name": "ix_product_options_group_id", "columns": ["group_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_options_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_status_history

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `previous`: TEXT; required.
- `current`: TEXT; required.

Constraints: [{"name": "fk_product_status_history_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_product_status_history_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_status_history", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_product_status_history_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_status_history_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_tags

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `tag`: TEXT; required.

Constraints: [{"name": "fk_product_tags_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_tags", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_tags_product_id", "type": "UniqueConstraint", "sql": null, "columns": ["product_id", "tag"]}].
Indexes: [{"name": "ix_product_tags_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_tax_categories

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `tax_code_id`: UUID; required; FK → finance.tax_codes.id (RESTRICT).

Constraints: [{"name": "fk_product_tax_categories_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "fk_product_tax_categories_tax_code_id_tax_codes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["tax_code_id"]}, {"name": "pk_product_tax_categories", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_tax_categories_product_id", "type": "UniqueConstraint", "sql": null, "columns": ["product_id", "tax_code_id"]}].
Indexes: [{"name": "ix_product_tax_categories_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_tax_categories_tax_code_id", "columns": ["tax_code_id"], "unique": false, "predicate": "None"}].

## catalog.product_variants

- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `sku`: TEXT; required.
- `name`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_product_variants_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_variants", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_variants_product_id", "type": "UniqueConstraint", "sql": null, "columns": ["product_id", "sku"]}].
Indexes: [{"name": "ix_product_variants_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## commerce.orders

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `quote_id`: UUID; required; FK → commerce.checkout_quotes.id (RESTRICT).
- `status`: TEXT; required.
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT).
- `total`: NUMERIC(20, 4); required.
- `version`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_orders_nonnegative_total", "type": "CheckConstraint", "sql": "total >= 0", "columns": []}, {"name": "fk_orders_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_orders_quote_id_checkout_quotes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["quote_id"]}, {"name": "fk_orders_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_orders", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_orders_quote_id", "type": "UniqueConstraint", "sql": null, "columns": ["quote_id"]}].
Indexes: [{"name": "ix_orders_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.coupons

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `campaign_id`: UUID; required; FK → engagement.promotional_campaigns.id (RESTRICT).
- `code`: TEXT; required.
- `total_limit`: INTEGER; required.
- `per_user_limit`: INTEGER; required.
- `per_merchant_limit`: INTEGER; required.
- `redeemed`: INTEGER; required.
- `stackable`: BOOLEAN; required.

Constraints: [{"name": "ck_coupons_rule_0", "type": "CheckConstraint", "sql": "total_limit > 0 AND per_user_limit > 0 AND per_merchant_limit > 0 AND redeemed BETWEEN 0 AND total_limit", "columns": []}, {"name": "fk_coupons_campaign_id_promotional_campaigns", "type": "ForeignKeyConstraint", "sql": null, "columns": ["campaign_id"]}, {"name": "pk_coupons", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_coupons_code", "type": "UniqueConstraint", "sql": null, "columns": ["code"]}].
Indexes: [{"name": "ix_coupons_campaign_id", "columns": ["campaign_id"], "unique": false, "predicate": "None"}].

## engagement.subscription_billing_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `subscription_id`: UUID; required; FK → engagement.customer_subscriptions.id (RESTRICT).
- `period_start`: TIMESTAMP WITH TIME ZONE; required.
- `amount`: NUMERIC(20, 4); required.
- `provider_reference`: TEXT; nullable.
- `status`: TEXT; required.

Constraints: [{"name": "fk_subscription_billing_events_subscription_id_customer_subscriptions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["subscription_id"]}, {"name": "pk_subscription_billing_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_subscription_billing_events_subscription_id", "type": "UniqueConstraint", "sql": null, "columns": ["subscription_id", "period_start"]}].
Indexes: [{"name": "ix_subscription_billing_events_subscription_id", "columns": ["subscription_id"], "unique": false, "predicate": "None"}].

## finance.ledger_books

- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `legal_entity_id`: UUID; required; FK → merchant.merchant_legal_entities.id (RESTRICT).
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_ledger_books_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_ledger_books_legal_entity_id_merchant_legal_entities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["legal_entity_id"]}, {"name": "fk_ledger_books_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_ledger_books", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_ledger_book_currency_scope", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id", "currency"]}, {"name": "uq_ledger_book_org_scope", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id"]}, {"name": "uq_ledger_books_legal_entity_id", "type": "UniqueConstraint", "sql": null, "columns": ["legal_entity_id", "currency"]}].
Indexes: [].

## finance.payout_requests

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `batch_id`: UUID; required; FK → finance.settlement_batches.id (RESTRICT).
- `idempotency_key`: TEXT; required.
- `amount`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_payout_requests_batch_id_settlement_batches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["batch_id"]}, {"name": "pk_payout_requests", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_payout_requests_idempotency_key", "type": "UniqueConstraint", "sql": null, "columns": ["idempotency_key"]}].
Indexes: [{"name": "ix_payout_requests_batch_id", "columns": ["batch_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_routes

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `status`: TEXT; required.

Constraints: [{"name": "fk_delivery_routes_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_delivery_routes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_routes_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_availability

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `available`: BOOLEAN; required.
- `changed_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_pilot_availability_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_availability", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_availability_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_capabilities

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `capability`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_pilot_capabilities_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_capabilities", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_capabilities_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_documents

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `document_type`: TEXT; required.
- `private_object_key`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_pilot_documents_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_documents", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_documents_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_incentives

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `policy_reference`: TEXT; required.

Constraints: [{"name": "fk_pilot_incentives_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_pilot_incentives_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_incentives", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_incentives_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_incentives_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_latest_location

- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `latitude`: NUMERIC(10, 7); required.
- `longitude`: NUMERIC(10, 7); required.
- `observed_at`: TIMESTAMP WITH TIME ZONE; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_pilot_latest_location_location_coordinates", "type": "CheckConstraint", "sql": "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", "columns": []}, {"name": "fk_pilot_latest_location_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_latest_location", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_pilot_latest_location_pilot_id", "type": "UniqueConstraint", "sql": null, "columns": ["pilot_id"]}].
Indexes: [].

## fulfillment.pilot_location_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `latitude`: NUMERIC(20, 4); required.
- `longitude`: NUMERIC(20, 4); required.
- `observed_at`: TIMESTAMP WITH TIME ZONE; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_pilot_location_events_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_location_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_history_retention", "columns": ["expires_at", "id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_history_subject_time", "columns": ["pilot_id", "observed_at", "id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_location_events_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_service_zones

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).

Constraints: [{"name": "fk_pilot_service_zones_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pilot_service_zones_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_pilot_service_zones", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_service_zones_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_service_zones_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_shifts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_pilot_shifts_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_shifts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_shifts_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_status_history

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `previous`: TEXT; required.
- `current`: TEXT; required.
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).

Constraints: [{"name": "fk_pilot_status_history_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_pilot_status_history_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_status_history", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_status_history_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_status_history_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_vehicles

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `vehicle_type`: TEXT; required.
- `registration_token`: TEXT; required.

Constraints: [{"name": "fk_pilot_vehicles_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "pk_pilot_vehicles", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_vehicles_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}].

## geo.delivery_service_areas

- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).
- `name`: TEXT; required.
- `spatial_ready`: BOOLEAN; required; default false.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_delivery_service_areas_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_delivery_service_areas", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_delivery_service_areas_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "zone_id"]}].
Indexes: [{"name": "ix_delivery_service_areas_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## geo.geo_locations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `address_id`: UUID; required; FK → geo.addresses.id (RESTRICT).
- `latitude`: NUMERIC(20, 4); required.
- `longitude`: NUMERIC(20, 4); required.
- `source`: TEXT; required.

Constraints: [{"name": "ck_geo_locations_rule_0", "type": "CheckConstraint", "sql": "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", "columns": []}, {"name": "fk_geo_locations_address_id_addresses", "type": "ForeignKeyConstraint", "sql": null, "columns": ["address_id"]}, {"name": "pk_geo_locations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_geo_locations_address_id", "columns": ["address_id"], "unique": false, "predicate": "None"}].

## geo.holidays

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `calendar_id`: UUID; required; FK → geo.operating_calendars.id (RESTRICT).
- `local_date`: DATE; required.
- `closed`: BOOLEAN; required.
- `name`: TEXT; required.

Constraints: [{"name": "fk_holidays_calendar_id_operating_calendars", "type": "ForeignKeyConstraint", "sql": null, "columns": ["calendar_id"]}, {"name": "pk_holidays", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_holidays_calendar_id", "type": "UniqueConstraint", "sql": null, "columns": ["calendar_id", "local_date"]}].
Indexes: [{"name": "ix_holidays_calendar_id", "columns": ["calendar_id"], "unique": false, "predicate": "None"}].

## geo.zone_boundaries

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).
- `revision`: INTEGER; required.
- `effective_at`: TIMESTAMP WITH TIME ZONE; required.
- `object_key`: TEXT; required.

Constraints: [{"name": "fk_zone_boundaries_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_zone_boundaries", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_zone_boundaries_zone_id", "type": "UniqueConstraint", "sql": null, "columns": ["zone_id", "revision"]}].
Indexes: [{"name": "ix_zone_boundaries_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## geo.zone_capacity_settings

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).
- `maximum_active_tasks`: INTEGER; required.
- `version`: INTEGER; required.

Constraints: [{"name": "ck_zone_capacity_settings_rule_0", "type": "CheckConstraint", "sql": "maximum_active_tasks > 0", "columns": []}, {"name": "fk_zone_capacity_settings_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_zone_capacity_settings", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_zone_capacity_settings_zone_id", "type": "UniqueConstraint", "sql": null, "columns": ["zone_id"]}].
Indexes: [{"name": "ix_zone_capacity_settings_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## geo.zone_delivery_policies

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).
- `delivery_method`: TEXT; required.
- `maximum_distance_m`: INTEGER; required.
- `active`: BOOLEAN; required.

Constraints: [{"name": "ck_zone_delivery_policies_rule_0", "type": "CheckConstraint", "sql": "maximum_distance_m > 0", "columns": []}, {"name": "fk_zone_delivery_policies_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_zone_delivery_policies", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_zone_delivery_policies_zone_id", "type": "UniqueConstraint", "sql": null, "columns": ["zone_id", "delivery_method"]}].
Indexes: [{"name": "ix_zone_delivery_policies_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## geo.zone_operating_hours

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).
- `weekday`: INTEGER; required.
- `opens_at`: TIME WITHOUT TIME ZONE; required.
- `closes_at`: TIME WITHOUT TIME ZONE; required.

Constraints: [{"name": "ck_zone_operating_hours_rule_0", "type": "CheckConstraint", "sql": "weekday BETWEEN 0 AND 6", "columns": []}, {"name": "ck_zone_operating_hours_rule_1", "type": "CheckConstraint", "sql": "opens_at < closes_at", "columns": []}, {"name": "fk_zone_operating_hours_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_zone_operating_hours", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_zone_operating_hours_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## geo.zone_service_categories

- `zone_id`: UUID; required; FK → geo.service_zones.id (RESTRICT).
- `category_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).
- `enabled`: BOOLEAN; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_zone_service_categories_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "fk_zone_service_categories_zone_id_service_zones", "type": "ForeignKeyConstraint", "sql": null, "columns": ["zone_id"]}, {"name": "pk_zone_service_categories", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_zone_service_categories_zone_id", "type": "UniqueConstraint", "sql": null, "columns": ["zone_id", "category_id"]}].
Indexes: [{"name": "ix_zone_service_categories_zone_id", "columns": ["zone_id"], "unique": false, "predicate": "None"}].

## integration.integration_credentials_references

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `connection_id`: UUID; required; FK → integration.integration_connections.id (RESTRICT).
- `secret_manager_reference`: TEXT; required.
- `rotated_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_integration_credentials_references_connection_id_integration_connections", "type": "ForeignKeyConstraint", "sql": null, "columns": ["connection_id"]}, {"name": "pk_integration_credentials_references", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_integration_credentials_references_connection_id", "columns": ["connection_id"], "unique": false, "predicate": "None"}].

## integration.integration_errors

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `connection_id`: UUID; required; FK → integration.integration_connections.id (RESTRICT).
- `error_code`: TEXT; required.
- `safe_message`: TEXT; required.
- `retry_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_integration_errors_connection_id_integration_connections", "type": "ForeignKeyConstraint", "sql": null, "columns": ["connection_id"]}, {"name": "pk_integration_errors", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_integration_errors_connection_id", "columns": ["connection_id"], "unique": false, "predicate": "None"}].

## integration.integration_sync_checkpoints

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `connection_id`: UUID; required; FK → integration.integration_connections.id (RESTRICT).
- `stream`: TEXT; required.
- `cursor`: TEXT; required.

Constraints: [{"name": "fk_integration_sync_checkpoints_connection_id_integration_connections", "type": "ForeignKeyConstraint", "sql": null, "columns": ["connection_id"]}, {"name": "pk_integration_sync_checkpoints", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_integration_sync_checkpoints_connection_id", "type": "UniqueConstraint", "sql": null, "columns": ["connection_id", "stream"]}].
Indexes: [{"name": "ix_integration_sync_checkpoints_connection_id", "columns": ["connection_id"], "unique": false, "predicate": "None"}].

## integration.integration_sync_jobs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `connection_id`: UUID; required; FK → integration.integration_connections.id (RESTRICT).
- `status`: TEXT; required.
- `available_at`: TIMESTAMP WITH TIME ZONE; required.
- `attempts`: INTEGER; required.

Constraints: [{"name": "fk_integration_sync_jobs_connection_id_integration_connections", "type": "ForeignKeyConstraint", "sql": null, "columns": ["connection_id"]}, {"name": "pk_integration_sync_jobs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_integration_sync_jobs_connection_id", "columns": ["connection_id"], "unique": false, "predicate": "None"}].

## integration.integration_webhook_subscriptions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `connection_id`: UUID; required; FK → integration.integration_connections.id (RESTRICT).
- `event_type`: TEXT; required.
- `endpoint_reference`: TEXT; required.
- `active`: BOOLEAN; required.

Constraints: [{"name": "fk_integration_webhook_subscriptions_connection_id_integration_connections", "type": "ForeignKeyConstraint", "sql": null, "columns": ["connection_id"]}, {"name": "pk_integration_webhook_subscriptions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_integration_webhook_subscriptions_connection_id", "columns": ["connection_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_agent_tool_calls

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `session_id`: UUID; required; FK → intelligence.ai_agent_sessions.id (RESTRICT).
- `tool_name`: TEXT; required.
- `argument_digest`: TEXT; required.
- `policy_decision`: TEXT; required.
- `result_digest`: TEXT; nullable.

Constraints: [{"name": "fk_ai_agent_tool_calls_session_id_ai_agent_sessions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["session_id"]}, {"name": "pk_ai_agent_tool_calls", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_agent_tool_calls_session_id", "columns": ["session_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_feedback

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `run_id`: UUID; required; FK → intelligence.ai_inference_runs.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `rating`: INTEGER; required.
- `safe_comment`: TEXT; nullable.

Constraints: [{"name": "fk_ai_feedback_run_id_ai_inference_runs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["run_id"]}, {"name": "fk_ai_feedback_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_ai_feedback", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_feedback_run_id", "columns": ["run_id"], "unique": false, "predicate": "None"}, {"name": "ix_ai_feedback_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_prediction_records

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `run_id`: UUID; required; FK → intelligence.ai_inference_runs.id (RESTRICT).
- `prediction_type`: TEXT; required.
- `output`: JSONB; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_ai_prediction_records_run_id_ai_inference_runs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["run_id"]}, {"name": "pk_ai_prediction_records", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_prediction_records_run_id", "columns": ["run_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_risk_signals

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `run_id`: UUID; required; FK → intelligence.ai_inference_runs.id (RESTRICT).
- `subject_digest`: TEXT; required.
- `kind`: TEXT; required.
- `score`: NUMERIC(20, 4); required.
- `review_status`: TEXT; required.

Constraints: [{"name": "fk_ai_risk_signals_run_id_ai_inference_runs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["run_id"]}, {"name": "pk_ai_risk_signals", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_risk_signals_run_id", "columns": ["run_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_bank_accounts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `legal_entity_id`: UUID; required; FK → merchant.merchant_legal_entities.id (RESTRICT).
- `provider_token`: TEXT; required.
- `display_last_four`: TEXT; required.
- `verified_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_merchant_bank_accounts_legal_entity_id_merchant_legal_entities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["legal_entity_id"]}, {"name": "pk_merchant_bank_accounts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_bank_accounts_legal_entity_id", "columns": ["legal_entity_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_branches

- `brand_id`: UUID; required; FK → merchant.merchant_brands.id (RESTRICT).
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT); FK → merchant.merchant_brands.organization_id (RESTRICT).
- `city_id`: UUID; required; FK → geo.cities.id (RESTRICT).
- `name`: TEXT; required.
- `status`: TEXT; required.
- `accepting_orders`: BOOLEAN; required.
- `latitude`: NUMERIC(10, 7); required.
- `longitude`: NUMERIC(10, 7); required.
- `version`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_merchant_branches_branch_status", "type": "CheckConstraint", "sql": "status IN ('pending','approved','rejected','suspended')", "columns": []}, {"name": "ck_merchant_branches_coordinates", "type": "CheckConstraint", "sql": "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", "columns": []}, {"name": "fk_merchant_branches_brand_id_merchant_brands", "type": "ForeignKeyConstraint", "sql": null, "columns": ["brand_id", "organization_id"]}, {"name": "fk_merchant_branches_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "fk_merchant_branches_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_branches", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_branches_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id"]}].
Indexes: [{"name": "ix_merchant_branches_city_id", "columns": ["city_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_branches_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_category_assignments

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `brand_id`: UUID; required; FK → merchant.merchant_brands.id (RESTRICT).
- `category_id`: UUID; required; FK → merchant.merchant_categories.id (RESTRICT).

Constraints: [{"name": "fk_merchant_category_assignments_brand_id_merchant_brands", "type": "ForeignKeyConstraint", "sql": null, "columns": ["brand_id"]}, {"name": "fk_merchant_category_assignments_category_id_merchant_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "pk_merchant_category_assignments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_category_assignments_brand_id", "type": "UniqueConstraint", "sql": null, "columns": ["brand_id", "category_id"]}].
Indexes: [{"name": "ix_merchant_category_assignments_brand_id", "columns": ["brand_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_category_assignments_category_id", "columns": ["category_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_contracts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `legal_entity_id`: UUID; required; FK → merchant.merchant_legal_entities.id (RESTRICT).
- `private_object_key`: TEXT; required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_merchant_contracts_legal_entity_id_merchant_legal_entities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["legal_entity_id"]}, {"name": "fk_merchant_contracts_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_contracts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_contracts_legal_entity_id", "columns": ["legal_entity_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_contracts_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_tax_registrations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `legal_entity_id`: UUID; required; FK → merchant.merchant_legal_entities.id (RESTRICT).
- `country_id`: UUID; required; FK → geo.countries.id (RESTRICT).
- `registration_token`: TEXT; required.
- `tax_type`: TEXT; required.

Constraints: [{"name": "fk_merchant_tax_registrations_country_id_countries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["country_id"]}, {"name": "fk_merchant_tax_registrations_legal_entity_id_merchant_legal_entities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["legal_entity_id"]}, {"name": "pk_merchant_tax_registrations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_tax_registrations_country_id", "columns": ["country_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_tax_registrations_legal_entity_id", "columns": ["legal_entity_id"], "unique": false, "predicate": "None"}].

## catalog.merchant_catalogs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `branch_id`: UUID; nullable; FK → merchant.merchant_branches.id (RESTRICT).
- `name`: TEXT; required.
- `active`: BOOLEAN; required.

Constraints: [{"name": "fk_merchant_catalogs_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_merchant_catalogs_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_catalogs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_catalogs_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_catalogs_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## catalog.product_availability_windows

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "ck_product_availability_windows_rule_0", "type": "CheckConstraint", "sql": "ends_at > starts_at", "columns": []}, {"name": "fk_product_availability_windows_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_product_availability_windows_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_availability_windows", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_product_availability_windows_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_availability_windows_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_branch_availability

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `available`: BOOLEAN; required.

Constraints: [{"name": "fk_product_branch_availability_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_product_branch_availability_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_product_branch_availability", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_branch_availability_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id", "variant_id"]}].
Indexes: [{"name": "ix_product_branch_availability_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_branch_availability_variant_id", "columns": ["variant_id"], "unique": false, "predicate": "None"}].

## catalog.product_combinations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `product_id`: UUID; required; FK → catalog.products.id (RESTRICT).
- `component_variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `quantity`: NUMERIC(20, 4); required.

Constraints: [{"name": "ck_product_combinations_rule_0", "type": "CheckConstraint", "sql": "quantity > 0", "columns": []}, {"name": "fk_product_combinations_component_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["component_variant_id"]}, {"name": "fk_product_combinations_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "pk_product_combinations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_product_combinations_component_variant_id", "columns": ["component_variant_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_combinations_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}].

## catalog.product_option_assignments

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `option_id`: UUID; required; FK → catalog.option_values.id (RESTRICT).

Constraints: [{"name": "fk_product_option_assignments_option_id_option_values", "type": "ForeignKeyConstraint", "sql": null, "columns": ["option_id"]}, {"name": "fk_product_option_assignments_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_product_option_assignments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_product_option_assignments_variant_id", "type": "UniqueConstraint", "sql": null, "columns": ["variant_id", "option_id"]}].
Indexes: [{"name": "ix_product_option_assignments_option_id", "columns": ["option_id"], "unique": false, "predicate": "None"}, {"name": "ix_product_option_assignments_variant_id", "columns": ["variant_id"], "unique": false, "predicate": "None"}].

## catalog.product_prices

- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT).
- `price_book_id`: UUID; nullable; FK → catalog.price_books.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_product_prices_nonnegative_price", "type": "CheckConstraint", "sql": "amount >= 0", "columns": []}, {"name": "ck_product_prices_valid_price_period", "type": "CheckConstraint", "sql": "ends_at IS NULL OR ends_at > starts_at", "columns": []}, {"name": "fk_product_prices_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_product_prices_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_product_prices_price_book_id_price_books", "type": "ForeignKeyConstraint", "sql": null, "columns": ["price_book_id"]}, {"name": "fk_product_prices_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_product_prices", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_price_lookup", "columns": ["branch_id", "variant_id", "starts_at"], "unique": false, "predicate": "None"}].

## commerce.corporate_order_references

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `purchase_order_reference`: TEXT; required.

Constraints: [{"name": "fk_corporate_order_references_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_corporate_order_references_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_corporate_order_references", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_corporate_order_references_order_id", "type": "UniqueConstraint", "sql": null, "columns": ["order_id"]}].
Indexes: [{"name": "ix_corporate_order_references_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_corporate_order_references_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## commerce.merchant_orders

- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `status`: TEXT; required.
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT).
- `total`: NUMERIC(20, 4); required.
- `version`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_merchant_orders_nonnegative_total", "type": "CheckConstraint", "sql": "total >= 0", "columns": []}, {"name": "fk_merchant_orders_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_merchant_orders_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_merchant_orders_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_merchant_orders", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_orders_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "branch_id"]}].
Indexes: [{"name": "ix_merchant_orders_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_orders_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## commerce.order_adjustments

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `reason`: TEXT; required.
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).

Constraints: [{"name": "fk_order_adjustments_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_order_adjustments_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_order_adjustments_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_order_adjustments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_adjustments_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_adjustments_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_adjustments_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## commerce.order_amount_breakdowns

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `kind`: TEXT; required.
- `amount`: NUMERIC(20, 4); required.
- `funding_organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).

Constraints: [{"name": "fk_order_amount_breakdowns_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_order_amount_breakdowns_funding_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["funding_organization_id"]}, {"name": "fk_order_amount_breakdowns_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_order_amount_breakdowns", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_amount_breakdowns_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_amount_breakdowns_funding_organization_id", "columns": ["funding_organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_amount_breakdowns_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## commerce.order_discounts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `campaign_id`: UUID; nullable; FK → engagement.promotional_campaigns.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `funding_organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).

Constraints: [{"name": "fk_order_discounts_campaign_id_promotional_campaigns", "type": "ForeignKeyConstraint", "sql": null, "columns": ["campaign_id"]}, {"name": "fk_order_discounts_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_order_discounts_funding_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["funding_organization_id"]}, {"name": "fk_order_discounts_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_order_discounts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_discounts_campaign_id", "columns": ["campaign_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_discounts_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_discounts_funding_organization_id", "columns": ["funding_organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_discounts_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## commerce.order_idempotency_records

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `key`: TEXT; required.
- `fingerprint`: TEXT; required.
- `order_id`: UUID; nullable; FK → commerce.orders.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_order_idempotency_records_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_order_idempotency_records_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_order_idempotency_records", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_order_idempotency_records_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id", "key"]}].
Indexes: [].

## commerce.order_refund_requests

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `requested_by`: UUID; required; FK → identity.users.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `reason`: TEXT; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_order_refund_requests_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_order_refund_requests_requested_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["requested_by"]}, {"name": "pk_order_refund_requests", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_refund_requests_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_refund_requests_requested_by", "columns": ["requested_by"], "unique": false, "predicate": "None"}].

## commerce.order_tax_lines

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `tax_code_id`: UUID; required; FK → finance.tax_codes.id (RESTRICT).
- `rate`: NUMERIC(20, 4); required.
- `taxable_amount`: NUMERIC(20, 4); required.
- `amount`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_order_tax_lines_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_order_tax_lines_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_order_tax_lines_tax_code_id_tax_codes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["tax_code_id"]}, {"name": "pk_order_tax_lines", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_tax_lines_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_tax_lines_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_tax_lines_tax_code_id", "columns": ["tax_code_id"], "unique": false, "predicate": "None"}].

## commerce.order_timeline_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `event_type`: TEXT; required.
- `safe_payload`: JSONB; required.

Constraints: [{"name": "fk_order_timeline_events_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_order_timeline_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_timeline_events_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## engagement.coupon_eligibility_rules

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `coupon_id`: UUID; required; FK → engagement.coupons.id (RESTRICT).
- `category_id`: UUID; nullable; FK → catalog.product_categories.id (RESTRICT).
- `minimum_amount`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_coupon_eligibility_rules_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "fk_coupon_eligibility_rules_coupon_id_coupons", "type": "ForeignKeyConstraint", "sql": null, "columns": ["coupon_id"]}, {"name": "pk_coupon_eligibility_rules", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_coupon_eligibility_rules_category_id", "columns": ["category_id"], "unique": false, "predicate": "None"}, {"name": "ix_coupon_eligibility_rules_coupon_id", "columns": ["coupon_id"], "unique": false, "predicate": "None"}].

## engagement.coupon_redemptions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `coupon_id`: UUID; required; FK → engagement.coupons.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_coupon_redemptions_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_coupon_redemptions_coupon_id_coupons", "type": "ForeignKeyConstraint", "sql": null, "columns": ["coupon_id"]}, {"name": "fk_coupon_redemptions_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_coupon_redemptions_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_coupon_redemptions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_coupon_redemptions_coupon_id", "type": "UniqueConstraint", "sql": null, "columns": ["coupon_id", "order_id", "branch_id"]}].
Indexes: [{"name": "ix_coupon_redemptions_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_coupon_redemptions_coupon_id", "columns": ["coupon_id"], "unique": false, "predicate": "None"}, {"name": "ix_coupon_redemptions_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_coupon_redemptions_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.customer_favorites

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `product_id`: UUID; nullable; FK → catalog.products.id (RESTRICT).

Constraints: [{"name": "fk_customer_favorites_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_customer_favorites_product_id_products", "type": "ForeignKeyConstraint", "sql": null, "columns": ["product_id"]}, {"name": "fk_customer_favorites_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_customer_favorites", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_customer_favorites_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_customer_favorites_product_id", "columns": ["product_id"], "unique": false, "predicate": "None"}, {"name": "ix_customer_favorites_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## engagement.loyalty_transactions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `account_id`: UUID; required; FK → engagement.loyalty_accounts.id (RESTRICT).
- `order_id`: UUID; nullable; FK → commerce.orders.id (RESTRICT).
- `points`: INTEGER; required.
- `idempotency_key`: TEXT; required.

Constraints: [{"name": "fk_loyalty_transactions_account_id_loyalty_accounts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["account_id"]}, {"name": "fk_loyalty_transactions_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_loyalty_transactions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_loyalty_transactions_idempotency_key", "type": "UniqueConstraint", "sql": null, "columns": ["idempotency_key"]}].
Indexes: [{"name": "ix_loyalty_transactions_account_id", "columns": ["account_id"], "unique": false, "predicate": "None"}, {"name": "ix_loyalty_transactions_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## engagement.merchant_promotions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `campaign_id`: UUID; required; FK → engagement.promotional_campaigns.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).

Constraints: [{"name": "fk_merchant_promotions_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_merchant_promotions_campaign_id_promotional_campaigns", "type": "ForeignKeyConstraint", "sql": null, "columns": ["campaign_id"]}, {"name": "pk_merchant_promotions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_promotions_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_promotions_campaign_id", "columns": ["campaign_id"], "unique": false, "predicate": "None"}].

## finance.invoices

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `order_id`: UUID; nullable; FK → commerce.orders.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `invoice_number`: TEXT; required.
- `total`: NUMERIC(20, 4); required.
- `issued_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_invoices_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_invoices_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_invoices_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_invoices", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_invoices_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_invoices_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_invoices_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.journal_entries

- `organization_id`: UUID; required; FK → finance.ledger_books.organization_id (RESTRICT); FK → identity.organizations.id (RESTRICT).
- `book_id`: UUID; required; FK → finance.ledger_books.id (RESTRICT); FK → finance.ledger_books.id (RESTRICT).
- `idempotency_key`: TEXT; required.
- `status`: TEXT; required.
- `description`: TEXT; required.
- `reversal_of`: UUID; nullable; FK → finance.journal_entries.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_journal_entries_journal_status", "type": "CheckConstraint", "sql": "status IN ('draft','posted')", "columns": []}, {"name": "fk_journal_book_scope", "type": "ForeignKeyConstraint", "sql": null, "columns": ["book_id", "organization_id"]}, {"name": "fk_journal_entries_book_id_ledger_books", "type": "ForeignKeyConstraint", "sql": null, "columns": ["book_id"]}, {"name": "fk_journal_entries_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_journal_entries_reversal_of_journal_entries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reversal_of"]}, {"name": "pk_journal_entries", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_journal_entries_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id"]}, {"name": "uq_journal_entries_organization_id", "type": "UniqueConstraint", "sql": null, "columns": ["organization_id", "idempotency_key"]}].
Indexes: [].

## finance.ledger_accounts

- `organization_id`: UUID; required; FK → finance.ledger_books.organization_id (RESTRICT); FK → identity.organizations.id (RESTRICT).
- `book_id`: UUID; required; FK → finance.ledger_books.id (RESTRICT); FK → finance.ledger_books.id (RESTRICT).
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT); FK → finance.ledger_books.currency (RESTRICT).
- `code`: TEXT; required.
- `kind`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_account_book_scope", "type": "ForeignKeyConstraint", "sql": null, "columns": ["book_id", "organization_id", "currency"]}, {"name": "fk_ledger_accounts_book_id_ledger_books", "type": "ForeignKeyConstraint", "sql": null, "columns": ["book_id"]}, {"name": "fk_ledger_accounts_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_ledger_accounts_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_ledger_accounts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_ledger_accounts_book_id", "type": "UniqueConstraint", "sql": null, "columns": ["book_id", "code"]}, {"name": "uq_ledger_accounts_id", "type": "UniqueConstraint", "sql": null, "columns": ["id", "organization_id", "currency"]}].
Indexes: [{"name": "ix_ledger_accounts_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.payment_intents

- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `provider`: TEXT; required.
- `status`: TEXT; required.
- `currency`: VARCHAR(3); required; FK → finance.currencies.code (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `refunded`: NUMERIC(20, 4); required.
- `provider_reference`: TEXT; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_payment_intents_payment_amounts", "type": "CheckConstraint", "sql": "amount > 0 AND refunded BETWEEN 0 AND amount", "columns": []}, {"name": "fk_payment_intents_currency_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency"]}, {"name": "fk_payment_intents_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_payment_intents", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_payment_intents_order_id", "type": "UniqueConstraint", "sql": null, "columns": ["order_id", "provider"]}, {"name": "uq_payment_intents_provider_reference", "type": "UniqueConstraint", "sql": null, "columns": ["provider_reference"]}].
Indexes: [].

## finance.payout_attempts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `request_id`: UUID; required; FK → finance.payout_requests.id (RESTRICT).
- `provider_reference`: TEXT; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_payout_attempts_request_id_payout_requests", "type": "ForeignKeyConstraint", "sql": null, "columns": ["request_id"]}, {"name": "pk_payout_attempts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_payout_attempts_request_id", "columns": ["request_id"], "unique": false, "predicate": "None"}].

## finance.payout_bank_references

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `request_id`: UUID; required; FK → finance.payout_requests.id (RESTRICT).
- `provider_bank_token`: TEXT; required.
- `display_last_four`: TEXT; required.

Constraints: [{"name": "fk_payout_bank_references_request_id_payout_requests", "type": "ForeignKeyConstraint", "sql": null, "columns": ["request_id"]}, {"name": "pk_payout_bank_references", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_payout_bank_references_request_id", "columns": ["request_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_windows

- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; required.
- `capacity`: INTEGER; required.
- `reserved`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_delivery_windows_window_capacity", "type": "CheckConstraint", "sql": "ends_at > starts_at AND capacity >= 0 AND reserved BETWEEN 0 AND capacity", "columns": []}, {"name": "fk_delivery_windows_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_delivery_windows", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_windows_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_vehicle_assignments

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `vehicle_id`: UUID; required; FK → fulfillment.pilot_vehicles.id (RESTRICT).
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_pilot_vehicle_assignments_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pilot_vehicle_assignments_vehicle_id_pilot_vehicles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["vehicle_id"]}, {"name": "pk_pilot_vehicle_assignments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_vehicle_assignments_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_vehicle_assignments_vehicle_id", "columns": ["vehicle_id"], "unique": false, "predicate": "None"}].

## fulfillment.route_optimization_runs

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `route_id`: UUID; required; FK → fulfillment.delivery_routes.id (RESTRICT).
- `strategy`: TEXT; required.
- `input_hash`: TEXT; required.
- `result`: JSONB; required.

Constraints: [{"name": "fk_route_optimization_runs_route_id_delivery_routes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["route_id"]}, {"name": "pk_route_optimization_runs", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_route_optimization_runs_route_id", "columns": ["route_id"], "unique": false, "predicate": "None"}].

## fulfillment.scheduled_order_occurrences

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `plan_id`: UUID; required; FK → fulfillment.recurring_order_plans.id (RESTRICT).
- `scheduled_at`: TIMESTAMP WITH TIME ZONE; required.
- `order_id`: UUID; nullable; FK → commerce.orders.id (RESTRICT).
- `status`: TEXT; required.
- `revalidation_reason`: TEXT; nullable.

Constraints: [{"name": "fk_scheduled_order_occurrences_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_scheduled_order_occurrences_plan_id_recurring_order_plans", "type": "ForeignKeyConstraint", "sql": null, "columns": ["plan_id"]}, {"name": "pk_scheduled_order_occurrences", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_scheduled_order_occurrences_plan_id", "type": "UniqueConstraint", "sql": null, "columns": ["plan_id", "scheduled_at"]}].
Indexes: [{"name": "ix_scheduled_order_occurrences_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_scheduled_order_occurrences_plan_id", "columns": ["plan_id"], "unique": false, "predicate": "None"}].

## identity.user_role_assignments

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `role_id`: UUID; required; FK → identity.roles.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `city_id`: UUID; nullable; FK → geo.cities.id (RESTRICT).
- `branch_id`: UUID; nullable; FK → merchant.merchant_branches.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_user_role_assignments_scoped_assignment", "type": "CheckConstraint", "sql": "(city_id IS NULL AND branch_id IS NULL) OR organization_id IS NOT NULL", "columns": []}, {"name": "fk_user_role_assignments_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_user_role_assignments_city_id_cities", "type": "ForeignKeyConstraint", "sql": null, "columns": ["city_id"]}, {"name": "fk_user_role_assignments_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_user_role_assignments_role_id_roles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["role_id"]}, {"name": "fk_user_role_assignments_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_user_role_assignments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_user_role_assignments_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id", "role_id", "organization_id", "city_id", "branch_id"]}].
Indexes: [{"name": "ix_user_role_assignments_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_user_role_assignments_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## integration.webhook_delivery_attempts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `subscription_id`: UUID; required; FK → integration.integration_webhook_subscriptions.id (RESTRICT).
- `outbox_event_id`: UUID; required; FK → integration.outbox_events.id (RESTRICT).
- `attempt`: INTEGER; required.
- `response_code`: INTEGER; nullable.

Constraints: [{"name": "fk_webhook_delivery_attempts_outbox_event_id_outbox_events", "type": "ForeignKeyConstraint", "sql": null, "columns": ["outbox_event_id"]}, {"name": "fk_webhook_delivery_attempts_subscription_id_integration_webhook_subscriptions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["subscription_id"]}, {"name": "pk_webhook_delivery_attempts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_webhook_delivery_attempts_outbox_event_id", "columns": ["outbox_event_id"], "unique": false, "predicate": "None"}, {"name": "ix_webhook_delivery_attempts_subscription_id", "columns": ["subscription_id"], "unique": false, "predicate": "None"}].

## intelligence.ai_agent_action_approvals

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `tool_call_id`: UUID; required; FK → intelligence.ai_agent_tool_calls.id (RESTRICT).
- `approver_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `decision`: TEXT; required.

Constraints: [{"name": "fk_ai_agent_action_approvals_approver_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["approver_id"]}, {"name": "fk_ai_agent_action_approvals_tool_call_id_ai_agent_tool_calls", "type": "ForeignKeyConstraint", "sql": null, "columns": ["tool_call_id"]}, {"name": "pk_ai_agent_action_approvals", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ai_agent_action_approvals_approver_id", "columns": ["approver_id"], "unique": false, "predicate": "None"}, {"name": "ix_ai_agent_action_approvals_tool_call_id", "columns": ["tool_call_id"], "unique": false, "predicate": "None"}].

## inventory.inventory_locations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `name`: TEXT; required.

Constraints: [{"name": "fk_inventory_locations_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_inventory_locations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_inventory_locations_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id", "name"]}].
Indexes: [{"name": "ix_inventory_locations_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## inventory.inventory_policy_settings

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `allow_backorders`: BOOLEAN; required.
- `reservation_ttl_seconds`: INTEGER; required.

Constraints: [{"name": "ck_inventory_policy_settings_rule_0", "type": "CheckConstraint", "sql": "reservation_ttl_seconds BETWEEN 60 AND 86400", "columns": []}, {"name": "fk_inventory_policy_settings_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_inventory_policy_settings", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_inventory_policy_settings_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id"]}].
Indexes: [{"name": "ix_inventory_policy_settings_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## inventory.stock_balances

- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `on_hand`: NUMERIC(20, 4); required.
- `reserved`: NUMERIC(20, 4); required.
- `version`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_stock_balances_sellable_stock", "type": "CheckConstraint", "sql": "on_hand >= 0 AND reserved >= 0 AND reserved <= on_hand", "columns": []}, {"name": "fk_stock_balances_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_stock_balances_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_stock_balances", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_stock_balances_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id", "variant_id"]}].
Indexes: [{"name": "ix_stock_balances_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_commission_agreements

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `contract_id`: UUID; required; FK → merchant.merchant_contracts.id (RESTRICT).
- `rate`: NUMERIC(20, 4); required.
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "ck_merchant_commission_agreements_rule_0", "type": "CheckConstraint", "sql": "rate BETWEEN 0 AND 1", "columns": []}, {"name": "fk_merchant_commission_agreements_contract_id_merchant_contracts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["contract_id"]}, {"name": "pk_merchant_commission_agreements", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_commission_agreements_contract_id", "columns": ["contract_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_fulfillment_capabilities

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `method`: TEXT; required.
- `active`: BOOLEAN; required.

Constraints: [{"name": "fk_merchant_fulfillment_capabilities_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_merchant_fulfillment_capabilities", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_fulfillment_capabilities_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id", "method"]}].
Indexes: [{"name": "ix_merchant_fulfillment_capabilities_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_onboarding_reviews

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `reviewer_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `decision`: TEXT; required.
- `safe_reason`: TEXT; required.

Constraints: [{"name": "fk_merchant_onboarding_reviews_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_merchant_onboarding_reviews_reviewer_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reviewer_id"]}, {"name": "pk_merchant_onboarding_reviews", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_onboarding_reviews_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_onboarding_reviews_reviewer_id", "columns": ["reviewer_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_operating_hours

- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `weekday`: INTEGER; required.
- `opens_at`: TIME WITHOUT TIME ZONE; required.
- `closes_at`: TIME WITHOUT TIME ZONE; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_merchant_operating_hours_valid_hours", "type": "CheckConstraint", "sql": "weekday BETWEEN 0 AND 6 AND opens_at < closes_at", "columns": []}, {"name": "fk_merchant_operating_hours_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_merchant_operating_hours", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_operating_hours_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id", "weekday", "opens_at"]}].
Indexes: [{"name": "ix_merchant_operating_hours_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_service_areas

- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `area_id`: UUID; required; FK → geo.delivery_service_areas.id (RESTRICT).
- `category_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).
- `delivery_method`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_merchant_service_areas_area_id_delivery_service_areas", "type": "ForeignKeyConstraint", "sql": null, "columns": ["area_id"]}, {"name": "fk_merchant_service_areas_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_merchant_service_areas_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "pk_merchant_service_areas", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_service_areas_branch_id", "type": "UniqueConstraint", "sql": null, "columns": ["branch_id", "area_id", "category_id", "delivery_method"]}].
Indexes: [{"name": "ix_merchant_service_areas_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_special_hours

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `local_date`: DATE; required.
- `opens_at`: TIME WITHOUT TIME ZONE; required.
- `closes_at`: TIME WITHOUT TIME ZONE; required.

Constraints: [{"name": "ck_merchant_special_hours_rule_0", "type": "CheckConstraint", "sql": "opens_at < closes_at", "columns": []}, {"name": "fk_merchant_special_hours_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_merchant_special_hours", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_special_hours_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_staff

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `branch_id`: UUID; nullable; FK → merchant.merchant_branches.id (RESTRICT).
- `active`: BOOLEAN; required.

Constraints: [{"name": "fk_merchant_staff_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_merchant_staff_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_merchant_staff_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_merchant_staff", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_staff_organization_id", "type": "UniqueConstraint", "sql": null, "columns": ["organization_id", "user_id", "branch_id"]}].
Indexes: [{"name": "ix_merchant_staff_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_staff_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_staff_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_status_history

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `previous`: TEXT; required.
- `current`: TEXT; required.

Constraints: [{"name": "fk_merchant_status_history_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_merchant_status_history_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_merchant_status_history", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_status_history_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_status_history_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## merchant.merchant_temporary_closures

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `starts_at`: TIMESTAMP WITH TIME ZONE; required.
- `ends_at`: TIMESTAMP WITH TIME ZONE; required.
- `reason`: TEXT; required.

Constraints: [{"name": "ck_merchant_temporary_closures_rule_0", "type": "CheckConstraint", "sql": "ends_at > starts_at", "columns": []}, {"name": "fk_merchant_temporary_closures_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "pk_merchant_temporary_closures", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_temporary_closures_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}].

## operations.refund_approval_requests

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `requested_by`: UUID; required; FK → identity.users.id (RESTRICT).
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_refund_approval_requests_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_refund_approval_requests_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_refund_approval_requests_requested_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["requested_by"]}, {"name": "pk_refund_approval_requests", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_refund_approval_requests_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_refund_approval_requests_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}, {"name": "ix_refund_approval_requests_requested_by", "columns": ["requested_by"], "unique": false, "predicate": "None"}].

## operations.support_tickets

- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `order_id`: UUID; nullable; FK → commerce.orders.id (RESTRICT).
- `organization_id`: UUID; nullable; FK → identity.organizations.id (RESTRICT).
- `subject`: TEXT; required.
- `status`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_support_tickets_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_support_tickets_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "fk_support_tickets_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_support_tickets", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_support_tickets_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## catalog.catalog_sections

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `catalog_id`: UUID; required; FK → catalog.merchant_catalogs.id (RESTRICT).
- `name`: TEXT; required.
- `sort_order`: INTEGER; required.

Constraints: [{"name": "fk_catalog_sections_catalog_id_merchant_catalogs", "type": "ForeignKeyConstraint", "sql": null, "columns": ["catalog_id"]}, {"name": "pk_catalog_sections", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_catalog_sections_catalog_id", "columns": ["catalog_id"], "unique": false, "predicate": "None"}].

## commerce.cart_items

- `cart_id`: UUID; required; FK → commerce.carts.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `quantity`: NUMERIC(20, 4); required.
- `address_id`: UUID; nullable; FK → geo.addresses.id (RESTRICT).
- `window_id`: UUID; required; FK → fulfillment.delivery_windows.id (RESTRICT).
- `delivery_method`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_cart_items_positive_quantity", "type": "CheckConstraint", "sql": "quantity > 0", "columns": []}, {"name": "fk_cart_items_address_id_addresses", "type": "ForeignKeyConstraint", "sql": null, "columns": ["address_id"]}, {"name": "fk_cart_items_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_cart_items_cart_id_carts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["cart_id"]}, {"name": "fk_cart_items_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "fk_cart_items_window_id_delivery_windows", "type": "ForeignKeyConstraint", "sql": null, "columns": ["window_id"]}, {"name": "pk_cart_items", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_cart_items_cart_id", "columns": ["cart_id"], "unique": false, "predicate": "None"}].

## commerce.order_cancellations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `merchant_order_id`: UUID; nullable; FK → commerce.merchant_orders.id (RESTRICT).
- `reason_id`: UUID; nullable; FK → commerce.cancellation_reasons.id (RESTRICT).
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `refund_required`: BOOLEAN; required.

Constraints: [{"name": "fk_order_cancellations_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_order_cancellations_merchant_order_id_merchant_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["merchant_order_id"]}, {"name": "fk_order_cancellations_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_order_cancellations_reason_id_cancellation_reasons", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reason_id"]}, {"name": "pk_order_cancellations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_cancellations_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_cancellations_merchant_order_id", "columns": ["merchant_order_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_cancellations_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_cancellations_reason_id", "columns": ["reason_id"], "unique": false, "predicate": "None"}].

## commerce.order_status_history

- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `merchant_order_id`: UUID; nullable; FK → commerce.merchant_orders.id (RESTRICT).
- `previous`: TEXT; nullable.
- `current`: TEXT; required.
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_order_status_history_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_order_status_history_merchant_order_id_merchant_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["merchant_order_id"]}, {"name": "fk_order_status_history_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_order_status_history", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_status_history_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## finance.invoice_lines

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `invoice_id`: UUID; required; FK → finance.invoices.id (RESTRICT).
- `description`: TEXT; required.
- `quantity`: NUMERIC(20, 4); required.
- `unit_price`: NUMERIC(20, 4); required.
- `total`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_invoice_lines_invoice_id_invoices", "type": "ForeignKeyConstraint", "sql": null, "columns": ["invoice_id"]}, {"name": "pk_invoice_lines", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_invoice_lines_invoice_id", "columns": ["invoice_id"], "unique": false, "predicate": "None"}].

## finance.journal_lines

- `journal_id`: UUID; required; FK → finance.journal_entries.id (RESTRICT).
- `organization_id`: UUID; required; FK → finance.journal_entries.organization_id (RESTRICT); FK → finance.ledger_accounts.organization_id (RESTRICT).
- `account_id`: UUID; required; FK → finance.ledger_accounts.id (RESTRICT).
- `currency`: VARCHAR(3); required; FK → finance.ledger_accounts.currency (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_journal_lines_nonzero_line", "type": "CheckConstraint", "sql": "amount <> 0", "columns": []}, {"name": "fk_journal_lines_account_id_ledger_accounts", "type": "ForeignKeyConstraint", "sql": null, "columns": ["account_id", "organization_id", "currency"]}, {"name": "fk_journal_lines_journal_id_journal_entries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["journal_id", "organization_id"]}, {"name": "pk_journal_lines", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_journal_lines_journal_id", "columns": ["journal_id"], "unique": false, "predicate": "None"}].

## finance.merchant_payables

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `organization_id`: UUID; required; FK → identity.organizations.id (RESTRICT).
- `merchant_order_id`: UUID; required; FK → commerce.merchant_orders.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_merchant_payables_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_merchant_payables_merchant_order_id_merchant_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["merchant_order_id"]}, {"name": "fk_merchant_payables_organization_id_organizations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["organization_id"]}, {"name": "pk_merchant_payables", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_merchant_payables_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_payables_merchant_order_id", "columns": ["merchant_order_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_payables_organization_id", "columns": ["organization_id"], "unique": false, "predicate": "None"}].

## finance.payment_attempts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `payment_id`: UUID; required; FK → finance.payment_intents.id (RESTRICT).
- `idempotency_key`: TEXT; required.
- `status`: TEXT; required.
- `provider_reference`: TEXT; nullable.

Constraints: [{"name": "fk_payment_attempts_payment_id_payment_intents", "type": "ForeignKeyConstraint", "sql": null, "columns": ["payment_id"]}, {"name": "pk_payment_attempts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_payment_attempts_payment_id", "type": "UniqueConstraint", "sql": null, "columns": ["payment_id", "idempotency_key"]}].
Indexes: [{"name": "ix_payment_attempts_payment_id", "columns": ["payment_id"], "unique": false, "predicate": "None"}].

## finance.payment_authorizations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `payment_id`: UUID; required; FK → finance.payment_intents.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `provider_reference`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_payment_authorizations_payment_id_payment_intents", "type": "ForeignKeyConstraint", "sql": null, "columns": ["payment_id"]}, {"name": "pk_payment_authorizations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_payment_authorizations_payment_id", "columns": ["payment_id"], "unique": false, "predicate": "None"}].

## finance.payment_captures

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `payment_id`: UUID; required; FK → finance.payment_intents.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `provider_reference`: TEXT; required.

Constraints: [{"name": "fk_payment_captures_payment_id_payment_intents", "type": "ForeignKeyConstraint", "sql": null, "columns": ["payment_id"]}, {"name": "pk_payment_captures", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_payment_captures_provider_reference", "type": "UniqueConstraint", "sql": null, "columns": ["provider_reference"]}].
Indexes: [{"name": "ix_payment_captures_payment_id", "columns": ["payment_id"], "unique": false, "predicate": "None"}].

## finance.payment_reconciliations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `payment_id`: UUID; required; FK → finance.payment_intents.id (RESTRICT).
- `provider_reference`: TEXT; required.
- `amount`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_payment_reconciliations_payment_id_payment_intents", "type": "ForeignKeyConstraint", "sql": null, "columns": ["payment_id"]}, {"name": "pk_payment_reconciliations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_payment_reconciliations_payment_id", "columns": ["payment_id"], "unique": false, "predicate": "None"}].

## finance.payment_refunds

- `payment_id`: UUID; required; FK → finance.payment_intents.id (RESTRICT).
- `approval_id`: UUID; nullable; FK → operations.refund_approval_requests.id (RESTRICT).
- `idempotency_key`: TEXT; required.
- `amount`: NUMERIC(20, 4); required.
- `status`: TEXT; required.
- `provider_reference`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_payment_refunds_positive_refund", "type": "CheckConstraint", "sql": "amount > 0", "columns": []}, {"name": "fk_payment_refunds_approval_id_refund_approval_requests", "type": "ForeignKeyConstraint", "sql": null, "columns": ["approval_id"]}, {"name": "fk_payment_refunds_payment_id_payment_intents", "type": "ForeignKeyConstraint", "sql": null, "columns": ["payment_id"]}, {"name": "pk_payment_refunds", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_payment_refunds_approval_id", "type": "UniqueConstraint", "sql": null, "columns": ["approval_id"]}, {"name": "uq_payment_refunds_payment_id", "type": "UniqueConstraint", "sql": null, "columns": ["payment_id", "idempotency_key"]}, {"name": "uq_payment_refunds_provider_reference", "type": "UniqueConstraint", "sql": null, "columns": ["provider_reference"]}].
Indexes: [].

## finance.payment_webhook_events

- `provider`: TEXT; required.
- `event_id`: TEXT; required.
- `payment_id`: UUID; required; FK → finance.payment_intents.id (RESTRICT).
- `payload_hash`: TEXT; required.
- `processed_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_payment_webhook_events_payment_id_payment_intents", "type": "ForeignKeyConstraint", "sql": null, "columns": ["payment_id"]}, {"name": "pk_payment_webhook_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_payment_webhook_events_provider", "type": "UniqueConstraint", "sql": null, "columns": ["provider", "event_id"]}].
Indexes: [].

## finance.settlement_lines

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `batch_id`: UUID; required; FK → finance.settlement_batches.id (RESTRICT).
- `journal_id`: UUID; required; FK → finance.journal_entries.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `payee_reference`: TEXT; required.

Constraints: [{"name": "fk_settlement_lines_batch_id_settlement_batches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["batch_id"]}, {"name": "fk_settlement_lines_journal_id_journal_entries", "type": "ForeignKeyConstraint", "sql": null, "columns": ["journal_id"]}, {"name": "pk_settlement_lines", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_settlement_lines_batch_id", "columns": ["batch_id"], "unique": false, "predicate": "None"}, {"name": "ix_settlement_lines_journal_id", "columns": ["journal_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_slot_capacity

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `window_id`: UUID; required; FK → fulfillment.delivery_windows.id (RESTRICT).
- `category_id`: UUID; required; FK → catalog.product_categories.id (RESTRICT).
- `capacity`: INTEGER; required.

Constraints: [{"name": "ck_delivery_slot_capacity_rule_0", "type": "CheckConstraint", "sql": "capacity >= 0", "columns": []}, {"name": "fk_delivery_slot_capacity_category_id_product_categories", "type": "ForeignKeyConstraint", "sql": null, "columns": ["category_id"]}, {"name": "fk_delivery_slot_capacity_window_id_delivery_windows", "type": "ForeignKeyConstraint", "sql": null, "columns": ["window_id"]}, {"name": "pk_delivery_slot_capacity", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_delivery_slot_capacity_window_id", "type": "UniqueConstraint", "sql": null, "columns": ["window_id", "category_id"]}].
Indexes: [{"name": "ix_delivery_slot_capacity_category_id", "columns": ["category_id"], "unique": false, "predicate": "None"}, {"name": "ix_delivery_slot_capacity_window_id", "columns": ["window_id"], "unique": false, "predicate": "None"}].

## fulfillment.fulfillment_units

- `merchant_order_id`: UUID; required; FK → commerce.merchant_orders.id (RESTRICT).
- `window_id`: UUID; required; FK → fulfillment.delivery_windows.id (RESTRICT).
- `delivery_method`: TEXT; required.
- `address_snapshot`: JSONB; nullable.
- `status`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_fulfillment_units_merchant_order_id_merchant_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["merchant_order_id"]}, {"name": "fk_fulfillment_units_window_id_delivery_windows", "type": "ForeignKeyConstraint", "sql": null, "columns": ["window_id"]}, {"name": "pk_fulfillment_units", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_fulfillment_units_merchant_order_id", "columns": ["merchant_order_id"], "unique": false, "predicate": "None"}].

## fulfillment.scheduled_orders

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `window_id`: UUID; required; FK → fulfillment.delivery_windows.id (RESTRICT).
- `revalidate_at`: TIMESTAMP WITH TIME ZONE; required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_scheduled_orders_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "fk_scheduled_orders_window_id_delivery_windows", "type": "ForeignKeyConstraint", "sql": null, "columns": ["window_id"]}, {"name": "pk_scheduled_orders", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_scheduled_orders_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}, {"name": "ix_scheduled_orders_window_id", "columns": ["window_id"], "unique": false, "predicate": "None"}].

## fulfillment.scheduling_job_records

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `occurrence_id`: UUID; required; FK → fulfillment.scheduled_order_occurrences.id (RESTRICT).
- `attempts`: INTEGER; required.
- `available_at`: TIMESTAMP WITH TIME ZONE; required.
- `locked_until`: TIMESTAMP WITH TIME ZONE; nullable.
- `completed_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_scheduling_job_records_occurrence_id_scheduled_order_occurrences", "type": "ForeignKeyConstraint", "sql": null, "columns": ["occurrence_id"]}, {"name": "pk_scheduling_job_records", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_scheduling_job_records_occurrence_id", "type": "UniqueConstraint", "sql": null, "columns": ["occurrence_id"]}].
Indexes: [{"name": "ix_scheduling_job_records_occurrence_id", "columns": ["occurrence_id"], "unique": false, "predicate": "None"}].

## inventory.inventory_alerts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `stock_id`: UUID; required; FK → inventory.stock_balances.id (RESTRICT).
- `kind`: TEXT; required.
- `resolved_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_inventory_alerts_stock_id_stock_balances", "type": "ForeignKeyConstraint", "sql": null, "columns": ["stock_id"]}, {"name": "pk_inventory_alerts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_inventory_alerts_stock_id", "columns": ["stock_id"], "unique": false, "predicate": "None"}].

## inventory.inventory_items

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `location_id`: UUID; required; FK → inventory.inventory_locations.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).

Constraints: [{"name": "fk_inventory_items_location_id_inventory_locations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["location_id"]}, {"name": "fk_inventory_items_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_inventory_items", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_inventory_items_location_id", "type": "UniqueConstraint", "sql": null, "columns": ["location_id", "variant_id"]}].
Indexes: [{"name": "ix_inventory_items_location_id", "columns": ["location_id"], "unique": false, "predicate": "None"}, {"name": "ix_inventory_items_variant_id", "columns": ["variant_id"], "unique": false, "predicate": "None"}].

## inventory.stock_batches

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `stock_id`: UUID; required; FK → inventory.stock_balances.id (RESTRICT).
- `lot_code`: TEXT; required.
- `quantity`: NUMERIC(20, 4); required.
- `reserved`: NUMERIC(20, 4); required.
- `received_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "ck_stock_batches_rule_0", "type": "CheckConstraint", "sql": "quantity >= 0", "columns": []}, {"name": "ck_stock_batches_rule_1", "type": "CheckConstraint", "sql": "reserved BETWEEN 0 AND quantity", "columns": []}, {"name": "fk_stock_batches_stock_id_stock_balances", "type": "ForeignKeyConstraint", "sql": null, "columns": ["stock_id"]}, {"name": "pk_stock_batches", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_stock_batches_stock_id", "type": "UniqueConstraint", "sql": null, "columns": ["stock_id", "lot_code"]}].
Indexes: [{"name": "ix_stock_batches_stock_id", "columns": ["stock_id"], "unique": false, "predicate": "None"}].

## inventory.stock_count_sessions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `location_id`: UUID; required; FK → inventory.inventory_locations.id (RESTRICT).
- `started_by`: UUID; required; FK → identity.users.id (RESTRICT).
- `completed_at`: TIMESTAMP WITH TIME ZONE; nullable.
- `status`: TEXT; required.

Constraints: [{"name": "fk_stock_count_sessions_location_id_inventory_locations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["location_id"]}, {"name": "fk_stock_count_sessions_started_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["started_by"]}, {"name": "pk_stock_count_sessions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_stock_count_sessions_location_id", "columns": ["location_id"], "unique": false, "predicate": "None"}, {"name": "ix_stock_count_sessions_started_by", "columns": ["started_by"], "unique": false, "predicate": "None"}].

## merchant.merchant_staff_roles

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `staff_id`: UUID; required; FK → merchant.merchant_staff.id (RESTRICT).
- `role_id`: UUID; required; FK → identity.roles.id (RESTRICT).

Constraints: [{"name": "fk_merchant_staff_roles_role_id_roles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["role_id"]}, {"name": "fk_merchant_staff_roles_staff_id_merchant_staff", "type": "ForeignKeyConstraint", "sql": null, "columns": ["staff_id"]}, {"name": "pk_merchant_staff_roles", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_merchant_staff_roles_staff_id", "type": "UniqueConstraint", "sql": null, "columns": ["staff_id", "role_id"]}].
Indexes: [{"name": "ix_merchant_staff_roles_role_id", "columns": ["role_id"], "unique": false, "predicate": "None"}, {"name": "ix_merchant_staff_roles_staff_id", "columns": ["staff_id"], "unique": false, "predicate": "None"}].

## operations.refund_approval_decisions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `request_id`: UUID; required; FK → operations.refund_approval_requests.id (RESTRICT).
- `decided_by`: UUID; required; FK → identity.users.id (RESTRICT).
- `decision`: TEXT; required.
- `reason`: TEXT; required.

Constraints: [{"name": "fk_refund_approval_decisions_decided_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["decided_by"]}, {"name": "fk_refund_approval_decisions_request_id_refund_approval_requests", "type": "ForeignKeyConstraint", "sql": null, "columns": ["request_id"]}, {"name": "pk_refund_approval_decisions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_refund_approval_decisions_decided_by", "columns": ["decided_by"], "unique": false, "predicate": "None"}, {"name": "ix_refund_approval_decisions_request_id", "columns": ["request_id"], "unique": false, "predicate": "None"}].

## operations.support_escalations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `ticket_id`: UUID; required; FK → operations.support_tickets.id (RESTRICT).
- `raised_by`: UUID; required; FK → identity.users.id (RESTRICT).
- `reason`: TEXT; required.
- `resolved_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_support_escalations_raised_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["raised_by"]}, {"name": "fk_support_escalations_ticket_id_support_tickets", "type": "ForeignKeyConstraint", "sql": null, "columns": ["ticket_id"]}, {"name": "pk_support_escalations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_support_escalations_raised_by", "columns": ["raised_by"], "unique": false, "predicate": "None"}, {"name": "ix_support_escalations_ticket_id", "columns": ["ticket_id"], "unique": false, "predicate": "None"}].

## operations.support_ticket_messages

- `ticket_id`: UUID; required; FK → operations.support_tickets.id (RESTRICT).
- `author_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `body`: TEXT; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_support_ticket_messages_author_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["author_id"]}, {"name": "fk_support_ticket_messages_ticket_id_support_tickets", "type": "ForeignKeyConstraint", "sql": null, "columns": ["ticket_id"]}, {"name": "pk_support_ticket_messages", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_support_ticket_messages_ticket_id", "columns": ["ticket_id"], "unique": false, "predicate": "None"}].

## operations.ticket_assignments

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `ticket_id`: UUID; required; FK → operations.support_tickets.id (RESTRICT).
- `agent_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `assigned_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_ticket_assignments_agent_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["agent_id"]}, {"name": "fk_ticket_assignments_ticket_id_support_tickets", "type": "ForeignKeyConstraint", "sql": null, "columns": ["ticket_id"]}, {"name": "pk_ticket_assignments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_ticket_assignments_agent_id", "columns": ["agent_id"], "unique": false, "predicate": "None"}, {"name": "ix_ticket_assignments_ticket_id", "columns": ["ticket_id"], "unique": false, "predicate": "None"}].

## commerce.cart_item_options

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `cart_item_id`: UUID; required; FK → commerce.cart_items.id (RESTRICT).
- `option_id`: UUID; required; FK → catalog.option_values.id (RESTRICT).
- `quantity`: INTEGER; required.

Constraints: [{"name": "ck_cart_item_options_rule_0", "type": "CheckConstraint", "sql": "quantity > 0", "columns": []}, {"name": "fk_cart_item_options_cart_item_id_cart_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["cart_item_id"]}, {"name": "fk_cart_item_options_option_id_option_values", "type": "ForeignKeyConstraint", "sql": null, "columns": ["option_id"]}, {"name": "pk_cart_item_options", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_cart_item_options_cart_item_id", "type": "UniqueConstraint", "sql": null, "columns": ["cart_item_id", "option_id"]}].
Indexes: [{"name": "ix_cart_item_options_cart_item_id", "columns": ["cart_item_id"], "unique": false, "predicate": "None"}, {"name": "ix_cart_item_options_option_id", "columns": ["option_id"], "unique": false, "predicate": "None"}].

## commerce.checkout_quote_lines

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `quote_id`: UUID; required; FK → commerce.checkout_quotes.id (RESTRICT).
- `cart_item_id`: UUID; required; FK → commerce.cart_items.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `snapshot`: JSONB; required.

Constraints: [{"name": "fk_checkout_quote_lines_cart_item_id_cart_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["cart_item_id"]}, {"name": "fk_checkout_quote_lines_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_checkout_quote_lines_quote_id_checkout_quotes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["quote_id"]}, {"name": "pk_checkout_quote_lines", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_checkout_quote_lines_cart_item_id", "columns": ["cart_item_id"], "unique": false, "predicate": "None"}, {"name": "ix_checkout_quote_lines_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_checkout_quote_lines_quote_id", "columns": ["quote_id"], "unique": false, "predicate": "None"}].

## commerce.order_addresses

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_id`: UUID; required; FK → commerce.orders.id (RESTRICT).
- `fulfillment_unit_id`: UUID; required; FK → fulfillment.fulfillment_units.id (RESTRICT).
- `kind`: TEXT; required.
- `snapshot`: JSONB; required.

Constraints: [{"name": "fk_order_addresses_fulfillment_unit_id_fulfillment_units", "type": "ForeignKeyConstraint", "sql": null, "columns": ["fulfillment_unit_id"]}, {"name": "fk_order_addresses_order_id_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_id"]}, {"name": "pk_order_addresses", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_addresses_fulfillment_unit_id", "columns": ["fulfillment_unit_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_addresses_order_id", "columns": ["order_id"], "unique": false, "predicate": "None"}].

## commerce.order_items

- `merchant_order_id`: UUID; required; FK → commerce.merchant_orders.id (RESTRICT).
- `fulfillment_unit_id`: UUID; required; FK → fulfillment.fulfillment_units.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `product_name`: TEXT; required.
- `variant_name`: TEXT; required.
- `unit`: TEXT; required.
- `quantity`: NUMERIC(20, 4); required.
- `unit_price`: NUMERIC(20, 4); required.
- `total`: NUMERIC(20, 4); required.
- `snapshot`: JSONB; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_order_items_order_item_amounts", "type": "CheckConstraint", "sql": "quantity > 0 AND unit_price >= 0 AND total >= 0", "columns": []}, {"name": "fk_order_items_fulfillment_unit_id_fulfillment_units", "type": "ForeignKeyConstraint", "sql": null, "columns": ["fulfillment_unit_id"]}, {"name": "fk_order_items_merchant_order_id_merchant_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["merchant_order_id"]}, {"name": "fk_order_items_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_order_items", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_items_fulfillment_unit_id", "columns": ["fulfillment_unit_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_items_merchant_order_id", "columns": ["merchant_order_id"], "unique": false, "predicate": "None"}].

## finance.credit_notes

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `invoice_id`: UUID; required; FK → finance.invoices.id (RESTRICT).
- `refund_id`: UUID; nullable; FK → finance.payment_refunds.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `reason`: TEXT; required.

Constraints: [{"name": "fk_credit_notes_invoice_id_invoices", "type": "ForeignKeyConstraint", "sql": null, "columns": ["invoice_id"]}, {"name": "fk_credit_notes_refund_id_payment_refunds", "type": "ForeignKeyConstraint", "sql": null, "columns": ["refund_id"]}, {"name": "pk_credit_notes", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_credit_notes_invoice_id", "columns": ["invoice_id"], "unique": false, "predicate": "None"}, {"name": "ix_credit_notes_refund_id", "columns": ["refund_id"], "unique": false, "predicate": "None"}].

## finance.refund_allocations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `refund_id`: UUID; required; FK → finance.payment_refunds.id (RESTRICT).
- `merchant_order_id`: UUID; required; FK → commerce.merchant_orders.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_refund_allocations_merchant_order_id_merchant_orders", "type": "ForeignKeyConstraint", "sql": null, "columns": ["merchant_order_id"]}, {"name": "fk_refund_allocations_refund_id_payment_refunds", "type": "ForeignKeyConstraint", "sql": null, "columns": ["refund_id"]}, {"name": "pk_refund_allocations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_refund_allocations_merchant_order_id", "columns": ["merchant_order_id"], "unique": false, "predicate": "None"}, {"name": "ix_refund_allocations_refund_id", "columns": ["refund_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_tasks

- `fulfillment_unit_id`: UUID; required; FK → fulfillment.fulfillment_units.id (RESTRICT).
- `status`: TEXT; required.
- `version`: INTEGER; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_delivery_tasks_fulfillment_unit_id_fulfillment_units", "type": "ForeignKeyConstraint", "sql": null, "columns": ["fulfillment_unit_id"]}, {"name": "pk_delivery_tasks", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_delivery_tasks_fulfillment_unit_id", "type": "UniqueConstraint", "sql": null, "columns": ["fulfillment_unit_id"]}].
Indexes: [].

## fulfillment.pilot_settlement_references

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `settlement_line_id`: UUID; required; FK → finance.settlement_lines.id (RESTRICT).

Constraints: [{"name": "fk_pilot_settlement_references_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pilot_settlement_references_settlement_line_id_settlement_lines", "type": "ForeignKeyConstraint", "sql": null, "columns": ["settlement_line_id"]}, {"name": "pk_pilot_settlement_references", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_settlement_references_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_settlement_references_settlement_line_id", "columns": ["settlement_line_id"], "unique": false, "predicate": "None"}].

## inventory.expiry_dates

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `batch_id`: UUID; required; FK → inventory.stock_batches.id (RESTRICT).
- `expires_on`: DATE; required.

Constraints: [{"name": "fk_expiry_dates_batch_id_stock_batches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["batch_id"]}, {"name": "pk_expiry_dates", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_expiry_dates_batch_id", "type": "UniqueConstraint", "sql": null, "columns": ["batch_id"]}].
Indexes: [{"name": "ix_expiry_dates_batch_id", "columns": ["batch_id"], "unique": false, "predicate": "None"}].

## inventory.stock_count_lines

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `session_id`: UUID; required; FK → inventory.stock_count_sessions.id (RESTRICT).
- `variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `counted`: NUMERIC(20, 4); required.

Constraints: [{"name": "ck_stock_count_lines_rule_0", "type": "CheckConstraint", "sql": "counted >= 0", "columns": []}, {"name": "fk_stock_count_lines_session_id_stock_count_sessions", "type": "ForeignKeyConstraint", "sql": null, "columns": ["session_id"]}, {"name": "fk_stock_count_lines_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["variant_id"]}, {"name": "pk_stock_count_lines", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_stock_count_lines_session_id", "type": "UniqueConstraint", "sql": null, "columns": ["session_id", "variant_id"]}].
Indexes: [{"name": "ix_stock_count_lines_session_id", "columns": ["session_id"], "unique": false, "predicate": "None"}, {"name": "ix_stock_count_lines_variant_id", "columns": ["variant_id"], "unique": false, "predicate": "None"}].

## commerce.order_item_options

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_item_id`: UUID; required; FK → commerce.order_items.id (RESTRICT).
- `name_snapshot`: TEXT; required.
- `amount`: NUMERIC(20, 4); required.
- `quantity`: INTEGER; required.

Constraints: [{"name": "ck_order_item_options_rule_0", "type": "CheckConstraint", "sql": "quantity > 0", "columns": []}, {"name": "fk_order_item_options_order_item_id_order_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_item_id"]}, {"name": "pk_order_item_options", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_item_options_order_item_id", "columns": ["order_item_id"], "unique": false, "predicate": "None"}].

## commerce.order_substitutions

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `order_item_id`: UUID; required; FK → commerce.order_items.id (RESTRICT).
- `replacement_variant_id`: UUID; required; FK → catalog.product_variants.id (RESTRICT).
- `approved_by`: UUID; required; FK → identity.users.id (RESTRICT).
- `price_difference`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_order_substitutions_approved_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["approved_by"]}, {"name": "fk_order_substitutions_order_item_id_order_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_item_id"]}, {"name": "fk_order_substitutions_replacement_variant_id_product_variants", "type": "ForeignKeyConstraint", "sql": null, "columns": ["replacement_variant_id"]}, {"name": "pk_order_substitutions", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_order_substitutions_approved_by", "columns": ["approved_by"], "unique": false, "predicate": "None"}, {"name": "ix_order_substitutions_order_item_id", "columns": ["order_item_id"], "unique": false, "predicate": "None"}, {"name": "ix_order_substitutions_replacement_variant_id", "columns": ["replacement_variant_id"], "unique": false, "predicate": "None"}].

## engagement.reviews

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `user_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `order_item_id`: UUID; required; FK → commerce.order_items.id (RESTRICT).
- `rating`: INTEGER; required.
- `body`: TEXT; required.
- `moderation_status`: TEXT; required.

Constraints: [{"name": "ck_reviews_rule_0", "type": "CheckConstraint", "sql": "rating BETWEEN 1 AND 5", "columns": []}, {"name": "fk_reviews_order_item_id_order_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_item_id"]}, {"name": "fk_reviews_user_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["user_id"]}, {"name": "pk_reviews", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_reviews_user_id", "type": "UniqueConstraint", "sql": null, "columns": ["user_id", "order_item_id"]}].
Indexes: [{"name": "ix_reviews_order_item_id", "columns": ["order_item_id"], "unique": false, "predicate": "None"}, {"name": "ix_reviews_user_id", "columns": ["user_id"], "unique": false, "predicate": "None"}].

## finance.pilot_payables

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "fk_pilot_payables_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_pilot_payables_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pilot_payables_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_pilot_payables", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_payables_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_payables_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_payables_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_attempts

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `outcome`: TEXT; required.
- `reason_id`: UUID; nullable; FK → fulfillment.failed_delivery_reasons.id (RESTRICT).

Constraints: [{"name": "fk_delivery_attempts_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_delivery_attempts_reason_id_failed_delivery_reasons", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reason_id"]}, {"name": "fk_delivery_attempts_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_delivery_attempts", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_attempts_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_delivery_attempts_reason_id", "columns": ["reason_id"], "unique": false, "predicate": "None"}, {"name": "ix_delivery_attempts_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_confirmations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `confirmed_at`: TIMESTAMP WITH TIME ZONE; required.
- `mode`: TEXT; required.

Constraints: [{"name": "fk_delivery_confirmations_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_delivery_confirmations_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_delivery_confirmations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_confirmations_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_delivery_confirmations_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_stops

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `address_snapshot`: JSONB; required.
- `position`: INTEGER; required.

Constraints: [{"name": "fk_delivery_stops_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_delivery_stops", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_stops_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.delivery_task_items

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `order_item_id`: UUID; required; FK → commerce.order_items.id (RESTRICT).
- `quantity`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_delivery_task_items_order_item_id_order_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_item_id"]}, {"name": "fk_delivery_task_items_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_delivery_task_items", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_task_items_order_item_id", "columns": ["order_item_id"], "unique": false, "predicate": "None"}, {"name": "ix_delivery_task_items_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.dispatch_events

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `event_type`: TEXT; required.
- `actor_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `strategy`: TEXT; required.

Constraints: [{"name": "fk_dispatch_events_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_dispatch_events_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_dispatch_events", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_dispatch_events_actor_id", "columns": ["actor_id"], "unique": false, "predicate": "None"}, {"name": "ix_dispatch_events_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.pickup_confirmations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `confirmed_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_pickup_confirmations_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pickup_confirmations_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_pickup_confirmations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pickup_confirmations_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pickup_confirmations_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.pickup_stops

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `branch_id`: UUID; required; FK → merchant.merchant_branches.id (RESTRICT).
- `position`: INTEGER; required.

Constraints: [{"name": "fk_pickup_stops_branch_id_merchant_branches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["branch_id"]}, {"name": "fk_pickup_stops_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_pickup_stops", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pickup_stops_branch_id", "columns": ["branch_id"], "unique": false, "predicate": "None"}, {"name": "ix_pickup_stops_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.pilot_assignments

- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `status`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_pilot_assignments_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pilot_assignments_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_pilot_assignments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_assignments_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_assignments_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}, {"name": "uq_active_task_assignment", "columns": ["task_id"], "unique": true, "predicate": "status IN ('offered','accepted','picked_up')"}].

## fulfillment.pilot_earnings

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `pilot_id`: UUID; required; FK → fulfillment.pilot_profiles.id (RESTRICT).
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `currency_id`: UUID; required; FK → finance.currencies.id (RESTRICT).
- `amount`: NUMERIC(20, 4); required.

Constraints: [{"name": "fk_pilot_earnings_currency_id_currencies", "type": "ForeignKeyConstraint", "sql": null, "columns": ["currency_id"]}, {"name": "fk_pilot_earnings_pilot_id_pilot_profiles", "type": "ForeignKeyConstraint", "sql": null, "columns": ["pilot_id"]}, {"name": "fk_pilot_earnings_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_pilot_earnings", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_pilot_earnings_currency_id", "columns": ["currency_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_earnings_pilot_id", "columns": ["pilot_id"], "unique": false, "predicate": "None"}, {"name": "ix_pilot_earnings_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.proof_of_delivery

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `mode`: TEXT; required.
- `private_object_key`: TEXT; nullable.
- `acknowledged_by`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_proof_of_delivery_acknowledged_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["acknowledged_by"]}, {"name": "fk_proof_of_delivery_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_proof_of_delivery", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_delivery_proof_retention", "columns": ["expires_at", "id"], "unique": false, "predicate": "None"}, {"name": "ix_proof_of_delivery_acknowledged_by", "columns": ["acknowledged_by"], "unique": false, "predicate": "None"}, {"name": "ix_proof_of_delivery_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## fulfillment.route_stops

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `route_id`: UUID; required; FK → fulfillment.delivery_routes.id (RESTRICT).
- `task_id`: UUID; required; FK → fulfillment.delivery_tasks.id (RESTRICT).
- `position`: INTEGER; required.
- `kind`: TEXT; required.

Constraints: [{"name": "fk_route_stops_route_id_delivery_routes", "type": "ForeignKeyConstraint", "sql": null, "columns": ["route_id"]}, {"name": "fk_route_stops_task_id_delivery_tasks", "type": "ForeignKeyConstraint", "sql": null, "columns": ["task_id"]}, {"name": "pk_route_stops", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_route_stops_route_id", "columns": ["route_id"], "unique": false, "predicate": "None"}, {"name": "ix_route_stops_task_id", "columns": ["task_id"], "unique": false, "predicate": "None"}].

## inventory.stock_reservations

- `stock_id`: UUID; required; FK → inventory.stock_balances.id (RESTRICT).
- `order_item_id`: UUID; required; FK → commerce.order_items.id (RESTRICT).
- `quantity`: NUMERIC(20, 4); required.
- `status`: TEXT; required.
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "ck_stock_reservations_positive_reservation", "type": "CheckConstraint", "sql": "quantity > 0", "columns": []}, {"name": "fk_stock_reservations_order_item_id_order_items", "type": "ForeignKeyConstraint", "sql": null, "columns": ["order_item_id"]}, {"name": "fk_stock_reservations_stock_id_stock_balances", "type": "ForeignKeyConstraint", "sql": null, "columns": ["stock_id"]}, {"name": "pk_stock_reservations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_stock_reservations_order_item_id", "type": "UniqueConstraint", "sql": null, "columns": ["order_item_id"]}].
Indexes: [{"name": "ix_stock_reservations_expires_at", "columns": ["expires_at"], "unique": false, "predicate": "None"}, {"name": "ix_stock_reservations_stock_id", "columns": ["stock_id"], "unique": false, "predicate": "None"}].

## engagement.review_media

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `review_id`: UUID; required; FK → engagement.reviews.id (RESTRICT).
- `private_object_key`: TEXT; required.

Constraints: [{"name": "fk_review_media_review_id_reviews", "type": "ForeignKeyConstraint", "sql": null, "columns": ["review_id"]}, {"name": "pk_review_media", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_review_media_review_id", "columns": ["review_id"], "unique": false, "predicate": "None"}].

## engagement.review_moderation

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `review_id`: UUID; required; FK → engagement.reviews.id (RESTRICT).
- `reviewer_id`: UUID; required; FK → identity.users.id (RESTRICT).
- `decision`: TEXT; required.

Constraints: [{"name": "fk_review_moderation_review_id_reviews", "type": "ForeignKeyConstraint", "sql": null, "columns": ["review_id"]}, {"name": "fk_review_moderation_reviewer_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reviewer_id"]}, {"name": "pk_review_moderation", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_review_moderation_review_id", "columns": ["review_id"], "unique": false, "predicate": "None"}, {"name": "ix_review_moderation_reviewer_id", "columns": ["reviewer_id"], "unique": false, "predicate": "None"}].

## fulfillment.assignment_offers

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `assignment_id`: UUID; required; FK → fulfillment.pilot_assignments.id (RESTRICT).
- `expires_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_assignment_offers_assignment_id_pilot_assignments", "type": "ForeignKeyConstraint", "sql": null, "columns": ["assignment_id"]}, {"name": "pk_assignment_offers", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_assignment_offers_assignment_id", "columns": ["assignment_id"], "unique": false, "predicate": "None"}].

## fulfillment.assignment_responses

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `assignment_id`: UUID; required; FK → fulfillment.pilot_assignments.id (RESTRICT).
- `response`: TEXT; required.
- `responded_at`: TIMESTAMP WITH TIME ZONE; required.

Constraints: [{"name": "fk_assignment_responses_assignment_id_pilot_assignments", "type": "ForeignKeyConstraint", "sql": null, "columns": ["assignment_id"]}, {"name": "pk_assignment_responses", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}].
Indexes: [{"name": "ix_assignment_responses_assignment_id", "columns": ["assignment_id"], "unique": false, "predicate": "None"}].

## inventory.batch_reservation_allocations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `reservation_id`: UUID; required; FK → inventory.stock_reservations.id (RESTRICT).
- `batch_id`: UUID; required; FK → inventory.stock_batches.id (RESTRICT).
- `quantity`: NUMERIC(20, 4); required.
- `status`: TEXT; required.

Constraints: [{"name": "ck_batch_reservation_allocations_rule_0", "type": "CheckConstraint", "sql": "quantity > 0", "columns": []}, {"name": "fk_batch_reservation_allocations_batch_id_stock_batches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["batch_id"]}, {"name": "fk_batch_reservation_allocations_reservation_id_stock_reservations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reservation_id"]}, {"name": "pk_batch_reservation_allocations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_batch_reservation_allocations_reservation_id", "type": "UniqueConstraint", "sql": null, "columns": ["reservation_id", "batch_id"]}].
Indexes: [{"name": "ix_batch_reservation_allocations_batch_id", "columns": ["batch_id"], "unique": false, "predicate": "None"}, {"name": "ix_batch_reservation_allocations_reservation_id", "columns": ["reservation_id"], "unique": false, "predicate": "None"}].

## inventory.reservation_expirations

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `reservation_id`: UUID; required; FK → inventory.stock_reservations.id (RESTRICT).
- `due_at`: TIMESTAMP WITH TIME ZONE; required.
- `processed_at`: TIMESTAMP WITH TIME ZONE; nullable.

Constraints: [{"name": "fk_reservation_expirations_reservation_id_stock_reservations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reservation_id"]}, {"name": "pk_reservation_expirations", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_reservation_expirations_reservation_id", "type": "UniqueConstraint", "sql": null, "columns": ["reservation_id"]}].
Indexes: [{"name": "ix_reservation_expirations_reservation_id", "columns": ["reservation_id"], "unique": false, "predicate": "None"}].

## inventory.stock_movements

- `stock_id`: UUID; required; FK → inventory.stock_balances.id (RESTRICT).
- `batch_id`: UUID; nullable; FK → inventory.stock_batches.id (RESTRICT).
- `reservation_id`: UUID; nullable; FK → inventory.stock_reservations.id (RESTRICT).
- `quantity`: NUMERIC(20, 4); required.
- `kind`: TEXT; required.
- `idempotency_key`: TEXT; required.
- `actor_id`: UUID; nullable; FK → identity.users.id (RESTRICT).
- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `updated_at`: TIMESTAMP WITH TIME ZONE; required; default now().

Constraints: [{"name": "fk_stock_movements_actor_id_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["actor_id"]}, {"name": "fk_stock_movements_batch_id_stock_batches", "type": "ForeignKeyConstraint", "sql": null, "columns": ["batch_id"]}, {"name": "fk_stock_movements_reservation_id_stock_reservations", "type": "ForeignKeyConstraint", "sql": null, "columns": ["reservation_id"]}, {"name": "fk_stock_movements_stock_id_stock_balances", "type": "ForeignKeyConstraint", "sql": null, "columns": ["stock_id"]}, {"name": "pk_stock_movements", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_stock_movements_idempotency_key", "type": "UniqueConstraint", "sql": null, "columns": ["idempotency_key"]}].
Indexes: [{"name": "ix_stock_movements_stock_id", "columns": ["stock_id"], "unique": false, "predicate": "None"}].

## inventory.stock_adjustments

- `id`: UUID; required; PK.
- `created_at`: TIMESTAMP WITH TIME ZONE; required; default now().
- `movement_id`: UUID; required; FK → inventory.stock_movements.id (RESTRICT).
- `reason`: TEXT; required.
- `approved_by`: UUID; required; FK → identity.users.id (RESTRICT).

Constraints: [{"name": "fk_stock_adjustments_approved_by_users", "type": "ForeignKeyConstraint", "sql": null, "columns": ["approved_by"]}, {"name": "fk_stock_adjustments_movement_id_stock_movements", "type": "ForeignKeyConstraint", "sql": null, "columns": ["movement_id"]}, {"name": "pk_stock_adjustments", "type": "PrimaryKeyConstraint", "sql": null, "columns": ["id"]}, {"name": "uq_stock_adjustments_movement_id", "type": "UniqueConstraint", "sql": null, "columns": ["movement_id"]}].
Indexes: [{"name": "ix_stock_adjustments_approved_by", "columns": ["approved_by"], "unique": false, "predicate": "None"}, {"name": "ix_stock_adjustments_movement_id", "columns": ["movement_id"], "unique": false, "predicate": "None"}].

## Database-only invariants

The deferred `finance.require_balanced_journal` constraint trigger is included in the total database constraint count in addition to ordinary ORM constraints. Full guard definitions are frozen in Alembic revisions 0001 and 0003. There are 57 user triggers, including posted-journal/line immutability, currency balance, scope, refund approval and append-only records.

