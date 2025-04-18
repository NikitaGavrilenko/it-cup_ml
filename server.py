import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import speech_recognition as sr
from langchain_ollama import OllamaLLM

app = FastAPI()

# Конфигурация
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MODEL_NAME = "llama3"  # Измените при необходимости
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# Инициализация
recognizer = sr.Recognizer()
llm = OllamaLLM(model=MODEL_NAME)


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[session_id] = websocket
        return session_id

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]


manager = ConnectionManager()


async def extract_entities(text: str) -> dict:
    """Анализ текста с помощью LLM"""
    prompt = f"""Извлеки сущности из требования:
    Текст: "{text}"
    Формат JSON: {{"actor":"","action":"","object":"","result":""}}
    Пример: "Система должна логировать ошибки" → {{"actor":"Система","action":"логировать","object":"ошибки","result":"отслеживание проблем"}}"""

    try:
        response = await llm.ainvoke(prompt)
        return json.loads(response)
    except Exception as e:
        print(f"LLM Error: {e}")
        return fallback_parser(text)


def fallback_parser(text: str) -> dict:
    """Резервный парсер"""
    words = text.split()
    return {
        "actor": words[0] if words else "Система",
        "action": " ".join(words[1:3]) if len(words) > 2 else "не определено",
        "object": " ".join(words[3:]) if len(words) > 3 else "не определено",
        "result": text.split(".")[0],
        "is_fallback": True
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)
    try:
        while True:
            # Получаем данные от клиента
            data = await websocket.receive_json()

            if data["type"] == "text":
                # Текстовый анализ
                text = data["content"]
                entities = await extract_entities(text)
                await websocket.send_json({
                    "type": "analysis_result",
                    "text": text,
                    "entities": entities,
                    "timestamp": datetime.now().isoformat()
                })

            elif data["type"] == "audio":
                # Обработка аудио
                audio_data = bytes(data["content"], "latin1")
                audio_path = UPLOAD_DIR / f"{session_id}.wav"

                with open(audio_path, "wb") as f:
                    f.write(audio_data)

                with sr.AudioFile(str(audio_path)) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio, language="ru-RU")
                    os.remove(audio_path)

                entities = await extract_entities(text)
                await websocket.send_json({
                    "type": "audio_result",
                    "text": text,
                    "entities": entities,
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


@app.get("/health")
async def health_check():
    return {"status": "OK", "model": MODEL_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)