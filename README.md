# Analyst Assistant - WebSocket API для извлечения сущностей из требований

## Описание проекта

Этот проект предоставляет WebSocket API для анализа текстовых требований и извлечения сущностей (актор, действие, объект, результат) с использованием Ollama LLM.

## Требования

- Python 3.9+
- Ollama (установка: https://ollama.ai/)
- Модель LLM (например, llama3)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd analyst-assistant
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Установите Ollama и нужную модель:
```bash
ollama pull llama3
```

## Запуск сервера

```bash
uvicorn server:app --reload
```

Сервер будет доступен по адресу: `ws://localhost:8000/ws`

## Использование

### WebSocket API

Подключитесь к WebSocket и отправляйте текстовые требования. Сервер вернет JSON с извлеченными сущностями.

Пример клиента (client.py):
```python
import websockets
import asyncio
import json

async def analyze_requirement(requirement: str):
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        await ws.send(requirement)
        response = await ws.recv()
        return json.loads(response)

requirements = [
    "Система должна создавать резервные копии ежедневно",
    "Администратор может блокировать пользователей"
]

for req in requirements:
    result = asyncio.run(analyze_requirement(req))
    print(f"Требование: {req}")
    print(f"Актор: {result['actor']}")
    print(f"Действие: {result['action']}")
    print(f"Объект: {result['object']}")
    print(f"Результат: {result['result']}\n")
```

### HTTP Endpoints

- `GET /` - Проверка состояния сервера
- `GET /docs` - Swagger документация (если FastAPI)


## Логирование

Сервер записывает логи в консоль и в файл `analyst_assistant.log`:

```
2025-04-18 12:00:00 - server - INFO - New connection: abc123
2025-04-18 12:00:05 - server - INFO - Received: "Система должна..."
```

## Режим Fallback

Если модель LLM недоступна, сервер использует простой алгоритм извлечения сущностей.

## Разработка

1. Установите dev-зависимости:
```bash
pip install -r requirements-dev.txt
```

2. Запустите тесты:
```bash
pytest
```

## Лицензия

MIT License