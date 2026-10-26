"""Enforce separate refund approval and preserve legal-entity ledger identity.

Existing pre-approval sandbox records remain historical; new refunds require approval.
No business data is deleted or rewritten.
"""

from alembic import op

revision = "20261026_0003"
down_revision = "20261026_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE finance.payment_refunds ADD COLUMN approval_id uuid,
        ADD CONSTRAINT fk_payment_refunds_approval_id_refund_approval_requests
        FOREIGN KEY (approval_id) REFERENCES operations.refund_approval_requests(id) ON DELETE RESTRICT,
        ADD CONSTRAINT uq_payment_refunds_approval_id UNIQUE(approval_id)""")
    for statement in HARDENING:
        op.execute(statement)


HARDENING = [
    """CREATE FUNCTION finance.guard_refund_approval() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE approved_order uuid; payment_order uuid; approved_amount numeric; approval_status text;
    BEGIN
      SELECT order_id,amount,status INTO approved_order,approved_amount,approval_status
        FROM operations.refund_approval_requests WHERE id=NEW.approval_id FOR UPDATE;
      SELECT order_id INTO payment_order FROM finance.payment_intents WHERE id=NEW.payment_id;
      IF NEW.approval_id IS NULL OR approval_status IS DISTINCT FROM 'approved'
         OR approved_order IS DISTINCT FROM payment_order OR approved_amount IS DISTINCT FROM NEW.amount THEN
        RAISE EXCEPTION 'Matching refund approval required' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER refund_approval_required BEFORE INSERT ON finance.payment_refunds
       FOR EACH ROW EXECUTE FUNCTION finance.guard_refund_approval()""",
    """CREATE TRIGGER immutable_refund BEFORE UPDATE OR DELETE ON finance.payment_refunds
       FOR EACH ROW EXECUTE FUNCTION audit.deny_record_mutation()""",
    """CREATE FUNCTION finance.guard_account_identity() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF (NEW.book_id IS DISTINCT FROM OLD.book_id OR NEW.currency IS DISTINCT FROM OLD.currency
          OR NEW.organization_id IS DISTINCT FROM OLD.organization_id)
         AND EXISTS(SELECT 1 FROM finance.journal_lines WHERE account_id=OLD.id) THEN
        RAISE EXCEPTION 'Posted account identity is immutable' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER account_identity BEFORE UPDATE ON finance.ledger_accounts
       FOR EACH ROW EXECUTE FUNCTION finance.guard_account_identity()""",
    """CREATE FUNCTION finance.guard_book_identity() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF (NEW.legal_entity_id IS DISTINCT FROM OLD.legal_entity_id
          OR NEW.currency IS DISTINCT FROM OLD.currency OR NEW.organization_id IS DISTINCT FROM OLD.organization_id)
         AND EXISTS(SELECT 1 FROM finance.journal_entries WHERE book_id=OLD.id) THEN
        RAISE EXCEPTION 'Posted book identity is immutable' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE TRIGGER book_identity BEFORE UPDATE ON finance.ledger_books
       FOR EACH ROW EXECUTE FUNCTION finance.guard_book_identity()""",
]


def downgrade():
    raise RuntimeError(
        "Removing financial controls requires an explicit reviewed forward migration"
    )
