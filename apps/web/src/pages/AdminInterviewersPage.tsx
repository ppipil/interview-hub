import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { adminApi } from "../services/api";
import {
  INTERVIEWER_PROVIDERS,
  INTERVIEWER_TYPES,
  type AdminInterviewer,
  type InterviewMode,
  type InterviewRole,
  type InterviewerProvider,
  type InterviewerType,
  type UpsertAdminInterviewerRequest,
} from "../types";
import { modeOptions, roleOptions } from "../config/interviewOptions";

type RequestState = "idle" | "loading" | "saving" | "deleting";

interface AdminFormState {
  id: string;
  type: InterviewerType;
  provider: InterviewerProvider;
  name: string;
  title: string;
  description: string;
  avatarUrl: string;
  tagsText: string;
  supportedRoles: InterviewRole[];
  supportedModes: InterviewMode[];
  persona: string;
  promptStrategy: string;
  skillPrompt: string;
  interviewFlow: string;
  avatarApiKey: string;
  enabled: boolean;
}

const providerLabels: Record<InterviewerProvider, string> = {
  doubao: "豆包",
  secondme_legacy: "SecondMe Legacy",
  secondme_visitor: "SecondMe Visitor Chat",
};

const typeLabels: Record<InterviewerType, string> = {
  system: "系统面试官",
  avatar: "AI 分身面试官",
};

const emptyForm = (): AdminFormState => ({
  id: "",
  type: "avatar",
  provider: "secondme_visitor",
  name: "",
  title: "",
  description: "",
  avatarUrl: "",
  tagsText: "SecondMe, 分身",
  supportedRoles: ["frontend", "backend", "product_manager", "operations", "data_analyst"],
  supportedModes: ["guided", "real"],
  persona: "",
  promptStrategy: "avatar_skill",
  skillPrompt: "",
  interviewFlow: "",
  avatarApiKey: "",
  enabled: true,
});

const formFromInterviewer = (interviewer: AdminInterviewer): AdminFormState => ({
  id: interviewer.id,
  type: interviewer.type,
  provider: interviewer.provider,
  name: interviewer.name,
  title: interviewer.title,
  description: interviewer.description,
  avatarUrl: interviewer.avatarUrl,
  tagsText: interviewer.tags?.join(", ") ?? "",
  supportedRoles: interviewer.supportedRoles ?? [],
  supportedModes: interviewer.supportedModes,
  persona: interviewer.persona ?? "",
  promptStrategy: interviewer.promptStrategy ?? "",
  skillPrompt: interviewer.skillPrompt ?? "",
  interviewFlow: interviewer.interviewFlow ?? "",
  avatarApiKey: interviewer.avatarApiKey ?? "",
  enabled: interviewer.enabled,
});

const splitTags = (value: string) =>
  value
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);

const isProviderAllowed = (type: InterviewerType, provider: InterviewerProvider) => {
  if (type === "system") {
    return provider === "doubao";
  }
  return provider !== "doubao";
};

const nextProviderForType = (type: InterviewerType, currentProvider: InterviewerProvider): InterviewerProvider => {
  if (isProviderAllowed(type, currentProvider)) {
    return currentProvider;
  }
  return type === "system" ? "doubao" : "secondme_visitor";
};

const defaultPromptStrategy = (type: InterviewerType) => (type === "system" ? "system_structured" : "avatar_skill");

