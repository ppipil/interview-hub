from __future__ import annotations

from typing import Iterable, List

from app.core.errors import ValidationError
from app.models.api import InterviewRole, InterviewStageKey
from app.models.persistence import FormalQuestionBankWrite

FORMAL_QUESTION_STAGE_KEYS: tuple[InterviewStageKey, ...] = (
  "intro",
  "fundamentals",
  "project",
  "system_design",
  "behavioral",
  "closing",
)

FORMAL_QUESTION_STAGE_LABELS: dict[InterviewStageKey, str] = {
  "intro": "背景介绍",
  "fundamentals": "基础能力",
  "project": "项目深挖",
  "system_design": "系统设计",
  "behavioral": "行为追问",
  "closing": "总结收口",
}

ROUND_STAGE_PLAN: dict[int, tuple[InterviewStageKey, ...]] = {
  1: ("intro",),
  2: ("intro", "fundamentals"),
  3: ("intro", "fundamentals", "closing"),
  4: ("intro", "fundamentals", "fundamentals", "closing"),
  5: ("intro", "fundamentals", "fundamentals", "fundamentals", "closing"),
  6: ("intro", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "closing"),
  7: ("intro", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "closing"),
  8: ("intro", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "closing"),
  9: ("intro", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "closing"),
  10: ("intro", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "fundamentals", "closing"),
}


ROLE_PROFILES = {
  "frontend": {
    "label": "前端",
    "artifact": "页面或应用",
    "system": "前端工程方案",
    "metric": "性能、稳定性和体验指标",
  },
  "backend": {
    "label": "后端",
    "artifact": "服务或系统",
    "system": "后端系统方案",
    "metric": "吞吐、延迟和稳定性指标",
  },
  "product_manager": {
    "label": "产品",
    "artifact": "产品或功能",
    "system": "产品机制或业务方案",
    "metric": "转化、留存和交付效率指标",
  },
  "operations": {
    "label": "运营",
    "artifact": "活动或增长项目",
    "system": "运营机制或活动方案",
    "metric": "增长、活跃和转化指标",
  },
  "data_analyst": {
    "label": "数据分析",
    "artifact": "分析专题或数据项目",
    "system": "指标体系或分析方案",
    "metric": "准确性、洞察深度和业务影响指标",
  },
}

