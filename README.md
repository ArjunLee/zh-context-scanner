# zh-context-scanner

> [中文版](README_zh.md) | [Running Guide](RUNNING.md) | [LLM Config](LLM_CONFIG_GUIDE.md)

CLI/TUI tool for detecting and translating Chinese text in source code to English.

**Part of [VaultSave](https://github.com/ArjunLee/VaultSave)** (Not yet open source.)

## Features

- **Dual Translation Modes**: Comment-only (fast) or full-content (complete)
- **Smart Scanning**: Mode-aware counting, supports Rust/Python/TypeScript/Go/Java/C/C++
- **AI Translation**: DeepSeek/OpenAI API with batch processing and caching
- **Professional TUI**: Bilingual (EN/ZH), Git Diff preview, paginated navigation
- **Backup System**: Timestamped backups with one-click restore
- **Setup Wizard**: Interactive project configuration on first run

## Installation

```bash
cd tools/zh-context-scanner
uv sync
```

## Quick Start

### 1. Configure LLM API

Create `.env.local`:

```bash
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

> See [LLM_CONFIG_GUIDE.md](LLM_CONFIG_GUIDE.md) for all supported providers.

### 2. Run Setup Wizard (First Time)

```bash
uv run python -m src.main
```

The setup wizard will guide you to create `config/Project_Config.yaml`.

### 3. Translate Files

1. Select translation mode in Preferences (Comment Only / Full)
2. Run Full Scan or Incremental Scan
3. Select file → Preview (Git Diff style) → Apply translation

## Configuration

### Project Config (Flat YAML Structure)

`config/Project_Config.yaml`:

```yaml
project_name: MyProject

paths:
  - "src/frontend"
  - "src/backend"

extensions:
  - ".rs"
  - ".tsx"
  - ".ts"
  - ".py"

exclude_subdirs:
  - "target"
  - "node_modules"
  - "__pycache__"

global_excludes:
  - ".git"
```

**Key**: All paths share the same extensions and exclude_subdirs (flat arrays, not nested per-path).

### Git Ignore Strategy

- `config/example.Project_Config.yaml` - Template (tracked in git)
- `config/Project_Config.yaml` - Your config (ignored in git)

If `Project_Config.yaml` missing, it's auto-copied from `example.Project_Config.yaml`.

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--root` | Project root (auto-detected) |
| `--config` | Custom YAML config file |
| `--setup` | Force run setup wizard |
| `--scan` | Headless scan mode |
| `--json` | JSON output |
| `--restore` | Restore from backup |

## Translation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Comment Only | Translate only comments | Quick internationalization |
| Full Content | Translate all Chinese | Complete cleanup |

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
- 6 sections per page, auto-show page number

## Directory Structure

```
tools/zh-context-scanner/
├── src/                    # Core source code
│   ├── ui/                 # TUI components
│   ├── solid_logger/       # Logging system
│   ├── config.py           # Configuration management
│   ├── scanner.py          # Chinese detection
│   ├── whole_file_translator.py  # AI translation
│   └── main.py             # Entry point
├── config/
│   ├── example.Project_Config.yaml  # Template (tracked)
│   └── Project_Config.yaml          # User config (ignored)
├── .backup/                # Translation backups
├── .log/                   # Log files
├── .env.local              # LLM API credentials
└── pyproject.toml          # Project metadata
```

## Running Directory

| Scenario | Run From |
|----------|----------|
| VaultSave project | `VaultSave/` or `VaultSave/tools/zh-context-scanner/` |
| Other projects | Your project root or use `--root` |

```bash
# From project root
uv run python -m src.main

# Specify root explicitly
uv run python -m src.main --root /path/to/project
```

## Backup & Restore

```bash
# Restore latest backup
uv run python -m src.main --restore latest

# Restore specific backup
uv run python -m src.main --restore 2026-04-15_143022

# Restore single file
uv run python -m src.main --restore latest --restore-file src/main.rs
```

## Post-Translation Verification

```bash
cargo check              # Rust syntax
npm run typecheck        # TypeScript types
git diff                 # View changes
```

## License

MIT