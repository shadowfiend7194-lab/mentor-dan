PRO -> FREE DOWNGRADE PATCH

Based on MENTOR DAN NEW (4).

Replace these files:
1. services/subscription.py
2. services/pro_test_reset.py
3. database/habits.py
4. database/goals.py
5. database/migrations.py
6. handlers/day/screen.py
7. handlers/goal/screen.py

What this changes:
- When PRO expires, PRO habits are not deleted.
- Up to 2 oldest FREE-slot habits remain active (preferably one good + one bad).
- Remaining active habits get pro_status='frozen'.
- Main goal remains active; other active goals get pro_status='frozen'.
- My Day hides frozen habits for non-PRO users and shows a frozen notice after PRO expiration.
- My Goal hides frozen goals for non-PRO users and shows how many goals are frozen.
- Re-enabling test PRO restores frozen habits/goals to active.
- PRO data such as motivation, difficulty and goal_id is preserved.
- No new database tables are added; migrations only ensure pro_status columns exist.
