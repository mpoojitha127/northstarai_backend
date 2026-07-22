"""
Reflection Engine + final response composition.

The brief asks the model to silently interrogate its own answer
("what assumptions am I making, what could go wrong, is there a better
strategy") and weave that into the response naturally, rather than bolting
on a visible checklist. We implement that as prompt instructions on the
MAIN answer call rather than a third API call: reflection is cheap to fold
into the generation prompt because it shapes the answer itself, unlike
alignment judgment which needs to be structured and independently reliable.

If the model does surface an explicit caveat, we also try to lift it back
out into a short bullet list (`reflection_notes`) for the UI to show as a
small "worth noting" strip under the answer -- best-effort, not required
for the response to work.
"""
import re

from app.services.ai_provider import get_ai_provider

_SYSTEM_PROMPT = """You are NorthStar AI, a strategic mentor -- not a compliant assistant.

Before answering, silently ask yourself:
- What assumptions am I making about what the user actually needs?
- What could go wrong if the user follows this advice literally?
- Is there a strategically better approach than a literal answer to what
  was asked?

Then answer the user's request directly and usefully. Weave any important
caveat or better-strategy insight naturally into the answer -- do not
label it "reflection" or produce a separate meta-commentary section.
Keep the tone of an experienced, candid mentor: warm but direct, willing to
push back, never obsequious. Use markdown formatting (including code blocks
where relevant) when it helps clarity.
"""


def generate_response(
    *,
    user_request: str,
    goal_context: str | None,
    alignment_reason: str,
    conversation_history: list[dict],
) -> str:
    history_block = ""
    for turn in conversation_history[-6:]:
        role = "User" if turn["role"] == "user" else "NorthStar"
        history_block += f"{role}: {turn['content']}\n"

    user_prompt = f"""{"GOAL CONTEXT: " + goal_context if goal_context else ""}
ALIGNMENT NOTE FOR YOUR AWARENESS (do not repeat verbatim, use it to inform tone): {alignment_reason}

RECENT CONVERSATION
{history_block}

CURRENT USER MESSAGE
{user_request}
"""
    provider = get_ai_provider()
    return provider.generate(_SYSTEM_PROMPT, user_prompt)


_CAVEAT_PATTERN = re.compile(r"(?:worth noting|keep in mind|one risk|assumption)[^.\n]*[.\n]", re.IGNORECASE)


def extract_reflection_notes(response_text: str) -> list[str]:
    """Best-effort extraction of caveat-like sentences for the UI strip."""
    matches = _CAVEAT_PATTERN.findall(response_text)
    return [m.strip().rstrip(".") for m in matches[:3]]
