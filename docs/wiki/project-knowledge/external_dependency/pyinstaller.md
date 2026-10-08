---
kind: "project_knowledge"
category: "external_dependency"
title: "PyInstaller"
name: "pyinstaller"
slug: "pyinstaller"
scopes: ["**"]
updated_at: "2026-10-08"
---

# PyInstaller

PyInstaller 是一个 Python 打包工具，可将 Python 程序及其依赖打包成独立的可执行文件（exe / 二进制），使最终用户无需安装 Python 环境即可运行。本项目用它将 `main.py` 打包成单文件可执行程序，供 Windows 与 macOS 双平台分发。

## 集成方式

本项目通过两条路径使用 PyInstaller：

1. **本地打包**（`build.bat`）：先 `pip install pyinstaller -q` 安装工具，再执行 `pyinstaller --onefile --windowed --name 教务抢课 main.py`，产物为 `dist\教务抢课.exe`，脚本随后校验产物是否存在并提示结果。

2. **CI/CD 打包**（`.github/workflows/build.yml`）：在 `Build Release` 工作流中，通过 matrix 策略并行构建 Windows（`windows-latest`）与 macOS（`macos-latest`）两个平台。安装依赖 `pip install requests PyYaml pyinstaller` 后，执行 `pyinstaller --onefile --windowed --name "${{ matrix.artifact }}" main.py`，产物 `dist/${{ matrix.artifact }}` 通过 `svenstaro/upload-release-action@v2` 上传到 GitHub Release。

## 配置要点

- **`--onefile`**：将所有依赖打包进单个可执行文件，分发便捷，但启动略慢（需解压临时目录）。
- **`--windowed`**：GUI 模式，不弹出控制台窗口，适合 tkinter 等图形界面程序；本项目 UI 基于 tkinter，故必须使用此选项。
- **`--name`**：指定产物名称。本地打包固定为 `教务抢课`；CI/CD 中通过 matrix 变量 `${{ matrix.artifact }}` 动态命名，Windows 产物为 `NB-TOOL.exe`，macOS 产物为 `NB-TOOL-mac`。
- **入口点**：统一为 `main.py`。
- **Python 版本**：CI/CD 中通过 `actions/setup-python@v5` 固定使用 Python 3.12。
- **产物路径**：PyInstaller 默认输出到 `dist/` 目录，CI/CD 从该目录上传至 Release。