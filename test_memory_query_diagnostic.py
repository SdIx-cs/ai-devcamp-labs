"""Diagnostic test comparing Memory Bank query retrieval."""

import os
from vertexai._genai import Client

PROJECT_ID = os.environ.get("PROJECT_ID", "ai-devcamp-sharon")
ENGINE_ID = os.environ.get("ENGINE_ID", "5332930736754262016")
LOCATION = os.environ.get("LOCATION", "us-central1")

engine_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
client = Client(project=PROJECT_ID, location=LOCATION)

query = "Building in public hashtags posting style"
print(f"Connecting to: {engine_name}")
print(f"Executing diagnostic query: {query!r}\n")

results = list(
    client.agent_engines.memories.retrieve(
        name=engine_name,
        scope={"user_id": "devcamp-user"},
        similarity_search_params={"search_query": query},
    )
)

print(f"Total matching memories retrieved: {len(results)}")
for idx, item in enumerate(results, start=1):
    mem = item.memory
    print(f"\n[Result #{idx}]")
    print(f"Fact   : {mem.fact}")
    print(f"Topics : {[str(t) for t in mem.topics] if mem.topics else 'None'}")
    print(f"Scope  : {mem.scope}")
