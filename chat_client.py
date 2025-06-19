import asyncio
import logging
import os
import time
from typing import AsyncIterator

import openai

import config


class ChatClient:
    def __init__(self, api_key: str | None = None, debug: bool = False):
        self.debug = debug
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=config.BASE_URL,
            timeout=config.TIMEOUT,
        )

    async def _request_with_retry(self, func, *args, **kwargs):
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                start = time.monotonic()
                resp = await func(*args, **kwargs)
                elapsed = time.monotonic() - start
                logging.debug("Request took %.2fs", elapsed)
                return resp
            except openai.APIStatusError as e:
                if 500 <= e.status_code < 600:
                    delay = config.RETRY_BACKOFF**attempt
                    logging.warning(
                        "Server %s error, retry in %s s", e.status_code, delay
                    )
                    await asyncio.sleep(delay)
                    continue
                if e.status_code == 429:
                    logging.warning(
                        "\u041f\u0440\u0435\u0432\u044b\u0448\u0435\u043d \u043b\u0438\u043c\u0438\u0442 \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432, \u0436\u0434\u0451\u043c 20 \u0441"
                    )
                    await asyncio.sleep(20)
                    continue
                raise
            except (openai.APITimeoutError, openai.APIConnectionError) as e:
                delay = config.RETRY_BACKOFF**attempt
                logging.warning("Network error %s, retry in %s s", e, delay)
                await asyncio.sleep(delay)
            except Exception:
                logging.exception("Unexpected error")
                raise
        raise RuntimeError("Failed after retries")

    async def ask(self, text: str) -> str:
        payload = {
            "model": config.TEXT_MODEL,
            "messages": [{"role": "user", "content": text}],
        }
        if self.debug:
            logging.debug("Chat payload: %s", payload)
        resp = await self._request_with_retry(
            self.client.chat.completions.create, **payload
        )
        if self.debug and resp.usage is not None:
            logging.debug(
                "Tokens: prompt %s, completion %s",
                resp.usage.prompt_tokens,
                resp.usage.completion_tokens,
            )
        return resp.choices[0].message.content.strip()

    async def tts(
        self, text: str, voice: str = config.DEFAULT_VOICE, fmt: str = "mp3"
    ) -> AsyncIterator[bytes]:
        params = {
            "model": config.VOICE_MODEL,
            "voice": voice,
            "input": text,
            "response_format": fmt,
            "stream": True,
        }
        if self.debug:
            dbg = {k: v for k, v in params.items() if k != "input"}
            logging.debug("TTS params: %s", dbg)
        resp = await self._request_with_retry(self.client.audio.speech.create, **params)
        return resp.aiter_bytes()
