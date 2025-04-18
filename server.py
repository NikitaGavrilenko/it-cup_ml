from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
from datetime import datetime
import uuid
import json
from langchain_ollama import OllamaLLM
import asyncio

app = FastAPI()

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация модели LLM
logger.info("Initializing LLM model...")
try:
    llm = OllamaLLM(model="mistral")
    logger.info("LLM model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LLM model: {str(e)}")
    raise


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        session_id = str(uuid.uuid4())[:8]
        self.active_connections[session_id] = websocket
        logger.info(f"New connection: {session_id}")
        return session_id

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Connection closed: {session_id}")


manager = ConnectionManager()


async def extract_entities(text: str) -> dict:
    prompt = f"""Анализируй текст как системный аналитик. Извлеки сущности в JSON:

    Текст: "{text}"

    Структура ответа:
    {{
        "actor": "кто выполняет действие",
        "action": "что делает",
        "object": "над чем выполняется действие",
        "result": "ожидаемый результат"
    }}"""

    try:
        response = await llm.ainvoke(prompt)
        return json.loads(response.strip())
    except Exception as e:
        logger.error(f"LLM error: {str(e)}")
        return {
            "actor": "Система",
            "action": "не определено",
            "object": "не определено",
            "result": "не определено"
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)

    try:
        while True:
            try:
                # Ожидаем текстовое сообщение от клиента
                data = await websocket.receive_text()
                logger.info(f"Received from {session_id}: {data}")

                # Извлекаем сущности
                entities = await extract_entities(data)
                entities["session_id"] = session_id
                entities["timestamp"] = datetime.now().isoformat()

                # Отправляем ответ
                await websocket.send_json(entities)
                logger.info(f"Sent to {session_id}: {entities}")

            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON: {str(e)}"
                await websocket.send_text(error_msg)
                logger.error(error_msg)

    except WebSocketDisconnect:
        logger.info(f"Client {session_id} disconnected")
    except Exception as e:
        logger.error(f"Error with {session_id}: {str(e)}")
    finally:
        manager.disconnect(session_id)


@app.get("/")
async def health_check():
    return {"status": "OK"}