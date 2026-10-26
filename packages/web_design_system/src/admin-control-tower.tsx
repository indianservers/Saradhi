"use client";

import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  Bell,
  Bike,
  Building2,
  Check,
  ChevronDown,
  Clock3,
  Download,
  Ellipsis,
  FileText,
  Filter,
  HandCoins,
  LayoutDashboard,
  Map as MapIcon,
  MapPin,
  Megaphone,
  MessageSquareText,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Store,
  Users,
  Wallet,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

const nav = [
  ["overview", "Dashboard", LayoutDashboard],
  ["operations", "Live Operations", Activity],
  ["orders", "Orders", FileText],
  ["merchants", "Merchants", Store],
  ["fleet", "Delivery Fleet", Bike],
  ["cities", "City Operations", MapIcon],
  ["finance", "Finance", Wallet],
  ["support", "Support", MessageSquareText],
  ["promotions", "Promotions", Megaphone],
  ["analytics", "Analytics", BarChart3],
  ["ai", "AI Insights", Sparkles],
] as const;
type Screen = (typeof nav)[number][0];
type IconType = (typeof nav)[number][2];
const preview = process.env.NODE_ENV !== "production";

const sampleOrders = [
  ["#QB78520", "Brew & Bites", "Arjun Mehta", "Picking", "4 min"],
  ["#QB78519", "FreshMart", "Priya Sharma", "On the way", "12 min"],
  ["#QB78518", "Pizza Planet", "Karan Jain", "On the way", "8 min"],
  ["#QB78517", "The Good Bowl", "Sneha R.", "Delayed", "25 min"],
  ["#QB78516", "Burger Hub", "Rahul V.", "On the way", "10 min"],
  ["#QB78515", "Chai Adda", "Ananya Das", "Delivered", "6 min"],
] as const;
const sampleMerchants = [
  ["BB", "Brew & Bites", "Beverages", "Bengaluru", "1,248", "4.8", "Active"],
  ["FM", "FreshMart", "Grocery", "Hyderabad", "2,034", "4.6", "Active"],
  ["PP", "Pizza Planet", "QSR", "Chennai", "1,876", "4.5", "Active"],
  ["GB", "The Good Bowl", "Healthy Food", "Mumbai", "1,421", "4.7", "Active"],
  ["BH", "Burger Hub", "Fast Food", "Bengaluru", "1,112", "4.4", "Active"],
] as const;
const samplePilots = [
  ["RK", "Rohit Kumar", "KA 05 AB 1234", "Indiranagar", "12", "4.9", "Online"],
  [
    "IS",
    "Imran Shaik",
    "TS 09 CD 4456",
    "Banjara Hills",
    "9",
    "4.8",
    "On delivery",
  ],
  ["SR", "Suresh B.", "KA 01 XY 2101", "Koramangala", "14", "4.7", "Online"],
  ["VK", "Vikram R.", "TN 10 PQ 7788", "T. Nagar", "8", "4.6", "Idle"],
] as const;
const cities = ["Bengaluru", "Hyderabad", "Chennai", "Mumbai", "Delhi NCR"];

function Trend({ variant = "area" }: { variant?: "area" | "bars" }) {
  if (variant === "bars")
    return (
      <div className="qb-bars" aria-label="Preview weekly payout trend">
        {[35, 50, 43, 68, 49, 78, 61, 88, 67, 94, 72, 84, 55, 76, 93, 69].map(
          (h, i) => (
            <i key={i} style={{ height: `${h}%` }} />
          ),
        )}
      </div>
    );
  return (
    <svg
      className="qb-chart"
      viewBox="0 0 600 190"
      role="img"
      aria-label="Illustrative preview trend chart"
    >
      <defs>
        <linearGradient id="qb-fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#7546f5" stopOpacity=".2" />
          <stop offset="1" stopColor="#7546f5" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[36, 82, 128, 174].map((y) => (
        <line key={y} x1="0" x2="600" y1={y} y2={y} stroke="#edf0f6" />
      ))}
      <path
        d="M0 146 C45 128 61 143 95 120 S155 80 190 112 S252 152 286 99 S340 116 374 84 S424 109 462 64 S524 83 553 49 S579 60 600 26 L600 190 L0 190Z"
        fill="url(#qb-fill)"
      />
      <path
        d="M0 146 C45 128 61 143 95 120 S155 80 190 112 S252 152 286 99 S340 116 374 84 S424 109 462 64 S524 83 553 49 S579 60 600 26"
        fill="none"
        stroke="#6f3df4"
        strokeWidth="3"
      />
      <path
        d="M0 160 C51 152 73 128 110 139 S177 121 216 136 S276 129 318 120 S386 124 420 98 S488 112 525 91 S573 104 600 84"
        fill="none"
        stroke="#ff650d"
        strokeWidth="2.5"
        strokeDasharray="5 5"
      />
    </svg>
  );
}

