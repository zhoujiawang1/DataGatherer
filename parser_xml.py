"""
Parses Apple Watch sleep data from an Apple Health XML export.
Used on Windows during development and testing.

To export: iPhone Health app → profile picture → Export All Health Data → share the zip.
Unzip and place export.xml in sample_data/
"""

import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from collections import defaultdict


# Maps Apple Health sleep stage values to readable labels
SLEEP_STAGE_MAP = {
    "HKCategoryValueSleepAnalysisAsleep":            "Asleep",
    "HKCategoryValueSleepAnalysisInBed":             "In Bed",
    "HKCategoryValueSleepAnalysisAwake":             "Awake",
    "HKCategoryValueSleepAnalysisAsleepREM":         "REM",
    "HKCategoryValueSleepAnalysisAsleepCore":        "Core",
    "HKCategoryValueSleepAnalysisAsleepDeep":        "Deep",
    "HKCategoryValueSleepAnalysisAsleepUnspecified": "Unspecified",
}

DATE_FMT = "%Y-%m-%d %H:%M:%S %z"


def _parse_dt(s):
    return datetime.strptime(s, DATE_FMT)


def _assign_night(start_dt):
    """
    Assigns a sleep record to the correct calendar night.
    Sleep before 6AM belongs to the previous calendar day.
    e.g. falling asleep at 11PM on Mar 25 → night of Mar 25
         waking at 1AM on Mar 26       → still night of Mar 25
    """
    d = start_dt.date()
    if start_dt.hour < 6:
        d -= timedelta(days=1)
    return d


def load_raw_records(xml_path, source_filter="Watch"):
    """
    Returns a list of raw sleep interval dicts from the XML export.
    Filters to Apple Watch records only by default.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    records = []
    for rec in root.iter("Record"):
        if rec.attrib.get("type") != "HKCategoryTypeIdentifierSleepAnalysis":
            continue
        source = rec.attrib.get("sourceName", "")
        if source_filter and source_filter.lower() not in source.lower():
            continue

        value = rec.attrib.get("value", "")
        stage = SLEEP_STAGE_MAP.get(value, value)
        start = _parse_dt(rec.attrib["startDate"])
        end   = _parse_dt(rec.attrib["endDate"])
        duration_min = round((end - start).total_seconds() / 60, 1)

        records.append({
            "night":        str(_assign_night(start)),
            "start":        start.strftime("%Y-%m-%d %H:%M"),
            "end":          end.strftime("%Y-%m-%d %H:%M"),
            "duration_min": duration_min,
            "stage":        stage,
            "source":       source,
        })

    records.sort(key=lambda r: r["start"])
    return records


def build_summary(raw_records):
    """
    Aggregates raw records into one summary row per night.
    Counts minutes for each sleep stage.
    """
    nights = defaultdict(lambda: {
        "in_bed_min":      0,
        "asleep_min":      0,
        "rem_min":         0,
        "core_min":        0,
        "deep_min":        0,
        "awake_min":       0,
        "unspecified_min": 0,
    })

    for rec in raw_records:
        night = rec["night"]
        stage = rec["stage"]
        dur   = rec["duration_min"]

        if stage == "In Bed":
            nights[night]["in_bed_min"] += dur
        elif stage == "Asleep":
            nights[night]["asleep_min"] += dur
        elif stage == "REM":
            nights[night]["rem_min"]    += dur
            nights[night]["asleep_min"] += dur
        elif stage == "Core":
            nights[night]["core_min"]   += dur
            nights[night]["asleep_min"] += dur
        elif stage == "Deep":
            nights[night]["deep_min"]   += dur
            nights[night]["asleep_min"] += dur
        elif stage == "Awake":
            nights[night]["awake_min"]  += dur
        elif stage == "Unspecified":
            nights[night]["unspecified_min"] += dur
            nights[night]["asleep_min"]      += dur

    summaries = []
    for night, data in sorted(nights.items()):
        asleep = data["asleep_min"]
        in_bed = data["in_bed_min"] if data["in_bed_min"] > 0 else asleep
        efficiency = round((asleep / in_bed * 100), 1) if in_bed > 0 else None

        summaries.append({
            "night":           night,
            "in_bed_min":      round(in_bed, 1),
            "asleep_min":      round(asleep, 1),
            "rem_min":         round(data["rem_min"], 1),
            "core_min":        round(data["core_min"], 1),
            "deep_min":        round(data["deep_min"], 1),
            "awake_min":       round(data["awake_min"], 1),
            "efficiency_pct":  efficiency,
        })

    return summaries
