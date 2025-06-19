# GPT-TTS CLI

Консольный бот для общения с моделью GPT-4.1 с озвучкой ответов.

## Требования
- Python 3.10+
- openai 1.x
- ffplay (из пакета ffmpeg)
- python-dotenv

## Запуск
```bash
# переменная окружения OPENAI_API_KEY должна содержать ваш токен
# можно создать файл `.env` с записью `OPENAI_API_KEY=...`
# тогда ключ будет загружен автоматически
OPENAI_API_KEY=... python main.py [--voice alloy] [--debug]
```
