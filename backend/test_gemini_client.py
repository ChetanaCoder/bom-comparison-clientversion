import asyncio
from utils.gemini_client import GeminiClient

async def test_gemini_client():
    client = GeminiClient()
    print("API Available:", client.is_available())

    # Test content generation
    prompt = "Translate 'こんにちは' to English."
    translation = await client.generate_content(prompt, temperature=0.1)
    print("Generated Content:", translation)

    # Test translate method convenience
    translated_text = await client.translate("今日はいい天気です。", source="ja", target="en")
    print("Translated Text:", translated_text)

asyncio.run(test_gemini_client())
