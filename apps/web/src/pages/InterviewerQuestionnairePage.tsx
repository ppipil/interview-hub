import { useState } from "react";
import type { ReactNode } from "react";

import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, Sparkles } from "lucide-react";

import { roleOptions } from "../config/interviewOptions";
import { ApiClientError, adminApi } from "../services/api";
import { useInterviewStore } from "../store/useInterviewStore";
import type {
  AdminInterviewer,
  InterviewRole,
  UpsertAdminInterviewerRequest,
} from "../types";

type CompanyPreset = "ali" | "startup" | "global" | "state_owned" | "internet";
type FlowTemplate = "standard5" | "project3" | "pressure4" | "friendly3";

interface QuestionnaireForm {
  company: CompanyPreset;
  role: InterviewRole;
  styleIds: string[];
  focusIds: string[];
  flowTemplate: FlowTemplate;
  avatarApiKey: string;
  extraNotes: string;
}

interface OptionItem<T extends string> {
  id: T;
  label: string;
  helper: string;
}

const companyOptions: OptionItem<CompanyPreset>[] = [
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

const styleOptions = [
  { id: "rigorous", label: "严谨深入", prompt: "追求答案的准确性、边界条件和技术深度。" },
  { id: "project", label: "项目深挖", prompt: "优先从候选人的真实项目切入，持续追问取舍、数据和结果。" },
  { id: "structured", label: "结构化评分", prompt: "按知识、经验、表达、问题解决能力进行结构化判断。" },
  { id: "concise", label: "简洁直接", prompt: "问题短、目标明确，不做冗长铺垫。" },
  { id: "pressure", label: "适度压力", prompt: "在关键回答含糊时追问细节，但保持专业和尊重。" },
  { id: "friendly", label: "友好引导", prompt: "语气温和，允许候选人补充思考过程。" },
];

const focusOptions = [
  { id: "project_experience", label: "项目经验", prompt: "项目背景、职责边界、技术难点、结果指标。" },
  { id: "fundamentals", label: "基础知识", prompt: "岗位基础概念、原理解释、常见坑和边界条件。" },
  { id: "system_design", label: "系统设计", prompt: "架构拆分、可扩展性、性能、稳定性和容错。" },
  { id: "algorithm", label: "算法 / 数据结构", prompt: "复杂度、数据结构选择、常见题型思路。" },
  { id: "communication", label: "沟通表达", prompt: "表达是否清晰、能否讲清取舍和协作方式。" },
  { id: "business", label: "业务理解", prompt: "能否把技术方案和业务目标、用户价值连接起来。" },
];

const flowOptions: OptionItem<FlowTemplate>[] = [
  { id: "standard5", label: "标准 5 阶段", helper: "自我介绍、基础、项目、场景、收尾" },
  { id: "project3", label: "项目深挖 3 阶段", helper: "更适合 1 分钟内快速验证分身风格" },
  { id: "pressure4", label: "压力追问 4 阶段", helper: "更像真实技术面，追问会更密" },
  { id: "friendly3", label: "友好引导 3 阶段", helper: "适合面试官调研和轻量演示" },
];

const defaultForm: QuestionnaireForm = {
  company: "ali",
  role: "backend",
  styleIds: ["rigorous", "project", "structured"],
  focusIds: ["project_experience", "fundamentals", "system_design", "communication"],
  flowTemplate: "standard5",
  avatarApiKey: "",
  extraNotes: "",
};

const roleLabelOf = (role: InterviewRole) =>
  roleOptions.find((option) => option.value === role)?.label ?? role;

const selectedLabels = <T extends { id: string; label: string }>(options: T[], ids: string[]) =>
  options.filter((option) => ids.includes(option.id)).map((option) => option.label);

const selectedPrompts = <T extends { id: string; prompt: string }>(options: T[], ids: string[]) =>
  options.filter((option) => ids.includes(option.id)).map((option) => option.prompt);

const createInterviewerId = (role: InterviewRole) =>
  `questionnaire_${role}_${Date.now().toString(36)}`.replace(/[^A-Za-z0-9_-]/g, "_");

const flowStageCount = (template: FlowTemplate) => {
  if (template === "standard5") {
    return 5;
  }
  if (template === "pressure4") {
    return 4;
  }
  return 3;
};

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

const buildPayload = (form: QuestionnaireForm): UpsertAdminInterviewerRequest => {
  const avatarApiKey = form.avatarApiKey.trim();
  const hasAvatarKey = avatarApiKey.length > 0;
  const roleLabel = roleLabelOf(form.role);
  const company = companyMeta[form.company];
  const styleLabels = selectedLabels(styleOptions, form.styleIds);
  const focusLabels = selectedLabels(focusOptions, form.focusIds);
  const interviewerId = createInterviewerId(form.role);

  return {
    id: interviewerId,
    type: hasAvatarKey ? "avatar" : "system",
    provider: hasAvatarKey ? "secondme_visitor" : "doubao",
    name: `${company.namePrefix}${roleLabel}面试官`,
    title: hasAvatarKey ? "SecondMe 分身面试官" : "豆包系统面试官",
    description: `${company.promptLabel}风格的${roleLabel}面试官，关注${focusLabels.slice(0, 3).join("、")}。`,
    avatarUrl: `https://api.dicebear.com/9.x/bottts/svg?seed=${encodeURIComponent(interviewerId)}`,
    tags: [company.tag, roleLabel, ...styleLabels.slice(0, 2), hasAvatarKey ? "SecondMe" : "豆包"],
    supportedRoles: [form.role],
    supportedModes: ["guided", "real"],
    persona: `一位${company.promptLabel}背景的${roleLabel}面试官，风格偏${styleLabels.join("、")}。`,
    promptStrategy: hasAvatarKey ? "avatar_skill" : "system_structured",
    skillPrompt: buildSkillPrompt(form),
    interviewFlow: buildInterviewFlow(form),
    avatarApiKey: hasAvatarKey ? avatarApiKey : null,
    enabled: true,
  };
};

const getErrorMessage = (error: unknown) => {
  if (error instanceof ApiClientError) {
    return error.response.error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "创建失败，请稍后再试。";
};

export const InterviewerQuestionnairePage = () => {
  const [form, setForm] = useState<QuestionnaireForm>(defaultForm);
  const [createdInterviewer, setCreatedInterviewer] = useState<AdminInterviewer | null>(null);
  const [requestState, setRequestState] = useState<"idle" | "saving">("idle");
  const [error, setError] = useState<string | null>(null);
  const fetchInterviewers = useInterviewStore((state) => state.fetchInterviewers);
  const updateSetup = useInterviewStore((state) => state.updateSetup);
  const setStage = useInterviewStore((state) => state.setStage);

  const updateForm = (patch: Partial<QuestionnaireForm>) => {
    setForm((current) => ({ ...current, ...patch }));
    setError(null);
    setCreatedInterviewer(null);
  };

  const toggleLimited = (field: "styleIds" | "focusIds", id: string, limit: number) => {
    setForm((current) => {
      const exists = current[field].includes(id);
      const nextValues = exists
        ? current[field].filter((item) => item !== id)
        : [...current[field], id].slice(-limit);
      return { ...current, [field]: nextValues };
    });
    setError(null);
    setCreatedInterviewer(null);
  };

  const submitQuestionnaire = async () => {
    if (!form.styleIds.length || !form.focusIds.length) {
      setError("至少保留一个风格和一个考察点。");
      return;
    }

    setRequestState("saving");
    setError(null);
    setCreatedInterviewer(null);

    try {
      const payload = buildPayload(form);
      const response = await adminApi.createInterviewer(payload);
      setCreatedInterviewer(response.data);
    } catch (currentError) {
      setError(getErrorMessage(currentError));
    } finally {
      setRequestState("idle");
    }
  };

  const goToSetup = async () => {
    if (!createdInterviewer) {
      return;
    }

    await fetchInterviewers(form.role);
    updateSetup({
      role: form.role,
      mode: "guided",
      totalRounds: flowStageCount(form.flowTemplate),
    });
    updateSetup({ interviewerId: createdInterviewer.id });
    setStage("setup");
    window.history.pushState({}, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  const sourceLabel = form.avatarApiKey.trim() ? "SecondMe 分身面试官" : "豆包系统面试官";
  const goHome = () => {
    window.history.pushState({}, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));
  };

  return (
    <main className="min-h-screen overflow-hidden bg-[#f6f0e5] text-slate-950">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(15,23,42,0.12),transparent_26%),radial-gradient(circle_at_88%_12%,rgba(14,165,233,0.18),transparent_24%),linear-gradient(135deg,rgba(255,255,255,0.86),rgba(246,240,229,0.7))]" />
      <div className="relative mx-auto grid min-h-screen max-w-7xl gap-6 px-4 py-5 sm:px-6 lg:grid-cols-[0.86fr_1.14fr] lg:px-8 lg:py-8">
        <section className="flex flex-col justify-between rounded-[2.25rem] bg-slate-950 p-6 text-white shadow-2xl shadow-slate-950/25 sm:p-8">
          <div>
            <button
              className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm font-bold text-slate-200 transition hover:border-white/30 hover:bg-white/10"
              onClick={goHome}
              type="button"
            >
              <ArrowLeft className="h-4 w-4" />
              回到首页
            </button>

            <div className="mt-12 space-y-5">
              <p className="w-fit rounded-full bg-cyan-300 px-3 py-1 text-xs font-black uppercase tracking-[0.28em] text-slate-950">
                1-minute Builder
              </p>
              <h1 className="max-w-xl font-heading text-4xl font-black leading-tight tracking-tight sm:text-5xl">
                让真实面试官，快速变成可练习的 AI 面试官。
              </h1>
              <p className="max-w-lg text-base leading-8 text-slate-300">
                这张问卷先服务内测：多数题都有默认值，面试官懒得写也能提交。填了 SecondMe API Key
                就走分身，不填就自动创建豆包系统面试官。
              </p>
            </div>
          </div>

          <div className="mt-10 grid gap-3 text-sm text-slate-300 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            <InfoTile label="01" text="选公司气质和岗位" />
            <InfoTile label="02" text="勾风格和考察点" />
            <InfoTile label="03" text="一键写入面试官库" />
          </div>
        </section>

        <section className="rounded-[2.25rem] border border-slate-950/10 bg-white/86 p-4 shadow-2xl shadow-slate-900/10 backdrop-blur sm:p-6">
          <div className="mb-5 flex flex-col gap-3 border-b border-slate-950/10 pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-500">Questionnaire</p>
              <h2 className="mt-2 font-heading text-3xl font-black tracking-tight text-slate-950">
                面试官快速录入
              </h2>
            </div>
            <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-black text-slate-700">
              当前将创建：{sourceLabel}
            </div>
          </div>

          {createdInterviewer ? (
            <div className="mb-5 rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-950">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
                <div>
                  <p className="font-black">已加入后端面试官数据库：{createdInterviewer.name}</p>
                  <p className="mt-1 text-sm leading-6 text-emerald-800">
                    现在可以去设置页选择它测试。如果想继续采访另一位面试官，也可以直接改问卷再提交一份。
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          {error ? (
            <div className="mb-5 rounded-3xl border border-red-200 bg-red-50 p-4 text-sm font-bold text-red-800">
              {error}
            </div>
          ) : null}

          <div className="space-y-5">
            <Field label="1. 这位面试官更像哪类公司？" hint="默认选阿里/大厂，适合你现在的后端测试号。">
              <OptionGrid>
                {companyOptions.map((option) => (
                  <OptionButton
                    key={option.id}
                    active={form.company === option.id}
                    helper={option.helper}
                    label={option.label}
                    onClick={() => updateForm({ company: option.id })}
                  />
                ))}
              </OptionGrid>
            </Field>

            <Field label="2. TA 主要面什么岗位？" hint="这会决定设置页筛选和生成出来的 skill 重点。">
              <select
                className="admin-input max-w-md"
                value={form.role}
                onChange={(event) => updateForm({ role: event.target.value as InterviewRole })}
              >
                {roleOptions.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="3. 面试风格，最多选 3 个" hint="如果不想想，保留默认就可以。">
              <ChipGrid>
                {styleOptions.map((style) => (
                  <ToggleChip
                    key={style.id}
                    active={form.styleIds.includes(style.id)}
                    label={style.label}
                    onClick={() => toggleLimited("styleIds", style.id, 3)}
                  />
                ))}
              </ChipGrid>
            </Field>

            <Field label="4. 核心考察点，最多选 4 个">
              <ChipGrid>
                {focusOptions.map((focus) => (
                  <ToggleChip
                    key={focus.id}
                    active={form.focusIds.includes(focus.id)}
                    label={focus.label}
                    onClick={() => toggleLimited("focusIds", focus.id, 4)}
                  />
                ))}
              </ChipGrid>
            </Field>

            <Field label="5. 面试流程模板" hint="它会写入 interviewFlow，后端会按轮次把对应阶段作为硬约束发给 AI。">
              <OptionGrid>
                {flowOptions.map((option) => (
                  <OptionButton
                    key={option.id}
                    active={form.flowTemplate === option.id}
                    helper={option.helper}
                    label={option.label}
                    onClick={() => updateForm({ flowTemplate: option.id })}
                  />
                ))}
              </OptionGrid>
            </Field>

            <Field
              label="6. SecondMe Avatar API Key，可不填"
              hint="填 sk-... 就创建 AI 分身面试官；不填就创建豆包系统面试官，后续也能在隐藏管理台补 key。"
            >
              <input
                className="admin-input max-w-2xl font-mono"
                value={form.avatarApiKey}
                placeholder="sk-...（可选）"
                onChange={(event) => updateForm({ avatarApiKey: event.target.value })}
              />
            </Field>

            <Field label="7. 补充要求，可不填" hint="比如：必须问一次 CAP；不要太温柔；更关注线上排障。">
              <textarea
                className="admin-textarea min-h-28"
                value={form.extraNotes}
                placeholder="可留空，默认会生成一套可用 skill。"
                onChange={(event) => updateForm({ extraNotes: event.target.value })}
              />
            </Field>
          </div>

          <div className="mt-7 flex flex-col gap-3 border-t border-slate-950/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-semibold leading-6 text-slate-500">
              提交后会自动生成名称、persona、skill、流程和标签，并保存到数据库。
            </p>
            <div className="flex flex-wrap gap-3">
              {createdInterviewer ? (
                <button
                  className="rounded-full border border-slate-950/15 px-5 py-3 text-sm font-black text-slate-800 transition hover:bg-slate-100"
                  onClick={() => {
                    void goToSetup();
                  }}
                  type="button"
                >
                  去设置页选择它
                </button>
              ) : null}
              <button
                className="inline-flex items-center justify-center gap-2 rounded-full bg-slate-950 px-6 py-3 text-sm font-black text-white shadow-xl shadow-slate-950/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={requestState === "saving"}
                onClick={() => {
                  void submitQuestionnaire();
                }}
                type="button"
              >
                {requestState === "saving" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {requestState === "saving" ? "正在写入数据库" : "生成并加入面试官库"}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

interface FieldProps {
  label: string;
  hint?: string;
  children: ReactNode;
}

const Field = ({ label, hint, children }: FieldProps) => (
  <section className="space-y-3">
    <div>
      <h3 className="text-sm font-black text-slate-950">{label}</h3>
      {hint ? <p className="mt-1 text-xs font-semibold leading-5 text-slate-500">{hint}</p> : null}
    </div>
    {children}
  </section>
);

const OptionGrid = ({ children }: { children: ReactNode }) => (
  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{children}</div>
);

const ChipGrid = ({ children }: { children: ReactNode }) => (
  <div className="flex flex-wrap gap-2">{children}</div>
);

interface OptionButtonProps {
  active: boolean;
  label: string;
  helper: string;
  onClick: () => void;
}

const OptionButton = ({ active, label, helper, onClick }: OptionButtonProps) => (
  <button
    className={[
      "min-h-24 rounded-3xl border p-4 text-left transition",
      active
        ? "border-slate-950 bg-slate-950 text-white shadow-xl shadow-slate-950/15"
        : "border-slate-950/10 bg-white/70 text-slate-900 hover:border-slate-950/25 hover:bg-white",
    ].join(" ")}
    onClick={onClick}
    type="button"
  >
    <span className="block text-sm font-black">{label}</span>
    <span className={["mt-2 block text-xs leading-5", active ? "text-slate-300" : "text-slate-500"].join(" ")}>
      {helper}
    </span>
  </button>
);

interface ToggleChipProps {
  active: boolean;
  label: string;
  onClick: () => void;
}

const ToggleChip = ({ active, label, onClick }: ToggleChipProps) => (
  <button
    className={[
      "rounded-full border px-4 py-2 text-sm font-black transition",
      active
        ? "border-cyan-400 bg-cyan-300 text-slate-950 shadow-lg shadow-cyan-900/10"
        : "border-slate-950/10 bg-white/70 text-slate-600 hover:bg-white",
    ].join(" ")}
    onClick={onClick}
    type="button"
  >
    {label}
  </button>
);

const InfoTile = ({ label, text }: { label: string; text: string }) => (
  <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-4">
    <p className="text-xs font-black tracking-[0.2em] text-cyan-200">{label}</p>
    <p className="mt-2 font-bold leading-6 text-white">{text}</p>
  </div>
);
