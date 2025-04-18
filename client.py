import websockets
import asyncio
import json


async def test_client():
    test_requirements = [
        "Система должна автоматически создавать резервные копии баз данных каждые 24 часа",
        "Администратор должен иметь возможность просматривать историю изменений всех документов",
        "Пользователь может отменять последнее действие в течение 5 минут после его выполнения",
        "Модуль отчетов должен генерировать PDF-документы по шаблону"
    ]

    try:
        # Устанавливаем таймаут через asyncio.wait_for
        async with websockets.connect("ws://localhost:8000/ws") as ws:
            print("Тестирование извлечения сущностей...\n")

            for req in test_requirements:
                print(f"Отправка требования: {req}")
                await ws.send(req)  # Отправляем требование

                # Получаем ответ с таймаутом
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    entities = json.loads(response)

                    print("\nИзвлечённые сущности:")
                    print(f"- Актор: {entities['actor']}")
                    print(f"- Действие: {entities['action']}")
                    print(f"- Объект: {entities['object']}")
                    print(f"- Результат: {entities['result']}\n")

                    await asyncio.sleep(1)  # Пауза между запросами

                except asyncio.TimeoutError:
                    print("Таймаут при ожидании ответа от сервера")
                    continue

    except websockets.exceptions.ConnectionClosedError:
        print("Соединение было закрыто сервером")
    except websockets.exceptions.InvalidURI:
        print("Неверный URL сервера")
    except websockets.exceptions.WebSocketException as e:
        print(f"Ошибка WebSocket: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_client())