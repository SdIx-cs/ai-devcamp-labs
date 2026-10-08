import { GoogleAuth } from "google-auth-library";

const auth = new GoogleAuth({
  scopes: ["https://www.googleapis.com/auth/cloud-platform"],
});

/**
 * Returns the target backend origin URL.
 * Defaults to http://localhost:8000 for local development.
 */
export function getBackendOrigin(): string {
  if (process.env.ADK_BACKEND_ORIGIN) {
    return process.env.ADK_BACKEND_ORIGIN.replace(/\/+$/, "");
  }
  if (process.env.ADK_BACKEND_URL) {
    return process.env.ADK_BACKEND_URL.replace(/\/api\/adk\/?$/, "").replace(/\/+$/, "");
  }
  return "http://localhost:8000";
}

/**
 * Checks if the target URL points to a Google endpoint (Reasoning Engine or Cloud Run).
 */
export function isGoogleEndpoint(urlStr: string): boolean {
  try {
    const parsed = new URL(urlStr);
    return (
      parsed.hostname.endsWith(".googleapis.com") ||
      parsed.hostname === "googleapis.com" ||
      parsed.hostname.endsWith(".run.app")
    );
  } catch {
    return urlStr.includes("googleapis.com");
  }
}

/**
 * Retrieves a Bearer token from Application Default Credentials
 * only when targeting a Google endpoint.
 */
export async function getAuthHeader(targetUrl: string): Promise<string | null> {
  if (!isGoogleEndpoint(targetUrl)) {
    return null;
  }
  try {
    const token = await auth.getAccessToken();
    if (token) return `Bearer ${token}`;

    const reqHeaders = await auth.getRequestHeaders(targetUrl);
    if (typeof (reqHeaders as any)?.get === "function") {
      const val = (reqHeaders as any).get("authorization") || (reqHeaders as any).get("Authorization");
      if (val) return val;
    } else if (reqHeaders) {
      const rec = reqHeaders as unknown as Record<string, string>;
      const val = rec["authorization"] || rec["Authorization"];
      if (val) return val;
    }
  } catch (err) {
    console.error("Could not retrieve ADC token for Google endpoint:", err);
  }
  return null;
}

/**
 * Proxies an incoming Next.js request to the backend upstream server,
 * attaching Application Default Credentials when targeting a Google endpoint
 * and streaming the response body straight through.
 */
export async function proxyBackend(req: Request, targetPath: string): Promise<Response> {
  const origin = getBackendOrigin();
  const cleanPath = targetPath.startsWith("/") ? targetPath : `/${targetPath}`;
  const incomingUrl = new URL(req.url);
  const targetUrl = new URL(`${origin}${cleanPath}`);
  targetUrl.search = incomingUrl.search;

  const headers = new Headers();
  for (const [key, value] of req.headers.entries()) {
    const lower = key.toLowerCase();
    // Drop hop-by-hop and host headers
    if (
      lower === "host" ||
      lower === "connection" ||
      lower === "keep-alive" ||
      lower === "transfer-encoding" ||
      lower === "content-length"
    ) {
      continue;
    }
    headers.set(key, value);
  }

  const authHeader = await getAuthHeader(targetUrl.toString());
  if (authHeader) {
    headers.delete("authorization");
    headers.set("Authorization", authHeader);
  }

  const method = req.method.toUpperCase();
  let body: BodyInit | null = null;
  if (method !== "GET" && method !== "HEAD") {
    body = await req.arrayBuffer();
  }

  const upstreamRes = await fetch(targetUrl.toString(), {
    method,
    headers,
    body,
    // @ts-ignore - duplex is needed in Node.js fetch for bodies
    duplex: body ? "half" : undefined,
  });

  const responseHeaders = new Headers();
  for (const [key, value] of upstreamRes.headers.entries()) {
    const lower = key.toLowerCase();
    if (
      lower === "content-encoding" ||
      lower === "transfer-encoding" ||
      lower === "content-length"
    ) {
      continue;
    }
    responseHeaders.set(key, value);
  }

  const contentType = upstreamRes.headers.get("content-type") || "";
  if (contentType.includes("text/event-stream")) {
    responseHeaders.set("Cache-Control", "no-cache, no-transform");
    responseHeaders.set("X-Accel-Buffering", "no");
  }

  return new Response(upstreamRes.body, {
    status: upstreamRes.status,
    statusText: upstreamRes.statusText,
    headers: responseHeaders,
  });
}
