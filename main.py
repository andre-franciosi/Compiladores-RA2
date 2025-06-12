import sys
import json
import os
import pathlib
from lexer import Lexer
from parser_ra3 import Parser
from semantic import SemanticAnalyzer
from codegen import CodeGenerator

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo_fonte> [--ast] [--asm]")
        return

    fname = sys.argv[1]
    show_ast = '--ast' in sys.argv
    gen_asm = '--asm' in sys.argv

    try:
        with open(fname, "r", encoding="utf-8") as fp:
            source = fp.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{fname}' não encontrado.")
        return

    # --- 1. Análise Léxica ---
    lexer = Lexer(source)
    tokens, lex_errors = lexer.tokenize()
    if lex_errors:
        print("Erros Léxicos Encontrados:")
        for err in lex_errors:
            print(f"  - {err}")
        return

    # --- 2. Análise Sintática ---
    parser = Parser(tokens)
    syntactically_valid_ast = parser.parse_program()
    if parser.errors:
        print("Erros Sintáticos Encontrados (linhas correspondentes ignoradas):")
        for err in parser.errors:
            print(f"  - {err}")

    # --- 3. Análise Semântica ---
    semantic_analyzer = SemanticAnalyzer()
    semantically_valid_statements = []
    
    for stmt in syntactically_valid_ast['statements']:
        error_count_before = len(semantic_analyzer.errors)
        semantic_analyzer.visit(stmt)
        if len(semantic_analyzer.errors) == error_count_before:
            semantically_valid_statements.append(stmt)
    
    if semantic_analyzer.errors:
        print("\nErros Semânticos Encontrados (linhas correspondentes ignoradas):")
        for err in semantic_analyzer.errors:
            print(f"  - {err}")

    # --- Criação da AST Final e Geração de Código ---
    final_ast = {"type": "Program", "statements": semantically_valid_statements}

    if show_ast:
        print("\n--- AST Final (apenas com instruções válidas) ---")
        print(json.dumps(final_ast, indent=2))
        print("-------------------------------------------------")
    
    if not final_ast['statements']:
        print("\nNenhuma instrução válida restou. Geração de código Assembly cancelada.")
        return
        
    if gen_asm:
        print(f"\nAnalise concluida. Gerando codigo para {len(final_ast['statements'])} instrucao(oes) valida(s)...")
        code_gen = CodeGenerator()
        assembly_code = code_gen.generate(final_ast)
        
        # --- ALTERADO: Bloco para salvar o arquivo na pasta 'out' ---
        try:
            # Define o diretorio de saida
            output_dir = pathlib.Path("out")
            # Cria o diretorio se ele nao existir
            output_dir.mkdir(exist_ok=True)
            
            # Monta o caminho de saida completo (ex: 'out/teste1.S')
            output_filename = output_dir / ("gerado.S")

            with open(output_filename, "w", encoding="latin-1") as fp:
                fp.write(assembly_code)
            print(f"Codigo Assembly gerado com sucesso em '{output_filename}'")
        except IOError as e:
            print(f"Erro ao escrever o arquivo de saida: {e}")


if __name__ == "__main__":
    main()
