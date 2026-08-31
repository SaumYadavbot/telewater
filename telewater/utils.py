""" Various utility functions are defined in this module.
"""

import logging
import os
import re
import shutil
from datetime import datetime

import requests

from telewater import conf


def download_image(url: str, filename: str = "image.png") -> bool:
    try:
        print("Downloading watermark image ...")

        response = requests.get(url, stream=True, timeout=30)

        if response.status_code == 200:
            print("Got watermark file response")

            with open(filename, "wb") as file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, file)

            print(f"Watermark file created: {filename}")
            return True

        print(f"Watermark download failed: HTTP {response.status_code}")
        return False

    except Exception as err:
        print(f"Watermark download error: {err}")
        return False


def get_args(text: str):
    splitted = text.split(" ", 1)

    if not len(splitted) == 2:
        return ""

    prefix, args = splitted

    print(prefix)

    args = args.strip()

    print(args)

    return args


def cleanup(*files):
    """
    Safely remove temporary files.
    Ignore None values and already deleted files.
    """

    for file in files:

        # Prevent TypeError when file path is None
        if not file:
            continue

        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up: {file}")
            else:
                print(f"File already removed: {file}")

        except Exception as err:
            logging.warning(f"Cleanup failed for {file}: {err}")


def stamp(file: str, user: str):

    now = str(datetime.now())

    outf = safe_name(f"{user} {now} {file}")

    try:
        os.rename(file, outf)

        print(f"File stamped: {outf}")

        return outf

    except Exception as err:

        logging.warning(
            f"Stamping file name failed for {file} to {outf}: {err}"
        )

        # IMPORTANT:
        # If rename fails, return the original file path
        # instead of returning None.
        return file


def safe_name(file_name: str):
    return re.sub(
        pattern=r"[-!@#$%^&*()\s]",
        repl="_",
        string=file_name
    )


def gen_kv_str():

    kv_string = "\n**Below is your current configuration**\n\n"

    for k, v in conf.config.dict().items():

        kv_string += f"`{k} : {v}`\n"

    return kv_string
