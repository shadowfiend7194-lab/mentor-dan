import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("AITUNNEL_API_KEY"),
    base_url=os.getenv("AITUNNEL_BASE_URL"),
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": "Ответь одной короткой фразой: кто ты?"
        }
    ],
)

print(response.choices[0].message.content)