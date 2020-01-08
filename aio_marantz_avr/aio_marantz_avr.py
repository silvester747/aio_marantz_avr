"""Main module."""

import telnetlib3

from enum import Enum
from typing import Any, List, Mapping, Optional, Tuple, Type


async def connect(host: str, port: int = 23):
    reader, writer = await telnetlib3.open_connection(host, port=port, encoding="ascii")
    return MarantzAVR(reader, writer)


def _on_off_from_bool(value: bool) -> str:
    if value:
        return "ON"
    else:
        return "OFF"


def _on_off_to_bool(value: str) -> bool:
    return value == "ON"


class Power(Enum):
    Off = "OFF"
    On = "ON"
    Standby = "STANDBY"


class InputSource(Enum):
    Phono = "PHONO"
    CD = "CD"
    DVD = "DVD"
    Bluray = "BD"
    TV = "TV"
    CblSat = "SAT/CBL"
    MediaPlayer = "MPLAY"
    Game = "GAME"
    Tuner = "TUNER"
    HDRadio = "HDRADIO"
    SiriusXM = "SIRIUSXM"
    Pandora = "PANDORA"
    InternetRadio = "IRADIO"
    Server = "SERVER"
    Favorites = "FAVORITES"
    Aux1 = "AUX1"
    Aux2 = "AUX2"
    Aux3 = "AUX3"
    Aux4 = "AUX4"
    Aux5 = "AUX5"
    Aux6 = "AUX6"
    Aux7 = "AUX7"
    OnlineMusic = "NET"
    Bluetooth = "BT"


class SurroundMode(Enum):
    # Settable values
    Movie = "MOVIE"
    Music = "MUSIC"
    Game = "GAME"
    Direct = "DIRECT"
    PureDirect = "PURE DIRECT"
    Stereo = "STEREO"
    Auto = "AUTO"
    DolbyDigital = "DOLBY DIGITAL"
    DtsSurround = "DTS SURROUND"
    Auro3D = "AURO3D"
    Auro2DSurround = "AURO2DSURR"
    MultiChannelStereo = "MCH STEREO"
    Virtual = "VIRTUAL"

    # Rotate between options
    Left = "LEFT"
    Right = "RIGHT"

    # Return only
    # TODO: Split combined modes
    DolbySurround = "DOLBY SURROUND"
    DolbyAtmos = "DOLBY ATMOS"
    DolbyDigitalDS = "DOLBY D+DS"
    DolbyDigitalNeuralX = "DOLBY D+NEURAL:X"
    DolbyDigitalPlus = "DOLBY D+"
    DolbyDigitalPlusDS = "DOLBY D+ +DS"
    DolbyDigitalPlusNeuralX = "DOLBY D+ +NEURAL:X"
    DolbyHD = "DOLBY HD"
    DolbyHDDS = "DOLBY HD+DS"
    DolbyHDNeuralX = "DOLBY HD+NEURAL:X"
    NeuralX = "NEURAL:X"
    DtsEsDscrt6_1 = "DTS ES DSCRT6.1"
    DtsEsMtrx6_1 = "DTS ES MTRX6.1"
    DtsDS = "DTS+DS"
    DtsNeuralX = "DTS+NEURAL:X"
    DtsEsMtrxNeuralX = "DTS ES MTRX+NEURAL:X"
    DtsEsDscrtNeuralX = "DTS ES DSCRT+NEURAL:X"
    Dts96_24 = "DTS96/24"
    Dts96EsMtrx = "DTS96 ES MTRX"
    DtsHD = "DTS HD"
    DtsHDMstr = "DTS HD MSTR"
    DtsHDDS = "MSDTS HD+DS"
    DtsHDNeuralX = "DTS HD+NEURAL:X"
    DtsX = "DTS:X"
    DtsXMstr = "DTS:X MSTR"
    DtsExpress = "DTS EXPRESS"
    DtsES8ChDscrt = "DTS ES 8CH DSCRT"
    MultiChIn = "MULTI CH IN"
    MultiChInDS = "M CH IN+DS"
    MultiChInNeuralX = "M CH IN+NEURAL:X"
    MultiChIn7_1 = "MULTI CH IN 7.1"


