# 🔧 Создание файла .env для демо

## Быстрая настройка (2 минуты)

### Вариант 1: Копирование (рекомендуется)

```bash
# Если есть .env.example
cp backend/.env.example backend/.env
```

### Вариант 2: Создание вручную

Создайте файл `backend/.env` со следующим содержимым:

```env
# ═══════════════════════════════════════════════════
# ОБЯЗАТЕЛЬНО ДЛЯ ДЕМО
# ═══════════════════════════════════════════════════

# Режим демонстрации (без реальных API)
DEMO_MODE=true

# ═══════════════════════════════════════════════════
# НЕ ОБЯЗАТЕЛЬНО ДЛЯ ДЕМО (можно оставить пустыми)
# ═══════════════════════════════════════════════════

# GigaChat API (для production RAG)
GIGACHAT_TOKEN=

# OpenAI API (для embeddings)
OPENAI_API_KEY=

# MAX messenger (после хакатона)
MAX_BOT_TOKEN=
MAX_WEBHOOK_SECRET=

# ═══════════════════════════════════════════════════
# БАЗА ДАННЫХ (уже настроена)
# ═══════════════════════════════════════════════════

DATABASE_URL=sqlite:///./data/korsik.db

# ═══════════════════════════════════════════════════
# НАСТРОЙКИ RAG (опционально)
# ═══════════════════════════════════════════════════

# Модель для векторизации (по умолчанию text-embedding-3-small)
# EMBEDDING_MODEL=text-embedding-3-small

# Путь к векторной БД (по умолчанию ./chroma_db)
# CHROMA_DB_PATH=./chroma_db
```

---

## Проверка корректности

### Шаг 1: Убедитесь, что файл создан
```bash
ls -la backend/.env
```

Должно вывести:
```
-rw-r--r-- 1 user user 1234 Oct 24 16:20 backend/.env
```

### Шаг 2: Проверьте содержимое
```bash
cat backend/.env | grep DEMO_MODE
```

Должно вывести:
```
DEMO_MODE=true
```

### Шаг 3: Запустите сервер
```bash
cd backend
uvicorn app.main:app --reload
```

Если всё правильно, вы увидите:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## Конфигурация для разных режимов

### Демо-режим (для хакатона)
```env
DEMO_MODE=true
DATABASE_URL=sqlite:///./data/korsik.db
```
✅ Работает без реальных API токенов
✅ Использует заглушки для GigaChat и OpenAI
✅ Подходит для презентации

### Production-режим (после хакатона)
```env
DEMO_MODE=false

# Реальные токены
GIGACHAT_TOKEN=ваш_токен_gigachat
OPENAI_API_KEY=sk-ваш_ключ_openai
MAX_BOT_TOKEN=ваш_токен_max

DATABASE_URL=sqlite:///./data/korsik.db
```
✅ Полная функциональность
✅ Реальные ответы от GigaChat
✅ Реальная отправка сообщений в MAX

---

## Получение токенов (после хакатона)

### GigaChat API
1. Перейдите на https://developers.sber.ru/studio/workspaces
2. Создайте проект
3. Получите токен для GigaChat API
4. Вставьте в `GIGACHAT_TOKEN=`

### OpenAI API
1. Перейдите на https://platform.openai.com/api-keys
2. Создайте новый ключ
3. Вставьте в `OPENAI_API_KEY=`

### MAX Messenger
1. Перейдите на https://business.max.ru/self
2. Зарегистрируйте бота
3. Получите токен
4. Вставьте в `MAX_BOT_TOKEN=`

---

## Переменные окружения (полный список)

| Переменная | Обязательна? | Значение по умолчанию | Описание |
|------------|--------------|----------------------|----------|
| `DEMO_MODE` | ✅ Да | `false` | Режим демонстрации без реальных API |
| `DATABASE_URL` | ✅ Да | `sqlite:///./data/korsik.db` | Путь к базе данных |
| `GIGACHAT_TOKEN` | ⚠️ Production | - | Токен GigaChat API |
| `OPENAI_API_KEY` | ⚠️ Production | - | Ключ OpenAI API |
| `MAX_BOT_TOKEN` | ⚠️ Production | - | Токен бота MAX |
| `MAX_WEBHOOK_SECRET` | ❌ Нет | - | Секрет для webhook MAX |
| `EMBEDDING_MODEL` | ❌ Нет | `text-embedding-3-small` | Модель для векторизации |
| `CHROMA_DB_PATH` | ❌ Нет | `./chroma_db` | Путь к ChromaDB |

---

## Безопасность

### ⚠️ ВАЖНО!

1. **Не коммитьте `.env` в git!**
   - Файл уже добавлен в `.gitignore`
   - Храните токены в секрете

2. **Не публикуйте токены:**
   - Не показывайте `.env` на экране во время презентации
   - Не делитесь скриншотами с токенами

3. **Используйте DEMO_MODE:**
   - На хакатоне всегда используйте `DEMO_MODE=true`
   - Переключайте на production только после получения реальных токенов

---

## Troubleshooting

### Ошибка: "File not found: .env"
**Решение:** Создайте файл `backend/.env` по инструкции выше

### Ошибка: "DEMO_MODE not set"
**Решение:** Добавьте строку `DEMO_MODE=true` в `.env`

### Ошибка: "Invalid GigaChat token"
**Если DEMO_MODE=false:**
- Проверьте правильность токена
- Убедитесь, что токен активен

**Если DEMO_MODE=true:**
- Эта ошибка не должна возникать
- Проверьте, что переменная установлена правильно

---

## ✅ После создания .env

Вы готовы к запуску! Выполните:

```bash
# Загрузите демо-данные (один раз)
python backend/scripts/seed_demo.py

# Запустите сервер
start_demo.bat

# Откройте демо
# http://127.0.0.1:8000/demo/max/chat
```

---

*Создано: Claude Sonnet 5.5*
*Дата: 24 октября 2026*
