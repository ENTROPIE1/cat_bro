# GPT-TTS CLI

Консольный бот для общения с моделью GPT-4.1 с озвучкой ответов.

## Требования
- Python 3.10+
- openai 1.x
- ffplay (из пакета ffmpeg)

## Запуск
```bash
# переменная окружения OPENAI_API_KEY должна содержать ваш токен
OPENAI_API_KEY=... python main.py [--voice alloy] [--debug]
```
