"""Command-line entry point for the prototype installer.

The CLI reports basic system information, including GPU model and VRAM when
available, and optionally prompts the user to store API keys.
"""
from __future__ import annotations

import argparse
import json

from . import system_info, api_keys


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype Windows AI installer")
    parser.add_argument(
        "--show-config-dir",
        action="store_true",
        help="print the directory where API keys are stored",
    )
    args = parser.parse_args()

    info = system_info.detect_system()
    print("Detected system info:")
    print(json.dumps(info, indent=2))
    if info.get("gpu_model"):
        print(
            f"GPU: {info['gpu_model']} (VRAM: {info.get('gpu_vram_gb', 'unknown')} GB)"
        )

    if args.show_config_dir:
        print(f"Config directory: {api_keys.CONFIG_DIR}")

    if input("Would you like to add an API key? (y/N) ").strip().lower() == "y":
        api_keys.prompt_and_save()
    else:
        print("No API key stored.")


if __name__ == "__main__":
    main()
