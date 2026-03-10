import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company     TEXT    NOT NULL,
    job_id      TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    location    TEXT,
    url         TEXT,
    posted_date TEXT,
    scraped_at  TEXT    NOT NULL,
    is_active   INTEGER NOT NULL DEFAULT 1,
    UNIQUE (company, job_id)
);
"""


@contextmanager
def get_conn(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)
        for col in ("description", "summary"):
            try:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # already exists


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def upsert_jobs(conn: sqlite3.Connection, jobs: list[dict]) -> tuple[int, int]:
    """Insert or update jobs. Returns (inserted, updated) counts."""
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for job in jobs:
        cursor = conn.execute(
            """
            INSERT INTO jobs (company, job_id, title, location, url, posted_date, scraped_at, is_active)
            VALUES (:company, :job_id, :title, :location, :url, :posted_date, :scraped_at, 1)
            ON CONFLICT (company, job_id) DO UPDATE SET
                title       = excluded.title,
                location    = excluded.location,
                url         = excluded.url,
                posted_date = excluded.posted_date,
                scraped_at  = excluded.scraped_at,
                is_active   = 1
            """,
            {**job, "scraped_at": now},
        )
        if cursor.lastrowid and conn.execute(
            "SELECT changes()"
        ).fetchone()[0] == 1:
            # changes() == 1 means a row was actually modified or inserted
            # Use rowid comparison: new insert has rowid == lastrowid and previously didn't exist
            inserted += 1
        else:
            updated += 1

    return inserted, updated


def upsert_jobs_batch(conn: sqlite3.Connection, jobs: list[dict]) -> dict:
    """Upsert a batch and return counts based on pre-existing state."""
    if not jobs:
        return {"inserted": 0, "updated": 0, "inserted_ids": set()}

    now = datetime.now(timezone.utc).isoformat()
    company = jobs[0]["company"]

    # Fetch existing job_ids for this company
    existing = {
        row["job_id"]
        for row in conn.execute(
            "SELECT job_id FROM jobs WHERE company = ?", (company,)
        ).fetchall()
    }

    to_insert = [j for j in jobs if j["job_id"] not in existing]
    to_update = [j for j in jobs if j["job_id"] in existing]
    inserted_ids = {j["job_id"] for j in to_insert}

    conn.executemany(
        """
        INSERT OR IGNORE INTO jobs (company, job_id, title, location, url, posted_date, scraped_at, is_active)
        VALUES (:company, :job_id, :title, :location, :url, :posted_date, :scraped_at, 1)
        """,
        [{**j, "scraped_at": now} for j in to_insert],
    )

    conn.executemany(
        """
        UPDATE jobs SET
            title       = :title,
            location    = :location,
            url         = :url,
            posted_date = :posted_date,
            scraped_at  = :scraped_at,
            is_active   = 1
        WHERE company = :company AND job_id = :job_id
        """,
        [{**j, "scraped_at": now} for j in to_update],
    )

    return {"inserted": len(to_insert), "updated": len(to_update), "inserted_ids": inserted_ids}


def update_description_summary(
    conn: sqlite3.Connection, company: str, job_id: str, description: str, summary: str
) -> None:
    conn.execute(
        "UPDATE jobs SET description=?, summary=? WHERE company=? AND job_id=?",
        (description, summary, company, job_id),
    )


def mark_inactive(conn: sqlite3.Connection, company: str, seen_job_ids: set[str]) -> int:
    """
    Mark jobs for `company` that are NOT in `seen_job_ids` as inactive.
    Scoped per company so a failed scrape doesn't ghost other companies' jobs.
    Returns count of rows deactivated.
    """
    if not seen_job_ids:
        # No jobs seen — don't deactivate anything (scrape likely failed)
        return 0

    placeholders = ",".join("?" * len(seen_job_ids))
    cursor = conn.execute(
        f"""
        UPDATE jobs
        SET is_active = 0
        WHERE company = ?
          AND job_id NOT IN ({placeholders})
          AND is_active = 1
        """,
        [company, *seen_job_ids],
    )
    return cursor.rowcount
