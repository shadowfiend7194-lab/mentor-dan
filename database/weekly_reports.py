from database.connection import get_connection

def save_weekly_report(
    user_id,
    text
):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO weekly_reports
        (
            user_id,
            report_date,
            text
        )

        VALUES (?, date('now'), ?)

        """,
        (
            user_id,
            text
        )
    )


    conn.commit()
    conn.close()



def get_last_reports(
    user_id,
    limit=3
):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT report_date,text

        FROM weekly_reports

        WHERE user_id = ?

        ORDER BY id DESC

        LIMIT ?

        """,
        (
            user_id,
            limit
        )
    )


    rows = cursor.fetchall()


    conn.close()


    return rows