# src/bot/llm.py
import os

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    async def generate(self, prompt: str) -> str:
        # Fallback if no key configured
        if not self.api_key:
            return f"(no LLM key set) You said: {prompt}"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.responses.create(
                model="gpt-4o-mini",
                input=f"Answer concisely for a Teams bot user:\n\n{prompt}"
            )
            # Prefer the aggregate helper if available
            text = getattr(resp, "output_text", None)
            if text:
                return text.strip()
            # Fallback extractor
            for item in getattr(resp, "output", []):
                if getattr(item, "type", "") == "message":
                    for c in getattr(item.message, "content", []):
                        if getattr(c, "type", "") == "output_text" and getattr(c, "text", ""):
                            return c.text.strip()
            return "Sorry, I couldn't generate a response."
        except Exception as e:
            return f"(LLM error: {e})"
