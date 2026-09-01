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


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"OK"
        )

    def log_message(
        self,
        format,
        *args
    ):
        pass


def run_web_server():

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    try:

        server = HTTPServer(
            (
                "0.0.0.0",
                port
            ),
            HealthHandler
        )

        print(
            f"HEALTH SERVER STARTED ON "
            f"0.0.0.0:{port}",
            flush=True
        )

        server.serve_forever()

    except Exception as e:

        print(
            f"HEALTH SERVER ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        raise


# =========================================================
# SET BOT COMMANDS
# =========================================================

def set_bot_commands(client):

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
                    for key, value
                    in conf.COMMANDS.items()
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
            "CONTINUING WITHOUT UPDATING "
            "COMMAND MENU...",
            flush=True
        )

    except Exception as e:

        print(
            f"BOT COMMAND SETTING ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        print(
            "CONTINUING...",
            flush=True
        )


# =========================================================
# START BOT
# =========================================================

def start_bot(
    API_ID: int,
    API_HASH: str,
    name: str,
    token: str
):

    print(
        "========================================",
        flush=True
    )

    print(
        "BOT STARTING...",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

    # -----------------------------------------------------
    # 1. START RENDER HEALTH SERVER
    # -----------------------------------------------------

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    print(
        "HEALTH SERVER THREAD STARTED",
        flush=True
    )

    # -----------------------------------------------------
    # 2. CREATE WORKING DIRECTORY
    # -----------------------------------------------------

    os.makedirs(
        name,
        exist_ok=True
    )

    os.chdir(
        name
    )

    print(
        f"BOT WORKING DIRECTORY: "
        f"{os.getcwd()}",
        flush=True
    )

    # -----------------------------------------------------
    # 3. DOWNLOAD WATERMARK IMAGE
    # -----------------------------------------------------

    print(
        "DOWNLOADING WATERMARK IMAGE...",
        flush=True
    )

    try:

        download_image(
            url=conf.config.watermark
        )

        print(
            "IMAGE DOWNLOAD COMPLETE",
            flush=True
        )

    except Exception as e:

        print(
            f"IMAGE DOWNLOAD ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        raise

    # -----------------------------------------------------
    # 4. CREATE TELEGRAM CLIENT
    # -----------------------------------------------------

    print(
        "CREATING TELEGRAM CLIENT...",
        flush=True
    )

    client = TelegramClient(
        name,
        API_ID,
        API_HASH,

        # Automatically retry Telegram connection.
        connection_retries=None,

        # Wait 5 seconds between connection retries.
        retry_delay=5,

        # Enable Telethon automatic reconnect.
        auto_reconnect=True,
    )

    print(
        "TELEGRAM CLIENT CREATED",
        flush=True
    )

    # -----------------------------------------------------
    # 5. LOGIN WITH AUTOMATIC RETRY
    # -----------------------------------------------------

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

            wait_time = (
                int(e.seconds)
                + 10
            )

            print(
                f"TELEGRAM FLOOD WAIT: "
                f"{e.seconds} seconds",
                flush=True
            )

            print(
                f"WAITING {wait_time} "
                f"SECONDS BEFORE RETRYING...",
                flush=True
            )

            time.sleep(
                wait_time
            )

        except Exception as e:

            print(
                f"TELEGRAM STARTUP ERROR: "
                f"{type(e).__name__}: {e}",
                flush=True
            )

            print(
                "RETRYING TELEGRAM STARTUP "
                "IN 10 SECONDS...",
                flush=True
            )

            time.sleep(
                10
            )


    # -----------------------------------------------------
    # 6. SET BOT COMMANDS
    # -----------------------------------------------------

    set_bot_commands(
        client
    )

    # -----------------------------------------------------
    # 7. REGISTER EVENTS ONLY ONCE
    # -----------------------------------------------------

    print(
        "REGISTERING BOT EVENTS...",
        flush=True
    )

    for key, val in ALL_EVENTS.items():

        print(
            f"ADDING EVENT: {key}",
            flush=True
        )

        client.add_event_handler(
            *val
        )

    print(
        "ALL BOT EVENTS REGISTERED",
        flush=True
    )

    # -----------------------------------------------------
    # 8. BOT READY
    # -----------------------------------------------------

    print(
        "========================================",
        flush=True
    )

    print(
        f"TELEGRAM BOT IS FULLY STARTED: {name}",
        flush=True
    )

    print(
        "TELEGRAM AUTO-RECONNECT: ENABLED",
        flush=True
    )

    print(
        "WAITING FOR TELEGRAM UPDATES...",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

    # -----------------------------------------------------
    # 9. MAIN CONNECTION LOOP
    # -----------------------------------------------------

    while True:

        try:

            # -------------------------------------------------
            # CHECK CONNECTION BEFORE RUNNING
            # -------------------------------------------------

            if not client.is_connected():

                print(
                    "TELEGRAM CONNECTION IS NOT ACTIVE.",
                    flush=True
                )

                print(
                    "CONNECTING AGAIN...",
                    flush=True
                )

                client.connect()

                if not client.is_user_authorized():

                    print(
                        "TELEGRAM CLIENT IS NOT AUTHORIZED.",
                        flush=True
                    )

                    client.start(
                        bot_token=token
                    )

                print(
                    "TELEGRAM CONNECTION RESTORED.",
                    flush=True
                )

            # -------------------------------------------------
            # KEEP TELEGRAM RUNNING
            # -------------------------------------------------

            print(
                "TELEGRAM CONNECTION ACTIVE.",
                flush=True
            )

            client.run_until_disconnected()

            # -------------------------------------------------
            # IF THIS RETURNS, CONNECTION ENDED
            # -------------------------------------------------

            print(
                "========================================",
                flush=True
            )

            print(
                "TELEGRAM CONNECTION ENDED.",
                flush=True
            )

            print(
                "RECONNECTING IN 5 SECONDS...",
                flush=True
            )

            print(
                "========================================",
                flush=True
            )

            time.sleep(
                5
            )

        except FloodWaitError as e:

            wait_time = (
                int(e.seconds)
                + 10
            )

            print(
                f"TELEGRAM FLOOD WAIT: "
                f"{e.seconds} seconds",
                flush=True
            )

            print(
                f"WAITING {wait_time} "
                f"SECONDS BEFORE RECONNECT...",
                flush=True
            )

            time.sleep(
                wait_time
            )

        except KeyboardInterrupt:

            print(
                "BOT STOPPED BY USER.",
                flush=True
            )

            break

        except Exception as e:

            print(
                "========================================",
                flush=True
            )

            print(
                f"TELEGRAM CONNECTION ERROR: "
                f"{type(e).__name__}: {e}",
                flush=True
            )

            print(
                "========================================",
                flush=True
            )

            # -------------------------------------------------
            # CLEAN DISCONNECT
            # -------------------------------------------------

            try:

                if client.is_connected():

                    print(
                        "DISCONNECTING TELEGRAM CLIENT...",
                        flush=True
                    )

                    client.disconnect()

            except Exception as disconnect_error:

                print(
                    f"DISCONNECT ERROR: "
                    f"{type(disconnect_error).__name__}: "
                    f"{disconnect_error}",
                    flush=True
                )

            # -------------------------------------------------
            # RETRY
            # -------------------------------------------------

            print(
                "RECONNECTING IN 5 SECONDS...",
                flush=True
            )

            time.sleep(
                5
            )

    # -----------------------------------------------------
    # FINAL CLEAN DISCONNECT
    # -----------------------------------------------------

    try:

        if client.is_connected():

            client.disconnect()

    except Exception:

        pass


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    start_bot(
        int(
            os.environ["API_ID"]
        ),
        os.environ["API_HASH"],
        os.environ.get(
            "BOT_NAME",
            "telewater"
        ),
        os.environ["API_TOKEN"],
    )
