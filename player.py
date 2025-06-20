import asyncio
import subprocess
import tempfile
import os
import logging
from typing import AsyncIterator

try:
    from playsound import playsound
except Exception:  # pragma: no cover - optional dependency
    playsound = None


FFPLAY_PATH = os.path.join("ffmpeg", "bin", "ffplay.exe")

# Output device name for routing audio through VB-CABLE
AUDIO_OUT = "CABLE Input"


def _play_file_ffplay(path: str) -> bool:
    """Play file using ffplay if available. Return True if successful."""
    if not os.path.exists(FFPLAY_PATH):
        return False
    try:
        logging.info("Аудио выводится в устройство: %s", AUDIO_OUT)
        subprocess.run(
            [FFPLAY_PATH, "-nodisp", "-autoexit",
             "-audio_device", AUDIO_OUT,
             path],
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


async def play_stream(stream_iter: AsyncIterator[bytes]) -> None:
    """Play an audio stream.

    The iterator must yield raw bytes of an MP3 file. The data is saved to a
    temporary ``.mp3`` file which is then played using ``ffplay`` located at
    :data:`FFPLAY_PATH`. After playback the file is removed.
    """

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            async for chunk in stream_iter:
                tmp.write(chunk)
            tmp_path = tmp.name
        play_file(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
