import os

from openai import OpenAI

from services.dan.prompt import build_dan_prompt
from services.dan.memory import remember


# =========================================================
# НАСТРОЙКИ AI
# =========================================================

AI_MODE = os.getenv(
    "AI_MODE",
    "api",
).lower()

AI_MODEL = os.getenv(
    "AI_MODEL",
    "gpt-4o-mini",
)

AITUNNEL_API_KEY = os.getenv(
    "AITUNNEL_API_KEY"
)

AITUNNEL_BASE_URL = os.getenv(
    "AITUNNEL_BASE_URL",
    "https://api.aitunnel.ru/v1",
)


# =========================================================
# OPENAI-СОВМЕСТИМЫЙ CLIENT
# =========================================================

client = None

if AI_MODE == "api":

    if not AITUNNEL_API_KEY:

        raise RuntimeError(
            "AITUNNEL_API_KEY не найден в .env"
        )

    client = OpenAI(
        api_key=AITUNNEL_API_KEY,
        base_url=AITUNNEL_BASE_URL,
    )


# =========================================================
# СОХРАНЕНИЕ ВАЖНЫХ ФАКТОВ
# =========================================================

def remember_from_message(
    user_id,
    user_message,
):

    message = user_message.strip()
    lower_message = message.lower()

    # -----------------------------------------------------
    # ИМЯ
    # -----------------------------------------------------

    prefixes = (
        "меня зовут ",
        "зови меня ",
        "мое имя ",
        "моё имя ",
    )

    for prefix in prefixes:

        if lower_message.startswith(prefix):

            value = message[
                len(prefix):
            ].strip()

            if value:

                remember(
                    user_id,
                    "name",
                    value,
                    importance=10,
                )

            return

    # -----------------------------------------------------
    # ЦЕЛЬ
    # -----------------------------------------------------

    prefixes = (
        "моя цель ",
        "главная цель ",
        "я хочу ",
        "я хочу достичь ",
        "хочу достичь ",
    )

    for prefix in prefixes:

        if lower_message.startswith(prefix):

            value = message[
                len(prefix):
            ].strip()

            if value:

                remember(
                    user_id,
                    "goal",
                    value,
                    importance=9,
                )

            return

    # -----------------------------------------------------
    # ПРЕДПОЧТЕНИЯ
    # -----------------------------------------------------

    prefixes = (
        "мне нравится ",
        "я люблю ",
        "мне нравится, когда ",
    )

    for prefix in prefixes:

        if lower_message.startswith(prefix):

            value = message[
                len(prefix):
            ].strip()

            if value:

                remember(
                    user_id,
                    "preference",
                    value,
                    importance=6,
                )

            return

    # -----------------------------------------------------
    # НЕ ЛЮБИТ
    # -----------------------------------------------------

    prefixes = (
        "я не люблю ",
        "мне не нравится ",
        "я ненавижу ",
    )

    for prefix in prefixes:

        if lower_message.startswith(prefix):

            value = message[
                len(prefix):
            ].strip()

            if value:

                remember(
                    user_id,
                    "dislike",
                    value,
                    importance=7,
                )

            return


# =========================================================
# TEST MODE
# =========================================================

def test_ai_response(
    context,
    user_message,
):

    profile = context.get(
        "profile",
        {},
    )

    name = (
        profile.get("name")
        or "друг"
    )

    return (
        f"{name}, я тебя услышал.\n\n"
        "Расскажи чуть подробнее. "
        "Мне важно понять, что именно "
        "происходит сейчас, а не додумывать за тебя."
    )


# =========================================================
# API MODE
# =========================================================

def api_ai_response(
    prompt,
    user_message,
):

    if client is None:

        raise RuntimeError(
            "AI client не инициализирован"
        )

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

        temperature=0.7,

        max_tokens=500,
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise RuntimeError(
            "AI вернул пустой ответ"
        )

    return content.strip()


# =========================================================
# ОСНОВНАЯ ФУНКЦИЯ ДЭНА
# =========================================================

def get_dan_response(
    user_id,
    user_message,
):

    # -----------------------------------------------------
    # СОХРАНЯЕМ ВАЖНЫЕ ФАКТЫ
    # -----------------------------------------------------

    remember_from_message(
        user_id,
        user_message,
    )

    # -----------------------------------------------------
    # ПОЛУЧАЕМ ПОЛНЫЙ КОНТЕКСТ
    # -----------------------------------------------------

    from services.dan.context import (
        get_dan_context,
    )

    context = get_dan_context(
        user_id
    )

    # -----------------------------------------------------
    # СОЗДАЁМ PROMPT
    # -----------------------------------------------------

    prompt = build_dan_prompt(
        context,
        user_message,
    )

    # -----------------------------------------------------
    # TEST MODE
    # -----------------------------------------------------

    if AI_MODE == "test":

        return test_ai_response(
            context,
            user_message,
        )

    # -----------------------------------------------------
    # API MODE
    # -----------------------------------------------------

    if AI_MODE == "api":

        try:

            return api_ai_response(
                prompt,
                user_message,
            )

        except Exception as error:

            print(
                f"[DAN AI ERROR] "
                f"{type(error).__name__}: {error}"
            )

            return (
                "Сейчас у меня небольшая проблема "
                "с подключением. Дай мне пару секунд "
                "и попробуй ещё раз."
            )

    # -----------------------------------------------------
    # НЕИЗВЕСТНЫЙ РЕЖИМ
    # -----------------------------------------------------

    raise ValueError(
        f"Неизвестный AI_MODE: {AI_MODE}"
    )