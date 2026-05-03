# zh-context-scanner

> [English](README.md) | [运行指南](RUNNING_zh.md) | [LLM 配置](LLM_CONFIG_GUIDE_zh.md)

CLI/TUI 工具，用于检测和翻译源码中的中文内容为英文。

**来自 [VaultSave](https://github.com/ArjunLee/VaultSave)**（暂未开源）

## 功能特性

- **双翻译模式**：仅注释（快速）或全内容（完整）
- **智能扫描**：按模式统计中文行数，支持 Rust/Python/TypeScript/Go/Java/C/C++
- **AI 翻译**：DeepSeek/OpenAI API 批量翻译 + 智能缓存
- **专业 TUI**：中英文双语、Git Diff 预览、分页导航
- **备份系统**：时间戳备份、一键恢复
- **Setup Wizard**：首次运行交互式配置

## 安装

```bash
cd tools/zh-context-scanner
uv sync
```

## 快速开始

### 1. 配置 LLM API

创建 `.env.local`：

```bash
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

> 详见 [LLM_CONFIG_GUIDE_zh.md](LLM_CONFIG_GUIDE_zh.md) 支持的所有提供商。

### 2. 运行 Setup Wizard（首次）

```bash
uv run python -m src.main
```

向导将引导你创建 `config/Project_Config.yaml`。

### 3. 翻译文件

1. 在偏好设置中选择翻译模式（仅注释 / 全内容）
2. 运行全量扫描或增量扫描
3. 选择文件 → 预览（Git Diff 风格） → 应用翻译

## 配置说明

### 项目配置（扁平化 YAML 结构）

`config/Project_Config.yaml`：

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

**关键**：所有路径共享相同的 extensions 和 exclude_subdirs（三个独立数组，不嵌套）。

### Git Ignore 策略

- `config/example.Project_Config.yaml` - 模板（被 git 追踪）
- `config/Project_Config.yaml` - 你的配置（被 git 忽略）

若 `Project_Config.yaml` 不存在，自动从 `example.Project_Config.yaml` 复制。

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--root` | 项目根目录（自动检测） |
| `--config` | 自定义 YAML 配置文件 |
| `--setup` | 强制运行 Setup Wizard |
| `--scan` | Headless 扫描模式 |
| `--json` | JSON 输出 |
| `--restore` | 从备份恢复 |

## 翻译模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| 仅翻译注释 | 只翻译注释中的中文 | 快速国际化 |
| 全内容翻译 | 翻译所有中文 | 完整清理 |

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
- 每页显示 6 个变更段，自动显示页码

## 目录结构

```
tools/zh-context-scanner/
├── src/                    # 核心源码
│   ├── ui/                 # TUI 组件
│   ├── solid_logger/       # 日志系统
│   ├── config.py           # 配置管理
│   ├── scanner.py          # 中文检测
│   ├── whole_file_translator.py  # AI 翻译
│   └── main.py             # 入口
├── config/
│   ├── example.Project_Config.yaml  # 模板（被追踪）
│   └── Project_Config.yaml          # 用户配置（被忽略）
├── .backup/                # 翻译备份
├── .log/                   # 日志文件
├── .env.local              # LLM API 凭证
└── pyproject.toml          # 项目元数据
```

## 运行目录

| 场景 | 运行位置 |
|------|----------|
| VaultSave 项目 | `VaultSave/` 或 `VaultSave/tools/zh-context-scanner/` |
| 其他项目 | 你的项目根目录或使用 `--root` |

```bash
# 从项目根目录运行
uv run python -m src.main

# 显式指定根目录
uv run python -m src.main --root /path/to/project
```

## 备份与恢复

```bash
# 恢复最新备份
uv run python -m src.main --restore latest

# 恢复指定备份
uv run python -m src.main --restore 2026-04-15_143022

# 恢复单个文件
uv run python -m src.main --restore latest --restore-file src/main.rs
```

## 翻译后验证

```bash
cargo check              # Rust 语法检查
npm run typecheck        # TypeScript 类型检查
git diff                 # 查看变更
```

## 许可证

MIT