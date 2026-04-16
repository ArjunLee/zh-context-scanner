"""
File: ui/tui.py
Description: Rich TUI main interface with Live refresh and pagination
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: whole_file_translator.py, backup_manager.py, scanner.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from src import __version__
from src.backup_manager import (
    cleanup_backups,
    list_backups,
    restore_backup,
)
from src.config import Config
from src.models import FileTranslationResult, TranslationMode
from src.paths import PathRegistry
from src.preference import PreferenceManager, UserPreferences
from src.scanner import (
    collect_files,
    contains_chinese,
    count_chinese_lines,
)
from src.ui.components import (
    ScanProgress,
    print_error,
    print_info,
    print_success,
    render_backup_list_panel,
    render_file_list_panel,
    render_menu_panel,
    render_notice_panel,
)
from src.ui.constants import (
    ICON_BACKUP,
    ICON_EXIT,
    ICON_INCREMENTAL,
    ICON_LANGUAGE,
    ICON_MANUAL,
    ICON_MODE,
    ICON_SCAN,
    ICON_SETTINGS,
    PAGE_SIZE,
    STYLE_ACCENT,
    STYLE_MUTED,
    STYLE_NORMAL,
    STYLE_SELECTED,
    STYLE_TITLE,
)
from src.ui.i18n import LANG_MODES, I18n
from src.ui.keyboard import (
    KEY_BACK,
    KEY_DOWN,
    KEY_ENTER,
    KEY_ESC,
    KEY_LEFT,
    KEY_QUIT,
    KEY_RIGHT,
    KEY_UP,
    read_key,
)
from src.whole_file_translator import WholeFileTranslator

# Console with custom theme (matching VaultSave_Database_Review style)
console = Console(
    theme=Theme(
        {
            STYLE_ACCENT: "cyan",
            STYLE_SELECTED: "magenta",
            STYLE_MUTED: "grey50",
            STYLE_TITLE: "magenta bold",
            STYLE_NORMAL: "cyan",
        }
    ),
    emoji=True,
)


def select_translation_mode() -> TranslationMode:
    """Let user select translation mode with Live refresh."""
    options = [
        I18n.get("mode_comment_only"),
        I18n.get("mode_full"),
    ]
    selected = 0

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = render_menu_panel(
                title=I18n.get("mode_title"),
                options=options,
                selected=selected,
                footer=I18n.get("footer_menu_hint"),
            )
            live.update(panel)
            key = read_key()
            if key == KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key == KEY_ENTER:
                break
            elif key == KEY_QUIT:
                return None

    mode = TranslationMode.COMMENT_ONLY if selected == 0 else TranslationMode.FULL
    return mode


async def run_full_scan(config: Config, mode: TranslationMode = TranslationMode.FULL) -> list[tuple[Path, int]]:
    """Run full scan - return files with Chinese text.

    Args:
        config: Configuration
        mode: Translation mode to filter which Chinese lines to count

    Returns:
        List of (file_path, chinese_line_count) tuples
    """
    files = collect_files(
        config.root_path,
        config.scan_targets,
        config.global_excludes,
    )
    progress = ScanProgress(console)
    progress.start(len(files))

    results: list[tuple[Path, int]] = []
    for file in files:
        line_count = count_chinese_lines(file, mode=mode)
        if line_count > 0:
            results.append((file, line_count))
        progress.advance()

    progress.stop()
    # Update timestamp after full scan for future incremental scans
    from src.paths import PathRegistry
    tool_root = PathRegistry.detect_tool_root()
    path_registry = PathRegistry(tool_root)
    from src.scanner import save_last_scan_timestamp
    save_last_scan_timestamp(path_registry.log_dir)
    return results


async def run_incremental_scan(config: Config, mode: TranslationMode = TranslationMode.FULL) -> list[tuple[Path, int]]:
    """Run incremental scan - only files modified after last scan.

    Args:
        config: Configuration
        mode: Translation mode to filter which Chinese lines to count

    Returns:
        List of (file_path, chinese_line_count) tuples for modified files
    """
    from src.paths import PathRegistry
    from src.scanner import find_files_with_chinese_incremental

    tool_root = PathRegistry.detect_tool_root()
    path_registry = PathRegistry(tool_root)

    # Get last scan timestamp for display
    from src.scanner import load_last_scan_timestamp
    last_timestamp = load_last_scan_timestamp(path_registry.log_dir)

    results = find_files_with_chinese_incremental(
        config.root_path,
        config.scan_targets,
        config.global_excludes,
        path_registry.log_dir,
        mode,
    )

    # Display info about incremental scan
    if last_timestamp > 0:
        last_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_timestamp))
        console.print(f"[cyan]Last scan: {last_time_str}[/]")
        console.print(f"[green]Found {len(results)} modified files with Chinese text[/]")

    return results


def render_whole_file_preview(result: FileTranslationResult, diff_page: int = 0) -> Panel:
    """Render whole-file translation preview with git diff style and pagination.
    
    Args:
        result: Translation result to preview
        diff_page: Current page number for diff display (0-indexed)
    """
    # Build info header
    info_table = Table(show_header=False, box=None, expand=True)
    info_table.add_column(width=20)
    info_table.add_column(width=40)
    info_table.add_row(f"📄 {I18n.get('preview_file_label')}", str(result.file_path)[-50:])
    info_table.add_row(f"🎯 {I18n.get('preview_mode_label')}", result.mode.value)

    # Line match status
    if result.lines_match:
        status = f"[green]✓ {I18n.get('preview_lines_match')} {result.line_count_original}[/green]"
    else:
        status = f"[red]⚠ {I18n.get('preview_lines_mismatch')} {result.line_count_original} → {result.line_count_translated}[/red]"
    info_table.add_row(f"📊 {I18n.get('preview_status_label')}", status)

    # Build diff table - git diff style (only show changed sections)
    diff_table = Table(
        title=f"[bold]{I18n.get('whole_file_diff_header')}[/bold]",
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    diff_table.add_column(I18n.get("col_line_num"), style="dim", width=6, justify="right")
    diff_table.add_column(I18n.get("col_original"), style="red", width=35)
    diff_table.add_column(I18n.get("col_translated"), style="green", width=35)

    original_lines = result.original_content.splitlines()
    translated_lines = result.translated_content.splitlines()
    total_lines = min(len(original_lines), len(translated_lines))

    # Git diff style: find changed sections and show them with context
    changed_sections = []
    i = 0
    while i < total_lines:
        orig = original_lines[i]
        trans = translated_lines[i]
        if orig != trans:
            # Found a changed line - collect the section
            section_start = i
            section_lines = []
            # Collect consecutive changes (max 5 lines per section)
            while i < total_lines and original_lines[i] != translated_lines[i] and len(section_lines) < 5:
                section_lines.append((i + 1, original_lines[i], translated_lines[i]))
                i += 1
            changed_sections.append((section_start + 1, section_lines))
        else:
            i += 1

    # Pagination for changed sections
    sections_per_page = 6
    total_diff_pages = max(1, (len(changed_sections) + sections_per_page - 1) // sections_per_page)

    # Ensure page is within bounds
    diff_page = max(0, min(diff_page, total_diff_pages - 1))

    # Get sections for current page
    start_idx = diff_page * sections_per_page
    end_idx = min(start_idx + sections_per_page, len(changed_sections))
    shown_sections = changed_sections[start_idx:end_idx]

    # Render changed sections with ellipsis between
    prev_end = 0
    for section_num, (section_start, section_lines) in enumerate(shown_sections):
        # Add ellipsis if there's a gap
        if section_start > prev_end + 1 and prev_end > 0:
            ellipsis = I18n.get("preview_ellipsis")
            diff_table.add_row("...", f"[dim]{ellipsis}[/dim]", f"[dim]{ellipsis}[/dim]")

        for line_num, orig, trans in section_lines:
            # Truncate long lines
            orig_display = orig[:33] if len(orig) > 33 else orig
            trans_display = trans[:33] if len(trans) > 33 else trans
            diff_table.add_row(str(line_num), orig_display, trans_display)

        prev_end = section_start + len(section_lines) - 1

    # Combine into Panel
    total_changes = sum(len(s[1]) for s in changed_sections)
    summary_template = I18n.get("preview_total_summary")
    summary_text = summary_template.replace('{changes}', str(total_changes)).replace('{sections}', str(len(changed_sections)))

    # Add pagination hint if multiple pages
    pagination_hint = ""
    if total_diff_pages > 1:
        pagination_hint = f" [dim]| 变更段 {diff_page + 1}/{total_diff_pages} (← → 翻页)[/dim]"

    content = Group(
        info_table,
        Text(""),
        diff_table,
        Text(""),
        Text.from_markup(f"[dim]{summary_text}{pagination_hint}[/dim]"),
        Text.from_markup(f"[dim]{I18n.get('complete_return_hint')}[/dim]"),
    )

    border_style = "green" if result.lines_match else "yellow"
    return Panel(
        content,
        title=f"[bold cyan]{I18n.get('whole_file_preview_title')}[/bold cyan]",
        border_style=border_style,
        box=box.ROUNDED,
        padding=(1, 1),
    )


async def handle_whole_file_translation(
    config: Config,
    file_path: Path,
    mode: TranslationMode,
    relative_root: Path | None = None,
) -> bool:
    """Handle whole-file translation for a single file.
    
    Args:
        relative_root: Root path for calculating backup relative paths.
                       If None, uses config.root_path (default behavior).
    
    Returns:
        True if translation was successful and applied, False otherwise.
    """
    if not config.llm_api_key:
        print_error(console, I18n.get("error_no_api_key"))
        Prompt.ask("\nPress Enter to continue...")
        return False

    translator = WholeFileTranslator(
        api_key=config.llm_api_key,
        model=config.llm_model,
        base_url=config.llm_base_url,
        force_model=config.llm_force_model,
    )

    with console.status(f"[bold yellow]{I18n.get('whole_file_translating')}[/]"):
        result = await translator.translate_file(file_path, mode)

    await translator.close()

    if not result.success:
        print_error(console, f"{I18n.get('whole_file_failed')} {result.error}")
        Prompt.ask("\nPress Enter to continue...")
        return False

    # Show preview and action selection with Live
    actions = [
        I18n.get("whole_file_apply"),
        I18n.get("whole_file_reject"),
    ]
    selected = 0
    diff_page = 0  # Track which page of diff sections is being viewed

    # Use Group to display preview AND action menu together (not overwrite)
    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            preview_panel = render_whole_file_preview(result, diff_page)
            action_panel = render_menu_panel(
                title=I18n.get("tui_select_title"),
                options=actions,
                selected=selected,
                footer=I18n.get("footer_detail_hint"),
            )
            # Combine preview and action into single display using Group
            combined = Group(preview_panel, Text(""), action_panel)
            live.update(combined)

            key = read_key()
            if key == KEY_UP:
                selected = (selected - 1) % len(actions)
            elif key == KEY_DOWN:
                selected = (selected + 1) % len(actions)
            elif key == KEY_LEFT:
                # Navigate to previous diff page
                diff_page = max(0, diff_page - 1)
            elif key == KEY_RIGHT:
                # Navigate to next diff page (will be clamped in render function)
                diff_page += 1
            elif key == KEY_BACK or key == KEY_ESC:
                return False
            elif key == KEY_ENTER:
                break
            elif key == KEY_QUIT:
                return False

    if selected == 0:  # Apply
        root_for_backup = relative_root or config.root_path
        success = translator.apply_translation(result, config.backup_dir, root_for_backup)

        # Build completion panel with professional styling
        if success:
            # Success panel with checklist
            complete_table = Table(show_header=False, box=None, expand=True)
            complete_table.add_column(width=25)
            complete_table.add_column(width=35)
            complete_table.add_row(f"[green]✓[/] {I18n.get('complete_status_label')}", f"[green]{I18n.get('complete_status_success')}[/]")
            complete_table.add_row(f"[cyan]📦[/] {I18n.get('complete_backup_location')}", str(config.backup_dir)[-40:])
            complete_table.add_row("", "")
            complete_table.add_row(f"[bold]{I18n.get('complete_verify_steps')}[/]", "")
            complete_table.add_row("[ ] 1.", "cargo check")
            complete_table.add_row("[ ] 2.", "npm run typecheck")
            complete_table.add_row("[ ] 3.", "git diff --stat")

            complete_panel = Panel(
                Group(
                    complete_table,
                    Text(""),
                    Text.from_markup(f"[dim]{I18n.get('complete_return_hint')}[/dim]"),
                ),
                title=f"[bold green]✓ {I18n.get('complete_title_success')}[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 1),
            )
        else:
            complete_panel = Panel(
                Group(
                    Text.from_markup(f"[red]✗ {I18n.get('complete_title_error')}[/red]"),
                    Text.from_markup(f"[dim]{I18n.get('whole_file_failed')}[/dim]"),
                    Text(""),
                    Text.from_markup(f"[dim]{I18n.get('complete_return_hint')}[/dim]"),
                ),
                title=f"[bold red]{I18n.get('complete_title_error')}[/bold red]",
                border_style="red",
                box=box.ROUNDED,
                padding=(1, 1),
            )

        # Show completion panel with Live
        with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
            live.update(complete_panel)
            read_key()

        return success

    return False


async def handle_scan_results(
    config: Config,
    results: list[tuple[Path, int]],
    input_dir: Path | None = None,
    default_mode: TranslationMode | None = None,
) -> None:
    """Handle scan results - paginated file list with Live navigation.
    
    Args:
        config: Configuration
        results: Scan results (file_path, chinese_line_count)
        input_dir: Optional input directory for manual path mode
        default_mode: Default translation mode from main menu
    """
    total = len(results)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = 0
    selected = 0
    mode = default_mode  # Use mode from main menu, or None to prompt user

    # Get items for current page
    def get_page_items(page_num: int) -> list[tuple[Path, int]]:
        start = page_num * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        return results[start:end]

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            items = get_page_items(page)
            if selected >= len(items):
                selected = max(0, len(items) - 1)

            panel = render_file_list_panel(
                items=items,
                selected=selected,
                page=page,
                total_pages=total_pages,
                total_rows=total,
            )
            live.update(panel)

            key = read_key()
            if key == KEY_UP and items:
                selected = max(0, selected - 1)
                continue
            if key == KEY_DOWN and items:
                selected = min(len(items) - 1, selected + 1)
                continue
            if key == KEY_LEFT and page > 0:
                page -= 1
                selected = 0
                continue
            if key == KEY_RIGHT and page < total_pages - 1:
                page += 1
                selected = 0
                continue
            if key == KEY_BACK or key == KEY_ESC:
                if input_dir:
                    print_info(console, f"✓ {I18n.get('tui_completed_directory')} {input_dir}")
                return
            if key == KEY_QUIT:
                return

            # S key for save JSON
            if key.lower() == "s":
                tool_root = PathRegistry.detect_tool_root()
                path_registry = PathRegistry(tool_root)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = path_registry.get_report_path(timestamp)
                output_data = {
                    "scan_time": datetime.now().isoformat(),
                    "total_files": len(results),
                    "total_lines": sum(r[1] for r in results),
                    "files": [{"path": str(r[0]), "chinese_lines": r[1]} for r in results],
                }
                output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
                print_success(console, f"{I18n.get('tui_saved_to')} {output_path}")
                continue

            if key == KEY_ENTER and items:
                # Translate selected file
                if not config.llm_api_key:
                    print_error(console, I18n.get("error_no_api_key"))
                    continue

                if mode is None:
                    mode = select_translation_mode()
                    if mode is None:
                        continue

                file_path = items[selected][0]
                # Use input_dir as relative_root for manual path mode
                root_for_backup = input_dir or config.root_path
                translated = await handle_whole_file_translation(config, file_path, mode, relative_root=root_for_backup)

                # Refresh the results list if translation was successful
                if translated:
                    # Re-scan the file to get updated chinese line count
                    from src.scanner import count_chinese_lines
                    new_count = count_chinese_lines(file_path, mode=mode)
                    # Update the results list
                    for idx, (path, count) in enumerate(results):
                        if path == file_path:
                            results[idx] = (path, new_count)
                            break
                    # Recalculate total
                    total = len(results)
                    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)


def render_preferences_panel(
    prefs: UserPreferences,
    selected: int,
) -> Panel:
    """Render preferences settings panel with current values."""
    # Build language display
    lang_current = I18n.get("menu_language_chinese") if prefs.language == "zh" else I18n.get("menu_language_english")
    lang_line = f"{ICON_LANGUAGE} {I18n.get('preferences_language')}: {lang_current}"

    # Build translation mode display
    mode_current = (
        I18n.get("translation_mode_comment_only")
        if prefs.translation_mode == "comment_only"
        else I18n.get("translation_mode_full")
    )
    mode_line = f"{ICON_MODE} {I18n.get('preferences_translation_mode')}: {mode_current}"

    options = [lang_line, mode_line, f"{ICON_EXIT} {I18n.get('action_return')}"]

    body = Text()
    for idx, option in enumerate(options):
        prefix = "→ " if idx == selected else "  "
        style = STYLE_SELECTED if idx == selected else STYLE_NORMAL
        # Remove the leading spaces from option since prefix already adds spacing
        display_option = option.strip() if idx < 2 else option.strip()
        body.append(f"{prefix}{display_option}\n", style=style)

    # Build current status display at top
    status_text = Text()
    status_text.append(f"{ICON_SETTINGS} {I18n.get('preferences_title')}\n\n", style=STYLE_TITLE)
    status_text.append(f"{I18n.get('preferences_current')}:\n", style=STYLE_MUTED)
    status_text.append(f"  • {I18n.get('preferences_language')}: {lang_current}\n", style="cyan")
    status_text.append(
        f"  • {I18n.get('preferences_translation_mode')}: {mode_current}\n",
        style="cyan",
    )
    status_text.append("\n")
    status_text.append(I18n.get("preferences_select_hint"), style=STYLE_MUTED)

    return Panel(
        Group(
            status_text,
            Text("\n"),
            body,
            Text("\n"),
            Text(I18n.get("preferences_footer_hint"), style=STYLE_MUTED),
        ),
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def handle_preferences_menu(config: Config) -> tuple[str, TranslationMode]:
    """Handle preferences settings menu with Live navigation.

    Returns:
        Tuple of (language, translation_mode) after user interaction.
    """
    pref_manager = PreferenceManager()
    prefs = pref_manager.load()

    # Apply loaded preferences to system
    I18n.set_lang(prefs.language)
    translation_mode = prefs.get_translation_mode()

    selected = 0
    options_count = 3  # language, mode, return

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = render_preferences_panel(prefs, selected)
            live.update(panel)

            key = read_key()
            if key == KEY_UP:
                selected = (selected - 1) % options_count
                continue
            if key == KEY_DOWN:
                selected = (selected + 1) % options_count
                continue
            if key == KEY_BACK or key == KEY_ESC or key == KEY_QUIT:
                break
            if key == KEY_ENTER:
                if selected == 0:
                    # Toggle language
                    new_lang = "en" if prefs.language == "zh" else "zh"
                    prefs = pref_manager.update_language(new_lang)
                elif selected == 1:
                    # Toggle translation mode
                    new_mode = (
                        TranslationMode.FULL
                        if prefs.translation_mode == "comment_only"
                        else TranslationMode.COMMENT_ONLY
                    )
                    prefs = pref_manager.update_translation_mode(new_mode)
                    translation_mode = prefs.get_translation_mode()
                else:
                    # Return to main menu
                    break

    # Apply final preferences
    I18n.set_lang(prefs.language)
    translation_mode = prefs.get_translation_mode()
    return prefs.language, translation_mode


def handle_backup_menu(config: Config) -> None:
    """Handle backup history menu with Live navigation."""
    backups = list_backups(config.backup_dir)

    if not backups:
        # Show notice and wait
        with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
            panel = render_notice_panel(I18n.get("tui_no_backups"))
            live.update(panel)
            read_key()
        return

    total = len(backups)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = 0
    selected = 0

    def get_page_items(page_num: int) -> list:
        start = page_num * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        return backups[start:end]

    # Live context outside while loop - single context prevents flicker
    exit_key = None
    selected_backup = None

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            items = get_page_items(page)
            if selected >= len(items):
                selected = max(0, len(items) - 1)

            panel = render_backup_list_panel(
                backups=items,
                selected=selected,
                page=page,
                total_pages=total_pages,
                total_rows=total,
            )
            live.update(panel)

            key = read_key()
            if key == KEY_UP and items:
                selected = max(0, selected - 1)
                continue
            if key == KEY_DOWN and items:
                selected = min(len(items) - 1, selected + 1)
                continue
            if key == KEY_LEFT and page > 0:
                page -= 1
                selected = 0
                continue
            if key == KEY_RIGHT and page < total_pages - 1:
                page += 1
                selected = 0
                continue
            if key == KEY_BACK or key == KEY_ESC:
                exit_key = "back"
                break
            if key == KEY_QUIT:
                exit_key = "quit"
                break

            if key == KEY_ENTER and items:
                exit_key = "enter"
                selected_backup = items[selected]
                break

    # Handle action menu outside Live context
    if exit_key == "enter" and selected_backup:
        action_result = handle_backup_actions(config, selected_backup)
        if action_result == "quit":
            return
        if action_result == "refresh":
            # Re-enter backup menu after refresh
            handle_backup_menu(config)


def handle_backup_actions(config: Config, backup) -> str:
    """Show action menu for selected backup."""
    actions = [
        I18n.get("action_restore"),
        I18n.get("action_keep_all"),
        I18n.get("action_keep_recent"),
        I18n.get("action_clean_all"),
        I18n.get("action_return"),
    ]
    selected = 0

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = render_menu_panel(
                title=I18n.get("tui_backup_actions_title"),
                options=actions,
                selected=selected,
                footer=I18n.get("footer_menu_hint"),
            )
            live.update(panel)
            key = read_key()
            if key == KEY_UP:
                selected = (selected - 1) % len(actions)
            elif key == KEY_DOWN:
                selected = (selected + 1) % len(actions)
            elif key == KEY_BACK or key == KEY_ESC:
                return "back"
            elif key == KEY_QUIT:
                return "quit"
            elif key == KEY_ENTER:
                break

    if selected == 0:  # Restore
        try:
            restored = restore_backup(config.backup_dir, config.root_path, backup.backup_id)
            print_success(console, f"{I18n.get('main_restored')} {len(restored)}")
        except Exception as e:
            print_error(console, str(e))
        Prompt.ask("\nPress Enter to continue...")
        return "refresh"

    elif selected == 1:  # Keep all
        return "back"

    elif selected == 2:  # Keep recent
        removed = cleanup_backups(config.backup_dir, keep_count=2)
        if removed:
            print_success(console, f"{I18n.get('backup_removed')} {len(removed)}")
        Prompt.ask("\nPress Enter to continue...")
        return "refresh"

    elif selected == 3:  # Clean all
        import shutil
        all_backups = list_backups(config.backup_dir)
        for b in all_backups:
            shutil.rmtree(b.backup_path)
        print_success(console, f"{I18n.get('backup_removed')} {len(all_backups)}")
        Prompt.ask("\nPress Enter to continue...")
        return "refresh"

    else:  # Return
        return "back"


async def handle_manual_path(config: Config, translation_mode: TranslationMode = TranslationMode.COMMENT_ONLY) -> None:
    """Handle manual path input with Live refresh navigation.
    
    Args:
        config: Configuration
        translation_mode: Translation mode from main menu
    """
    buffer = ""

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            # Build input panel with current buffer
            input_text = Text()
            input_text.append(buffer if buffer else I18n.get("tui_input_placeholder"), style="cyan" if buffer else "grey50")
            input_text.append("▏", style="white")

            footer = f"{I18n.get('manual_drag_hint')}\n{I18n.get('footer_menu_hint')}"

            panel = Panel(
                Group(
                    Text(f"📁 {I18n.get('menu_manual_path')}", style="magenta bold"),
                    Text(""),
                    input_text,
                    Text(""),
                    Text(footer, style="grey50"),
                ),
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            live.update(panel)

            key = read_key()

            # Handle navigation keys
            if key == KEY_BACK or key == KEY_ESC:
                # Return to main menu
                return
            if key == KEY_QUIT:
                return
            if key == KEY_ENTER:
                # Process the input path
                break

            # Handle text input
            if key == KEY_BACK and buffer:
                buffer = buffer[:-1]
                continue
            if len(key) == 1 and key.isprintable():
                buffer += key

    # Process the path after Enter
    path_str = buffer.strip()
    if not path_str:
        return

    path = Path(path_str)
    if not path.exists():
        path = config.root_path / path_str
    if not path.exists():
        # Show error and wait for key
        with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
            panel = render_notice_panel(f"⚠️ {I18n.get('tui_path_not_found')} {path_str}")
            live.update(panel)
            read_key()
        return

    if path.is_file():
        if contains_chinese(path.read_text(encoding="utf-8", errors="replace")):
            if not config.llm_api_key:
                print_error(console, I18n.get("error_no_api_key"))
                return
            # Use mode from main menu, or prompt user if not set
            mode_to_use = translation_mode if translation_mode else select_translation_mode()
            if mode_to_use:
                # For single file, use its parent directory as relative_root
                file_parent = path.parent if path.is_file() else path
                await handle_whole_file_translation(config, path, mode_to_use, relative_root=file_parent)
        else:
            with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
                panel = render_notice_panel(f"ℹ️ {I18n.get('tui_no_chinese_file')}")
                live.update(panel)
                read_key()
    else:
        console.print(f"\n[cyan]{I18n.get('tui_scan_directory')} {path}[/]")
        progress = ScanProgress(console)
        all_files = list(path.glob("**/*"))
        excludes = ["target", "dist", "node_modules", ".git", "__pycache__", "gen", ".venv"]
        all_files = [f for f in all_files if f.is_file() and not any(exc in str(f) for exc in excludes)]
        progress.start(len(all_files))

        results: list[tuple[Path, int]] = []
        for file in all_files:
            line_count = count_chinese_lines(file, mode=translation_mode)
            if line_count > 0:
                results.append((file, line_count))
            progress.advance()
        progress.stop()

        if results:
            await handle_scan_results(config, results, input_dir=path, default_mode=translation_mode)
        else:
            with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
                panel = render_notice_panel(f"ℹ️ {I18n.get('tui_no_chinese_dir')}")
                live.update(panel)
                read_key()


async def run_tui(config: Config) -> None:
    """Run the main TUI loop with Live navigation."""
    # Load user preferences at startup
    pref_manager = PreferenceManager()
    translation_mode = pref_manager.apply_to_system()

    # Helper function to build options list
    def build_options() -> list[str]:
        return [
            f"{ICON_SCAN} {I18n.get('menu_full_scan')}",
            f"{ICON_INCREMENTAL} {I18n.get('menu_incremental')}",
            f"{ICON_MANUAL} {I18n.get('menu_manual_path')}",
            f"{ICON_BACKUP} {I18n.get('menu_backup_history')}",
            f"{ICON_SETTINGS} {I18n.get('menu_preferences')}",
            f"{ICON_EXIT} {I18n.get('menu_exit')}",
        ]

    options = build_options()
    selected = 0
    lang_info = LANG_MODES[I18n.lang()]
    choice = None

    # Build title with proper Rich styling
    title_text = Text()
    title_text.append(f"{lang_info.emoji} {I18n.get('header_language')} | ", style="magenta bold")
    title_text.append(f"zh-context-scanner v{__version__}", style="bold cyan")

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = render_menu_panel(
                title=title_text,
                options=options,
                selected=selected,
                footer=I18n.get("footer_menu_hint"),
            )
            live.update(panel)

            key = read_key()
            if key == KEY_UP:
                selected = (selected - 1) % len(options)
                continue
            if key == KEY_DOWN:
                selected = (selected + 1) % len(options)
                continue
            if key == KEY_QUIT:
                choice = 5  # Exit
                break
            if key == KEY_ENTER:
                choice = selected
            else:
                continue

            # Process selection
            if choice == 5:  # Exit
                break

            if choice == 4:  # Preferences
                break

            if choice == 3:  # Backup history
                break

            if choice == 2:  # Manual path
                break

            # Full scan or incremental scan
            break

    # Handle sub-menus outside Live context
    if choice == 4:  # Preferences
        handle_preferences_menu(config)
        # Reload preferences after returning from preferences menu
        translation_mode = pref_manager.apply_to_system()
        lang_info = LANG_MODES[I18n.lang()]
        # Rebuild title with new language
        title_text = Text()
        title_text.append(f"{lang_info.emoji} {I18n.get('header_language')} | ", style="magenta bold")
        title_text.append(f"zh-context-scanner v{__version__}", style="bold cyan")
        await run_tui(config)
        return

    if choice == 3:  # Backup history
        handle_backup_menu(config)
        await run_tui(config)
        return

    if choice == 2:  # Manual path
        await handle_manual_path(config, translation_mode=translation_mode)
        await run_tui(config)
        return

    if choice == 5:  # Exit confirmed
        exit_text = Text()
        exit_text.append(I18n.get("exit_thank_you") + " ", style="dim")
        exit_text.append("zh-context-scanner", style="bold cyan")
        exit_text.append(f" v{__version__}", style="cyan")
        exit_text.append("\n\n")
        exit_text.append("✓ ", style="green")
        exit_text.append(I18n.get("exit_changes_saved"), style="green italic")
        exit_text.append("\n")
        exit_text.append("✓ ", style="green")
        exit_text.append(I18n.get("exit_backup_ready"), style="green italic")
        exit_text.append("\n\n")
        exit_text.append(I18n.get("exit_farewell"), style="bold magenta")

        exit_panel = Panel(
            exit_text,
            title=f"[bold green]✓[/] {I18n.get('exit_title')}",
            subtitle=f"[dim]{I18n.get('exit_subtitle')}[/]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(exit_panel)
        return

    # Full scan or incremental scan (choice: 0=full, 1=incremental)
    if choice == 0:
        results = await run_full_scan(config, mode=translation_mode)
    else:
        results = await run_incremental_scan(config, mode=translation_mode)

    if results:
        await handle_scan_results(config, results, default_mode=translation_mode)
        await run_tui(config)
    else:
        print_info(console, I18n.get("tui_no_chinese_dir"))
        await run_tui(config)
