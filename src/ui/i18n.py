"""
File: ui/i18n.py
Description: TUI internationalization (EN/ZH bilingual support)
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LangMode:
    """Language mode configuration."""
    key: str
    label: str
    emoji: str


LANG_MODES: dict[str, LangMode] = {
    "en": LangMode(key="en", label="English", emoji="🌐"),
    "zh": LangMode(key="zh", label="中文", emoji="🇨🇳"),
}


class I18n:
    """TUI internationalization manager."""

    _lang: str = "zh"  # Default to Chinese

    MESSAGES: dict[str, dict[str, str]] = {
        # === Header ===
        "header_title": {
            "en": "zh-context-scanner v1.0.2",
            "zh": "zh-context-scanner v1.0.2",
        },
        "header_language": {
            "en": "Language: English",
            "zh": "语言: 中文",
        },
        # === Main.py Headless ===
        "main_scan_complete": {
            "en": "Scan complete:",
            "zh": "扫描完成:",
        },
        "main_files": {
            "en": "files",
            "zh": "文件",
        },
        "main_matches": {
            "en": "matches",
            "zh": "处中文",
        },
        "main_error_input_required": {
            "en": "Error: --input report.json required for --replace",
            "zh": "错误: --replace 需要 --input report.json",
        },
        "main_error_no_api": {
            "en": "Error: API key not found",
            "zh": "错误: 未找到 API 密钥",
        },
        "main_replaced": {
            "en": "Replaced:",
            "zh": "已替换:",
        },
        "main_skipped": {
            "en": "Skipped:",
            "zh": "已跳过:",
        },
        "main_backup": {
            "en": "Backup:",
            "zh": "备份:",
        },
        "main_restored": {
            "en": "Restored files",
            "zh": "已恢复文件",
        },
        "main_error": {
            "en": "Error:",
            "zh": "错误:",
        },
        # === Menu ===
        "menu_full_scan": {
            "en": "Full Scan",
            "zh": "全仓库扫描",
        },
        "menu_incremental": {
            "en": "Incremental Scan",
            "zh": "增量扫描（基于修改时间）",
        },
        "menu_manual_path": {
            "en": "Manual Path Input",
            "zh": "手动输入路径",
        },
        "menu_backup_history": {
            "en": "Backup History",
            "zh": "查看历史备份",
        },
        "menu_language": {
            "en": "Language Switch",
            "zh": "语言切换",
        },
        "menu_language_label": {
            "en": "Language:",
            "zh": "语言:",
        },
        "menu_language_chinese": {
            "en": "English",
            "zh": "中文",
        },
        "menu_language_english": {
            "en": "English",
            "zh": "English",
        },
        "menu_exit": {
            "en": "Exit",
            "zh": "退出",
        },
        "menu_prompt": {
            "en": "Select option:",
            "zh": "请选择操作:",
        },
        # === Scan Results ===
        "scan_complete": {
            "en": "Scan Complete:",
            "zh": "扫描完成:",
        },
        "scan_files": {
            "en": "files",
            "zh": "文件",
        },
        "scan_matches": {
            "en": "Chinese texts found",
            "zh": "处中文",
        },
        "scan_warnings": {
            "en": "warnings",
            "zh": "警告",
        },
        "col_file": {
            "en": "File",
            "zh": "文件",
        },
        "col_count": {
            "en": "Count",
            "zh": "中文数量",
        },
        "col_warnings": {
            "en": "Warnings",
            "zh": "警告数量",
        },
        "result_prompt": {
            "en": "Enter # to preview | S Save JSON | R Replace | Enter Back",
            "zh": "输入序号预览 | S 保存JSON | R 执行替换 | Enter 返回",
        },
        # === File Preview ===
        "preview_title": {
            "en": "Chinese texts",
            "zh": "处中文",
        },
        "preview_raw_mode": {
            "en": "[RAW MODE] Showing original Chinese positions - Press T to translate",
            "zh": "[原始模式] 显示中文位置 - 按 T 开始翻译",
        },
        "preview_translated_mode": {
            "en": "[TRANSLATED MODE] Showing translation preview",
            "zh": "[翻译模式] 显示翻译预览",
        },
        "preview_translate_btn": {
            "en": "[T] Translate Preview (call DeepSeek API)",
            "zh": "[T] 翻译预览（调用 DeepSeek API）",
        },
        "preview_hint": {
            "en": "Hint: Press T to start translation, will not auto-execute",
            "zh": "提示：按 T 才会开始翻译，不会自动执行",
        },
        "error_invalid_input": {
            "en": "Invalid input",
            "zh": "输入无效",
        },
        # === TUI Hardcoded Fixes ===
        "tui_original_text": {
            "en": "Original",
            "zh": "原文",
        },
        "tui_translated_text": {
            "en": "Translated",
            "zh": "译文",
        },
        "tui_input_index_hint": {
            "en": "Enter # to preview file (show original positions only)",
            "zh": "输入序号 → 预览该文件（仅显示原文位置）",
        },
        "tui_save_json_hint": {
            "en": "S → Save JSON report",
            "zh": "S → 保存 JSON 报告",
        },
        "tui_return_menu_hint": {
            "en": "Enter → Return to main menu",
            "zh": "Enter → 返回主菜单",
        },
        "tui_skip_warnings": {
            "en": "S → Skip warnings",
            "zh": "S → 跳过警告项",
        },
        "tui_return_list_hint": {
            "en": "R → Return to file list",
            "zh": "R → 返回文件列表",
        },
        "tui_translate_btn": {
            "en": "T → Translate preview (call DeepSeek API)",
            "zh": "T → 翻译预览（调用 DeepSeek API）",
        },
        "tui_translate_single": {
            "en": "Single file translation",
            "zh": "单个文件翻译",
        },
        "tui_translate_all": {
            "en": "Translate all files",
            "zh": "翻译所有文件",
        },
        "tui_completed_directory": {
            "en": "Completed directory:",
            "zh": "已完成目录:",
        },
        "tui_translate_hint": {
            "en": "Hint: Press T to start translation, will NOT auto-execute",
            "zh": "提示：按 T 才会开始翻译，不会自动执行",
        },
        "tui_translating_status": {
            "en": "Translating...",
            "zh": "正在翻译...",
        },
        "tui_backup_replace_status": {
            "en": "Backing up and replacing...",
            "zh": "备份并替换...",
        },
        "tui_confirm_title": {
            "en": "Confirm Replacement",
            "zh": "确认替换",
        },
        "tui_confirm_file": {
            "en": "File:",
            "zh": "文件:",
        },
        "tui_confirm_count": {
            "en": "Replace count:",
            "zh": "替换数量:",
        },
        "tui_confirm_skip": {
            "en": "Warnings skipped:",
            "zh": "警告跳过:",
        },
        "tui_confirm_warning": {
            "en": "Warning: Please manually verify syntax after replacement",
            "zh": "警告: 替换后请手动验证语法正确",
        },
        "tui_complete_title": {
            "en": "Replacement Complete",
            "zh": "替换完成",
        },
        "tui_replaced_count": {
            "en": "Replaced:",
            "zh": "已替换:",
        },
        "tui_skipped_count": {
            "en": "Skipped:",
            "zh": "已跳过:",
        },
        "tui_backup_path": {
            "en": "Backup location:",
            "zh": "备份位置:",
        },
        "tui_verify_hint": {
            "en": "Run cargo check / npm run typecheck to verify",
            "zh": "请运行 cargo check / npm run typecheck 验证",
        },
        "tui_restore_hint": {
            "en": "Restore with: python -m src.main --restore",
            "zh": "如有问题: python -m src.main --restore",
        },
        "tui_scan_directory": {
            "en": "Scanning directory:",
            "zh": "扫描目录:",
        },
        "tui_no_chinese_file": {
            "en": "No Chinese text found in this file",
            "zh": "该文件未找到中文",
        },
        "tui_no_chinese_dir": {
            "en": "No Chinese text found in this directory",
            "zh": "该目录未找到中文",
        },
        "tui_translation_failed": {
            "en": "Translation failed",
            "zh": "翻译失败",
        },
        "tui_no_backups": {
            "en": "No backups found",
            "zh": "未找到备份",
        },
        "tui_saved_to": {
            "en": "Saved to:",
            "zh": "已保存至:",
        },
        "tui_path_not_found": {
            "en": "Path not found:",
            "zh": "路径未找到:",
        },
        "preview_apply": {
            "en": "[A] Apply replaceable",
            "zh": "[A] 应用可替换项",
        },
        "preview_skip": {
            "en": "[S] Skip warnings",
            "zh": "[S] 跳过警告项",
        },
        "preview_return": {
            "en": "[R] Return",
            "zh": "[R] 返回",
        },
        "line_prefix": {
            "en": "L",
            "zh": "行",
        },
        "arrow_to": {
            "en": "->",
            "zh": "→",
        },
        # === Replace Confirmation ===
        "confirm_title": {
            "en": "Confirm Replacement",
            "zh": "确认替换",
        },
        "confirm_replace_count": {
            "en": "Will replace Chinese texts",
            "zh": "将替换处中文",
        },
        "confirm_backup_dir": {
            "en": "Backup directory:",
            "zh": "备份目录:",
        },
        "confirm_warning_hint": {
            "en": "Warning: Run cargo check / npm run typecheck after replacement",
            "zh": "警告: 替换后请运行 cargo check / npm run typecheck 验证",
        },
        "confirm_prompt": {
            "en": "Confirm? [Y/n]",
            "zh": "确认执行? [Y/n]",
        },
        # === Replace Complete ===
        "replace_complete": {
            "en": "Replacement Complete!",
            "zh": "替换完成！",
        },
        "replace_replaced": {
            "en": "Replaced:",
            "zh": "已替换:",
        },
        "replace_skipped": {
            "en": "Skipped:",
            "zh": "已跳过:",
        },
        "replace_complex": {
            "en": "(complex scenarios)",
            "zh": "（复杂场景）",
        },
        "replace_backup_location": {
            "en": "Backup location:",
            "zh": "备份位置:",
        },
        "verify_hint": {
            "en": "Run these commands to verify:",
            "zh": "请运行以下命令验证:",
        },
        "verify_cargo": {
            "en": "cargo check              # Rust syntax check",
            "zh": "cargo check              # Rust 语法检查",
        },
        "verify_npm": {
            "en": "npm run typecheck        # TypeScript type check",
            "zh": "npm run typecheck        # TypeScript 类型检查",
        },
        "verify_git": {
            "en": "git diff                 # View changes",
            "zh": "git diff                 # 查看变更详情",
        },
        "restore_hint": {
            "en": "Restore backup with: python -m src.main --restore latest",
            "zh": "如有问题，可恢复备份: python -m src.main --restore latest",
        },
        # === Backup History ===
        "backup_title": {
            "en": "Backup History",
            "zh": "历史备份",
        },
        "backup_found": {
            "en": "Found backups",
            "zh": "发现历史备份",
        },
        "backup_size": {
            "en": "Total size:",
            "zh": "占用:",
        },
        "backup_keep_all": {
            "en": "[1] Keep all",
            "zh": "[1] 保留全部",
        },
        "backup_keep_recent": {
            "en": "[2] Keep recent 2",
            "zh": "[2] 仅保留最近 2 次",
        },
        "backup_clean_all": {
            "en": "[3] Clean all",
            "zh": "[3] 清空全部",
        },
        "backup_restored": {
            "en": "Restored files from backup",
            "zh": "已从备份恢复文件",
        },
        "backup_removed": {
            "en": "Removed backups:",
            "zh": "已删除备份:",
        },
        # === Progress ===
        "progress_scanning": {
            "en": "Scanning files...",
            "zh": "扫描文件中...",
        },
        "progress_collecting": {
            "en": "Collecting files...",
            "zh": "收集文件中...",
        },
        "progress_translating": {
            "en": "Translating...",
            "zh": "翻译中...",
        },
        "progress_replacing": {
            "en": "Replacing...",
            "zh": "替换中...",
        },
        "progress_title": {
            "en": "Scanning Progress",
            "zh": "扫描进度",
        },
        "progress_full_title": {
            "en": "Full Scan",
            "zh": "全量扫描",
        },
        "progress_incremental_title": {
            "en": "Incremental Scan",
            "zh": "增量扫描",
        },
        "progress_last_scan": {
            "en": "Last full scan",
            "zh": "上次全量扫描",
        },
        "progress_files_found": {
            "en": "Files with Chinese",
            "zh": "含中文文件",
        },
        "progress_collected": {
            "en": "Scanned",
            "zh": "已扫描",
        },
        "progress_elapsed": {
            "en": "Elapsed",
            "zh": "耗时",
        },
        "progress_hint": {
            "en": "Press Ctrl+C to abort",
            "zh": "按 Ctrl+C 可中断",
        },
        "progress_total_scanned": {
            "en": "Total scanned",
            "zh": "已扫描",
        },
        "progress_complete_title": {
            "en": "Scan Complete",
            "zh": "扫描完成",
        },
        "progress_complete_with_results": {
            "en": "Found files containing Chinese text",
            "zh": "已发现含中文的文件",
        },
        "progress_complete_no_results": {
            "en": "No Chinese text found",
            "zh": "未找到中文内容",
        },
        "progress_complete_hint": {
            "en": "Press Enter to continue",
            "zh": "按 Enter 继续",
        },
        # === Errors ===
        "error_no_api_key": {
            "en": "API key not found. Please set i18n_auto_translate_k in .env.local",
            "zh": "未找到 API 密钥。请在 .env.local 中设置 i18n_auto_translate_k",
        },
        "error_scan_failed": {
            "en": "Scan failed:",
            "zh": "扫描失败：",
        },
        "error_translate_failed": {
            "en": "Translation failed:",
            "zh": "翻译失败：",
        },
        "error_backup_not_found": {
            "en": "Backup not found:",
            "zh": "未找到备份：",
        },
        # === Manual Path ===
        "manual_prompt": {
            "en": "Enter file/directory path:",
            "zh": "输入文件或目录路径:",
        },
        "manual_drag_hint": {
            "en": "(You can drag and drop file/folder here)",
            "zh": "（可拖拽文件或文件夹到此）",
        },
        # === Translation Mode ===
        "mode_title": {
            "en": "Select Translation Mode",
            "zh": "选择翻译模式",
        },
        "mode_comment_only": {
            "en": "[C] Comment mode (default) - Only translate comments",
            "zh": "[C] 注释模式（默认） - 仅翻译注释",
        },
        "mode_full": {
            "en": "[F] Full mode - Translate all Chinese text",
            "zh": "[F] 全量模式 - 翻译所有中文",
        },
        "mode_selected": {
            "en": "Selected mode:",
            "zh": "已选模式:",
        },
        # === Whole File Translation ===
        "whole_file_translating": {
            "en": "The large model is translating the document (Python is supervising with a whip in hand)...",
            "zh": "大模型正在翻译文件(Python正手持鞭子监工中)...",
        },
        "whole_file_wait_hint": {
            "en": "Please wait a moment, do not close the terminal...",
            "zh": "稍候片刻，请勿关闭终端...",
        },
        "single_file_translation_mode": {
            "en": "Single-File Translation Mode",
            "zh": "单文件翻译模式",
        },
        "translating_file_label": {
            "en": "Translating:",
            "zh": "正在翻译:",
        },
        "whole_file_preview_title": {
            "en": "Whole-File Translation Preview",
            "zh": "整体文件翻译预览",
        },
        "whole_file_lines_mismatch": {
            "en": "Line count mismatch! Original: {}, Translated: {}",
            "zh": "行数不匹配！原文: {} 行，译文: {} 行",
        },
        "whole_file_diff_header": {
            "en": "Diff (first 30 lines)",
            "zh": "差异对比（前 30 行）",
        },
        "whole_file_original_header": {
            "en": "Original",
            "zh": "原文",
        },
        "whole_file_translated_header": {
            "en": "Translated",
            "zh": "译文",
        },
        "whole_file_apply": {
            "en": "[A] Apply translation",
            "zh": "[A] 应用翻译",
        },
        "whole_file_reject": {
            "en": "[R] Reject and return",
            "zh": "[R] 拒绝并返回",
        },
        "whole_file_success": {
            "en": "Translation applied successfully",
            "zh": "翻译已成功应用",
        },
        "whole_file_failed": {
            "en": "Translation failed:",
            "zh": "翻译失败：",
        },
        # === Live Navigation Footer ===
        "footer_nav_hint": {
            "en": "↑／↓ Select | ←／→ Page | Enter Confirm | q Quit",
            "zh": "↑／↓ 选择 | ←／→ 翻页 | Enter 确定 | q 退出",
        },
        "footer_page_hint": {
            "en": "←／→ Page | ↑／↓ Select | Enter Open | Backspace Back | q Quit",
            "zh": "←／→ 翻页 | ↑／↓ 选择 | Enter 打开 | Backspace 返回 | q 退出",
        },
        "footer_menu_hint": {
            "en": "↑／↓ Select | Enter Confirm | q Quit",
            "zh": "↑／↓ 选择 | Enter 确定 | q 退出",
        },
        "footer_detail_hint": {
            "en": "↑／↓ Select action | Enter Confirm | Backspace Return",
            "zh": "↑／↓ 选择操作 | Enter 确定 | Backspace 返回",
        },
        "footer_page_info": {
            "en": "Page",
            "zh": "页",
        },
        "footer_total": {
            "en": "Total",
            "zh": "总数",
        },
        "footer_list_hint": {
            "en": "↑／↓ Select | ←／→ Page | Enter Translate | S Save JSON | Backspace Return | q Quit",
            "zh": "↑／↓ 选择 | ←／→ 翻页 | Enter 翻译 | S 保存 JSON | Backspace 返回 | q 退出",
        },
        "footer_backup_hint": {
            "en": "↑／↓ Select | ←／→ Page | Enter Restore | Backspace Return | q Quit",
            "zh": "↑／↓ 选择 | ←／→ 翻页 | Enter 恢复 | Backspace 返回 | q 退出",
        },
        "scan_results_title": {
            "en": "Scan Results",
            "zh": "扫描结果",
        },
        "col_files": {
            "en": "files",
            "zh": "文件",
        },
        "tui_no_files": {
            "en": "No files found",
            "zh": "未找到文件",
        },
        "tui_select_title": {
            "en": "Select Option",
            "zh": "选择操作",
        },
        "tui_backup_actions_title": {
            "en": "Backup Actions",
            "zh": "备份操作",
        },
        "action_keep_all": {
            "en": "Keep all backups",
            "zh": "保留所有备份",
        },
        "action_keep_recent": {
            "en": "Keep recent 2 backups",
            "zh": "保留最近2个备份",
        },
        "action_clean_all": {
            "en": "Clean all backups",
            "zh": "清理所有备份",
        },
        "action_restore": {
            "en": "Restore this backup",
            "zh": "恢复此备份",
        },
        "action_return": {
            "en": "Return to main menu",
            "zh": "返回主菜单",
        },
        "tui_input_placeholder": {
            "en": "(Enter file/directory path, or Backspace to return)",
            "zh": "(输入文件或目录路径，Backspace 返回)",
        },
        "backup_col_filename": {
            "en": "Filename",
            "zh": "文件名",
        },
        "backup_col_count": {
            "en": "Count",
            "zh": "数量",
        },
        "backup_col_time": {
            "en": "Time",
            "zh": "时间",
        },
        "backup_unknown_file": {
            "en": "(unknown)",
            "zh": "(未知)",
        },
        "complete_status_success": {
            "en": "Successfully applied",
            "zh": "已成功应用",
        },
        "complete_backup_location": {
            "en": "Backup location:",
            "zh": "备份位置:",
        },
        "complete_verify_steps": {
            "en": "Verification steps",
            "zh": "验证步骤",
        },
        "complete_return_hint": {
            "en": "Press Enter to return",
            "zh": "按 Enter 返回主菜单",
        },
        "complete_title_success": {
            "en": "Translation Complete",
            "zh": "翻译完成",
        },
        "complete_title_error": {
            "en": "Error",
            "zh": "错误",
        },
        "complete_status_label": {
            "en": "Translation status:",
            "zh": "翻译状态:",
        },
        "preview_file_label": {
            "en": "File:",
            "zh": "文件:",
        },
        "preview_mode_label": {
            "en": "Mode:",
            "zh": "模式:",
        },
        "preview_status_label": {
            "en": "Status:",
            "zh": "状态:",
        },
        "preview_lines_match": {
            "en": "Lines match:",
            "zh": "行数匹配:",
        },
        "preview_lines_mismatch": {
            "en": "Lines mismatch:",
            "zh": "行数不匹配:",
        },
        "preview_diff_count": {
            "en": "changes, showing first",
            "zh": "处变更，显示前",
        },
        "preview_lines_suffix": {
            "en": "lines",
            "zh": "行",
        },
        "preview_no_diff": {
            "en": "No differences",
            "zh": "无差异",
        },
        "col_original": {
            "en": "Original",
            "zh": "原文",
        },
        "col_translated": {
            "en": "Translated",
            "zh": "译文",
        },
        "col_line_num": {
            "en": "Line",
            "zh": "行号",
        },
        "preview_remaining_sections": {
            "en": "... more sections",
            "zh": "... 还有 {count} 个变更段",
        },
        "preview_total_summary": {
            "en": "Total {changes} lines changed, {sections} sections",
            "zh": "共 {changes} 行变更，{sections} 个变更段",
        },
        "preview_ellipsis": {
            "en": "---",
            "zh": "───",
        },
        # === Translation Mode Switch ===
        "menu_translation_mode": {
            "en": "Translation Mode",
            "zh": "翻译模式",
        },
        "menu_translation_mode_label": {
            "en": "Translation Mode:",
            "zh": "翻译模式:",
        },
        "translation_mode_comment_only": {
            "en": "Comment Only (fast)",
            "zh": "仅翻译注释 (快速)",
        },
        "translation_mode_full": {
            "en": "Full Content (slow)",
            "zh": "全内容翻译 (慢速)",
        },
        "translation_mode_selected": {
            "en": "Current mode:",
            "zh": "当前模式:",
        },
        # === Preferences Settings ===
        "menu_preferences": {
            "en": "Preferences",
            "zh": "偏好设置",
        },
        "preferences_title": {
            "en": "Preferences Settings",
            "zh": "偏好设置",
        },
        "preferences_language": {
            "en": "Language",
            "zh": "语言",
        },
        "preferences_translation_mode": {
            "en": "Translation Mode",
            "zh": "翻译模式",
        },
        "preferences_current": {
            "en": "Current",
            "zh": "当前",
        },
        "preferences_saved": {
            "en": "Settings saved",
            "zh": "设置已保存",
        },
        "preferences_language_section": {
            "en": "Language Selection",
            "zh": "语言选择",
        },
        "preferences_mode_section": {
            "en": "Translation Mode Selection",
            "zh": "翻译模式选择",
        },
        "preferences_select_hint": {
            "en": "Press Enter to change, Backspace to return",
            "zh": "Enter 切换 | Backspace 返回",
        },
        "preferences_footer_hint": {
            "en": "↑／↓ Select | Enter Change | Backspace Return | q Quit",
            "zh": "↑／↓ 选择 | Enter 切换 | Backspace 返回 | q 退出",
        },
        "preferences_project": {
            "en": "Current Project",
            "zh": "当前项目",
        },
        "preferences_init_project": {
            "en": "Initialize Project",
            "zh": "项目初始化",
        },
        "preferences_no_project": {
            "en": "(Not configured)",
            "zh": "(未配置)",
        },
        "init_confirm_title": {
            "en": "Confirm Project Initialization",
            "zh": "确认项目初始化",
        },
        "init_confirm_message": {
            "en": "This will delete the existing config and reset preferences",
            "zh": "将删除现有配置文件并重置偏好设置",
        },
        "init_confirm_action": {
            "en": "Confirm Initialize",
            "zh": "确认初始化",
        },
        "init_cancel_action": {
            "en": "Cancel",
            "zh": "取消",
        },
        "init_confirm_file": {
            "en": "Config file:",
            "zh": "配置文件:",
        },
        # === Exit Screen ===
        "exit_thank_you": {
            "en": "Thank you for using",
            "zh": "感谢您使用",
        },
        "exit_changes_saved": {
            "en": "All changes have been saved",
            "zh": "所有变更已保存",
        },
        "exit_backup_ready": {
            "en": "Backup system is ready",
            "zh": "备份系统已就绪",
        },
        "exit_farewell": {
            "en": "See you next time! 👋",
            "zh": "下次再见！👋",
        },
        "exit_title": {
            "en": "Exit Successful",
            "zh": "退出成功",
        },
        "exit_subtitle": {
            "en": "Press Ctrl+C to close",
            "zh": "按 Ctrl+C 关闭",
        },
        # === Setup Wizard ===
        "setup_title": {
            "en": "Setup Wizard",
            "zh": "设置向导",
        },
        "setup_intro": {
            "en": "Configure zh-context-scanner for your project",
            "zh": "为您的项目配置中文扫描工具",
        },
        "setup_quick_option": {
            "en": "Quick Setup (Interactive)",
            "zh": "快速设置（交互式）",
        },
        "setup_manual_option": {
            "en": "Manual Setup (Edit YAML)",
            "zh": "手动设置（编辑 YAML）",
        },
        "setup_exit_option": {
            "en": "Exit",
            "zh": "退出",
        },
        "setup_complete_title": {
            "en": "Setup Complete!",
            "zh": "设置完成！",
        },
        "setup_success_title": {
            "en": "Success",
            "zh": "成功",
        },
        "setup_project_created": {
            "en": "Project configured:",
            "zh": "已配置项目:",
        },
        "setup_config_saved": {
            "en": "Config saved to:",
            "zh": "配置已保存至:",
        },
        "setup_press_enter": {
            "en": "Press Enter to continue...",
            "zh": "按 Enter 继续...",
        },
        "setup_manual_hint": {
            "en": "Please manually edit:",
            "zh": "请手动编辑:",
        },
        "setup_manual_config_location": {
            "en": "Project config file location:",
            "zh": "项目配置文件位置:",
        },
        "setup_manual_edit_hint": {
            "en": "Edit this file to customize scan targets and excludes",
            "zh": "编辑此文件可自定义扫描目标和排除目录",
        },
        "setup_press_enter_exit": {
            "en": "Press Enter to exit...",
            "zh": "按 Enter 退出...",
        },
        "setup_no_api_key": {
            "en": "API Key not configured. Please edit .env.local first.",
            "zh": "API Key 未配置。请先编辑 .env.local。",
        },
        "setup_api_key_hint": {
            "en": "API Key location:",
            "zh": "API Key 位置:",
        },
        "setup_wizard_menu_hint": {
            "en": "Select setup method",
            "zh": "选择设置方式",
        },
        # === Tech Stack Selection ===
        "tech_stack_title": {
            "en": "Select Tech Stacks",
            "zh": "选择技术栈",
        },
        "tech_stack_description": {
            "en": "Choose all stacks in your project (multi-select)",
            "zh": "选择项目中使用的所有技术栈（多选）",
        },
        "tech_stack_footer_hint": {
            "en": "Space/Enter Toggle | ESC Back",
            "zh": "Space/Enter 切换选中 | ESC 返回上一步",
        },
        "tech_stack_selected_count": {
            "en": "Selected: {} stacks",
            "zh": "已选择: {} 个技术栈",
        },
        "tech_stack_min_warning": {
            "en": "Please select at least one tech stack",
            "zh": "请至少选择一个技术栈",
        },
        "tech_stack_confirm": {
            "en": "Confirm Selection",
            "zh": "确认选择",
        },
        # === Path Input ===
        "path_input_title": {
            "en": "Enter Scan Target Path",
            "zh": "输入扫描目标路径",
        },
        "path_add_title": {
            "en": "Add Scan Targets",
            "zh": "添加扫描目标",
        },
        "path_selected_stacks": {
            "en": "Selected stacks: {}",
            "zh": "已选技术栈 {}",
        },
        "path_add_for_stacks": {
            "en": "Add scan targets for them",
            "zh": "为它们添加扫描的目标",
        },
        "path_added_targets": {
            "en": "Added targets:",
            "zh": "已添加目标:",
        },
        "path_pending_add": {
            "en": "pending...",
            "zh": "待添加...",
        },
        "path_input_label": {
            "en": "Input path (drag/paste/type):",
            "zh": "输入路径(支持文件夹拖拽/粘贴/输入):",
        },
        "path_add_footer_hint": {
            "en": "Enter Add | Empty+Enter Finish | Tab Select | ESC Back",
            "zh": "Enter 确认添加 | 空输入+Enter 完成 | Tab 选择模式 | ESC 返回",
        },
        "path_select_footer_hint": {
            "en": "Up/Down Select | D Delete | Tab/Backspace Exit Select | ESC Back",
            "zh": "↑↓ 选择 | D 删除选中 | Tab/Backspace 退出选择 | ESC 返回",
        },
        "path_removed": {
            "en": "Removed target:",
            "zh": "已移除目标:",
        },
        "path_select_mode_hint": {
            "en": "Select mode: use Up/Down to select, D to delete",
            "zh": "选择模式: ↑↓ 选择目标, D 删除选中",
        },
        "path_min_one_warning": {
            "en": "Please add at least one scan target",
            "zh": "请至少添加一个扫描目标",
        },
        "path_drag_hint": {
            "en": "Drag folder here or type path manually",
            "zh": "拖拽文件夹到此或手动输入路径",
        },
        "path_add_another": {
            "en": "Add another scan target?",
            "zh": "是否添加其他扫描目标？",
        },
        "path_yes": {
            "en": "Yes, add another",
            "zh": "是，继续添加",
        },
        "path_no": {
            "en": "No, proceed to finish",
            "zh": "否，完成设置",
        },
        "path_empty_warning": {
            "en": "Path cannot be empty",
            "zh": "路径不能为空",
        },
        "path_not_found_warning": {
            "en": "Path not found: {}",
            "zh": "路径不存在: {}",
        },
        "path_is_file_warning": {
            "en": "Path is a file. Single file scan supported.",
            "zh": "路径是文件。支持单文件扫描。",
        },
        "path_scan_target_added": {
            "en": "Scan target added:",
            "zh": "已添加扫描目标:",
        },
        # === Project Name ===
        "project_name_title": {
            "en": "Enter Project Name",
            "zh": "输入项目名称",
        },
        "project_name_explanation": {
            "en": "Used for config filename and reports",
            "zh": "用于配置文件命名和报告显示",
        },
        "project_name_example": {
            "en": "Example: MyProject, VaultSave",
            "zh": "示例: MyProject, VaultSave",
        },
        "project_name_empty_warning": {
            "en": "Project name cannot be empty",
            "zh": "项目名称不能为空",
        },
        "project_name_sanitized": {
            "en": "Name sanitized to: {}",
            "zh": "名称已过滤为: {}",
        },
        "footer_input_hint": {
            "en": "Type name | Enter Confirm | ESC Back",
            "zh": "输入名称 | Enter 确认 | ESC 返回",
        },
    }

    @classmethod
    def lang(cls) -> str:
        """Get current language."""
        return cls._lang

    @classmethod
    def toggle(cls) -> str:
        """Toggle language, return new lang code."""
        cls._lang = "zh" if cls._lang == "en" else "en"
        return cls._lang

    @classmethod
    def set_lang(cls, lang: str) -> None:
        """Set language explicitly."""
        if lang in LANG_MODES:
            cls._lang = lang

    @classmethod
    def get(cls, key: str) -> str:
        """Get message in current language."""
        entry = cls.MESSAGES.get(key)
        if not entry:
            return key
        return entry.get(cls._lang, entry.get("en", key))

    @classmethod
    def format(cls, key: str, *args: object) -> str:
        """Get message with format arguments."""
        template = cls.get(key)
        return template.format(*args) if args else template
