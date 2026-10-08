import { NextRequest } from "next/server";
import { proxyBackend } from "@/app/lib/proxy";

export async function POST(req: NextRequest) {
  return proxyBackend(req, "/api/adk");
}

export async function GET(req: NextRequest) {
  return proxyBackend(req, "/api/adk");
}

export async function OPTIONS(req: NextRequest) {
  return proxyBackend(req, "/api/adk");
}
