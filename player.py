import asyncio
import logging
import shutil


async def play_stream(chunks):
    """Play audio chunks using ffplay if available."""
    if not shutil.which("ffplay"):
        logging.error("ffplay not found. Cannot play audio stream.")
        async for _ in chunks:
            pass
        return
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
