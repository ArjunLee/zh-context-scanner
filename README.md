# zh-context-scanner

> 🌏 [中文版](README_zh.md) | 📖 [Running Guide](RUNNING.md)

A CLI/TUI tool for detecting and translating Chinese text in source code, designed to help open-source projects standardize their codebase for international release.

**A tool from [VaultSave](https://github.com/ArjunLee/VaultSave)** - Not yet open source.

## Quick Navigation

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Multi-Project Support](#multi-project-support)
- [Translation Modes](#translation-modes)
- [CLI Arguments](#cli-arguments)
- [Preview & Review](#preview--review)
- [Best Practices](#best-practices)
- [FAQ](#faq)

## Features

### Core Features

- **Dual Translation Modes**
  - **Comment Only Mode** (Fast) - Translates only comments, leaves code strings unchanged
  - **Full Content Mode** (Slow) - Translates all Chinese text (logs, UI strings, literals)
  - One-click mode switch in main menu, synchronized throughout scan and translation

- **Smart Scanning**
  - Accurately counts Chinese lines based on selected translation mode
  - Supports comment detection for multiple languages: Rust/Python/TypeScript/JavaScript/Go/Java/C/C++
  - Incremental scanning based on file modification time
  - Automatic warning for complex scenarios (template strings, multiline comments, regex literals)

- **AI Translation Engine**
  - Whole-file translation (WholeFileTranslator)
  - Incremental comment translation (CommentTranslator)
  - File header term caching for consistency
  - Technical terminology preservation
  - DeepSeek API batch translation with intelligent caching

- **Professional TUI Interface**
  - Bilingual support (EN/ZH)
  - Translation mode switching
  - Paginated display (← → keys)
  - Git Diff style code preview
  - Change section pagination (6 sections per page, browse all with flip)
  - Auto-refresh after translation
  - Flicker-free design (Live refresh)

- **Backup System**
  - Timestamped backup directories
  - Backup history viewer (table display)
  - One-click restore
  - Cleanup strategy (keep recent N backups)
  - Backup record JSON indexing

- **Preview & Review**
  - Git Diff style comparison (Original | Translated side-by-side)
  - Change section pagination (← → to browse all sections)
  - Line count matching validation
  - Translation status visualization

### Technical Features

- **Chinese Detection**: Uses `regex` library with Unicode Han property support
- **Streaming Read**: Line-by-line processing for large files
- **Headless Mode**: JSON output for CI/CD integration

## Installation

```bash
cd tools/zh-context-scanner
uv sync
```

> 💡 **Tip**: Command examples below use Bash format (cross-platform compatible).
> - **Windows PowerShell**: Replace `:` with `=`, e.g., `--config=my_project.yaml`
> - **Windows CMD**: Same as Bash format

## Configuration

Create `.env.local` file with your LLM API key:

```bash
# Recommended: Universal API key (supports multiple LLM providers)
LLM_API_KEY=sk-your-api-key

# Optional: Custom Base URL and model
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat
```

> **Supported Providers**: DeepSeek, OpenAI, Azure OpenAI, Moonshot, MiniMax, etc.
> 
> **Detailed Guide**:
> - [LLM Configuration Guide (English)](LLM_CONFIG_GUIDE.md) - Full LLM configuration guide
> - [LLM 配置指南（中文）](LLM_CONFIG_GUIDE_zh.md) - 完整的 LLM 配置说明
> 
> **Example Config**: [.env.local.example](.env.local.example)

## Usage

### TUI Interactive Mode (Recommended)

```bash
uv run python -m src.main
```

> **Cross-Platform Tip**:
> - **Bash/Zsh** (Linux/macOS/WSL): `uv run python -m src.main`
> - **PowerShell**: `uv run python -m src.main`
> - **CMD**: `uv run python -m src.main`
> - Same command for all platforms, no adjustment needed

**Main Menu Functions**:
- 🔍 **Full Scan** - Scan all target files
- 📊 **Incremental Scan** - Scan based on modification time
- 📁 **Manual Path Input** - Scan specific file or directory
- 💾 **Backup History** - View and restore backups
- 🔧 **Preferences** - Language, Translation Mode
- 👋 **Exit**

**Translation Workflow**:
1. Select translation mode (Comment Only / Full Content)
2. Scan results show Chinese line count (filtered by mode)
3. Select file to preview (Git Diff style)
4. Browse all change sections (← → keys)
5. Confirm and apply translation
6. Results auto-refresh (show latest Chinese count)

### Headless Scan Mode

```bash
# Scan and output JSON report
uv run python -m src.main --scan --json > report.json

# Scan with custom root directory
uv run python -m src.main --scan --root /path/to/project

# Use custom configuration file (YAML format)
uv run python -m src.main --scan --config my_project.yaml
```

> **Path Format**:
> - **Linux/macOS**: `--root /home/user/project`
> - **Windows**: `--root E:/Dev/project` or `--root E:\Dev\project` (both supported)

### Replace Mode

```bash
# Execute replacements from report (non-interactive)
uv run python -m src.main --replace --input report.json --yes
```

### Restore Backup

```bash
# Restore from latest backup
uv run python -m src.main --restore latest

# Restore from specific backup
uv run python -m src.main --restore 2026-04-15_143022

# Restore single file
uv run python -m src.main --restore latest --restore-file src/main.rs
```

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--root` | Project root directory (auto-detected if not specified) |
| `--config` | JSON config file for custom scan targets |
| `--scan` | Run scan and output report |
| `--incremental` | Incremental scan based on file modification time |
| `--input` | Input report JSON file for `--replace` |
| `--replace` | Execute replacements from report |
| `--yes` | Skip all confirmations |
| `--restore` | Restore from backup (default: latest) |
| `--restore-file` | Restore single file |
| `--json` | Output JSON format |

## Translation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Comment Only** | Only translates comments, leaves code strings unchanged | Quick internationalization of comments |
| **Full Content** | Translates all Chinese (logs, UI text, strings) | Complete internationalization |

**Switch Mode**: Select item 5 (🔧 Preferences) -> Translation Mode in main menu

## Multi-Project Support

This tool supports multi-project configuration via YAML configuration files.

### Configuration File Format

Create `my_project.yaml`:

```yaml
# Project name (optional, used in logs)
project_name: "My Awesome Project"

# Scan target configuration
scan_targets:
  - path: "src"
    extensions:
      - ".ts"
      - ".tsx"
      - ".js"
      - ".jsx"
    exclude_subdirs:
      - "node_modules"
      - "dist"
      - "__tests__"
  
  - path: "backend"
    extensions:
      - ".py"
    exclude_subdirs:
      - "__pycache__"
      - ".venv"
  
  - path: "src-tauri/src"
    extensions:
      - ".rs"
    exclude_subdirs:
      - "target"
      - "gen"

# Global exclude directories (optional, defaults include common directories)
global_excludes:
  - "node_modules"
  - "dist"
  - ".git"
  - ".venv"
  - "__pycache__"
  - "target"
```

### Usage

```bash
# Use YAML configuration file
uv run python -m src.main --config my_project.yaml

# Combine with --scan argument
uv run python -m src.main --scan --config my_project.yaml
```

### Built-in Project Templates

The tool includes default configuration for VaultSave project, ready to use without configuration file:

```bash
# Use default configuration directly (VaultSave project)
uv run python -m src.main
```

> **Configuration Priority**:
> 1. Use `--config` to specify YAML configuration file → Use custom configuration
> 2. Don't use `--config` → Use built-in VaultSave default configuration

### Example Configuration File

The project includes an example configuration file [`example.config.yaml`](example.config.yaml) that can be copied and modified for use.

## Warning Types

The tool automatically detects and skips complex scenarios:

| Warning | Description |
|---------|-------------|
| `template_string` | Contains `${...}` interpolation |
| `multiline_string` | Multiline string literal (`"""`, `'''`) |
| `multiline_comment` | Multiline comment block (`/* */`) |
| `regex_literal` | Regex pattern literal |
| `escape_chars` | Contains backslash escapes |

## Backup Structure

```
.backup/
├── 2026-04-15_143022/     # Timestamped backup
│   ├── apps/desktop/.../main.rs
│   ├── scripts/pipeline/i18n.py
│   └── backup_record.json
├── 2026-04-15_150833/
└── latest/                # Latest backup copy
```

## Preview & Review

**Git Diff Style Preview**:
```
┌─ Whole-File Translation Preview ──────────────────────────┐
│ File: ...src/backup_services/auto_backup/executor.rs      │
│ Mode: Comment Only                                        │
│ Status: ✓ Lines match: 156                                │
│                                                           │
│ ┌─ Diff ─────────────────────────────────────────────────┐│
│ │ Line │   Original    │   Translated   │                ││
│ │──────│───────────────│────────────────│                ││
│ │  43  │ // 无法获取   │ // Unable to   │                ││
│ │      │ APPDATA 环境  │ get APPDATA    │                ││
│ │      │ 变量          │ env variable   │                ││
│ │ ...  │     ───       │     ───        │                ││
│ │ 112  │ // 存档目录   │ // Save data   │                ││
│ │      │ 不存在        │ directory does │                ││
│ │      │               │ not exist      │                ││
│ └────────────────────────────────────────────────────────┘│
│                                                           │
│ Total 12 lines changed, 4 sections | Section 1/4 (← →)    │
│ Press Enter to return to main menu                        │
└───────────────────────────────────────────────────────────┘
```

**Pagination**:
- ← key: Previous page
- → key: Next page
- 6 sections per page
- Auto-show page number (Section 1/4)

## Best Practices

### Recommended Workflow

1. **First-time use**: Choose Full Content mode for complete internationalization
2. **Daily maintenance**: Choose Comment Only mode for quick comment handling
3. **Review changes**: Use ← → keys to carefully browse all sections
4. **Backup & restore**: Immediately restore via backup history if issues occur

### Performance Optimization

- **Large file translation**: Auto-detects line count, warns if exceeds threshold
- **Batch translation**: Use incremental scan to translate only modified files
- **Terminology consistency**: Maintain `file_header_terms.yaml` for file header terms

## FAQ

### Q: Why are scan results related to translation mode?

A: In Comment Only mode, the scanner automatically filters out Chinese in code strings and only counts Chinese lines in comments. This lets you focus on comment internationalization.

### Q: How to view all change sections?

A: In the preview screen, use ← → keys to flip pages. Each page shows 6 sections, and the bottom displays the current page (e.g., "Section 1/4").

### Q: How to verify translation quality?

A: 
1. Carefully review each section in the preview
2. Run `cargo check` / `npm run typecheck` after applying
3. Use `git diff` to see full changes
4. Restore via backup history if issues occur

## Post-Replace Verification

After replacement, run these commands to verify:

```bash
cargo check              # Rust syntax check
npm run typecheck        # TypeScript type check
git diff                 # View changes
```

## License

MIT