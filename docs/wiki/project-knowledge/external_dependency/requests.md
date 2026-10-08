---
kind: "project_knowledge"
category: "external_dependency"
title: "requests"
name: "requests"
slug: "requests"
scopes: ["**"]
updated_at: "2026-10-08"
---

# requests

Python 第三方 HTTP 客户端库，用于与教务系统交互的全链路网络通信：校准服务器时间、检查 Cookie 有效性、探测选课接口、查询课程列表、提交选课请求。本项目未声明版本（无 requirements.txt），直接使用系统安装的 requests。

## 集成方式

- **导入**：`grab_core.py:1` 顶部 `import requests`，作为唯一网络依赖。
- **会话复用**：`GrabCore.__init__`（`grab_core.py:14`）创建 `requests.Session()`，整个抢课生命周期复用同一会话，保持底层 TCP 连接池，减少握手开销。
- **请求方法**：全部通过 `self.session` 发起，涵盖 GET 与 POST：
  | 方法 | 用途 | 位置 |
  | --- | --- | --- |
  | `session.get` | 校准时间 / 检查 Cookie / 探测接口 | `grab_core.py:36,49,67` |
  | `session.post` | 查询课程 / 提交选课 | `grab_core.py:113,183` |
- **无封装层**：未对 requests 做二次封装，直接在业务方法内调用，异常由各方法内 `try/except` 捕获后返回布尔或默认值。

## 配置要点

- **User-Agent 伪装**：`grab_core.py:16-20` 将请求头设为 Chrome 120 桌面端 UA，规避教务系统对非浏览器流量的拦截。
- **Cookie 注入**：`grab_core.py:15` 通过 `session.headers['Cookie']` 写入用户提供的登录 Cookie，后续所有请求自动携带。
- **超时控制**：GET 探测类请求 `timeout=5`，POST 选课提交 `timeout=3`（`grab_core.py:183`），兼顾响应等待与抢课时效。
- **重定向跟踪**：`check_cookie` 与 `detect_apis` 显式设置 `allow_redirects=True`（`grab_core.py:51,68`），通过 `resp.url` 判断是否被重定向至登录页以识别 Cookie 失效。
- **响应解析**：优先 `resp.json()`，失败时回退正则提取 JSON 片段再 `json.loads`（`grab_core.py:126-134`），兼容教务系统非标准响应体。
- **并发安全**：`_rush` 通过 `ThreadPoolExecutor(max_workers=5)` 并发提交选课，多个线程共享同一 `Session`，依赖 requests Session 的线程安全特性。