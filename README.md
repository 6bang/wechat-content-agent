# wechat-content-agent

`wechat-content-agent` 是一个课程咨询型微信公众号内容自动化生产系统，服务电商咨询、管理课程和企业服务业务。

它不是普通写稿工具。第一阶段只负责每天自动生成内容包、写入飞书协作文档、飞书群阶段汇报、邮箱备份和 GitHub Actions 定时运行；最终公众号发布必须由主编、老板或运营人工确认后执行。

## 适合业务

适合面向电商老板、运营负责人、电商管理者的课程、咨询、企业服务内容生产，尤其适合以下方向：

- 电商 SOP 流程化、流程化组织、新品 SOP、爆款复制体系
- 目标管理、薪酬绩效激励、运营岗位管理体系
- 中层干部培养、电商老板管理升级
- 年销售额 3000 万到 2 亿、团队 50-200 人、运营团队 5-10 人的电商公司

## C/E/S 三层内容模型

- `C层 Company / Commerce`: 泛流量内容，用企业家故事、商业案例、经营认知破圈，提高打开率。
- `E层 E-commerce`: 行业流量内容，讲电商老板痛点、平台变化、运营团队、选品投流和经营难题，筛选精准用户。
- `S层 SOP / System`: 专业内容，讲 SOP、流程工具、目标管理、绩效激励和管理模板，建立专业信任并推动咨询转化。

漏斗逻辑：`C层破圈 → E层筛选 → S层成交`。

## 一周 2-3-2 编排

每天生成 3 个候选选题，并且 C/E/S 三个层级各写 1 篇完整文章。主编给出推荐优先发布稿，最终由老板/主编人工选择当天发哪篇。

- 周一 `C1` 老板认知课
- 周二 `E1` 电商老板观察
- 周三 `S1` SOP流程课
- 周四 `E2` 电商团队管理
- 周五 `S2` 流程工具箱
- 周六 `C2` 商业案例拆解
- 周日 `E3` 一周电商复盘

## Agent 分工

- `选题策划 Agent`: 生成 C/E/S 三层候选选题。
- `内容主编 Agent`: 按评分模型评估 3 个选题，给出今日推荐优先发布稿。
- `内容编辑 Agent`: 分别为 C/E/S 三个选题生成文章大纲和公众号初稿。
- `审稿 Agent`: 分别审阅 C/E/S 三篇文章，从标题、开头、逻辑、案例、方法、专业度、转化和风险角度审稿定稿。
- `新媒体运营 Agent`: 分别为 C/E/S 三篇文章生成标题、摘要、封面、朋友圈、社群、私聊、评论区问题和复盘模板。
- `视觉排版 Agent`: 分别为 C/E/S 三篇文章生成封面方向、正文配图清单、流程图、看板图、检查清单、结尾引导卡和公众号排版建议。
- `总控 Agent / daily_pipeline`: 串联全流程，保存 outputs，创建飞书协作文档，触发飞书与邮箱通知。

## 主编评分模型

主编 Agent 会对每个选题打 6 项分数，每项 1-5 分：

- `pain_score`: 痛点强度
- `spread_score`: 传播价值
- `precision_score`: 精准流量价值
- `trust_score`: 专业信任价值
- `conversion_score`: 业务转化价值
- `calendar_score`: 当天栏目节奏匹配度

总分：`total_score = pain_score + spread_score + precision_score + trust_score + conversion_score + calendar_score`。

## 每日流程

第一版每天北京时间凌晨 1 点一次性跑完整流程，整体比原计划提前 5 小时：

1. 读取品牌配置和一周内容日历
2. 根据当天星期确定栏目编号
3. 生成 C/E/S 三个候选选题
4. 飞书汇报：选题策划完成
5. 主编评估并给出推荐优先发布稿
6. 飞书汇报：主编评估完成
7. 生成 C/E/S 三篇文章大纲
8. 飞书汇报：文章大纲完成
9. 生成 C/E/S 三篇公众号初稿
10. 飞书汇报：公众号初稿完成
11. 审稿并生成 C/E/S 三篇终稿
12. 飞书汇报：审稿定稿完成
13. 生成 C/E/S 三篇发布包
14. 飞书汇报：发布包完成
15. 视觉排版 Agent 生成 C/E/S 三篇视觉排版方案和原创 SVG 示意图
16. 飞书汇报：视觉排版完成
17. 生成 `article_selection.md`、三篇 `wechat_ready_article.md`、`email_summary.md`
18. 如果开启飞书文档，创建飞书协作文档并写入完整内容包
19. 生成 `feishu_message.md`，其中包含飞书文档链接
20. 飞书汇报：今日内容包完成
21. 如果开启邮箱，发送邮箱备份
22. GitHub Actions 上传 `outputs/` artifact
23. 等待人工确认发布

