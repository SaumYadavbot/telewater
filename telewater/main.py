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
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


def start_bot(API_ID: int, API_HASH: str, name: str, token: str):
    threading.Thread(target=run_web_server, daemon=True).start()

    os.makedirs(name, exist_ok=True)
    os.chdir(name)

        print("BOT STARTING...")

    download_image(url=conf.config.watermark)
    print("IMAGE DOWNLOAD COMPLETE")

    print("STARTING TELEGRAM...")
    client = TelegramClient(name, API_ID, API_HASH).start(bot_token=token)
    print("TELEGRAM BOT LOGIN COMPLETE")

    while True:
        try:
            print("Starting Telegram bot...")
            client.start(bot_token=token)
            print("Telegram bot authorization successful.")
            break

        except FloodWaitError as e:
            wait_time = int(e.seconds) + 10
            print(
                f"Telegram requested a wait of {e.seconds} seconds. "
                f"Waiting {wait_time} seconds before retrying..."
            )
            time.sleep(wait_time)

        except Exception as e:
            print(f"Telegram startup error: {type(e).__name__}: {e}")
            raise

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

    for key, val in ALL_EVENTS.items():
        print(f"Adding event {key}")
        client.add_event_handler(*val)

    print(f"Started bot {name}")
    client.run_until_disconnected()


if __name__ == "__main__":
    start_bot(
        int(os.environ["API_ID"]),
        os.environ["API_HASH"],
        os.environ.get("BOT_NAME", "telewater"),
        os.environ["API_TOKEN"],
    )
