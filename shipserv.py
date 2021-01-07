# The game server.
import shipclient
import common 
from enum import Enum
import asyncio
import shipclient

class Server:
    def __init__(self):
        self.clients = set()

    async def server(self, reader, writer):
        c = shipclient.Client(reader, writer)
        self.clients.add(c)
        try:
            while True:
                await c.parse_cmd()
        except ConnectionError:
            self.clients.remove(c)

    async def start_server(self):
        if common.windows:
            unix_server = await asyncio.start_server(self.server, '127.0.0.1', 8888)
        else:
            unix_server = await asyncio.start_unix_server(self.server, './chatsock')
        async with unix_server:
            await unix_server.serve_forever()



def main():
    if __name__ == "__main__":
        common.Battleship().game_server = Server()
        asyncio.run(common.Battleship().game_server.start_server())

main()