function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`qb-badge ${tone}`}>{children}</span>;
}
function Metric({
  title,
  value,
  delta,
  icon: Icon,
  tone = "purple",
}: {
  title: string;
  value: string;
  delta?: string;
  icon: IconType;
  tone?: string;
}) {
  return (
    <article className="qb-metric">
      <div className="qb-metric-top">
        <span>{title}</span>
        <i className={`qb-iconbox ${tone}`}>
          <Icon size={16} />
        </i>
      </div>
      <strong>{value}</strong>
      <div className="qb-delta">
        <ArrowUpRight size={13} />
        {delta ?? "Preview metric"}
        <span> vs previous period</span>
      </div>
    </article>
  );
}
function Panel({
  title,
  sub,
  action,
  children,
  className = "",
}: {
  title: string;
  sub?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`qb-panel ${className}`}>
      <div className="qb-panel-head">
        <div>
          <h2>{title}</h2>
          {sub && <p>{sub}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function Overview({ onViewAll }: { onViewAll: () => void }) {
  return (
    <>
      <div className="qb-metrics">
        <Metric
          title="Total Orders"
          value={preview ? "24,532" : "—"}
          delta="12%"
          icon={FileText}
          tone="blue"
        />
        <Metric
          title="GMV"
          value={preview ? "₹18.4L" : "—"}
          delta="18%"
          icon={HandCoins}
          tone="orange"
        />
        <Metric
          title="Active Merchants"
          value={preview ? "1,248" : "—"}
          delta="6%"
          icon={Store}
          tone="violet"
        />
        <Metric
          title="Active Pilots"
          value={preview ? "892" : "—"}
          delta="9%"
          icon={Bike}
          tone="green"
        />
      </div>
      <div className="qb-grid-two">
        <Panel
          title="Orders & GMV trend"
          sub={
            preview
              ? "Last 24 hours · preview chart"
              : "Requires an analytics aggregate API"
          }
          action={
            <div className="qb-legend">
              <span>
                <i className="orange-dot" />
                Orders
              </span>
              <span>
                <i />
                GMV
              </span>
            </div>
          }
        >
          {preview ? (
            <>
              <Trend />
              <div className="qb-axis">
                <span>12 AM</span>
                <span>4 AM</span>
                <span>8 AM</span>
                <span>12 PM</span>
                <span>4 PM</span>
                <span>8 PM</span>
              </div>
            </>
          ) : (
            <Empty
              icon={BarChart3}
              title="Trend data unavailable"
              detail="No platform analytics aggregate endpoint is connected."
            />
          )}
        </Panel>
        <Panel
          title="Live city performance"
          action={
            <button className="qb-link" onClick={onViewAll}>
              View all <ArrowUpRight size={13} />
            </button>
          }
        >
          <div className="qb-city-head">
            <span>City</span>
            <span>Orders</span>
            <span>On-time</span>
          </div>
          {(preview ? cities.slice(0, 5) : []).map((city, i) => (
            <div className="qb-city-row" key={city}>
              <span>
                <i className={`qb-city-dot c${i}`} />
                {city}
              </span>
              <strong>
                {["6,422", "5,221", "4,112", "3,981", "2,876"][i]}
              </strong>
              <Badge tone="success">
                {["94%", "96%", "95%", "92%", "93%"][i]}
              </Badge>
            </div>
          ))}
          {!preview && (
            <Empty
              icon={MapPin}
              title="City metrics unavailable"
              detail="Select a city to inspect authorized operational metrics."
            />
          )}
        </Panel>
      </div>
      <div className="qb-metrics bottom-metrics">
        <Metric
          title="On-time Delivery"
          value={preview ? "93.6%" : "—"}
          delta="1.2%"
          icon={Clock3}
          tone="green"
        />
        <Metric
          title="Avg. Delivery Time"
          value={preview ? "28 min" : "—"}
          delta="8%"
          icon={Activity}
          tone="blue"
        />
        <Metric
          title="Customer Rating"
          value={preview ? "4.7 / 5" : "—"}
          delta="0.1"
          icon={Sparkles}
          tone="orange"
        />
        <Metric
          title="Successful Orders"
          value={preview ? "98.1%" : "—"}
          delta="0.4%"
          icon={Check}
          tone="violet"
        />
      </div>
    </>
  );
}

function OrdersTable({
  rows = sampleOrders,
}: {
  rows?: readonly (readonly string[])[];
}) {
  const [query, setQuery] = useState("");
  const filtered = rows.filter((row) =>
    row.join(" ").toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <Panel
      title="Live orders"
      sub={
        preview
          ? "Sample preview rows · not live operational data"
          : "Order records from the connected API"
      }
      action={
        <div className="qb-table-tools">
          <label className="qb-small-search">
            <Search size={14} />
            <input
              placeholder="Search orders"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
        </div>
      }
    >
      {!preview && (
        <div className="qb-unavailable">
          <AlertTriangle size={17} />
          <span>
            Order summary metrics are not available from the current API.
            Authenticate and connect an operations feed to populate this table.
          </span>
        </div>
      )}
      <div className="qb-table-wrap">
        <table>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Merchant</th>
              <th>Customer</th>
              <th>Status</th>
              <th>ETA</th>
            </tr>
          </thead>
          <tbody>
            {preview ? (
              filtered.map((r, i) => (
                <tr key={r[0]}>
                  <td className="mono">{r[0]}</td>
                  <td>
                    <b>{r[1]}</b>
                  </td>
                  <td>{r[2]}</td>
                  <td>
                    <Badge
                      tone={
                        r[3] === "Delayed"
                          ? "danger"
                          : r[3] === "Delivered"
                            ? "success"
                            : r[3] === "Picking"
                              ? "warning"
                              : "info"
                      }
                    >
                      {r[3]}
                    </Badge>
                  </td>
                  <td>{r[4]}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5}>
                  <Empty
                    icon={FileText}
                    title="No live order feed"
                    detail="Connect authenticated operations data to view orders."
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function Empty({
  icon: Icon,
  title,
  detail,
}: {
  icon: IconType;
  title: string;
  detail: string;
}) {
  return (
    <div className="qb-empty">
      <span>
        <Icon size={20} />
      </span>
      <b>{title}</b>
      <small>{detail}</small>
    </div>
  );
}

function Merchants({ cityNames }: { cityNames: Map<string, string> }) {
  const [query, setQuery] = useState("");
  const live = useBackend<{ items: BranchRecord[] }>(
    "api/v1/merchants/branches?limit=50",
  );
  const records = live.data?.items ?? [];
  const showPreview = preview && records.length === 0;
  const filtered = records.filter((x) =>
    `${x.name} ${cityNames.get(x.city_id) ?? ""}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const demo = sampleMerchants.filter((x) =>
    x.join(" ").toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <Panel
      title="Merchant partners"
      sub={
        records.length
          ? "Approved branches from live API"
          : showPreview
            ? "Sample preview · no live branches available"
            : "Approved merchant branches"
      }
      action={
        <div className="qb-table-tools">
          <label className="qb-small-search">
            <Search size={14} />
            <input
              placeholder="Search merchants"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <button className="qb-outline" onClick={() => setQuery("")}>
            <Filter size={14} /> Clear
          </button>
          <button
            className="qb-primary"
            disabled
            title="Merchant creation is not available in the current API contract"
          >
            <Building2 size={15} /> Add merchant
          </button>
        </div>
      }
    >
      {live.error && !showPreview && (
        <div className="qb-unavailable">
          <AlertTriangle size={17} /> Merchant API: {live.error}. Approval and
          create actions need a configured company_admin session.
        </div>
      )}
      {live.loading && (
        <div className="qb-unavailable">Loading approved branches…</div>
      )}
      <div className="qb-table-wrap">
        <table>
          <thead>
            <tr>
              <th>Merchant / branch</th>
              <th>Category</th>
              <th>City</th>
              <th>Orders (30d)</th>
              <th>Rating</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {records.length ? (
              filtered.map((r, i) => (
                <tr key={r.id}>
                  <td>
                    <div className="qb-merchant-cell">
                      <span className={`qb-merchant-avatar a${i % 5}`}>
                        <Store size={13} />
                      </span>
                      <b>{r.name}</b>
                    </div>
                  </td>
                  <td>—</td>
                  <td>{cityNames.get(r.city_id) ?? r.city_id.slice(0, 8)}</td>
                  <td>—</td>
                  <td>—</td>
                  <td>
                    <Badge tone={r.accepting_orders ? "success" : "warning"}>
                      {r.accepting_orders ? "Accepting" : "Paused"}
                    </Badge>
                  </td>
                  <td>
                    <button
                      className="qb-icon-button"
                      aria-label={`Merchant actions ${r.name}`}
                      disabled
                      title="Merchant actions are not available in the current API contract"
                    >
                      <Ellipsis size={16} />
                    </button>
                  </td>
                </tr>
              ))
            ) : showPreview ? (
              demo.map((r, i) => (
                <tr key={r[1]}>
                  <td>
                    <div className="qb-merchant-cell">
                      <span className={`qb-merchant-avatar a${i}`}>{r[0]}</span>
                      <b>{r[1]}</b>
                    </div>
                  </td>
                  <td>{r[2]}</td>
                  <td>{r[3]}</td>
                  <td>{r[4]}</td>
                  <td>★ {r[5]}</td>
                  <td>
                    <Badge tone="success">{r[6]}</Badge>
                  </td>
                  <td>
                    <button
                      className="qb-icon-button"
                      aria-label={`Merchant actions ${r[1]}`}
                      disabled
                      title="Merchant actions are not available in the current API contract"
                    >
                      <Ellipsis size={16} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7}>
                  <Empty
                    icon={Store}
                    title="No merchant records loaded"
                    detail={live.error ?? "No approved branches were returned."}
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function Fleet({ cityId }: { cityId: string | null }) {
  const live = useBackend<{ counts: Record<string, number> }>(
    cityId ? `api/v1/operations/cities/${cityId}/fleet` : null,
  );
  const counts = live.data?.counts;
  const showPreview = preview && !counts;
  const metric = (key: string, fallback: string) =>
    counts ? String(counts[key] ?? 0) : showPreview ? fallback : "—";
  return (
    <>
      <div className="qb-metrics">
        <Metric
          title="Verified pilots"
          value={metric("total", "3,421")}
          icon={Bike}
        />
        <Metric
          title="Online"
          value={metric("online_available", "892")}
          icon={Activity}
          tone="green"
        />
        <Metric
          title="On delivery"
          value={metric("assigned", "726")}
          icon={MapPin}
          tone="blue"
        />
        <Metric
          title="Offline / idle"
          value={metric("offline", "1,659")}
          icon={Clock3}
          tone="orange"
        />
      </div>
      <Panel
        title="Pilot fleet"
        sub={
          counts
            ? "Live aggregate from city fleet API"
            : showPreview
              ? "Sample preview records · fleet roster API is not available"
              : "Fleet data needs an authenticated city scope"
        }
        action={
          <button
            className="qb-outline"
            onClick={() => window.location.reload()}
          >
            <Filter size={14} /> Refresh
          </button>
        }
      >
        {live.error && !showPreview && (
          <div className="qb-unavailable">
            <AlertTriangle size={17} /> {live.error}
          </div>
        )}
        {counts ? (
          <Empty
            icon={Bike}
            title="Aggregate fleet only"
            detail="The API returns availability counts, not a pilot roster or current locations."
          />
        ) : showPreview ? (
          <div className="qb-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Pilot</th>
                  <th>Vehicle</th>
                  <th>Current location</th>
                  <th>Deliveries</th>
                  <th>Rating</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {samplePilots.map((r, i) => (
                  <tr key={r[1]}>
                    <td>
                      <div className="qb-person">
                        <i>{r[0]}</i>
                        <b>{r[1]}</b>
                      </div>
                    </td>
                    <td>{r[2]}</td>
                    <td>{r[3]}</td>
                    <td>{r[4]}</td>
                    <td>★ {r[5]}</td>
                    <td>
                      <Badge
                        tone={
                          r[6] === "Online"
                            ? "success"
                            : r[6] === "Idle"
                              ? "warning"
                              : "info"
                        }
                      >
                        {r[6]}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            icon={Bike}
            title="Fleet unavailable"
            detail="Connect a city and authenticated fleet API."
          />
        )}
      </Panel>
    </>
  );
}

function CityMap() {
  return preview ? (
    <div className="qb-city-layout">
      <Panel
        title="Bengaluru operations map"
        sub="Illustrative zones · map provider not connected"
        className="qb-map-panel"
      >
        <div className="qb-map">
          <div className="qb-map-river" />
          <div className="qb-road road1" />
          <div className="qb-road road2" />
          <div className="qb-road road3" />
          <div className="qb-zone z1">
            Indiranagar <Badge tone="danger">High demand</Badge>
          </div>
          <div className="qb-zone z2">
            Koramangala <Badge tone="warning">Medium</Badge>
          </div>
          <div className="qb-zone z3">
            Hebbal <Badge tone="info">Balanced</Badge>
          </div>
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <span className={`qb-map-pin p${i}`} key={i}>
              <Bike size={13} />
            </span>
          ))}
          <div className="qb-map-foot">
            <MapPin size={14} /> Map preview only · no live locations
          </div>
        </div>
      </Panel>
      <div className="qb-city-side">
        <Panel title="Zone health" sub="Illustrative zone conditions">
          {[
            ["Indiranagar", "High", "danger"],
            ["Koramangala", "Medium", "warning"],
            ["Hebbal", "Balanced", "success"],
            ["Whitefield", "Medium", "warning"],
          ].map(([n, s, t]) => (
            <div className="qb-zone-row" key={n}>
              <span>
                <i className={`qb-zone-indicator ${t}`} />
                <b>{n}</b>
              </span>
              <Badge tone={t}>{s}</Badge>
            </div>
          ))}
        </Panel>
        <Panel
          title="Demand · next 6 hours"
          sub="Deterministic fallback · untrained model"
        >
          <div className="qb-demand-bars">
            {[42, 64, 55, 84, 68, 94, 70, 59, 82, 47, 74, 62].map((h, i) => (
              <i key={i} style={{ height: `${h}%` }} />
            ))}
          </div>
          <div className="qb-footnote">
            <AlertTriangle size={13} /> No real history in local development
            database
          </div>
        </Panel>
      </div>
    </div>
  ) : (
    <Empty
      icon={MapIcon}
      title="Live map unavailable"
      detail="Map provider and authenticated city-zone data are not connected."
    />
  );
}

function Finance() {
  return (
    <>
      {preview && (
        <div className="qb-metrics">
          <Metric title="Total payouts" value="₹3.24 Cr" icon={Wallet} />
          <Metric
            title="Platform revenue"
            value="₹1.06 Cr"
            icon={HandCoins}
            tone="orange"
          />
          <Metric
            title="Commission collected"
            value="₹87.4 L"
            icon={Activity}
            tone="violet"
          />
          <Metric
            title="Pending settlements"
            value="₹24.6 L"
            icon={Clock3}
            tone="blue"
          />
        </div>
      )}
      <div className="qb-grid-two">
        <Panel
          title="Payouts trend"
          sub={
            preview
              ? "Illustrative preview chart"
              : "No company-wide payout aggregate is available"
          }
        >
          {preview ? (
            <>
              <Trend variant="bars" />
              <div className="qb-axis">
                <span>Apr 1</span>
                <span>Apr 8</span>
                <span>Apr 15</span>
                <span>Apr 22</span>
                <span>Apr 30</span>
              </div>
            </>
          ) : (
            <Empty
              icon={BarChart3}
              title="Payout trend unavailable"
              detail="Finance APIs expose ledger primitives, not this aggregate."
            />
          )}
        </Panel>
        <Panel title="Settlement status">
          {preview ? (
            <div className="qb-settlement">
              <div className="qb-donut">
                <b>92%</b>
                <small>Preview</small>
              </div>
              <div className="qb-settlement-legend">
                <span>
                  <i className="s1" />
                  Settled <b>1,248</b>
                </span>
                <span>
                  <i className="s2" />
                  Processing <b>86</b>
                </span>
                <span>
                  <i className="s3" />
                  On hold <b>24</b>
                </span>
                <span>
                  <i className="s4" />
                  Failed <b>12</b>
                </span>
              </div>
            </div>
          ) : (
            <Empty
              icon={Wallet}
              title="Settlement status unavailable"
              detail="A finance aggregation endpoint is required."
            />
          )}
        </Panel>
      </div>
      <div className="qb-unavailable">
        <AlertTriangle size={17} /> Finance cards above are illustrative preview
        values only. The current API exposes ledger/payment primitives but no
        company-wide payout aggregate.
      </div>
    </>
  );
}

function Support() {
  const rows = [
    ["#TK-0842", "Order not delivered", "#785020", "High", "Open"],
    ["#TK-0841", "Wrong item received", "#785018", "High", "Open"],
    ["#TK-0840", "Payout delay", "Merchant", "Medium", "In progress"],
    ["#TK-0839", "Delivery partner feedback", "#785016", "Low", "Resolved"],
  ];
  return (
    <Panel
      title="Support & refunds queue"
      sub={
        preview
          ? "Illustrative tickets · not live support records"
          : "Support tickets from backend"
      }
      action={
        <button
          className="qb-outline"
          disabled
          title="Live support filters require a support queue API"
        >
          <Filter size={14} /> Filter
        </button>
      }
    >
      {!preview && (
        <div className="qb-unavailable">
          <AlertTriangle size={17} /> Authenticate to load support tickets.
        </div>
      )}
      <div className="qb-table-wrap">
        <table>
          <thead>
            <tr>
              <th>Ticket</th>
              <th>Subject</th>
              <th>Related to</th>
              <th>Priority</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {(preview ? rows : []).map((r) => (
              <tr key={r[0]}>
                <td className="mono">{r[0]}</td>
                <td>
                  <b>{r[1]}</b>
                </td>
                <td>{r[2]}</td>
                <td>
                  <Badge tone={r[3] === "High" ? "danger" : "warning"}>
                    {r[3]}
                  </Badge>
                </td>
                <td>
                  <Badge tone={r[4] === "Resolved" ? "success" : "info"}>
                    {r[4]}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!preview && (
        <Empty
          icon={MessageSquareText}
          title="No ticket feed"
          detail="Support queue requires an authenticated session."
        />
      )}
    </Panel>
  );
}

function Promotions() {
  return (
    <>
      <Panel
        title="Promotions & pricing"
        sub={
          preview
            ? "Illustrative campaign preview · no live pricing data"
            : "Campaign endpoints are not connected"
        }
        action={
          <button
            className="qb-primary"
            disabled
            title="Campaign creation is not available in the current API contract"
          >
            <Megaphone size={15} /> Create campaign
          </button>
        }
      >
        {!preview && (
          <div className="qb-unavailable">
            <AlertTriangle size={17} /> Promotions and city pricing endpoints
            are not available in the generated API contract.
          </div>
        )}
        <div className="qb-campaigns">
          {(preview
            ? [
                [
                  "FLAT ₹50 OFF",
                  "Active",
                  "On orders above ₹499",
                  "Bengaluru · 124 merchants",
                ],
                [
                  "Free delivery",
                  "Active",
                  "On orders above ₹299",
                  "All cities · 86 merchants",
                ],
                [
                  "Lunch combo",
                  "Scheduled",
                  "10% off from 12–3 PM",
                  "Hyderabad · 32 merchants",
                ],
              ]
            : []
          ).map(([name, status, desc, scope], i) => (
            <div className="qb-campaign" key={name}>
              <div className={`qb-campaign-mark m${i}`}>%</div>
              <div>
                <b>{name}</b>
                <p>{desc}</p>
                <small>{scope}</small>
              </div>
              <Badge tone={status === "Active" ? "success" : "warning"}>
                {status}
              </Badge>
              <button
                className="qb-icon-button"
                aria-label={`Edit ${name}`}
                disabled
                title="Campaign editing is not available in the current API contract"
              >
                <Ellipsis size={16} />
              </button>
            </div>
          ))}
        </div>
        {!preview && (
          <Empty
            icon={Megaphone}
            title="Campaigns unavailable"
            detail="The current API has no promotions management endpoint."
          />
        )}
      </Panel>
      <Panel
        title="Dynamic pricing rules"
        sub="Capability not present in current backend contract"
      >
        <Empty
          icon={Settings2}
          title="Pricing rules not connected"
          detail="Commission and city-specific delivery fee administration is not exposed yet."
        />
      </Panel>
    </>
  );
}

function Analytics() {
  const views = {
    Orders: [
      ["Total orders", "64,221"],
      ["Unique customers", "4,312"],
      ["Repeat rate", "28.4%"],
      ["Avg. order value", "₹284"],
    ],
    Customers: [
      ["Active customers", "4,312"],
      ["New customers", "1,204"],
      ["Repeat rate", "28.4%"],
      ["Lifetime value", "₹892"],
    ],
    Merchants: [
      ["Active merchants", "1,248"],
      ["New partners", "82"],
      ["Avg. rating", "4.6 / 5"],
      ["Orders / merchant", "51.5"],
    ],
    Delivery: [
      ["Deliveries", "62,840"],
      ["On-time", "93.6%"],
      ["Avg. delivery", "28 min"],
      ["Active pilots", "892"],
    ],
    Revenue: [
      ["GMV", "₹18.4L"],
      ["Net revenue", "₹2.1L"],
      ["Commission", "11.4%"],
      ["Avg. order value", "₹284"],
    ],
  } as const;
  const [selected, setSelected] = useState<keyof typeof views>("Orders");
  const reportIcons = [FileText, Users, Activity, HandCoins];
  const reportTones = ["purple", "blue", "green", "orange"];
  return (
    <>
      <Panel
        title="Analytics & reports"
        sub={`Preview view · ${selected}`}
        action={
          <button className="qb-outline" onClick={() => window.print()}>
            <Download size={14} /> Export
          </button>
        }
      >
        <div className="qb-tabs" role="tablist" aria-label="Analytics view">
          {Object.keys(views).map((name) => (
            <button
              role="tab"
              aria-selected={selected === name}
              className={selected === name ? "selected" : ""}
              key={name}
              onClick={() => setSelected(name as keyof typeof views)}
            >
              {name}
            </button>
          ))}
        </div>
        {preview ? (
          <>
            <div className="qb-report-grid">
              {views[selected].map(([title, value], index) => {
                const Icon = reportIcons[index];
                return (
                  <Metric
                    key={title}
                    title={title}
                    value={value}
                    icon={Icon}
                    tone={reportTones[index]}
                  />
                );
              })}
            </div>
            <Trend />
          </>
        ) : (
          <Empty
            icon={BarChart3}
            title="Analytics unavailable"
            detail="No aggregate reporting endpoint is available in the current API contract."
          />
        )}
      </Panel>
      <div className="qb-unavailable">
        <AlertTriangle size={17} /> Report values are preview-only. No
        aggregated analytics endpoint is currently available.
      </div>
    </>
  );
}

function AIControlTower() {
  const live = useBackend<{
    items: {
      model_id: string;
      version_id?: string;
      name: string;
      algorithm: string;
      status: string;
      validation_passed: boolean;
    }[];
  }>("api/v1/ai/models");
  const models = live.data?.items ?? [];
  const items = [
    [
      "Demand forecast",
      "Seasonal baseline output is deterministic and untrained; no development order history is available.",
      "Rule-based",
      "warning",
    ],
    [
      "Dispatch suggestions",
      "Advisory optimization can recommend assignments but does not commit them.",
      "Deterministic",
      "info",
    ],
    [
      "Delay risk",
      "Review-only rules; no trained or calibrated model is available.",
      "Rule-based",
      "warning",
    ],
    [
      "Copilot",
      "No LLM provider is configured. Queries are unavailable.",
      "Unavailable",
      "danger",
    ],
  ];
  return (
    <>
      <div className="qb-ai-banner">
        <div className="qb-ai-orb">
          <Sparkles size={27} />
        </div>
        <div>
          <b>Quickbuddy AI · Control tower</b>
          <p>Operational intelligence with visible model provenance</p>
        </div>
        <Badge tone="warning">No trained models</Badge>
      </div>
      <div className="qb-ai-grid">
        {items.map(([title, desc, status, tone]) => (
          <article className="qb-ai-card" key={title}>
            <div>
              <h3>{title}</h3>
              <Badge tone={tone}>{status}</Badge>
            </div>
            <p>{desc}</p>
            <button
              className="qb-link"
              onClick={() => window.location.reload()}
            >
              Refresh status <ArrowUpRight size={13} />
            </button>
          </article>
        ))}
      </div>
      <Panel
        title="Model registry"
        sub={
          models.length
            ? "Connected registry records"
            : "Live registry metadata"
        }
      >
        {live.error && !preview && (
          <div className="qb-unavailable">
            <AlertTriangle size={16} />
            {live.error}
          </div>
        )}
        {live.loading && (
          <div className="qb-unavailable">Loading model registry…</div>
        )}
        {models.length ? (
          models.map((model) => (
            <div
              className="qb-model-row"
              key={model.version_id ?? model.model_id}
            >
              <span>
                <i className="qb-model-icon">
                  <Sparkles size={15} />
                </i>
                <b>{model.name}</b>
              </span>
              <Badge
                tone={model.status === "production" ? "success" : "warning"}
              >
                {model.status}
              </Badge>
              <small>
                {model.algorithm} · validation{" "}
                {model.validation_passed ? "passed" : "not passed"}
              </small>
            </div>
          ))
        ) : preview ? (
          <>
            <div className="qb-model-row">
              <span>
                <i className="qb-model-icon">
                  <Sparkles size={15} />
                </i>
                <b>Demand · seasonal baseline</b>
              </span>
              <Badge tone="warning">Deterministic fallback</Badge>
              <small>Untrained · evaluation needs real history</small>
            </div>
            <div className="qb-model-row">
              <span>
                <i className="qb-model-icon">
                  <Activity size={15} />
                </i>
                <b>ETA · provider fallback</b>
              </span>
              <Badge tone="warning">Fallback</Badge>
              <small>Not a trained ETA model</small>
            </div>
          </>
        ) : (
          <Empty
            icon={Sparkles}
            title="Model registry unavailable"
            detail="Authenticate with an AI-enabled role to inspect registered model versions."
          />
        )}
      </Panel>
      <div className="qb-unavailable">
        <ShieldCheck size={17} /> No confidence, accuracy or trained-model claim
        is shown for deterministic fallbacks.
      </div>
    </>
  );
}

function Operations({ cityId }: { cityId: string | null }) {
  const live = useBackend<{
    counts: Record<string, number>;
    tasks: { id: string; status: string; version: number }[];
  }>(cityId ? `api/v1/operations/cities/${cityId}/dispatch?limit=50` : null);
  const counts = live.data?.counts;
  const showPreview = preview && !counts;
  return (
    <>
      <div className="qb-metrics">
        <Metric
          title="Active tasks"
          value={
            counts
              ? String(Object.values(counts).reduce((a, b) => a + b, 0))
              : showPreview
                ? "1,284"
                : "—"
          }
          icon={FileText}
          tone="blue"
        />
        <Metric
          title="Unassigned"
          value={
            counts ? String(counts.unassigned ?? 0) : showPreview ? "412" : "—"
          }
          icon={Clock3}
          tone="orange"
        />
        <Metric
          title="Assigned"
          value={
            counts ? String(counts.assigned ?? 0) : showPreview ? "726" : "—"
          }
          icon={Bike}
          tone="green"
        />
        <Metric
          title="Picked up"
          value={
            counts ? String(counts.picked_up ?? 0) : showPreview ? "62" : "—"
          }
          icon={AlertTriangle}
          tone="violet"
        />
      </div>
      {live.data ? (
        <Panel title="Dispatch tasks" sub="Authenticated city dispatch API">
          <div className="qb-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>Status</th>
                  <th>Version</th>
                  <th>Merchant</th>
                  <th>Customer</th>
                </tr>
              </thead>
              <tbody>
                {live.data.tasks.map((task) => (
                  <tr key={task.id}>
                    <td className="mono">{task.id}</td>
                    <td>
                      <Badge
                        tone={
                          task.status === "picked_up"
                            ? "info"
                            : task.status === "unassigned"
                              ? "warning"
                              : "success"
                        }
                      >
                        {task.status}
                      </Badge>
                    </td>
                    <td>{task.version}</td>
                    <td>—</td>
                    <td>—</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      ) : (
        <>
          {live.error && !showPreview && (
            <div className="qb-unavailable">
              <AlertTriangle size={17} />
              {live.error}
            </div>
          )}
          {showPreview ? (
            <OrdersTable />
          ) : (
            <Empty
              icon={Activity}
              title="Live dispatch unavailable"
              detail="Select a city and sign in with dispatch access to load tasks."
            />
          )}
        </>
      )}
    </>
  );
}

function Orders() {
  return <OrdersTable />;
}

type CityRecord = { id: string; name: string };
type BranchRecord = {
  id: string;
  name: string;
  city_id: string;
  accepting_orders: boolean;
};
type BackendState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};
function useBackend<T>(path: string | null): BackendState<T> {
  const [state, setState] = useState<BackendState<T>>({
    data: null,
    loading: Boolean(path),
    error: null,
  });
  useEffect(() => {
    if (!path) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    const controller = new AbortController();
    setState({ data: null, loading: true, error: null });
    fetch(`/api/backend/${path}`, {
      signal: controller.signal,
      cache: "no-store",
    })
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok)
          throw new Error(body.detail ?? `API returned ${response.status}`);
        return body as T;
      })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({
            data: null,
            loading: false,
            error:
              error instanceof Error ? error.message : "Backend request failed",
          });
      });
    return () => controller.abort();
  }, [path]);
  return state;
}

const screenInfo: Record<
  Screen,
  { title: string; eyebrow: string; description: string; icon: IconType }
> = {
  overview: {
    title: "Platform overview",
    eyebrow: "Operations at a glance",
    description: "Monitor service health across your cities.",
    icon: LayoutDashboard,
  },
  operations: {
    title: "Live operations",
    eyebrow: "Order control center",
    description: "Track fulfillment and surface exceptions early.",
    icon: Activity,
  },
  orders: {
    title: "Orders",
    eyebrow: "Order management",
    description: "Search and review current order activity.",
    icon: FileText,
  },
  merchants: {
    title: "Merchant management",
    eyebrow: "Partner network",
    description: "Review merchant availability and operating status.",
    icon: Store,
  },
  fleet: {
    title: "Pilot fleet",
    eyebrow: "Delivery operations",
    description: "Monitor the delivery partner fleet by city.",
    icon: Bike,
  },
  cities: {
    title: "City operations",
    eyebrow: "Supply & demand",
    description: "Review zone conditions and pilot positioning.",
    icon: MapIcon,
  },
  finance: {
    title: "Finance & settlements",
    eyebrow: "Financial operations",
    description: "Reconcile platform and partner settlement activity.",
    icon: Wallet,
  },
  support: {
    title: "Support & refunds",
    eyebrow: "Customer experience",
    description: "Triage service requests and refund approvals.",
    icon: MessageSquareText,
  },
  promotions: {
    title: "Promotions & pricing",
    eyebrow: "Commercial operations",
    description: "Manage campaigns and pricing policies.",
    icon: Megaphone,
  },
  analytics: {
    title: "Analytics & reports",
    eyebrow: "Business intelligence",
    description: "Explore platform performance and export reports.",
    icon: BarChart3,
  },
  ai: {
    title: "AI control tower",
    eyebrow: "Model-aware operations",
    description: "Review forecasts, risks and dispatch recommendations.",
    icon: Sparkles,
  },
};

export function AdminControlTower() {
  const [screen, setScreen] = useState<Screen>("overview");
  const [city, setCity] = useState("All Cities");
  const [cityRecords, setCityRecords] = useState<CityRecord[]>([]);
  const [apiState, setApiState] = useState("Checking API");
  const [search, setSearch] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    let alive = true;
    fetch("/api/backend/api/v1/geo/cities?limit=50", { cache: "no-store" })
      .then(async (r) => {
        if (!r.ok) throw new Error("Geography API unavailable");
        const body = await r.json();
        const list = body.items ?? body.data ?? [];
        if (alive) {
          setCityRecords(
            list.filter((x: unknown): x is CityRecord =>
              Boolean(x && typeof x === "object" && "id" in x && "name" in x),
            ),
          );
          setApiState("Geography connected");
        }
      })
      .catch(() => {
        if (alive) setApiState("API unavailable");
      });
    return () => {
      alive = false;
    };
  }, []);
  const info = screenInfo[screen];
  const ScreenIcon = info.icon;
  const activeNav = useMemo(() => nav.find((x) => x[0] === screen), [screen]);
  const switchScreen = (key: Screen) => {
    setScreen(key);
    setMenuOpen(false);
    if (typeof window !== "undefined")
      history.replaceState(
        null,
        "",
        key === "overview" ? "/" : `/?view=${key}`,
      );
  };
  const availableCities = [
    "All Cities",
    ...(cityRecords.length ? cityRecords.map((x) => x.name) : cities),
  ];
  const cityId =
    city === "All Cities"
      ? null
      : (cityRecords.find((x) => x.name === city)?.id ?? null);
  const cityById = new Map(cityRecords.map((x) => [x.id, x.name]));
  useEffect(() => {
    const view = new URLSearchParams(window.location.search).get(
      "view",
    ) as Screen | null;
    if (view && view in screenInfo) setScreen(view);
  }, []);
  const render = () => {
    switch (screen) {
      case "overview":
        return <Overview onViewAll={() => switchScreen("cities")} />;
      case "operations":
        return <Operations cityId={cityId} />;
      case "orders":
        return <Orders />;
      case "merchants":
        return <Merchants cityNames={cityById} />;
      case "fleet":
        return <Fleet cityId={cityId} />;
      case "cities":
        return <CityMap />;
      case "finance":
        return <Finance />;
      case "support":
        return <Support />;
      case "promotions":
        return <Promotions />;
      case "analytics":
        return <Analytics />;
      case "ai":
        return <AIControlTower />;
    }
  };
  return (
    <div className="qb-admin">
      <aside className={`qb-sidebar ${menuOpen ? "open" : ""}`}>
        <a
          className="qb-brand"
          href="/"
          onClick={(e) => {
            e.preventDefault();
            switchScreen("overview");
          }}
        >
          <span className="qb-brand-symbol">Q</span>
          <span>
            quickbuddy<small>COMPANY ADMIN</small>
          </span>
        </a>
        <div className="qb-nav-label">WORKSPACE</div>
        <nav>
          {nav.map(([key, label, Icon]) => (
            <button
              key={key}
              className={`qb-nav-item ${screen === key ? "active" : ""}`}
              onClick={() => switchScreen(key)}
            >
              <Icon size={16} />
              <span>{label}</span>
              {key === "operations" && <i className="qb-nav-live" />}
            </button>
          ))}
        </nav>
        <div className="qb-sidebar-bottom">
          <div className="qb-user">
            <span>AS</span>
            <div>
              <b>Admin workspace</b>
              <small>Company administrator</small>
            </div>
            <Ellipsis size={16} />
          </div>
          <div className="qb-secure">
            <ShieldCheck size={13} /> Permission-scoped access
          </div>
        </div>
      </aside>
      {menuOpen && (
        <button
          className="qb-backdrop"
          onClick={() => setMenuOpen(false)}
          aria-label="Close navigation"
        />
      )}
      <main className="qb-main">
        <header className="qb-topbar">
          <button
            className="qb-mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <Settings2 size={18} />
          </button>
          <div className="qb-breadcrumb">
            <span>Quickbuddy</span>
            <b>/</b>
            <strong>{info.title}</strong>
          </div>
          <label className="qb-global-search">
            <Search size={15} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const q = search.trim().toLowerCase();
                  const match = nav.find(([, label]) =>
                    label.toLowerCase().includes(q),
                  );
                  if (match) switchScreen(match[0]);
                }
              }}
              placeholder="Search sections, press Enter"
            />
            <kbd>⌘ K</kbd>
          </label>
          <div className="qb-top-actions">
            <button
              className="qb-city-select"
              onClick={() =>
                setCity(
                  (c) =>
                    availableCities[
                      (availableCities.indexOf(c) + 1) % availableCities.length
                    ],
                )
              }
            >
              <MapPin size={14} />
              {city}
              <ChevronDown size={13} />
            </button>
            <span
              className={`qb-api-state ${apiState === "API connected" ? "ok" : ""}`}
            >
              <i />
              {apiState}
            </span>
            <button
              className="qb-icon-button notification"
              aria-label="Notifications"
              onClick={() => switchScreen("support")}
            >
              <Bell size={17} />
              <i />
            </button>
            <button
              className="qb-avatar"
              aria-label="Admin profile"
              disabled
              title="Profile settings require an authenticated identity"
            >
              AS
            </button>
          </div>
        </header>
        <div className="qb-content">
          <div className="qb-page-title">
            <div>
              <div className="qb-eyebrow">
                <ScreenIcon size={13} />
                {info.eyebrow}
              </div>
              <h1>{info.title}</h1>
              <p>{info.description}</p>
            </div>
            <div className="qb-page-actions">
              <button
                className="qb-outline"
                onClick={() => window.location.reload()}
              >
                <Clock3 size={14} /> Refresh data
              </button>
              <button className="qb-outline" onClick={() => window.print()}>
                <Download size={14} /> Export
              </button>
            </div>
          </div>
          {preview && (
            <div className="qb-preview-notice">
              <AlertTriangle size={14} />
              <b>Preview data</b>
              <span>
                Illustrative records appear only in development; production uses
                connected API responses.
              </span>
              <button onClick={() => switchScreen("ai")}>
                Data policy <ArrowUpRight size={12} />
              </button>
            </div>
          )}
          {activeNav && (
            <div className="qb-screen-tabs">
              {nav.slice(0, 5).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => switchScreen(key)}
                  className={key === screen ? "selected" : ""}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
          {render()}
          <footer className="qb-footer">
            <span>QUICKBUDDY OPERATIONS</span>
            <span>
              API: {apiState} · {preview ? "Development preview" : "Live mode"}
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}
