"""
Parses Apple Watch sleep data from the SQLite database produced by healthkit-to-sqlite.
Used on macOS with a real Apple Watch data source.

Setup:
    pip install healthkit-to-sqlite
    healthkit-to-sqlite health.db   # run once, then daily via cron
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict


SLEEP_STAGE_MAP = {
    "HKCategoryValueSleepAnalysisAsleep":            "Asleep",
    "HKCategoryValueSleepAnalysisInBed":             "In Bed",
    "HKCategoryValueSleepAnalysisAwake":             "Awake",
    "HKCategoryValueSleepAnalysisAsleepREM":         "REM",
    "HKCategoryValueSleepAnalysisAsleepCore":        "Core",
    "HKCategoryValueSleepAnalysisAsleepDeep":        "Deep",
    "HKCategoryValueSleepAnalysisAsleepUnspecified": "Unspecified",
}


def _assign_night(start_dt):
    d = start_dt.date()
    if start_dt.hour < 6:
        d -= timedelta(days=1)
    return d


def load_raw_records(db_path, source_filter="Watch"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT startDate, endDate, value, sourceName
        FROM sleep_analysis
        ORDER BY startDate
    """)

    records = []
    for row in cur.fetchall():
        source = row["sourceName"] or ""
        if source_filter and source_filter.lower() not in source.lower():
            continue

        start = datetime.fromisoformat(row["startDate"])
        end   = datetime.fromisoformat(row["endDate"])
        stage = SLEEP_STAGE_MAP.get(row["value"], row["value"])
        duration_min = round((end - start).total_seconds() / 60, 1)

        records.append({
            "night":        str(_assign_night(start)),
            "start":        start.strftime("%Y-%m-%d %H:%M"),
            "end":          end.strftime("%Y-%m-%d %H:%M"),
            "duration_min": duration_min,
            "stage":        stage,
            "source":       source,
        })

    conn.close()
    return records


def build_summary(raw_records):
    """Same logic as parser_xml — imported from there to avoid duplication."""
    from parser_xml import build_summary as _build
    return _build(raw_records)
