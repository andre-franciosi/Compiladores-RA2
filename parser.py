import sys
from main_ra2 import Lexer

"""
Parser RA‑3 – Análise Sintática (LL(1))
-------------------------------------------------
* Descendente recursivo puro (sem bibliotecas externas)
* Panic‑mode recovery: continua após erro e tenta analisar o resto
* Gera AST para:
  – Operações RPN  + − * / % | ^
  – Comandos  N RES  (resultado relativo),  V MEM  (store),  MEM (load)
  – Construções  (if … then … else …)  e  (for id ini fim corpo)
USO:
    python parser.py fonte.txt [--ast]
"""

# ───────────────── AST helpers ─────────────────

def num(value, kind):  
    return {"type": "Number", "value": value, "kind": kind}

def ident(name):         return {"type": "Identifier", "name": name}

def mem():               return {"type": "Mem"}

def op(symbol, args):    return {"type": "Op", "op": symbol, "args": args}

def res(arg):            return {"type": "Res", "arg": arg}               # topo pilha

def res_rel(n):          return {"type": "ResRelative", "n": n}           # N RES

def store(val):          return {"type": "Store", "val": val}             # V MEM

def if_node(c, t, e):    return {"type": "If", "cond": c, "then": t, "else": e}

def for_node(v, i, f, b):return {"type": "For", "var": v, "init": i, "end": f, "body": b}

_AST_TYPES = {
    "Number", "Identifier", "Mem", "Op", "Res", "ResRelative",
    "Store", "If", "For"
}