后续如果拆成分阶段运行，建议使用下面这套北京时间：

| 时间 | Agent / 阶段 | 工作内容 |
| --- | --- | --- |
| 01:00 | 选题策划 Agent | 生成 C/E/S 三层选题 |
| 03:00 | 内容主编 Agent | 评估选题，给出今日推荐 |
| 04:00 | 内容编辑 Agent | 生成三篇文章大纲 |
| 05:00 | 内容编辑 Agent | 生成三篇公众号初稿 |
| 06:00 | 审稿 Agent | 审稿、修改、生成终稿 |
| 07:00 | 新媒体运营 Agent | 生成三篇发布包 |
| 07:20 | 视觉排版 Agent | 生成视觉排版方案和配图素材 |
| 07:30 | 总控 Agent | 创建飞书文档、发送汇总通知和邮箱备份 |

人工发布时间仍建议保留 `18:00`，方便主编、运营和老板白天确认后再发布。

## 输出文件

每天会在 `outputs/YYYY-MM-DD/` 下生成：

```text
topics.json
topics.md
selected_topic.md
article_selection.md
draft.md
review.md
final_article.md
wechat_ready_article.md
publish_package.md
visual_layout.md
visual_assets/
courseware_reference.md
feishu_doc_preview.md
feishu_message.md
email_summary.md
run_summary.json
articles/C/draft.md
articles/C/review.md
articles/C/final_article.md
articles/C/wechat_ready_article.md
articles/C/publish_package.md
articles/C/visual_layout.md
articles/C/visual_assets/
articles/E/draft.md
articles/E/review.md
articles/E/final_article.md
articles/E/wechat_ready_article.md
articles/E/publish_package.md
articles/E/visual_layout.md
articles/E/visual_assets/
articles/S/draft.md
articles/S/review.md
articles/S/final_article.md
articles/S/wechat_ready_article.md
articles/S/publish_package.md
articles/S/visual_layout.md
articles/S/visual_assets/
```

顶层 `wechat_ready_article.md`、`final_article.md`、`publish_package.md`、`visual_layout.md` 保留主编推荐稿，兼容旧流程。真正的三篇候选稿在 `articles/C`、`articles/E`、`articles/S` 目录里。

## 本地运行

```bash
cd /Users/liuwenjun-15-air/Documents/New\ project\ 2/wechat-content-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 src/main.py
```

指定日期运行：

```bash
python3 src/main.py --date 2026-05-12
```

只跑某个阶段用于调试：

```bash
python3 src/main.py --stage topics
python3 src/main.py --stage editor
python3 src/main.py --stage draft
```

## Mock 模式

默认使用 mock 模式，不需要真实 OpenAI API 也能跑通：

```env
USE_MOCK=true
MODEL=gpt-5.5-thinking
```

## OpenAI API

要切换真实 API，在 `.env` 或 GitHub Secrets 中设置：

```env
USE_MOCK=false
OPENAI_API_KEY=你的 OpenAI API Key
MODEL=gpt-5.5-thinking
```

所有 Agent 都通过 `src/utils/llm.py` 的 `call_llm(system_prompt, user_prompt)` 调用模型。API 调用失败会输出清晰错误日志。

## GitHub 课件库参考

建议让 Agent 写文章前先读取你的私有课件库 `6bang/6bang-courseware`。这样生成的内容会优先参考课程框架、岗位流程、SOP、S/A/B/C 评估、案例和销售素材，而不是凭空写。

本地运行时，在 `.env` 里配置：

```env
ENABLE_COURSEWARE_CONTEXT=true
COURSEWARE_PATH=/Users/liuwenjun-15-air/Documents/6bang-courseware
COURSEWARE_REFERENCE_PATHS=01_课程总纲,02_线下课课件,05_客户案例,06_销售素材,07_公众号素材
COURSEWARE_MAX_FILES=12
```

GitHub Actions 运行时，因为课件库是私有仓库，需要额外配置一个只读 token：

