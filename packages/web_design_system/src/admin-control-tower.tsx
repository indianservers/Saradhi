"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  Activity,
  AlertTriangle,
  Bike,
  Building2,
  Check,
  ChevronDown,
  CircleHelp,
  DollarSign,
  Database,
  Download,
  Clock3,
  Command,
  FileText,
  LayoutDashboard,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Store,
  Upload,
  Users,
} from "lucide-react";

type City = { id: string; name: string };
type Organization = { id: string; name: string };
type RefundApproval = {
  id: string;
  order_id: string;
  requested_by: string;
  organization_id: string;
  amount: string;
  status: string;
  created_at: string;
};
type Branch = {
  id: string;
  name: string;
  city_id: string;
  merchant_type?: string | null;
  accepting_orders: boolean;
};
type Dispatch = {
  city_id: string;
  counts: Record<string, number>;
  tasks: { id: string; status: string; version: number }[];
};
type Fleet = { counts: Record<string, number>; generated_at: string };
type Incident = {
  id: string;
  pilot_id: string;
  delivery_task_id: string | null;
  category: string;
  severity: string;
  status: string;
  safety_emergency: boolean;
  summary: string;
  resolution_summary: string | null;
  created_at: string;
};
type Model = {
  model_id: string;
  version_id: string;
  name: string;
  purpose: string;
  provider: string;
  version: string;
  algorithm: string;
  status: string;
  validation_passed: boolean;
  metrics: Record<string, unknown>;
};
type BulkJob = {
  id: string;
  entity: string;
  status: string;
  row_count: number;
  valid_count: number;
  created_count: number;
  failed_count: number;
  previewed: boolean;
  created_at: string;
};
type CustomerRow = {
  id: string;
  name: string;
  status: string;
  email: string | null;
  email_verified: boolean;
  phone: string | null;
  phone_verified: boolean;
  created_at: string;
  order_count: number;
  completed_order_count: number;
  gross_purchase_value: string;
  last_order_at: string | null;
};
type Result<T> = {
  data: T | null;
  error: string;
  loading: boolean;
  reload: () => void;
};

