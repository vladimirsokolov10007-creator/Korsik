@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Запуск демо Корсик 2.0
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден.
    echo Установите Python 3.10 или новее с python.org.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Создаю виртуальное окружение...
    python -m venv ".venv"
    if errorlevel 1 goto :error
)

set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist ".env" (
    echo [2/3] Создаю .env из демонстрационного шаблона...
    copy ".env.example" ".env" >nul
    if errorlevel 1 goto :error
)

"%PYTHON%" -c "import fastapi, uvicorn, httpx, dotenv, apscheduler" >nul 2>&1
if errorlevel 1 (
    echo [2/3] Устанавливаю зависимости...
    "%PYTHON%" -m pip install -r "requirements.txt"
    if errorlevel 1 goto :error
)

echo [3/3] Запускаю сервер...
echo.
echo Главная:   http://127.0.0.1:8000
echo Демо-чат:  http://127.0.0.1:8000/demo/max/chat
echo API docs:  http://127.0.0.1:8000/docs
echo.
echo Внешние ключи в DEMO_MODE=true не требуются.
echo Нажмите Ctrl+C для остановки.
echo ========================================
echo.

cd backend
"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%

:error
echo.
echo [ОШИБКА] Не удалось подготовить проект. Проверьте сообщения выше.
pause
exit /b 1
