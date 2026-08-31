"""Telegram event handlers for Telewater."""

import os

from telethon import events
from PIL import Image, ImageDraw, ImageFont

from watermark import File, Watermark, apply_watermark

from telewater import conf
from telewater.utils import cleanup, get_args, gen_kv_str, stamp


# =========================================================
# TEXT WATERMARK SETTINGS
# =========================================================

WATERMARK_TEXT = "ETERNAL CIVIL ACADEMY"
WATERMARK_USERNAME = "@EternalCivilAcademy"

WATERMARK_OPACITY = 51   # 20% of 255
WATERMARK_ANGLE = -12    # Slightly tilted


def create_text_watermark(
    filename="text_watermark.png",
    width=1800,
    height=500,
):
    """Create a transparent diagonal text watermark."""

    transparent = Image.new(
        "RGBA",
        (width, height),
        (255, 255, 255, 0),
    )

    layer = Image.new(
        "RGBA",
        (width, height),
        (255, 255, 255, 0),
    )

    draw = ImageDraw.Draw(layer)

    # Use a standard font available on Render.
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    title_font = ImageFont.truetype(
        font_path,
        110,
    )

    username_font = ImageFont.truetype(
        font_path,
        58,
    )

    # Main text
    title_bbox = draw.textbbox(
        (0, 0),
        WATERMARK_TEXT,
        font=title_font,
    )

    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    title_x = (width - title_width) // 2
    title_y = 150

    draw.text(
        (title_x, title_y),
        WATERMARK_TEXT,
        font=title_font,
        fill=(
            255,
            255,
            255,
            WATERMARK_OPACITY,
        ),
        stroke_width=3,
        stroke_fill=(
            0,
            0,
            0,
            WATERMARK_OPACITY,
        ),
    )

    # Username
    username_bbox = draw.textbbox(
        (0, 0),
        WATERMARK_USERNAME,
        font=username_font,
    )

    username_width = (
        username_bbox[2] - username_bbox[0]
    )

    username_x = (
        width - username_width
    ) // 2

    username_y = (
        title_y
        + title_height
        + 15
    )

    draw.text(
        (username_x, username_y),
        WATERMARK_USERNAME,
        font=username_font,
        fill=(
            255,
            255,
            255,
            WATERMARK_OPACITY,
        ),
        stroke_width=2,
        stroke_fill=(
            0,
            0,
            0,
            WATERMARK_OPACITY,
        ),
    )

    # Slight diagonal rotation
    rotated = layer.rotate(
        WATERMARK_ANGLE,
        expand=True,
        resample=Image.Resampling.BICUBIC,
    )

    rotated.save(
        filename,
        "PNG",
    )

    print(
        "Text watermark created successfully "
        "(20% opacity, slightly tilted).",
        flush=True,
    )

    return filename


# =========================================================
# START
# =========================================================

async def start(event):
    await event.respond(conf.START)
    raise events.StopPropagation


# =========================================================
# HELP
# =========================================================

async def bot_help(event):
    try:
        await event.respond(conf.HELP)
    finally:
        raise events.StopPropagation


# =========================================================
# SET CONFIG
# =========================================================

async def set_config(event):

    notes = f"""
This command is used to set the value of a config variable.

Usage:
`/set key: value`

Example:
`/set position: centre`

{gen_kv_str()}
""".replace(
        "    ",
        "",
    )

    try:

        pos_arg = get_args(
            event.message.text
        )

        if not pos_arg:
            raise ValueError(notes)

        splitted = pos_arg.split(
            ":",
            1,
        )

        if len(splitted) != 2:
            raise ValueError(
                "Incorrect argument format"
            )

        key, value = [
            item.strip()
            for item in splitted
        ]

        config_dict = conf.config.dict()

        if key not in config_dict.keys():
            raise ValueError(
                f"The key {key} is not a valid "
                f"key in configuration."
            )

        config_dict[key] = value

        conf.config = conf.Config(
            **config_dict
        )

        print(
            f"Configuration updated: "
            f"{key} = {value}",
            flush=True,
        )

        await event.respond(
            f"The value of {key} was set to {value}"
        )

    except ValueError as err:

        print(
            f"Config error: {err}",
            flush=True,
        )

        await event.respond(
            str(err)
        )

    except Exception as err:

        print(
            f"Config error: "
            f"{type(err).__name__}: {err}",
            flush=True,
        )

    finally:
        raise events.StopPropagation


