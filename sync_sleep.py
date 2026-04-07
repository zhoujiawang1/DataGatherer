"""
Main entry point. Run this script daily (via cron on Mac or Task Scheduler on Windows).

Usage:
    python sync_sleep.py                   # uses DATA_SOURCE env var (default: xml)
    DATA_SOURCE=sqlite python sync_sleep.py  # use on Mac with healthkit-to-sqlite
"""

import config
import sheets_writer


def main():
    print(f"Data source: {config.DATA_SOURCE}")

    if config.DATA_SOURCE == "sqlite":
        from parser_sqlite import load_raw_records, build_summary
        path = config.HEALTH_DB_PATH
    else:
        from parser_xml import load_raw_records, build_summary
        path = config.HEALTH_XML_PATH

    print(f"Loading sleep records from: {path}")
    raw = load_raw_records(path)
    print(f"  Found {len(raw)} raw sleep intervals")

    summary = build_summary(raw)
    print(f"  Found {len(summary)} nights")

    print("Writing to Google Sheets...")
    sheets_writer.write_raw(raw)
    sheets_writer.write_summary(summary)

    print("Done.")


if __name__ == "__main__":
    main()
