@echo off
echo 📡 GitHub Status Check
cd /d "%~dp0"

REM Show Git status summary
echo.
echo 📝 Checking which files are staged, modified, or ignored...
git status

REM Optional: show .gitignore effectiveness
echo.
echo 🧰 Files ignored (from .gitignore):
git check-ignore * > nul 2>&1
IF %ERRORLEVEL% EQU 1 (
    echo ✅ All files accounted for.
) ELSE (
    git check-ignore *
)

echo.
echo 🔍 To push changes, run: push_safe.bat
pause
