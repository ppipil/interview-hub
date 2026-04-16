import type { InterviewMode, InterviewRole, InterviewStage } from "../types";

export interface RoleOption {
  value: InterviewRole;
  label: string;
}

export interface ModeOption {
  value: InterviewMode;
  label: string;
}

export const roleOptions: RoleOption[] = [
  {
    value: "frontend",
    label: "前端工程师",
  },
  {
    value: "backend",
    label: "后端工程师",
  },
  {
    value: "product_manager",
    label: "产品经理",
  },
  {
    value: "operations",
    label: "运营",
  },
  {
    value: "data_analyst",
    label: "数据分析",
  },
];

export const modeOptions: ModeOption[] = [
  {
    value: "guided",
    label: "带飞模式",
  },
  {
    value: "real",
    label: "地狱拉练",
  },
];

export const stageLabels: Record<InterviewStage, string> = {
  home: "热身大厅",
  setup: "配置挑战",
  interview: "实战对话",
  feedback: "战报复盘",
};
