# 🎓 应急管理大学教务管理系统抢课工具 | University of Emergency Management Educational Administration System Course Grabbing Tool

> 选课如打仗，手速定生死。本工具是你选课战场上的自动化武器。
>
> Course selection is war, and speed decides survival. This tool is your automated weapon on the battlefield of course registration.

---

## 🤔 这是什么 | What is this

一个帮你抢课的小工具。选课开放瞬间，它比你手快 100 倍，正如其名：NB TOOL。

A small tool to help you grab courses. At the moment registration opens, it fires 100× faster than your fingers — hence the name: NB TOOL.

**原理很简单**：填个 Cookie 和课名，它在开放时间前就开始疯狂提交选课请求，抢到为止。抢不到？没关系，它还会帮你蹲守，等别人退课了立刻补上。

**How it works**: Enter your Cookie and course name. It starts blasting registration requests before the open time and doesn't stop until you get the course. Didn't get it? No worries — it switches to sentry mode and grabs it the instant someone drops it.

## ✨ 功能 | Features

- ⚡ **秒抢 / Rush grab**: 开放时间前提前开火，5 线程并发盲提交，快到飞起 / Fires before open time with 5 concurrent threads, blazing fast
- 🎣 **捡漏 / Scavenge**: 秒抢没中？自动转入蹲守模式，有人退课秒补位 / Missed the rush? Auto-switches to sentry mode, instantly fills vacated spots
- 🕐 **时间校准 / Time calibration**: 自动从服务器校准时间，电脑时间不准也不怕 / Auto-calibrates from server time, no worries if your clock is off
- 🔍 **接口自动探测 / Auto API detection**: 填个 Cookie 就行，不用手动抓包（大概率）/ Just paste your Cookie, no manual packet sniffing (probably)
- 🖱️ **傻瓜式 UI / Idiot-proof UI**: 双击 exe 就能用，不装 Python，不装任何依赖 / Double-click the exe, no Python or dependencies needed

## 📖 使用说明 | Usage

此软件仅为开发测试和技术交流，所以没有标准使用教程，使用方式不公开，大家自行研究。

This software is for development testing and technical exchange only. There is no standard usage tutorial. The usage method is not publicly disclosed — figure it out yourself.

如有技术交流需求请加作者联系方式：**18845329616**

For technical exchange, contact the author: **18845329616**

## ⚙️ 抢课策略 | Strategy

```
开放时间前 3 秒 / 3s before open time
    ↓
秒抢模式（5线程并发盲提交）/ Rush mode (5 threads blind-fire)
    ├─ 抢到 → ✅ 结束 / Got it → ✅ Done
    └─ 课余量归零 → 自动转入捡漏 / Capacity hits 0 → auto-switch to scavenge
              ↓
      捡漏模式（1.5秒/次查余量）/ Scavenge mode (check every 1.5s)
              ├─ 有人退课 → 立即提交 → ✅ / Someone drops → instant submit → ✅
              └─ 一直等... / Keep waiting...
```

## ⚠️ 注意事项 | Caveats

- Cookie 有效期一般 1~2 小时，过期了重新登录复制一个 / Cookie lasts ~1–2 hours, re-login and copy a fresh one when it expires
- 别把频率调太高，教务系统也许会封你 IP？/ Don't crank the frequency too high — the system might ban your IP
- 本工具仅供学习交流，抢课有风险，使用需谨慎 / For learning & exchange only. Grabbing courses is risky, use with caution
- 如果抢不到，应该是你人品问题，不是工具问题 😏 / If you still can't get it, it's your karma, not the tool 😏

## 🛠️ 技术栈 | Tech Stack

- Python + requests（纯接口调用，不装浏览器）/ Pure API calls, no browser
- tkinter（UI，Python 自带）/ UI, bundled with Python
- PyInstaller（打包成单 exe）/ Packaged into a single exe

## 📝 待完善 | TODO

- [ ] 接口自动探测需用真实 Cookie 验证（等教务系统更新选课数据后测试）/ Auto-detection needs validation with a real Cookie (after the system updates course data)
- [ ] 如果自动探测失败，加一个手动填接口 URL 的选项 / If auto-detection fails, add a manual URL input option

## 📄 License

MIT — 随便用，抢不到不背锅，作者也不一定抢得到。
MIT — Do whatever, we don't take the blame if you miss a course. The author might not get one either.

---

made by [112114141](https://github.com/112114141)