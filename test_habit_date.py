from datetime import datetime, timedelta

from database.connection import get_connection


conn = get_connection()
cursor = conn.cursor()


old_date = (
    datetime.now()
    - timedelta(days=26)
).strftime(
    "%Y-%m-%d %H:%M:%S"
)


cursor.execute(
    """
    UPDATE habits

    SET
        created_at = ?,
        formed = 0,
        formed_at = NULL,
        last_review_date = NULL

    WHERE id = (

        SELECT id
        FROM habits

        WHERE habit_type = ?

        AND active = 1

        ORDER BY id DESC

        LIMIT 1

    )

    """,
    (
        old_date,
        "good",
    )
)


conn.commit()
conn.close()


print(
    "✅ Дата привычки изменена:",
    old_date
)