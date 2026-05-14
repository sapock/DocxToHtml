@echo off
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "DocxToHtml" ^
    --icon NONE ^
    converter.py
echo.
echo 빌드 완료. dist\DocxToHtml.exe 를 확인하세요.
pause
