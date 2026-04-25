# Lanhu Design Reader

从 `lanhu-mcp` 单摘出来的蓝湖设计稿读取小工具。它不是 MCP 服务，只提供一个轻量 Python client 和 CLI，方便在脚本、Agent、CI 或本地工具里读取蓝湖 UI 设计稿。

> 本项目提取并简化自 [dsphper/lanhu-mcp](https://github.com/dsphper/lanhu-mcp) 的设计稿读取逻辑，遵循 MIT License。它不是官方蓝湖 MCP 服务。

## 功能

- 解析蓝湖项目 URL（`tid` / `pid` / `image_id`）
- 读取设计稿列表
- 读取单张设计稿的 Sketch/PS JSON
- 读取 DDS schema JSON
- 提取切图信息和下载 URL
- 支持 Figma / Sketch / Photoshop 上传稿
- Photoshop 稿支持 `assets[].isSlice`，并按 PS 语义生成 iOS / Android 多倍率 URL

## 安装

```bash
cd /Users/xuwenxin/Desktop/work/meishubao/lanhu-design-reader
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 鉴权

使用浏览器里蓝湖登录态的 cookie：

```bash
export LANHU_COOKIE='你的蓝湖 Cookie'
```

如果要读取 DDS schema，且 DDS 需要单独 cookie：

```bash
export DDS_COOKIE='你的 DDS Cookie'
```

## CLI 用法

列出设计稿：

```bash
lanhu-design-reader designs 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx'
```

读取设计稿原始 JSON：

```bash
lanhu-design-reader sketch 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx&image_id=yyy' -o sketch.json
```

读取切图信息：

```bash
lanhu-design-reader slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy -o slices.json
```

下载 iOS @2x 切图：

```bash
lanhu-design-reader download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale ios_2x -o ./slices_ios_2x
```

下载 Android xhdpi 切图：

```bash
lanhu-design-reader download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale android_xhdpi -o ./slices_android_xhdpi
```

## Python 用法

```python
import asyncio
from lanhu_design_reader import LanhuDesignClient

async def main():
    url = "https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx"
    image_id = "yyy"

    async with LanhuDesignClient() as client:
        params = client.parse_url(url)
        slices = await client.get_design_slices_info(
            image_id,
            params["team_id"],
            params["project_id"],
        )
        print(slices["total_slices"])

asyncio.run(main())
```

## Photoshop 切图倍率说明

PS 上传稿里，蓝湖的 `layer.width / height` 对应切图面板的基准像素，等同：

- iOS `@2x`
- Android `xhdpi`

例如电话图标基准为 `40x40`：

- `1x` / `ios_1x` / `android_mdpi` = `20x20`
- `2x` / `ios_2x` / `android_xhdpi` = `40x40`
- `3x` / `ios_3x` / `android_xxhdpi` = `60x60`
- `android_xxxhdpi` = `80x80`

## Credits

Core ideas and part of the design-reading flow are extracted from
[dsphper/lanhu-mcp](https://github.com/dsphper/lanhu-mcp), licensed under MIT.

This project is a standalone SDK/CLI for experiments and automation, not an official Lanhu MCP server.
