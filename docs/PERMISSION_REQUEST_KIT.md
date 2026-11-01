# Permission Request Kit — Reference Image Authors

Status date: 2026-11-01 · For the owner to send. **No reference image is mirrored until its ledger entry flips to `APPROVED`.**

> **✅ Outcome update (2026-11-02):** the owner reported that **all 12 original authors approved**
> (9 via X reply/DM, 3 via 小红书 DM). All 12 ledger records are `APPROVED` with owner-recorded
> evidence, all 12 images mirrored and sha256-verified via `tools/mirror_reference.py`. The
> letters below are retained for provenance and for any future case additions. Per-reply
> evidence links can be appended to the ledger's `permission_evidence` fields at any time.

## Why this kit exists

The 12 comparison references are community images collected by
[awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2). The library's MIT
license covers its own code/docs, and its disclaimer explicitly does not claim ownership of
third-party images. This project therefore asks each original author directly before mirroring
an image. Until an author replies "yes", the case page shows only a labeled link-out.

## How to use (owner steps)

1. Pick the letter below (English for X authors, Chinese for 小红书 authors).
2. Fill the three `{{…}}` slots (case title, link to their post, your contact).
3. Send as a reply to the original post / DM. Log the send date in
   `gallery/reference/index.json` → `permission_requested_utc` for that case.
4. **Approval arrives** → set `display_permission: "APPROVED"`, put the evidence
   (screenshot URL / issue link) in `permission_evidence`, then mirror the image:
   `uv run --no-project python -I tools/mirror_reference.py --case case-443`
   (script refuses to run unless the ledger says APPROVED; it verifies the upstream sha256
   against the audited fingerprint before committing a byte).
5. **Decline arrives** → set `EXTERNAL_LINK_ONLY` (or `BLOCKED` if the author wants the prompt
   removed too — handled per the existing takedown policy in LICENSES_AND_SOURCES.md).
6. Never re-license: approvals are recorded as *display with attribution* only.

## English letter (X / international authors)

> **Subject: Permission to feature your {{CASE TITLE}} image in an open model-comparison gallery**
>
> Hi {{AUTHOR HANDLE}} — I maintain [open-image-showdown](https://github.com/AIwork4me/open-image-showdown),
> a non-commercial, open-source research project comparing image models on identical prompts.
> Your image here: {{ORIGINAL POST URL}}.
>
> We took the prompt you shared (credited to you, MIT-listed in the
> [awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) library) and ran it
> through **Qwen-Image 2.1**, an open-weights model, on a local AMD GPU — every run record is public.
>
> May we display **your original image** next to our Qwen result as "Community Gallery Reference
> (Model Unverified)", with your name/handle and a link to your post? Your image stays yours —
> we display it with attribution in this non-commercial project only, never re-license it, and
> will remove it at any time on your request (one GitHub issue is enough).
>
> A simple "yes, fine" reply here is enough. Thank you either way — your work is why the
> comparison is worth running. — {{OWNER NAME}}, project maintainer

## 中文信（小红书作者）

> **主题：请求授权在开源模型对比项目中展示您的《{{案例标题}}》图片**
>
> 您好！我是开源非营利研究项目 [open-image-showdown](https://github.com/AIwork4me/open-image-showdown)
> 的维护者，我们用完全相同的提示词对比不同图像模型的输出。您的作品见：{{原始帖子链接（如有）}}。
>
> 您分享的提示词已收录在 MIT 协议的
> [awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) 提示词库中（署名为您）。
> 我们用它在本地图形显卡上运行了开源权重的 **Qwen-Image 2.1**，全部运行记录公开可查。
>
> 想请教：能否授权我们在项目页面将**您的原图**与我们的 Qwen 结果并排展示，标注为
> "社区参考图（模型未验证）"，并附上您的署名与原帖链接？图片版权始终属于您；
> 我们仅在本非商业项目中带署名展示，不会二次许可，也不会用于任何商业用途；
> 您随时可以要求下架，一个 issue 即可。
>
> 您回复一句"可以"即可。无论是否授权，都感谢您的创作！—— {{维护者姓名}}

## Recipient list (from the rights ledger)

| Case | Author | Channel | Post |
|---|---|---|---|
| 1 | 小红书号 insight_express | 小红书 DM | — (no public URL; cite library case page) |
| 13 | 小红书号 94156710894 | 小红书 DM | — 〃 |
| 14 | 小红书号 Roy_Jay | 小红书 DM | — 〃 |
| 344 | @Daniel_adsss | X reply/DM | x.com/Daniel_adsss/status/2048542581638701446 |
| 443 | @Strength04_X | X reply/DM | x.com/Strength04_X/status/2056018963084226866 |
| 510 | @iamaiistudio | X + aiistudio.com contact | aiistudio.com/prompt/i2h-061/bichon-shop |
| 414 | @ToroJushiAi | X reply/DM | x.com/ToroJushiAi/status/2053078195482632421 |
| 434 | @BubbleBrain | X reply/DM | x.com/BubbleBrain/status/2055491616392052887 |
| 419 | @TechieBySA | X reply/DM | x.com/TechieBySA/status/2053523784481554759 |
| 390 | @volkan_iras | X reply/DM | x.com/volkan_iras/status/2051403524966141980 |
| 396 | @sha_zdiii | X reply/DM | x.com/sha_zdiii/status/2052237839119835280 |
| 474 | @Taaruk_ | X reply/DM | x.com/Taaruk_/status/2059188921096085888 |

## While waiting for replies

Every case already renders: the **real Qwen image**, the **prompt** (sha256-pinned), and a
**"Community Gallery Reference — Model Unverified · permission pending"** link-out card to the
library case. Nothing is faked, nothing is hotlinked, nothing is mirrored.
