import websockets
import asyncio
import json
import pyaudio
import base64

async def send_text(ws, text):
    await ws.send(json.dumps({
        "type": "text",
        "content": text
    }))
    response = await ws.recv()
    print("\nРезультат анализа текста:")
    print(json.dumps(json.loads(response), indent=2, ensure_ascii=False))

async def send_audio(ws):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )

    print("Запись аудио (5 секунд)...")
    frames = []
    for _ in range(0, int(16000 / 1024 * 5)):
        data = stream.read(1024)
        frames.append(data)
    stream.stop_stream()
    stream.close()

    audio_bytes = b"".join(frames)
    await ws.send(json.dumps({
        "type": "audio",
        "content": base64.b64encode(audio_bytes).decode("latin1")
    }))
    response = await ws.recv()
    print("\nРезультат анализа аудио:")
    print(json.dumps(json.loads(response), indent=2, ensure_ascii=False))

async def main():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        while True:
            print("\n1. Анализ текста")
            print("2. Анализ аудио")
            print("3. Выход")
            choice = input("Выберите действие: ")

            if choice == "1":
                text = input("Введите требование: ")
                await send_text(ws, text)
            elif choice == "2":
                await send_audio(ws)
            elif choice == "3":
                break

if __name__ == "__main__":
    asyncio.run(main())