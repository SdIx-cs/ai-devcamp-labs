"""Diagnostic script to test Memory Bank ingestion for deployed Reasoning Engine."""

import os
from vertexai._genai import Client

# Target engine coordinates
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-devcamp-sharon")
ENGINE_ID = os.environ.get("ENGINE_ID", "5332930736754262016")
LOCATION = os.environ.get("LOCATION", "us-central1")

engine_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"

print(f"Connecting to Reasoning Engine: {engine_name}...")
client = Client(project=PROJECT_ID, location=LOCATION)

# Conversation containing user preference
conversation = [
    {
        "content": {
            "role": "user",
            "parts": [
                {
                    "text": "I always sign off with Building in public. and never use more than five hashtags."
                }
            ],
        }
    },
    {
        "content": {
            "role": "model",
            "parts": [
                {
                    "text": "Understood! I will ensure all posts sign off with 'Building in public.' and keep hashtags to five or fewer."
                }
            ],
        }
    },
]

print("\nGenerating memory via client.agent_engines.memories.generate()...")
operation = client.agent_engines.memories.generate(
    name=engine_name,
    direct_contents_source={"events": conversation},
    scope={"user_id": "devcamp-user"},
)

print(f"Generate operation status: done={operation.done}")
if hasattr(operation, "response") and operation.response:
    print(f"Generated memories count: {len(operation.response.generated_memories)}")

print("\nListing memories from Reasoning Engine...")
memories = list(client.agent_engines.memories.list(name=engine_name))
print(f"Total memories found: {len(memories)}")

for idx, mem in enumerate(memories, start=1):
    print(f"\n--- Memory #{idx} ---")
    print(f"Name   : {mem.name}")
    print(f"Fact   : {mem.fact}")
    print(f"Scope  : {mem.scope}")
    if mem.topics:
        topic_labels = []
        for t in mem.topics:
            if getattr(t, "managed_memory_topic", None):
                topic_labels.append(f"Managed: {t.managed_memory_topic}")
            elif getattr(t, "custom_memory_topic_label", None):
                topic_labels.append(f"Custom: {t.custom_memory_topic_label}")
            else:
                topic_labels.append(str(t))
        print(f"Topics : {', '.join(topic_labels)}")
    if mem.create_time:
        print(f"Created: {mem.create_time}")
