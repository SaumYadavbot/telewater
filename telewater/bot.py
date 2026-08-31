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

# Visible watermark diagonal:
# approximately 75% of original image diagonal
WATERMARK_DIAGONAL_RATIO = 0.75

# Render watermark at 4K resolution before scaling
WATERMARK_RENDER_WIDTH = 3840

# Minimum Full-HD output for photos
MINIMUM_FULL_HD = 1920


# =========================================================
# CREATE HIGH-RESOLUTION TEXT WATERMARK
# =========================================================

def create_text_watermark(
    media_width,
    media_height,
    filename="text_watermark.png",
):
    """
    Creates a high-resolution watermark.

    Features:
    - 60% opacity
    - 30%+ larger text target
    - Complete title always visible
    - Visible watermark diagonal approximately 75%
      of the original image diagonal
    - Rendered at 4K before final scaling
    """

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    font_path = (
        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans-Bold.ttf"
    )

    # -----------------------------------------------------
    # HIGH-RESOLUTION WORKING CANVAS
    # -----------------------------------------------------

    canvas_width = WATERMARK_RENDER_WIDTH

    # Initial font target:
    #
    # Original = 0.065
    # 30% larger = 0.0845

    title_size = int(
        canvas_width * 0.0845
    )

    username_size = int(
        canvas_width * 0.0442
    )

    title_size = max(
        60,
        title_size,
    )

    username_size = max(
        40,
        username_size,
    )

    # -----------------------------------------------------
    # MEASUREMENT CANVAS
    # -----------------------------------------------------

    measure_image = Image.new(
        "RGBA",
        (1, 1),
        (0, 0, 0, 0),
    )

    measure_draw = ImageDraw.Draw(
        measure_image
    )

    # -----------------------------------------------------
    # MAKE SURE COMPLETE TITLE FITS
    # -----------------------------------------------------

    while True:

        test_font = ImageFont.truetype(
            font_path,
            title_size,
        )

        bbox = measure_draw.textbbox(
            (0, 0),
            WATERMARK_TEXT,
            font=test_font,
            stroke_width=6,
        )

        text_width = (
            bbox[2] - bbox[0]
        )

        if text_width <= canvas_width - 240:
            break

        title_size -= 1

        if title_size <= 60:
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
    # TEXT DIMENSIONS
    # -----------------------------------------------------

    title_bbox = measure_draw.textbbox(
        (0, 0),
        WATERMARK_TEXT,
        font=title_font,
        stroke_width=6,
    )

    title_width = (
        title_bbox[2] - title_bbox[0]
    )

    title_height = (
        title_bbox[3] - title_bbox[1]
    )

    username_bbox = measure_draw.textbbox(
        (0, 0),
        WATERMARK_USERNAME,
        font=username_font,
        stroke_width=4,
    )

    username_width = (
        username_bbox[2] - username_bbox[0]
    )

    username_height = (
        username_bbox[3] - username_bbox[1]
    )

    # -----------------------------------------------------
    # TIGHT CANVAS AROUND TEXT
    # -----------------------------------------------------
    #
    # Important:
    # We don't use a huge transparent canvas for the
    # final diagonal calculation.
    #
    # This means the ACTUAL visible watermark becomes
    # approximately 75% of the image diagonal.

    padding_x = 120
    padding_y = 100

    layer_width = (
        max(
            title_width,
            username_width,
        )
        + (padding_x * 2)
    )

    layer_height = (
        title_height
        + username_height
        + 80
        + (padding_y * 2)
    )

    layer = Image.new(
        "RGBA",
        (
            layer_width,
            layer_height,
        ),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(
        layer
    )

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title_x = (
        layer_width - title_width
    ) // 2

    title_y = padding_y

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
        stroke_width=6,
        stroke_fill=(
            0,
            0,
            0,
            WATERMARK_OPACITY,
        ),
    )

    # -----------------------------------------------------
    # USERNAME
    # -----------------------------------------------------

    username_x = (
        layer_width - username_width
    ) // 2

    username_y = (
        title_y
        + title_height
        + 30
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
        stroke_width=4,
        stroke_fill=(
            0,
            0,
            0,
            WATERMARK_OPACITY,
        ),
    )

    # -----------------------------------------------------
    # ROTATE AT HIGH RESOLUTION
    # -----------------------------------------------------

    rotated = layer.rotate(
        WATERMARK_ANGLE,
        expand=True,
        resample=Image.Resampling.BICUBIC,
    )

    # -----------------------------------------------------
    # REMOVE EXCESS TRANSPARENT BORDER
    # -----------------------------------------------------
    #
    # This makes diagonal calculation based on the actual
    # visible watermark rather than an oversized canvas.

    alpha = rotated.getchannel("A")

    bbox = alpha.getbbox()

    if bbox:

        rotated = rotated.crop(
            bbox
        )

    # -----------------------------------------------------
    # ORIGINAL IMAGE DIAGONAL
    # -----------------------------------------------------

    media_diagonal = math.hypot(
        media_width,
        media_height,
    )

    # -----------------------------------------------------
    # TARGET WATERMARK DIAGONAL
    # -----------------------------------------------------

    target_diagonal = (
        media_diagonal
        * WATERMARK_DIAGONAL_RATIO
    )

    # -----------------------------------------------------
    # CURRENT VISIBLE WATERMARK DIAGONAL
    # -----------------------------------------------------

    current_diagonal = math.hypot(
        rotated.width,
        rotated.height,
    )

    # -----------------------------------------------------
    # SCALE WATERMARK TO 75% DIAGONAL
    # -----------------------------------------------------

    if current_diagonal > 0:

        scale = (
            target_diagonal
            / current_diagonal
        )

        final_width = max(
            1,
            int(
                rotated.width
                * scale
            ),
        )

        final_height = max(
            1,
            int(
                rotated.height
                * scale
            ),
        )

        rotated = rotated.resize(
            (
                final_width,
                final_height,
            ),
            Image.Resampling.LANCZOS,
        )

    # -----------------------------------------------------
    # SAVE LOSSLESS WATERMARK
    # -----------------------------------------------------

    rotated.save(
        filename,
        "PNG",
        optimize=True,
    )

    print(
        "High-resolution watermark created: "
        "60% opacity | 30%+ larger text | "
        "75% diagonal",
        flush=True,
    )

    return filename


