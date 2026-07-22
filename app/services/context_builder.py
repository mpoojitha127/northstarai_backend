"""
Context Builder

This module prepares all the information the AI needs before generating
a response.

Instead of only sending the current user prompt, we provide:

- Long-term goal
- Conversation history
- Relevant memories
- Current request

This gives the model much better context and keeps prompt construction
out of the chat route.
"""

from dataclasses import dataclass


@dataclass
class AIContext:
    system_prompt: str
    user_prompt: str


def build_context(
    *,
    goal_title: str | None,
    goal_description: str | None,
    conversation_history: list[dict],
    memories: list[str],
    current_request: str,
) -> AIContext:
    """
    Build the prompts that will be sent to the AI provider.
    """

    # -----------------------------
    # Goal
    # -----------------------------
    if goal_title:
        goal_section = f"""
LONG-TERM GOAL

Title:
{goal_title}

Description:
{goal_description or "No description provided."}
"""
    else:
        goal_section = """
LONG-TERM GOAL

No long-term goal is currently linked.
"""

    # -----------------------------
    # Conversation History
    # -----------------------------
    history_lines = []

    for message in conversation_history:
        role = message["role"].upper()
        content = message["content"]

        history_lines.append(f"{role}: {content}")

    history_text = "\n".join(history_lines)

    if not history_text:
        history_text = "No previous conversation."

    # -----------------------------
    # Memory
    # -----------------------------
    if memories:
        memory_text = "\n".join(f"- {m}" for m in memories)
    else:
        memory_text = "No relevant memories."

    # -----------------------------
    # System Prompt
    # -----------------------------
    system_prompt = """
You are an expert AI assistant.

Always answer accurately and honestly.

Prioritize helping the user achieve their long-term goal when one is available.

Use the previous conversation and relevant memories naturally.

If multiple solutions exist, recommend the one that best supports the user's long-term objective.

Do not mention that you were given memories, previous conversation, or internal context.

Keep responses clear, practical, and actionable.
"""

    # -----------------------------
    # User Prompt
    # -----------------------------
    user_prompt = f"""
{goal_section}

---------------------------------------

PREVIOUS CONVERSATION

{history_text}

---------------------------------------

RELEVANT MEMORIES

{memory_text}

---------------------------------------

CURRENT USER REQUEST

{current_request}
"""

    return AIContext(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )