"""Unified command-line interface for Gemini Search MCP."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

from .config import CACHE_DIR
from .server import run as run_server

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fall back for <3.11
    import tomli as tomllib  # type: ignore[assignment]

import tomli_w

DEFAULT_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
COPILOT_CONFIG_PATH = Path.home() / ".copilot" / "config.json"
DEFAULT_SERVER_NAME = "gemini-search"


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        content = path.read_text(encoding="utf-8")
        # Detect format by file extension
        if path.suffix == ".json":
            data = json.loads(content)
        else:  # .toml
            data = tomllib.loads(content)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to parse config at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Config file {path} must contain a table/object")
    return data


def _write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Detect format by file extension
    if path.suffix == ".json":
        serialized = json.dumps(data, indent=2) + "\n"
    else:  # .toml
        serialized = tomli_w.dumps(data)
    path.write_text(serialized, encoding="utf-8")


def _parse_env(entries: Sequence[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw in entries:
        if "=" not in raw:
            raise RuntimeError(f"Environment entry must be KEY=VALUE: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise RuntimeError(f"Environment key missing in entry: {raw}")
        env[key] = value
    return env


def _configure(args: argparse.Namespace) -> int:
    env_entries = list(args.env or [])
    if args.api_key:
        env_entries.append(f"GOOGLE_API_KEY={args.api_key}")
    if args.cache_dir:
        env_entries.append(f"GEMINI_MCP_CACHE={args.cache_dir}")

    try:
        env = _parse_env(env_entries)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Determine which configs to update
    configs_to_update = []
    if args.config:
        # User specified a custom config path
        configs_to_update.append(args.config)
    else:
        # Auto-detect based on cli_type
        if args.cli_type in ("codex", "both"):
            if DEFAULT_CONFIG_PATH.parent.exists() or args.cli_type == "codex":
                configs_to_update.append(DEFAULT_CONFIG_PATH)
        if args.cli_type in ("copilot", "both"):
            if COPILOT_CONFIG_PATH.parent.exists() or args.cli_type == "copilot":
                configs_to_update.append(COPILOT_CONFIG_PATH)
    
    if not configs_to_update:
        print("Error: No config files to update. Use --config to specify a path.", file=sys.stderr)
        return 1

    success_count = 0
    for config_path in configs_to_update:
        try:
            data = _load_config(config_path)
            servers = data.setdefault("mcp_servers", {})
            if not isinstance(servers, dict):
                raise RuntimeError("Existing config uses non-table value for 'mcp_servers'")
            if args.server_name in servers and args.no_overwrite:
                print(f"Warning: Server '{args.server_name}' already exists in {config_path}; skipping (use without --no-overwrite to replace)", file=sys.stderr)
                continue
            
            entry: dict[str, Any] = {"command": args.command}
            if args.command_args:
                entry["args"] = args.command_args
            if env:
                entry["env"] = env
            servers[args.server_name] = entry
            _write_config(config_path, data)
            print(f"✅ Configured MCP server '{args.server_name}' in {config_path}")
            success_count += 1
        except RuntimeError as exc:
            print(f"Error updating {config_path}: {exc}", file=sys.stderr)
            continue

    if success_count == 0:
        return 1
    
    print(f"\n🎉 Successfully configured {success_count} config file(s)!")
    return 0


def _clear_cache(args: argparse.Namespace) -> int:
    cache_dir: Path = args.cache_dir
    if not cache_dir.exists():
        print(f"Cache directory {cache_dir} does not exist; nothing to clear.")
        return 0
    if not cache_dir.is_dir():
        print(f"Error: Cache path is not a directory: {cache_dir}", file=sys.stderr)
        return 1
    try:
        for child in cache_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        if args.remove_root:
            cache_dir.rmdir()
    except OSError as exc:  # noqa: BLE001
        print(f"Error clearing cache: {exc}", file=sys.stderr)
        return 1
    print(f"Cleared cache at {cache_dir}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gemini-search-mcp",
        description="Run and manage the Gemini Search MCP server.",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=False)

    # run
    parser_run = subparsers.add_parser("run", help="Start the MCP server (default)")
    parser_run.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport to use (only stdio is supported).",
    )

    # configure
    parser_config = subparsers.add_parser(
        "configure",
        help="Add or update the MCP configuration for Codex or Copilot CLI.",
    )
    parser_config.add_argument(
        "--cli-type",
        choices=["codex", "copilot", "both"],
        default="both",
        help="Which CLI to configure (default: both).",
    )
    parser_config.add_argument(
        "--config",
        type=Path,
        help="Path to config file (auto-detected if not specified).",
    )
    parser_config.add_argument(
        "--server-name",
        default=DEFAULT_SERVER_NAME,
        help="Table key to use inside mcp_servers.",
    )
    parser_config.add_argument(
        "--command",
        default="gemini-search-mcp",
        help="Command to execute for this server.",
    )
    parser_config.add_argument(
        "--command-args",
        nargs="*",
        default=[],
        help="Arguments to pass to the command.",
    )
    parser_config.add_argument(
        "--env",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help="Additional environment variables.",
    )
    parser_config.add_argument(
        "--api-key",
        help="Shortcut for GOOGLE_API_KEY=<value>.",
    )
    parser_config.add_argument(
        "--cache-dir",
        help="Shortcut for GEMINI_MCP_CACHE=<dir>.",
    )
    parser_config.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if the server entry already exists.",
    )

    # clear-cache
    parser_cache = subparsers.add_parser(
        "clear-cache",
        help="Remove cached conversion outputs.",
    )
    parser_cache.add_argument(
        "--cache-dir",
        type=Path,
        default=CACHE_DIR,
        help="Cache directory to clean (defaults to GEMINI_MCP_CACHE).",
    )
    parser_cache.add_argument(
        "--remove-root",
        action="store_true",
        help="Delete the cache directory itself after clearing contents.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command = args.cmd or "run"
    if command == "run":
        # If no subcommand was provided, args.transport won't exist
        transport = getattr(args, "transport", "stdio")
        if transport != "stdio":
            print("Only stdio transport is supported.", file=sys.stderr)
            return 1
        run_server()
        return 0
    if command == "configure":
        return _configure(args)
    if command == "clear-cache":
        return _clear_cache(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
