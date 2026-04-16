# Running Guide

> 🌏 [中文版](RUNNING_zh.md) | [Back to README](README.md)

## Recommended Launch Methods (No Warning)

### Windows CMD
```cmd
run.bat
```

### PowerShell
```powershell
.\run.ps1
```

### Manual Launch (Clear Environment Variable)
```powershell
# PowerShell
$env:VIRTUAL_ENV=""
uv run python -m src.main

# CMD
set VIRTUAL_ENV=
uv run python -m src.main
```

## Why Clear VIRTUAL_ENV?

When you're in another Python virtual environment (e.g., `your-project-backend`), the system sets the `VIRTUAL_ENV` environment variable.
`uv` detects this variable doesn't match the current project's `.venv` and outputs a warning.

The launch scripts automatically clear this variable to ensure the tool uses its own virtual environment.

## Main Menu Example

```
┌─ zh-context-scanner v1.0.2 ──────────────────────────────────┐
│                                                           │
│  Project root: /home/user/your-project                    │
│  Language: English                                        │
│  Translation mode: Comment Only (Fast)                    │
│                                                           │
│  Select action                                            │
│  🔍 Full Scan                                             │
│  📊 Incremental Scan                                      │
│  📁 Manual Path Input                                     │
│  💾 Backup History                                        │
│  🔧 Preferences                                           │
│  👋 Exit                                                  │
│                                                           │
│  Enter number (1-6):                                      │
└───────────────────────────────────────────────────────────┘
```

## LLM Configuration

Configure in `.env.local` file:

```bash
# Required: API Key
LLM_API_KEY=sk-your-api-key

# Optional: Custom Base URL (default: DeepSeek)
# LLM_BASE_URL=https://api.deepseek.com

# Optional: Custom model (default: deepseek-chat)
# LLM_MODEL=deepseek-chat

# Optional: Force use configured model (skip auto-binding)
# LLM_FORCE_MODEL=false
```

### Model Auto-Binding

The tool automatically selects the optimal model based on translation mode (unless `LLM_FORCE_MODEL=true`):

| Translation Mode | Auto-Bound Model | Description |
|------------------|------------------|-------------|
| Comment Only | `deepseek-chat` | Fast, low cost, 8K output limit |
| Full Content | `deepseek-reasoner` | 64K output limit, suitable for large files |

Set `LLM_FORCE_MODEL=true` to force using the model specified in `LLM_MODEL`.

> Detailed configuration guide: [LLM Configuration Guide](LLM_CONFIG_GUIDE.md)

## Troubleshooting

### Issue: VIRTUAL_ENV warning on startup

**Solution**: Use launch scripts (`run.bat` or `.\run.ps1`), they automatically clear the environment variable.

### Issue: Translation failed

**Solution**:
1. Check if `.env.local` has a valid `LLM_API_KEY`
2. Check network connection
3. View log files for detailed errors

### Issue: Scan results are 0

**Solution**:
1. Check if scan target path is correct
2. Confirm the project actually contains Chinese text
3. Try switching translation mode (some modes don't count Chinese in code strings)

### Issue: Translation output truncated

**Solution**:
1. Use `deepseek-reasoner` model (64K output limit)
2. Or set `LLM_FORCE_MODEL=true` and configure a model with larger output capacity

---

**Last Updated**: 2026-04-16