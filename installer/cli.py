"""Command-line entry point for the prototype installer.

The CLI reports basic system information, including GPU model and VRAM when
available, and optionally prompts the user to store API keys.
"""
from __future__ import annotations

import argparse
import json

from . import system_info, api_keys, plugins, env


def install_all() -> None:
    """Discover plugins and install their requested dependencies."""

    registry = plugins.discover_plugins()
    deps = sorted(registry.dependencies)
    if not deps:
        print("No plugin dependencies to install.")
        return
    env_path = env.create_env("plugins")
    env.install_packages(env_path, deps)
    print(f"Installed {len(deps)} packages into {env_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype Windows AI installer")
    parser.add_argument(
        "--show-config-dir",
        action="store_true",
        help="print the directory where API keys are stored",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="list stored API keys",
    )
    parser.add_argument(
        "--delete-key",
        metavar="SERVICE",
        help="delete the stored API key for SERVICE",
    )
    parser.add_argument(
        "--install-all",
        action="store_true",
        help="install plugin dependencies in their own environment",
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

    performed_action = False
    if args.list_keys:
        keys = api_keys.list_keys()
        if keys:
            print("Stored API keys:")
            for service in keys:
                print(f"- {service}")
        else:
            print("No API keys stored.")
        performed_action = True

    if args.delete_key:
        if api_keys.delete_key(args.delete_key):
            print(f"Deleted key for {args.delete_key}")
        else:
            print(f"No key stored for {args.delete_key}")
        performed_action = True

    if not performed_action:
        if input("Would you like to add an API key? (y/N) ").strip().lower() == "y":
            api_keys.prompt_and_save()
        else:
            print("No API key stored.")

    if args.install_all:
        install_all()


if __name__ == "__main__":
    main()
