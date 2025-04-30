@echo off
echo Creating virtual environment...
python -m venv automation_env

echo Activating virtual environment...
call automation_env\Scripts\activate.bat

echo Installing required packages...
pip install playwright pandas openpyxl

echo Installing playwright browsers...
playwright install chromium

echo Setup completed!
pause