# Manga Desk

漫画下载桌面工具。当前发布版 `v0.2.2` 面向 Windows；macOS 界面可从源码运行，安装包仍在开发中。两个界面使用同一套 Python 下载引擎，提供下载队列、PDF 生成、输出目录打开和 JSON 会话记录。

## 界面预览

macOS 开发版（演示任务数据）：

![Manga Desk macOS 下载队列](docs/images/manga-desk-macos.png)

Windows `v0.2.2` 发布版：

![Manga Desk Windows 下载队列](docs/images/manga-desk-0.2.2.png)

## 安装

从 [Releases](https://github.com/flyingrtx2333/ehentaiDownloader/releases) 下载最新的 `Manga.Desk_*_x64-setup.exe`，安装后直接运行 **Manga Desk**。正式安装包内置下载引擎，使用时不需要单独安装 Python。

## 功能

- 粘贴作品第一页地址，创建并查看下载任务。
- 可指定保存位置、文件夹名称，并在完成后生成 PDF。
- 点击已完成任务可在系统文件管理器打开输出文件夹；PDF 会定位到生成文件。
- 任务状态与最近 200 条活动记录保存在系统应用数据目录的 `session.json`，重启后自动恢复。
- 下载、PDF 工具、历史记录和偏好设置均在同一桌面界面中完成。

## 从源码运行

需要 Node.js、Rust 和 Python 3.10+。macOS 可用 `brew install node python@3.12` 和 [rustup](https://rustup.rs/) 安装工具链。在项目根目录准备 Python 依赖：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows 使用 `py -3.12 -m venv .venv`，再用 `.venv\Scripts\python.exe -m pip install -r requirements.txt`。

然后启动桌面开发环境：

```bash
cd desktop
npm install
npm run tauri dev
```

桌面前端按运行系统选择 `desktop/src/windows/` 或 `desktop/src/mac/`。两个界面分别维护，使用共用的 Python 引擎。macOS 界面默认保存到系统“下载”目录。开发时可用 `MANGA_DESK_PYTHON` 指定 Python 解释器；默认优先使用根目录 `.venv`。

如需仅使用旧版 Tk 界面：

```bash
python ui.py
```

## 发布构建

```bash
cd desktop
npm install
npx tauri build --config src-tauri/tauri.windows.conf.json
```

当前发布构建面向 Windows，需在 Windows 上运行上述命令；安装包位于 `desktop/src-tauri/target/release/bundle/`。macOS 开发版已有应用图标，但发布前仍需打包对应平台的 Python 引擎并完成安装包验证。

## 代理配置

在桌面应用的“偏好设置”中填写代理主机和端口。默认值为 `127.0.0.1:7890`。
