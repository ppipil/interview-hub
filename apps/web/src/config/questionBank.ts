import type {
  AdminQuestionBankQuestion,
  InterviewRole,
  InterviewStageKey,
  UpsertQuestionBankQuestionRequest,
} from "../types";

export const questionBankStageOptions: Array<{ value: InterviewStageKey; label: string }> = [
  { value: "intro", label: "背景介绍" },
  { value: "fundamentals", label: "基础能力" },
  { value: "project", label: "项目深挖" },
  { value: "system_design", label: "系统设计" },
  { value: "behavioral", label: "行为追问" },
  { value: "closing", label: "总结收口" },
];

const validStageKeys = new Set<InterviewStageKey>(questionBankStageOptions.map((item) => item.value));
const stageLabelByKey: Record<InterviewStageKey, string> = Object.fromEntries(
  questionBankStageOptions.map((item) => [item.value, item.label]),
) as Record<InterviewStageKey, string>;
const stageKeyByAlias = new Map<string, InterviewStageKey>([
  ["intro", "intro"],
  ["背景介绍", "intro"],
  ["自我介绍", "intro"],
  ["开场", "intro"],
  ["fundamentals", "fundamentals"],
  ["基础能力", "fundamentals"],
  ["基础", "fundamentals"],
  ["基础知识", "fundamentals"],
  ["project", "project"],
  ["项目深挖", "project"],
  ["项目", "project"],
  ["项目经验", "project"],
  ["system_design", "system_design"],
  ["系统设计", "system_design"],
  ["场景设计", "system_design"],
  ["behavioral", "behavioral"],
  ["行为追问", "behavioral"],
  ["行为面", "behavioral"],
  ["协作追问", "behavioral"],
  ["closing", "closing"],
  ["总结收口", "closing"],
  ["收尾", "closing"],
  ["总结", "closing"],
]);

export const questionBankTextareaHint =
  "每行一题，推荐直接写：题目 | 参考答案(可选) | 标签1,标签2(可选)。如需区分开场/收尾，也可写：阶段 | 题目 | 参考答案 | 标签";

export const serializeQuestionBankText = (
  questions: Array<AdminQuestionBankQuestion | UpsertQuestionBankQuestionRequest>,
) =>
  questions
    .slice()
    .sort((left, right) => (left.sortOrder ?? 0) - (right.sortOrder ?? 0))
    .map((question) => {
      const cells =
        question.stageKey === "fundamentals"
          ? [question.question.trim()]
          : [stageLabelByKey[question.stageKey], question.question.trim()];
      if (question.referenceAnswer?.trim()) {
        cells.push(question.referenceAnswer.trim());
      }
      if (question.tags.length) {
        if (cells.length === 2) {
          cells.push("");
        }
        cells.push(question.tags.join(","));
      }
      return cells.join(" | ");
    })
    .join("\n");

export const parseQuestionBankText = (
  text: string,
  role: InterviewRole,
): UpsertQuestionBankQuestionRequest[] => {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"));

  return lines.map((line, index) => {
    const cells = line.split("|").map((part) => part.trim());
    const firstCell = cells[0] ?? "";
    const explicitStageKey = stageKeyByAlias.get(firstCell);
    const hasExplicitStage = explicitStageKey !== undefined && cells.length >= 2;
    const normalizedStageKey: InterviewStageKey = hasExplicitStage && explicitStageKey ? explicitStageKey : "fundamentals";
    const rawQuestion = hasExplicitStage ? cells[1] ?? "" : firstCell;
    const rawReference = hasExplicitStage ? cells[2] ?? "" : cells[1] ?? "";
    const rawTags = hasExplicitStage ? cells[3] ?? "" : cells[2] ?? "";

    if (!rawQuestion) {
      throw new Error(`第 ${index + 1} 行格式不正确，请至少填写题目。`);
    }
    if (!validStageKeys.has(normalizedStageKey)) {
      throw new Error(`第 ${index + 1} 行的阶段无效：${firstCell}`);
    }
    return {
      role,
      stageKey: normalizedStageKey,
      question: rawQuestion,
      referenceAnswer: rawReference || null,
      tags: rawTags
        .split(/[,，]/)
        .map((tag) => tag.trim())
        .filter(Boolean),
      enabled: true,
      sortOrder: (index + 1) * 10,
    };
  });
};
