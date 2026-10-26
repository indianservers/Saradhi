# Support Console

The support app provides a real inbox backed by `GET /api/v1/support/tickets`, with claim, conversation read, reply, and resolve actions. The inbox is cursor-bounded to 50 rows. It lists unassigned tickets and tickets assigned to the caller; details are only available after a successful claim. Claims lock the ticket row and reject already-owned or resolved tickets. A reply or resolution requires the current assignee. Ticket listing, conversation reads, claims, and resolutions create audit events.

Migration `20261026_0013` adds `assigned_to_id`. Migration `20261026_0014` allows a global assignment only for the dedicated `support_agent` role. The queue returns no user identifier or contact details. Internal notes, attachments, SLA/priority, escalations, merchant disputes, refund cases, and reopening are not implemented. The current message API is customer-visible; do not use it for internal notes.
