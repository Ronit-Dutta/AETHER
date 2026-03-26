import os
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
for model in client.models.list():
    print(f"Model ID: {model.name}")