1. 在 GitHub 右上角头像里进入 `Settings`。
2. 点击 `Developer settings`。
3. 点击 `Personal access tokens`。
4. 推荐选择 `Fine-grained tokens`，只授权 `6bang-courseware` 这个仓库。
5. 权限给 `Contents: Read-only`。如果仓库文件用了 Git LFS，也要确保 token 能读取仓库内容。
6. 生成 token 后，回到 `wechat-content-agent` 仓库。
7. 进入 `Settings` → `Secrets and variables` → `Actions`。
8. 新增 Secret：`COURSEWARE_REPO_TOKEN`，值粘贴刚生成的 token。

还需要新增这些 Secrets：

```text
ENABLE_COURSEWARE_CONTEXT=true
COURSEWARE_REFERENCE_PATHS=01_课程总纲,02_线下课课件,05_客户案例,06_销售素材,07_公众号素材
COURSEWARE_MAX_FILES=12
```

每天运行后会多生成一个文件：

```text
outputs/YYYY-MM-DD/courseware_reference.md
```

这个文件会列出本次 Agent 实际读取了哪些课件、提取了哪些参考内容。你检查文章是否“吃到课件”时，先看这个文件。

## 飞书机器人

在飞书群中添加自定义机器人，复制 Webhook。不要把 Webhook 写进代码，只能放在 `.env` 或 GitHub Secrets。

```env
ENABLE_FEISHU=true
ENABLE_FEISHU_STAGE_REPORT=true
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/...
```

飞书消息会包含“公众号”关键词，避免关键词安全设置拦截。发送失败只打印日志，不中断主流程。

如果群里已经拉了多个 Agent 机器人，可以给每个角色单独配置 Webhook：

```env
FEISHU_TOPIC_WEBHOOK_URL=选题策划Agent机器人Webhook
FEISHU_EDITOR_WEBHOOK_URL=内容主编Agent机器人Webhook
FEISHU_WRITER_WEBHOOK_URL=内容编辑Agent机器人Webhook
FEISHU_REVIEWER_WEBHOOK_URL=审稿Agent机器人Webhook
FEISHU_PUBLISHER_WEBHOOK_URL=新媒体运营Agent机器人Webhook
FEISHU_VISUAL_WEBHOOK_URL=视觉排版Agent机器人Webhook
FEISHU_CONTROLLER_WEBHOOK_URL=总控Agent机器人Webhook
```

汇报对应关系：

- 选题策划完成：`FEISHU_TOPIC_WEBHOOK_URL`
- 主编评估完成：`FEISHU_EDITOR_WEBHOOK_URL`
- 大纲完成、初稿完成：`FEISHU_WRITER_WEBHOOK_URL`
- 审稿定稿完成：`FEISHU_REVIEWER_WEBHOOK_URL`
- 发布包完成：`FEISHU_PUBLISHER_WEBHOOK_URL`
- 视觉排版完成：`FEISHU_VISUAL_WEBHOOK_URL`
- 今日内容包完成、最终汇总通知：`FEISHU_CONTROLLER_WEBHOOK_URL`

如果某个专属 Webhook 没配置，系统会自动退回 `FEISHU_WEBHOOK_URL`。

## 飞书协作文档

如果开启飞书文档，系统会在每天内容包生成后自动创建一份飞书文档，把以下内容写进去：

- 今日基础信息和人工确认发布规则
- C/E/S 三篇候选文章连续阅读版
- 每篇正文按公众号阅读节奏重新分段，尽量控制在手机端 3 行以内
- 可复制公众号正文会自动增加引言金句、分隔线、短段落、重点句加粗和留白
- 同步到公众号草稿箱时，会使用更适合微信阅读的标题、引用块、行高和段落间距
- 段落之间留一行空白，三篇文章之间留 5 行
- 发布包、视觉排版方案、配图素材和草稿箱同步命令放在文末索引，避免打断阅读

同时会在本地输出 `feishu_doc_preview.md`，方便你在 GitHub artifact 里预览飞书文档正文结构。

需要配置：

```env
ENABLE_FEISHU_DOC=true
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxx
FEISHU_DOC_FOLDER_TOKEN=fldcnxxxxxxxxxxxx
FEISHU_DOC_BASE_URL=https://your-company.feishu.cn
```

说明：