# ──────────────────── PARSER ────────────────────
class Parser:
    """LL(1) parser descendente com panic‑mode."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors: list[str] = []

    # -------- utilidades básicas --------
    def curr(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def error(self, msg, tok=None):
        tok = tok or self.curr()
        line = tok.get("line", "?") if tok else "?"
        col  = tok.get("col", "?") if tok else "?"
        self.errors.append(f"[linha {line}, col {col}] {msg}")

    def synchronize(self):
        # Consome o token que causou o erro
        if self.curr():
            self.pos += 1

        sync = {"LPAREN", "RPAREN", "INTEGER", "REAL", "IDENTIFIER", "MEM"}
        while self.curr() and self.curr()["type"] not in sync:
            self.pos += 1


    def expect(self, kind):
        tok = self.curr()
        if not tok or tok["type"] != kind:
            self.error(f"Esperado {kind}, encontrado {tok['type'] if tok else 'EOF'}", tok)
            self.synchronize()
            return {"type": kind, "value": None}
        self.pos += 1
        return tok

    # --------------- entrada ---------------
    def parse_program(self):
        prog = []
        while self.curr():
            try:
                prog.append(self.parse_expr())
            except SyntaxError as exc:
                self.error(str(exc))
                self.synchronize()
        return prog

    # -------------- expressões --------------
    def parse_expr(self):
        tok = self.curr()
        if tok is None:
            raise SyntaxError("Fim inesperado")

        t = tok["type"]

        if t == "LPAREN":
            return self.parse_list()

        if t in {"INTEGER", "REAL"}:
            self.pos += 1
            return num(tok["value"], t)

        if t == "IDENTIFIER":
            self.pos += 1
            return ident(tok["value"])

        if t == "MEM":
            self.pos += 1
            return mem()

        raise SyntaxError(f"Token inesperado {t}")


    # -------- listas entre parênteses --------
    def parse_list(self):
        self.expect("LPAREN")
        if not self.curr():
            self.error("Parêntese aberto sem conteúdo")
            return {"type": "Error"}
        head = self.curr()["type"]
        if head == "IF":
            node = self.parse_if()
        elif head == "FOR":
            node = self.parse_for()
        else:
            node = self.parse_rpn()
        self.expect("RPAREN")
        return node

    def parse_if(self):
        self.expect("IF")
        cond = self.parse_expr(); self.expect("THEN")
        thn  = self.parse_expr(); self.expect("ELSE")
        els  = self.parse_expr()
        return if_node(cond, thn, els)

    def parse_for(self):
        self.expect("FOR")
        var_tok = self.expect("IDENTIFIER")
        ini = self.parse_expr(); end = self.parse_expr(); body = self.parse_expr()
        return for_node(var_tok["value"], ini, end, body)

    # ----------------- RPN ------------------
    def parse_rpn(self):
        elems = []
        while self.curr() and self.curr()["type"] != "RPAREN":
            t = self.curr()["type"]
            if t == "LPAREN":
                elems.append(self.parse_expr())
            elif t in {"INTEGER", "REAL", "IDENTIFIER", "MEM"}:
                elems.append(self.parse_expr())
            else:  # operador / palavra-chave
                elems.append(self.curr()); self.pos += 1
        return self._validate_rpn(elems)

    # ---------- helpers binários ----------
    @staticmethod
    def _is_ast(node):
        return isinstance(node, dict) and node.get("type") in _AST_TYPES

    def _bin_symbol(self, token):
        if token["type"] == "OPERATOR":
            return token["value"]
        mapping = {
            "PLUS": "+", "MINUS": "-", "STAR": "*", "SLASH": "/",
            "PIPE": "|", "MOD": "%", "POW": "^"
        }
        return mapping.get(token["type"])

    # ------------- validação RPN -------------
    def _validate_rpn(self, elems):
        stack = []
        i = 0
        while i < len(elems):
            node = elems[i]
            if self._is_ast(node):
                stack.append(node); i += 1; continue

            ttype = node["type"]
            # ---- operador binário ----
            sym = self._bin_symbol(node)
            if sym is not None:
                if len(stack) < 2:
                    self.error("Operador binário sem operandos suficientes", node)
                    return {"type": "Error"}
                b = stack.pop(); a = stack.pop(); stack.append(op(sym, [a, b]))
                i += 1; continue

            # ---- RES / N RES ----
            if ttype == "RES":
                if not stack:
                    self.error("RES sem operando", node)
                    return {"type": "Error"}

                val = stack.pop()

                # Caso seja um número inteiro → N RES
                if val["type"] == "Number" and val.get("kind") == "INTEGER":
                    stack.append(res_rel(int(val["value"])))
                else:
                    # Qualquer outra coisa (real, identificador, expr) → RES simples
                    if val["type"] == "Number" and val.get("kind") != "INTEGER":
                        self.error("N RES requer operando inteiro", node)
                    stack.append(res(val))

                i += 1
                continue


            # ---- V MEM ----
            if ttype == "V":
                nxt = elems[i + 1] if i + 1 < len(elems) else None
                is_mem = nxt and ((isinstance(nxt, dict) and nxt.get("type") == "Mem") or (not isinstance(nxt, dict) and nxt["type"] == "MEM"))
                if not is_mem:
                    self.error("Uso de V exige MEM logo após", node); return {"type": "Error"}
                if not stack:
                    self.error("V MEM requer valor", node); return {"type": "Error"}
                val = stack.pop(); stack.append(store(val)); i += 2; continue

            # ---- desconhecido ----
            self.error(f"Token inesperado {ttype} na expressão RPN", node); return {"type": "Error"}

        if len(stack) != 1:
            self.error("Expressão RPN mal‑formada – sobram operandos")
            return {"type": "Error"}
        return stack[0]

# ────────────────── CLI ──────────────────

def process_file(fname: str, show_ast: bool = False):
    """Processa um arquivo fonte e exibe resultados."""
    with open(fname, "r", encoding="utf-8") as fp:
        source = fp.read()
    
    # Análise léxica
    lexer = Lexer(source)
    tokens, lex_errors = lexer.tokenize()
    if lex_errors:
        print("\n".join(lex_errors))
        return
    
    # Análise sintática
    parser = Parser(tokens)
    ast = parser.parse_program()
    
    # Exibir erros
    if parser.errors:
        print("\n".join(parser.errors))
    
    # Exibir AST se solicitado
    if show_ast:
        import json
        print(json.dumps(ast, indent=2))

# Ponto de entrada principal
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USO: python parser.py fonte.txt [--ast]")
        sys.exit(1)
    
    fname = sys.argv[1]
    show_ast = "--ast" in sys.argv
    process_file(fname, show_ast)
