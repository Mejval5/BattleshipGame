from enum import Enum
import asyncio
import re
from typing import Dict, List, Optional, Any
import random
import functools
import re

# Command systems
windows = True

def get_hash(server_salt, client_salt, ships):
    return 1

def convert_message_to_command(client, message):
    parsed_message = parse(message)

    if client.state == PlayerState.LOGGING_IN:
        return while_not_logged(client, parsed_message)
    
    if client.state == PlayerState.PLACING_SHIPS:
        return while_placing_ships(client, parsed_message)
            
    if client.state == PlayerState.CAN_JOIN_GAMES:
        return while_in_lobby(client, parsed_message)
        
    if client.state == PlayerState.IN_GAME:
        return while_playing(client, parsed_message)

    if client.state == PlayerState.SENDING_LAYOUT:
        return while_game_ended(client, parsed_message)

    return ErrorCommand(client, "client has no state")

def while_not_logged(client, parsed_message):
    fingerprint = NickParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        return LogInCommand(client, fingerprint.get_nick(), fingerprint.get_salt())
    else:
        return ErrorCommand(client, "could not log in")


def while_placing_ships(client, parsed_message):
    fingerprint = PutShipParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        if client.player.add_ship_to_board(*fingerprint.get_params()):
            return MessageCommand(client ,"Ship placed")
        return ErrorCommand(client, "cant't place ship")
    return ErrorCommand(client, "could not parse ship placement")

def while_game_ended(client, parsed_message):
    fingerprint = LayoutParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        game_id = fingerprint.get_game_id()
        game = Battleship().get_game_by_id(game_id)
        if game is not None:
            return game.check_for_cheating_by_layout(client.player, fingerprint.get_layout())
    return ErrorCommand(client, "layout not parsed")

def while_in_lobby(client, parsed_message):
    start_attempt = try_to_start(client, parsed_message)
    if start_attempt is not None:
        return start_attempt

    join_attempt = try_to_join(client, parsed_message)
    if join_attempt is not None:
        return join_attempt

    auto_attempt = try_to_auto(client, parsed_message)
    if auto_attempt is not None:
        return auto_attempt    

    list_attempt = try_to_list(client, parsed_message)
    if list_attempt is not None:
        return list_attempt

    return ErrorCommand(client, "could not join or start game")
        
    def try_to_start(client, parsed_message):
        fingerprint = StartParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            return Battleship().start_game(client, fingerprint.get_hash())       
        
    def try_to_list(client, parsed_message):
        fingerprint = ListParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            return Battleship().list_games(client)

    def try_to_join(client, parsed_message):
        fingerprint = JoinParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            _hash = fingerprint.get_hash()
            if game is not None:
                return game.join_peer(client, _hash)

    
    def try_to_auto(client, parsed_message):
        fingerprint = AutoParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            return Battleship().get_auto_game(client)
            

def while_playing(client, parsed_message):
    
    shoot_attempt = try_to_shoot(client, parsed_message)
    if shoot_attempt is not None:
        return shoot_attempt    

    feedback_attempt = try_to_declare_hit(client, parsed_message)
    if feedback_attempt is not None:
        return feedback_attempt  
    
    def try_to_declare_hit():
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                return game.hit() # TODO

    def try_to_declare_miss():
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                return game.miss() # TODO
    
    def try_to_shoot():
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                return client.player.shoot(fingerprint.get_x, fingerprint.get_y, game_id)



# Battleship main class

class Expression:
    def __init__(self):
        self.tokens = []

    def __str__(self):
        return "".join(str(t) for t in self.tokens)

    def __eq__(self, other):
        return self.tokens == other.tokens

    def is_compound(self):
        return False

    def is_whitespace(self):
        return False

    def is_atom(self):
        return False

    def is_literal(self):
        return False

    def is_bool(self):
        return False

    def is_number(self):
        return False

    def is_string(self):
        return False

    def is_identifier(self):
        return False


class Compound(Expression):
    def __init__(self):
        self._children = []

    def __iter__(self):
        return iter(self._children)

    def __repr__(self):
        return f"Compound({self._children})"

    def append(self, exp):
        self._children.append(exp)

    def is_compound(self):
        return iter(self._children)


