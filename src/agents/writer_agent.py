from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ArticleDraft, ContentTopic, EditorialDecision, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class WriterAgent:
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def write_article(self, decision: EditorialDecision) -> ArticleDraft:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号内容编辑。",
            json.dumps(
                {
                    "decision": to_serializable(decision),
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
                "案例结果": "团队通过流程、目标和检查点降低试错成本，产出更稳定。",
                "案例启发": "管理不是靠老板更忙，而是靠系统让团队重复做对动作。",
            },
            golden_sentences=[
                "不是员工不努力，而是公司没有标准动作。",
                "老板越忙，不一定代表公司越好，可能说明系统越弱。",
                "流程不是把人管死，而是让普通人也能做出稳定结果。",
                "管理的终点，不是老板更勤奋，而是团队能自动运转。",
                "SOP不是写给老板看的，而是写给团队重复执行的。",
            ],
            full_draft=body,
            ending_cta="如果你也想梳理店铺运营流程，可以私信关键词「诊断」，先从一个核心流程开始拆。",
            topic=topic,
        )

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
        return [
            "开头: 用一个电商老板熟悉的管理困境切入",
            f"观点: {topic.core_insight}",
            f"痛点: {topic.pain_point}",
            "拆解: 问题为什么不是单点动作能解决",
            "方法: 给出 3 个可执行管理动作",
            "案例: 用一个电商团队的真实管理场景讲透",
            "金句: 用一句老板能记住的话收住观点",
            "结尾: 用低压力方式引导留言或私信咨询",
        ]

    def _build_body(self, topic: ContentTopic, outline: list[str], editor_note: str) -> str:
        return "\n\n".join(
            [
                f"# {topic.title}",
                "## 一、先说一个老板最熟悉的场景",
                (
                    f"很多{topic.target_reader}都会遇到类似问题：{topic.pain_point}。"
                    "早上刚到公司，运营说活动节奏要改；客服说差评还没处理；美工说详情页还差素材；投手说预算要不要加；仓库说赠品快没了。"
                    "每个人都在找老板拍板，老板一天开了五六个会，手机消息还一直响。"
                ),
                (
                    "最难受的不是忙，而是忙完以后发现结果并没有变稳定。"
                    "今天这个问题解决了，明天换一个产品、换一个运营、换一个平台规则，又要重新救一次火。"
                    "老板会有一种很强的无力感：公司看起来有团队，实际上关键动作还是靠自己盯。"
                ),
                (
                    "所以这篇文章不想讲大道理，也不想劝老板再努力一点。"
                    "我们要拆的是一个更底层的问题：为什么团队明明有人，事情却总是推不动；为什么公司明明有流程，执行却还是靠临时催。"
                ),
                "## 二、表面是执行问题，背后是系统问题",
                (
                    "很多管理问题，表面看都是人的问题。运营不主动，主管不负责，客服不复盘，美工不理解卖点。"
                    "但你往下追三层，通常会发现不是这个人突然变差了，而是公司没有把一件事的标准动作讲清楚。"
                ),
                (
                    f"{topic.core_insight}。"
                    "如果目标只停留在一句“这个月要把销售额做起来”，团队就只能靠经验猜。"
                    "有经验的人能猜对一部分，新人猜不对，跨岗位的人更猜不对。"
                ),
                (
                    "管理的麻烦就在这里：老板脑子里有判断，团队手上没有标准；老板知道哪里不对，员工不知道下一步怎么改。"
                    "时间一长，公司就会形成一种隐形依赖：凡是重要的事，都要等老板给答案。"
                ),
                "## 三、真正拖垮团队的，不是能力差，而是动作没有被拆开",
                (
                    "电商团队最怕一句话：你自己看着办。"
                    "这句话听起来是授权，实际上很多时候是把不确定性甩给员工。"
                    "员工不是不想做好，而是不知道做到什么程度算好，什么时候必须反馈，出了异常应该找谁。"
                ),
                (
                    "比如上新这件事，很多公司只会说“这周把新品上完”。"
                    "但新品上完之前，选品依据是什么，价格带怎么定，竞品差评看了没有，主图测试过没有，详情页卖点有没有排序，首轮投放预算怎么设，数据到什么程度要停，没人写清楚。"
                ),
                (
                    "动作没有拆开，管理就只能靠感觉。"
                    "感觉好的时候，大家配合得还行；一旦订单下滑、平台变化、人员调整，问题就会集中爆出来。"
                    "这也是为什么很多电商公司不是死在一个大错误上，而是死在一堆小动作长期不稳定上。"
                ),
                "## 四、老板要抓的不是更多细节，而是三类关键节点",
                (
                    "第一类节点，叫输入节点。"
                    "任何运营动作开始之前，必须先问：这件事需要哪些信息才能开工？"
                    "比如做详情页，输入不是“产品资料”四个字，而是目标人群、核心卖点、竞品对比、价格理由、用户顾虑、评价素材。"
                ),
                (
                    "第二类节点，叫交付节点。"
                    "员工做完一件事，不能只说“做完了”，而要交付一个可检查的结果。"
                    "例如运营提交的不是“活动方案”，而是活动目标、商品清单、价格机制、库存风险、推广节奏、复盘时间。"
                ),
                (
                    "第三类节点，叫异常节点。"
                    "公司最容易失控的地方，往往不是正常流程，而是异常情况。"
                    "点击率突然下降怎么办，转化率低于多少要改图，库存低于几天要预警，差评集中出现谁来处理，这些必须提前写进规则。"
                ),
                "## 五、一个电商团队的案例：老板少盯了，结果反而稳了",
                (
                    f"我们用一个典型场景来讲。{topic.case_direction}。"
                    "这家公司过去上新很快，一个月能推不少款，但真正能跑出来的少。"
                    "老板一开始以为是运营能力不够，后来发现问题并不在某一个人身上。"
                ),
                (
                    "他们的问题是，每次上新都像重新创业。"
                    "选品靠运营经验，主图靠美工感觉，投放靠临时判断，复盘靠月底开会。"
                    "每个人都做了事，但这些动作没有连成一条能复用的流程。"
                ),
                (
                    "后来他们先不急着加人，也不急着换运营，而是把新品流程拆成六个表：选品判断表、竞品拆解表、卖点排序表、素材清单表、投放测试表、复盘更新表。"
                    "每个表只解决一个问题，每个表都有负责人和截止时间。"
                ),
                (
                    "变化不是立刻爆单，而是管理开始变轻了。"
                    "老板不用每天问“这个新品怎么样了”，只要看流程看板，就知道卡在哪一步；主管也不用凭印象汇报，因为每个节点都有记录。"
                    "这就是流程化的价值：它不是替代人，而是让人少靠猜。"
                ),
                "## 六、落地时先别贪大，先做一条最小闭环",
                (
                    "很多公司做 SOP 失败，是因为一上来就想做一本很厚的制度。"
                    "最后文档写了几十页，员工不看，主管不用，老板也没时间维护。"
                    "真正能落地的 SOP，应该先从一条高频、高痛点、高价值的流程开始。"
                ),
                (
                    "比如你现在最头疼的是上新，就先做新品 SOP；最头疼的是客服差评，就先做差评处理 SOP；最头疼的是运营复盘，就先做周复盘 SOP。"
                    "不要追求一次做全，先让团队在一件事上尝到“有标准更轻松”的甜头。"
                ),
                (
                    "一条最小闭环至少包括六个字段：输入、动作、标准、负责人、交付物、异常处理。"
                    "只要这六个字段写清楚，很多模糊沟通就会减少。"
                    "老板要看的也不是员工有没有忙，而是这六个字段有没有按时交付。"
                ),
                "## 七、给老板的三个动作，今天就能开始",
                (
                    "第一个动作，把目标拆成动作。"
                    "不要只说销售额、利润率、投产比，而要拆到团队每天能执行的动作。"
                    "比如销售额背后对应的是商品结构、流量入口、转化素材、客服承接、复购动作。"
                ),
                (
                    "第二个动作，把经验写成表单。"
                    "老板和老运营脑子里的经验，如果不变成表单，就很难复制给新人。"
                    "表单不是为了好看，而是为了让团队在关键节点不漏项。"
                ),
                (
                    "第三个动作，把复盘接回流程。"
                    "很多公司复盘只是开会总结，讲完就结束。"
                    "真正有用的复盘，必须改模板、改标准、改检查点。"
                    "否则同样的问题下个月还会再来一次。"
                ),
                "## 八、最后说一句实在话",
                (
                    "老板越忙，不一定代表公司越好，很多时候说明系统还不够强。"
                    "团队越依赖老板，老板越难从日常事务里抽身；老板越抽不开身，公司越难做真正的增长动作。"
                ),
                (
                    "流程不是把人管死，而是把关键动作讲清楚。"
                    "SOP 也不是写给老板看的，而是写给团队重复执行的。"
                    "当普通员工也能按标准做出稳定结果，公司才真正从人治走向系统化。"
                ),
                f"主编提示：{editor_note}",
                (
                    "如果你也想梳理店铺运营流程，可以先在团队里选一条最痛的流程，把输入、动作、标准、负责人、交付物、异常处理写出来。"
                    "如果你愿意，也可以私信关键词「诊断」，我们先帮你看一条流程到底卡在哪里。"
                ),
            ]
        )
