@echo off
echo ===================================================
echo             ZENEXAM AI - TEST RUNNER
echo ===================================================
echo.
echo Activating virtual environment...
call ..\Hack2Skill\myenv\Scripts\activate.bat
echo.
echo Running Python unit tests...
python -m unittest test_app.py
echo.
echo ===================================================
pause
