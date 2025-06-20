# GPT-TTS CLI

Консольный бот для общения с моделью GPT-4.1 с озвучкой ответов. Если `ffplay` недоступен, звук будет воспроизведён через модуль `playsound`.

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
OPENAI_API_KEY=... python main.py [--token KEY] [--save-token] [--voice alloy] [--system "text"] [--debug] [--vtube/--no-vtube]
```

Опцию использования VTube Studio можно заранее указать в `config.py`,
изменив значение `ENABLE_VTUBE` на `True` или `False`.

### Lip sync c VTube Studio

Запустите программу с флагом `--vtube` (или `-v`), чтобы
синхронизировать параметр `MouthOpen` модели VTube Studio с громкостью
озвучки. Приложение подключится к VTube Studio по адресу
`ws://127.0.0.1:8001`. Не забудьте включить доступ к WebSocket API в
настройках VTube Studio.
