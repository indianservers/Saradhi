import { cookies } from "next/headers";

const uuid = "[0-9a-fA-F-]{36}";

function allowed(path: string) {
  return (
    path === "api/v1/geo/cities" ||
    path === "api/v1/merchants/branches" ||
    path === "api/v1/ai/models" ||
    path === "api/v1/ai/copilot/status" ||
    new RegExp(`^api/v1/operations/cities/${uuid}/(dispatch|fleet)$`).test(path)
  );
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const upstreamPath = path.join("/");
  if (!allowed(upstreamPath))
    return Response.json(
      { detail: "Backend route is not allowed by this read-only proxy." },
      { status: 404 },
    );

  const base = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  const upstream = new URL(`/${upstreamPath}`, base);
  upstream.search = new URL(request.url).search;
  const token = (await cookies()).get("qb_access")?.value;
  const headers = new Headers({ accept: "application/json" });
  if (token) headers.set("authorization", `Bearer ${token}`);

  try {
    const response = await fetch(upstream, { headers, cache: "no-store" });
    return new Response(response.body, {
      status: response.status,
      headers: {
        "content-type":
          response.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
      },
    });
  } catch {
    return Response.json(
      { detail: "Configured backend is unavailable." },
      { status: 503 },
    );
  }
}
