# Lanhu Design Reader

一个给 AI / 同事 / 脚本使用的蓝湖设计稿读取工具。

它从 [dsphper/lanhu-mcp](https://github.com/dsphper/lanhu-mcp) 里单独摘出了**设计稿读取和切图导出**这部分能力，并做成更轻量的 CLI / Cursor Skill / Cursor MCP。

> 不是官方蓝湖 MCP 服务。  
> 不包含官方 MCP 的 Axure 需求分析、留言板、飞书通知、团队协作知识库等功能。  
> 主要解决：让 AI 能读取蓝湖 UI 设计稿、拿切图、下载 Web / iOS / Android 对应倍率资源。

## 它和官方 lanhu-mcp 是什么关系？

可以这样理解：

| 能力 | 官方 lanhu-mcp | 本项目 |
| --- | --- | --- |
| 读取蓝湖 UI 设计稿列表 | 支持 | 支持 |
| 读取单张设计稿 JSON | 支持 | 支持 |
| 获取切图信息 | 支持 | 支持 |
| 下载切图 | 支持 | 支持 |
| Figma / Sketch 稿切图 | 支持 | 支持 |
| Photoshop 上传稿切图 | 原版不完整 | 支持 |
| PS 稿 iOS / Android 倍率 | 原版不完整 | 支持 |
| Axure 需求文档分析 | 支持 | 不支持 |
| AI 分析需求 / 四阶段需求分析 | 支持 | 不支持 |
| 留言板 / 飞书通知 | 支持 | 不支持 |

一句话：**本项目只摘了官方 MCP 里“蓝湖设计稿读取和切图”相关能力，并额外支持 PS 上传稿。**

## 给同事的最简单说法

让 AI 执行这句话：

```text
帮我克隆并安装这个蓝湖设计稿读取工具：
https://github.com/xuwenxindeai/lanhu-design-reader
安装后确认 lh-design 命令可用，并指导我配置 LANHU_COOKIE。
```

如果要接入 Cursor MCP，让 AI 执行：

```text
帮我克隆并安装 https://github.com/xuwenxindeai/lanhu-design-reader
安装时带 MCP 依赖：pip install -e .[mcp]
然后帮我配置 Cursor MCP，使用 lh-design-mcp。
```

## 安装

```bash
git clone https://github.com/xuwenxindeai/lanhu-design-reader.git
cd lanhu-design-reader
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

安装后验证：

```bash
lh-design --help
```

如果要用 Cursor MCP：

```bash
pip install -e .[mcp]
lh-design-mcp --help
```

## 配置蓝湖 Cookie

这个工具需要蓝湖登录态 Cookie。

临时配置：

```bash
export LANHU_COOKIE='你的蓝湖 Cookie'
```

长期配置可以写到 `.env`：

```env
LANHU_COOKIE=你的蓝湖 Cookie
```

如果要读取 DDS schema，且 DDS 需要单独 cookie：

```env
DDS_COOKIE=你的 DDS Cookie
```

## 日常使用：CLI

### 1. 查看设计稿列表

```bash
lh-design designs 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx'
```

### 2. 读取切图信息

```bash
lh-design slices 'https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx' --image-id yyy -o slices.json
```

如果 URL 里已经带 `image_id=yyy`，可以省略 `--image-id`。

### 3. 下载 Web 切图

Web 同学用通用 `1x / 2x / 3x`：

```bash
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale 1x -o ./web_1x
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale 2x -o ./web_2x
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale 3x -o ./web_3x
```

### 4. 下载 iOS 切图

iOS 同学用 `ios_2x / ios_3x`：

```bash
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale ios_2x -o ./ios_2x
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale ios_3x -o ./ios_3x
```

### 5. 下载 Android 切图

Android 同学用 `android_*`：

```bash
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale android_mdpi -o ./drawable-mdpi
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale android_hdpi -o ./drawable-hdpi
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale android_xhdpi -o ./drawable-xhdpi
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale android_xxhdpi -o ./drawable-xxhdpi
lh-design download-slices '<蓝湖URL>' --image-id yyy --scale android_xxxhdpi -o ./drawable-xxxhdpi
```

## Cursor 里怎么用？

本项目支持三种方式。

### 方式一：让 Cursor AI 调 CLI

安装好后，在 Cursor 里直接说：

```text
用 lh-design 读取这个蓝湖设计稿的切图：
<蓝湖URL>
image_id 是 yyy
我是 iOS，请下载 ios_2x 和 ios_3x。
```

Web 同学说：

```text
用 lh-design 读取这个蓝湖设计稿的切图：
<蓝湖URL>
image_id 是 yyy
我是 Web，请下载 1x、2x、3x。
```

Android 同学说：

```text
用 lh-design 读取这个蓝湖设计稿的切图：
<蓝湖URL>
image_id 是 yyy
我是 Android，请下载 drawable 对应倍率资源。
```

这是最简单的方式，不需要配置 MCP。

### 方式二：安装 Cursor Skill

仓库里带了一个 skill 模板：

```text
cursor-skills/lanhu-design/SKILL.md
```

复制到个人 Cursor skills：

```bash
mkdir -p ~/.cursor/skills/lanhu-design
cp cursor-skills/lanhu-design/SKILL.md ~/.cursor/skills/lanhu-design/SKILL.md
```

之后你在 Cursor 里说“蓝湖设计稿”“切图”“UI稿”“iOS @2x”“Android drawable”“Web 2x”等，AI 会更容易自动使用 `lh-design`。

### 方式三：配置 Cursor MCP

这种方式配置好以后，Cursor 会自动启动工具；同事不需要手动输入一长串启动命令。

#### 第一步：安装 MCP 版本

```bash
pip install -e .[mcp]
```

#### 第二步：找到 `lh-design-mcp` 的真实路径

在安装目录执行：

```bash
pwd
```

假设输出是：

```text
/Users/zhangsan/work/lanhu-design-reader
```

那 MCP 命令路径就是：

```text
/Users/zhangsan/work/lanhu-design-reader/.venv/bin/lh-design-mcp
```

#### 第三步：配置 Cursor MCP

把下面配置加到 Cursor 的 MCP 配置里：

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

需要替换两处：

- `/absolute/path/to/lanhu-design-reader`：换成你电脑上的项目路径
- `your_lanhu_cookie_here`：换成你的蓝湖 Cookie

配置好后，重启 Cursor 或刷新 MCP。

之后可以直接问 Cursor：

```text
用 lanhu-design-reader 读取这个蓝湖设计稿的切图：<蓝湖URL>
image_id 是 yyy，我要 iOS @2x/@3x。
```

#### 高级用法：HTTP 模式（不懂可以忽略）

普通同事不用这一段。只有你想手动启动一个本地 MCP 服务时才需要。

先启动服务：

```bash
LANHU_COOKIE='这里填你的蓝湖 Cookie' lh-design-mcp --transport http --host 127.0.0.1 --port 8001
```

再把 Cursor MCP 配成：

```json
{
  "mcpServers": {
    "lanhu-design-reader": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

MCP 工具包括：

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

## 常见问题

### 这个能替代官方 lanhu-mcp 吗？

不能完全替代。它只覆盖设计稿读取和切图相关能力。需求文档、Axure 分析、留言板、飞书通知等仍然用官方 `lanhu-mcp`。

### Web / iOS / Android 应该用哪个 scale？

- Web：`1x / 2x / 3x`
- iOS：`ios_2x / ios_3x`
- Android：`android_mdpi / android_hdpi / android_xhdpi / android_xxhdpi / android_xxxhdpi`

### Photoshop 上传稿支持吗？

支持。它会读取 PS 稿里的 `assets[].isSlice`，并找到对应图层的 `images.png_xxxhd` / `images.svg`。

## Credits

Core ideas and part of the design-reading flow are extracted from
[dsphper/lanhu-mcp](https://github.com/dsphper/lanhu-mcp), licensed under MIT.

This project is a standalone SDK/CLI/MCP wrapper for experiments and automation, not an official Lanhu MCP server.
