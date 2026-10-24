from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/demo/max", tags=["MAX Demo"])


@router.get("/chat", response_class=HTMLResponse)
async def max_chat_demo() -> str:
    """Интерактивная демонстрация чат-бота MAX."""
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Корсик в MAX — Демо</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #e5ddd5;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: min(500px, 100vw);
            height: min(800px, 100vh);
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 24px rgba(0,0,0,0.12);
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 8px 8px 0 0;
        }
        .header h1 {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .header p {
            font-size: 13px;
            opacity: 0.9;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #f0f2f5;
        }
        .message {
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
        }
        .message.user {
            align-items: flex-end;
        }
        .message-bubble {
            max-width: 75%;
            padding: 8px 12px;
            border-radius: 12px;
            word-wrap: break-word;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        .message.bot .message-bubble {
            background: white;
            border: 1px solid #e4e6eb;
            color: #050505;
        }
        .message.user .message-bubble {
            background: #667eea;
            color: white;
        }
        .message-time {
            font-size: 11px;
            color: #65676b;
            margin-top: 4px;
            padding: 0 4px;
        }
        .message.user .message-time {
            text-align: right;
        }
        .sources {
            margin-top: 8px;
            padding: 8px;
            background: #f7f8fa;
            border-radius: 8px;
            font-size: 11px;
            color: #65676b;
        }
        .sources strong {
            display: block;
            margin-bottom: 4px;
            color: #050505;
        }
        .input-area {
            padding: 12px;
            background: white;
            border-top: 1px solid #e4e6eb;
            border-radius: 0 0 8px 8px;
            display: flex;
            gap: 8px;
        }
        .input-area input {
            flex: 1;
            padding: 10px 12px;
            border: 1px solid #ccc;
            border-radius: 20px;
            font-size: 14px;
            outline: none;
        }
        .input-area input:focus {
            border-color: #667eea;
        }
        .input-area button {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .input-area button:hover {
            background: #5568d3;
        }
        .input-area button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .typing {
            padding: 8px 12px;
            background: white;
            border: 1px solid #e4e6eb;
            border-radius: 12px;
            max-width: 75%;
            color: #65676b;
            font-size: 13px;
        }
        .typing span {
            animation: blink 1.4s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink {
            0%, 60%, 100% { opacity: 1; }
            30% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Корсик</h1>
            <p>Помощник по адаптации сотрудников</p>
        </div>
        <div class="messages" id="messages">
            <div class="message bot">
                <div class="message-bubble">
                    Здравствуйте! Я Корсик, помощник по адаптации.

Напишите /start для начала или задайте вопрос о компании.
                </div>
                <div class="message-time">Только что</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="input" placeholder="Напишите сообщение..." />
            <button id="send">➤</button>
        </div>
    </div>

    <script>
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('send');
        const userId = 'demo_' + Math.random().toString(36).substr(2, 9);

        function addMessage(text, isUser = false, sources = null) {
            const msg = document.createElement('div');
            msg.className = `message ${isUser ? 'user' : 'bot'}`;

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.textContent = text;

            const time = document.createElement('div');
            time.className = 'message-time';
            time.textContent = new Date().toLocaleTimeString('ru', {hour: '2-digit', minute: '2-digit'});

            msg.appendChild(bubble);
            msg.appendChild(time);

            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = `<strong>Источники:</strong>` +
                    sources.map(s => `${s.document_name}`).join(', ');
                msg.appendChild(sourcesDiv);
            }

            messages.appendChild(msg);
            messages.scrollTop = messages.scrollHeight;
        }

        function showTyping() {
            const typing = document.createElement('div');
            typing.className = 'message bot';
            typing.id = 'typing';
            typing.innerHTML = `
                <div class="typing">
                    Печатает<span>.</span><span>.</span><span>.</span>
                </div>
            `;
            messages.appendChild(typing);
            messages.scrollTop = messages.scrollHeight;
        }

        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }

        async function sendMessage() {
            const text = input.value.trim();
            if (!text) return;

            addMessage(text, true);
            input.value = '';
            sendBtn.disabled = true;

            showTyping();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: userId,
                        text: text,
                        chat_id: 'demo_chat_' + userId
                    })
                });

                const data = await response.json();
                hideTyping();
                addMessage(data.text, false, data.sources);
            } catch (error) {
                hideTyping();
                addMessage('Ошибка соединения. Проверьте, что сервер запущен.', false);
            }

            sendBtn.disabled = false;
            input.focus();
        }

        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        input.focus();
    </script>
</body>
</html>
""".strip()


@router.post("/webhook/test")
async def test_max_webhook(request: Request) -> dict:
    """Тестовый endpoint для проверки обработки MAX webhook."""
    try:
        payload = await request.json()
    except ValueError:
        return {"error": "Invalid JSON"}

    from app.integrations.max import parse_max_update

    incoming = parse_max_update(payload)
    if incoming is None:
        return {
            "status": "ignored",
            "reason": "Could not parse message from payload",
            "payload": payload
        }

    database = request.app.state.database
    database.ensure_employee(incoming.user_id, incoming.display_name)
    result = await request.app.state.chat_service.reply(incoming.user_id, incoming.text)

    return {
        "status": "processed",
        "incoming": {
            "user_id": incoming.user_id,
            "chat_id": incoming.chat_id,
            "text": incoming.text,
            "display_name": incoming.display_name
        },
        "reply": result.as_dict()
    }
