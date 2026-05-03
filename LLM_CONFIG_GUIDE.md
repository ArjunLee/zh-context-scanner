# LLM Configuration Guide

> [中文版](LLM_CONFIG_GUIDE_zh.md) | [Back to README](README.md)

## Quick Setup

Create `.env.local` in project root:

```bash
# Required
LLM_API_KEY=sk-your-api-key

# Optional (default: DeepSeek)
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash

# Optional: Force use configured model
LLM_FORCE_MODEL=false
```

## Supported Providers

| Provider | Base URL | Default Model |
|----------|----------|---------------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-v4-flash` |
| OpenAI | `https://api.openai.com/v1` | `gpt-5.3` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| MiniMax | `https://api.minimax.chat/v1/text/chatcompletion_v2` | `abab6.5s` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `Pro/Qwen/Qwen2.5-72B-Instruct` |
| Local (LM Studio) | `http://localhost:8000/v1` | Your model |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | API key |
| `LLM_BASE_URL` | No | API endpoint |
| `LLM_MODEL` | No | Model name |
| `LLM_FORCE_MODEL` | No | Skip auto-binding (`true`/`false`) |

### Backward Compatible Variables

| Variable | Status |
|----------|--------|
| `DEEPSEEK_API_KEY` | Deprecated |
| `OPENAI_API_KEY` | Deprecated |
| `i18n_auto_translate_k` | Deprecated |

## Model Auto-Binding

Tool auto-selects model based on translation mode (unless `LLM_FORCE_MODEL=true`):

| Mode | Auto Model | Output Limit |
|------|------------|---------------|
| Comment Only | `deepseek-v4-flash` | 8K |
| Full Content | `deepseek-v4-pro` | 64K |

Force override:

```bash
LLM_MODEL=deepseek-v4-flash
LLM_FORCE_MODEL=true
```

## Configuration Examples

### DeepSeek (Recommended)

```bash
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

### OpenAI

```bash
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

### Local LM Studio

```bash
LLM_API_KEY=local
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=local-model
```

## Security Notes

1. Never commit `.env.local` to git (already in `.gitignore`)
2. Rotate API keys regularly
3. Use environment variables in production

## Troubleshooting

**Translation failed**: Check `LLM_API_KEY` and network connection.

**Output truncated**: Use `deepseek-v4-pro` (64K limit) or set `LLM_FORCE_MODEL=true`.

---

Last Updated: 2026-04-17