from enum import Enum
import asyncio
import re
from typing import Dict, List, Optional, Any
import random
import functools
import re
import copy

# Command systems
windows = True

def hash_game(server_salt, client_salt, ships):
    string = str(server_salt) + str(client_salt) + str(ships)
    _hash = hash(string)
    return _hash


async def parse_message_and_do_commands(client, message):
    parsed_message = parse(message)
    split_commands(client, parsed_message)


def split_commands(client, parsed_message):
    all_compounds = False
    if hasattr(parsed_message, "_children"):
        all_compounds = True

        for child in parsed_message._children:
            if type(child) != Compound:
                all_compounds = False

        if all_compounds:
            for child in parsed_message._children:
                split_commands(client, child)
                return
    try_to_do_command(client, parsed_message)
                

def try_to_do_command(client, parsed_message):

    if client.player.state == PlayerState.LOGGING_IN:
        while_not_logged(client, parsed_message)
    
    elif client.player.state == PlayerState.PLACING_SHIPS:
        while_placing_ships(client, parsed_message)
            
    elif client.player.state == PlayerState.CAN_JOIN_GAMES:
        while_in_lobby(client, parsed_message)
        
    elif client.player.state == PlayerState.IN_GAME:
        while_playing(client, parsed_message)

    elif client.player.state == PlayerState.SENDING_LAYOUT:
        while_game_ended(client, parsed_message)

    elif client.player.state == PlayerState.BLOCKED:
        pass

    else:
        ErrorMessage(client, "client has no state")

def while_not_logged(client, parsed_message):
    fingerprint = NickParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        LogInCommand(client, fingerprint.get_nick(), fingerprint.get_salt())
    else:
        ErrorMessage(client, "could not log in")


def while_placing_ships(client, parsed_message):
    fingerprint = PutShipParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        if client.player.add_ship_to_board(*fingerprint.get_params()):
            Message(client ,"Ship placed")
        else:
            ErrorMessage(client, "cant't place ship")
    else:
        ErrorMessage(client, "could not parse ship placement")

def while_game_ended(client, parsed_message):
    fingerprint = LayoutParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        game_id = fingerprint.get_game_id()
        game = Battleship().get_game_by_id(game_id)
        if game is not None:
            game.check_for_cheating_by_layout(client, fingerprint.get_layout())
        else:
            ErrorMessage(client, "game does not exist")
    else:
        ErrorMessage(client, "layout not parsed")

def while_in_lobby(client, parsed_message):
        
    def try_to_start(client, parsed_message):
        fingerprint = StartParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            Battleship().start_game(client, fingerprint.get_hash())
            return True
        
    def try_to_list(client, parsed_message):
        fingerprint = ListParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            Battleship().list_games(client)
            return True

    def try_to_join(client, parsed_message):
        fingerprint = JoinParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            _hash = fingerprint.get_hash()
            if game is not None:
                game.join_peer(client, _hash)
                return True

    
    def try_to_auto(client, parsed_message):
        fingerprint = AutoParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            Battleship().get_auto_game(client, fingerprint.get_hash())
            return True

    parsed_any = []
    
    parsed_any.append(try_to_start(client, parsed_message))

    parsed_any.append(try_to_join(client, parsed_message))

    parsed_any.append(try_to_auto(client, parsed_message))

    parsed_any.append(try_to_list(client, parsed_message))

    if not True in parsed_any:
        ErrorMessage(client, "invalid command for start game")
            

def while_playing(client, parsed_message):

    def try_to_declare_hit(client, parsed_message):
        fingerprint = HitParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                game.try_to_hit(client, True)
                return True

    def try_to_declare_miss(client, parsed_message):
        fingerprint = MissParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                game.try_to_hit(client, False)
                return True
    
    def try_to_shoot(client, parsed_message):
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                game.shoot(fingerprint.get_x(), fingerprint.get_y(), client)
                return True
                
    parsed_any = []
    
    parsed_any.append(try_to_shoot(client, parsed_message))

    parsed_any.append(try_to_declare_hit(client, parsed_message))

    parsed_any.append(try_to_declare_miss(client, parsed_message))
    
    if not True in parsed_any:
        ErrorMessage(client, "invalid command in game")



