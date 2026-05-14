from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

from models.content import ContentTopic
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


TOPIC_BANKS: dict[str, list[dict[str, Any]]] = {
    "C": [
        {
            "title": "为什么老板越懂业务，团队越离不开他？",
            "target_user": "电商老板、创业者、管理者",
            "user_pain": "老板业务能力很强，但团队所有关键判断都等老板拍板。",
            "content_angle": "从老板能力太强反而成为组织瓶颈切入，讲企业如何从个人能力走向组织能力。",
            "opening_hook": "很多老板最累的地方，不是不会做业务，而是公司每件大事都绕不开自己。",
            "core_point": "老板的能力如果不能变成团队标准，能力越强，组织越依赖他。",
            "case_direction": "一个老板从亲自判断选品、投流、客服问题，到把判断标准做成会议机制和流程表。",
            "conversion_value": "可自然引出流程化组织、目标管理和老板管理升级咨询。",
            "suitable_product": "打造流程化组织",
            "recommended_score": 89,
            "reason": "有老板代入感和管理认知冲突，适合 C 层破圈。",
        },
        {
            "title": "公司变大以后，为什么老板反而更累？",
            "target_user": "电商老板、创业者、管理者",
            "user_pain": "团队人数变多，沟通成本上升，老板每天被各种小事拉扯。",
            "content_angle": "从公司规模扩大后的管理失控切入，讲流程、责任和复盘的重要性。",
            "opening_hook": "很多老板以为公司变大后，自己会轻松一点，结果发现每天更像在救火。",
            "core_point": "公司变大不是自然变强，只有系统变强，老板才会变轻。",
            "case_direction": "一个 50 人团队老板从一天十几个群里救火，到用周目标、流程卡点和复盘会管理。",
            "conversion_value": "可承接流程化组织和中层管理咨询。",
            "suitable_product": "打造流程化组织",
            "recommended_score": 90,
            "reason": "老板痛点强，适合泛流量传播。",
        },
        {
            "title": "老板越会干活，公司越难长大",
            "target_user": "电商老板、创业者、管理者",
            "user_pain": "老板亲自下场能解决问题，但团队长期学不会独立负责。",
            "content_angle": "从老板个人英雄主义切入，讲复制能力和组织标准。",
            "opening_hook": "有些公司最大的能力，是老板本人；最大的风险，也是老板本人。",
            "core_point": "公司要长大，靠的不是老板多能干，而是把能干的方法复制出去。",
            "case_direction": "一个老板亲自做爆款成功后，团队无法复制，最后拆出选品、测款、打品流程。",
            "conversion_value": "可引出爆款复制体系和流程化组织课程。",
            "suitable_product": "爆款复制体系",
            "recommended_score": 88,
            "reason": "观点尖锐，有转发价值。",
        },
        {
            "title": "真正厉害的老板，不是管人，而是建系统",
            "target_user": "电商老板、管理者",
            "user_pain": "老板每天盯人、催人、骂人，但结果仍然不稳定。",
            "content_angle": "从管人到建系统的认知升级切入，讲目标、流程、跟踪三件事。",
            "opening_hook": "很多老板不是不努力，而是把太多精力用在了盯人上。",
            "core_point": "管理的终点不是老板更勤奋，而是团队能靠系统稳定运转。",
            "case_direction": "一个老板从盯客服响应、运营动作，到建立目标看板和异常跟踪机制。",
            "conversion_value": "可承接目标管理和流程化组织咨询。",
            "suitable_product": "目标管理",
            "recommended_score": 91,
            "reason": "适合建立管理专业信任。",
        },
        {
            "title": "为什么很多公司不是死在机会少，而是死在复制不了？",
            "target_user": "电商老板、创业者、管理者",
            "user_pain": "公司偶尔能做出结果，但很难持续复制成功动作。",
            "content_angle": "从成功不可复制切入，讲经验沉淀、流程复盘和人才复制。",
            "opening_hook": "做出一次结果不难，难的是换一个人、换一个品、换一个月还能做出来。",
            "core_point": "真正值钱的不是一次成功，而是成功背后的复制系统。",
            "case_direction": "一个团队从靠个人经验做成单品，到用复盘模板沉淀可复制动作。",
            "conversion_value": "可引出爆款复制体系、SOP流程化课程。",
            "suitable_product": "爆款复制体系",
            "recommended_score": 90,
            "reason": "商业认知和电商方法能自然连接。",
        },
        {
            "title": "老板天天盯进度，为什么结果还是失控？",
            "target_user": "电商老板、管理者",
            "user_pain": "老板每天催进度，但团队只汇报动作，不对最终结果负责。",
            "content_angle": "从盯进度无效切入，讲结果拆解、过程检查和复盘闭环。",
            "opening_hook": "很多老板每天都在问进度，但真正该问的不是做没做，而是有没有往结果靠近。",
            "core_point": "进度不是管理的终点，结果、标准和复盘才是。",
            "case_direction": "一个团队从每天报事项，到每周按目标、数据、卡点复盘。",
            "conversion_value": "可引出目标管理和流程跟踪体系。",
            "suitable_product": "目标管理",
            "recommended_score": 88,
            "reason": "老板日常场景强，容易引发共鸣。",
        },
        {
            "title": "为什么公司越忙，越说明管理有漏洞？",
            "target_user": "电商老板、创业者、管理者",
            "user_pain": "团队每天加班很久，但业绩和交付并没有稳定提升。",
            "content_angle": "从忙碌假象切入，讲效率、流程和优先级管理。",
            "opening_hook": "有些公司看起来特别忙，但忙到最后，老板只看到疲惫，看不到增长。",
            "core_point": "忙不等于有效，真正有效的是关键动作被重复做对。",
            "case_direction": "一个团队从会议多、群消息多，到用关键动作清单压缩无效忙碌。",
            "conversion_value": "可承接流程化组织和项目管理课程。",
            "suitable_product": "流程化组织",
            "recommended_score": 87,
            "reason": "适合 C 层经营认知传播。",
        },
        {
            "title": "真正能长大的公司，都在减少老板的存在感",
            "target_user": "电商老板、管理者",
            "user_pain": "公司一离开老板就慢下来，说明组织没有独立运行能力。",
            "content_angle": "从老板存在感切入，讲组织自动运转和制度化能力。",
            "opening_hook": "判断一家公司有没有长大，不是看老板多厉害，而是看老板不在时还能不能跑。",
            "core_point": "老板要从业务发动机，变成系统设计师。",
            "case_direction": "一个老板从每天参与业务细节，到只看目标、过程和异常。",
            "conversion_value": "可引出流程化组织和老板管理升级咨询。",
            "suitable_product": "打造流程化组织",
            "recommended_score": 91,
            "reason": "观点有传播性，适合破圈。",
        },
        {
            "title": "公司不是没人可用，是老板没有把人用成系统",
            "target_user": "电商老板、创业者、管理者",
            "user_pain": "老板觉得没人能独当一面，但团队也没有被训练出标准动作。",
            "content_angle": "从无人可用切入，讲岗位标准、训练和复制。",
            "opening_hook": "很多老板说没人可用，但换个角度看，是公司没有一套把人训练出来的方法。",
            "core_point": "人不是自然变强的，人是被岗位标准和训练体系塑造出来的。",
            "case_direction": "一个团队用岗位流程、带教清单和复盘机制训练新人。",
            "conversion_value": "可引出运营岗位体系和中层干部培养。",
            "suitable_product": "中层干部培养",
            "recommended_score": 89,
            "reason": "老板用人痛点强。",
        },
        {
            "title": "老板一松手就乱，说明公司还没真正长大",
            "target_user": "电商老板、管理者",
            "user_pain": "老板只要不盯，团队动作就变形，结果就下滑。",
            "content_angle": "从老板不能松手切入，讲流程标准和检查机制。",
            "opening_hook": "有些老板不是不想放手，是一放手公司就出问题。",
            "core_point": "能不能放手，取决于系统有没有接住老板的判断和标准。",
            "case_direction": "一个老板通过异常看板和周复盘，把救火变成机制管理。",
            "conversion_value": "可引出流程化组织和目标管理咨询。",
            "suitable_product": "打造流程化组织",
            "recommended_score": 90,
            "reason": "强痛点，适合老板认知课。",
        },
    ],
    "E": [
        {
            "title": "运营招来了，为什么店铺还是跑不起来？",
            "target_user": "电商老板、运营负责人、电商管理者",
            "user_pain": "老板花钱招了运营，但新人进来后仍然没有清晰动作和稳定结果。",
            "content_angle": "从招人无效切入，讲岗位流程、能力标准和结果检查。",
            "opening_hook": "很多老板招运营时很有期待，三个月后只剩一个问题：钱花了，结果呢？",
            "core_point": "招运营之前，先把岗位动作、数据标准和复盘机制搭清楚。",
            "case_direction": "一个店铺连续换运营没起色，最后通过岗位SOP和绩效看板稳定产出。",
            "conversion_value": "可引出运营岗位管理体系和薪酬绩效激励课程。",
            "suitable_product": "运营岗位管理体系",
            "recommended_score": 92,
            "reason": "精准命中电商老板招人和用人痛点。",
        },
        {
            "title": "电商团队为什么总是运营急、客服乱、美工返工？",
            "target_user": "电商老板、运营负责人、部门主管",
            "user_pain": "运营、客服、美工之间协作混乱，问题反复出现，老板只能协调。",
            "content_angle": "从跨岗位协作断点切入，讲流程分工和交付标准。",
            "opening_hook": "很多电商团队不是没人干活，而是每个人都很忙，结果却对不上。",
            "core_point": "团队协作乱，底层不是态度问题，而是交付标准和流程接口不清楚。",
            "case_direction": "运营提需求、美工反复改图、客服反馈没人接，最后用流程接口表解决。",
            "conversion_value": "可引出岗位流程梳理和团队管理咨询。",
            "suitable_product": "运营岗位管理体系",
            "recommended_score": 93,
            "reason": "行业场景强，适合 E 层精准获客。",
        },
        {
            "title": "为什么你的运营只会等老板给方向？",
            "target_user": "电商老板、运营负责人",
            "user_pain": "运营遇到问题就等老板判断，缺少独立拆解和复盘能力。",
            "content_angle": "从运营依赖老板切入，讲岗位能力模型、目标拆解和复盘训练。",
            "opening_hook": "有些运营不是不干活，而是一遇到关键判断，就把球踢回老板。",
            "core_point": "运营不能只会执行动作，还要有目标、数据和复盘能力。",
            "case_direction": "一个运营从每天汇报动作，到按数据看板提出下一步方案。",
            "conversion_value": "可引出运营岗位训练和中层干部培养。",
            "suitable_product": "运营岗位管理体系",
            "recommended_score": 90,
            "reason": "精准打中运营负责人培养问题。",
        },
        {
            "title": "店铺利润越来越薄，问题可能不在投流",
            "target_user": "电商老板、运营负责人",
            "user_pain": "投流成本上升，利润变薄，团队只会继续加预算。",
            "content_angle": "从利润压力切入，讲选品、价格、转化、复盘和流程协同。",
            "opening_hook": "很多老板一看到店铺掉利润，第一反应是投流不行，但真相往往没这么简单。",
            "core_point": "利润问题不是单点投流问题，而是选品、转化、供应链和运营流程一起决定的。",
            "case_direction": "一个店铺通过利润看板拆出毛利、转化率、退款率和推广占比问题。",
            "conversion_value": "可引出运营流程化和目标管理咨询。",
            "suitable_product": "目标管理",
            "recommended_score": 89,
            "reason": "适合行业流量和经营复盘。",
        },
        {
            "title": "为什么电商老板越管越细，主管越没担当？",
            "target_user": "电商老板、电商管理者、运营主管",
            "user_pain": "老板管得越细，主管越习惯等指令，不愿意承担结果。",
            "content_angle": "从老板和主管的责任边界切入，讲中层目标、授权和检查机制。",
            "opening_hook": "很多老板培养不出主管，不是因为没人，而是自己一直没有真正放过权。",
            "core_point": "主管要有担当，前提是目标清楚、权责清楚、检查标准清楚。",
            "case_direction": "一个运营主管从传话筒变成项目负责人，靠的是目标卡和周复盘机制。",
            "conversion_value": "可引出中层干部培养和目标管理课程。",
            "suitable_product": "中层干部培养",
            "recommended_score": 91,
            "reason": "精准命中管理升级问题。",
        },
        {
            "title": "客服回复很勤快，为什么询单还是转不动？",
            "target_user": "电商老板、客服主管、运营负责人",
            "user_pain": "客服消息回复不少，但询单转化、客单和复购没有提升。",
            "content_angle": "从客服勤快但无转化切入，讲客服流程、需求判断和话术复盘。",
            "opening_hook": "很多老板看客服数据，只看到回复量，却没看到每一次询单有没有被推进。",
            "core_point": "客服管理不是看忙不忙，而是看有没有把客户往成交动作上推。",
            "case_direction": "一个客服团队通过响应时间、需求标签、异议处理和复盘表提升询单转化。",
            "conversion_value": "可引出客服SOP和岗位绩效体系。",
            "suitable_product": "电商SOP流程化",
            "recommended_score": 90,
            "reason": "场景具体，容易带来咨询。",
        },
        {
            "title": "美工总返工，真不是审美问题",
            "target_user": "电商老板、运营负责人、美工主管",
            "user_pain": "美工反复改图，运营不满意，老板觉得效率低。",
            "content_angle": "从美工返工切入，讲需求交付、卖点标准和素材复盘。",
            "opening_hook": "很多团队的美工不是不会做图，而是每次接到的需求都不清楚。",
            "core_point": "美工效率低，底层常常是运营需求和卖点标准没定义。",
            "case_direction": "一个团队用图片需求单、卖点库和点击率复盘减少返工。",
            "conversion_value": "可引出运营流程化和岗位协作流程。",
            "suitable_product": "运营岗位管理体系",
            "recommended_score": 88,
            "reason": "电商团队常见痛点，适合行业流量。",
        },
        {
            "title": "为什么店铺一做活动，团队就开始乱？",
            "target_user": "电商老板、运营负责人、项目负责人",
            "user_pain": "大促、上新、直播活动一来，运营、客服、仓库协同混乱。",
            "content_angle": "从活动失控切入，讲活动SOP、时间节点和责任分工。",
            "opening_hook": "很多店铺平时还能跑，一到活动就乱成一锅粥。",
            "core_point": "活动不是靠临时冲刺，而是靠提前拆节点、定责任、做预案。",
            "case_direction": "一个大促项目用活动节点表、负责人清单和异常预案稳定推进。",
            "conversion_value": "可引出大促SOP和项目管理流程。",
            "suitable_product": "电商SOP流程化",
            "recommended_score": 91,
            "reason": "行业场景高频，方法感强。",
        },
        {
            "title": "运营日报写了一堆，为什么老板还是看不懂？",
            "target_user": "电商老板、运营负责人",
            "user_pain": "日报内容很多，但老板看不到问题、判断和下一步动作。",
            "content_angle": "从日报无效切入，讲数据字段、问题判断和动作复盘。",
            "opening_hook": "有些运营每天都交日报，但老板看完只剩一个感受：写了很多，没说重点。",
            "core_point": "日报不是记录流水账，而是让老板看见业务判断。",
            "case_direction": "一个运营日报从罗列动作，改成目标、数据、异常、动作、复盘五栏。",
            "conversion_value": "可引出运营看板和目标管理工具。",
            "suitable_product": "目标管理",
            "recommended_score": 89,
            "reason": "能沉淀成工具模板，转化自然。",
        },
        {
            "title": "为什么老运营越来越佛，新项目没人扛？",
            "target_user": "电商老板、运营负责人",
            "user_pain": "成熟项目没人主动突破，新项目老人不愿意接。",
            "content_angle": "从老运营动力不足切入，讲薪酬绩效、项目激励和责任机制。",
            "opening_hook": "很多老板最怕的不是新人不行，而是老运营开始越来越佛。",
            "core_point": "团队没有动力，往往不是钱少，而是钱没有和关键动作、关键结果绑定。",
            "case_direction": "一个运营团队通过新老项目激励机制，让核心人员愿意承担新项目。",
            "conversion_value": "可引出薪酬绩效激励课程。",
            "suitable_product": "薪酬绩效激励",
            "recommended_score": 92,
            "reason": "痛点强，咨询转化价值高。",
        },
    ],
    "S": [
        {
            "title": "岗位流程怎么梳理，才不是写一堆废纸？",
            "target_user": "电商老板、运营负责人、部门主管",
            "user_pain": "公司写过SOP，但员工不看、不用，最后变成文件夹里的摆设。",
            "content_angle": "从SOP落不下去切入，讲流程拆解、操作步骤和数据评估。",
            "opening_hook": "很多公司不是没有SOP，而是SOP写完以后，就再也没有进入过业务现场。",
            "core_point": "岗位流程要能落地，必须连接动作、责任人、检查标准和复盘。",
            "case_direction": "用仓库打单、拣货、验货、打包和客服响应流程做案例。",
            "conversion_value": "可引出岗位流程梳理、电商SOP流程化咨询。",
            "suitable_product": "电商SOP流程化",
            "recommended_score": 95,
            "reason": "工具感强，适合 S 层建立信任。",
        },
        {
            "title": "新品SOP流程，第一步到底该做什么？",
            "target_user": "电商老板、运营负责人、产品负责人",
            "user_pain": "很多公司上新很快，但前置判断不足，后面详情页、投流、直播都浪费。",
            "content_angle": "从新品前置验证切入，讲选品逻辑、测款标准和打品节奏。",
            "opening_hook": "很多团队一上新品，第一反应就是催详情页，结果钱花了，方向却错了。",
            "core_point": "新品SOP的第一步不是执行，而是验证产品机会和打品路径。",
            "case_direction": "一个新品因没做前置验证导致库存积压，后来用开品看板降低试错。",
            "conversion_value": "可引出新品SOP流程和爆款复制体系课程。",
            "suitable_product": "新品SOP流程",
            "recommended_score": 94,
            "reason": "专业度和转化价值都高。",
        },
        {
            "title": "运营复盘会怎么开，才不会变成甩锅会？",
            "target_user": "电商老板、运营负责人、运营主管",
            "user_pain": "复盘会经常变成解释原因、互相甩锅，下一次问题照样发生。",
            "content_angle": "从复盘会低效切入，讲数据、动作、原因、改进和责任闭环。",
            "opening_hook": "有些团队每周都开复盘会，但复盘完以后，问题还是原样出现。",
            "core_point": "复盘不是追责会，而是把有效动作沉淀成下一次的标准。",
            "case_direction": "一次投流失败复盘，从预算、素材、转化、客服承接四个环节拆解。",
            "conversion_value": "可引出目标管理、流程跟踪和运营复盘工具。",
            "suitable_product": "目标管理",
            "recommended_score": 93,
            "reason": "高频管理场景，容易引发咨询。",
        },
        {
            "title": "客服SOP别只写话术，真正要管的是转化过程",
            "target_user": "电商老板、客服主管、运营负责人",
            "user_pain": "客服话术很多，但询单转化、响应速度和问题闭环没有稳定提升。",
            "content_angle": "从客服话术误区切入，讲响应、诊断、推荐、异议处理和复盘。",
            "opening_hook": "很多公司一做客服SOP，就开始堆话术，但客户不成交，问题不在话术数量。",
            "core_point": "客服SOP不是话术库，而是询单转化过程管理。",
            "case_direction": "一个团队把客服流程拆成响应时间、需求判断、推荐话术、异议处理和复盘。",
            "conversion_value": "可引出客服流程化和岗位绩效体系。",
            "suitable_product": "电商SOP流程化",
            "recommended_score": 92,
            "reason": "工具感强，适合精准转化。",
        },
        {
            "title": "目标管理不是喊口号，而是把结果拆到每天",
            "target_user": "电商老板、运营负责人、管理者",
            "user_pain": "公司有月目标，但团队不知道每天要完成哪些动作和数据。",
            "content_angle": "从目标落不下去切入，讲年度、月度、周度和最小作战单元。",
            "opening_hook": "很多团队不是没有目标，而是目标只写在墙上，没有拆进每天的动作里。",
            "core_point": "目标管理的关键，是把大结果拆成小动作、小数据和小复盘。",
            "case_direction": "一个店铺把月销售目标拆成链接、渠道、转化率和日动作看板。",
            "conversion_value": "可引出目标管理和流程化组织课程。",
            "suitable_product": "目标管理",
            "recommended_score": 94,
            "reason": "专业内容强，适合课程转化。",
        },
        {
            "title": "运营岗位说明书，为什么不能只写职责？",
            "target_user": "电商老板、运营负责人、人事负责人",
            "user_pain": "岗位说明书写了很多职责，但新人仍然不知道每天怎么做。",
            "content_angle": "从岗位说明书无效切入，讲结果、动作、标准、工具和考核字段。",
            "opening_hook": "很多公司的岗位说明书看起来很完整，但员工看完还是不知道明天怎么干。",
            "core_point": "岗位说明书不是职责清单，而是岗位交付系统。",
            "case_direction": "把运营岗位拆成结果指标、日常动作、协作接口和复盘要求。",
            "conversion_value": "可引出运营岗位管理体系和招聘流程化。",
            "suitable_product": "运营岗位管理体系",
            "recommended_score": 93,
            "reason": "专业度强，适合工具转化。",
        },
        {
            "title": "一张流程表，怎么让新人少踩一半坑？",
            "target_user": "电商老板、运营负责人、部门主管",
            "user_pain": "新人入职靠口头带教，老员工反复教，新人还是容易漏动作。",
            "content_angle": "从新人带教成本切入，讲流程表、检查点和带教复盘。",
            "opening_hook": "新人上手慢，很多时候不是人笨，而是公司没有把路画清楚。",
            "core_point": "流程表的价值，是让新人先按正确路径做，再在复盘里变强。",
            "case_direction": "一个客服新人用流程表完成响应、推荐、异议处理和复盘。",
            "conversion_value": "可引出岗位流程表和训战体系。",
            "suitable_product": "中层干部培养",
            "recommended_score": 92,
            "reason": "易形成资料领取和私域转化。",
        },
        {
            "title": "SOP没人执行，通常是这3个地方没写清楚",
            "target_user": "电商老板、运营负责人、主管",
            "user_pain": "SOP发布以后员工不执行，主管也不知道怎么检查。",
            "content_angle": "从SOP执行失败切入，讲责任人、触发场景、验收标准。",
            "opening_hook": "很多公司以为SOP没人执行，是员工态度问题，其实是SOP本身没写到执行层。",
            "core_point": "能执行的SOP，必须写清谁做、什么时候做、做到什么算合格。",
            "case_direction": "以新品上架SOP为例，拆出触发条件、动作、责任和验收。",
            "conversion_value": "可引出电商SOP流程化课程。",
            "suitable_product": "电商SOP流程化",
            "recommended_score": 95,
            "reason": "专业干货强，转化价值高。",
        },
        {
            "title": "绩效考核为什么越做，员工越反感？",
            "target_user": "电商老板、运营负责人、人事负责人",
            "user_pain": "绩效表越来越复杂，员工不买账，主管也觉得难落地。",
            "content_angle": "从绩效反感切入，讲指标设计、过程动作和利益分配。",
            "opening_hook": "很多老板做绩效，是想点燃团队，最后却把团队点炸了。",
            "core_point": "绩效不是扣钱工具，而是让关键动作和关键结果被看见。",
            "case_direction": "一个运营岗位绩效从拍脑袋提成，改成销售、利润、过程动作和项目奖金。",
            "conversion_value": "可引出薪酬绩效激励课程。",
            "suitable_product": "薪酬绩效激励",
            "recommended_score": 94,
            "reason": "痛点强，课程转化明确。",
        },
        {
            "title": "流程看板怎么做，老板才能一眼看懂业务？",
            "target_user": "电商老板、运营负责人、项目负责人",
            "user_pain": "老板想看业务进展，但团队给的数据散、表格乱、问题不清楚。",
            "content_angle": "从老板看不见业务切入，讲流程看板字段和异常管理。",
            "opening_hook": "老板最怕的不是问题多，而是问题已经发生了，自己最后一个知道。",
            "core_point": "好的流程看板，不是展示数据，而是暴露卡点。",
            "case_direction": "一个打品看板包含产品、阶段、负责人、关键数据、异常和下一步动作。",
            "conversion_value": "可引出流程工具箱和目标管理咨询。",
            "suitable_product": "流程工具箱",
            "recommended_score": 93,
            "reason": "工具感强，适合S层成交。",
        },
    ],
}