class Atom(Expression):
    def is_atom(self):
        return True


class Token:
    REGEX = ""
    def __init__(self, x: str):
        self.value: Any = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    def __eq__(self, other):
        return self.value == other.value


@functools.total_ordering
class Number(Token, Atom):
    REGEX = r"[+-]?\d+(\.\d+)?"

    def __init__(self, x: str):
        try:
            self.value = int(x)
        except ValueError:
            self.value = float(x)
        self.real = self.value

    def __str__(self):
        return str(self.value)

    def __add__(self, other):
        return self.real + other.real

    def __sub__(self, other):
        return self.real - other.real

    def __mul__(self, other):
        return self.real * other.real

    def __truediv__(self, other):
        return self.real / other.real

    def __lt__(self, other):
        return self.real < other.real

    def __eq__(self, other):
        return self.real == other.real

    def __radd__(self, other):
        return self.real + other.real

    def __rsub__(self, other):
        return other.real - self.real

    def __rmul__(self, other):
        return self.real * other.real

    def __rtruediv__(self, other):
        return other.real / self.real

    def __int__(self):
        return int(self.value)

    def is_number(self):
        return True

    def is_literal(self):
        return True


class String(Token, Atom):
    REGEX = r'"(((\\\\)|(\\")|[^\\"])*)"'

    def __init__(self, x: str):
        m = re.fullmatch(self.REGEX, x)
        if m is not None:
            self.value = m.group(1)
        else:
            raise RuntimeError(f"Cannot tokenize {x}")

    def __str__(self):
        return "\"{}\"".format(self.value)

    def is_string(self):
        return True

    def is_literal(self):
        return True


class Boolean(Token, Atom):
    REGEX = r'(#f)|(#t)'

    def __init__(self, x: str):
        self.value = True if x == "#t" else False

    def __str__(self):
        return "#t" if self.value else "#f"

    def __bool__(self):
        return self.value

    def is_bool(self):
        return True

    def is_literal(self):
        return True


class Identifier(Token, Atom):
    initial_ID = r"a-z!$%&*/:<=>?^_~"
    next_ID = initial_ID+r"\d+\-.@#"
    REGEX = r"(["+initial_ID+r"]["+next_ID+r"]*)|[+-]"

    def __init__(self, x: str):
        self.value = x

    def __str__(self):
        return self.value

    def is_identifier(self):
        return True

class LPar(Token):
    REGEX = r"(\(|\[)"

    def __str__(self):
        return "("


class RPar(Token):
    REGEX = r"(\)|\])"

    def __str__(self):
        return ")"


class Whitespace(Token):
    REGEX = r"\s+"

    def __init__(self, x: str):
        self.value: str = x

    def __str__(self):
        return self.value

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Battleship(metaclass=Singleton):

    def __init__(self):
        self.game_server = Server()
        self.server_salt = random.randint(0,999999999999999999999)
        self.players = set()
        self.games = set()

    def list_games(self, client):
        message ="(games"
        for g in self.games:
            message += " " + g.game_to_text
        message += ")"
        return MessageCommand(client, message)

    def get_player_by_nick(self, nick):
        for p in self.players:
            if p.nick == nick:
                return p

    def get_game_by_id(self, id):
        for g in self.games:
            if g.id == id:
                return g

    def remove_game(self, game):
        for g in self.games:
            if g.id == game.id:
                self.games.remove(g)
                del g

    def add_player(self, player):
        self.players.add(player)

    def remove_player(self, player):
        for p in self.players:
            if p.nick == player.nick:
                self.players.remove(p)
                
    def nickname_in_use(self, nick):
        for p in self.players:
            if nick == p.nick:
                return True
        return False

    def get_first_free_game_by_nick(self, nick):
        pass

    def get_auto_game(self, client, _hash):
        for g in self.games:
            if g.state == GameState.WAITING:
                return g.join_peer(client, _hash)
        return self.start_game(client, _hash)

    def start_game(self, client, _hash):
        game = Game(client, _hash)
        self.games.add(game)
        return MessageCommand(client, "Game Started, ID: " + game.id)


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
        self.client.state = PlayerState.PLACING_SHIPS    



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
            return JoinGame(game_id, self.client, get_hash(Battleship().server_salt, self.client.player.salt, self.client.player.own_board)).do()

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


