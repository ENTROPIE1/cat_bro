import asyncio
import logging
import os
import time
from typing import AsyncIterator

import httpx

import config


class ChatClient:
    def __init__(
        self,
        api_key: str | None = None,
        debug: bool = False,
        system_prompt: str | None = config.SYSTEM_PROMPT,
        history_limit: int = 40,
    ):
        self.debug = debug
        self.history_limit = history_limit
        self.messages: list[dict[str, str]] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(
            base_url=config.BASE_URL,
            timeout=config.TIMEOUT,
            headers=self._headers,
        )

    async def _request_with_retry(self, func, *args, **kwargs):
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                start = time.monotonic()
                resp = await func(*args, **kwargs)
                resp.raise_for_status()
                elapsed = time.monotonic() - start
                logging.debug("Request took %.2fs", elapsed)
                return resp
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if 500 <= status < 600:
                    delay = config.RETRY_BACKOFF**attempt
                    logging.warning(
                        "Server %s error, retry in %s s", status, delay
                    )
                    await asyncio.sleep(delay)
                    continue
                if status == 429:
                    logging.warning(
                        "\u041f\u0440\u0435\u0432\u044b\u0448\u0435\u043d \u043b\u0438\u043c\u0438\u0442 \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432, \u0436\u0434\u0451\u043c 20 \u0441"
                    )
                    await asyncio.sleep(20)
                    continue
                raise
            except (httpx.TimeoutException, httpx.TransportError) as e:
                delay = config.RETRY_BACKOFF**attempt
                logging.warning("Network error %s, retry in %s s", e, delay)
                await asyncio.sleep(delay)
            except Exception:
                logging.exception("Unexpected error")
                raise
        raise RuntimeError("Failed after retries")

    async def ask(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})
        payload = {
            "model": config.TEXT_MODEL,
            "messages": self.messages[-self.history_limit :],
        }
        if self.debug:
            logging.debug("Chat payload: %s", payload)
        resp = await self._request_with_retry(
            self.client.post, "/chat/completions", json=payload
        )
        data = resp.json()
        if self.debug and data.get("usage"):
            usage = data["usage"]
            logging.debug(
                "Tokens: prompt %s, completion %s",
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
            )
        reply = data["choices"][0]["message"]["content"].strip()
        self.messages.append({"role": "assistant", "content": reply})
        if len(self.messages) > self.history_limit:
            self.messages = self.messages[-self.history_limit :]
        return reply

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
        resp = await self._request_with_retry(
            self.client.post, "/audio/speech", json=params
        )
        return resp.aiter_bytes()

    async def close(self) -> None:
        await self.client.aclose()
