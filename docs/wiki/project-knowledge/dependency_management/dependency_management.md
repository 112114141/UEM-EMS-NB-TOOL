---
kind: "project_knowledge"
category: "dependency_management"
title: "依赖管理"
scopes: ["**"]
updated_at: "2026-10-08"
---

# 依赖管理

## 概述
本项目为 Python 桌面抢课工具，依赖结构简单。项目**未使用任何正式依赖声明文件**（无 `requirements.txt`、`pyproject.toml`、`setup.py`），依赖信息以文字形式散落在 README.md 与 CI 配置中。运行时仅依赖第三方库 `requests`（HTTP 请求）；UI 使用 Python 自带标准库 `tkinter`，无需单独安装；打包通过 `PyInstaller` 完成。README 中提到 `PyYAML`，但源码中未实际 import，属于冗余说明。项目无依赖版本锁定机制，无统一依赖管理策略。

## 关键文件与位置
- `README.md:71-73` — 技术栈说明（Python + requests / tkinter / PyInstaller）
- `README.md:84` — 源码运行依赖安装命令：`pip install requests PyYAML`
- `.github/workflows/build.yml:26` — CI 指定 Python 版本 `3.12`
- `.github/workflows/build.yml:27` — CI 依赖安装：`pip install requests PyYAML pyinstaller`
- `.github/workflows/build.yml:28` — PyInstaller 打包命令
- `grab_core.py:1` — 运行时实际 import 的第三方依赖 `requests`
- `grab_core.py:2-8` — 标准库导入（time/random/re/json/datetime/email.utils/concurrent.futures）
- `ui.py:1-7` — UI 标准库导入（tkinter/threading/webbrowser/platform）及内部模块 `grab_core`

## 架构与约定
**依赖分层**：
- **运行时依赖**：`requests`（唯一第三方运行时依赖，用于 HTTP 会话、Cookie 维持、接口探测与选课提交，见 `grab_core.py:1`）
- **UI 依赖**：`tkinter`（Python 标准库，随解释器分发，见 `ui.py:1-2`）
- **打包依赖**：`PyInstaller`（仅 CI 环境使用，打包为单文件 exe/mac，见 `build.yml:28`）
- **标准库**：`time`/`random`/`re`/`json`/`datetime`/`threading`/`concurrent.futures` 等，无需安装

**依赖安装方式**：
- 本地开发：按 README 文字说明手动执行 `pip install requests PyYAML`
- CI 构建：在 `build.yml` 中直接 `pip install requests PyYAML pyinstaller`

**Python 版本**：CI 固定 `3.12`；README 建议 `3.10+`

## 开发者应遵守的规则
1. **新增第三方依赖时**，必须同步更新 README.md 的安装命令与 `build.yml` 的 `pip install` 行，保持两处一致（当前项目无单一事实来源）。
2. **禁止引入未在 README 与 CI 中声明的第三方库**，否则打包产物会缺失依赖。
3. **优先使用 Python 标准库**，避免增加打包体积（PyInstaller `--onefile` 会将所有依赖打入单 exe）。
4. **不依赖版本锁定**：当前未固定任何依赖版本，开发者需注意 `requests` 等库的 API 兼容性；如需锁定，应引入 `requirements.txt` 并在 README 与 CI 中引用。
5. **PyYAML 说明需清理**：README 与 CI 中列出的 `PyYAML` 在源码中未被使用，新增依赖前应先核实现有声明是否真实被引用。
6. **打包依赖（PyInstaller）不得出现在运行时 import 中**，仅作为构建工具使用。