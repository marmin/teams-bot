# src/bot/llm_hf.py
import os
import asyncio
from huggingface_hub import InferenceClient

DEFAULT_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct-1M")

class HFLLM:
    """Hugging Face LLM wrapper for Teams bot."""

    def __init__(self, model: str | None = None, api_token: str | None = None):
        self.model = model or DEFAULT_MODEL
        self.token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.token:
            raise ValueError("HUGGINGFACE_API_TOKEN is not set.")
        self.client = InferenceClient(api_key=self.token)

    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM for a given prompt."""
   
        def _call():
            # Use the chat endpoint (task = conversational)
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise assistant for a Microsoft Teams bot."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=256,
                temperature=0.5,
            )
            msg = resp.choices[0].message
            return (msg["content"] if isinstance(msg, dict) else getattr(msg, "content", "")) or ""

        
        try:
            text = await asyncio.to_thread(_call)
            return (text or "").strip()
        except Exception as e:
            return f"(HF LLM error: {e})"
