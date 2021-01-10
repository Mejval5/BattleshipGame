# Game classes
from enumerators import *
import random


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
        self.state = [[]]

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
        self.state = self.layout.copy()

    def add_ship(self, ship):
        if not self.ship_crosses_ship(ship) and not self.ship_crosses_edge(ship):
            if not ship.vertical:
                for f in self.state[ship.y]:
                    if ship.x <= f.x < ship.x + ship.size:
                        f.set_value(BoardFieldType.SHIP)
            else:
                for f in self.state:
                    f[ship.x].set_value(BoardFieldType.SHIP)
        else:
            raise RuntimeError()  # co chceme vract při failu?
        return ship  # message nebo messagecommand

    def ship_crosses_ship(self, ship):
        if not ship.vertical:
            for f in self.state[ship.y]:
                if ship.x <= f.x < ship.x + ship.size:
                    if f.value == BoardFieldType.SHIP:
                        return True
        else:
            for row in self.state:
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
        self.id = random.randint(0, 9999999999999)
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
        pass  # check if correct player calls round if not, send error

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



