"""
File: scan_progress_live.py
Description: Real-time scan progress component with streaming updates
Author: Arjun Li
Created: 2026-04-17
Last Modified: 2026-04-17
Related modules: tui.py, scanner.py
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Literal

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

from src import __version__
from src.ui.constants import STYLE_MUTED, STYLE_TITLE
from src.ui.i18n import I18n
from src.ui.keyboard import KEY_ENTER, KEY_QUIT, read_key


class ScanProgressLive:
    """Real-time scan progress component with streaming file updates.

    Single-phase design: Progress bar updates as each file is yielded and scanned.
    No artificial delays - updates reflect actual work progress.
    """

    def __init__(
        self,
        console: Console,
        mode: Literal["full", "incremental"] = "full",
        last_scan_time: float | None = None,
    ) -> None:
        self._console = console
        self._mode = mode
        self._last_scan_time = last_scan_time
        self._live: Live | None = None
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None
        self._results: list[tuple[Path, int]] = []
        self._files_with_chinese: int = 0
        self._files_scanned: int = 0
        self._current_file: str = ""
        self._start_time: float = 0

    def start(self) -> None:
        """Initialize and start the real-time progress display."""
        self._start_time = time.time()

        self._progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self._console,
            expand=False,
        )
        self._task_id = self._progress.add_task(
            I18n.get("progress_scanning"),
            total=None,
        )

        self._live = Live(
            self._render_display(),
            console=self._console,
            refresh_per_second=10,
            screen=True,
        )
        self._live.start()

    def update_file(
        self,
        file_path: Path,
        found_chinese: bool,
        line_count: int,
    ) -> None:
        """Update progress with current file scan result."""
        if not self._progress or not self._live or self._task_id is None:
            return

        self._files_scanned += 1

        file_name = file_path.name
        if len(file_name) > 40:
            file_name = "..." + file_name[-37:]
        self._current_file = file_name

        if found_chinese:
            self._files_with_chinese += 1
            self._results.append((file_path, line_count))

        self._live.update(self._render_display())

    def set_total(self, total: int) -> None:
        """Set total files count for determinate progress bar."""
        if not self._progress or self._task_id is None:
            return
        self._progress.update(self._task_id, total=total)

    def _render_display(self) -> Panel:
        """Build the current display panel."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        content_lines: list[Text] = []

        title_line = Text()
        if self._mode == "incremental" and self._last_scan_time:
            last_time_str = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(self._last_scan_time),
            )
            title_line.append(
                f"{I18n.get('progress_incremental_title')} | ",
                style=STYLE_TITLE,
            )
            title_line.append(
                f"{I18n.get('progress_last_scan')}: {last_time_str}",
                style=STYLE_MUTED,
            )
        else:
            title_line.append(
                f"{I18n.get('progress_full_title')}",
                style=STYLE_TITLE,
            )
        content_lines.append(title_line)
        content_lines.append(Text())

        content_lines.append(Text.from_markup(f"[dim]zh-context-scanner v{__version__}[/]"))
        content_lines.append(Text())

        if self._progress:
            content_lines.append(self._progress)

        if self._current_file:
            file_line = Text()
            file_line.append("  → ", style="dim")
            file_line.append(self._current_file, style="cyan")
            content_lines.append(file_line)

        content_lines.append(Text())

        stats_line = Text()
        stats_line.append(
            f"{I18n.get('progress_collected')}: ",
            style=STYLE_MUTED,
        )
        stats_line.append(str(self._files_scanned), style="cyan")
        stats_line.append("  |  ", style=STYLE_MUTED)
        stats_line.append(
            f"{I18n.get('progress_files_found')}: ",
            style=STYLE_MUTED,
        )
        if self._files_with_chinese > 0:
            stats_line.append(str(self._files_with_chinese), style="green bold")
        else:
            stats_line.append("0", style="dim")
        stats_line.append(f"  |  {I18n.get('progress_elapsed')}: ", style=STYLE_MUTED)
        stats_line.append(elapsed_str, style="dim")
        content_lines.append(stats_line)

        content_lines.append(Text())
        content_lines.append(Text.from_markup(f"[dim]{I18n.get('progress_hint')}[/]"))

        border_style = "cyan" if self._files_with_chinese > 0 else "yellow"

        return Panel(
            Group(*content_lines),
            title=f"[bold cyan]🔍 {I18n.get('progress_title')}[/]",
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def finish(self, wait_for_key: bool = True) -> list[tuple[Path, int]]:
        """Stop progress and show completion panel, return results.

        Args:
            wait_for_key: If True, wait for user to press Enter before closing.
                         If False, show panel briefly then auto-close.
        """
        if not self._live:
            return self._results

        elapsed = time.time() - self._start_time if self._start_time else 0
        elapsed_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"

        completion_panel = self._build_completion_panel(elapsed_str)
        self._live.update(completion_panel)

        if wait_for_key:
            while True:
                key = read_key()
                if key == KEY_ENTER or key == KEY_QUIT:
                    break
        else:
            time.sleep(1.0)

        self._live.stop()

        return self._results

    def _build_completion_panel(self, elapsed_str: str) -> Panel:
        """Build the completion summary panel."""
        content_lines: list[Text] = []

        status_line = Text()
        if self._files_with_chinese > 0:
            status_line.append("✓ ", style="green bold")
            status_line.append(
                I18n.get("progress_complete_with_results"),
                style="green",
            )
        else:
            status_line.append("✓ ", style="cyan bold")
            status_line.append(
                I18n.get("progress_complete_no_results"),
                style="cyan",
            )
        content_lines.append(status_line)
        content_lines.append(Text())

        stats_line = Text()
        stats_line.append(f"{I18n.get('progress_total_scanned')}: ", style=STYLE_MUTED)
        stats_line.append(str(self._files_scanned), style="dim")
        stats_line.append("  ")
        stats_line.append(f"{I18n.get('progress_files_found')}: ", style=STYLE_MUTED)
        if self._files_with_chinese > 0:
            stats_line.append(str(self._files_with_chinese), style="green bold")
        else:
            stats_line.append("0", style="dim")
        stats_line.append("  ")
        stats_line.append(f"{I18n.get('progress_elapsed')}: ", style=STYLE_MUTED)
        stats_line.append(elapsed_str, style="dim")
        content_lines.append(stats_line)
        content_lines.append(Text())

        content_lines.append(Text.from_markup(f"[dim]{I18n.get('progress_complete_hint')}[/]"))

        border_style = "green" if self._files_with_chinese > 0 else "cyan"

        return Panel(
            Group(*content_lines),
            title=f"[bold green]✓ {I18n.get('progress_complete_title')}[/]",
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2),
        )