# Battleship main class

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
            message += " " + g.game_to_text()
        message += ")"
        Message(client, message)

    def get_player_by_nick(self, nick):
        for p in self.players:
            if p.nick == nick:
                return p

    def get_game_by_id(self, id):
        for g in self.games:
            if g.id == id:
                return g

    def remove_game(self, game):
        removed_game = None
        for g in self.games:
            if g.id == game.id:
                removed_game = g
        if removed_game is not None:
            self.games.remove(removed_game)
            del removed_game

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
        for g in self.games:
            if nick == g.player_nicks[PlayerType.HOST]:
                return g
        return None

    def get_auto_game(self, client, _hash):
        for g in self.games:
            if g.state == GameState.WAITING:
                return g.join_peer(client, _hash)
        return self.start_game(client, _hash)

    def start_game(self, client, _hash):
        game = Game(client, _hash)
        self.games.add(game)
        Message(client, "Game Started, ID: " + str(game.id))


class Command():

    def __init__(self, client):
        self.client = client
        self.do()

    def do(self):
        raise NotImplementedError()


class LogInCommand(Command):
    def __init__(self, client, nick, salt):
        self.client = client
        self.nick = nick
        self.salt = salt
        self.do()

    def set_nick(self):
        if not self.nick.isalnum() or Battleship().nickname_in_use(self.nick) or not self.salt.isalnum():
            return False
        return True

    def do(self):
        if self.set_nick():        
            self.login_client()
            SaltMessage(self.client, self.client.player.salt)
        else:
            ErrorMessage(self.client)
    
    def login_client(self):
        self.client.logged_in = True
        self.client.player = Player(self.nick, self.salt)
        self.client.player.state = PlayerState.PLACING_SHIPS
        Battleship().add_player(self.client.player)



class GameCommand(Command):

    def __init__(self, client, game_id):
        self.game_id = game_id
        self.client = client
        self.do()

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
        self.do()

    def do(self):
        if self.get_game():
            self.game.join_peer(self.client.player)
        else:
            ErrorMessage(self.client)

class LeaveGame(GameCommand):

    def do(self):
        if self.get_game():
            self.game.leave(self.client.player)
        else:
            ErrorMessage(self.client)

class EndLayout(GameCommand):
    
    def __init__(self, client, game_id, layout):
        self.game_id = game_id
        self.client = client
        self.layout = layout
        self.do()

    def do(self):
        if self.get_game():
            self.game.parse_layout(self.client, self.layout)
        else:
            ErrorMessage(self.client)

class PutShip(Command):
    def __init__(self, client, x, y, size, vertical):
        self.client = client
        self.ship = Ship(x, y, size, vertical)
        self.do()

    def do(self):        
        self.client.player.own_board.add_ship(self.ship)

class CreateGame(Command):

    def __init__(self, client, hash):
        self.client = client
        self.hash = hash
        self.do()

    def do(self):
        Battleship().start_game(self.client, self.hash)

class ListGames(Command):

    def do(self):
        Battleship().list_games()

class JoinAuto(Command):

    def do(self):
        Battleship().get_auto_game(self.client)

class JoinToNickCommand(Command):

    def __init__(self, client, join_nick):
        self.join_nick = join_nick
        self.client = client
        self.do()
    
    def do(self):
        game_id = Battleship().get_first_free_game_by_nick(self.join_nick)
        if game_id is None:
            ErrorMessage(self.client)
        else:
            JoinGame(game_id, self.client, hash_game(Battleship().server_salt, self.client.player.salt, self.client.player.own_board)).do()

class EnemyCommand(Command):

    def do(self):
        self.client.player.enemy_board.return_board_state()

class BoardCommand(Command):

    def do(self):
        self.client.player.own_board.return_board_state()

class ShootCommand(GameCommand):

    def __init__(self, client, game_id, x, y):
        self.client = client
        self.game_id = game_id
        self.x = x
        self.y = y

    def do(self):
        if self.get_game():
            self.game.shoot(self.client.player, self.x, self.y)
        else:
            ErrorMessage(self.client)

""" 

class ErrorCommand(Command):

    def __init__(self, client, error = ""):
        self.client = client
        self.error = error
        self.do()

    def do(self):
        ErrorMessage(self.client, self.error)

class MessageCommand(Command):

    def __init__(self, client, message):
        self.client = client
        self.message = message
        self.do()

    def do(self):
        Message(self.client, self.message)

class SaltCommand(Command):

    def __init__(self, client, salt):
        self.client = client
        self.salt = salt
        self.do()

    def do(self):
        SaltMessage(self.client, self.salt) """

# Messaging systems


class Message():

    def __init__(self, client, message):
        self.message = message
        self.client = client
        self.send_message_async()
    
    def send_message_async(self):
        asyncio.create_task(self.send_message())
    
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
        self.send_message_async()

