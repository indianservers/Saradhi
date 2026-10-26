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
  Clock3,
  Command,
  FileText,
  LayoutDashboard,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Store,
} from "lucide-react";

type City = { id: string; name: string };
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
    const run = async () => {
      try {
        const response = await fetch(`/api/backend/${path}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok)
          throw new Error(body.detail ?? `Backend returned ${response.status}`);
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
      }
    };
    setLoading(true);
    void run();
    const timer = window.setInterval(() => void run(), 30_000);
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
  ] as const;
  const health = [dispatch, fleet, incidents].some((x) => x.error)
    ? "Limited"
    : [dispatch, fleet, incidents].every((x) => x.data !== null)
      ? "Connected"
      : "Checking";
  const refresh = () =>
    [cities, dispatch, fleet, incidents, branches, models].forEach((resource) =>
      resource.reload(),
    );
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
