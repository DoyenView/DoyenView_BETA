@echo off
echo 📡 Running GitHub sync script...
cd /d "%~dp0"

REM Stage updated, deleted, and new files
git add .

REM Commit and push if needed
git diff --cached --quiet
IF %ERRORLEVEL% NEQ 0 (
    git commit -m "🔄 Safe sync update: %DATE% %TIME%"
    git push origin main
    echo ✅ GitHub push complete.
) ELSE (
    echo ✅ No changes to commit.
)
pause
