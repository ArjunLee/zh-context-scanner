# 启动方式

> 🌏 [English Version](RUNNING.md) | [返回 README](README_zh.md)

## 推荐启动方式（无 warning）

### Windows CMD
```cmd
run.bat
```

### PowerShell
```powershell
.\run.ps1
```

### 手动启动（清除环境变量）
```powershell
# PowerShell
$env:VIRTUAL_ENV=""
uv run python -m src.main

# CMD
set VIRTUAL_ENV=
uv run python -m src.main
```

## 为什么需要清除 VIRTUAL_ENV？

当你在其他 Python 虚拟环境中（如 `your-project-backend`）时，系统会设置 `VIRTUAL_ENV` 环境变量。
`uv` 检测到这个变量与当前项目的 `.venv` 不匹配，会输出 warning。

启动脚本会自动清除这个变量，确保使用工具自己的虚拟环境。

## 主菜单示例

```
┌─ 中文上下文扫描器 v1.0.2 ─────────────────────────────────────┐
│                                                            │
│  项目根目录：/home/user/your-project                       │
│  语言：中文                                                │
│  翻译模式：仅翻译注释 (快速)                               │
│                                                            │
│  请选择操作                                                │
│  🔍 全仓库扫描                                             │
│  📊 增量扫描                                               │
│  📁 手动输入路径                                           │
│  💾 查看历史备份                                           │
│  🔧 偏好设置                                               │
│  👋 退出                                                   │
│                                                            │
│  输入序号 (1-6):                                           │
└────────────────────────────────────────────────────────────┘
```

## LLM 配置

在 `.env.local` 文件中配置：

```bash
# 必需：API 密钥
LLM_API_KEY=sk-your-api-key

# 可选：自定义 Base URL（默认 DeepSeek）
# LLM_BASE_URL=https://api.deepseek.com

# 可选：自定义模型（默认 deepseek-chat）
# LLM_MODEL=deepseek-chat

# 可选：强制使用配置模型（跳过自动绑定）
# LLM_FORCE_MODEL=false
```

### 模型自动绑定说明

工具会根据翻译模式自动选择最优模型（除非设置 `LLM_FORCE_MODEL=true`）：

| 翻译模式 | 自动绑定模型 | 说明 |
|----------|-------------|------|
| 仅翻译注释 | `deepseek-chat` | 快速、低成本、8K 输出限制 |
| 全内容翻译 | `deepseek-reasoner` | 64K 输出限制，适合大文件 |

设置 `LLM_FORCE_MODEL=true` 可强制使用 `LLM_MODEL` 配置的模型。

> 详细配置指南：[LLM 配置指南（中文）](LLM_CONFIG_GUIDE_zh.md)

## 故障排查

### 问题：启动时显示 VIRTUAL_ENV warning

**解决**：使用启动脚本（`run.bat` 或 `.\run.ps1`），会自动清除环境变量。

### 问题：翻译失败

**解决**：
1. 检查 `.env.local` 是否配置了有效的 `LLM_API_KEY`
2. 检查网络连接
3. 查看日志文件了解详细错误

### 问题：扫描结果为 0

**解决**：
1. 检查扫描目标路径是否正确
2. 确认项目中确实包含中文
3. 尝试切换翻译模式（某些模式下代码字符串中的中文不会被统计）

### 问题：翻译结果截断

**解决**：
1. 使用 `deepseek-reasoner` 模型（64K 输出限制）
2. 或设置 `LLM_FORCE_MODEL=true` 并配置大输出模型

---

**最后更新**: 2026-04-16