from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ContentTopic, PublishPackage, ReviewResult, VisualAsset, VisualLayoutPackage, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class VisualDesignerAgent:
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def design_layout(
        self,
        topic: ContentTopic,
        review: ReviewResult,
        package: PublishPackage,
    ) -> VisualLayoutPackage:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号视觉排版 Agent。",
            json.dumps(
                {
                    "topic": to_serializable(topic),
                    "review": to_serializable(review),
                    "publish_package": to_serializable(package),
                    "task": "根据定稿文章和发布包，生成公众号视觉排版方案与配图清单。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

        return VisualLayoutPackage(
            title=review.final_title,
            selected_layer=topic.layer,
            cover_direction=self._cover_direction(topic, review),
            article_tone=self._article_tone(topic),
            typography_rules=self._typography_rules(),
            color_rules=self._color_rules(topic),
            section_layout=self._section_layout(topic),
            visual_assets=self._visual_assets(topic, review, package),
            feishu_doc_notes=self._feishu_doc_notes(),
            wechat_layout_notes=self._wechat_layout_notes(),
            image_generation_notes=self._image_generation_notes(),
        )

    def _cover_direction(self, topic: ContentTopic, review: ReviewResult) -> str:
        return (
            f"封面突出「{review.final_title}」的核心冲突，画面以电商老板、团队看板、流程节点为主，"
            "不要做抽象渐变和营销感大字报。"
        )

    def _article_tone(self, topic: ContentTopic) -> str:
        if topic.layer == "C":
            return "老板认知型：留白多一点，用商业观察和经营系统感承接破圈阅读。"
        if topic.layer == "E":
            return "行业痛点型：突出电商团队真实场景、岗位协作和老板管理焦虑。"
        return "专业工具型：突出SOP、表格、检查清单和流程看板，让读者感觉能直接拿去用。"

    def _typography_rules(self) -> list[str]:
        return [
            "标题控制在两行以内，突出冲突词和老板痛点。",
            "正文每段 2-4 行，关键金句单独成段并加粗。",
            "二级小标题使用问题式表达，例如“为什么爆款不能复制”。",
            "方法部分用编号清单，避免大段连续论述。",
            "案例和方法之间插入图表，降低手机阅读压力。",
        ]

    def _color_rules(self, topic: ContentTopic) -> list[str]:
        base = {
            "C": "深墨色 + 暖金色 + 米白底，强调经营认知和老板视角。",
            "E": "深蓝灰 + 橙色提示 + 浅灰底，强调行业问题和团队管理。",
            "S": "深绿色 + 蓝色数据线 + 白底，强调SOP、流程和工具感。",
        }
        return [
            base.get(topic.layer, "深灰 + 品牌辅助色 + 白底，保持专业克制。"),
            "整篇不要只用单一颜色，重点信息用同一种强调色。",
            "工具表和流程图保持低饱和背景，避免像促销海报。",
        ]

    def _section_layout(self, topic: ContentTopic) -> list[str]:
        return [
            "开头痛点场景后放一张“问题地图”或“老板忙乱场景图”。",
            "讲原因时放流程断点图，说明问题不是单个员工造成的。",
            "讲方法时放知识库、多维表、流程看板三件套图。",
            "讲案例时放前后对比图：靠人盯人 vs 靠系统推进。",
            "结尾放领取资料/流程诊断表卡片，二维码区域留白。",
        ]

    def _visual_assets(
        self,
        topic: ContentTopic,
        review: ReviewResult,
        package: PublishPackage,
    ) -> list[VisualAsset]:
        return [
            VisualAsset(
                filename="cover.svg",
                asset_type="封面主视觉",
                title="公众号封面图",
                purpose="提高打开率，让老板一眼看懂文章冲突。",
                placement="公众号封面，不放入正文；飞书文档顶部展示。",
                prompt=(
                    f"为课程咨询型公众号生成封面，主题《{review.final_title}》，"
                    "画面包含电商老板、团队协作看板、流程节点，专业、克制、有管理感。"
                ),
                caption=f"{topic.layer}层内容｜给电商老板的管理提醒",
                alt_text=f"{review.final_title}封面图",
                notes="封面不要堆太多文字，主标题优先使用发布包中的封面主标题。",
            ),
            VisualAsset(
                filename="problem_map.svg",
                asset_type="问题地图",
                title="老板看到的是结果，系统暴露的是断点",
                purpose="把文章开头的痛点变成一张可视化问题图。",
                placement="插入在开头痛点场景之后。",
                prompt=(
                    "生成电商团队问题地图：老板救火、运营卡点、客服反馈、美工返工、数据复盘缺失，"
                    "用清晰节点表达问题断点。"
                ),
                caption="很多管理问题，表面是人不行，底层是流程断点没有被看见。",
                alt_text="电商团队管理问题地图",
                notes="适合做成横向流程断点图，手机端宽度不要超过正文宽度。",
            ),
            VisualAsset(
                filename="process_map.svg",
                asset_type="流程图",
                title="从经验到SOP的转化路径",
                purpose="解释文章核心方法，让读者看到经验如何变成流程资产。",
                placement="插入在方法部分第一段之后。",
                prompt=(
                    "生成电商SOP流程图：经验复盘、字段拆解、标准动作、责任人、数据看板、复盘更新，"
                    "形成闭环。"
                ),
                caption="SOP不是文件夹，而是经验、标准、执行和复盘之间的闭环。",
                alt_text="电商SOP流程闭环图",
                notes="用 5-6 个节点即可，不要画成复杂流程系统。",
            ),
            VisualAsset(
                filename="dashboard_table.svg",
                asset_type="多维表 / 看板示意图",
                title="运营过程看板示意",
                purpose="增强工具感，让运营知道文章不是只讲观点。",
                placement="插入在“知识库 + 多维表 + 流程可视化”段落之后。",
                prompt=(
                    "生成电商运营多维表看板示意图，字段包含产品、负责人、阶段、关键数据、异常、下一步动作、复盘结论。"
                ),
                caption="把流程接到日常看板，老板才能从“问人”变成“看系统”。",
                alt_text="电商运营多维表看板",
                notes="可以用表格截图风格，但内容必须原创，不复制任何真实客户数据。",
            ),
            VisualAsset(
                filename="checklist_card.svg",
                asset_type="检查清单",
                title="老板今天可以先查这5件事",
                purpose="把文章结尾的方法变成可执行行动建议。",
                placement="插入在结尾转化前。",
                prompt=(
                    "生成老板检查清单卡片：流程是否有负责人、标准是否清楚、数据是否更新、异常是否记录、复盘是否反哺模板。"
                ),
                caption="先不用全公司做SOP，先把最痛的一条流程查清楚。",
                alt_text="电商老板流程检查清单",
                notes="适合朋友圈二次分发，也适合放进销售跟进素材。",
            ),
            VisualAsset(
                filename="cta_card.svg",
                asset_type="资料领取 / 咨询引导卡",
                title="领取电商流程诊断表",
                purpose="承接文章转化，引导私域咨询或资料领取。",
                placement="文章最后，互动问题之后。",
                prompt=(
                    "生成课程咨询型公众号结尾引导卡，主题是领取电商流程诊断表，预留二维码位置，"
                    "语气专业克制，不夸大承诺。"
                ),
                caption="想先知道团队最该标准化哪条流程，可以从一张诊断表开始。",
                alt_text="电商流程诊断表领取卡",
                notes="二维码由运营在公众号后台人工替换，不在自动化里生成个人微信二维码。",
            ),
        ]

    def _feishu_doc_notes(self) -> list[str]:
        return [
            "飞书文档按“选题-定稿-视觉排版-发布包”顺序排布，方便主编审稿。",
            "每篇文章的视觉排版方案放在对应文章发布包后面。",
            "图片文件路径要保留，运营可下载 SVG 或按提示词重新生成位图。",
            "主编确认稿件后，运营再决定是否把 SVG 转成 PNG/JPG 后上传公众号后台。",
        ]

    def _wechat_layout_notes(self) -> list[str]:
        return [
            "公众号后台正文先复制 wechat_ready_article.md，再按 visual_layout.md 插图。",
            "每个大段之间最多插入 1 张图，避免图片过密影响阅读。",
            "工具图放在方法段，检查清单放在结尾前，二维码卡放在最后。",
            "同步草稿箱后仍需人工检查图片、封面、摘要和手机端预览。",
        ]

    def _image_generation_notes(self) -> list[str]:
        return [
            "第一版自动生成原创 SVG 示意图，适合飞书审稿和排版参考。",
            "如果要做更精致的封面图，可以把 visual_layout.md 里的提示词交给设计工具或图片生成模型。",
            "实际公众号发布前，运营需要确认图片尺寸、二维码、品牌标识和版权安全。",
        ]
