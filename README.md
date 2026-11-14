# WorkReminder

WorkReminder 是一个 Windows 10/11 系统托盘工具，用于在用户连续工作达到设定时长后进行提醒。程序只读取 Windows 提供的“距离最近一次键盘或鼠标输入的时间”，不记录按键内容、鼠标位置、窗口标题或用户正在进行的具体操作。

## 运行环境

- Windows 10 / 11
- Python 3.11 或更高版本
- 不需要管理员权限

## 安装依赖

请使用项目指定的 Python 环境安装：

```powershell
python.exe -m pip install -r requirements.txt
```

## 开发模式运行

```powershell
python.exe main.py
```

程序启动后默认不显示主窗口，只在系统托盘运行。配置文件和日志位于：

`%APPDATA%\WorkReminder\config.json`

`%APPDATA%\WorkReminder\workreminder.log`

## 测试

```powershell
python.exe -m pytest
```

## 打包

在项目根目录执行：

```powershell
python.exe -m PyInstaller build/workreminder.spec
```

输出目标为 `dist\workreminder_v1.exe`。程序的 EXE、托盘和设置窗口图标均使用项目根目录下的 `picuture_256x256.ico`；文件不存在时会回退到 Qt 默认图标。

生成 0.2 版本可使用 `build/workreminder_v0_2.spec`，输出为 `dist\workreminder_v0_2.exe`。

## 判定逻辑

程序使用 `GetLastInputInfo()` 获得最后一次键盘或鼠标输入距当前经过的秒数：

- idle 时间小于活动阈值时，用户被视为处于活动状态；首次活动会创建一个工作 session。
- 工作时长使用“最后确认活动时间 − session 开始时间”计算。短暂 idle 不会继续增加有效工作时长，也不会立即重置 session。
- idle 时间达到休息阈值时，当前 session 结束；下一次活动会创建新的 session。
- 达到连续工作提醒时间后触发首次提醒，之后按照“再次提醒间隔时间”周期提醒。
- 只有在休息时间达到阈值并结束当前 session 后，周期提醒才会重置。
- 设置中可选“启用超时黑洞”（默认关闭）。超过连续工作提醒时间后，主屏幕中央显示可穿透鼠标的黑洞动画，随工作时长增长，超时 15 分钟达到最大；达到休息判定时间或关闭选项后消失。短暂离开时保留当前大小。
- 黑洞是参考项目视觉风格绘制的透明动画，不包含其屏幕折射和光线追踪效果。

程序不安装全局键盘或鼠标 hook，不记录用户按下了什么键，不记录鼠标轨迹，不截图，也不监控前台窗口或具体应用。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)。

## 致谢

感谢 [cabbagehao 的 Black Hole Timer](https://github.com/cabbagehao/blackhole-timer) 为本项目的黑洞提醒效果提供灵感；也感谢该项目所致谢的 [Ghostty Blackhole](https://github.com/s0xDk/ghostty-blackhole) 及其相关工作。WorkReminder 的黑洞动画是独立绘制的视觉效果。
