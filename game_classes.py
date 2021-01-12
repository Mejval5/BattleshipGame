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
                sort_threes()
                return True
            elif self.ships[32] is None:
                self.ships[32] = ship
                sort_threes()
                return True
        return False
        
        
        def sort_threes():
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

        test_hash = get_hash(Battleship.server_salt, test_player.salt, test_player.own_board.get_ship_tuples())


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
        Battleship.list_games().remove_game(self)
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

from enumerators import *
from communication import *
from common import *
import random