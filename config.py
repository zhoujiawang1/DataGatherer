import os

# Google Sheets
CREDENTIALS_FILE = "credentials.json"  # Service account key downloaded from Google Cloud
SPREADSHEET_NAME = "Apple Watch Sleep Data"  # Name of your Google Sheet

# Sheet tab names
RAW_DATA_SHEET = "Raw Data"
SUMMARY_SHEET = "Summary"

# Data source — switches between Windows (xml) and Mac (sqlite)
DATA_SOURCE = os.getenv("DATA_SOURCE", "xml")  # "xml" on Windows, "sqlite" on Mac

# Paths
HEALTH_XML_PATH = os.getenv("HEALTH_XML_PATH", "sample_data/export.xml")  # Apple Health export
HEALTH_DB_PATH = os.getenv("HEALTH_DB_PATH", "health.db")                 # healthkit-to-sqlite output (Mac)
