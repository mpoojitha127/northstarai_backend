"""
Strategic Alignment Engine.

This is the differentiator the whole product is built around: before we let
the base model answer, we ask a second, structurally different question --
not "how do I answer this" but "does answering this the way it's asked serve
the user's stated long-term goal?"

Design decision: we run this as a SEPARATE model call with json_mode=True,
rather than folding it into the main answer generation. Two reasons:
1. It needs to reason about the goal even when the user's message alone
   gives no hint of misalignment -- that requires holding the goal as the
   frame, not a footnote, which competes with quality of the main answer
   if merged into one prompt.
2. Structured output (verdict/reason/alternative) is far more reliable when
   it's the model's only job, rather than one section of a longer response.

The cost is one extra API call per turn. For an MVP that's the right
trade-off; if latency becomes a problem, the two calls can be parallelized
since alignment evaluation does not depend on the final answer text.
"""
import json
from dataclasses import dataclass

from app.services.ai_provider import get_ai_provider

_SYSTEM_PROMPT = """You are the Strategic Alignment Engine inside NorthStar AI.

You do not answer the user's question. Your only job is to judge whether
the user's CURRENT REQUEST supports, is neutral toward, or works against
their stated LONG-TERM GOAL.

Respond with strict JSON only, no markdown, no commentary, matching this
schema exactly:
{
  "verdict": "aligned" | "partially_aligned" | "misaligned",
  "reason": "one or two sentences explaining the judgment, referencing the goal directly",
  "alternative": "a concrete better next action, or empty string if verdict is aligned"
}

Guidelines:
- "aligned": the request is a direct, efficient step toward the goal.
- "partially_aligned": the request is reasonable but not the highest-leverage
  use of time right now, or it addresses a side concern while the core goal
  deadline is close.
- "misaligned": the request actively risks delaying, derailing, or
  contradicting the goal (e.g. large time investment in a low-priority
  polish item while a hard deadline looms, or an action that contradicts a
  prior stated decision).
- Be a candid mentor, not a scold. Most requests are aligned or partially
  aligned -- reserve "misaligned" for requests with real strategic cost.
- Ground the reason in the specific goal and deadline given, not generic
  advice.
"""


@dataclass
class AlignmentJudgment:
    verdict: str
    reason: str
    alternative: str


def evaluate_alignment(
    *,
    goal_title: str,
    goal_description: str,
    goal_deadline: str | None,
    goal_priority: str,
    relevant_memories: list[str],
    user_request: str,
) -> AlignmentJudgment:
    memory_block = (
        "\n".join(f"- {m}" for m in relevant_memories) if relevant_memories else "(no prior relevant decisions)"
    )
    user_prompt = f"""LONG-TERM GOAL
Title: {goal_title}
Description: {goal_description or "(none provided)"}
Priority: {goal_priority}
Deadline: {goal_deadline or "(no deadline set)"}

RELEVANT PAST DECISIONS / MILESTONES
{memory_block}

CURRENT REQUEST
{user_request}

Return the JSON verdict now."""

    provider = get_ai_provider()
    raw = provider.generate(_SYSTEM_PROMPT, user_prompt, json_mode=True)

    try:
        data = json.loads(raw)
        return AlignmentJudgment(
            verdict=data.get("verdict", "aligned"),
            reason=data.get("reason", ""),
            alternative=data.get("alternative", ""),
        )
    except (json.JSONDecodeError, AttributeError):
        # Fail safe: never block the user's chat because alignment JSON was
        # malformed. Default to "aligned" with a note, rather than crashing
        # or silently pretending nothing happened.
        return AlignmentJudgment(
            verdict="aligned",
            reason="Alignment check could not be parsed this turn; defaulting to aligned.",
            alternative="",
        )
