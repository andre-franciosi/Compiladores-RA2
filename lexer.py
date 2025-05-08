# André Franciosi de Almeida
# Grupo 6

import re

def lexer(text):
    token_specification = [
        ('NUMBER', r'\d+(\.\d*)?'),
        ('ADD', r'\+'),
        ('SUB', r'-'),
        ('MUL', r'\*'),
        ('DIVINT', r'/'),
        ('DIVREAL', r'\|'),
        ('MOD', r'%'),
        ('POW', r'\^'),
        ('RES', r'\bRES\b'),
        ('MEM', r'\bMEM\b'),
        ('VMEM', r'\bV\b'),
        ('IF', r'\bif\b'),
        ('THEN', r'\bthen\b'),
        ('ELSE', r'\belse\b'),
        ('FOR', r'\bfor\b'),
        ('ID', r'[A-Za-z]+'),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('SKIP', r'[ \t]+'),
        ('NEWLINE', r'\n'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

    tokens = []
    line_num = 1
    line_start = 0

    for mo in re.finditer(tok_regex, text):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start

        if kind == 'NEWLINE':
            line_num += 1
            line_start = mo.end()
            continue
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'{value!r} inesperado na linha {line_num}, coluna {column}')
        
        tokens.append({
            'type': kind,
            'value': value,
            'line': line_num,
            'column': column
        })
    return tokens
