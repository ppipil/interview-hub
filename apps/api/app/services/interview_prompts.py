from __future__ import annotations

import re
from typing import Dict

from app.models.api import InterviewMode, InterviewRole, Interviewer

ROLE_LABELS: Dict[InterviewRole, str] = {
  "frontend": "前端工程师",
  "backend": "后端工程师",
  "product_manager": "产品经理",
  "operations": "运营",
  "data_analyst": "数据分析",
}

MODE_LABELS: Dict[InterviewMode, str] = {
  "guided": "带飞模式",
  "real": "真实模式",
}


def build_avatar_bootstrap_prompt(
  interviewer: Interviewer,
  role: InterviewRole,
  mode: InterviewMode,
  total_rounds: int,
) -> str:
  skill_prompt = _format_skill_prompt(interviewer)
  stage_prompt = _format_stage_prompt(interviewer, current_round=1, total_rounds=total_rounds)
  return (
    f"{skill_prompt}"
    f"{stage_prompt}"
    f"你是 {interviewer.name}，当前正在作为{ROLE_LABELS[role]}模拟面试官进行面试。"
    "面试官 Skill 只用于决定你的风格、关注点和追问习惯；当前阶段任务卡是流程硬约束。"
    f"本次模式是{MODE_LABELS[mode]}，整场共{total_rounds}轮，现在是第1轮。"
    "请严格执行当前阶段任务卡，只输出一个问题本身，不要自我介绍，不要解释流程，不要列点，不要提前反馈。"
  )


def build_avatar_follow_up_prompt(
  interviewer: Interviewer,
  role: InterviewRole,
  mode: InterviewMode,
  next_round: int,
  total_rounds: int,
  answer: str,
) -> str:
  skill_prompt = _format_skill_prompt(interviewer)
  stage_prompt = _format_stage_prompt(interviewer, current_round=next_round, total_rounds=total_rounds)
  return (
    f"{skill_prompt}"
    f"{stage_prompt}"
    f"候选人刚才针对{ROLE_LABELS[role]}岗位的回答如下：{answer}\n"
    f"你是 {interviewer.name}。面试官 Skill 只用于决定你的风格、关注点和追问习惯；当前阶段任务卡是流程硬约束。"
    f"本次模式是{MODE_LABELS[mode]}，整场共{total_rounds}轮，现在是第{next_round}轮。"
    "请严格执行当前阶段任务卡，并结合候选人刚才回答提出一个最合适的问题。"
    "只输出一个问题本身，不要复述候选人的回答，不要给建议，不要解释流程，不要列点，不要提前反馈。"
  )


def build_system_bootstrap_prompt(
  interviewer: Interviewer,
  role: InterviewRole,
  mode: InterviewMode,
  total_rounds: int,
) -> str:
  mode_style = "适度给出思路提醒和拆解提示" if mode == "guided" else "保持正式、克制、贴近真实面试"
  skill_prompt = _format_skill_prompt(interviewer)
  stage_prompt = _format_stage_prompt(interviewer, current_round=1, total_rounds=total_rounds)
  return (
    f"{skill_prompt}"
    f"{stage_prompt}"
    f"你是 {interviewer.name}，正在模拟一场{ROLE_LABELS[role]}岗位面试。"
    f"当前模式为{MODE_LABELS[mode]}，风格要求是：{mode_style}。"
    f"本次总共{total_rounds}轮，现在是第1轮。"
    f"请严格执行当前阶段任务卡，提出一个清晰、自然的中文面试问题。"
    "只输出问题本身，不要自我介绍，不要解释规则，不要列点。"
  )


def build_system_follow_up_prompt(
  interviewer: Interviewer,
  role: InterviewRole,
  mode: InterviewMode,
  next_round: int,
  total_rounds: int,
  answer: str,
) -> str:
  mode_style = "可以适度提示方向，但仍要像面试官追问" if mode == "guided" else "像真实面试官一样直接追问"
  skill_prompt = _format_skill_prompt(interviewer)
  stage_prompt = _format_stage_prompt(interviewer, current_round=next_round, total_rounds=total_rounds)
  return (
    f"{skill_prompt}"
    f"{stage_prompt}"
    f"你是 {interviewer.name}，正在模拟一场{ROLE_LABELS[role]}岗位面试。"
    f"当前模式为{MODE_LABELS[mode]}，追问风格要求：{mode_style}。"
    f"候选人刚才的回答是：{answer}\n"
    f"整场共{total_rounds}轮，现在需要提出第{next_round}轮问题。"
    "请严格执行当前阶段任务卡，并基于候选人刚才的回答提出一个最合理的后续问题。"
    "只输出问题本身，不要复述回答，不要额外点评，不要列点。"
  )


def _format_skill_prompt(interviewer: Interviewer) -> str:
  skill_prompt = (interviewer.skillPrompt or "").strip()
  if not skill_prompt:
    return ""
  return (
    "【Interview Hub 面试官 Skill】\n"
    f"{skill_prompt}\n"
    "【Skill 结束】\n"
  )


def _format_stage_prompt(interviewer: Interviewer, current_round: int, total_rounds: int) -> str:
  interview_flow = (interviewer.interviewFlow or "").strip()
  stage = _select_stage(interview_flow, current_round=current_round, total_rounds=total_rounds)
  if not stage:
    return (
      "【当前阶段任务卡】\n"
      f"当前轮次：第 {current_round} / {total_rounds} 轮。\n"
      "流程规则：只提出当前轮次最合适的一个面试问题，不要提前总结，不要输出反馈。\n"
      "【任务卡结束】\n"
    )

  return (
    "【当前阶段任务卡】\n"
    f"当前轮次：第 {current_round} / {total_rounds} 轮。\n"
    f"{stage}\n"
    "硬性规则：只能执行本阶段任务；不能跳到其他阶段；不能提前总结；不能输出反馈；只能问一个问题。\n"
    "【任务卡结束】\n"
  )


def _select_stage(interview_flow: str, current_round: int, total_rounds: int) -> str:
  if not interview_flow:
    return ""

  stages = _extract_numbered_stages(interview_flow)
  if not stages:
    return interview_flow

  stage_count = len(stages)
  index = min(stage_count - 1, max(0, round((current_round - 1) * stage_count / max(total_rounds, 1))))
  return stages[index]


def _extract_numbered_stages(interview_flow: str) -> list[str]:
  matches = list(re.finditer(r"(?m)^\s*(?:第\s*)?(\d+)\s*(?:阶段|[.、])[:：]?", interview_flow))
  if not matches:
    return []

  stages: list[str] = []
  for index, match in enumerate(matches):
    start = match.start()
    end = matches[index + 1].start() if index + 1 < len(matches) else len(interview_flow)
    stage = interview_flow[start:end].strip()
    if stage:
      stages.append(stage)
  return stages
