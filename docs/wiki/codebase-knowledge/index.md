---
layout_version: "agent/v1"
store_schema_version: "v1alpha1"
title: "抢课 代码库知识（codebase）"
description: "抢课 代码库知识；按模块树组织。"
repo: "抢课"
locale: "zh"
source: "codebase"
generated_at: "2026-10-08"
module_count: 3
---

# 抢课 代码库知识 / Codebase Knowledge

## 格式说明 / Format Guide
- **目录层级 = 模块树**：子目录即子模块。含子模块的模块写成目录，其自身内容在该目录的 `README.md`；无子模块的模块是平铺的 `<模块名>.md`。
- **模块命名**：使用模块描述名（功能描述），而非目录名/包名。
- **模块文件 frontmatter**：`description`（一句话摘要）、`module_id`（稳定身份）、`updated_at`（该模块最近更新）。
- **正文**：`## 标题 <!-- category:x -->` 每段是一个知识维度；`## 关系` 段按 **依赖 / 被依赖 / 相关** 三向各一行列出邻居模块。

## 层级总览 / Module Tree

- **抢课工具**：应急管理大学教务系统自动抢课工具
  - [抢课核心引擎](抢课核心引擎.md) — 教务系统选课接口探测、时间校准、秒抢与捡漏全流程
  - [图形界面](图形界面.md) — 基于 tkinter 的抢课工具图形界面，提供参数输入、抢课控制与日志展示
  - [本地测试](本地测试.md) — 模拟教务系统 HTTP 服务器并端到端验证抢课核心引擎

## 项目统计

| 指标 | 值 |
|------|-----|
| 语言 | Python |
| 源文件数 | 4 |
| 模块数 | 3 |
| API 端点数 | 0 |
| 符号数 | 37 |
| 功能点数 | 0 |