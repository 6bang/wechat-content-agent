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
```

封面图二选一：

- 推荐：配置 `WECHAT_THUMB_MEDIA_ID`，使用公众号素材库里已经上传过的封面素材。
- 或者：配置 `WECHAT_COVER_IMAGE_PATH`，脚本会先上传本地封面图，再创建草稿。

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

## GitHub Actions

工作流文件：`.github/workflows/daily_content.yml`。

- 每天北京时间 01:00 自动运行
- GitHub cron 使用 UTC，所以配置为 `0 17 * * *`
- 支持 `workflow_dispatch` 手动运行
- 使用 `ubuntu-latest` 和 Python 3.11
- 运行 `python src/main.py`
- 上传当天 `outputs/YYYY-MM-DD/` 作为 artifact

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
ENABLE_WECHAT_DRAFT
WECHAT_APP_ID
WECHAT_APP_SECRET
WECHAT_AUTHOR
WECHAT_THUMB_MEDIA_ID
WECHAT_COVER_IMAGE_PATH
WECHAT_CONTENT_SOURCE_URL
```

手动运行方式：

1. 打开 GitHub 仓库页面。
2. 点击 `Actions`。
3. 选择 `Daily WeChat Content Agent`。
4. 点击 `Run workflow`。
5. 可选填写 `run_date`，不填则使用北京时间当天。
6. 运行成功后，在 Summary 里下载 artifact 查看稿件。

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
