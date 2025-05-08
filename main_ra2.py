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
        if self.pos < len(self.input):
            self.current_char = self.input[self.pos]
        else:
            self.current_char = None

    def _add_token(self, token_type, value):
        self.tokens.append({
            'type': token_type,
            'value': value,
            'line': self.line,
            'col': self.start_col
        })

    def _state_initial(self):
        if self.current_char.isspace():
            self._advance()
        elif self.current_char == '(':
            self._add_token('LPAREN', '(')
            self._advance()
        elif self.current_char == ')':
            self._add_token('RPAREN', ')')
            self._advance()
        elif self.current_char in {'+', '-', '*', '|', '/', '%', '^'}:
            self._add_token('OPERATOR', self.current_char)
            self._advance()
        elif self.current_char.isdigit() or self.current_char == '.':
            self._state_number()
        elif self.current_char.isalpha():
            self._state_identifier()
        else:
            raise SyntaxError(f"Caractere inválido '{self.current_char}' na linha {self.line}, coluna {self.col}")

    def _state_number(self):
        self.start_pos = self.pos
        self.start_col = self.col
        has_decimal = False
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if has_decimal:
                    raise SyntaxError(f"Número inválido na linha {self.line}, coluna {self.col}")
                has_decimal = True
            self._advance()
        value = self.input[self.start_pos:self.pos]
        self._add_token('REAL' if has_decimal else 'INTEGER', value)

    def _state_identifier(self):
        self.start_pos = self.pos
        self.start_col = self.col
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            self._advance()
        value = self.input[self.start_pos:self.pos]
        keywords = {
            'RES': 'RES',
            'MEM': 'MEM',
            'V': 'V',
            'if': 'IF',
            'then': 'THEN',
            'else': 'ELSE',
            'for': 'FOR'
        }
        if value in keywords:
            self._add_token(keywords[value], value)
        else:
            self._add_token('IDENTIFIER', value)

    def tokenize(self):
        while self.current_char is not None:
            self.start_pos = self.pos
            self.start_col = self.col
            self._state_initial()
        return self.tokens

def process_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    lexer = Lexer(content)
    try:
        tokens = lexer.tokenize()
        for token in tokens:
            print(f"{token['type']:8} {token['value']:5} (Line: {token['line']}, Col: {token['col']})")
    except SyntaxError as e:
        print(f"Erro léxico: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo_de_teste>")
        sys.exit(1)
    process_file(sys.argv[1])