@dataclass
class TopicAgent:
    brand: dict[str, Any]
    layers: dict[str, Any]
    courseware_context: dict[str, Any] | None = None
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def generate_topics(self, calendar_item: dict[str, Any]) -> list[ContentTopic]:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号选题策划 Agent。",
            json.dumps(
                {
                    "brand": self.brand,
                    "layers": self.layers,
                    "calendar_item": calendar_item,
                    "courseware_context": self._courseware_prompt_context(),
                    "task": "生成 C/E/S 三个公众号选题。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        layer_config = self.layers.get("layers", {})
        context = calendar_item.get("business_context", "电商老板正在面对增长放缓和团队管理压力。")
        priority = calendar_item.get("priority", "把经营问题拆成可执行的管理动作。")

        return [
            self._build_layer_topic("C", layer_config.get("C", {}), calendar_item, context),
            self._build_layer_topic("E", layer_config.get("E", {}), calendar_item, context),
            self._build_layer_topic("S", layer_config.get("S", {}), calendar_item, priority),
        ]

    def _courseware_prompt_context(self) -> dict[str, Any]:
        context = self.courseware_context or {}
        return {
            "enabled": context.get("enabled", False),
            "available": context.get("available", False),
            "root": context.get("root", ""),
            "files": [item.get("path", "") for item in context.get("files", [])],
            "summary": context.get("summary", ""),
        }

    def _courseware_hint(self) -> str:
        context = self.courseware_context or {}
        if not context.get("available"):
            return "暂无课件库参考，本次使用通用课程咨询框架。"
        files = "、".join(item.get("path", "") for item in context.get("files", [])[:3])
        return f"参考 GitHub 课件库：{files}。重点吸收岗位流程、SOP、SABC评估和流程化组织方法。"

    def _build_layer_topic(
        self,
        layer: str,
        config: dict[str, Any],
        calendar_item: dict[str, Any],
        context: str,
    ) -> ContentTopic:
        template = self._select_template(layer, calendar_item)
        courseware_hint = self._courseware_hint()
        return ContentTopic(
            topic_id=layer,
            title=template["title"],
            layer=layer,
            layer_name=config.get("name", {"C": "泛流量", "E": "行业流量", "S": "专业内容"}.get(layer, "")),
            target_user=template["target_user"],
            user_pain=template["user_pain"],
            content_angle=f"{template['content_angle']} 背景: {context}。{courseware_hint}",
            opening_hook=template["opening_hook"],
            core_point=template["core_point"],
            article_structure=template.get("article_structure", self._article_structure_for(layer)),
            case_direction=template["case_direction"],
            conversion_value=template["conversion_value"],
            suitable_product=template["suitable_product"],
            recommended_score=template["recommended_score"],
            reason=template["reason"],
        )

    def _select_template(self, layer: str, calendar_item: dict[str, Any]) -> dict[str, Any]:
        templates = TOPIC_BANKS[layer]
        recent_titles = set(calendar_item.get("recent_topic_titles", []))
        start_index = self._date_seed(calendar_item) % len(templates)
        for offset in range(len(templates)):
            template = templates[(start_index + offset) % len(templates)]
            if template["title"] not in recent_titles:
                return template
        return templates[start_index]

    def _date_seed(self, calendar_item: dict[str, Any]) -> int:
        raw_date = str(calendar_item.get("date", ""))
        try:
            return date.fromisoformat(raw_date).toordinal()
        except ValueError:
            return len(raw_date)

    def _article_structure_for(self, layer: str) -> list[str]:
        if layer == "C":
            return ["现象", "冲突", "真相", "解决方案"]
        if layer == "E":
            return ["问题", "原因", "方法", "案例", "总结"]
        return ["痛点场景", "错误认知", "流程步骤", "工具模板", "行动建议"]
