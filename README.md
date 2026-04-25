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
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

安装后推荐使用短命令 `lh-design`；长命令 `lanhu-design-reader` 也保留可用。

如果要接入 Cursor MCP，也安装 MCP 依赖：

```bash
pip install -e .[mcp]
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
lh-design designs 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx'
```

读取设计稿原始 JSON：

```bash
lh-design sketch 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx&image_id=yyy' -o sketch.json
```

读取切图信息：

```bash
lh-design slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy -o slices.json
```

### Web 同学

Web 资源使用通用 `1x / 2x / 3x`：

```bash
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale 1x -o ./web_1x
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale 2x -o ./web_2x
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale 3x -o ./web_3x
```

### iOS 同学

iOS 资源使用 `ios_2x / ios_3x`：

```bash
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale ios_2x -o ./ios_2x
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale ios_3x -o ./ios_3x
```

### Android 同学

Android 资源使用 `android_*`：

```bash
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale android_mdpi -o ./drawable-mdpi
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale android_xhdpi -o ./drawable-xhdpi
lh-design download-slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy --scale android_xxhdpi -o ./drawable-xxhdpi
```

## Cursor 中使用

### 方式一：CLI

让 Cursor Agent 使用 `lh-design` 命令即可。适合最轻量的团队用法：

```text
用 lh-design 读取这个蓝湖设计稿的切图：<蓝湖URL>
image_id 是 yyy。我是 iOS/Web/Android，请下载对应倍率资源。
```

### 方式二：Cursor Skill

仓库内提供了模板：

```text
cursor-skills/lanhu-design/SKILL.md
```

复制到个人 Cursor skills：

```bash
mkdir -p ~/.cursor/skills/lanhu-design
cp cursor-skills/lanhu-design/SKILL.md ~/.cursor/skills/lanhu-design/SKILL.md
```

之后在 Cursor 里提到“蓝湖设计稿 / 切图 / UI稿 / iOS @2x / Android drawable / Web 2x”等场景，AI 会优先按该 skill 使用 `lh-design`。

### 方式三：Cursor MCP

安装 MCP 依赖后，本项目提供 `lh-design-mcp`：

```bash
pip install -e .[mcp]
lh-design-mcp --help
```

#### stdio 配置

推荐给 Cursor 使用 stdio。复制 `examples/cursor-mcp.stdio.json` 到 Cursor MCP 配置，并把路径换成你本机实际路径：

```json
{
  "mcpServers": {
    "lanhu-design-reader": {
      "command": "/absolute/path/to/lanhu-design-reader/.venv/bin/lh-design-mcp",
      "args": [],
      "env": {
        "LANHU_COOKIE": "your_lanhu_cookie_here"
      }
    }
  }
}
```

#### HTTP 配置

也可以手动启动 HTTP MCP：

```bash
LANHU_COOKIE='你的蓝湖 Cookie' lh-design-mcp --transport http --host 127.0.0.1 --port 8001
```

Cursor MCP 配置：

```json
{
  "mcpServers": {
    "lanhu-design-reader": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

MCP 工具包含：

- `lanhu_get_designs`
- `lanhu_get_design_slices`
- `lanhu_download_slices`
- `lanhu_get_sketch_json`
- `lanhu_get_schema_json`

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
