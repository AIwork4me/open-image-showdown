<div align="center">

<img src="web/public/social/project.png" width="800" alt="Open Image Showdown — GPT Image 2 对决 Qwen-Image 2.1" />

# Open Image Showdown

## GPT Image 2 对决 Qwen-Image 2.1

### 同一提示词，两个模型，你来评判。

**12 个真实 Qwen-Image 2.1 本地生成案例（AMD RX 7900 XTX）· GPT 侧由社区自带 Key 补齐**

[English](README.md) · [挑战列表](#12-个挑战) · [网站](https://aiwork4me.github.io/open-image-showdown/) · [投稿指南](CONTRIBUTING.md) · [方法论](docs/METHODOLOGY.md)

</div>

---

**一句话说清楚：** 每个案例的提示词都来自 MIT 协议的
[awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2)
案例库（逐案保留原作者署名），冻结后以 sha256 锁定。**Qwen 侧是我们真实跑出来的** ——
RX 7900 XTX、原生 Windows ROCm、bf16 权重、40 步、固定 seed 42，每次运行的完整记录都提交在仓库里。
**GPT 侧刻意留空**：本项目没有 OpenAI API Key，也不假装有。如果你有，一条命令、
先看费用预估、确认后才发起付费请求，然后把结果附到 GitHub Issue。经审核的投稿会把
Open Challenge 变成 **Verified Comparison** —— 图是你的，署名也是你的。

**不伪造配对、不编造排名、不做无法验证的宣称。** GPT 图片只有在人工审核运行证据后才会展示，
绝不凭“看起来像”判定模型身份。

## 12 个挑战

| # | 案例 | 考验点 | 画布 | 状态 |
|---|---|---|---|---|
| 1 | [城市生命系统图谱](https://aiwork4me.github.io/open-image-showdown/#/case/case-1) | 12 组中英双语面板排版 | 720×1280 | 🟡 Open |
| 13 | [数学试卷实拍](https://aiwork4me.github.io/open-image-showdown/#/case/case-13) | 照相写实 + 中文密排文本 | 1024×1024 | 🟡 Open |
| 14 | [番茄炒蛋食谱信息图](https://aiwork4me.github.io/open-image-showdown/#/case/case-14) | 中文书法标题 + 版式 | 720×1280 | 🟡 Open |
| 344 | [NOIR 街头服饰海报](https://aiwork4me.github.io/open-image-showdown/#/case/case-344) | 品牌质感、少量文字 | 1024×1024 | 🟡 Open |
| 443 | [塔可爆炸拆解信息图](https://aiwork4me.github.io/open-image-showdown/#/case/case-443) | 5 个精确英文标签 | 832×1248 | 🟡 Open |
| 510 | [Bichon Shop 图标](https://aiwork4me.github.io/open-image-showdown/#/case/case-510) | 应用图标工艺 | 1024×1024 | 🟡 Open |
| 414 | [室内晨间写实摄影](https://aiwork4me.github.io/open-image-showdown/#/case/case-414) | 自然光人像写实 | 832×1248 | 🟡 Open |
| 434 | [东京街头胶片人像](https://aiwork4me.github.io/open-image-showdown/#/case/case-434) | 胶片颗粒 + 签名文字 | 720×1280 | 🟡 Open |
| 419 | [可颂烘焙分镜板](https://aiwork4me.github.io/open-image-showdown/#/case/case-419) | 8 格分镜排版 | 1280×720 | 🟡 Open |
| 390 | [羊毛毡微缩世界·日本](https://aiwork4me.github.io/open-image-showdown/#/case/case-390) | 手工材质小世界 | 832×1248 | 🟡 Open |
| 396 | [龙类复古百科海报](https://aiwork4me.github.io/open-image-showdown/#/case/case-396) | 复古信息密度 | 768×1088 | 🟡 Open |
| 474 | [四城极简旅行海报](https://aiwork4me.github.io/open-image-showdown/#/case/case-474) | 扁平设计 + 城市名排版 | 1280×720 | 🟡 Open |

## 自带 Key，投稿 GPT 结果

```bash
# 1) 你的 Key 只放在环境变量里 —— 绝不写进文件、Issue 或 PR
$env:OPENAI_API_KEY = "sk-..."

# 2) 选一个案例 —— 先显示模型/尺寸/画质/费用预估，输入 YES 才会发起付费请求
uv run --no-project python -I tools/generate_gpt.py --case case-443

# 3) 把生成的 image.png + run.json + SUBMISSION.md 附到 Issue：
#    https://github.com/AIwork4me/open-image-showdown/issues/new?template=gpt_submission.md
```

CLI 固定使用 `gpt-image-2-2026-04-21` 快照，默认只生成一张，尺寸与 Qwen 画布
像素级一致（gpt-image-2 支持自定义 16 像素倍数尺寸），付费重试上限 2 次，
写盘前会对每个产物做密钥自扫描。详见 [docs/SECURITY.md](docs/SECURITY.md)。

## 复现 Qwen 侧

需要 AMD gfx1100 显卡（RX 7900 XTX）、[qwen-image-rocm](https://github.com/AIwork4me/qwen-image-rocm)
引擎（权重与 ComfyUI 按提交锁定）、Windows + ROCm：

```powershell
powershell -File <qwen-image-rocm>\phase2-comfyui\launch_comfyui.ps1 -Port 8188 `
  -SdpMode math -ComfyArgs "--disable-smart-memory"
```

```bash
uv run --python 3.12 --with requests --with websocket-client --with jsonschema \
  python -I tools/generate_qwen.py --base-url http://127.0.0.1:8188
```

同样的权重（`Comfy-Org/Qwen-Image-2.1@aacf31a6`）+ ComfyUI 提交 + seed 42 可确定性复现全部图片。
12/12 全部成功，约 1 兆像素、每张 46–58 秒、显存 14–16 GB ——
包括这套 GPU 环境有记录以来的首批非正方形画布。[完整记录 →](docs/QWEN_12_CASE_RESULTS.md)

## 信任与验证

- **状态由 schema 强制**：`OPEN_CHALLENGE` → `COMMUNITY_SUBMITTED` → `REVIEWED_COMPARISON`（或 `BLOCKED`）[方法论 →](docs/METHODOLOGY.md)
- **每次 PR 自动校验**：提示词/图片 sha256 重算、尺寸核对、来源链完整性、重复检测、密钥扫描、站点数据一致性、静态构建
- **独立项目**：*独立社区研究项目，与 OpenAI、阿里/Qwen、AMD 均无隶属或背书关系。*
- **三层许可分别表述**：代码 MIT · 案例提示词经上游 MIT 库转载并保留署名 · Qwen 图片 CC BY-NC 4.0（权重受 Qwen Research License 约束）[许可与来源 →](LICENSES_AND_SOURCES.md)

---

<div align="center"><b>Same Prompt. Two Models. You Decide.</b></div>
