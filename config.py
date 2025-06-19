BASE_URL = "https://api.proxyapi.ru/openai/v1"
TEXT_MODEL = "gpt-4.1"
VOICE_MODEL = "tts-1-hd"
DEFAULT_VOICE = "alloy"
CHAT_ENDPOINT = f"{BASE_URL}/chat/completions"
TTS_ENDPOINT = f"{BASE_URL}/audio/speech"
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2
# Default system prompt used to initialize conversation history
SYSTEM_PROMPT = ""