# =========================================================
# HIGH QUALITY PHOTO OUTPUT
# =========================================================

def prepare_high_quality_image(
    input_path,
    output_path,
    minimum_long_side=MINIMUM_FULL_HD,
):
    """
    Prepare final photo output.

    If the processed image is smaller than Full HD,
    it is enlarged to at least 1920px on its long side.

    JPEG is saved at maximum quality with 4:4:4
    chroma subsampling so text/watermark edges remain
    as clean as possible.
    """

    with Image.open(
        input_path
    ) as image:

        # -------------------------------------------------
        # Convert safely to RGB
        # -------------------------------------------------

        if image.mode == "RGBA":

            background = Image.new(
                "RGB",
                image.size,
                (255, 255, 255),
            )

            background.paste(
                image,
                mask=image.getchannel("A"),
            )

            image = background

        else:

            image = image.convert(
                "RGB"
            )

        # -------------------------------------------------
        # ORIGINAL PROCESSED SIZE
        # -------------------------------------------------

        width, height = image.size

        long_side = max(
            width,
            height,
        )

        # -------------------------------------------------
        # UPSCALE TO FULL HD IF NEEDED
        # -------------------------------------------------

        if long_side < minimum_long_side:

            scale = (
                minimum_long_side
                / long_side
            )

            new_width = max(
                1,
                int(
                    width * scale
                ),
            )

            new_height = max(
                1,
                int(
                    height * scale
                ),
            )

            image = image.resize(
                (
                    new_width,
                    new_height,
                ),
                Image.Resampling.LANCZOS,
            )

        # -------------------------------------------------
        # MAXIMUM JPEG QUALITY
        # -------------------------------------------------

        image.save(
            output_path,
            "JPEG",
            quality=100,
            subsampling=0,
            optimize=True,
        )

        print(
            f"Final image: "
            f"{image.width}x{image.height} | "
            f"JPEG quality 100 | "
            f"4:4:4 chroma",
            flush=True,
        )


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
    high_quality_file = None

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
        # CREATE 4K HIGH-RESOLUTION WATERMARK
        # -------------------------------------------------

        watermark_file = (
            create_text_watermark(
                media_width=media_width,
                media_height=media_height,
                filename="text_watermark.png",
            )
        )

        if not watermark_file:

            print(
                "Text watermark was not created.",
                flush=True,
            )

            return

        if not os.path.exists(
            watermark_file
        ):

            print(
                "Text watermark file does not exist.",
                flush=True,
            )

            return

        print(
            f"High-resolution watermark ready: "
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
        # HIGH QUALITY PHOTO PROCESSING
        # -------------------------------------------------
        #
        # Only photos are processed here.
        #
        # Videos/GIFs continue using the existing
        # apply_watermark output.

        if event.photo:

            try:

                high_quality_file = (
                    f"{out_file}.hq.jpg"
                )

                prepare_high_quality_image(
                    input_path=out_file,
                    output_path=high_quality_file,
                    minimum_long_side=1920,
                )

                if os.path.exists(
                    high_quality_file
                ):

                    # Remove old processed image.
                    try:

                        os.remove(
                            out_file
                        )

                    except OSError:
                        pass

                    out_file = (
                        high_quality_file
                    )

                    print(
                        "High-quality Full-HD photo "
                        "prepared successfully.",
                        flush=True,
                    )

            except Exception as quality_error:

                print(
                    "High-quality photo processing failed: "
                    f"{type(quality_error).__name__}: "
                    f"{quality_error}",
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
            high_quality_file,
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
