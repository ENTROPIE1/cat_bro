import subprocess, tempfile, os, logging


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
            check=True
        )
    except Exception as e:
        logging.error("Ошибка при воспроизведении: %s", e)


def play_stream(stream_iter: iter):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            for chunk in stream_iter:
                tmp.write(chunk)
            tmp_path = tmp.name
        play_file_ffplay(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
