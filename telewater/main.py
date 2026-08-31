"""This module provides the pythonic entry point for accessing telewater."""

import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telethon.sync import TelegramClient, functions, types
from telethon.errors import FloodWaitError

from telewater import conf
from telewater.bot import ALL_EVENTS
from telewater.utils import download_image


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", "10000"))

    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)

        print(
            f"HEALTH SERVER STARTED ON 0.0.0.0:{port}",
            flush=True
        )

        server.serve_forever()

    except Exception as e:
        print(
            f"HEALTH SERVER ERROR: {type(e).__name__}: {e}",
            flush=True
        )
        raise


def start_bot(API_ID: int, API_HASH: str, name: str, token: str):

    print("========================================", flush=True)
    print("BOT STARTING...", flush=True)
    print("========================================", flush=True)

    # --------------------------------------------------
    # 1. Start Render health server
    # --------------------------------------------------

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    print("HEALTH SERVER THREAD STARTED", flush=True)

    # --------------------------------------------------
    # 2. Create bot working directory
    # --------------------------------------------------

    os.makedirs(name, exist_ok=True)

    # Keep the original telewater behaviour.
    # The watermark/event code may depend on the
    # working directory.
    os.chdir(name)

    print(f"BOT WORKING DIRECTORY: {os.getcwd()}", flush=True)

    # --------------------------------------------------
    # 3. Download watermark image
    # --------------------------------------------------

    print("DOWNLOADING WATERMARK IMAGE...", flush=True)

    try:
        download_image(url=conf.config.watermark)

        print(
            "IMAGE DOWNLOAD COMPLETE",
            flush=True
        )

    except Exception as e:
        print(
            f"IMAGE DOWNLOAD ERROR: {type(e).__name__}: {e}",
            flush=True
        )
        raise

    # --------------------------------------------------
    # 4. Create Telegram client
    # --------------------------------------------------

    print("CREATING TELEGRAM CLIENT...", flush=True)

    client = TelegramClient(
        name,
        API_ID,
        API_HASH
    )

    print(
        "TELEGRAM CLIENT CREATED",
        flush=True
    )

    # --------------------------------------------------
    # 5. Login Telegram bot
    # --------------------------------------------------

    while True:

        try:
            print(
                "STARTING TELEGRAM BOT...",
                flush=True
            )

            client.start(
                bot_token=token
            )

            print(
                "TELEGRAM BOT LOGIN COMPLETE",
                flush=True
            )

            break

        except FloodWaitError as e:

            wait_time = int(e.seconds) + 10

            print(
                f"TELEGRAM FLOOD WAIT: "
                f"{e.seconds} seconds requested.",
                flush=True
            )

            print(
                f"WAITING {wait_time} SECONDS BEFORE RETRYING...",
                flush=True
            )

            time.sleep(wait_time)

        except Exception as e:

            print(
                f"TELEGRAM STARTUP ERROR: "
                f"{type(e).__name__}: {e}",
                flush=True
            )

            raise

    # --------------------------------------------------
    # 6. Set Telegram bot commands
    # --------------------------------------------------

    print(
        "SETTING BOT COMMANDS...",
        flush=True
    )

    try:

        client(
            functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(),
                lang_code="en",
                commands=[
                    types.BotCommand(
                        command=key,
                        description=value
                    )
                    for key, value in conf.COMMANDS.items()
                ]
            )
        )

        print(
            "BOT COMMANDS SET",
            flush=True
        )

    except FloodWaitError as e:

        print(
            f"FLOOD WAIT WHILE SETTING COMMANDS: "
            f"{e.seconds} seconds",
            flush=True
        )

        print(
            "CONTINUING WITHOUT UPDATING COMMAND MENU...",
            flush=True
        )

    except Exception as e:

        print(
            f"BOT COMMAND SETTING ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        print(
            "CONTINUING TO EVENT REGISTRATION...",
            flush=True
        )

    # --------------------------------------------------
    # 7. Register all bot events
    # --------------------------------------------------

    print(
        "REGISTERING BOT EVENTS...",
        flush=True
    )

    for key, val in ALL_EVENTS.items():

        print(
            f"ADDING EVENT: {key}",
            flush=True
        )

        client.add_event_handler(*val)

    print(
        "ALL BOT EVENTS REGISTERED",
        flush=True
    )

    # --------------------------------------------------
    # 8. Bot is fully ready
    # --------------------------------------------------

    print("========================================", flush=True)

    print(
        f"TELEGRAM BOT IS FULLY STARTED: {name}",
        flush=True
    )

    print(
        "WAITING FOR TELEGRAM UPDATES...",
        flush=True
    )

    print("========================================", flush=True)

    # --------------------------------------------------
    # 9. Keep bot running
    # --------------------------------------------------

    client.run_until_disconnected()


if __name__ == "__main__":

    start_bot(
        int(os.environ["API_ID"]),
        os.environ["API_HASH"],
        os.environ.get("BOT_NAME", "telewater"),
        os.environ["API_TOKEN"],
    )
