import { cookies } from "next/headers";

const uuid = "[0-9a-fA-F-]{36}";
const readRoutes = [
  /^api\/v1\/me$/,
  /^api\/v1\/me\/consents$/,
  /^api\/v1\/geo\/cities$/,
  /^api\/v1\/operations\/authorized-cities$/,
  /^api\/v1\/merchants\/branches$/,
  /^api\/v1\/ai\/models$/,
  /^api\/v1\/ai\/copilot\/status$/,
  /^api\/v1\/finance\/authorized-organizations$/,
  /^api\/v1\/finance\/refund-approvals$/,
  /^api\/v1\/bulk\/jobs$/,
  /^api\/v1\/bulk\/templates\/branches$/,
  /^api\/v1\/admin\/customers$/,
  /^api\/v1\/admin\/customers-export$/,
  new RegExp(
    `^api/v1/admin/customers/${uuid}(/(orders|payments|addresses|subscriptions|loyalty|referrals|campaigns|support|feedback|privacy|security))?$`,
  ),
  new RegExp(`^api/v1/bulk/imports/${uuid}$`),
  new RegExp(`^api/v1/bulk/imports/${uuid}/errors$`),
  /^api\/v1\/support\/tickets$/,
  new RegExp(`^api/v1/support/tickets/${uuid}/messages$`),
  new RegExp(
    `^api/v1/operations/cities/${uuid}/(dispatch|fleet|pilot-incidents)$`,
  ),
];
const writeRoutes = [
  /^api\/v1\/me\/consents$/,
  /^api\/v1\/admin\/customer-segments\/preview$/,
  /^api\/v1\/bulk\/imports$/,
  /^api\/v1\/bulk\/exports$/,
  new RegExp(`^api/v1/bulk/imports/${uuid}/(mapping|validate|dry-run|commit)$`),
  new RegExp(`^api/v1/bulk/jobs/${uuid}/cancel$`),
  new RegExp(`^api/v1/finance/refund-approvals/${uuid}/decision$`),
  new RegExp(
    `^api/v1/operations/pilot-incidents/${uuid}/(acknowledge|resolve)$`,
  ),
  new RegExp(`^api/v1/support/tickets/${uuid}/(claim|messages|resolve)$`),
];

function responseError(message: string, status: number) {
  return Response.json({ detail: message }, { status });
}

function sameOrigin(request: Request) {
  return request.headers.get("origin") === new URL(request.url).origin;
}

function apiBase() {
  const base = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  const parsed = new URL(base);
  if (
    parsed.protocol !== "https:" &&
    parsed.hostname !== "localhost" &&
    parsed.hostname !== "127.0.0.1"
  ) {
    throw new Error("API_BASE_URL must use HTTPS outside local development");
  }
  return parsed;
}