class ErrorMessage(Message):

    def __init__(self, client, error = ""):
        self.client = client
        self.message = self.get_error_message(error)
        self.send_message_async()
        
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
    BLOCKED = 5

class PlayerType(Enum):
    HOST = 'host'
    PEER = 'peer'

class GameState(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"

class RoundState(Enum):
    SHOOTING = "shooting"
    CHECKING = "checking"

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
            if type(parsed_message._children[0]) is Identifier:
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
        self.tokens = [LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, RPar]
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
        self.tokens = [LPar, Identifier, Whitespace, String, RPar]
        self.parsed_message = parsed_message
    
    def get_hash(self):
        return self.parsed_message._children[1].value

class LayoutParseFingerPrint(ParseFingerPrint):

    def __init__(self, parsed_message):
        self.command = self.extract_command(parsed_message)
        self.expected_command = 'layout'
        self.tokens = [LPar, Identifier, Whitespace, Number, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, Whitespace, LPar, Identifier, Whitespace, Number, Whitespace, Number, Whitespace, Number, Whitespace, Identifier, RPar, RPar]
        self.parsed_message = parsed_message
    
    def get_game_id(self):
        return self.parsed_message._children[1].value

    def get_layout(self):
        return [a for a in self.parsed_message._children[2:]]


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
                for f in self.layout[ship.y - ship.size + 1:ship.y + 1]:
                    f[ship.x].set_value(BoardFieldType.SHIP)
            #self.ship_printer()
            return self.add_ship_to_holder(ship)
        else:
            return False  # co chceme vract při failu?

    def ship_printer(self):
        print_layout = [[Field(x, y, BoardFieldType.WATER) for x in range(10)] for y in range(10)]
        for y in range(9,-1,-1):
            for x in range(10):
                print_layout[y][x] = self.layout[y][x].value.value
            print(print_layout[y])
        print("\n")

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
            for row in self.layout[ship.y - ship.size + 1:ship.y + 1]:
                if row[ship.x] == BoardFieldType.SHIP:
                    return True
        return False

    def ship_crosses_edge(self, ship: Ship):
        if not ship.vertical:
            if (ship.x + ship.size) > 10:
                return True
            return False
        else:
            if (ship.y - ship.size) < -1:
                return True
            return False

    def check_if_shots_are_valid(self, shots):
        test_layout = copy.copy(self.layout)
        for shot in shots:
            # shot = [x y bool]
            if shot[2]:
                if test_layout[shot[1]][shot[0]].get_value() == BoardFieldType.SHIP:
                    test_layout[shot[1]][shot[0]].set_value(BoardFieldType.HIT)
                else:
                    return False
            else:
                if test_layout[shot[1]][shot[0]].get_value() == BoardFieldType.SHIP:
                    return False
                else:
                    test_layout[shot[1]][shot[0]].set_value(BoardFieldType.MISS)
        return True
                    
class Player:
    def __init__(self, nick, salt):
        self.nick = nick
        self.own_board = PlayerBoard()
        self.enemy_board = EnemyBoard()
        self.salt = salt
        self.state = PlayerState.LOGGING_IN

    def add_ship_to_board(self, x, y, size, vertical):
        ship = Ship(x, y, size, vertical)
        if self.own_board.add_ship(ship):
            self.check_if_all_ships_are_placed()
            return True
        return False

    def check_if_all_ships_are_placed(self):
        all_placed = True

        for ship in self.own_board.ships.values():
            if ship is None:
                all_placed = False

        if all_placed:
            self.state = PlayerState.CAN_JOIN_GAMES

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


class Game():
    def __init__(self, client, _hash):
        self.id = random.randint(0, 9999999999999)
        self.state = GameState.WAITING  
        self.turn_state = RoundState.SHOOTING
        self.hit_stat = {PlayerType.HOST: 0, PlayerType.PEER: 0}
        self.clients = {PlayerType.HOST: client, PlayerType.PEER: None}
        self.player_nicks = {PlayerType.HOST: client.player.nick, PlayerType.PEER: None}
        self.player_hashes = {PlayerType.HOST: _hash, PlayerType.PEER: None}  
        self.player_hashes_valid = {PlayerType.HOST: None, PlayerType.PEER: None} 
        self.player_boards_valid = {PlayerType.HOST: None, PlayerType.PEER: None}  
        self.player_has_won = {PlayerType.HOST: False, PlayerType.PEER: False}  
        self.turn = 0  #
        self.shots = {PlayerType.HOST: [], PlayerType.PEER: []}
        self.player_turn = PlayerType.HOST
        client.player.state = PlayerState.BLOCKED

    def game_to_text(self):
        if self.state == GameState.ACTIVE:
            text = f"({self.state.value} \"{self.player_nicks[PlayerType.HOST]}\" \"{self.player_nicks[PlayerType.PEER]}\" {self.id})"
        else:
            text = f"({self.state.value} \"{self.player_nicks[PlayerType.HOST]}\" {self.id})"
        return text

    def check_for_cheating_by_layout(self, client, layout):
        client.player.state = PlayerState.BLOCKED

        test_player = Player(client.player.nick, client.player.salt)
        test_player_type = self.get_playertype_by_nick(test_player.nick)
        if test_player_type is None:
            ErrorMessage(client, "You ain't in this game boy")

        self.player_boards_valid[test_player_type] = True
        for item in layout:
            if not test_player.add_ship_to_board(*ShipParser(item).get_params()):
                self.player_boards_valid[test_player_type] = False
                break

        if not test_player.own_board.check_if_shots_are_valid(self.shots[self.get_opposite_player_type(test_player_type)]):
            self.player_boards_valid[test_player_type] = False
        
        test_hash = hash_game(Battleship().server_salt, test_player.salt, test_player.own_board.get_ship_tuples())
        self.player_hashes_valid[test_player_type] = str(test_hash) == self.player_hashes[test_player_type]

        self.check_if_both_hashes_are_in()

    def check_if_both_hashes_are_in(self):
        if self.player_hashes_valid[PlayerType.HOST] is not None and self.player_hashes_valid[PlayerType.PEER] is not None:
            self.check_hash_validation()

    def check_hash_validation(self):
        if self.are_both_hashes_valid() and self.are_both_boards_valid():
            for c in self.clients.values():
                Message(c, "(game ok)")
        else:
            for c in self.clients.values():
                Message(c, "(game aborted)")
                for player_type in [PlayerType.HOST, PlayerType.PEER]:
                    if not self.player_hashes_valid[player_type]:
                        Message(c, "(hash-mismatch " + str(self.id) + f" \"{self.player_nicks[player_type]}\")")
                    if not self.player_boards_valid[player_type]:
                        Message(c, "(board-mismatch " + str(self.id) + f" \"{self.player_nicks[player_type]}\")")
        Battleship().remove_game(self)
        self.reset_players()
        del self

    def reset_players(self):
        for client in self.clients.values():
            nick = client.player.nick
            salt = client.player.salt
            client.player = Player(nick, salt)
            client.player.state = PlayerState.PLACING_SHIPS

    def are_both_boards_valid(self):
        return self.player_boards_valid[PlayerType.HOST] and self.player_boards_valid[PlayerType.PEER]

    def are_both_hashes_valid(self):
        return self.player_hashes_valid[PlayerType.HOST] and self.player_hashes_valid[PlayerType.PEER]

    def get_playertype_by_nick(self, nick):
        if self.player_nicks[PlayerType.HOST] == nick:
            return PlayerType.HOST
        if self.player_nicks[PlayerType.PEER] == nick:
            return PlayerType.PEER
        return None

    def end_turn(self):
        if self.player_turn == PlayerType.PEER:
            self.check_end_game()

        if self.state == GameState.ACTIVE: 
            self.player_turn = self.get_opposite_player_type(self.player_turn)
            self.turn_state = RoundState.SHOOTING
            self.turn += 1

    def get_opposite_player_type(self, player_type):
        if player_type == PlayerType.HOST:
            return PlayerType.PEER
        elif player_type == PlayerType.PEER:
            return PlayerType.HOST

    def finished(self):
        if self.state == GameState.ENDED:
            return True

    def won(self):
        pass

    def draw(self):
        if self.player_has_won[PlayerType.HOST] and self.player_has_won[PlayerType.PEER]:
            return True
        return False

    def aborted(self):
        pass

    def round(self, x, y):
        opposite_player_type = self.get_opposite_player_type(self.player_turn)
        opposite_client = self.clients[opposite_player_type]
        message = "(shoot " + str(self.id) + " " + str(x) + " " + str(y) + ")"
        Message(opposite_client, message)
        self.shots[self.player_turn].append([x, y, None])
        self.turn_state = RoundState.CHECKING

    def join_peer(self, client, _hash):
        if self.player_nicks[PlayerType.PEER] is None and self.state == GameState.WAITING:
            self.state = GameState.ACTIVE
            self.player_hashes[PlayerType.PEER] = _hash
            self.player_nicks[PlayerType.PEER] = client.player.nick  
            self.clients[PlayerType.PEER] = client 
            Message(client, f"(client joined to game id: {self.id})")
            Message(self.clients[PlayerType.HOST], f"(client joined to game id: {self.id})")
            for c in self.clients.values():
                c.player.state = PlayerState.IN_GAME
        else:
            ErrorMessage(client, "game full")

    def leave(self, player):
        pass

    def shoot(self, x, y, client):
        if self.state == GameState.ACTIVE: 
            player_type = self.get_player_type_by_nick(client.player.nick)
            if self.turn_state == RoundState.SHOOTING:
                if player_type is not None:
                    if player_type == self.player_turn:
                        self.round(x, y)
                        return
        ErrorMessage(client)
        

    def get_player_type_by_nick(self, nick):
        for key in self.player_nicks.keys():
            if self.player_nicks[key] == nick:
                return key

    def try_to_hit(self, client, hit_bool):
        if self.state == GameState.ACTIVE: 
            player_type = self.get_player_type_by_nick(client.player.nick)
            other_player_type = self.get_opposite_player_type(player_type)
            if self.turn_state == RoundState.CHECKING:
                if other_player_type == self.player_turn:
                    self.set_damage(hit_bool)
                    return
        ErrorMessage(client)

    def tell_miss_or_hit_to_player(self, hit_bool):
        if hit_bool:
            Message(self.clients[self.player_turn], "(hit " + str(self.id) + ")")
        else:
            Message(self.clients[self.player_turn], "(miss " + str(self.id) + ")")

    def miss(self):
        self.shots[self.player_turn][-1][2] = False
        self.tell_miss_or_hit_to_player(False)
        self.end_turn()

    def hit(self):
        self.shots[self.player_turn][-1][2] = True
        self.tell_miss_or_hit_to_player(True)
        self.end_turn()

    def set_damage(self, hit_bool):
        if hit_bool:
            self.hit()
        else:
            self.miss()

    def count_hits(self, player_type):
        hits = 0
        for shot in self.shots[player_type]:
            if shot[-1]:
                hits += 1
        return hits

    def check_end_game(self):
        for player_type in [PlayerType.HOST, PlayerType.PEER]:
            hits = self.count_hits(player_type)
            if hits == 17:
                self.player_has_won[player_type] = True
                self.state = GameState.ENDED
        if self.state == GameState.ENDED:
            for player_type in [PlayerType.HOST, PlayerType.PEER]:
                self.clients[player_type].player.state = PlayerState.SENDING_LAYOUT
                Message(self.clients[player_type], self.end_message())

    def end_message(self):
        if self.player_has_won[PlayerType.PEER] and self.player_has_won[PlayerType.HOST]:
            return "(end " + str(self.id) + " draw)"
        else:
            for player_type in [PlayerType.HOST, PlayerType.PEER]:
                if self.player_has_won[player_type]:
                    return "(end " + str(self.id) + " " + self.player_nicks[player_type] + ")"



class ShipParser():

    def __init__(self, ship_compound):
        self.ship_compound = ship_compound

    def get_x(self):
        return self.ship_compound._children[2].value

    def get_y(self):
        return self.ship_compound._children[3].value

    def get_size(self):
        return self.ship_compound._children[1].value
    
    def is_vertical(self):
        if self.ship_compound._children[4].value == "vertical":
            return True
        if self.ship_compound._children[4].value == "horizontal":
            return False

    def get_params(self):
        return self.get_x(), self.get_y(), self.get_size(), self.is_vertical()

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
        self.player = Player(None, None)
        Battleship().game_server.clients.add(self)
        self._drain_lock = asyncio.Lock()
        self.message_reader = MessageReader(self)

    async def parse_cmd(self):
        message = await self.message_reader.read_message()

        asyncio.create_task(parse_message_and_do_commands(self, message))

        #command = 

        #return_message = command.do()

        #asyncio.create_task(return_message)



# Command systems
windows = True

async def testing_env():
    a = asyncio.create_task(Battleship().game_server.start_server())
    #b = asyncio.create_task(tests())
    await a
    #await b

def main():
    if __name__ == "__main__":
        Battleship().game_server = Server()
        asyncio.run(testing_env())

class Tester:
    def __init__(self, nick, salt):
        self.nick = nick
        self.salt = salt

        
        
    async def one_test(self, message):
        await self.write(message)
        return await self.read_and_print()

    async def create_client(self):
        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 8888)
        self.client = Client(self.reader, self.writer)
        return

    async def write(self, message):
        self.writer.write((message+"\n\r").encode())
        await self.writer.drain()


    async def read_and_print(self):
        return_message = await self.reader.readline()
        msg = self.nick + ": " + return_message.decode().lstrip()
        print(msg)
        return return_message.decode()

