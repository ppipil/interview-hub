import { useState } from "react";
import type { ReactNode } from "react";

import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, Sparkles } from "lucide-react";

import { roleOptions } from "../config/interviewOptions";
import { questionBankTextareaHint } from "../config/questionBank";
import {
  buildQuestionnairePayload,
  companyOptions,
  defaultQuestionnaireForm,
  flowOptions,
  flowStageCount,
  focusOptions,
  isValidQuestionnaireUsername,
  normalizeQuestionnaireUsername,
  styleOptions,
  type QuestionnaireForm,
} from "../config/interviewerQuestionnaire";
import { ApiClientError, adminApi } from "../services/api";
import { useInterviewStore } from "../store/useInterviewStore";
import type { AdminInterviewer, InterviewRole } from "../types";

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
  const [form, setForm] = useState<QuestionnaireForm>(defaultQuestionnaireForm);
  const [createdInterviewer, setCreatedInterviewer] = useState<AdminInterviewer | null>(null);
  const [requestState, setRequestState] = useState<"idle" | "saving">("idle");
  const [error, setError] = useState<string | null>(null);
  const fetchInterviewers = useInterviewStore((state) => state.fetchInterviewers);
  const updateSetup = useInterviewStore((state) => state.updateSetup);
  const setStage = useInterviewStore((state) => state.setStage);
  const normalizedUsername = normalizeQuestionnaireUsername(form.interviewerUsername);

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

  const importQuestionBankFile = async (file: File | undefined) => {
    if (!file) {
      return;
    }
    const text = await file.text();
    updateForm({ questionBankText: text });
  };

  const submitQuestionnaire = async () => {
    if (!isValidQuestionnaireUsername(normalizedUsername)) {
      setError("面试官用户名只支持 3-32 位英文、数字、_、-。如果你填的是中文，请换成拼音或英文标识。");
      return;
    }

    if (!form.styleIds.length || !form.focusIds.length) {
      setError("至少保留一个风格和一个考察点。");
      return;
    }

    setRequestState("saving");
    setError(null);
    setCreatedInterviewer(null);

    try {
      const payload = buildQuestionnairePayload(form);
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
  };

  const sourceLabel = form.avatarApiKey.trim() ? "SecondMe 分身面试官" : "豆包系统面试官";
  const goHome = () => {
    setStage("home");
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
                这张问卷先服务内测：面试官信息和风格通过选择题快速收集，题库不再由系统自动生成。填了 SecondMe
                API Key 就走分身，不填就自动创建豆包系统面试官。
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
                    现在可以去设置页选择它测试。后续如果继续使用同一个用户名提交，会更新这位面试官和它绑定的专属题库。
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
            <Field
              label="1. 面试官姓名，可不填"
              hint="这是展示给候选人的名字；留空时系统会自动生成“阿里后端面试官”这类名称。"
            >
              <input
                className="admin-input max-w-2xl"
                value={form.interviewerName}
                placeholder="比如：李扬 / Alice / 阿里后端技术面试官"
                onChange={(event) => updateForm({ interviewerName: event.target.value })}
              />
            </Field>

            <Field
              label="2. 面试官用户名，必填"
              hint="题库和面试官识别都按这个用户名绑定。同一个用户名再次提交时，会更新同一位面试官和它的专属题库。"
            >
              <div className="space-y-2">
                <input
                  className="admin-input max-w-2xl font-mono"
                  value={form.interviewerUsername}
                  placeholder="比如：liyang_backend"
                  onChange={(event) => updateForm({ interviewerUsername: event.target.value })}
                />
                <p className="text-xs font-semibold leading-5 text-slate-500">
                  将保存为：
                  <span className="ml-1 font-mono text-slate-700">
                    {normalizedUsername || "请输入 3-32 位英文、数字、_、-"}
                  </span>
                </p>
              </div>
            </Field>

            <Field label="3. 这位面试官更像哪类公司？" hint="默认选阿里/大厂，适合你现在的后端测试号。">
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

            <Field label="4. TA 主要面什么岗位？" hint="这会决定设置页筛选和生成出来的 skill 重点。">
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

            <Field label="5. 面试风格，最多选 3 个" hint="如果不想想，保留默认就可以。">
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

            <Field label="6. 核心考察点，最多选 4 个">
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

            <Field label="7. 面试流程模板" hint="它会写入 interviewFlow，后端会按轮次把对应阶段作为硬约束发给 AI。">
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
              label="8. SecondMe Avatar API Key，可不填"
              hint="填 sk-... 就创建 AI 分身面试官；不填就创建豆包系统面试官，后续也能在隐藏管理台补 key。"
            >
              <input
                className="admin-input max-w-2xl font-mono"
                value={form.avatarApiKey}
                placeholder="sk-...（可选）"
                onChange={(event) => updateForm({ avatarApiKey: event.target.value })}
              />
            </Field>

            <Field label="9. 补充要求，可不填" hint="比如：必须问一次 CAP；不要太温柔；更关注线上排障。">
              <textarea
                className="admin-textarea min-h-28"
                value={form.extraNotes}
                placeholder="可留空，这里只会影响面试官 persona / skill，不会自动生成题库。"
                onChange={(event) => updateForm({ extraNotes: event.target.value })}
              />
            </Field>

            <Field
              label="10. 面试官专属题库，可选上传/粘贴"
              hint={`${questionBankTextareaHint}。这些题会绑定到当前用户名对应的面试官；初版只传专业八股题就行，自我介绍和收尾会走通用题库。`}
            >
              <div className="space-y-3">
                <input
                  className="block w-full rounded-2xl border border-dashed border-slate-900/20 bg-white/70 p-4 text-sm font-semibold"
                  type="file"
                  accept=".txt,.md,text/plain,text/markdown"
                  onChange={(event) => {
                    void importQuestionBankFile(event.target.files?.[0]);
                    event.target.value = "";
                  }}
                />
                <textarea
                  className="admin-textarea min-h-48 font-mono text-sm"
                  value={form.questionBankText}
                  placeholder={
                    "请解释一下 Redis 为什么快？ | 优秀回答应覆盖内存、数据结构、IO 模型和使用场景。 | Redis,缓存\nMySQL 索引为什么会失效？ | 优秀回答应讲清常见失效场景和排查方法。 | MySQL,索引"
                  }
                  onChange={(event) => updateForm({ questionBankText: event.target.value })}
                />
              </div>
            </Field>
          </div>

          <div className="mt-7 flex flex-col gap-3 border-t border-slate-950/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-semibold leading-6 text-slate-500">
              提交后会自动生成名称、persona、skill、流程和标签；只有你手动粘贴或上传的题库，才会作为当前用户名对应面试官的专属题库入库。
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
