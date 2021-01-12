from lisp import *

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
