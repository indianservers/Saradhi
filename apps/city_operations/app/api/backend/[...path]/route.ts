import { backendProxy } from "@quickbuddy/web-design-system/server-routes";
type Context = { params: Promise<{ path: string[] }> };
export async function GET(request: Request, { params }: Context) {
  return backendProxy(request, (await params).path);
}
export async function POST(request: Request, { params }: Context) {
  return backendProxy(request, (await params).path);
}
