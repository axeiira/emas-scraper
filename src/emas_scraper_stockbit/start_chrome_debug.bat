@echo off
echo Starting Chrome with debugging enabled...
echo.
echo This will allow the scraper to connect to your browser session.
echo.
echo After Chrome opens:
echo 1. Go to https://stockbit.com/login
echo 2. Log in with your credentials  
echo 3. Navigate to https://stockbit.com/symbol/EMAS
echo 4. Run the session_scraper.py
echo.
echo Starting Chrome now...

mkdir "C:\temp\chrome_debug" 2>nul

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug"