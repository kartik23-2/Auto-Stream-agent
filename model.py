from google import genai
from google.genai import types
from config import GOOGLE_API_KEY, MODEL_NAME

client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

def ask_llm(prompt):
    if not GOOGLE_API_KEY:
        return 'Gemini API key is missing. Add GOOGLE_API_KEY to your .env file.'

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=500,
            ),
        )
        return response.text
    except Exception:
        return 'The AI service is temporarily unavailable. Please try again in a moment.'