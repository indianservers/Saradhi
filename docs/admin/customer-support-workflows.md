# Customer support workflows

Support agents see a privacy-minimized queue of unassigned tickets and tickets assigned to themselves. Claim is row-locked; only the assigned agent can view the conversation, reply, or resolve. Queue records omit customer user IDs. Reads and mutations are audited.

Customer-visible messages are the only conversation type currently supported. Internal notes, priority routing, order/payment context panels, team reassignment, and escalation history are not implemented. Do not put internal staff commentary into customer replies.