# =========================================================
# GET CONFIG
# =========================================================

async def get_config(event):

    notes = f"""
This command is used to get the value of a configuration variable.

Usage:
`/get key`

Example:
`/get position`

{gen_kv_str()}
""".replace(
        "    ",
        "",
    )

    try:

        key = get_args(
            event.message.text
        )

        if not key:
            raise ValueError(notes)

        config_dict = conf.config.dict()

        await event.respond(
            str(config_dict.get(key))
        )

    except ValueError as err:

        print(
            err,
            flush=True,
        )

        await event.respond(
            str(err)
        )

    finally:
        raise events.StopPropagation


# =========================================================
# WATERMARKER
# =========================================================

async def watermarker(event):

    # Only process incoming media.
    if not (
        event.photo
        or event.video
        or event.gif
    ):
        return

    print(
        "========================================",
        flush=True,
    )

    print(
        f"Watermark request received: "
        f"chat={event.chat_id}, "
        f"message={event.id}",
        flush=True,
    )

    org_file = None
    out_file = None
    watermark_file = None

    try:

        # ---------------------------------------------
        # Download original media
        # ---------------------------------------------

        downloaded_file = (
            await event.download_media("")
        )

        if not downloaded_file:

            print(
                "Could not download original media.",
                flush=True,
            )

            return

        org_file = stamp(
            downloaded_file,
            user=str(event.sender_id),
        )

        print(
            f"File stamped: {org_file}",
            flush=True,
        )

        # ---------------------------------------------
        # Create TEXT watermark
        # ---------------------------------------------

        watermark_file = create_text_watermark(
            filename="text_watermark.png"
        )

        # ---------------------------------------------
        # Apply watermark
        # ---------------------------------------------

        file = File(
            org_file
        )

        wtm = Watermark(
            File(watermark_file),
            pos=conf.config.position,
        )

        out_file = apply_watermark(
            file,
            wtm,
            frame_rate=conf.config.frame_rate,
            preset=conf.config.preset,
        )

        if not out_file:

            print(
                "Watermark processing failed.",
                flush=True,
            )

            return

        print(
            f"Watermark processing completed: "
            f"{out_file}",
            flush=True,
        )

        # ---------------------------------------------
        # Preserve original caption
        # ---------------------------------------------

        caption = (
            event.message.message
            or None
        )

        # ---------------------------------------------
        # Send to SAME CHANNEL
        # ---------------------------------------------

        sent_message = (
            await event.client.send_file(
                event.chat_id,
                out_file,
                caption=caption,
            )
        )

        print(
            f"Watermarked media sent: "
            f"chat={event.chat_id}, "
            f"message={sent_message.id}",
            flush=True,
        )

        # ---------------------------------------------
        # Delete ORIGINAL message
        # ---------------------------------------------

        try:

            await event.client.delete_messages(
                event.chat_id,
                event.id,
            )

            print(
                f"Original message deleted: "
                f"{event.id}",
                flush=True,
            )

        except Exception as delete_error:

            print(
                "ORIGINAL MESSAGE DELETE FAILED: "
                f"{type(delete_error).__name__}: "
                f"{delete_error}",
                flush=True,
            )

    except Exception as err:

        print(
            "========================================",
            flush=True,
        )

        print(
            f"WATERMARK ERROR: "
            f"{type(err).__name__}: {err}",
            flush=True,
        )

        print(
            "========================================",
            flush=True,
        )

    finally:

        # Never try to os.remove(None)
        cleanup(
            org_file,
            out_file,
            watermark_file,
        )


# =========================================================
# ALL EVENTS
# =========================================================

ALL_EVENTS = {

    "start": (
        start,
        events.NewMessage(
            pattern=r"^/start(?:@\w+)?$"
        ),
    ),

    "help": (
        bot_help,
        events.NewMessage(
            pattern=r"^/help(?:@\w+)?$"
        ),
    ),

    "set": (
        set_config,
        events.NewMessage(
            pattern=r"^/set(?:@\w+)?(?:\s|$)"
        ),
    ),

    "get": (
        get_config,
        events.NewMessage(
            pattern=r"^/get(?:@\w+)?(?:\s|$)"
        ),
    ),

    "watermarker": (
        watermarker,
        events.NewMessage(
            incoming=True,
            func=lambda event: (
                event.photo
                or event.video
                or event.gif
            ),
        ),
    ),
}
