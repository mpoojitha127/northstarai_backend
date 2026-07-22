"""
NorthStar AI Layer

This service evaluates whether an AI response aligns with the user's
long-term goal and improves the response when necessary.

NorthStar DOES NOT replace the AI.

It acts as a strategic intelligence layer between the AI model and the user.
"""

from dataclasses import dataclass
import json

from app.services.ai_provider import get_ai_provider


@dataclass
class NorthStarAnalysis:
    alignment: str
    alignment_score: int
    reason: str
    warning: str
    suggestion: str
    enhanced_response: str


class NorthStarLayer:

    def __init__(self):
        self.ai = get_ai_provider()

    def analyze(
        self,
        goal: str,
        user_prompt: str,
        ai_response: str,
    ) -> NorthStarAnalysis:
        print("====== NORTHSTAR START =======")

        system_prompt = """
You are NorthStar AI.

You are NOT another chatbot.

You are an experienced founder, mentor and strategic advisor.

Your responsibility is to evaluate whether the AI's response helps the user achieve their LONG-TERM GOAL.

Never blindly agree with the original AI response.

Always prioritize the user's long-term success over their immediate request.

If the response could delay, distract, or harm the user's goal,
explain why and improve it.

Scoring Guide:

100 = Perfectly aligned
75 = Mostly aligned
50 = Partially aligned
25 = Weakly aligned
0 = Completely misaligned

Return ONLY a valid JSON object.

Do NOT use markdown.

Do NOT wrap the JSON inside.

The response MUST start with { and end with }.

JSON Schema:

{
    "alignment":"Aligned | Partially Aligned | Misaligned",
    "alignment_score":95,
    "reason":"Why you reached this conclusion.",
    "warning":"Potential risks if any.",
    "suggestion":"How the user should proceed.",
    "enhanced_response":"Improved version of the original AI response."
}
"""

        user_message = f"""
==========================
LONG TERM GOAL
==========================

{goal}

==========================
USER REQUEST
==========================

{user_prompt}

==========================
ORIGINAL AI RESPONSE
==========================

{ai_response}

==========================

Evaluate the response.

If needed, improve it.

Return ONLY JSON.
"""
        print("NorthStar: Calling AI....")
        result = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_message,
            json_mode=True,
        )

        print("NorthStar: AI Returned")
        print(result[:300])
        try:

            result = result.strip()

            if result.startswith("```json"):
                result = result.replace("```json", "", 1)

            if result.startswith("```"):
                result = result.replace("```", "", 1)

            if result.endswith("```"):
                result = result[:-3]

            result = result.strip()

            data = json.loads(result)
            
            print("NorthStar: JSON Parsed Successfully")

            return NorthStarAnalysis(
                alignment=data.get("alignment", "Aligned"),
                alignment_score=int(data.get("alignment_score", 100)),
                reason=data.get("reason", ""),
                warning=data.get("warning", ""),
                suggestion=data.get("suggestion", ""),
                enhanced_response=data.get(
                    "enhanced_response",
                    ai_response,
                ),
            )

        except Exception as e:

            print("NorthStar JSON Parsing Error:")
            print(result)
            print(e)

            return NorthStarAnalysis(
                alignment="Unknown",
                alignment_score=0,
                reason=f"NorthStar parsing failed: {str(e)}",
                warning="",
                suggestion="",
                enhanced_response=ai_response,
            )


northstar = NorthStarLayer()