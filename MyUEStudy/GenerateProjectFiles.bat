@echo off
chcp 65001 >nul

echo ============================================
echo   GenerateProjectFiles FYEditor (Win64 Development)
echo ============================================
echo.

call E:\UnrealEngine\Engine\Build\BatchFiles\GenerateProjectFiles.bat ^
    -project="F:\TestProject\TestProject.uproject" ^
    -game ^
    -engine

echo.
if %ERRORLEVEL% EQU 0 (
    echo GenerateProjectFiles SUCCESS!
) else (
    echo GenerateProjectFiles FAILED with error code: %ERRORLEVEL%
)

pause
