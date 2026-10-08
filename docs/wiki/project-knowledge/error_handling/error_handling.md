---
kind: "project_knowledge"
category: "error_handling"
title: "异常处理"
scopes: ["**"]
updated_at: "2026-10-08"
---

# 异常处理

## 概述
本项目未定义自定义异常类，也未设置全局异常处理器。异常处理采用"静默降级"策略：网络请求与数据解析均用 try/except 包裹，异常时返回安全默认值（False / None / 空列表），保证抢课主循环不因单次请求失败而中断。选课结果判定不依赖异常机制，而是通过 `_check_result` 方法对响应文本做关键字匹配，将业务状态（成功/已满/失败/Cookie过期）映射为统一的 `(bool, str)` 元组。UI 层在后台线程中用 try/except 兜底捕获核心逻辑异常并写入日志，finally 中恢复按钮状态。

## 关键文件与位置
- `grab_core.py:35-45` — `calibrate_time` 时间校准，异常返回 False
- `grab_core.py:47-57` — `check_cookie` Cookie 校验，异常返回 False
- `grab_core.py:59-76` — `detect_apis` 接口探测，逐路径 try/except pass
- `grab_core.py:109-120` — `find_course` 课程查询，异常返回 None
- `grab_core.py:122-152` — `_extract_courses` JSON 解析，多层降级返回 []
- `grab_core.py:154-171` — `_parse_course` 余量解析，(ValueError, TypeError) 容忍
- `grab_core.py:173-186` — `submit_select` 选课提交，异常返回 (False, str(e))
- `grab_core.py:188-206` — `_check_result` 关键字匹配判定结果
- `grab_core.py:307-316` — `_rush` 线程超时处理，取消 futures 并日志
- `grab_core.py:353-355` — `_scavenge` 检测 Cookie 过期并退出
- `ui.py:215-219` — `start_grab` 时间格式校验，ValueError 弹窗提示
- `ui.py:221-224` — `start_grab` 提前量解析，ValueError 降级为默认 3.0
- `ui.py:240-247` — `_run_grab` 后台线程兜底捕获并日志，finally 恢复 UI

## 架构与约定
1. **降级优先**：所有网络/解析异常被捕获后返回安全默认值，不向上抛出，保证主循环连续运行。
2. **结果判定与异常分离**：`_check_result` 不抛异常，纯关键字匹配返回 `(success: bool, msg: str)`，调用方据 msg 内容（如 "Cookie过期"）决定后续流程。
3. **线程超时自愈**：`_rush` 中 `as_completed` 超时后取消未完成 futures，记日志后继续下一轮，不终止秒抢。
4. **UI 层兜底**：后台线程 `_run_grab` 用 try/except/finally 包裹 `core.run`，异常写入日志，finally 通过 `root.after` 在主线程恢复控件状态。
5. **日志分级**：UI 通过消息中 emoji/关键字（✅/✗/⚠/✓）映射颜色标签，无独立错误日志文件。

## 开发者应遵守的规则
1. 新增网络请求方法时，必须用 try/except 包裹并在异常分支返回安全默认值（False/None/[]），禁止向抢课主循环抛出异常。
2. 业务结果判定统一走 `(bool, str)` 元组约定，`str` 需可被关键字检测（如含 "Cookie过期"），不要引入自定义异常类替代。
3. 后台线程中调用核心逻辑必须经 `_run_grab` 模式（try/except 日志 + finally 恢复 UI），禁止在子线程直接操作 Tkinter 控件。
4. 捕获异常时除 `submit_select` 返回 `str(e)` 外，其余降级点使用 `except Exception` 静默处理；不要捕获后既不降级也不日志，避免吞掉关键错误。
5. 日志消息通过 emoji/中文关键字承载分级语义，新增错误路径应使用 ✗ 前缀以触发 UI 红色标签。