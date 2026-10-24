# ✅ Чек-лист запуска демо для хакатона

## 1. Подготовка окружения

```bash
# Установите зависимости
cd backend
pip install -r requirements.txt
```

## 2. Настройка .env

Скопируйте `.env.example` → `.env` и заполните **минимально необходимые** поля:

```bash
# Обязательные
GIGACHAT_TOKEN=ваш_токен_gigachat
OPENAI_API_KEY=ваш_ключ_openai  # Для эмбеддингов

# Для демо достаточно оставить как есть
DEMO_MODE=true
```

## 3. Загрузка демо-данных

```bash
python backend/scripts/seed_demo.py
```

Вы увидите:
```
[+] Создан пользователь: Алексей Иванов
[+] Создан пользователь: Мария Петрова
[+] Создан пользователь: Дмитрий Смирнов
[+] Добавлено 6 демо-сообщений
[+] Создано 2 эскалаций в HR
[+] Добавлено 2 feedback-записей

[OK] Демо-данные готовы!
```

## 4. Запуск сервера

```bash
cd backend
uvicorn app.main:app --reload
```

Или используйте скрипт:
```bash
./start_demo.bat  # Windows
```

## 5. Проверка работы

### A. API Health Check
```bash
curl http://127.0.0.1:8000/health
```

### B. Демо-интерфейс MAX
Откройте в браузере:
```
http://127.0.0.1:8000/demo/max/chat
```

### C. Тестирование через API

**Отправить тестовое сообщение:**
```bash
curl -X POST http://127.0.0.1:8000/webhook/max/test \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user_001",
    "message": "Привет! Расскажи про мой первый день"
  }'
```

## 6. Доступные эндпоинты

| Эндпоинт | Описание |
|----------|----------|
| `GET /` | Главная страница |
| `GET /health` | Проверка состояния |
| `GET /demo/max/chat` | Демо-интерфейс MAX |
| `POST /webhook/max/test` | Тестовый webhook для MAX |
| `POST /webhook/max` | Продакшн webhook (требует токен) |
| `GET /api/users` | Список пользователей |
| `GET /api/escalations` | HR-эскалации |
| `GET /api/pulse-feedback` | Feedback сотрудников |

## 7. Демо-сценарии для презентации

### Сценарий 1: Новый сотрудник задаёт вопросы
```json
{
  "user_id": "demo_user_003",
  "message": "Как мне попасть в столовую?"
}
```

### Сценарий 2: Запрос личной информации
```json
{
  "user_id": "demo_user_001",
  "message": "Когда у меня первая встреча с руководителем?"
}
```

### Сценарий 3: Эскалация в HR
```json
{
  "user_id": "demo_user_002",
  "message": "У меня проблема с доступом к рабочей системе"
}
```

## 8. Просмотр логов

Логи сохраняются в:
```
backend/logs/app.log
```

Смотрите в реальном времени:
```bash
tail -f backend/logs/app.log
```

## 9. Troubleshooting

### Ошибка: "GigaChat token not found"
→ Проверьте `.env`, поле `GIGACHAT_TOKEN`

### Ошибка: "Database file not found"
→ Запустите `python backend/scripts/seed_demo.py`

### Порт 8000 занят
→ Измените порт: `uvicorn app.main:app --port 8001`

## 10. Что показать жюри

1. **Демо-интерфейс MAX** → реальный диалог с ботом
2. **API Dashboard** → `/api/users`, `/api/escalations`
3. **Логи взаимодействий** → как бот понимает контекст
4. **RAG в действии** → ответы на основе документации Газпромнефти

---

## Готово! 🚀

Теперь проект готов для демонстрации на хакатоне.

**Полезные ссылки:**
- [README по MAX интеграции](./MAX_INTEGRATION.md)
- [Примеры API запросов](./API_EXAMPLES.md)
- [Документация по запуску](./HACKATHON_README.md)
