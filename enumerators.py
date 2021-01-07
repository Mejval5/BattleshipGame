from enum import Enum

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
    WAITING = 0
    ACTIVE = 1

class BoardFieldType(Enum):
    WATER = 'w'
    MISS = 'm'
    HIT = 'h'
    SHIP = 's'
    UNKNOWN = '?'