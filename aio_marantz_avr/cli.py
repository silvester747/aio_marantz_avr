"""Console script for aio_marantz_avr."""
import argparse
import asyncio
import sys

from .avr import connect, DisconnectedError
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
        print(f"NEW Power: {avr.power}")

    if args.turn_off:
        await avr.turn_off()
        print(f"NEW Power: {avr.power}")

    if args.mute_volume_on:
        await avr.mute_volume(True)
        print(f"NEW Is volume muted: {avr.is_volume_muted}")

    if args.mute_volume_off:
        await avr.mute_volume(False)
        print(f"NEW Is volume muted: {avr.is_volume_muted}")

    if args.select_source:
        await avr.select_source(InputSource[args.select_source])
        print(f"NEW Source: {avr.source}")

    if args.select_sound_mode:
        await avr.select_sound_mode(SurroundMode[args.select_sound_mode])
        print(f"NEW Sound mode: {avr.sound_mode}")

    if args.set_volume_level:
        await avr.set_volume_level(args.set_volume_level)
        print(f"NEW Volume level: {avr.volume_level}")

    if args.volume_level_up:
        await avr.volume_level_up()
        print(f"NEW Volume level: {avr.volume_level}")

    if args.volume_level_down:
        await avr.volume_level_down()
        print(f"NEW Volume level: {avr.volume_level}")


def main():
    """Console script for aio_marantz_avr."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, help="Host name or IP of the AVR.")
    parser.add_argument("--show", action="store_true", help="Show all properties.")
    parser.add_argument("--turn-on", action="store_true", help="Turn the AVR on.")
    parser.add_argument("--turn-off", action="store_true", help="Turn the AVR off.")
    parser.add_argument("--mute-volume-on", action="store_true", help="Turn volume mute on.")
    parser.add_argument("--mute-volume-off", action="store_true", help="Turn volume mute off.")
    parser.add_argument(
        "--select-source", choices=InputSource.__members__.keys(), help="Select input source.",
    )
    parser.add_argument(
        "--select-sound-mode", choices=SurroundMode.__members__.keys(), help="Select sound mode.",
    )
    parser.add_argument("--set-volume-level", type=int, help="Set the volume level.")
    parser.add_argument("--volume-level-up", action="store_true", help="Turn the volume level up.")
    parser.add_argument(
        "--volume-level-down", action="store_true", help="Turn the volume level down."
    )
    args = parser.parse_args()

    try:
        asyncio.run(run(args))
    except DisconnectedError:
        print("Connection lost.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
