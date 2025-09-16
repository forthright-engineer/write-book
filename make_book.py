from __future__ import annotations

import argparse
import os
import sys
import yaml

from book_maker import Orchestrator
from book_maker.publisher import publish


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a book with multi-agent workflow")
    parser.add_argument("--commission", default="commissioning.yaml", help="Path to commissioning YAML")
    args = parser.parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        print("Error: Please set MISTRAL_API_KEY in your environment.")
        return 2

    orch = Orchestrator(args.commission, api_key=api_key)
    toc, chapters = orch.build()

    cfg = None
    with open(args.commission, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    outputs = publish(cfg, toc, chapters)
    print("Done. Outputs:")
    for k, v in outputs.items():
        print(f"- {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
