from datetime import datetime

from database.connection import get_connection



def save_checkin_status(
    user_id,
    checkin_type,
    completed
):

    conn = get_connection()
    cursor = conn.cursor()


    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    cursor.execute(
        """
        INSERT OR REPLACE INTO checkin_history
        (
            user_id,
            type,
            date,
            completed
        )

        VALUES (?, ?, ?, ?)

        """,
        (
            user_id,
            checkin_type,
            today,
            completed
        )
    )


    conn.commit()
    conn.close()