export const AdminInterviewersPage = () => {
  const [interviewers, setInterviewers] = useState<AdminInterviewer[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState<AdminFormState>(() => emptyForm());
  const [isCreating, setIsCreating] = useState(false);
  const [requestState, setRequestState] = useState<RequestState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isAvatarKeyVisible, setIsAvatarKeyVisible] = useState(false);

  const selectedInterviewer = useMemo(
    () => interviewers.find((item) => item.id === selectedId) ?? null,
    [interviewers, selectedId],
  );
  const hasFullAvatarApiKey = form.avatarApiKey.trim().length > 0;

  const loadInterviewers = async () => {
    setRequestState("loading");
    setError(null);
    try {
      const response = await adminApi.getInterviewers();
      setInterviewers(response.data);
      if (!selectedId && response.data[0]) {
        setSelectedId(response.data[0].id);
        setForm(formFromInterviewer(response.data[0]));
        setIsCreating(false);
      }
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "管理台加载失败。");
    } finally {
      setRequestState("idle");
    }
  };

  useEffect(() => {
    void loadInterviewers();
  }, []);

  const selectInterviewer = (interviewer: AdminInterviewer) => {
    setSelectedId(interviewer.id);
    setForm(formFromInterviewer(interviewer));
    setIsCreating(false);
    setNotice(null);
    setError(null);
    setIsAvatarKeyVisible(false);
  };

  const startCreating = () => {
    setSelectedId(null);
    setForm(emptyForm());
    setIsCreating(true);
    setNotice(null);
    setError(null);
    setIsAvatarKeyVisible(false);
  };

  const updateForm = (patch: Partial<AdminFormState>) => {
    setForm((current) => ({ ...current, ...patch }));
  };

  const toggleRole = (role: InterviewRole) => {
    setForm((current) => ({
      ...current,
      supportedRoles: current.supportedRoles.includes(role)
        ? current.supportedRoles.filter((item) => item !== role)
        : [...current.supportedRoles, role],
    }));
  };

  const toggleMode = (mode: InterviewMode) => {
    setForm((current) => ({
      ...current,
      supportedModes: current.supportedModes.includes(mode)
        ? current.supportedModes.filter((item) => item !== mode)
        : [...current.supportedModes, mode],
    }));
  };

  const importSkillFile = async (file: File | undefined) => {
    if (!file) {
      return;
    }
    const text = await file.text();
    updateForm({ skillPrompt: text });
    setNotice(`已读取 ${file.name}，保存后会写入数据库。`);
  };

  const buildPayload = (): UpsertAdminInterviewerRequest => ({
    id: form.id.trim(),
    type: form.type,
    provider: form.provider,
    name: form.name.trim(),
    title: form.title.trim(),
    description: form.description.trim(),
    avatarUrl: form.avatarUrl.trim() || null,
    tags: splitTags(form.tagsText),
    supportedRoles: form.supportedRoles,
    supportedModes: form.supportedModes,
    persona: form.persona.trim() || null,
    promptStrategy: form.promptStrategy.trim() || defaultPromptStrategy(form.type),
    skillPrompt: form.skillPrompt.trim() || null,
    interviewFlow: form.interviewFlow.trim() || null,
    avatarApiKey: form.avatarApiKey.trim() || null,
    enabled: form.enabled,
  });

  const saveInterviewer = async () => {
    setRequestState("saving");
    setError(null);
    setNotice(null);
    try {
      const payload = buildPayload();
      const response = isCreating
        ? await adminApi.createInterviewer(payload)
        : await adminApi.updateInterviewer(payload.id, payload);
      await loadInterviewers();
      setSelectedId(response.data.id);
      setForm({
        ...formFromInterviewer(response.data),
        avatarApiKey: response.data.avatarApiKey ?? payload.avatarApiKey ?? "",
      });
      setIsCreating(false);
      setIsAvatarKeyVisible(false);
      setNotice("已保存到数据库，回到设置页后会读取新的面试官配置。");
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "保存失败。");
    } finally {
      setRequestState("idle");
    }
  };

  const deleteInterviewer = async () => {
    if (!selectedId || !window.confirm("确认删除这条数据库配置吗？默认面试官会恢复为本地配置，自定义面试官会从列表消失。")) {
      return;
    }
    setRequestState("deleting");
    setError(null);
    setNotice(null);
    try {
      await adminApi.deleteInterviewer(selectedId);
      setSelectedId(null);
      setForm(emptyForm());
      setIsCreating(true);
      setIsAvatarKeyVisible(false);
      await loadInterviewers();
      setNotice("已删除数据库配置。");
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "删除失败。");
    } finally {
      setRequestState("idle");
    }
  };

  return (
    <main className="min-h-screen bg-[#0d1117] px-4 py-5 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-[340px_1fr]">
        <section className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/30 backdrop-blur">
          <div className="mb-6 space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-300">Hidden Admin</p>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white">面试官管理台</h1>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  本页不挂主导航，用于内测录入面试官资料、SecondMe key 和 Interview Hub skill。
                </p>
              </div>
              <button
                className="rounded-full border border-cyan-300/30 px-3 py-2 text-xs font-bold text-cyan-200 transition hover:bg-cyan-300/10"
                onClick={startCreating}
              >
                新增
              </button>
            </div>
          </div>

          {error ? (
            <div className="mb-4 rounded-3xl border border-red-400/30 bg-red-500/10 p-4 text-sm leading-6 text-red-100">
              {error}
            </div>
          ) : null}

          <div className="space-y-3">
            {requestState === "loading" ? (
              <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-4 text-sm text-slate-400">
                正在读取面试官配置...
              </div>
            ) : null}

            {interviewers.map((interviewer) => (
              <button
                key={interviewer.id}
                className={[
                  "w-full rounded-3xl border p-4 text-left transition",
                  selectedId === interviewer.id
                    ? "border-cyan-300/60 bg-cyan-300/10 shadow-lg shadow-cyan-950/40"
                    : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.06]",
                ].join(" ")}
                onClick={() => selectInterviewer(interviewer)}
              >
                <div className="flex items-start gap-3">
                  <img
                    src={interviewer.avatarUrl}
                    alt={interviewer.name}
                    className="h-12 w-12 rounded-2xl border border-white/10 bg-slate-900 object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate text-sm font-black text-white">{interviewer.name}</p>
                      <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold text-slate-300">
                        {typeLabels[interviewer.type]}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{interviewer.title}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-bold">
                      <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-emerald-200">
                        {providerLabels[interviewer.provider]}
                      </span>
                      <span className="rounded-full bg-white/10 px-2 py-1 text-slate-300">
                        {interviewer.profileExists ? "DB profile" : "默认配置"}
                      </span>
                      <span className="rounded-full bg-white/10 px-2 py-1 text-slate-300">
                        {interviewer.hasAvatarApiKey ? interviewer.avatarApiKeyMasked ?? "key 已保存" : "未存 key"}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-[#f4efe4] p-4 text-slate-950 shadow-2xl shadow-black/20 sm:p-6">
          <div className="mb-6 flex flex-col gap-3 border-b border-slate-900/10 pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.3em] text-slate-500">
                {isCreating ? "Create Profile" : "Edit Profile"}
              </p>
              <h2 className="mt-2 text-3xl font-black tracking-tight">
                {isCreating ? "录入新的面试官" : selectedInterviewer?.name ?? "选择一个面试官"}
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                className="rounded-full bg-slate-950 px-5 py-3 text-sm font-black text-white transition hover:-translate-y-0.5 disabled:opacity-50"
                disabled={requestState === "saving"}
                onClick={() => {
                  void saveInterviewer();
                }}
              >
                {requestState === "saving" ? "保存中..." : "保存"}
              </button>
              <button
                className="rounded-full border border-slate-950/20 px-5 py-3 text-sm font-black text-slate-800 transition hover:bg-white disabled:opacity-50"
                disabled={isCreating || !selectedInterviewer?.profileExists || requestState === "deleting"}
                onClick={() => {
                  void deleteInterviewer();
                }}
              >
                删除/恢复默认
              </button>
            </div>
          </div>

          {notice ? (
            <div className="mb-5 rounded-3xl border border-emerald-700/20 bg-emerald-100 p-4 text-sm font-semibold text-emerald-900">
              {notice}
            </div>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            <Field label="面试官 ID" hint="只支持英文、数字、下划线和连字符。">
              <input
                className="admin-input"
                value={form.id}
                disabled={!isCreating}
                placeholder="例如 secondme_tech"
                onChange={(event) => updateForm({ id: event.target.value })}
              />
            </Field>

            <Field label="启用状态">
              <label className="flex h-12 items-center gap-3 rounded-2xl border border-slate-900/10 bg-white/70 px-4 text-sm font-bold">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(event) => updateForm({ enabled: event.target.checked })}
                />
                在设置页显示这个面试官
              </label>
            </Field>

            <Field label="面试官类型">
              <div className="grid grid-cols-2 gap-2">
                {INTERVIEWER_TYPES.map((type) => (
                  <button
                    key={type}
                    className={[
                      "rounded-2xl border px-4 py-3 text-sm font-black transition",
                      form.type === type
                        ? "border-slate-950 bg-slate-950 text-white"
                        : "border-slate-900/10 bg-white/70 text-slate-700 hover:bg-white",
                    ].join(" ")}
                    onClick={() =>
                      updateForm({
                        type,
                        provider: nextProviderForType(type, form.provider),
                        promptStrategy: defaultPromptStrategy(type),
                      })
                    }
                    type="button"
                  >
                    {typeLabels[type]}
                  </button>
                ))}
              </div>
            </Field>

            <Field label="Provider">
              <select
                className="admin-input"
                value={form.provider}
                onChange={(event) => updateForm({ provider: event.target.value as InterviewerProvider })}
              >
                {INTERVIEWER_PROVIDERS.filter((provider) => isProviderAllowed(form.type, provider)).map((provider) => (
                  <option key={provider} value={provider}>
                    {providerLabels[provider]}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="名称">
              <input
                className="admin-input"
                value={form.name}
                placeholder="例如 王老师技术面试官"
                onChange={(event) => updateForm({ name: event.target.value })}
              />
            </Field>

            <Field label="标题">
              <input
                className="admin-input"
                value={form.title}
                placeholder="例如 前端项目深挖官"
                onChange={(event) => updateForm({ title: event.target.value })}
              />
            </Field>

            <Field label="头像 URL">
              <input
                className="admin-input"
                value={form.avatarUrl}
                placeholder="留空会自动用 DiceBear 生成"
                onChange={(event) => updateForm({ avatarUrl: event.target.value })}
              />
            </Field>

            <Field label="标签" hint="用逗号分隔。">
              <input
                className="admin-input"
                value={form.tagsText}
                placeholder="SecondMe, 技术, 项目追问"
                onChange={(event) => updateForm({ tagsText: event.target.value })}
              />
            </Field>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <Field label="支持岗位">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {roleOptions.map((role) => (
                  <label key={role.value} className="admin-check">
                    <input
                      type="checkbox"
                      checked={form.supportedRoles.includes(role.value)}
                      onChange={() => toggleRole(role.value)}
                    />
                    {role.label}
                  </label>
                ))}
              </div>
            </Field>

            <Field label="支持模式">
              <div className="grid grid-cols-2 gap-2">
                {modeOptions.map((mode) => (
                  <label key={mode.value} className="admin-check">
                    <input
                      type="checkbox"
                      checked={form.supportedModes.includes(mode.value)}
                      onChange={() => toggleMode(mode.value)}
                    />
                    {mode.label}
                  </label>
                ))}
              </div>
            </Field>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <Field label="描述">
              <textarea
                className="admin-textarea min-h-32"
                value={form.description}
                placeholder="这个面试官负责什么场景、什么岗位、什么风格。"
                onChange={(event) => updateForm({ description: event.target.value })}
              />
            </Field>

            <Field label="人设补充 Persona">
              <textarea
                className="admin-textarea min-h-32"
                value={form.persona}
                placeholder="例如：语气直接、少寒暄、优先追问项目中的取舍。"
                onChange={(event) => updateForm({ persona: event.target.value })}
              />
            </Field>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_280px]">
            <div className="space-y-4">
              <Field
                label="面试官 Skill"
                hint="写这个面试官是谁、风格、关注点和评价标准。不要把阶段流程都塞在这里。"
              >
                <textarea
                  className="admin-textarea min-h-56 font-mono text-sm"
                  value={form.skillPrompt}
                  placeholder="例：你是阿里后端技术面试官，严谨、冷静、技术要求高，重点关注高并发、分布式、系统设计和工程实践。"
                  onChange={(event) => updateForm({ skillPrompt: event.target.value })}
                />
              </Field>

              <Field
                label="面试流程"
                hint="按“第1阶段、第2阶段...”粘贴流程。后端会按当前轮次抽取对应阶段，作为硬约束发给 AI。"
              >
                <textarea
                  className="admin-textarea min-h-72 font-mono text-sm"
                  value={form.interviewFlow}
                  placeholder={"第1阶段：自我介绍与背景了解\n问题：请简要介绍一下你的背景和之前的工作经历。\n目的：了解候选人技术背景。\n\n第2阶段：算法与数据结构\n问题：链表中间节点、高并发消息队列、CAP 定理。\n目的：测试算法和分布式思维。"}
                  onChange={(event) => updateForm({ interviewFlow: event.target.value })}
                />
              </Field>
            </div>

            <div className="space-y-4">
              <Field label="上传 Skill 文件">
                <input
                  className="block w-full rounded-2xl border border-dashed border-slate-900/20 bg-white/70 p-4 text-sm font-semibold"
                  type="file"
                  accept=".txt,.md,text/plain,text/markdown"
                  onChange={(event) => {
                    void importSkillFile(event.target.files?.[0]);
                    event.target.value = "";
                  }}
                />
              </Field>

              <Field
                label="SecondMe Avatar API Key"
                hint={
                  hasFullAvatarApiKey
                    ? `已入库：${selectedInterviewer?.avatarApiKeyMasked ?? "已脱敏"}；默认隐藏，点右侧按钮可显示。`
                    : selectedInterviewer?.hasAvatarApiKey
                      ? "当前接口只返回了脱敏 key，没有返回完整 key；请重启后端和前端后刷新。"
                    : "AI 分身面试官需要 sk-...；系统面试官可留空。"
                }
              >
                <div className="relative">
                  <input
                    className="admin-input pr-20 font-mono"
                    type={isAvatarKeyVisible ? "text" : "password"}
                    value={form.avatarApiKey}
                    placeholder={selectedInterviewer?.hasAvatarApiKey ? "数据库未返回完整 key" : "sk-..."}
                    onChange={(event) => updateForm({ avatarApiKey: event.target.value })}
                  />
                  <button
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-slate-950 px-3 py-1.5 text-xs font-black text-white transition hover:bg-slate-800"
                    type="button"
                    disabled={!hasFullAvatarApiKey}
                    onClick={() => setIsAvatarKeyVisible((current) => !current)}
                  >
                    {isAvatarKeyVisible ? "隐藏" : "显示"}
                  </button>
                </div>
              </Field>

              <Field label="Prompt Strategy">
                <input
                  className="admin-input"
                  value={form.promptStrategy}
                  placeholder={defaultPromptStrategy(form.type)}
                  onChange={(event) => updateForm({ promptStrategy: event.target.value })}
                />
              </Field>
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
  <label className="block space-y-2">
    <span className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{label}</span>
    {children}
    {hint ? <span className="block text-xs leading-5 text-slate-500">{hint}</span> : null}
  </label>
);
