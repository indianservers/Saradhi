import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { createApi } from "@quickbuddy/sdk";

// Server-only: browser never receives the access token. Future OIDC callback must
// set qb_access as HttpOnly, Secure, SameSite=Lax with a short expiration.
export async function requireRole(role: string | string[]) {
  const token = (await cookies()).get("qb_access")?.value;
  if (!token) redirect("/login");
  const base = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  const api = createApi(base, async () => token);
  try {
    const { data } = await api.GET("/api/v1/me", { cache: "no-store" });
    const allowed = Array.isArray(role) ? role : [role];
    if (data?.roles.some((item) => allowed.includes(item))) return data;
  } catch {
    /* Fail closed if identity cannot be verified. */
  }
  redirect("/login?reason=access");
}