class DataDefinition:
    query: str
    data_names: List[str]

    def __init__(self, query: str, data_names: List[str]):
        self.query = query
        self.data_names = data_names

class MarantzAVR:
    DATA_DEFS: List[DataDefinition] = [
        DataDefinition("PW?", ["PW"]),
        DataDefinition("MU?", ["MU"]),
        DataDefinition("MV?", ["MV", "MVMAX"]),
        DataDefinition("SI?", ["SI"]),
        DataDefinition("MS?", ["MS"]),
    ]

    _reader: telnetlib3.TelnetReader
    _writer: telnetlib3.TelnetWriter

    _data: Mapping[str, Optional[str]]
    _reading: bool

    def __init__(self, reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
        self._reader = reader
        self._writer = writer
        self._prepare_data()
        self._reading = False

    def _prepare_data(self):
        self._data = {}
        for data_def in self. DATA_DEFS:
            for name in data_def.data_names:
                self._data[name] = None

    @property
    def power(self) -> Optional[Power]:
        """Power state of the AVR."""
        return self._get_enum_data("PW", Power)

    @property
    def is_volume_muted(self) -> Optional[bool]:
        """Boolean if volume is currently muted."""
        return self._get_boolean_data("MU")

    @property
    def volume_level(self) -> Optional[int]:
        """Volume level of the AVR zone (00..max_volume_level)."""
        return self._get_int_data("MV")

    @property
    def max_volume_level(self) -> Optional[int]:
        """Maximum volume level of the AVR zone."""
        return self._get_int_data("MVMAX")

    @property
    def source(self) -> Optional[InputSource]:
        """Name of the current input source."""
        return self._get_enum_data("SI", InputSource)

    @property
    def source_list(self) -> List[InputSource]:
        """List of available input sources."""
        return list(InputSource)

    @property
    def sound_mode(self) -> Optional[SurroundMode]:
        """Name of the current sound mode."""
        return self._get_enum_data("MS", SurroundMode)

    @property
    def sound_mode_list(self) -> List[SurroundMode]:
        """List of available sound modes."""
        return list(SurroundMode)

    async def refresh(self) -> None:
        if self._reading:
            return

        for data_def in self.DATA_DEFS:
            await self._send_command(data_def.query)
            await self._wait_for_response(*data_def.data_names)

    async def turn_on(self) -> None:
        await self._send_command("PW", "ON")
        await self._wait_for_response("PW")

    async def turn_off(self) -> None:
        await self._send_command("PW", "OFF")
        await self._wait_for_response("PW")

    async def mute_volume(self, mute: bool) -> None:
        await self._send_command("MU", _on_off_from_bool(mute))
        await self._wait_for_response("MU")

    async def select_source(self, source: InputSource) -> None:
        await self._send_command("SI", source.value)
        await self._wait_for_response("SI")

    async def select_sound_mode(self, mode: SurroundMode) -> None:
        await self._send_command("MS", mode.value)
        await self._wait_for_response("MS")

    async def _send_command(self, *parts: Tuple[str]) -> None:
        self._writer.write("".join(parts))
        self._writer.write("\r")
        await self._writer.drain()

    async def _wait_for_response(self, *names: Tuple[str]) -> None:
        if self._reading:
            return

        self._reading = True
        try:
            names = list(names)
            while True:
                line = await self._reader.readline()
                match = self._process_response(line)
                if match in names:
                    names.remove(match)
                    if len(names) == 0:
                        return
        finally:
            self._reading = False

    def _process_response(self, response: str) -> Optional[str]:
        matches = [name for name in self._data.keys() if response.startswith(name)]

        if not matches:
            return None

        if len(matches) > 1:
            matches.sort(key=len, reverse=True)
        match = matches[0]

        self._data[match] = response.strip()[len(match):]
        return match

    def _get_boolean_data(self, name: str) -> Optional[bool]:
        value = self._data[name]
        if value is not None:
            return _on_off_to_bool(self._data[name])
        return None

    def _get_int_data(self, name: str) -> Optional[int]:
        value = self._data[name]
        if value is not None:
            return int(value)
        return None

    def _get_enum_data(self, name: str, enum_type: Type) -> Optional[Any]:
        value = self._data[name]
        if value is not None:
            return enum_type(value)
        return None
