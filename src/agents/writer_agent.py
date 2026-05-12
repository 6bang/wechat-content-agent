from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ArticleDraft, ContentTopic, EditorialDecision, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class WriterAgent:
    courseware_context: dict[str, object] | None = None
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def write_article(self, decision: EditorialDecision) -> ArticleDraft:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号内容编辑。",
            json.dumps(
                {
                    "decision": to_serializable(decision),
                    "courseware_context": self._courseware_prompt_context(),
                    "task": "根据主编确定的选题生成文章大纲和公众号正文。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        topic = decision.selected_topic
        outline = self._build_outline(topic)
        body = self._build_body(topic, outline, decision.editor_note)
        return ArticleDraft(
            title=decision.final_title_suggestion,
            article_type=decision.article_positioning,
            target_user=decision.target_user,
            core_pain=topic.user_pain,
            core_point=topic.core_point,
            opening_hook=topic.opening_hook,
            outline=outline,
            case_design={
                "案例背景": topic.case_direction,
                "案例冲突": topic.user_pain,
                "案例结果": "团队通过岗位流程、操作步骤、数据评估和复盘机制降低试错成本，产出更稳定。",
                "案例启发": "管理不是靠老板更忙，而是靠流程让团队重复做对动作。",
            },
            golden_sentences=[
                "不是员工不努力，而是公司没有标准动作。",
                "老板越忙，不一定代表公司越好，可能说明系统越弱。",
                "流程不是把人管死，而是让普通人也能做出稳定结果。",
                "管理的终点，不是老板更勤奋，而是团队能自动运转。",
                "SOP不是写给老板看的，而是写给团队重复执行的。",
                "先找流程，再找方法，最后找人跑。",
            ],
            full_draft=body,
            ending_cta="如果你也想梳理店铺运营流程，可以私信关键词「诊断」，先从一个核心流程开始拆。",
            topic=topic,
        )

    def _courseware_prompt_context(self) -> dict[str, object]:
        context = self.courseware_context or {}
        return {
            "enabled": context.get("enabled", False),
            "available": context.get("available", False),
            "files": [item.get("path", "") for item in context.get("files", [])],
            "summary": context.get("summary", ""),
        }

    def write_draft(self, topic: ContentTopic) -> dict[str, str]:
        decision = EditorialDecision(
            scoring_table={},
            selected_topic=topic,
            selection_reason="兼容旧调用。",
            article_positioning="方法论干货型",
            target_user=topic.target_user,
            writing_direction="保持结构清晰，给出可执行建议。",
            avoid_direction="不要写成泛泛观点文。",
            must_include_points=["痛点", "方法", "案例"],
            conversion_suggestion=topic.suitable_product,
            final_title_suggestion=topic.title,
        )
        draft = self.write_article(decision)
        return {"title": draft.title, "body": draft.body}

    def _build_outline(self, topic: ContentTopic) -> list[str]:
        outline = [
            "开头: 用一个电商老板熟悉的管理困境切入",
            f"观点: {topic.core_insight}",
            f"痛点: {topic.pain_point}",
            "拆解: 问题为什么不是单点动作能解决",
            "方法: 给出 3 个可执行管理动作",
            "案例: 用一个电商团队的真实管理场景讲透",
            "金句: 用一句老板能记住的话收住观点",
            "结尾: 用低压力方式引导留言或私信咨询",
        ]
        if self._has_courseware_context():
            outline.insert(4, "课程方法框架: 先找流程，再找方法，最后找人跑；用 S/A/B/C 标准评估过程结果")
        return outline

    def _build_body(self, topic: ContentTopic, outline: list[str], editor_note: str) -> str:
        pain_point = clean_sentence(topic.pain_point)
        core_insight = clean_sentence(topic.core_insight)
        case_direction = clean_sentence(topic.case_direction)
        return "\n\n".join(
            [
                f"# {topic.title}",
                "## 一、我见过很多电商团队，真正的差距不在单点能力",
                (
                    "这几年我看过很多电商团队，有一个现象特别明显："
                    "第一个结果，经常是靠人拼出来的；第二个结果，很多公司就复制不出来了。"
                    f"这背后对应到今天的选题，就是：{pain_point}。"
                ),
                (
                    "很多老板也会说，我们也总结了经验，我们也做了复盘，我们也有 SOP。"
                    "但一换人，动作就变形；一换品，打法就重来；一换平台节奏，团队又开始问老板怎么办。"
                    "这时候问题就不是有没有经验，而是经验有没有被做成系统。"
                ),
                (
                    "真正厉害的团队，不是每个人都特别强，而是普通人进来以后，也知道第一步做什么、第二步交付什么、异常情况找谁处理。"
                    "这篇文章不讲虚的，我们就拆一个问题：为什么赚钱的电商团队，最后都要做流程化。"
                ),
                "## 二、表面是执行问题，背后是系统问题",
                (
                    "你以为的问题，可能是运营能力不行。"
                    "但真正的问题往往是：没有一套能跑起来的流程系统。"
                    "运营不是不想做好，而是很多关键动作没有被拆成标准，没有被写进工具，也没有被老板看见。"
                ),
                (
                    f"{core_insight}。"
                    "如果目标只停留在一句“这个月把销售额做起来”，团队只能靠经验猜。"
                    "有经验的人能猜对一部分，新人猜不对，跨岗位的人更猜不对。"
                ),
                (
                    "很多老板真正累的地方，不是工作量大，而是所有判断都堆在自己身上。"
                    "老板脑子里有标准，团队手上没有标准；老板知道哪里不对，员工不知道下一步怎么改。"
                    "时间一长，公司就形成一种隐形依赖：凡是重要的事，都等老板给答案。"
                ),
                "## 三、爆款为什么不能复制",
                (
                    "很多团队做出一个爆款以后，会以为自己已经掌握方法了。"
                    "但等到下一个品再来一遍，发现还是靠同一个运营、同一个美工、同一个老板盯着跑。"
                    "这就说明，公司记住的是结果，没有沉淀过程。"
                ),
                (
                    "本质上，很多公司没有结构化知识，只有碎片经验。"
                    "运营知道这个品当时怎么推，美工知道那张图为什么好，老板知道当时怎么拍板。"
                    "但这些经验分散在聊天记录、会议纪要、个人脑子和临时表格里。"
                ),
                (
                    "没有结构化知识，就很难复制。"
                    "因为复制不是复制一句“这个品当时投得不错”，而是复制从选品、测图、上架、投放、优化到复盘的整套过程。"
                    "爆款可复制，靠的不是人，而是流程。"
                ),
                "## 四、一个真实场景：3个运营能打爆款，但团队复制不出来",
                (
                    f"我们用一个典型场景来讲。{case_direction}。"
                    "这家公司销售体量不算小，团队里也有几个能力不错的运营。"
                    "问题是，某个运营能做出来，换一个人就做不出来；这个品能跑出来，换一个品又要从头摸索。"
                ),
                (
                    "老板一开始觉得是招人问题，后来发现不是。"
                    "真正的问题是公司没有把“打爆款的过程”拆出来。"
                    "选品怎么选、测图怎么测、点击率多少算合格、转化率低了怎么优化、投流怎么分阶段加预算，都没有形成统一记录。"
                ),
                (
                    "后来我们帮他们做的不是换人，也不是再开几次培训。"
                    "而是把打爆款这件事拆成最小作战单元：每一步有 SOP、有记录、有复盘。"
                    "这样新人不是听老员工讲故事，而是照着流程看动作、看标准、看数据。"
                ),
                "## 五、核心方法：先找流程，再找方法，最后找人跑",
                (
                    "第一，找流程。"
                    "不要一上来就写一大本制度，而是先把一个岗位每天到底怎么交付拆清楚。"
                    "按一线项目里的落地方法，可以从主题开始拆到一级流程、二级流程、操作步骤，再补上数据评估。"
                ),
                (
                    "第二，找方法。"
                    "流程不是把动作写下来就结束了，还要找出现在最有效的方法。"
                    "先盘点团队目前跑得通的方法，再看市场上有没有更好的方法，最后用 AB 测试验证，留下效率最高、结果最稳的做法。"
                ),
                (
                    "第三，找人跑。"
                    "SOP 不是办公室里憋出来的，必须让业务里最会打仗的人先跑出来。"
                    "我们把这种人叫“兵王”：他先把方法跑通，再把过程梳理成 SOP，然后带人跑，最后换人也能跑。"
                ),
                (
                    "最后再加一套 S/A/B/C 评估标准。"
                    "S 是超出预期，A 是优秀，B 是合格，C 是不合格。"
                    "没有这个标准，流程就只是一张纸；有了标准，主管才知道怎么检查，员工才知道做到什么程度算过关。"
                ),
                (
                    "比如仓库流程，不要只写“负责发货”。"
                    "要拆成打单、拣货、验货、打包、快递分区揽收，每一步写清时间要求、责任人、异常处理和合格标准。"
                    "客服流程也一样，不是只要求“服务好客户”，而是看询单转化率、响应时间、销售过程和话术库。"
                ),
                "## 六、为什么一定要拆成最小作战单元",
                (
                    "所谓最小作战单元，就是把一个大动作拆到团队可以直接执行。"
                    "比如“做好选品”太大，员工不知道从哪下手。"
                    "但拆成类目趋势、竞品销量、差评痛点、价格带、供应链稳定性、毛利空间，动作就清楚了。"
                ),
                (
                    "再比如“优化转化率”也太大。"
                    "拆开以后，可能是主图点击、详情页首屏、评价结构、客服话术、价格利益点、赠品组合。"
                    "每个小动作都能被检查，每个小动作都有数据反馈。"
                ),
                (
                    "流程化的关键，不是把流程画出来，而是把路跑出来。"
                    "选品、拍摄、上架、投流、优化、复盘，每一步都要有负责人、当前进度、数据表现。"
                    "这些全部在一张表里实时更新，老板才不用靠问人来掌握业务。"
                ),
                "## 七、最后结果是什么",
                (
                    "第一，新人可以上手。"
                    "新人进来以后，不再靠老员工口头带，也不是先坐在那里看资料。"
                    "他可以顺着流程看：今天负责哪一步，标准是什么，交付物是什么，异常怎么处理。"
                ),
                (
                    "第二，爆款可以识别和复制。"
                    "过去是一个人做出一个爆款，现在是团队知道爆款是怎么跑出来的。"
                    "哪些动作有效，哪些数据达标，哪些节点踩坑，都会沉淀下来。"
                ),
                (
                    "第三，老板能看懂全局。"
                    "老板不需要每天追着问人，也不用等月底才知道结果。"
                    "过程数据在表里，卡点在看板里，复盘在知识库里。"
                    "管理就从“问人”变成“看系统”。"
                ),
                "## 八、给老板的三个动作，今天就能开始",
                (
                    "第一个动作，先选一条最痛的流程。"
                    "不要一上来全公司做 SOP，先从上新、打品、客服差评、运营复盘里选一个最痛的。"
                    "痛点越具体，越容易落地。"
                ),
                (
                    "第二个动作，把成功经验写成字段。"
                    "不要只写“这个品当时做得好”，而要写清楚为什么好：卖点、素材、投放、价格、评价、库存、复盘。"
                    "字段越清楚，经验越容易被复制。"
                ),
                (
                    "第三个动作，把流程接到日常看板。"
                    "如果 SOP 只存在文档里，它迟早会被忘掉。"
                    "只有接到每天的工作台，接到负责人和数据，流程才会真的跑起来。"
                ),
                f"主编提示：{editor_note}",
                (
                    "如果你现在 SOP 写了但团队不执行，多店铺管理混乱，爆款靠人、复制不了，那你缺的可能不是努力。"
                    "你缺的是一套知识库、流程表和可视化看板组成的流程系统。"
                    "如果你需要，可以私信关键词「流程表」，先领一份电商运营流程诊断表，从一条流程开始改。"
                ),
            ]
        )

    def _has_courseware_context(self) -> bool:
        context = self.courseware_context or {}
        return bool(context.get("available") and context.get("summary"))


def clean_sentence(text: str) -> str:
    return text.strip().rstrip("。.!！?？；;，,、")
