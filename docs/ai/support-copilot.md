# Support copilot

`POST /api/v1/ai/agents/support/query` requires the current support assignment and a claimed ticket assigned to that user. It retrieves ticket status, message count and linked-order presence only. It does not send customer-authored text to the model, decide refund eligibility, issue a refund, or send a customer response.

Message summarization, approved policy retrieval, response drafting, escalation recommendations and the support workspace panel remain to be implemented. Existing support ticket read/write policies remain authoritative.
