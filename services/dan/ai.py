import os

from dotenv import load_dotenv
from openai import OpenAI

from services.dan.prompt import build_dan_prompt
from services.dan.memory import remember
from services.dan.context import get_context_for_level
from database.dan.conversations import save_dan_message

load_dotenv()

AI_MODE = os.getenv("AI_MODE", "api").lower()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "350"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

AITUNNEL_API_KEY = os.getenv("AITUNNEL_API_KEY")
AITUNNEL_BASE_URL = os.getenv(
    "AITUNNEL_BASE_URL",
    "https://api.aitunnel.ru/v1",
)

client = None

if AI_MODE == "api":
    if not AITUNNEL_API_KEY:
        raise RuntimeError("AITUNNEL_API_KEY не найден в .env")

    client = OpenAI(
        api_key=AITUNNEL_API_KEY,
        base_url=AITUNNEL_BASE_URL,
    )


def remember_from_message(user_id, user_message):
    """Очень консервативно сохраняет только явно выраженные долгосрочные факты."""
    message = (user_message or "").strip()
    if not message:
        return

    lower = message.lower()

    name_prefixes = (
        "меня зовут ",
        "зови меня ",
        "мое имя ",
        "моё имя ",
    )
    for prefix in name_prefixes:
        if lower.startswith(prefix):
            value = message[len(prefix):].strip()
            if value and len(value) <= 80:
                remember(user_id, "name", value, importance=10)
            return

    goal_prefixes = (
        "моя цель — ",
        "моя цель - ",
        "моя цель: ",
        "главная цель — ",
        "главная цель - ",
        "главная цель: ",
        "хочу достичь ",
        "хочу добиться ",
    )
    for prefix in goal_prefixes:
        if lower.startswith(prefix):
            value = message[len(prefix):].strip()
            if value and len(value) <= 300:
                remember(user_id, "goal", value, importance=9)
            return

    preference_prefixes = (
        "мне нравится ",
        "я люблю ",
        "мне не нравится ",
        "я не люблю ",
    )
    for prefix in preference_prefixes:
        if lower.startswith(prefix):
            value = message[len(prefix):].strip()
            if value and len(value) <= 250:
                key = "preference" if "не " not in prefix else "dislike"
                remember(user_id, key, value, importance=6 if key == "preference" else 7)
            return


def detect_context_level(user_message):
    """
    Локальный маршрутизатор контекста.
    Он не пытается понять смысл сообщения за модель —
    только решает, насколько много данных стоит передать.
    """
    text = (user_message or "").strip().lower()

    analysis_markers = (
        "проанализируй",
        "разбери меня",
        "разбери ситуацию",
        "что со мной происходит",
        "почему я постоянно",
        "почему я всегда",
        "почему я не могу",
        "почему я так делаю",
        "в чем я неправ",
        "в чём я неправ",
        "скажи честно",
        "скажи неприятную правду",
        "оцени меня",
        "оцени мое поведение",
        "оцени моё поведение",
        "дай мне разбор",
        "сделай разбор",
        "разбор моей ситуации",
    )
    if any(marker in text for marker in analysis_markers):
        return "analysis"

    personal_markers = (
        "я ",
        "мне ",
        "у меня ",
        "моя ",
        "мои ",
        "помоги",
        "посоветуй",
        "дай совет",
        "что мне делать",
        "как мне поступить",
        "помнишь",
        "дисциплин",
        "привыч",
        "цель",
        "режим",
        "сон",
        "стресс",
        "энерг",
        "настро",
    )
    if any(marker in text for marker in personal_markers):
        return "personal"

    return "conversation"


def api_ai_response(prompt, user_message):
    if client is None:
        raise RuntimeError("AI client не инициализирован")

    print("\n================ DAN AI ================")
    print("MODEL:", AI_MODEL)
    print("CONTEXT PROMPT CHARS:", len(prompt))
    print("USER MESSAGE CHARS:", len(user_message))
    print("MAX TOKENS:", AI_MAX_TOKENS)

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=AI_TEMPERATURE,
        max_tokens=AI_MAX_TOKENS,
    )

    usage = getattr(response, "usage", None)
    if usage is not None:
        print(
            "DAN TOKENS:",
            "prompt=", getattr(usage, "prompt_tokens", None),
            "completion=", getattr(usage, "completion_tokens", None),
            "total=", getattr(usage, "total_tokens", None),
        )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("AI вернул пустой ответ")

    return content.strip()


def test_ai_response(context, user_message):
    profile = context.get("profile", {})
    name = profile.get("name") or "друг"
    return (
        f"{name}, я тебя услышал. "
        "Давай разберёмся по сути, без лишней воды."
    )


def get_dan_response(user_id, user_message):
    """
    Полный цикл одного сообщения.

    Важно: предыдущая история загружается ДО сохранения текущего сообщения,
    поэтому текущая реплика не дублируется внутри prompt.
    """
    user_message = (user_message or "").strip()
    if not user_message:
        return ""

    remember_from_message(user_id, user_message)

    context_level = detect_context_level(user_message)

    print("\n========== DAN CONTEXT ==========")
    print("MESSAGE:", user_message)
    print("CONTEXT LEVEL:", context_level)
    print("=================================")

    # История здесь ещё не содержит текущую реплику.
    context = get_context_for_level(
        user_id,
        context_level,
    )

    prompt = build_dan_prompt(
        context,
        user_message,
        context_level=context_level,
    )

    # Сохраняем вход после формирования контекста.
    save_dan_message(
        user_id=user_id,
        role="user",
        message=user_message,
    )

    try:
        if AI_MODE == "test":
            response = test_ai_response(context, user_message)
        elif AI_MODE == "api":
            response = api_ai_response(prompt, user_message)
        else:
            raise ValueError(
                f"Неизвестный AI_MODE: {AI_MODE}"
            )
    except Exception as error:
        print(
            f"[DAN AI ERROR] {type(error).__name__}: {error}"
        )
        return (
            "Сейчас у меня небольшая проблема с подключением. "
            "Попробуй ещё раз через пару секунд."
        )

    if response:
        save_dan_message(
            user_id=user_id,
            role="assistant",
            message=response,
        )

    return response
