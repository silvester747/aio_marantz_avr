#!/usr/bin/env python

"""Tests for `avr` package."""

import asyncio
import pytest
import telnetlib3

from typing import Awaitable, List, Mapping

from aio_marantz_avr import (connect, DisconnectedError, InputSource, Power, SurroundMode,
                             AvrTimeoutError)


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


def create_task(coro):
    # asyncio.create_task does not exist yet in python 3.6, but ensure_future does the same
    return asyncio.ensure_future(coro)


@pytest.fixture
async def test_server(test_shell, unused_tcp_port):
    server = await telnetlib3.create_server(shell=test_shell.shell, port=unused_tcp_port,
                                            encoding="ascii")
    server_task = create_task(server.wait_closed())
    yield server
    test_shell.writer.close()
    server.close()
    await server_task


@pytest.mark.asyncio
async def test_connect(test_server, test_shell, unused_tcp_port):
    avr = await connect("localhost", port=unused_tcp_port)
    assert avr is not None
    assert test_shell.connected


@pytest.fixture
async def avr(test_server, unused_tcp_port):
    return await connect("localhost", port=unused_tcp_port)


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
    assert avr.power == Power.On


@pytest.mark.asyncio
async def test_turn_off(avr, test_shell):
    await test_shell.run_and_respond(
        avr.turn_off(),
        {"PWSTANDBY\r": ["PWSTANDBY\r"]}
    )
    assert avr.power == Power.Standby


@pytest.mark.asyncio
async def test_select_source(avr, test_shell):
    await test_shell.run_and_respond(
        avr.select_source(InputSource.DVD),
        {"SIDVD\r": ["SIDVD\r"]}
    )
    assert avr.source == InputSource.DVD


@pytest.mark.asyncio
async def test_select_sound_mode(avr, test_shell):
    await test_shell.run_and_respond(
        avr.select_sound_mode(SurroundMode.Movie),
        {"MSMOVIE\r": ["MSMOVIE\r"]}
    )
    assert avr.sound_mode == SurroundMode.Movie


@pytest.mark.asyncio
async def test_set_volume_level(avr, test_shell):
    await test_shell.run_and_respond(
        avr.set_volume_level(30),
        {"MV30\r": ["MV30\r"]}
    )
    assert avr.volume_level == 30.


@pytest.mark.asyncio
async def test_set_volume_level_single_digit(avr, test_shell):
    await test_shell.run_and_respond(
        avr.set_volume_level(3),
        {"MV03\r": ["MV03\r"]}
    )
    assert avr.volume_level == 3.


@pytest.mark.asyncio
async def test_volume_level_up(avr, test_shell):
    await test_shell.run_and_respond(
        avr.volume_level_up(),
        {"MVUP\r": ["MV30\r"]}
    )
    assert avr.volume_level == 30.


@pytest.mark.asyncio
async def test_volume_level_down(avr, test_shell):
    await test_shell.run_and_respond(
        avr.volume_level_down(),
        {"MVDOWN\r": ["MV30\r"]}
    )
    assert avr.volume_level == 30.


@pytest.mark.asyncio
async def test_volume_level_decimal(avr, test_shell):
    await test_shell.run_and_respond(
        avr.volume_level_down(),
        {"MVDOWN\r": ["MV305\r"]}
    )
    assert avr.volume_level == 30.5


@pytest.mark.asyncio
async def test_refresh(avr, test_shell):
    await test_shell.run_and_respond(
        avr.refresh(),
        {"MU?\r": ["MUOFF\r"], "PW?\r": ["PWON\r"], "MV?\r": ["MV400\r", "MVMAX980\r"],
         "SI?\r": ["SISAT/CBL\r"], "MS?\r": ["MSDOLBY DIGITAL\r"], }
    )
    assert avr.power == Power.On
    assert avr.is_volume_muted is False
    assert avr.volume_level == 40.
    assert avr.max_volume_level == 98.
    assert avr.source == InputSource.CblSat
    assert avr.sound_mode == SurroundMode.DolbyDigital


@pytest.mark.asyncio
async def test_timeout_during_refresh(avr, test_shell):
    task = create_task(test_shell.expect_and_respond({"MU?\r": ["MUOFF\r"], }))

    with pytest.raises(AvrTimeoutError):
        await avr.refresh()

    task.cancel()


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
    turn_on_task = create_task(avr.turn_on())
    command = await test_shell.reader.readline()
    assert command == "PWON\r"

    await avr.refresh()

    test_shell.writer.write("PWON\r")
    await test_shell.writer.drain()
    await turn_on_task


@pytest.mark.asyncio
async def test_run_command_while_refreshing(avr, test_shell):
    refresh_task = create_task(avr.refresh())
    command = await test_shell.reader.readline()
    assert command

    await avr.turn_on()
    command2 = await test_shell.reader.readline()
    assert command2 == "PWON\r"

    refresh_task.cancel()


@pytest.mark.asyncio
async def test_refresh_after_disconnect(avr, test_shell, test_server):
    test_shell.writer.close()
    test_server.close()

    with pytest.raises(DisconnectedError):
        await avr.refresh()


@pytest.mark.asyncio
async def test_send_command_after_disconnect(avr, test_shell, test_server):
    test_shell.writer.close()
    test_server.close()

    with pytest.raises(DisconnectedError):
        await avr.turn_on()


@pytest.mark.asyncio
async def test_timeout_in_command(avr):
    with pytest.raises(AvrTimeoutError):
        await avr.turn_on()