async def tests():
    tester = Tester("first", "firstSalt")
    tester2 = Tester("second", "secondSalt")
    await tester.create_client()
    await tester2.create_client()

    await test_tested(tester, tester.nick, tester.salt)
    _hash1 = hash_game(Battleship().server_salt,tester.salt,[(6, 8, True), (1, 6, True), (1, 8, False), (2, 2, False), (7, 2, False)])
    _hash2 = hash_game(Battleship().server_salt,tester2.salt,[(6, 8, True), (1, 6, True), (1, 8, False), (2, 2, False), (7, 2, False)])
    message = "(auto \"" + str(_hash1) + "\")"
    await tester.one_test(message)
    await test_tested(tester2, tester2.nick, tester2.salt)
    message = "(list)"
    await tester2.one_test(message)
    message = "(auto \"" + str(_hash2) + "\")"
    game_id = (await tester2.one_test(message)).replace("(client joined to game id: ", "").replace("\r", "").replace(")\n", "").lstrip()
    await tester.read_and_print()

    await shoot_ships(tester, tester2, str(game_id))
    message = "(layout "+str(game_id)+" (ship 5 6 8 vertical) (ship 4 1 6 vertical) (ship 3 1 8 horizontal) (ship 3 2 2 horizontal) (ship 2 7 2 horizontal))"
    await tester.read_and_print()
    await tester2.read_and_print()

    await tester.write(message)
    await tester2.write(message)
    await tester.read_and_print()
    await tester2.read_and_print()
    
    await test_tested(tester, tester.nick, tester.salt)
    await test_tested(tester2, tester2.nick, tester2.salt)
    message = "(list)"
    await tester2.one_test(message)
    message = "(auto \"" + str(_hash2) + "\")"
    await tester2.one_test(message)
    message = "(list)"
    await tester.one_test(message)
    message = "(auto \"" + str(_hash1) + "\")"
    game_id = (await tester.one_test(message)).replace("(client joined to game id: ", "").replace("\r", "").replace(")\n", "").lstrip()
    await tester2.read_and_print()

    await shoot_ships(tester2, tester, str(game_id))
    message = "(layout "+str(game_id)+" (ship 5 6 7 vertical) (ship 4 1 6 vertical) (ship 3 1 8 horizontal) (ship 3 2 2 horizontal) (ship 2 7 2 horizontal))"
    await tester.read_and_print()
    await tester2.read_and_print()

    await tester.write(message)
    await tester2.write(message)
    await tester.read_and_print()
    await tester2.read_and_print()
    await tester.read_and_print()
    await tester2.read_and_print()
    await tester.read_and_print()
    await tester2.read_and_print()
    await tester.read_and_print()
    await tester2.read_and_print()
    await tester.read_and_print()
    await tester2.read_and_print()

    message = "(list)"
    await tester2.one_test(message)

async def shoot_ships(tester, tester2, game_id):
    for i in [[2, 2], [3, 2], [4, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 8], [2, 8], [3, 8], [7, 2], [8, 2], [6, 4], [6, 5], [6, 6], [6, 7], [6, 8]]:
        message = "(shoot " + game_id + " " + str(i[0]) + " " + str(i[1]) + ")"
        message2 = "(hit " + game_id + ")"
        await tester.write(message)
        await tester2.read_and_print()
        await tester2.write(message2)
        await tester.read_and_print()

        await tester2.write(message)
        await tester.read_and_print()
        await tester.write(message2)
        await tester2.read_and_print()

async def test_tested(tester, name, salty):
    message = "(nick \""+name+"\" \""+salty+"\")"
    await tester.one_test(message)
    message = "(put_ship 1 8 3 #f)"
    await tester.one_test(message)
    message = "(put_ship 6 8 5 #t)"
    await tester.one_test(message)
    message = "(put_ship 1 6 4 #t)"
    await tester.one_test(message)
    message = "(put_ship 2 2 3 #f)"
    await tester.one_test(message)
    message = "(put_ship 7 2 2 #f)"
    await tester.one_test(message)

main()


