"""
Writes sleep data to Google Sheets using a service account.

Setup:
    1. Go to console.cloud.google.com
    2. Create a project → enable Google Sheets API
    3. Create a Service Account → download JSON key → save as credentials.json
    4. Share your Google Sheet with the service account email
"""

import gspread
from google.oauth2.service_account import Credentials
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

RAW_HEADERS = ["Night", "Start", "End", "Duration (min)", "Stage", "Source"]
SUMMARY_HEADERS = [
    "Night", "In Bed (min)", "Asleep (min)", "REM (min)",
    "Core (min)", "Deep (min)", "Awake (min)", "Sleep Efficiency (%)"
]


def _get_client():
    creds = Credentials.from_service_account_file(config.CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_or_create_sheet(spreadsheet, tab_name, headers):
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
        ws.append_row(headers, value_input_option="USER_ENTERED")
    return ws


def _existing_nights(ws, col=1):
    """Returns a set of night strings already in the sheet (skips header row)."""
    values = ws.col_values(col)
    return set(values[1:])  # skip header


def write_raw(raw_records):
    client = _get_client()
    spreadsheet = client.open(config.SPREADSHEET_NAME)
    ws = _get_or_create_sheet(spreadsheet, config.RAW_DATA_SHEET, RAW_HEADERS)

    existing = _existing_nights(ws)

    new_rows = [
        [
            r["night"],
            r["start"],
            r["end"],
            r["duration_min"],
            r["stage"],
            r["source"],
        ]
        for r in raw_records
        if r["night"] not in existing
    ]

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"  Raw Data: added {len(new_rows)} rows")
    else:
        print("  Raw Data: nothing new to add")


def write_summary(summary_records):
    client = _get_client()
    spreadsheet = client.open(config.SPREADSHEET_NAME)
    ws = _get_or_create_sheet(spreadsheet, config.SUMMARY_SHEET, SUMMARY_HEADERS)

    existing = _existing_nights(ws)

    new_rows = [
        [
            s["night"],
            s["in_bed_min"],
            s["asleep_min"],
            s["rem_min"],
            s["core_min"],
            s["deep_min"],
            s["awake_min"],
            s["efficiency_pct"],
        ]
        for s in summary_records
        if s["night"] not in existing
    ]

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"  Summary: added {len(new_rows)} rows")
    else:
        print("  Summary: nothing new to add")
