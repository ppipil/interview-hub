import { roleOptions } from "./interviewOptions";
import { parseQuestionBankText } from "./questionBank";
import type { InterviewRole, UpsertAdminInterviewerRequest } from "../types";

export type CompanyPreset = "ali" | "startup" | "global" | "state_owned" | "internet";
export type FlowTemplate = "standard5" | "project3" | "pressure4" | "friendly3";

export interface QuestionnaireForm {
  interviewerName: string;
  interviewerUsername: string;
  company: CompanyPreset;
  role: InterviewRole;
  styleIds: string[];
  focusIds: string[];
  flowTemplate: FlowTemplate;
  avatarApiKey: string;
  extraNotes: string;
  questionBankText: string;
}

interface OptionItem<T extends string> {
  id: T;
  label: string;
  helper: string;
}

interface PromptOption {
  id: string;
  label: string;
  prompt: string;
}

export const companyOptions: OptionItem<CompanyPreset>[] = [
  { id: "ali", label: "阿里 / 大厂", helper: "严谨、深挖、重工程能力" },
  { id: "startup", label: "创业公司", helper: "快节奏、重落地和 Owner 意识" },
  { id: "internet", label: "互联网公司", helper: "通用技术面，适合先测试" },
  { id: "global", label: "外企", helper: "结构化、沟通清晰、边界感强" },
  { id: "state_owned", label: "国企 / 稳定型", helper: "稳健、规范、关注协作" },
];

const companyMeta: Record<CompanyPreset, { namePrefix: string; promptLabel: string; tag: string }> = {
  ali: { namePrefix: "阿里", promptLabel: "阿里巴巴/互联网大厂", tag: "大厂" },
  startup: { namePrefix: "创业公司", promptLabel: "高速成长型创业公司", tag: "创业" },
  internet: { namePrefix: "互联网", promptLabel: "成熟互联网公司", tag: "互联网" },
  global: { namePrefix: "外企", promptLabel: "跨国科技公司", tag: "外企" },
  state_owned: { namePrefix: "稳健型", promptLabel: "规范稳健型组织", tag: "稳健" },
};

export const styleOptions: PromptOption[] = [
  { id: "rigorous", label: "严谨深入", prompt: "追求答案的准确性、边界条件和技术深度。" },
  { id: "project", label: "项目深挖", prompt: "优先从候选人的真实项目切入，持续追问取舍、数据和结果。" },
  { id: "structured", label: "结构化评分", prompt: "按知识、经验、表达、问题解决能力进行结构化判断。" },
  { id: "concise", label: "简洁直接", prompt: "问题短、目标明确，不做冗长铺垫。" },
  { id: "pressure", label: "适度压力", prompt: "在关键回答含糊时追问细节，但保持专业和尊重。" },
  { id: "friendly", label: "友好引导", prompt: "语气温和，允许候选人补充思考过程。" },
];

export const focusOptions: PromptOption[] = [
  { id: "project_experience", label: "项目经验", prompt: "项目背景、职责边界、技术难点、结果指标。" },
  { id: "fundamentals", label: "基础知识", prompt: "岗位基础概念、原理解释、常见坑和边界条件。" },
  { id: "system_design", label: "系统设计", prompt: "架构拆分、可扩展性、性能、稳定性和容错。" },
  { id: "algorithm", label: "算法 / 数据结构", prompt: "复杂度、数据结构选择、常见题型思路。" },
  { id: "communication", label: "沟通表达", prompt: "表达是否清晰、能否讲清取舍和协作方式。" },
  { id: "business", label: "业务理解", prompt: "能否把技术方案和业务目标、用户价值连接起来。" },
];

export const flowOptions: OptionItem<FlowTemplate>[] = [
  { id: "standard5", label: "标准 5 阶段", helper: "自我介绍、基础、项目、场景、收尾" },
  { id: "project3", label: "项目深挖 3 阶段", helper: "更适合 1 分钟内快速验证分身风格" },
  { id: "pressure4", label: "压力追问 4 阶段", helper: "更像真实技术面，追问会更密" },
  { id: "friendly3", label: "友好引导 3 阶段", helper: "适合面试官调研和轻量演示" },
];

