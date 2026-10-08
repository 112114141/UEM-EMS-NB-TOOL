---
kind: "project_knowledge"
category: "external_dependency"
title: "tkinter"
name: "tkinter"
slug: "tkinter"
scopes: ["**"]
updated_at: "2026-10-08"
---

# tkinter

tkinter 是 Python 标准库内置的 GUI 框架，无需单独安装。本项目通过 `import tkinter as tk` 与 `from tkinter import ttk, scrolledtext, messagebox` 引入，用于构建抢课工具的桌面界面，包括选课信息输入、时间设置、抢课控制与日志显示。

## 集成方式

- **入口**：`main.py` 实例化 `GrabUI` 并调用 `run()`，内部执行 `self.root.mainloop()` 启动事件循环。
- **主窗口**：`GrabUI.__init__` 中通过 `tk.Tk()` 创建根窗口，设置标题、固定尺寸 `680x700`、`resizable(False, False)` 禁止拉伸，并调用 `_center_window()` 居中显示。
- **控件选型**：统一使用 ttk 主题控件（`ttk.LabelFrame`/`ttk.Entry`/`ttk.Spinbox`/`ttk.Button`）保证跨平台外观一致；Cookie 输入用 `tk.Text` + `ttk.Scrollbar` 实现横向滚动多行文本；日志区用 `scrolledtext.ScrolledText`。
- **布局**：pack 与 grid 混用——顶层框架用 pack 纵向排列，框架内部用 grid 对齐标签与输入控件。
- **状态绑定**：`tk.StringVar` 绑定状态标签，通过 `set()` 实时更新抢课状态文案。

## 配置要点

- **字体适配**：`_font()` 与 `_mono_font()` 依据 `platform.system()` 切换——macOS 用 `PingFang SC`/`Menlo`，Windows 用 `微软雅黑`/`Consolas`，避免乱码。
- **跨线程 UI 更新**：抢课逻辑在独立 `threading.Thread`（daemon=True）中运行，通过 `self.root.after(0, callback)` 将日志写入与按钮状态变更调度回主线程，避免直接操作控件引发线程安全问题。
- **日志着色与限流**：`ScrolledText` 通过 `tag_config` 定义 success/error/warning/info 四种前景色，`append_log` 按消息内容匹配标签；超过 500 行自动截断旧日志防止内存膨胀。
- **输入校验**：`messagebox.showwarning` 在 Cookie、课程名为空或时间格式错误时弹出提示并中断启动。
- **Spinbox 只读**：年月日时分秒均设 `state='readonly'`，限定取值范围（`from_`/`to`），避免非法输入。
- **超链接标签**：水印用 `tk.Label` + `bind('<Button-1>')` + `webbrowser.open` 实现可点击链接。