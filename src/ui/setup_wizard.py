"""
File: setup_wizard.py
Description: Interactive setup wizard for project configuration
Author: Arjun Li
Created: 2026-04-16
Last Modified: 2026-04-16
Related modules: main.py, config_generator.py, tech_stack_presets.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

from src.config import Config, ScanTarget
from src.config_generator import create_scan_target, sanitize_project_name, save_config_file
from src.paths import PathRegistry
from src.preference import PreferenceManager
from src.ui.constants import (
    ICON_API_KEY,
    ICON_CHECKBOX_OFF,
    ICON_CHECKBOX_ON,
    ICON_CONFIG,
    ICON_EXIT,
    ICON_FOLDER,
    ICON_MANUAL,
    ICON_QUICK,
    ICON_SUCCESS,
    ICON_WIZARD,
    STYLE_ACCENT,
    STYLE_MUTED,
    STYLE_NORMAL,
    STYLE_SELECTED,
    STYLE_TITLE,
)
from src.ui.i18n import I18n
from src.ui.keyboard import (
    KEY_BACK,
    KEY_DOWN,
    KEY_ENTER,
    KEY_ESC,
    KEY_SPACE,
    KEY_TAB,
    KEY_UP,
    read_key,
)
from src.ui.tech_stack_presets import get_all_presets, get_default_global_excludes, merge_presets

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console(
    theme=Theme(
        {
            "accent": "cyan",
            "selected": "magenta",
            "muted": "grey50",
            "title": "magenta bold",
            "normal": "cyan",
        }
    ),
    emoji=True,
    force_terminal=True,
)


SIGNAL_BACK = "back"


def run_setup_wizard() -> Config | None:
    """Run setup wizard and return Config on success, None on exit from main menu."""
    while True:
        choice = _show_setup_menu()

        if choice == "exit":
            return None
        elif choice == "quick":
            result = _handle_quick_setup()
            if result == SIGNAL_BACK:
                continue
            elif result is None:
                return None
            else:
                return result
        elif choice == "manual":
            _handle_manual_setup()
            continue


def _show_setup_menu() -> str:
    """Show setup menu and return user choice: quick/manual/exit.

    Only this menu allows ESC to exit the entire program.
    """
    options = ["quick", "manual", "exit"]
    selected = 0

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = _render_setup_menu_panel(selected)
            live.update(panel)

            key = read_key()

            if key == KEY_UP:
                selected = (selected - 1) % len(options)
            elif key == KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key == KEY_ENTER:
                return options[selected]
            elif key == KEY_ESC or key == KEY_BACK:
                return "exit"


def _render_setup_menu_panel(selected: int) -> Panel:
    """Render setup menu selection panel."""
    options_text = [
        f"{ICON_QUICK} {I18n.get('setup_quick_option')}",
        f"{ICON_MANUAL} {I18n.get('setup_manual_option')}",
        f"{ICON_EXIT} {I18n.get('setup_exit_option')}",
    ]

    body = Text()
    for idx, option in enumerate(options_text):
        prefix = "-> " if idx == selected else "   "
        style = STYLE_SELECTED if idx == selected else STYLE_NORMAL
        body.append(f"{prefix}{option}\n", style=style)

    content = Group(
        Text(f"{ICON_WIZARD} {I18n.get('setup_title')}", style=STYLE_TITLE),
        Text(""),
        Text(I18n.get("setup_intro"), style=STYLE_MUTED),
        Text(""),
        body,
        Text(""),
        Text(I18n.get("footer_menu_hint"), style=STYLE_MUTED),
    )

    return Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _handle_quick_setup() -> Config | str | None:
    """Handle quick setup flow with proper ESC navigation.

    Returns:
        Config on success, SIGNAL_BACK to return to main menu, None on error.
    """
    scan_targets: list[ScanTarget] = []

    # Step 1: Tech stack selection (one-time)
    preset_keys = _show_tech_stack_selection()
    if preset_keys is None:
        return SIGNAL_BACK

    if not preset_keys:
        _show_warning_panel(I18n.get("tech_stack_min_warning"))
        return SIGNAL_BACK

    extensions, excludes = merge_presets(preset_keys)
    presets_info = _get_presets_display_info(preset_keys)

    # Step 2: Scan targets input (multi-add in single panel)
    result = _show_scan_targets_panel(presets_info, extensions, excludes, scan_targets)
    if result == SIGNAL_BACK:
        return SIGNAL_BACK
    elif result is None:
        return SIGNAL_BACK

    # Step 3: Project name
    project_name = _show_project_name_input()
    if project_name is None:
        return SIGNAL_BACK

    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name:
        _show_warning_panel(I18n.get("project_name_empty_warning"))
        return SIGNAL_BACK

    if sanitized_name != project_name:
        _show_info_panel(I18n.format("project_name_sanitized", sanitized_name))

    tool_root = PathRegistry.detect_tool_root()
    path_registry = PathRegistry(tool_root)
    global_excludes = get_default_global_excludes()

    config_path = save_config_file(sanitized_name, scan_targets, global_excludes, path_registry)

    pref_manager = PreferenceManager()
    pref_manager.update_config_file(str(config_path))

    has_api_key = _check_api_key(path_registry)
    if not has_api_key:
        _show_api_key_warning(path_registry)

    _show_completion_panel(sanitized_name, config_path)

    return Config(
        root_path=Path.cwd(),
        backup_dir=path_registry.backup_dir,
        project_name=sanitized_name,
        scan_targets=scan_targets,
        global_excludes=global_excludes,
    )


def _get_presets_display_info(preset_keys: list[str]) -> str:
    """Get display string for selected presets."""
    from src.ui.tech_stack_presets import get_preset_by_key
    parts = []
    for key in preset_keys:
        preset = get_preset_by_key(key)
        if preset and hasattr(preset, "emoji"):
            parts.append(f"{preset.emoji} {preset.name}")
        elif preset:
            parts.append(preset.name)
    return ", ".join(parts)


def _show_scan_targets_panel(
    presets_info: str,
    extensions: list[str],
    excludes: list[str],
    scan_targets: list[ScanTarget],
) -> str | None:
    """Show scan targets input panel with multi-add support.

    Supports hybrid mode:
    - Input mode: Type paths, Enter to add, Backspace to delete input
    - Select mode (Tab to switch): Up/Down to select, Delete to remove target

    Returns:
        "done" when user confirms targets, SIGNAL_BACK on ESC, None on error.
    """
    buffer = ""
    feedback_msg = ""
    feedback_style = ""
    select_mode = False
    selected_target_idx = 0

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = _render_scan_targets_panel(
                presets_info, scan_targets, buffer, feedback_msg, feedback_style,
                select_mode, selected_target_idx
            )
            live.update(panel)

            key = read_key()

            if select_mode:
                if key == KEY_UP and scan_targets:
                    selected_target_idx = (selected_target_idx - 1) % len(scan_targets)
                elif key == KEY_DOWN and scan_targets:
                    selected_target_idx = (selected_target_idx + 1) % len(scan_targets)
                elif key == KEY_BACK:
                    select_mode = False
                    feedback_msg = ""
                elif key == KEY_ESC:
                    return SIGNAL_BACK
                elif key.lower() == "d":
                    if scan_targets:
                        removed = scan_targets.pop(selected_target_idx)
                        if selected_target_idx >= len(scan_targets) and scan_targets:
                            selected_target_idx = len(scan_targets) - 1
                        feedback_msg = f"{I18n.get('path_removed')} {removed.path}"
                        feedback_style = "yellow"
                        if not scan_targets:
                            select_mode = False
                            selected_target_idx = 0
                elif key == KEY_TAB:
                    select_mode = False
                    feedback_msg = ""
            else:
                if key == KEY_BACK:
                    if buffer:
                        buffer = buffer[:-1]
                        feedback_msg = ""
                elif key == KEY_ESC:
                    return SIGNAL_BACK
                elif key == KEY_ENTER:
                    if not buffer.strip():
                        if scan_targets:
                            return "done"
                        feedback_msg = I18n.get("path_min_one_warning")
                        feedback_style = "yellow"
                    else:
                        path_str = buffer.strip()
                        path_obj = Path(path_str)
                        if not path_obj.exists():
                            feedback_msg = I18n.format("path_not_found_warning", path_str)
                            feedback_style = "red"
                        else:
                            resolved_path = path_obj.resolve().as_posix()
                            target = create_scan_target(resolved_path, extensions, excludes)
                            scan_targets.append(target)
                            buffer = ""
                            feedback_msg = f"{I18n.get('path_scan_target_added')} {resolved_path}"
                            feedback_style = "green"
                elif key == KEY_TAB and scan_targets:
                    select_mode = True
                    selected_target_idx = 0
                    feedback_msg = I18n.get("path_select_mode_hint")
                    feedback_style = "cyan"
                elif len(key) == 1 and key.isprintable():
                    buffer += key
                    feedback_msg = ""

    return None


def _truncate_path_suffix(path: str, max_len: int = 55) -> str:
    """Truncate path from prefix, preserving suffix (project name).

    Example: E:/Dev/.../VaultSave/apps/desktop/ui
    """
    if len(path) <= max_len:
        return path
    return "..." + path[-(max_len - 3):]


def _render_scan_targets_panel(
    presets_info: str,
    scan_targets: list[ScanTarget],
    buffer: str,
    feedback_msg: str,
    feedback_style: str,
    select_mode: bool,
    selected_target_idx: int,
) -> Panel:
    """Render scan targets multi-add panel with hybrid mode."""
    targets_list = Text()
    if scan_targets:
        for idx, target in enumerate(scan_targets, 1):
            display_path = _truncate_path_suffix(target.path, 55)
            if select_mode and idx - 1 == selected_target_idx:
                targets_list.append(f"  {idx}. {display_path}\n", style="red bold")
            else:
                targets_list.append(f"  {idx}. {display_path}\n", style="cyan")
    else:
        targets_list.append(f"  ({I18n.get('path_pending_add')})\n", style="grey50")

    if buffer:
        input_text = Text(buffer, style="cyan")
    else:
        cursor_char = "_" if int(time.time() * 2) % 2 == 0 else " "
        input_text = Text(cursor_char, style="cyan bold")

    feedback_text = Text()
    if feedback_msg:
        feedback_text.append(f"\n{feedback_msg}\n", style=feedback_style)

    if select_mode:
        footer_hint = I18n.get("path_select_footer_hint")
    else:
        footer_hint = I18n.get("path_add_footer_hint")

    content = Group(
        Text(f"{ICON_FOLDER} {I18n.get('path_add_title')}", style=STYLE_TITLE),
        Text(""),
        Text(I18n.format("path_selected_stacks", presets_info), style="muted"),
        Text(I18n.get("path_add_for_stacks"), style="muted"),
        Text(""),
        Text(I18n.get("path_added_targets"), style="cyan bold"),
        targets_list,
        Text(""),
        Text(I18n.get("path_input_label"), style=STYLE_MUTED),
        input_text,
        feedback_text,
        Text(""),
        Text(footer_hint, style=STYLE_MUTED),
    )

    return Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _show_tech_stack_selection() -> list[str] | None:
    """Show tech stack multi-select and return selected preset keys.

    Returns:
        List of selected preset keys on confirm, None on back/cancel.
    """
    presets = get_all_presets()
    selected_indices: set[int] = set()
    cursor = 0
    confirm_idx = len(presets)
    total_items = len(presets) + 1

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = _render_tech_stack_panel(presets, selected_indices, cursor)
            live.update(panel)

            key = read_key()

            if key == KEY_UP:
                cursor = (cursor - 1) % total_items
            elif key == KEY_DOWN:
                cursor = (cursor + 1) % total_items
            elif key == KEY_SPACE and cursor < confirm_idx:
                if cursor in selected_indices:
                    selected_indices.discard(cursor)
                else:
                    selected_indices.add(cursor)
            elif key == KEY_ENTER:
                if cursor == confirm_idx:
                    selected_keys = [presets[i].key for i in sorted(selected_indices)]
                    return selected_keys
                elif cursor < confirm_idx:
                    if cursor in selected_indices:
                        selected_indices.discard(cursor)
                    else:
                        selected_indices.add(cursor)
            elif key == KEY_ESC or key == KEY_BACK:
                return None

    return None


def _render_tech_stack_panel(
    presets: list,
    selected_indices: set[int],
    cursor: int,
) -> Panel:
    """Render tech stack multi-select panel with confirm option."""
    body = Text()
    confirm_idx = len(presets)

    for idx, preset in enumerate(presets):
        checked = ICON_CHECKBOX_ON if idx in selected_indices else ICON_CHECKBOX_OFF
        prefix = "->" if idx == cursor else "  "
        emoji = preset.emoji if hasattr(preset, "emoji") else ""

        if idx in selected_indices:
            style = "green bold"
        elif idx == cursor:
            style = STYLE_SELECTED
        else:
            style = STYLE_MUTED

        line = f"{prefix} [{checked}] {emoji} {preset.name}"
        body.append(f"{line}\n", style=style)

    body.append("\n")

    confirm_prefix = "->" if cursor == confirm_idx else "  "
    confirm_style = STYLE_SELECTED if cursor == confirm_idx else "cyan"
    body.append(f"{confirm_prefix} [✓] {I18n.get('tech_stack_confirm')}\n", style=confirm_style)

    content = Group(
        Text(f"{ICON_FOLDER} {I18n.get('tech_stack_title')}", style=STYLE_TITLE),
        Text(""),
        Text(I18n.get("tech_stack_description"), style=STYLE_MUTED),
        Text(""),
        body,
        Text(""),
        Text(I18n.format("tech_stack_selected_count", len(selected_indices)), style="cyan"),
        Text(""),
        Text(I18n.get("tech_stack_footer_hint"), style=STYLE_MUTED),
    )

    return Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _show_path_input() -> str | None:
    """Show path input panel and return entered path."""
    buffer = ""

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = _render_path_input_panel(buffer)
            live.update(panel)

            key = read_key()

            if key == KEY_BACK:
                if buffer:
                    buffer = buffer[:-1]
            elif key == KEY_ESC:
                return None
            elif key == KEY_ENTER:
                return buffer.strip()
            elif len(key) == 1 and key.isprintable():
                buffer += key

    return None


def _render_path_input_panel(buffer: str) -> Panel:
    """Render path input panel."""
    input_text = Text()
    input_text.append(buffer if buffer else I18n.get("path_drag_hint"), style="cyan" if buffer else "grey50")
    input_text.append("|", style="white")

    content = Group(
        Text(f"{ICON_FOLDER} {I18n.get('path_input_title')}", style=STYLE_TITLE),
        Text(""),
        input_text,
        Text(""),
        Text(I18n.get("manual_drag_hint"), style=STYLE_MUTED),
        Text(""),
        Text(I18n.get("footer_input_hint"), style=STYLE_MUTED),
    )

    return Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _show_add_another_prompt() -> bool | None:
    """Show add another target prompt and return True/False/None."""
    options = [True, False]
    selected = 0

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = _render_add_another_panel(selected)
            live.update(panel)

            key = read_key()

            if key == KEY_UP or key == KEY_DOWN:
                selected = (selected + 1) % len(options)
            elif key == KEY_ENTER:
                return options[selected]
            elif key == KEY_ESC or key == KEY_BACK:
                return None


def _render_add_another_panel(selected: int) -> Panel:
    """Render add another target prompt panel."""
    options_text = [
        f"{ICON_FOLDER} {I18n.get('path_yes')}",
        f"{ICON_SUCCESS} {I18n.get('path_no')}",
    ]

    body = Text()
    for idx, option in enumerate(options_text):
        prefix = "-> " if idx == selected else "   "
        style = STYLE_SELECTED if idx == selected else STYLE_NORMAL
        body.append(f"{prefix}{option}\n", style=style)

    content = Group(
        Text(I18n.get("path_add_another"), style=STYLE_TITLE),
        Text(""),
        body,
        Text(""),
        Text(I18n.get("footer_menu_hint"), style=STYLE_MUTED),
    )

    return Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _show_project_name_input() -> str | None:
    """Show project name input panel."""
    buffer = ""

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        while True:
            panel = _render_project_name_panel(buffer)
            live.update(panel)

            key = read_key()

            if key == KEY_BACK:
                if buffer:
                    buffer = buffer[:-1]
            elif key == KEY_ESC:
                return None
            elif key == KEY_ENTER:
                return buffer.strip()
            elif len(key) == 1 and key.isprintable():
                buffer += key

    return None


def _render_project_name_panel(buffer: str) -> Panel:
    """Render project name input panel."""
    input_text = Text()
    input_text.append(buffer if buffer else I18n.get("project_name_example"), style="cyan" if buffer else "grey50")
    input_text.append("|", style="white")

    content = Group(
        Text(f"{ICON_CONFIG} {I18n.get('project_name_title')}", style=STYLE_TITLE),
        Text(""),
        input_text,
        Text(""),
        Text(I18n.get("project_name_explanation"), style=STYLE_MUTED),
        Text(""),
        Text(I18n.get("footer_input_hint"), style=STYLE_MUTED),
    )

    return Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _check_api_key(path_registry: PathRegistry) -> bool:
    """Check if API key is configured in .env.local."""
    env_path = path_registry.env_local
    if not env_path.exists():
        return False

    content = env_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in ("LLM_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "i18n_auto_translate_k"):
                return True
    return False


def _show_api_key_warning(path_registry: PathRegistry) -> None:
    """Show API key not configured warning."""
    env_path = path_registry.env_local

    content = Group(
        Text(f"{ICON_API_KEY} {I18n.get('setup_no_api_key')}", style="yellow bold"),
        Text(""),
        Text(I18n.format("setup_api_key_hint", str(env_path)), style=STYLE_MUTED),
        Text(""),
        Text(I18n.get("setup_press_enter"), style=STYLE_MUTED),
    )

    panel = Panel(
        content,
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        live.update(panel)
        read_key()


def _show_completion_panel(project_name: str, config_path: Path) -> None:
    """Show setup completion panel."""
    content = Group(
        Text(f"{ICON_SUCCESS} {I18n.get('setup_complete_title')}", style="green bold"),
        Text(""),
        Text(I18n.get("setup_project_created"), style="cyan"),
        Text(project_name, style="magenta bold"),
        Text(""),
        Text(I18n.get("setup_config_saved"), style="cyan"),
        Text(str(config_path), style="dim"),
        Text(""),
        Text(I18n.get("setup_press_enter"), style=STYLE_MUTED),
    )

    panel = Panel(
        content,
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        live.update(panel)
        read_key()


def _handle_manual_setup() -> None:
    """Handle manual setup flow."""
    tool_root = PathRegistry.detect_tool_root()
    project_config = tool_root / "Project_Config.yaml"

    content = Group(
        Text(f"{ICON_MANUAL} {I18n.get('setup_manual_option')}", style=STYLE_TITLE),
        Text(""),
        Text(I18n.get("setup_manual_config_location"), style="cyan"),
        Text(str(project_config), style="yellow bold"),
        Text(""),
        Text(I18n.get("setup_manual_edit_hint"), style=STYLE_MUTED),
        Text(""),
        Text(I18n.get("setup_press_enter_exit"), style=STYLE_MUTED),
    )

    panel = Panel(
        content,
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        live.update(panel)
        read_key()


def _show_warning_panel(message: str) -> None:
    """Show warning panel."""
    panel = Panel(
        Text(message, style="yellow bold"),
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        live.update(panel)
        read_key()


def _show_info_panel(message: str) -> None:
    """Show info panel."""
    panel = Panel(
        Text(message, style="cyan"),
        border_style=STYLE_ACCENT,
        box=box.ROUNDED,
        padding=(1, 2),
    )

    with Live(console=console, auto_refresh=True, refresh_per_second=10, screen=True) as live:
        live.update(panel)
        read_key()
