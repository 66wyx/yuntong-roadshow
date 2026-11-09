# 云瞳手持项目的 Git 协作流程

| 分支 | 用途 |
|---|---|
| `main` | GitHub 默认分支，发布路演站 |
| `handheld` | 手持接收器集成分支，汇合 V4 结构与 P4/C6 接收固件 |
| `feat/*`、`fix/*`、`hw/*`、`docs/*`、`chore/*` | 从 `handheld` 建立的单任务分支 |

V4 结构支线 `codex/rig-p1-printable-shell`、空口验证支线 `codex/rid-real-air-loopback` 和 Claude 的 UI 修复已进入 `handheld` 的历史。早期分支可用于追溯交付和验证记录。

## 获取项目

```bash
git lfs install
git clone --branch handheld https://github.com/66wyx/yuntong-roadshow.git
cd yuntong-roadshow
git lfs pull
```

`.blend`、`.glb`、STEP、BREP、STL 和已公开的硬件 PDF 走 Git LFS。打开模型前运行 `git lfs pull`，并用 `git lfs ls-files` 查看受管文件。LFS 指针检查用于验证入库格式。

## 开工与提交

从干净工作区开始。已经在另一个分支编辑时，先运行 `git fetch origin`，再用 `git worktree add -b feat/rid-frame-filter ../yuntong-rid-filter origin/handheld` 建独立目录。

```bash
git status --short --branch
git fetch origin
git switch -c docs/display-bringup origin/handheld
```

每个提交只处理一个可独立验证的改动。标题用 `type(scope): summary`，例如 `fix(ui): preserve stale target state`。正文记录需要交接的取舍和验证结果。

```bash
git diff
git add -- hardware/display-hy-a354tu102gg/README.md
git diff --cached --name-status
git diff --cached --check
git commit -m "docs(display): update bring-up notes"
git push -u origin docs/display-bringup
```

同一份 Blender 或 CAD 源文件安排一人编辑。保存源文件后，按需要同时提交生成脚本、导出件和对应验证记录。公开仓库内的供应商资料、现场数据与配置应先核对发布范围。现场标定、生产配置、`.env` 和团队本地保管的 V01 点屏 PDF 按忽略规则处理。

## PR 与合并

1. 从任务分支创建 PR，base 选 **`handheld`**。
2. 说明改动目标、已验证项和待实测项。固件与结构的结论分别记录，主机测试、ESP-IDF 构建和实板验证各自注明。
3. 等 **Handheld checks** 通过，再以 Squash 合并。确认分支的工作已合入后，可删除对应任务分支。多人协作时请相关维护者检查差异。

模板随手持分支保存，使用 GitHub CLI 时可直接带入正文。先填好内容，再创建 PR。网页版选择 `handheld` 为 base 并填入同样的三项内容。 [PR 正文模板](../.github/pull_request_template.md)

```bash
gh pr create --base handheld --title "docs(display): update bring-up notes" --body-file .github/pull_request_template.md
gh pr merge --squash --delete-branch
```

## 本地检查

在仓库根目录运行。P4 主机检查需要 C11 编译器，Windows 可以通过 Ubuntu/WSL 运行对应两条命令。

```bash
python -m pip install -e '.[dev]' Pillow
python -m pytest
python hardware/rid-handheld-evt1/firmware/p4-prototype/test_rid_validation.py
python hardware/rid-handheld-evt1/firmware/p4/tools/host_check.py
git lfs fsck --pointers HEAD
npm test
npm ci --prefix frontend
npm run test --prefix frontend
npm run typecheck --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
```

Node 版本按根目录 `package.json` 的 `engines`。P4 的 `host_check.py` 已开启 `-Werror`。普通构建使用仓库内配置，带 Sites 托管元数据的构建使用本机 `frontend/.openai/hosting.json`。板载固件构建与实物验证步骤见 [P4 固件说明](../hardware/rid-handheld-evt1/firmware/p4/README.md)。

## 交接入口

- [项目 README](../README.md) 汇总当前结构、显示路线、固件与验证记录。
- [Claude 接手说明](../README_CLAUDE_HANDOFF.md) 包含 Blender MCP、历史版本和试装入口。
