# André Franciosi de Almeida
# Grupo 6

from collections import deque

class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    def __repr__(self):
        if not self.children:
            return f"Node({self.value})"
        return f"Node({self.value}, {self.children})"

def tokenize(expr):
    expr = expr.replace('(', ' ( ').replace(')', ' ) ')
    return deque(expr.strip().split())

def parse_expression(expr):
    tokens = tokenize(expr)
    return parse_tokens(tokens)

def parse_expression_file(filepath):
    expressions = []
    metadata = {
        'results': [],
        'mem': 0.0
    }
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                tree = parse_expression(line)
                expressions.append(tree)
    return expressions, metadata

def parse_tokens(tokens):
    stack = []
    while tokens:
        token = tokens.popleft()
        if token == '(':
            node = parse_tokens(tokens)
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError("Expressão vazia entre parênteses")

            # Comando especial (N RES)
            if len(stack) >= 2 and stack[-1].value == 'RES':
                n_node = stack.pop(-2)
                return Node('RES', [n_node])

            # Comando especial (V MEM)
            if len(stack) >= 3 and stack[-2].value == 'V' and stack[-1].value == 'MEM':
                v_node = stack.pop(-3)
                return Node('V_MEM', [v_node])

            # Comando especial (MEM)
            if stack[-1].value == 'MEM':
                return Node('MEM')

            # Estrutura if...then...else
            if any(n.value == 'if' for n in stack):
                try:
                    idx_if = [i for i, n in enumerate(stack) if n.value == 'if'][0]
                    idx_then = [i for i, n in enumerate(stack) if n.value == 'then'][0]
                    idx_else = [i for i, n in enumerate(stack) if n.value == 'else'][0]

                    cond = stack[idx_if + 1:idx_then]
                    then_expr = stack[idx_then + 1:idx_else]
                    else_expr = stack[idx_else + 1:]

                    return Node('if', [
                        cond[0] if len(cond) == 1 else Node('cond', cond),
                        then_expr[0] if len(then_expr) == 1 else Node('then', then_expr),
                        else_expr[0] if len(else_expr) == 1 else Node('else', else_expr)
                    ])
                except Exception as e:
                    raise ValueError(f"Erro de sintaxe em estrutura if: {e}")

            # Estrutura for i start end (corpo)
            if len(stack) == 5 and stack[0].value == 'for':
                ident = stack[1]
                start = stack[2]
                end = stack[3]
                body = stack[4]
                return Node('for', [ident, start, end, body])

            # Expressão binária padrão
            if len(stack) >= 3:
                a = stack.pop(0)
                b = stack.pop(0)
                op = stack.pop(0)
                return Node(op.value, [a, b])

            return stack.pop(0)
        else:
            try:
                val = float(token)
                stack.append(Node(val))
            except ValueError:
                stack.append(Node(token))
    return stack[0] if len(stack) == 1 else stack
