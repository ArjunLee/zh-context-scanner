# LLM 配置指南

> 🌏 [English Version](LLM_CONFIG_GUIDE.md) | [返回 README](README_zh.md)

## 🌐 支持的 LLM 提供商

zh-context-scanner 使用 **OpenAI 兼容 API** 格式，支持多种 LLM 提供商。

---

## ⚡ 快速配置

### 方案 1：通用配置（推荐）

适用于所有 OpenAI 兼容服务，**推荐使用**：

```bash
# .env.local
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 方案 2：DeepSeek 专用（向后兼容）

```bash
# .env.local
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
# 自动使用 DeepSeek 默认配置
```

### 方案 3：OpenAI 专用（向后兼容）

```bash
# .env.local
OPENAI_API_KEY=sk-your-openai-api-key
# 自动使用 OpenAI 默认配置
```

---

## 🔧 常用提供商配置

### DeepSeek

```bash
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

**获取 API Key**: https://platform.deepseek.com/

### OpenAI

```bash
LLM_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

**获取 API Key**: https://platform.openai.com/

### Azure OpenAI

```bash
LLM_API_KEY=your-azure-api-key
LLM_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-15-preview
LLM_MODEL=gpt-4o
```

**配置说明**: https://learn.microsoft.com/azure/ai-services/openai/

### Moonshot (Kimi)

```bash
LLM_API_KEY=sk-your-moonshot-api-key
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_MODEL=moonshot-v1-8k
```

**获取 API Key**: https://platform.moonshot.cn/

### MiniMax

```bash
LLM_API_KEY=sk-your-minimax-api-key
LLM_BASE_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
LLM_MODEL=abab6.5s
```

**获取 API Key**: https://platform.minimaxi.com/

### SiliconFlow

```bash
LLM_API_KEY=sk-your-siliconflow-api-key
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Pro/Qwen/Qwen2.5-72B-Instruct
```

**获取 API Key**: https://cloud.siliconflow.cn/

---

## 📋 环境变量说明

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `LLM_API_KEY` | API 密钥（通用，推荐） | `sk-xxx` |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_BASE_URL` | API 端点 URL | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `LLM_FORCE_MODEL` | 强制使用配置模型（跳过自动绑定） | `false` |

### 向后兼容的变量

| 变量名 | 说明 | 状态 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek 专用密钥 | ⚠️ 向后兼容 |
| `OPENAI_API_KEY` | OpenAI 专用密钥 | ⚠️ 向后兼容 |
| `i18n_auto_translate_k` | 旧版通用密钥 | ⚠️ 向后兼容 |

---

## 🎯 模型自动绑定

工具会根据翻译模式自动选择最优模型（除非设置 `LLM_FORCE_MODEL=true`）：

| 翻译模式 | 自动绑定模型 | 说明 |
|----------|-------------|------|
| 仅翻译注释 (COMMENT_ONLY) | `deepseek-chat` | 快速、低成本、8K 输出限制 |
| 全内容翻译 (FULL) | `deepseek-reasoner` | 64K 输出限制，适合大文件 |

**强制覆盖**：设置 `LLM_FORCE_MODEL=true` 可强制使用 `LLM_MODEL` 配置的模型。

```bash
# 示例：强制使用 deepseek-chat 进行全量翻译
LLM_MODEL=deepseek-chat
LLM_FORCE_MODEL=true
```

---

## 🎯 优先级规则

配置加载优先级（从高到低）：

1. **LLM_API_KEY** + 自定义 URL/Model
2. **DEEPSEEK_API_KEY**（自动配置 DeepSeek）
3. **OPENAI_API_KEY**（自动配置 OpenAI）
4. **i18n_auto_translate_k**（使用默认 DeepSeek）

---

## 🧪 测试配置

运行以下命令测试配置是否正确：

```bash
# 启动 TUI
uv run python -m src.main

# 或使用自定义配置
uv run python -m src.main --config my_project.yaml
```

---

## 🔒 安全建议

1. **永远不要提交 `.env.local` 到 Git**
   - 项目已配置 `.gitignore` 自动忽略

2. **使用环境变量（生产环境）**
   ```bash
   export LLM_API_KEY=sk-xxx
   uv run python -m src.main
   ```

3. **定期轮换 API Key**
   - 避免长期使用同一密钥

4. **限制 API Key 权限**
   - 只授予必要的权限

---

## ❓ 常见问题

### Q: 我应该使用哪个配置方式？

**A**: 推荐使用 **`LLM_API_KEY`** 通用配置，原因：
- 统一接口，易于切换提供商
- 专业规范，符合行业标准
- 支持自定义 URL 和模型

### Q: 如何切换不同的 LLM 提供商？

**A**: 修改 `.env.local` 中的配置：

```bash
# 切换到 OpenAI
LLM_API_KEY=sk-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

### Q: 支持本地部署的模型吗？

**A**: 支持！只要提供 OpenAI 兼容的 API 端点即可：

```bash
LLM_API_KEY=local-key  # 或留空
LLM_BASE_URL=http://localhost:8000/v1  # Local LM Studio / vLLM
LLM_MODEL=local-model
```

### Q: 如何验证配置是否生效？

**A**: 启动工具后，在翻译过程中会显示使用的 API 端点和模型信息。

---

## 📚 相关文档

- [README_zh.md](README_zh.md) - 完整使用文档
- [RUNNING.md](RUNNING.md) - 运行指南
- [example.config.yaml](example.config.yaml) - 配置示例

---

**最后更新**: 2026-04-15  
**版本**: v2.0

