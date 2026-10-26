# Admin design system

The company, city operations, and support apps use the shared design tokens and components in `packages/web_design_system/src/styles.css` and `admin-control-tower.tsx`. The system provides the same dark navigation rail, scoped workspace header, responsive content layout, metric cards, tables, status notices, empty states, and actionable panels.

Operational states are labeled from backend values. Unavailable API data is shown as an error/empty state rather than a fabricated zero. Inputs and actions have accessible labels; reduced-motion rules are included in the shared stylesheet. Responsive CSS breakpoints are present for tablet and mobile layouts.

Phase 7.A added finance approval organization selection, decision reason input, and approve/reject actions to the shared company console. A full authenticated visual review remains unverified because no test user credentials are available in the current session.
