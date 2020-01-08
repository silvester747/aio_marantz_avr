#!/usr/bin/env python

"""Tests for `aio_marantz_avr` package."""

import asyncio
import pytest
import telnetlib3

from typing import Awaitable, List, Mapping, Optional

from aio_marantz_avr import aio_marantz_avr


class TestShell:
    reader = None
    writer = None

    @property
    def connected(self):
        return self.reader is not None and self.writer is not None

    def shell(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def run_and_respond(self, aw: Awaitable,
                              response_mapping: Mapping[str, List[str]]) -> None:
        await asyncio.wait_for(asyncio.gather(aw, self.expect_and_respond(response_mapping)),
                               timeout=5)

    async def expect_and_respond(self, response_mapping: Mapping[str, List[str]]) -> None:
        while True:
            command = await self.reader.readline()

            if command in response_mapping:
                responses = response_mapping[command]
                del response_mapping[command]
                for response in responses:
                    self.writer.write(response)
                    await self.writer.drain()
                if not response_mapping:
                    return


@pytest.fixture
def test_shell():
    return TestShell()


@pytest.fixture
async def test_server(test_shell, unused_tcp_port):
    server = await telnetlib3.create_server(shell=test_shell.shell, port=unused_tcp_port,
                                            encoding="ascii")
    server_task = asyncio.create_task(server.wait_closed())
    yield server
    test_shell.writer.close()
    server.close()
    await server_task


@pytest.mark.asyncio
async def test_connect(test_server, test_shell, unused_tcp_port):
    avr = await aio_marantz_avr.connect("localhost", port=unused_tcp_port)
    assert avr is not None
    assert test_shell.connected


@pytest.fixture
async def avr(test_server, unused_tcp_port):
    return await aio_marantz_avr.connect("localhost", port=unused_tcp_port)


@pytest.mark.asyncio
async def test_mute_on(avr, test_shell):
    await test_shell.run_and_respond(
        avr.mute_volume(True),
        {"MUON\r": ["MUON\r"]}
    )
    assert avr.is_volume_muted is True


@pytest.mark.asyncio
async def test_mute_off(avr, test_shell):
    await test_shell.run_and_respond(
        avr.mute_volume(False),
        {"MUOFF\r": ["MUOFF\r"]}
    )
    assert avr.is_volume_muted is False


@pytest.mark.asyncio
async def test_turn_on(avr, test_shell):
    await test_shell.run_and_respond(
        avr.turn_on(),
        {"PWON\r": ["PWON\r"]}
    )
    assert avr.power == aio_marantz_avr.Power.On


@pytest.mark.asyncio
async def test_turn_off(avr, test_shell):
    await test_shell.run_and_respond(
        avr.turn_off(),
        {"PWOFF\r": ["PWOFF\r"]}
    )
    assert avr.power == aio_marantz_avr.Power.Off


@pytest.mark.asyncio
async def test_turn_off_to_standby(avr, test_shell):
    await test_shell.run_and_respond(
        avr.turn_off(),
        {"PWOFF\r": ["PWSTANDBY\r"]}
    )
    assert avr.power == aio_marantz_avr.Power.Standby


@pytest.mark.asyncio
async def test_select_source(avr, test_shell):
    await test_shell.run_and_respond(
        avr.select_source(aio_marantz_avr.InputSource.DVD),
        {"SIDVD\r": ["SIDVD\r"]}
    )
    assert avr.source == aio_marantz_avr.InputSource.DVD


@pytest.mark.asyncio
async def test_select_sound_mode(avr, test_shell):
    await test_shell.run_and_respond(
        avr.select_sound_mode(aio_marantz_avr.SurroundMode.Movie),
        {"MSMOVIE\r": ["MSMOVIE\r"]}
    )
    assert avr.sound_mode == aio_marantz_avr.SurroundMode.Movie


@pytest.mark.asyncio
async def test_refresh(avr, test_shell):
    await test_shell.run_and_respond(
        avr.refresh(),
        {"MU?\r": ["MUOFF\r"], "PW?\r": ["PWON\r"], "MV?\r": ["MV400\r", "MVMAX980\r"],
         "SI?\r": ["SISAT/CBL\r"], "MS?\r": ["MSDOLBY DIGITAL\r"],}
    )
    assert avr.power == aio_marantz_avr.Power.On
    assert avr.is_volume_muted is False
    assert avr.volume_level == 400
    assert avr.max_volume_level == 980
    assert avr.source == aio_marantz_avr.InputSource.CblSat
    assert avr.sound_mode == aio_marantz_avr.SurroundMode.DolbyDigital


def test_initial_state(avr):
    """Initial states are unknown, so None"""
    assert avr.power is None
    assert avr.is_volume_muted is None
    assert avr.volume_level is None
    assert avr.max_volume_level is None
    assert avr.source is None
    assert avr.sound_mode is None


@pytest.mark.asyncio
async def test_refresh_while_running_command(avr, test_shell):
    turn_on_task = asyncio.create_task(avr.turn_on())
    command = await test_shell.reader.readline()
    assert command == "PWON\r"

    await avr.refresh()

    test_shell.writer.write("PWON\r")
    await test_shell.writer.drain()
    await turn_on_task


@pytest.mark.asyncio
async def test_run_command_while_refreshing(avr, test_shell):
    refresh_task = asyncio.create_task(avr.refresh())
    command = await test_shell.reader.readline()
    assert command

    await avr.turn_on()
    command2 = await test_shell.reader.readline()
    assert command2 == "PWON\r"

    refresh_task.cancel()

