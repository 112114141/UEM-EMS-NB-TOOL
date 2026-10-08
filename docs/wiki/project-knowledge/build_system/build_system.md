---
kind: "project_knowledge"
category: "build_system"
title: "构建系统"
scopes: ["**"]
updated_at: "2026-10-08"
---

# 构建系统

## 概述
本项目基于 Python 3.12 + PyInstaller 构建，产出单文件可执行程序。提供两条构建路径：本地通过 `build.bat` 一键打包 Windows exe；CI/CD 通过 GitHub Actions 在推送 `v*` tag 时自动跨平台构建（Windows + macOS）并发布到 GitHub Release。最终用户无需安装 Python 环境即可运行。

## 关键文件与位置
- `build.bat` — 本地 Windows 打包脚本，产出 `dist\教务抢课.exe`
- `.github/workflows/build.yml` — GitHub Actions CI/CD 工作流，跨平台构建并发布到 Release
- `main.py` — PyInstaller 打包入口脚本
- `README.md` — 技术栈与运行说明（技术栈小节）

## 架构与约定
**本地构建（build.bat）**：
- 先 `pip install pyinstaller`，再执行 `pyinstaller --onefile --windowed --name 教务抢课 main.py`
- `--onefile` 打包为单文件；`--windowed` 无控制台窗口
- 产物名：`教务抢课.exe`（中文命名，仅本地使用）

**CI/CD 构建（build.yml）**：
- 触发条件：push tag `v*` 或手动 workflow_dispatch
- Matrix 矩阵：windows-latest → `NB-TOOL.exe`；macos-latest → `NB-TOOL-mac`
- Python 版本固定 3.12，安装依赖：requests、PyYAML、pyinstaller
- 产物通过 svenstaro/upload-release-action 上传至对应 tag 的 Release（overwrite: true）

**命名差异**：本地产物名为中文「教务抢课.exe」，CI 产物名为英文 `NB-TOOL.exe` / `NB-TOOL-mac`，对外发布以 CI 为准。

## 开发者应遵守的规则
1. 打包入口固定为 `main.py`，新增模块以 import 方式引入，勿改入口文件名
2. 本地快速验证用 `build.bat`；正式发布须打 `v*` tag 触发 CI，禁止手动上传 Release 产物
3. 新增运行依赖时，须同步更新 build.yml 的 `pip install` 列表和 README 的依赖说明
4. PyInstaller 参数保持 `--onefile --windowed`，确保单文件且无控制台窗口
5. Python 版本以 3.12 为准（README 标注 3.10+ 为最低兼容，CI 固定 3.12）