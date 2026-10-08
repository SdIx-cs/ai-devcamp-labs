import { NextRequest } from "next/server";
import { proxyBackend } from "@/app/lib/proxy";

type RouteContext = {
  params: Promise<{ path: string[] }> | { path: string[] };
};

export async function GET(req: NextRequest, context: RouteContext) {
  const params = await Promise.resolve(context.params);
  const path = Array.isArray(params.path) ? params.path.join("/") : params.path;
  return proxyBackend(req, `/outputs/${path}`);
}

export async function HEAD(req: NextRequest, context: RouteContext) {
  const params = await Promise.resolve(context.params);
  const path = Array.isArray(params.path) ? params.path.join("/") : params.path;
  return proxyBackend(req, `/outputs/${path}`);
}
