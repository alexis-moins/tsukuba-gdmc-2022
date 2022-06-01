import asyncio
from asyncio import Task, Semaphore

import aiohttp

from aiohttp import ClientSession, ClientConnectionError
from collections import deque
from dataclasses import dataclass
from typing import Coroutine, Deque, Iterable

from src.blocks.block import Block
from src.utils.coordinates import Coordinates


#
__URL = 'http://localhost:9000/blocks?x=0&y=0&z=0&customFlags=0110010&doBlockUpdate=False'


# List of http PUT request body
__requests: list[str] = []

# The size of the buffer. Once the buffer has reached this number of blocks, the
# blocks inside of the buffer will be scheduled to be sent to the minecraft server
buffer_size: int = 10_000

# The maximum number of requests that are sent to the minecraft server at the same
# time. Changing this number as well as the buffer_size might either improve or worsen
# the time the simulation takes to complete
concurrent_request_number: int = 4


@dataclass
class Buffer:
    """Represents a buffer of blocks, shared between processes, that shall at
    some point be sent to the minecraft server"""
    _buffer: Deque = deque()

    def add(self, block: Block) -> None:
        """Add the given [block] to the buffer"""
        self._buffer.append(block)
        schedule_buffer_sending()

    def extend(self, blocks: Iterable[Block]) -> None:
        """Add all the blocks in the given iterable to the buffer"""
        for block in blocks:
            self.add(block)

    def exhaust(self) -> Deque[Block]:
        """Return the blocks in the buffer then empty the buffer"""
        buffer = self._buffer.copy()
        self._buffer.clear()
        return buffer

    def __len__(self) -> int:
        """Return the number of blocks in the buffer"""
        return len(self._buffer)


# The block buffer. Contains all the blocks that will be sent to the minecraft server
# and placed in the world by schedule_buffer_sending once its size exceeds the buffer_size
__buffer = Buffer()


def schedule_buffer_sending(*, force: bool = False) -> None:
    """Send the whole buffer to the minecraft server. If [force] is set to true, send
    the buffer even if it has not reached the [buffer_size] limit yet"""
    if not force and len(__buffer) < buffer_size:
        return None

    print(f'SCHEDULING SENDING of {len(__buffer)} blocks')
    blocks = __buffer.exhaust()

    request_body = get_request_body(blocks)
    __requests.append(request_body)


def add_block_to_buffer(block: Block | Iterable[Block]) -> None:
    """Add the given [block] to the block buffer. Block may be either be a Block or
    any iterable of blocks"""
    __buffer.add(block) if type(block) is Block else __buffer.extend(block)


def add_string_to_buffer(block_name: str, coordinates: Coordinates) -> None:
    """Add the given [block_name] to the block buffer, specifying the [coordinates] on
    which the block should be placed"""
    block = Block(block_name, coordinates)
    __buffer.add(block)


async def __send_request(session, i, request_body: str, semaphore: Semaphore):
    """"""
    async with semaphore:
        try:
            print(semaphore._value)
            print(f'Starting request {i}')
            await session.put(__URL, data=request_body)
            print(f'Ending request {i}')
        except ClientConnectionError:

            await __send_request(session, i, request_body, semaphore)


def get_corountines(session: ClientSession) -> list[Coroutine]:
    """Return the list of coroutines that shall be gathered to send the different http
    PUT requests to the minecraft server concurrently by providing an asynchronous
    http [session]"""
    semaphore = Semaphore(value=concurrent_request_number)

    return [__send_request(session, i, request_body, semaphore)
            for i, request_body in enumerate(__requests)]


async def send_buffers(*, empty_buffer: bool = True) -> None:
    """Send all the scheduled buffer sending to the minecraft server. If [force] is set
    to true, schedule the current buffer even if it has not reached the [buffer_size]
    limit yet"""
    if empty_buffer:
        schedule_buffer_sending(force=True)

    if not __requests:
        # No tasks to create
        return None

    async with aiohttp.ClientSession() as session:
        coroutines = get_corountines(session)
        await asyncio.gather(*coroutines)


def format_block(block: Block) -> str:
    """Return a formatted string of the given [block] name and coordinates, ready to
    be sent to the minecraft server via the http PUT protocol"""
    return '{} {} {} {}'.format(*block.coordinates, block.full_name)


def get_request_body(blocks: Iterable[Block]) -> str:
    """Return a formatted multiline string of the given [blocks] name and coordinates,
    ready to be sent to the minecraft server via the http PUT protocol. This is similar
    to calling format_block on all the blocks of the given iterable"""
    formatted_blocks = [format_block(block) for block in blocks]
    return '\n'.join(formatted_blocks)


# async def __send_request(body: str) -> int:
#     """"""

#     async with aiohttp.ClientSession() as session:
#         response = await session.put(url, data=body)

#     return response.status


async def place_block(block: Block | tuple[str, Coordinates]) -> None:
    """Place the given [block] on the minecraft server. Block may be either a Block
    object or a tuple of the block name and its coordinates. Note that this method
    does not take adventage of the asynchronous buffer"""
    coordinates = block.coordinates if isinstance(block, Block) else block[1]
    name = block.full_name if isinstance(block, Block) else block[0]

    body = '{} {} {} {}'.format(coordinates, name)

    async with aiohttp.ClientSession() as session:
        await session.put(__URL, data=body)


# async def send_blocks(blocks: Iterable[Block], *, retries: int = 5, update_neighbours: bool = True, flags: str = None):
#     """"""
#     body = str.join("\n", [format_block(block) for block in blocks])

#     try:
#         response = __send_request(body)
#         return response
#     except ConnectionError as e:
#         print("Request failed: {} Retrying ({} left)".format(e, retries))
#         if retries > 0:
#             # return sendBlocks(x, y, z, retries - 1)
#             pass
#     return False