BACKEND_FUNDAMENTALS_BANK: tuple[tuple[str, tuple[str, ...]], ...] = (
  (
    "Java/语言基础",
    (
      "HashMap 的底层实现、扩容机制，以及为什么 1.8 之后引入红黑树？",
      "ConcurrentHashMap 如何保证线程安全？请对比 1.7 分段锁和 1.8 的 CAS + synchronized。",
      "JVM 内存区域里，堆、栈、方法区、程序计数器分别负责什么？",
      "常见垃圾回收算法有哪些？CMS 和 G1 收集器的区别是什么？",
      "什么是双亲委派模型？为什么类加载要这样设计？",
      "线程的状态是怎么流转的？sleep() 和 wait() 的区别是什么？",
      "什么是 JMM 里的原子性、可见性、有序性？volatile 的原理是什么？",
      "synchronized 和 ReentrantLock 有什么区别、优缺点及底层实现差异？",
      "线程池的核心参数有哪些？常见拒绝策略有哪些？核心线程数一般怎么定？",
      "ThreadLocal 的底层实现是什么？为什么它可能导致内存泄漏？",
    ),
  ),
  (
    "数据库（MySQL）",
    (
      "为什么 MySQL 索引使用 B+ 树，而不是 B 树或红黑树？",
      "哪些场景会导致索引失效？比如左模糊、函数操作、类型转换分别会有什么影响？",
      "请简述事务的 ACID 特性，以及它们在 MySQL 里通常怎么实现。",
      "MySQL 支持哪些事务隔离级别？默认是哪一个？",
      "MVCC 的实现原理是什么？请结合 ReadView 和隐藏字段来讲。",
      "什么是幻读？InnoDB 是如何解决幻读问题的？",
      "binlog、redo log、undo log 的区别分别是什么？",
      "给你一条执行很慢的 SQL，你的优化思路一般是什么？",
      "MySQL 里的全局锁、表锁、行锁分别是什么？记录锁、间隙锁、临键锁又怎么理解？",
      "什么情况下需要分库分表？垂直拆分和水平拆分有什么区别？",
    ),
  ),
  (
    "缓存（Redis）",
    (
      "Redis 五种基本数据类型分别是什么？各自适合哪些典型场景？",
      "RDB 和 AOF 的优缺点分别是什么？什么是混合持久化？",
      "Redis 为什么通常被说成是单线程的？单线程为什么还能这么快？",
      "Redis 的过期策略和内存淘汰机制分别是什么？常见的 LRU、LFU 又是怎么工作的？",
      "什么是缓存穿透、缓存击穿、缓存雪崩？分别怎么解决？",
      "Redis 如何实现分布式锁？Redisson 的看门狗机制是什么？",
      "哨兵模式和集群模式有什么区别？各自解决什么问题？",
      "数据库和缓存如何保证一致性？为什么很多场景会选择先更新数据库再删缓存？",
      "为什么 zset 底层使用跳表，而不是红黑树？",
      "Redis 事务的 multi/exec 机制能保证哪些原子性，不能保证哪些？",
    ),
  ),
  (
    "计算机网络与系统",
    (
      "TCP 三次握手和四次挥手的详细过程是什么？为什么挥手通常需要四次？",
      "为什么客户端在连接关闭后通常要等待 2MSL，也就是 TIME_WAIT？",
      "TCP 和 UDP 的区别是什么？各自更适合哪些应用场景？",
      "HTTP 和 HTTPS 的区别是什么？HTTPS 的加密过程通常怎么走？",
      "常见 HTTP 状态码里，200、301、302、403、404、500、502、504 分别代表什么？",
      "在浏览器里输入一个 URL 后，从 DNS 解析到页面渲染，完整过程大致是什么？",
      "进程和线程的区别与联系是什么？什么是上下文切换？",
      "为什么需要虚拟内存？分页和分段有什么区别？",
    ),
  ),
  (
    "分布式与微服务",
    (
      "CAP 理论里的 C、A、P 分别是什么？在真实系统里通常怎么权衡？",
      "什么是 BASE 理论？基本可用、软状态、最终一致性分别怎么理解？",
      "2PC、3PC、TCC、消息最终一致性这几种分布式事务方案有什么区别？",
      "常见的负载均衡算法有哪些？轮询、随机、一致性 Hash 分别适合什么场景？",
      "Nacos、Eureka、Zookeeper 在服务注册与发现上有什么区别？",
      "什么是服务雪崩？Sentinel 或 Hystrix 的熔断降级原理可以怎么讲？",
    ),
  ),
  (
    "算法与数据结构",
    (
      "快速排序和归并排序的时间复杂度、稳定性和核心原理分别是什么？",
      "怎么反转链表？又怎么用快慢指针检测环形链表？",
      "二叉树的前中后序遍历怎么写？递归和迭代各有什么思路？",
      "动态规划里，像爬楼梯、最长递增子序列这类题通常怎么建立状态转移？",
      "给定一个有序数组，二分查找时最容易出错的边界条件有哪些？",
      "怎么用双向链表加 HashMap 手写一个 LRU 缓存？",
    ),
  ),
)


def get_stage_plan(total_rounds: int) -> tuple[InterviewStageKey, ...]:
  plan = ROUND_STAGE_PLAN.get(total_rounds)
  if not plan:
    raise ValidationError("当前仅支持 1 到 10 轮面试。", field="totalRounds")
  return plan


def get_stage_key_for_round(round_number: int, total_rounds: int) -> InterviewStageKey:
  if round_number < 1:
    raise ValidationError("轮次必须从 1 开始。", field="round")
  plan = get_stage_plan(total_rounds)
  try:
    return plan[round_number - 1]
  except IndexError as exc:
    raise ValidationError("轮次超出当前面试配置。", field="round") from exc


def validate_stage_key(stage_key: str) -> InterviewStageKey:
  if stage_key not in FORMAL_QUESTION_STAGE_KEYS:
    allowed = "、".join(FORMAL_QUESTION_STAGE_KEYS)
    raise ValidationError(f"题库阶段只支持：{allowed}。", field="stageKey")
  return stage_key  # type: ignore[return-value]


