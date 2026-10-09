# 🎓 应急管理大学教务管理系统抢课工具 | University of Emergency Management Educational Administration System Course Grabbing Tool

> 选课如打仗，手速定生死。本工具是你选课战场上的自动化武器。
>
> Course selection is war, and speed decides survival. This tool is your automated weapon on the battlefield of course registration.

---

## 🤔 这是什么 | What is this

一个帮你抢课的小工具。选课开放瞬间，它比你手快 100 倍，正如其名：NB TOOL。

A small tool to help you grab courses. At the moment registration opens, it fires 100× faster than your fingers — hence the name: NB TOOL.

**原理很简单**：填个 Cookie 和班级，选好主选备选课程，它在开放时间前就开始疯狂提交选课请求，抢到为止。抢不到？没关系，它还会帮你蹲守，等别人退课了立刻补上。

**How it works**: Enter your Cookie and class name, pick your primary and backup courses. It starts blasting registration requests before the open time and doesn't stop until you get the course. Didn't get it? No worries — it switches to sentry mode and grabs it the instant someone drops it.

## ✨ 功能 | Features

- 📋 **主选/备选勾选 / Primary & backup selection**: 课程列表分「主」「备」两列独立勾选，主选限同一课程不同班号，备选随便选，同一行互斥；主选行标绿色、备选行标黄色 / Two-column selection: primary (same course, different sections) + backup (anything goes), mutually exclusive per row; primary rows highlighted green, backup rows yellow
- 📦 **课程数据内置 / Built-in course data**: 189个教学班数据内置，填班级即可显示可选课程，零延迟 / 189 course sections built-in, just type your class name — zero latency
- ⚡ **秒抢 / Rush grab**: 串行提交，主选轮询→主选全没名额自动切换备选 / Serial submission, primary rotation → auto-switch to backup when primary exhausted
- 🎣 **捡漏 / Scavenge**: 秒抢没中？自动转入蹲守模式，每5轮刷新余量，有人退课秒补位 / Missed the rush? Auto-switches to sentry mode, refreshes capacity every 5 rounds, instantly fills vacated spots
- 🔧 **-555自动减速 / -555 auto-throttle**: 触发操作过快时延迟自动翻倍，连续10轮无-555自动恢复 / Auto-doubles delay on rate limit, recovers after 10 clean rounds
- 🔑 **Cookie验证 / Cookie validation**: 一键验证Cookie是否有效 / One-click Cookie validity check
- 🕐 **时间校准 / Time calibration**: 自动从服务器校准时间，电脑时间不准也不怕 / Auto-calibrates from server time, no worries if your clock is off
- 📝 **日志颜色区分 / Color-coded logs**: 成功绿色、失败红色、警告橙色、信息蓝色 / Green=success, red=failure, orange=warning, blue=info
- 🖱️ **傻瓜式 UI / Idiot-proof UI**: 双击 exe 就能用，不装 Python，不装任何依赖 / Double-click the exe, no Python or dependencies needed

## 📖 使用说明 | Usage

此软件仅为开发测试和技术交流，所以没有标准使用教程，使用方式不公开，大家自行研究。

This software is for development testing and technical exchange only. There is no standard usage tutorial. The usage method is not publicly disclosed — figure it out yourself.

如有技术交流需求请加作者联系方式：**18845329616**

For technical exchange, contact the author: **18845329616**

### 💾 下载 | Download

去 [Releases](https://github.com/112114141/UEM-EMS-NB-TOOL/releases) 页面下载对应平台版本：

Go to the [Releases](https://github.com/112114141/UEM-EMS-NB-TOOL/releases) page and download the version for your platform:

| 平台 / Platform | 文件 / File | 说明 / Note |
|---|---|---|
| Windows | `NB-TOOL.exe` | 双击运行 / Double-click to run |
| macOS | `NB-TOOL-mac.zip` | 解压后右键 .app → 打开 / Unzip, right-click .app → Open |

## ⚙️ 抢课策略 | Strategy

```
开放时间前 10 秒 / 10s before open time
    ↓
秒抢模式（串行提交）/ Rush mode (serial submission)
    ├─ 抢到 → ✅ 结束 / Got it → ✅ Done
    └─ 主选全没名额 → 自动切换备选 / Primary exhausted → auto-switch to backup
         ├─ 备选抢到 → ✅ 结束 / Backup got it → ✅ Done
         └─ 全没名额 → 转入捡漏 / All exhausted → switch to scavenge
               ↓
       捡漏模式（1.5秒/次查余量）/ Scavenge mode (check every 1.5s)
               ├─ 有人退课 → 立即提交 → ✅ / Someone drops → instant submit → ✅
               └─ 一直等... / Keep waiting...
```

## ⚠️ 注意事项 | Caveats

- Cookie 有效期一般 1~2 小时，过期了重新登录复制一个 / Cookie lasts ~1–2 hours, re-login and copy a fresh one when it expires
- 本工具仅供学习交流，抢课有风险，使用需谨慎 / For learning & exchange only. Grabbing courses is risky, use with caution
- 如果抢不到，应该是你人品问题，不是工具问题 😏 / If you still can't get it, it's your karma, not the tool 😏

## 🛠️ 技术栈 | Tech Stack

- Python + requests（纯接口调用，不装浏览器）/ Pure API calls, no browser
- tkinter（UI，Python 自带）/ UI, bundled with Python
- PyInstaller（打包成单 exe）/ Packaged into a single exe

## 🔧 从源码运行 | Run from source

不想下载打包版？可以直接跑源码（适合 Mac 用户或想改代码的同学）：

Don't want the packaged version? Run directly from source (suitable for Mac users or those who want to tweak the code):

```bash
# 1. 装 Python 3.10+ / Install Python 3.10+
# 2. 装依赖 / Install dependencies
pip install requests PyYAML
# 3. 运行 / Run
python main.py
```

## 📄 License

MIT — 随便用，抢不到不背锅，作者也不一定抢得到。
MIT — Do whatever, we don't take the blame if you miss a course. The author might not get one either.

---

made by [112114141](https://github.com/112114141)[左晟宇] with ❤️