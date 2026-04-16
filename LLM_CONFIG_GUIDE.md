# LLM Configuration Guide

> 🌏 [中文版](LLM_CONFIG_GUIDE_zh.md) | [Back to README](README.md)

## 🌐 Supported LLM Providers

zh-context-scanner uses the **OpenAI-compatible API** format and supports multiple LLM providers.

---

## ⚡ Quick Configuration

### Option 1: Universal Configuration (Recommended)

Suitable for all OpenAI-compatible services, **recommended**:

```bash
# .env.local
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### Option 2: DeepSeek Specific (Backward Compatible)

```bash
# .env.local
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
# Automatically uses DeepSeek default configuration
```

### Option 3: OpenAI Specific (Backward Compatible)

```bash
# .env.local
OPENAI_API_KEY=sk-your-openai-api-key
# Automatically uses OpenAI default configuration
```

---

## 🔧 Common Provider Configuration

### DeepSeek

```bash
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

**Get API Key**: https://platform.deepseek.com/

### OpenAI

```bash
LLM_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

**Get API Key**: https://platform.openai.com/

### Azure OpenAI

```bash
LLM_API_KEY=your-azure-api-key
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-15-preview
LLM_MODEL=gpt-4o
```

**Configuration Guide**: https://learn.microsoft.com/azure/ai-services/openai/

### Moonshot (Kimi)

```bash
LLM_API_KEY=sk-your-moonshot-api-key
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_MODEL=moonshot-v1-8k
```

**Get API Key**: https://platform.moonshot.cn/

### MiniMax

```bash
LLM_API_KEY=sk-your-minimax-api-key
LLM_BASE_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
LLM_MODEL=abab6.5s
```

**Get API Key**: https://platform.minimaxi.com/

### SiliconFlow

```bash
LLM_API_KEY=sk-your-siliconflow-api-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Pro/Qwen/Qwen2.5-72B-Instruct
```

**Get API Key**: https://cloud.siliconflow.cn/

---

## 📋 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | API Key (universal, recommended) | `sk-xxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BASE_URL` | API endpoint URL | `https://api.deepseek.com` |
| `LLM_MODEL` | Model name | `deepseek-chat` |
| `LLM_FORCE_MODEL` | Force use configured model (skip auto-binding) | `false` |

### Backward Compatible Variables

| Variable | Description | Status |
|----------|-------------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek specific key | ⚠️ Backward compatible |
| `OPENAI_API_KEY` | OpenAI specific key | ⚠️ Backward compatible |
| `i18n_auto_translate_k` | Legacy universal key | ⚠️ Backward compatible |

---

## 🎯 Model Auto-Binding

The tool automatically selects the optimal model based on translation mode (unless `LLM_FORCE_MODEL=true`):

| Translation Mode | Auto-Bound Model | Description |
|------------------|------------------|-------------|
| Comment Only (COMMENT_ONLY) | `deepseek-chat` | Fast, low cost, 8K output limit |
| Full Content (FULL) | `deepseek-reasoner` | 64K output limit, suitable for large files |

**Force Override**: Set `LLM_FORCE_MODEL=true` to force using the model specified in `LLM_MODEL`.

```bash
# Example: Force use deepseek-chat for full content translation
LLM_MODEL=deepseek-chat
LLM_FORCE_MODEL=true
```

---

## 🎯 Priority Rules

Configuration loading priority (high to low):

1. **LLM_API_KEY** + Custom URL/Model
2. **DEEPSEEK_API_KEY** (Auto-configure DeepSeek)
3. **OPENAI_API_KEY** (Auto-configure OpenAI)
4. **i18n_auto_translate_k** (Use default DeepSeek)

---

## 🧪 Test Configuration

Run the following command to test if the configuration is correct:

```bash
# Launch TUI
uv run python -m src.main

# Or use custom configuration
uv run python -m src.main --config my_project.yaml
```

---

## 🔒 Security Recommendations

1. **Never commit `.env.local` to Git**
   - Project has `.gitignore` configured to automatically ignore

2. **Use environment variables (production)**
   ```bash
   export LLM_API_KEY=sk-xxx
   uv run python -m src.main
   ```

3. **Rotate API Keys regularly**
   - Avoid long-term use of the same key

4. **Limit API Key permissions**
   - Grant only necessary permissions

---

## ❓ FAQ

### Q: Which configuration method should I use?

**A**: Recommend using **`LLM_API_KEY`** universal configuration because:
- Unified interface, easy to switch providers
- Professional standard,符合 industry standards
- Supports custom URL and model

### Q: How to switch between different LLM providers?

**A**: Modify configuration in `.env.local`:

```bash
# Switch to OpenAI
LLM_API_KEY=sk-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

### Q: Does it support locally deployed models?

**A**: Yes! Just provide an OpenAI-compatible API endpoint:

```bash
LLM_API_KEY=local-key  # or leave empty
LLM_BASE_URL=http://localhost:8000/v1  # Local LM Studio / vLLM
LLM_MODEL=local-model
```

### Q: How to verify the configuration is working?

**A**: After launching the tool, the translation process will display the API endpoint and model information being used.

---

## 📚 Related Documents

- [README.md](README.md) - Complete usage documentation
- [RUNNING.md](RUNNING.md) - Running guide
- [example.config.yaml](example.config.yaml) - Configuration example

---

**Last Updated**: 2026-04-15  
**Version**: v1.0.2

