# 图标和构建说明

本项目将平台图标资源放在仓库约定的 `resources/icons/` 目录（首选位置）。历史上我们也在 `docs/` 中保存源图，但推荐把源图与生成的目标图都放进 `resources/icons/`，便于打包工具统一引用。

项目包含（建议将副本放入 `resources/icons/`）：

- `datamonitor_logo_dark.png` — 深色版主标识
- `datamonitor_logo_icon.png` — 用于生成 `.ico` / `.icns` 的源图（建议为正方形、1024×1024）
- `datamonitor_logo_standard.png` — 标准版主标识
- `datamonitor_logo_transparent.png` — 透明背景版标识

生成平台专用图标

1. 生成 Windows `.ico`（使用 Pillow）

```bash
# 依赖 Pillow
python -m pip install --user Pillow
# 脚本会优先在 resources/icons/ 查找源图，若未找到再回退到 docs/
python tools/gen_ico.py
# 输出：resources/icons/datamonitor.ico
```

2. 生成 macOS `.icns`（使用系统工具 sips + iconutil）

```bash
# 清理旧图标集并创建 .iconset
rm -rf resources/icons/datamonitor.iconset resources/icons/datamonitor.icns
mkdir -p resources/icons/datamonitor.iconset

# 以 resources/icons/datamonitor_logo_icon.png 为源生成各尺寸（回退到 docs/ 若未找到）
sips -z 16 16 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_16x16.png
sips -z 32 32 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_16x16@2x.png
sips -z 32 32 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_32x32.png
sips -z 64 64 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_32x32@2x.png
sips -z 128 128 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_128x128.png
sips -z 256 256 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_128x128@2x.png
sips -z 256 256 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_256x256.png
sips -z 512 512 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_256x256@2x.png
sips -z 512 512 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_512x512.png
sips -z 1024 1024 resources/icons/datamonitor_logo_icon.png --out resources/icons/datamonitor.iconset/icon_512x512@2x.png

# 使用 iconutil 打包为 .icns
iconutil -c icns resources/icons/datamonitor.iconset -o resources/icons/datamonitor.icns
# 输出：resources/icons/datamonitor.icns
```

在构建时使用图标

- `build.py` 会在 macOS 上优先使用 `resources/icons/datamonitor.icns`（若存在），回退到 `docs/datamonitor.icns`。
- Windows 构建会优先使用 `resources/icons/datamonitor.ico`（若存在），回退到 `docs/datamonitor.ico`。

重新构建应用

```bash
# 使用项目根目录的 Python 运行构建脚本（请确保已激活 venv 并安装 PyInstaller）
python build.py
# 生成产物位于 dist/ 目录：DataMonitor.app（macOS）和 DataMonitor 可执行程序
```

注意

- 推荐把源 PNG 与生成的 .ico/.icns 一起提交到 `resources/icons/`，这样 CI/打包脚本可以在一致的位置查找。
- macOS 下 `.icns` 需要通过 `iconutil` 生成（系统自带），不能直接用单个 PNG 作为 .app 的图标。
- 如果构建脚本未找到图标，它仍会使用默认图标并完成构建。
