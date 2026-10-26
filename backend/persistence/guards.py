"""PostgreSQL invariants included verbatim in the frozen migration snapshot."""

GUARDS = [
    """CREATE FUNCTION finance.guard_ledger_book() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.organization_id IS DISTINCT FROM
         (SELECT organization_id FROM merchant.merchant_legal_entities WHERE id=NEW.legal_entity_id) THEN
        RAISE EXCEPTION 'Legal entity organization mismatch' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER ledger_book_scope BEFORE INSERT OR UPDATE ON finance.ledger_books
       FOR EACH ROW EXECUTE FUNCTION finance.guard_ledger_book()""",
    """CREATE FUNCTION finance.guard_posted_journal() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.status = 'posted' THEN
        RAISE EXCEPTION 'Posted journals are immutable' USING ERRCODE='23514';
      END IF;
      IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER guard_posted_journal BEFORE UPDATE OR DELETE ON finance.journal_entries
       FOR EACH ROW EXECUTE FUNCTION finance.guard_posted_journal()""",
    """CREATE FUNCTION finance.guard_journal_line() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE journal_status text; currency_scale integer;
    BEGIN
      IF TG_OP <> 'INSERT' THEN
        SELECT status INTO journal_status FROM finance.journal_entries WHERE id=OLD.journal_id FOR UPDATE;
        IF journal_status='posted' THEN
          RAISE EXCEPTION 'Posted journal lines are immutable' USING ERRCODE='23514';
        END IF;
      END IF;
      IF TG_OP <> 'DELETE' THEN
        IF (SELECT book_id FROM finance.ledger_accounts WHERE id=NEW.account_id)
           IS DISTINCT FROM (SELECT book_id FROM finance.journal_entries WHERE id=NEW.journal_id) THEN
          RAISE EXCEPTION 'Journal legal entity/currency book mismatch' USING ERRCODE='23514';
        END IF;
        SELECT status INTO journal_status FROM finance.journal_entries WHERE id=NEW.journal_id FOR UPDATE;
        IF journal_status='posted' THEN
          RAISE EXCEPTION 'Cannot add lines to a posted journal' USING ERRCODE='23514';
        END IF;
        SELECT scale INTO currency_scale FROM finance.currencies WHERE code=NEW.currency;
        IF NEW.amount <> round(NEW.amount,currency_scale) THEN
          RAISE EXCEPTION 'Invalid currency precision' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
      END IF;
      RETURN OLD;
    END $$""",
    """CREATE TRIGGER guard_journal_line BEFORE INSERT OR UPDATE OR DELETE ON finance.journal_lines
       FOR EACH ROW EXECUTE FUNCTION finance.guard_journal_line()""",
    """CREATE FUNCTION finance.require_balanced_journal() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF EXISTS(SELECT 1 FROM finance.journal_entries WHERE id=NEW.id AND status='posted') THEN
        IF (SELECT count(*) FROM finance.journal_lines WHERE journal_id=NEW.id) < 2 OR
           EXISTS(SELECT currency FROM finance.journal_lines WHERE journal_id=NEW.id
                  GROUP BY currency HAVING sum(amount)<>0) THEN
          RAISE EXCEPTION 'Posted journal must balance by currency' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NULL;
    END $$""",
    """CREATE CONSTRAINT TRIGGER require_balanced_journal
       AFTER INSERT OR UPDATE ON finance.journal_entries DEFERRABLE INITIALLY DEFERRED
       FOR EACH ROW EXECUTE FUNCTION finance.require_balanced_journal()""",
    """CREATE FUNCTION audit.deny_record_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
       BEGIN RAISE EXCEPTION 'Immutable record cannot be rewritten or deleted' USING ERRCODE='23514'; END $$""",
    """CREATE FUNCTION integration.guard_event_envelope() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP='DELETE' THEN
        RAISE EXCEPTION 'Outbox events require controlled archival' USING ERRCODE='23514';
      END IF;
      IF NEW.id<>OLD.id OR NEW.event_type<>OLD.event_type OR NEW.payload<>OLD.payload
         OR NEW.aggregate_id<>OLD.aggregate_id OR NEW.payload_version<>OLD.payload_version
         OR NEW.correlation_id<>OLD.correlation_id THEN
        RAISE EXCEPTION 'Outbox event envelope is immutable' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER guard_event_envelope BEFORE UPDATE OR DELETE ON integration.outbox_events
       FOR EACH ROW EXECUTE FUNCTION integration.guard_event_envelope()""",
    """CREATE FUNCTION identity.guard_scoped_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE branch_org uuid; branch_city uuid; role_name text;
    BEGIN
      SELECT name INTO role_name FROM identity.roles WHERE id=NEW.role_id;
      IF NEW.organization_id IS NULL AND role_name NOT IN
         ('customer','delivery_pilot','platform_super_admin','support_agent')
         AND NOT (role_name IN ('city_manager','city_operator')
                  AND NEW.city_id IS NOT NULL AND NEW.branch_id IS NULL) THEN
        RAISE EXCEPTION 'Role requires organization scope' USING ERRCODE='23514';
      END IF;
      IF NEW.branch_id IS NOT NULL THEN
        SELECT organization_id,city_id INTO branch_org,branch_city FROM merchant.merchant_branches WHERE id=NEW.branch_id;
        IF branch_org IS DISTINCT FROM NEW.organization_id OR
           (NEW.city_id IS NOT NULL AND branch_city IS DISTINCT FROM NEW.city_id) THEN
          RAISE EXCEPTION 'Role assignment scope mismatch' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER guard_scoped_assignment BEFORE INSERT OR UPDATE ON identity.user_role_assignments
       FOR EACH ROW EXECUTE FUNCTION identity.guard_scoped_assignment()""",
    """CREATE FUNCTION catalog.guard_branch_product_scope() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE branch_org uuid; product_org uuid;
    BEGIN
      SELECT organization_id INTO branch_org FROM merchant.merchant_branches WHERE id=NEW.branch_id;
      SELECT p.organization_id INTO product_org FROM catalog.product_variants v
        JOIN catalog.products p ON p.id=v.product_id WHERE v.id=NEW.variant_id;
      IF branch_org IS DISTINCT FROM product_org THEN
        RAISE EXCEPTION 'Branch and product organization mismatch' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$""",
]


def invariant_statements(metadata):
    statements = list(GUARDS)
    immutable = {
        "commerce.order_items",
        "commerce.order_status_history",
        "inventory.stock_movements",
        "audit.audit_events",
        "integration.inbox_processed_messages",
    }
    for table in metadata.sorted_tables:
        if table.info.get("immutable") or table.fullname in immutable:
            statements.append(
                f"CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "
                f"{table.fullname} FOR EACH ROW EXECUTE FUNCTION audit.deny_record_mutation()"
            )
    for table in ("catalog.product_prices", "inventory.stock_balances", "commerce.cart_items"):
        statements.append(
            f"CREATE TRIGGER branch_product_scope BEFORE INSERT OR UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION catalog.guard_branch_product_scope()"
        )
    return statements
