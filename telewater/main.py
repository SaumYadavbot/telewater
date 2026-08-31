""" This module provides the pythonic entry point for accessing telewater.
"""


import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telethon.sync import TelegramClient, functions, types

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

    download_image(url=conf.config.watermark)

    client = TelegramClient(name, API_ID, API_HASH).start(bot_token=token)

    client(
        functions.bots.SetBotCommandsRequest(
            commands=[
                types.BotCommand(command=key, description=value)
                for key, value in conf.COMMANDS.items()
            ]
        )
    )

    for key, val in ALL_EVENTS.items():
        print(f"Adding event {key}")
        client.add_event_handler(*val)

    print(f"Started bot {name}")
    client.run_until_disconnected()
