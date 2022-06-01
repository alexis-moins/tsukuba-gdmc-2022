import asyncio
from asyncio import Task, tasks
import requests
import aiohttp
from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable

from src.blocks.block import Block
from src.utils.coordinates import Coordinates


URL = f'http://localhost:9000/blocks?x=0&y=0&z=0&customFlags=0100011&doBlockUpdate=True'

# List of
_requests: list[str] = []


# The size of the buffer. Once the buffer has reached this number of blocks, the
# __buffer_handler will send all the blocks to the minecraft server at once.
buffer_size: int = 10_000


@dataclass
class Buffer:
    """Represents a buffer of blocks, shared between processes, that shall at
    some point be sent to the minecraft server"""
    _buffer: Deque = deque()

    def add(self, block: Block) -> None:
        """Add the given [block] to the buffer"""
        self._buffer.append(block)

        if len(self) >= buffer_size:
            schedule_buffer_sending(force=True)

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


def schedule_buffer_sending(*, force: bool = False) -> None:
    """Send the whole buffer to the minecraft server. If [force] is set to true, send
    the buffer even if it has not reached the [buffer_size] limit yet"""
    if not force and len(_buffer) < buffer_size:
        return None

    print(f'SCHEDULING SENDING of {len(_buffer)} blocks')
    blocks = _buffer.exhaust()

    request_body = get_request_body(blocks)
    _requests.append(request_body)


# The block buffer. Contains all the blocks that will be sent to the minecraftserver
# and placed in the world by the __buffer_handler once its size exceeds the buffer_size
_buffer = Buffer()


def add_block_to_buffer(block: Block | Iterable[Block]) -> None:
    """Add the given [block] to the block buffer. Block may be either be a Block or
    any iterable of blocks"""
    _buffer.add(block) if type(block) is Block else _buffer.extend(block)


def add_string_to_buffer(block_name: str, coordinates: Coordinates) -> None:
    """Add the given [block_name] to the block buffer, specifying the [coordinates] on
    which the block should be placed"""
    block = Block(block_name, coordinates)
    _buffer.add(block)


def get_tasks(session: aiohttp.ClientSession) -> list[Task]:
    """"""
    return [session.put(URL, data=request_body) for request_body in _requests]


async def send_buffers(*, empty_buffer: bool = True) -> None:
    """Send all the scheduled buffer sending to the minecraft server. If [force] is set
    to true, schedule the current buffer even if it has not reached the [buffer_size]
    limit yet"""
    if empty_buffer:
        schedule_buffer_sending(force=True)

    if not _requests:
        # No tasks to create
        return None

    async with aiohttp.ClientSession() as session:
        tasks = get_tasks(session)
        await asyncio.gather(*tasks)


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
        await session.put(URL, data=body)


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
