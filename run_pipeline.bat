@echo off
cd /d "%~dp0"

:: Set environment variables for email alerts
set EMAIL_USER=cmausman14@gmail.com
set EMAIL_PASS=mzhe jdag cqvr sooi

:: 1. Run local Python scraper
python scraper.py

:: 2. Stage, commit, and push updated CSV to GitHub
git add master_leads.csv
git commit -m "🤖 Local Pipeline Refresh: Live verified MLO leads updated"
git push origin main

echo ✅ Pipeline Sync Complete!
