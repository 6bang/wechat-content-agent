# wechat-content-agent

`wechat-content-agent` 是一个课程咨询型微信公众号内容自动化生产系统，服务电商咨询、管理课程和企业服务业务。

它不是普通写稿工具。第一阶段只负责每天自动生成内容包、飞书群阶段汇报、邮箱备份和 GitHub Actions 定时运行；最终公众号发布必须由主编、老板或运营人工确认后执行。

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

每天生成 3 个候选选题，但每天只选择 1 个主选题成稿。

- 周一 `C1` 老板认知课
- 周二 `E1` 电商老板观察
- 周三 `S1` SOP流程课
- 周四 `E2` 电商团队管理
- 周五 `S2` 流程工具箱
- 周六 `C2` 商业案例拆解
- 周日 `E3` 一周电商复盘

## Agent 分工

- `选题策划 Agent`: 生成 C/E/S 三层候选选题。
- `内容主编 Agent`: 按评分模型评估 3 个选题，选出今日主选题。
- `内容编辑 Agent`: 生成文章大纲和公众号初稿。
- `审稿 Agent`: 从标题、开头、逻辑、案例、方法、专业度、转化和风险角度审稿定稿。
- `新媒体运营 Agent`: 生成标题、摘要、封面、朋友圈、社群、私聊、评论区问题和复盘模板。
- `总控 Agent / daily_pipeline`: 串联全流程，保存 outputs，触发飞书与邮箱通知。

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

第一版每天北京时间早上 6 点一次性跑完整流程：

1. 读取品牌配置和一周内容日历
2. 根据当天星期确定栏目编号
3. 生成 C/E/S 三个候选选题
4. 飞书汇报：选题策划完成
5. 主编评估并选出主选题
6. 飞书汇报：主编评估完成
7. 生成文章大纲
8. 飞书汇报：文章大纲完成
9. 生成公众号初稿
10. 飞书汇报：公众号初稿完成
11. 审稿并生成终稿
12. 飞书汇报：审稿定稿完成
13. 生成发布包
14. 飞书汇报：发布包完成
15. 生成 `wechat_ready_article.md`、`feishu_message.md`、`email_summary.md`
16. 飞书汇报：今日内容包完成
17. 如果开启邮箱，发送邮箱备份
18. GitHub Actions 上传 `outputs/` artifact
19. 等待人工确认发布

## 输出文件

每天会在 `outputs/YYYY-MM-DD/` 下生成：

```text
topics.json
topics.md
selected_topic.md
draft.md
review.md
final_article.md
wechat_ready_article.md
publish_package.md
feishu_message.md
email_summary.md
run_summary.json
```

其中 `wechat_ready_article.md` 只包含最终公众号正文，方便运营复制到公众号后台；`final_article.md` 保留审稿结论和终稿完整记录。

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

## GitHub Actions

工作流文件：`.github/workflows/daily_content.yml`。

- 每天北京时间 06:00 自动运行
- GitHub cron 使用 UTC，所以配置为 `0 22 * * *`
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
ENABLE_EMAIL
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
EMAIL_TO
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

1. 系统生成 `wechat_ready_article.md` 和 `publish_package.md`
2. 飞书群收到“今日内容包完成”
3. 主编检查终稿并回复 `通过 / 修改`
4. 运营复制正文到公众号后台并回复 `已排版 / 待排版`
5. 老板或主编回复 `可发 / 暂缓`
6. 运营人工发布

## 测试

```bash
python3 -m pytest -q
```

测试覆盖：

- daily pipeline 能生成完整输出目录
- 11 个每日输出文件存在
- 周一到周日栏目编号分别返回 C1/E1/S1/E2/S2/C2/E3

## 后续升级方向

- 自动创建飞书文档并写入正文和发布包
- 接入公众号草稿箱，但仍保留人工确认发布
- 增加行业热点抓取和同行爆文选题池
- 增加次日 09:00 数据复盘
- 把优秀文章沉淀为课程案例库、销售跟进素材和朋友圈长图
