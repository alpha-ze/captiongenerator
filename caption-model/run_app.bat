@echo off
title Image Caption App

REM Optional: activate virtual environment
REM call venv\Scripts\activate

echo Starting Flask app...
start "" http://localhost:8000

REM Replace with your Python path if needed
python app.py

pause
 