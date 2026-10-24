@echo off
chcp 65001 >nul
echo ========================================
echo   Тестирование API
echo ========================================
echo.

:: Проверка сервера
curl -s http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Сервер не запущен!
    echo Запустите: start_demo.bat
    pause
    exit /b 1
)

echo [OK] Сервер работает
echo.

:: Тест 1: Health check
echo [Тест 1] Health Check
curl -s http://127.0.0.1:8000/health
echo.
echo.

:: Тест 2: Список пользователей
echo [Тест 2] Список пользователей
curl -s http://127.0.0.1:8000/api/users | python -m json.tool
echo.
echo.

:: Тест 3: Отправка тестового сообщения
echo [Тест 3] Тестовое сообщение боту
curl -X POST http://127.0.0.1:8000/webhook/max/test ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"demo_user_001\",\"message\":\"Привет! Расскажи про офис\"}"
echo.
echo.

:: Тест 4: Эскалации
echo [Тест 4] HR-эскалации
curl -s http://127.0.0.1:8000/api/escalations | python -m json.tool
echo.
echo.

echo ========================================
echo   Тесты завершены!
echo ========================================
echo.
echo Откройте демо-чат: http://127.0.0.1:8000/demo/max/chat
echo.
pause
