# The client API.
import common
import asyncio

class Client:
    def __init__(self, reader, writer):
        self.writer = writer
        self.reader = reader
        self.player = None
        self.state = common.PlayerState.LOGGING_IN
        common.Battleship().game_server.clients.add(self)
        self._drain_lock = asyncio.Lock()
        self.message_reader = common.MessageReader(self)

    async def parse_cmd(self):
        message = await self.message_reader.read_message()

        command = common.convert_message_to_command(self, message)

        return_message = command.do()

        await return_message.send_message()