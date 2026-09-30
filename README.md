# 三义漫剧评审线 `sanyi-manhua-review`（Claude Code / Codex / Kimi Code 通用）

> ⚠️ 本仓库公开发布评审规则。不要把真实剧本、客户资料或密钥提交到本仓库。

漫剧/短剧剧本的**评分、评级、锐评、审稿、快速看稿与开发决策**。**只做评分，不做任何写作任务**：不写稿、不续写、不改稿、不写替换场景；优化建议只给到"改哪一场、改成什么类型的事件"这一级的改法方向。
独立发布，不依赖任何写作 skill；项目如果恰好使用三义写作线的目录结构，会自动识别。

当前版本：2.4.0

## 使用许可

可免费安装和使用未经修改的原版评分 Skill（包括商业项目）；不得修改 Skill 本体或再分发文件。完整条款见 [LICENSE.md](LICENSE.md)。本仓库不是开源项目；GitHub 平台内的查看与 Fork 权利仍按 GitHub 服务条款执行。

---

## 安装

以下命令已填写本仓库地址。

### Claude Code
```
/plugin marketplace add ronalluotoufang-gif/-
/plugin install sanyi-manhua-review@sanyi-manhua-review
```
建议在 `/plugin` → Marketplaces 中开启自动更新。

### Codex
```
codex plugin marketplace add ronalluotoufang-gif/-
codex plugin add sanyi-manhua-review@sanyi-manhua-review
```
之后更新：`codex plugin marketplace upgrade sanyi-manhua-review`，然后重启 Codex。

### Kimi Work 桌面端

在 Work 模式的新会话中输入 `/` 选择 `plugin-builder`，把 `https://github.com/ronalluotoufang-gif/-` 发给它，并要求导入 `sanyi-manhua-review`。提示已登记后，打开「插件」→「个人」找到该插件并点击安装。评审时另开新会话，选择评分插件使用。

### Kimi Code
在 Kimi Code 对话里运行：
```
/plugins install https://github.com/ronalluotoufang-gif/-
/reload
```
⚠️ Kimi Code 从 GitHub 安装时不经过 GitHub 登录，**私有仓库大概率无法用这种方式安装**，请用下面的手动安装。

### 手动安装（任何工具都适用，私有仓库推荐）
先运行 `git clone https://github.com/ronalluotoufang-gif/-.git`，进入克隆目录，然后：
- macOS / Linux：`bash install.sh`
- Windows：`powershell -ExecutionPolicy Bypass -File install.ps1`

脚本会把 skill 复制到 `~/.claude/skills/`（Claude Code）和 `~/.agents/skills/`（Codex 与 Kimi Code 共用）。更新时 `git pull` 后再运行一次。

### Claude.ai 网页版 / Claude Desktop
把 `skills/sanyi-manhua-review/` 打包成 zip，在 设置 → Capabilities → Skills 上传。

---

## 使用

| 工具 | 手动调用 |
|---|---|
| Claude Code | `/sanyi-manhua-review` |
| Codex | `$sanyi-manhua-review` |
| Kimi Code | `/skill:sanyi-manhua-review` |

也可以直接说"给前 10 集打个分""快速看看这几集值不值得继续"。

1. **开一个新会话再评审**。刚写完或改完稿的会话里直接评，知道创作意图会让分数偏高。
2. 告诉它要评的材料，例如"评审 剧本/EP01–EP10"。只给剧本、大纲、人设、企划这类材料，不要给写作思路、修改记录、自检表。
3. 想按评审意见改稿时，另开一个写作会话，把评审报告交给它。
4. 正式评审会在项目 `reviews/` 目录生成同名的 `.md`（留档）和 `.html`（离线预览），需要本机有 Python 3。轻量模式直接在对话里回复。

### 评审模式

| 材料 | 模式 | 结果 |
|---|---|---|
| 企划案、一句话梗概 | 立项潜力 | 潜力评级 |
| 人物小传、世界观、分集大纲 | 开发准备度 | 准备度评级 |
| 前 3 集 / 前 10 集 / 完整正文 | 落地执行 | 100 分 + 评级 + 前 10 集逐集审计；EP11 之后做集尾扫描，7 个细项按集数分段（前 10 集 50%、EP11–30 30%、EP31 起 20%）加权合成 |
| "快速看看" | 轻量 | 不出分数和评级，只给门槛检查、致命问题、开发决策 |

---

## 目录结构

```
.claude-plugin/plugin.json + marketplace.json   ← Claude Code
.codex-plugin/plugin.json                       ← Codex 插件清单
.agents/plugins/marketplace.json                ← Codex 市场清单
kimi.plugin.json                                ← Kimi Code
skills/sanyi-manhua-review/                     ← skill 本体（三个工具共用）
  SKILL.md                                      ← 执行层（常驻）
  references/                                   ← 参考层 8 份，按需读取（含《剧本质量检查项》）
  scripts/render_review_html.py                 ← MD → HTML 离线预览
install.sh / install.ps1                        ← 手动安装
tools/check_versions.py                         ← 发布前检查三套清单版本
CHANGELOG.md
```

---

## 更新规则的流程

1. 改 `skills/sanyi-manhua-review/` 下的文件；评分模型、权重、锚点、门槛、输出结构变化时在 `CHANGELOG.md` 登记。
2. 把三个清单的 `version` 改成同一个新版本号：`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`kimi.plugin.json`。
3. 运行 `python3 tools/check_versions.py`，显示"三套清单一致"后提交推送。

不改版本号的话，Claude Code 和 Codex 那边不会推送更新。校准样例库、评分复盘表追加数据不需要升版本。
