import asyncio
import logging
import os
import shutil
import tempfile

try:
    from playsound import playsound
except Exception:  # pragma: no cover - optional dependency
    playsound = None


async def play_stream(chunks):
    """Play audio chunks using ffplay if available or playsound as fallback."""
    if shutil.which("ffplay"):
        proc = await asyncio.create_subprocess_exec(
            "ffplay",
            "-autoexit",
            "-nodisp",
            "-loglevel",
            "quiet",
            "-",
            stdin=asyncio.subprocess.PIPE,
        )
        async for chunk in chunks:
            if proc.stdin is not None:
                proc.stdin.write(chunk)
                await proc.stdin.drain()
        if proc.stdin:
            proc.stdin.close()
        await proc.wait()
        return

    if playsound:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            async for chunk in chunks:
                tmp.write(chunk)
            tmp.flush()
            tmp_path = tmp.name
        try:
            await asyncio.to_thread(playsound, tmp_path)
        except Exception as e:  # pragma: no cover - platform specific
            logging.error("playsound failed: %s", e)
        finally:
            os.unlink(tmp_path)
        return

    logging.error("No audio player available. Install ffmpeg or playsound module.")
    async for _ in chunks:
        pass