export const defaultQuestionnaireForm: QuestionnaireForm = {
  interviewerName: "",
  interviewerUsername: "",
  company: "ali",
  role: "backend",
  styleIds: ["rigorous", "project", "structured"],
  focusIds: ["project_experience", "fundamentals", "system_design", "communication"],
  flowTemplate: "standard5",
  avatarApiKey: "",
  extraNotes: "",
  questionBankText: "",
};

export const flowStageCount = (template: FlowTemplate) => {
  if (template === "standard5") {
    return 5;
  }
  if (template === "pressure4") {
    return 4;
  }
  return 3;
};

export const normalizeQuestionnaireUsername = (value: string) =>
  value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_-]/g, "")
    .replace(/_{2,}/g, "_")
    .replace(/-{2,}/g, "-")
    .replace(/^[_-]+|[_-]+$/g, "");

export const isValidQuestionnaireUsername = (value: string) =>
  /^[a-z0-9_-]{3,32}$/.test(value);

export const buildQuestionnairePayload = (form: QuestionnaireForm): UpsertAdminInterviewerRequest => {
  const avatarApiKey = form.avatarApiKey.trim();
  const hasAvatarKey = avatarApiKey.length > 0;
  const questionBankText = form.questionBankText.trim();
  const roleLabel = roleLabelOf(form.role);
  const company = companyMeta[form.company];
  const styleLabels = selectedLabels(styleOptions, form.styleIds);
  const focusLabels = selectedLabels(focusOptions, form.focusIds);
  const interviewerId = createInterviewerId(
    form.role,
    normalizeQuestionnaireUsername(form.interviewerUsername),
  );
  const interviewerName =
    form.interviewerName.trim() || `${company.namePrefix}${roleLabel}面试官`;

  return {
    id: interviewerId,
    type: hasAvatarKey ? "avatar" : "system",
    provider: hasAvatarKey ? "secondme_visitor" : "doubao",
    name: interviewerName,
    title: hasAvatarKey ? "SecondMe 分身面试官" : "豆包系统面试官",
    description: `${company.promptLabel}风格的${roleLabel}面试官，关注${focusLabels.slice(0, 3).join("、")}。`,
    avatarUrl: `https://api.dicebear.com/9.x/bottts/svg?seed=${encodeURIComponent(interviewerId)}`,
    tags: [
      company.tag,
      roleLabel,
      ...styleLabels.slice(0, 2),
      hasAvatarKey ? "SecondMe" : "豆包",
      `user:${normalizeQuestionnaireUsername(form.interviewerUsername)}`,
    ],
    supportedRoles: [form.role],
    supportedModes: ["guided", "real"],
    persona: `一位${company.promptLabel}背景的${roleLabel}面试官，风格偏${styleLabels.join("、")}。`,
    promptStrategy: hasAvatarKey ? "avatar_skill" : "system_structured",
    skillPrompt: buildSkillPrompt(form),
    interviewFlow: buildInterviewFlow(form),
    avatarApiKey: hasAvatarKey ? avatarApiKey : null,
    enabled: true,
    ownedQuestions: questionBankText ? parseQuestionBankText(questionBankText, form.role) : undefined,
  };
};

const roleLabelOf = (role: InterviewRole) =>
  roleOptions.find((option) => option.value === role)?.label ?? role;

const selectedLabels = <T extends { id: string; label: string }>(options: T[], ids: string[]) =>
  options.filter((option) => ids.includes(option.id)).map((option) => option.label);

const selectedPrompts = <T extends { id: string; prompt: string }>(options: T[], ids: string[]) =>
  options.filter((option) => ids.includes(option.id)).map((option) => option.prompt);

const createInterviewerId = (role: InterviewRole, username: string) =>
  `questionnaire_${role}_${username}`.replace(/[^A-Za-z0-9_-]/g, "_");

const buildSkillPrompt = (form: QuestionnaireForm) => {
  const roleLabel = roleLabelOf(form.role);
  const company = companyMeta[form.company];
  const styles = selectedPrompts(styleOptions, form.styleIds);
  const focuses = selectedPrompts(focusOptions, form.focusIds);
  const extra = form.extraNotes.trim();

  return [
    `你是${company.promptLabel}的${roleLabel}面试官。`,
    "",
    "面试官风格：",
    ...styles.map((item) => `- ${item}`),
    "",
    "核心考察点：",
    ...focuses.map((item) => `- ${item}`),
    "",
    "提问规则：",
    "- 每轮只问一个主问题，候选人回答后再决定是否追问。",
    "- 优先追问候选人答案中的模糊点、缺失条件、真实数据和技术取舍。",
    "- 面试过程中不要提前给分，不要提前输出完整反馈。",
    "- 如果候选人回答很短，先要求补充背景、约束和思路，再进入下一题。",
    extra ? "" : null,
    extra ? "补充要求：" : null,
    extra || null,
  ]
    .filter((line): line is string => line !== null)
    .join("\n");
};

