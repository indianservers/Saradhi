import createClient from "openapi-fetch";
import type { paths, components } from "./schema";

export type ApiError = components["schemas"]["ErrorResponse"];
export type Me = components["schemas"]["PrincipalView"];
export type TokenProvider = () => Promise<string | null>;

export function createApi(baseUrl: string, getToken: TokenProvider) {
  const api = createClient<paths>({ baseUrl });
  api.use({
    async onRequest({ request }) {
      const token = await getToken();
      if (token) request.headers.set("Authorization", `Bearer ${token}`);
      request.headers.set("X-Request-ID", crypto.randomUUID());
      return request;
    },
  });
  return api;
}
