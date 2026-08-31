"""Various utility functions are defined in this module."""

import logging
import os
import re
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from telewater import conf


def create_text_watermark(
    text: str = "ETERNAL CIVIL ACADEMY",
    filename: str = "image.png",
    opacity: int = 30,
) -> bool:
    """
    Creates a transparent text watermark image.

    Opacity:
        0   = invisible
        30  = 30% opacity
        100 = fully visible
    """

    try:
        # 30% opacity = approximately 51/255
        alpha = int(255 * (opacity / 100))

        # Transparent watermark canvas
        width = 1000
        height = 180

        watermark = Image.new(
            "RGBA",
            (width, height),
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(watermark)

        # Try common Linux fonts available on Render
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]

        font = None

        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, 64)
                break

        # Fallback font
        if font is None:
            font = ImageFont.load_default()

        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # White text with 20% opacity
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, alpha),
        )

        # Save transparent PNG
        watermark.save(filename, "PNG")

        print(
            f"{opacity}% opacity text watermark created successfully",
            flush=True,
        )

        return True

    except Exception as err:
        print(
            f"TEXT WATERMARK ERROR: {type(err).__name__}: {err}",
            flush=True,
        )
        return False


def download_image(url: str, filename: str = "image.png") -> bool:
    """
    Kept with the old function name so the existing bot code
    does not need to be changed.

    Instead of downloading an external image, it now creates
    the text watermark locally.
    """

    # Remove old watermark so every deployment gets a fresh one
    try:
        if os.path.exists(filename):
            os.remove(filename)
            print("Old watermark removed", flush=True)
    except Exception as err:
        print(f"Could not remove old watermark: {err}", flush=True)

    return create_text_watermark(
        text="ETERNAL CIVIL ACADEMY",
        filename=filename,
        opacity=30,
    )


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


def stamp(file: str, user: str):

    now = str(datetime.now())

    outf = safe_name(f"{user} {now} {file}")

    try:
        os.rename(file, outf)
        return outf

    except Exception as err:
        logging.warning(
            f"Stamping file name failed for {file} to {outf}: {err}"
        )


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
