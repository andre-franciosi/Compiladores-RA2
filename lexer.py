# lexer.py
# Baseado no seu arquivo main_ra2.py

import sys

class Lexer:
    def __init__(self, input_text):
        self.input = input_text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.start_pos = 0
        self.start_col = 1
        self.current_char = self.input[self.pos] if self.pos < len(self.input) else None
        self.tokens = []

    def _advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.col = 0
        self.pos += 1
        self.col += 1
        self.current_char = self.input[self.pos] if self.pos < len(self.input) else None

    def _add_token(self, token_type, value):
        self.tokens.append({
            'type': token_type,
            'value': value,
            'line': self.line,
            'col': self.start_col
        })

    def _make_number(self):
        num_str = ''
        dot_count = 0
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
            num_str += self.current_char
            self._advance()
        
        if dot_count == 0:
            self._add_token('INT', int(num_str))
        else:
            self._add_token('FLOAT', float(num_str))

    def _make_identifier(self):
        id_str = ''
        while self.current_char is not None and self.current_char.isalnum():
            id_str += self.current_char
            self._advance()
        
        keywords = {
            'N': 'N', 'RES': 'RES', 'V': 'V', 'MEM': 'MEM',
            'if': 'IF', 'then': 'THEN', 'else': 'ELSE',
            'for': 'FOR'
        }
        token_type = keywords.get(id_str, 'ID')
        self._add_token(token_type, id_str)

    def tokenize(self):
        errors = []
        while self.current_char is not None:
            self.start_pos = self.pos
            self.start_col = self.col

            if self.current_char.isspace():
                self._advance()
                continue
            
            if self.current_char.isdigit():
                self._make_number()
                continue

            if self.current_char.isalnum():
                self._make_identifier()
                continue
            
            # Mapeamento de caracteres para tokens
            char_to_token = {
                '(': 'LPAREN', ')': 'RPAREN',
                '+': 'PLUS', '-': 'MINUS', '*': 'MUL', '/': 'DIV',
                '%': 'MOD', '|': 'PIPE', '^': 'POW'
            }

            if self.current_char in char_to_token:
                self._add_token(char_to_token[self.current_char], self.current_char)
                self._advance()
            else:
                errors.append(f"Caractere ilegal '{self.current_char}' na linha {self.line}:{self.col}")
                self._advance()

        self._add_token('EOF', None)
        return self.tokens, errors