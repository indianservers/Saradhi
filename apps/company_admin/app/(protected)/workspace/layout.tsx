import type { ReactNode } from "react";
import { requireRole } from "@quickbuddy/web-design-system/auth";
export default async function Layout({ children }: { children: ReactNode }) {
  await requireRole("company_admin");
  return children;
}
