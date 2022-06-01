import time
import requests
import threading
from typing import Deque, Iterable
from collections import deque

from src.blocks.block import Block
from src.utils.coordinates import Coordinates


class Buffer:
    """"""

    def __init__(self) -> None:
        """"""
        self.__buffer = deque()
        self.__lock = threading.Lock()

    def get(self) -> Block:
        """Return a single block from the buffer"""
        with self.__lock:
            return self.__buffer.popleft()

    def add(self, block: Block) -> None:
        """Add the given [block] to the buffer"""
        with self.__lock:
            self.__buffer.append(block)

    def extend(self, blocks: Iterable[Block]) -> None:
        """Add all the blocks in the given iterable to the buffer"""
        with self.__lock:
            self.__buffer.extend(blocks)

    def exhaust(self) -> Deque[Block]:
        """Return the blocks in the buffer then empty the buffer"""
        with self.__lock:
            buffer = self.__buffer.copy()
            self.__buffer.clear()
            return buffer

    def __len__(self) -> int:
        """Return the number of blocks in the buffer"""
        with self.__lock:
            return len(self.__buffer)


# The size of the buffer. Once the buffer has reached this number of blocks, the
# __buffer_handler will send all the blocks to the minecraft server at once.
buffer_size: int = 1024

# The block buffer. Contains all the blocks that will be sent to the minecraftserver
# and placed in the world by the __buffer_handler once its size exceeds the buffer_size
__buffer = Buffer()


flags: str = '0100011'


def add_to_buffer(block: Block | Iterable[Block]) -> None:
    """Add the given [block] to the block buffer. Block may be either be a Block or
    any iterable of blocks"""
    __buffer.add(block) if type(block) is Block else __buffer.extend(block)


def add_raw_to_buffer(block_name: str, coordinates: Coordinates) -> None:
    """Add the given [block_name] to the block buffer, specifying the [coordinates] on
    which the block should be placed"""
    block = Block(block_name, coordinates)
    __buffer.add(block)


def send_buffer(*, force: bool = False) -> None:
    """Send the whole buffer to the minecraft server. If [force] is set to true, send
    the buffer even if it has not reached the [buffer_size] limit yet"""
    if not force and len(__buffer) < buffer_size:
        return None

    print(f'SENDING BUFFER of size {len(__buffer)}')

    blocks = __buffer.exhaust()
    send_blocks(blocks)


def __buffer_handler() -> None:
    """Try to send the buffer to the minecraft server every time its size exceeds
    the buffer_size limit"""
    while True:
        # Attempt at sending the buffer
        send_buffer()


# Create a thread to handle and place blocks taken from the __buffer. This thread runs
# as a daemon, which means it will automatically be deleted upon success or exit
threading.Thread(target=__buffer_handler, daemon=True).start()


def format_block(block: Block) -> None:
    """"""
    return '{} {} {} {}'.format(*block.coordinates, block.full_name)


def place_block(block: Block | tuple[str, Coordinates]) -> None:
    """Place the given [block] on the minecraft server. Block may be either a Block
    object or a tuple of the block name and its coordinates"""
    coordinates = block.coordinates if isinstance(block, Block) else block[1]
    name = block.full_name if isinstance(block, Block) else block[0]

    body = '{} {} {} {}'.format(coordinates, name)
    __send_request(body)


def __send_request(body: str) -> None:
    """"""
    url = f'http://localhost:9000/blocks?x=0&y=0&z=0&customFlags={flags}&doBlockUpdate=True'

    try:
        response = requests.put(url, body)
    except ConnectionError:
        return "0"
    return response.text


def send_blocks(blocks: Iterable[Block], *, retries: int = 5, update_neighbours: bool = True, flags: str = None):
    """"""
    body = str.join("\n", [format_block(block) for block in blocks])

    try:
        response = __send_request(body)
        return response
    except ConnectionError as e:
        print("Request failed: {} Retrying ({} left)".format(e, retries))
        if retries > 0:
            # return sendBlocks(x, y, z, retries - 1)
            pass
    return False
