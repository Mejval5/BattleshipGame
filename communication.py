
# Command systems
windows = True

class Command():

    def __init__(self, client):
        self.client = client

    def do(self):
        raise NotImplementedError()


class LogInCommand(Command):
    def __init__(self, client, nick, salt):
        self.client = client
        self.nick = nick
        self.salt = salt

    def set_nick(self):
        if not self.nick.isalnum() or Battleship().nickname_in_use(self.nick) or not self.salt.isalnum():
            return False
        return True

    def do(self):
        if self.set_nick():        
            self.login_client()
            return SaltMessage(self.client, self.client.player.salt)
        else:
            return ErrorMessage(self.client)
    
    def login_client(self):
        self.client.logged_in = True
        self.client.player = Player(self.nick, self.salt)    



class GameCommand(Command):

    def __init__(self, client, game_id):
        self.game_id = game_id
        self.client = client

    def get_game(self):
        self.game = Battleship().get_game_by_id(self.game_id)
        if self.game is None:
            return False
        return True

class JoinGame(GameCommand):

    def __init__(self, client, game_id, hash):
        self.client = client
        self.game_id = game_id
        self.hash = hash

    def do(self):
        if self.get_game():
            return self.game.join_peer(self.client.player)
        else:
            return ErrorMessage(self.client)

class LeaveGame(GameCommand):

    def do(self):
        if self.get_game():
            return self.game.leave(self.client.player)
        else:
            return ErrorMessage(self.client)

class EndLayout(GameCommand):
    
    def __init__(self, client, game_id, layout):
        self.game_id = game_id
        self.client = client
        self.layout = layout

    def do(self):
        if self.get_game():
            return self.game.parse_layout(self.client, self.layout)
        else:
            return ErrorMessage(self.client)

class PutShip(Command):
    def __init__(self, client, x, y, size, vertical):
        self.client = client
        self.ship = Ship(x, y, size, vertical)

    def do(self):        
        return self.client.player.own_board.add_ship(self.ship)

class CreateGame(Command):

    def __init__(self, client, hash):
        self.client = client
        self.hash = hash

    def do(self):
        return Battleship().start_game(self.client, self.hash)

class ListGames(Command):

    def do(self):
        return Battleship().list_games()

class JoinAuto(Command):

    def do(self):
        return Battleship().get_auto_game(self.client)

class JoinToNickCommand(Command):

    def __init__(self, client, join_nick):
        self.join_nick = join_nick
        self.client = client
    
    def do(self):
        game_id = Battleship().get_first_free_game_by_nick(self.join_nick)
        if game_id is None:
            return ErrorMessage(self.client)
        else:
            return JoinGame(game_id, self.client, get_hash(self.client.player.own_board)).do()

class EnemyCommand(Command):

    def do(self):
        return self.client.player.enemy_board.return_board_state()

class BoardCommand(Command):

    def do(self):
        return self.client.player.own_board.return_board_state()

class ShootCommand(GameCommand):

    def __init__(self, client, game_id, x, y):
        self.client = client
        self.game_id = game_id
        self.x = x
        self.y = y

    def do(self):
        if self.get_game():
            return self.game.shoot(self.client.player, self.x, self.y)
        else:
            return ErrorMessage(self.client)



class ErrorCommand(Command):

    def __init__(self, client, error = ""):
        self.client = client
        self.error = error

    def do(self):
        return ErrorMessage(self.client, self.error)

class MessageCommand(Command):

    def __init__(self, client, message):
        self.client = client
        self.message = message

    def do(self):
        return Message(self.client, self.message)

class SaltCommand(Command):

    def __init__(self, client, salt):
        self.client = client
        self.salt = salt

    def do(self):
        return SaltMessage(self.client, self.salt)

# Messaging systems


class Message():

    def __init__(self, client, message):
        self.message = message
        self.client = client
    
    async def send_message(self):
        if windows:
            self.client.writer.write(f"{self.message}\n\r".encode())
        else:
            self.client.writer.write(f"{self.message}\n".encode())
        async with self.client._drain_lock:
            await self.client.writer.drain()

class SaltMessage(Message):
    
    def __init__(self, client, salt):
        self.message = "ok " + salt
        self.client = client

class ErrorMessage(Message):

    def __init__(self, client, error = ""):
        self.client = client
        self.message = self.get_error_message(error)
        
    def get_error_message(self, error=""):
        if error:
            error_message = f"error {error}!"
        else:
            error_message = "error"
        return error_message


class MessageReader():

    def __init__(self, client):
        self.client = client
    
    async def read_message(self):
        data = await self.client.reader.readline()
        if windows:
            return data.decode().rstrip("\n").rstrip("\r")
        else:
            return data.decode().rstrip("\n")

from common import *
from game_classes import Player, Ship