# parser_ra3.py
# Baseado no seu arquivo parser.py

# AST helpers - Funções para criar os nós da AST
def num(value, kind): return {"type": "Number", "value": value, "kind": kind}
def ident(name): return {"type": "Identifier", "name": name}
def mem(): return {"type": "Mem"}
def op(symbol, args): return {"type": "Op", "op": symbol, "args": args}
def res(arg): return {"type": "Res", "arg": arg}
def res_rel(n): return {"type": "ResRelative", "n": n}
def store(val): return {"type": "Store", "val": val}
def if_node(c, t, e): return {"type": "If", "cond": c, "then_b": t, "else_b": e}
def for_node(i, s, e, b): return {"type": "For", "id": i, "start": s, "end": e, "body": b}
def program_node(statements): return {"type": "Program", "statements": statements}

def with_meta(node, token):
    """Adiciona metadados (linha, coluna) a um nó da AST."""
    if node:
        node['line'] = token['line']
        node['col'] = token['col']
    return node

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.errors = []

    def error(self, message, token=None):
        token = token or self.current_token
        self.errors.append(f"Erro de Parser na linha {token['line']}:{token['col']}: {message}")

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        return self.current_token

    def eat(self, token_type):
        if self.current_token['type'] == token_type:
            self.advance()
        else:
            self.error(f"Esperado {token_type}, mas encontrou {self.current_token['type']}")

    def parse_program(self):
        statements = []
        while self.current_token['type'] != 'EOF':
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            # Sincronização em caso de erro para tentar continuar
            if self.errors and self.current_token['type'] != 'EOF':
                 # Tenta avançar para a próxima declaração, que pode começar com palavras-chave
                 while self.current_token['type'] not in ['IF', 'FOR', 'LPAREN', 'INT', 'FLOAT', 'ID', 'EOF']:
                     self.advance()
        return program_node(statements)
    def parse_statement(self):
        start_token = self.current_token  # Guarda o token inicial para metadados
        node = None
        if self.current_token['type'] == 'LPAREN':
            node = self.parse_rpn_expression()
        elif self.current_token['type'] == 'IF':
            node = self.parse_if()
        elif self.current_token['type'] == 'FOR':
            node = self.parse_for()
        else:
            self.error(f"Declaração inválida iniciada com {self.current_token['type']}")
            self.advance() # Evita loop infinito
            return None
        
        # Adiciona a informação de linha/coluna ao nó da instrução
        return with_meta(node, start_token)

    def parse_rpn_expression(self):
        self.eat('LPAREN')
        nodes = []
        # Loop para coletar todos os tokens/nós dentro dos parênteses
        while self.current_token['type'] not in ['RPAREN', 'EOF']:
            node = self.parse_rpn_token()
            if node:
                nodes.append(node)
            else:
                # Um erro foi encontrado e reportado por parse_rpn_token.
                # Para nos recuperarmos, pulamos até o fechamento dos parênteses.
                while self.current_token['type'] not in ['RPAREN', 'EOF']:
                    self.advance()
                break  # Sai do loop 'while' para esta expressão RPN

        self.eat('RPAREN')

        # Constrói a árvore de expressão a partir da notação RPN
        stack = []
        for node in nodes:
            # Esta verificação agora é segura porque 'nodes' não contém None
            if node['type'] in ['PLUS', 'MINUS', 'MUL', 'DIV', 'MOD', 'POW', 'PIPE']:
                if len(stack) < 2:
                    self.error("Operador RPN com operandos insuficientes")
                    return None
                right = stack.pop()
                left = stack.pop()
                stack.append(op(node['value'], [left, right]))
            elif node['type'] == 'Store':
                 if not stack:
                     self.error("V MEM requer um valor na pilha")
                     return None
                 val = stack.pop()
                 stack.append(store(val))
            elif node['type'] == 'ResRelative':
                if not stack:
                    self.error("N RES requer um valor na pilha")
                    return None
                n_val = stack.pop()
                stack.append(res_rel(n_val))
            else:
                stack.append(node)
        
        if not nodes: # Se a expressão estava vazia ou continha apenas erros
            return None

        if len(stack) != 1:
            self.error("Expressão RPN malformada")
            return None
        
        return res(stack[0])

    def parse_rpn_token(self):
        token = self.current_token
        self.advance()

        if token['type'] == 'INT':
            return num(token['value'], 'int')
        if token['type'] == 'FLOAT':
            return num(token['value'], 'float')
        if token['type'] == 'ID':
            return ident(token['value'])
        if token['type'] in ['PLUS', 'MINUS', 'MUL', 'DIV', 'MOD', 'POW', 'PIPE']:
            return {'type': token['type'], 'value': token['value']}

        # Comandos especiais
        if token['type'] == 'N':
            self.eat('RES')
            return {'type': 'ResRelative'}
        if token['type'] == 'V':
            self.eat('MEM')
            return {'type': 'Store'}
        if token['type'] == 'MEM':
            return mem()
        
        self.error(f"Token inesperado '{token['value']}' na expressão RPN")
        return None

    def parse_if(self):
        self.eat('IF')
        cond = self.parse_rpn_expression()
        self.eat('THEN')
        then_b = self.parse_statement()
        else_b = None
        if self.current_token['type'] == 'ELSE':
            self.eat('ELSE')
            else_b = self.parse_statement()
        return if_node(cond, then_b, else_b)

    def parse_for(self):
        self.eat('FOR')
        var_id = ident(self.current_token['value'])
        self.eat('ID')
        start = self.parse_rpn_expression()
        end = self.parse_rpn_expression()
        body = self.parse_statement()
        return for_node(var_id, start, end, body)