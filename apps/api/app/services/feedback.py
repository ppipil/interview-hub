from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.errors import UpstreamServiceError
from app.models.api import (
  ConversationMessage,
  FeedbackDimension,
  InterviewFeedback,
  InterviewMode,
  InterviewRole,
  RoundReview,
  Session,
)

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

DIMENSION_LABELS = {
  "clarity": "表达清晰度",
  "depth": "专业深度",
  "relevance": "问题贴合度",
}
DIMENSION_KEYS_BY_LABEL = {label: key for key, label in DIMENSION_LABELS.items()}


class FeedbackService:
  def build_feedback_prompt(self, session: Session, messages: List[ConversationMessage]) -> str:
    transcript = self._build_transcript(messages)
    return (
      "现在这场模拟面试已经结束。"
      f"请你继续以{ROLE_LABELS[session.role]}面试官的身份，"
      "基于下面这份完整对话生成最终复盘。"
      "你必须只返回一个紧凑但信息充分的 JSON 对象，不要使用 Markdown，不要加代码块，不要写额外说明，不要换行。\n"
      "JSON 字段必须严格使用以下 key："
      "summary、dimensions、strengths、improvements、suggestedAnswer、roundReviews。\n"
      "输出规则：\n"
      "1. summary：一段中文综合评价，控制在70字以内。\n"
      "2. dimensions：固定输出 3 个对象，key 只能是 clarity、depth、relevance；"
      "label 分别是 表达清晰度、专业深度、问题贴合度；score 为 1 到 5 的整数；comment 控制在18字以内。\n"
      "3. strengths：输出 2 条中文亮点，每条控制在18字以内。\n"
      "4. improvements：输出 3 条中文改进建议，每条控制在24字以内。\n"
      "5. suggestedAnswer：输出一句更成熟的回答策略或参考表达，控制在80字以内。\n"
      "6. roundReviews：按轮次输出数组，每项必须包含 round、evaluation、referenceAnswer；"
      "不要输出 note、comment、复盘观察等额外字段；"
      "evaluation 用中文评价这一轮回答的优点和缺口，控制在45字以内；"
      "referenceAnswer 要比普通建议更详细，控制在180到260字；"
      "必须结合本轮问题和候选人回答，给出可直接学习的示范答案；"
      "结构建议包含：先正面回答结论，再讲关键动作/技术取舍/数据结果，最后补一条复盘或风险意识；"
      "不要只写“可以按背景-行动-结果回答”这类空泛模板。\n"
      "7. 不要遗漏任何轮次，不要输出 null。\n"
      f"当前岗位：{ROLE_LABELS[session.role]}。\n"
      f"当前模式：{MODE_LABELS[session.mode]}。\n"
      f"总轮次：{session.totalRounds}。\n"
      f"完整对话如下：\n{transcript}"
    )

  def build_repair_prompt(
    self,
    session: Session,
    messages: List[ConversationMessage],
    raw_reply: str,
  ) -> str:
    return (
      "你刚才返回的内容格式不符合要求。"
      "现在请重新输出，并且只返回一个可解析、紧凑但信息充分的 JSON 对象，不要加任何解释、不要加 Markdown、不要加代码块、不要换行。\n"
      "字段仍然只能是：summary、dimensions、strengths、improvements、suggestedAnswer、roundReviews。\n"
      "roundReviews 每项只输出 round、evaluation、referenceAnswer，不要输出 note 或复盘观察。\n"
      "每个 roundReviews.referenceAnswer 需要保留详细示范答案，控制在180到260字，不能压缩成一句话。\n"
      "如果你上一次已经写好了内容，只需要把它整理成合法 JSON。\n"
      f"你上一次的回复是：\n{raw_reply}\n"
      f"原始面试对话如下：\n{self._build_transcript(messages)}\n"
      f"岗位：{ROLE_LABELS[session.role]}；模式：{MODE_LABELS[session.mode]}；总轮次：{session.totalRounds}。"
    )

  def parse_feedback(
    self,
    session: Session,
    messages: List[ConversationMessage],
    raw_reply: str,
  ) -> InterviewFeedback:
    payload = self._load_payload(raw_reply)
    summary = self._as_text(self._pick(payload, "summary", "综合评价"))
    suggested_answer = self._as_text(
      self._pick(payload, "suggestedAnswer", "suggested_answer", "recommendedAnswer", "参考回答"),
    )

    if not summary:
      raise UpstreamServiceError(
        "SecondMe 返回的反馈缺少 summary，暂时无法完成复盘。",
        code="SECONDME_FEEDBACK_PARSE_ERROR",
      )
    if not suggested_answer:
      raise UpstreamServiceError(
        "SecondMe 返回的反馈缺少 suggestedAnswer，暂时无法完成复盘。",
        code="SECONDME_FEEDBACK_PARSE_ERROR",
      )

    dimensions = self._normalize_dimensions(self._pick(payload, "dimensions", "维度评分"))
    strengths = self._normalize_string_list(self._pick(payload, "strengths", "亮点", "strength"))
    improvements = self._normalize_string_list(
      self._pick(payload, "improvements", "改进建议", "suggestions"),
    )
    raw_round_reviews = self._pick(payload, "roundReviews", "round_reviews", "回答复盘", "每轮复盘")
    round_reviews, parsed_round_note_count = self._normalize_round_reviews(
      raw_round_reviews,
      messages,
    )

    if len(dimensions) != 3 or not strengths or len(improvements) < 2 or parsed_round_note_count == 0:
      raise UpstreamServiceError(
        "SecondMe 返回的反馈字段不完整，暂时无法完成复盘。",
        code="SECONDME_FEEDBACK_PARSE_ERROR",
      )

    return InterviewFeedback(
      sessionId=session.id,
      summary=summary,
      dimensions=dimensions,
      strengths=strengths,
      improvements=improvements,
      suggestedAnswer=suggested_answer,
      roundReviews=round_reviews,
      generatedAt=self._now(),
    )

  def _load_payload(self, raw_reply: str) -> Dict[str, Any]:
    content = raw_reply.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
    if fence_match:
      content = fence_match.group(1).strip()

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
      raise UpstreamServiceError(
        "SecondMe 返回的反馈不是合法 JSON。",
        code="SECONDME_FEEDBACK_PARSE_ERROR",
      )

    try:
      payload = json.loads(content[start : end + 1])
    except json.JSONDecodeError as exc:
      relaxed_payload = self._load_relaxed_payload(content[start : end + 1])
      if relaxed_payload is not None:
        return relaxed_payload
      raise UpstreamServiceError(
        "SecondMe 返回的反馈 JSON 无法解析。",
        code="SECONDME_FEEDBACK_PARSE_ERROR",
      ) from exc

    if not isinstance(payload, dict):
      raise UpstreamServiceError(
        "SecondMe 返回的反馈格式异常。",
        code="SECONDME_FEEDBACK_PARSE_ERROR",
      )
    return payload

  def _load_relaxed_payload(self, raw_payload: str) -> Optional[Dict[str, Any]]:
    summary = self._extract_string_field(raw_payload, "summary")
    suggested_answer = self._extract_string_field(raw_payload, "suggestedAnswer")
    strengths = self._extract_string_array(raw_payload, "strengths")
    improvements = self._extract_string_array(raw_payload, "improvements")

    dimensions = [
      {
        "key": self._decode_json_string(match.group("key")),
        "label": self._decode_json_string(match.group("label")),
        "score": int(match.group("score")),
        "comment": self._decode_json_string(match.group("comment")),
      }
      for match in re.finditer(
        r'"?key"\s*:\s*"(?P<key>(?:[^"\\]|\\.)*)"\s*,\s*'
        r'"label"\s*:\s*"(?P<label>(?:[^"\\]|\\.)*)"\s*,\s*'
        r'"score"\s*:\s*(?P<score>\d+)\s*,\s*'
        r'"comment"\s*:\s*"(?P<comment>(?:[^"\\]|\\.)*)"',
        raw_payload,
        flags=re.DOTALL,
      )
    ]
    round_reviews = [
      {
        "round": int(match.group("round")),
        "note": self._decode_json_string(match.group("note")),
      }
      for match in re.finditer(
        r'"?round"\s*:\s*(?P<round>\d+)\s*,\s*"note"\s*:\s*"(?P<note>(?:[^"\\]|\\.)*)"',
        raw_payload,
        flags=re.DOTALL,
      )
    ]

    if not summary or not suggested_answer or len(dimensions) != 3 or not strengths or len(improvements) < 2:
      return None

    return {
      "summary": summary,
      "dimensions": dimensions,
      "strengths": strengths,
      "improvements": improvements,
      "suggestedAnswer": suggested_answer,
      "roundReviews": round_reviews,
    }

  def _normalize_dimensions(self, raw_dimensions: Any) -> List[FeedbackDimension]:
    if not isinstance(raw_dimensions, list):
      return []

    normalized: List[FeedbackDimension] = []
    for item in raw_dimensions:
      if not isinstance(item, dict):
        continue

      label = self._as_text(item.get("label"))
      key = self._as_text(item.get("key")) or DIMENSION_KEYS_BY_LABEL.get(label, "")
      label = label or DIMENSION_LABELS.get(key)
      comment = self._as_text(item.get("comment") or item.get("note") or item.get("点评"))
      score = self._coerce_score(item.get("score"))
      if not key or not label or score is None or not comment:
        continue

      normalized.append(
        FeedbackDimension(
          key=key,
          label=label,
          score=score,
          comment=comment,
        ),
      )

    return normalized

  def _normalize_round_reviews(
    self,
    raw_round_reviews: Any,
    messages: List[ConversationMessage],
  ) -> Tuple[List[RoundReview], int]:
    transcript_rounds = self._build_round_transcript(messages)
    if not transcript_rounds:
      return [], 0

    reviews_by_round: Dict[int, Dict[str, str]] = {}
    if isinstance(raw_round_reviews, list):
      for index, item in enumerate(raw_round_reviews, start=1):
        if not isinstance(item, dict):
          continue

        round_number = self._coerce_round_number(item.get("round")) or index
        note = self._as_text(item.get("note") or item.get("comment") or item.get("复盘") or item.get("点评"))
        evaluation = self._as_text(
          item.get("evaluation")
          or item.get("评价")
          or item.get("评语")
          or item.get("assessment")
          or item.get("comment"),
        )
        reference_answer = self._as_text(
          item.get("referenceAnswer")
          or item.get("reference_answer")
          or item.get("参考答案")
          or item.get("suggestedAnswer")
          or item.get("optimizedAnswer"),
        )
        if note or evaluation or reference_answer:
          reviews_by_round[round_number] = {
            "note": note,
            "evaluation": evaluation,
            "referenceAnswer": reference_answer,
          }

    normalized: List[RoundReview] = []
    for entry in transcript_rounds:
      review = reviews_by_round.get(entry["round"], {})
      normalized.append(
        RoundReview(
          round=entry["round"],
          question=entry["question"],
          answer=entry["answer"],
          note=review.get("note") or "",
          evaluation=review.get("evaluation") or review.get("note") or "这一轮回答还需要补充更具体的评价。",
          referenceAnswer=review.get("referenceAnswer") or self._build_fallback_reference_answer(entry),
        ),
      )
    return normalized, len(reviews_by_round)

  def _build_fallback_reference_answer(self, round_entry: Dict[str, Any]) -> str:
    question = self._as_text(round_entry.get("question")) or "这个问题"
    answer = self._as_text(round_entry.get("answer"))
    if answer:
      return (
        f"可以先正面回应“{question}”，再把回答展开成一个完整案例：先说明业务背景和目标，"
        f"再讲你当时的职责、关键动作和技术/方案取舍，例如为什么这样拆分、如何验证风险、如何协同推进。"
        "最后补充结果数据、上线效果或复盘反思，让面试官看到你不仅做了事，也理解问题本质和改进空间。"
      )
    return (
      f"建议先直接回答“{question}”的核心判断，再补一个真实或模拟案例：背景是什么、约束是什么、"
      "你会采取哪些步骤、如何衡量结果、遇到风险怎么兜底。即使暂时没有亲身经历，也可以说明你的分析框架，"
      "让答案从“不会/没做过”变成有逻辑的解决方案。"
    )

  def _build_round_transcript(self, messages: List[ConversationMessage]) -> List[Dict[str, Any]]:
    questions_by_round: Dict[int, str] = {}
    answers_by_round: Dict[int, str] = {}

    for message in messages:
      if message.role == "assistant" and message.round not in questions_by_round:
        questions_by_round[message.round] = message.content.strip()
      if message.role == "user":
        answers_by_round[message.round] = message.content.strip()

    rounds = sorted(set(questions_by_round) | set(answers_by_round))
    return [
      {
        "round": round_number,
        "question": questions_by_round.get(round_number, "这一轮的问题记录缺失。"),
        "answer": answers_by_round.get(round_number, ""),
      }
      for round_number in rounds
    ]

  def _build_transcript(self, messages: List[ConversationMessage]) -> str:
    transcript_lines: List[str] = []
    for entry in self._build_round_transcript(messages):
      transcript_lines.append(f"第{entry['round']}轮")
      transcript_lines.append(f"面试官问题：{entry['question']}")
      transcript_lines.append(f"候选人回答：{entry['answer'] or '（本轮未作答）'}")
    return "\n".join(transcript_lines)

  def _normalize_string_list(self, value: Any) -> List[str]:
    if isinstance(value, list):
      normalized = [self._as_text(item) for item in value]
      return [item for item in normalized if item]

    if isinstance(value, str):
      parts = [item.strip(" -•\t") for item in value.splitlines()]
      return [item for item in parts if item]

    return []

  def _extract_string_field(self, raw_payload: str, field: str) -> str:
    match = re.search(
      rf'"{re.escape(field)}"\s*:\s*"((?:[^"\\]|\\.)*)"',
      raw_payload,
      flags=re.DOTALL,
    )
    if not match:
      return ""
    return self._decode_json_string(match.group(1))

  def _extract_string_array(self, raw_payload: str, field: str) -> List[str]:
    match = re.search(
      rf'"{re.escape(field)}"\s*:\s*\[(.*?)\]',
      raw_payload,
      flags=re.DOTALL,
    )
    if not match:
      return []
    return [
      self._decode_json_string(item)
      for item in re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1), flags=re.DOTALL)
    ]

  def _pick(self, payload: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
      if key in payload:
        return payload[key]
    return None

  def _as_text(self, value: Any) -> str:
    return str(value).strip() if isinstance(value, (str, int, float)) else ""

  def _decode_json_string(self, value: str) -> str:
    try:
      return str(json.loads(f'"{value}"')).strip()
    except json.JSONDecodeError:
      return value.strip()

  def _coerce_score(self, value: Any) -> Optional[int]:
    if isinstance(value, bool):
      return None
    if isinstance(value, (int, float)):
      return max(1, min(5, int(value)))
    if isinstance(value, str) and value.strip().isdigit():
      return max(1, min(5, int(value.strip())))
    return None

  def _coerce_round_number(self, value: Any) -> Optional[int]:
    if isinstance(value, bool):
      return None
    if isinstance(value, int):
      return value if value > 0 else None
    if isinstance(value, str):
      match = re.search(r"\d+", value)
      if match:
        return int(match.group())
    return None

  def _now(self) -> str:
    return datetime.now(timezone.utc).isoformat()