- `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 来自飞书开放平台的企业自建应用。
- `FEISHU_DOC_FOLDER_TOKEN` 是飞书文件夹链接里 `/folder/` 后面的那段 token。
- `FEISHU_DOC_BASE_URL` 是可选项，用于拼出文档链接，例如 `https://你的企业域名.feishu.cn`。如果飞书接口直接返回文档 URL，可以不配。
- 创建或写入飞书文档失败时，只打印日志并继续发送群通知，不中断主流程。
- 如果飞书文档创建成功，`feishu_message.md` 和飞书群最终通知里会带上文档链接。

## 飞书阶段汇报机制

飞书群被当作“公众号内容团队战情室”。每个 Agent 完成后都会汇报：

- 当前角色
- 当前任务
- 当前状态
- 本阶段摘要
- 交付文件
- 下一步动作

通知规则：

- `ENABLE_FEISHU=false`: 所有飞书通知都不发送。
- `ENABLE_FEISHU=true` 且 `ENABLE_FEISHU_STAGE_REPORT=true`: 发送阶段通知和最终汇总通知。
- `ENABLE_FEISHU=true` 且 `ENABLE_FEISHU_STAGE_REPORT=false`: 只发送最终汇总通知。

## 邮箱备份

开启邮箱备份：

```env
ENABLE_EMAIL=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_email_password_or_app_password
EMAIL_TO=receiver@example.com
```

邮件标题格式：`【公众号今日稿件】日期｜文章标题`。

附件包括：

- `wechat_ready_article.md`
- `final_article.md`
- `publish_package.md`
- `feishu_message.md`

邮件发送失败不会中断主流程。

## 公众号草稿箱同步

确认稿件后，可以在本地 Mac 把当天文章同步到公众号草稿箱。第一版只创建草稿，不自动发布。

需要先在 `.env` 配置：

```env
ENABLE_WECHAT_DRAFT=true
WECHAT_APP_ID=你的公众号AppID
WECHAT_APP_SECRET=你的公众号AppSecret
WECHAT_AUTHOR=老六
WECHAT_THUMB_MEDIA_ID=可选，已经上传过的封面素材media_id
WECHAT_COVER_IMAGE_PATH=assets/default_cover.jpg
WECHAT_CONTENT_SOURCE_URL=
ENABLE_WECHAT_RESOURCE_FOOTER=true
WECHAT_RESOURCE_FOOTER_TEXT=我这里整理一份合适品牌的打品的SOP流程\n\n如果你有需要可以找我
WECHAT_RESOURCE_IMAGE_PATHS=assets/brand_sop_flow_01.jpg,assets/brand_sop_flow_02.jpg,assets/brand_sop_flow_03.jpg,assets/brand_sop_flow_04.jpg
ENABLE_WECHAT_CONTACT_QR=true
WECHAT_CONTACT_QR_IMAGE_PATH=assets/wechat_contact_qr.jpg
```

封面图二选一：

- 推荐：配置 `WECHAT_THUMB_MEDIA_ID`，使用公众号素材库里已经上传过的封面素材。
- 或者：配置 `WECHAT_COVER_IMAGE_PATH`，脚本会先上传本地封面图，再创建草稿。

文章结尾会自动增加资料领取文案、打品 SOP 流程图和微信二维码。请把图片保存到：

```text
assets/brand_sop_flow_01.jpg
assets/brand_sop_flow_02.jpg
assets/brand_sop_flow_03.jpg
assets/brand_sop_flow_04.jpg
assets/wechat_contact_qr.jpg
```

默认结尾文案是：

```text
我这里整理一份合适品牌的打品的SOP流程

如果你有需要可以找我
```

如果只想保留文字，不想插图，把 `.env` 里的 `WECHAT_RESOURCE_IMAGE_PATHS` 清空即可；如果不想放二维码，把 `ENABLE_WECHAT_CONTACT_QR=false`。

先本地预检，不调用微信接口：

```bash
cd /Users/liuwenjun-15-air/Documents/New\ project\ 2/wechat-content-agent
source .venv/bin/activate
python src/sync_wechat_draft.py --date 2026-05-11 --layer C --dry-run
```

确认后同步到公众号草稿箱：

```bash
python src/sync_wechat_draft.py --date 2026-05-11 --layer C
```

把 `--layer C` 换成 `--layer E` 或 `--layer S`，就能同步对应层级的候选稿。如果不加 `--layer`，默认同步顶层主编推荐稿。

成功后会生成：

```text
outputs/2026-05-11/articles/C/wechat_draft_result.json
```

并在终端显示公众号草稿 `media_id`。如果开启飞书通知，也会向群里汇报“公众号草稿箱同步完成”。

