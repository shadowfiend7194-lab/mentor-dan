import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("AITUNNEL_API_KEY")

if not api_key:
    raise ValueError("AITUNNEL_API_KEY не найден в .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.aitunnel.ru/v1",
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Ты Дэн, персональный наставник. Отвечай естественно и по-человечески.",
        },
        {
            "role": "user",
            "content": "Привет, Дэн. Скажи пару слов о себе.",
        },
    ],
)

print(response.choices[0].message.content)