class PlayerState(Enum):
    LOGGING_IN = 0
    PLACING_SHIPS = 1
    CAN_JOIN_GAMES = 2
    IN_GAME = 3
    SENDING_LAYOUT = 4

class PlayerType(Enum):
    HOST = 'host'
    PEER = 'peer'

class GameState(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"

class BoardFieldType(Enum):
    WATER = 'w'
    MISS = 'm'
    HIT = 'h'
    SHIP = 's'
    UNKNOWN = '?'


class ParseFingerPrint:

    def __init__(self):
        self.command = None
        self.expected_command = None
        self.tokens = []
        self.parsed_message = object
        self.parsed_message.tokens = []

    def extract_command(self, parsed_message):
        if hasattr(parsed_message, "_children"):
            return parsed_message._children[0].value
        return ""

    def is_valid(self):
        if self.command != self.expected_command:
            return False
        if len(self.tokens) != len(self.parsed_message.tokens):
            return False
        for i in range(len(self.tokens)):
            if self.tokens[i] != type(self.parsed_message.tokens[i]):
                return False
        return True

class NickParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'nick'
        self.tokens = [LPar, Identifier, Whitespace, String, Whitespace, String, RPar]
        self.parsed_message = parsed_message
        
    def get_salt(self):
        return self.parsed_message._children[2].value

    def get_nick(self):
        return self.parsed_message._children[1].value

class PutShipParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'put_ship'
        self.tokens = [LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Boolean, RPar]
        self.parsed_message = parsed_message

    def get_x(self):
        return self.parsed_message._children[1].value

    def get_y(self):
        return self.parsed_message._children[2].value

    def get_size(self):
        return self.parsed_message._children[3].value
    
    def is_vertical(self):
        return self.parsed_message._children[4].value

    def get_params(self):
        return self.get_x(), self.get_y(), self.get_size(), self.is_vertical()


class EnemyParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'enemy'
        self.tokens = [LPar, Identifier, RPar]
        self.parsed_message = parsed_message
    
    def get_salt(self):
        return self.parsed_message._children[2].value


class ShootParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'shoot'
        self.tokens = [LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, RPar]
        self.parsed_message = parsed_message
    
    def get_game_id(self):
        return self.parsed_message._children[1].value

    def get_x(self):
        return self.parsed_message._children[2].value

    def get_y(self):
        return self.parsed_message._children[3].value

class JoinParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'join'
        self.tokens = [LPar, Identifier, Whitespace, Number, Whitespace, String, RPar]
        self.parsed_message = parsed_message
    
    def get_game_id(self):
        return self.parsed_message._children[1].value

    def get_hash(self):
        return self.parsed_message._children[2].value


class StartParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'start'
        self.tokens = [LPar, Identifier, Whitespace, String, RPar]
        self.parsed_message = parsed_message

    def get_hash(self):
        return self.parsed_message._children[1].value


class ListParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'list'
        self.tokens = [LPar, Identifier, RPar]
        self.parsed_message = parsed_message

class AutoParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'auto'
        self.tokens = [LPar, Identifier, RPar]
        self.parsed_message = parsed_message

class LayoutParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'layout'
        self.tokens = [LPar, Identifier, Whitespace, Number, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, RPar]
        self.parsed_message = parsed_message
    
    def get_game_id(self):
        return self.parsed_message._children[1].value

    def get_layout(self):
        return self.parsed_message._children[2:].value


class HitParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'hit'
        self.tokens = [LPar, Identifier, Whitespace, Number, RPar]
        self.parsed_message = parsed_message
    
    def get_game_id(self):
        return self.parsed_message._children[1].value

class MissParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'miss'
        self.tokens = [LPar, Identifier, Whitespace, Number, RPar]
        self.parsed_message = parsed_message
    
    def get_game_id(self):
        return self.parsed_message._children[1].value

# Game classes

class Ship:
    def __init__(self, x, y, size, vertical):
        self.x = x
        self.y = y
        self.size = size
        self.vertical = vertical

    def take_hit(self):
        pass

    def place_ship(self, board):
        pass

    def self_to_tuple(self):
        return (self.x, self.y, self.vertical)


class Field:
    def __init__(self, x, y, val):
        self.x = x
        self.y = y
        self.value = val

    def set_value(self, val):
        self.value = val

    def get_value(self):
        return self.value


class Board:

    def __init__(self):
        self.layout = [[]]

    def return_board_state(self):
        return self.layout


class EnemyBoard(Board):
    def __init__(self):
        super().__init__()
        # self.layout = [[BoardFieldType.UNKNOWN for x in range(10)] for y in range(10)]
        self.layout = [[Field(x, y, BoardFieldType.UNKNOWN) for x in range(10)] for y in range(10)]


class PlayerBoard(Board):
    def __init__(self):
        super().__init__()
        self.layout = [[Field(x, y, BoardFieldType.WATER) for x in range(10)] for y in range(10)]
        self.ships =    {5: None,
                        4: None,
                        31: None,
                        32: None,
                        2: None}

    def get_ship_tuples(self):
        ship_list = []
        for key in [5, 4, 31, 32, 2]:
            ship_list.append(self.ships[key].self_to_tuple())
        return ship_list

    def add_ship(self, ship):
        if not self.ship_crosses_ship(ship) and not self.ship_crosses_edge(ship) and self.is_ship_by_size_missing(ship):
            if not ship.vertical:
                for f in self.layout[ship.y]:
                    if ship.x <= f.x < ship.x + ship.size:
                        f.set_value(BoardFieldType.SHIP)
            else:
                for f in self.layout:
                    f[ship.x].set_value(BoardFieldType.SHIP)
            return self.add_ship_to_holder(ship)
        else:
            return False  # co chceme vract při failu?
        return True  # message nebo messagecommand

    def is_ship_by_size_missing(self, ship):
        if ship.size in (5, 4, 2):
             return self.ships[ship.size] is None
        if ship.size == 3:
            return self.ships[31] is None or self.ships[32] is None
        return False

    def add_ship_to_holder(self, ship):
        if ship.size in (5, 4, 2):
            if self.ships[ship.size] is None:
                self.ships[ship.size] = ship
                return True
        if ship.size == 3:
            if self.ships[31] is None:
                self.ships[31] = ship
                self.sort_threes()
                return True
            elif self.ships[32] is None:
                self.ships[32] = ship
                self.sort_threes()
                return True
        return False
                
    def sort_threes(self):
        ship_a = self.ships[31]
        ship_b = self.ships[32]
        if ship_a is not None and ship_b is not None:
            if ship_a.x < ship_b.x:
                self.ships[31] = ship_a
                self.ships[32] = ship_b
            elif ship_b.x < ship_a.x:
                self.ships[31] = ship_b
                self.ships[32] = ship_a
            else:
                if ship_a.y < ship_b.y:
                    self.ships[31] = ship_a
                    self.ships[32] = ship_b
                elif ship_b.y < ship_a.y:
                    self.ships[31] = ship_b
                    self.ships[32] = ship_a 
           

    def ship_crosses_ship(self, ship):
        if not ship.vertical:
            for f in self.layout[ship.y]:
                if ship.x <= f.x < ship.x + ship.size:
                    if f.value == BoardFieldType.SHIP:
                        return True
        else:
            for row in self.layout:
                for f in row[ship.x:ship.x + ship.size]:
                    if f.value == BoardFieldType.SHIP:
                        return True
        return False

    def ship_crosses_edge(self, ship: Ship):
        if not ship.vertical:
            if (ship.x + ship.size) > 9:
                return True
            return False
        else:
            if (ship.x + ship.size) > 9:
                return True
            return False


class Player:
    def __init__(self, nick, salt):
        self.nick = nick
        self.own_board = PlayerBoard()
        self.enemy_board = EnemyBoard()
        self.salt = salt

    def add_ship_to_board(self, x, y, size, vertical):
        ship = Ship(x, y, size, vertical)
        if self.own_board.add_ship(ship):
            return True
        return False

    def start(self):
        pass

    def restart(self):
        pass

    def join_game(self, game_id):
        pass

    def end(self):
        pass

    def enemy(self):
        pass

    def board(self):
        return

    def shoot(self, x, y, game_id):
        pass


class Game():
    def __init__(self, client, _hash):
        self.id = random.randint(0, 9999999999999)
        self.state = GameState.WAITING  # active / waiting
        self.hit_stat = {PlayerType.HOST: 0, PlayerType.PEER: 0}
        self.clients = {PlayerType.HOST: client, PlayerType.PEER: None}
        self.player_nicks = {PlayerType.HOST: client.player.nick, PlayerType.PEER: None}
        self.player_hashes = {PlayerType.HOST: _hash, PlayerType.PEER: None}  # maybe just players?
        self.player_hashes_valid = {PlayerType.HOST: None, PlayerType.PEER: None}  # maybe just players?
        self.player_boards_valid = {PlayerType.HOST: None, PlayerType.PEER: None}  # maybe just players?
        self.turn = 0  #
        self.player_turn = PlayerType.HOST

    def game_to_text(self):
        if self.state == GameState.ACTIVE:
            text = f"({self.state} \"{self.player_nicks[PlayerType.HOST]}\" \"{self.player_nicks[PlayerType.PEER]}\" {self.id})"
        else:
            text = f"({self.state} \"{self.player_nicks[PlayerType.HOST]}\" {self.id})"
        return text

    def check_for_cheating_by_layout(self, client, layout):
        test_player = Player(client.player.nick, client.player.salt)
        test_player_type = self.get_playertype_by_nick(test_player.nick)
        if test_player_type is None:
            return ErrorCommand(client, "You ain't in this game boy")

        self.player_boards_valid[test_player_type] = True
        for item in layout:
            if not test_player.add_ship_to_board(*ShipParser(item).get_params()):
                self.player_boards_valid[test_player_type] = False
                break

        test_hash = get_hash(Battleship().server_salt, test_player.salt, test_player.own_board.get_ship_tuples())


        self.player_hashes_valid[test_player_type] = test_hash == self.player_hashes[test_player_type]
        return self.check_if_both_hashes_are_in(client)

    def check_if_both_hashes_are_in(self, client):
        if self.player_hashes_valid[PlayerType.HOST] is not None and self.player_hashes_valid[PlayerType.PEER] is not None:
            self.check_hash_validation()
        return MessageCommand(client, "")

    async def check_hash_validation(self):
        if self.player_hashes_valid[PlayerType.HOST] and self.player_hashes_valid[PlayerType.PEER]:
            for c in self.clients.values():
                await Message(c, "(game ok)").send_message()
        else:
            for c in self.clients.values():
                await Message(c, "(game aborted)").send_message()
                for player_type in [PlayerType.HOST, PlayerType.PEER]:
                    if not self.player_hashes_valid[player_type]:
                        await Message(c, "(hash-mismatch " + self.id + f" \"{self.player_nicks[player_type]}\")").send_message()
                    if not self.player_boards_valid[player_type]:
                        await Message(c, "(board-mismatch " + self.id + f" \"{self.player_nicks[player_type]}\")").send_message()
        Battleship().list_games().remove_game(self)
        del self





    def get_playertype_by_nick(self, nick):
        if self.player_nicks[PlayerType.HOST] == nick:
            return PlayerType.HOST
        if self.player_nicks[PlayerType.PEER] == nick:
            return PlayerType.PEER
        return None

    def end_turn(self):
        if self.player_turn == PlayerType.HOST:
            self.player_turn = PlayerType.PEER
        else:
            self.player_turn = PlayerType.HOST
        self.turn += 1

    def finished(self):
        pass

    def won(self):
        pass

    def draw(self):
        pass

    def aborted(self):
        pass

    def round(self, x, y):
        pass  # check if correct player calls round if not, send error

    def join_peer(self, client, _hash):
        if self.player_nicks[PlayerType.PEER] is None:
            self.state = GameState.ACTIVE
            self.player_hashes[PlayerType.PEER] = _hash
            self.player_nicks[PlayerType.PEER] = client.nick  
            self.clients[PlayerType.PEER] = client 
            return MessageCommand(client, f"(client joined to game id: {self.id})")
        return ErrorCommand(client, "game full")

    def leave(self, player):
        pass

    def shoot(self, x, y, player):
        pass

    def miss(self):
        pass

    def hit(self):
        pass

class ShipParser():

    def __init__(self, ship_compound):
        self.ship_compound = ship_compound

    def get_x(self):
        return self.ship_compound._children[1]

    def get_y(self):
        return self.ship_compound._children[2]

    def get_size(self):
        return self.ship_compound._children[3]
    
    def is_vertical(self):
        return self.ship_compound._children[4]

    def get_params(self):
        return self.get_x(), self.get_y(), self.get_size(), self.is_vertical()

def tokenize(x: str) -> List[Token]:
    def start(pattern: str, x: str):
        match = re.match(pattern, x)
        if match is None:
            return "", x
        if match.span()[0] == 0:
            return x[:match.span()[1]], x[match.span()[1]:]
        return "", x
    tokens = []
    while x:
        for sub in Token.__subclasses__():
            match, x = start(sub.REGEX, x)
            if match:
                tok = sub(match)
                if isinstance(tok, Whitespace):
                    tok.value = tok.value[0]
                tokens.append(tok)
                break
        else:
            raise RuntimeError(f"Cannot tokenize {x}.")
    return tokens

def matching_pars(tokens: List[Token]) -> Dict[int, int]:
    pars = []
    lefts = []
    for i, token in enumerate(tokens):
        if isinstance(token, LPar):
            lefts.append(i)
        if isinstance(token, RPar):
            try:
                pars.append((lefts.pop(), i))
            except IndexError:
                raise RuntimeError("Parentheses do not match.")
    if lefts:
        raise RuntimeError("Parentheses not properly closed.")
    return dict(pars)

def nest(tokens: List[Token],pars: Dict[int, int], start: int, end: int) -> Compound:
    exp = Compound()
    x = start
    while x < end:
        t = tokens[x]
        if isinstance(t, LPar):
            p = nest(tokens, pars, x+1, pars[x])
            p.tokens = tokens[x:pars[x]+1]
            exp.append(p)
            x = pars[x]
        if isinstance(t, Atom):
            exp.append(t)
        x += 1
    return exp


def parse(x: str) -> Optional[Expression]:
    try:
        tokens = tokenize(x)
        cleaned_tokens = [t for t in tokens if not isinstance(t, Whitespace)]
        pars = matching_pars(tokens)
    except RuntimeError:
        return None
    if not pars and len(cleaned_tokens) > 1:
        return None
    for pair in pars.items():
        if abs(pair[1] - pair[0]) == 1:
            return None
    if not cleaned_tokens:
        return None
    if not pars:
        if isinstance(cleaned_tokens[0], Atom):
            atom = cleaned_tokens[0]
            atom.tokens = tokens
            return atom
    nested = nest(tokens, pars, 1, len(tokens)-1)
    nested.tokens = tokens
    return nested

class Server:
    def __init__(self):
        self.clients = set()

    async def server(self, reader, writer):
        c = Client(reader, writer)
        self.clients.add(c)
        try:
            while True:
                await c.parse_cmd()
        except ConnectionError:
            self.clients.remove(c)

    async def start_server(self):
        if windows:
            unix_server = await asyncio.start_server(self.server, '127.0.0.1', 8888)
        else:
            unix_server = await asyncio.start_unix_server(self.server, './chatsock')
        async with unix_server:
            await unix_server.serve_forever()

class Client:
    def __init__(self, reader, writer):
        self.writer = writer
        self.reader = reader
        self.player = None
        self.state = PlayerState.LOGGING_IN
        Battleship().game_server.clients.add(self)
        self._drain_lock = asyncio.Lock()
        self.message_reader = MessageReader(self)

    async def parse_cmd(self):
        message = await self.message_reader.read_message()

        command = convert_message_to_command(self, message)

        return_message = command.do()

        await return_message.send_message()




# Command systems
windows = True


def main():
    if __name__ == "__main__":
        Battleship().game_server = Server()
        asyncio.run(Battleship().game_server.start_server())




main()


