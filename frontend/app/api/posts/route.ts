import { NextRequest } from "next/server";
import { proxyBackend } from "@/app/lib/proxy";

export async function GET(req: NextRequest) {
  return proxyBackend(req, "/api/posts");
}
