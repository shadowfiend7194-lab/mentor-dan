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
    """
    Сохраняет только очевидные долгосрочные факты.

    Это НЕ AI-анализ.
    Никаких дополнительных запросов к модели.
    """

    message = user_message.strip()

    if not message:
        return

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

            value = message[len(prefix):].strip()

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

            value = message[len(prefix):].strip()

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

            value = message[len(prefix):].strip()

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

            value = message[len(prefix):].strip()

            if value:
                remember(
                    user_id,
                    "dislike",
                    value,
                    importance=7,
                )

            return


# =========================================================
# ОПРЕДЕЛЕНИЕ УРОВНЯ КОНТЕКСТА
# =========================================================

def detect_context_level(user_message):
    """
    Локально определяет, насколько глубоко
    Дэн должен использовать пользовательский контекст.

    conversation:
        обычный разговор / короткая реплика.

    personal:
        пользователь говорит о себе,
        своей ситуации, целях, привычках,
        состоянии или просит обычный совет.

    analysis:
        пользователь явно хочет глубокий разбор,
        анализ поведения или персональную оценку.
    """

    text = user_message.strip().lower()

    # =====================================================
    # ANALYSIS
    # =====================================================

    analysis_markers = (
        "проанализируй",
        "проанализируй меня",
        "разбери меня",
        "разбери ситуацию",
        "разберись во мне",
        "разберись со мной",
        "что со мной происходит",
        "что происходит со мной",
        "почему я постоянно",
        "почему я всегда",
        "почему я не могу",
        "почему я так делаю",
        "почему у меня постоянно",
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
        "разбери мою ситуацию",
    )

    if any(marker in text for marker in analysis_markers):
        return "analysis"

    # =====================================================
    # PERSONAL
    # =====================================================

    personal_markers = (
        "я не хочу",
        "я хочу",
        "я могу",
        "я не могу",
        "я не сделал",
        "я сделал",
        "я опять",
        "я снова",
        "я пропустил",
        "я забил",
        "я устал",
        "я устал от",
        "мне лень",
        "мне сложно",
        "мне тяжело",
        "мне плохо",
        "мне трудно",
        "не могу заставить себя",
        "ничего не хочу делать",
        "ничего не хочется",
        "у меня нет сил",
        "у меня нет желания",
        "у меня проблема",
        "у меня проблемы",
        "моя цель",
        "мои цели",
        "моя привычка",
        "мои привычки",
        "мой режим",
        "мой сон",
        "моя дисциплина",
        "мое состояние",
        "моё состояние",
        "моя мотивация",
        "помнишь",
        "ты помнишь",
        "как у меня",
        "что у меня",
        "что со мной",
        "помоги мне",
        "что мне делать",
        "как мне поступить",
        "как мне",
        "дай совет",
        "посоветуй",
    )

    if any(marker in text for marker in personal_markers):
        return "personal"

    # =====================================================
    # ОЧЕНЬ КОРОТКИЕ / БЫТОВЫЕ СООБЩЕНИЯ
    # =====================================================

    return "conversation"


# =========================================================
# ПОЛУЧЕНИЕ НУЖНОГО КОНТЕКСТА
# =========================================================

def get_context_for_level(
    user_id,
    context_level,
):
    """
    Получает только тот контекст,
    который нужен текущему типу сообщения.

    Это главный механизм экономии токенов.
    """

    from services.dan.context import (
        get_user_profile,
        get_user_habits_context,
        get_current_state,
        get_user_statistics,
        get_memories_context,
        get_conversation_context,
    )

    # =====================================================
    # BASIC
    # =====================================================
    #
    # Для обычного факта / бытовой фразы.
    #
    # Например:
    #
    # "ананас"
    # "сегодня дождь"
    # "я посмотрел фильм"
    #
    # Никакая пользовательская аналитика не нужна.
    #

    if context_level == "basic":

        return {
            "profile": {},
            "goals": [],
            "habits": [],
            "habit_trends": {},
            "current_state": {},
            "statistics": {},
            "memories": [],
            "conversation": [],
        }

    # =====================================================
    # CONVERSATION
    # =====================================================
    #
    # Для живого общения.
    #
    # Нужна только небольшая история разговора.
    #

    if context_level == "conversation":

        return {
            "profile": {},
            "goals": [],
            "habits": [],
            "habit_trends": {},
            "current_state": {},
            "statistics": {},
            "memories": [],
            "conversation": get_conversation_context(
                user_id,
                limit=6,
            ),
        }

    # =====================================================
    # PERSONAL
    # =====================================================
    #
    # Пользователь говорит о себе.
    #
    # Даём Дэну персональный контекст,
    # но без тяжёлой аналитики.
    #

    if context_level == "personal":

        return {
            "profile": get_user_profile(
                user_id
            ),

            "goals": __import__(
                "database.goals",
                fromlist=["get_user_goals"],
            ).get_user_goals(
                user_id
            ),

            "habits": get_user_habits_context(
                user_id
            ),

            "habit_trends": {},

            "current_state": get_current_state(
                user_id
            ),

            "statistics": {},

            "memories": get_memories_context(
                user_id,
                limit=10,
            ),

            "conversation": get_conversation_context(
                user_id,
                limit=6,
            ),
        }

    # =====================================================
    # ANALYSIS
    # =====================================================
    #
    # Полный контекст.
    #
    # Используется только тогда,
    # когда пользователь действительно просит анализа.
    #

    if context_level == "analysis":

        from services.dan.context import (
            get_dan_context,
        )

        return get_dan_context(
            user_id
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    return {
        "profile": {},
        "goals": [],
        "habits": [],
        "habit_trends": {},
        "current_state": {},
        "statistics": {},
        "memories": [],
        "conversation": [],
    }


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

    print(
        "\n================ AI DEBUG ================"
    )

    print(
        "SYSTEM PROMPT CHARS:",
        len(prompt),
    )

    print(
        "USER MESSAGE CHARS:",
        len(user_message),
    )

    print(
        "SYSTEM PROMPT PREVIEW:",
        prompt[:500],
    )

    print(
        "==========================================\n"
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

    print(
        "AI USAGE:",
        response.usage,
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
    # 1. Сохраняем очевидные важные факты
    # -----------------------------------------------------

    remember_from_message(
        user_id,
        user_message,
    )

    # -----------------------------------------------------
    # 2. Определяем уровень контекста
    # -----------------------------------------------------

    context_level = detect_context_level(
        user_message
    )

    print(
        "\n========== DAN CONTEXT =========="
    )

    print(
        "MESSAGE:",
        user_message,
    )

    print(
        "CONTEXT LEVEL:",
        context_level,
    )

    print(
        "=================================\n"
    )

    # -----------------------------------------------------
    # 3. Получаем ТОЛЬКО нужный контекст
    # -----------------------------------------------------

    context = get_context_for_level(
        user_id,
        context_level,
    )

    # -----------------------------------------------------
    # 4. Создаём prompt
    # -----------------------------------------------------

    prompt = build_dan_prompt(
        context,
        user_message,
        context_level=context_level,
    )

    # -----------------------------------------------------
    # 5. TEST MODE
    # -----------------------------------------------------

    if AI_MODE == "test":

        return test_ai_response(
            context,
            user_message,
        )

    # -----------------------------------------------------
    # 6. API MODE
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
    # 7. НЕИЗВЕСТНЫЙ РЕЖИМ
    # -----------------------------------------------------

    raise ValueError(
        f"Неизвестный AI_MODE: {AI_MODE}"
    )
