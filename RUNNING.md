# Running Guide

> [中文版](RUNNING_zh.md) | [Back to README](README.md)

## Recommended Launch Methods

### Windows

```powershell
# PowerShell
.\run.ps1

# Or local dev script
.\run_local.ps1
```

```cmd
# CMD
run.bat
```

### Manual Launch

```bash
# Clear VIRTUAL_ENV to avoid uv warning
$env:VIRTUAL_ENV=""  # PowerShell
set VIRTUAL_ENV=     # CMD

uv run python -m src.main
```

## Why Clear VIRTUAL_ENV?

When in another Python venv, `uv` detects mismatch and outputs warning. Launch scripts auto-clear this variable.

## First-Time Setup

1. Create `.env.local` with your LLM API key
2. Run `uv run python -m src.main`
3. Setup Wizard guides you to create `config/Project_Config.yaml`
4. Select paths, extensions, and exclude directories
5. Start translating!

## Main Menu

```
┌─ zh-context-scanner v1.0.2 ────────────────────────────┐
│ 🌏 Language: English | Mode: Comment Only              │
│                                                        │
│ 🔍 Full Scan                                           │
│ 📊 Incremental Scan                                    │
│ 📁 Manual Path Input                                   │
│ 💾 Backup History                                      │
│ 🔧 Preferences                                         │
│ 👋 Exit                                                │
│                                                        │
│ ↑↓ Navigate | Enter Select | Q Quit                    │
└────────────────────────────────────────────────────────┘
```

## Workflow

1. **Configure**: Preferences → Language, Translation Mode
2. **Scan**: Full/Incremental scan finds Chinese files
3. **Preview**: Select file → Git Diff preview (← → flip pages)
4. **Apply**: Confirm and apply translation
5. **Backup**: Auto-created in `.backup/`, restore via Backup History

## Troubleshooting

### VIRTUAL_ENV warning

Use launch scripts (`run.ps1`, `run.bat`) which auto-clear the variable.

### Translation failed

1. Check `.env.local` has valid `LLM_API_KEY`
2. Check network connection
3. Check `.log/zh-context-scanner.log` for errors

### Scan results 0

1. Verify scan paths in `config/Project_Config.yaml`
2. Check project actually contains Chinese
3. Try different translation mode

### Output truncated

Use `deepseek-reasoner` model (64K limit) or set `LLM_FORCE_MODEL=true`.

---

Last Updated: 2026-04-17