"""
File: ui/components.py
Description: Rich TUI components for zh-context-scanner with Live refresh
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

from pathlib import Path

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from src.models import FileScanResult, WarningType
from src.ui.constants import (
    ICON_BACKUP,
    ICON_FILE,
    MAX_PATH_DISPLAY_LENGTH,
    STYLE_ACCENT,
    STYLE_MUTED,
    STYLE_NORMAL,
    STYLE_SELECTED,
    STYLE_TITLE,
)
from src.ui.i18n import I18n


def render_main_menu(console: Console) -> Table:
    """Render the main menu table."""
    table = Table(
        title=I18n.get("header_title"),
        header_style="bold cyan",
        show_lines=False,
        expand=True,
    )
    table.add_column("Option", style="white", width=40)

    table.add_row(I18n.get("menu_full_scan"))
    table.add_row(I18n.get("menu_incremental"))
    table.add_row(I18n.get("menu_manual_path"))
    table.add_row(I18n.get("menu_backup_history"))
    table.add_row(I18n.get("menu_language"))
    table.add_row(I18n.get("menu_exit"))

    return table


def render_scan_results(
    console: Console,
    results: list[FileScanResult],
    total_files: int,
    total_matches: int,
    total_warnings: int,
) -> Table:
    """Render scan results table."""
    table = Table(
        title=f"{I18n.get('scan_complete')} {total_files} {I18n.get('scan_files')}, {total_matches} {I18n.get('scan_matches')}",
        header_style="bold magenta",
        show_lines=True,
        expand=True,
    )
    table.add_column("#", style="cyan", no_wrap=True, width=3)
    table.add_column(I18n.get("col_file"), style="white", width=40)
    table.add_column(I18n.get("col_count"), style="green", width=10)
    table.add_column(I18n.get("col_warnings"), style="yellow", width=15)

    for idx, result in enumerate(results, 1):
        rel_path = result.file_path.name
        warning_str = str(result.warnings_count) if result.warnings_count else "0"
        if result.warnings_count > 0:
            warning_str = f"[yellow]{result.warnings_count}[/yellow]"
        table.add_row(str(idx), rel_path, str(result.total_matches), warning_str)

    return table


def render_file_preview(
    console: Console,
    result: FileScanResult,
    translations: dict[str, str] | None = None,
) -> Panel:
    """Render file preview panel with matches."""
    lines: list[str] = []
    for match in result.matches[:20]:  # Limit to 20 items for display
        line_info = f"{I18n.get('line_prefix')}{match.line_number}: {match.line_content}"
        if match.warning:
            warning_label = get_warning_label(match.warning)
            lines.append(f"[dim]{line_info}[/]")
            lines.append(f"[yellow]  {I18n.get('arrow_to')} [SKIP] ({warning_label})[/]")
        elif translations and match.matched_text in translations:
            translated = translations[match.matched_text]
            lines.append(f"[white]{line_info}[/]")
            lines.append(f"[green]  {I18n.get('arrow_to')} {match.line_content[:match.column_start]}[bold]{translated}[/bold]{match.line_content[match.column_end:]}[/]")
        else:
            lines.append(f"[white]{line_info}[/]")
            lines.append(f"[dim]  {I18n.get('arrow_to')} (pending translation)[/]")

    content = "\n".join(lines)
    return Panel(
        content,
        title=f"{result.file_path.name} - {result.total_matches} {I18n.get('preview_title')}",
        border_style="cyan",
    )


def get_warning_label(warning: WarningType) -> str:
    """Get human-readable warning label."""
    labels = {
        WarningType.TEMPLATE_STRING: "template string ${}",
        WarningType.MULTILINE_STRING: "multiline string",
        WarningType.REGEX_LITERAL: "regex literal",
        WarningType.ESCAPE_CHARS: "escape chars",
        WarningType.MULTILINE_COMMENT: "multiline comment",
    }
    return labels.get(warning, warning.value)


def render_confirm_panel(
    console: Console,
    replace_count: int,
    skip_count: int,
    backup_path: Path,
) -> Panel:
    """Render confirmation panel."""
    lines = [
        I18n.format("confirm_replace_count", replace_count),
        f"{I18n.get('confirm_backup_dir')} {backup_path}",
        f"[yellow]{I18n.get('confirm_warning_hint')}[/]",
    ]
    return Panel(
        "\n".join(lines),
        title=I18n.get("confirm_title"),
        border_style="yellow",
    )


def render_complete_panel(
    console: Console,
    replaced: int,
    skipped: int,
    backup_path: Path,
) -> Panel:
    """Render completion panel with verification hints."""
    lines = [
        f"[green]{I18n.get('replace_replaced')} {replaced}[/]",
        f"[yellow]{I18n.get('replace_skipped')} {skipped} {I18n.get('replace_complex')}[/]",
        "",
        f"{I18n.get('replace_backup_location')} {backup_path}",
        "",
        f"[bold]{I18n.get('verify_hint')}[/]",
        f"  {I18n.get('verify_cargo')}",
        f"  {I18n.get('verify_npm')}",
        f"  {I18n.get('verify_git')}",
        "",
        f"[dim]{I18n.get('restore_hint')}[/]",
    ]
    return Panel(
        "\n".join(lines),
        title=f"[green]{I18n.get('replace_complete')}[/]",
        border_style="green",
    )


def render_backup_history(
    console: Console,
    backups: list,
    total_size: int,
) -> Table:
    """Render backup history table."""
    size_mb = total_size / (1024 * 1024)
    table = Table(
        title=f"{I18n.get('backup_title')} - {I18n.get('backup_found')} {len(backups)} ({I18n.get('backup_size')} {size_mb:.2f}MB)",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("ID", style="cyan", width=20)
    table.add_column("Files", style="white", width=10)
    table.add_column("Created", style="dim", width=20)

    for backup in backups:
        table.add_row(
            backup.backup_id,
            str(backup.total_files),
            backup.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    return table


def print_success(console: Console, message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/] {message}")


def print_error(console: Console, message: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/] {message}")


def print_warning(console: Console, message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠[/] {message}")


def print_info(console: Console, message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ[/] {message}")


class ScanProgress:
    """Progress bar wrapper for scanning."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._progress: Progress | None = None
        self._task_ids: dict[str, TaskID] = {}

    def start(self, total_files: int) -> None:
        """Initialize progress bar."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self._console,
            expand=True,
        )
        self._progress.start()
        self._task_ids["scan"] = self._progress.add_task(
            I18n.get("progress_scanning"),
            total=total_files,
        )

    def advance(self) -> None:
        """Advance progress by 1."""
        if self._progress and "scan" in self._task_ids:
            self._progress.advance(self._task_ids["scan"])

    def stop(self) -> None:
        """Stop and clear progress bar."""
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._task_ids.clear()


# Live refresh components


def render_menu_panel(title: str | Text, options: list[str], selected: int, footer: str) -> Panel:
    """Render interactive menu with arrow indicator."""
    body = Text()
    for idx, option in enumerate(options):
        prefix = "→ " if idx == selected else "  "
        style = STYLE_SELECTED if idx == selected else STYLE_NORMAL
        body.append(f"{prefix}{option}\n", style=style)

    # Handle title - if it's a Text object, use it directly; otherwise wrap with style
    if isinstance(title, Text):
        title_renderable = title
    else:
        title_renderable = Text(title, style=STYLE_TITLE)

    return Panel(
        Group(
            title_renderable,
            Text(""),
            body,
            Text(""),
            Text(footer, style=STYLE_MUTED),
        ),
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_file_list_panel(
    items: list[tuple[Path, int]],
    selected: int,
    page: int,
    total_pages: int,
    total_rows: int,
) -> Panel:
    """Render paginated file list with arrow navigation."""
    lines = Text()
    if not items:
        lines.append(I18n.get("tui_no_files"), style=STYLE_MUTED)
    for idx, (file_path, count) in enumerate(items):
        prefix = "→ " if idx == selected else "  "
        style = STYLE_SELECTED if idx == selected else STYLE_NORMAL
        rel_path = str(file_path)
        if len(rel_path) > MAX_PATH_DISPLAY_LENGTH:
            rel_path = "..." + rel_path[-(MAX_PATH_DISPLAY_LENGTH - 3):]
        display_line = f"{prefix}{rel_path}: {count} {I18n.get('col_count')}\n"
        lines.append(display_line, style=style)

    footer_text = (
        f"{ICON_FILE} {I18n.get('footer_page_info')} {page + 1}/{max(total_pages, 1)} {I18n.get('footer_total')}: {total_rows}\n"
        + I18n.get("footer_list_hint")
    )
    return Panel(
        Group(
            Text(f"{ICON_FILE} {I18n.get('scan_results_title')}", style=STYLE_TITLE),
            Text(""),
            lines,
            Text(""),
            Text(footer_text, style=STYLE_MUTED),
        ),
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_backup_list_panel(
    backups: list,
    selected: int,
    page: int,
    total_pages: int,
    total_rows: int,
) -> Panel:
    """Render paginated backup history list with file names."""
    lines = Text()
    if not backups:
        lines.append(I18n.get("tui_no_backups"), style=STYLE_MUTED)
    else:
        # Header line - use i18n for column names
        header = f"{I18n.get('backup_col_filename'):<40} {I18n.get('backup_col_count'):>8} {I18n.get('backup_col_time'):>16}\n"
        lines.append(header, style=STYLE_MUTED)
        lines.append("─" * 64 + "\n", style=STYLE_MUTED)

        for idx, backup in enumerate(backups):
            prefix = "→ " if idx == selected else "  "
            style = STYLE_SELECTED if idx == selected else STYLE_NORMAL

            # Get file name(s) - show first file if multiple
            if backup.files_backed_up:
                file_name = str(backup.files_backed_up[0])
                if len(file_name) > 38:
                    file_name = "..." + file_name[-35:]
                if len(backup.files_backed_up) > 1:
                    file_name += f" (+{len(backup.files_backed_up) - 1})"
            else:
                file_name = I18n.get("backup_unknown_file")

            # Format time
            created_str = backup.created_at.strftime("%Y-%m-%d %H:%M")

            display_line = f"{prefix}{file_name:<38} {backup.total_files:>8} {created_str:>16}\n"
            lines.append(display_line, style=style)

    footer_text = (
        f"{ICON_BACKUP} {I18n.get('footer_page_info')} {page + 1}/{max(total_pages, 1)} {I18n.get('footer_total')}: {total_rows}\n"
        + I18n.get("footer_backup_hint")
    )
    return Panel(
        Group(
            Text(f"{ICON_BACKUP} {I18n.get('backup_title')}", style=STYLE_TITLE),
            Text(""),
            lines,
            Text(""),
            Text(footer_text, style=STYLE_MUTED),
        ),
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_notice_panel(message: str) -> Panel:
    """Render a simple notice/message panel."""
    return Panel(
        Align.center(Text(message, style=STYLE_TITLE)),
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )
