# Lanhu Design Skill

AgentSkills-compatible skill for reading Lanhu UI designs and downloading Web, iOS, and Android slices through `lh-design`.

This skill is intended for Cursor, OpenClaw, ClawHub, and other agents that load skills from folders containing `SKILL.md`.

## Publishing Metadata

Name:

```text
lanhu-design
```

Display name:

```text
Lanhu Design
```

Short description:

```text
Read Lanhu UI designs, inspect slices, and download Web, iOS, and Android assets with lh-design.
```

Category:

```text
Design assets / UI implementation
```

Repository:

```text
https://github.com/xuwenxindeai/lanhu-design-reader
```

Required dependency:

```text
lh-design CLI from xuwenxindeai/lanhu-design-reader
```

Required secrets:

```text
LANHU_COOKIE
```

Optional secrets:

```text
DDS_COOKIE
```

Security summary:

```text
The skill contains only agent instructions. It does not bundle executable scripts, store cookies, or include exported design assets. The separately installed lh-design CLI uses LANHU_COOKIE/DDS_COOKIE from the user's environment or ~/.lanhu-design-reader/.env to call Lanhu APIs.
```

Suggested marketplace summary:

```text
Lanhu Design helps coding agents turn Lanhu UI designs into implementation-ready assets. It guides the agent to inspect design slices first, then download the correct Web, iOS, or Android asset scales using the lh-design CLI.
```

## What It Does

- Reads Lanhu project/stage URLs.
- Lists UI designs and identifies target `image_id` values.
- Extracts slice metadata into `slices.json`.
- Downloads Web `1x/2x/3x` assets.
- Downloads iOS `ios_2x/ios_3x` assets.
- Downloads Android `drawable-*` assets.
- Handles Figma, Sketch, and Photoshop-uploaded Lanhu designs supported by `lh-design`.

## Skill Folder

```text
lanhu-design/
  SKILL.md
```

The skill itself is intentionally small. Installation details and security notes live in this README so the agent-facing `SKILL.md` stays focused.

## Requirements

- Python 3.10+
- `git`
- Network access to `lanhuapp.com`
- A valid `LANHU_COOKIE`
- The `lh-design` command from `xuwenxindeai/lanhu-design-reader`

Optional:

- `DDS_COOKIE`, when DDS schema reads need a different login cookie

## Install `lh-design`

Recommended user-level install:

```bash
curl -fsSL https://raw.githubusercontent.com/xuwenxindeai/lanhu-design-reader/main/install.sh | bash
```

Default paths:

```text
Source: ~/.lanhu-design-reader/src
Virtualenv: ~/.lanhu-design-reader/venv
Config: ~/.lanhu-design-reader/.env
Command: ~/.local/bin/lh-design
```

Verify:

```bash
lh-design --help
```

## Configure Cookie

Temporary shell configuration:

```bash
export LANHU_COOKIE='your-lanhu-cookie'
```

Recommended persistent configuration:

```text
~/.lanhu-design-reader/.env
```

```env
LANHU_COOKIE=your-lanhu-cookie
DDS_COOKIE=
```

Keep cookies out of prompts, screenshots, logs, commits, and issue reports.

## Install The Skill

### ClawHub / OpenClaw Registry

The skill is published on ClawHub as:

```text
lanhu-design@1.0.0
```

Install from OpenClaw:

```bash
openclaw skills install lanhu-design
```

Inspect the published package:

```bash
clawhub inspect lanhu-design
```

### OpenClaw Workspace Skill

Copy the skill folder into an OpenClaw workspace `skills` directory:

```bash
mkdir -p ./skills
cp -R cursor-skills/lanhu-design ./skills/lanhu-design
```

Start a new OpenClaw session after installing or updating the skill.

### OpenClaw User Skill

Copy the skill folder into the user-level skills directory:

```bash
mkdir -p ~/.openclaw/skills
cp -R cursor-skills/lanhu-design ~/.openclaw/skills/lanhu-design
```

Verify that OpenClaw can see the skill:

```bash
openclaw skills info lanhu-design --json
```

The skill should report:

```text
source: openclaw-managed
eligible: true
```

### Cursor Skill

Copy the skill folder into Cursor skills:

```bash
mkdir -p ~/.cursor/skills
cp -R cursor-skills/lanhu-design ~/.cursor/skills/lanhu-design
```

## Example Prompts

```text
用 lh-design 读取这个蓝湖设计稿的切图：
<蓝湖URL>
image_id 是 yyy
我是 iOS，请下载 ios_2x 和 ios_3x。
```

```text
用 lh-design 读取这个蓝湖设计稿的切图：
<蓝湖URL>
我是 Web，请下载 1x、2x、3x。
```

```text
用 lh-design 读取这个蓝湖设计稿的切图：
<蓝湖URL>
我是 Android，请下载 drawable 对应倍率资源。
```

## Security Notes

- This skill does not include executable scripts. It instructs the agent to use the separately installed `lh-design` CLI.
- `lh-design` uses Lanhu cookies to call Lanhu APIs. Treat `LANHU_COOKIE` and `DDS_COOKIE` as secrets.
- Review `install.sh` before running it if installing in a sensitive environment.
- Avoid piping remote scripts directly into `bash` in high-security environments; download and inspect the script first.
- Do not commit `.env`, downloaded design JSON, or exported assets if they contain private product designs.
- Prefer project-local output directories for downloaded slices so generated assets are easy to review and clean up.

## Publishing Checklist

- `lanhu-design/SKILL.md` has valid YAML frontmatter with `name` and `description`.
- The skill folder name matches the skill name: `lanhu-design`.
- The skill does not store cookies, tokens, downloaded assets, or generated JSON.
- The README explains installation, configuration, examples, and security boundaries.
- `lh-design --help` works after installation.
- A realistic Lanhu URL can run `lh-design slices` and produce `slices.json`.

## Credits

The underlying CLI is maintained at:

https://github.com/xuwenxindeai/lanhu-design-reader

Core design-reading ideas are extracted from `dsphper/lanhu-mcp`, licensed under MIT.