const buildInterviewFlow = (form: QuestionnaireForm) => {
  const roleLabel = roleLabelOf(form.role);

  if (form.flowTemplate === "project3") {
    return [
      "第1阶段：背景校准",
      `目标：让候选人用 1-2 分钟介绍${roleLabel}相关经历，确认最近一个最有代表性的项目。`,
      "问题方向：项目背景、本人职责、技术栈、最终结果。",
      "",
      "第2阶段：项目深挖",
      "目标：围绕一个项目连续追问技术难点、关键决策、故障处理、性能或效率指标。",
      "问题方向：为什么这么设计、替代方案是什么、线上风险怎么控制。",
      "",
      "第3阶段：总结收口",
      "目标：要求候选人复盘做得好的地方、遗憾点和下一次会如何优化。",
      "问题方向：经验沉淀、团队协作、未来改进。",
    ].join("\n");
  }

  if (form.flowTemplate === "pressure4") {
    return [
      "第1阶段：快速背景确认",
      `目标：快速判断候选人是否具备${roleLabel}岗位基础匹配度。`,
      "问题方向：最近项目、核心职责、最熟悉的技术领域。",
      "",
      "第2阶段：基础与边界追问",
      "目标：检查基础知识是否扎实，特别关注概念边界、异常情况和复杂度。",
      "问题方向：原理解释、常见错误、极端场景。",
      "",
      "第3阶段：高压场景题",
      "目标：观察候选人在约束变化、资源不足或线上事故场景下的拆解能力。",
      "问题方向：排障路径、优先级、监控指标、回滚方案。",
      "",
      "第4阶段：反思与收尾",
      "目标：要求候选人总结方案取舍和成长空间，不提前给完整反馈。",
      "问题方向：最大风险、如何验证、如果重做会改什么。",
    ].join("\n");
  }

  if (form.flowTemplate === "friendly3") {
    return [
      "第1阶段：轻量自我介绍",
      `目标：用友好方式了解候选人的${roleLabel}背景，降低紧张感。`,
      "问题方向：过往经历、最有成就感的项目、希望练习的方向。",
      "",
      "第2阶段：能力探索",
      "目标：从候选人熟悉领域出发，逐步检查基础、项目和解决问题能力。",
      "问题方向：一个真实问题如何拆解、如何协作、如何判断结果好坏。",
      "",
      "第3阶段：建议收口",
      "目标：让候选人补充未展示的亮点，并为后续反馈收集依据。",
      "问题方向：还有什么想补充、对岗位有什么问题、希望得到哪类建议。",
    ].join("\n");
  }

  return [
    "第1阶段：自我介绍与背景了解",
    `目标：了解候选人的${roleLabel}背景、技术栈、项目经历和表达能力。`,
    "问题方向：请简要介绍你的背景、最近项目、你负责的核心模块。",
    "",
    "第2阶段：岗位基础能力",
    "目标：检查岗位基础知识是否扎实，能否讲清原理、复杂度、边界条件和常见坑。",
    "问题方向：基础概念、常见场景题、关键技术原理。",
    "",
    "第3阶段：项目与工程实践",
    "目标：深挖候选人的真实项目经验，判断是否真正做过、理解过、复盘过。",
    "问题方向：技术难点、方案取舍、性能优化、故障处理、协作推进。",
    "",
    "第4阶段：系统设计或综合场景",
    "目标：评估候选人的拆解能力、架构意识、风险意识和可扩展思维。",
    "问题方向：设计一个高并发/高可用/可观测的业务系统，说明关键模块和取舍。",
    "",
    "第5阶段：总结与候选人提问",
    "目标：让候选人补充亮点、提问，并为最终反馈收集最后信息。",
    "问题方向：你还有什么想补充？你对岗位或团队有什么问题？",
  ].join("\n");
};