注意：微信公众号接口通常需要 IP 白名单。最稳做法是把你 Mac 当前公网 IP 加到公众号后台白名单后，在本地执行同步命令。

## 企业微信远程控制

企业微信版本分成两件事：

- `企业微信群机器人汇报`：GitHub Actions 每个阶段完成后，把进度发到企业微信群。
- `企业微信自建应用接收指令`：你给“公众号远程控制 Agent”发一句话，它触发 GitHub Actions。

提醒一下：企业微信群里的普通自定义机器人通常只能“发消息到群”，不能“读取群里别人发的指令”。所以第一版最稳的方式是：在企业微信自建应用会话里发控制指令，在企业微信群里看阶段汇报。后续如果一定要监听群聊指令，需要做企业微信会话内容存档或更复杂的服务端方案。

已内置服务入口：

```bash
python src/remote/wecom_remote_control.py
```

支持的指令：

```text
重写今日三篇
只跑选题
主编评估
写大纲
写初稿
审稿
发布包
视觉排版
发C
发E
发S
2026-05-14 发C
帮助
```

推荐理解：

- `重写今日三篇`：触发完整 GitHub Actions 流水线，重新生成 C/E/S 三篇文章。
- `只跑选题`：只跑选题阶段。
- `发C / 发E / 发S`：触发 Actions 先生成当天内容，再同步对应层级到公众号草稿箱。

注意：`发C / 发E / 发S` 在 GitHub Actions 云端执行时，微信公众号后台也可能要求固定 IP 白名单。如果同步草稿箱失败，先用企业微信远程生成内容包，然后回到本地 Mac 执行 `python src/sync_wechat_draft.py --date 日期 --layer C/E/S` 会更稳。

### 企业微信后台设置

如果你只想先看企业微信群阶段汇报，先做“群机器人”即可：

1. 打开企业微信群。
2. 点右上角 `...`。
3. 选择 `群机器人`。
4. 添加一个自定义机器人，名字可以叫 `公众号内容流水线`。
5. 复制 Webhook。
6. 在 GitHub Secrets 里新增：
   - `ENABLE_WECOM_NOTIFY=true`
   - `WECOM_WEBHOOK_URL=刚复制的企业微信群机器人Webhook`

如果你还想“远程发指令”，继续做下面的自建应用：

