""" This module defines the functions that handle different events.
"""

from telethon import events
from watermark import File, Watermark, apply_watermark

from telewater import conf
from telewater.utils import cleanup, download_image, gen_kv_str, get_args, stamp


async def start(event):
    await event.respond(conf.START)
    raise events.StopPropagation


async def bot_help(event):
    try:
        await event.respond(conf.HELP)
    finally:
        raise events.StopPropagation


async def set_config(event):

    notes = f"""This command is used to set the value of a config variable.
    Usage `/set key: val`
    Example `/set watermark: https://link/to/watermark.png`
    {gen_kv_str()}
    """.replace(
        "    ", ""
    )

    try:
        pos_arg = get_args(event.message.text)
        if not pos_arg:
            raise ValueError(f"{notes}")
        splitted = pos_arg.split(":", 1)

        if not len(splitted) == 2:
            raise ValueError("Incorrect argument format")

        key, value = [item.strip() for item in splitted]

        config_dict = conf.config.dict()
        if not key in config_dict.keys():
            raise ValueError(f"The key {key} is not a valid key in configuration.")

        config_dict[key] = value
        print(config_dict)

        conf.config = conf.Config(**config_dict)

        print(conf.config)
        if key == "watermark":
            cleanup("image.png")
            download_image(url=value)
        await event.respond(f"The value of {key} was set to {value}")

    except ValueError as err:
        print(err)
        await event.respond(str(err))
    except Exception as err:
        print(err)

    finally:
        raise events.StopPropagation


async def get_config(event):

    notes = f"""This command is used to get the value of a configuration variable.
    Usage `/get key`
    Example `/get x_off`
    {gen_kv_str()}
    """.replace(
        "    ", ""
    )

    try:
        key = get_args(event.message.text)
        if not key:
            raise ValueError(f"{notes}")
        config_dict = conf.config.dict()
        await event.respond(f"{config_dict.get(key)}")
    except ValueError as err:
        print(err)
        await event.respond(str(err))

"""This module defines the functions that handle different events."""

from telethon import events
from watermark import File, Watermark, apply_watermark

from telewater import conf
from telewater.utils import (
    cleanup,
    download_image,
    gen_kv_str,
    get_args,
    stamp,
)


async def start(event):
    await event.respond(conf.START)
    raise events.StopPropagation


async def bot_help(event):
    try:
        await event.respond(conf.HELP)
    finally:
        raise events.StopPropagation


async def set_config(event):

    notes = f"""This command is used to set the value of a config variable.
    Usage `/set key: val`
    Example `/set watermark: https://link/to/watermark.png`
    {gen_kv_str()}
    """.replace(
        "    ", ""
    )

    try:
        pos_arg = get_args(event.message.text)

        if not pos_arg:
            raise ValueError(notes)

        splitted = pos_arg.split(":", 1)

        if not len(splitted) == 2:
            raise ValueError("Incorrect argument format")

        key, value = [
            item.strip()
            for item in splitted
        ]

        config_dict = conf.config.dict()

        if key not in config_dict.keys():
            raise ValueError(
                f"The key {key} is not a valid key in configuration."
            )

        config_dict[key] = value

        print(config_dict)

        conf.config = conf.Config(**config_dict)

        print(conf.config)

        if key == "watermark":
            cleanup(
                "image.png",
                "watermark_15.png",
            )

            download_image(url=value)

        await event.respond(
            f"The value of {key} was set to {value}"
        )

    except ValueError as err:
        print(err)
        await event.respond(str(err))

    except Exception as err:
        print(err)

    finally:
        raise events.StopPropagation


async def get_config(event):

    notes = f"""This command is used to get the value of a configuration variable.
    Usage `/get key`
    Example `/get x_off`
    {gen_kv_str()}
    """.replace(
        "    ", ""
    )

    try:
        key = get_args(event.message.text)

        if not key:
            raise ValueError(notes)

        config_dict = conf.config.dict()

        await event.respond(
            f"{config_dict.get(key)}"
        )

    except ValueError as err:
        print(err)
        await event.respond(str(err))

    finally:
        raise events.StopPropagation


async def watermarker(event):

    # Only process incoming media messages.
    # This prevents the bot from processing its own output.
    if not (
        event.photo
        or event.video
        or event.gif
    ):
        return

    print(
        f"Watermark request received: "
        f"chat={event.chat_id}, message={event.id}",
        flush=True,
    )

    org_file = None
    out_file = None

    try:

        # Download original media.
        downloaded_file = await event.download_media("")

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

        # Make sure the 15% opacity watermark exists.
        if not download_image(
            url=conf.config.watermark,
            filename="image.png",
        ):
            print(
                "Could not prepare watermark image.",
                flush=True,
            )
            return

        watermark_file = (
            "watermark_15.png"
        )

        if not __import__("os").path.exists(
            watermark_file
        ):
            print(
                "15% opacity watermark file is missing.",
                flush=True,
            )
            return

        # Apply 15% opacity watermark.
        file = File(org_file)

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

        # Preserve original caption/text.
        caption = event.message.message or None

        # Send the processed image/video back to
        # THE SAME CHANNEL where the original appeared.
        sent_message = await event.client.send_file(
            event.chat_id,
            out_file,
            caption=caption,
        )

        print(
            f"Watermarked media sent: "
            f"chat={event.chat_id}, "
            f"message={sent_message.id}",
            flush=True,
        )

        # Delete the original ONLY after the new
        # watermarked media has been sent successfully.
        try:

            await event.client.delete_messages(
                event.chat_id,
                event.id,
            )

            print(
                f"Original message deleted: {event.id}",
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
            f"WATERMARK ERROR: "
            f"{type(err).__name__}: {err}",
            flush=True,
        )

    finally:

        cleanup(
            org_file,
            out_file,
        )


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
