# Mockup implementation matrix

Audit baseline: all 40 screens are identified in [target-mockup-inventory.md](target-mockup-inventory.md). Existing Flutter applications each have only `/` and show disabled “planned capability” cards. Company admin has `/`, `/login`, and `/workspace`, all foundation shells. No screen listed below was implemented at the beginning of this phase. At phase start, screenshot comparisons had not been captured; see the Phase 3 review status in the final column.

| App / screen | Target | Route to implement | Reusable components | Backend surface | Baseline status | Phase 3 screenshot review |
|---|---|---|---|---|---|---|
| Customer · Splash/onboarding | Customer board r1c1 | `/onboarding` | BrandIntro, PrimaryAction | auth challenges/login | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Home discovery | Customer r1c2 | `/` | AppBar, LocationSelector, Search, CategoryCard, MerchantCard, BottomNav | geo, branches, catalogue, recommendations | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Restaurant listing | Customer r1c3 | `/restaurants` | FilterChips, MerchantCard, FavoriteButton | branches, categories | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Restaurant menu | Customer r1c4 | `/restaurants/[merchantId]` | MerchantHero, ProductCard, AddonSheet, CartBar | products, variants, prices, carts | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Search/filters | Customer r1c5 | `/search` | SearchField, FilterSheet, ResultList | branches, products, categories | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Cart | Customer r2c1 | `/cart` | CartLine, QuantityControl, PriceBreakdown, StickyAction | carts, quote | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Address/payment | Customer r2c2 | `/checkout` | AddressCard, PaymentOption, PriceBreakdown | addresses, quote, sandbox payments | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Schedule/multi-merchant | Customer r2c3 | `/checkout/schedule` | ScheduleSlot, MerchantGroup, CompatibilityNotice | windows, carts, quote | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Live tracking | Customer r2c4 | `/orders/[orderId]/tracking` | DeliveryMap, ETA, Timeline, ContactActions | tracking, timeline, realtime ticket | Starter only | Not captured; see `phase-3-final-report.md` |
| Customer · Delivered/rating | Customer r2c5 | `/orders/[orderId]/complete` | RatingStars, Feedback, ReorderAction | orders, support | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Login/go online | Pilot r1c1 | `/` and `/login` | PilotHeader, EligibilityStatus, AvailabilityToggle | auth, pilot availability | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Dashboard | Pilot r1c2 | `/dashboard` | ShiftSummary, EarningsMetric, ShortcutGrid | pilot availability, city fleet | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Incoming request | Pilot r1c3 | `/requests/[assignmentId]` | OfferCard, ExpiryTimer, AcceptReject | offer, accept/reject assignment | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Navigate to merchant | Pilot r1c4 | `/tasks/[taskId]/pickup/navigation` | DeliveryMap, Directions, StopCard | ETA, location, tracking | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Pickup verification | Pilot r1c5 | `/tasks/[taskId]/pickup` | OrderSummary, VerificationChecklist, ConfirmAction | pickup, task snapshot | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Multi-stop route | Pilot r2c1 | `/routes/active` | StopList, RouteOverview, DeliveryMap | dispatch, assignments | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Navigate to customer | Pilot r2c2 | `/tasks/[taskId]/delivery/navigation` | DeliveryMap, RecipientCard, Instructions | tracking, ETA, location | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Complete delivery | Pilot r2c3 | `/tasks/[taskId]/complete` | OTPField, ProofCapture, FailureFlow | delivery task, delivery confirmation | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Earnings | Pilot r2c4 | `/earnings` | PeriodTabs, EarningsBreakdown, HistoryList | finance endpoints where available | Starter only | Not captured; see `phase-3-final-report.md` |
| Pilot · Profile/support | Pilot r2c5 | `/profile` | ProfileHeader, SettingsList, SupportAction | identity, support tickets | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Dashboard | Merchant r1c1 | `/` and `/dashboard` | BranchHeader, AvailabilityToggle, MetricRow, QuickLinks | branches, merchant orders | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Live queue | Merchant r1c2 | `/orders` | QueueTabs, OrderCard, StatusBadge, AcceptAction | orders, merchant-order transitions | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Preparation | Merchant r1c3 | `/orders/[childId]` | OrderDetails, PrepTimer, ReadyAction, ExtraTimeAction | merchant-order transitions | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Kitchen display | Merchant r1c4 | `/kitchen` | KitchenTicket, PriorityBadge, PrepTimer | merchant orders | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Menu management | Merchant r1c5 | `/menu` | ProductRow, AvailabilityToggle, AddItem | products, prices, variants | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Inventory | Merchant r2c1 | `/inventory` | StockRow, LowStockBadge, AdjustmentSheet | inventory, batches, adjustments | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Promotions | Merchant r2c2 | `/promotions` | CampaignCard, CampaignStatus, CreateAction | no campaign API in current contract | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Analytics | Merchant r2c3 | `/analytics` | MetricCard, TrendChart, PeriodFilter | no merchant analytics API in current contract | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Settlements | Merchant r2c4 | `/settlements` | PayoutSummary, SettlementRow, StatementAction | finance journals/payments; merchant payout query gap | Starter only | Not captured; see `phase-3-final-report.md` |
| Merchant · Branch settings | Merchant r2c5 | `/settings` | SettingsGroup, BranchCard, HoursEditor | branches, hours, capabilities | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Platform overview | Admin r1c1 | `/` | AdminShell, KPIGrid, TrendChart, CityTable | cities, dispatch/fleet, finance where available | Starter only | Manual browser review; no screenshot saved; see `comparisons/admin-overview.md` |
| Admin · Live operations | Admin r1c2 | `/operations` | KPIGrid, OrderTable, LiveMapPanel, OrderDrawer | dispatch and fleet; no universal live-order metrics endpoint | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Merchant management | Admin r1c3 | `/merchants` | FilterToolbar, DataTable, StatusBadge, ApprovalDialog | branches, review | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Pilot fleet | Admin r2c1 | `/fleet` | FleetTable, AvailabilityBadge, PilotActions | operations fleet | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · City map | Admin r2c2 | `/cities` | CitySelector, MapPanel, DemandLegend, ZoneSummary | geo cities/zones, AI demand/positioning | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Finance | Admin r2c3 | `/finance` | FinanceKpis, PayoutTrend, SettlementTable | finance journals/payments; aggregate payout queries may be unavailable | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Support/refunds | Admin r3c1 | `/support` | TicketQueue, PriorityBadge, RefundReview | support tickets, refund approvals | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Promotions/pricing | Admin r3c2 | `/promotions` | CampaignTable, PricingRules, PerformanceCard | no promotions/pricing admin API in current contract | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · Analytics/reports | Admin r3c3 | `/analytics` | ReportFilters, TrendChart, ExportAction | no aggregate analytics endpoint in current contract | Starter only | Not captured; see `phase-3-final-report.md` |
| Admin · AI control tower | Admin r3c4 | `/ai` | AIInsightCard, ModelStatus, RecommendationReview | AI model registry, forecasts, dispatch recommendations | Starter only | Not captured; see `phase-3-final-report.md` |

Static preview records, if used to exercise layout, must be explicitly labeled as preview data and must not be represented as backend results.


The route column records the planned reference-to-route mapping from the pre-implementation audit. Current implemented route names and partial backend status are documented in `phase-3-final-report.md`. The only live visual review recorded so far is the admin overview (`comparisons/admin-overview.md`); other screen screenshots remain uncaptured.
