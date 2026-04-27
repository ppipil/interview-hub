from __future__ import annotations

import re
from typing import Dict, Sequence

from app.models.api import ConversationMessage, InterviewMode, InterviewRole, Interviewer

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

INTERNAL_PROMPT_MARKERS = (
  "【Interview Hub 面试官 Skill】",
  "【Skill 结束】",
  "【当前阶段任务卡】",
  "【任务卡结束】",
  "当前阶段任务卡是流程硬约束",
  "硬性规则：",
  "流程规则：",
  "只输出一个问题本身",
  "面试官 Skill 只用于决定",
  "请严格执行当前阶段任务卡",
  "候选人刚才针对",
)

_NON_PUBLIC_QUESTION_TERMS = (
  "Interview Hub",
  "Skill",
  "任务卡",
  "硬性规则",
  "流程规则",
  "当前轮次",
  "只输出",
  "不要",
  "不能",
  "候选人刚才",
  "本次模式",
  "整场共",
  "你是 ",
  "面试官 Skill",
  "模式为",
  "风格要求",
  "目的：",
  "目标：",
)


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
  messages: Sequence[ConversationMessage] | None = None,
) -> str:
  mode_style = "可以适度提示方向，但仍要像面试官追问" if mode == "guided" else "像真实面试官一样直接追问"
  skill_prompt = _format_skill_prompt(interviewer)
  stage_prompt = _format_stage_prompt(interviewer, current_round=next_round, total_rounds=total_rounds)
  history_prompt = _format_history_prompt(messages)
  return (
    f"{skill_prompt}"
    f"{stage_prompt}"
    f"{history_prompt}"
    f"你是 {interviewer.name}，正在模拟一场{ROLE_LABELS[role]}岗位面试。"
    f"当前模式为{MODE_LABELS[mode]}，追问风格要求：{mode_style}。"
    f"候选人刚才的回答是：{answer}\n"
    f"整场共{total_rounds}轮，现在需要提出第{next_round}轮问题。"
    "必须先避开已问过的问题和已覆盖的考察点；不得把旧问题换一种说法重复再问。"
    "如果当前阶段已经问过类似问题，请切换到本阶段另一个能力点、追问更深细节，或进入更高阶约束。"
    "请严格执行当前阶段任务卡，并基于候选人刚才的回答提出一个最合理的后续问题。"
    "只输出问题本身，不要复述回答，不要额外点评，不要列点。"
  )


def sanitize_interviewer_question(raw_question: str, fallback: str = "") -> str:
  """Prevent internal orchestration prompts from being shown as interview questions."""
  text = (raw_question or "").strip()
  if not text:
    return ""

  if not _looks_like_internal_prompt(text):
    return text

  extracted = (
    _extract_question_after_last_marker(text)
    or _extract_question_from_stage_card(text)
    or _extract_question_candidate(text)
  )
  cleaned = (extracted or fallback).strip()
  if cleaned and not _looks_like_internal_prompt(cleaned):
    return cleaned
  return fallback.strip()


def build_fallback_interviewer_question(
  interviewer: Interviewer,
  role: InterviewRole,
  current_round: int,
  total_rounds: int,
) -> str:
  role_label = ROLE_LABELS[role]
  stage = _select_stage(
    (interviewer.interviewFlow or "").strip(),
    current_round=current_round,
    total_rounds=total_rounds,
  )

  if current_round <= 1 or "自我介绍" in stage or "背景" in stage:
    return f"请简要介绍一下你的背景，以及最近一个与{role_label}岗位相关的项目经历。"
  if "算法" in stage or "数据结构" in stage:
    return "请讲一道你熟悉的数据结构或算法题，并说明你的解法、复杂度和边界情况。"
  if "系统设计" in stage or "架构" in stage or "高并发" in stage:
    return "请设计一个高并发业务系统，并说明架构拆分、缓存策略和可用性保障。"
  if "行为" in stage or "STAR" in stage or "协作" in stage:
    return "请用 STAR 方法描述一次你解决技术难题或推动团队协作的经历。"
  if "总结" in stage or "提问" in stage:
    return "你还有哪些想补充的项目亮点，或者有什么想问面试官的问题？"
  return f"请结合你的{role_label}经历，说明一个关键项目难点、你的解决思路和最终结果。"


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


def _format_history_prompt(messages: Sequence[ConversationMessage] | None) -> str:
  if not messages:
    return ""

  asked_questions = [
    _truncate_for_prompt(message.content)
    for message in messages
    if message.role == "assistant" and message.content.strip()
  ][-8:]
  recent_messages = [
    f"{'面试官' if message.role == 'assistant' else '候选人'}：{_truncate_for_prompt(message.content, max_length=180)}"
    for message in messages[-6:]
    if message.content.strip()
  ]

  parts: list[str] = ["【已发生的面试上下文】"]
  if asked_questions:
    parts.append("已问过的问题（严禁重复或换壳重复）：")
    parts.extend(f"- {question}" for question in asked_questions)
  if recent_messages:
    parts.append("最近对话：")
    parts.extend(f"- {message}" for message in recent_messages)
  parts.append("【上下文结束】")
  return "\n".join(parts) + "\n"


def _truncate_for_prompt(value: str, max_length: int = 220) -> str:
  compacted = " ".join((value or "").split())
  if len(compacted) <= max_length:
    return compacted
  return f"{compacted[:max_length - 1]}…"


def _looks_like_internal_prompt(text: str) -> bool:
  return any(marker in text for marker in INTERNAL_PROMPT_MARKERS)


def _extract_question_after_last_marker(text: str) -> str:
  marker_positions = [text.rfind(marker) + len(marker) for marker in INTERNAL_PROMPT_MARKERS if marker in text]
  if not marker_positions:
    return ""
  tail = text[max(marker_positions):].strip()
  return _extract_question_candidate(tail)


def _extract_question_from_stage_card(text: str) -> str:
  match = re.search(r"【当前阶段任务卡】(?P<section>.*?)【任务卡结束】", text, re.S)
  if not match:
    return ""
  return _extract_question_candidate(match.group("section"))


def _extract_question_candidate(text: str) -> str:
  for candidate in re.findall(r"[“\"]([^”\"]{4,180})[”\"]", text):
    normalized = _normalize_question_candidate(candidate)
    if _is_public_question_candidate(normalized):
      return normalized

  for line in text.splitlines():
    normalized = _normalize_question_candidate(line)
    if _is_public_question_candidate(normalized):
      return normalized

  for sentence in re.findall(r"[^。！？!?；;\n]{4,180}[？?。]", text):
    normalized = _normalize_question_candidate(sentence)
    if _is_public_question_candidate(normalized):
      return normalized

  return ""


def _normalize_question_candidate(candidate: str) -> str:
  normalized = candidate.strip()
  normalized = re.sub(r"^[\s\-*•（(]*\d+[).、]\s*", "", normalized)
  normalized = re.sub(r"^(?:问题|提问|问题方向|示例问题)\s*[:：]\s*", "", normalized)
  normalized = normalized.strip(" \n\r\t\"'“”《》")
  return normalized


def _is_public_question_candidate(candidate: str) -> bool:
  if len(candidate) < 4:
    return False
  if any(term in candidate for term in _NON_PUBLIC_QUESTION_TERMS):
    return False
  return "？" in candidate or "?" in candidate or candidate.startswith("请")
