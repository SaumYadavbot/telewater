"""Telegram event handlers for Telewater."""

import os
import math

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

# Approximately 60% opacity
# 255 x 0.60 = 153
WATERMARK_OPACITY = 153

# Slightly tilted
WATERMARK_ANGLE = -15

# Watermark diagonal will be approximately 75%
# of the original media diagonal.
WATERMARK_DIAGONAL_RATIO = 0.75


# =========================================================
# CREATE TEXT WATERMARK
# =========================================================

def create_text_watermark(
    media_width,
    media_height,
    filename="text_watermark.png",
):
    """
    Create a large diagonal-based text watermark.

    The final rotated watermark occupies approximately
    75% of the original media diagonal.

    The complete text is always fitted inside the
    watermark layer so that no letters are clipped.
    """

    # -----------------------------------------------------
    # ORIGINAL MEDIA DIAGONAL
    # -----------------------------------------------------

    media_diagonal = math.sqrt(
        (media_width ** 2)
        + (media_height ** 2)
    )

    # Target watermark diagonal
    target_diagonal = (
        media_diagonal
        * WATERMARK_DIAGONAL_RATIO
    )

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    font_path = (
        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans-Bold.ttf"
    )

    # -----------------------------------------------------
    # INITIAL WATERMARK SIZE
    # -----------------------------------------------------
    #
    # Start with a large canvas.
    # The final size will be calculated from the
    # diagonal after rotation.
    #

    watermark_width = int(
        media_width * 0.90
    )

    watermark_width = max(
        watermark_width,
        600,
    )

    watermark_width = min(
        watermark_width,
        2400,
    )

    # -----------------------------------------------------
    # FONT SIZE
    # -----------------------------------------------------
    #
    # Original title ratio was 0.065.
    # New target is approximately 30% larger:
    #
    # 0.065 x 1.30 = 0.0845
    #

    title_size = max(
        32,
        int(watermark_width * 0.0845),
    )

    username_size = max(
        22,
        int(watermark_width * 0.0442),
    )

    # -----------------------------------------------------
    # TEMP DRAWING OBJECT FOR MEASUREMENT
    # -----------------------------------------------------

    measure_layer = Image.new(
        "RGBA",
        (1, 1),
        (255, 255, 255, 0),
    )

    measure_draw = ImageDraw.Draw(
        measure_layer
    )

    # -----------------------------------------------------
    # FIT COMPLETE TITLE
    # -----------------------------------------------------
    #
    # This makes sure the complete:
    #
    # ETERNAL CIVIL ACADEMY
    #
    # fits inside the watermark.
    #

    while True:

        test_font = ImageFont.truetype(
            font_path,
            title_size,
        )

        title_bbox = measure_draw.textbbox(
            (0, 0),
            WATERMARK_TEXT,
            font=test_font,
            stroke_width=2,
        )

        title_width = (
            title_bbox[2]
            - title_bbox[0]
        )

        if (
            title_width
            <= watermark_width - 80
        ):
            break

        title_size -= 1

        if title_size <= 32:
            break

    title_font = ImageFont.truetype(
        font_path,
        title_size,
    )

    username_font = ImageFont.truetype(
        font_path,
        username_size,
    )

    # -----------------------------------------------------
    # GET TITLE DIMENSIONS
    # -----------------------------------------------------

    title_bbox = measure_draw.textbbox(
        (0, 0),
        WATERMARK_TEXT,
        font=title_font,
        stroke_width=2,
    )

    title_width = (
        title_bbox[2]
        - title_bbox[0]
    )

    title_height = (
        title_bbox[3]
        - title_bbox[1]
    )

    # -----------------------------------------------------
    # USERNAME DIMENSIONS
    # -----------------------------------------------------

    username_bbox = measure_draw.textbbox(
        (0, 0),
        WATERMARK_USERNAME,
        font=username_font,
        stroke_width=1,
    )

    username_width = (
        username_bbox[2]
        - username_bbox[0]
    )

    username_height = (
        username_bbox[3]
        - username_bbox[1]
    )

    # -----------------------------------------------------
    # CANVAS HEIGHT
    # -----------------------------------------------------

    temp_height = int(
        title_height
        + username_height
        + 80
    )

    # -----------------------------------------------------
    # CREATE TRANSPARENT LAYER
    # -----------------------------------------------------

    layer = Image.new(
        "RGBA",
        (
            watermark_width,
            temp_height,
        ),
        (255, 255, 255, 0),
    )

    draw = ImageDraw.Draw(layer)

    # -----------------------------------------------------
    # CENTER TITLE
    # -----------------------------------------------------

    title_x = (
        watermark_width
        - title_width
    ) // 2

    title_y = 20

    draw.text(
        (
            title_x,
            title_y,
        ),
        WATERMARK_TEXT,
        font=title_font,
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

    # -----------------------------------------------------
    # CENTER USERNAME
    # -----------------------------------------------------

    username_x = (
        watermark_width
        - username_width
    ) // 2

    username_y = (
        title_y
        + title_height
        + 14
    )

    draw.text(
        (
            username_x,
            username_y,
        ),
        WATERMARK_USERNAME,
        font=username_font,
        fill=(
            255,
            255,
            255,
            WATERMARK_OPACITY,
        ),
        stroke_width=1,
        stroke_fill=(
            0,
            0,
            0,
            WATERMARK_OPACITY,
        ),
    )

    # -----------------------------------------------------
    # ROTATE
    # -----------------------------------------------------

    rotated = layer.rotate(
        WATERMARK_ANGLE,
        expand=True,
        resample=Image.Resampling.BICUBIC,
    )

    # -----------------------------------------------------
    # CURRENT WATERMARK DIAGONAL
    # -----------------------------------------------------

    current_diagonal = math.sqrt(
        (rotated.width ** 2)
        + (rotated.height ** 2)
    )

    # -----------------------------------------------------
    # SCALE TO EXACTLY APPROXIMATELY 75%
    # OF ORIGINAL MEDIA DIAGONAL
    # -----------------------------------------------------

    if current_diagonal > 0:

        scale = (
            target_diagonal
            / current_diagonal
        )

        new_width = max(
            1,
            int(rotated.width * scale),
        )

        new_height = max(
            1,
            int(rotated.height * scale),
        )

        rotated = rotated.resize(
            (
                new_width,
                new_height,
            ),
            Image.Resampling.LANCZOS,
        )

    # -----------------------------------------------------
    # FINAL SAFETY CHECK
    # -----------------------------------------------------
    #
    # The watermark itself is never allowed to exceed
    # the target diagonal.
    #

    final_diagonal = math.sqrt(
        (rotated.width ** 2)
        + (rotated.height ** 2)
    )

    if final_diagonal > target_diagonal:

        scale = (
            target_diagonal
            / final_diagonal
        )

        rotated = rotated.resize(
            (
                max(
                    1,
                    int(rotated.width * scale),
                ),
                max(
                    1,
                    int(rotated.height * scale),
                ),
            ),
            Image.Resampling.LANCZOS,
        )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    rotated.save(
        filename,
        "PNG",
    )

    print(
        "60% opacity watermark created. "
        "Watermark diagonal is approximately "
        "75% of original media diagonal.",
        flush=True,
    )

    return filename


# =========================================================
# START
# =========================================================

async def start(event):

    await event.respond(
        conf.START
    )

    raise events.StopPropagation


# =========================================================
# HELP
# =========================================================

async def bot_help(event):

    try:

        await event.respond(
            conf.HELP
        )

    finally:

        raise events.StopPropagation


# =========================================================
# SET CONFIG
# =========================================================

async def set_config(event):

    notes = f"""
This command is used to set the value of a config variable.

Usage:
/set key: value

Example:
/set position: centre

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

            raise ValueError(
                notes
            )

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

        config_dict = (
            conf.config.dict()
        )

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
/get key

Example:
/get position

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

            raise ValueError(
                notes
            )

        config_dict = (
            conf.config.dict()
        )

        await event.respond(
            str(
                config_dict.get(key)
            )
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

        # -------------------------------------------------
        # DOWNLOAD ORIGINAL MEDIA
        # -------------------------------------------------

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
            user=str(
                event.sender_id
            ),
        )

        print(
            f"File stamped: {org_file}",
            flush=True,
        )

        # -------------------------------------------------
        # GET ORIGINAL MEDIA DIMENSIONS
        # -------------------------------------------------

        media_width = 1280
        media_height = 720

        try:

            if event.photo:

                with Image.open(
                    org_file
                ) as original_image:

                    media_width, media_height = (
                        original_image.size
                    )

            else:

                media_width = 1280
                media_height = 720

        except Exception as dimension_error:

            print(
                "Could not determine media dimensions: "
                f"{type(dimension_error).__name__}: "
                f"{dimension_error}",
                flush=True,
            )

        print(
            f"Original media size: "
            f"{media_width}x{media_height}",
            flush=True,
        )

        # -------------------------------------------------
        # CREATE LARGE DIAGONAL WATERMARK
        # -------------------------------------------------

        watermark_file = (
            create_text_watermark(
                media_width=media_width,
                media_height=media_height,
                filename="text_watermark.png",
            )
        )

        if not watermark_file or not os.path.exists(
            watermark_file
        ):

            print(
                "Text watermark file was not created.",
                flush=True,
            )

            return

        print(
            f"Text watermark ready: "
            f"{watermark_file}",
            flush=True,
        )

        # -------------------------------------------------
        # APPLY WATERMARK
        # -------------------------------------------------

        file = File(
            org_file
        )

        wtm = Watermark(
            File(
                watermark_file
            ),
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

        # -------------------------------------------------
        # PRESERVE ORIGINAL CAPTION
        # -------------------------------------------------

        caption = (
            event.message.message
            or None
        )

        # -------------------------------------------------
        # SEND TO SAME CHANNEL
        # -------------------------------------------------

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

        # -------------------------------------------------
        # DELETE ORIGINAL MESSAGE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CLEAN UP
        # -------------------------------------------------

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
