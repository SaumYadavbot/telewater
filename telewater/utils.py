"""Various utility functions are defined in this module."""

import logging
import os
import re
import shutil
import subprocess
from datetime import datetime

import requests

from telewater import conf


def download_image(url: str, filename: str = "image.png") -> bool:
    try:
        print("Downloading watermark image ...", flush=True)

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        print("Got watermark file response", flush=True)

        with open(filename, "wb") as file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, file)

        print(f"Watermark file created: {filename}", flush=True)

        # Create a 15% opacity version.
        # watermark.py uses FFmpeg internally, so FFmpeg is already
        # required by this project.
        transparent_filename = "watermark_15.png"

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                filename,
                "-vf",
                "format=rgba,colorchannelmixer=aa=0.15",
                transparent_filename,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            print(
                f"FFmpeg watermark opacity error: {result.stderr}",
                flush=True,
            )
            return False

        print(
            "15% opacity watermark created successfully",
            flush=True,
        )

        return True

    except Exception as err:
        print(
            f"Watermark download/processing error: {type(err).__name__}: {err}",
            flush=True,
        )
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
    for file in files:
        try:
            os.remove(file)
        except FileNotFoundError:
            logging.info(f"File {file} does not exist.")
        except Exception as err:
            logging.warning(
                f"Could not remove {file}: {err}"
            )


def stamp(file: str, user: str):
    now = str(datetime.now())

    outf = safe_name(
        f"{user} {now} {file}"
    )

    try:
        os.rename(file, outf)
        return outf

    except Exception as err:
        logging.warning(
            f"Stamping file name failed for {file} to {outf}: {err}"
        )
        return file


def safe_name(file_name: str):
    return re.sub(
        pattern=r"[-!@#$%^&*()\s]",
        repl="_",
        string=file_name,
    )


def gen_kv_str():
    kv_string = "\n**Below is your current configuration**\n\n"

    for k, v in conf.config.dict().items():
        kv_string += f"`{k} : {v}`\n"

    return kv_string
