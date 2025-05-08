# André Franciosi de Almeida
# Grupo 6

from pathlib import Path
import sys
from lexer import lexer
from parser import parse_expression

def main():
    if len(sys.argv) < 2:
        print("Uso: python main_ra2.py <arquivo.txt>")
        return

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ Arquivo {file_path} não encontrado.")
        return

    with open(file_path, 'r') as f:
        text = f.read()

    print("========== 🔍 ANÁLISE LÉXICA ==========\n")
    try:
        tokens = lexer(text)
        for token in tokens:
            print(f"({token['value']}, {token['type']}, {token['line']}, {token['column']})")
    except Exception as e:
        print(f"❌ Erro léxico: {e}")

    print("\n========== 🌳 ANÁLISE SINTÁTICA ==========\n")
    lines = text.strip().splitlines()
    for line_num, line in enumerate(lines, start=1):
        try:
            if not line.strip():
                continue
            tree = parse_expression(line)
            print(f"Linha {line_num}: {line.strip()}")
            print(f"AST: {tree}\n")
        except Exception as e:
            print(f"❌ Erro sintático na linha {line_num}: {e}\n")

if __name__ == "__main__":
    main()