1. 打开 [企业微信管理后台](https://work.weixin.qq.com/wework_admin/frame)。
2. 进入 `应用管理`。
3. 选择 `自建`，点击 `创建应用`。
4. 应用名称建议填：`公众号远程控制 Agent`。
5. 可见范围先选你自己，后面再加运营或主编。
6. 创建完成后，记录这三个值：
   - `企业ID`：在 `我的企业` → `企业信息` 里查看，对应 `WECOM_CORP_ID`。
   - `AgentId`：应用详情页里查看，对应 `WECOM_AGENT_ID`。
   - `Secret`：应用详情页里查看，对应 `WECOM_APP_SECRET`。
7. 在应用详情里找到 `接收消息` 或 `API接收消息`。
8. 设置 `URL`：填你部署后的公网地址，例如 `https://你的域名/wecom/callback`。
9. 设置 `Token`：自己填一串随机字符串，保存到 `WECOM_CALLBACK_TOKEN`。
10. 设置 `EncodingAESKey`：点击随机生成，保存到 `WECOM_ENCODING_AES_KEY`。
11. 点击保存。如果提示校验失败，说明你的远程服务还没启动、URL 不通，或者环境变量填错。

### 远程服务环境变量

企业微信回调服务需要部署在一个有公网 HTTPS 地址的地方，比如 Render、Railway、腾讯云、阿里云或一台固定服务器。不要部署在 GitHub Actions 里，GitHub Actions 只负责被触发后跑任务。

远程服务需要配置：

```env
ENABLE_WECOM_REMOTE_CONTROL=true
ENABLE_WECOM_NOTIFY=true
WECOM_WEBHOOK_URL=企业微信群机器人Webhook
WECOM_CORP_ID=你的企业ID
WECOM_AGENT_ID=你的应用AgentId
WECOM_APP_SECRET=你的应用Secret
WECOM_CALLBACK_TOKEN=你在企业微信后台填写的Token
WECOM_ENCODING_AES_KEY=企业微信后台生成的EncodingAESKey
WECOM_ALLOWED_USER_IDS=

GITHUB_OWNER=6bang
GITHUB_REPO=wechat-content-agent
GITHUB_WORKFLOW_FILE=daily_content.yml
GITHUB_DEFAULT_BRANCH=main
GITHUB_ACTIONS_TOKEN=你的GitHub远程触发token
```

`WECOM_ALLOWED_USER_IDS` 可以先留空，表示可见范围内的人都能发指令。后续想限制谁能控制，再填企业微信用户 ID，多个用英文逗号隔开。

`GITHUB_ACTIONS_TOKEN` 建议用 Fine-grained GitHub token：

1. GitHub 右上角头像 → `Settings`。
2. 进入 `Developer settings`。
3. 点击 `Personal access tokens` → `Fine-grained tokens`。
4. 只选择 `6bang/wechat-content-agent` 仓库。
5. 权限给：
   - `Actions: Read and write`
   - `Contents: Read-only`
6. 生成后只粘贴到远程服务环境变量里，不要写进代码。

### 本地测试企业微信服务

本地只能测试服务是否能启动，企业微信正式回调必须用公网 HTTPS 地址。

```bash
cd /Users/liuwenjun-15-air/Documents/New\ project\ 2/wechat-content-agent
source .venv/bin/activate
pip install -r requirements.txt
python src/remote/wecom_remote_control.py
```

浏览器打开：

```text
http://127.0.0.1:8080/healthz
```

看到 `{"status":"ok"}` 就说明服务启动正常。

### 企业微信群使用方式

1. 把自建应用配置到你能收到消息的范围。
2. 在企业微信里找到 `公众号远程控制 Agent` 这个应用。
3. 给这个应用发：`帮助`。
4. 如果服务配置正确，它会返回可用指令菜单。
5. 发：`重写今日三篇`。
6. GitHub Actions 会开始运行，飞书/企业微信群后续会看到阶段汇报。

如果你发现普通群里发 `帮助` 没反应，不是你设置错了，大概率是普通群机器人不能接收指令。先在“公众号远程控制 Agent”这个自建应用会话里发指令，企业微信群负责接收汇报。

## 对标公众号每日监控

系统可以每天盯 4 个对标公众号的最近一篇文章：

```text
笔记侠
罗辑思维
刘润
差评君
```

监控结果会输出到：

```text
outputs/competitor_monitor/YYYY-MM-DD/competitor_monitor.md
outputs/competitor_monitor/YYYY-MM-DD/competitor_monitor.json
```

如果开启飞书，会把报告发到飞书群。报告包括：

- 最新文章标题
- 发布时间
- 阅读数
- 点赞/喜欢数
- 分享数
- 评论数
- 选题角度
- 给六邦公众号的选题启发

重要说明：微信官方没有给普通开发者开放“读取别的公众号阅读数”的稳定接口。要自动获取阅读数，需要接入第三方数据源。当前项目已预留 `Just One API` 接入，使用其微信公众号“用户发布帖子”和“文章互动指标”接口。相关接口文档：[`用户发布帖子`](https://docs.justoneapi.com/zh/api/wechat-official-accounts/user-published-posts-v1)、[`文章互动指标`](https://docs.justoneapi.com/zh/api/wechat-official-accounts/article-engagement-metrics-v1)。

先在配置文件里补公众号微信号：

```text
config/competitor_accounts.yaml
```

里面的 `wxid` 要填公众号资料页里的“微信号”，不是显示名称。你可以在微信里打开公众号主页，点右上角资料页查看。

环境变量：

```env
ENABLE_COMPETITOR_MONITOR_FEISHU=true
COMPETITOR_MONITOR_PROVIDER=justoneapi
JUSTONE_API_KEY=你的JustOneAPIKey
JUSTONE_API_BASE=https://api.justoneapi.com
```

本地手动运行：

```bash
cd /Users/liuwenjun-15-air/Documents/New\ project\ 2/wechat-content-agent
source .venv/bin/activate
python src/monitor_competitors.py
```

指定日期：

```bash
python src/monitor_competitors.py --date 2026-05-15
```

如果暂时没有 API Key，系统也会生成报告，但阅读数会显示 `待获取`，并提示需要补 `JUSTONE_API_KEY` 或 `wxid`。这样不会影响主内容流水线。

GitHub Actions 文件：

```text
.github/workflows/competitor_monitor.yml
```

默认每天北京时间 10:00 运行，也支持手动运行。需要在 GitHub Secrets 增加：

```text
ENABLE_COMPETITOR_MONITOR_FEISHU
COMPETITOR_MONITOR_PROVIDER
JUSTONE_API_KEY
JUSTONE_API_BASE
```

## GitHub Actions

工作流文件：`.github/workflows/daily_content.yml`。

- 每天北京时间 01:00 自动运行
- GitHub cron 使用 UTC，所以配置为 `0 17 * * *`
- 支持 `workflow_dispatch` 手动运行
- 使用 `ubuntu-latest` 和 Python 3.11
- 运行 `python src/main.py`
- 上传当天 `outputs/YYYY-MM-DD/` 作为 artifact
- 企业微信远程控制会通过 `workflow_dispatch` 传入 `action`、`stage`、`layer` 参数
- 如果配置 `ENABLE_WECOM_NOTIFY=true` 和 `WECOM_WEBHOOK_URL`，也会把阶段汇报发到企业微信群

需要配置 GitHub Secrets：

```text
OPENAI_API_KEY
USE_MOCK
MODEL
ENABLE_FEISHU
ENABLE_FEISHU_STAGE_REPORT
FEISHU_WEBHOOK_URL
FEISHU_TOPIC_WEBHOOK_URL
FEISHU_EDITOR_WEBHOOK_URL
FEISHU_WRITER_WEBHOOK_URL
FEISHU_REVIEWER_WEBHOOK_URL
FEISHU_PUBLISHER_WEBHOOK_URL
FEISHU_VISUAL_WEBHOOK_URL
FEISHU_CONTROLLER_WEBHOOK_URL
ENABLE_FEISHU_DOC
FEISHU_APP_ID
FEISHU_APP_SECRET
FEISHU_DOC_FOLDER_TOKEN
FEISHU_DOC_BASE_URL
ENABLE_EMAIL
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
EMAIL_TO
ENABLE_COURSEWARE_CONTEXT
COURSEWARE_REPO_TOKEN
COURSEWARE_REFERENCE_PATHS
COURSEWARE_MAX_FILES
ENABLE_WECHAT_DRAFT
WECHAT_APP_ID
WECHAT_APP_SECRET
WECHAT_AUTHOR
WECHAT_THUMB_MEDIA_ID
WECHAT_COVER_IMAGE_PATH
WECHAT_CONTENT_SOURCE_URL
ENABLE_WECOM_NOTIFY
WECOM_WEBHOOK_URL
```

手动运行方式：

1. 打开 GitHub 仓库页面。
2. 点击 `Actions`。
3. 选择 `Daily WeChat Content Agent`。
4. 点击 `Run workflow`。
5. 可选填写 `run_date`，不填则使用北京时间当天。
6. `action` 默认选 `daily_pipeline`。
7. `stage` 默认选 `all`，也可以选 `topics/editor/outline/draft/review/publish/visual`。
8. 如果 `action` 选 `sync_wechat_draft`，再选择 `layer` 为 `C/E/S`。
9. 运行成功后，在 Summary 里下载 artifact 查看稿件。

## 人工确认发布

第一阶段不要自动发布公众号。原因：

- 微信后台适合人工排版和最终确认
- 飞书更适合协作审稿和留痕
- 自动发布风险高，容易绕过老板或主编确认

人工流程：

1. 系统生成 C/E/S 三篇候选文章和对应发布包
2. 系统创建飞书协作文档，并把链接发到飞书群
3. 飞书群收到“今日内容包完成”
4. 主编在飞书文档里检查三篇稿件并回复 `发C / 发E / 发S / 修改`
5. 本地运行 `python src/sync_wechat_draft.py --date YYYY-MM-DD --layer C/E/S` 同步被选中的稿件到公众号草稿箱
6. 运营进入公众号后台检查排版并回复 `已排版 / 待排版`
7. 老板或主编回复 `可发 / 暂缓`
8. 运营人工发布

## 测试

```bash
python3 -m pytest -q
```

测试覆盖：

- daily pipeline 能生成完整输出目录
- 每日顶层文件和 C/E/S 三篇候选稿文件存在
- 周一到周日栏目编号分别返回 C1/E1/S1/E2/S2/C2/E3

## 后续升级方向

- 增加固定 IP 云服务器，稳定执行公众号草稿箱同步
- 增加行业热点抓取和同行爆文选题池
- 增加次日 09:00 数据复盘
- 把优秀文章沉淀为课程案例库、销售跟进素材和朋友圈长图
