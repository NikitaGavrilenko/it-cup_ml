from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import uvicorn
from natasha import Doc, Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger
from langchain_ollama import OllamaLLM
import time

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Инициализация NLP
try:
    logger.info("Инициализация NLP...")
    segmenter = Segmenter()
    morph_vocab = MorphVocab()
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)

    # Тестовая обработка
    test_doc = Doc("тест")
    test_doc.segment(segmenter)
    test_doc.tag_morph(morph_tagger)
    logger.info("NLP модели успешно загружены")
except Exception as e:
    logger.error(f"Ошибка инициализации NLP: {e}")
    raise

# Инициализация LLM
try:
    logger.info("Инициализация LLM...")
    llm = OllamaLLM(
        model="mistral",
        base_url="http://localhost:11434",
        timeout=300  # Увеличенный таймаут
    )
    # Тестовый запрос
    test_response = llm.invoke("Тест")[:50]
    logger.info(f"LLM подключена: {test_response}...")
except Exception as e:
    logger.error(f"Ошибка подключения LLM: {e}")
    raise


class Request(BaseModel):
    text: str
    command: str = "parse"


class Response(BaseModel):
    status: str
    data: Dict[str, Any] = {}
    processing_time: float


@app.post("/api/process")
async def process_text(request: Request):
    start_time = time.time()
    try:
        logger.info(f"Обработка запроса: {request.command}")

        if not request.text.strip():
            raise HTTPException(400, "Пустой текст")

        # NLP анализ
        doc = Doc(request.text)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)

        nlp_result = {
            "actors": [t.text for t in doc.tokens if t.pos == "PROPN"],
            "actions": [t.text for t in doc.tokens if t.pos == "VERB"],
            "objects": [t.text for t in doc.tokens if t.pos == "NOUN"]
        }

        # LLM обработка
        if request.command == "voice":
            prompt = f"""Разбери текст на структуру:
            АКТОР|ДЕЙСТВИЕ|ОБЪЕКТ|РЕЗУЛЬТАТ
            Текст: {request.text}"""
            llm_response = llm.invoke(prompt)

            result = {
                "nlp": nlp_result,
                "llm": llm_response,
                "source": "voice"
            }
        else:
            result = {"nlp": nlp_result}

        return Response(
            status="success",
            data=result,
            processing_time=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=600,
        log_level="info"
    )