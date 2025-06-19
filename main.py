import argparse
import asyncio
import logging
import os

import config
from dotenv import load_dotenv, set_key
from pathlib import Path
from chat_client import ChatClient
from player import play_stream


async def run():
    load_dotenv()
    parser = argparse.ArgumentParser(description="GPT-TTS CLI")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="\u0440\u0435\u0436\u0438\u043c \u043e\u0442\u043b\u0430\u0434\u043a\u0438",
    )
    parser.add_argument(
        "--voice",
        default=config.DEFAULT_VOICE,
        help="\u0433\u043e\u043b\u043e\u0441 TTS",
    )
    parser.add_argument(
        "--token",
        help="OpenAI API key",
    )
    parser.add_argument(
        "--system",
        default="",
        help="system prompt",
    )
    parser.add_argument(
        "--save-token",
        action="store_true",
        help="save provided token to .env",
    )
    args = parser.parse_args()

    if args.token:
        os.environ["OPENAI_API_KEY"] = args.token
        if args.save_token:
            env_path = Path(".env")
            set_key(env_path, "OPENAI_API_KEY", args.token)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )

    try:
        client = ChatClient(
            api_key=args.token,
            debug=args.debug,
            system_prompt=args.system,
        )
    except RuntimeError as e:
        print(e)
        return

    print(
        "GPT-TTS CLI. \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u0430\u043f\u0440\u043e\u0441. \u0414\u043b\u044f \u0432\u044b\u0445\u043e\u0434\u0430: /exit, q"
    )
    while True:
        try:
            text = input("\u003e ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in {"/exit", "q", "quit"}:
            break
        if not text:
            continue
        try:
            reply = await client.ask(text)
            print(reply)
            chunks = await client.tts(reply, voice=args.voice)
            await play_stream(chunks)
        except Exception as e:
            logging.error("%s", e)
    print("\u0414\u043e \u0441\u0432\u0438\u0434\u0430\u043d\u0438\u044f!")
    await client.close()


if __name__ == "__main__":
    asyncio.run(run())
