# Mac Setup — Automated Daily Sleep Sync

This document is for Claude on Mac to complete the automated setup of the DataGatherer project.

## Context
This project reads sleep data from Apple Health and writes it to a Google Sheet named **"Apple Watch Sleep Data"**.
- The Windows side is already done (code written, repo created)
- The Mac is responsible for the automated daily sync using `healthkit-to-sqlite`
- Google Sheets credentials (`credentials.json`) need to be placed in the project folder on Mac

---

## Steps to Complete

### 1. Clone the repo
```bash
git clone https://github.com/zhoujiawang1/DataGatherer.git
cd DataGatherer
```

### 2. Set up the Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install healthkit-to-sqlite
```

### 3. Get credentials.json
- Copy `credentials.json` (Google service account key) into the `DataGatherer` folder
- This file was downloaded from Google Cloud Console and must NOT be committed to git

### 4. Export Apple Health data from iPhone
- iPhone → Health app → profile picture → **Export All Health Data**
- AirDrop the zip to Mac (e.g. `~/Downloads/export.zip`)

### 5. Convert to SQLite
```bash
healthkit-to-sqlite ~/Downloads/export.zip ~/health.db
```

### 6. Test manually
```bash
DATA_SOURCE=sqlite HEALTH_DB_PATH=~/health.db python sync_sleep.py
```
Verify that data appears in the Google Sheet before proceeding.

### 7. Create the launchd plist
Replace `YOUR_MAC_USERNAME` with the output of `whoami`.

```bash
cat > ~/Library/LaunchAgents/com.datagatherer.sleepsync.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.datagatherer.sleepsync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_MAC_USERNAME/DataGatherer/venv/bin/python</string>
        <string>/Users/YOUR_MAC_USERNAME/DataGatherer/sync_sleep.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DATA_SOURCE</key>
        <string>sqlite</string>
        <key>HEALTH_DB_PATH</key>
        <string>/Users/YOUR_MAC_USERNAME/health.db</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/sleep_sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/sleep_sync_error.log</string>
</dict>
</plist>
EOF
```

### 8. Activate the scheduler
```bash
launchctl load ~/Library/LaunchAgents/com.datagatherer.sleepsync.plist
```

---

## How it works after setup
```
Apple Watch  →  (automatic, always-on)   →  Apple Health
Apple Health →  (daily export via plist) →  health.db  (via healthkit-to-sqlite)
health.db    →  (daily at 8am, launchd)  →  Google Sheets  (via sync_sleep.py)
```

## Troubleshooting
- Check logs at `/tmp/sleep_sync.log` and `/tmp/sleep_sync_error.log`
- To reload the scheduler after changes: `launchctl unload` then `launchctl load`
- Google Sheet must be named exactly: `Apple Watch Sleep Data`
- Google Sheet must be shared with the service account email from `credentials.json`
