import asyncio
import subprocess
import tempfile
import os
import logging
from typing import AsyncIterator, Optional

import numpy as np

from vtube import VTubeClient

try:
    from playsound import playsound
except Exception:  # pragma: no cover - optional dependency
    playsound = None


FFPLAY_PATH = os.path.join("ffmpeg", "bin", "ffplay.exe")


def _play_file_ffplay(path: str) -> bool:
    """Play file using ffplay if available. Return True if successful."""
    if not os.path.exists(FFPLAY_PATH):
        return False
    try:
        subprocess.run(
            [FFPLAY_PATH, "-nodisp", "-autoexit", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception as e:  # pragma: no cover - runtime path issues
        logging.warning("ffplay error: %s", e)
        return False


def _play_file_playsound(path: str) -> bool:
    """Play file using playsound if available."""
    if playsound is None:
        return False
    try:
        playsound(path)
        return True
    except Exception as e:  # pragma: no cover - runtime path issues
        logging.error("playsound error: %s", e)
        return False


def play_file(path: str) -> None:
    if not os.path.exists(path):
        logging.warning("Файл для воспроизведения не найден: %s", path)
        return
    if _play_file_ffplay(path):
        return
    if _play_file_playsound(path):
        return
    logging.error("Не удалось воспроизвести звук: ffplay и playsound недоступны")


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
    """Save audio stream to a temp file and play it."""
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            async for chunk in chunks:
                if vtube and pcm:
                    level = _rms_level(chunk)
                    asyncio.create_task(vtube.send_level(level))
                tmp.write(chunk)
            tmp_path = tmp.name
        play_file(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
