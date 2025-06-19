# GPT-TTS CLI

Консольный бот для общения с моделью GPT-4.1 с озвучкой ответов. Если `ffplay` недоступен, используется модуль `playsound`.

## Требования
- Python 3.10+
- httpx >= 0.28
- ffplay (из пакета ffmpeg) или модуль `playsound`
- python-dotenv

Все зависимости можно установить командой:

```bash
pip install -r requirements.txt
```

Клиент использует [httpx](https://www.python-httpx.org/) напрямую и не зависит от библиотеки `openai`, поэтому конфликт версий `httpx` исключён.
Системный промпт по умолчанию задаётся в `config.py`. Его можно переопределить опцией `--system` при запуске.

## Запуск
```bash
# переменная окружения OPENAI_API_KEY должна содержать ваш токен
# можно создать файл `.env` с записью `OPENAI_API_KEY=...`
# или передать ключ параметром `--token`. Опция `--save-token` сохраняет его в `.env`
OPENAI_API_KEY=... python main.py [--token KEY] [--save-token] [--voice alloy] [--system "text"] [--debug]
```
