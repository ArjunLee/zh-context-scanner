# zh-context-scanner

> 🌏 [English Version](README.md) | 📖 [运行指南](RUNNING_zh.md)

CLI/TUI 工具，用于检测和翻译源码中的中文内容，帮助开源项目实现国际化规范化。

**来自 [VaultSave](https://github.com/ArjunLee/VaultSave)** - 暂未开源。

## 快速导航

- [功能特性](#功能特性)
- [安装](#安装)
- [配置](#配置)
- [使用方式](#使用方式)
- [多项目支持](#多项目支持)
- [翻译模式](#翻译模式)
- [命令行参数](#命令行参数)
- [预览与审查](#预览与审查)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 功能特性

### 核心功能

- **双模式翻译** 
  - **仅翻译注释模式**（快速）- 只翻译注释中的中文，不改动代码字符串
  - **全内容翻译模式**（慢速）- 翻译所有中文（包括日志、UI 文本、字符串字面量）
  - 主菜单一键切换，扫描和翻译全流程同步

- **智能扫描** 
  - 根据选择的翻译模式精准统计中文行数
  - 支持多种语言的注释识别：Rust/Python/TypeScript/JavaScript/Go/Java/C/C++
  - 增量扫描（基于文件修改时间）
  - 复杂场景自动警告（模板字符串、多行注释、正则字面量等）

- **AI 翻译引擎** 
  - 整文件翻译（WholeFileTranslator）- 完整文件翻译
  - 增量注释翻译（CommentTranslator）- 仅翻译注释
  - 文件头部术语缓存优化 - 统一术语翻译
  - 技术术语库保持 - 专业术语自动保留
  - DeepSeek API 批量翻译 + 智能缓存

- **专业级 TUI 界面** 
  - 中英文双语切换
  - 翻译模式切换
  - 分页显示（← → 翻页）
  - Git Diff 风格代码预览
  - 变更段分页浏览（每页 6 段，支持翻页查看所有变更）
  - 翻译后结果自动刷新
  - 无闪屏设计（Live 刷新）

- **备份系统**
  - 时间戳备份目录
  - 备份历史查看（表格展示）
  - 一键恢复
  - 清理策略（保留最近 N 个备份）
  - 备份记录 JSON 索引

- **预览与审查**
  - Git Diff 风格差异对比（原文 | 译文对照）
  - 变更段分页浏览（← → 翻页查看所有变更段）
  - 行数匹配验证（自动检测行数差异）
  - 翻译状态可视化

### 技术特性

- **中文检测**：使用 `regex` 库 + Unicode Han 属性，支持基本区汉字和扩展区
- **流式读取**：逐行处理，支持大文件
- **Headless 模式**：JSON 输出，支持 CI/CD 集成

## 安装

```bash
cd tools/zh-context-scanner
uv sync
```

> **提示**：以下命令示例使用 Bash 格式（跨平台通用）。
> - **Windows PowerShell**：将 `:` 替换为 `=`，如 `--config=my_config.json`
> - **Windows CMD**：命令格式与 Bash 相同

## 配置

创建 `.env.local` 文件，配置 LLM API 密钥：

```bash
# 推荐使用通用配置（支持多种 LLM 提供商）
LLM_API_KEY=sk-your-api-key

# 可选：自定义 Base URL 和模型
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat
```

> **支持的提供商**：DeepSeek、OpenAI、Azure OpenAI、Moonshot、MiniMax 等
> 
> **详细配置指南**：
> - [LLM 配置指南（中文）](LLM_CONFIG_GUIDE_zh.md) - 完整的 LLM 配置说明
> - [LLM Configuration Guide (English)](LLM_CONFIG_GUIDE.md) - Full LLM configuration guide
> 
> **配置示例**：[.env.local.example](.env.local.example)

## 使用方式

### TUI 交互模式（推荐）

```bash
uv run python -m src.main
```

> **跨平台提示**：
> - **Bash/Zsh**（Linux/macOS/WSL）：`uv run python -m src.main`
> - **PowerShell**：`uv run python -m src.main`
> - **CMD**：`uv run python -m src.main`
> - 所有平台命令相同，无需调整

**主菜单功能**：
- 🔍 **全仓库扫描** - 扫描所有目标文件
- 📊 **增量扫描** - 基于修改时间的增量扫描
- 📁 **手动输入路径** - 扫描指定文件或目录
- 💾 **查看历史备份** - 查看并恢复备份
- 🔧 **偏好设置** - 语言切换、翻译模式
- 👋 **退出**

**翻译流程**：
1. 选择翻译模式（仅注释 / 全内容）
2. 扫描结果显示中文行数（按模式过滤）
3. 选择文件预览（Git Diff 风格）
4. 翻页查看所有变更段（← → 键）
5. 确认翻译并应用
6. 结果自动刷新（显示最新中文行数）

### Headless 扫描模式

```bash
# 扫描并输出 JSON 报告
uv run python -m src.main --scan --json > report.json

# 指定自定义根目录
uv run python -m src.main --scan --root /path/to/project

# 使用自定义配置文件（YAML 格式）
uv run python -m src.main --scan --config my_project.yaml
```

> **路径格式**：
> - **Linux/macOS**：`--root /home/user/project`
> - **Windows**：`--root E:/Dev/project` 或 `--root E:\Dev\project`（两种格式都支持）

### 替换模式

```bash
# 从报告执行替换（非交互）
uv run python -m src.main --replace --input report.json --yes
```

### 恢复备份

```bash
# 恢复最新备份
uv run python -m src.main --restore latest

# 恢复指定备份
uv run python -m src.main --restore 2026-04-15_143022

# 恢复单个文件
uv run python -m src.main --restore latest --restore-file src/main.rs
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--root` | 项目根目录（未指定则自动检测） |
| `--config` | 自定义扫描目标 JSON 配置文件 |
| `--scan` | 运行扫描并输出报告 |
| `--incremental` | 增量扫描（基于文件修改时间） |
| `--input` | `--replace` 模式的输入报告 JSON |
| `--replace` | 从报告执行替换 |
| `--yes` | 跳过所有确认 |
| `--restore` | 恢复备份（默认：latest） |
| `--restore-file` | 恢复单个文件 |
| `--json` | 输出 JSON 格式 |

## 翻译模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| **仅翻译注释** | 只翻译注释中的中文，不改动代码字符串 | 快速国际化注释说明 |
| **全内容翻译** | 翻译所有中文（包括日志、UI 文本、字符串） | 完整国际化，去除所有中文 |

**切换方式**：主菜单选择第 5 项 🔧 偏好设置 -> 翻译模式

## VaultSave 项目扫描目标

| 路径 | 扩展名 | 排除目录 |
|------|--------|----------|
| `apps/desktop/ui` | `.tsx, .ts, .css` | `locales, DebugPage, dist, node_modules` |
| `apps/desktop/src-tauri/src` | `.rs` | `target, gen` |
| `scripts/pipeline` | `.py` | `__pycache__` |
| `ci_pipeline.py` | `.py` | - |
| `shared` | `.toml` | - |
| `sync_app_meta.py` | `.py` | - |

## 多项目支持

本工具支持多项目配置，通过 YAML 配置文件适配不同项目。

### 配置文件格式

创建 `my_project.yaml`：

```yaml
# 项目名称（可选，用于日志显示）
project_name: "My Awesome Project"

# 扫描目标配置
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

# 全局排除目录（可选，默认值已包含常见目录）
global_excludes:
  - "node_modules"
  - "dist"
  - ".git"
  - ".venv"
  - "__pycache__"
  - "target"
```

### 使用方式

```bash
# 使用 YAML 配置文件
uv run python -m src.main --config my_project.yaml

# 结合 --scan 参数
uv run python -m src.main --scan --config my_project.yaml
```

### 内置项目模板

工具内置了 VaultSave 项目的默认配置，无需配置文件即可使用：

```bash
# 直接使用默认配置（VaultSave 项目）
uv run python -m src.main
```

> **配置文件优先级**：
> 1. 使用 `--config` 指定 YAML 配置文件 → 使用自定义配置
> 2. 不使用 `--config` → 使用内置的 VaultSave 默认配置

### 示例配置文件

项目包含示例配置文件 [`example.config.yaml`](example.config.yaml)，可直接复制修改使用。

## 警告类型

工具自动检测并跳过复杂场景：

| 警告 | 说明 |
|------|------|
| `template_string` | 包含 `${...}` 模板字符串 |
| `multiline_string` | 多行字符串字面量（`"""`、`'''`） |
| `multiline_comment` | 多行注释块（`/* */`） |
| `regex_literal` | 正则表达式字面量 |
| `escape_chars` | 包含反斜杠转义字符 |

## 备份目录结构

```
.backup/
├── 2026-04-15_143022/     # 时间戳备份
│   ├── apps/desktop/.../main.rs
│   ├── scripts/pipeline/i18n.py
│   └── backup_record.json
├── 2026-04-15_150833/
└── latest/                # 最新备份副本
```

## 预览与审查

**Git Diff 风格预览**：
```
┌─ 整体文件翻译预览 ────────────────────────────────────────┐
│ 文件：...src/backup_services/auto_backup/executor.rs　　  │
│ 模式：Comment Only                                        │
│ 状态：✓ 行数匹配：156                                     │
│                                                           │
│ ┌─ 差异对比 ────────────────────────────────────────────┐ │
│ │ 行号 │     原文      │     译文      │                │ │
│ │──────│───────────────│───────────────│                │ │
│ │  43  │ // 无法获取   │ // Unable to  │                │ │
│ │      │ APPDATA 环境  │ get APPDATA   │                │ │
│ │      │ 变量          │ env variable  │                │ │
│ │ ...  │     ───       │     ───       │                │ │
│ │ 112  │ // 存档目录   │ // Save data  │                │ │
│ │      │ 不存在        │ directory does│                │ │
│ │      │               │ not exist     │                │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                           │
│ 共 12 行变更，4 个变更段 | 变更段 1/4 (← → 翻页)          │
│ 按 Enter 返回主菜单                                       │
└───────────────────────────────────────────────────────────┘
```

**翻页功能**：
- ← 键：上一页
- → 键：下一页
- 每页显示 6 个变更段
- 自动显示页码（变更段 1/4）

## 最佳实践

### 推荐流程

1. **第一次使用**：选择全内容翻译模式，完整国际化
2. **日常维护**：选择仅翻译注释模式，快速处理新增注释
3. **审查变更**：使用 ← → 键仔细查看所有变更段
4. **备份恢复**：如有问题，立即通过备份历史恢复

### 性能优化

- **大文件翻译**：自动检测行数，超过阈值会警告
- **批量翻译**：使用增量扫描只翻译修改的文件
- **术语统一**：维护 `file_header_terms.yaml` 统一文件头部术语

## 常见问题

### Q: 为什么扫描结果和翻译模式有关？

A: 在 仅翻译注释模式下，扫描时会自动过滤掉代码字符串中的中文，只统计注释中的中文行数。这样可以让你专注于注释的国际化。

### Q: 如何查看所有变更段？

A: 在预览界面使用 ← → 键翻页，每页显示 6 个变更段，底部会显示当前页码（如"变更段 1/4"）。

### Q: 翻译后如何验证质量？

A: 
1. 在预览界面仔细查看每个变更段
2. 应用翻译后运行 `cargo check` / `npm run typecheck`
3. 使用 `git diff` 查看完整变更
4. 如有问题，通过备份历史恢复

## 替换后验证

替换完成后，运行以下命令验证：

```bash
cargo check              # Rust 语法检查
npm run typecheck        # TypeScript 类型检查
git diff                 # 查看变更详情
```

## 许可证

MIT