def build_seed_formal_questions(default_avatar_interviewer_id: str) -> List[FormalQuestionBankWrite]:
  questions: List[FormalQuestionBankWrite] = []
  for role in ROLE_PROFILES:
    questions.extend(_build_global_fallback_questions(role))

  questions.extend(_build_sample_interviewer_bank(default_avatar_interviewer_id))
  return questions


def build_stage_questions_from_role(role: InterviewRole) -> List[FormalQuestionBankWrite]:
  profile = ROLE_PROFILES[role]
  templates = _build_templates_for_role(role)
  questions: List[FormalQuestionBankWrite] = []
  sort_order = 10
  for stage_key in ("intro", "fundamentals", "closing"):
    stage_templates = templates[stage_key]
    question_text = stage_templates[0]
    questions.append(
      FormalQuestionBankWrite(
        scope_type="interviewer",
        interviewer_id=None,
        role=role,
        stage_key=stage_key,
        question=question_text,
        reference_answer=_build_reference_answer(stage_key, profile["label"]),
        tags=[FORMAL_QUESTION_STAGE_LABELS[stage_key], profile["label"]],
        enabled=True,
        sort_order=sort_order,
      )
    )
    sort_order += 10
  return questions


def normalize_question_tags(tags: Iterable[str]) -> List[str]:
  normalized: List[str] = []
  for tag in tags:
    value = str(tag).strip()
    if value and value not in normalized:
      normalized.append(value)
  return normalized


def _flatten_backend_fundamentals_bank() -> List[tuple[str, str]]:
  return [
    (category, question_text)
    for category, questions in BACKEND_FUNDAMENTALS_BANK
    for question_text in questions
  ]


def _build_global_fallback_questions(role: InterviewRole) -> List[FormalQuestionBankWrite]:
  profile = ROLE_PROFILES[role]
  templates = _build_templates_for_role(role)
  backend_fundamentals = dict(_flatten_backend_fundamentals_bank()) if role == "backend" else {}
  questions: List[FormalQuestionBankWrite] = []
  sort_order = 10
  for stage_key in FORMAL_QUESTION_STAGE_KEYS:
    for question_text in templates[stage_key]:
      tags = ["通用题库", profile["label"], FORMAL_QUESTION_STAGE_LABELS[stage_key]]
      backend_category = backend_fundamentals.get(question_text)
      if backend_category:
        tags.append(backend_category)
      questions.append(
        FormalQuestionBankWrite(
          scope_type="global",
          interviewer_id=None,
          role=role,
          stage_key=stage_key,
          question=question_text,
          reference_answer=_build_reference_answer(stage_key, profile["label"]),
          tags=tags,
          enabled=True,
          sort_order=sort_order,
        )
      )
      sort_order += 10
  return questions


def _build_sample_interviewer_bank(interviewer_id: str) -> List[FormalQuestionBankWrite]:
  return [
    FormalQuestionBankWrite(
      scope_type="interviewer",
      interviewer_id=interviewer_id,
      role="backend",
      stage_key="fundamentals",
      question="如果让你用 HashMap 证明自己的 Java 基础，你会怎么讲它的底层实现、扩容机制，以及 1.8 为什么引入红黑树？",
      reference_answer="优秀回答应覆盖数组加链表/红黑树结构、哈希扰动、扩容与再散列、树化阈值，以及这些设计背后的时间复杂度取舍。",
      tags=["示例面试官", "后端八股", "Java/语言基础"],
      enabled=True,
      sort_order=10,
    ),
    FormalQuestionBankWrite(
      scope_type="interviewer",
      interviewer_id=interviewer_id,
      role="backend",
      stage_key="fundamentals",
      question="如果从数据库原理里挑一道高频题，你会怎么回答为什么 MySQL 索引使用 B+ 树，而不是 B 树或红黑树？",
      reference_answer="优秀回答应说明磁盘 IO、页大小、树高、范围查询和顺序扫描成本，并把 B+ 树与 B 树、红黑树的差异讲清楚。",
      tags=["示例面试官", "后端八股", "数据库（MySQL）"],
      enabled=True,
      sort_order=20,
    ),
    FormalQuestionBankWrite(
      scope_type="interviewer",
      interviewer_id=interviewer_id,
      role="backend",
      stage_key="fundamentals",
      question="你会怎么系统解释缓存穿透、缓存击穿、缓存雪崩，以及各自的解决方案？",
      reference_answer="优秀回答应分别说明成因、典型表现、缓存空值/布隆过滤器/互斥锁/限流降级等方案，并补充真实业务里的取舍。",
      tags=["示例面试官", "后端八股", "缓存（Redis）"],
      enabled=True,
      sort_order=30,
    ),
  ]


