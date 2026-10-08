"""Configure Reasoning Engine Memory Bank settings.

Usage:
    GOOGLE_CLOUD_PROJECT=YOUR_PROJECT AGENT_ENGINE_ID=ENGINE_ID uv run python backend/memory_bank_config.py apply
    GOOGLE_CLOUD_PROJECT=YOUR_PROJECT AGENT_ENGINE_ID=ENGINE_ID uv run python backend/memory_bank_config.py show
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load local environment if available
load_dotenv()


def get_engine_coordinates() -> tuple[str, str, str]:
    """Resolves project, location, and engine ID from env or metadata."""
    project = (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("PROJECT_ID")
    )
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    if location == "global":
        location = None  # Reasoning Engines reside in regions (e.g. us-central1), not 'global'
    engine_id = os.environ.get("AGENT_ENGINE_ID")

    # If coordinates are missing, try reading deployment_metadata.json
    metadata_path = Path("deployment_metadata.json")
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                runtime_id = data.get("remote_agent_runtime_id", "")
                m = re.search(r"projects/([^/]+)/locations/([^/]+)/reasoningEngines/([^/]+)", runtime_id)
                if m:
                    proj, loc, eid = m.groups()
                    project = project or proj
                    location = location or loc
                    engine_id = engine_id or eid
        except Exception:
            pass

    # If engine_id or location is still missing, try APP_URL
    app_url = os.environ.get("APP_URL", "")
    if app_url:
        m = re.search(r"projects/([^/]+)/locations/([^/]+)/reasoningEngines/([^/]+)", app_url)
        if m:
            proj, loc, eid = m.groups()
            project = project or proj
            location = location or loc
            engine_id = engine_id or eid

    location = location or "us-central1"

    if not project or not engine_id:
        print("Error: Could not determine GOOGLE_CLOUD_PROJECT and/or AGENT_ENGINE_ID.", file=sys.stderr)
        print("Please provide them via environment variables or flags.", file=sys.stderr)
        sys.exit(1)

    return project, location, engine_id


def build_memory_bank_config() -> dict:
    """Builds the Memory Bank configuration with managed topics, custom topic, and 90-day TTL."""
    return {
        "customization_configs": [
            {
                "memory_topics": [
                    {
                        "managed_memory_topic": {
                            "managed_topic_enum": "USER_PREFERENCES"
                        }
                    },
                    {
                        "managed_memory_topic": {
                            "managed_topic_enum": "EXPLICIT_INSTRUCTIONS"
                        }
                    },
                    {
                        "custom_memory_topic": {
                            "label": "posting_style",
                            "description": "User preferences for social media post writing style, tone, format, emoji usage, and sign-offs.",
                        }
                    },
                ]
            }
        ],
        "ttl_config": {
            "default_ttl": "7776000s",  # 90 days = 90 * 24 * 3600s
        },
    }


def apply_config(client, engine_name: str) -> None:
    """Applies memory bank configuration via PATCH on the Reasoning Engine."""
    print(f"Applying Memory Bank configuration to {engine_name}...")
    memory_bank_config = build_memory_bank_config()
    update_config = {
        "context_spec": {
            "memory_bank_config": memory_bank_config,
        }
    }

    try:
        client.agent_engines.update(name=engine_name, config=update_config)
        print("Successfully applied Memory Bank configuration!")
        show_config(client, engine_name)
    except Exception as e:
        print(f"Failed to update Memory Bank configuration: {e}", file=sys.stderr)
        sys.exit(1)


def show_config(client, engine_name: str) -> None:
    """Fetches and displays current Memory Bank configuration for the engine."""
    print(f"\nFetching Memory Bank configuration for {engine_name}...")
    try:
        engine = client.agent_engines.get(name=engine_name)
    except Exception as e:
        print(f"Failed to fetch Reasoning Engine: {e}", file=sys.stderr)
        sys.exit(1)

    # The engine data can be in api_resource dict or object attributes
    api_res = getattr(engine, "api_resource", None) or {}
    if hasattr(api_res, "model_dump"):
        api_res = api_res.model_dump(exclude_none=True)
    elif not isinstance(api_res, dict):
        api_res = {}

    context_spec = api_res.get("context_spec") or {}
    memory_bank = context_spec.get("memory_bank_config") or {}

    if not memory_bank:
        print("No Memory Bank configuration found on this engine.")
        return

    print("Memory Bank Configuration:")
    print("--------------------------")
    ttl = memory_bank.get("ttl_config", {}).get("default_ttl")
    if ttl:
        print(f"• Default TTL: {ttl}")

    customization_configs = memory_bank.get("customization_configs") or []
    for i, custom_cfg in enumerate(customization_configs):
        topics = custom_cfg.get("memory_topics") or []
        if topics:
            print(f"• Memory Topics (Config #{i+1}):")
            for topic in topics:
                managed = topic.get("managed_memory_topic", {}).get("managed_topic_enum")
                if managed:
                    print(f"    - [Managed] {managed}")
                custom = topic.get("custom_memory_topic", {})
                if custom:
                    label = custom.get("label", "custom")
                    desc = custom.get("description", "")
                    print(f"    - [Custom] {label}: {desc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Memory Bank for Agent Engine")
    parser.add_argument("action", choices=["apply", "show"], help="Action to perform: apply or show")
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--location", help="GCP location (default: us-central1)")
    parser.add_argument("--engine-id", help="Reasoning Engine ID")

    args = parser.parse_args()

    project, location, engine_id = get_engine_coordinates()
    if args.project:
        project = args.project
    if args.location:
        location = args.location
    if args.engine_id:
        engine_id = args.engine_id

    engine_name = f"projects/{project}/locations/{location}/reasoningEngines/{engine_id}"

    # Import GenAI Client from vertexai
    from vertexai._genai import Client

    client = Client(project=project, location=location)

    if args.action == "apply":
        apply_config(client, engine_name)
    elif args.action == "show":
        show_config(client, engine_name)


if __name__ == "__main__":
    main()
