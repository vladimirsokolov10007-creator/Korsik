@echo off
chcp 65001 >nul
echo ========================================
echo   Запуск демо для хакатона
echo ========================================
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.11+ с python.org
    pause
    exit /b 1
)

:: Проверка .env
if not exist "backend\.env" (
    echo [ВНИМАНИЕ] Файл .env не найден
    echo Копирую .env.example...
    copy backend\.env.example backend\.env
    echo.
    echo [!] Откройте backend\.env и заполните:
    echo     - GIGACHAT_TOKEN
    echo     - OPENAI_API_KEY
    echo.
    pause
)

:: Проверка зависимостей
echo [1/4] Проверка зависимостей...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Устанавливаю зависимости...
    pip install -r backend\requirements.txt
)

:: Проверка базы данных
echo [2/4] Проверка базы данных...
if not exist "backend\data\korsik.db" (
    echo База данных не найдена. Создаю демо-данные...
    python backend\scripts\seed_demo.py
    echo.
)

:: Запуск сервера
echo [3/4] Запуск сервера...
echo.
echo ========================================
echo   Сервер запущен!
echo ========================================
echo.
echo Демо-чат:      http://127.0.0.1:8000/demo/max/chat
echo Главная:       http://127.0.0.1:8000
echo API Users:     http://127.0.0.1:8000/api/users
echo API Escalations: http://127.0.0.1:8000/api/escalations
echo.
echo Нажмите Ctrl+C для остановки
echo ========================================
echo.

cd backend
uvicorn app.main:app --reload
