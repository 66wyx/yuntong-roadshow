# 云瞳手持项目的 Git 管理

本分支：`codex/yuntong-handheld`。仓库：<https://github.com/66wyx/yuntong-roadshow>。

`main` 是原有路演展示站的分支；手持项目从其历史建立独立分支。提交到手持分支不会触发当前仅监听 `main` 的 Pages 自动发布。是否合并与发布由后续开发任务单独决定。

## 首次获取

安装 Git 与 Git LFS 后执行：

```bash
git lfs install
git clone --branch codex/yuntong-handheld --single-branch https://github.com/66wyx/yuntong-roadshow.git
cd yuntong-roadshow
git lfs pull
git status
```

`.blend`、`.glb`、STEP、STL 和硬件 PDF 由 Git LFS 管理。只下载 GitHub 的 ZIP 时可能拿到 LFS 指针；交接模型应使用上述克隆方式。图片、SVG、HTML、代码和说明文档由普通 Git 管理。

## 日常开发

开始工作前先确认当前分支和本地修改：

```bash
git status
git branch --show-current
git pull --ff-only
```

完成一项可独立说明的修改后，检查差异并提交明确的文件：

```bash
git diff
git add hardware/rid-handheld-id-a3/README.md
git diff --cached --stat
git commit -m "docs: update handheld display envelope"
git push
```

较大的变更可另建 `codex/具体任务` 分支，再通过 PR 合并到 `codex/yuntong-handheld`。避免强制推送共享分支。Windows 本地仓库当前已配置 GitHub 账户的提交身份；其他电脑需设置自己的 `user.name` 和 `user.email`。

## 目录与纳入范围

| 路径 | 管理内容 |
|---|---|
| `README_CLAUDE_HANDOFF.md` | 接手说明与 Blender MCP 入口 |
| `hardware/rid-handheld-*` | 工业设计、CAD、固件、生成脚本、渲染与验证资料 |
| `output/rid-rams-*` | 与手持外观有关的概念图、提示词及说明 |
| `docs/` | RID、硬件、交互及关联系统说明 |
| `tools/mcp-blender-*.ps1` | 已有 Blender MCP 检查/设置辅助脚本 |
| `src/`、`frontend/`、`tests/` | 关联云瞳监控系统源码与测试 |
| `site/`、根目录 Node 脚本与 `test/` | 从 `main` 继承的路演站与包验证 |

忽略项包括依赖、虚拟环境、编译缓存、`.env`、现场配置、录像数据、临时文件、重复 ZIP、Blender 自动备份、无关旗帜图片及 KiCad MCP 测试目录。这些本机文件仍保留在磁盘中。

保存 `.blend` 后再提交；未保存的 Blender 场景不会进入 Git。跨电脑运行已有脚本前，检查其中的本机绝对路径、字体路径和 MCP 配置。模型目录中的历史版本与说明应一起提交，避免将外观模型误认为已验证的加工图。
