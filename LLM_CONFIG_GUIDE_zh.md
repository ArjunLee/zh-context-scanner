# LLM 配置指南

> [English](LLM_CONFIG_GUIDE.md) | [返回 README](README_zh.md)

## 快速配置

在项目根目录创建 `.env.local`：

```bash
# 必需
LLM_API_KEY=sk-your-api-key

# 可选（默认：DeepSeek）
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 可选：强制使用配置模型
LLM_FORCE_MODEL=false
```

## 支持的提供商

| 提供商 | Base URL | 默认模型 |
|--------|----------|----------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-5.3` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| MiniMax | `https://api.minimax.chat/v1/text/chatcompletion_v2` | `abab6.5s` |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `Pro/Qwen/Qwen2.5-72B-Instruct` |
| 本地 LM Studio | `http://localhost:8000/v1` | 你的模型 |

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `LLM_API_KEY` | 是 | API 密钥 |
| `LLM_BASE_URL` | 否 | API 端点 |
| `LLM_MODEL` | 否 | 模型名称 |
| `LLM_FORCE_MODEL` | 否 | 跳过自动绑定 (`true`/`false`) |

### 向后兼容变量

| 变量 | 状态 |
|------|------|
| `DEEPSEEK_API_KEY` | 已废弃 |
| `OPENAI_API_KEY` | 已废弃 |
| `i18n_auto_translate_k` | 已废弃 |

## 模型自动绑定

工具根据翻译模式自动选择模型（除非设置 `LLM_FORCE_MODEL=true`）：

| 模式 | 自动模型 | 输出限制 |
|------|----------|----------|
| 仅翻译注释 | `deepseek-chat` | 8K |
| 全内容翻译 | `deepseek-reasoner` | 64K |

强制覆盖：

```bash
LLM_MODEL=deepseek-chat
LLM_FORCE_MODEL=true
```

## 配置示例

### DeepSeek（推荐）

```bash
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### OpenAI

```bash
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

### 本地 LM Studio

```bash
LLM_API_KEY=local
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=local-model
```

## 安全提示

1. 永远不要提交 `.env.local` 到 git（已在 `.gitignore` 中）
2. 定期轮换 API 密钥
3. 生产环境使用环境变量

## 故障排查

**翻译失败**：检查 `LLM_API_KEY` 和网络连接。

**输出截断**：使用 `deepseek-reasoner`（64K 限制）或设置 `LLM_FORCE_MODEL=true`。

---

最后更新：2026-04-17