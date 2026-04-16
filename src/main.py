"""
File: main.py
Description: CLI entry point (TUI mode only, headless deprecated)
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: ui/tui.py, backup_manager.py
"""

from __future__ import annotations

import asyncio
import json

from rich.console import Console

from src import __version__
from src.backup_manager import restore_backup
from src.config import Config, parse_args
from src.preference import PreferenceManager
from src.scanner import find_files_with_chinese
from src.ui.i18n import I18n

console = Console()


def run_headless_scan(config: Config) -> None:
    """Run scan in headless mode, output JSON."""
    results = find_files_with_chinese(
        config.root_path,
        config.scan_targets,
        config.global_excludes,
    )
    total_files = len(results)
    total_lines = sum(r[1] for r in results)

    if config.json_output:
        output_data = {
            "scan_time": __import__("datetime").datetime.now().isoformat(),
            "total_files": total_files,
            "total_lines": total_lines,
            "files": [{"path": str(r[0]), "chinese_lines": r[1]} for r in results],
        }
        print(json.dumps(output_data, indent=2))
    else:
        console.print(f"[green]{I18n.get('main_scan_complete')}[/] {total_files} {I18n.get('main_files')}, {total_lines} {I18n.get('main_matches')}")
        for file_path, line_count in results:
            console.print(f"  {file_path}: {line_count} {I18n.get('main_matches')}")


def run_restore(config: Config) -> None:
    """Run restore from backup."""
    if not config.restore_target:
        return

    try:
        restored = restore_backup(
            config.backup_dir,
            config.root_path,
            config.restore_target,
            config.restore_file,
        )
        console.print(f"[green]{I18n.get('main_restored')} {len(restored)}[/]")
    except FileNotFoundError as e:
        console.print(f"[red]{I18n.get('main_error')} {e}[/]")


def entry() -> None:
    """Main entry point."""
    from src.paths import PathRegistry
    from src.solid_logger import configure_logging

    args = parse_args()

    # Setup logger with PathRegistry and rotation
    tool_root = PathRegistry.detect_tool_root()
    path_registry = PathRegistry(tool_root)
    configure_logging(version=__version__, path_registry=path_registry)

    # Initialize preference manager
    pref_manager = PreferenceManager()

    # Reset invalid config state if file is missing
    pref_manager.reset_if_invalid()

    # Check if setup wizard should be triggered
    needs_setup = (
        not pref_manager.has_valid_config()
        or args.setup
    )

    if needs_setup:
        from src.ui.setup_wizard import run_setup_wizard
        config = run_setup_wizard()
        if config is None:
            return
    else:
        prefs = pref_manager.load()
        config = Config.from_cli_args(args, config_file=prefs.last_config_file)

    if args.restore:
        run_restore(config)
        return

    if args.scan or args.json:
        run_headless_scan(config)
        return

    from src.ui.tui import run_tui
    try:
        asyncio.run(run_tui(config))
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        from rich import box
        from rich.panel import Panel
        from rich.text import Text

        exit_text = Text()
        exit_text.append("\n", end="")
        exit_text.append("Interrupted by user", style="yellow bold")
        exit_text.append("\n\n", end="")
        exit_text.append("Thank you for using ", style="dim")
        exit_text.append("zh-context-scanner", style="bold cyan")
        exit_text.append("\n\n", end="")
        exit_text.append("[OK] ", style="green")
        exit_text.append("Session terminated safely", style="green italic")
        exit_text.append("\n", end="")
        exit_text.append("[OK] ", style="green")
        exit_text.append("No data loss", style="green italic")
        exit_text.append("\n\n", end="")
        exit_text.append("See you next time!", style="bold magenta")

        exit_panel = Panel(
            exit_text,
            title="[bold yellow]![/] Interrupted",
            subtitle="[dim]Session ended by Ctrl+C[/]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(exit_panel)


if __name__ == "__main__":
    entry()
