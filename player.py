import asyncio
import logging
import os
import shutil
import tempfile
from typing import AsyncIterator, Optional

import numpy as np

from vtube import VTubeClient

try:
    from playsound import playsound
except Exception:  # pragma: no cover - optional dependency
    playsound = None


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
    """Play audio chunks using ffplay if available or playsound as fallback.

    Args:
        chunks: Stream of audio bytes.
        pcm: ``True`` if ``chunks`` provide raw PCM s16le 24 kHz mono.
        vtube: Optional ``VTubeClient`` for lip sync updates.
    """
    if shutil.which("ffplay"):
        cmd = [
            "ffplay",
            "-autoexit",
            "-nodisp",
            "-loglevel",
            "quiet",
        ]
        if pcm:
            cmd += ["-f", "s16le", "-ar", "24000", "-ac", "1"]
        cmd.append("-")
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdin=asyncio.subprocess.PIPE
        )
        async for chunk in chunks:
            if vtube and pcm:
                level = _rms_level(chunk)
                asyncio.create_task(vtube.send_level(level))
            if proc.stdin is not None:
                proc.stdin.write(chunk)
                await proc.stdin.drain()
        if proc.stdin:
            proc.stdin.close()
        await proc.wait()
        return

    if playsound and not pcm:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            async for chunk in chunks:
                tmp.write(chunk)
            tmp_path = tmp.name
        try:
            playsound(tmp_path)
        finally:
            os.unlink(tmp_path)
        return

    logging.error("No audio player available. Install ffmpeg or playsound module.")
    async for _ in chunks:
        pass
