# Game classes
from enumerators import *
import random



class Board:

    def __init__(self):
        self.layout = [[]]

    def get_field(self, x, y):  # TODO use this
        return self.layout[y][x]

    def set_field(self, x, y, value):  # TODO use this
        self.layout[y][x] = value

    def return_board_state(self):
        pass

class EnemyBoard(Board):
    def __init__(self):
        super().__init__()
        self.layout = [[BoardFieldType.UNKNOWN for x in range(10)] for y in range(10)]



class PlayerBoard(Board):
    def __init__(self):
        super().__init__()
        self.layout = [[BoardFieldType.WATER for x in range(10)] for y in range(10)]

    def add_ship(self, ship):
        pass

    def ship_crosses_ship(self):
        pass  # TODO

    def ship_crosses_edge(self):
        pass  # TODO


class Ship:
    def __init__(self, x, y, size, vertical):
        self.x = x
        self.y = y
        self.size = size
        self.vertical = vertical

    def take_hit(self):
        pass

    def sink(self):
        pass

    def place_ship(self, board):
        pass

class Player:
    def __init__(self, nick, salt):
        self.nick = nick
        self.own_board = None
        self.enemy_board = None
        self.salt = salt
        self.ships = []
    
    def add_ship_to_board(self, x, y, size, vertical):
        ship = Ship(x, y, size, vertical)
        self.ships.append(ship)
        return self.own_board.add_ship(ship)

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
    def __init__(self, host):
        self.id = random.randint(0,9999999999999)
        self.state = GameState.WAITING  # active / waiting
        self.hit_stat = {PlayerType.HOST: 0, PlayerType.PEER: 0}
        self.player_nicks = {PlayerType.HOST: host.nick, PlayerType.PEER: None}
        self.player_hashes = {PlayerType.HOST: host.hash, PlayerType.PEER: None}  # maybe just players?
        self.turn = 0  #
        self.player_turn = PlayerType.HOST

    def check_for_cheating_by_layout(self, client, layout):
        pass

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
        pass # check if correct player calls round if not, send error

    def join_peer(self, peer, _hash):
        if self.player_nicks[PlayerType.PEER] is not None:
            pass  # send error
        self.state = GameState.ACTIVE
        self.player_hashes[PlayerType.PEER] = _hash
        self.player_nicks[PlayerType.PEER] = peer.nick

    def leave(self, player):
        pass

    def shoot(self, x, y, player):
        pass

    def miss(self):
        pass

    def hit(self):
        pass



