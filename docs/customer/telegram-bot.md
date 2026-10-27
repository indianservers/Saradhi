# Telegram customer channel

## Run locally

Run `./.venv/Scripts/python.exe -m backend.integrations.telegram.control` and open
http://127.0.0.1:8765. Start the live API, language model and Telegram worker from this page.
The dedicated API runs on port 8001; the pre-existing API on port 8000 is untouched.
Override `QUICKBUDDY_API_URL` for a different backend.

The bot token stays in ignored `.secrets/telegram.env`. Backend customer sessions are
Fernet-encrypted in `.local/telegram/accounts.sqlite3`; the key is in an ACL-restricted
`.secrets/telegram-accounts.key`. Never commit or copy secrets into deployment images.
Sign in or create your own customer account on the local page, then send its one-use
`Link ...` pairing command to Telegram within five minutes. Passwords are never sent to chat.
A pairing code can bind exactly one chat. Existing account sessions refresh through the backend.

Live Telegram uses `/api/v1/channel/catalog`, not the simulator JSON. An unlinked customer
receives account-linking instructions; an unavailable backend never falls back to demo menus.
The simulator uses separate SQLite files and never creates live orders or payments.

## Ordering implementation

1. Live catalog reads merchant products, branch prices, variants and published product ratings.
2. Current stock, explicit branch availability, approved/accepting branches, active cities and
   available future windows filter discovery. All conditions are rechecked at quote/confirmation.
3. A persistent customer basket supports up to 30 lines across merchants.
4. Portion sizes use merchant variants. Merchant-defined option groups support spice and extras;
   preparation notes are saved into the authoritative order-line snapshot.
5. Individual lines support quantity edits, removal and customization; cancelling an edit retains
   the previous line. Every committed edit invalidates the prior quote.
6. The backend quote returns item, extra, delivery, tax, discount and total components. This core
   has no approved tax or delivery-fee calculator: configured taxable products fail closed;
   pickup quotes can show zero fees/tax/discount where applicable. Delivery fee `null` blocks order
   placement. No arbitrary fee/tax percentage or discount is fabricated.
7. GPS is reused from a saved profile; delivery requires backend serviceability. Local PostgreSQL
   lacks PostGIS, so courier checkout remains unavailable, not falsely serviceable.
8. Customers choose a future merchant window for each restaurant separately.
9. Place order is bound to the exact quote ID, fingerprint and expiry. Merchant child orders remain
   pending until authorized merchants accept them via existing merchant workflows.
10. Payment starts only when every merchant has accepted. Hosted Razorpay checkout uses the backend
    intent; verification delegates to the backend signature/provider checks and signed webhooks.
    Live credentials, approved deployment configuration and public HTTPS checkout/webhook URLs are
    still required. Set `TELEGRAM_CHECKOUT_BASE_URL` to a gateway reachable by customers. Its local
    default works only on this computer. Do not publish the local control room; expose only scoped
    `/checkout/*` routes behind a properly configured gateway.

Merchant product details are managed with `PUT /api/v1/channel/products/{product_id}/details`
under existing organization-scoped `catalog.write`. It supports ingredients, reviewed allergen
information, dietary labels, image URL and option groups/values. Merchant prices/inventory remain
managed by existing APIs/apps. `GET /api/v1/channel/merchant-orders/{id}/items` exposes chosen
options and preparation notes only to the authorized merchant branch.
Migration `20261027_0022` adds customer metadata and cart preparation notes. It has been applied
to the authorized local dev and test databases.

## Conversation and discovery implementation

11. English, Telugu and Hindi can be switched from Languages. Core navigation/cart messages are
    translated. Merchant descriptions and some operational/error messages remain in their source
    language; complete language QA and full message localization are outstanding.
12. Native-script and transliterated dish normalization supports phrases such as
    `chicken biryani kavali`, alongside the trained model's proposed search phrase.
13. Telegram voice messages are transcribed locally with multilingual Whisper tiny. Customers must
    select Use transcript before it enters discovery; it never directly submits or pays an order.
    Voice clips are limited to 120 seconds/10 MB. English generated-audio smoke testing is provided;
    real Telugu/Hindi speech quality is not validated.
14. Typo correction uses current merchant dish/restaurant vocabulary.
15. Follow-ups retain query context, including cheaper, vegetarian, numeric/word quantities and budgets.
16. Vegetarian/vegan/gluten-free/Jain/halal filters use merchant labels; absent labels are unknown.
17. Ingredient/allergen information comes only from the merchant. Missing reviewed information is
    flagged; absence of a declared allergen is never advertised as an allergen-safety guarantee.
18. Budget/person meal suggestions offer same-restaurant combinations before confirmed fees.
19. Favorite dishes and restaurants are scoped to the chat and hide currently unavailable entries.
20. Inline navigation supports item selection, edit/remove, options, pagination, cart and checkout.