function useLive<T>(path: string | null): Result<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(Boolean(path));
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion((n) => n + 1), []);
  useEffect(() => {
    if (!path) {
      setData(null);
      setError("");
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    let inFlight = false;
    const run = async () => {
      if (inFlight || controller.signal.aborted) return;
      inFlight = true;
      try {
        const response = await fetch(`/api/backend/${path}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok)
          throw new Error(
            body.error?.message ??
              body.detail ??
              `Backend returned ${response.status}`,
          );
        if (!controller.signal.aborted) {
          setData(body as T);
          setError("");
          setLoading(false);
        }
      } catch (reason) {
        if (!controller.signal.aborted) {
          setData(null);
          setError(
            reason instanceof Error ? reason.message : "Backend request failed",
          );
          setLoading(false);
        }
      } finally {
        inFlight = false;
      }
    };
    setData(null);
    setError("");
    setLoading(true);
    void run();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void run();
    }, 30_000);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [path, version]);
  return { data, error, loading, reload };
}

function Notice({ error }: { error: string }) {
  return error ? (
    <div className="qb-unavailable" role="status">
      <AlertTriangle size={16} />
      {error}
    </div>
  ) : null;
}
function Empty({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="qb-empty">
      <span>
        <CircleHelp size={20} />
      </span>
      <b>{title}</b>
      <small>{detail}</small>
    </div>
  );
}
function Metric({
  title,
  value,
  icon: Icon,
}: {
  title: string;
  value: number | string;
  icon: typeof Activity;
}) {
  return (
    <article className="qb-metric">
      <div className="qb-metric-top">
        <span>{title}</span>
        <i className="qb-iconbox purple">
          <Icon size={16} />
        </i>
      </div>
      <strong>{value}</strong>
      <div className="qb-delta">Current backend snapshot</div>
    </article>
  );
}

export function AdminControlTower() {
  const [cityId, setCityId] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [screen, setScreen] = useState("overview");
  const cities = useLive<{ items: City[] }>(
    "api/v1/operations/authorized-cities?limit=100",
  );
  useEffect(() => {
    if (!cityId && cities.data?.items.length)
      setCityId(cities.data.items[0].id);
  }, [cityId, cities.data]);
  const dispatch = useLive<Dispatch>(
    cityId ? `api/v1/operations/cities/${cityId}/dispatch?limit=50` : null,
  );
  const fleet = useLive<Fleet>(
    cityId ? `api/v1/operations/cities/${cityId}/fleet` : null,
  );
  const incidents = useLive<{ items: Incident[] }>(
    cityId
      ? `api/v1/operations/cities/${cityId}/pilot-incidents?limit=50`
      : null,
  );
  const branches = useLive<{ items: Branch[] }>(
    cityId ? `api/v1/merchants/branches?city_id=${cityId}&limit=50` : null,
  );
  const models = useLive<{ items: Model[] }>("api/v1/ai/models");
  const organizations = useLive<{ items: Organization[] }>(
    "api/v1/finance/authorized-organizations",
  );
  useEffect(() => {
    if (!organizationId && organizations.data?.items.length)
      setOrganizationId(organizations.data.items[0].id);
  }, [organizationId, organizations.data]);
  const refunds = useLive<{ items: RefundApproval[] }>(
    organizationId
      ? `api/v1/finance/refund-approvals?organization_id=${organizationId}&limit=100`
      : null,
  );
  const bulkJobs = useLive<{ items: BulkJob[] }>(
    screen === "data" ? "api/v1/bulk/jobs?limit=50" : null,
  );
  const selected = cities.data?.items.find((city) => city.id === cityId);
  const items = dispatch.data?.counts ?? {};
  const activeTasks = Object.values(items).reduce(
    (total, count) => total + Number(count || 0),
    0,
  );
  const nav = [
    ["overview", "Overview", LayoutDashboard],
    ["dispatch", "Dispatch", Activity],
    ["merchants", "Merchants", Store],
    ["fleet", "Fleet", Bike],
    ["incidents", "Incidents", AlertTriangle],
    ["ai", "AI operations", Sparkles],
    ["finance", "Refund approvals", DollarSign],
    ["customers", "Customers", Users],
    ["data", "Data operations", Database],
  ] as const;
  const health = [dispatch, fleet, incidents].some((x) => x.error)
    ? "Limited"
    : [dispatch, fleet, incidents].every((x) => x.data !== null)
      ? "Connected"
      : "Checking";
  const refresh = () =>
    [
      cities,
      dispatch,
      fleet,
      incidents,
      branches,
      models,
      organizations,
      refunds,
      bulkJobs,
    ].forEach((resource) => resource.reload());
  async function signOut() {
    await fetch("/api/session", { method: "DELETE" });
    window.location.assign("/login");
  }

  return (
    <div className="qb-admin">
      <aside className="qb-sidebar">
        <a className="qb-brand" href="/">
          <span className="qb-brandmark">
            <Command size={19} />
          </span>
          <span>
            quickbuddy<span className="brand-dot">.</span>
            <small>CONTROL TOWER</small>
          </span>
        </a>
        <div className="qb-nav-label">PLATFORM</div>
        <nav aria-label="Control tower">
          {nav.map(([key, label, Icon]) => (
            <button
              key={key}
              className={`qb-nav-item ${screen === key ? "active" : ""}`}
              onClick={() => setScreen(key)}
            >
              <Icon size={16} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="qb-sidebar-bottom">
          <ShieldCheck size={15} /> Backend enforced scopes
        </div>
      </aside>
      <main className="qb-main">
        <header className="qb-topbar">
          <div className="qb-breadcrumb">
            <span>Quickbuddy</span>
            <b>/</b>
            <strong>Super Admin</strong>
          </div>
          <div className="qb-top-actions">
            <span
              className={`qb-api-state ${health === "Connected" ? "ok" : ""}`}
            >
              <i />
              API {health}
            </span>
            <label className="qb-city-select">
              <MapPin size={14} />
              <select
                aria-label="City scope"
                value={cityId}
                onChange={(e) => setCityId(e.target.value)}
              >
                <option value="">Select authorized city</option>
                {(cities.data?.items ?? []).map((city) => (
                  <option key={city.id} value={city.id}>
                    {city.name}
                  </option>
                ))}
              </select>
              <ChevronDown size={13} />
            </label>
            {screen === "finance" && (
              <label
                className="qb-city-select"
                aria-label="Finance organization"
              >
                <Building2 size={14} />
                <select
                  aria-label="Finance organization"
                  value={organizationId}
                  onChange={(event) => setOrganizationId(event.target.value)}
                >
                  <option value="">Select organization</option>
                  {(organizations.data?.items ?? []).map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
                <ChevronDown size={13} />
              </label>
            )}
            <button
              className="qb-icon-button"
              aria-label="Refresh dashboard"
              onClick={refresh}
            >
              <RefreshCw size={15} />
            </button>
            <button className="qb-outline" onClick={() => void signOut()}>
              Sign out
            </button>
          </div>
        </header>
        <section className="qb-content">
          <div className="qb-page-title">
            <div>
              <div className="qb-eyebrow">
                <Activity size={12} /> OPERATIONS CONTROL TOWER
              </div>
              <h1>{nav.find(([key]) => key === screen)?.[1]}</h1>
              <p>
                {selected
                  ? `${selected.name} · live backend snapshots refresh every 30 seconds`
                  : "Select a city to load its authorized operational data."}
              </p>
            </div>
            <div className="qb-page-actions">
              <button className="qb-outline" onClick={refresh}>
                <RefreshCw size={14} /> Refresh data
              </button>
            </div>
          </div>
          <Notice error={cities.error} />
          {screen === "overview" && (
            <>
              <div className="qb-metrics">
                <Metric
                  title="Active delivery tasks"
                  value={dispatch.data ? activeTasks : "—"}
                  icon={FileText}
                />
                <Metric
                  title="Available pilots"
                  value={fleet.data?.counts.online_available ?? "—"}
                  icon={Bike}
                />
                <Metric
                  title="Verified fleet"
                  value={
                    fleet.data
                      ? Object.values(fleet.data.counts).reduce(
                          (a, b) => a + b,
                          0,
                        )
                      : "—"
                  }
                  icon={Activity}
                />
                <Metric
                  title="Open pilot incidents"
                  value={
                    incidents.data?.items.filter(
                      (item) => item.status !== "resolved",
                    ).length ?? "—"
                  }
                  icon={AlertTriangle}
                />
              </div>
              <div className="qb-grid-two">
                <section className="qb-panel">
                  <div className="qb-panel-head">
                    <div>
                      <h2>Dispatch status</h2>
                      <p>Counts from the selected city dispatch service</p>
                    </div>
                  </div>
                  <Notice error={dispatch.error} />
                  {dispatch.data ? (
                    <div className="qb-table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>State</th>
                            <th>Tasks</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(dispatch.data.counts).map(
                            ([status, count]) => (
                              <tr key={status}>
                                <td>{status.replaceAll("_", " ")}</td>
                                <td>{count}</td>
                              </tr>
                            ),
                          )}
                        </tbody>
                      </table>
                    </div>
                  ) : dispatch.loading ? (
                    <Empty
                      title="Loading dispatch"
                      detail="Fetching the authorized city snapshot."
                    />
                  ) : null}
                </section>
                <section className="qb-panel">
                  <div className="qb-panel-head">
                    <div>
                      <h2>Operational incidents</h2>
                      <p>Pilot reported incidents, newest first</p>
                    </div>
                    <button
                      className="qb-link"
                      onClick={() => setScreen("incidents")}
                    >
                      Open queue
                    </button>
                  </div>
                  <Notice error={incidents.error} />
                  {incidents.data?.items.length
                    ? incidents.data.items.slice(0, 5).map((incident) => (
                        <div className="qb-zone-row" key={incident.id}>
                          <span>
                            <i
                              className={`qb-zone-indicator ${incident.safety_emergency ? "danger" : "warning"}`}
                            />
                            <b>{incident.category}</b>
                            <small>{incident.summary}</small>
                          </span>
                          <span>{incident.status}</span>
                        </div>
                      ))
                    : !incidents.error && (
                        <Empty
                          title="No reported incidents"
                          detail="No pilot incidents were returned for this city."
                        />
                      )}
                </section>
              </div>
            </>
          )}
          {screen === "dispatch" && (
            <section className="qb-panel">
              <div className="qb-panel-head">
                <div>
                  <h2>Active dispatch tasks</h2>
                  <p>
                    Authoritative statuses from the city dispatch API. Customer
                    and pilot PII are not exposed by this endpoint.
                  </p>
                </div>
              </div>
              <Notice error={dispatch.error} />
              {dispatch.data?.tasks.length ? (
                <div className="qb-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Task</th>
                        <th>Status</th>
                        <th>Version</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dispatch.data.tasks.map((task) => (
                        <tr key={task.id}>
                          <td className="mono">{task.id}</td>
                          <td>{task.status.replaceAll("_", " ")}</td>
                          <td>{task.version}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                !dispatch.error && (
                  <Empty
                    title={
                      dispatch.loading ? "Loading dispatch" : "No active tasks"
                    }
                    detail={
                      dispatch.loading
                        ? "Fetching the city queue."
                        : "No unassigned, offered, assigned or picked up tasks are currently returned."
                    }
                  />
                )
              )}
            </section>
          )}
          {screen === "merchants" && (
            <section className="qb-panel">
              <div className="qb-panel-head">
                <div>
                  <h2>Approved merchant branches</h2>
                  <p>
                    Live branches accepting orders. Registration review actions
                    are not exposed by this read API.
                  </p>
                </div>
              </div>
              <Notice error={branches.error} />
              {branches.data?.items.length ? (
                <div className="qb-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Branch</th>
                        <th>Category</th>
                        <th>Availability</th>
                      </tr>
                    </thead>
                    <tbody>
                      {branches.data.items.map((branch) => (
                        <tr key={branch.id}>
                          <td>
                            <Building2 size={14} /> {branch.name}
                          </td>
                          <td>{branch.merchant_type ?? "—"}</td>
                          <td>
                            {branch.accepting_orders
                              ? "Accepting orders"
                              : "Paused"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                !branches.error && (
                  <Empty
                    title={
                      branches.loading
                        ? "Loading branches"
                        : "No approved branches"
                    }
                    detail={
                      branches.loading
                        ? "Fetching city branches."
                        : "The API returned no approved, order-accepting branches for this city."
                    }
                  />
                )
              )}
            </section>
          )}
          {screen === "fleet" && (
            <section className="qb-panel">
              <div className="qb-panel-head">
                <div>
                  <h2>Verified pilot fleet</h2>
                  <p>
                    Aggregate state counts from the city fleet endpoint; it does
                    not expose a pilot roster or GPS locations.
                  </p>
                </div>
              </div>
              <Notice error={fleet.error} />
              {fleet.data ? (
                <div className="qb-metrics">
                  {Object.entries(fleet.data.counts).map(([state, count]) => (
                    <Metric
                      key={state}
                      title={state.replaceAll("_", " ")}
                      value={count}
                      icon={Bike}
                    />
                  ))}
                </div>
              ) : (
                <Empty
                  title={fleet.loading ? "Loading fleet" : "Fleet unavailable"}
                  detail={
                    fleet.error ||
                    "Select an authorized city to load the aggregate fleet snapshot."
                  }
                />
              )}
            </section>
          )}
          {screen === "incidents" && <IncidentQueue resource={incidents} />}
          {screen === "ai" && (
            <section className="qb-panel">
              <div className="qb-panel-head">
                <div>
                  <h2>Registered AI model versions</h2>
                  <p>
                    Registry provenance only. Forecasts, drift, accuracy and
                    model health are not inferred here.
                  </p>
                </div>
              </div>
              <Notice error={models.error} />
              {models.data?.items.length ? (
                <div className="qb-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Model</th>
                        <th>Purpose</th>
                        <th>Version</th>
                        <th>Algorithm</th>
                        <th>Status</th>
                        <th>Validation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {models.data.items.map((model) => (
                        <tr key={model.version_id}>
                          <td>{model.name}</td>
                          <td>{model.purpose}</td>
                          <td>{model.version}</td>
                          <td>{model.algorithm}</td>
                          <td>{model.status}</td>
                          <td>
                            {model.validation_passed ? "Passed" : "Not passed"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                !models.error && (
                  <Empty
                    title={
                      models.loading
                        ? "Loading model registry"
                        : "No registered model versions"
                    }
                    detail={
                      models.loading
                        ? "Reading model lifecycle records."
                        : "The registry returned no model versions."
                    }
                  />
                )
              )}
            </section>
          )}
          {screen === "finance" && <RefundApprovalQueue resource={refunds} />}
          {screen === "data" && (
            <BulkImportCenter cityId={cityId} jobs={bulkJobs} />
          )}
          {screen === "customers" && <CustomerDirectory cityId={cityId} />}
          <footer className="qb-footer">
            <span>QUICKBUDDY PLATFORM</span>
            <span>
              Server-side identity · backend scope checks · REST snapshots
            </span>
          </footer>
        </section>
      </main>
    </div>
  );
}

function RefundApprovalQueue({
  resource,
}: {
  resource: Result<{ items: RefundApproval[] }>;
}) {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [reasons, setReasons] = useState<Record<string, string>>({});
  async function decide(
    row: RefundApproval,
    decision: "approved" | "rejected",
  ) {
    const reason = reasons[row.id]?.trim() ?? "";
    if (reason.length < 5) {
      setError("Enter a decision reason of at least 5 characters.");
      return;
    }
    setBusy(row.id);
    setError("");
    try {
      const response = await fetch(
        `/api/backend/api/v1/finance/refund-approvals/${row.id}/decision`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ decision, reason }),
        },
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(body.detail ?? `Decision failed (${response.status})`);
      resource.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Decision failed");
    } finally {
      setBusy("");
    }
  }
  return (
    <section className="qb-panel">
      <div className="qb-panel-head">
        <div>
          <h2>Refund approval requests</h2>
          <p>
            Amounts and decisions come from the finance approval ledger.
            Requesters cannot approve their own requests; the backend rechecks
            finance.write scope.
          </p>
        </div>
      </div>
      <Notice error={error || resource.error} />
      {resource.data?.items.length ? (
        <div className="qb-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Order</th>
                <th>Requested</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Decision reason</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {resource.data.items.map((row) => (
                <tr key={row.id}>
                  <td className="mono">{row.order_id}</td>
                  <td>{new Date(row.created_at).toLocaleString()}</td>
                  <td>{row.amount}</td>
                  <td>{row.status}</td>
                  <td>
                    {row.status === "pending" ? (
                      <input
                        aria-label={`Decision reason for ${row.id}`}
                        maxLength={500}
                        value={reasons[row.id] ?? ""}
                        onChange={(event) =>
                          setReasons((current) => ({
                            ...current,
                            [row.id]: event.target.value,
                          }))
                        }
                        placeholder="Required reason"
                      />
                    ) : (
                      "Recorded in audit trail"
                    )}
                  </td>
                  <td>
                    {row.status === "pending" ? (
                      <div className="qb-inline-actions">
                        <button
                          className="qb-outline"
                          disabled={busy === row.id}
                          onClick={() => void decide(row, "approved")}
                        >
                          Approve
                        </button>
                        <button
                          className="qb-outline"
                          disabled={busy === row.id}
                          onClick={() => void decide(row, "rejected")}
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        !resource.error && (
          <Empty
            title={
              resource.loading ? "Loading approvals" : "No refund requests"
            }
            detail={
              resource.loading
                ? "Reading organization scoped finance records."
                : "No refund requests exist in the selected organization."
            }
          />
        )
      )}
    </section>
  );
}

const branchImportFields = [
  "external_ref",
  "brand_id",
  "city_id",
  "branch_name",
  "latitude",
  "longitude",
] as const;

function csvHeaderCells(line: string) {
  const cells: string[] = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"' && quoted && line[i + 1] === '"') {
      value += '"';
      i += 1;
    } else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) {
      cells.push(value.trim());
      value = "";
    } else value += char;
  }
  cells.push(value.trim());
  return cells.map((cell) => cell.replace(/^\uFEFF/, ""));
}

function BulkImportCenter({
  cityId,
  jobs,
}: {
  cityId: string;
  jobs: Result<{ items: BulkJob[] }>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [job, setJob] = useState<BulkJob | null>(null);
  const [preview, setPreview] = useState<{
    rows: {
      row_number: number;
      status: string;
      branch_name: string;
      external_ref: string;
      issues: { field: string; code: string }[];
    }[];
  } | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function call(
    path: string,
    body?: unknown,
    headersIn?: HeadersInit,
    methodOverride?: "GET" | "POST",
  ) {
    const response = await fetch(`/api/backend/api/v1/${path}`, {
      method: methodOverride ?? (body === undefined ? "GET" : "POST"),
      headers:
        body === undefined
          ? headersIn
          : {
              "content-type": "application/json",
              ...Object.fromEntries(new Headers(headersIn)),
            },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    const data = response.headers.get("content-type")?.includes("json")
      ? await response.json().catch(() => ({}))
      : await response.text();
    if (!response.ok) {
      const detail =
        typeof data === "object" && data && "detail" in data
          ? String(data.detail)
          : `Request failed (${response.status})`;
      throw new Error(detail);
    }
    return data as Record<string, unknown>;
  }

  async function showPreview(currentJob: BulkJob) {
    const result = (await call(
      `bulk/imports/${currentJob.id}/dry-run`,
      undefined,
      undefined,
      "POST",
    )) as unknown as {
      rows: NonNullable<typeof preview>["rows"];
    } & BulkJob;
    setJob(result);
    setPreview(result);
    jobs.reload();
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    setBusy("upload");
    setError("");
    setNotice("");
    setPreview(null);
    try {
      if (
        !file.name.toLowerCase().endsWith(".csv") ||
        file.size > 5 * 1024 * 1024
      )
        throw new Error("Choose a CSV file no larger than 5 MiB.");
      let source: string;
      try {
        source = new TextDecoder("utf-8", { fatal: true }).decode(
          await file.arrayBuffer(),
        );
      } catch {
        throw new Error("CSV must be valid UTF-8 text.");
      }
      const firstLine = source.split(/\r?\n/, 1)[0];
      const fields = csvHeaderCells(firstLine);
      if (fields.length > 20 || fields.some((field) => !field))
        throw new Error("CSV must have at most 20 non-empty column headers.");
      setHeaders(fields);
      const initialMap = Object.fromEntries(
        branchImportFields.map((field) => [
          field,
          fields.find(
            (header) =>
              header
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "_")
                .replace(/^_|_$/g, "") === field,
          ) ?? "",
        ]),
      );
      setMapping(initialMap);
      const response = await fetch("/api/backend/api/v1/bulk/imports", {
        method: "POST",
        headers: {
          "content-type": "text/csv; charset=utf-8",
          "x-bulk-entity": "branches",
          "idempotency-key": crypto.randomUUID(),
        },
        body: source,
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(result.detail ?? `Upload failed (${response.status})`);
      const createdJob = result as BulkJob;
      setJob(createdJob);
      const exactTemplate = branchImportFields.every(
        (field) => initialMap[field],
      );
      if (exactTemplate) await showPreview(createdJob);
      else
        setNotice(
          "Map each required field to a CSV column, then preview the changes.",
        );
      jobs.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "CSV upload failed.");
    } finally {
      setBusy("");
    }
  }

  async function mapAndPreview() {
    if (!job) return;
    setBusy("mapping");
    setError("");
    try {
      await call(`bulk/imports/${job.id}/mapping`, { mapping });
      await showPreview(job);
      setNotice(
        "Preview only: successful rows create pending branches. They remain closed until separately approved.",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Mapping failed.");
    } finally {
      setBusy("");
    }
  }

  async function commitImport() {
    if (!job) return;
    setBusy("commit");
    setError("");
    try {
      const result = (await call(
        `bulk/imports/${job.id}/commit`,
      )) as unknown as BulkJob;
      setJob(result);
      setNotice(
        `${result.created_count} pending branches created; ${result.failed_count} rows failed.`,
      );
      jobs.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Commit failed.");
    } finally {
      setBusy("");
    }
  }

  async function cancelImport() {
    if (!job) return;
    setBusy("cancel");
    setError("");
    try {
      const result = (await call(
        `bulk/jobs/${job.id}/cancel`,
        {},
      )) as unknown as BulkJob;
      setJob(result);
      setPreview(null);
      setNotice("The uncommitted import job was cancelled.");
      jobs.reload();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Cancellation failed.",
      );
    } finally {
      setBusy("");
    }
  }

  async function exportBranches() {
    if (!cityId) return;
    setBusy("export");
    setError("");
    try {
      const response = await fetch("/api/backend/api/v1/bulk/exports", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          entity: "branches",
          city_id: cityId,
          limit: 500,
        }),
      });
      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        throw new Error(result.detail ?? `Export failed (${response.status})`);
      }
      const objectUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download =
        response.headers
          .get("content-disposition")
          ?.match(/filename="([^"]+)"/)?.[1] ?? "quickbuddy-branches.csv";
      link.click();
      URL.revokeObjectURL(objectUrl);
      setNotice(
        "Authorized branch export downloaded. The backend recorded the export audit event.",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Export failed.");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="qb-bulk-layout">
      <section className="qb-panel qb-bulk-panel">
        <div className="qb-panel-head">
          <div>
            <h2>Branch onboarding import</h2>
            <p>
              CSV only · 5 MiB maximum · 5,000 rows maximum · imports create
              pending branches
            </p>
          </div>
          <a
            className="qb-outline qb-bulk-template"
            href="/api/backend/api/v1/bulk/templates/branches"
          >
            <Download size={14} /> CSV template
          </a>
        </div>
        <form className="qb-bulk-upload" onSubmit={upload}>
          <label className="qb-bulk-drop">
            <Upload size={20} />
            <b>{file?.name ?? "Choose a branch CSV"}</b>
            <span>
              Stable external reference, brand and city IDs, name and
              coordinates
            </span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <button className="qb-primary" disabled={!file || Boolean(busy)}>
            {busy === "upload" ? "Validating…" : "Upload and validate"}
          </button>
        </form>
        {headers.length > 0 &&
          job &&
          !job.previewed &&
          job.status !== "CANCELLED" && (
            <div className="qb-bulk-map">
              <h3>Map columns</h3>
              <div className="qb-bulk-map-grid">
                {branchImportFields.map((field) => (
                  <label key={field}>
                    {field.replaceAll("_", " ")}
                    <select
                      value={mapping[field] ?? ""}
                      onChange={(event) =>
                        setMapping((old) => ({
                          ...old,
                          [field]: event.target.value,
                        }))
                      }
                    >
                      <option value="">Choose column</option>
                      {headers.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
              <button
                className="qb-outline"
                disabled={
                  Boolean(busy) ||
                  branchImportFields.some((field) => !mapping[field])
                }
                onClick={() => void mapAndPreview()}
              >
                {busy === "mapping" ? "Mapping…" : "Map columns and preview"}
              </button>
            </div>
          )}
        {error && <Notice error={error} />}
        {notice && (
          <div className="qb-unavailable" role="status">
            {notice}
          </div>
        )}
        {job && (
          <div className="qb-bulk-job">
            <div className="qb-bulk-job-heading">
              <div>
                <b>Import preview</b>
                <small>Job {job.id}</small>
              </div>
              <span className={`qb-status-pill ${job.status.toLowerCase()}`}>
                {job.status}
              </span>
            </div>
            <div className="qb-bulk-stats">
              <span>
                <b>{job.row_count}</b> rows
              </span>
              <span>
                <b>{job.valid_count}</b> eligible
              </span>
              <span>
                <b>{job.failed_count}</b> with errors
              </span>
            </div>
            {preview && (
              <div className="qb-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Row</th>
                      <th>Branch</th>
                      <th>Source ref</th>
                      <th>Result</th>
                      <th>Issues</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((row) => (
                      <tr key={row.row_number}>
                        <td>{row.row_number}</td>
                        <td>{row.branch_name}</td>
                        <td>{row.external_ref}</td>
                        <td>{row.status}</td>
                        <td>
                          {row.issues
                            .map((issue) => `${issue.field}: ${issue.code}`)
                            .join("; ") || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {job.previewed && job.status === "VALIDATED" && (
              <div className="qb-bulk-actions">
                <p>
                  Commit creates branches in pending review status. No branch is
                  auto-approved or opened for orders.
                </p>
                <button
                  className="qb-primary"
                  disabled={!job.valid_count || Boolean(busy)}
                  onClick={() => void commitImport()}
                >
                  {busy === "commit"
                    ? "Committing…"
                    : `Commit ${job.valid_count} valid rows`}
                </button>
                <button
                  className="qb-outline"
                  disabled={Boolean(busy)}
                  onClick={() => void cancelImport()}
                >
                  {busy === "cancel" ? "Cancelling…" : "Cancel import"}
                </button>
              </div>
            )}
            {!job.previewed && job.status === "VALIDATED" && (
              <button
                className="qb-outline"
                disabled={Boolean(busy)}
                onClick={() => void cancelImport()}
              >
                {busy === "cancel" ? "Cancelling…" : "Cancel import"}
              </button>
            )}
          </div>
        )}
      </section>
      <section className="qb-panel">
        <div className="qb-panel-head">
          <div>
            <h2>Branch export</h2>
            <p>
              Authorized rows in the selected city · CSV capped at 500 rows ·
              audited
            </p>
          </div>
        </div>
        <button
          className="qb-outline"
          disabled={!cityId || Boolean(busy)}
          onClick={() => void exportBranches()}
        >
          <Download size={14} />{" "}
          {busy === "export" ? "Preparing…" : "Export selected city"}
        </button>
        <p className="qb-bulk-privacy">
          Customer contact, payment, KYC and settlement data are not included in
          this export. Exports are generated on demand and are not stored as
          public files.
        </p>
      </section>
      <section className="qb-panel qb-bulk-history">
        <div className="qb-panel-head">
          <div>
            <h2>Recent jobs</h2>
            <p>Only jobs created by your current account are shown.</p>
          </div>
          <button className="qb-link" onClick={jobs.reload}>
            Refresh
          </button>
        </div>
        <Notice error={jobs.error} />
        {jobs.data?.items.length ? (
          <div className="qb-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Entity</th>
                  <th>Status</th>
                  <th>Rows</th>
                  <th>Created</th>
                  <th>Errors</th>
                </tr>
              </thead>
              <tbody>
                {jobs.data.items.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td>{item.entity}</td>
                    <td>{item.status}</td>
                    <td>{item.row_count}</td>
                    <td>{item.created_count}</td>
                    <td>{item.failed_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title={jobs.loading ? "Loading jobs" : "No import jobs yet"}
            detail={
              jobs.loading
                ? "Fetching your private job history."
                : "Completed and validated jobs will appear here."
            }
          />
        )}
      </section>
    </div>
  );
}

function IncidentQueue({
  resource,
}: {
  resource: Result<{ items: Incident[] }>;
}) {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [resolution, setResolution] = useState<Record<string, string>>({});
  async function act(incident: Incident, action: "acknowledge" | "resolve") {
    const summary = resolution[incident.id]?.trim() ?? "";
    if (action === "resolve" && summary.length < 10) {
      setError("Enter a resolution summary of at least 10 characters.");
      return;
    }
    setBusy(incident.id);
    setError("");
    try {
      const response = await fetch(
        `/api/backend/api/v1/operations/pilot-incidents/${incident.id}/${action}`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body:
            action === "resolve"
              ? JSON.stringify({ resolution_summary: summary })
              : undefined,
        },
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(body.detail ?? `Action failed (${response.status})`);
      resource.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Action failed");
    } finally {
      setBusy("");
    }
  }
  return (
    <section className="qb-panel">
      <div className="qb-panel-head">
        <div>
          <h2>Pilot incident queue</h2>
          <p>
            Actions are revalidated by city scope and incident state on the
            backend.
          </p>
        </div>
      </div>
      <Notice error={error || resource.error} />
      {resource.data?.items.length ? (
        <div className="qb-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Severity / category</th>
                <th>Summary</th>
                <th>State</th>
                <th>Reported</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {resource.data.items.map((incident) => (
                <tr key={incident.id}>
                  <td>
                    {incident.severity} · {incident.category}
                    {incident.safety_emergency && (
                      <strong className="qb-danger-label">
                        {" "}
                        Safety emergency
                      </strong>
                    )}
                  </td>
                  <td>{incident.summary}</td>
                  <td>{incident.status}</td>
                  <td>{new Date(incident.created_at).toLocaleString()}</td>
                  <td>
                    {incident.status === "open" ? (
                      <button
                        className="qb-outline"
                        disabled={busy === incident.id}
                        onClick={() => void act(incident, "acknowledge")}
                      >
                        <Check size={13} /> Acknowledge
                      </button>
                    ) : incident.status === "acknowledged" ? (
                      <div className="qb-incident-resolve">
                        <input
                          aria-label="Resolution summary"
                          value={resolution[incident.id] ?? ""}
                          onChange={(event) =>
                            setResolution((current) => ({
                              ...current,
                              [incident.id]: event.target.value,
                            }))
                          }
                          minLength={10}
                          maxLength={1000}
                          placeholder="Resolution summary"
                        />
                        <button
                          className="qb-outline"
                          disabled={busy === incident.id}
                          onClick={() => void act(incident, "resolve")}
                        >
                          <Check size={13} /> Resolve
                        </button>
                      </div>
                    ) : (
                      (incident.resolution_summary ?? "Resolved")
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        !resource.error && (
          <Empty
            title={
              resource.loading ? "Loading incident queue" : "No pilot incidents"
            }
            detail={
              resource.loading
                ? "Fetching incidents for the selected city."
                : "No pilot-reported incidents were returned."
            }
          />
        )
      )}
    </section>
  );
}

export function CityOperationsWorkspace() {
  const [cityId, setCityId] = useState("");
  const cities = useLive<{ items: City[] }>(
    "api/v1/operations/authorized-cities?limit=100",
  );
  useEffect(() => {
    if (!cityId && cities.data?.items.length)
      setCityId(cities.data.items[0].id);
  }, [cityId, cities.data]);
  const selected = cities.data?.items.find((city) => city.id === cityId);
  const dispatch = useLive<Dispatch>(
    cityId ? `api/v1/operations/cities/${cityId}/dispatch?limit=50` : null,
  );
  const incidents = useLive<{ items: Incident[] }>(
    cityId
      ? `api/v1/operations/cities/${cityId}/pilot-incidents?limit=50`
      : null,
  );
  return (
    <div className="qb-admin">
      <aside className="qb-sidebar">
        <a className="qb-brand" href="/">
          <span className="qb-brandmark">
            <Command size={19} />
          </span>
          <span>
            quickbuddy<span className="brand-dot">.</span>
            <small>CITY OPERATIONS</small>
          </span>
        </a>
        <div className="qb-nav-label">CITY WORKSPACE</div>
        <div className="qb-nav-item active">
          <Activity size={16} />
          <span>Dispatch & incidents</span>
        </div>
        <div className="qb-sidebar-bottom">
          <ShieldCheck size={15} /> Backend enforced city scope
        </div>
      </aside>
      <main className="qb-main">
        <header className="qb-topbar">
          <div className="qb-breadcrumb">
            <span>Quickbuddy</span>
            <b>/</b>
            <strong>City Operations</strong>
          </div>
          <div className="qb-top-actions">
            <label className="qb-city-select">
              <MapPin size={14} />
              <select
                aria-label="Authorized city"
                value={cityId}
                onChange={(e) => setCityId(e.target.value)}
              >
                <option value="">Select city</option>
                {(cities.data?.items ?? []).map((city) => (
                  <option key={city.id} value={city.id}>
                    {city.name}
                  </option>
                ))}
              </select>
              <ChevronDown size={13} />
            </label>
          </div>
        </header>
        <section className="qb-content">
          <div className="qb-page-title">
            <div>
              <div className="qb-eyebrow">
                <Activity size={12} /> CITY OPERATIONS
              </div>
              <h1>Dispatch & pilot incidents</h1>
              <p>
                {selected
                  ? `${selected.name} · authorized operational snapshots`
                  : "Select a city. Every operation is checked against your assigned city scope."}
              </p>
            </div>
            <div className="qb-page-actions">
              <button
                className="qb-outline"
                onClick={() => {
                  cities.reload();
                  dispatch.reload();
                  incidents.reload();
                }}
              >
                <RefreshCw size={14} /> Refresh
              </button>
            </div>
          </div>
          <Notice error={cities.error} />
          <div className="qb-metrics">
            <Metric
              title="Unassigned tasks"
              value={dispatch.data?.counts.unassigned ?? "—"}
              icon={Clock3}
            />
            <Metric
              title="Offers pending"
              value={dispatch.data?.counts.offered ?? "—"}
              icon={Activity}
            />
            <Metric
              title="Assigned"
              value={dispatch.data?.counts.assigned ?? "—"}
              icon={Bike}
            />
            <Metric
              title="Open pilot incidents"
              value={
                incidents.data?.items.filter(
                  (item) => item.status !== "resolved",
                ).length ?? "—"
              }
              icon={AlertTriangle}
            />
          </div>
          <div className="qb-grid-two">
            <section className="qb-panel">
              <div className="qb-panel-head">
                <div>
                  <h2>Dispatch queue</h2>
                  <p>
                    Cursor-limited current tasks; sensitive customer and pilot
                    records are not returned.
                  </p>
                </div>
              </div>
              <Notice error={dispatch.error} />
              {dispatch.data?.tasks.length ? (
                <div className="qb-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Task ID</th>
                        <th>Status</th>
                        <th>Version</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dispatch.data.tasks.map((task) => (
                        <tr key={task.id}>
                          <td className="mono">{task.id}</td>
                          <td>{task.status.replaceAll("_", " ")}</td>
                          <td>{task.version}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                !dispatch.error && (
                  <Empty
                    title={
                      dispatch.loading ? "Loading dispatch" : "No active tasks"
                    }
                    detail={
                      dispatch.loading
                        ? "Loading the authorized city queue."
                        : "The dispatch API returned no active tasks."
                    }
                  />
                )
              )}
            </section>
            <IncidentQueue resource={incidents} />
          </div>
          <div className="qb-unavailable">
            <ShieldCheck size={16} /> Manual task reassignment and live GPS maps
            are not exposed by the current authorized API contracts.
          </div>
          <footer className="qb-footer">
            <span>QUICKBUDDY PLATFORM</span>
            <span>
              REST snapshots · 30 second refresh · city scope enforced
              server-side
            </span>
          </footer>
        </section>
      </main>
    </div>
  );
}

type SupportTicket = {
  id: string;
  subject: string;
  status: string;
  order_id: string | null;
  created_at: string;
  assigned_to_me: boolean;
};
type TicketMessage = {
  id: string;
  body: string;
  author: "agent" | "customer";
  created_at: string;
};
export function SupportConsoleWorkspace() {
  const tickets = useLive<{ items: SupportTicket[] }>(
    "api/v1/support/tickets?limit=50",
  );
  const [selectedId, setSelectedId] = useState("");
  const selected =
    tickets.data?.items.find((ticket) => ticket.id === selectedId) ??
    tickets.data?.items[0];
  useEffect(() => {
    if (!selectedId && tickets.data?.items.length)
      setSelectedId(tickets.data.items[0].id);
  }, [selectedId, tickets.data]);
  const messages = useLive<{ items: TicketMessage[] }>(
    selected?.assigned_to_me
      ? `api/v1/support/tickets/${selected.id}/messages`
      : null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function ticketAction(path: string, body?: unknown) {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(
        `/api/backend/api/v1/support/tickets/${selected.id}/${path}`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: body === undefined ? undefined : JSON.stringify(body),
        },
      );
      const result = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(result.detail ?? `Request failed (${response.status})`);
      tickets.reload();
      messages.reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  async function reply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = String(form.get("body") ?? "").trim();
    if (!body) return;
    await ticketAction("messages", { body });
    event.currentTarget.reset();
  }
  return (
    <div className="qb-admin">
      <aside className="qb-sidebar">
        <a className="qb-brand" href="/">
          <span className="qb-brandmark">
            <Command size={19} />
          </span>
          <span>
            quickbuddy<span className="brand-dot">.</span>
            <small>QUICKBUDDY CARE</small>
          </span>
        </a>
        <div className="qb-nav-label">SUPPORT</div>
        <div className="qb-nav-item active">
          <FileText size={16} />
          <span>Ticket inbox</span>
        </div>
        <div className="qb-sidebar-bottom">
          <ShieldCheck size={15} /> Assigned ticket access
        </div>
      </aside>
      <main className="qb-main">
        <header className="qb-topbar">
          <div className="qb-breadcrumb">
            <span>Quickbuddy</span>
            <b>/</b>
            <strong>Support Console</strong>
          </div>
          <div className="qb-top-actions">
            <button className="qb-outline" onClick={tickets.reload}>
              <RefreshCw size={14} /> Refresh queue
            </button>
          </div>
        </header>
        <section className="qb-content">
          <div className="qb-page-title">
            <div>
              <div className="qb-eyebrow">
                <ShieldCheck size={12} /> QUICKBUDDY CARE
              </div>
              <h1>Support ticket inbox</h1>
              <p>
                Only unassigned tickets and tickets assigned to you are listed.
                Claim before opening a conversation.
              </p>
            </div>
          </div>
          <Notice error={tickets.error || error} />
          {tickets.data?.items.length ? (
            <div className="qb-grid-two">
              <section className="qb-panel">
                <div className="qb-panel-head">
                  <div>
                    <h2>Queue</h2>
                    <p>{tickets.data.items.length} tickets in this page</p>
                  </div>
                </div>
                <div className="qb-support-list">
                  {tickets.data.items.map((ticket) => (
                    <button
                      key={ticket.id}
                      className={`qb-support-item ${selected?.id === ticket.id ? "selected" : ""}`}
                      onClick={() => setSelectedId(ticket.id)}
                    >
                      <b>{ticket.subject}</b>
                      <span>
                        {ticket.status}{" "}
                        {ticket.assigned_to_me
                          ? "· assigned to you"
                          : "· unassigned"}
                      </span>
                      <small>
                        {ticket.order_id
                          ? `Order ${ticket.order_id}`
                          : "No order reference"}{" "}
                        · {new Date(ticket.created_at).toLocaleString()}
                      </small>
                    </button>
                  ))}
                </div>
              </section>
              <section className="qb-panel">
                <div className="qb-panel-head">
                  <div>
                    <h2>{selected?.subject}</h2>
                    <p>
                      {selected?.order_id
                        ? `Order reference ${selected.order_id}`
                        : "No order reference attached"}{" "}
                      · {selected?.status}
                    </p>
                  </div>
                  {selected && !selected.assigned_to_me && (
                    <button
                      className="qb-primary"
                      disabled={busy}
                      onClick={() => void ticketAction("claim")}
                    >
                      <Check size={13} /> Claim ticket
                    </button>
                  )}
                </div>
                {selected?.assigned_to_me ? (
                  <>
                    <Notice error={messages.error} />
                    <div className="qb-thread">
                      {messages.data?.items.length
                        ? messages.data.items.map((message) => (
                            <article
                              className={`qb-message ${message.author}`}
                              key={message.id}
                            >
                              <small>
                                {message.author} ·{" "}
                                {new Date(message.created_at).toLocaleString()}
                              </small>
                              <p>{message.body}</p>
                            </article>
                          ))
                        : !messages.error && (
                            <Empty
                              title={
                                messages.loading
                                  ? "Loading conversation"
                                  : "No messages"
                              }
                              detail={
                                messages.loading
                                  ? "Loading the assigned ticket conversation."
                                  : "The ticket has no messages yet."
                              }
                            />
                          )}
                    </div>
                    {selected.status !== "resolved" ? (
                      <form className="qb-reply" onSubmit={reply}>
                        <textarea
                          name="body"
                          placeholder="Reply to the customer"
                          required
                          maxLength={5000}
                        />
                        <button className="qb-primary" disabled={busy}>
                          Send reply
                        </button>
                        <button
                          type="button"
                          className="qb-outline"
                          disabled={busy}
                          onClick={() => void ticketAction("resolve")}
                        >
                          Resolve ticket
                        </button>
                      </form>
                    ) : (
                      <div className="qb-unavailable">Ticket resolved.</div>
                    )}
                  </>
                ) : (
                  <Empty
                    title="Ticket not claimed"
                    detail="Claim this case to read the customer conversation and reply. The backend will reject claims outside your support scope."
                  />
                )}
              </section>
            </div>
          ) : (
            !tickets.error && (
              <Empty
                title={
                  tickets.loading
                    ? "Loading ticket queue"
                    : "No tickets available"
                }
                detail={
                  tickets.loading
                    ? "Fetching your scoped support queue."
                    : "No unassigned or personally assigned tickets were returned."
                }
              />
            )
          )}
          <div className="qb-unavailable">
            <AlertTriangle size={16} /> Customer phone, email, addresses and
            unrestricted order details are intentionally excluded from this
            ticket list.
          </div>
          <footer className="qb-footer">
            <span>QUICKBUDDY CARE</span>
            <span>Ticket claims and replies are checked by the backend</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

function CustomerDirectory({ cityId }: { cityId: string }) {
  const [query, setQuery] = useState("");
  const [settledQuery, setSettledQuery] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setSettledQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState("overview");
  const [minimumOrders, setMinimumOrders] = useState("1");
  const [dormantDays, setDormantDays] = useState("");
  const [segmentCount, setSegmentCount] = useState<number | null>(null);
  const [segmentError, setSegmentError] = useState("");
  const [segmentBusy, setSegmentBusy] = useState(false);
  const path = cityId
    ? `api/v1/admin/customers?city_id=${cityId}&limit=50${settledQuery ? `&q=${encodeURIComponent(settledQuery)}` : ""}`
    : null;
  const customers = useLive<{
    items: CustomerRow[];
    next_cursor: string | null;
  }>(path);
  const detail = useLive<{
    customer: Omit<
      CustomerRow,
      | "order_count"
      | "completed_order_count"
      | "gross_purchase_value"
      | "last_order_at"
      | "created_at"
    > & { registered_at: string };
    summary: Record<string, string | number | null>;
  }>(selectedId ? `api/v1/admin/customers/${selectedId}` : null);
  const tabData = useLive<{
    items?: Record<string, unknown>[];
    accounts?: Record<string, unknown>[];
    transactions?: Record<string, unknown>[];
    refunds?: Record<string, unknown>[];
    events?: Record<string, unknown>[];
    notification_preferences?: Record<string, unknown>[];
    preference_keys?: string[];
    marketing_consent_evidence?: Record<string, unknown>[];
    active_session_count?: number;
  }>(
    selectedId && tab !== "overview"
      ? `api/v1/admin/customers/${selectedId}/${tab}`
      : null,
  );
  const tabs = [
    "overview",
    "orders",
    "payments",
    "addresses",
    "subscriptions",
    "loyalty",
    "referrals",
    "campaigns",
    "support",
    "feedback",
    "privacy",
    "security",
  ];

  async function previewSegment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!cityId) return;
    setSegmentBusy(true);
    setSegmentError("");
    try {
      const conditions: { field: string; op: string; value: number }[] = [
        { field: "order_count", op: "gte", value: Number(minimumOrders) },
      ];
      if (dormantDays)
        conditions.push({
          field: "last_order_days",
          op: "gte",
          value: Number(dormantDays),
        });
      const response = await fetch(
        "/api/backend/api/v1/admin/customer-segments/preview",
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ city_id: cityId, logic: "and", conditions }),
          cache: "no-store",
        },
      );
      const result = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(result.detail ?? `Preview failed (${response.status})`);
      setSegmentCount(Number(result.matched_count));
    } catch (reason) {
      setSegmentError(
        reason instanceof Error ? reason.message : "Segment preview failed.",
      );
    } finally {
      setSegmentBusy(false);
    }
  }

  async function exportCustomers() {
    if (!cityId) return;
    const response = await fetch(
      `/api/backend/api/v1/admin/customers-export?city_id=${cityId}&limit=500&purpose=customer_directory`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      const result = await response.json().catch(() => ({}));
      window.alert(result.detail ?? `Export failed (${response.status})`);
      return;
    }
    const blobUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download =
      response.headers
        .get("content-disposition")
        ?.match(/filename="([^"]+)"/)?.[1] ?? "quickbuddy-customers.csv";
    link.click();
    URL.revokeObjectURL(blobUrl);
  }

  return (
    <section className="qb-customer-workspace">
      <section className="qb-panel qb-customer-directory">
        <div className="qb-panel-head">
          <div>
            <h2>Customer directory</h2>
            <p>
              Authorized city scope · masked contact details · cursor pagination
            </p>
          </div>
          <button
            className="qb-outline"
            disabled={!cityId}
            onClick={() => void exportCustomers()}
          >
            <Download size={14} /> Export safe fields
          </button>
        </div>
        <label className="qb-customer-search">
          Search by customer name
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Start typing a name"
          />
        </label>
        <form className="qb-segment-preview" onSubmit={previewSegment}>
          <div>
            <b>Segment preview</b>
            <small>
              Current authorized city · exact count · no audience export
            </small>
          </div>
          <label>
            Minimum orders
            <input
              type="number"
              min="0"
              max="100000"
              value={minimumOrders}
              onChange={(event) => setMinimumOrders(event.target.value)}
            />
          </label>
          <label>
            Dormant days
            <input
              type="number"
              min="1"
              max="3650"
              placeholder="Any"
              value={dormantDays}
              onChange={(event) => setDormantDays(event.target.value)}
            />
          </label>
          <button className="qb-outline" disabled={!cityId || segmentBusy}>
            {segmentBusy ? "Counting…" : "Preview segment"}
          </button>
          {segmentCount !== null && (
            <small className="qb-segment-count">
              {segmentCount.toLocaleString()} matching customers
            </small>
          )}
          {segmentError && (
            <small className="qb-segment-error">{segmentError}</small>
          )}
        </form>
        {!cityId ? (
          <Empty
            title="Select a city"
            detail="Customer records are scoped to authorized cities."
          />
        ) : customers.error ? (
          <Notice error={customers.error} />
        ) : (
          <div className="qb-customer-list">
            {(customers.data?.items ?? []).map((row) => (
              <button
                key={row.id}
                className={`qb-customer-card ${selectedId === row.id ? "selected" : ""}`}
                onClick={() => {
                  setSelectedId(row.id);
                  setTab("overview");
                }}
              >
                <span className="qb-customer-avatar">
                  {row.name?.slice(0, 1)?.toUpperCase() ?? "C"}
                </span>
                <span className="qb-customer-identity">
                  <b>{row.name || "Unnamed customer"}</b>
                  <small>
                    {row.email ?? row.phone ?? "No contact on file"}
                  </small>
                </span>
                <span className="qb-customer-metrics">
                  <b>{row.order_count} orders</b>
                  <small>{row.status}</small>
                </span>
              </button>
            ))}
            {!customers.loading && !customers.data?.items.length && (
              <Empty
                title="No customers in this scope"
                detail="Try another city or a shorter name search."
              />
            )}
          </div>
        )}
        <p className="qb-customer-privacy">
          This directory masks contact details and omits addresses and payment
          identifiers. Values are historical gross purchases; refunds and
          discount funding are not deducted.
        </p>
      </section>
      <section className="qb-panel qb-customer-profile">
        {!selectedId ? (
          <Empty
            title="Select a customer"
            detail="Customer 360 loads only after you open a record."
          />
        ) : detail.error ? (
          <Notice error={detail.error} />
        ) : detail.loading || !detail.data ? (
          <Empty
            title="Loading Customer 360"
            detail="Retrieving an authorized summary."
          />
        ) : (
          <>
            <div className="qb-customer-profile-head">
              <span className="qb-customer-avatar large">
                {detail.data.customer.name?.slice(0, 1)?.toUpperCase() ?? "C"}
              </span>
              <div>
                <h2>{detail.data.customer.name || "Unnamed customer"}</h2>
                <p>
                  {detail.data.customer.status} · Registered{" "}
                  {new Date(
                    detail.data.customer.registered_at,
                  ).toLocaleDateString()}
                </p>
                <small>
                  {detail.data.customer.email ?? "Email unavailable"} ·{" "}
                  {detail.data.customer.phone ?? "Phone unavailable"}
                </small>
              </div>
            </div>
            <div className="qb-customer-tabs" role="tablist">
              {tabs.map((name) => (
                <button
                  key={name}
                  role="tab"
                  aria-selected={tab === name}
                  className={tab === name ? "active" : ""}
                  onClick={() => setTab(name)}
                >
                  {name}
                </button>
              ))}
            </div>
            {tab === "overview" ? (
              <div className="qb-customer-summary-grid">
                {[
                  ["Orders", detail.data.summary.order_count],
                  ["Completed", detail.data.summary.completed_order_count],
                  [
                    "Gross purchases",
                    `₹${detail.data.summary.gross_purchase_value}`,
                  ],
                  ["Refunds", `₹${detail.data.summary.refund_total}`],
                  [
                    "Loyalty points",
                    detail.data.summary.loyalty_points_balance,
                  ],
                  [
                    "Last order",
                    detail.data.summary.last_order_at
                      ? new Date(
                          String(detail.data.summary.last_order_at),
                        ).toLocaleDateString()
                      : "—",
                  ],
                ].map(([label, value]) => (
                  <article key={String(label)}>
                    <small>{label}</small>
                    <b>{value}</b>
                  </article>
                ))}
                <p>{detail.data.summary.historical_contribution_note}</p>
              </div>
            ) : tabData.error ? (
              <Notice error={tabData.error} />
            ) : tabData.loading ? (
              <Empty
                title={`Loading ${tab}`}
                detail="Fetching a bounded customer history page."
              />
            ) : (
              <div className="qb-customer-tab-data">
                {tab === "privacy" && (
                  <article>
                    <b>Marketing consent</b>
                    <small>
                      Customer-authored consent events. Notification preferences
                      are shown separately.
                      {tabData.data?.preference_keys?.length
                        ? ` Other preference keys: ${tabData.data.preference_keys.join(", ")}`
                        : " No other preference keys are recorded."}
                    </small>
                  </article>
                )}
                {tab === "security" && (
                  <article>
                    <b>
                      {tabData.data?.active_session_count ?? 0} active sessions
                    </b>
                    <small>
                      Read-only security summary; session revocation is not
                      available in CRM.
                    </small>
                  </article>
                )}
                {(tabData.data?.items ?? tabData.data?.accounts ?? []).map(
                  (row, index) => (
                    <article key={String(row.id ?? `${tab}-${index}`)}>
                      <b>
                        {String(
                          row.subject ??
                            row.plan ??
                            row.program ??
                            row.status ??
                            row.rating ??
                            "Customer record",
                        )}
                      </b>
                      <small>
                        {Object.entries(row)
                          .filter(([key]) => key !== "id")
                          .map(
                            ([key, value]) =>
                              `${key.replaceAll("_", " ")}: ${String(value ?? "—")}`,
                          )
                          .join(" · ")}
                      </small>
                    </article>
                  ),
                )}
                {tab === "loyalty" &&
                  (tabData.data?.transactions ?? []).map((row, index) => (
                    <article key={`txn-${index}`}>
                      <b>{String(row.points)} points movement</b>
                      <small>{String(row.created_at)}</small>
                    </article>
                  ))}
                {[
                  ...(tabData.data?.refunds ?? []),
                  ...(tabData.data?.notification_preferences ?? []),
                  ...(tabData.data?.marketing_consent_evidence ?? []),
                  ...(tabData.data?.events ?? []),
                ].map((row, index) => (
                  <article key={`extra-${index}`}>
                    <b>
                      {String(
                        row.status ??
                          row.channel ??
                          row.type ??
                          ("enabled" in row
                            ? `Marketing ${row.enabled ? "opt-in" : "opt-out"}`
                            : "Record"),
                      )}
                    </b>
                    <small>
                      {Object.entries(row)
                        .map(
                          ([key, value]) =>
                            `${key.replaceAll("_", " ")}: ${String(value ?? "—")}`,
                        )
                        .join(" · ")}
                    </small>
                  </article>
                ))}
                {!tabData.data?.items?.length &&
                  !tabData.data?.accounts?.length &&
                  !tabData.data?.transactions?.length &&
                  !tabData.data?.refunds?.length &&
                  !tabData.data?.notification_preferences?.length &&
                  !tabData.data?.marketing_consent_evidence?.length &&
                  !tabData.data?.events?.length &&
                  !tabData.data?.preference_keys?.length &&
                  !tabData.data?.active_session_count && (
                    <Empty
                      title={`No ${tab} records`}
                      detail="No records are available in the connected Quickbuddy systems."
                    />
                  )}
              </div>
            )}
          </>
        )}
      </section>
    </section>
  );
}