export async function backendProxy(request: Request, path: string[]) {
  const route = path.join("/");
  const method = request.method.toUpperCase();
  const allowed =
    method === "GET"
      ? readRoutes.some((pattern) => pattern.test(route))
      : method === "POST" && writeRoutes.some((pattern) => pattern.test(route));
  if (!allowed)
    return responseError("Backend route is not allowed by this proxy.", 404);
  if (method !== "GET" && !sameOrigin(request))
    return responseError("Cross-origin request rejected.", 403);

  const jar = await cookies();
  const token = jar.get("qb_access")?.value;
  if (!token) return responseError("Authentication required.", 401);
  const upstream = new URL(`/${route}`, apiBase());
  upstream.search = new URL(request.url).search;
  const headers = new Headers({
    accept: "application/json",
    authorization: `Bearer ${token}`,
  });
  for (const header of ["idempotency-key", "x-bulk-entity"]) {
    const value = request.headers.get(header);
    if (value) headers.set(header, value);
  }
  let body: string | undefined;
  if (method !== "GET") {
    const length = Number(request.headers.get("content-length") ?? "0");
    const contentType =
      request.headers.get("content-type")?.toLowerCase() ?? "";
    const isCsv =
      route === "api/v1/bulk/imports" && contentType.startsWith("text/csv");
    if (!isCsv && !contentType.startsWith("application/json"))
      return responseError(
        "JSON or supported CSV content type is required.",
        415,
      );
    const maxBytes = isCsv ? 5 * 1024 * 1024 : 16_384;
    if (length > maxBytes)
      return responseError("Request body is too large.", 413);
    headers.set(
      "content-type",
      isCsv ? "text/csv; charset=utf-8" : "application/json",
    );
    body = await request.text();
    if (new TextEncoder().encode(body).byteLength > maxBytes)
      return responseError("Request body is too large.", 413);
  }
  try {
    let response = await fetch(upstream, {
      method,
      headers,
      body,
      cache: "no-store",
    });
    if (response.status === 401) {
      const refreshToken = jar.get("qb_refresh")?.value;
      if (refreshToken) {
        const refreshed = await fetch(
          new URL("/api/v1/auth/refresh", apiBase()),
          {
            method: "POST",
            headers: {
              "content-type": "application/json",
              accept: "application/json",
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
            cache: "no-store",
          },
        );
        if (refreshed.ok) {
          const session = (await refreshed.json()) as {
            access_token?: string;
            refresh_token?: string;
            expires_in?: number;
          };
          if (
            session.access_token &&
            session.refresh_token &&
            session.expires_in
          ) {
            const secure = new URL(request.url).protocol === "https:";
            const options = {
              httpOnly: true,
              secure,
              sameSite: "lax" as const,
              path: "/",
            };
            jar.set("qb_access", session.access_token, {
              ...options,
              maxAge: session.expires_in,
            });
            jar.set("qb_refresh", session.refresh_token, {
              ...options,
              maxAge: 60 * 60 * 24 * 30,
            });
            headers.set("authorization", `Bearer ${session.access_token}`);
            response = await fetch(upstream, {
              method,
              headers,
              body,
              cache: "no-store",
            });
          }
        } else {
          jar.delete("qb_access");
          jar.delete("qb_refresh");
        }
      }
    }
    return new Response(response.body, {
      status: response.status,
      headers: {
        "content-type":
          response.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
        ...(response.headers.get("content-disposition")
          ? {
              "content-disposition": response.headers.get(
                "content-disposition",
              )!,
            }
          : {}),
      },
    });
  } catch {
    return responseError("Configured backend is unavailable.", 503);
  }
}

export async function sessionRoute(request: Request) {
  if (!sameOrigin(request))
    return responseError("Cross-origin request rejected.", 403);
  const jar = await cookies();
  const base = apiBase();
  if (request.method === "POST") {
    const length = Number(request.headers.get("content-length") ?? "0");
    if (length > 8_192) return responseError("Request body is too large.", 413);
    if (
      !request.headers
        .get("content-type")
        ?.toLowerCase()
        .startsWith("application/json")
    ) {
      return responseError("JSON content type is required.", 415);
    }
    let credentials: unknown;
    try {
      credentials = await request.json();
    } catch {
      return responseError("Invalid sign-in request.", 400);
    }
    if (
      !credentials ||
      typeof credentials !== "object" ||
      !("email" in credentials) ||
      !("password" in credentials) ||
      typeof credentials.email !== "string" ||
      typeof credentials.password !== "string"
    ) {
      return responseError("Email and password are required.", 400);
    }
    try {
      const upstream = await fetch(new URL("/api/v1/auth/login", base), {
        method: "POST",
        headers: {
          "content-type": "application/json",
          accept: "application/json",
        },
        body: JSON.stringify(credentials),
        cache: "no-store",
      });
      if (!upstream.ok)
        return new Response(upstream.body, {
          status: upstream.status,
          headers: {
            "content-type": "application/json",
            "cache-control": "no-store",
          },
        });
      const token = (await upstream.json()) as {
        access_token?: string;
        refresh_token?: string;
        expires_in?: number;
      };
      if (!token.access_token || !token.refresh_token || !token.expires_in)
        return responseError(
          "Authentication provider returned an invalid session.",
          502,
        );
      const secure = new URL(request.url).protocol === "https:";
      const options = {
        httpOnly: true,
        secure,
        sameSite: "lax" as const,
        path: "/",
      };
      jar.set("qb_access", token.access_token, {
        ...options,
        maxAge: token.expires_in,
      });
      jar.set("qb_refresh", token.refresh_token, {
        ...options,
        maxAge: 60 * 60 * 24 * 30,
      });
      return Response.json(
        { authenticated: true },
        { headers: { "cache-control": "no-store" } },
      );
    } catch {
      return responseError("Configured backend is unavailable.", 503);
    }
  }

  if (request.method === "DELETE") {
    const access = jar.get("qb_access")?.value;
    const refresh = jar.get("qb_refresh")?.value;
    if (access && refresh) {
      try {
        await fetch(new URL("/api/v1/auth/logout", base), {
          method: "POST",
          headers: {
            authorization: `Bearer ${access}`,
            "content-type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refresh }),
          cache: "no-store",
        });
      } catch {
        /* Always clear the local session, including during an outage. */
      }
    }
    jar.delete("qb_access");
    jar.delete("qb_refresh");
    return Response.json(
      { authenticated: false },
      { headers: { "cache-control": "no-store" } },
    );
  }
  return responseError("Method not allowed.", 405);
}
