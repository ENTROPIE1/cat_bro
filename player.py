import asyncio
import subprocess
import tempfile
import os
import logging
from typing import AsyncIterator, Optional

import numpy as np

from vtube import VTubeClient


FFPLAY_PATH = os.path.join("ffmpeg", "bin", "ffplay.exe")


def play_file_ffplay(path: str):
    if not os.path.exists(FFPLAY_PATH):
        logging.warning("ffplay.exe не найден: %s", FFPLAY_PATH)
        return
    if not os.path.exists(path):
        logging.warning("Файл для воспроизведения не найден: %s", path)
        return
    try:
        subprocess.run(
            [FFPLAY_PATH, "-nodisp", "-autoexit", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception as e:
        logging.error("Ошибка при воспроизведении: %s", e)


def _rms_level(data: bytes) -> float:
    arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    if arr.size == 0:
        return 0.0
    rms = np.sqrt(np.mean(arr ** 2))
    return float(min(max(rms / 32768.0, 0.0), 1.0))


async def play_stream(
    chunks: AsyncIterator[bytes],
    *,
    pcm: bool = False,
    vtube: Optional[VTubeClient] = None,
) -> None:
    """Save audio stream to a temp file and play it using ffplay."""
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            async for chunk in chunks:
                if vtube and pcm:
                    level = _rms_level(chunk)
                    asyncio.create_task(vtube.send_level(level))
                tmp.write(chunk)
            tmp_path = tmp.name
        play_file_ffplay(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
