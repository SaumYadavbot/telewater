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

# Approximately 40% opacity
WATERMARK_OPACITY = 102

# Slightly tilted
WATERMARK_ANGLE = -15


# =========================================================
# CREATE TEXT WATERMARK
# =========================================================

def create_text_watermark(
    media_width,
    media_height,
    filename="text_watermark.png",
):
    """
    Create a responsive text watermark.

    Text is targeted to be at least 30% larger than
    the original version, while automatically fitting
    the complete text so no letters are clipped.
    """

    # -----------------------------------------------------
    # Watermark width
    # -----------------------------------------------------

    watermark_width = int(media_width * 0.65)

    # Safety limits
    watermark_width = max(500, watermark_width)
    watermark_width = min(1800, watermark_width)

    # -----------------------------------------------------
    # Font sizes
    # At least 30% larger than original
    #
    # Original title    = 0.065
    # Original username = 0.034
    #
    # New target:
    # title    = 0.0845
    # username = 0.0442
    # -----------------------------------------------------

    title_size = max(
        32,
        int(watermark_width * 0.0845),
    )

    username_size = max(
        22,
        int(watermark_width * 0.0442),
    )

    # -----------------------------------------------------
    # Font
    # -----------------------------------------------------

    font_path = (
        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans-Bold.ttf"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Automatically reduce ONLY if the complete title
    # does not fit. This prevents:
    #
    # ETERNAL CIVIL ACADEMY
    #
    # from being clipped on either side.
    # -----------------------------------------------------

    while True:

        test_font = ImageFont.truetype(
            font_path,
            title_size,
        )

        test_layer = Image.new(
            "RGBA",
            (1, 1),
            (255, 255, 255, 0),
        )

        test_draw = ImageDraw.Draw(
            test_layer
        )

        test_bbox = test_draw.textbbox(
            (0, 0),
            WATERMARK_TEXT,
            font=test_font,
            stroke_width=2,
        )

        test_width = (
            test_bbox[2]
            - test_bbox[0]
        )

        # 40px safety margin
        if (
            test_width <= watermark_width - 40
            or title_size <= 32
        ):
            break

        title_size -= 1

    title_font = ImageFont.truetype(
        font_path,
        title_size,
    )

    username_font = ImageFont.truetype(
        font_path,
        username_size,
    )

    # -----------------------------------------------------
    # Create transparent drawing layer
    # -----------------------------------------------------

    temp_height = int(
        title_size * 2.8
        + username_size * 1.8
        + 80
    )

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
    # Main text dimensions
    # -----------------------------------------------------

    title_bbox = draw.textbbox(
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

    title_x = (
        watermark_width
        - title_width
    ) // 2

    title_y = 20

    # -----------------------------------------------------
    # Main watermark text
    # -----------------------------------------------------

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
    # Username
    # -----------------------------------------------------

    username_bbox = draw.textbbox(
        (0, 0),
        WATERMARK_USERNAME,
        font=username_font,
        stroke_width=1,
    )

    username_width = (
        username_bbox[2]
        - username_bbox[0]
    )

    username_x = (
        watermark_width
        - username_width
    ) // 2

    username_y = (
        title_y
        + title_height
        + 12
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
    # Rotate slightly
    # -----------------------------------------------------

    rotated = layer.rotate(
        WATERMARK_ANGLE,
        expand=True,
        resample=Image.Resampling.BICUBIC,
    )

    # -----------------------------------------------------
    # Keep watermark within reasonable size
    # -----------------------------------------------------

    max_width = int(
        media_width * 0.78
    )

    max_height = int(
        media_height * 0.35
    )

    scale = min(
        1.0,
        max_width / rotated.width,
        max_height / rotated.height,
    )

    if scale < 1.0:

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
    # Save watermark
    # -----------------------------------------------------

    rotated.save(
        filename,
        "PNG",
    )

    print(
        "40% opacity, 30%+ larger responsive "
        "text watermark created successfully.",
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
        # Download original media
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
        # Get original media dimensions
        # -------------------------------------------------

        media_width = 1280
        media_height = 720

        try:

            # For photos, use the real dimensions.
            if event.photo:

                with Image.open(
                    org_file
                ) as original_image:

                    media_width, media_height = (
                        original_image.size
                    )

            else:

                # Safe default for videos/GIFs.
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
        # Create responsive text watermark
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
        # Apply watermark
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
        # Preserve original caption
        # -------------------------------------------------

        caption = (
            event.message.message
            or None
        )

        # -------------------------------------------------
        # Send to SAME CHANNEL
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
        # Delete ORIGINAL message
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
        # Clean up only valid file paths.
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
