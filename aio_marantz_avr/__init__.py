"""Top-level package for AsyncIO Marantz AVR."""

__author__ = """Rob van der Most"""
__email__ = "silvester747@gmail.com"
__version__ = "0.1.0"

from .avr import AvrTimeoutError, connect, DisconnectedError, MarantzAVR
from .enums import InputSource, Power, SurroundMode

__all__ = [
    "connect",
    "DisconnectedError",
    "MarantzAVR",
    "InputSource",
    "Power",
    "SurroundMode",
]
