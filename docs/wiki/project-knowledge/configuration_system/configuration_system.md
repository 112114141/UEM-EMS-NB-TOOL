---
kind: "project_knowledge"
category: "configuration_system"
title: "配置体系"
scopes: ["**"]
updated_at: "2026-10-08"
---

# 配置体系

## 概述
本项目无任何配置文件（无 application.yml、config.yaml、.env 等），所有运行参数均通过 Tkinter 图形界面在运行时由用户手动输入，不进行持久化存储。配置项包括：Cookie（教务系统会话凭证）、课程名关键词、选课开放时间（年月日时分秒）、提前量（秒）。此外，`GrabCore` 构造函数内置 `base_url` 默认值，指向应急管理大学教务系统地址，可作为可替换的部署参数。

## 关键文件与位置
- `ui.py` — 图形界面，定义全部用户可输入的配置项及默认值
  - Cookie 输入框：`ui.py:58`（多行文本，不持久化）
  - 课程名输入框：`ui.py:73`
  - 开放时间 Spinbox 组（年/月/日/时/分/秒）：`ui.py:85`–`ui.py:112`
  - 提前量输入框：`ui.py:117`（默认值 `3`，见 `ui.py:118`）
  - 配置读取与校验入口：`ui.py:202`（`start_grab` 方法）
- `grab_core.py` — 抢课核心逻辑，承载唯一硬编码可配置参数
  - `GrabCore.__init__` 的 `base_url` 默认值：`grab_core.py:12`（默认 `https://jw.cidp.edu.cn`）

## 架构与约定
**运行时配置模式**：用户在 UI 中填写参数 → `start_grab` 方法读取并校验 → 构造 `GrabCore(cookie, log_func=self.log)` → 启动后台线程执行抢课。配置生命周期仅限于单次抢课会话，程序关闭后即丢失。

**默认值约定**：
- 开放时间默认 `2026-12-20 12:00:00`（年/月/日/时/分/秒各 Spinbox 的初始值）
- 提前量默认 `3` 秒；输入非法时回退为 `3.0`（`ui.py:222`–`ui.py:224`）
- `base_url` 默认 `https://jw.cidp.edu.cn`，当前 UI 未暴露该参数，仅可通过修改源码或调用方传参替换

**校验约定**：`start_grab` 对 Cookie、课程名做非空校验，对时间字符串做 `strptime` 格式校验，提前量做 `float` 转换容错。

**无环境隔离**：项目不区分开发/测试/生产环境，无环境变量读取逻辑。

## 开发者应遵守的规则
1. 不得将 Cookie 或任何会话凭证写入源码、日志或配置文件；Cookie 仅由用户在运行时输入。
2. 如需对接其他教务系统，修改 `grab_core.py:12` 的 `base_url` 默认值，或在 `ui.py:232` 构造 `GrabCore` 时显式传入 `base_url` 参数。
3. 新增配置项时，应在 `ui.py` 的 `_build_ui` 中添加对应控件，并在 `start_grab` 中读取校验后传入 `GrabCore.run`；禁止引入配置文件以保持运行时配置模式的一致性。
4. 时间相关参数统一使用 `datetime` 对象在模块间传递，字符串格式固定为 `%Y-%m-%d %H:%M:%S`。
5. 提前量等数值参数须做类型转换容错，避免因用户输入非法值导致程序崩溃。