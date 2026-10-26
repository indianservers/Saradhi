# Customer delivery verification

The existing `POST /api/v1/delivery-tasks/{task_id}/acknowledge` is authorized for the customer who owns the order. There is no pilot-side OTP issue/verification, proof image upload, recipient-unavailable reason catalog, return-to-merchant flow, COD evidence, or pilot-authenticated completion contract. The pilot app therefore does not present a false “delivered” action. It exposes the existing generic failure transition with a confirmation warning that the backend currently records no reason or return workflow.

Before enabling pilot completion, add a server-side proof policy, short-lived verification challenge bound to the assignment, attempt limits, replay protection, private evidence storage, and an idempotent completion transaction. Do not make completion a client-only status mutation.
