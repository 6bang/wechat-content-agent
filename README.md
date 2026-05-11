# wechat-content-agent

面向“电商运营课程咨询类微信公众号”的自动化内容生产项目骨架。

项目服务对象是电商老板、电商运营负责人、电商管理者。内容策略分为三层：

- `C层`: 泛流量内容，参考刘润、金错刀、创业黑马，讲企业家故事、企业经营、商业认知。
- `E层`: 行业流量内容，参考派代网、第一财经电商内容，讲电商行业、电商老板、电商运营、电商管理。
- `S层`: 专业转化内容，讲电商 SOP、流程化组织、目标管理、绩效激励、流程工具。

## 工作流

1. `TopicAgent` 每天生成 3 个选题，分别对应 C 层、E 层、S 层。
2. `EditorInChiefAgent` 从 3 个选题中评估出 1 个今日主选题。
3. `WriterAgent` 根据主选题生成文章大纲和公众号正文。
4. `ReviewerAgent` 修改、审核并产出定稿。
5. `OperationsAgent` 生成发布包：标题、摘要、封面文案、朋友圈文案、社群文案、私聊话术和评论区互动问题。
6. `DailyPipeline` 将过程产物保存到 `outputs/`。

## 每日定时节奏

```bash
python3 src/main.py --stage topics   # 06:00 选题
python3 src/main.py --stage editor   # 08:00 主编评估
python3 src/main.py --stage outline  # 09:00 写大纲
python3 src/main.py --stage draft    # 10:00 写初稿
python3 src/main.py --stage review   # 11:00 审稿
python3 src/main.py --stage publish  # 12:00 发布包
```

## 目录结构

```text
wechat-content-agent/
├── README.md
├── .env.example
├── requirements.txt
├── config/
│   ├── brand.yaml
│   ├── content_layers.yaml
│   ├── schedule.yaml
│   └── content_calendar.yaml
├── prompts/
│   ├── topic_agent.md
│   ├── editor_in_chief_agent.md
│   ├── writer_agent.md
│   ├── reviewer_agent.md
│   └── operations_agent.md
├── src/
│   ├── main.py
│   ├── agents/
│   ├── models/
│   ├── notify/
│   ├── workflow/
│   ├── storage/
│   └── utils/
├── outputs/
│   ├── topics/
│   ├── outlines/
│   ├── drafts/
│   ├── reviews/
│   ├── final/
│   └── publish_package/
└── tests/
```

## 快速开始

```bash
cd wechat-content-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 src/main.py
```

## LLM 配置

默认使用 mock 模式，方便本地测试：

```env
USE_MOCK=true
```

如需调用真实 OpenAI API，在 `.env` 中配置：

```env
USE_MOCK=false
OPENAI_API_KEY=你的 API Key
OPENAI_MODEL=gpt-4.1-mini
```

## 飞书通知

发布包阶段会生成 `outputs/YYYY-MM-DD/feishu_message.md`。只有满足以下条件时，系统才会把该文件内容发送到飞书群机器人：

```env
ENABLE_FEISHU=true
ENABLE_FEISHU_STAGE_REPORT=true
FEISHU_WEBHOOK_URL=你的飞书群机器人 Webhook
```

注意事项：

- `ENABLE_FEISHU` 未配置或不是 `true` 时，不发送飞书。
- `ENABLE_FEISHU_STAGE_REPORT=false` 时，只发送最终汇总通知，不发送每个 Agent 的阶段汇报。
- `FEISHU_WEBHOOK_URL` 只能通过环境变量或 GitHub Secrets 提供，不要写进代码。
- 飞书消息内容会包含“公众号”关键词，避免群机器人关键词安全设置拦截。
- 飞书发送失败只打印日志，不会中断主流程。

GitHub Actions 中请配置以下 Secrets：

```text
ENABLE_FEISHU=true
ENABLE_FEISHU_STAGE_REPORT=true
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/...
```

如果要调用真实 OpenAI，也需要配置：

```text
OPENAI_API_KEY=你的 API Key
```

## 飞书阶段汇报机制

每个 Agent 完成后都会向飞书群汇报一次，让飞书群变成“公众号内容团队战情室”。阶段汇报会包含当前角色、当前任务、当前状态、交付文件和下一步动作。

默认通知规则：

- `ENABLE_FEISHU=false`：所有飞书通知都不发送。
- `ENABLE_FEISHU=true` 且 `ENABLE_FEISHU_STAGE_REPORT=true`：发送每个阶段通知和最终汇总通知。
- `ENABLE_FEISHU=true` 且 `ENABLE_FEISHU_STAGE_REPORT=false`：只发送最终汇总通知。

如果不想每个阶段都通知，在 `.env` 或 GitHub Secrets 中设置：

```env
ENABLE_FEISHU_STAGE_REPORT=false
```

如果使用 GitHub Actions，请在 GitHub Secrets 中增加：

```text
ENABLE_FEISHU_STAGE_REPORT=true
```

## 测试

```bash
python3 -m pytest tests
```

当前代码是可运行骨架，默认使用规则和模板生成内容；后续可以在 `src/utils/llm.py` 中接入真实 LLM。
