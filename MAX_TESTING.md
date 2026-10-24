# Тестирование интеграции MAX — Примеры запросов

## 📨 Тестовые payloads для webhook

### Вариант 1: Простое сообщение

```json
{
  "message": {
    "sender": {
      "user_id": "max_user_12345",
      "name": "Алексей Тестовый"
    },
    "recipient": {
      "chat_id": "chat_67890"
    },
    "body": {
      "text": "Какой рабочий график?"
    }
  }
}
```

### Вариант 2: С вложенным update

```json
{
  "update": {
    "message": {
      "sender": {
        "userId": "max_user_12345",
        "displayName": "Мария Петрова"
      },
      "chat_id": "chat_67890",
      "body": {
        "text": "/start"
      }
    }
  }
}
```

### Вариант 3: Альтернативная структура

```json
{
  "message": {
    "user_id": "max_user_12345",
    "chat_id": "chat_67890",
    "text": "Где получить пропуск?",
    "sender": {
      "name": "Дмитрий Смирнов"
    }
  }
}
```

## 🧪 cURL команды для тестирования

### 1. Тест webhook через демо endpoint

```bash
curl -X POST "http://127.0.0.1:8000/demo/max/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "sender": {
        "user_id": "test_user_001",
        "name": "Тестовый Пользователь"
      },
      "recipient": {
        "chat_id": "test_chat_001"
      },
      "body": {
        "text": "Какой рабочий график?"
      }
    }
  }'
```

### 2. Тест реального webhook (с секретом)

```bash
curl -X POST "http://127.0.0.1:8000/webhooks/max" \
  -H "Content-Type: application/json" \
  -H "X-Max-Webhook-Secret: ваш_секрет_из_env" \
  -d '{
    "message": {
      "sender": {
        "user_id": "real_max_user",
        "name": "Настоящий Сотрудник"
      },
      "recipient": {
        "chat_id": "real_chat_id"
      },
      "body": {
        "text": "/start"
      }
    }
  }'
```

### 3. Прямой вызов API чата

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "chat_id": "test_chat_001",
    "text": "Какой рабочий график?"
  }'
```

## 🔍 Ожидаемые ответы

### Успешный ответ с источником

```json
{
  "text": "Рабочий график — 5 дней в неделю с 9:00 до 18:00, перерыв с 13:00 до 14:00.\n\nИсточник: Правила внутреннего трудового распорядка",
  "sources": [
    {
      "document_name": "правила_внутреннего_трудового_распорядка.md",
      "section": "2.1 Режим работы",
      "score": 0.89
    }
  ],
  "escalated": false,
  "model_used": "retrieval_only",
  "dialog_state": "ready"
}
```

### Эскалация в HR (нет ответа в базе)

```json
{
  "text": "В утверждённых документах нет ответа на этот вопрос. Я не буду гадать.\n\nМогу подготовить обращение HR с вашим текстом:\n«Где получить пропуск?»\n\nНапишите «Отправить HR», чтобы подтвердить передачу, «Изменить текст» или «Не сейчас».",
  "sources": [],
  "escalated": false,
  "model_used": "none",
  "dialog_state": "hr_confirm"
}
```

### Команда /start

```json
{
  "text": "Здравствуйте! Я Корсик, помощник по адаптации. Помогу собрать маршрут на первые недели и найти информацию в утверждённых документах.\n\n...\n\nКакая у вас должность?",
  "sources": [],
  "escalated": false,
  "model_used": "none",
  "dialog_state": "ask_job"
}
```

## 🎭 Сценарии для демонстрации

### Сценарий 1: Успешный поиск в базе знаний

**Запросы по порядку:**

1. `/start`
2. `Инженер-технолог`
3. `есть опыт`
4. `GrPP`
5. `03.11.2026`
6. `получать`
7. `Какой рабочий график?` ← показать источник

### Сценарий 2: Эскалация в HR

1. `Где получить пропуск?` ← нет в базе
2. `Отправить HR` ← подтверждение

### Сценарий 3: Отмена регистрации

1. `/start`
2. `Менеджер`
3. `/cancel` ← остановка

## 🔧 PowerShell скрипт для быстрого теста

```powershell
# test_max_webhook.ps1
$url = "http://127.0.0.1:8000/demo/max/webhook/test"
$body = @{
    message = @{
        sender = @{
            user_id = "ps_test_$(Get-Random)"
            name = "PowerShell Тестер"
        }
        recipient = @{
            chat_id = "ps_chat_001"
        }
        body = @{
            text = "Какой рабочий график?"
        }
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5
```

Запуск:
```powershell
.\test_max_webhook.ps1
```

## 📊 Python скрипт для нагрузочного тестирования

```python
import asyncio
import httpx

async def test_webhook(user_id: int):
    async with httpx.AsyncClient() as client:
        payload = {
            "message": {
                "sender": {
                    "user_id": f"load_test_{user_id}",
                    "name": f"User {user_id}"
                },
                "recipient": {
                    "chat_id": f"chat_{user_id}"
                },
                "body": {
                    "text": "Какой рабочий график?"
                }
            }
        }
        response = await client.post(
            "http://127.0.0.1:8000/demo/max/webhook/test",
            json=payload
        )
        print(f"User {user_id}: {response.status_code}")

async def main():
    tasks = [test_webhook(i) for i in range(10)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🌐 Настройка ngrok для публичного webhook

### 1. Запустите ngrok

```bash
ngrok http 8000
```

### 2. Скопируйте HTTPS URL

Пример: `https://abc123.ngrok.io`

### 3. Зарегистрируйте webhook в MAX

Webhook URL:
```
https://abc123.ngrok.io/webhooks/max
```

### 4. Обновите .env

```env
APP_BASE_URL=https://abc123.ngrok.io
```

### 5. Тест через ngrok

```bash
curl -X POST "https://abc123.ngrok.io/webhooks/max" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "sender": {"user_id": "ngrok_test", "name": "Test"},
      "recipient": {"chat_id": "test_chat"},
      "body": {"text": "Тест через ngrok"}
    }
  }'
```

## 📝 Проверочный чек-лист

- [ ] Локальный endpoint `/demo/max/webhook/test` работает
- [ ] Парсинг различных форматов payload успешен
- [ ] Ответ с источником возвращается корректно
- [ ] Эскалация в HR срабатывает
- [ ] Команды `/start`, `/help`, `/status` работают
- [ ] Регистрация проходит полный цикл
- [ ] ngrok туннель открыт (для реального MAX)
- [ ] Webhook зарегистрирован в кабинете MAX

---

**🎉 Готово к тестированию!**
