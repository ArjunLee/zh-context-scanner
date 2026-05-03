# 运行指南

> [English](RUNNING.md) | [返回 README](README_zh.md)

## 推荐启动方式

### Windows

```powershell
# PowerShell
.\run.ps1

# 或本地开发脚本
.\run_local.ps1
```

```cmd
# CMD
run.bat
```

### 手动启动

```bash
# 清除 VIRTUAL_ENV 避免 uv 警告
$env:VIRTUAL_ENV=""  # PowerShell
set VIRTUAL_ENV=     # CMD

uv run python -m src.main
```

## 为什么清除 VIRTUAL_ENV？

在其他 Python 虚拟环境中时，`uv` 检测到不匹配会输出警告。启动脚本自动清除该变量。

## 首次使用流程

1. 创建 `.env.local` 配置 LLM API 密钥
2. 运行 `uv run python -m src.main`
3. Setup Wizard 引导你创建 `config/Project_Config.yaml`
4. 选择扫描路径、扩展名、排除目录
5. 开始翻译！

## 主菜单

```
┌─ 中文上下文扫描器 v1.0.2 ────────────────────────────────┐
│ 🌏 语言：中文 | 模式：仅翻译注释                         │
│                                                        │
│ 🔍 全仓库扫描                                           │
│ 📊 增量扫描                                             │
│ 📁 手动输入路径                                         │
│ 💾 查看历史备份                                         │
│ 🔧 偏好设置                                             │
│ 👋 退出                                                 │
│                                                        │
│ ↑↓ 导航 | Enter 选择 | Q 退出                           │
└────────────────────────────────────────────────────────┘
```

## 工作流程

1. **配置**：偏好设置 → 语言、翻译模式
2. **扫描**：全量/增量扫描发现中文文件
3. **预览**：选择文件 → Git Diff 预览（← → 翻页）
4. **应用**：确认并应用翻译
5. **备份**：自动创建于 `.backup/`，通过备份历史恢复

## 故障排查

### VIRTUAL_ENV 警告

使用启动脚本（`run.ps1`、`run.bat`）会自动清除变量。

### 翻译失败

1. 检查 `.env.local` 是否有有效的 `LLM_API_KEY`
2. 检查网络连接
3. 查看 `.log/zh-context-scanner.log` 错误详情

### 扫描结果为 0

1. 检查 `config/Project_Config.yaml` 中扫描路径是否正确
2. 确认项目确实包含中文
3. 尝试切换翻译模式

### 输出截断

使用 `deepseek-v4-pro` 模型（64K 限制）或设置 `LLM_FORCE_MODEL=true`。

---

最后更新：2026-04-17