## TensorFlow training and evaluation

Install the isolated runtime with:

```powershell
./.venv/Scripts/python.exe -m venv .local/telegram-ai-venv
./.local/telegram-ai-venv/Scripts/python.exe -m pip install -r backend/integrations/telegram/language-requirements.txt
./.local/telegram-ai-venv/Scripts/python.exe -m backend.integrations.telegram.train_nlp
./.local/telegram-ai-venv/Scripts/python.exe -m backend.integrations.telegram.audit_nlp
```

The committed synthetic corpus `nlp-commands.jsonl` contains 795 unique commands: 677 training
and 118 development paraphrases. TensorFlow trains a character GRU encoder-decoder with additive
attention and autoregressive action/dish/quantity/budget/diet output. This is sequence generation,
not just an intent classifier. FLAN-T5 small remains a pretrained search-phrase fallback.

The current 60-epoch run scores 85.59% complete structured match on the development set, which
was used while iterating. On a separate 20-phrase post-training audit it scores 50% exact match
and 55% intent accuracy. These are synthetic/development results, not production accuracy.
Neural action automation is deliberately not promoted. Confidence-gated dish suggestions can
assist discovery; explicit commands, merchant catalog validation, user review and backend rules
remain authoritative. Further broad query understanding needs representative real query data
and independent multilingual evaluation. Do not tune against the independent audit file.

Models, weights, full evaluation output and audio smoke files remain ignored under `.local/`.
No private customer conversations were used as training data. The control page shows training
metrics and NLP interpretation traces without exposing tokens.

## Validation and limitations

Focused unit/integration tests cover account pairing, ownership, multilingual normalization,
edit/cancel behavior, customizations, server option pricing, availability filtering, pending
merchant state, stale quotes and payment acceptance gating. The existing 18-test commerce
vertical slice also passes. Live provider payments have not been exercised without credentials.
No real merchant data is seeded into dev. WhatsApp, geocoding, production hosting, full
localization, broad NLP quality and production voice quality remain follow-up work.

References: [Telegram API](https://core.telegram.org/bots/api),
[FLAN-T5](https://huggingface.co/google/flan-t5-small),
[Razorpay Payment Links](https://razorpay.com/docs/api/payments/payment-links/create-standard/),
[Faster Whisper](https://github.com/SYSTRAN/faster-whisper).
PyAV 15.1.0 is pinned for faster-whisper 1.2.1 compatibility with audio decoding.

The contextual TensorFlow generative planner, training corpus and current evaluation
are documented in [Dialogue brain](dialogue-brain.md). It carries conversation memory
and proposes validated actions; it does not directly submit orders or payments.

## Food and grocery browsing

The customer menu offers Food, Groceries, All items, Restaurants and Stores.
Product cards show the restaurant/store, price, grocery pack unit, and merchant
photo. When no photo is supplied, Telegram and the simulator show a labeled
product illustration. Results paginate six cards at a time. Demo grocery products
are clearly marked DEMO; live products still come only from merchant-managed
catalogs. The live adapter preserves merchant product photos and units.

Medicines are removed from navigation. Medicine requests are declined, pharmacy
merchant catalogs are excluded, and configured medicine items cannot be selected
or quoted through the Telegram catalog. Existing carts must resolve selections
against the filtered catalog before live checkout.

## Multi-restaurant checkout

One cart can contain several restaurants/stores. Checkout selects a supported
slot for each branch, then shows each separate delivery with its items, extras,
delivery fee, scheduled arrival window and total, plus one combined amount.
Arrival windows come from merchant delivery slots, not live courier tracking.
Pickup has zero delivery fee and shows a pickup window. Multiple items in the
same branch/window/address share one delivery fee. Separate deliveries may arrive
at different times. Every merchant must accept before live payment is offered.

Merchants configure a fixed fee per delivery with authenticated
`PUT /api/v1/channel/branches/{branch_id}/delivery-fee`, body
`{"currency":"INR","amount":"35.00"}`. Authorization retains organization,
city and branch scopes. Zero explicitly enables free delivery. The backend uses
the latest effective branch rule (or configured city `delivery` rule), and blocks
unpriced delivery. Fee changes invalidate an already-reviewed quote. Fees are
included in the parent order/payment amount and recorded separately from merchant
item revenue. Existing tax and coverage checks remain mandatory.

The local simulator supports a labeled DEMO combined checkout with sample fees
and minute ranges. Add dishes from two restaurants, share sample GPS, choose
Checkout then Delivery. No demo order or payment is created.

Verification: focused bot/pricing tests and real PostgreSQL tests cover combined
amounts, separate merchant orders, payment amount, fee changes and permissions.
The delivery-accounting integration test isolates geographic serviceability;
existing coverage-rejection integration tests run separately.
