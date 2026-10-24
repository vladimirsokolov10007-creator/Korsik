@echo off
chcp 65001 >nul
cls
echo ╔════════════════════════════════════════════════╗
echo ║   Проверка готовности к хакатону               ║
echo ╚════════════════════════════════════════════════╝
echo.

set ERRORS=0

:: Проверка 1: Python
echo [1/8] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo     [X] Python не найден!
    set /a ERRORS+=1
) else (
    echo     [OK] Python установлен
)

:: Проверка 2: Файл .env
echo [2/8] Проверка .env...
if exist "backend\.env" (
    echo     [OK] Файл .env существует
) else (
    echo     [!] Файл .env не найден
    echo     [!] Скопируйте .env.example в .env
    set /a ERRORS+=1
)

:: Проверка 3: Зависимости
echo [3/8] Проверка зависимостей...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo     [!] FastAPI не установлен
    echo     [!] Запустите: pip install -r backend\requirements.txt
    set /a ERRORS+=1
) else (
    echo     [OK] Зависимости установлены
)

:: Проверка 4: База данных
echo [4/8] Проверка базы данных...
if exist "backend\data\korsik.db" (
    echo     [OK] База данных существует
) else (
    echo     [!] База данных не найдена
    echo     [!] Запустите: python backend\scripts\seed_demo.py
    set /a ERRORS+=1
)

:: Проверка 5: Документация
echo [5/8] Проверка документации...
if exist "БЫСТРЫЙ_СТАРТ.md" (
    echo     [OK] Документация готова
) else (
    echo     [X] Документация не найдена
    set /a ERRORS+=1
)

:: Проверка 6: Скрипты
echo [6/8] Проверка скриптов...
if exist "start_demo.bat" (
    echo     [OK] Скрипты готовы
) else (
    echo     [X] start_demo.bat не найден
    set /a ERRORS+=1
)

:: Проверка 7: Логи
echo [7/8] Проверка директории логов...
if exist "backend\logs" (
    echo     [OK] Директория логов существует
) else (
    echo     [!] Создаю директорию логов...
    mkdir backend\logs
    echo     [OK] Директория создана
)

:: Проверка 8: Порт
echo [8/8] Проверка порта 8000...
netstat -ano | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo     [OK] Порт 8000 свободен
) else (
    echo     [!] Порт 8000 занят
    echo     [!] Используйте другой порт или остановите процесс
)

echo.
echo ════════════════════════════════════════════════
if %ERRORS%==0 (
    echo [OK] Всё готово к запуску!
    echo.
    echo Следующие шаги:
    echo   1. Запустите: start_demo.bat
    echo   2. Откройте: http://127.0.0.1:8000/demo/max/chat
    echo   3. Протестируйте все 3 сценария
    echo.
    echo Документация:
    echo   - БЫСТРЫЙ_СТАРТ.md
    echo   - ГОТОВО_К_ХАКАТОНУ.md
    echo   - DEMO_CHECKLIST.md
) else (
    echo [!] Найдено проблем: %ERRORS%
    echo.
    echo Прочитайте сообщения выше и устраните проблемы.
    echo Затем запустите эту проверку снова.
)
echo ════════════════════════════════════════════════
echo.
pause
