"""
Enhanced Gemini Client with API key authentication for autonomous agents
"""

import os
import json
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://api.ai-gateway.tigeranalytics.com/chat/completions"
        self.model_name = "gemini-2.0-flash"
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY not configured. Client will return mock responses.")

    async def generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate content using Tiger Analytics Gemini chat completions API"""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.debug("API key missing; returning mock response")
            return f"Mock response for prompt: {prompt[:100]}... (Configure GEMINI_API_KEY for real AI processing)"

        url = self.base_url
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Expect response like: {"choices": [{"message": {"content": "response text"}}], ...}
                        if "choices" in data and len(data["choices"]) > 0:
                            message = data["choices"][0].get("message")
                            if message and "content" in message:
                                return message["content"]
                        logger.warning("Unexpected Gemini API response structure")
                        return "Unable to parse Gemini response"
                    else:
                        error_text = await response.text()
                        logger.error(f"Gemini API error {response.status}: {error_text}")
                        return f"API Error {response.status}: {error_text}"
        except asyncio.TimeoutError:
            logger.error("Gemini API request timed out")
            return "Request timed out - please try again"
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return f"API Error: {str(e)}"

    async def translate(self, text: str, source: str = "ja", target: str = "en") -> str:
        """Use chat completion to perform translation"""
        prompt = (
            f"Translate the following {source} text to {target}, preserving technical and part number details:\n\n"
            f"{text}"
        )
        return await self.generate_content(prompt, temperature=0.1, max_tokens=1500)

    def is_available(self) -> bool:
        """Check if Gemini API key is configured"""
        return bool(self.api_key and self.api_key != "your_gemini_api_key_here")
