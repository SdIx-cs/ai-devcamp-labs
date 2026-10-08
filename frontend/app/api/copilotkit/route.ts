import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

function getRuntime() {
  const port = process.env.PORT || "3000";
  return new CopilotRuntime({
    agents: {
      social_poster: new HttpAgent({
        url: process.env.ADK_BACKEND_URL || `http://127.0.0.1:${port}/api/adk`,
      }),
    },
  });
}

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: getRuntime(),
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
