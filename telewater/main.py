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
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.environ.get("PORT", "8080"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"HEALTH SERVER STARTED ON PORT {port}", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"HEALTH SERVER ERROR: {e}", flush=True)


def start_bot(API_ID: int, API_HASH: str, name: str, token: str):
    print("BOT STARTING...", flush=True)

    # Start Render health server
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # Create bot working directory (avoid changing working directory globally)
    os.makedirs(name, exist_ok=True)

    # Download watermark image
    print("DOWNLOADING WATERMARK IMAGE...", flush=True)
    try:
        download_image(url=conf.config.watermark)
        print("IMAGE DOWNLOAD COMPLETE", flush=True)
    except Exception as e:
        print(f"IMAGE DOWNLOAD FAILED: {e}", flush=True)

    # Create Telegram client using path inside session folder
    print("CREATING TELEGRAM CLIENT...", flush=True)
    session_path = os.path.join(name, name)
    client = TelegramClient(session_path, API_ID, API_HASH)

    print("TELEGRAM CLIENT CREATED", flush=True)

    # Start Telegram bot
    while True:
        try:
            print("STARTING TELEGRAM BOT...", flush=True)
            client.start(bot_token=token)
            print("TELEGRAM BOT LOGIN COMPLETE", flush=True)
            break
        except FloodWaitError as e:
            wait_time = int(e.seconds) + 10
            print(f"TELEGRAM FLOOD WAIT: {e.seconds} seconds requested.", flush=True)
            print(f"WAITING {wait_time} SECONDS BEFORE RETRYING...", flush=True)
            time.sleep(wait_time)
        except Exception as e:
            print(f"TELEGRAM STARTUP ERROR: {type(e).__name__}: {e}", flush=True)
            raise e

    # Set Telegram bot commands
    try:
        print("SETTING BOT COMMANDS...", flush=True)
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
        print("BOT COMMANDS SET", flush=True)
    except Exception as e:
        print(f"FAILED TO SET COMMANDS: {e}", flush=True)

    # Register all bot event handlers
    print("REGISTERING BOT EVENTS...", flush=True)
    for key, val in ALL_EVENTS.items():
        print(f"ADDING EVENT: {key}", flush=True)
        client.add_event_handler(*val)

    print("ALL BOT EVENTS REGISTERED", flush=True)
    print(f"BOT IS FULLY STARTED: {name}", flush=True)

    # Keep bot running
    client.run_until_disconnected()


if __name__ == "__main__":
    start_bot(
        int(os.environ["API_ID"]),
        os.environ["API_HASH"],
        os.environ.get("BOT_NAME", "telewater"),
        os.environ["API_TOKEN"],
    )
