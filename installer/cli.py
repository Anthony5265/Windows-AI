"""Command-line entry point for the prototype installer.

The CLI reports basic system information, including GPU name and VRAM when
available, and optionally prompts the user to store API keys.
"""
from __future__ import annotations

import argparse
import json

from . import system_info, api_keys, plugins, env
from .logging_config import get_logger


logger = get_logger(__name__)


def install_all() -> None:
    """Discover plugins and install their requested dependencies."""

    registry = plugins.discover_plugins()
    if not registry.dependencies:
        print("No plugin dependencies to install.")
        return

    for plugin_name, deps in sorted(registry.dependencies.items()):
        env_path = env.create_env(plugin_name)
        env.install_packages(env_path, sorted(deps))
        print(
            f"Installed {len(deps)} packages for {plugin_name} into {env_path}"
        )


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
    if info.get("gpu_name"):
        print(
            f"GPU: {info['gpu_name']} (VRAM: {info.get('gpu_vram_gb', 'unknown')} GB)"
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
        try:
            choice = input(
                "API key options: [l]ist, [d]elete, [a]dd or [n]one? "
            ).strip().lower()
        except Exception:
            logger.exception("Failed to read API key choice")
            choice = "n"

        if choice == "l":
            keys = api_keys.list_keys()
            if keys:
                print("Stored API keys:")
                for service in keys:
                    print(f"- {service}")
            else:
                print("No API keys stored.")
        elif choice == "d":
            try:
                service = input("Service to delete: ").strip()
            except Exception:
                logger.exception("Failed to read service to delete")
                service = ""
            if service:
                if api_keys.delete_key(service):
                    print(f"Deleted key for {service}")
                else:
                    print(f"No key stored for {service}")
        elif choice in {"a", "y"}:  # support legacy 'y' for yes to add
            api_keys.prompt_and_save()
        else:
            print("No API key stored.")

    if args.install_all:
        install_all()

    # Offer to launch the Control Center after setup completes
    try:
        launch = input("Launch Control Center GUI now? [y/N] ").strip().lower()
    except Exception:
        logger.exception("Failed to read launch choice")
        launch = "n"
    if launch in {"y", "yes"}:
        try:
            from control_center.gui import main as launch_gui

            launch_gui()
        except Exception:  # pragma: no cover - runtime path
            logger.exception("Failed to launch Control Center")


if __name__ == "__main__":
    main()