def _build_templates_for_role(role: InterviewRole) -> dict[InterviewStageKey, list[str]]:
  profile = ROLE_PROFILES[role]
  label = profile["label"]
  artifact = profile["artifact"]
  system = profile["system"]
  metric = profile["metric"]
  fundamentals_templates = (
    [question_text for _, question_text in _flatten_backend_fundamentals_bank()]
    if role == "backend"
    else [
      f"请解释一个你最熟悉的{label}基础知识点，并说明它的核心原理、适用场景和常见问题。",
      f"如果让我判断你的{label}基础是否扎实，你会选哪个知识点来证明自己？",
      f"讲一个{label}岗位常见八股题，说明定义、原理和实际使用场景。",
      f"说一个你熟悉的{label}技术概念，重点解释为什么这样设计，而不只是背定义。",
      f"如果你来给同学讲一个{label}知识点，你会选什么？请讲清核心逻辑。",
      f"挑一个你在面试中最容易被问到的{label}八股题，完整回答一次。",
      f"讲一个你觉得最能区分初中高级{label}工程师的基础问题，并给出你的答案。",
      f"如果从原理、场景和常见坑三个角度回答一道{label}八股题，你会怎么组织？",
      f"说一个你最常用的{label}技术组件，讲清它为什么这样工作、什么时候不适合用。",
      f"请讲一道典型的{label}专业基础题，除了标准答案，也补充你在真实工作中的理解。",
    ]
  )
  return {
    "intro": [
      f"请先做一个简短的自我介绍，并讲一个最近最能体现你{label}能力的{artifact}。",
      f"先用 1-2 分钟介绍一下你的相关经历，再补一个你最近做过的典型{artifact}。",
    ],
    "fundamentals": fundamentals_templates,
    "project": [
      f"讲一个你真实做过的{artifact}难题：背景是什么、最难的点是什么、你最后怎么解决？",
      f"回到一个真实{artifact}场景，说明你做过的关键取舍，以及这个取舍最终带来了什么结果。",
    ],
    "system_design": [
      f"如果现在让你设计或优化一个{system}，你会先拆哪几个关键模块？为什么？",
      f"给你一个需要长期扩展的{system}场景，你会如何在方案里兼顾{metric}？",
    ],
    "behavioral": [
      f"说一个你在跨团队协作中推进{artifact}的例子：当时最大的阻力是什么，你怎么推动落地？",
      f"讲一次你在压力或不确定性比较高的情况下推进{artifact}的经历，你是怎么做判断和复盘的？",
    ],
    "closing": [
      f"最后如果还有一个你觉得能加分的{label}亮点，请你再补充一下。",
      f"最后一题：你还有什么想补充，或者有什么想问面试官的吗？",
    ],
  }


def _build_reference_answer(stage_key: InterviewStageKey, role_label: str) -> str:
  if stage_key == "intro":
    return f"优秀回答通常会先交代业务背景，再说明自己负责的模块、使用的方法，以及一个可被继续追问的结果或指标，帮助面试官快速判断{role_label}经验的真实性。"
  if stage_key == "fundamentals":
    return f"优秀回答需要同时讲清概念、原理、适用边界和真实使用经验，而不是只背定义；最好能补充一个常见误区，体现{role_label}基础的扎实程度。"
  if stage_key == "project":
    return f"优秀回答应围绕背景、难点、方案、取舍、验证和结果展开，重点证明候选人不仅参与过，而且真正理解这个{role_label}问题为什么难、为什么这么做。"
  if stage_key == "system_design":
    return f"优秀回答通常会从目标、约束、核心模块、关键链路、稳定性策略和观测手段展开，并说明为什么这些设计能支撑业务与{role_label}场景要求。"
  if stage_key == "behavioral":
    return f"优秀回答需要体现具体场景、你的责任、当时的冲突或压力、采取的行动和最终结果，最好再补一层复盘，说明你如何提升自己的{role_label}协作能力。"
  return f"优秀回答应该简洁总结亮点与不足，既能回扣前面的问题，也能体现候选人对自己当前{role_label}能力边界的认识。"
