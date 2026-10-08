---
kind: "project_knowledge"
category: "logging_system"
title: "日志系统"
scopes: ["**"]
updated_at: "2026-10-08"
---

# 日志系统

## 概述
本项目未使用专业日志框架（无 logging.basicConfig / logback 等），而是采用自定义轻量日志机制。日志由两层组成：核心层 `GrabCore.log` 负责加时间戳前缀并通过回调函数输出；UI 层 `GrabUI.log` / `append_log` 负责将日志写入 tkinter ScrolledText 控件、按内容关键字着色、超 500 行自动截断，并通过 `root.after` 调度保证线程安全。系统无日志级别分类、无日志文件持久化。

## 关键文件与位置
- `grab_core.py:12` — `GrabCore.__init__` 接收外部 `log_func` 回调
- `grab_core.py:25` — 默认回退为 `print`：`self._log = log_func or print`
- `grab_core.py:27` — `GrabCore.log(msg)` 加 `[HH:MM:SS.ms]` 时间戳前缀并调用回调
- `ui.py:138` — `log_text` ScrolledText 日志控件定义
- `ui.py:144` — 四种着色 tag 配置（success/error/warning/info）
- `ui.py:160` — `_get_log_tag(msg)` 按关键字判定着色类别
- `ui.py:171` — `_update_status(msg)` 根据日志内容同步状态栏
- `ui.py:183` — `append_log(msg)` 写入控件、着色、500 行截断、更新状态
- `ui.py:194` — `log(msg)` 通过 `root.after(0, ...)` 调度到主线程
- `ui.py:232` — `GrabCore(cookie, log_func=self.log)` 注入 UI 日志回调

## 架构与约定
**两层回调注入架构**：核心层不直接依赖 UI，通过构造函数 `log_func` 参数注入输出通道；UI 将自身 `self.log` 方法作为回调传入 `GrabCore`，实现核心层日志向 UI 控件的转发。

**时间戳格式**：`GrabCore.log` 统一加 `[HH:MM:SS.ms]` 前缀（毫秒级，`%f` 截取前 3 位），所有核心层日志均带时间戳。

**着色规则**（`_get_log_tag` 按关键字匹配，优先级从上到下）：
- `success`（绿 #27AE60）：含 `✅` 或 `成功`
- `error`（红 #E74C3C）：含 `✗`、`失败` 或 `过期`
- `warning`（橙 #E67E22）：含 `⚠`
- `info`（蓝 #2980B9）：含 `✓` 或 `>>>`
- `normal`：默认黑色

**行数限制**：`append_log` 写入后检测总行数，超过 500 行则从头部删除多余行，防止内存膨胀。

**线程安全**：抢课逻辑在独立子线程运行，`GrabUI.log` 不直接操作 tkinter 控件，而是通过 `root.after(0, ...)` 将 `append_log` 调度到 Tk 主线程事件循环执行。

**状态联动**：`_update_status` 根据日志关键字（倒计时/开始秒抢/转入捡漏/抢课成功/已停止）同步更新顶部状态栏文字。

## 开发者应遵守的规则
1. 核心层（`GrabCore`）禁止直接 `print` 输出日志，必须通过 `self.log(msg)` 走回调通道，保证无 UI 运行时仍可输出。
2. 新增日志消息时，按语义使用对应 emoji/关键字前缀（`✅`/`✗`/`⚠`/`✓`/`>>>`），以便自动着色与状态联动正确生效。
3. 在子线程中禁止直接调用 `append_log` 或操作 `log_text` 控件，必须通过 `GrabUI.log`（即 `root.after` 调度）访问 UI。
4. 不要引入 logging 模块或第三方日志框架替换现有机制，以免破坏回调注入与着色联动；如需持久化，应在外层包装 `log_func` 而非改动核心。
5. 日志消息保持单行、简洁，避免输出 Cookie、敏感请求体等隐私信息。