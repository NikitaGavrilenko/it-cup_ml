import requests
import logging
from pathlib import Path
from transformers import pipeline

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.stt = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small",
            device="cpu"
        )
        self.server_url = "http://localhost:8000/api/process"

    def transcribe(self, audio_path: str) -> str:
        """Транскрибация аудио в текст"""
        try:
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Файл не найден: {audio_path}")

            logger.info("Начало распознавания аудио...")
            result = self.stt(audio_path)
            text = result.get("text", "").strip()

            if not text:
                raise ValueError("Пустой результат распознавания")

            logger.info(f"Распознанный текст: {text}")
            return text

        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            raise

    def send_to_server(self, text: str) -> dict:
        """Отправка текста на сервер"""
        try:
            logger.info("Отправка запроса на сервер...")
            response = requests.post(
                self.server_url,
                json={"text": text, "command": "voice"},
                timeout=60  # Увеличенный таймаут
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка соединения: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            raise


if __name__ == "__main__":
    client = Client()
    audio_file = "test_audio.mp3"

    try:
        # Проверка сервера
        health = requests.get("http://localhost:8000/", timeout=5)
        logger.info(f"Сервер доступен: {health.status_code}")

        # Обработка аудио
        text = client.transcribe(audio_file)
        result = client.send_to_server(text)

        logger.info(f"Результат обработки:\n{result}")

    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")