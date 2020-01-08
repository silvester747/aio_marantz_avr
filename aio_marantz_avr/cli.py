"""Console script for aio_marantz_avr."""
import argparse
import asyncio
import sys

from .avr import connect
from .enums import InputSource, SurroundMode


async def run(args):
    avr = await connect(host=args.host)

    if args.show:
        await avr.refresh()
        print(f"Power: {avr.power}")
        print(f"Is volume muted: {avr.is_volume_muted}")
        print(f"Volume level: {avr.volume_level}")
        print(f"Max volume level: {avr.max_volume_level}")
        print(f"Source: {avr.source}")
        print(f"Sound mode: {avr.sound_mode}")

    if args.turn_on:
        await avr.turn_on()

    if args.turn_off:
        await avr.turn_off()

    if args.mute_volume_on:
        await avr.mute_volume(True)

    if args.mute_volume_off:
        await avr.mute_volume(False)

    if args.select_source:
        await avr.select_source(InputSource[args.select_source])

    if args.select_sound_mode:
        await avr.select_sound_mode(SurroundMode[args.select_sound_mode])


def main():
    """Console script for aio_marantz_avr."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, help="Host name or IP of the AVR.")
    parser.add_argument("--show", action="store_true", help="Show all properties.")
    parser.add_argument("--turn-on", action="store_true", help="Turn the AVR on.")
    parser.add_argument("--turn-off", action="store_true", help="Turn the AVR off.")
    parser.add_argument("--mute-volume-on", action="store_true", help="Turn volume mute on.")
    parser.add_argument("--mute-volume-off", action="store_true", help="Turn volume mute off.")
    parser.add_argument("--select-source", choices=InputSource.__members__.keys(),
                        help="Select input source.")
    parser.add_argument("--select-sound-mode", choices=SurroundMode.__members__.keys(),
                        help="Select sound mode.")
    args = parser.parse_args()

    asyncio.run(run(args))

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
