import {
  ArrowUpRight,
  Boxes,
  ChevronRight,
  CircleHelp,
  Command,
  MapPin,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
export { AdminControlTower } from "./admin-control-tower";

export function Shell({
  title,
  eyebrow,
  modules,
  children,
}: {
  title: string;
  eyebrow: string;
  modules: string[];
  children?: ReactNode;
}) {
  return (
    <div className="workspace">
      <aside>
        <a className="brand" href="/">
          <span className="brandmark">
            <Boxes size={21} />
          </span>
          quickbuddy<span className="brand-dot">.</span>
        </a>
        <p className="nav-label">WORKSPACE</p>
        <a className="active navitem" href="/">
          <Command size={17} />
          Overview
        </a>
        <nav aria-label="Planned modules">
          {modules.map((label) => (
            <span className="navitem muted" key={label}>
              <ChevronRight size={15} />
              {label}
              <small>Planned</small>
            </span>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <ShieldCheck size={16} /> Permission scoped workspace
        </div>
      </aside>
      <main>
        <header>
          <span>
            <MapPin size={15} /> All regions · configuration pending
          </span>
          <a href="/login">
            <CircleHelp size={18} /> Access
          </a>
        </header>
        <section className="content">
          <div className="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p className="intro">
            One connected platform. A clear view of what comes next.
          </p>
          <div className="foundation">
            <span className="status-dot" />
            <strong>Foundation workspace</strong>
            <span>Phase 1 / Architecture & application shell</span>
          </div>
          <div className="section-title">
            <h2>Your workspace</h2>
            <span>Built around your role</span>
          </div>
          <div className="module-grid">
            {modules.slice(0, 4).map((label, i) => (
              <article key={label}>
                <span className="module-number">0{i + 1}</span>
                <ArrowUpRight size={18} />
                <h3>{label}</h3>
                <p>
                  Domain boundary prepared. Business capabilities arrive in
                  later phases.
                </p>
                <span className="tag">Planned capability</span>
              </article>
            ))}
          </div>
          {children}
          <div className="note">
            <ShieldCheck size={21} />
            <div>
              <strong>Access starts with trust</strong>
              <p>
                Operational data requires verified identity and the appropriate
                workspace role.
              </p>
            </div>
          </div>
          <footer>
            QUICKBUDDY PLATFORM
            <span>Shared backend · Independent applications</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

export function Login({ name }: { name: string }) {
  return (
    <main className="login">
      <div className="login-panel">
        <span className="brandmark">
          <ShieldCheck />
        </span>
        <p className="eyebrow">QUICKBUDDY / {name}</p>
        <h1>Secure workspace access</h1>
        <p>
          Identity provider setup is required before sign-in is available. Your
          administrator must configure OIDC and provision your workspace role.
        </p>
        <div className="foundation">
          Authentication is closed until configured.
        </div>
        <a className="backlink" href="/">
          Explore the platform shell <ArrowUpRight size={16} />
        </a>
      </div>
    </main>
  );
}
