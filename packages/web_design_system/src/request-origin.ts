/** Use the browser's target Host, which Next may normalize in request.url. */
export function isSameOrigin(request: Request): boolean {
  try {
    const origin = request.headers.get("origin");
    if (!origin) return false;
    const target = new URL(request.url);
    const host = request.headers.get("host") ?? target.host;
    const expected = new URL(`${target.protocol}//${host}`);
    return new URL(origin).origin === expected.origin;
  } catch {
    return false;
  }
}
